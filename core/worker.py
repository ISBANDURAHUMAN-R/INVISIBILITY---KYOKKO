"""
PROJECT KYOKKO
Asynchronous Background Workers
Non-blocking execution for camera discovery and calibration countdowns.
"""

import time
from typing import Callable, Optional
from PySide6.QtCore import QObject, QRunnable, QThread, Signal, Slot


class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(str)
    result = Signal(object)
    progress = Signal(int)


class FunctionWorker(QRunnable):
    """Executes a arbitrary python callable on the Qt thread pool."""

    def __init__(self, fn: Callable, *args, **kwargs):
        super(FunctionWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class CalibrationCountdownWorker(QThread):
    """Runs a 3-second or 5-second countdown for empty room background capture."""
    tick = Signal(int)       # Remaining seconds (3, 2, 1, 0)
    capture = Signal()       # Emitted at 0 seconds
    finished_countdown = Signal()

    def __init__(self, seconds: int = 3):
        super(CalibrationCountdownWorker, self).__init__()
        self.seconds = seconds
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        for s in range(self.seconds, 0, -1):
            if self._is_cancelled:
                return
            self.tick.emit(s)
            time.sleep(1.0)

        if not self._is_cancelled:
            self.tick.emit(0)
            self.capture.emit()
            time.sleep(0.1)

        self.finished_countdown.emit()
