"""
PROJECT KYOKKO
Centralized Logger Service
Dual logging to file, SQLite database, and real-time UI subscribers.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Callable, List, Optional
from database.db_manager import DatabaseManager


class LoggerService:
    _instance: Optional["LoggerService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerService, cls).__new__(cls)
            cls._instance._init_logger()
        return cls._instance

    def _init_logger(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "kyokko.log")

        self.logger = logging.getLogger("KYOKKO")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        # File Handler (5 MB max, 3 backups)
        file_handler = RotatingFileHandler(
            self.log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Stream Handler for console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(file_formatter)
        self.logger.addHandler(console_handler)

        self.db = DatabaseManager()
        self._subscribers: List[Callable[[str, str, str], None]] = []

    def subscribe(self, callback: Callable[[str, str, str], None]) -> None:
        """Subscribe to live log events (level, category, message)."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[str, str, str], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify(self, level: str, category: str, message: str) -> None:
        for cb in self._subscribers:
            try:
                cb(level, category, message)
            except Exception:
                pass

    def info(self, category: str, message: str) -> None:
        self.logger.info(f"[{category}] {message}")
        self.db.add_log("INFO", category, message)
        self._notify("INFO", category, message)

    def warning(self, category: str, message: str) -> None:
        self.logger.warning(f"[{category}] {message}")
        self.db.add_log("WARNING", category, message)
        self._notify("WARNING", category, message)

    def error(self, category: str, message: str) -> None:
        self.logger.error(f"[{category}] {message}")
        self.db.add_log("ERROR", category, message)
        self._notify("ERROR", category, message)

    def gesture(self, message: str) -> None:
        self.logger.info(f"[GESTURE] {message}")
        self.db.add_log("GESTURE", "GESTURE", message)
        self._notify("GESTURE", "GESTURE", message)


# Global helper instance
logger = LoggerService()
