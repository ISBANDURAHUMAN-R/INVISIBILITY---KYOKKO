"""
PROJECT KYOKKO
Background Restoration & Cinematic Alpha Blending Engine
Seamless body replacement, smooth dissolve transitions, and illumination balancing.
"""

import time
from typing import Optional
import cv2
import numpy as np


class BackgroundRestorer:
    def __init__(self, transition_ms: int = 250):
        self.transition_ms = transition_ms
        self._current_alpha: float = 0.0  # 0.0 = visible, 1.0 = invisible
        self._target_alpha: float = 0.0
        self._last_time: float = time.time()

    def set_target_state(self, invisible: bool) -> None:
        self._target_alpha = 1.0 if invisible else 0.0

    @property
    def current_alpha(self) -> float:
        return self._current_alpha

    def is_transitioning(self) -> bool:
        return abs(self._current_alpha - self._target_alpha) > 0.005

    def restore(
        self,
        camera_frame: np.ndarray,
        background_frame: Optional[np.ndarray],
        person_mask: np.ndarray,
        alternative_mode: str = "none",  # 'none', 'blur', 'virtual_bg'
    ) -> np.ndarray:
        """
        Combine camera_frame and background_frame using person_mask and smooth alpha transitions.
        person_mask: float32 [0.0, 1.0] where 1.0 = person, 0.0 = background.
        """
        if camera_frame is None or camera_frame.size == 0:
            return camera_frame

        now = time.time()
        dt = max(0.001, min(0.1, now - self._last_time))
        self._last_time = now

        # Update smooth transition alpha
        if self.transition_ms <= 0:
            self._current_alpha = self._target_alpha
        else:
            step = dt / (self.transition_ms / 1000.0)
            if self._current_alpha < self._target_alpha:
                self._current_alpha = min(self._target_alpha, self._current_alpha + step)
            elif self._current_alpha > self._target_alpha:
                self._current_alpha = max(self._target_alpha, self._current_alpha - step)

        # If completely visible (alpha == 0), return original camera frame directly
        if self._current_alpha <= 0.001:
            return camera_frame

        h, w = camera_frame.shape[:2]

        # Alternative mode handling if no background captured
        if background_frame is None:
            if alternative_mode == "blur":
                # Blur user or background
                bg_replacement = cv2.GaussianBlur(camera_frame, (51, 51), 0)
            else:
                # Dark ambient aesthetic backdrop
                bg_replacement = np.full((h, w, 3), (20, 15, 30), dtype=np.uint8)
                # Add prompt text to background
                cv2.putText(
                    bg_replacement,
                    "KYOKKO: Background Not Calibrated",
                    (w // 2 - 200, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (160, 120, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    bg_replacement,
                    "Step out of frame & click 'Capture Background'",
                    (w // 2 - 220, h // 2 + 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (200, 200, 200),
                    1,
                    cv2.LINE_AA,
                )
        else:
            bg_replacement = background_frame
            if bg_replacement.shape[:2] != (h, w):
                bg_replacement = cv2.resize(bg_replacement, (w, h), interpolation=cv2.INTER_LINEAR)

        # Compute effective blending weight: person_mask * transition_alpha
        # Where effective_mask is 1.0, show background. Where 0.0, show camera frame.
        effective_mask = (person_mask * self._current_alpha)[:, :, np.newaxis]

        # Seamless vectorized alpha blend
        cam_float = camera_frame.astype(np.float32)
        bg_float = bg_replacement.astype(np.float32)

        blended = cam_float * (1.0 - effective_mask) + bg_float * effective_mask
        return np.clip(blended, 0, 255).astype(np.uint8)

    def reset(self) -> None:
        self._current_alpha = 0.0
        self._target_alpha = 0.0
