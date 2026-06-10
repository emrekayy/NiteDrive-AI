"""Preflight checks for cameras, Arduino, and Python dependencies."""
from __future__ import annotations

import glob
import os


def check_imports() -> None:
    missing = []
    for name in ("cv2", "mediapipe", "numpy", "serial"):
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        raise SystemExit(f"Missing packages: {', '.join(missing)}.  pip install -r requirements.txt")


def check_cameras() -> list[int]:
    import cv2

    found: list[int] = []
    for idx in range(6):
        cap = cv2.VideoCapture(idx)
        try:
            if cap.isOpened():
                ok, frame = cap.read()
                if ok and frame is not None:
                    found.append(idx)
        finally:
            cap.release()
    return found


def check_arduino() -> str | None:
    explicit = os.environ.get("DROWSINESS_SERIAL_PORT", "").strip()
    if explicit:
        return explicit
    ports = sorted(glob.glob("/dev/cu.usbserial*"))
    return ports[-1] if ports else None
