"""
PROJECT KYOKKO
Unit Tests: Invisibility Engine Subsystem
"""

import tempfile
import unittest
import numpy as np
from invisibility.background_capture import BackgroundCapture
from invisibility.background_restoration import BackgroundRestorer
from invisibility.mask_processing import MaskProcessor


class TestInvisibilitySubsystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bg_capture = BackgroundCapture(storage_dir=self.temp_dir)
        self.mask_processor = MaskProcessor(threshold=0.5, feather=5, dilation=2)
        self.restorer = BackgroundRestorer(transition_ms=100)

    def test_mask_processing(self):
        raw_mask = np.zeros((100, 100), dtype=np.float32)
        # Person in center circle
        raw_mask[30:70, 30:70] = 0.9

        refined = self.mask_processor.refine(raw_mask)
        self.assertEqual(refined.shape, (100, 100))
        self.assertEqual(refined.dtype, np.float32)
        # Person region should be high confidence
        self.assertGreater(refined[50, 50], 0.8)
        # Background should be 0.0
        self.assertAlmostEqual(refined[5, 5], 0.0, places=1)

    def test_background_capture_and_restoration(self):
        cam_frame = np.full((100, 100, 3), 200, dtype=np.uint8)  # White-ish
        bg_frame = np.full((100, 100, 3), 50, dtype=np.uint8)    # Dark background

        # Capture background
        success = self.bg_capture.capture_instant(bg_frame, name="Test BG")
        self.assertTrue(success)
        self.assertTrue(self.bg_capture.has_background())

        # Create person mask
        person_mask = np.zeros((100, 100), dtype=np.float32)
        person_mask[20:80, 20:80] = 1.0  # Center is person

        # Visible state (target = False)
        self.restorer.set_target_state(False)
        out_vis = self.restorer.restore(cam_frame, bg_frame, person_mask)
        # Should match camera frame
        self.assertEqual(int(out_vis[50, 50, 0]), 200)

        # Trigger Invisibility
        self.restorer.set_target_state(True)
        # Transition over time
        import time
        time.sleep(0.12)
        out_invis = self.restorer.restore(cam_frame, bg_frame, person_mask)

        # In center (where person was), pixels should now match background (50) instead of camera (200)!
        self.assertAlmostEqual(float(out_invis[50, 50, 0]), 50.0, delta=15.0)
        # Outside person (where person_mask was 0), should still match camera (200)
        self.assertEqual(int(out_invis[5, 5, 0]), 200)

    def test_multi_frame_denoised_capture(self):
        frames = [np.random.randint(40, 60, (50, 50, 3), dtype=np.uint8) for _ in range(5)]
        success = self.bg_capture.capture_denoised(frames, name="Denoised BG")
        self.assertTrue(success)
        self.assertIsNotNone(self.bg_capture.current_background)


if __name__ == "__main__":
    unittest.main()
