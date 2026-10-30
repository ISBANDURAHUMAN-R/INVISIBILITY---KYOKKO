"""
PROJECT KYOKKO
Data Models for SQLite Database
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserSetting:
    key: str
    value: str
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CameraProfile:
    id: Optional[int] = None
    name: str = "Default Camera"
    camera_index: int = 0
    resolution_w: int = 1280
    resolution_h: int = 720
    fps: int = 30
    is_default: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BackgroundProfile:
    id: Optional[int] = None
    name: str = "Studio Clean Background"
    image_path: str = ""
    resolution_w: int = 1280
    resolution_h: int = 720
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GestureConfig:
    id: Optional[int] = None
    name: str = "Default Touch Gesture"
    hand_preference: str = "Both"  # 'Left', 'Right', 'Both'
    sensitivity: float = 0.45      # Normalized head-touch threshold distance
    activation_delay_ms: int = 200 # Time hand must touch head before triggering
    release_delay_ms: int = 150    # Time hand must be away before restoring
    cooldown_ms: int = 500         # Min time between state flips
    is_active: bool = True


@dataclass
class ActivityLog:
    id: Optional[int] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    level: str = "INFO"            # 'INFO', 'WARNING', 'ERROR', 'GESTURE'
    category: str = "SYSTEM"       # 'CAMERA', 'GESTURE', 'VIRTUAL_CAM', 'INVISIBILITY', 'UI'
    message: str = ""
