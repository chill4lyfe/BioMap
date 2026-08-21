# src/tracking/result.py

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class Track:
    """
    One cell followed through time.

    Each observation corresponds to one frame in which
    the cell was successfully detected.
    """

    track_id: int

    positions: list[tuple[float, float]] = field(
        default_factory=list
    )

    frames: list[int] = field(
        default_factory=list
    )

    areas: list[float] = field(
        default_factory=list
    )

    detection_ids: list[int] = field(
        default_factory=list
    )

    confidences: list[float] = field(
        default_factory=list
    )

    missed_frames: int = 0

    @property
    def length(self) -> int:
        return len(self.positions)

    @property
    def last_position(self) -> tuple[float, float]:
        if not self.positions:
            raise ValueError(
                f"Track {self.track_id} has no observations."
            )
        return self.positions[-1]

    @property
    def start_frame(self) -> int:
        if not self.frames:
            raise ValueError(
                f"Track {self.track_id} has no frames."
            )
        return self.frames[0]

    @property
    def end_frame(self) -> int:
        if not self.frames:
            raise ValueError(
                f"Track {self.track_id} has no frames."
            )
        return self.frames[-1]

    @property
    def last_area(self) -> Optional[float]:
        return self.areas[-1] if self.areas else None

    @property
    def mean_confidence(self) -> Optional[float]:
        if not self.confidences:
            return None

        return float(
            np.mean(self.confidences)
        )

    def add_observation(
        self,
        frame: int,
        position: tuple[float, float],
        area: Optional[float] = None,
        detection_id: Optional[int] = None,
        confidence: Optional[float] = None,
    ):
        """
        Append one successful detection to this track.
        """

        self.frames.append(int(frame))
        self.positions.append(
            (
                float(position[0]),
                float(position[1]),
            )
        )

        if area is not None:
            self.areas.append(float(area))

        if detection_id is not None:
            self.detection_ids.append(
                int(detection_id)
            )

        if confidence is not None:
            self.confidences.append(
                float(confidence)
            )


@dataclass
class TrackingResult:
    tracks: dict[int, Track]

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    def persistent_tracks(
        self,
        minimum_length: int = 2,
    ) -> dict[int, Track]:

        return {
            track_id: track
            for track_id, track in self.tracks.items()
            if track.length >= minimum_length
        }

    def get_track(
        self,
        track_id: int,
    ) -> Track:

        if track_id not in self.tracks:
            raise KeyError(
                f"Track {track_id} does not exist."
            )

        return self.tracks[track_id]