"""
PROJECT KYOKKO
Mask Refinement & Edge Processing Engine
Morphological expansion, Gaussian feathering, and temporal EMA smoothing.
"""

from typing import Optional
import cv2
import numpy as np


class MaskProcessor:
    def __init__(
        self,
        threshold: float = 0.55,
        feather: int = 7,
        dilation: int = 3,
        temporal_smooth: float = 0.65, # Weight of current frame mask
    ):
        self.threshold = threshold
        self.feather = feather
        self.dilation = dilation
        self.temporal_smooth = temporal_smooth
        self._prev_mask: Optional[np.ndarray] = None

    def update_params(
        self,
        threshold: Optional[float] = None,
        feather: Optional[int] = None,
        dilation: Optional[int] = None,
        temporal_smooth: Optional[float] = None,
    ) -> None:
        if threshold is not None:
            self.threshold = max(0.1, min(0.95, threshold))
        if feather is not None:
            k = max(1, feather)
            if k % 2 == 0:
                k += 1
            self.feather = k
        if dilation is not None:
            self.dilation = max(0, dilation)
        if temporal_smooth is not None:
            self.temporal_smooth = max(0.1, min(1.0, temporal_smooth))

    def refine(self, raw_mask: np.ndarray) -> np.ndarray:
        """
        Process raw float segmentation mask [0.0, 1.0] into a polished,
        feathered, temporally smoothed alpha mask of dtype float32 [0.0, 1.0].
        """
        if raw_mask is None or raw_mask.size == 0:
            return np.zeros((1, 1), dtype=np.float32)

        # 1. Binary Threshold
        bin_mask = (raw_mask > self.threshold).astype(np.uint8) * 255

        # 2. Morphological dilation & closing
        if self.dilation > 0:
            k_size = self.dilation * 2 + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
            bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, kernel)
            bin_mask = cv2.dilate(bin_mask, kernel, iterations=1)

        # 3. Edge Feathering via Gaussian Blur
        if self.feather > 1:
            k = self.feather if self.feather % 2 == 1 else self.feather + 1
            feathered = cv2.GaussianBlur(bin_mask, (k, k), 0)
        else:
            feathered = bin_mask

        # Normalize to float32 [0.0, 1.0]
        refined_float = feathered.astype(np.float32) / 255.0

        # 4. Temporal Smoothing (EMA)
        if self._prev_mask is not None and self._prev_mask.shape == refined_float.shape:
            smoothed = (
                self.temporal_smooth * refined_float
                + (1.0 - self.temporal_smooth) * self._prev_mask
            )
        else:
            smoothed = refined_float

        self._prev_mask = smoothed.copy()
        return smoothed

    def reset(self) -> None:
        self._prev_mask = None
