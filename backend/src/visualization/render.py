# src/visualization/render.py

import numpy as np

from .volume import (
    normalize_for_display,
    get_z_slice,
    get_mip,
    get_middle_slice,
)


def prepare_slice(
    volume: np.ndarray,
    z: int,
) -> np.ndarray:
    """
    Return a normalized uint8 Z slice.
    """

    slice_2d = get_z_slice(volume, z)

    return normalize_for_display(slice_2d)


def prepare_mip(
    volume: np.ndarray,
) -> np.ndarray:
    """
    Return a normalized uint8 MIP.
    """

    mip = get_mip(volume)

    return normalize_for_display(mip)


def prepare_middle_slice(
    volume: np.ndarray,
) -> np.ndarray:
    """
    Return the normalized middle Z slice.
    """

    middle = get_middle_slice(volume)

    return normalize_for_display(middle)