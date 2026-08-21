import numpy as np
import tifffile

from .base import (
    Detection,
    SegmentationResult,
)


class CellposeSegmenter:

    def __init__(
        self,
        model_name: str = "cyto2",
        gpu: bool = False,
    ):
        try:
            from cellpose import models
        except ImportError as exc:
            raise ImportError(
                "Cellpose is not installed. "
                "Install it in the environment used for "
                "Advanced mode."
            ) from exc

        self.gpu = gpu

        # Cellpose 4 can fall back when a requested pretrained
        # model is unavailable.
        try:
            self.model = models.CellposeModel(
                gpu=gpu,
                pretrained_model=model_name,
            )
        except Exception:
            self.model = models.CellposeModel(
                gpu=gpu,
            )

    @staticmethod
    def _prepare_image(volume):
        """
        Convert arbitrary supported microscopy volume to
        a normalized 2D MIP.

        This is deliberately 2D for the prototype.
        """

        volume = np.asarray(volume)

        if volume.ndim == 3:
            image = np.max(volume, axis=0)
        elif volume.ndim == 2:
            image = volume
        else:
            raise ValueError(
                f"Expected 2D/3D microscopy data, "
                f"got shape {volume.shape}"
            )

        image = image.astype(np.float32)

        minimum = image.min()
        maximum = image.max()

        if maximum > minimum:
            image = (
                (image - minimum)
                / (maximum - minimum)
                * 255.0
            )

        return image.astype(np.uint8)

    def segment(
        self,
        volume,
        frame_index: int = 0,
    ):

        image = self._prepare_image(volume)

        result = self.model.eval(
            image,
            diameter=None,
        )

        masks = result[0]

        detections = []

        for label in np.unique(masks):

            if label == 0:
                continue

            ys, xs = np.where(
                masks == label
            )

            if len(xs) == 0:
                continue

            centroid = (
                float(xs.mean()),
                float(ys.mean()),
            )

            detections.append(
                Detection(
                    detection_id=len(detections) + 1,
                    centroid=centroid,
                    area=float(len(xs)),
                    mask=(masks == label),
                    confidence=1.0,
                )
            )

        return SegmentationResult(
            frame_index=frame_index,
            image=image,
            detections=detections,
            label_mask=masks,
        )