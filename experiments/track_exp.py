import cv2
import numpy as np
import matplotlib.pyplot as plt
import tifffile
import os
import glob
from scipy.optimize import linear_sum_assignment

# --- 1. CONFIGURATION ---
DATASET_NAME = "Fluo-N3DH-CHO"
AREA_LIMIT = 150
DISTANCE_THRESHOLD = 35.0  # Max pixel jump allowed between consecutive frames

base_dir = os.path.join("datasets", DATASET_NAME, "01")
st_dir = os.path.join("datasets", DATASET_NAME, "01_ST", "SEG")

frame_files = sorted(glob.glob(os.path.join(base_dir, "*.tif")))
if not frame_files:
    raise FileNotFoundError(f"No .tif files found in {base_dir}")

print(f"Loaded {len(frame_files)} raw frames from {DATASET_NAME}.")

# --- 2. SHAPE-AGNOSTIC SEGMENTATION & DETECTION ---
def segment_and_extract(image_path):
    """Loads 3D TIFF, applies MIP projection, morphological filtering, and extracts centroids via contour moments."""
    img3d = tifffile.imread(image_path)
    img2d = np.max(img3d, axis=0) if len(img3d.shape) == 3 else img3d
    
    norm = cv2.normalize(img2d, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    denoised = cv2.GaussianBlur(norm, (7, 7), 0)
    
    kernel_tophat = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
    tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel_tophat)
    _, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Contour moments treat round, stretched, and irregular shapes as unified single bodies
    contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_centroids = []
    for cnt in contours:
        if cv2.contourArea(cnt) > AREA_LIMIT:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                valid_centroids.append((cx, cy))
                
    return norm, np.array(valid_centroids)

# --- 3. MULTI-FRAME TRACKING & SILVER TRUTH EVALUATION LOOP ---
tracks = {}
next_track_id = 1
active_cells = {}

first_img = None
last_img = None
start_centroids = []

# Evaluation tracking across all frames
total_gt_cells_all = 0
total_tp_all = 0
total_fp_all = 0
evaluated_frames_count = 0

print("Starting end-to-end multi-frame tracking and accuracy verification...")

for frame_idx, frame_path in enumerate(frame_files):
    norm_img, current_centroids = segment_and_extract(frame_path)
    
    # Extract frame number (e.g. "t000.tif" -> "000")
    filename = os.path.basename(frame_path)
    frame_str = os.path.splitext(filename)[0].replace("t", "")
    
    # Check for corresponding Silver Truth mask
    st_path_candidates = [
        os.path.join(st_dir, f"man_seg{frame_str}.tif"),
        os.path.join(st_dir, f"man_seg_{frame_str}.tif")
    ]
    st_path = next((p for p in st_path_candidates if os.path.exists(p)), None)
    
    # Frame-level accuracy check against ST
    if st_path:
        st_vol = tifffile.imread(st_path)
        st2d = np.max(st_vol, axis=0) if len(st_vol.shape) == 3 else st_vol
        st_labels = np.unique(st2d)
        st_labels = st_labels[st_labels > 0]
        
        frame_gt_cells = len(st_labels)
        hit_labels = set()
        for (cx, cy) in current_centroids:
            try:
                hit_label = st2d[cy, cx]
                if hit_label > 0:
                    hit_labels.add(hit_label)
            except IndexError:
                pass
                
        # True Positives: The number of unique GT cells we successfully hit
        frame_tp = len(hit_labels)
        
        # False Positives: Total predicted dots MINUS the ones that were useful
        # (This correctly penalizes multiple dots inside the same cell!)
        frame_fp = len(current_centroids) - frame_tp
                
        total_gt_cells_all += frame_gt_cells
        total_tp_all += frame_tp
        total_fp_all += frame_fp
        evaluated_frames_count += 1

    # Initialize at frame 0
    if frame_idx == 0:
        first_img = norm_img
        start_centroids = current_centroids
        for centroid in current_centroids:
            tracks[next_track_id] = [centroid]
            active_cells[next_track_id] = centroid
            next_track_id += 1
        continue
        
    last_img = norm_img
    
    if not active_cells or len(current_centroids) == 0:
        continue
        
    track_ids = list(active_cells.keys())
    prev_centroids = list(active_cells.values())
    
    # Hungarian spatial cost matrix
    cost_matrix = np.zeros((len(prev_centroids), len(current_centroids)))
    for i, p_c in enumerate(prev_centroids):
        for j, c_c in enumerate(current_centroids):
            cost_matrix[i, j] = np.linalg.norm(p_c - c_c)
            
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    new_active_cells = {}
    matched_current_indices = set()
    
    # Associate matched tracks
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] < DISTANCE_THRESHOLD:
            t_id = track_ids[i]
            tracks[t_id].append(current_centroids[j])
            new_active_cells[t_id] = current_centroids[j]
            matched_current_indices.add(j)
            
    # Initialize newly appearing tracks
    for j, centroid in enumerate(current_centroids):
        if j not in matched_current_indices:
            tracks[next_track_id] = [centroid]
            new_active_cells[next_track_id] = centroid
            next_track_id += 1
            
    active_cells = new_active_cells

# --- 4. CUMULATIVE ACCURACY METRICS ---
print(f"\n================ TRACKING & ACCURACY REPORT ================")
print(f"Total Frames Processed:                {len(frame_files)}")
print(f"Total ST Frames Evaluated:             {evaluated_frames_count}")
print(f"Total Unique Cell Tracks Identified:   {len(tracks)}")

if evaluated_frames_count > 0:
    global_precision = total_tp_all / (total_tp_all + total_fp_all) if (total_tp_all + total_fp_all) > 0 else 0
    global_recall = total_tp_all / total_gt_cells_all if total_gt_cells_all > 0 else 0
    global_f1 = 2 * (global_precision * global_recall) / (global_precision + global_recall) if (global_precision + global_recall) > 0 else 0
    
    print(f"Cumulative True Positives:             {total_tp_all}")
    print(f"Cumulative False Positives:            {total_fp_all}")
    print(f"Overall Silver Truth Precision:        {global_precision * 100:.1f}%")
    print(f"Overall Silver Truth Recall:           {global_recall * 100:.1f}%")
    print(f"Overall Silver Truth F1-Score:         {global_f1 * 100:.1f}%")
print(f"============================================================")

# --- 5. VISUALIZATION DASHBOARD ---
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Panel 1: Start Frame
axes[0].imshow(first_img, cmap='gray')
axes[0].set_title(f"Initial State: Frame 0 ({len(start_centroids)} cells detected)")
axes[0].axis('off')
for pt in start_centroids:
    axes[0].plot(pt[0], pt[1], 'ro', markersize=6)

# Panel 2: End Frame with Complete Trajectories
axes[1].imshow(last_img, cmap='gray')
axes[1].set_title(f"Final State: Frame {len(frame_files) - 1} with Full Trajectories")
axes[1].axis('off')

# Color map for distinct trajectories
cmap = plt.get_cmap('gist_rainbow', len(tracks))

for idx, (t_id, path) in enumerate(tracks.items()):
    if len(path) > 2:  # Only plot persistent cell tracks
        path = np.array(path)
        color = cmap(idx)
        axes[1].plot(path[:, 0], path[:, 1], color=color, linewidth=2, alpha=0.8)
        axes[1].plot(path[-1, 0], path[-1, 1], 'o', color=color, markersize=5)

plt.tight_layout()
plt.show()