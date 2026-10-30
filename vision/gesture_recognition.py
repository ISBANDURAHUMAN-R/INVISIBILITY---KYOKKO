"""
PROJECT KYOKKO
Gesture Recognition Engine
Precise hand-to-head touch detection, false-positive filtering, and hysteresis state machine.
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from vision.hand_detection import HandDetectionResult, HandInfo
from vision.head_detection import HeadDetectionResult, HeadInfo


class GestureStateName(str, Enum):
    IDLE = "IDLE"
    CONFIRMING = "CONFIRMING"
    ACTIVE = "ACTIVE"
    RELEASING = "RELEASING"
    COOLDOWN = "COOLDOWN"


@dataclass
class GestureStatus:
    is_triggered: bool = False              # Whether invisibility should be active
    state: GestureStateName = GestureStateName.IDLE
    confidence: float = 0.0                 # 0.0 to 1.0
    normalized_distance: float = 1.0        # < sensitivity means touching
    pixel_distance: float = 999.0
    active_hand: str = "None"               # 'Left', 'Right', 'None'
    touch_point: Optional[Tuple[int, int]] = None
    target_node: Optional[Tuple[int, int]] = None
    progress: float = 0.0                   # 0.0 to 1.0 (activation or release progress)
    message: str = "Ready"


class GestureRecognizer:
    def __init__(
        self,
        hand_preference: str = "Both",     # 'Left', 'Right', 'Both'
        sensitivity: float = 0.58,         # Normalized distance threshold
        activation_delay_ms: int = 120,    # Hold duration to activate
        release_delay_ms: int = 120,       # Hold duration away to deactivate
        cooldown_ms: int = 300,            # Min cooldown between state flips
        enabled: bool = True,
    ):
        self.hand_preference = hand_preference
        self.sensitivity = sensitivity
        self.activation_delay_ms = activation_delay_ms
        self.release_delay_ms = release_delay_ms
        self.cooldown_ms = cooldown_ms
        self.enabled = enabled

        # State tracking
        self._current_state = GestureStateName.IDLE
        self._is_invisibility_active = False
        self._touch_start_time: Optional[float] = None
        self._release_start_time: Optional[float] = None
        self._cooldown_end_time: float = 0.0

        # Smoothing
        self._distance_ema: float = 1.0

    def set_config(
        self,
        hand_preference: Optional[str] = None,
        sensitivity: Optional[float] = None,
        activation_delay_ms: Optional[int] = None,
        release_delay_ms: Optional[int] = None,
        cooldown_ms: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        if hand_preference is not None:
            self.hand_preference = hand_preference
        if sensitivity is not None:
            self.sensitivity = max(0.1, min(1.0, sensitivity))
        if activation_delay_ms is not None:
            self.activation_delay_ms = max(50, activation_delay_ms)
        if release_delay_ms is not None:
            self.release_delay_ms = max(50, release_delay_ms)
        if cooldown_ms is not None:
            self.cooldown_ms = max(0, cooldown_ms)
        if enabled is not None:
            self.enabled = enabled

    def process(
        self,
        hand_result: HandDetectionResult,
        head_result: HeadDetectionResult,
    ) -> GestureStatus:
        now = time.time()

        if not self.enabled:
            self._is_invisibility_active = False
            self._current_state = GestureStateName.IDLE
            return GestureStatus(
                is_triggered=False,
                state=GestureStateName.IDLE,
                confidence=0.0,
                normalized_distance=1.0,
                message="Gesture Detection Disabled",
            )

        # In cooldown?
        if now < self._cooldown_end_time:
            progress = max(0.0, (self._cooldown_end_time - now) / (self.cooldown_ms / 1000.0))
            return GestureStatus(
                is_triggered=self._is_invisibility_active,
                state=GestureStateName.COOLDOWN,
                confidence=0.0,
                normalized_distance=self._distance_ema,
                progress=progress,
                message=f"Cooldown ({int((self._cooldown_end_time - now)*1000)}ms)",
            )

        head = head_result.primary_head
        if not head or not hand_result.hands:
            # No head or hand detected -> process release
            return self._handle_touch_absence(now)

        # Filter hands by preference
        valid_hands: List[HandInfo] = []
        for hand in hand_result.hands:
            if self.hand_preference == "Both":
                valid_hands.append(hand)
            elif self.hand_preference == "Left" and hand.label == "Left":
                valid_hands.append(hand)
            elif self.hand_preference == "Right" and hand.label == "Right":
                valid_hands.append(hand)

        if not valid_hands:
            return self._handle_touch_absence(now)

        # Calculate closest hand-to-head touch distance
        min_dist = float("inf")
        best_touch_pt = None
        best_target_node = None
        best_hand_label = "None"

        hx, hy, hw, hh = head.bbox
        head_scale = max(head.head_scale, 50.0)
        neck_threshold_y = hy + hh * 1.45  # Hand must be higher than lower neck/chest

        for hand in valid_hands:
            # Probe all key hand points: all 5 fingertips, knuckles, palm, wrist
            probe_pts = list(hand.keypoints.values())
            if hand.pixel_landmarks and len(hand.pixel_landmarks) >= 21:
                # Add MCP knuckles (5, 9, 13, 17) and DIP joints (7, 11, 15, 19)
                probe_pts.extend([hand.pixel_landmarks[idx] for idx in (5, 7, 9, 11, 13, 15, 17, 19)])

            for px, py in probe_pts:
                # Vertical filter: reject hands resting down on chest or desk
                if py > neck_threshold_y:
                    continue

                # Test distance against each touch target node
                for zx, zy, radius in head.touch_zones:
                    d = math.hypot(px - zx, py - zy)
                    # Effective distance factoring node radius
                    effective_d = max(0.0, d - radius * 0.6)
                    if effective_d < min_dist:
                        min_dist = effective_d
                        best_touch_pt = (px, py)
                        best_target_node = (zx, zy)
                        best_hand_label = hand.label

                # Also test distance against head bounding box perimeter
                box_d = self._point_to_box_distance(px, py, hx, hy, hw, hh)
                if box_d < min_dist:
                    min_dist = box_d
                    best_touch_pt = (px, py)
                    best_target_node = (
                        max(hx, min(hx + hw, px)),
                        max(hy, min(hy + hh, py)),
                    )
                    best_hand_label = hand.label

        # Normalize distance relative to head scale
        if min_dist == float("inf"):
            return self._handle_touch_absence(now)

        normalized_dist = min_dist / head_scale
        # Fast responsive EMA smoothing
        self._distance_ema = 0.85 * normalized_dist + 0.15 * self._distance_ema

        # Calculate confidence: 1.0 when touching (d=0), 0.0 when d >= sensitivity * 1.5
        confidence = max(0.0, min(1.0, 1.0 - (self._distance_ema / (self.sensitivity * 1.5))))

        is_touching = self._distance_ema <= self.sensitivity

        if is_touching:
            return self._handle_touch_presence(
                now,
                self._distance_ema,
                min_dist,
                confidence,
                best_hand_label,
                best_touch_pt,
                best_target_node,
            )
        else:
            return self._handle_touch_absence(
                now,
                self._distance_ema,
                min_dist,
                confidence,
                best_hand_label,
                best_touch_pt,
                best_target_node,
            )

    def _handle_touch_presence(
        self,
        now: float,
        norm_dist: float,
        pixel_dist: float,
        confidence: float,
        hand_label: str,
        touch_pt: Optional[Tuple[int, int]],
        target_node: Optional[Tuple[int, int]],
    ) -> GestureStatus:
        self._release_start_time = None

        if not self._is_invisibility_active:
            # Currently visible, hand touching head
            if self._touch_start_time is None:
                self._touch_start_time = now

            elapsed_ms = (now - self._touch_start_time) * 1000.0
            progress = min(1.0, elapsed_ms / max(1.0, float(self.activation_delay_ms)))

            if elapsed_ms >= self.activation_delay_ms:
                # Confirmed! Flip to invisible!
                self._is_invisibility_active = True
                self._current_state = GestureStateName.ACTIVE
                self._touch_start_time = None
                return GestureStatus(
                    is_triggered=True,
                    state=GestureStateName.ACTIVE,
                    confidence=confidence,
                    normalized_distance=norm_dist,
                    pixel_distance=pixel_dist,
                    active_hand=hand_label,
                    touch_point=touch_pt,
                    target_node=target_node,
                    progress=1.0,
                    message="Invisibility ACTIVATED",
                )
            else:
                self._current_state = GestureStateName.CONFIRMING
                return GestureStatus(
                    is_triggered=False,
                    state=GestureStateName.CONFIRMING,
                    confidence=confidence,
                    normalized_distance=norm_dist,
                    pixel_distance=pixel_dist,
                    active_hand=hand_label,
                    touch_point=touch_pt,
                    target_node=target_node,
                    progress=progress,
                    message=f"Confirming ({int(progress * 100)}%)",
                )
        else:
            # Already invisible, touching maintained
            self._current_state = GestureStateName.ACTIVE
            return GestureStatus(
                is_triggered=True,
                state=GestureStateName.ACTIVE,
                confidence=confidence,
                normalized_distance=norm_dist,
                pixel_distance=pixel_dist,
                active_hand=hand_label,
                touch_point=touch_pt,
                target_node=target_node,
                progress=1.0,
                message="Invisibility ACTIVE",
            )

    def _handle_touch_absence(
        self,
        now: float,
        norm_dist: float = 1.0,
        pixel_dist: float = 999.0,
        confidence: float = 0.0,
        hand_label: str = "None",
        touch_pt: Optional[Tuple[int, int]] = None,
        target_node: Optional[Tuple[int, int]] = None,
    ) -> GestureStatus:
        self._touch_start_time = None

        if self._is_invisibility_active:
            # Currently invisible, hand has released head
            if self._release_start_time is None:
                self._release_start_time = now

            elapsed_ms = (now - self._release_start_time) * 1000.0
            progress = min(1.0, elapsed_ms / max(1.0, float(self.release_delay_ms)))

            if elapsed_ms >= self.release_delay_ms:
                # Confirmed release! Flip back to visible!
                self._is_invisibility_active = False
                self._current_state = GestureStateName.IDLE
                self._release_start_time = None
                self._cooldown_end_time = now + (self.cooldown_ms / 1000.0)
                return GestureStatus(
                    is_triggered=False,
                    state=GestureStateName.IDLE,
                    confidence=confidence,
                    normalized_distance=norm_dist,
                    pixel_distance=pixel_dist,
                    active_hand=hand_label,
                    progress=0.0,
                    message="Visibility Restored",
                )
            else:
                self._current_state = GestureStateName.RELEASING
                return GestureStatus(
                    is_triggered=True,  # Still invisible while releasing
                    state=GestureStateName.RELEASING,
                    confidence=confidence,
                    normalized_distance=norm_dist,
                    pixel_distance=pixel_dist,
                    active_hand=hand_label,
                    progress=progress,
                    message=f"Releasing ({int((1.0 - progress) * 100)}%)",
                )
        else:
            self._current_state = GestureStateName.IDLE
            return GestureStatus(
                is_triggered=False,
                state=GestureStateName.IDLE,
                confidence=confidence,
                normalized_distance=norm_dist,
                pixel_distance=pixel_dist,
                active_hand=hand_label,
                touch_point=touch_pt,
                target_node=target_node,
                progress=0.0,
                message="Awaiting Gesture",
            )

    def draw_debug_overlay(self, frame_bgr: np.ndarray, status: GestureStatus) -> np.ndarray:
        """Render touch vector and target indicator onto frame."""
        if status.touch_point and status.target_node:
            overlay = frame_bgr.copy()
            tp = status.touch_point
            tn = status.target_node

            # Line connecting fingertip to target zone
            color = (0, 255, 128) if status.is_triggered else (0, 165, 255)
            cv2.line(overlay, tp, tn, color, 2, cv2.LINE_AA)
            cv2.circle(overlay, tp, 5, (0, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(overlay, tn, 7, color, 2, cv2.LINE_AA)

            # Touch distance label
            mid_x = (tp[0] + tn[0]) // 2
            mid_y = (tp[1] + tn[1]) // 2
            label = f"{status.normalized_distance:.2f}"
            cv2.putText(overlay, label, (mid_x, mid_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

            return cv2.addWeighted(overlay, 0.85, frame_bgr, 0.15, 0)
        return frame_bgr

    def _point_to_box_distance(self, px: int, py: int, bx: int, by: int, bw: int, bh: int) -> float:
        # Distance from point (px, py) to axis-aligned box (bx, by, bw, bh)
        cx = max(bx, min(bx + bw, px))
        cy = max(by, min(by + bh, py))
        return math.hypot(px - cx, py - cy)

    def reset(self):
        self._current_state = GestureStateName.IDLE
        self._is_invisibility_active = False
        self._touch_start_time = None
        self._release_start_time = None
        self._cooldown_end_time = 0.0
