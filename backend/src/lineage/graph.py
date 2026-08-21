from dataclasses import dataclass
import networkx as nx

from src.tracking.result import TrackingResult
from src.tracking.events import DivisionEvent


@dataclass
class LineageNode:
    track_id: int
    start_frame: int
    end_frame: int
    track_length: int


class LineageGraph:

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_track(
        self,
        track_id: int,
        start_frame: int,
        end_frame: int,
        track_length: int,
    ):
        self.graph.add_node(
            track_id,
            start_frame=start_frame,
            end_frame=end_frame,
            track_length=track_length,
        )

    def add_division(
        self,
        parent_id: int,
        daughter_ids: tuple[int, int],
        frame: int,
        confidence: float = 0.0,
    ):
        for daughter_id in daughter_ids:
            self.graph.add_edge(
                parent_id,
                daughter_id,
                event="division",
                frame=frame,
                confidence=confidence,
            )

    @classmethod
    def from_tracking(
        cls,
        tracking_result: TrackingResult,
    ) -> "LineageGraph":

        lineage = cls()

        for track_id, track in (
            tracking_result.tracks.items()
        ):
            lineage.add_track(
                track_id=track_id,
                start_frame=track.start_frame,
                end_frame=track.end_frame,
                track_length=track.length,
            )

        return lineage

    def apply_divisions(self, events):
        for event in events:
            self.add_division(
                parent_id=event.parent_id,
                daughter_ids=event.daughter_ids,
                frame=event.frame,
                confidence=event.confidence,
            )

    # --------------------------------------------------------------
    # Queries useful to the eventual frontend
    # --------------------------------------------------------------

    def parents(self) -> list[int]:
        return [
            node
            for node in self.graph.nodes
            if self.graph.out_degree(node) > 0
        ]

    def roots(self) -> list[int]:
        return [
            node
            for node in self.graph.nodes
            if self.graph.in_degree(node) == 0
        ]

    def daughters(
        self,
        parent_id: int,
    ) -> list[int]:
        return list(
            self.graph.successors(parent_id)
        )

    def parent(
        self,
        track_id: int,
    ):
        parents = list(
            self.graph.predecessors(track_id)
        )

        return parents[0] if parents else None

    def divisions(self) -> list[tuple[int, int]]:
        return [
            (parent, child)
            for parent, child in self.graph.edges
        ]

    def to_dict(self) -> dict:
        """
        JSON-friendly representation for the future API.
        """

        nodes = []

        for node, data in self.graph.nodes(
            data=True
        ):
            nodes.append(
                {
                    "track_id": int(node),
                    "start_frame": int(
                        data["start_frame"]
                    ),
                    "end_frame": int(
                        data["end_frame"]
                    ),
                    "track_length": int(
                        data["track_length"]
                    ),
                }
            )

        edges = []

        for parent, child, data in (
            self.graph.edges(data=True)
        ):
            edges.append(
                {
                    "parent_id": int(parent),
                    "child_id": int(child),
                    "event": data.get("event"),
                    "frame": int(data["frame"]),
                    "confidence": float(
                        data.get("confidence", 0.0)
                    ),
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
        }