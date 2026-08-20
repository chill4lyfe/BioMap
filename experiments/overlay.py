import tifffile
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

base_dir = os.path.join("datasets", "Fluo-N3DH-CHO")
seg_dir = os.path.join(base_dir, "01_GT", "SEG")
raw_path = os.path.join(base_dir, "01", "t000.tif")
mask_files = glob.glob(os.path.join(seg_dir, "*.tif"))

if not mask_files:
    print("Error: Could not find any .tif files in the SEG folder.")
else:
    mask_path = sorted(mask_files)[0] # Grabs man_seg_004_000.tif
    print(f"Found mask: {os.path.basename(mask_path)}")
    raw_img = tifffile.imread(raw_path)
    mask_img = tifffile.imread(mask_path)

    print(f"Raw image shape: {raw_img.shape}")
    print(f"Mask image shape: {mask_img.shape}")
    if len(raw_img.shape) == 3 and len(mask_img.shape) == 2:
        # Extract the Z-slice number from the filename (e.g., man_seg_004_000 -> 4)
        filename = os.path.basename(mask_path)
        parts = filename.replace(".tif", "").split("_")
        
        try:
            z_slice = int(parts[2]) # The '004' part
            print(f"Extracting Z-slice {z_slice} from raw image to match the mask.")
        except:
            z_slice = 0 # Fallback just in case
            
        raw_display = raw_img[z_slice]
        mask_display = mask_img
    else:
        # Fallback if both happen to be 2D or 3D
        raw_display = raw_img[0] if len(raw_img.shape) == 3 else raw_img
        mask_display = mask_img[0] if len(mask_img.shape) == 3 else mask_img

    # 4. Visualization!
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Plot A: Raw Image
    axes[0].imshow(raw_display, cmap='gray')
    axes[0].set_title(f"Raw Cells (Z-Slice {z_slice})")
    axes[0].axis('off')

    # Plot B: The Mask
    masked_data = np.ma.masked_where(mask_display == 0, mask_display)
    axes[1].imshow(mask_display, cmap='gray') # dark background
    axes[1].imshow(masked_data, cmap='nipy_spectral', interpolation='none')
    axes[1].set_title(f"Ground Truth Mask: {os.path.basename(mask_path)}")
    axes[1].axis('off')

    # Plot C: The Overlay
    axes[2].imshow(raw_display, cmap='gray')
    axes[2].imshow(masked_data, cmap='nipy_spectral', alpha=0.4, interpolation='none')
    axes[2].set_title("Overlay (Perfect for SIH Presentation)")
    axes[2].axis('off')

    plt.tight_layout()
    plt.show()