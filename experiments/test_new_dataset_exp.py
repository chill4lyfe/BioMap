import cv2
import numpy as np
import matplotlib.pyplot as plt
import tifffile
import os
import glob
from scipy.optimize import linear_sum_assignment

# --- 1. CONFIGURATION ---
DATASET_NAME = "Fluo-C3DL-MDA231"
START_FRAME = 0
END_FRAME = 3
AREA_LIMIT = 150 # Keeping this to filter dust

base_dir = os.path.join("datasets", DATASET_NAME, "01")
gt_dir = os.path.join("datasets", DATASET_NAME, "01_ST", "SEG")

raw_files = sorted(glob.glob(os.path.join(base_dir, "*.tif")))
gt_files = sorted(glob.glob(os.path.join(gt_dir, "*.tif")))

if not raw_files:
    raise FileNotFoundError(f"Could not find .tif files in {base_dir}. Check your extracted folder!")

# --- 2. PIPELINE FUNCTIONS ---
def get_mip_and_detect(image_path):
    """Flattens 3D raw image and finds shape-agnostic centroids."""
    img3d = tifffile.imread(image_path)
    # Maximum Intensity Projection (MIP)
    img2d = np.max(img3d, axis=0) if len(img3d.shape) == 3 else img3d
    
    norm = cv2.normalize(img2d, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    denoised = cv2.GaussianBlur(norm, (7, 7), 0)
    
    # Using a slightly larger Top-Hat kernel (80x80) because MDA231 cells can be large/stretched
    kernel_tophat = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (80, 80))
    tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel_tophat)
    _, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    kernel = np.ones((3,3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    
    contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    centroids = []
    predicted_mask = np.zeros_like(norm)
    
    for cnt in contours:
        if cv2.contourArea(cnt) > AREA_LIMIT:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centroids.append((cx, cy))
                cv2.drawContours(predicted_mask, [cnt], -1, 255, -1)
                
    return norm, np.array(centroids), predicted_mask

def flatten_gt_mask(gt_path):
    """Flattens the 3D Ground Truth into a single 2D map of valid cell zones."""
    gt3d = tifffile.imread(gt_path)
    gt2d = np.max(gt3d, axis=0) if len(gt3d.shape) == 3 else gt3d
    return gt2d

# --- 3. EVALUATE ACCURACY ON FRAME 0 ---
# --- 3. EVALUATE ACCURACY ON FRAME 0 ---
print(f"Evaluating accuracy on {DATASET_NAME} - Frame 0...")
norm0, centroids0, pred_mask0 = get_mip_and_detect(raw_files[0])

# Extract frame number: e.g. "t000.tif" -> "000"
filename = os.path.basename(raw_files[0])
name_only = os.path.splitext(filename)[0]
frame_str = name_only.replace("t", "")

# Case A: Single 3D volume file (e.g. man_seg000.tif or man_seg_000.tif)
single_gt_candidates = [
    os.path.join(gt_dir, f"man_seg{frame_str}.tif"),
    os.path.join(gt_dir, f"man_seg_{frame_str}.tif")
]
single_gt_path = next((p for p in single_gt_candidates if os.path.exists(p)), None)

# Case B: Multi-slice 2D files (e.g. man_seg_000_*.tif)
multi_gt_files = sorted(glob.glob(os.path.join(gt_dir, f"man_seg_{frame_str}_*.tif")))

gt2d = None

if single_gt_path:
    print(f"Found single volume ST file: {os.path.basename(single_gt_path)}")
    gt_vol = tifffile.imread(single_gt_path)
    gt2d = np.max(gt_vol, axis=0) if len(gt_vol.shape) == 3 else gt_vol

elif multi_gt_files:
    print(f"Found {len(multi_gt_files)} slice ST files for frame {frame_str}. Combining...")
    for gt_file in multi_gt_files:
        slice_img = tifffile.imread(gt_file)
        if gt2d is None:
            gt2d = np.zeros_like(slice_img)
        gt2d = np.maximum(gt2d, slice_img)

if gt2d is not None:
    gt_labels = np.unique(gt2d)
    gt_labels = gt_labels[gt_labels > 0]
    total_gt_cells = len(gt_labels)
    
    true_positives = 0
    false_positives = 0
    hit_gt_labels = set()
    
    for (cx, cy) in centroids0:
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
    
    print(f"\n--- FRAME 0 ACCURACY ({DATASET_NAME}) ---")
    print(f"Ground Truth Cells: {total_gt_cells}")
    print(f"Predicted Cells:    {len(centroids0)}")
    print(f"True Positives:     {true_positives}")
    print(f"False Positives:    {false_positives}")
    print(f"False Negatives:    {false_negatives}")
    print(f"Precision:          {precision*100:.1f}%")
    print(f"Recall:             {recall*100:.1f}%")
    print(f"F1-Score:           {f1_score*100:.1f}%")
else:
    print(f"No matching ST mask found for frame {frame_str}. Skipping accuracy calc.")
    f1_score = 0
    gt2d = np.zeros_like(norm0)

# --- 4. RUN TRACKING FROM START_FRAME TO END_FRAME ---
print("Running temporal tracking...")
window_files = raw_files[START_FRAME : END_FRAME + 1]
tracks = {}
next_track_id = 1
active_cells = {}
last_img = None

for idx, frame_path in enumerate(window_files):
    img, centroids, _ = get_mip_and_detect(frame_path)
    last_img = img
    
    if idx == 0:
        for c in centroids:
            tracks[next_track_id] = [c]
            active_cells[next_track_id] = c
            next_track_id += 1
        continue
        
    if not active_cells or len(centroids) == 0:
        continue
        
    track_ids = list(active_cells.keys())
    prev_centroids = list(active_cells.values())
    
    cost_matrix = np.zeros((len(prev_centroids), len(centroids)))
    for i, p_c in enumerate(prev_centroids):
        for j, c_c in enumerate(centroids):
            cost_matrix[i, j] = np.linalg.norm(p_c - c_c)
            
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    new_active_cells = {}
    matched_current_indices = set()
    
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] < 40.0: # Increased tracking distance for faster MDA231 cells
            t_id = track_ids[i]
            tracks[t_id].append(centroids[j])
            new_active_cells[t_id] = centroids[j]
            matched_current_indices.add(j)
            
    for j, c in enumerate(centroids):
        if j not in matched_current_indices:
            tracks[next_track_id] = [c]
            new_active_cells[next_track_id] = c
            next_track_id += 1
            
    active_cells = new_active_cells

# --- 5. VISUALIZATION DASHBOARD ---
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Panel 1: The Raw MIP Image
axes[0].imshow(norm0, cmap='gray')
axes[0].set_title(f"1. {DATASET_NAME} Raw MIP")
axes[0].axis('off')

# Panel 2: Accuracy Overlay
gt_display = np.ma.masked_where(gt2d == 0, gt2d)
axes[1].imshow(norm0, cmap='gray')
axes[1].imshow(gt_display, cmap='ocean', alpha=0.4)
for (cx, cy) in centroids0:
    axes[1].plot(cx, cy, 'r+', markersize=8)
axes[1].set_title(f"2. Detection vs GT (F1: {f1_score*100:.1f}%)")
axes[1].axis('off')

# Panel 3: Tracking Trajectories
axes[2].imshow(last_img, cmap='gray')
axes[2].set_title(f"3. Tracks (Frames {START_FRAME}-{END_FRAME})")
axes[2].axis('off')
for t_id, path in tracks.items():
    if len(path) > 1: 
        path = np.array(path)
        axes[2].plot(path[:, 0], path[:, 1], 'y-', linewidth=2)
        axes[2].plot(path[-1, 0], path[-1, 1], 'go', markersize=5)

plt.tight_layout()
plt.show()