# test_lineage.py

from src.data import BioMapDataset
from src.segmentation import ClassicalSegmenter
from src.tracking import CentroidTracker
from src.lineage import LineageReconstructor

DATASET = "Fluo-N3DH-CHO"
SEQUENCE = "01"

# Fixed path to account for running from the backend directory
dataset = BioMapDataset(
    f"../datasets/{DATASET}"
)

segmenter = ClassicalSegmenter()
detections_per_frame = []

for frame in range(dataset.frame_count(SEQUENCE)):

    volume = dataset.load_frame(
        sequence=SEQUENCE,
        frame=frame,
    )

    result = segmenter.segment(volume)

    # Wrap CellDetection objects into a proxy/mock object with 'detection_id' and 'confidence'
    frame_detections = []
    for d in result.detections:
        class ProxyDetection:
            def __init__(self, cell_det):
                self.centroid = cell_det.centroid
                self.area = cell_det.area
                self.detection_id = cell_det.cell_id  # Map cell_id to detection_id
                self.confidence = 1.0                # Default confidence
        
        frame_detections.append(ProxyDetection(d))

    detections_per_frame.append(frame_detections)

tracker = CentroidTracker(
    max_distance=35.0,
    max_missed_frames=1,
)

tracking = tracker.track(
    detections_per_frame
)

lineage = LineageReconstructor().reconstruct(
    tracking
)

print("Tracks:", tracking.track_count)
print("Division events:", lineage.division_count)
print("Roots:", lineage.graph.roots())

print("\nLineage JSON structure:")
print(
    lineage.to_dict()
)