"""
PROJECT KYOKKO
Toast Notification Component
Non-intrusive floating status alerts for calibration, errors, and system events.
"""

from typing import Optional
from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget


class ToastNotification(QFrame):
    def __init__(self, message: str, level: str = "INFO", duration_ms: int = 3000, parent: Optional[QWidget] = None):
        super(ToastNotification, self).__init__(parent)
        self.duration_ms = duration_ms

        color_map = {
            "INFO": ("#9d4edd", "#251b4b"),
            "SUCCESS": ("#00f59b", "#052e1f"),
            "WARNING": ("#ffb703", "#3a2503"),
            "ERROR": ("#ff0055", "#380614"),
        }
        border_col, bg_col = color_map.get(level.upper(), ("#9d4edd", "#251b4b"))

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 8px;
                padding: 6px 14px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        icon_lbl = QLabel("✦" if level != "ERROR" else "⚠")
        icon_lbl.setStyleSheet(f"color: {border_col}; font-size: 14px; font-weight: bold;")
        layout.addWidget(icon_lbl)

        text_lbl = QLabel(message)
        text_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600;")
        layout.addWidget(text_lbl)

        self.adjustSize()

        # Fade out timer
        QTimer.singleShot(duration_ms, self.close)

    @classmethod
    def show_toast(cls, parent: QWidget, message: str, level: str = "INFO", duration_ms: int = 3000):
        toast = cls(message, level=level, duration_ms=duration_ms, parent=parent)
        # Position top-center of parent window
        pw = parent.width()
        tw = toast.width()
        toast.move((pw - tw) // 2, 24)
        toast.show()
        toast.raise_()
