"""
PROJECT KYOKKO
Virtual Camera System
pyvirtualcam DirectShow driver streaming, OBS Virtual Camera compatibility, and emergency shutdown.
"""

import threading
import time
from typing import Dict, Optional
import cv2
import numpy as np
from services.logger_service import logger


class VirtualCamera:
    def __init__(self):
        self._cam = None
        self._lock = threading.Lock()
        self._is_broadcasting: bool = False
        self._backend_available: bool = False
        self._active_backend: Optional[str] = None
        self._device_name: str = "Virtual Camera Device"
        self._width: int = 1280
        self._height: int = 720
        self._target_fps: int = 30

        # Stats
        self._frames_sent: int = 0
        self._dropped_frames: int = 0
        self._fps_counter: int = 0
        self._fps_start_time: float = time.time()
        self._actual_fps: float = 0.0

        self._check_backend_status()

    def _check_backend_status(self) -> None:
        try:
            import pyvirtualcam
            # We don't instantiate camera until start() is called, but check import
            self._backend_available = True
        except ImportError:
            self._backend_available = False
            logger.warning("VIRTUAL_CAM", "pyvirtualcam package not available!")

    @property
    def is_broadcasting(self) -> bool:
        return self._is_broadcasting

    @property
    def backend_available(self) -> bool:
        return self._backend_available

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    def start(self, width: int = 1280, height: int = 720, fps: int = 30) -> bool:
        with self._lock:
            self.stop()

            self._width = width
            self._height = height
            self._target_fps = fps

            try:
                import pyvirtualcam
                logger.info("VIRTUAL_CAM", f"Initializing DirectShow Virtual Camera ({width}x{height} @ {fps}fps)...")
                self._cam = pyvirtualcam.Camera(
                    width=width,
                    height=height,
                    fps=fps,
                    fmt=pyvirtualcam.PixelFormat.BGR,
                    print_fps=False,
                )
                self._active_backend = self._cam.backend
                self._device_name = self._cam.device
                self._is_broadcasting = True
                self._backend_available = True
                self._fps_start_time = time.time()
                self._fps_counter = 0
                logger.info("VIRTUAL_CAM", f"Virtual Camera LIVE on backend '{self._active_backend}' ({self._device_name})")
                return True
            except Exception as e:
                self._is_broadcasting = False
                self._cam = None
                logger.warning(
                    "VIRTUAL_CAM",
                    f"DirectShow virtual camera backend error: {e}. (OBS Virtual Camera driver may need installation)",
                )
                return False

    def send(self, frame: np.ndarray) -> bool:
        if not self._is_broadcasting or self._cam is None:
            return False

        if frame is None or frame.size == 0:
            return False

        try:
            h, w = frame.shape[:2]
            if w != self._width or h != self._height:
                send_frame = cv2.resize(frame, (self._width, self._height), interpolation=cv2.INTER_LINEAR)
            else:
                send_frame = frame

            self._cam.send(send_frame)
            self._frames_sent += 1
            self._fps_counter += 1

            now = time.time()
            if now - self._fps_start_time >= 1.0:
                self._actual_fps = self._fps_counter / (now - self._fps_start_time)
                self._fps_counter = 0
                self._fps_start_time = now

            return True
        except Exception as e:
            self._dropped_frames += 1
            logger.error("VIRTUAL_CAM", f"Error sending frame to virtual camera: {e}")
            return False

    def stop(self) -> None:
        if self._cam is not None:
            try:
                logger.info("VIRTUAL_CAM", "Stopping Virtual Camera output...")
                self._cam.close()
            except Exception as e:
                logger.error("VIRTUAL_CAM", f"Error closing virtual camera: {e}")
            finally:
                self._cam = None
                self._is_broadcasting = False

    def emergency_shutdown(self) -> None:
        """Immediate killswitch to stop broadcasting in any emergency."""
        logger.warning("VIRTUAL_CAM", "EMERGENCY SHUTDOWN TRIGGERED! Ceasing virtual camera broadcast.")
        self.stop()

    def get_diagnostics(self) -> Dict[str, any]:
        return {
            "is_broadcasting": self._is_broadcasting,
            "backend_available": self._backend_available,
            "backend": self._active_backend or "None",
            "device": self._device_name,
            "resolution": f"{self._width}x{self._height}",
            "target_fps": self._target_fps,
            "actual_fps": round(self._actual_fps, 1),
            "frames_sent": self._frames_sent,
            "dropped_frames": self._dropped_frames,
        }
