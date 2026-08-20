import os
import networkx as nx
import matplotlib.pyplot as plt

# --- 1. LOAD DATA ---
DATASET_NAME = "Fluo-N3DH-CHO"
track_file = os.path.join("datasets", DATASET_NAME, "01_GT", "TRA", "man_track.txt")

lineage_data = []
with open(track_file, "r") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) == 4:
            lineage_data.append(tuple(map(int, parts)))

# --- 2. BUILD GRAPH ---
G = nx.DiGraph()
for cell_id, start, end, parent_id in lineage_data:
    G.add_node(cell_id)
    if parent_id != 0:
        G.add_edge(parent_id, cell_id)

# --- 3. BEAUTIFUL FOREST VISUALIZATION ---
plt.figure(figsize=(16, 10))
plt.title("Complete Lineage Forest (All Cell Families)", fontsize=18)

try:
    # graphviz 'dot' layout is perfect for hierarchical trees
    from networkx.drawing.nx_agraph import graphviz_layout
    pos = graphviz_layout(G, prog='dot')
except ImportError:
    pos = nx.spring_layout(G, seed=42)

# Find root nodes (cells with no parents) to color them differently
roots = [n for n, d in G.in_degree() if d == 0]
children = [n for n, d in G.in_degree() if d > 0]

nx.draw_networkx_nodes(G, pos, nodelist=roots, node_color="lightgreen", 
                       node_size=600, edgecolors="black", label="Founder Cells")
nx.draw_networkx_nodes(G, pos, nodelist=children, node_color="skyblue", 
                       node_size=600, edgecolors="black", label="Daughter Cells")
nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, edge_color="gray", width=2)
nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold")

plt.legend(loc="upper left")
plt.axis('off')
plt.tight_layout()
plt.show()