"""
PROJECT KYOKKO
Main Application Window
Master orchestrator connecting the navigation sidebar, stacked pages, and ProcessingPipeline thread.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from core.events import events
from core.pipeline import ProcessingPipeline
from services.logger_service import logger
from settings.app_settings import settings
from ui.components.sidebar import Sidebar
from ui.components.toast import ToastNotification
from ui.pages import (
    AboutPage,
    BackgroundStudioPage,
    CameraStudioPage,
    DashboardPage,
    DeviceManagerPage,
    EffectsPage,
    GestureControlsPage,
    SettingsPage,
)
from ui.themes import load_stylesheet


class MainWindow(QMainWindow):
    def __init__(self, pipeline: Optional[ProcessingPipeline] = None):
        super(MainWindow, self).__init__()
        self.pipeline = pipeline or ProcessingPipeline()

        self.setWindowTitle("KYOKKO - Gesture-Controlled Invisibility Virtual Camera")
        self.resize(1240, 800)
        self.setMinimumSize(960, 600)

        # Apply QSS stylesheet
        self.setStyleSheet(load_stylesheet())

        # Central Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.page_changed.connect(self._on_page_changed)
        main_layout.addWidget(self.sidebar)

        # Stacked Pages
        self.stack = QStackedWidget(self)

        self.page_dashboard = DashboardPage(self)
        self.page_camera = CameraStudioPage(self)
        self.page_gesture = GestureControlsPage(self)
        self.page_bg = BackgroundStudioPage(self)
        self.page_effects = EffectsPage(self)
        self.page_device = DeviceManagerPage(self)
        self.page_settings = SettingsPage(self)
        self.page_about = AboutPage(self)

        self.stack.addWidget(self.page_dashboard)  # Index 0
        self.stack.addWidget(self.page_camera)     # Index 1
        self.stack.addWidget(self.page_gesture)    # Index 2
        self.stack.addWidget(self.page_bg)         # Index 3
        self.stack.addWidget(self.page_effects)    # Index 4
        self.stack.addWidget(self.page_device)     # Index 5
        self.stack.addWidget(self.page_settings)   # Index 6
        self.stack.addWidget(self.page_about)      # Index 7

        main_layout.addWidget(self.stack, 1)

        # Wire Inter-Page Signals to Pipeline
        self._wire_signals()

        # Start Pipeline Thread
        logger.info("MAIN", "Starting computer vision pipeline worker thread...")
        self.pipeline.start()

    def _wire_signals(self):
        # Dashboard Actions
        self.page_dashboard.start_virtual_cam_requested.connect(self._start_virtual_cam)
        self.page_dashboard.stop_virtual_cam_requested.connect(self._stop_virtual_cam)
        self.page_dashboard.calibrate_bg_requested.connect(self._calibrate_background)
        self.page_dashboard.toggle_manual_invisibility.connect(self._set_manual_invisibility)

        # Camera Studio Actions
        self.page_camera.camera_settings_changed.connect(self._on_camera_format_changed)
        self.page_camera.overlays_changed.connect(self._on_overlays_changed)

        # Gesture Controls Actions
        self.page_gesture.gesture_config_changed.connect(self._reload_pipeline_config)

        # Background Studio Actions
        self.page_bg.capture_instant_requested.connect(self._calibrate_background)
        self.page_bg.countdown_calibration_requested.connect(self.page_dashboard._start_countdown_calibration)
        self.page_bg.import_background_requested.connect(self._import_background)
        self.page_bg.settings_updated.connect(self._reload_pipeline_config)

        # Effects Page Actions
        self.page_effects.effects_updated.connect(self._reload_pipeline_config)

        # Device Manager Actions
        self.page_device.camera_selected.connect(self._switch_camera_device)

        # Settings Page Actions
        self.page_settings.settings_changed.connect(self._reload_pipeline_config)

    def _on_page_changed(self, index: int):
        self.stack.setCurrentIndex(index)

    def _start_virtual_cam(self):
        w = settings.resolution_w
        h = settings.resolution_h
        fps = settings.fps
        success = self.pipeline.virtual_cam.start(w, h, fps)
        if success:
            events.virtual_cam_state_changed.emit(True, self.pipeline.virtual_cam.device_name)
        else:
            ToastNotification.show_toast(
                self,
                "OBS Virtual Camera driver not found. Install OBS Studio or driver.",
                level="WARNING",
            )

    def _stop_virtual_cam(self):
        self.pipeline.virtual_cam.stop()
        events.virtual_cam_state_changed.emit(False, "")

    def _calibrate_background(self):
        self.pipeline.trigger_calibration()

    def _set_manual_invisibility(self, state: Optional[bool]):
        self.pipeline.invisibility_engine.set_manual_override(state)

    def _on_camera_format_changed(self, w: int, h: int, fps: int):
        logger.info("MAIN", f"Re-initializing camera hardware to {w}x{h} @ {fps}fps...")
        self.pipeline.camera.stop()
        self.pipeline.camera.start(settings.camera_index, w, h, fps)

    def _on_overlays_changed(self):
        pass

    def _reload_pipeline_config(self):
        self.pipeline.reload_configuration()

    def _import_background(self, path: str):
        success = self.pipeline.invisibility_engine.bg_capture.import_image(path)
        if success:
            ToastNotification.show_toast(self, "Background image successfully imported!", level="SUCCESS")
            self.page_bg.refresh_background_display()
        else:
            ToastNotification.show_toast(self, "Failed to import background image.", level="ERROR")

    def _switch_camera_device(self, cam_idx: int):
        w = settings.resolution_w
        h = settings.resolution_h
        fps = settings.fps
        self.pipeline.camera.stop()
        self.pipeline.camera.start(cam_idx, w, h, fps)

    def closeEvent(self, event: QCloseEvent):
        logger.info("MAIN", "Closing KYOKKO application. Releasing pipeline and camera resources...")
        self.pipeline.stop()
        event.accept()
