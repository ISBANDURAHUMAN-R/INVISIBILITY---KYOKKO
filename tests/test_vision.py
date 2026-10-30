"""
PROJECT KYOKKO
Unit Tests: Vision & Gesture Subsystem
"""

import unittest
import numpy as np
from vision.gesture_recognition import GestureRecognizer, GestureStateName
from vision.hand_detection import HandDetectionResult, HandDetector, HandInfo
from vision.head_detection import HeadDetectionResult, HeadDetector, HeadInfo
from vision.person_segmentation import PersonSegmenter


class TestVisionSubsystem(unittest.TestCase):
    def setUp(self):
        self.hand_detector = HandDetector()
        self.head_detector = HeadDetector()
        self.segmenter = PersonSegmenter()
        self.gesture_rec = GestureRecognizer(
            sensitivity=0.45,
            activation_delay_ms=100,
            release_delay_ms=100,
            cooldown_ms=100,
        )

    def tearDown(self):
        self.hand_detector.close()
        self.head_detector.close()
        self.segmenter.close()

    def test_detector_empty_frame(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        hands = self.hand_detector.process(frame)
        self.assertIsInstance(hands, HandDetectionResult)
        self.assertEqual(len(hands.hands), 0)

        heads = self.head_detector.process(frame)
        self.assertIsInstance(heads, HeadDetectionResult)
        self.assertIsNone(heads.primary_head)

        seg = self.segmenter.process(frame)
        self.assertEqual(seg.mask.shape, (480, 640))
        self.assertFalse(seg.has_person)

    def test_gesture_logic_simulation(self):
        # Create synthetic HeadInfo
        head = HeadInfo(
            bbox=(200, 100, 150, 150),
            center=(275, 175),
            head_scale=150.0,
            confidence=0.95,
            keypoints={"forehead": (275, 120), "right_temple": (220, 140), "left_temple": (330, 140),
                       "right_ear": (210, 170), "left_ear": (340, 170), "crown": (275, 105), "nose": (275, 160)},
            touch_zones=[(275, 120, 25), (220, 140, 25), (330, 140, 25)],
        )
        head_res = HeadDetectionResult(heads=[head], primary_head=head)

        # 1. Hand touching temple (e.g. at (225, 142))
        touching_hand = HandInfo(
            label="Right",
            score=0.92,
            landmarks=[(0, 0, 0)] * 21,
            pixel_landmarks=[(225, 142)] * 21,
            keypoints={
                "index_tip": (225, 142),
                "thumb_tip": (225, 142),
                "middle_tip": (225, 142),
                "ring_tip": (225, 142),
                "pinky_tip": (225, 142),
                "wrist": (225, 200),
                "palm": (225, 160),
            },
        )
        hand_res = HandDetectionResult(hands=[touching_hand])

        # First frame touching: should be CONFIRMING
        status = self.gesture_rec.process(hand_res, head_res)
        self.assertIn(status.state, (GestureStateName.CONFIRMING, GestureStateName.ACTIVE))
        self.assertLess(status.normalized_distance, 0.45)

        # Simulate holding for > 150ms
        import time
        time.sleep(0.12)
        status2 = self.gesture_rec.process(hand_res, head_res)
        self.assertTrue(status2.is_triggered)
        self.assertEqual(status2.state, GestureStateName.ACTIVE)

        # 2. Hand moves far away (e.g. to (500, 400))
        far_hand = HandInfo(
            label="Right",
            score=0.90,
            landmarks=[(0, 0, 0)] * 21,
            pixel_landmarks=[(500, 400)] * 21,
            keypoints={
                "index_tip": (500, 400),
                "thumb_tip": (500, 400),
                "middle_tip": (500, 400),
                "ring_tip": (500, 400),
                "pinky_tip": (500, 400),
                "wrist": (500, 450),
                "palm": (500, 420),
            },
        )
        far_hand_res = HandDetectionResult(hands=[far_hand])

        # First frame releasing: still invisible while releasing
        status3 = self.gesture_rec.process(far_hand_res, head_res)
        self.assertTrue(status3.is_triggered)
        self.assertEqual(status3.state, GestureStateName.RELEASING)

        # After release delay: returns to visible (IDLE)
        time.sleep(0.12)
        status4 = self.gesture_rec.process(far_hand_res, head_res)
        self.assertFalse(status4.is_triggered)
        self.assertEqual(status4.state, GestureStateName.IDLE)


if __name__ == "__main__":
    unittest.main()
