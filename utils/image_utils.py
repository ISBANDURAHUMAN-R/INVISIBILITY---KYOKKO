"""
PROJECT KYOKKO
Image Utilities
Color conversions, Qt Image conversions, and spatial transforms.
"""

from typing import Tuple
import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap


def cv_frame_to_qimage(frame: np.ndarray) -> QImage:
    """Convert an OpenCV BGR numpy array to QImage."""
    if frame is None or frame.size == 0:
        return QImage()

    if len(frame.shape) == 2:  # Grayscale
        h, w = frame.shape
        bytes_per_line = w
        return QImage(frame.data, w, h, bytes_per_line, QImage.Format_Grayscale8).copy()

    h, w, ch = frame.shape
    bytes_per_line = ch * w
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()


def cv_frame_to_qpixmap(frame: np.ndarray) -> QPixmap:
    """Convert an OpenCV BGR numpy array to QPixmap."""
    qimg = cv_frame_to_qimage(frame)
    return QPixmap.fromImage(qimg)


def resize_and_pad(
    frame: np.ndarray, target_w: int, target_h: int, pad_color: Tuple[int, int, int] = (15, 10, 25)
) -> np.ndarray:
    """Resize image preserving aspect ratio with letterboxing/pillarboxing."""
    h, w = frame.shape[:2]
    if w == target_w and h == target_h:
        return frame

    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    pad_top = (target_h - new_h) // 2
    pad_bottom = target_h - new_h - pad_top
    pad_left = (target_w - new_w) // 2
    pad_right = target_w - new_w - pad_left

    padded = cv2.copyMakeBorder(
        resized,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        cv2.BORDER_CONSTANT,
        value=pad_color,
    )
    return padded
