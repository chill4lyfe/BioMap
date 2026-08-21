from pathlib import Path
import numpy as np
from .loader import DatasetLoader
from .metadata import (
    DatasetMetadata,
    SequenceMetadata,
    VolumeMetadata,
)


class BioMapDataset:
    """
    High-level dataset interface used by the rest of BioMap.

    Everything downstream should eventually interact with this class
    rather than constructing dataset paths manually.
    """

    def __init__(
        self,
        dataset_path: str | Path,
    ):
        self.loader = DatasetLoader(dataset_path)

        self.path = Path(dataset_path)

        self.metadata = self._build_metadata()

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _build_metadata(self) -> DatasetMetadata:
        """Inspect the dataset and construct metadata."""

        sequences = self.loader.list_sequences()

        metadata = DatasetMetadata(
            name=self.path.name,
            root_path=str(self.path),
            sequences=sequences,
        )

        for sequence in sequences:
            raw_frames = self.loader.list_raw_frames(sequence)

            first_frame = self.loader.load_frame(
                sequence,
                0,
            )

            st_files = self.loader.list_segmentation_files(
                sequence,
                "ST",
            )

            gt_files = self.loader.list_segmentation_files(
                sequence,
                "GT",
            )

            tra_file = self.loader.get_tracking_file(sequence)

            seq_metadata = SequenceMetadata(
                name=sequence,
                frame_count=len(raw_frames),
                frame_shape=tuple(first_frame.shape),
                frame_dtype=str(first_frame.dtype),
                has_st=len(st_files) > 0,
                has_gt=len(gt_files) > 0,
                has_tra=tra_file is not None,
                raw_frame_names=[
                    p.name for p in raw_frames
                ],
            )

            metadata.sequence_metadata[sequence] = seq_metadata

        return metadata

    # ------------------------------------------------------------------
    # Public data access
    # ------------------------------------------------------------------

    def sequences(self) -> list[str]:
        return self.metadata.sequences

    def frame_count(self, sequence: str = "01") -> int:
        return self.metadata.sequence_metadata[
            sequence
        ].frame_count

    def frame_shape(self, sequence: str = "01") -> tuple[int, ...]:
        return self.metadata.sequence_metadata[
            sequence
        ].frame_shape

    def load_frame(
        self,
        frame: int,
        sequence: str = "01",
    ) -> np.ndarray:
        return self.loader.load_frame(
            sequence,
            frame,
        )

    def get_volume_metadata(
        self,
        frame: int = 0,
        sequence: str = "01",
    ) -> VolumeMetadata:

        volume = self.load_frame(
            frame=frame,
            sequence=sequence,
        )

        return VolumeMetadata(
            shape=tuple(volume.shape),
            dtype=str(volume.dtype),
            dimensions=volume.ndim,
            z=volume.shape[0],
            y=volume.shape[1],
            x=volume.shape[2],
            min_value=float(volume.min()),
            max_value=float(volume.max()),
        )

    # ------------------------------------------------------------------
    # Annotation access
    # ------------------------------------------------------------------

    def segmentation_files(
        self,
        sequence: str = "01",
        annotation_type: str = "ST",
    ) -> list[Path]:

        return self.loader.list_segmentation_files(
            sequence,
            annotation_type,
        )

    def tracking_annotations(
        self,
        sequence: str = "01",
    ):
        return self.loader.load_tracking_annotations(
            sequence
        )

    # ------------------------------------------------------------------
    # Debug / inspection
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Return a human-readable dataset summary."""

        lines = [
            f"Dataset: {self.metadata.name}",
            f"Path: {self.metadata.root_path}",
            f"Sequences: {', '.join(self.sequences())}",
            "",
        ]

        for sequence in self.sequences():
            meta = self.metadata.sequence_metadata[
                sequence
            ]

            lines.extend(
                [
                    f"Sequence {sequence}:",
                    f"  Frames: {meta.frame_count}",
                    f"  Shape: {meta.frame_shape}",
                    f"  Dtype: {meta.frame_dtype}",
                    f"  ST: {'yes' if meta.has_st else 'no'}",
                    f"  GT: {'yes' if meta.has_gt else 'no'}",
                    f"  TRA: {'yes' if meta.has_tra else 'no'}",
                    "",
                ]
            )

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"BioMapDataset("
            f"name='{self.metadata.name}', "
            f"sequences={self.sequences()}"
            f")"
        )