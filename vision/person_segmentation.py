"""
PROJECT KYOKKO
MediaPipe Person Segmentation Module
Ultra-fast full-body person masking and confidence extraction.
"""

from dataclasses import dataclass
from typing import Optional
import cv2
import mediapipe as mp
import numpy as np


@dataclass
class SegmentationResult:
    mask: np.ndarray             # float32 mask [0.0, 1.0] at full input resolution
    has_person: bool             # Whether a person is present
    person_coverage: float       # Percentage of frame covered by person (0.0 - 1.0)


class PersonSegmenter:
    def __init__(self, model_selection: int = 0):
        """
        model_selection: 0 for general (higher quality), 1 for landscape (faster).
        """
        self.model_selection = model_selection
        self.mp_selfie = mp.solutions.selfie_segmentation
        self.segmenter = self.mp_selfie.SelfieSegmentation(model_selection=model_selection)

    def set_model(self, model_selection: int) -> None:
        if model_selection != self.model_selection:
            self.model_selection = model_selection
            self.segmenter.close()
            self.segmenter = self.mp_selfie.SelfieSegmentation(model_selection=model_selection)

    def process(self, frame_bgr: np.ndarray, downscale_factor: float = 1.0) -> SegmentationResult:
        if frame_bgr is None or frame_bgr.size == 0:
            return SegmentationResult(mask=np.zeros((1, 1), dtype=np.float32), has_person=False, person_coverage=0.0)

        h, w = frame_bgr.shape[:2]

        # Optionally downscale for ultra-fast inference
        if downscale_factor < 0.99:
            proc_w = max(160, int(w * downscale_factor))
            proc_h = max(120, int(h * downscale_factor))
            infer_frame = cv2.resize(frame_bgr, (proc_w, proc_h), interpolation=cv2.INTER_LINEAR)
        else:
            infer_frame = frame_bgr

        frame_rgb = cv2.cvtColor(infer_frame, cv2.COLOR_BGR2RGB)
        results = self.segmenter.process(frame_rgb)

        raw_mask = results.segmentation_mask  # float32 [0.0, 1.0]

        if raw_mask is None:
            full_mask = np.zeros((h, w), dtype=np.float32)
            return SegmentationResult(mask=full_mask, has_person=False, person_coverage=0.0)

        # Upscale mask back to original frame dimensions if inference was downscaled
        if raw_mask.shape[:2] != (h, w):
            full_mask = cv2.resize(raw_mask, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            full_mask = raw_mask.copy()

        # Calculate person presence and coverage
        coverage = float(np.mean(full_mask > 0.4))
        has_person = coverage > 0.02  # At least 2% of frame

        return SegmentationResult(
            mask=full_mask,
            has_person=has_person,
            person_coverage=coverage,
        )

    def close(self):
        if self.segmenter:
            self.segmenter.close()
