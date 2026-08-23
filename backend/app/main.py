from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from src.data.dataset import BioMapDataset
from src.segmentation.base import Detection
from src.segmentation.classical import ClassicalSegmenter
from src.tracking.centroid_tracker import CentroidTracker
from src.tracking.events import DivisionDetector
from src.lineage.reconstruct import LineageReconstructor


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="BioMap API",
    version="2.0.0",
    description="Cell segmentation, tracking and lineage reconstruction API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

# BioMap/
# ├── backend/
# │   ├── app/main.py
# │   └── src/
# └── datasets/

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = PROJECT_ROOT / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

dataset_cache: dict[str, BioMapDataset] = {}


# ============================================================
# REQUEST MODELS
# ============================================================

class PipelineRequest(BaseModel):
    mode: str = "basic"
    start_frame: int = 0
    end_frame: Optional[int] = None


# ============================================================
# DATASET HELPERS
# ============================================================

def get_available_datasets() -> list[str]:
    return sorted(
        item.name
        for item in DATASETS_DIR.iterdir()
        if item.is_dir() and not item.name.startswith(".")
    )


def get_dataset(dataset_name: str) -> BioMapDataset:
    if dataset_name not in get_available_datasets():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_name}' not found.",
        )

    if dataset_name not in dataset_cache:
        try:
            dataset_cache[dataset_name] = BioMapDataset(
                DATASETS_DIR / dataset_name
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load dataset: {exc}",
            ) from exc

    return dataset_cache[dataset_name]


def normalise_mode(mode: str) -> str:
    value = mode.strip().lower()

    if value in {"basic", "classical", "fast", "basic / fast (classical)"}:
        return "basic"

    if value in {"advanced", "ai", "cellpose", "advanced / ai (cellpose)"}:
        return "advanced"

    raise HTTPException(
        status_code=400,
        detail=(
            f"Unknown processing mode '{mode}'. "
            "Use 'basic' or 'advanced'."
        ),
    )


# ============================================================
# GT HELPERS
# ============================================================

def find_segmentation_gt(
    dataset_name: str,
    sequence_id: str,
    frame_idx: int,
) -> Optional[Path]:
    dataset_dir = DATASETS_DIR / dataset_name

    candidates = [
        dataset_dir
        / f"{sequence_id}_ST"
        / "SEG"
        / f"man_seg{frame_idx:03d}.tif",

        dataset_dir
        / f"{sequence_id}_ST"
        / "SEG"
        / f"man_seg_{frame_idx:03d}.tif",
    ]

    return next((path for path in candidates if path.exists()), None)


def find_tracking_gt(
    dataset_name: str,
    sequence_id: str,
) -> Optional[Path]:
    dataset_dir = DATASETS_DIR / dataset_name

    candidates = [
        dataset_dir
        / f"{sequence_id}_GT"
        / "TRA"
        / "man_track.txt",

        dataset_dir
        / f"{sequence_id}_ST"
        / "TRA"
        / "man_track.txt",
    ]

    return next((path for path in candidates if path.exists()), None)


def load_gt_mask(path: Path) -> np.ndarray:
    import tifffile

    mask = tifffile.imread(path)

    if mask.ndim == 3:
        mask = np.max(mask, axis=0)

    return mask


# ============================================================
# DETECTION EVALUATION
# ============================================================

def evaluate_frame_detections(
    detections: list[Detection],
    gt_mask: np.ndarray,
) -> dict:
    """
    Evaluate centroid detections against a labelled GT mask.

    A prediction is considered a hit when its centroid falls inside
    a GT object.

    Each GT object can only be credited once, preventing multiple
    predictions inside the same cell from artificially increasing TP.
    """

    gt_labels = np.unique(gt_mask)
    gt_labels = gt_labels[gt_labels > 0]

    gt_count = len(gt_labels)

    hit_labels: set[int] = set()
    prediction_hits = 0

    for detection in detections:
        x, y = detection.centroid

        x = int(round(x))
        y = int(round(y))

        if (
            y < 0
            or y >= gt_mask.shape[0]
            or x < 0
            or x >= gt_mask.shape[1]
        ):
            continue

        label = int(gt_mask[y, x])

        if label > 0:
            prediction_hits += 1
            hit_labels.add(label)

    tp = len(hit_labels)
    fp = max(0, len(detections) - tp)
    fn = max(0, gt_count - tp)

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "ground_truth": gt_count,
        "predicted": len(detections),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ============================================================
# TRACKING GT / DIVISION EVALUATION
# ============================================================

