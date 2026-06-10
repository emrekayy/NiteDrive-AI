from __future__ import annotations

import glob
import json
import os
import sys
import cv2
import mediapipe as mp
import numpy as np
import time
import serial
from collections import deque
from typing import Optional

from src.face_tracking import (
    DrowsinessFrameTracker,
    eye_points_from_landmarks,
    LEFT_EYE_INDICES,
    RIGHT_EYE_INDICES,
)
from src.arduino_serial import (
    ALERT_DANGER,
    ALERT_SAFE,
    ALERT_WARNING,
    QUIET_SERIAL_LOG,
    send_alert,
    send_safe_reset,
)


def compute_alert_level(
    baseline_phase: bool,
    both_eyes_closed: bool,
    closure_duration: float,
    head_alarm_state: bool,
    perclos: float,
    head_drop_delta: float,
) -> str:
    """
    Her karede yalnızca bu anki ölçülere göre karar (göz için ardışık sayaç yok).

    Kurallar:
    - Kalibrasyon: SAFE
    - Göz açık: SAFE (kullanıcı kuralı — anında sıfırlanır)
    - Göz kapalıysa ekranda süre anlık görünür
    - DANGER/alarm sadece gözler kesintisiz >= EYE_ALARM_MIN_DURATION kapalıysa verilir
    - Kısa kırpmalar Arduino'ya WARNING/DANGER göndermez
    - Kafa düşmesi: WARNING seviyesini artırabilir
    - PERCLOS / soft head değerleri gösterge içindir; Arduino alarmını yapıştırmasın diye seri karara girmez
    """
    if baseline_phase:
        return ALERT_SAFE

    if both_eyes_closed:
        if closure_duration >= EYE_ALARM_MIN_DURATION:
            return ALERT_DANGER
        return ALERT_SAFE

    if head_alarm_state:
        return ALERT_WARNING

    return ALERT_SAFE


# =========================
# AYARLAR
# =========================
SERIAL_PORT_DEFAULT = "/dev/cu.usbserial-10"
BAUD_RATE = 9600
# Ortam: DROWSINESS_CAMERA=pc|phone  DROWSINESS_SERIAL_PORT=...  DROWSINESS_SKIP_ARDUINO=1
# Test: DROWSINESS_MAX_FRAMES=5 DROWSINESS_HEADLESS=1
SKIP_ARDUINO = os.environ.get("DROWSINESS_SKIP_ARDUINO", "").strip() == "1"
HEADLESS = os.environ.get("DROWSINESS_HEADLESS", "").strip() == "1"
MAX_FRAMES = int(os.environ.get("DROWSINESS_MAX_FRAMES", "0") or "0")

# Göz ayarları (sadece süre eşikleri; kare sayacı kaldırıldı)
EAR_THRESHOLD = float(os.environ.get("DROWSINESS_EAR_THRESHOLD", "0.23"))
# EAR için küçük hysteresis: ekranda kapalı/açık metninin titremesini azaltır.
# Alarm süresi ham kapanma sinyalinden hesaplanır, böylece blink sonrası süre yapışmaz.
EAR_HYSTERESIS = 0.01
EYE_WARNING_MIN_DURATION = float(os.environ.get("DROWSINESS_EYE_WARNING_SECONDS", "0.35"))
EYE_ALARM_MIN_DURATION = float(os.environ.get("DROWSINESS_EYE_DANGER_SECONDS", "1.7"))

# Head-drop ayarları
HEAD_BASELINE_SECONDS = 3.0
HEAD_DROP_DELTA_THRESHOLD = 0.10
HEAD_DROP_MIN_DURATION = 2.0
HEAD_CONSEC_FRAMES_REQUIRED = 10

PERCLOS_WARNING = 0.10
PERCLOS_DANGER = 0.28
HEAD_SOFT_DROP_DELTA = 0.055

WINDOW_NAME = "AI Drowsiness + Arduino"
DASHBOARD_STATE_FILE = os.environ.get("DROWSINESS_DASHBOARD_STATE_FILE", ".nitedrive_live.json")
DASHBOARD_FRAME_FILE = os.environ.get("DROWSINESS_DASHBOARD_FRAME_FILE", ".nitedrive_live.jpg")
DASHBOARD_PUBLISH_INTERVAL_SEC = float(os.environ.get("DROWSINESS_DASHBOARD_INTERVAL", "0.25"))
_dashboard_last_publish_time = 0.0

