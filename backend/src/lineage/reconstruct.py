# src/lineage/reconstruct.py

from dataclasses import dataclass

from src.tracking.result import TrackingResult
from src.tracking.events import (
    DivisionDetector,
    DivisionEvent,
)

from .graph import LineageGraph


@dataclass
class LineageResult:
    graph: LineageGraph
    division_events: list[DivisionEvent]

    @property
    def division_count(self) -> int:
        return len(self.division_events)

    def to_dict(self) -> dict:
        data = self.graph.to_dict()

        data["division_events"] = [
            {
                "parent_id": event.parent_id,
                "daughter_ids": list(
                    event.daughter_ids
                ),
                "frame": event.frame,
                "parent_position": list(
                    event.parent_position
                ),
                "daughter_positions": [
                    list(position)
                    for position in event.daughter_positions
                ],
                "spatial_score": event.spatial_score,
                "area_score": event.area_score,
            }
            for event in self.division_events
        ]

        return data


class LineageReconstructor:

    def __init__(
        self,
        division_detector: DivisionDetector | None = None,
    ):
        self.division_detector = (
            division_detector
            or DivisionDetector()
        )

    def reconstruct(
        self,
        tracking_result: TrackingResult,
    ) -> LineageResult:

        graph = LineageGraph.from_tracking(
            tracking_result
        )

        events = self.division_detector.detect(
            tracking_result
        )

        graph.apply_divisions(events)

        return LineageResult(
            graph=graph,
            division_events=events,
        )