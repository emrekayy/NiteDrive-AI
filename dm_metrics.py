"""
Simulated driver-monitoring metrics and risk classification.

Future integration:
    - `extract_features()` → wire to `features.DrowsinessFrameTracker`
    - `predict_fatigue()` → load `train_model.py` Random Forest artifact
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


RISK_SAFE = "GÜVENLİ"
RISK_WARNING = "UYARI"
RISK_DROWSINESS = "UYKULUK TESPİT EDİLDİ"


@dataclass
class DriverMetrics:
    ear: float
    perclos: float
    blink_count: int
    head_angle: float
    fatigue_score: float
    risk_level: str
    timestamp: float


def extract_features(frame_rgb: np.ndarray, t: float) -> dict[str, float]:
    """
    Placeholder feature extraction (demo simulation).
    Replace with MediaPipe landmarks + EAR / PERCLOS from `features.py`.
    """
    del frame_rgb  # unused in demo
    ear = 0.25 + 0.07 * np.sin(t * 1.1) + 0.02 * np.cos(t * 2.3)
    perclos = 32 + 18 * np.sin(t * 0.55 + 0.8) + 6 * np.cos(t * 1.7)
    blink_count = int(12 + 8 * np.sin(t * 0.35) + 5 * (np.sin(t * 3.2) > 0.92))
    head_angle = 18 + 12 * np.sin(t * 0.45 + 1.2)
    return {
        "ear": float(np.clip(ear, 0.18, 0.32)),
        "perclos": float(np.clip(perclos, 10, 55)),
        "blink_count": int(np.clip(blink_count, 0, 30)),
        "head_angle": float(np.clip(head_angle, 0, 35)),
    }


def predict_fatigue(features: dict[str, float]) -> float:
    """
    Placeholder Random Forest inference.
    Maps ocular + head features to a 0–100 fatigue score.
    """
    ear_penalty = (0.32 - features["ear"]) / 0.14 * 35
    perclos_penalty = (features["perclos"] - 10) / 45 * 40
    head_penalty = features["head_angle"] / 35 * 20
    blink_mod = 8 if features["blink_count"] < 5 else 0
    score = ear_penalty + perclos_penalty + head_penalty + blink_mod
    return float(np.clip(score, 0, 100))


def classify_risk(fatigue_score: float, perclos: float, ear: float) -> str:
    """Rule-based risk tier for demo; mirror production alert thresholds later."""
    if fatigue_score >= 72 or perclos >= 48 or ear <= 0.20:
        return RISK_DROWSINESS
    if fatigue_score >= 45 or perclos >= 28 or ear <= 0.24:
        return RISK_WARNING
    return RISK_SAFE


def compute_metrics(frame_rgb: np.ndarray, t: float) -> DriverMetrics:
    """Full pipeline step: features → fatigue model → risk label."""
    feats = extract_features(frame_rgb, t)
    fatigue = predict_fatigue(feats)
    risk = classify_risk(fatigue, feats["perclos"], feats["ear"])
    return DriverMetrics(
        ear=feats["ear"],
        perclos=feats["perclos"],
        blink_count=feats["blink_count"],
        head_angle=feats["head_angle"],
        fatigue_score=fatigue,
        risk_level=risk,
        timestamp=t,
    )


def append_history(history: pd.DataFrame, metrics: DriverMetrics, max_rows: int = 120) -> pd.DataFrame:
    """Rolling time-series buffer for Plotly charts."""
    row = {
        "time_s": round(metrics.timestamp, 2),
        "EAR": metrics.ear,
        "PERCLOS": metrics.perclos,
        "Fatigue Score": metrics.fatigue_score,
        "Blink Count": metrics.blink_count,
        "Head Angle": metrics.head_angle,
    }
    history = pd.concat([history, pd.DataFrame([row])], ignore_index=True)
    if len(history) > max_rows:
        history = history.iloc[-max_rows:].reset_index(drop=True)
    return history
