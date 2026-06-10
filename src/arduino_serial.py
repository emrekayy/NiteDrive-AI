"""Arduino serial alert protocol (SAFE / WARNING / DANGER)."""
from __future__ import annotations

import os
import time
from typing import Optional

import serial

ALERT_SAFE = "SAFE"
ALERT_WARNING = "WARNING"
ALERT_DANGER = "DANGER"

SERIAL_HEARTBEAT_SEC = 0.75
_serial_last_tx_time = 0.0
QUIET_SERIAL_LOG = os.environ.get("DROWSINESS_QUIET", "").strip() == "1"


def send_alert(
    arduino: serial.Serial,
    level: str,
    last_sent: Optional[str],
    *,
    force: bool = False,
) -> str:
    """Send SAFE / WARNING / DANGER + LF when level changes or heartbeat expires."""
    global _serial_last_tx_time
    now = time.time()
    if _serial_last_tx_time <= 0.0:
        _serial_last_tx_time = now
    changed = last_sent is None or level != last_sent
    stale = (now - _serial_last_tx_time) >= SERIAL_HEARTBEAT_SEC
    if force or changed or stale:
        payload = (level + "\n").encode("ascii", errors="strict")
        arduino.write(payload)
        arduino.flush()
        _serial_last_tx_time = now
        if not QUIET_SERIAL_LOG:
            tag = "SENDING"
            if force:
                tag = "SENDING(force)"
            elif stale and not changed:
                tag = "SENDING(heartbeat)"
            print(f"{tag}: {level!r} payload={payload!r}", flush=True)
    return level


def send_safe_reset(arduino: serial.Serial, last_sent: Optional[str]) -> str:
    """Repeat SAFE so Arduino exits alert mode reliably (buzzer off)."""
    level = last_sent
    for _ in range(3):
        level = send_alert(arduino, ALERT_SAFE, level, force=True)
        time.sleep(0.03)
    return ALERT_SAFE
