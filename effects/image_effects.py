"""
PROJECT KYOKKO
Image Effects Engine
Real-time high-performance video adjustments, cinematic color filters, and transforms.
"""

from dataclasses import dataclass
from typing import Tuple
import cv2
import numpy as np


@dataclass
class EffectsConfig:
    brightness: int = 0         # [-100, 100]
    contrast: float = 1.0       # [0.5, 3.0]
    saturation: float = 1.0     # [0.0, 3.0]
    blur_amount: int = 0        # [0, 25] (must be odd if > 0)
    sharpen_amount: float = 0.0 # [0.0, 2.0]
    grayscale: bool = False
    color_filter: str = "Normal"# 'Normal', 'Cyberpunk', 'Matrix', 'Sepia', 'Cinema Cool', 'Noir', 'Warm Sunset'
    mirror_mode: bool = False
    output_resolution: Tuple[int, int] = (0, 0) # (w, h) 0 = keep input


class ImageEffects:
    def __init__(self, config: EffectsConfig = None):
        self.config = config or EffectsConfig()

    def update_config(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)

    def apply(self, frame: np.ndarray) -> np.ndarray:
        if frame is None or frame.size == 0:
            return frame

        out = frame

        # 1. Mirror Mode (Horizontal flip)
        if self.config.mirror_mode:
            out = cv2.flip(out, 1)

        # 2. Brightness & Contrast
        if self.config.brightness != 0 or abs(self.config.contrast - 1.0) > 0.01:
            out = cv2.convertScaleAbs(out, alpha=self.config.contrast, beta=self.config.brightness)

        # 3. Saturation (HSV space)
        if abs(self.config.saturation - 1.0) > 0.01:
            hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * self.config.saturation, 0, 255)
            out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # 4. Grayscale
        if self.config.grayscale or self.config.color_filter == "Noir":
            gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
            if self.config.color_filter == "Noir":
                # High-contrast noir look
                gray = cv2.equalizeHist(gray)
            out = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # 5. Color Filters
        elif self.config.color_filter != "Normal":
            out = self._apply_color_filter(out, self.config.color_filter)

        # 6. Blur
        if self.config.blur_amount > 0:
            k = self.config.blur_amount
            if k % 2 == 0:
                k += 1
            out = cv2.GaussianBlur(out, (k, k), 0)

        # 7. Sharpening
        if self.config.sharpen_amount > 0.01:
            blurred = cv2.GaussianBlur(out, (0, 0), 3)
            out = cv2.addWeighted(out, 1.0 + self.config.sharpen_amount, blurred, -self.config.sharpen_amount, 0)

        # 8. Custom Output Resolution
        if self.config.output_resolution[0] > 0 and self.config.output_resolution[1] > 0:
            target_w, target_h = self.config.output_resolution
            if out.shape[1] != target_w or out.shape[0] != target_h:
                out = cv2.resize(out, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

        return out

    def _apply_color_filter(self, frame: np.ndarray, filter_name: str) -> np.ndarray:
        if filter_name == "Cyberpunk":
            # Boost blues in shadows and pink/magenta in highlights
            b, g, r = cv2.split(frame.astype(np.float32))
            b = np.clip(b * 1.25 + 15, 0, 255)
            r = np.clip(r * 1.15 + 10, 0, 255)
            g = np.clip(g * 0.85, 0, 255)
            return cv2.merge([b, g, r]).astype(np.uint8)

        elif filter_name == "Matrix":
            # Green phosphor matrix glow
            b, g, r = cv2.split(frame.astype(np.float32))
            g = np.clip(g * 1.35 + 20, 0, 255)
            b = np.clip(b * 0.4, 0, 255)
            r = np.clip(r * 0.5, 0, 255)
            return cv2.merge([b, g, r]).astype(np.uint8)

        elif filter_name == "Sepia":
            sepia_matrix = np.array(
                [[0.131, 0.534, 0.272],
                 [0.168, 0.686, 0.349],
                 [0.189, 0.769, 0.393]]
            )
            return np.clip(cv2.transform(frame, sepia_matrix), 0, 255).astype(np.uint8)

        elif filter_name == "Cinema Cool":
            # Teal & Orange Hollywood cinema tone
            b, g, r = cv2.split(frame.astype(np.float32))
            b = np.clip(b * 1.15, 0, 255)
            r = np.clip(r * 1.10, 0, 255)
            g = np.clip(g * 0.95, 0, 255)
            return cv2.merge([b, g, r]).astype(np.uint8)

        elif filter_name == "Warm Sunset":
            b, g, r = cv2.split(frame.astype(np.float32))
            r = np.clip(r * 1.25 + 10, 0, 255)
            g = np.clip(g * 1.05 + 5, 0, 255)
            b = np.clip(b * 0.85, 0, 255)
            return cv2.merge([b, g, r]).astype(np.uint8)

        return frame
