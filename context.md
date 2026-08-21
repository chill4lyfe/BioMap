## Transfer Prompt — BioMap / SIH GGSIPU2620

I am continuing development of my college's internal SIH Round 1 project:

**GGSIPU2620 — AI-Based 3D Microscopy Cell Detection, Tracking & Lineage Reconstruction System**

The complete project context/architecture/research is in the attached **`3D-Cell.lineage.md`**. Treat that file as the primary project specification and preserve its terminology and intended architecture.

### Project constraints

- This is **only internal college Round 1**.
    
- Approximately **5 implementation days**.
    
- Goal: convincing, visually impressive prototype, not publication-grade scientific software.
    
- Heavy use of pretrained/open-source models and AI assistance.
    
- Development laptop: **i5-8350U, 24 GB RAM, Kubuntu, no dedicated GPU**.
    
- VS Code for local development.
    
- Google Colab/Kaggle GPU available when necessary.
    
- Do not assume heavy 3D deep learning is required.
    
- Current target datasets:
    
    - **Fluo-N3DH-CHO**
        
    - **Fluo-C3DL-MDA231**
        
- Generality matters, but optimization/accuracy is primarily for these two datasets.
    

### Desired progression

```text
Dataset
→ ingestion
→ visualization
→ detection/segmentation
→ tracking
→ division detection
→ lineage reconstruction
→ web dashboard/polish
```

### Current project state

Initial experiments were developed under:

```text
experiments/
```

including visualization, overlay, preprocessing, segmentation, tracking, division, evaluation, Cellpose experimentation, etc.

Those experiments are **reference/experimental code only**. Do not blindly reproduce them. We are migrating useful logic into the actual production pipeline.

Current production areas include:

```text
src/data/
src/segmentation/
src/tracking/
src/lineage/
```

`app/` and other production application directories will now be developed.

### Dataset observations

#### Fluo-N3DH-CHO

- sequences: `01`, `02`
    
- each sequence: 92 frames
    
- each frame: `(5, 443, 512)`
    
- dtype: `uint8`
    
- ST, GT and TRA available
    

#### Fluo-C3DL-MDA231

- sequences: `01`, `02`
    
- each sequence: 12 frames
    
- each frame: `(30, 512, 512)`
    
- dtype: `uint16`
    
- ST, GT and TRA available
    

Common CTC-style structure:

```text
01/
  t000.tif
  t001.tif
  ...

01_ERR_SEG/
  mask000.tif
  ...

01_GT/
  SEG/
  TRA/
    man_track.txt
    ...

01_ST/
  SEG/
    man_seg000.tif
    ...
```

ST is being used as our practical evaluation reference because our initial centroid-hit evaluation against GT gave misleadingly low scores (~30%), whereas ST produced substantially better results (~80–90%+). We understand this is a prototype evaluation approach, not a publication-grade benchmark.

### Current segmentation architecture

We have two intended modes:

```text
Basic / Fast
    ↓
OpenCV + morphology + thresholding + watershed/contours

Advanced / AI
    ↓
Cellpose pretrained model
```

Both should eventually return the **same internal detection representation**, so tracking and lineage are independent of the selected segmentation method.

Current detection abstraction:

```python
Detection:
    detection_id
    centroid
    area
    mask
    confidence
```

Current segmentation result contains:

```python
SegmentationResult:
    frame_index
    image
    detections
    label_mask
```

### Cellpose experiment

Cellpose was successfully tested in Google Colab on Fluo-N3DH-CHO.

The experiment used:

- Cellpose pretrained model
    
- GPU
    
- 2D MIP from the 3D microscopy frame
    
- Cellpose segmentation
    
- centroid extraction
    

Observed test result against ST:

```text
Ground Truth Cells: 10
Predicted Cells:    11
Precision:          90.9%
Recall:            100.0%
F1:                 95.2%
```

Important: this is currently **2D MIP Cellpose**, not true volumetric 3D Cellpose segmentation. For the 5-day prototype, this is intentional/practical unless later evidence shows true 3D inference is worth the complexity.

Cellpose environment required NumPy compatibility handling in Colab, including NumPy `1.26.4`.

### Current tracking architecture

Production tracker:

```text
CentroidTracker
    ↓
Hungarian assignment
    ↓
maximum centroid-distance constraint
    ↓
Track objects
```

Current `Track` stores:

- `track_id`
    
- position history
    
- frame history
    
- area history
    
- detection IDs
    
- confidence history
    
- missed-frame information
    

Therefore a cell track now contains meaningful per-frame information rather than only a trajectory.

`TrackingResult` contains all tracks and supports persistent-track filtering.

### Current division architecture

We replaced the simplistic experimental division evaluation with a more conservative heuristic.

A candidate division considers:

1. Parent track termination
    
2. Two daughter tracks appearing shortly afterward
    
3. Spatial proximity
    
4. Temporal proximity
    
5. Daughter-track persistence
    
6. Area consistency when available
    

`DivisionEvent` stores:

- parent ID
    
- daughter IDs
    
- event frame
    
- parent position
    
- daughter positions
    
- confidence
    
- spatial score
    
- temporal score
    
- persistence score
    
- area score
    

The lineage graph connects:

```text
Parent
 ├── Daughter A
 └── Daughter B
```

and is JSON-serializable for eventual frontend/API use.

A basic lineage test currently produced approximately:

```text
Tracks: 242
Division events: 11
```

on CHO.

These values are experimental and should **not** be presented as scientifically validated ground truth.

### Current lineage architecture

```text
Detection
    ↓
TrackingResult
    ↓
DivisionDetector
    ↓
DivisionEvent[]
    ↓
LineageGraph
```

The graph exposes roots, parents, daughters, parent lookup, divisions, and JSON serialization.

### Important product goal

The final application should not merely display static plots.

The intended UI should support:

- smooth ZIP dataset upload
    
- automatic extraction/discovery
    
- dataset metadata/features displayed to researcher
    
- sequence/frame selection
    
- original microscopy visualization
    
- 3D/volume-aware visualization where practical
    
- segmentation overlays
    
- temporal navigation
    
- tracking trajectories
    
- clickable cells
    
- selected-cell trajectory/history
    
- division event visualization
    
- parent → daughter relationships
    
- interactive lineage graph
    
- researcher-oriented statistics/dashboard
    
- Basic/Fast vs Advanced/AI processing toggle
    
- visually impressive presentation suitable for a ~2-minute hackathon demonstration
    

The backend should therefore expose structured data rather than returning only rendered matplotlib figures.

### Development rule for this chat

We are now entering the **web application phase**.

Do NOT unnecessarily continue experimenting with standalone scripts.

First decide the clean application architecture/API boundary, then on my command we'll implement it incrementally. After this prompt, is purely brainstorming phases step by step...breakdown in multiple phases so that we can keep track of progress and build sequentially.

Likely direction:

```text
Frontend
   ↓
Backend API
   ↓
Pipeline/service layer
   ↓
data / segmentation / tracking / lineage
```

The frontend should consume JSON/structured results and request frames/visualizations as needed.

Keep implementation lightweight and practical for the 5-day constraint.

**Do not over-engineer.**

When I provide existing files, inspect them before replacing them. If something is missing, ask for the specific file rather than inventing its contents.

Also: keep responses concise and code-focused. I will provide files/results step-by-step as needed.