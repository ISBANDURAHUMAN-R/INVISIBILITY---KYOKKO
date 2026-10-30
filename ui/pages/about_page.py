"""
PROJECT KYOKKO
About Page
Brand identity, architecture overview, gesture usage guide, and technology stack.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class AboutPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super(AboutPage, self).__init__(parent)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Hero Banner
        hero = QFrame()
        hero.setObjectName("CardSurface")
        hero.setStyleSheet("""
            QFrame#CardSurface {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a0f38, stop:1 #0c0818);
                border: 1px solid #7b2cbf;
                border-radius: 12px;
                padding: 24px;
            }
        """)
        h_layout = QVBoxLayout(hero)
        h_layout.setSpacing(8)

        hero_badge = QLabel("PROJECT KYOKKO  •  VERSION 1.0.0")
        hero_badge.setStyleSheet("color: #00d2ff; font-weight: 700; letter-spacing: 2px; font-size: 11px;")
        h_layout.addWidget(hero_badge)

        hero_title = QLabel("Gesture-Controlled Invisibility Virtual Camera")
        hero_title.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: 800;")
        h_layout.addWidget(hero_title)

        hero_desc = QLabel(
            "KYOKKO is a state-of-the-art Windows desktop application engineered for seamless, "
            "cinematic person invisibility during video conferences and live streaming. "
            "Simply touch your head to dissolve completely from the webcam feed, and release your hand to reappear."
        )
        hero_desc.setStyleSheet("color: #9f97bf; font-size: 14px; line-height: 1.5;")
        hero_desc.setWordWrap(True)
        h_layout.addWidget(hero_desc)

        layout.addWidget(hero)

        # Quick How-It-Works Card
        guide_card = QFrame()
        guide_card.setObjectName("CardSurface")
        g_layout = QVBoxLayout(guide_card)
        g_layout.setContentsMargins(20, 18, 20, 18)
        g_layout.setSpacing(12)

        g_title = QLabel("HOW TO USE KYOKKO")
        g_title.setObjectName("Heading3")
        g_layout.addWidget(g_title)

        steps = [
            ("1. Calibrate Background", "Click 'Quick Calibration (3s)' and step out of frame. KYOKKO captures a clean, multi-frame denoised image of your empty room."),
            ("2. Start Virtual Camera", "Click 'Start Virtual Camera'. KYOKKO begins streaming the composite feed to DirectShow (OBS Virtual Camera device)."),
            ("3. Connect Meeting App", "In Zoom, Google Meet, Microsoft Teams, or Discord, switch your video input from your physical webcam to 'OBS Virtual Camera'."),
            ("4. Execute Invisibility Gesture", "Raise your hand and touch your temple, forehead, or ear. Your entire body immediately dissolves into the background."),
            ("5. Reappear Naturally", "Lower your hand back down. Your camera feed smoothly restores without any glitch, stutter, or frame freezing."),
        ]

        for step_title, step_desc in steps:
            row = QVBoxLayout()
            row.setSpacing(2)
            st = QLabel(step_title)
            st.setStyleSheet("color: #c77dff; font-weight: bold; font-size: 13px;")
            sd = QLabel(step_desc)
            sd.setStyleSheet("color: #9f97bf; font-size: 12px;")
            sd.setWordWrap(True)
            row.addWidget(st)
            row.addWidget(sd)
            g_layout.addLayout(row)
            g_layout.addSpacing(4)

        layout.addWidget(guide_card)

        # Technology Stack Card
        tech_card = QFrame()
        tech_card.setObjectName("CardSurface")
        t_layout = QVBoxLayout(tech_card)
        t_layout.setContentsMargins(20, 18, 20, 18)
        t_layout.setSpacing(10)

        t_title = QLabel("CORE TECHNOLOGY ARCHITECTURE")
        t_title.setObjectName("Heading3")
        t_layout.addWidget(t_title)

        tech_items = [
            ("Python 3.12 Engine", "High-performance asynchronous execution pipeline and thread synchronization."),
            ("OpenCV 4", "Low-latency frame capture, color adjustments, image feathering, and morphological dilation."),
            ("MediaPipe AI Core", "Neural networks for real-time 3D hand tracking, face/head localization, and full-body person segmentation."),
            ("PySide6 (Qt for Python)", "Hardware-accelerated native Windows GUI with obsidian and purple cinematic styling."),
            ("pyvirtualcam & DirectShow", "Kernel-level video streaming compatible with Zoom, Meet, Teams, and Discord."),
            ("SQLite 3 Database", "Thread-safe persistence for user settings, camera profiles, and background calibrations."),
        ]

        for name, desc in tech_items:
            t_row = QHBoxLayout()
            n_lbl = QLabel(f"• {name}:")
            n_lbl.setStyleSheet("color: #ffffff; font-weight: 600; font-size: 12px;")
            n_lbl.setFixedWidth(200)
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet("color: #9f97bf; font-size: 12px;")
            t_row.addWidget(n_lbl)
            t_row.addWidget(d_lbl)
            t_row.addStretch()
            t_layout.addLayout(t_row)

        layout.addWidget(tech_card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
