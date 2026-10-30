"""
PROJECT KYOKKO
Invisibility Engine Coordinator
Unified pipeline orchestrator for person segmentation, background replacement, and status overlays.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np
from invisibility.background_capture import BackgroundCapture
from invisibility.background_restoration import BackgroundRestorer
from invisibility.mask_processing import MaskProcessor
from vision.gesture_recognition import GestureStatus
from vision.person_segmentation import PersonSegmenter, SegmentationResult


@dataclass
class InvisibilityEngineOutput:
    output_frame: np.ndarray             # Final composite frame for virtual cam / preview
    raw_mask: np.ndarray                # Raw segmentation mask [0.0, 1.0]
    refined_mask: np.ndarray            # Processed feathered mask [0.0, 1.0]
    is_invisible: bool                  # Whether target is set to invisible
    transition_alpha: float             # Current transition progress 0.0 -> 1.0
    has_background: bool                # Whether a background frame is ready


class InvisibilityEngine:
    def __init__(
        self,
        segmentation_model: int = 0,
        mask_threshold: float = 0.55,
        mask_feather: int = 7,
        mask_dilation: int = 3,
        transition_ms: int = 250,
    ):
        self.segmenter = PersonSegmenter(model_selection=segmentation_model)
        self.mask_processor = MaskProcessor(
            threshold=mask_threshold,
            feather=mask_feather,
            dilation=dilation_from_int(mask_dilation),
        )
        self.bg_capture = BackgroundCapture()
        self.restorer = BackgroundRestorer(transition_ms=transition_ms)

        self.manual_override: Optional[bool] = None  # None = follow gesture, True = force invisible, False = force visible
        self.alternative_mode: str = "none"

    def set_manual_override(self, state: Optional[bool]) -> None:
        self.manual_override = state

    def set_alternative_mode(self, mode: str) -> None:
        self.alternative_mode = mode

    def process(
        self,
        frame_bgr: np.ndarray,
        gesture_status: GestureStatus,
        show_mask_overlay: bool = False,
        downscale_factor: float = 1.0,
    ) -> InvisibilityEngineOutput:
        if frame_bgr is None or frame_bgr.size == 0:
            dummy = np.zeros((1, 1, 3), dtype=np.uint8)
            return InvisibilityEngineOutput(
                output_frame=dummy,
                raw_mask=np.zeros((1, 1), dtype=np.float32),
                refined_mask=np.zeros((1, 1), dtype=np.float32),
                is_invisible=False,
                transition_alpha=0.0,
                has_background=False,
            )

        h, w = frame_bgr.shape[:2]

        # 1. Determine target invisibility state
        if self.manual_override is not None:
            target_invisible = self.manual_override
        else:
            target_invisible = gesture_status.is_triggered

        self.restorer.set_target_state(target_invisible)

        # 2. Run Person Segmentation if target is invisible or in transition or user requests mask overlay
        needs_segmentation = (
            target_invisible
            or self.restorer.is_transitioning()
            or show_mask_overlay
            or self.restorer.current_alpha > 0.001
        )

        if needs_segmentation:
            seg_result = self.segmenter.process(frame_bgr, downscale_factor=downscale_factor)
            raw_mask = seg_result.mask
            refined_mask = self.mask_processor.refine(raw_mask)
        else:
            raw_mask = np.zeros((h, w), dtype=np.float32)
            refined_mask = np.zeros((h, w), dtype=np.float32)

        # 3. Retrieve aligned background
        bg_frame = self.bg_capture.get_aligned_background(w, h)

        # 4. Perform background restoration / person removal
        output_frame = self.restorer.restore(
            camera_frame=frame_bgr,
            background_frame=bg_frame,
            person_mask=refined_mask,
            alternative_mode=self.alternative_mode,
        )

        # 5. Optional diagnostic mask visualization
        if show_mask_overlay and needs_segmentation:
            overlay_mask = (refined_mask * 255).astype(np.uint8)
            colored_mask = cv2.applyColorMap(overlay_mask, cv2.COLORMAP_MAGMA)
            output_frame = cv2.addWeighted(output_frame, 0.7, colored_mask, 0.3, 0)

        return InvisibilityEngineOutput(
            output_frame=output_frame,
            raw_mask=raw_mask,
            refined_mask=refined_mask,
            is_invisible=target_invisible,
            transition_alpha=self.restorer.current_alpha,
            has_background=self.bg_capture.has_background(),
        )

    def close(self):
        self.segmenter.close()


def dilation_from_int(val: int) -> int:
    return max(0, val)
