"""
Canlı yorgunluk skoru, ML tahmin yumuşatma ve SAFE/WARNING/DANGER eşlemesi.
Özellik vektörü veya model eğitimi değiştirilmez; yalnızca sonradan okunan değerler kullanılır.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional

ALERT_SAFE = "SAFE"
ALERT_WARNING = "WARNING"
ALERT_DANGER = "DANGER"

_RANK = {ALERT_SAFE: 0, ALERT_WARNING: 1, ALERT_DANGER: 2}
_INV = {0: ALERT_SAFE, 1: ALERT_WARNING, 2: ALERT_DANGER}

SMOOTH_WINDOW = 10
SMOOTH_MAJORITY_ON = 6
SMOOTH_MAJORITY_OFF = 4

FATIGUE_EMA_ALPHA = 0.18


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def smooth_ml_prediction(
    history: Deque[int],
    raw_pred: int,
    last_smoothed: int,
) -> int:
    """
    Son 10 karede çoğunluk + gri bölgede önceki kararı koru (titreme azaltma).
    raw_pred: 0 veya 1 (pipeline çıktısı).
    """
    history.append(int(raw_pred))
    n = len(history)
    s = sum(history)
    if n < SMOOTH_WINDOW:
        return 1 if (s / n) >= 0.5 else 0
    if s >= SMOOTH_MAJORITY_ON:
        return 1
    if s <= SMOOTH_MAJORITY_OFF:
        return 0
    return last_smoothed


def raw_fatigue_score(
    perclos: float,
    blink_rate: float,
    ear: float,
    head_drop: float,
) -> float:
    """
    0–100 skor; PERCLOS, blink (10 sn penceresi), EAR (düşük = yorgun), head_drop (1'den sapma).
    Ağırlıklar sabit; özellik hesaplaması features modülünde kalır.
    """
    c_p = _clip(perclos, 0.0, 1.0)
    ear_closedness = _clip((0.30 - ear) / 0.14, 0.0, 1.0)
    c_b = _clip(blink_rate / 14.0, 0.0, 1.0)
    c_h = _clip(abs(head_drop - 1.0) / 0.35, 0.0, 1.0)
    score = 100.0 * (0.36 * c_p + 0.28 * ear_closedness + 0.18 * c_b + 0.18 * c_h)
    return _clip(score, 0.0, 100.0)


def ema_fatigue(prev: Optional[float], raw: float, alpha: float = FATIGUE_EMA_ALPHA) -> float:
    if prev is None:
        return raw
    return (1.0 - alpha) * prev + alpha * raw


def fatigue_alert_level(ema_score: float, prev_level: str) -> str:
    """
    EMA yorgunluk skorundan seviye; eşiklerde histerezis (aynı seviye etrafında titreme azaltır).
    """
    if prev_level == ALERT_SAFE:
        if ema_score >= 78:
            return ALERT_DANGER
        if ema_score >= 44:
            return ALERT_WARNING
        return ALERT_SAFE

    if prev_level == ALERT_WARNING:
        if ema_score >= 78:
            return ALERT_DANGER
        if ema_score <= 36:
            return ALERT_SAFE
        return ALERT_WARNING

    # DANGER
    if ema_score <= 58:
        return ALERT_WARNING if ema_score >= 34 else ALERT_SAFE
    return ALERT_DANGER


def max_alert_level(a: str, b: str) -> str:
    """İki kaynaktan daha kötü (yüksek öncelikli) uyarıyı seç."""
    return _INV[max(_RANK.get(a, 0), _RANK.get(b, 0))]
