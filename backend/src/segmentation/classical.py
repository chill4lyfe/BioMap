# src/segmentation/classical.py

import cv2
import numpy as np

from .result import CellDetection, SegmentationResult


class ClassicalSegmenter:
    """
    Fast OpenCV-based segmentation.

    Pipeline:
        3D volume
            ↓
        MIP
            ↓
        normalization
            ↓
        Gaussian blur
            ↓
        morphological Top-Hat
            ↓
        Otsu threshold
            ↓
        morphological opening
            ↓
        watershed separation
            ↓
        cell instances
    """

    def __init__(
        self,
        blur_kernel: int = 7,
        tophat_kernel: int = 50,
        opening_kernel: int = 3,
        opening_iterations: int = 2,
        distance_threshold: float = 0.20,
        min_area: float = 150.0,
    ):
        self.blur_kernel = blur_kernel
        self.tophat_kernel = tophat_kernel
        self.opening_kernel = opening_kernel
        self.opening_iterations = opening_iterations
        self.distance_threshold = distance_threshold
        self.min_area = min_area

    def _validate_volume(self, volume: np.ndarray) -> None:
        if volume.ndim != 3:
            raise ValueError(
                f"Expected volume (Z,Y,X), got {volume.shape}"
            )

    def _normalize(self, image: np.ndarray) -> np.ndarray:
        image_min = float(image.min())
        image_max = float(image.max())

        if image_max <= image_min:
            return np.zeros(
                image.shape,
                dtype=np.uint8,
            )

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

    def _get_mip(self, volume: np.ndarray) -> np.ndarray:
        return np.max(volume, axis=0)

    def _create_binary_mask(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        normalized = self._normalize(image)

        denoised = cv2.GaussianBlur(
            normalized,
            (
                self.blur_kernel,
                self.blur_kernel,
            ),
            0,
        )

        tophat_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (
                self.tophat_kernel,
                self.tophat_kernel,
            ),
        )

        tophat = cv2.morphologyEx(
            denoised,
            cv2.MORPH_TOPHAT,
            tophat_kernel,
        )

        _, binary = cv2.threshold(
            tophat,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )

        kernel = np.ones(
            (
                self.opening_kernel,
                self.opening_kernel,
            ),
            dtype=np.uint8,
        )

        opening = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            kernel,
            iterations=self.opening_iterations,
        )

        return normalized, opening

    def _watershed(
        self,
        normalized: np.ndarray,
        binary: np.ndarray,
    ) -> np.ndarray:

        kernel = np.ones((3, 3), dtype=np.uint8)

        sure_background = cv2.dilate(
            binary,
            kernel,
            iterations=3,
        )

        distance = cv2.distanceTransform(
            binary,
            cv2.DIST_L2,
            5,
        )

        max_distance = distance.max()

        if max_distance <= 0:
            return np.zeros(
                binary.shape,
                dtype=np.int32,
            )

        _, sure_foreground = cv2.threshold(
            distance,
            self.distance_threshold * max_distance,
            255,
            cv2.THRESH_BINARY,
        )

        sure_foreground = sure_foreground.astype(
            np.uint8
        )

        unknown = cv2.subtract(
            sure_background,
            sure_foreground,
        )

        _, markers = cv2.connectedComponents(
            sure_foreground
        )

        markers = markers + 1
        markers[unknown == 255] = 0

        color_image = cv2.cvtColor(
            normalized,
            cv2.COLOR_GRAY2BGR,
        )

        markers = cv2.watershed(
            color_image,
            markers,
        )

        # Watershed boundaries are -1.
        # Background is marker 1.
        labels = markers.copy()

        labels[labels <= 1] = 0
        labels[labels < 0] = 0

        return labels.astype(np.int32)

    def _extract_detections(
        self,
        labels: np.ndarray,
    ) -> list[CellDetection]:

        detections = []

        label_ids = np.unique(labels)
        label_ids = label_ids[label_ids > 0]

        new_id = 1

        for label_id in label_ids:

            mask = labels == label_id

            area = float(np.count_nonzero(mask))

            if area < self.min_area:
                continue

            ys, xs = np.where(mask)

            if len(xs) == 0:
                continue

            cx = float(xs.mean())
            cy = float(ys.mean())

            detections.append(
                CellDetection(
                    cell_id=new_id,
                    centroid=(cx, cy),
                    area=area,
                    mask=mask,
                )
            )

            new_id += 1

        # Rebuild clean consecutive labels.
        clean_labels = np.zeros_like(labels)

        for detection in detections:
            clean_labels[detection.mask] = detection.cell_id

        return detections, clean_labels

    def segment(
        self,
        volume: np.ndarray,
        frame_index: int = 0,
    ) -> SegmentationResult:

        self._validate_volume(volume)

        mip = self._get_mip(volume)

        normalized, binary = self._create_binary_mask(
            mip
        )

        labels = self._watershed(
            normalized,
            binary,
        )

        detections, labels = self._extract_detections(
            labels
        )

        clean_binary = (
            labels > 0
        ).astype(np.uint8) * 255

        return SegmentationResult(
            labels=labels,
            binary_mask=clean_binary,
            working_image=normalized,
            detections=detections,
        )