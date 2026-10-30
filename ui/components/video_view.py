"""
PROJECT KYOKKO
High-Performance Video Viewport Widget
Maintains proper aspect ratio, smooth rendering, and status overlay graphics.
"""

from typing import Optional
import cv2
import numpy as np
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget
from utils.image_utils import cv_frame_to_qimage


class VideoView(QWidget):
    def __init__(self, parent: Optional[QWidget] = None, title: str = "Live Feed"):
        super(VideoView, self).__init__(parent)
        self.title = title
        self._current_qimage: Optional[QImage] = None
        self._is_active: bool = False
        self._status_text: str = "Connecting to camera..."

        self.setMinimumSize(320, 180)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

    def update_frame(self, frame_bgr: Optional[np.ndarray]) -> None:
        if frame_bgr is None or frame_bgr.size == 0:
            self._current_qimage = None
            self._is_active = False
        else:
            self._current_qimage = cv_frame_to_qimage(frame_bgr)
            self._is_active = True
        self.update()

    def set_status(self, text: str) -> None:
        self._status_text = text
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # Background fill
        painter.fillRect(0, 0, w, h, QColor("#08060f"))

        if self._is_active and self._current_qimage is not None and not self._current_qimage.isNull():
            img_w = self._current_qimage.width()
            img_h = self._current_qimage.height()

            # Aspect ratio fit (letterboxing)
            scale = min(w / img_w, h / img_h)
            draw_w = int(img_w * scale)
            draw_h = int(img_h * scale)
            draw_x = (w - draw_w) // 2
            draw_y = (h - draw_h) // 2

            target_rect = QRect(draw_x, draw_y, draw_w, draw_h)
            painter.drawImage(target_rect, self._current_qimage)

            # Elegant border around video viewport
            painter.setPen(QPen(QColor("#271b4a"), 1))
            painter.drawRect(target_rect)
        else:
            # Standby screen
            painter.setPen(QPen(QColor("#1a142e"), 2, Qt.DashLine))
            painter.drawRoundedRect(10, 10, w - 20, h - 20, 12, 12)

            painter.setPen(QPen(QColor("#9d4edd")))
            painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
            painter.drawText(QRect(0, h // 2 - 25, w, 30), Qt.AlignCenter, "KYOKKO CAMERA STUDIO")

            painter.setPen(QPen(QColor("#635b80")))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(QRect(0, h // 2 + 10, w, 25), Qt.AlignCenter, self._status_text)
