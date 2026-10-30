"""
PROJECT KYOKKO
Application Settings Facade
Clean strongly-typed access to active configurations.
"""

from services.config_service import config


class AppSettings:
    @property
    def camera_index(self) -> int:
        return config.get_int("default_camera_index", 0)

    @camera_index.setter
    def camera_index(self, val: int):
        config.set("default_camera_index", val)

    @property
    def resolution_w(self) -> int:
        return config.get_int("default_resolution_w", 1280)

    @resolution_w.setter
    def resolution_w(self, val: int):
        config.set("default_resolution_w", val)

    @property
    def resolution_h(self) -> int:
        return config.get_int("default_resolution_h", 720)

    @resolution_h.setter
    def resolution_h(self, val: int):
        config.set("default_resolution_h", val)

    @property
    def fps(self) -> int:
        return config.get_int("default_fps", 30)

    @fps.setter
    def fps(self, val: int):
        config.set("default_fps", val)

    @property
    def show_landmarks(self) -> bool:
        return config.get_bool("show_landmarks", True)

    @show_landmarks.setter
    def show_landmarks(self, val: bool):
        config.set("show_landmarks", "1" if val else "0")

    @property
    def show_mask_overlay(self) -> bool:
        return config.get_bool("show_mask_overlay", False)

    @show_mask_overlay.setter
    def show_mask_overlay(self, val: bool):
        config.set("show_mask_overlay", "1" if val else "0")

    @property
    def show_hud(self) -> bool:
        return config.get_bool("show_hud", True)

    @show_hud.setter
    def show_hud(self, val: bool):
        config.set("show_hud", "1" if val else "0")

    @property
    def mirror_mode(self) -> bool:
        return config.get_bool("mirror_mode", True)

    @mirror_mode.setter
    def mirror_mode(self, val: bool):
        config.set("mirror_mode", "1" if val else "0")

    @property
    def transition_ms(self) -> int:
        return config.get_int("invisibility_transition_ms", 250)

    @transition_ms.setter
    def transition_ms(self, val: int):
        config.set("invisibility_transition_ms", val)

    @property
    def mask_threshold(self) -> float:
        return config.get_float("mask_threshold", 0.55)

    @mask_threshold.setter
    def mask_threshold(self, val: float):
        config.set("mask_threshold", val)

    @property
    def mask_feather(self) -> int:
        return config.get_int("mask_feather", 7)

    @mask_feather.setter
    def mask_feather(self, val: int):
        config.set("mask_feather", val)

    @property
    def mask_dilation(self) -> int:
        return config.get_int("mask_dilation", 3)

    @mask_dilation.setter
    def mask_dilation(self, val: int):
        config.set("mask_dilation", val)

    @property
    def segmentation_model(self) -> int:
        return config.get_int("segmentation_model", 0)

    @segmentation_model.setter
    def segmentation_model(self, val: int):
        config.set("segmentation_model", val)

    @property
    def theme(self) -> str:
        return config.get("app_theme", "dark_purple")

    @theme.setter
    def theme(self, val: str):
        config.set("app_theme", val)


settings = AppSettings()
