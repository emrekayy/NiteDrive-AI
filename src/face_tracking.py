"""
Ortak drowsiness özellikleri: EAR (çift göz), blink, PERCLOS (zaman penceresi), head_drop.
Canlı, veri toplama ve offline CSV rolling aynı tanımları kullanır.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Deque, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# --- MediaPipe FaceMesh göz indeksleri (6 nokta EAR) ---
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263
NOSE_TIP = 1
CHIN = 152

# Model girdisi (train_model / ai_live ile aynı sıra)
ML_FEATURE_COLUMNS = ["EAR", "Blink", "Duration", "PERCLOS", "EAR_mean", "EAR_std"]

DEFAULT_EAR_THRESHOLD = 0.23
DEFAULT_BLINK_MAX_CLOSED_SEC = 0.6
DEFAULT_BLINK_COUNT_WINDOW_SEC = 10.0
DEFAULT_PERCLOS_WINDOW_SEC = 60.0
EAR_ROLLING_WINDOW = 5


def landmark_xy(landmarks: Sequence[Any], idx: int, w: int, h: int) -> np.ndarray:
    lm = landmarks[idx]
    return np.array([lm.x * w, lm.y * h], dtype=np.float32)


def eye_points_from_landmarks(
    landmarks: Sequence[Any], indices: Sequence[int], w: int, h: int
) -> np.ndarray:
    return np.array([landmark_xy(landmarks, i, w, h) for i in indices], dtype=np.float32)


def eye_aspect_ratio(eye_points: np.ndarray) -> float:
    a = np.linalg.norm(eye_points[1] - eye_points[5])
    b = np.linalg.norm(eye_points[2] - eye_points[4])
    c = np.linalg.norm(eye_points[0] - eye_points[3])
    if c == 0:
        return 0.0
    return float((a + b) / (2.0 * c))


def ear_both_eyes_from_landmarks(
    landmarks: Sequence[Any], w: int, h: int
) -> Tuple[float, float, float]:
    left_pts = eye_points_from_landmarks(landmarks, LEFT_EYE_INDICES, w, h)
    right_pts = eye_points_from_landmarks(landmarks, RIGHT_EYE_INDICES, w, h)
    left_ear = eye_aspect_ratio(left_pts)
    right_ear = eye_aspect_ratio(right_pts)
    avg = (left_ear + right_ear) / 2.0
    return left_ear, right_ear, avg


def head_drop_ratio(landmarks: Sequence[Any], w: int, h: int) -> float:
    left_eye = landmark_xy(landmarks, LEFT_EYE_OUTER, w, h)
    right_eye = landmark_xy(landmarks, RIGHT_EYE_OUTER, w, h)
    nose = landmark_xy(landmarks, NOSE_TIP, w, h)
    chin = landmark_xy(landmarks, CHIN, w, h)
    eye_center = (left_eye + right_eye) / 2.0
    eye_to_nose = float(nose[1] - eye_center[1])
    nose_to_chin = float(chin[1] - nose[1])
    if nose_to_chin == 0.0:
        return 0.0
    return eye_to_nose / nose_to_chin


def both_eyes_closed(
    left_ear: float, right_ear: float, ear_threshold: float = DEFAULT_EAR_THRESHOLD
) -> bool:
    return left_ear < ear_threshold and right_ear < ear_threshold


def rolling_ear_mean_std_from_buffer(
    ear_values: Sequence[float], window: int = EAR_ROLLING_WINDOW
) -> Tuple[float, float]:
    """Canlı buffer: pandas rolling(5, min_periods=1).std(ddof=1) ile uyumlu."""
    seq = list(ear_values)
    if not seq:
        return 0.0, 0.0
    w = seq[-window:] if len(seq) > window else seq
    mean_v = float(np.mean(w))
    if len(w) <= 1:
        return mean_v, 0.0
    std_v = float(np.std(w, ddof=1))
    if np.isnan(std_v):
        std_v = 0.0
    return mean_v, std_v


def apply_rolling_ear_features_df(
    df: pd.DataFrame, ear_col: str = "EAR", window: int = EAR_ROLLING_WINDOW
) -> pd.DataFrame:
    """Offline eğitim: EAR sütunundan EAR_mean / EAR_std (rolling)."""
    out = df.copy()
    roll = out[ear_col].rolling(window, min_periods=1)
    out["EAR_mean"] = roll.mean()
    out["EAR_std"] = roll.std().fillna(0.0)
    return out


class EyeTemporalTracker:
    """
    Blink: gözler kapalı → açıldığında kapanma süresi <= blink_max ise say.
    PERCLOS: son perclos_window_sec içindeki örneklerde 'her iki göz kapalı' oranı.
    Duration: şu anki kapanış süresi (açıksa 0).
    Blink sütunu: son blink_window_sec içindeki geçerli blink sayısı.
    """

    def __init__(
        self,
        blink_max_closed_sec: float = DEFAULT_BLINK_MAX_CLOSED_SEC,
        blink_count_window_sec: float = DEFAULT_BLINK_COUNT_WINDOW_SEC,
        perclos_window_sec: float = DEFAULT_PERCLOS_WINDOW_SEC,
    ):
        self.blink_max_closed_sec = blink_max_closed_sec
        self.blink_count_window_sec = blink_count_window_sec
        self.perclos_window_sec = perclos_window_sec

        self._was_closed = False
        self._closed_start: Optional[float] = None
        self._blink_times: Deque[float] = deque()
        self._perclos_samples: Deque[Tuple[float, int]] = deque()

    def reset(self) -> None:
        self._was_closed = False
        self._closed_start = None
        self._blink_times.clear()
        self._perclos_samples.clear()

    def step(self, both_eyes_closed_flag: bool, t: float) -> dict:
        closure_duration = 0.0

        if both_eyes_closed_flag:
            if not self._was_closed:
                self._closed_start = t
            self._was_closed = True
            if self._closed_start is not None:
                closure_duration = t - self._closed_start
        else:
            if self._was_closed and self._closed_start is not None:
                closed_duration = t - self._closed_start
                if 0 < closed_duration <= self.blink_max_closed_sec:
                    self._blink_times.append(t)
            self._was_closed = False
            self._closed_start = None

        while self._blink_times and t - self._blink_times[0] > self.blink_count_window_sec:
            self._blink_times.popleft()

        self._perclos_samples.append((t, 1 if both_eyes_closed_flag else 0))
        while (
            self._perclos_samples
            and t - self._perclos_samples[0][0] > self.perclos_window_sec
        ):
            self._perclos_samples.popleft()

        if self._perclos_samples:
            perclos = sum(s for _, s in self._perclos_samples) / len(self._perclos_samples)
        else:
            perclos = 0.0

        return {
            "blinks_in_window": len(self._blink_times),
            "closure_duration": float(closure_duration),
            "perclos": float(perclos),
        }


class DrowsinessFrameTracker:
    """Tek karede geometri + zamansal özellikler + EAR rolling (ML ile uyumlu)."""

    def __init__(
        self,
        ear_threshold: float = DEFAULT_EAR_THRESHOLD,
        blink_max_closed_sec: float = DEFAULT_BLINK_MAX_CLOSED_SEC,
        blink_count_window_sec: float = DEFAULT_BLINK_COUNT_WINDOW_SEC,
        perclos_window_sec: float = DEFAULT_PERCLOS_WINDOW_SEC,
        ear_rolling_window: int = EAR_ROLLING_WINDOW,
    ):
        self.ear_threshold = ear_threshold
        self._temporal = EyeTemporalTracker(
            blink_max_closed_sec=blink_max_closed_sec,
            blink_count_window_sec=blink_count_window_sec,
            perclos_window_sec=perclos_window_sec,
        )
        self._ear_buf: Deque[float] = deque(maxlen=ear_rolling_window)

    def reset(self) -> None:
        self._temporal.reset()
        self._ear_buf.clear()

    def update(self, landmarks: Sequence[Any], w: int, h: int, t: Optional[float] = None) -> dict:
        now = time.time() if t is None else t

        left_ear, right_ear, avg_ear = ear_both_eyes_from_landmarks(landmarks, w, h)
        closed = both_eyes_closed(left_ear, right_ear, self.ear_threshold)
        head = head_drop_ratio(landmarks, w, h)

        self._ear_buf.append(avg_ear)
        ear_mean, ear_std = rolling_ear_mean_std_from_buffer(self._ear_buf)
        temp = self._temporal.step(closed, now)

        return {
            "EAR": float(avg_ear),
            "left_ear": float(left_ear),
            "right_ear": float(right_ear),
            "Blink": int(temp["blinks_in_window"]),
            "Duration": float(temp["closure_duration"]),
            "PERCLOS": float(temp["perclos"]),
            "EAR_mean": ear_mean,
            "EAR_std": ear_std,
            "Head_drop": float(head),
            "both_eyes_closed": closed,
        }


def static_image_geometry_row(landmarks: Sequence[Any], w: int, h: int) -> dict:
    """Tek kare (Kaggle görseli): zamansal özellik yok."""
    left_ear, right_ear, avg_ear = ear_both_eyes_from_landmarks(landmarks, w, h)
    head = head_drop_ratio(landmarks, w, h)
    return {
        "EAR": float(avg_ear),
        "Head_drop": float(head),
        "left_ear": float(left_ear),
        "right_ear": float(right_ear),
    }
