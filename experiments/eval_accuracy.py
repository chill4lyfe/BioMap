import cv2
import numpy as np
import matplotlib.pyplot as plt
import tifffile
import os
import glob

# --- 1. LOAD RAW & GROUND TRUTH ---
base_dir = os.path.join("datasets", "Fluo-N3DH-CHO")
raw_path = os.path.join(base_dir, "01", "t000.tif")

# Find the exact ground truth mask we mapped earlier
# Point to the dense Silver Truth (ST) mask
seg_dir = os.path.join(base_dir, "01_ST", "SEG")
st_mask_path = os.path.join(seg_dir, "man_seg000.tif")

# Load and flatten (MIP) both the Raw and the ST Mask
raw_img3d = tifffile.imread(raw_path)
raw_img = np.max(raw_img3d, axis=0) if len(raw_img3d.shape) == 3 else raw_img3d

gt_mask3d = tifffile.imread(st_mask_path)
gt_mask = np.max(gt_mask3d, axis=0) if len(gt_mask3d.shape) == 3 else gt_mask3d

# --- 2. SHAPE-AGNOSTIC DETECTION (CONTOURS) ---
norm = cv2.normalize(raw_img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
denoised = cv2.GaussianBlur(norm, (7, 7), 0)

kernel_tophat = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel_tophat)
_, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

kernel = np.ones((3,3), np.uint8)
opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

# Find Contours (Wraps the whole shape, regardless of if it's round or elongated)
contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

predicted_centroids = []
predicted_mask = np.zeros_like(gt_mask) # Blank canvas to draw our predictions

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 100:  # Area filter to kill dust
        # Calculate the mathematical center of the irregular shape
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            predicted_centroids.append((cx, cy))
            # Draw it on our blank canvas for visualization
            cv2.drawContours(predicted_mask, [cnt], -1, 255, -1)

# --- 3. ACCURACY CALCULATION ---
# How many ground truth cells actually exist?
gt_labels = np.unique(gt_mask)
gt_labels = gt_labels[gt_labels > 0] # Ignore 0 (background)
total_gt_cells = len(gt_labels)

true_positives = 0
false_positives = 0
hit_gt_labels = set()

# Check every predicted center dot: did it land inside a real cell?
for (cx, cy) in predicted_centroids:
    try:
        hit_label = gt_mask[cy, cx]
        if hit_label > 0:
            true_positives += 1
            hit_gt_labels.add(hit_label)
        else:
            false_positives += 1 # Hit the background (dust)
    except IndexError:
        pass # Center was somehow off-screen

false_negatives = total_gt_cells - len(hit_gt_labels) # Cells we completely missed

# Metrics
precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
recall = len(hit_gt_labels) / total_gt_cells if total_gt_cells > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

print(f"--- ACCURACY REPORT ---")
print(f"Ground Truth Cells: {total_gt_cells}")
print(f"Predicted Cells: {len(predicted_centroids)}")
print(f"True Positives (Correct): {true_positives}")
print(f"False Positives (Dust/Noise): {false_positives}")
print(f"False Negatives (Missed Cells): {false_negatives}")
print(f"Precision: {precision*100:.1f}%")
print(f"Recall: {recall*100:.1f}%")
print(f"F1-Score: {f1_score*100:.1f}%")

# --- 4. VISUALIZATION ---
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

axes[0].imshow(norm, cmap='gray')
axes[0].set_title("1. Raw Image")
axes[0].axis('off')

# Show GT
gt_display = np.ma.masked_where(gt_mask == 0, gt_mask)
axes[1].imshow(norm, cmap='gray')
axes[1].imshow(gt_display, cmap='nipy_spectral', alpha=0.5)
axes[1].set_title(f"2. Ground Truth ({total_gt_cells} cells)")
axes[1].axis('off')

# Show our Prediction
pred_display = np.ma.masked_where(predicted_mask == 0, predicted_mask)
axes[2].imshow(norm, cmap='gray')
axes[2].imshow(pred_display, cmap='cool', alpha=0.5)
for (cx, cy) in predicted_centroids:
    axes[2].plot(cx, cy, 'r+', markersize=10) # Red crosshairs on centers
axes[2].set_title(f"3. Our Prediction (F1: {f1_score*100:.1f}%)")
axes[2].axis('off')

plt.tight_layout()
plt.show()