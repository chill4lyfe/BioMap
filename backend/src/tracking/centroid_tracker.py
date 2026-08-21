import numpy as np
from scipy.optimize import linear_sum_assignment

from src.segmentation.base import Detection
from .result import Track, TrackingResult


class CentroidTracker:
    """
    Lightweight multi-object tracker.

    Associates detections between consecutive frames
    using the Hungarian algorithm and centroid distance.
    """

    def __init__(
        self,
        max_distance: float = 35.0,
        max_missed_frames: int = 1,
    ):
        self.max_distance = max_distance
        self.max_missed_frames = max_missed_frames

    @staticmethod
    def _distance(a, b) -> float:
        return float(
            np.linalg.norm(
                np.asarray(a, dtype=np.float32)
                - np.asarray(b, dtype=np.float32)
            )
        )

    def _new_track(
        self,
        track_id: int,
        detection: Detection,
        frame_index: int,
    ) -> Track:

        track = Track(
            track_id=track_id
        )

        track.add_observation(
            frame=frame_index,
            position=detection.centroid,
            area=detection.area,
            detection_id=detection.detection_id,
            confidence=detection.confidence,
        )

        return track

    def _find_division_pairs(
        self,
        active_ids,
        tracks,
        detections,
    ):
        """
        Find conservative parent -> two-detection split candidates.

        This prevents Hungarian matching from consuming one daughter
        as a continuation of the parent track.
        """

        candidates = []

        for track_id in active_ids:
            parent = tracks[track_id]

            if parent.length < 4:
                continue

            parent_position = parent.last_position

            nearby = []

            for detection_index, detection in enumerate(
                detections
            ):
                distance = self._distance(
                    parent_position,
                    detection.centroid,
                )

                if distance <= self.max_distance:
                    nearby.append(
                        (
                            detection_index,
                            distance,
                            detection,
                        )
                    )

            if len(nearby) < 2:
                continue

            nearby.sort(
                key=lambda item: item[1]
            )

            a = nearby[0]
            b = nearby[1]

            daughter_distance = self._distance(
                a[2].centroid,
                b[2].centroid,
            )

            if daughter_distance > self.max_distance:
                continue

            if parent.last_area is not None:
                daughter_area = (
                    float(a[2].area)
                    + float(b[2].area)
                )

                if parent.last_area > 0:
                    area_ratio = (
                        daughter_area
                        / parent.last_area
                    )

                    if not (
                        0.25
                        <= area_ratio
                        <= 3.0
                    ):
                        continue

            spatial_score = (
                1.0
                - (
                    (a[1] + b[1])
                    / (
                        2.0
                        * self.max_distance
                    )
                )
            )

            candidates.append(
                {
                    "parent_id": track_id,
                    "detections": (
                        a[0],
                        b[0],
                    ),
                    "score": spatial_score,
                }
            )

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return candidates

    def track(
        self,
        detections_per_frame: list[list[Detection]],
    ) -> TrackingResult:

        tracks: dict[int, Track] = {}

        # Track IDs currently alive.
        active: dict[int, int] = {}

        # Number of consecutive frames without an observation.
        missed: dict[int, int] = {}

        next_track_id = 1

        for frame_index, detections in enumerate(
            detections_per_frame
        ):

            detections = list(detections)

            # ------------------------------------------------------
            # First frame
            # ------------------------------------------------------

            if frame_index == 0:

                for detection in detections:

                    track = self._new_track(
                        next_track_id,
                        detection,
                        frame_index,
                    )

                    tracks[next_track_id] = track
                    active[next_track_id] = next_track_id
                    missed[next_track_id] = 0

                    next_track_id += 1

                continue

            active_ids = list(active.keys())

            # ------------------------------------------------------
            # Nothing currently active
            # ------------------------------------------------------

            if not active_ids:

                for detection in detections:

                    track = self._new_track(
                        next_track_id,
                        detection,
                        frame_index,
                    )

                    tracks[next_track_id] = track
                    active[next_track_id] = next_track_id
                    missed[next_track_id] = 0

                    next_track_id += 1

                continue

            # ------------------------------------------------------
            # No detections in this frame
            # ------------------------------------------------------

            if not detections:

                expired = []

                for track_id in active_ids:

                    missed[track_id] += 1

                    if (
                        missed[track_id]
                        > self.max_missed_frames
                    ):
                        expired.append(track_id)

                for track_id in expired:
                    active.pop(track_id, None)
                    missed.pop(track_id, None)

                continue

            # ------------------------------------------------------
            # Build Hungarian cost matrix
            # ------------------------------------------------------

            cost_matrix = np.zeros(
                (
                    len(active_ids),
                    len(detections),
                ),
                dtype=np.float32,
            )

            for i, track_id in enumerate(active_ids):

                previous_position = (
                    tracks[track_id].last_position
                )

                for j, detection in enumerate(
                    detections
                ):
                    cost_matrix[i, j] = (
                        self._distance(
                            previous_position,
                            detection.centroid,
                        )
                    )

            # ------------------------------------------------------
            # Division-aware split candidates
            # ------------------------------------------------------

            division_candidates = (
                self._find_division_pairs(
                    active_ids,
                    tracks,
                    detections,
                )
            )

            division_parents = set()
            division_detections = set()

            for candidate in division_candidates:

                parent_id = candidate["parent_id"]
                daughter_indices = candidate["detections"]

                if parent_id in division_parents:
                    continue

                if any(
                    index in division_detections
                    for index in daughter_indices
                ):
                    continue

                division_parents.add(parent_id)
                division_detections.update(
                    daughter_indices
                )

            # ------------------------------------------------------
            # Hungarian assignment
            # ------------------------------------------------------

            rows, cols = linear_sum_assignment(
                cost_matrix
            )

            matched_tracks = set()
            matched_detections = set()

            # ------------------------------------------------------
            # Accept only spatially valid matches
            # ------------------------------------------------------

            for row, col in zip(rows, cols):

                track_id = active_ids[row]
                detection = detections[col]

                # Do not consume a possible daughter as
                # continuation of the parent.
                if track_id in division_parents:
                    continue

                if col in division_detections:
                    continue

                distance = cost_matrix[
                    row,
                    col,
                ]

                if distance > self.max_distance:
                    continue

                association_confidence = max(
                    0.0,
                    1.0 - (
                        distance
                        / self.max_distance
                    ),
                )

                track_confidence = (
                    detection.confidence
                    * association_confidence
                )

                tracks[track_id].add_observation(
                    frame=frame_index,
                    position=detection.centroid,
                    area=detection.area,
                    detection_id=detection.detection_id,
                    confidence=track_confidence,
                )

                tracks[track_id].missed_frames = 0
                missed[track_id] = 0

                matched_tracks.add(track_id)
                matched_detections.add(col)

            # ------------------------------------------------------
            # Unmatched existing tracks
            # ------------------------------------------------------

            expired = []

            for track_id in active_ids:

                if track_id in matched_tracks:
                    continue

                # Possible division parent: terminate it here.
                if track_id in division_parents:
                    expired.append(track_id)
                    continue

                missed[track_id] += 1

                tracks[track_id].missed_frames = (
                    missed[track_id]
                )

                if (
                    missed[track_id]
                    > self.max_missed_frames
                ):
                    expired.append(track_id)

            for track_id in expired:
                active.pop(track_id, None)
                missed.pop(track_id, None)

            # ------------------------------------------------------
            # Unmatched detections become new tracks
            # ------------------------------------------------------

            for detection_index, detection in enumerate(
                detections
            ):

                if detection_index in matched_detections:
                    continue

                track = self._new_track(
                    next_track_id,
                    detection,
                    frame_index,
                )

                tracks[next_track_id] = track
                active[next_track_id] = next_track_id
                missed[next_track_id] = 0

                next_track_id += 1

        return TrackingResult(
            tracks=tracks
        )