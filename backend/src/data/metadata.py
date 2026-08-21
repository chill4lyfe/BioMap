# src/data/metadata.py

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VolumeMetadata:
    """
    Metadata describing one microscopy volume.

    Expected volume layout:
        (Z, Y, X)
    """

    shape: tuple[int, ...]
    dtype: str
    dimensions: int

    z: Optional[int] = None
    y: Optional[int] = None
    x: Optional[int] = None

    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class SequenceMetadata:
    """Metadata describing one CTC sequence."""

    name: str
    frame_count: int

    frame_shape: Optional[tuple[int, ...]] = None
    frame_dtype: Optional[str] = None

    has_st: bool = False
    has_gt: bool = False
    has_tra: bool = False

    raw_frame_names: list[str] = field(default_factory=list)


@dataclass
class DatasetMetadata:
    """High-level metadata for a BioMap dataset."""

    name: str
    root_path: str

    sequences: list[str] = field(default_factory=list)

    sequence_metadata: dict[str, SequenceMetadata] = field(
        default_factory=dict
    )