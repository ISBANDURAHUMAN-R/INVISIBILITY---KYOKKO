"""
PROJECT KYOKKO
Real-Time Computer Vision Pipeline Thread
High-performance decoupled worker thread running video capture, vision inference,
invisibility compositing, and virtual camera streaming at up to 60 FPS.
"""

import time
from typing import List, Optional
import cv2
import numpy as np
from PySide6.QtCore import QThread
from camera.camera_manager import CameraManager
from camera.virtual_camera import VirtualCamera
from core.events import events
from effects.image_effects import EffectsConfig, ImageEffects
from invisibility.invisibility_engine import InvisibilityEngine
from services.config_service import config
from services.logger_service import logger
from settings.app_settings import settings
from vision.gesture_recognition import GestureRecognizer, GestureStatus
from vision.hand_detection import HandDetector
from vision.head_detection import HeadDetector


class ProcessingPipeline(QThread):
    def __init__(self):
        super(ProcessingPipeline, self).__init__()
        self._is_running: bool = False

        # Core subsystems
        self.camera = CameraManager()
        self.virtual_cam = VirtualCamera()
        self.hand_detector = HandDetector()
        self.head_detector = HeadDetector()
        self.gesture_recognizer = GestureRecognizer()
        self.effects = ImageEffects()
        self.invisibility_engine = InvisibilityEngine()

        # Calibration queue
        self._calibrating: bool = False
        self._calibration_frames: List[np.ndarray] = []
        self._calibration_target_count: int = 12

        # Telemetry
        self._pipeline_fps_counter: int = 0
        self._pipeline_fps_start: float = time.time()
        self._actual_pipeline_fps: float = 0.0
        self._last_latency_ms: float = 0.0

        # Load initial configs
        self.reload_configuration()

    def reload_configuration(self) -> None:
        """Synchronize active pipeline with current settings and database configurations."""
        gesture_cfg = self.invisibility_engine.bg_capture.db.get_active_gesture_config()
        self.gesture_recognizer.set_config(
            hand_preference=gesture_cfg.hand_preference,
            sensitivity=gesture_cfg.sensitivity,
            activation_delay_ms=gesture_cfg.activation_delay_ms,
            release_delay_ms=gesture_cfg.release_delay_ms,
            cooldown_ms=gesture_cfg.cooldown_ms,
            enabled=gesture_cfg.is_active,
        )

        self.invisibility_engine.restorer.transition_ms = settings.transition_ms
        self.invisibility_engine.mask_processor.update_params(
            threshold=settings.mask_threshold,
            feather=settings.mask_feather,
            dilation=settings.mask_dilation,
        )
        self.invisibility_engine.segmenter.set_model(settings.segmentation_model)

        self.effects.update_config(
            brightness=config.get_int("brightness", 0),
            contrast=config.get_float("contrast", 1.0),
            saturation=config.get_float("saturation", 1.0),
            blur_amount=config.get_int("blur_amount", 0),
            sharpen_amount=config.get_float("sharpen_amount", 0.0),
            color_filter=config.get("color_filter", "Normal"),
            mirror_mode=settings.mirror_mode,
        )

    def trigger_calibration(self) -> None:
        """Trigger accumulation of multi-frame empty room background."""
        self._calibration_frames.clear()
        self._calibrating = True
        logger.info("INVISIBILITY", "Starting background frame accumulation for calibration...")

    def run(self) -> None:
        self._is_running = True
        logger.info("PIPELINE", "Processing Pipeline thread started.")

        # Start camera hardware
        cam_idx = settings.camera_index
        res_w = settings.resolution_w
        res_h = settings.resolution_h
        target_fps = settings.fps

        if not self.camera.start(cam_idx, res_w, res_h, target_fps):
            events.error_occurred.emit("CAMERA", f"Could not open camera device {cam_idx}")

        frame_duration = 1.0 / max(10, target_fps)

        while self._is_running:
            loop_start = time.time()

            ret, raw_frame = self.camera.read()
            if not ret or raw_frame is None:
                time.sleep(0.01)
                continue

            # Handle background calibration accumulation if requested
            if self._calibrating:
                self._calibration_frames.append(raw_frame.copy())
                if len(self._calibration_frames) >= self._calibration_target_count:
                    success = self.invisibility_engine.bg_capture.capture_denoised(
                        self._calibration_frames, name="Studio Recalibrated Background"
                    )
                    self._calibrating = False
                    self._calibration_frames.clear()
                    events.background_calibrated.emit(success, "Background successfully calibrated and saved!")
                    logger.info("INVISIBILITY", "Background calibration finished.")

            # 1. Apply image adjustments & filters (mirror, color, brightness, etc.)
            preprocessed_frame = self.effects.apply(raw_frame)

            # 2. Run Vision Detection (Hands & Head)
            downscale = config.get_float("performance_downscale", 1.0)
            hand_result = self.hand_detector.process(preprocessed_frame)
            head_result = self.head_detector.process(preprocessed_frame)

            # 3. Gesture Recognition
            gesture_status = self.gesture_recognizer.process(hand_result, head_result)

            # 4. Invisibility Engine (Person segmentation + Background replacement)
            show_mask = settings.show_mask_overlay
            invis_output = self.invisibility_engine.process(
                frame_bgr=preprocessed_frame,
                gesture_status=gesture_status,
                show_mask_overlay=show_mask,
                downscale_factor=downscale,
            )

            # Final clean frame destined for virtual camera output (without HUD overlays)
            virtual_cam_frame = invis_output.output_frame

            # 5. Broadcast to Virtual Camera
            if self.virtual_cam.is_broadcasting:
                self.virtual_cam.send(virtual_cam_frame)

            # 6. Compose HUD / Landmark Overlays for GUI Preview (if enabled)
            display_frame = virtual_cam_frame.copy()
            if settings.show_hud:
                # If invisibility is active, user is invisible!
                # If visible or transitioning, draw sleek target landmarks if enabled
                if settings.show_landmarks and invis_output.transition_alpha < 0.95:
                    display_frame = self.hand_detector.draw_landmarks(display_frame, hand_result)
                    display_frame = self.head_detector.draw_head_overlay(display_frame, head_result)
                    display_frame = self.gesture_recognizer.draw_debug_overlay(display_frame, gesture_status)

                # Draw minimal HUD status pill in top corner
                display_frame = self._draw_hud_watermark(display_frame, gesture_status, invis_output)

            # 7. Dispatch frames to UI
            events.frame_ready.emit(raw_frame, display_frame)
            events.gesture_updated.emit(gesture_status)

            # 8. Compute telemetry
            loop_end = time.time()
            self._last_latency_ms = (loop_end - loop_start) * 1000.0

            self._pipeline_fps_counter += 1
            if loop_end - self._pipeline_fps_start >= 1.0:
                self._actual_pipeline_fps = self._pipeline_fps_counter / (loop_end - self._pipeline_fps_start)
                self._pipeline_fps_counter = 0
                self._pipeline_fps_start = loop_end

                stats = {
                    "camera_fps": self.camera.actual_fps,
                    "pipeline_fps": round(self._actual_pipeline_fps, 1),
                    "virtual_fps": self.virtual_cam.actual_fps,
                    "latency_ms": round(self._last_latency_ms, 1),
                    "is_invisible": invis_output.is_invisible,
                    "transition_alpha": round(invis_output.transition_alpha, 2),
                    "gesture_state": gesture_status.state.value,
                    "hand": gesture_status.active_hand,
                    "confidence": round(gesture_status.confidence, 2),
                    "virtual_cam_active": self.virtual_cam.is_broadcasting,
                    "has_background": invis_output.has_background,
                }
                events.stats_updated.emit(stats)

            # Frame rate synchronization to prevent unnecessary CPU load
            elapsed = time.time() - loop_start
            sleep_time = frame_duration - elapsed
            if sleep_time > 0.002:
                time.sleep(sleep_time)

        # Cleanup on loop exit
        self.camera.stop()
        self.virtual_cam.stop()
        self.hand_detector.close()
        self.head_detector.close()
        self.invisibility_engine.close()
        logger.info("PIPELINE", "Processing Pipeline stopped and resources released.")

    def _draw_hud_watermark(
        self,
        frame: np.ndarray,
        gesture: GestureStatus,
        invis_output: any,
    ) -> np.ndarray:
        h, w = frame.shape[:2]

        # Top-left status badge
        badge_w = 210
        badge_h = 36
        badge_x = 16
        badge_y = 16

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (badge_x, badge_y),
            (badge_x + badge_w, badge_y + badge_h),
            (15, 10, 25),
            -1,
        )
        cv2.rectangle(
            overlay,
            (badge_x, badge_y),
            (badge_x + badge_w, badge_y + badge_h),
            (160, 50, 255),
            1,
        )

        # Indicator dot
        if invis_output.transition_alpha > 0.5:
            dot_color = (0, 255, 128)  # Glowing Green: INVISIBLE
            status_text = "INVISIBLE (KYOKKO)"
        elif gesture.state.value == "CONFIRMING":
            dot_color = (0, 215, 255)  # Gold: Confirming
            status_text = f"HOLDING ({int(gesture.progress*100)}%)"
        else:
            dot_color = (255, 150, 0)  # Cyan: Camera Live
            status_text = "CAMERA LIVE"

        cv2.circle(overlay, (badge_x + 18, badge_y + badge_h // 2), 6, dot_color, -1, cv2.LINE_AA)
        cv2.putText(
            overlay,
            status_text,
            (badge_x + 34, badge_y + 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        return cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)

    def stop(self) -> None:
        self._is_running = False
        self.wait(2000)
