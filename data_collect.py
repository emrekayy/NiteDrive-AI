"""
Yüksek kaliteli drowsiness eğitim verisi toplama.
- Özellikler: features.DrowsinessFrameTracker (ai_live.py ile aynı FaceMesh + aynı takip).
- Etiket: n → 0 (normal), d → 1 (uykulu), SPACE ile onay (yanlışlıkla kaydı önler).
"""

from __future__ import annotations

import csv
import math
import os
import time
from typing import Any, List, Optional

import cv2
import mediapipe as mp
from features import DrowsinessFrameTracker, ML_FEATURE_COLUMNS

# =========================
# AYARLAR
# =========================
OUTPUT_CSV = "new_data.csv"
# İki kayıt arası minimum süre (saniye)
MIN_SAVE_INTERVAL_SEC = 0.55
# Yüz görüldükten sonra en az bu kadar kare geçsin (PERCLOS/rolling otursun)
MIN_STABLE_FACE_FRAMES = 45
# Onay penceresi (saniye): n veya d sonrası SPACE süresi
CONFIRM_WINDOW_SEC = 2.5

# Uykulu (1) kayit: gercek davranis sinyali yoksa kaydetme
DROWSY_MIN_DURATION_SEC = 0.3
DROWSY_MIN_PERCLOS = 0.1

CSV_HEADER: List[str] = list(ML_FEATURE_COLUMNS) + ["Head_drop", "Label"]

# Ekranda uyar metni (saniye)
invalid_drowsy_message_until = 0.0

# =========================
# Durum
# =========================
last_save_time = 0.0
normal_count = 0
drowsy_count = 0
saved_count = 0

stable_face_frames = 0

pending_label: Optional[int] = None
pending_deadline = 0.0


def ensure_csv() -> None:
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADER)


def append_row(row: List[Any]) -> None:
    with open(OUTPUT_CSV, "a", newline="") as f:
        csv.writer(f).writerow(row)


def can_save_debounce() -> bool:
    global last_save_time
    now = time.time()
    if now - last_save_time < MIN_SAVE_INTERVAL_SEC:
        return False
    last_save_time = now
    return True


def landmarks_finite(lm: Any, w: int, h: int) -> bool:
    """Basit doğrulama: ana landmark indeksleri sonlu mu."""
    try:
        for i in (0, 1, 33, 152, 263, 362):
            p = lm[i]
            x, y = float(p.x) * w, float(p.y) * h
            if not (math.isfinite(x) and math.isfinite(y)):
                return False
        return True
    except (IndexError, TypeError, ValueError, AttributeError):
        return False


def build_feature_row(feat: dict, label: int) -> List[Any]:
    """ML_FEATURE_COLUMNS + Head_drop + Label (train_model ile uyumlu sıra)."""
    return [feat[c] for c in ML_FEATURE_COLUMNS] + [feat["Head_drop"], label]


def row_values_valid(row: List[Any]) -> bool:
    """NaN/Inf yok; Label hariç sayısal alanlar sonlu."""
    for i, v in enumerate(row[:-1]):
        try:
            fv = float(v)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(fv):
            return False
    lab = row[-1]
    if lab not in (0, 1):
        return False
    return True


def reset_pending() -> None:
    global pending_label, pending_deadline
    pending_label = None
    pending_deadline = 0.0


# =========================
# MEDIAPIPE (ai_live.py ile aynı kurulum)
# =========================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

tracker = DrowsinessFrameTracker()

ensure_csv()

cap = cv2.VideoCapture(0)