# =========================
# KAMERA SEÇİMİ (çalışma zamanı, OpenCV VideoCapture)
# =========================
# OpenCV, işletim sisteminin gördüğü her kameraya bir tamsayı indeksi verir.
#
# PC  → genelde indeks 0 (yerleşik FaceTime / webcam).
# Phone → USB ile bağlı telefon, ek uygulama olmadan "standart webcam" (UVC) olarak
#         görünmelidir; işletim sistemi tanıdıktan sonra OpenCV de aynı indeksten
#         okur (çoğu kurulumda 1 veya 2; DROWSINESS_PHONE_CAMERA_INDEX ile ayarlanır).
#
# Akış: kullanıcıya sorulur → seçime göre indeks → VideoCapture açılır → test karesi.
# Açılamazsa uyarı yazılır ve kullanıcı tekrar PC / Phone seçebilir.
CAMERA_PROMPT = "PC or Phone (Enter = PC): "
PC_CAMERA_INDEX = int(os.environ.get("DROWSINESS_PC_CAMERA_INDEX", "0"))
PHONE_CAMERA_INDEX = int(os.environ.get("DROWSINESS_PHONE_CAMERA_INDEX", "1"))
EXPLICIT_CAMERA_INDEX = os.environ.get("DROWSINESS_CAMERA_INDEX", "").strip()
_CAMERA_PROBE_MAX = 6
_CAMERA_OPEN_RETRIES = 3
_CAMERA_OPEN_RETRY_DELAY_SEC = 0.45
CAMERA_CYCLE_INDICES = [
    int(part)
    for part in os.environ.get("DROWSINESS_CAMERA_CYCLE", "0,1").split(",")
    if part.strip().isdigit()
]
PHONE_CAMERA_INDEX_FILE = os.environ.get("DROWSINESS_PHONE_CAMERA_INDEX_FILE", ".phone_camera_index")
ACTIVE_CAMERA_INDEX: int | None = None


def _try_read_camera_index(device_index: int) -> bool:
    """Bir indekste cihazın gerçekten kare verip vermediğini kısa test eder."""
    cap = cv2.VideoCapture(device_index)
    try:
        if not cap.isOpened():
            return False
        ok, frame = cap.read()
        return bool(ok and frame is not None)
    finally:
        cap.release()


def discover_camera_indices(max_index: int = _CAMERA_PROBE_MAX) -> list[int]:
    """OpenCV'nin okuyabildiği tüm kamera indekslerini listeler."""
    found: list[int] = []
    for idx in range(max_index):
        if _try_read_camera_index(idx):
            found.append(idx)
    return found


