"""
PROJECT KYOKKO
Gesture Controls Page
Full customization of hand-to-head detection, touch sensitivity, delays, and interactive testing sandbox.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from core.events import events
from database.db_manager import DatabaseManager
from database.models import GestureConfig
from ui.components.gesture_meter import GestureMeter
from ui.components.toast import ToastNotification
from vision.gesture_recognition import GestureStatus


class GestureControlsPage(QWidget):
    gesture_config_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(GestureControlsPage, self).__init__(parent)
        self.db = DatabaseManager()
        self._test_trigger_count: int = 0
        self._last_state: str = "IDLE"

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Title
        title = QLabel("Gesture Controls")
        title.setObjectName("Heading1")
        sub = QLabel("Configure hand-to-head touch sensitivity, activation delays, and test gestures in real-time")
        sub.setObjectName("Subheading")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Settings Card
        cfg_card = QFrame()
        cfg_card.setObjectName("CardSurface")
        cfg_layout = QVBoxLayout(cfg_card)
        cfg_layout.setContentsMargins(20, 18, 20, 18)
        cfg_layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_title = QLabel("DETECTION PARAMETERS")
        header_title.setObjectName("Heading3")
        header_row.addWidget(header_title)
        header_row.addStretch()

        self.chk_enable = QCheckBox("Enable Gesture Detection")
        self.chk_enable.setChecked(True)
        self.chk_enable.toggled.connect(self._on_values_changed)
        header_row.addWidget(self.chk_enable)
        cfg_layout.addLayout(header_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(14)

        # Hand Preference
        hand_lbl = QLabel("Hand Selection")
        hand_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.hand_combo = QComboBox()
        self.hand_combo.addItems(["Both", "Left", "Right"])
        self.hand_combo.currentIndexChanged.connect(self._on_values_changed)
        grid.addWidget(hand_lbl, 0, 0)
        grid.addWidget(self.hand_combo, 0, 1)

        # Sensitivity Slider
        sens_lbl = QLabel("Touch Sensitivity")
        sens_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.sens_val_lbl = QLabel("0.45 (Standard)")
        self.sens_val_lbl.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.sens_slider = QSlider(Qt.Horizontal)
        self.sens_slider.setRange(20, 80)
        self.sens_slider.setValue(45)
        self.sens_slider.valueChanged.connect(self._on_sens_changed)

        sens_row = QHBoxLayout()
        sens_row.addWidget(self.sens_slider)
        sens_row.addWidget(self.sens_val_lbl)
        grid.addWidget(sens_lbl, 1, 0)
        grid.addLayout(sens_row, 1, 1)

        # Activation Delay Slider
        act_lbl = QLabel("Activation Delay")
        act_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.act_val_lbl = QLabel("200 ms")
        self.act_val_lbl.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.act_slider = QSlider(Qt.Horizontal)
        self.act_slider.setRange(50, 1000)
        self.act_slider.setValue(200)
        self.act_slider.valueChanged.connect(self._on_act_changed)

        act_row = QHBoxLayout()
        act_row.addWidget(self.act_slider)
        act_row.addWidget(self.act_val_lbl)
        grid.addWidget(act_lbl, 2, 0)
        grid.addLayout(act_row, 2, 1)

        # Release Delay Slider
        rel_lbl = QLabel("Release Delay")
        rel_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.rel_val_lbl = QLabel("150 ms")
        self.rel_val_lbl.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.rel_slider = QSlider(Qt.Horizontal)
        self.rel_slider.setRange(50, 800)
        self.rel_slider.setValue(150)
        self.rel_slider.valueChanged.connect(self._on_rel_changed)

        rel_row = QHBoxLayout()
        rel_row.addWidget(self.rel_slider)
        rel_row.addWidget(self.rel_val_lbl)
        grid.addWidget(rel_lbl, 3, 0)
        grid.addLayout(rel_row, 3, 1)

        # Cooldown Slider
        cd_lbl = QLabel("Gesture Cooldown")
        cd_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.cd_val_lbl = QLabel("500 ms")
        self.cd_val_lbl.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.cd_slider = QSlider(Qt.Horizontal)
        self.cd_slider.setRange(100, 2000)
        self.cd_slider.setValue(500)
        self.cd_slider.valueChanged.connect(self._on_cd_changed)

        cd_row = QHBoxLayout()
        cd_row.addWidget(self.cd_slider)
        cd_row.addWidget(self.cd_val_lbl)
        grid.addWidget(cd_lbl, 4, 0)
        grid.addLayout(cd_row, 4, 1)

        cfg_layout.addLayout(grid)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._save_to_database)
        btn_row.addWidget(save_btn)

        reset_btn = QPushButton("Reset to Recommended")
        reset_btn.setObjectName("SecondaryBtn")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_row.addWidget(reset_btn)

        btn_row.addStretch()
        cfg_layout.addLayout(btn_row)

        layout.addWidget(cfg_card)

        # Live Gesture Testing Sandbox Card
        test_card = QFrame()
        test_card.setObjectName("CardSurface")
        test_layout = QVBoxLayout(test_card)
        test_layout.setContentsMargins(20, 18, 20, 18)
        test_layout.setSpacing(14)

        t_title = QLabel("INTERACTIVE GESTURE TESTING SANDBOX")
        t_title.setObjectName("Heading3")
        test_layout.addWidget(t_title)

        # Live Gauge
        self.test_meter = GestureMeter(self)
        test_layout.addWidget(self.test_meter)

        # Live Feedback Info Row
        feedback_row = QHBoxLayout()
        self.feedback_lbl = QLabel("Live Feedback: Awaiting hand movement towards head...")
        self.feedback_lbl.setStyleSheet("color: #00d2ff; font-weight: 600;")
        feedback_row.addWidget(self.feedback_lbl)
        feedback_row.addStretch()

        self.counter_lbl = QLabel("Test Triggers: 0")
        self.counter_lbl.setStyleSheet("color: #00f59b; font-weight: 700;")
        feedback_row.addWidget(self.counter_lbl)

        reset_count_btn = QPushButton("Reset Counter")
        reset_count_btn.setObjectName("SecondaryBtn")
        reset_count_btn.setFixedWidth(110)
        reset_count_btn.clicked.connect(self._reset_counter)
        feedback_row.addWidget(reset_count_btn)

        test_layout.addLayout(feedback_row)
        layout.addWidget(test_card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        self._load_from_database()
        events.gesture_updated.connect(self._on_gesture_updated)

    def _on_sens_changed(self, val: int):
        f = val / 100.0
        self.sens_val_lbl.setText(f"{f:.2f}")
        self._on_values_changed()

    def _on_act_changed(self, val: int):
        self.act_val_lbl.setText(f"{val} ms")
        self._on_values_changed()

    def _on_rel_changed(self, val: int):
        self.rel_val_lbl.setText(f"{val} ms")
        self._on_values_changed()

    def _on_cd_changed(self, val: int):
        self.cd_val_lbl.setText(f"{val} ms")
        self._on_values_changed()

    def _load_from_database(self):
        cfg = self.db.get_active_gesture_config()
        idx = self.hand_combo.findText(cfg.hand_preference)
        if idx >= 0:
            self.hand_combo.setCurrentIndex(idx)
        self.sens_slider.setValue(int(cfg.sensitivity * 100))
        self.act_slider.setValue(cfg.activation_delay_ms)
        self.rel_slider.setValue(cfg.release_delay_ms)
        self.cd_slider.setValue(cfg.cooldown_ms)
        self.chk_enable.setChecked(cfg.is_active)

    def _save_to_database(self):
        cfg = GestureConfig(
            name="Custom Gesture",
            hand_preference=self.hand_combo.currentText(),
            sensitivity=self.sens_slider.value() / 100.0,
            activation_delay_ms=self.act_slider.value(),
            release_delay_ms=self.rel_slider.value(),
            cooldown_ms=self.cd_slider.value(),
            is_active=self.chk_enable.isChecked(),
        )
        self.db.update_gesture_config(cfg)
        self.gesture_config_changed.emit()
        ToastNotification.show_toast(self.window(), "Gesture Configuration Saved", level="SUCCESS")

    def _reset_defaults(self):
        self.hand_combo.setCurrentText("Both")
        self.sens_slider.setValue(45)
        self.act_slider.setValue(200)
        self.rel_slider.setValue(150)
        self.cd_slider.setValue(500)
        self.chk_enable.setChecked(True)
        self._save_to_database()

    def _on_values_changed(self):
        self.gesture_config_changed.emit()

    def _reset_counter(self):
        self._test_trigger_count = 0
        self.counter_lbl.setText("Test Triggers: 0")

    def _on_gesture_updated(self, status: GestureStatus):
        self.test_meter.update_status(status, sensitivity=self.sens_slider.value() / 100.0)
        self.feedback_lbl.setText(f"Live Feedback: {status.message}")

        if status.state.value == "ACTIVE" and self._last_state != "ACTIVE":
            self._test_trigger_count += 1
            self.counter_lbl.setText(f"Test Triggers: {self._test_trigger_count}")

        self._last_state = status.state.value
