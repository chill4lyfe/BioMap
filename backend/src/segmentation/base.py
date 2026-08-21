from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Detection:
    detection_id: int
    centroid: tuple[float, float]
    area: float
    mask: Optional[np.ndarray] = None
    confidence: float = 1.0


@dataclass
class SegmentationResult:
    frame_index: int
    image: np.ndarray
    detections: list[Detection]
    label_mask: Optional[np.ndarray] = None

    @property
    def count(self):
        return len(self.detections)

    @property
    def centroids(self):
        return np.asarray(
            [d.centroid for d in self.detections],
            dtype=np.float32,
        )