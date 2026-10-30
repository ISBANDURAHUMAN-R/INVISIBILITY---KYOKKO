"""
PROJECT KYOKKO
Background Capture & Recalibration Module
Multi-frame noise reduction, automatic background persistence, and profile management.
"""

import os
import time
from typing import List, Optional, Tuple
import cv2
import numpy as np
from database.db_manager import DatabaseManager
from database.models import BackgroundProfile
from services.logger_service import logger


class BackgroundCapture:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.storage_dir = os.path.join(base_dir, "assets", "backgrounds")
        else:
            self.storage_dir = storage_dir

        os.makedirs(self.storage_dir, exist_ok=True)
        self.db = DatabaseManager()
        self._current_background: Optional[np.ndarray] = None
        self._load_active_background()

    def _load_active_background(self) -> None:
        active_prof = self.db.get_active_background_profile()
        if active_prof and os.path.exists(active_prof.image_path):
            img = cv2.imread(active_prof.image_path)
            if img is not None:
                self._current_background = img
                logger.info("INVISIBILITY", f"Loaded active background: {active_prof.name} ({img.shape[1]}x{img.shape[0]})")

    @property
    def current_background(self) -> Optional[np.ndarray]:
        return self._current_background

    def has_background(self) -> bool:
        return self._current_background is not None

    def capture_instant(self, frame: np.ndarray, name: str = "Captured Background") -> bool:
        """Capture a single frame as background."""
        if frame is None or frame.size == 0:
            return False

        h, w = frame.shape[:2]
        timestamp = int(time.time())
        filename = f"bg_{timestamp}_{w}x{h}.png"
        filepath = os.path.join(self.storage_dir, filename)

        cv2.imwrite(filepath, frame)
        self._current_background = frame.copy()

        profile = BackgroundProfile(
            name=f"{name} ({w}x{h})",
            image_path=filepath,
            resolution_w=w,
            resolution_h=h,
            is_active=True,
        )
        self.db.add_background_profile(profile)
        logger.info("INVISIBILITY", f"Saved new background: {filepath}")
        return True

    def capture_denoised(self, frames: List[np.ndarray], name: str = "Studio Calibrated Background") -> bool:
        """Combine multiple frames using temporal median filtering to remove noise and grain."""
        if not frames:
            return False

        h, w = frames[0].shape[:2]
        valid_frames = [f for f in frames if f.shape[:2] == (h, w)]
        if not valid_frames:
            return False

        # Temporal median filter
        stack = np.stack(valid_frames, axis=0)  # (N, H, W, 3)
        denoised = np.median(stack, axis=0).astype(np.uint8)

        return self.capture_instant(denoised, name=name)

    def import_image(self, file_path: str) -> bool:
        """Load background from external image file."""
        if not os.path.exists(file_path):
            return False

        img = cv2.imread(file_path)
        if img is None:
            return False

        h, w = img.shape[:2]
        filename = f"import_{int(time.time())}_{os.path.basename(file_path)}"
        target_path = os.path.join(self.storage_dir, filename)
        cv2.imwrite(target_path, img)

        self._current_background = img
        profile = BackgroundProfile(
            name=f"Imported: {os.path.basename(file_path)}",
            image_path=target_path,
            resolution_w=w,
            resolution_h=h,
            is_active=True,
        )
        self.db.add_background_profile(profile)
        return True

    def get_aligned_background(self, target_w: int, target_h: int) -> Optional[np.ndarray]:
        """Ensure background matches current camera resolution."""
        if self._current_background is None:
            return None

        bh, bw = self._current_background.shape[:2]
        if bw == target_w and bh == target_h:
            return self._current_background

        # Resize to match camera frame exactly
        return cv2.resize(self._current_background, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

    def clear(self) -> None:
        self._current_background = None
