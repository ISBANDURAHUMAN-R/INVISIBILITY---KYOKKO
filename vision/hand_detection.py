"""
PROJECT KYOKKO
MediaPipe Hand Detection Module
Real-time tracking of hand 3D landmarks, handedness, and fingertip keypoints.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np


@dataclass
class HandInfo:
    label: str  # 'Left' or 'Right'
    score: float
    landmarks: List[Tuple[float, float, float]]  # Normalized (x, y, z)
    pixel_landmarks: List[Tuple[int, int]]       # (x, y) in pixel coords
    keypoints: Dict[str, Tuple[int, int]]        # 'index_tip', 'thumb_tip', 'middle_tip', 'wrist', 'palm'


@dataclass
class HandDetectionResult:
    hands: List[HandInfo] = field(default_factory=list)
    raw_results: Optional[any] = None


class HandDetector:
    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.mp_draw = mp.solutions.drawing_utils

    def process(self, frame_bgr: np.ndarray) -> HandDetectionResult:
        if frame_bgr is None or frame_bgr.size == 0:
            return HandDetectionResult()

        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        detected_hands: List[HandInfo] = []
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                label = handedness.classification[0].label
                score = handedness.classification[0].score

                norm_pts = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                pixel_pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

                # Fingertips and key landmarks
                index_tip = pixel_pts[8]
                thumb_tip = pixel_pts[4]
                middle_tip = pixel_pts[12]
                ring_tip = pixel_pts[16]
                pinky_tip = pixel_pts[20]
                wrist = pixel_pts[0]

                # Palm center estimated from wrist and MCP knuckles (0, 5, 9, 13, 17)
                palm_x = int((pixel_pts[0][0] + pixel_pts[5][0] + pixel_pts[9][0] + pixel_pts[13][0] + pixel_pts[17][0]) / 5)
                palm_y = int((pixel_pts[0][1] + pixel_pts[5][1] + pixel_pts[9][1] + pixel_pts[13][1] + pixel_pts[17][1]) / 5)

                keypoints = {
                    "index_tip": index_tip,
                    "thumb_tip": thumb_tip,
                    "middle_tip": middle_tip,
                    "ring_tip": ring_tip,
                    "pinky_tip": pinky_tip,
                    "wrist": wrist,
                    "palm": (palm_x, palm_y),
                }

                detected_hands.append(
                    HandInfo(
                        label=label,
                        score=score,
                        landmarks=norm_pts,
                        pixel_landmarks=pixel_pts,
                        keypoints=keypoints,
                    )
                )

        return HandDetectionResult(hands=detected_hands, raw_results=results)

    def draw_landmarks(self, frame_bgr: np.ndarray, result: HandDetectionResult) -> np.ndarray:
        """Draw sleek neon purple / cyan aesthetic hand connections and keypoint halos."""
        if not result.hands:
            return frame_bgr

        overlay = frame_bgr.copy()
        for hand in result.hands:
            pts = hand.pixel_landmarks
            # Draw bones
            connections = self.mp_hands.HAND_CONNECTIONS
            for p1_idx, p2_idx in connections:
                cv2.line(overlay, pts[p1_idx], pts[p2_idx], (255, 128, 0), 2, cv2.LINE_AA)

            # Draw glowing joints
            for idx, pt in enumerate(pts):
                if idx in (4, 8, 12, 16, 20):  # Fingertips
                    cv2.circle(overlay, pt, 6, (255, 0, 190), -1, cv2.LINE_AA)
                    cv2.circle(overlay, pt, 9, (255, 200, 255), 1, cv2.LINE_AA)
                else:
                    cv2.circle(overlay, pt, 3, (200, 100, 255), -1, cv2.LINE_AA)

            # Label Hand
            wrist = hand.keypoints["wrist"]
            cv2.putText(
                overlay,
                f"{hand.label} ({int(hand.score * 100)}%)",
                (wrist[0] - 20, wrist[1] + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        # Smooth blend overlay with original frame
        return cv2.addWeighted(overlay, 0.85, frame_bgr, 0.15, 0)

    def close(self):
        if self.hands:
            self.hands.close()
