"""
PROJECT KYOKKO
Unit Tests: Camera & Device Subsystem
"""

import unittest
from camera.camera_manager import CameraManager
from camera.virtual_camera import VirtualCamera
from utils.system_info import check_virtual_camera_backends, enumerate_webcams


class TestCameraSubsystem(unittest.TestCase):
    def setUp(self):
        self.cam_mgr = CameraManager()
        self.vcam = VirtualCamera()

    def tearDown(self):
        self.cam_mgr.stop()
        self.vcam.stop()

    def test_webcam_enumeration(self):
        cams = enumerate_webcams(max_test=2)
        self.assertIsInstance(cams, list)
        # We previously detected Camera 0 on this system
        if cams:
            first_cam = cams[0]
            self.assertIn("index", first_cam)
            self.assertIn("name", first_cam)
            self.assertIn("default_width", first_cam)

    def test_virtual_cam_diagnostics(self):
        diag = self.vcam.get_diagnostics()
        self.assertIn("is_broadcasting", diag)
        self.assertIn("backend_available", diag)
        self.assertIn("dropped_frames", diag)

    def test_backend_check(self):
        status = check_virtual_camera_backends()
        self.assertIn("obs_installed", status)
        self.assertIn("pyvirtualcam_available", status)


if __name__ == "__main__":
    unittest.main()
