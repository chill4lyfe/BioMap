# src/tracking/events.py

from dataclasses import dataclass
import numpy as np


@dataclass
class DivisionEvent:
    parent_id: int
    daughter_ids: tuple[int, int]
    frame: int

    parent_position: tuple[float, float]
    daughter_positions: tuple[
        tuple[float, float],
        tuple[float, float],
    ]

    confidence: float
    spatial_score: float
    temporal_score: float
    persistence_score: float
    area_score: float


class DivisionDetector:
    """
    Conservative heuristic division detector.

    A division candidate requires:
      1. Parent track terminates.
      2. Two new tracks appear shortly afterward.
      3. Both daughters are spatially close to the parent.
      4. Both daughter tracks persist for multiple frames.
      5. If area information exists, daughter/parent area consistency
         contributes to confidence.
    """

    def __init__(
        self,
        max_parent_daughter_distance: float = 55.0,
        temporal_window: int = 2,
        min_parent_length: int = 4,
        min_daughter_length: int = 3,
        min_confidence: float = 0.55,
    ):
        self.max_distance = max_parent_daughter_distance
        self.temporal_window = temporal_window
        self.min_parent_length = min_parent_length
        self.min_daughter_length = min_daughter_length
        self.min_confidence = min_confidence

    @staticmethod
    def _distance(a, b):
        return float(
            np.linalg.norm(
                np.asarray(a, dtype=np.float32)
                - np.asarray(b, dtype=np.float32)
            )
        )

    @staticmethod
    def _clamp(value):
        return max(0.0, min(1.0, float(value)))

    def _area_score(self, parent, child_a, child_b):
        """
        Uses area only if the tracker provides it.

        If area isn't available, return neutral score rather than
        pretending we know something we don't.
        """

        parent_areas = getattr(parent, "areas", None)
        a_areas = getattr(child_a, "areas", None)
        b_areas = getattr(child_b, "areas", None)

        if not parent_areas or not a_areas or not b_areas:
            return 0.5

        parent_area = float(parent_areas[-1])
        daughter_area = (
            float(a_areas[0]) +
            float(b_areas[0])
        )

        if parent_area <= 0:
            return 0.5

        ratio = daughter_area / parent_area

        # Very tolerant because segmentation area can change
        # considerably around a division event.
        if 0.6 <= ratio <= 1.8:
            return 1.0

        if 0.4 <= ratio <= 2.2:
            return 0.7

        if 0.25 <= ratio <= 3.0:
            return 0.4

        return 0.0

    def detect(self, tracking_result):

        tracks = tracking_result.tracks
        events = []

        # A daughter track should not be assigned to multiple parents.
        used_daughters = set()

        for parent_id, parent in tracks.items():

            if parent.length < self.min_parent_length:
                continue

            parent_end = parent.end_frame
            parent_pos = parent.last_position

            candidates = []

            for child_id, child in tracks.items():

                if child_id == parent_id:
                    continue

                if child_id in used_daughters:
                    continue

                if child.length < self.min_daughter_length:
                    continue

                # Daughter must begin immediately after parent termination.
                delta = child.start_frame - parent_end

                if delta < 0 or delta > self.temporal_window:
                    continue

                distance = self._distance(
                    parent_pos,
                    child.positions[0],
                )

                if distance > self.max_distance:
                    continue

                # Closer = stronger evidence.
                spatial_score = self._clamp(
                    1.0 - distance / self.max_distance
                )

                # Immediate appearance is stronger evidence.
                temporal_score = self._clamp(
                    1.0 - delta / max(
                        1,
                        self.temporal_window
                    )
                )

                # Longer daughter tracks are less likely to be noise.
                persistence_score = self._clamp(
                    min(
                        child.length / 8.0,
                        1.0
                    )
                )

                candidates.append(
                    {
                        "id": child_id,
                        "distance": distance,
                        "spatial": spatial_score,
                        "temporal": temporal_score,
                        "persistence": persistence_score,
                    }
                )

            if len(candidates) < 2:
                continue

            # Prefer the two strongest candidates.
            candidates.sort(
                key=lambda x: (
                    x["spatial"]
                    + x["temporal"]
                    + x["persistence"]
                ),
                reverse=True,
            )

            a = candidates[0]
            b = candidates[1]

            child_a = tracks[a["id"]]
            child_b = tracks[b["id"]]

            area_score = self._area_score(
                parent,
                child_a,
                child_b,
            )

            confidence = (
                0.35 * (
                    a["spatial"] +
                    b["spatial"]
                ) / 2
                +
                0.20 * (
                    a["temporal"] +
                    b["temporal"]
                ) / 2
                +
                0.25 * (
                    a["persistence"] +
                    b["persistence"]
                ) / 2
                +
                0.20 * area_score
            )

            if confidence < self.min_confidence:
                continue

            event = DivisionEvent(
                parent_id=parent_id,
                daughter_ids=(
                    a["id"],
                    b["id"],
                ),
                frame=parent_end,
                parent_position=parent_pos,
                daughter_positions=(
                    child_a.positions[0],
                    child_b.positions[0],
                ),
                confidence=float(confidence),
                spatial_score=float(
                    (a["spatial"] + b["spatial"]) / 2
                ),
                temporal_score=float(
                    (a["temporal"] + b["temporal"]) / 2
                ),
                persistence_score=float(
                    (a["persistence"] + b["persistence"]) / 2
                ),
                area_score=float(area_score),
            )

            events.append(event)

            used_daughters.add(a["id"])
            used_daughters.add(b["id"])

        return events