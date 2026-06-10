"""
Camera capture and visualization overlay.

Future integration:
    - Replace simulation landmarks with MediaPipe FaceMesh results.
    - Pipe real EAR / head-pose from `features.py` onto the frame.
"""
from __future__ import annotations

import cv2
import numpy as np


def open_camera(device_index: int = 0) -> cv2.VideoCapture | None:
    """Open default webcam. Returns None if the device cannot be opened."""
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        cap.release()
        return None
    return cap


def read_frame(cap: cv2.VideoCapture | None) -> tuple[bool, np.ndarray]:
    """Read one BGR frame. Falls back to a synthetic black frame on failure."""
    if cap is not None:
        ok, frame = cap.read()
        if ok and frame is not None:
            return True, frame

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        "Kamera Goruntu Simulasyonu",
        (320, 360),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.4,
        (180, 180, 180),
        2,
        cv2.LINE_AA,
    )
    return False, frame


def draw_demo_overlay(frame: np.ndarray, t: float, head_angle: float, ear: float = 0.28) -> np.ndarray:
    """
    Premium Face Mesh simülasyonu: yoğun landmark, EAR çizgileri, head-pose oku, HUD.
    Gelecekte MediaPipe 468 landmark çıktısı ile değiştirilecek.
    """
    out = frame.copy()
    h, w = out.shape[:2]
    cx = int(w * 0.52 + 12 * np.sin(t * 0.7))
    cy = int(h * 0.48 + 8 * np.cos(t * 0.5))
    scale = min(w, h) * 0.15

    # Yoğun landmark ızgarası (468 etkisi)
    rng = np.random.default_rng(int(t * 10) % 10000)
    for _ in range(72):
        ox = rng.uniform(-0.62, 0.62)
        oy = rng.uniform(-0.55, 0.55)
        if ox * ox + oy * oy > 0.42:
            continue
        px = int(cx + ox * scale)
        py = int(cy + oy * scale)
        cv2.circle(out, (px, py), 1, (60, 220, 140), -1, lineType=cv2.LINE_AA)

    # Yüz konturu
    contour = [
        (-0.5, -0.3), (-0.35, -0.42), (-0.15, -0.45), (0, -0.46), (0.15, -0.45),
        (0.35, -0.42), (0.5, -0.3), (0.52, 0), (0.45, 0.28), (0.2, 0.42),
        (0, 0.46), (-0.2, 0.42), (-0.45, 0.28), (-0.52, 0),
    ]
    pts = np.array([(int(cx + ox * scale), int(cy + oy * scale)) for ox, oy in contour], np.int32)
    cv2.polylines(out, [pts], True, (34, 197, 94), 1, cv2.LINE_AA)

    # Göz landmark + EAR ölçüm çizgileri
    le = (int(cx - 0.15 * scale), int(cy - 0.08 * scale))
    re = (int(cx + 0.15 * scale), int(cy - 0.08 * scale))
    eye_w = int(0.11 * scale)
    eye_h = int(0.045 * scale * (0.5 + ear * 1.8))
    for ex in (le[0], re[0]):
        cv2.ellipse(out, (ex, le[1]), (eye_w, eye_h), 0, 0, 360, (34, 211, 238), 1, cv2.LINE_AA)
        cv2.line(out, (ex - eye_w, le[1]), (ex + eye_w, le[1]), (250, 204, 21), 1, cv2.LINE_AA)
        cv2.line(out, (ex, le[1] - eye_h), (ex, le[1] + eye_h), (250, 204, 21), 1, cv2.LINE_AA)

    nose = (cx, int(cy + 0.06 * scale))
    cv2.circle(out, nose, 4, (34, 211, 238), -1, lineType=cv2.LINE_AA)
    angle_rad = np.deg2rad(head_angle)
    arrow_len = int(scale * 1.15)
    tip = (int(nose[0] + arrow_len * np.sin(angle_rad)), int(nose[1] + arrow_len * np.cos(angle_rad)))
    cv2.arrowedLine(out, nose, tip, (56, 189, 248), 3, tipLength=0.22, line_type=cv2.LINE_AA)

    # HUD
    cv2.rectangle(out, (0, 0), (w, 78), (8, 12, 22), -1)
    cv2.putText(out, "NiteDrive | Face Mesh (MediaPipe)", (14, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.62, (56, 189, 248), 2, cv2.LINE_AA)
    cv2.putText(out, "Face Detected | Tracking Active | FPS: 30", (14, 54),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (74, 222, 128), 1, cv2.LINE_AA)
    cv2.rectangle(out, (w - 200, h - 36), (w - 8, h - 8), (8, 12, 22), -1)
    cv2.putText(out, f"EAR: {ear:.3f}", (w - 188, h - 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (250, 204, 21), 1, cv2.LINE_AA)
    return out


def frame_to_rgb(frame_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
