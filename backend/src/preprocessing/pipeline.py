import cv2
import numpy as np


def normalize_image(
    image: np.ndarray,
) -> np.ndarray:
    """
    Normalize arbitrary numeric microscopy data to uint8 [0, 255].

    Works with uint8, uint16, float, etc.
    """

    image = np.asarray(image)

    if image.size == 0:
        raise ValueError("Cannot normalize an empty image.")

    image_min = float(image.min())
    image_max = float(image.max())

    if image_max <= image_min:
        return np.zeros(image.shape, dtype=np.uint8)

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


def denoise_image(
    image: np.ndarray,
    kernel_size: int = 5,
) -> np.ndarray:
    """
    Gaussian denoising for a 2D uint8 image.
    """

    if image.ndim != 2:
        raise ValueError(
            f"Expected 2D image, got {image.shape}"
        )

    if kernel_size % 2 == 0:
        raise ValueError(
            "Gaussian kernel size must be odd."
        )

    return cv2.GaussianBlur(
        image,
        (kernel_size, kernel_size),
        0,
    )


def enhance_contrast(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    CLAHE local contrast enhancement.
    """

    if image.ndim != 2:
        raise ValueError(
            f"Expected 2D image, got {image.shape}"
        )

    clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=tile_grid_size,
    )

    return clahe.apply(image)


def preprocess_slice(
    image: np.ndarray,
    blur_kernel: int = 5,
    clip_limit: float = 2.0,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    Full preprocessing pipeline for one 2D slice.

    Pipeline:
        raw
        ↓
        normalization
        ↓
        Gaussian denoising
        ↓
        CLAHE
    """

    if image.ndim != 2:
        raise ValueError(
            f"Expected 2D image, got {image.shape}"
        )

    normalized = normalize_image(image)

    denoised = denoise_image(
        normalized,
        kernel_size=blur_kernel,
    )

    enhanced = enhance_contrast(
        denoised,
        clip_limit=clip_limit,
        tile_grid_size=tile_grid_size,
    )

    return enhanced


def preprocess_volume(
    volume: np.ndarray,
    blur_kernel: int = 5,
    clip_limit: float = 2.0,
    tile_grid_size: tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    Apply preprocessing independently to every Z slice.

    Input:
        (Z, Y, X)

    Output:
        (Z, Y, X), uint8
    """

    if volume.ndim != 3:
        raise ValueError(
            f"Expected 3D volume (Z,Y,X), got {volume.shape}"
        )

    processed = np.empty(
        volume.shape,
        dtype=np.uint8,
    )

    for z in range(volume.shape[0]):
        processed[z] = preprocess_slice(
            volume[z],
            blur_kernel=blur_kernel,
            clip_limit=clip_limit,
            tile_grid_size=tile_grid_size,
        )

    return processed


class Preprocessor:
    """
    Configurable preprocessing object.

    Useful later when the frontend/backend exposes
    preprocessing parameters.
    """

    def __init__(
        self,
        blur_kernel: int = 5,
        clip_limit: float = 2.0,
        tile_grid_size: tuple[int, int] = (8, 8),
    ):
        self.blur_kernel = blur_kernel
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size

    def process_slice(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        return preprocess_slice(
            image,
            blur_kernel=self.blur_kernel,
            clip_limit=self.clip_limit,
            tile_grid_size=self.tile_grid_size,
        )

    def process_volume(
        self,
        volume: np.ndarray,
    ) -> np.ndarray:

        return preprocess_volume(
            volume,
            blur_kernel=self.blur_kernel,
            clip_limit=self.clip_limit,
            tile_grid_size=self.tile_grid_size,
        )