def save_phone_camera_index(device_index: int) -> None:
    """Doğru telefon indeksini sonraki ./run.sh phone için saklar."""
    try:
        with open(PHONE_CAMERA_INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(f"{device_index}\n")
        print(f"Telefon kamera indeksi kaydedildi: {device_index}")
    except OSError as exc:
        print(f"Telefon kamera indeksi kaydedilemedi: {exc}")


def publish_dashboard_state(frame, state: dict) -> None:
    """Web panelinin okuyacağı son frame + metrik durumunu dosyaya yazar."""
    global _dashboard_last_publish_time

    now = time.time()
    if now - _dashboard_last_publish_time < DASHBOARD_PUBLISH_INTERVAL_SEC:
        return
    _dashboard_last_publish_time = now

    payload = dict(state)
    payload["timestamp"] = now
    payload["camera_index"] = ACTIVE_CAMERA_INDEX
    payload["frame_file"] = DASHBOARD_FRAME_FILE

    frame_tmp = f"{DASHBOARD_FRAME_FILE}.tmp.jpg"
    state_tmp = f"{DASHBOARD_STATE_FILE}.tmp"
    try:
        cv2.imwrite(frame_tmp, frame)
        os.replace(frame_tmp, DASHBOARD_FRAME_FILE)
        with open(state_tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(state_tmp, DASHBOARD_STATE_FILE)
    except OSError:
        pass


def _phone_device_index(available: list[int]) -> int:
    """
    USB telefon kamerası için OpenCV indeksi.
    Yapılandırılmış PHONE_CAMERA_INDEX önceliklidir; yoksa PC dışındaki ilk cihaz.
    """
    if PHONE_CAMERA_INDEX in available:
        return PHONE_CAMERA_INDEX
    others = [i for i in available if i != PC_CAMERA_INDEX]
    if others:
        return others[0]
    return PHONE_CAMERA_INDEX


def _device_for_choice(choice: str, available: list[int]) -> tuple[int, str] | None:
    """Metin seçimini (PC / Phone) OpenCV indeksine çevirir; geçersizde None."""
    c = choice.strip().lower()
    if c.isdigit():
        idx = int(c)
        return idx, f"Camera {idx}"
    if c in ("", "pc", "p"):
        idx = (
            PC_CAMERA_INDEX
            if PC_CAMERA_INDEX in available
            else (available[0] if available else PC_CAMERA_INDEX)
        )
        return idx, "PC"
    if c in ("phone", "tel", "telefon"):
        return _phone_device_index(available), "Phone"
    return None


def _read_camera_choice(available: list[int]) -> tuple[int, str]:
    """Kullanıcıdan CAMERA_PROMPT ile seçim alır."""
    while True:
        raw = input(CAMERA_PROMPT)
        mapped = _device_for_choice(raw, available)
        if mapped is not None:
            return mapped
        print("Geçersiz giriş. 'PC' veya 'Phone' yazın (Enter = PC).\n")


def try_open_video_capture(device_index: int, label: str) -> tuple[cv2.VideoCapture | None, str | None]:
    """
    cv2.VideoCapture ile cihazı açar ve bir test karesi okur.
    Başarılıysa (capture, None); değilse (None, hata_metni).
    """
    global ACTIVE_CAMERA_INDEX

    last_error = f"{label} kamerası (OpenCV indeks {device_index}) açılamadı."
    for attempt in range(1, _CAMERA_OPEN_RETRIES + 1):
        cap = cv2.VideoCapture(device_index)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok and frame is not None:
                h, w = frame.shape[:2]
                print(f"Kamera hazır: {label} — indeks {device_index}, {w}x{h}\n")
                ACTIVE_CAMERA_INDEX = device_index
                return cap, None
            last_error = f"{label} açıldı ancak kare okunamadı (indeks {device_index})."
            cap.release()
        else:
            last_error = f"{label} kamerası açılamadı (indeks {device_index}, deneme {attempt})."
        if attempt < _CAMERA_OPEN_RETRIES:
            time.sleep(_CAMERA_OPEN_RETRY_DELAY_SEC)

    visible = discover_camera_indices()
    hint = (
        f"  Görünen OpenCV cihazları: {visible or 'hiçbiri'}\n"
        "  Phone: telefon USB ile bağlı ve sistemde ikinci kamera olarak kayıtlı olmalı.\n"
        "  (Photo Booth / macOS Kamera uygulamasında listelenmeli; ekstra uygulama gerekmez\n"
        "   yalnızca telefonun kendi USB-webcam / MTP-kamera modu açık olmalı.)"
    )
    return None, f"UYARI: {last_error}\n{hint}"


def acquire_camera() -> cv2.VideoCapture:
    """
    Çalışma zamanı kamera seçimi: sor → aç → hata olursa yeniden sor.
    DROWSINESS_CAMERA=pc|phone ortam değişkeni ilk denemede soruyu atlar;
    açılamazsa yine interaktif seçime düşer.
    """
    env_once = os.environ.get("DROWSINESS_CAMERA", "").strip().lower()
    if EXPLICIT_CAMERA_INDEX:
        device_index = int(EXPLICIT_CAMERA_INDEX)
        label = f"Camera {device_index}"
        print("\n--- Kamera ---")
        print(f"  Doğrudan kamera indeksi: {device_index}\n")
        cap, err = try_open_video_capture(device_index, label)
        if cap is not None:
            return cap
        raise SystemExit(err or f"Kamera açılamadı: indeks {device_index}")
    use_env = bool(env_once)

    print("\n--- Kamera ---")
    print(f"  PC → yerleşik webcam (OpenCV indeks {PC_CAMERA_INDEX})")
    print(
        f"  Phone → USB telefon kamerası (tercihen indeks {PHONE_CAMERA_INDEX}, "
        "yoksa taramadaki ikinci cihaz)\n"
    )

    while True:
        available = discover_camera_indices()
        if available:
            print(f"  Tarama: kullanılabilir indeksler {available}")

        if use_env and env_once:
            mapped = _device_for_choice(env_once, available)
            use_env = False
            if mapped is None:
                print(f"  Geçersiz DROWSINESS_CAMERA={env_once!r}; soru sorulacak.\n")
                device_index, label = _read_camera_choice(available)
            else:
                device_index, label = mapped
                print(f"  Ortam seçimi: {label} (indeks {device_index})")
        else:
            device_index, label = _read_camera_choice(available)

        cap, err = try_open_video_capture(device_index, label)
        if cap is not None:
            return cap

        print(err)
        if use_env is False and not sys.stdin.isatty():
            raise SystemExit("Kamera açılamadı ve interaktif seçim yapılamıyor.")
        print("Başka bir kamera seçerek tekrar deneyebilirsiniz.\n")


def resolve_serial_port() -> str:
    explicit = os.environ.get("DROWSINESS_SERIAL_PORT", "").strip()
    if explicit:
        return explicit
    candidates = sorted(glob.glob("/dev/cu.usbserial*"))
    if not candidates:
        raise SystemExit(
            "Arduino seri portu bulunamadı.\n"
            "  • USB kablosunu kontrol edin.\n"
            "  • Elle: DROWSINESS_SERIAL_PORT=/dev/cu.usbserial-XX ./run.sh"
        )
    if SERIAL_PORT_DEFAULT in candidates:
        return SERIAL_PORT_DEFAULT
    return candidates[-1]


class _NullSerial:
    def write(self, data: bytes) -> None:
        pass

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def reset_input_buffer(self) -> None:
        pass


def connect_arduino() -> serial.Serial:
    if SKIP_ARDUINO:
        print("Arduino atlandı (DROWSINESS_SKIP_ARDUINO=1).")
        return _NullSerial()  # type: ignore[return-value]
    port = resolve_serial_port()
    print(f"Arduino: {port} @ {BAUD_RATE}")
    ser = serial.Serial(port, BAUD_RATE, timeout=1)
    time.sleep(2)
    try:
        ser.reset_input_buffer()
    except (AttributeError, OSError):
        pass
    return ser


def run_detection_loop(
    arduino: serial.Serial,
    cap: cv2.VideoCapture,
    face_mesh: mp.solutions.face_mesh.FaceMesh,
) -> None:
    global _serial_last_tx_time, ACTIVE_CAMERA_INDEX

    tracker = DrowsinessFrameTracker(ear_threshold=EAR_THRESHOLD)
    head_drop_history = deque(maxlen=20)
    head_baseline_values: list[float] = []
    head_baseline = None
    program_start_time = time.time()
    head_drop_start_time = None
    current_head_duration = 0.0
    head_alarm_counter = 0
    last_serial_level: Optional[str] = None
    eyes_closed_start_time: Optional[float] = None
    eyes_closed_state = False
    frame_count = 0

    _serial_last_tx_time = time.time()
    if not HEADLESS:
        print("Canlı izleme başladı. Çıkmak: q veya Ctrl+C. Kamera değiştir: c.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kamera görüntüsü alınamadı.")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        camera_text = (
            f"Kamera index: {ACTIVE_CAMERA_INDEX}"
            if ACTIVE_CAMERA_INDEX is not None
            else "Kamera index: bilinmiyor"
        )
        cv2.putText(frame, camera_text, (w - 330, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
        cv2.putText(frame, "c: kamera degistir", (w - 330, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        left_ear = 0.0
        right_ear = 0.0
        avg_ear = 0.0
        ear_mean = 0.0
        ear_std = 0.0
        blink_count_window = 0
        perclos = 0.0

        raw_head_drop = 0.0
        smooth_head_drop = 0.0
        head_drop_delta = 0.0

        both_eyes_closed = False
        head_alarm_state = False
        closure_duration = 0.0
        current_eye_duration = 0.0
        alert_level = ALERT_SAFE
        combined_level = ALERT_SAFE
        baseline_phase = False

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            feat = tracker.update(landmarks, w, h)
            left_ear = feat["left_ear"]
            right_ear = feat["right_ear"]
            avg_ear = feat["EAR"]
            ear_mean = feat["EAR_mean"]
            ear_std = feat["EAR_std"]
            blink_count_window = feat["Blink"]
            perclos = feat["PERCLOS"]
            raw_closed = (left_ear < EAR_THRESHOLD) and (right_ear < EAR_THRESHOLD)
            raw_open = (left_ear > (EAR_THRESHOLD + EAR_HYSTERESIS)) and (right_ear > (EAR_THRESHOLD + EAR_HYSTERESIS))
            if raw_closed:
                eyes_closed_state = True
            elif raw_open:
                eyes_closed_state = False
            display_eyes_closed = eyes_closed_state
            both_eyes_closed = raw_closed
            # Alarm süresi ham kapanma sinyaline bağlıdır. Hysteresis state'i yalnızca
            # ekrandaki kapalı/açık göstergesini yumuşatır; blink sonrası süre yapışmaz.
            now = time.time()
            if raw_closed:
                if eyes_closed_start_time is None:
                    eyes_closed_start_time = now
                closure_duration = now - eyes_closed_start_time
            else:
                eyes_closed_start_time = None
                closure_duration = 0.0
            current_eye_duration = closure_duration

            left_eye_points = eye_points_from_landmarks(landmarks, LEFT_EYE_INDICES, w, h)
            right_eye_points = eye_points_from_landmarks(landmarks, RIGHT_EYE_INDICES, w, h)

            raw_head_drop = feat["Head_drop"]
            head_drop_history.append(raw_head_drop)
            smooth_head_drop = float(np.mean(head_drop_history))

            elapsed_since_start = now - program_start_time
            baseline_phase = elapsed_since_start < HEAD_BASELINE_SECONDS

            if baseline_phase:
                head_baseline_values.append(smooth_head_drop)
                head_baseline = float(np.mean(head_baseline_values)) if len(head_baseline_values) > 0 else smooth_head_drop
                head_drop_delta = 0.0
                current_head_duration = 0.0
                head_alarm_counter = 0
                head_alarm_state = False
            else:
                if head_baseline is None:
                    head_baseline = smooth_head_drop

                head_drop_delta = smooth_head_drop - head_baseline

                if head_drop_delta > HEAD_DROP_DELTA_THRESHOLD:
                    if head_drop_start_time is None:
                        head_drop_start_time = now
                    current_head_duration = now - head_drop_start_time
                else:
                    head_drop_start_time = None
                    current_head_duration = 0.0
                    head_alarm_counter = 0

                if current_head_duration > HEAD_DROP_MIN_DURATION:
                    head_alarm_counter += 1
                else:
                    if head_drop_delta <= HEAD_DROP_DELTA_THRESHOLD:
                        head_alarm_counter = 0

                head_alarm_state = head_alarm_counter >= HEAD_CONSEC_FRAMES_REQUIRED

            alert_level = compute_alert_level(
                baseline_phase=baseline_phase,
                both_eyes_closed=both_eyes_closed,
                closure_duration=closure_duration,
                head_alarm_state=head_alarm_state,
                perclos=perclos,
                head_drop_delta=head_drop_delta,
            )

            combined_level = alert_level

            prev_serial = last_serial_level
            if combined_level == ALERT_SAFE and prev_serial in (ALERT_WARNING, ALERT_DANGER):
                last_serial_level = send_safe_reset(arduino, last_serial_level)
            else:
                last_serial_level = send_alert(arduino, combined_level, last_serial_level)
            if not QUIET_SERIAL_LOG and combined_level != prev_serial:
                print(
                    f"DEBUG frame: closed={both_eyes_closed} dur={closure_duration:.3f} "
                    f"display_dur={current_eye_duration:.3f} alert={alert_level} "
                    f"serial_was={prev_serial!r} serial_now={last_serial_level!r}",
                    flush=True,
                )

            for pt in left_eye_points.astype(int):
                cv2.circle(frame, tuple(pt), 2, (255, 0, 0), -1)
            for pt in right_eye_points.astype(int):
                cv2.circle(frame, tuple(pt), 2, (255, 0, 0), -1)

            y = 30
            gap = 28

            cv2.putText(frame, f"Left EAR: {left_ear:.3f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y += gap

            cv2.putText(frame, f"Right EAR: {right_ear:.3f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y += gap

            cv2.putText(frame, f"Avg EAR: {avg_ear:.3f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y += gap

            cv2.putText(frame, f"Closure dur (time): {closure_duration:.2f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            y += gap

            cv2.putText(frame, f"Blink(10s): {blink_count_window}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            y += gap

            cv2.putText(frame, f"PERCLOS: {perclos:.3f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            y += gap

            cv2.putText(frame, f"Head Raw: {raw_head_drop:.3f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            y += gap

            cv2.putText(frame, f"Head Smooth: {smooth_head_drop:.3f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            y += gap

            baseline_text = f"{head_baseline:.3f}" if head_baseline is not None else "YOK"
            cv2.putText(frame, f"Head Base: {baseline_text}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            y += gap

            cv2.putText(frame, f"Head Delta: {head_drop_delta:.3f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            y += gap

            cv2.putText(frame, f"Head Duration: {current_head_duration:.2f}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            y += gap

            cv2.putText(frame, f"HeadCount: {head_alarm_counter}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y += gap

            cv2.putText(frame, f"BothEyesClosed: {'YES' if display_eyes_closed else 'NO'}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 0, 255) if display_eyes_closed else (0, 255, 0), 2)
            y += gap

            if baseline_phase:
                remain = HEAD_BASELINE_SECONDS - elapsed_since_start
                cv2.putText(frame, f"Bas kalibrasyonu: {remain:.1f}s", (20, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                y += gap

            lvl_color = (0, 255, 0) if combined_level == ALERT_SAFE else (
                (0, 200, 255) if combined_level == ALERT_WARNING else (0, 0, 255)
            )
            cv2.putText(frame, f"SERI: {combined_level}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, lvl_color, 2)
            y += gap

            cv2.putText(frame, f"Seviye (anlik): {alert_level}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 2)
            y += gap

            if head_alarm_state:
                cv2.putText(frame, "KAFA DUSME UYARISI", (20, y + 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            if combined_level == ALERT_DANGER:
                cv2.putText(frame, "TEHLIKE SEVIYESI", (20, y + 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            elif combined_level == ALERT_WARNING:
                cv2.putText(frame, "UYARI SEVIYESI", (20, y + 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 3)

        else:
            combined_level = ALERT_SAFE
            if last_serial_level in (ALERT_WARNING, ALERT_DANGER):
                last_serial_level = send_safe_reset(arduino, last_serial_level)
            else:
                last_serial_level = send_alert(arduino, ALERT_SAFE, last_serial_level)

            tracker.reset()
            eyes_closed_start_time = None
            eyes_closed_state = False

            head_drop_start_time = None
            current_head_duration = 0.0
            head_alarm_counter = 0

            cv2.putText(frame, "Yuz bulunamadi", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        publish_dashboard_state(
            frame,
            {
                "face_detected": bool(results.multi_face_landmarks),
                "ear": float(avg_ear),
                "left_ear": float(left_ear),
                "right_ear": float(right_ear),
                "perclos": float(perclos),
                "blink_count": int(blink_count_window),
                "closure_duration": float(closure_duration),
                "head_drop": float(smooth_head_drop),
                "head_delta": float(head_drop_delta),
                "fatigue_score": float(
                    min(100.0, max(0.0, ((0.32 - avg_ear) / 0.12) * 45.0 + perclos * 75.0 + min(closure_duration / EYE_ALARM_MIN_DURATION, 1.0) * 20.0))
                    if avg_ear > 0
                    else 0.0
                ),
                "alert_level": combined_level,
            },
        )

        frame_count += 1
        if not HEADLESS:
            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("c"):
                cycle = CAMERA_CYCLE_INDICES or [0, 1]
                current = ACTIVE_CAMERA_INDEX if ACTIVE_CAMERA_INDEX is not None else cycle[0]
                try:
                    pos = cycle.index(current)
                    next_index = cycle[(pos + 1) % len(cycle)]
                except ValueError:
                    next_index = cycle[0]

                print(f"Kamera değiştiriliyor: {current} -> {next_index}")
                new_cap, err = try_open_video_capture(next_index, f"Camera {next_index}")
                if new_cap is None:
                    print(err or f"Kamera açılamadı: {next_index}")
                else:
                    cap.release()
                    cap = new_cap
                    save_phone_camera_index(next_index)
                    tracker = DrowsinessFrameTracker(ear_threshold=EAR_THRESHOLD)
                    head_drop_history.clear()
                    head_baseline_values.clear()
                    head_baseline = None
                    program_start_time = time.time()
                    head_drop_start_time = None
                    current_head_duration = 0.0
                    head_alarm_counter = 0
                    eyes_closed_start_time = None
                    eyes_closed_state = False
                    last_serial_level = send_safe_reset(arduino, last_serial_level)
        if MAX_FRAMES > 0 and frame_count >= MAX_FRAMES:
            print(f"Test modu: {MAX_FRAMES} kare işlendi.")
            break

    send_safe_reset(arduino, last_serial_level)
    cap.release()


def main() -> None:
    print("=== Uyku tespiti + Arduino ===\n")
    cap = acquire_camera()
    arduino = connect_arduino()
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    try:
        run_detection_loop(arduino, cap, face_mesh)
    finally:
        arduino.close()
        cap.release()
        face_mesh.close()
        if not HEADLESS:
            cv2.destroyAllWindows()
        print("Program sonlandı.")


if __name__ == "__main__":
    main()
