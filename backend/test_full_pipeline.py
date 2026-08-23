import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

import glob
import time
import tifffile

from src.segmentation.cellpose import CellposeSegmenter
from src.tracking import CentroidTracker
from src.lineage import LineageReconstructor

def test_pipeline_flow(dataset_dir="src/data/Fluo-N3DH-CHO/01", max_frames=5):
    # Locate frame files
    files = sorted(glob.glob(f"{dataset_dir}/*.tif"))[:max_frames]
    if not files:
        files = sorted(glob.glob(f"{dataset_dir}/*.tiff"))[:max_frames]
        
    if not files:
        print(f"❌ Error: No frame files found under {dataset_dir}")
        return

    print(f"=== Testing Pipeline Flow: Cellpose -> Tracking -> Lineage ({len(files)} Frames) ===")
    
    # 1. Initialize Cellpose Segmenter
    segmenter = CellposeSegmenter(gpu=True, diameter=30.0)
    
    t_start = time.time()
    seg_results = []
    
    # 2. Sequential Segmentation
    for frame_idx, file_path in enumerate(files):
        t_frame = time.time()
        volume = tifffile.imread(file_path)
        seg_res = segmenter.segment(volume, frame_index=frame_idx)
        seg_results.append(seg_res)
        print(f"  • Frame {frame_idx:02d}: {len(seg_res.detections):2d} detections ({time.time() - t_frame:.3f}s)")
    
    # 3. Hungarian Centroid Tracking
    t_track = time.time()
    tracker = CentroidTracker(max_distance=50.0)
    
    # Pass list of detection lists per frame
    all_frame_detections = [res.detections for res in seg_results]
    try:
        tracking_result = tracker.track(all_frame_detections)
    except TypeError:
        # Fallback if tracker expects (detections, frame_index) per frame
        for f_idx, dets in enumerate(all_frame_detections):
            tracker.track(dets)
        tracking_result = tracker.get_result() if hasattr(tracker, "get_result") else tracker

    tracks = getattr(tracking_result, "tracks", tracking_result)
    print(f"\n[Tracking] Generated {len(tracks)} tracks in {time.time() - t_track:.3f}s")
    
    # 4. Lineage Reconstruction / Mitosis
    t_lineage = time.time()
    reconstructor = LineageReconstructor()
    lineage_result = reconstructor.reconstruct(tracking_result)
    
    divisions = getattr(lineage_result, "divisions", [])
    graph = getattr(lineage_result, "graph", None)
    
    print(f"[Lineage] Division events detected: {len(divisions)}")
    if graph:
        root_ids = graph.root_ids() if callable(getattr(graph, "root_ids", None)) else getattr(graph, "root_ids", [])
        nodes = graph.nodes() if callable(getattr(graph, "nodes", None)) else getattr(graph, "nodes", [])
        print(f"[Lineage] Root lineages: {len(root_ids)} | Total nodes: {len(nodes)}")
        
    print(f"\n✅ Pipeline Flow: Cellpose → Tracking → Mitosis → Lineage completed in {time.time() - t_start:.2f}s total.")

if __name__ == "__main__":
    test_pipeline_flow()