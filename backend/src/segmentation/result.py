from dataclasses import dataclass
import numpy as np


@dataclass
class CellDetection:
    cell_id: int
    centroid: tuple[float, float]
    area: float
    mask: np.ndarray


@dataclass
class SegmentationResult:
    """
    Standard output consumed by tracking and visualization.
    """

    labels: np.ndarray
    binary_mask: np.ndarray
    working_image: np.ndarray
    detections: list[CellDetection]

    @property
    def cell_count(self) -> int:
        return len(self.detections)

    @property
    def centroids(self) -> np.ndarray:
        if not self.detections:
            return np.empty((0, 2), dtype=np.float32)

        return np.array(
            [d.centroid for d in self.detections],
            dtype=np.float32,
        )