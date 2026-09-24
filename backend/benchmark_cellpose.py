import os
import glob
import time
import numpy as np
import tifffile
from src.segmentation.cellpose import CellposeSegmenter

def test_dataset(name, sample_volume, expected_dtype):
    print(f"\n--- Testing Dataset: {name} ---")
    print(f"Input Shape: {sample_volume.shape}, Dtype: {sample_volume.dtype} (Expected: {expected_dtype})")
    
    segmenter = CellposeSegmenter(gpu=True)
    print(f"Cellpose GPU Active: {segmenter.gpu}")
    
    # Warmup / Initial pass
    start_time = time.time()
    result = segmenter.segment(sample_volume, frame_index=0)
    elapsed = time.time() - start_time
    
    print(f"Processed in: {elapsed:.3f}s")
    print(f"MIP Image Shape: {result.image.shape}")
    print(f"Detections Found: {len(result.detections)}")
    
    if len(result.detections) > 0:
        first_det = result.detections[0]
        print(f"Sample Detection: ID={first_det.detection_id}, Centroid={first_det.centroid}, Area={first_det.area}")
    else:
        print("Warning: 0 detections found.")

if __name__ == "__main__":
    # 1. Fluo-N3DH-CHO: 5 slices, 443x512, uint8
    cho_dummy = np.random.randint(0, 255, size=(5, 443, 512), dtype=np.uint8)
    test_dataset("Fluo-N3DH-CHO (Simulation)", cho_dummy, "uint8")

    # 2. Fluo-C3DL-MDA231: 30 slices, 512x512, uint16
    mda_dummy = np.random.randint(0, 65535, size=(30, 512, 512), dtype=np.uint16)
    test_dataset("Fluo-C3DL-MDA231 (Simulation)", mda_dummy, "uint16")
    
    print("\nBenchmark script completed successfully.")