"""
PROJECT KYOKKO
Interactive Gesture Meter Component
Dynamic visual gauge displaying hand-to-head proximity, threshold boundary, and hold progress.
"""

from typing import Optional
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
from vision.gesture_recognition import GestureStateName, GestureStatus


class GestureMeter(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super(GestureMeter, self).__init__(parent)
        self.setObjectName("CardSurface")
        self.setFixedHeight(110)

        self._normalized_distance: float = 1.0
        self._sensitivity: float = 0.45
        self._progress: float = 0.0
        self._state: str = "IDLE"
        self._confidence: float = 0.0
        self._active_hand: str = "None"

    def update_status(self, status: GestureStatus, sensitivity: float = 0.45):
        self._normalized_distance = status.normalized_distance
        self._sensitivity = sensitivity
        self._progress = status.progress
        self._state = status.state.value
        self._confidence = status.confidence
        self._active_hand = status.active_hand
        self.update()

    def paintEvent(self, event: QPaintEvent):
        super(GestureMeter, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Labels Header
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.setPen(QColor("#c77dff"))
        painter.drawText(16, 26, "GESTURE PROXIMITY & CONFIRMATION GAUGE")

        # State pill in top right
        state_color = QColor("#635b80")
        if self._state == "ACTIVE":
            state_color = QColor("#00f59b")  # Green
        elif self._state == "CONFIRMING":
            state_color = QColor("#ffb703")  # Gold
        elif self._state == "RELEASING":
            state_color = QColor("#00d2ff")  # Cyan

        pill_text = f"STATE: {self._state}"
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(state_color)
        painter.drawText(w - 150, 26, 134, 20, Qt.AlignRight, pill_text)

        # Proximity Track
        bar_x = 16
        bar_y = 44
        bar_w = w - 32
        bar_h = 16

        # Track background
        painter.setBrush(QColor("#0a0714"))
        painter.setPen(QPen(QColor("#271b4a"), 1))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 8, 8)

        # Active Fill: Distance representation (1.0 = far, 0.0 = touching)
        # We fill from right to left or show distance inversely so closer fills up
        proximity_factor = max(0.0, min(1.0, 1.0 - (self._normalized_distance / 1.0)))
        fill_w = int(bar_w * proximity_factor)

        if fill_w > 0:
            grad = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
            grad.setColorAt(0.0, QColor("#7b2cbf"))
            grad.setColorAt(1.0, QColor("#00d2ff") if self._state != "ACTIVE" else QColor("#00f59b"))

            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 8, 8)

        # Draw Sensitivity Threshold Marker Line
        thresh_pos = int(bar_w * (1.0 - self._sensitivity))
        marker_x = bar_x + thresh_pos
        painter.setPen(QPen(QColor("#ff0055"), 2))
        painter.drawLine(marker_x, bar_y - 3, marker_x, bar_y + bar_h + 3)

        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.setPen(QColor("#ff4d88"))
        painter.drawText(marker_x - 35, bar_y + bar_h + 16, "TRIGGER ZONE")

        # Bottom info row
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor("#9f97bf"))
        info_text = f"Distance: {self._normalized_distance:.2f}  |  Confidence: {int(self._confidence * 100)}%  |  Hand: {self._active_hand}"
        painter.drawText(bar_x, bar_y + bar_h + 28, info_text)

        # Hold Progress indicator
        if self._progress > 0.0:
            prog_text = f"Hold: {int(self._progress * 100)}%"
            painter.setPen(state_color)
            painter.drawText(w - 120, bar_y + bar_h + 28, 104, 20, Qt.AlignRight, prog_text)
