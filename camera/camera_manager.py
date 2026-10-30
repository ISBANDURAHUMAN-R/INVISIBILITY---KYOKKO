"""
PROJECT KYOKKO
Physical Camera Manager
Thread-safe hardware capture, dynamic resolution switching, and disconnection recovery.
"""

import threading
import time
from typing import Dict, Optional, Tuple
import cv2
import numpy as np
from services.logger_service import logger


class CameraManager:
    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self._current_index: int = 0
        self._width: int = 1280
        self._height: int = 720
        self._target_fps: int = 30
        self._is_running: bool = False

        # Telemetry
        self._fps_counter: int = 0
        self._fps_start_time: float = time.time()
        self._actual_fps: float = 0.0
        self._dropped_frames: int = 0
        self._last_frame_time: float = 0.0

    @property
    def is_running(self) -> bool:
        return self._is_running and self._cap is not None and self._cap.isOpened()

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def resolution(self) -> Tuple[int, int]:
        return (self._width, self._height)

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    def start(self, camera_index: int = 0, width: int = 1280, height: int = 720, fps: int = 30) -> bool:
        with self._lock:
            self.stop()

            self._current_index = camera_index
            self._width = width
            self._height = height
            self._target_fps = fps

            logger.info("CAMERA", f"Opening camera device index {camera_index} ({width}x{height} @ {fps}fps)...")
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                logger.warning("CAMERA", f"CAP_DSHOW failed for index {camera_index}, trying default backend...")
                cap = cv2.VideoCapture(camera_index)

            if not cap.isOpened():
                logger.error("CAMERA", f"Failed to open camera index {camera_index}!")
                return False

            # Set hardware properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer for lowest latency

            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._width = actual_w
            self._height = actual_h

            self._cap = cap
            self._is_running = True
            self._fps_start_time = time.time()
            self._fps_counter = 0
            logger.info("CAMERA", f"Camera {camera_index} successfully started! Resolution: {actual_w}x{actual_h}")
            return True

    def stop(self) -> None:
        if self._cap is not None:
            logger.info("CAMERA", f"Releasing camera {self._current_index}")
            self._is_running = False
            self._cap.release()
            self._cap = None

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self._is_running or self._cap is None:
            return False, None

        ret, frame = self._cap.read()
        now = time.time()

        if ret and frame is not None:
            self._fps_counter += 1
            if now - self._fps_start_time >= 1.0:
                self._actual_fps = self._fps_counter / (now - self._fps_start_time)
                self._fps_counter = 0
                self._fps_start_time = now
            self._last_frame_time = now
            return True, frame
        else:
            self._dropped_frames += 1
            # Check for camera disconnection
            if now - self._last_frame_time > 3.0 and self._last_frame_time > 0:
                logger.warning("CAMERA", "Camera stream interrupted! Attempting hardware reconnect...")
                self._attempt_reconnect()
            return False, None

    def _attempt_reconnect(self) -> None:
        try:
            self.stop()
            time.sleep(0.5)
            self.start(self._current_index, self._width, self._height, self._target_fps)
        except Exception as e:
            logger.error("CAMERA", f"Reconnect failed: {e}")

    def get_stats(self) -> Dict[str, any]:
        return {
            "is_running": self.is_running,
            "camera_index": self._current_index,
            "width": self._width,
            "height": self._height,
            "actual_fps": round(self._actual_fps, 1),
            "target_fps": self._target_fps,
            "dropped_frames": self._dropped_frames,
        }
