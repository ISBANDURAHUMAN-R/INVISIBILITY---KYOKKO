"""
PROJECT KYOKKO
System & Device Discovery Utilities
Webcam detection, virtual camera backend verification, and system telemetry.
"""

import os
import platform
import winreg
from typing import Dict, List, Optional, Tuple
import cv2


STANDARD_RESOLUTIONS = [
    (1920, 1080, "1080p Full HD (16:9)"),
    (1280, 720, "720p HD (16:9)"),
    (960, 540, "qHD (16:9)"),
    (640, 480, "480p VGA (4:3)"),
    (640, 360, "360p nHD (16:9)"),
    (320, 240, "QVGA (4:3)"),
]


def enumerate_webcams(max_test: int = 6) -> List[Dict[str, any]]:
    """Scan available physical webcam devices using DirectShow."""
    devices = []
    for idx in range(max_test):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            if fps <= 0:
                fps = 30
            backend = cap.getBackendName()

            # Attempt friendly name via Windows DirectShow device names if possible
            friendly_name = f"Camera {idx}"
            if idx == 0:
                friendly_name = "Camera 0 (Default / Integrated)"

            devices.append(
                {
                    "index": idx,
                    "name": friendly_name,
                    "default_width": w,
                    "default_height": h,
                    "default_fps": fps,
                    "backend": backend,
                    "working": ret,
                }
            )
            cap.release()
    return devices


def detect_supported_resolutions(camera_index: int) -> List[Tuple[int, int, str]]:
    """Probe camera device to determine supported resolutions."""
    supported = []
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        return [(1280, 720, "720p HD (Default)"), (640, 480, "480p VGA (Default)")]

    original_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    for w, h, label in STANDARD_RESOLUTIONS:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if actual_w == w and actual_h == h:
            supported.append((w, h, label))

    cap.release()

    if not supported:
        supported.append((original_w, original_h, f"{original_w}x{original_h} (Native)"))

    return supported


def check_virtual_camera_backends() -> Dict[str, any]:
    """
    Check if OBS Virtual Camera or UnityCapture filters are registered in Windows registry
    and check if pyvirtualcam can access them.
    """
    status = {
        "obs_installed": False,
        "unity_installed": False,
        "pyvirtualcam_available": False,
        "active_backend": None,
        "details": "",
    }

    # Check DirectShow Filter CLSID for OBS Virtual Camera
    obs_clsids = [
        r"CLSID\{A3FCE0F5-3493-419F-958A-ACDD9227A6D8}", # OBS Virtual Cam
        r"CLSID\{27B05C2D-93DC-43E2-B0DE-44E2ED0DB894}",
    ]
    for clsid in obs_clsids:
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, clsid):
                status["obs_installed"] = True
                break
        except OSError:
            pass

    # Check Program Files for OBS Studio
    obs_paths = [
        r"C:\Program Files\obs-studio\data\obs-plugins\win-dshow\virtualcam-install.bat",
        r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\obs-studio\bin\64bit\obs64.exe"),
    ]
    for p in obs_paths:
        if os.path.exists(p):
            status["obs_installed"] = True
            break

    # Test pyvirtualcam direct initialization
    try:
        import pyvirtualcam
        # We try a dry probe with minimal dimensions
        try:
            with pyvirtualcam.Camera(width=64, height=64, fps=15, print_fps=False) as cam:
                status["pyvirtualcam_available"] = True
                status["active_backend"] = cam.backend
                status["details"] = f"Connected to {cam.backend} ({cam.device})"
        except Exception as e:
            status["pyvirtualcam_available"] = False
            status["details"] = str(e)
    except ImportError:
        status["details"] = "pyvirtualcam package not installed"

    return status


def get_system_telemetry() -> Dict[str, str]:
    """Get system telemetry info."""
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python": platform.python_version(),
        "arch": platform.machine(),
        "processor": platform.processor() or "AMD64 Family",
    }
