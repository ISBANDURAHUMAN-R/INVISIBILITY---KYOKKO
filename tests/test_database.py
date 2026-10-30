"""
PROJECT KYOKKO
Unit Tests: Database Subsystem
"""

import os
import tempfile
import unittest
from database.db_manager import DatabaseManager
from database.models import BackgroundProfile, CameraProfile, GestureConfig


class TestDatabaseSubsystem(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        # Reset singleton for testing
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.temp_db_path)

    def tearDown(self):
        DatabaseManager._instance = None
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_settings_get_set(self):
        self.db.set_setting("test_key", "hello_world")
        val = self.db.get_setting("test_key")
        self.assertEqual(val, "hello_world")

    def test_camera_profiles(self):
        prof = CameraProfile(name="Test Cam", camera_index=1, resolution_w=1920, resolution_h=1080, fps=60)
        prof_id = self.db.add_camera_profile(prof)
        self.assertIsNotNone(prof_id)

        profiles = self.db.get_camera_profiles()
        self.assertTrue(any(p.name == "Test Cam" for p in profiles))

    def test_background_profiles(self):
        bg = BackgroundProfile(name="Empty Studio", image_path="/dummy/path.png", resolution_w=1280, resolution_h=720, is_active=True)
        bg_id = self.db.add_background_profile(bg)
        self.assertIsNotNone(bg_id)

        active = self.db.get_active_background_profile()
        self.assertIsNotNone(active)
        self.assertEqual(active.name, "Empty Studio")

    def test_gesture_configs(self):
        cfg = self.db.get_active_gesture_config()
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.hand_preference, "Both")

        cfg.sensitivity = 0.60
        self.db.update_gesture_config(cfg)
        updated = self.db.get_active_gesture_config()
        self.assertAlmostEqual(updated.sensitivity, 0.60, places=2)

    def test_activity_logs(self):
        self.db.add_log("INFO", "TEST", "Testing activity log insertion")
        logs = self.db.get_recent_logs(limit=10)
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0].category, "TEST")


if __name__ == "__main__":
    unittest.main()
