"""
PROJECT KYOKKO
Device Manager Page
Hardware camera discovery, virtual camera driver verification, diagnostics, and troubleshooting guide.
"""

import os
import subprocess
import sys
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from core.events import events
from core.worker import FunctionWorker
from settings.app_settings import settings
from ui.components.toast import ToastNotification
from utils.system_info import (
    check_virtual_camera_backends,
    detect_supported_resolutions,
    enumerate_webcams,
)


class DeviceManagerPage(QWidget):
    camera_selected = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super(DeviceManagerPage, self).__init__(parent)
        self._cameras: List[dict] = []

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Title
        title = QLabel("Device Manager")
        title.setObjectName("Heading1")
        sub = QLabel("Hardware camera discovery, driver diagnostics, and virtual camera broadcasting setup")
        sub.setObjectName("Subheading")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Discovered Physical Webcams Card
        cams_card = QFrame()
        cams_card.setObjectName("CardSurface")
        c_layout = QVBoxLayout(cams_card)
        c_layout.setContentsMargins(20, 18, 20, 18)
        c_layout.setSpacing(12)

        c_header = QHBoxLayout()
        c_title = QLabel("PHYSICAL WEBCAM DEVICES")
        c_title.setObjectName("Heading3")
        c_header.addWidget(c_title)
        c_header.addStretch()

        self.scan_btn = QPushButton("✦ Rescan Cameras")
        self.scan_btn.clicked.connect(self._scan_cameras)
        c_header.addWidget(self.scan_btn)

        self.select_btn = QPushButton("Set Active Camera")
        self.select_btn.setObjectName("SecondaryBtn")
        self.select_btn.clicked.connect(self._on_select_camera)
        c_header.addWidget(self.select_btn)

        c_layout.addLayout(c_header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Index", "Friendly Name", "Resolution", "Backend", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(140)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        c_layout.addWidget(self.table)

        layout.addWidget(cams_card)

        # Virtual Camera Backend Diagnostics Card
        vcam_card = QFrame()
        vcam_card.setObjectName("CardSurface")
        v_layout = QVBoxLayout(vcam_card)
        v_layout.setContentsMargins(20, 18, 20, 18)
        v_layout.setSpacing(14)

        v_title = QLabel("VIRTUAL CAMERA SYSTEM & DRIVERS")
        v_title.setObjectName("Heading3")
        v_layout.addWidget(v_title)

        self.vcam_info_lbl = QLabel("Checking virtual camera drivers...")
        self.vcam_info_lbl.setStyleSheet("color: #f8f7fc; font-size: 13px;")
        v_layout.addWidget(self.vcam_info_lbl)

        v_btn_row = QHBoxLayout()
        v_btn_row.setSpacing(12)

        check_btn = QPushButton("Verify Virtual Camera Drivers")
        check_btn.setObjectName("SecondaryBtn")
        check_btn.clicked.connect(self._check_virtual_cam)
        v_btn_row.addWidget(check_btn)

        install_btn = QPushButton("Install OBS Virtual Camera (winget)")
        install_btn.clicked.connect(self._install_obs_virtual_cam)
        v_btn_row.addWidget(install_btn)

        v_btn_row.addStretch()
        v_layout.addLayout(v_btn_row)

        layout.addWidget(vcam_card)

        # Connection Troubleshooting Guide
        guide_card = QFrame()
        guide_card.setObjectName("CardSurface")
        g_layout = QVBoxLayout(guide_card)
        g_layout.setContentsMargins(20, 18, 20, 18)
        g_layout.setSpacing(12)

        g_title = QLabel("TROUBLESHOOTING & APP INTEGRATION GUIDE")
        g_title.setObjectName("Heading3")
        g_layout.addWidget(g_title)

        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setMinimumHeight(160)
        guide_text.setHtml("""
            <p style='color: #c77dff; font-weight: bold;'>How to use KYOKKO with Zoom, Google Meet, Teams, & Discord:</p>
            <ol style='color: #9f97bf; line-height: 1.6;'>
                <li><b>Start KYOKKO Virtual Camera:</b> Click 'Start Virtual Camera' on the Dashboard or Camera Studio.</li>
                <li><b>Open your Video Conference Software:</b> (Zoom, Google Meet, Microsoft Teams, Discord).</li>
                <li><b>Select Camera:</b> In video settings, choose <b>'OBS Virtual Camera'</b> (or KYOKKO stream).</li>
                <li><b>Perform Gesture:</b> Touch your hand to your temple/head — you immediately disappear from the meeting call!</li>
                <li><b>Restore Feed:</b> Lower your hand to smoothly reappear without any glitch or frame freezing.</li>
            </ol>
            <p style='color: #635b80; font-size: 11px;'>Note: DirectShow virtual cameras are 100% compliant with all major Windows video conferencing software.</p>
        """)
        g_layout.addWidget(guide_text)

        layout.addWidget(guide_card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Initial scan
        self._scan_cameras()
        self._check_virtual_cam()

    def _scan_cameras(self):
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Scanning...")

        self._cameras = enumerate_webcams(max_test=4)
        self.table.setRowCount(len(self._cameras))

        for row, cam in enumerate(self._cameras):
            self.table.setItem(row, 0, QTableWidgetItem(str(cam["index"])))
            self.table.setItem(row, 1, QTableWidgetItem(cam["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(f"{cam['default_width']}x{cam['default_height']}"))
            self.table.setItem(row, 3, QTableWidgetItem(cam["backend"]))
            is_active = (cam["index"] == settings.camera_index)
            status_str = "ACTIVE SENSOR" if is_active else ("Available" if cam["working"] else "Offline")
            self.table.setItem(row, 4, QTableWidgetItem(status_str))

        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("✦ Rescan Cameras")

    def _on_select_camera(self):
        selected_rows = self.table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            cam_idx = int(self.table.item(row, 0).text())
            settings.camera_index = cam_idx
            self.camera_selected.emit(cam_idx)
            self._scan_cameras()
            ToastNotification.show_toast(self.window(), f"Selected Camera {cam_idx} as Active Sensor", level="SUCCESS")

    def _check_virtual_cam(self):
        status = check_virtual_camera_backends()
        if status["pyvirtualcam_available"]:
            self.vcam_info_lbl.setText(f"✓ DirectShow Virtual Camera Backend Ready: {status['details']}")
            self.vcam_info_lbl.setStyleSheet("color: #00f59b; font-weight: bold;")
        elif status["obs_installed"]:
            self.vcam_info_lbl.setText("✓ OBS Virtual Camera installed. Ready to start broadcasting.")
            self.vcam_info_lbl.setStyleSheet("color: #00d2ff; font-weight: bold;")
        else:
            self.vcam_info_lbl.setText("⚠ OBS Virtual Camera driver not detected on system. Click 'Install' below or install OBS Studio.")
            self.vcam_info_lbl.setStyleSheet("color: #ffb703; font-weight: bold;")

    def _install_obs_virtual_cam(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        bat_path = os.path.join(base_dir, "install_obs_virtual_camera.bat")
        installer_path = os.path.join(base_dir, "OBS-Studio-Installer.exe")

        # Also support frozen exe paths
        if not os.path.exists(bat_path):
            exe_dir = os.path.dirname(sys.executable)
            bat_path = os.path.join(exe_dir, "install_obs_virtual_camera.bat")
            installer_path = os.path.join(exe_dir, "OBS-Studio-Installer.exe")

        ToastNotification.show_toast(self.window(), "Launching Virtual Camera installer as Administrator...", level="INFO")
        try:
            if os.path.exists(bat_path):
                cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList \'/c \"\"{bat_path}\"\"\' -Verb RunAs"'
            elif os.path.exists(installer_path):
                cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process \'{installer_path}\' -Verb RunAs"'
            else:
                cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList \'-NoProfile -Command winget install --id OBSProject.OBSStudio -e --accept-source-agreements --accept-package-agreements; Pause\' -Verb RunAs"'
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            ToastNotification.show_toast(self.window(), f"Install launch error: {e}", level="ERROR")
