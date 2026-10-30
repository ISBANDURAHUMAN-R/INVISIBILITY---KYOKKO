"""
PROJECT KYOKKO
Database Manager (SQLite)
Thread-safe persistence for settings, camera profiles, backgrounds, and activity logs.
"""

from contextlib import contextmanager
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from database.models import (
    ActivityLog,
    BackgroundProfile,
    CameraProfile,
    GestureConfig,
    UserSetting,
)


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[str] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(base_dir, "database")
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, "kyokko.db")
        else:
            self.db_path = db_path

        self._db_lock = threading.Lock()
        self._init_tables()
        self._seed_default_data()
        self._initialized = True

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self) -> None:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()

            # User Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Camera Profiles Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS camera_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    camera_index INTEGER NOT NULL,
                    resolution_w INTEGER NOT NULL,
                    resolution_h INTEGER NOT NULL,
                    fps INTEGER NOT NULL,
                    is_default INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Background Profiles Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS background_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    resolution_w INTEGER NOT NULL,
                    resolution_h INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Gesture Configurations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gesture_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    hand_preference TEXT NOT NULL DEFAULT 'Both',
                    sensitivity REAL NOT NULL DEFAULT 0.45,
                    activation_delay_ms INTEGER NOT NULL DEFAULT 200,
                    release_delay_ms INTEGER NOT NULL DEFAULT 150,
                    cooldown_ms INTEGER NOT NULL DEFAULT 500,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            """)

            # Activity Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)

            conn.commit()

    def _seed_default_data(self) -> None:
        defaults = {
            "app_theme": "dark_purple",
            "default_camera_index": "0",
            "default_resolution_w": "1280",
            "default_resolution_h": "720",
            "default_fps": "30",
            "virtual_camera_name": "KYOKKO Virtual Camera",
            "auto_start_virtual_cam": "0",
            "invisibility_transition_ms": "250",
            "segmentation_model": "0",  # 0 = general, 1 = landscape
            "mask_threshold": "0.55",
            "mask_feather": "7",
            "mask_dilation": "3",
            "show_landmarks": "1",
            "show_mask_overlay": "0",
            "show_hud": "1",
            "mirror_mode": "1",
            "brightness": "0",
            "contrast": "1.0",
            "saturation": "1.0",
            "blur_amount": "0",
            "sharpen_amount": "0.0",
            "color_filter": "Normal",
            "performance_downscale": "1.0",
            "alternative_mode": "none",  # 'none', 'blur', 'virtual_bg'
        }

        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            for key, val in defaults.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO user_settings (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, val, datetime.now().isoformat()),
                )

            # Check if camera profile exists
            cursor.execute("SELECT COUNT(*) as count FROM camera_profiles")
            if cursor.fetchone()["count"] == 0:
                cursor.execute(
                    """INSERT INTO camera_profiles 
                       (name, camera_index, resolution_w, resolution_h, fps, is_default, created_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    ("Integrated HD Camera", 0, 1280, 720, 30, 1, datetime.now().isoformat()),
                )

            # Check if gesture config exists
            cursor.execute("SELECT COUNT(*) as count FROM gesture_configs")
            if cursor.fetchone()["count"] == 0:
                cursor.execute(
                    """INSERT INTO gesture_configs 
                       (name, hand_preference, sensitivity, activation_delay_ms, release_delay_ms, cooldown_ms, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    ("Standard Head-Touch", "Both", 0.58, 120, 120, 300, 1),
                )

            conn.commit()

    # --- Setting Operations ---
    def get_setting(self, key: str, default: Any = "") -> str:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else str(default)

    def set_setting(self, key: str, value: Any) -> None:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO user_settings (key, value, updated_at) 
                   VALUES (?, ?, ?) 
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at""",
                (key, str(value), datetime.now().isoformat()),
            )
            conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    # --- Camera Profiles ---
    def get_camera_profiles(self) -> List[CameraProfile]:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM camera_profiles ORDER BY is_default DESC, id ASC")
            return [
                CameraProfile(
                    id=row["id"],
                    name=row["name"],
                    camera_index=row["camera_index"],
                    resolution_w=row["resolution_w"],
                    resolution_h=row["resolution_h"],
                    fps=row["fps"],
                    is_default=bool(row["is_default"]),
                    created_at=row["created_at"],
                )
                for row in cursor.fetchall()
            ]

    def add_camera_profile(self, profile: CameraProfile) -> int:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            if profile.is_default:
                cursor.execute("UPDATE camera_profiles SET is_default = 0")
            cursor.execute(
                """INSERT INTO camera_profiles 
                   (name, camera_index, resolution_w, resolution_h, fps, is_default, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.name,
                    profile.camera_index,
                    profile.resolution_w,
                    profile.resolution_h,
                    profile.fps,
                    1 if profile.is_default else 0,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    # --- Background Profiles ---
    def get_background_profiles(self) -> List[BackgroundProfile]:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM background_profiles ORDER BY is_active DESC, id DESC")
            return [
                BackgroundProfile(
                    id=row["id"],
                    name=row["name"],
                    image_path=row["image_path"],
                    resolution_w=row["resolution_w"],
                    resolution_h=row["resolution_h"],
                    is_active=bool(row["is_active"]),
                    created_at=row["created_at"],
                )
                for row in cursor.fetchall()
            ]

    def get_active_background_profile(self) -> Optional[BackgroundProfile]:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM background_profiles WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return None
            return BackgroundProfile(
                id=row["id"],
                name=row["name"],
                image_path=row["image_path"],
                resolution_w=row["resolution_w"],
                resolution_h=row["resolution_h"],
                is_active=True,
                created_at=row["created_at"],
            )

    def set_active_background_profile(self, profile_id: int) -> None:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE background_profiles SET is_active = 0")
            cursor.execute("UPDATE background_profiles SET is_active = 1 WHERE id = ?", (profile_id,))
            conn.commit()

    def add_background_profile(self, profile: BackgroundProfile) -> int:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            if profile.is_active:
                cursor.execute("UPDATE background_profiles SET is_active = 0")
            cursor.execute(
                """INSERT INTO background_profiles 
                   (name, image_path, resolution_w, resolution_h, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    profile.name,
                    profile.image_path,
                    profile.resolution_w,
                    profile.resolution_h,
                    1 if profile.is_active else 0,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def delete_background_profile(self, profile_id: int) -> None:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM background_profiles WHERE id = ?", (profile_id,))
            conn.commit()

    # --- Gesture Configurations ---
    def get_active_gesture_config(self) -> GestureConfig:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gesture_configs WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return GestureConfig()
            return GestureConfig(
                id=row["id"],
                name=row["name"],
                hand_preference=row["hand_preference"],
                sensitivity=float(row["sensitivity"]),
                activation_delay_ms=int(row["activation_delay_ms"]),
                release_delay_ms=int(row["release_delay_ms"]),
                cooldown_ms=int(row["cooldown_ms"]),
                is_active=True,
            )

    def update_gesture_config(self, config: GestureConfig) -> None:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            if config.id is not None:
                cursor.execute(
                    """UPDATE gesture_configs 
                       SET name = ?, hand_preference = ?, sensitivity = ?, 
                           activation_delay_ms = ?, release_delay_ms = ?, cooldown_ms = ?, is_active = ?
                       WHERE id = ?""",
                    (
                        config.name,
                        config.hand_preference,
                        config.sensitivity,
                        config.activation_delay_ms,
                        config.release_delay_ms,
                        config.cooldown_ms,
                        1 if config.is_active else 0,
                        config.id,
                    ),
                )
            else:
                cursor.execute(
                    """INSERT INTO gesture_configs 
                       (name, hand_preference, sensitivity, activation_delay_ms, release_delay_ms, cooldown_ms, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, 1)""",
                    (
                        config.name,
                        config.hand_preference,
                        config.sensitivity,
                        config.activation_delay_ms,
                        config.release_delay_ms,
                        config.cooldown_ms,
                    ),
                )
            conn.commit()

    # --- Activity Logs ---
    def add_log(self, level: str, category: str, message: str) -> None:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO activity_logs (timestamp, level, category, message) VALUES (?, ?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), level, category, message),
            )
            conn.commit()

    def get_recent_logs(self, limit: int = 100) -> List[ActivityLog]:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [
                ActivityLog(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    level=row["level"],
                    category=row["category"],
                    message=row["message"],
                )
                for row in cursor.fetchall()
            ]

    def clear_logs(self) -> None:
        with self._db_lock, self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activity_logs")
            conn.commit()
