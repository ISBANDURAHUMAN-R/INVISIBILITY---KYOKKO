"""
PROJECT KYOKKO
MediaPipe Head & Face Detection Module
Accurate head bounding region, temple/forehead/ear touch zones, temporal persistence, and scale normalization.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import cv2
import mediapipe as mp
import numpy as np


@dataclass
class HeadInfo:
    bbox: Tuple[int, int, int, int]           # (x, y, w, h) in pixel coordinates
    center: Tuple[int, int]                    # (cx, cy)
    head_scale: float                          # Characteristic size in pixels
    confidence: float
    keypoints: Dict[str, Tuple[int, int]]      # 'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 'forehead', 'crown'
    touch_zones: List[Tuple[int, int, int]]    # List of (x, y, radius) spheres for head-touch target zones


@dataclass
class HeadDetectionResult:
    heads: List[HeadInfo] = field(default_factory=list)
    primary_head: Optional[HeadInfo] = None
    raw_results: Optional[any] = None


class HeadDetector:
    def __init__(self, min_detection_confidence: float = 0.35):
        self.mp_face = mp.solutions.face_detection
        self.detector = self.mp_face.FaceDetection(
            min_detection_confidence=min_detection_confidence,
            model_selection=1,  # 1 = full range
        )
        self._last_head: Optional[HeadInfo] = None
        self._last_head_time: float = 0.0

    def process(self, frame_bgr: np.ndarray) -> HeadDetectionResult:
        if frame_bgr is None or frame_bgr.size == 0:
            return HeadDetectionResult()

        now = time.time()
        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.detector.process(frame_rgb)

        detected_heads: List[HeadInfo] = []

        if results.detections:
            for detection in results.detections:
                score = detection.score[0]
                box = detection.location_data.relative_bounding_box
                bx = int(box.xmin * w)
                by = int(box.ymin * h)
                bw = int(box.width * w)
                bh = int(box.height * h)

                # Expand box upwards to include forehead and hair crown
                head_x = max(0, bx - int(bw * 0.20))
                head_y = max(0, by - int(bh * 0.40))
                head_w = min(w - head_x, int(bw * 1.40))
                head_h = min(h - head_y, int(bh * 1.55))

                cx = head_x + head_w // 2
                cy = head_y + head_h // 2
                head_scale = max(float(head_w), float(head_h), 50.0)

                # Extract key landmarks
                kps = {}
                for key_id, name in enumerate(["right_eye", "left_eye", "nose", "mouth", "right_ear", "left_ear"]):
                    kp = self.mp_face.get_key_point(detection, key_id)
                    kps[name] = (int(kp.x * w), int(kp.y * h))

                # Synthesize touch zone points: forehead, crown, left temple, right temple
                re = kps.get("right_eye", (cx - int(bw * 0.2), cy - int(bh * 0.1)))
                le = kps.get("left_eye", (cx + int(bw * 0.2), cy - int(bh * 0.1)))
                eye_center_x = (re[0] + le[0]) // 2
                eye_center_y = (re[1] + le[1]) // 2

                forehead = (eye_center_x, max(0, eye_center_y - int(bh * 0.35)))
                crown = (eye_center_x, max(0, head_y + 10))
                right_temple = (max(0, re[0] - int(bw * 0.30)), re[1] - int(bh * 0.15))
                left_temple = (min(w - 1, le[0] + int(bw * 0.30)), le[1] - int(bh * 0.15))

                kps["forehead"] = forehead
                kps["crown"] = crown
                kps["right_temple"] = right_temple
                kps["left_temple"] = left_temple

                # Define touch target zones with generous radii
                zone_radius = int(head_scale * 0.30)
                touch_zones = [
                    (forehead[0], forehead[1], zone_radius),
                    (crown[0], crown[1], zone_radius),
                    (right_temple[0], right_temple[1], zone_radius),
                    (left_temple[0], left_temple[1], zone_radius),
                    (kps["right_ear"][0], kps["right_ear"][1], zone_radius),
                    (kps["left_ear"][0], kps["left_ear"][1], zone_radius),
                    (cx, cy, zone_radius), # Face center
                ]

                head_info = HeadInfo(
                    bbox=(head_x, head_y, head_w, head_h),
                    center=(cx, cy),
                    head_scale=head_scale,
                    confidence=score,
                    keypoints=kps,
                    touch_zones=touch_zones,
                )
                detected_heads.append(head_info)

        # Sort by bounding box area (largest head is primary user)
        detected_heads.sort(key=lambda hd: hd.bbox[2] * hd.bbox[3], reverse=True)
        primary = detected_heads[0] if detected_heads else None

        if primary:
            self._last_head = primary
            self._last_head_time = now
        elif self._last_head and (now - self._last_head_time < 1.2):
            # Temporarily occluded head (e.g. hand touching face): maintain last known head position
            primary = self._last_head
            detected_heads = [primary]

        return HeadDetectionResult(heads=detected_heads, primary_head=primary, raw_results=results)

    def draw_head_overlay(self, frame_bgr: np.ndarray, result: HeadDetectionResult) -> np.ndarray:
        """Draw futuristic holographic targeting ring and touch zones around primary head."""
        if not result.primary_head:
            return frame_bgr

        overlay = frame_bgr.copy()
        head = result.primary_head
        hx, hy, hw, hh = head.bbox

        # Corner brackets around head box
        line_len = int(min(hw, hh) * 0.2)
        color = (180, 50, 240)  # Purple neon

        # Top-left
        cv2.line(overlay, (hx, hy), (hx + line_len, hy), color, 2, cv2.LINE_AA)
        cv2.line(overlay, (hx, hy), (hx, hy + line_len), color, 2, cv2.LINE_AA)
        # Top-right
        cv2.line(overlay, (hx + hw, hy), (hx + hw - line_len, hy), color, 2, cv2.LINE_AA)
        cv2.line(overlay, (hx + hw, hy), (hx + hw, hy + line_len), color, 2, cv2.LINE_AA)
        # Bottom-left
        cv2.line(overlay, (hx, hy + hh), (hx + line_len, hy + hh), color, 2, cv2.LINE_AA)
        cv2.line(overlay, (hx, hy + hh), (hx, hy + hh - line_len), color, 2, cv2.LINE_AA)
        # Bottom-right
        cv2.line(overlay, (hx + hw, hy + hh), (hx + hw - line_len, hy + hh), color, 2, cv2.LINE_AA)
        cv2.line(overlay, (hx + hw, hy + hh), (hx + hw - line_len, hy + hh), color, 2, cv2.LINE_AA)

        # Draw soft touch target nodes
        for zx, zy, _ in head.touch_zones:
            cv2.circle(overlay, (zx, zy), 4, (0, 240, 255), -1, cv2.LINE_AA)

        return cv2.addWeighted(overlay, 0.8, frame_bgr, 0.2, 0)

    def close(self):
        if self.detector:
            self.detector.close()
