"""
PROJECT KYOKKO
Settings Page
Global application preferences, performance tuning, privacy controls, and live log viewer.
"""

import os
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from database.db_manager import DatabaseManager
from services.config_service import config
from services.logger_service import logger
from settings.app_settings import settings
from ui.components.toast import ToastNotification
from utils.system_info import get_system_telemetry


class SettingsPage(QWidget):
    settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(SettingsPage, self).__init__(parent)
        self.db = DatabaseManager()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Title
        title = QLabel("Settings")
        title.setObjectName("Heading1")
        sub = QLabel("Application preferences, performance optimization, and telemetry logging")
        sub.setObjectName("Subheading")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Performance & AI Optimization Card
        perf_card = QFrame()
        perf_card.setObjectName("CardSurface")
        p_layout = QVBoxLayout(perf_card)
        p_layout.setContentsMargins(20, 18, 20, 18)
        p_layout.setSpacing(14)

        p_title = QLabel("PERFORMANCE & AI PIPELINE")
        p_title.setObjectName("Heading3")
        p_layout.addWidget(p_title)

        p_grid = QGridLayout()
        p_grid.setHorizontalSpacing(24)
        p_grid.setVerticalSpacing(12)

        # Downscale factor for inference
        ds_lbl = QLabel("AI Inference Resolution Scaling")
        ds_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.ds_combo = QComboBox()
        self.ds_combo.addItem("1.0x - Native Resolution (Highest Fidelity)", 1.0)
        self.ds_combo.addItem("0.75x - Balanced Quality & Speed", 0.75)
        self.ds_combo.addItem("0.50x - Ultra High FPS (Lower CPU Usage)", 0.50)

        cur_ds = config.get_float("performance_downscale", 1.0)
        for i in range(self.ds_combo.count()):
            if abs(self.ds_combo.itemData(i) - cur_ds) < 0.05:
                self.ds_combo.setCurrentIndex(i)
                break
        self.ds_combo.currentIndexChanged.connect(self._on_perf_changed)
        p_grid.addWidget(ds_lbl, 0, 0)
        p_grid.addWidget(self.ds_combo, 0, 1)

        # Transition Speed Slider
        trans_lbl = QLabel("Invisibility Transition Dissolve Speed")
        trans_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.trans_val = QLabel(f"{settings.transition_ms} ms")
        self.trans_val.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.trans_slider = QSlider(Qt.Horizontal)
        self.trans_slider.setRange(50, 1000)
        self.trans_slider.setValue(settings.transition_ms)
        self.trans_slider.valueChanged.connect(self._on_trans_changed)

        t_row = QHBoxLayout()
        t_row.addWidget(self.trans_slider)
        t_row.addWidget(self.trans_val)
        p_grid.addWidget(trans_lbl, 1, 0)
        p_grid.addLayout(t_row, 1, 1)

        p_layout.addLayout(p_grid)
        layout.addWidget(perf_card)

        # Privacy & Architecture Card
        priv_card = QFrame()
        priv_card.setObjectName("CardSurface")
        pr_layout = QVBoxLayout(priv_card)
        pr_layout.setContentsMargins(20, 18, 20, 18)
        pr_layout.setSpacing(10)

        pr_title = QLabel("PRIVACY & DATA SECURITY")
        pr_title.setObjectName("Heading3")
        pr_layout.addWidget(pr_title)

        pr_info = QLabel("✦ 100% Local Processing Guarantee: All OpenCV computer vision, MediaPipe neural networks, and video streams process strictly on-device in local memory. KYOKKO sends zero telemetry, zero video feeds, and zero biometric data to any external network or cloud server.")
        pr_info.setStyleSheet("color: #00f59b; font-size: 12px; line-height: 1.4;")
        pr_info.setWordWrap(True)
        pr_layout.addWidget(pr_info)

        sys_info = get_system_telemetry()
        sys_lbl = QLabel(f"Platform: {sys_info['os']} | Architecture: {sys_info['arch']} | Python: {sys_info['python']}")
        sys_lbl.setObjectName("MutedLabel")
        pr_layout.addWidget(sys_lbl)

        layout.addWidget(priv_card)

        # Live Activity Log Card
        log_card = QFrame()
        log_card.setObjectName("CardSurface")
        l_layout = QVBoxLayout(log_card)
        l_layout.setContentsMargins(20, 18, 20, 18)
        l_layout.setSpacing(12)

        l_header = QHBoxLayout()
        l_title = QLabel("SYSTEM & ACTIVITY LOGS")
        l_title.setObjectName("Heading3")
        l_header.addWidget(l_title)
        l_header.addStretch()

        clear_btn = QPushButton("Clear Logs")
        clear_btn.setObjectName("SecondaryBtn")
        clear_btn.clicked.connect(self._clear_logs)
        l_header.addWidget(clear_btn)

        export_btn = QPushButton("Export Log File...")
        export_btn.setObjectName("SecondaryBtn")
        export_btn.clicked.connect(self._export_logs)
        l_header.addWidget(export_btn)

        l_layout.addLayout(l_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(180)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0c0818;
                color: #c77dff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #271b4a;
            }
        """)
        l_layout.addWidget(self.log_text)
        layout.addWidget(log_card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Subscribe to live log notifications
        logger.subscribe(self._on_live_log)
        self._load_recent_logs()

    def _on_perf_changed(self):
        val = self.ds_combo.currentData()
        config.set("performance_downscale", val)
        self.settings_changed.emit()

    def _on_trans_changed(self, val: int):
        self.trans_val.setText(f"{val} ms")
        settings.transition_ms = val
        self.settings_changed.emit()

    def _load_recent_logs(self):
        logs = self.db.get_recent_logs(limit=40)
        lines = []
        for lg in reversed(logs):
            lines.append(f"[{lg.timestamp}] [{lg.level}] [{lg.category}] {lg.message}")
        self.log_text.setPlainText("\n".join(lines))
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def _on_live_log(self, level: str, category: str, message: str):
        line = f"[{level}] [{category}] {message}"
        self.log_text.append(line)

    def _clear_logs(self):
        self.db.clear_logs()
        self.log_text.clear()
        ToastNotification.show_toast(self.window(), "Logs Cleared", level="INFO")

    def _export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Log File", "kyokko_logs.txt", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())
            ToastNotification.show_toast(self.window(), f"Exported to {os.path.basename(path)}", level="SUCCESS")
