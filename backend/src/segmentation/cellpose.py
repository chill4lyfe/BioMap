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
        gpu: bool = True,
        diameter: float = None,
    ):
        try:
            from cellpose import models
            import torch
        except ImportError as exc:
            raise ImportError(
                "Cellpose or PyTorch is not installed. "
                "Ensure both are installed in your active environment."
            ) from exc

        # Set GPU only if CUDA is actually accessible
        self.gpu = bool(gpu and torch.cuda.is_available())
        self.diameter = diameter
        self.model_name = model_name

        try:
            self.model = models.CellposeModel(
                gpu=self.gpu,
                pretrained_model=model_name,
            )
        except Exception:
            # Fallback to standard cyto2 model if specific weight name fails
            self.model = models.CellposeModel(
                gpu=self.gpu,
                model_type="cyto2",
            )

    @staticmethod
    def _prepare_image(volume):
        """
        Convert arbitrary 2D/3D microscopy volume to a normalized 2D MIP.
        Handles both uint8 (CHO) and uint16 (MDA231) data types.
        """
        volume = np.asarray(volume)

        if volume.ndim == 3:
            image = np.max(volume, axis=0)
        elif volume.ndim == 2:
            image = volume
        else:
            raise ValueError(
                f"Expected 2D/3D microscopy data, got shape {volume.shape}"
            )

        image = image.astype(np.float32)

        minimum = float(image.min())
        maximum = float(image.max())

        if maximum > minimum:
            image = ((image - minimum) / (maximum - minimum)) * 255.0
        else:
            image = np.zeros_like(image)

        return image.astype(np.uint8)

    def segment(
        self,
        volume,
        frame_index: int = 0,
    ):
        image = self._prepare_image(volume)

        eval_output = self.model.eval(
            image,
            diameter=self.diameter,
            channels=[0, 0],
        )

        masks = eval_output[0] if isinstance(eval_output, tuple) else eval_output

        detections = []

        for label in np.unique(masks):
            if label == 0:
                continue

            ys, xs = np.where(masks == label)

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