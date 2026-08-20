import cv2
import numpy as np
import matplotlib.pyplot as plt
import tifffile
import os
import glob
import networkx as nx
from scipy.optimize import linear_sum_assignment

# --- 1. CONFIGURATION ---
DATASET_NAME = "Fluo-N3DH-CHO"
base_dir = os.path.join("datasets", DATASET_NAME, "01")
gt_track_file = os.path.join("datasets", DATASET_NAME, "01_GT", "TRA", "man_track.txt")

raw_files = sorted(glob.glob(os.path.join(base_dir, "*.tif")))
print(f"Loaded {len(raw_files)} frames from {DATASET_NAME}.")

# --- 2. SEGMENTATION & CENTROID EXTRACTION (MIP) ---
def get_mip_and_centroids(image_path):
    img3d = tifffile.imread(image_path)
    img2d = np.max(img3d, axis=0) if len(img3d.shape) == 3 else img3d
    
    norm = cv2.normalize(img2d, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    denoised = cv2.GaussianBlur(norm, (7, 7), 0)
    
    kernel_tophat = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
    tophat = cv2.morphologyEx(denoised, cv2.MORPH_TOPHAT, kernel_tophat)
    _, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    kernel = np.ones((3,3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    
    contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    centroids = []
    areas = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 150: # Area threshold to suppress background noise
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centroids.append((cx, cy))
                areas.append(area)
                
    return norm, np.array(centroids), np.array(areas)

# --- 3. RUN MULTI-FRAME TRACKING WITH HISTORICAL BUFFER ---
print("Extracting detections and tracking across all frames...")

# We store: { track_id: {'path': [(x,y)], 'frames': [f_idx], 'areas': [area]} }
tracks = {}
next_track_id = 1
active_cells = {} # { track_id: (x, y) }

for f_idx, frame_path in enumerate(raw_files):
    norm_img, centroids, areas = get_mip_and_centroids(frame_path)
    
    if f_idx == 0:
        for c, a in zip(centroids, areas):
            tracks[next_track_id] = {'path': [c], 'frames': [f_idx], 'areas': [a]}
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
        if cost_matrix[i, j] < 35.0: # Distance threshold (pixels)
            t_id = track_ids[i]
            tracks[t_id]['path'].append(centroids[j])
            tracks[t_id]['frames'].append(f_idx)
            tracks[t_id]['areas'].append(areas[j])
            new_active_cells[t_id] = centroids[j]
            matched_current_indices.add(j)
            
    for j, (c, a) in enumerate(zip(centroids, areas)):
        if j not in matched_current_indices:
            tracks[next_track_id] = {'path': [c], 'frames': [f_idx], 'areas': [a]}
            new_active_cells[next_track_id] = c
            next_track_id += 1
            
    active_cells = new_active_cells

# --- 4. PREDICT MITOSIS (RELAXED TEMPORAL WINDOW) ---
predicted_divisions = []
pred_G = nx.DiGraph()

for t_id in tracks.keys():
    pred_G.add_node(t_id)

MAX_PARENT_DAUGHTER_DIST = 50.0  # Increased spatial radius
TEMPORAL_WINDOW = 3              # Allow daughters to appear within 3 frames of parent termination

for parent_id, p_data in tracks.items():
    # Ignore tracks that were too short (noise specks)
    if len(p_data['path']) < 3:
        continue
        
    p_end_frame = p_data['frames'][-1]
    p_end_pos = np.array(p_data['path'][-1])
    p_last_area = p_data['areas'][-1]
    
    # Find candidate daughter cells starting within [p_end_frame, p_end_frame + TEMPORAL_WINDOW]
    candidates = []
    for child_id, c_data in tracks.items():
        if child_id == parent_id or len(c_data['path']) < 2:
            continue
            
        c_start_frame = c_data['frames'][0]
        # Daughter must start right as parent ends or shortly after
        if p_end_frame <= c_start_frame <= p_end_frame + TEMPORAL_WINDOW:
            c_start_pos = np.array(c_data['path'][0])
            dist = np.linalg.norm(p_end_pos - c_start_pos)
            if dist <= MAX_PARENT_DAUGHTER_DIST:
                candidates.append((child_id, dist, c_data['areas'][0]))
                
    # If 2 or more candidate daughters are found in the spatiotemporal neighborhood
    if len(candidates) >= 2:
        candidates.sort(key=lambda x: x[1]) # Closest spatial candidates first
        c1_id, d1, a1 = candidates[0]
        c2_id, d2, a2 = candidates[1]
        
        # Relaxed area check: Daughter combined area check
        area_sum = a1 + a2
        if 0.3 * p_last_area <= area_sum <= 3.0 * p_last_area:
            predicted_divisions.append((parent_id, c1_id, c2_id, p_end_frame))
            pred_G.add_edge(parent_id, c1_id)
            pred_G.add_edge(parent_id, c2_id)

# --- 5. GROUND TRUTH EVALUATION ---
gt_divisions_count = 0
if os.path.exists(gt_track_file):
    gt_lineage = []
    with open(gt_track_file, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                gt_lineage.append(tuple(map(int, parts)))
                
    # Count GT division events (Parent IDs that produce 2+ child records)
    parent_counts = {}
    for cell_id, start, end, parent_id in gt_lineage:
        if parent_id != 0:
            parent_counts[parent_id] = parent_counts.get(parent_id, 0) + 1
            
    gt_divisions_count = sum(1 for p, count in parent_counts.items() if count >= 2)

    # Compute Division Detection Accuracy Metrics
    tp = min(len(predicted_divisions), gt_divisions_count)
    fp = max(0, len(predicted_divisions) - gt_divisions_count)
    fn = max(0, gt_divisions_count - len(predicted_divisions))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\n--- GROUND TRUTH EVALUATION ---")
    print(f"Ground Truth Division Events: {gt_divisions_count}")
    print(f"Predicted Division Events:    {len(predicted_divisions)}")
    print(f"Division Precision:          {precision * 100:.1f}%")
    print(f"Division Recall:             {recall * 100:.1f}%")
    print(f"Division F1-Score:           {f1 * 100:.1f}%")

# --- 6. VISUALIZATION: PREDICTED LINEAGE GRAPH ---
plt.figure(figsize=(14, 8))
plt.title(f"Predicted Cell Lineage Forest ({len(predicted_divisions)} Divisions Detected | GT: {gt_divisions_count})", fontsize=16)

try:
    from networkx.drawing.nx_agraph import graphviz_layout
    pos = graphviz_layout(pred_G, prog='dot')
except ImportError:
    pos = nx.spring_layout(pred_G, seed=42)

# Color coding: Founder cells vs Daughter cells vs Unconnected
roots = [n for n, d in pred_G.in_degree() if d == 0 and pred_G.out_degree(n) > 0]
daughters = [n for n, d in pred_G.in_degree() if d > 0]
singletons = [n for n in pred_G.nodes() if pred_G.in_degree(n) == 0 and pred_G.out_degree(n) == 0]

nx.draw_networkx_nodes(pred_G, pos, nodelist=roots, node_color="lightgreen", node_size=500, edgecolors="black", label="Parent Cells")
nx.draw_networkx_nodes(pred_G, pos, nodelist=daughters, node_color="skyblue", node_size=500, edgecolors="black", label="Daughter Cells")
nx.draw_networkx_nodes(pred_G, pos, nodelist=singletons, node_color="gray", node_size=200, alpha=0.5, label="Non-Dividing Tracks")

nx.draw_networkx_edges(pred_G, pos, arrowstyle="->", arrowsize=15, edge_color="red", width=2)
nx.draw_networkx_labels(pred_G, pos, font_size=8, font_weight="bold")

plt.legend(loc="upper left")
plt.axis('off')
plt.tight_layout()
plt.show()