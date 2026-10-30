"""
PROJECT KYOKKO
Navigation Sidebar Widget
Cinematic glowing navigation bar with page switching and branding.
"""

from typing import List, Optional
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NavButton(QPushButton):
    def __init__(self, text: str, index: int, parent: Optional[QWidget] = None):
        super(NavButton, self).__init__(text, parent)
        self.index = index
        self._is_active = False
        self.setCheckable(False)
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def set_active(self, active: bool):
        self._is_active = active
        self.update_style()

    def update_style(self):
        if self._is_active:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #251b4b, stop:1 #17112e);
                    color: #ffffff;
                    border: none;
                    border-left: 3px solid #9d4edd;
                    border-radius: 0px 8px 8px 0px;
                    text-align: left;
                    padding-left: 18px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #9f97bf;
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px 8px 8px 0px;
                    text-align: left;
                    padding-left: 18px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #150f29;
                    color: #f8f7fc;
                    border-left: 3px solid #3d2b70;
                }
            """)


class Sidebar(QFrame):
    page_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super(Sidebar, self).__init__(parent)
        self.setFixedWidth(230)
        self.setStyleSheet("""
            QFrame {
                background-color: #0c0818;
                border-right: 1px solid #1f1638;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(6)

        # Brand Header
        brand_box = QHBoxLayout()
        brand_box.setSpacing(10)

        logo_glyph = QLabel("✦")
        logo_glyph.setStyleSheet("color: #9d4edd; font-size: 24px; font-weight: bold;")
        brand_box.addWidget(logo_glyph)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        app_title = QLabel("KYOKKO")
        app_title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 800; letter-spacing: 2px;")
        app_sub = QLabel("INVISIBILITY CAM")
        app_sub.setStyleSheet("color: #00d2ff; font-size: 9px; font-weight: 700; letter-spacing: 1px;")
        title_col.addWidget(app_title)
        title_col.addWidget(app_sub)
        brand_box.addLayout(title_col)
        brand_box.addStretch()

        layout.addLayout(brand_box)
        layout.addSpacing(20)

        # Nav items
        self.nav_items = [
            ("Dashboard", 0),
            ("Camera Studio", 1),
            ("Gesture Controls", 2),
            ("Background Studio", 3),
            ("Effects", 4),
            ("Device Manager", 5),
            ("Settings", 6),
            ("About KYOKKO", 7),
        ]

        self.buttons: List[NavButton] = []
        for text, idx in self.nav_items:
            btn = NavButton(text, idx, self)
            btn.clicked.connect(lambda checked=False, i=idx: self.select_page(i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # Bottom Status / Version Badge
        status_box = QFrame()
        status_box.setStyleSheet("""
            QFrame {
                background-color: #120d24;
                border: 1px solid #271b4a;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        s_layout = QVBoxLayout(status_box)
        s_layout.setContentsMargins(8, 8, 8, 8)
        s_layout.setSpacing(2)

        ver_lbl = QLabel("KYOKKO v1.0.0")
        ver_lbl.setStyleSheet("color: #c77dff; font-size: 11px; font-weight: 600;")
        engine_lbl = QLabel("MediaPipe AI Core")
        engine_lbl.setStyleSheet("color: #635b80; font-size: 10px;")
        s_layout.addWidget(ver_lbl)
        s_layout.addWidget(engine_lbl)

        layout.addWidget(status_box)

        # Select Dashboard by default
        self.select_page(0)

    def select_page(self, index: int):
        for btn in self.buttons:
            btn.set_active(btn.index == index)
        self.page_changed.emit(index)
