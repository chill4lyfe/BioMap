import cv2
import numpy as np
import matplotlib.pyplot as plt
import tifffile
import os
import glob
from scipy.optimize import linear_sum_assignment

# --- 1. CONFIGURATION ---
START_FRAME = 0   # e.g., 0 means t000.tif
END_FRAME = 50     # e.g., 3 means t003.tif (Tracks across 4 frames total)
AREA_LIMIT = 200  # Let's keep a reasonable baseline to block dust

# --- 2. REUSABLE SEGMENTATION (WITH MIP Z-AXIS FIX) ---
def segment_and_extract(image_path):
    img3d = tifffile.imread(image_path)
    
    # MIP: Flatten the 3D volume into 2D to stop cells from disappearing
    img = np.max(img3d, axis=0) if len(img3d.shape) == 3 else img3d
    
    norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    denoised = cv2.GaussianBlur(norm, (7, 7), 0)
    
    kernel_tophat = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
    tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel_tophat)
    _, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    kernel = np.ones((3,3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist_transform, 0.2 * dist_transform.max(), 255, 0)
    
    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(np.uint8(sure_fg))
    
    valid_centroids = []
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > AREA_LIMIT:
            valid_centroids.append(centroids[i])
            
    return norm, np.array(valid_centroids)

# --- 3. DATA INGESTION ---
base_dir = os.path.join("datasets", "Fluo-N3DH-CHO", "01")
all_files = sorted(glob.glob(os.path.join(base_dir, "*.tif")))

# Slice the specific window of frames we want to test
window_files = all_files[START_FRAME : END_FRAME + 1]
print(f"Tracking from {os.path.basename(window_files[0])} to {os.path.basename(window_files[-1])}...")

# --- 4. SEQUENTIAL TRACKING ---
tracks = {}
next_track_id = 1
active_cells = {}

first_img = None
last_img = None
start_centroids = [] # To store positions at START_FRAME

for idx, frame_path in enumerate(window_files):
    img, centroids = segment_and_extract(frame_path)
    
    if idx == 0:
        first_img = img
        start_centroids = centroids
        for c in centroids:
            tracks[next_track_id] = [c]
            active_cells[next_track_id] = c
            next_track_id += 1
        continue
        
    last_img = img
    if not active_cells or len(centroids) == 0:
        continue
        
    track_ids = list(active_cells.keys())
    prev_centroids = list(active_cells.values())
    
    # Hungarian Algorithm for this step
    cost_matrix = np.zeros((len(prev_centroids), len(centroids)))
    for i, p_c in enumerate(prev_centroids):
        for j, c_c in enumerate(centroids):
            cost_matrix[i, j] = np.linalg.norm(p_c - c_c)
            
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    new_active_cells = {}
    matched_current_indices = set()
    
    for i, j in zip(row_ind, col_ind):
        if cost_matrix[i, j] < 30.0: # Max pixels a cell can move per frame
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

# --- 5. VISUALIZATION ---
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Panel 1: Start Frame
axes[0].imshow(first_img, cmap='gray')
axes[0].set_title(f"Start: Frame {START_FRAME} ({os.path.basename(window_files[0])})")
axes[0].axis('off')
for pt in start_centroids:
    axes[0].plot(pt[0], pt[1], 'ro', markersize=6) # Red dots

# Panel 2: End Frame + Paths
axes[1].imshow(last_img, cmap='gray')
axes[1].set_title(f"End: Frame {END_FRAME} ({os.path.basename(window_files[-1])}) with Trajectories")
axes[1].axis('off')

# Plot only tracks that existed at the start AND made it to the end (or partway)
for t_id, path in tracks.items():
    if len(path) > 1: # Cell moved at least once
        path = np.array(path)
        axes[1].plot(path[:, 0], path[:, 1], 'y-', linewidth=2) # Yellow track line
        axes[1].plot(path[-1, 0], path[-1, 1], 'go', markersize=6) # Green dot at final location

plt.tight_layout()
plt.show()