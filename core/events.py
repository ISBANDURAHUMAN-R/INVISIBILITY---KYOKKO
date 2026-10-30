"""
PROJECT KYOKKO
Pipeline Event Signals
PySide6 signal bridges for thread-safe asynchronous GUI updates.
"""

from PySide6.QtCore import QObject, Signal


class PipelineEvents(QObject):
    # Emits (raw_frame_np, processed_frame_np)
    frame_ready = Signal(object, object)

    # Emits GestureStatus dataclass
    gesture_updated = Signal(object)

    # Emits performance telemetry dictionary
    stats_updated = Signal(dict)

    # Emits (success_bool, message_str)
    background_calibrated = Signal(bool, str)

    # Emits (is_running_bool, device_name_str)
    virtual_cam_state_changed = Signal(bool, str)

    # Emits (category_str, error_message_str)
    error_occurred = Signal(str, str)


events = PipelineEvents()
