## THIS WE RAN IN CELL 1:

```python
!wget -q http://data.celltrackingchallenge.net/training-datasets/Fluo-N3DH-CHO.zip

# 2. Unzip it quietly (-q) and overwrite (-o)
!unzip -q -o Fluo-N3DH-CHO.zip -d datasets/

# 1. Force-uninstall the stubborn default NumPy
!pip uninstall -y numpy

!pip install "numpy==1.26.4" "numba>=0.60.0" cellpose tifffile opencv-python matplotlib scipy -q

# 2. Force crash the backend to reload the package path
import os
os.kill(os.getpid(), 9)
```

## THIS WE RAN IN CELL 2
```python
import os
import cv2
import numpy as np
import tifffile
import matplotlib.pyplot as plt
from cellpose import models

# --- 1. CONFIGURATION & DATA LOADING ---
DATASET_NAME = "Fluo-N3DH-CHO"
raw_path = f"datasets/{DATASET_NAME}/01/t000.tif"

# CHANGED: Now pointing to the Silver Truth (ST) folder for dense annotations
st_path = f"datasets/{DATASET_NAME}/01_ST/SEG/man_seg000.tif"

print("Loading and preparing images...")
# Load Raw Image & Flatten (MIP)
img3d = tifffile.imread(raw_path)
img2d = np.max(img3d, axis=0) if len(img3d.shape) == 3 else img3d

# Load ST Mask (Full 3D volume for frame 000, flattened to 2D)
gt3d = tifffile.imread(st_path)
gt2d = np.max(gt3d, axis=0) if len(gt3d.shape) == 3 else gt3d

# --- 2. DEEP LEARNING SEGMENTATION (CELLPOSE) ---
print("Initializing Cellpose Model on GPU...")
# The new API uses CellposeModel and pretrained_model
model = models.CellposeModel(gpu=True, pretrained_model='cyto2')

print("Running Prediction on GPU...")
# model.eval() returns a tuple. The first element contains our pixel masks.
eval_results = model.eval(img2d, diameter=None, channels=[0,0])
masks = eval_results[0]

# --- 3. EXTRACT CENTROIDS FROM CELLPOSE MASKS ---
predicted_centroids = []
unique_cells = np.unique(masks)

for cell_id in unique_cells:
    if cell_id == 0:
        continue # Skip background

    y_coords, x_coords = np.where(masks == cell_id)
    cx = int(np.mean(x_coords))
    cy = int(np.mean(y_coords))
    predicted_centroids.append((cx, cy))

# --- 4. ACCURACY EVALUATION (COMPARED TO GT) ---
print("Evaluating Accuracy...")
gt_labels = np.unique(gt2d)
gt_labels = gt_labels[gt_labels > 0]
total_gt_cells = len(gt_labels)

true_positives = 0
false_positives = 0
hit_gt_labels = set()

for (cx, cy) in predicted_centroids:
    try:
        hit_label = gt2d[cy, cx]
        if hit_label > 0:
            true_positives += 1
            hit_gt_labels.add(hit_label)
        else:
            false_positives += 1
    except IndexError:
        pass

false_negatives = total_gt_cells - len(hit_gt_labels)

precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
recall = len(hit_gt_labels) / total_gt_cells if total_gt_cells > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

print(f"\n--- AI PREDICTION RESULTS ---")
print(f"Ground Truth Cells: {total_gt_cells}")
print(f"Predicted Cells: {len(predicted_centroids)}")
print(f"Precision: {precision*100:.1f}%")
print(f"Recall: {recall*100:.1f}%")
print(f"F1-Score: {f1_score*100:.1f}%")

# --- 5. VISUALIZATION DASHBOARD ---
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

axes[0].imshow(img2d, cmap='gray')
axes[0].set_title("1. Raw Image (MIP)")
axes[0].axis('off')

gt_display = np.ma.masked_where(gt2d == 0, gt2d)
axes[1].imshow(img2d, cmap='gray')
axes[1].imshow(gt_display, cmap='ocean', alpha=0.5)
axes[1].set_title(f"2. Ground Truth ({total_gt_cells} cells)")
axes[1].axis('off')

# Display Cellpose Mask
axes[2].imshow(img2d, cmap='gray')
axes[2].imshow(masks, cmap='nipy_spectral', alpha=0.4)
for (cx, cy) in predicted_centroids:
    axes[2].plot(cx, cy, 'r+', markersize=8)
axes[2].set_title(f"3. Cellpose AI Prediction (F1: {f1_score*100:.1f}%)")
axes[2].axis('off')

plt.tight_layout()
plt.show()
```

## THIS IS THE OUTPUT:
```text
WARNING:cellpose.models:pretrained model cyto2 not found, using default model
Loading and preparing images...
Initializing Cellpose Model on GPU...
WARNING:cellpose.models:channels argument is deprecated in v4.0.1+, Cellpose4 takes inputs with arbitrary channel orders. If the image has multiple channels, use channel_axis to specify the axis. Ignoring channels argument...
Running Prediction on GPU...
Evaluating Accuracy...

--- AI PREDICTION RESULTS ---
Ground Truth Cells: 10
Predicted Cells: 11
Precision: 90.9%
Recall: 100.0%
F1-Score: 95.2%
```

(image not attached)