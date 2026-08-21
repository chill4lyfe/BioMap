# src/visualization/volume.py

import numpy as np


def normalize_for_display(
    image: np.ndarray,
) -> np.ndarray:
    """
    Normalize an image/volume to uint8 for visualization.

    The original array is not modified.
    """

    image = np.asarray(image)

    if image.size == 0:
        raise ValueError("Cannot normalize an empty image.")

    image_min = image.min()
    image_max = image.max()

    if image_max == image_min:
        return np.zeros_like(image, dtype=np.uint8)

    normalized = (
        (image.astype(np.float32) - image_min)
        / (image_max - image_min)
        * 255.0
    )

    return np.clip(
        normalized,
        0,
        255,
    ).astype(np.uint8)


def get_z_slice(
    volume: np.ndarray,
    z: int,
) -> np.ndarray:
    """
    Extract one Z slice from a (Z, Y, X) volume.
    """

    if volume.ndim != 3:
        raise ValueError(
            f"Expected 3D volume (Z,Y,X), got {volume.shape}"
        )

    if z < 0 or z >= volume.shape[0]:
        raise IndexError(
            f"Z index {z} outside range "
            f"[0, {volume.shape[0] - 1}]"
        )

    return volume[z]


def get_mip(
    volume: np.ndarray,
) -> np.ndarray:
    """
    Maximum Intensity Projection along Z.

    Input:
        (Z, Y, X)

    Output:
        (Y, X)
    """

    if volume.ndim != 3:
        raise ValueError(
            f"Expected 3D volume (Z,Y,X), got {volume.shape}"
        )

    return np.max(volume, axis=0)


def get_middle_slice(
    volume: np.ndarray,
) -> np.ndarray:
    """Return the middle Z slice."""

    if volume.ndim != 3:
        raise ValueError(
            f"Expected 3D volume (Z,Y,X), got {volume.shape}"
        )

    return volume[volume.shape[0] // 2]