print("Veri toplama: n/d ile sec, SPACE ile onay, ESC iptal, q cikis")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    now = time.time()

    if pending_label is not None and now > pending_deadline:
        reset_pending()

    if res.multi_face_landmarks:
        lm = res.multi_face_landmarks[0].landmark
        if not landmarks_finite(lm, w, h):
            tracker.reset()
            stable_face_frames = 0
            reset_pending()
        else:
            feat = tracker.update(lm, w, h)
            stable_face_frames += 1

            ready = stable_face_frames >= MIN_STABLE_FACE_FRAMES

            # --- Etiket: n / d secimi (her zaman yeniden zamanlar) ---
            if key == ord("n"):
                pending_label = 0
                pending_deadline = now + CONFIRM_WINDOW_SEC
            elif key == ord("d"):
                pending_label = 1
                pending_deadline = now + CONFIRM_WINDOW_SEC

            if pending_label is not None:
                if key == 27:  # ESC
                    reset_pending()
                elif key == ord(" "):
                    if not ready:
                        print("Isinma suruyor: yuz sabitlenene kadar bekleyin, sonra SPACE.")
                    elif pending_label == 1:
                        if (
                            feat["Duration"] < DROWSY_MIN_DURATION_SEC
                            and feat["PERCLOS"] < DROWSY_MIN_PERCLOS
                        ):
                            invalid_drowsy_message_until = now + 2.8
                            print(
                                "INVALID DROWSY SAMPLE - NOT SAVED "
                                f"(Duration={feat['Duration']:.3f}, PERCLOS={feat['PERCLOS']:.4f})"
                            )
                            reset_pending()
                        elif can_save_debounce():
                            row = build_feature_row(feat, pending_label)
                            if row_values_valid(row):
                                append_row(row)
                                saved_count += 1
                                drowsy_count += 1
                                print(
                                    f"Kaydedildi [UYKULU] ornek #{saved_count} | "
                                    f"EAR={row[0]:.4f} Blink={row[1]} Dur={row[2]:.4f} "
                                    f"PERCLOS={row[3]:.4f} mu={row[4]:.4f} sig={row[5]:.4f} "
                                    f"Head={row[6]:.4f}"
                                )
                                reset_pending()
                            else:
                                print("Gecersiz ozellik (NaN/Inf); kayit atlandi, onay iptal.")
                                reset_pending()
                    elif pending_label == 0 and can_save_debounce():
                        row = build_feature_row(feat, pending_label)
                        if row_values_valid(row):
                            append_row(row)
                            saved_count += 1
                            normal_count += 1
                            print(
                                f"Kaydedildi [NORMAL] ornek #{saved_count} | "
                                f"EAR={row[0]:.4f} Blink={row[1]} Dur={row[2]:.4f} "
                                f"PERCLOS={row[3]:.4f} mu={row[4]:.4f} sig={row[5]:.4f} "
                                f"Head={row[6]:.4f}"
                            )
                            reset_pending()
                        else:
                            print("Gecersiz ozellik (NaN/Inf); kayit atlandi, onay iptal.")
                            reset_pending()

            # --- Ust bilgi paneli ---
            y0 = 18
            gap = 22
            y = y0
            cv2.putText(
                frame,
                "VERI TOPLAMA | n=Normal(0) d=Uykulu(1) sonra SPACE=onay | ESC=iptal | q=cikis",
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                1,
            )
            y += gap + 6
            cv2.putText(
                frame,
                "Normal goz kirpma, yavas kapama, uzun kapama, kafa dusurme senaryolarini canlandirin.",
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (200, 220, 200),
                1,
            )
            y += gap + 4

            if pending_label is None:
                cv2.putText(
                    frame,
                    "Etiket: (beklemede) — n veya d basin",
                    (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (180, 180, 180),
                    2,
                )
            else:
                lab_name = "NORMAL (0)" if pending_label == 0 else "UYKULU (1)"
                remain = max(0.0, pending_deadline - now)
                cv2.putText(
                    frame,
                    f"ONAY: {lab_name}  |  SPACE basin  ({remain:.1f}s)",
                    (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                )
            y += gap + 8

            warm_txt = (
                f"Isinma: {stable_face_frames}/{MIN_STABLE_FACE_FRAMES} kare"
                if not ready
                else "Isinma: TAMAM — kayit yapilabilir"
            )
            cv2.putText(frame, warm_txt, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 200, 255), 2)
            y += gap + 6

            # Canli ozellikler (ML + Head_drop)
            lines = [
                f"EAR {feat['EAR']:.4f}  L/R {feat['left_ear']:.4f}/{feat['right_ear']:.4f}",
                f"Blink(10s) {feat['Blink']}   Duration {feat['Duration']:.3f}s",
                f"PERCLOS {feat['PERCLOS']:.4f}   EAR_mu/sig {feat['EAR_mean']:.4f}/{feat['EAR_std']:.4f}",
                f"Head_drop {feat['Head_drop']:.4f}   GozKapali {feat['both_eyes_closed']}",
            ]
            for line in lines:
                y += gap
                cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 2)

            y += gap + 10
            cv2.putText(
                frame,
                f"Toplam: {saved_count}  |  Normal: {normal_count}  |  Uykulu: {drowsy_count}",
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 0),
                2,
            )
    else:
        tracker.reset()
        stable_face_frames = 0
        reset_pending()
        cv2.putText(
            frame,
            "Yuz yok — kameraya donun (ozellikler sifirlanir)",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    if invalid_drowsy_message_until > time.time():
        msg = "INVALID DROWSY SAMPLE - NOT SAVED"
        fh, fw = frame.shape[0], frame.shape[1]
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.75
        thick = 2
        (tw, th), _ = cv2.getTextSize(msg, font, scale, thick)
        cx = max(8, (fw - tw) // 2)
        cy = max(40, fh // 2)
        cv2.putText(frame, msg, (cx, cy), font, scale, (0, 0, 255), thick)

    cv2.imshow("DATA COLLECT", frame)

cap.release()
cv2.destroyAllWindows()

print(f"Bitti. Toplam kayit: {saved_count} -> {OUTPUT_CSV}")
