"""
PROJECT KYOKKO
Stat Card Component
Telemetry display widget for FPS, latency, gesture confidence, and camera status.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StatCard(QFrame):
    def __init__(
        self,
        title: str,
        initial_value: str = "--",
        unit: str = "",
        subtitle: str = "",
        accent_color: str = "#9d4edd",
        parent: Optional[QWidget] = None,
    ):
        super(StatCard, self).__init__(parent)
        self.setObjectName("CardSurface")
        self.accent_color = accent_color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        # Header row: Title + Accent dot
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {accent_color}; font-size: 10px;")
        header_row.addWidget(dot)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet("color: #9f97bf; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        header_row.addWidget(self.title_lbl)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Value row
        val_row = QHBoxLayout()
        val_row.setSpacing(4)
        self.value_lbl = QLabel(initial_value)
        self.value_lbl.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 700;")
        val_row.addWidget(self.value_lbl)

        if unit:
            self.unit_lbl = QLabel(unit)
            self.unit_lbl.setStyleSheet("color: #9f97bf; font-size: 13px; font-weight: 500; margin-bottom: 2px;")
            self.unit_lbl.setAlignment(Qt.AlignBottom)
            val_row.addWidget(self.unit_lbl)

        val_row.addStretch()
        layout.addLayout(val_row)

        # Subtitle
        if subtitle:
            self.sub_lbl = QLabel(subtitle)
            self.sub_lbl.setStyleSheet("color: #635b80; font-size: 11px;")
            layout.addWidget(self.sub_lbl)
        else:
            self.sub_lbl = None

    def set_value(self, val: str, subtitle: Optional[str] = None) -> None:
        self.value_lbl.setText(val)
        if subtitle is not None and self.sub_lbl is not None:
            self.sub_lbl.setText(subtitle)

    def set_accent_color(self, color: str) -> None:
        self.accent_color = color
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700;")