def load_gt_lineage(path: Path) -> list[dict]:
    lineage = []

    with path.open("r") as handle:
        for line in handle:
            parts = line.strip().split()

            if len(parts) != 4:
                continue

            cell_id, start, end, parent_id = map(int, parts)

            lineage.append(
                {
                    "track_id": cell_id,
                    "start_frame": start,
                    "end_frame": end,
                    "parent_id": parent_id,
                }
            )

    return lineage


def get_gt_division_events(
    lineage: list[dict],
) -> list[dict]:
    children_by_parent: dict[int, list[int]] = {}

    for record in lineage:
        parent = record["parent_id"]

        if parent <= 0:
            continue

        children_by_parent.setdefault(parent, []).append(
            record["track_id"]
        )

    events = []

    for parent_id, children in children_by_parent.items():
        if len(children) >= 2:
            events.append(
                {
                    "parent_id": parent_id,
                    "children": children,
                }
            )

    return events


def evaluate_divisions(
    predicted_events: list[dict],
    gt_events: list[dict],
) -> dict:
    """
    Conservative event-level evaluation.

    A predicted event counts as a TP only when its parent corresponds
    to a GT division parent. This avoids pretending that merely having
    the same number of events means the biological events were correct.
    """

    gt_by_parent = {
        int(event["parent_id"]): event
        for event in gt_events
    }

    matched_gt: set[int] = set()
    tp = 0

    for event in predicted_events:
        parent_id = int(event["parent_id"])

        if parent_id in gt_by_parent and parent_id not in matched_gt:
            matched_gt.add(parent_id)
            tp += 1

    fp = max(0, len(predicted_events) - tp)
    fn = max(0, len(gt_events) - tp)

    precision = (
        tp / (tp + fp)
        if tp + fp
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "ground_truth": len(gt_events),
        "predicted": len(predicted_events),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ============================================================
# DATASET API
# ============================================================

@app.get("/api/datasets")
def list_datasets():
    return {
        "datasets": get_available_datasets()
    }


@app.get("/api/datasets/{dataset_name}/metadata")
def get_dataset_metadata(dataset_name: str):
    dataset = get_dataset(dataset_name)

    sequences = {}

    for sequence_id in dataset.sequences():
        meta = dataset.metadata.sequence_metadata[sequence_id]

        sequences[sequence_id] = {
            "frameCount": meta.frame_count,
            "shape": list(meta.frame_shape),
            "dtype": str(meta.frame_dtype),
            "hasGroundTruth": bool(meta.has_gt),
            "hasTracking": bool(meta.has_tra),
        }

    return {
        "name": dataset.metadata.name,
        "sequences": sequences,
    }


# ============================================================
# ZIP UPLOAD
# ============================================================

@app.post("/api/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
):
    filename = file.filename or ""

    if not filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP datasets are supported.",
        )

    dataset_name = Path(filename).stem
    extract_path = DATASETS_DIR / dataset_name
    temp_zip = DATASETS_DIR / f".{dataset_name}.upload.zip"

    if extract_path.exists():
        return {
            "message": "Dataset already exists.",
            "name": dataset_name,
        }

    try:
        with temp_zip.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with zipfile.ZipFile(temp_zip, "r") as archive:
            bad_file = archive.testzip()

            if bad_file is not None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Corrupt ZIP entry: {bad_file}",
                )

            archive.extractall(extract_path)

        # Some CTC ZIPs may contain one top-level directory.
        nested = list(extract_path.iterdir())

        if (
            len(nested) == 1
            and nested[0].is_dir()
            and not (extract_path / "01").exists()
        ):
            inner = nested[0]

            for item in inner.iterdir():
                shutil.move(str(item), str(extract_path / item.name))

            inner.rmdir()

        try:
            dataset_cache[dataset_name] = BioMapDataset(
                extract_path
            )
        except Exception as exc:
            shutil.rmtree(extract_path, ignore_errors=True)

            raise HTTPException(
                status_code=400,
                detail=f"Invalid CTC dataset: {exc}",
            ) from exc

        return {
            "message": "Dataset uploaded successfully.",
            "name": dataset_name,
        }

    except HTTPException:
        raise

    except zipfile.BadZipFile as exc:
        shutil.rmtree(extract_path, ignore_errors=True)

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid ZIP archive.",
        ) from exc

    except Exception as exc:
        shutil.rmtree(extract_path, ignore_errors=True)

        raise HTTPException(
            status_code=500,
            detail=f"Dataset upload failed: {exc}",
        ) from exc

    finally:
        if temp_zip.exists():
            temp_zip.unlink()


