import cv2
import numpy as np
import matplotlib.pyplot as plt
import tifffile
import os

# --- 1. LOAD & BASIC PREP ---
base_dir = os.path.join("datasets", "Fluo-N3DH-CHO")
raw_path = os.path.join(base_dir, "01", "t000.tif")
raw_img = tifffile.imread(raw_path)
raw_slice = raw_img[4] if len(raw_img.shape) == 3 else raw_img

# Normalization & Blur (NO CLAHE THIS TIME!)
normalized = cv2.normalize(raw_slice, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
denoised = cv2.GaussianBlur(normalized, (7, 7), 0)

# --- 2. MODULE 3 & 4: DETECTION & SEGMENTATION ---

# Step A: Top-Hat Background Subtraction
# We use a kernel larger than our biggest cell (e.g., 50x50 pixels)
kernel_tophat = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel_tophat)

# Step B: Otsu Thresholding (now works because background is flattened)
_, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Cleanup
kernel = np.ones((3,3), np.uint8)
opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

# Step C: Detection (Distance Transform)
sure_bg = cv2.dilate(opening, kernel, iterations=3)
dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
# Find the absolute peaks of the cells
_, sure_fg = cv2.threshold(dist_transform, 0.2 * dist_transform.max(), 255, 0)
sure_fg = np.uint8(sure_fg)
unknown = cv2.subtract(sure_bg, sure_fg)

# Step D: Segmentation (Watershed)
_, markers = cv2.connectedComponents(sure_fg)
markers = markers + 1
markers[unknown == 255] = 0

# Watershed needs a 3-channel image
color_img = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
markers = cv2.watershed(color_img, markers)

# --- 3. VISUALIZATION ---
fig, axes = plt.subplots(1, 4, figsize=(20, 5))

axes[0].imshow(denoised, cmap='gray')
axes[0].set_title("1. Denoised Input")
axes[0].axis('off')

axes[1].imshow(tophat, cmap='gray')
axes[1].set_title("2. Top-Hat (Flattened Lighting)")
axes[1].axis('off')

axes[2].imshow(binary, cmap='gray')
axes[2].set_title("3. Otsu on Top-Hat")
axes[2].axis('off')

# Display Watershed 
markers_disp = np.ma.masked_where(markers <= 1, markers)
axes[3].imshow(denoised, cmap='gray')
axes[3].imshow(markers_disp, cmap='nipy_spectral', alpha=0.5, interpolation='none')
axes[3].set_title(f"4. Watershed Seg ({markers.max() - 1} cells)")
axes[3].axis('off')

plt.tight_layout()
plt.show()