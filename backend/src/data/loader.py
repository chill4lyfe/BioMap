# src/data/loader.py

from pathlib import Path
from typing import Optional

import tifffile
import numpy as np


class DatasetLoader:
    """
    Low-level loader for CTC-style microscopy datasets.

    This class is deliberately responsible only for:
        - locating files
        - loading TIFF volumes
        - discovering annotations

    It does NOT perform:
        - preprocessing
        - segmentation
        - tracking
        - visualization
    """

    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path)

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset directory does not exist: {self.dataset_path}"
            )

    # ------------------------------------------------------------------
    # Sequence discovery
    # ------------------------------------------------------------------

    def list_sequences(self) -> list[str]:
        """
        Return sequence directories such as:

            ["01", "02", ...]
        """

        sequences = []

        for path in sorted(self.dataset_path.iterdir()):
            if path.is_dir() and path.name.isdigit():
                sequences.append(path.name)

        return sequences

    # ------------------------------------------------------------------
    # Raw frames
    # ------------------------------------------------------------------

    def get_raw_dir(self, sequence: str) -> Path:
        """Return the raw image directory for a sequence."""

        path = self.dataset_path / sequence

        if not path.exists():
            raise FileNotFoundError(
                f"Sequence does not exist: {sequence}"
            )

        return path

    def list_raw_frames(self, sequence: str) -> list[Path]:
        """
        Return raw TIFF frames sorted chronologically.

        Expected examples:

            t000.tif
            t001.tif
            t002.tif
        """

        raw_dir = self.get_raw_dir(sequence)

        frames = sorted(
            raw_dir.glob("t*.tif"),
            key=lambda p: p.name
        )

        if not frames:
            raise FileNotFoundError(
                f"No raw TIFF frames found in {raw_dir}"
            )

        return frames

    def get_raw_frame_path(
        self,
        sequence: str,
        frame: int,
    ) -> Path:
        """Return the path to a specific raw frame."""

        frames = self.list_raw_frames(sequence)

        if frame < 0 or frame >= len(frames):
            raise IndexError(
                f"Frame {frame} is outside valid range "
                f"[0, {len(frames) - 1}]"
            )

        return frames[frame]

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_frame(
        self,
        sequence: str,
        frame: int,
    ) -> np.ndarray:
        """
        Load one raw microscopy frame.

        Expected output:
            3D NumPy array with shape (Z, Y, X)
        """

        path = self.get_raw_frame_path(sequence, frame)

        image = tifffile.imread(path)

        if image.ndim != 3:
            raise ValueError(
                f"Expected a 3D microscopy volume at {path}, "
                f"but received shape {image.shape}"
            )

        return image

    # ------------------------------------------------------------------
    # Annotation discovery
    # ------------------------------------------------------------------

    def _annotation_root(
        self,
        sequence: str,
        annotation_type: str,
    ) -> Optional[Path]:
        """
        Locate an annotation directory.

        Supported:
            ST
            GT
            TRA

        CTC datasets commonly use:

            01_ST/SEG
            01_GT/SEG
            01_GT/TRA
        """

        annotation_type = annotation_type.upper()

        if annotation_type not in {"ST", "GT"}:
            return None

        root = self.dataset_path / f"{sequence}_{annotation_type}"

        if not root.exists():
            return None

        return root

    def list_segmentation_files(
        self,
        sequence: str,
        annotation_type: str = "ST",
    ) -> list[Path]:
        """
        Find segmentation annotation TIFFs.

        Handles both forms encountered in the experiments:

            man_seg000.tif
            man_seg_000_004.tif
        """

        root = self._annotation_root(
            sequence,
            annotation_type,
        )

        if root is None:
            return []

        seg_dir = root / "SEG"

        if not seg_dir.exists():
            return []

        return sorted(seg_dir.glob("*.tif"))

    def get_tracking_file(
        self,
        sequence: str,
    ) -> Optional[Path]:
        """Locate the CTC tracking annotation file."""

        root = self.dataset_path / f"{sequence}_GT"
        tra_dir = root / "TRA"

        if not tra_dir.exists():
            return None

        candidates = [
            tra_dir / "man_track.txt",
            tra_dir / "res_track.txt",
        ]

        for path in candidates:
            if path.exists():
                return path

        txt_files = sorted(tra_dir.glob("*.txt"))

        return txt_files[0] if txt_files else None

    # ------------------------------------------------------------------
    # Annotation loading
    # ------------------------------------------------------------------

    def load_segmentation(
        self,
        path: str | Path,
    ) -> np.ndarray:
        """Load a segmentation TIFF."""

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Segmentation file does not exist: {path}"
            )

        return tifffile.imread(path)

    def load_tracking_annotations(
        self,
        sequence: str,
    ) -> Optional[np.ndarray]:
        """
        Load the CTC tracking text file.

        The exact semantic interpretation of the columns is intentionally
        left to the tracking/evaluation module.
        """

        path = self.get_tracking_file(sequence)

        if path is None:
            return None

        try:
            return np.loadtxt(path)
        except ValueError:
            # Some text files may contain headers/comments.
            return np.loadtxt(path, comments="#")