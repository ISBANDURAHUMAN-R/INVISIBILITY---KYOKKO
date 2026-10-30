"""
PROJECT KYOKKO
Background Studio Page
Empty-room background calibration, edge refinement sliders, segmentation model quality, and profile management.
"""

import os
from typing import Optional
import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from core.events import events
from database.db_manager import DatabaseManager
from settings.app_settings import settings
from ui.components.toast import ToastNotification
from ui.components.video_view import VideoView


class BackgroundStudioPage(QWidget):
    capture_instant_requested = Signal()
    countdown_calibration_requested = Signal()
    import_background_requested = Signal(str)
    settings_updated = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(BackgroundStudioPage, self).__init__(parent)
        self.db = DatabaseManager()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Title
        title = QLabel("Background Studio")
        title.setObjectName("Heading1")
        sub = QLabel("Calibrate empty-room backgrounds, refine AI segmentation masks, and manage background profiles")
        sub.setObjectName("Subheading")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Top section: Background Preview + Quick Actions
        preview_row = QHBoxLayout()
        preview_row.setSpacing(16)

        # Left: Background Image Viewport
        bg_card = QFrame()
        bg_card.setObjectName("CardSurface")
        bg_layout = QVBoxLayout(bg_card)
        bg_layout.setContentsMargins(14, 14, 14, 14)
        bg_title = QLabel("ACTIVE CLEAN BACKGROUND PREVIEW")
        bg_title.setObjectName("Heading3")
        bg_layout.addWidget(bg_title)

        self.bg_view = VideoView(self, title="Empty Room Background")
        self.bg_view.setMinimumHeight(280)
        bg_layout.addWidget(self.bg_view)
        preview_row.addWidget(bg_card, 3)

        # Right: Calibration Actions Card
        act_card = QFrame()
        act_card.setObjectName("CardSurface")
        act_layout = QVBoxLayout(act_card)
        act_layout.setContentsMargins(16, 16, 16, 16)
        act_layout.setSpacing(12)

        act_title = QLabel("CALIBRATION ACTIONS")
        act_title.setObjectName("Heading3")
        act_layout.addWidget(act_title)

        btn_countdown = QPushButton("✦ 3-Second Recalibration")
        btn_countdown.clicked.connect(lambda: self.countdown_calibration_requested.emit())
        act_layout.addWidget(btn_countdown)

        btn_instant = QPushButton("Capture Instant Frame")
        btn_instant.setObjectName("SecondaryBtn")
        btn_instant.clicked.connect(lambda: self.capture_instant_requested.emit())
        act_layout.addWidget(btn_instant)

        btn_import = QPushButton("Import Image File...")
        btn_import.setObjectName("SecondaryBtn")
        btn_import.clicked.connect(self._on_import_file)
        act_layout.addWidget(btn_import)

        btn_reset = QPushButton("Reset Background")
        btn_reset.setObjectName("DangerBtn")
        btn_reset.clicked.connect(self._on_reset_bg)
        act_layout.addWidget(btn_reset)

        act_layout.addStretch()

        # Explanatory Callout
        callout = QFrame()
        callout.setStyleSheet("""
            QFrame {
                background-color: #0c0818;
                border-left: 3px solid #00d2ff;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        c_layout = QVBoxLayout(callout)
        c_layout.setContentsMargins(6, 4, 6, 4)
        c_lbl = QLabel("Pro Tip: Step completely out of camera view before capturing to ensure 100% photorealistic invisibility.")
        c_lbl.setStyleSheet("color: #9f97bf; font-size: 11px;")
        c_lbl.setWordWrap(True)
        c_layout.addWidget(c_lbl)
        act_layout.addWidget(callout)

        preview_row.addWidget(act_card, 2)
        layout.addLayout(preview_row)

        # AI Segmentation & Mask Refinement Card
        mask_card = QFrame()
        mask_card.setObjectName("CardSurface")
        mask_layout = QVBoxLayout(mask_card)
        mask_layout.setContentsMargins(20, 18, 20, 18)
        mask_layout.setSpacing(14)

        m_title = QLabel("AI SEGMENTATION & MASK EDGE REFINEMENT")
        m_title.setObjectName("Heading3")
        mask_layout.addWidget(m_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)

        # Model Selection
        model_lbl = QLabel("Segmentation Model Quality")
        model_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.model_combo = QComboBox()
        self.model_combo.addItem("General Model (High Quality, 256x256)", 0)
        self.model_combo.addItem("Landscape Model (Ultra Fast, 144x256)", 1)
        self.model_combo.setCurrentIndex(settings.segmentation_model)
        self.model_combo.currentIndexChanged.connect(self._on_params_changed)
        grid.addWidget(model_lbl, 0, 0)
        grid.addWidget(self.model_combo, 0, 1)

        # Mask Threshold
        thresh_lbl = QLabel("Person Mask Threshold")
        thresh_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.thresh_val_lbl = QLabel(f"{settings.mask_threshold:.2f}")
        self.thresh_val_lbl.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.thresh_slider = QSlider(Qt.Horizontal)
        self.thresh_slider.setRange(20, 90)
        self.thresh_slider.setValue(int(settings.mask_threshold * 100))
        self.thresh_slider.valueChanged.connect(self._on_thresh_changed)

        t_row = QHBoxLayout()
        t_row.addWidget(self.thresh_slider)
        t_row.addWidget(self.thresh_val_lbl)
        grid.addWidget(thresh_lbl, 1, 0)
        grid.addLayout(t_row, 1, 1)

        # Edge Feathering (Gaussian Blur)
        feather_lbl = QLabel("Edge Smoothing / Feathering")
        feather_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.feather_val_lbl = QLabel(f"{settings.mask_feather} px")
        self.feather_val_lbl.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.feather_slider = QSlider(Qt.Horizontal)
        self.feather_slider.setRange(1, 25)
        self.feather_slider.setValue(settings.mask_feather)
        self.feather_slider.valueChanged.connect(self._on_feather_changed)

        f_row = QHBoxLayout()
        f_row.addWidget(self.feather_slider)
        f_row.addWidget(self.feather_val_lbl)
        grid.addWidget(feather_lbl, 2, 0)
        grid.addLayout(f_row, 2, 1)

        # Mask Dilation
        dil_lbl = QLabel("Mask Dilation (Clothing & Hair Coverage)")
        dil_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.dil_val_lbl = QLabel(f"{settings.mask_dilation} px")
        self.dil_val_lbl.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.dil_slider = QSlider(Qt.Horizontal)
        self.dil_slider.setRange(0, 10)
        self.dil_slider.setValue(settings.mask_dilation)
        self.dil_slider.valueChanged.connect(self._on_dil_changed)

        d_row = QHBoxLayout()
        d_row.addWidget(self.dil_slider)
        d_row.addWidget(self.dil_val_lbl)
        grid.addWidget(dil_lbl, 3, 0)
        grid.addLayout(d_row, 3, 1)

        mask_layout.addLayout(grid)
        layout.addWidget(mask_card)

        # Background Profiles Table Card
        prof_card = QFrame()
        prof_card.setObjectName("CardSurface")
        prof_layout = QVBoxLayout(prof_card)
        prof_layout.setContentsMargins(20, 18, 20, 18)
        prof_layout.setSpacing(12)

        prof_title = QLabel("SAVED BACKGROUND PROFILES")
        prof_title.setObjectName("Heading3")
        prof_layout.addWidget(prof_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Resolution", "Created", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(150)
        self.table.cellDoubleClicked.connect(self._on_profile_double_clicked)
        prof_layout.addWidget(self.table)

        layout.addWidget(prof_card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        self.refresh_background_display()
        events.background_calibrated.connect(lambda ok, msg: self.refresh_background_display())

    def _on_thresh_changed(self, val: int):
        f = val / 100.0
        self.thresh_val_lbl.setText(f"{f:.2f}")
        settings.mask_threshold = f
        self.settings_updated.emit()

    def _on_feather_changed(self, val: int):
        k = val if val % 2 == 1 else val + 1
        self.feather_val_lbl.setText(f"{k} px")
        settings.mask_feather = k
        self.settings_updated.emit()

    def _on_dil_changed(self, val: int):
        self.dil_val_lbl.setText(f"{val} px")
        settings.mask_dilation = val
        self.settings_updated.emit()

    def _on_params_changed(self):
        settings.segmentation_model = self.model_combo.currentData()
        self.settings_updated.emit()

    def _on_import_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Background Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path and os.path.exists(path):
            self.import_background_requested.emit(path)

    def _on_reset_bg(self):
        active = self.db.get_active_background_profile()
        if active and active.id:
            self.db.delete_background_profile(active.id)
        self.refresh_background_display()
        self.settings_updated.emit()
        ToastNotification.show_toast(self.window(), "Background Profile Cleared", level="WARNING")

    def refresh_background_display(self):
        active = self.db.get_active_background_profile()
        if active and os.path.exists(active.image_path):
            img = cv2.imread(active.image_path)
            if img is not None:
                self.bg_view.update_frame(img)
                self.bg_view.set_status("Active Background Ready")
        else:
            self.bg_view.update_frame(None)
            self.bg_view.set_status("No clean background calibrated yet.")

        # Refresh table
        profiles = self.db.get_background_profiles()
        self.table.setRowCount(len(profiles))
        for row, p in enumerate(profiles):
            self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(row, 1, QTableWidgetItem(p.name))
            self.table.setItem(row, 2, QTableWidgetItem(f"{p.resolution_w}x{p.resolution_h}"))
            self.table.setItem(row, 3, QTableWidgetItem(p.created_at[:16]))
            self.table.setItem(row, 4, QTableWidgetItem("ACTIVE" if p.is_active else "Saved"))

    def _on_profile_double_clicked(self, row: int, col: int):
        id_item = self.table.item(row, 0)
        if id_item:
            prof_id = int(id_item.text())
            self.db.set_active_background_profile(prof_id)
            self.refresh_background_display()
            self.settings_updated.emit()
            ToastNotification.show_toast(self.window(), "Active Background Updated", level="SUCCESS")
