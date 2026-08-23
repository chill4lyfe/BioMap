import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

import os
import glob
import time
import numpy as np
import tifffile
import matplotlib.pyplot as plt

from src.segmentation.cellpose import CellposeSegmenter
try:
    from src.segmentation.classical import ClassicalSegmenter
except ImportError:
    ClassicalSegmenter = None

def get_mask(result):
    """Safely extracts a 2D label mask regardless of attribute name differences."""
    for attr in ["label_mask", "mask", "labels", "labeled_image", "segmented_image"]:
        if hasattr(result, attr) and getattr(result, attr) is not None:
            return getattr(result, attr)
    # Reconstruct from detections if no direct 2D mask array exists
    h, w = result.image.shape
    reconstructed = np.zeros((h, w), dtype=np.int32)
    for det in result.detections:
        if hasattr(det, "mask") and det.mask is not None:
            reconstructed[det.mask] = det.detection_id
    return reconstructed

def find_ctc_volumes(dataset_folder):
    folder_path = Path(dataset_folder)
    if not folder_path.exists():
        alt_path = current_dir / dataset_folder
        if alt_path.exists():
            folder_path = alt_path

    patterns = ["01/*.tif", "01/*.tiff", "02/*.tif", "02/*.tiff", "**/*.tif", "**/*.tiff"]
    for pat in patterns:
        matched = sorted(glob.glob(str(folder_path / pat), recursive=True))
        if matched:
            return matched[0], tifffile.imread(matched[0])
    return None, None

def run_dataset_check(dataset_name, rel_path, diameter=30.0):
    print(f"\n=======================================================")
    print(f"Dataset: {dataset_name}")
    print(f"Target Path: {rel_path}")
    
    file_path, volume = find_ctc_volumes(rel_path)
    if volume is None:
        print(f"❌ Error: No .tif or .tiff files found in {rel_path}.")
        return
    
    print(f"✅ Found File: {file_path}")
    print(f"Volume Shape: {volume.shape} | Dtype: {volume.dtype}")
    
    # 1. Advanced (Cellpose GPU)
    cellpose_seg = CellposeSegmenter(gpu=True, diameter=diameter)
    t0 = time.time()
    res_adv = cellpose_seg.segment(volume, frame_index=0)
    adv_time = time.time() - t0
    
    print(f"\n[Advanced Mode - Cellpose GPU]")
    print(f"  • Inference Time: {adv_time:.4f}s (GPU Active: {cellpose_seg.gpu})")
    print(f"  • Detections Found: {len(res_adv.detections)}")
    
    # 2. Basic Mode
    res_basic = None
    if ClassicalSegmenter is not None:
        try:
            classical_seg = ClassicalSegmenter()
            t0 = time.time()
            res_basic = classical_seg.segment(volume, frame_index=0)
            basic_time = time.time() - t0
            print(f"\n[Basic Mode - OpenCV/Morphology]")
            print(f"  • Processing Time: {basic_time:.4f}s")
            print(f"  • Detections Found: {len(res_basic.detections)}")
        except Exception as e:
            print(f"\n[Basic Mode] Error: {e}")

    # Generate Visual Side-by-Side Comparison Plot
    out_img = f"verification_{dataset_name}.png"
    cols = 3 if res_basic is not None else 2
    fig, axes = plt.subplots(1, cols, figsize=(6 * cols, 5))
    
    axes[0].imshow(res_adv.image, cmap="gray")
    axes[0].set_title(f"2D MIP: {dataset_name}")
    
    if res_basic is not None:
        mask_basic = get_mask(res_basic)
        axes[1].imshow(mask_basic, cmap="nipy_spectral")
        axes[1].set_title(f"Basic Mode ({len(res_basic.detections)} cells)")
        ax_adv = axes[2]
    else:
        ax_adv = axes[1]
        
    mask_adv = get_mask(res_adv)
    ax_adv.imshow(mask_adv, cmap="nipy_spectral")
    for det in res_adv.detections:
        ax_adv.plot(det.centroid[0], det.centroid[1], 'r+', markersize=8)
    ax_adv.set_title(f"Advanced Cellpose ({len(res_adv.detections)} cells)")
    
    plt.tight_layout()
    plt.savefig(out_img, dpi=200)
    plt.close()
    print(f" Saved visual verification figure to: {out_img}")

if __name__ == "__main__":
    cho_dir = "src/data/Fluo-N3DH-CHO"
    mda_dir = "src/data/Fluo-C3DL-MDA231"
    
    run_dataset_check("Fluo-N3DH-CHO", cho_dir, diameter=30.0)
    run_dataset_check("Fluo-C3DL-MDA231", mda_dir, diameter=25.0)