"""
PROJECT KYOKKO
Configuration Service
High-performance in-memory cache with database backing for zero-overhead frame loop lookups.
"""

import threading
from typing import Any, Callable, Dict, List, Optional
from database.db_manager import DatabaseManager


class ConfigService:
    _instance: Optional["ConfigService"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigService, cls).__new__(cls)
                cls._instance._init_service()
            return cls._instance

    def _init_service(self):
        self.db = DatabaseManager()
        self._cache: Dict[str, str] = self.db.get_all_settings()
        self._listeners: List[Callable[[str, Any], None]] = []
        self._cache_lock = threading.Lock()

    def get(self, key: str, default: Any = "") -> str:
        with self._cache_lock:
            if key not in self._cache:
                val = self.db.get_setting(key, default)
                self._cache[key] = val
                return val
            return self._cache[key]

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self.get(key, "1" if default else "0").strip().lower()
        return val in ("1", "true", "yes", "on")

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        str_val = str(value)
        with self._cache_lock:
            self._cache[key] = str_val
        self.db.set_setting(key, str_val)
        self._notify_listeners(key, value)

    def add_listener(self, listener: Callable[[str, Any], None]) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[str, Any], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self, key: str, value: Any) -> None:
        for listener in self._listeners:
            try:
                listener(key, value)
            except Exception:
                pass


config = ConfigService()