# ============================================================
# FRAME IMAGE API
# ============================================================

@app.get(
    "/api/datasets/{dataset_name}/sequence/{sequence_id}"
    "/frame/{frame_idx}/image"
)
def get_frame_image(
    dataset_name: str,
    sequence_id: str,
    frame_idx: int,
):
    dataset = get_dataset(dataset_name)

    try:
        volume = dataset.load_frame(
            frame_idx,
            sequence=sequence_id,
        )

        if volume.ndim == 3:
            image = np.max(volume, axis=0)
        else:
            image = volume

        normalized = cv2.normalize(
            image,
            None,
            0,
            255,
            cv2.NORM_MINMAX,
            dtype=cv2.CV_8U,
        )

        success, encoded = cv2.imencode(
            ".png",
            normalized,
        )

        if not success:
            raise RuntimeError("Could not encode frame as PNG.")

        return Response(
            content=encoded.tobytes(),
            media_type="image/png",
        )

    except IndexError as exc:
        raise HTTPException(
            status_code=404,
            detail="Frame index out of bounds.",
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load frame: {exc}",
        ) from exc


# ============================================================
# PIPELINE
# ============================================================

@app.post(
    "/api/datasets/{dataset_name}/sequence/{sequence_id}/analyze"
)
def run_pipeline(
    dataset_name: str,
    sequence_id: str,
    request: PipelineRequest,
):
    dataset = get_dataset(dataset_name)

    mode = normalise_mode(request.mode)

    max_frames = dataset.frame_count(sequence_id)

    start_frame = max(
        0,
        min(request.start_frame, max_frames - 1),
    )

    end_frame = (
        max_frames
        if request.end_frame is None
        else min(max(request.end_frame, start_frame + 1), max_frames)
    )

    if start_frame >= end_frame:
        raise HTTPException(
            status_code=400,
            detail="Invalid frame range.",
        )

    # --------------------------------------------------------
    # SEGMENTER
    # --------------------------------------------------------

    if mode == "basic":
        segmenter = ClassicalSegmenter()

    else:
        # Advanced mode is deliberately imported lazily.
        # Cellpose is an optional/heavier dependency.
        try:
            from src.segmentation.cellpose import CellposeSegmenter

            segmenter = CellposeSegmenter()

        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Advanced / Cellpose mode is unavailable. "
                    "Make sure CellposeSegmenter is installed."
                ),
            ) from exc

    # --------------------------------------------------------
    # TRACKING / LINEAGE
    # --------------------------------------------------------

    tracker = CentroidTracker(
        max_distance=50.0,
        max_missed_frames=3,
    )

    division_detector = DivisionDetector(
        max_parent_daughter_distance=80.0,
        temporal_window=5,
        min_parent_length=3,
        min_confidence=0.3,
    )

    lineage_reconstructor = LineageReconstructor(
        division_detector=division_detector,
    )

    all_detections: list[list[Detection]] = []

    # --------------------------------------------------------
    # PER-FRAME ANALYSIS
    # --------------------------------------------------------

    frame_statistics = []

    evaluation_frames = 0
    detection_tp = 0
    detection_fp = 0
    detection_fn = 0
    detection_gt = 0
    detection_predictions = 0

    for frame_idx in range(start_frame, end_frame):
        volume = dataset.load_frame(
            frame_idx,
            sequence=sequence_id,
        )

        segmentation = segmenter.segment(volume)

        detections: list[Detection] = []

        for cell in segmentation.detections:
            detections.append(
                Detection(
                    detection_id=cell.cell_id,
                    centroid=cell.centroid,
                    area=cell.area,
                    mask=cell.mask,
                    confidence=getattr(
                        cell,
                        "confidence",
                        1.0,
                    ),
                )
            )

        all_detections.append(detections)

        frame_stat = {
            "frame": frame_idx,
            "detections": len(detections),
            "groundTruth": None,
            "truePositives": None,
            "falsePositives": None,
            "falseNegatives": None,
            "precision": None,
            "recall": None,
            "f1": None,
        }

        gt_path = find_segmentation_gt(
            dataset_name,
            sequence_id,
            frame_idx,
        )

        if gt_path is not None:
            gt_mask = load_gt_mask(gt_path)

            metrics = evaluate_frame_detections(
                detections,
                gt_mask,
            )

            evaluation_frames += 1

            detection_gt += metrics["ground_truth"]
            detection_predictions += metrics["predicted"]
            detection_tp += metrics["true_positives"]
            detection_fp += metrics["false_positives"]
            detection_fn += metrics["false_negatives"]

            frame_stat.update(
                {
                    "groundTruth": metrics["ground_truth"],
                    "truePositives": metrics["true_positives"],
                    "falsePositives": metrics["false_positives"],
                    "falseNegatives": metrics["false_negatives"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["f1"],
                }
            )

        frame_statistics.append(frame_stat)

    # --------------------------------------------------------
    # TRACKING
    # --------------------------------------------------------

    tracking_result = tracker.track(all_detections)

    tracks_data = {}

    for track_id, track in tracking_result.tracks.items():
        tracks_data[str(track_id)] = {
            "track_id": track.track_id,
            "positions": [
                [float(x), float(y)]
                for x, y in track.positions
            ],
            "frames": [
                int(frame)
                for frame in track.frames
            ],
            "areas": [
                float(area)
                for area in getattr(track, "areas", [])
            ],
            "mean_confidence": float(
                getattr(track, "mean_confidence", 1.0)
            ),
            "length": track.length,
            "start_frame": track.start_frame,
            "end_frame": track.end_frame,
        }

    # --------------------------------------------------------
    # LINEAGE
    # --------------------------------------------------------

    lineage_result = lineage_reconstructor.reconstruct(
        tracking_result
    )

    lineage_data = lineage_result.to_dict()

    predicted_divisions = lineage_data.get(
        "division_events",
        [],
    )

    # --------------------------------------------------------
    # GROUND TRUTH DIVISIONS
    # --------------------------------------------------------

    gt_lineage_path = find_tracking_gt(
        dataset_name,
        sequence_id,
    )

    gt_division_events = []

    if gt_lineage_path is not None:
        gt_lineage = load_gt_lineage(
            gt_lineage_path
        )

        gt_division_events = get_gt_division_events(
            gt_lineage
        )

    division_metrics = evaluate_divisions(
        predicted_divisions,
        gt_division_events,
    )

    # --------------------------------------------------------
    # GLOBAL DETECTION METRICS
    # --------------------------------------------------------

    global_precision = (
        detection_tp / (detection_tp + detection_fp)
        if detection_tp + detection_fp
        else 0.0
    )

    global_recall = (
        detection_tp / (detection_tp + detection_fn)
        if detection_tp + detection_fn
        else 0.0
    )

    global_f1 = (
        2
        * global_precision
        * global_recall
        / (global_precision + global_recall)
        if global_precision + global_recall
        else 0.0
    )

    # --------------------------------------------------------
    # DATASET / ANALYSIS SUMMARY
    # --------------------------------------------------------

    total_tracks = len(tracks_data)

    persistent_tracks = sum(
        1
        for track in tracks_data.values()
        if track["length"] >= 2
    )

    average_track_length = (
        sum(track["length"] for track in tracks_data.values())
        / total_tracks
        if total_tracks
        else 0.0
    )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "status": "success",

        "dataset": {
            "name": dataset_name,
            "sequence": sequence_id,
            "mode": mode,
            "startFrame": start_frame,
            "endFrame": end_frame - 1,
            "framesProcessed": end_frame - start_frame,
            "totalFrames": max_frames,
        },

        "capabilities": {
            "hasGroundTruth": gt_lineage_path is not None
            or evaluation_frames > 0,
            "hasTrackingGroundTruth": gt_lineage_path is not None,
            "hasSegmentationGroundTruth": evaluation_frames > 0,
            "advancedAvailable": True,
        },

        "statistics": {
            "totalTracks": total_tracks,
            "persistentTracks": persistent_tracks,
            "averageTrackLength": average_track_length,
            "divisionEvents": len(predicted_divisions),
            "groundTruthDivisionEvents": len(
                gt_division_events
            ),
        },

        "tracking": {
            "trackCount": total_tracks,
            "persistentTrackCount": persistent_tracks,
            "tracks": tracks_data,
        },

        "lineage": lineage_data,

        "evaluation": {
            "segmentation": {
                "framesEvaluated": evaluation_frames,
                "groundTruthCells": detection_gt,
                "predictedCells": detection_predictions,
                "truePositives": detection_tp,
                "falsePositives": detection_fp,
                "falseNegatives": detection_fn,
                "precision": global_precision,
                "recall": global_recall,
                "f1": global_f1,
            },

            "division": division_metrics,
        },

        "frames": frame_statistics,

        "frameRange": {
            "start": start_frame,
            "end": end_frame - 1,
            "count": end_frame - start_frame,
        },

    "summary": {
        "trackCount": tracking_result.track_count,
        "divisionCount": len(lineage_data.get("division_events", [])),
    },
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "BioMap API",
        "version": app.version,
    }