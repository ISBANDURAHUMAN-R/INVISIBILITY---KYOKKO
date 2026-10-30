"""
PROJECT KYOKKO
Effects Page
Real-time image grading, cinematic color filters, blur, sharpening, and color correction.
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
from services.config_service import config
from settings.app_settings import settings
from ui.components.toast import ToastNotification


class EffectsPage(QWidget):
    effects_updated = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super(EffectsPage, self).__init__(parent)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Title
        title = QLabel("Effects & Visual Grading")
        title.setObjectName("Heading1")
        sub = QLabel("Enhance your camera feed with brightness, contrast, cinematic color presets, and sharpening")
        sub.setObjectName("Subheading")
        layout.addWidget(title)
        layout.addWidget(sub)

        # Sliders Card
        card = QFrame()
        card.setObjectName("CardSurface")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)

        t1 = QLabel("COLOR & EXPOSURE CORRECTION")
        t1.setObjectName("Heading3")
        card_layout.addWidget(t1)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)

        # Brightness
        b_lbl = QLabel("Brightness")
        b_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.b_val = QLabel("0")
        self.b_val.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.b_slider = QSlider(Qt.Horizontal)
        self.b_slider.setRange(-100, 100)
        self.b_slider.setValue(config.get_int("brightness", 0))
        self.b_slider.valueChanged.connect(self._on_brightness_changed)

        b_row = QHBoxLayout()
        b_row.addWidget(self.b_slider)
        b_row.addWidget(self.b_val)
        grid.addWidget(b_lbl, 0, 0)
        grid.addLayout(b_row, 0, 1)

        # Contrast
        c_lbl = QLabel("Contrast")
        c_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.c_val = QLabel("1.00")
        self.c_val.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.c_slider = QSlider(Qt.Horizontal)
        self.c_slider.setRange(50, 250)
        self.c_slider.setValue(int(config.get_float("contrast", 1.0) * 100))
        self.c_slider.valueChanged.connect(self._on_contrast_changed)

        c_row = QHBoxLayout()
        c_row.addWidget(self.c_slider)
        c_row.addWidget(self.c_val)
        grid.addWidget(c_lbl, 1, 0)
        grid.addLayout(c_row, 1, 1)

        # Saturation
        s_lbl = QLabel("Saturation")
        s_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.s_val = QLabel("1.00")
        self.s_val.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.s_slider = QSlider(Qt.Horizontal)
        self.s_slider.setRange(0, 250)
        self.s_slider.setValue(int(config.get_float("saturation", 1.0) * 100))
        self.s_slider.valueChanged.connect(self._on_saturation_changed)

        s_row = QHBoxLayout()
        s_row.addWidget(self.s_slider)
        s_row.addWidget(self.s_val)
        grid.addWidget(s_lbl, 2, 0)
        grid.addLayout(s_row, 2, 1)

        # Blur
        blur_lbl = QLabel("Gaussian Blur")
        blur_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.blur_val = QLabel("0 px")
        self.blur_val.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(0, 25)
        self.blur_slider.setValue(config.get_int("blur_amount", 0))
        self.blur_slider.valueChanged.connect(self._on_blur_changed)

        blur_row = QHBoxLayout()
        blur_row.addWidget(self.blur_slider)
        blur_row.addWidget(self.blur_val)
        grid.addWidget(blur_lbl, 3, 0)
        grid.addLayout(blur_row, 3, 1)

        # Sharpening
        sh_lbl = QLabel("Sharpening (Unsharp Mask)")
        sh_lbl.setStyleSheet("color: #f8f7fc; font-weight: 600;")
        self.sh_val = QLabel("0.00")
        self.sh_val.setStyleSheet("color: #c77dff; font-weight: bold;")
        self.sh_slider = QSlider(Qt.Horizontal)
        self.sh_slider.setRange(0, 200)
        self.sh_slider.setValue(int(config.get_float("sharpen_amount", 0.0) * 100))
        self.sh_slider.valueChanged.connect(self._on_sharpen_changed)

        sh_row = QHBoxLayout()
        sh_row.addWidget(self.sh_slider)
        sh_row.addWidget(self.sh_val)
        grid.addWidget(sh_lbl, 4, 0)
        grid.addLayout(sh_row, 4, 1)

        card_layout.addLayout(grid)
        layout.addWidget(card)

        # Cinematic Filters Card
        filter_card = QFrame()
        filter_card.setObjectName("CardSurface")
        f_layout = QVBoxLayout(filter_card)
        f_layout.setContentsMargins(20, 18, 20, 18)
        f_layout.setSpacing(14)

        f_title = QLabel("CINEMATIC COLOR PRESETS & TONES")
        f_title.setObjectName("Heading3")
        f_layout.addWidget(f_title)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self.filter_buttons = {}
        presets = ["Normal", "Cyberpunk", "Matrix", "Cinema Cool", "Sepia", "Warm Sunset", "Noir"]
        current_preset = config.get("color_filter", "Normal")

        for p in presets:
            btn = QPushButton(p)
            btn.setObjectName("SecondaryBtn" if p != current_preset else "")
            btn.clicked.connect(lambda checked=False, name=p: self._select_filter(name))
            filter_row.addWidget(btn)
            self.filter_buttons[p] = btn

        filter_row.addStretch()
        f_layout.addLayout(filter_row)

        # Toggles row
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(24)

        self.chk_gray = QCheckBox("Grayscale Mode")
        self.chk_gray.setChecked(config.get_bool("grayscale", False))
        self.chk_gray.toggled.connect(self._on_gray_toggled)
        toggle_row.addWidget(self.chk_gray)

        self.chk_mirror = QCheckBox("Mirror Mode (Horizontal Flip)")
        self.chk_mirror.setChecked(settings.mirror_mode)
        self.chk_mirror.toggled.connect(self._on_mirror_toggled)
        toggle_row.addWidget(self.chk_mirror)

        toggle_row.addStretch()

        reset_btn = QPushButton("Reset All Effects")
        reset_btn.setObjectName("DangerBtn")
        reset_btn.setFixedWidth(140)
        reset_btn.clicked.connect(self._reset_all_effects)
        toggle_row.addWidget(reset_btn)

        f_layout.addLayout(toggle_row)
        layout.addWidget(filter_card)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _on_brightness_changed(self, val: int):
        self.b_val.setText(str(val))
        config.set("brightness", val)
        self.effects_updated.emit()

    def _on_contrast_changed(self, val: int):
        f = val / 100.0
        self.c_val.setText(f"{f:.2f}")
        config.set("contrast", f)
        self.effects_updated.emit()

    def _on_saturation_changed(self, val: int):
        f = val / 100.0
        self.s_val.setText(f"{f:.2f}")
        config.set("saturation", f)
        self.effects_updated.emit()

    def _on_blur_changed(self, val: int):
        k = val if val % 2 == 1 or val == 0 else val + 1
        self.blur_val.setText(f"{k} px")
        config.set("blur_amount", k)
        self.effects_updated.emit()

    def _on_sharpen_changed(self, val: int):
        f = val / 100.0
        self.sh_val.setText(f"{f:.2f}")
        config.set("sharpen_amount", f)
        self.effects_updated.emit()

    def _select_filter(self, name: str):
        config.set("color_filter", name)
        for p, btn in self.filter_buttons.items():
            if p == name:
                btn.setObjectName("")
            else:
                btn.setObjectName("SecondaryBtn")
            btn.setStyle(btn.style())
        self.effects_updated.emit()

    def _on_gray_toggled(self, checked: bool):
        config.set("grayscale", "1" if checked else "0")
        self.effects_updated.emit()

    def _on_mirror_toggled(self, checked: bool):
        settings.mirror_mode = checked
        self.effects_updated.emit()

    def _reset_all_effects(self):
        self.b_slider.setValue(0)
        self.c_slider.setValue(100)
        self.s_slider.setValue(100)
        self.blur_slider.setValue(0)
        self.sh_slider.setValue(0)
        self.chk_gray.setChecked(False)
        self._select_filter("Normal")
        ToastNotification.show_toast(self.window(), "Effects Reset to Default", level="INFO")
