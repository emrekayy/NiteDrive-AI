"""
NiteDrive simulation layer — demo metrics & camera feed.

Future integration:
    OpenCV        → dm_camera.open_camera / read_frame
    MediaPipe     → features.py landmark pipeline
    Random Forest → train_model.py artifact
    Arduino       → dm_alerts.send_arduino_alert / ai_live_arduino.py
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from dm_alerts import ArduinoStatus, send_arduino_alert
from dm_camera import draw_demo_overlay, frame_to_rgb, open_camera, read_frame
from dm_metrics import RISK_DROWSINESS, RISK_SAFE, RISK_WARNING, classify_risk, predict_fatigue


@dataclass
class SimulatedMetrics:
    ear: float
    perclos: float
    blink_count: int
    blink_duration: float
    head_angle: float
    fatigue_score: float
    risk_level: str
    timestamp: float


def simulate_metrics(t: float) -> SimulatedMetrics:
    """Generate realistic oscillating demo values for presentation video."""
    ear = 0.26 + 0.08 * np.sin(t * 1.05) + 0.02 * np.cos(t * 2.1)
    perclos = 28 + 22 * np.sin(t * 0.5 + 0.6) + 8 * np.cos(t * 1.4)
    blink_count = int(10 + 10 * np.sin(t * 0.3) + 6 * (np.sin(t * 3.0) > 0.9))
    blink_duration = 0.12 + 0.18 * max(0, np.sin(t * 2.5 + 1.0))
    head_angle = 15 + 14 * np.sin(t * 0.42 + 0.9)

    feats = {
        "ear": float(np.clip(ear, 0.18, 0.35)),
        "perclos": float(np.clip(perclos, 5, 60)),
        "blink_count": int(np.clip(blink_count, 0, 30)),
        "head_angle": float(np.clip(head_angle, 0, 35)),
    }
    fatigue = predict_fatigue(feats)
    risk = classify_risk(fatigue, feats["perclos"], feats["ear"])

    return SimulatedMetrics(
        ear=feats["ear"],
        perclos=feats["perclos"],
        blink_count=feats["blink_count"],
        blink_duration=float(np.clip(blink_duration, 0.08, 0.45)),
        head_angle=feats["head_angle"],
        fatigue_score=fatigue,
        risk_level=risk,
        timestamp=t,
    )


def render_camera_simulation(
    cap,
    t: float,
    head_angle: float,
    tracking_on: bool = True,
) -> tuple[np.ndarray, bool]:
    """
    Capture webcam frame or fallback simulation; draw monitoring overlay.
    Returns RGB frame and whether a live webcam is active.
    """
    live, frame_bgr = read_frame(cap)
    if tracking_on:
        frame_bgr = draw_demo_overlay(frame_bgr, t, head_angle, ear=0.26 + 0.06 * np.sin(t))
    return frame_to_rgb(frame_bgr), live


def append_metric_history(history: pd.DataFrame, m: SimulatedMetrics, max_rows: int = 150) -> pd.DataFrame:
    row = {
        "time_s": round(m.timestamp, 2),
        "EAR": m.ear,
        "PERCLOS": m.perclos,
        "Fatigue Score": m.fatigue_score,
        "Blink Count": m.blink_count,
        "Blink Duration": m.blink_duration,
        "Head Angle": m.head_angle,
    }
    history = pd.concat([history, pd.DataFrame([row])], ignore_index=True)
    if len(history) > max_rows:
        history = history.iloc[-max_rows:].reset_index(drop=True)
    return history


def get_arduino_status(metrics: SimulatedMetrics) -> ArduinoStatus:
    """Demo Arduino serial stub — wire to pyserial in production."""
    from dm_metrics import DriverMetrics

    dm = DriverMetrics(
        ear=metrics.ear,
        perclos=metrics.perclos,
        blink_count=metrics.blink_count,
        head_angle=metrics.head_angle,
        fatigue_score=metrics.fatigue_score,
        risk_level=metrics.risk_level,
        timestamp=metrics.timestamp,
    )
    return send_arduino_alert(dm)
