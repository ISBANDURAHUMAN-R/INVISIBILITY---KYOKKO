"""
PROJECT KYOKKO
Camera Studio Page
Side-by-side comparison of raw camera input vs final virtual cam feed, resolution/FPS configuration, and HUD overlays.
"""

from typing import Optional
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from core.events import events
from settings.app_settings import settings
from ui.components.video_view import VideoView
from utils.system_info import STANDARD_RESOLUTIONS


class CameraStudioPage(QWidget):
    camera_settings_changed = Signal(int, int, int) # w, h, fps
    overlays_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(CameraStudioPage, self).__init__(parent)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Camera Studio")
        title.setObjectName("Heading1")
        sub = QLabel("Direct sensor feed inspection, resolution switching, and visual telemetry overlays")
        sub.setObjectName("Subheading")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Side-by-Side Video Viewports
        dual_view_row = QHBoxLayout()
        dual_view_row.setSpacing(16)

        # Left: Raw Physical Camera
        raw_box = QFrame()
        raw_box.setObjectName("CardSurface")
        raw_layout = QVBoxLayout(raw_box)
        raw_layout.setContentsMargins(12, 12, 12, 12)
        raw_lbl = QLabel("RAW CAMERA SENSOR (PHYSICAL INPUT)")
        raw_lbl.setObjectName("Heading3")
        raw_layout.addWidget(raw_lbl)

        self.raw_view = VideoView(self, title="Raw Input Feed")
        self.raw_view.setMinimumHeight(320)
        raw_layout.addWidget(self.raw_view)
        dual_view_row.addWidget(raw_box, 1)

        # Right: Final Processed Virtual Camera Feed
        proc_box = QFrame()
        proc_box.setObjectName("CardSurface")
        proc_layout = QVBoxLayout(proc_box)
        proc_layout.setContentsMargins(12, 12, 12, 12)
        proc_lbl = QLabel("PROCESSED VIRTUAL CAMERA OUTPUT (BROADCAST)")
        proc_lbl.setObjectName("Heading3")
        proc_layout.addWidget(proc_lbl)

        self.proc_view = VideoView(self, title="Processed Output Feed")
        self.proc_view.setMinimumHeight(320)
        proc_layout.addWidget(self.proc_view)
        dual_view_row.addWidget(proc_box, 1)

        layout.addLayout(dual_view_row)

        # Controls & Overlays Panel
        ctrl_card = QFrame()
        ctrl_card.setObjectName("CardSurface")
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(20, 16, 20, 16)
        ctrl_layout.setSpacing(14)

        panel_title = QLabel("CAMERA FORMAT & OVERLAY CONTROLS")
        panel_title.setObjectName("Heading3")
        ctrl_layout.addWidget(panel_title)

        # Dropdowns row
        dropdown_row = QHBoxLayout()
        dropdown_row.setSpacing(16)

        # Resolution dropdown
        res_col = QVBoxLayout()
        res_col.setSpacing(4)
        res_lbl = QLabel("Resolution")
        res_lbl.setStyleSheet("color: #9f97bf; font-weight: 600;")
        self.res_combo = QComboBox()
        for w, h, label in STANDARD_RESOLUTIONS:
            self.res_combo.addItem(f"{label} - {w}x{h}", (w, h))

        # Select current
        cur_w, cur_h = settings.resolution_w, settings.resolution_h
        for i in range(self.res_combo.count()):
            cw, ch = self.res_combo.itemData(i)
            if cw == cur_w and ch == cur_h:
                self.res_combo.setCurrentIndex(i)
                break

        self.res_combo.currentIndexChanged.connect(self._on_format_changed)
        res_col.addWidget(res_lbl)
        res_col.addWidget(self.res_combo)
        dropdown_row.addLayout(res_col)

        # FPS dropdown
        fps_col = QVBoxLayout()
        fps_col.setSpacing(4)
        fps_lbl = QLabel("Target FPS")
        fps_lbl.setStyleSheet("color: #9f97bf; font-weight: 600;")
        self.fps_combo = QComboBox()
        for f in [60, 30, 24, 15]:
            self.fps_combo.addItem(f"{f} FPS", f)

        for i in range(self.fps_combo.count()):
            if self.fps_combo.itemData(i) == settings.fps:
                self.fps_combo.setCurrentIndex(i)
                break

        self.fps_combo.currentIndexChanged.connect(self._on_format_changed)
        fps_col.addWidget(fps_lbl)
        fps_col.addWidget(self.fps_combo)
        dropdown_row.addLayout(fps_col)

        dropdown_row.addStretch()
        ctrl_layout.addLayout(dropdown_row)

        # Checkboxes row
        chk_row = QHBoxLayout()
        chk_row.setSpacing(24)

        self.chk_landmarks = QCheckBox("Show AI Landmarks Overlay")
        self.chk_landmarks.setChecked(settings.show_landmarks)
        self.chk_landmarks.toggled.connect(self._on_overlay_toggled)
        chk_row.addWidget(self.chk_landmarks)

        self.chk_mask = QCheckBox("Show Person Segmentation Silhouette")
        self.chk_mask.setChecked(settings.show_mask_overlay)
        self.chk_mask.toggled.connect(self._on_overlay_toggled)
        chk_row.addWidget(self.chk_mask)

        self.chk_hud = QCheckBox("Show HUD Status Pill")
        self.chk_hud.setChecked(settings.show_hud)
        self.chk_hud.toggled.connect(self._on_overlay_toggled)
        chk_row.addWidget(self.chk_hud)

        self.chk_mirror = QCheckBox("Mirror Video (Horizontal Flip)")
        self.chk_mirror.setChecked(settings.mirror_mode)
        self.chk_mirror.toggled.connect(self._on_overlay_toggled)
        chk_row.addWidget(self.chk_mirror)

        chk_row.addStretch()
        ctrl_layout.addLayout(chk_row)

        layout.addWidget(ctrl_card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        events.frame_ready.connect(self._on_frame_ready)

    def _on_format_changed(self):
        w, h = self.res_combo.currentData()
        fps = self.fps_combo.currentData()
        settings.resolution_w = w
        settings.resolution_h = h
        settings.fps = fps
        self.camera_settings_changed.emit(w, h, fps)

    def _on_overlay_toggled(self):
        settings.show_landmarks = self.chk_landmarks.isChecked()
        settings.show_mask_overlay = self.chk_mask.isChecked()
        settings.show_hud = self.chk_hud.isChecked()
        settings.mirror_mode = self.chk_mirror.isChecked()
        self.overlays_changed.emit()

    def _on_frame_ready(self, raw_frame: np.ndarray, proc_frame: np.ndarray):
        self.raw_view.update_frame(raw_frame)
        self.proc_view.update_frame(proc_frame)
