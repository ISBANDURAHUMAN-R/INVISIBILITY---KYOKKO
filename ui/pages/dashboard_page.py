"""
PROJECT KYOKKO
Dashboard Page
Mission control center with live preview, telemetry stats, master invisibility switch, and quick calibration.
"""

from typing import Optional
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from core.events import events
from core.worker import CalibrationCountdownWorker
from ui.components.gesture_meter import GestureMeter
from ui.components.stat_card import StatCard
from ui.components.toast import ToastNotification
from ui.components.video_view import VideoView
from vision.gesture_recognition import GestureStatus


class DashboardPage(QWidget):
    start_virtual_cam_requested = Signal()
    stop_virtual_cam_requested = Signal()
    calibrate_bg_requested = Signal()
    toggle_manual_invisibility = Signal(object) # None = auto, True = force invis, False = force visible

    def __init__(self, parent: Optional[QWidget] = None):
        super(DashboardPage, self).__init__(parent)
        self._countdown_worker: Optional[CalibrationCountdownWorker] = None
        self._manual_state: Optional[bool] = None # None = auto

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header Title Row
        header_row = QHBoxLayout()
        header_col = QVBoxLayout()
        header_col.setSpacing(2)

        title = QLabel("Dashboard")
        title.setObjectName("Heading1")
        sub = QLabel("Gesture-controlled invisibility virtual camera studio")
        sub.setObjectName("Subheading")
        header_col.addWidget(title)
        header_col.addWidget(sub)
        header_row.addLayout(header_col)
        header_row.addStretch()

        # Master Invisibility Toggle Button
        self.master_toggle_btn = QPushButton("Auto Gesture Mode")
        self.master_toggle_btn.setFixedWidth(180)
        self.master_toggle_btn.clicked.connect(self._cycle_master_invisibility)
        header_row.addWidget(self.master_toggle_btn)

        # Emergency Cut Button
        self.emergency_btn = QPushButton("Emergency Kill")
        self.emergency_btn.setObjectName("DangerBtn")
        self.emergency_btn.setFixedWidth(140)
        self.emergency_btn.clicked.connect(self._on_emergency_cut)
        header_row.addWidget(self.emergency_btn)

        layout.addLayout(header_row)

        # Telemetry Stat Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self.card_fps = StatCard("Pipeline FPS", "30.0", "FPS", "Real-Time 30 FPS", "#9d4edd")
        self.card_latency = StatCard("Latency", "12.4", "ms", "Ultra-Low Latency", "#00d2ff")
        self.card_gesture = StatCard("Gesture", "IDLE", "", "Awaiting Touch", "#c77dff")
        self.card_vcam = StatCard("Virtual Cam", "STOPPED", "", "DirectShow Driver", "#ff4d88")

        stats_row.addWidget(self.card_fps)
        stats_row.addWidget(self.card_latency)
        stats_row.addWidget(self.card_gesture)
        stats_row.addWidget(self.card_vcam)
        layout.addLayout(stats_row)

        # Live Video Preview
        self.video_view = VideoView(self, title="Live Virtual Camera Feed")
        self.video_view.setMinimumHeight(440)
        layout.addWidget(self.video_view)

        # Interactive Gesture Proximity Meter
        self.gesture_meter = GestureMeter(self)
        layout.addWidget(self.gesture_meter)

        # Action Quick Controls Row
        action_bar = QFrame()
        action_bar.setObjectName("CardSurface")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(14)

        # Calibration button
        self.calibrate_btn = QPushButton("✦ Quick Calibration (3s)")
        self.calibrate_btn.clicked.connect(self._start_countdown_calibration)
        action_layout.addWidget(self.calibrate_btn)

        # Virtual Cam Start/Stop
        self.vcam_toggle_btn = QPushButton("Start Virtual Camera")
        self.vcam_toggle_btn.setObjectName("SecondaryBtn")
        self.vcam_toggle_btn.clicked.connect(self._toggle_virtual_cam)
        action_layout.addWidget(self.vcam_toggle_btn)

        action_layout.addStretch()

        # Quick calibration helper label
        self.calib_hint = QLabel("Step out of camera view before calibrating empty room.")
        self.calib_hint.setObjectName("MutedLabel")
        action_layout.addWidget(self.calib_hint)

        layout.addWidget(action_bar)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Connect pipeline event signals
        events.frame_ready.connect(self._on_frame_ready)
        events.gesture_updated.connect(self._on_gesture_updated)
        events.stats_updated.connect(self._on_stats_updated)
        events.background_calibrated.connect(self._on_bg_calibrated)
        events.virtual_cam_state_changed.connect(self._on_vcam_state_changed)

    def _cycle_master_invisibility(self):
        # Cycles: None (Auto) -> True (Force Invisible) -> False (Force Visible) -> None (Auto)
        if self._manual_state is None:
            self._manual_state = True
            self.master_toggle_btn.setText("Force INVISIBLE (Manual)")
            self.master_toggle_btn.setObjectName("SuccessBtn")
            self.master_toggle_btn.setStyle(self.master_toggle_btn.style())
        elif self._manual_state is True:
            self._manual_state = False
            self.master_toggle_btn.setText("Force VISIBLE (Manual)")
            self.master_toggle_btn.setObjectName("SecondaryBtn")
            self.master_toggle_btn.setStyle(self.master_toggle_btn.style())
        else:
            self._manual_state = None
            self.master_toggle_btn.setText("Auto Gesture Mode")
            self.master_toggle_btn.setObjectName("")
            self.master_toggle_btn.setStyle(self.master_toggle_btn.style())

        self.toggle_manual_invisibility.emit(self._manual_state)

    def _start_countdown_calibration(self):
        if self._countdown_worker and self._countdown_worker.isRunning():
            return

        self.calibrate_btn.setEnabled(False)
        self.calib_hint.setText("Calibrating in 3 seconds... Step away from camera!")
        self.calib_hint.setStyleSheet("color: #00d2ff; font-weight: bold;")

        self._countdown_worker = CalibrationCountdownWorker(seconds=3)
        self._countdown_worker.tick.connect(self._on_countdown_tick)
        self._countdown_worker.capture.connect(lambda: self.calibrate_bg_requested.emit())
        self._countdown_worker.finished_countdown.connect(self._on_countdown_finished)
        self._countdown_worker.start()

    def _on_countdown_tick(self, sec: int):
        if sec > 0:
            self.calibrate_btn.setText(f"Calibrating in {sec}s...")
            self.calib_hint.setText(f"Get ready! Room will be captured in {sec} second(s)...")
        else:
            self.calibrate_btn.setText("Capturing frames...")
            self.calib_hint.setText("Capturing empty room background frames...")

    def _on_countdown_finished(self):
        self.calibrate_btn.setEnabled(True)
        self.calibrate_btn.setText("✦ Quick Calibration (3s)")
        self.calib_hint.setText("Calibration complete.")
        self.calib_hint.setStyleSheet("color: #635b80;")

    def _toggle_virtual_cam(self):
        if self.card_vcam.value_lbl.text() == "STREAMING":
            self.stop_virtual_cam_requested.emit()
        else:
            self.start_virtual_cam_requested.emit()

    def _on_emergency_cut(self):
        self.stop_virtual_cam_requested.emit()
        self.toggle_manual_invisibility.emit(False)
        self._manual_state = False
        self.master_toggle_btn.setText("Force VISIBLE (Cut)")
        ToastNotification.show_toast(self.window(), "EMERGENCY CAMERA CUT EXECUTED", level="ERROR")

    def _on_frame_ready(self, raw_frame: np.ndarray, display_frame: np.ndarray):
        self.video_view.update_frame(display_frame)

    def _on_gesture_updated(self, status: GestureStatus):
        self.gesture_meter.update_status(status)

    def _on_stats_updated(self, stats: dict):
        self.card_fps.set_value(f"{stats.get('pipeline_fps', 30.0):.1f}")
        self.card_latency.set_value(f"{stats.get('latency_ms', 0.0):.1f}")

        g_state = stats.get("gesture_state", "IDLE")
        self.card_gesture.set_value(g_state)
        if g_state == "ACTIVE":
            self.card_gesture.set_accent_color("#00f59b")
        elif g_state == "CONFIRMING":
            self.card_gesture.set_accent_color("#ffb703")
        else:
            self.card_gesture.set_accent_color("#c77dff")

        is_vcam = stats.get("virtual_cam_active", False)
        if is_vcam:
            self.card_vcam.set_value("STREAMING")
            self.card_vcam.set_accent_color("#00f59b")
            self.vcam_toggle_btn.setText("Stop Virtual Camera")
            self.vcam_toggle_btn.setObjectName("DangerBtn")
        else:
            self.card_vcam.set_value("STOPPED")
            self.card_vcam.set_accent_color("#ff4d88")
            self.vcam_toggle_btn.setText("Start Virtual Camera")
            self.vcam_toggle_btn.setObjectName("SecondaryBtn")
        self.vcam_toggle_btn.setStyle(self.vcam_toggle_btn.style())

    def _on_bg_calibrated(self, success: bool, message: str):
        level = "SUCCESS" if success else "ERROR"
        ToastNotification.show_toast(self.window(), message, level=level)

    def _on_vcam_state_changed(self, is_running: bool, device: str):
        if is_running:
            ToastNotification.show_toast(self.window(), f"Virtual Camera Live: {device}", level="SUCCESS")
        else:
            ToastNotification.show_toast(self.window(), "Virtual Camera Stopped", level="INFO")
