"""
Arduino alert stub for demo dashboard.

Future integration:
    - `send_arduino_alert()` → `ai_live_arduino.send_alert()` over pyserial
"""
from __future__ import annotations

from dataclasses import dataclass

from dm_metrics import RISK_DROWSINESS, RISK_SAFE, RISK_WARNING, DriverMetrics


@dataclass
class ArduinoStatus:
    signal_sent: bool
    led_on: bool
    buzzer_active: bool
    last_command: str


def map_risk_to_serial(risk_level: str) -> str:
    """Match production serial protocol: SAFE / WARNING / DANGER."""
    if risk_level == RISK_DROWSINESS:
        return "DANGER"
    if risk_level == RISK_WARNING:
        return "WARNING"
    return "SAFE"


def send_arduino_alert(metrics: DriverMetrics) -> ArduinoStatus:
    """
    Demo stub — logs intent only.
    Replace body with `serial.Serial.write()` from `ai_live_arduino.py`.
    """
    command = map_risk_to_serial(metrics.risk_level)
    active = metrics.risk_level == RISK_DROWSINESS
    return ArduinoStatus(
        signal_sent=metrics.risk_level != RISK_SAFE,
        led_on=active,
        buzzer_active=active,
        last_command=command,
    )
