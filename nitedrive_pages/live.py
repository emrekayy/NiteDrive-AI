"""Sayfa 4 - Gercek zamanli canli izleme paneli."""
from __future__ import annotations

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dm_camera import frame_to_rgb
from dm_metrics import RISK_DROWSINESS, RISK_SAFE, RISK_WARNING


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_STATE_FILE = PROJECT_ROOT / os.environ.get("DROWSINESS_DASHBOARD_STATE_FILE", ".nitedrive_live.json")
DASHBOARD_STATE_MAX_AGE_SEC = float(os.environ.get("DROWSINESS_DASHBOARD_MAX_AGE", "5.0"))


def _risk_html(level: str) -> str:
    if level == RISK_DROWSINESS:
        return f'<div class="nd-risk-danger">⚠ {level}</div>'
    if level == RISK_WARNING:
        return f'<div class="nd-risk-warn">⚡ {level}</div>'
    return f'<div class="nd-risk-safe">✓ {level}</div>'


def _metric_card(label: str, val: str) -> str:
    return (
        f'<div class="nd-glass" style="padding:1rem;margin-bottom:0.5rem;">'
        f'<div class="nd-metric-lbl">{label}</div>'
        f'<div class="nd-metric-xl">{val}</div></div>'
    )


def _prediction_label(risk: str) -> str:
    if risk == RISK_DROWSINESS:
        return "DROWSY"
    if risk == RISK_WARNING:
        return "WARNING"
    return "SAFE"


def _arduino_out(risk: str) -> int:
    return 1 if risk == RISK_DROWSINESS else 0


def _waiting_frame(message: str) -> np.ndarray:
    blank = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.putText(blank, message, (120, 340), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (148, 163, 184), 2, cv2.LINE_AA)
    cv2.putText(blank, "./run.sh phone", (500, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (56, 189, 248), 2, cv2.LINE_AA)
    return frame_to_rgb(blank)


def _shared_ai_step() -> tuple[np.ndarray, bool, bool, dict] | None:
    try:
        state = json.loads(DASHBOARD_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if time.time() - float(state.get("timestamp", 0.0)) > DASHBOARD_STATE_MAX_AGE_SEC:
        return None

    frame_file = Path(str(state.get("frame_file", ".nitedrive_live.jpg")))
    if not frame_file.is_absolute():
        frame_file = PROJECT_ROOT / frame_file
    frame_bgr = cv2.imread(str(frame_file))
    if frame_bgr is None:
        return None

    alert = str(state.get("alert_level", "SAFE"))
    risk = RISK_DROWSINESS if alert == "DANGER" else (RISK_WARNING if alert == "WARNING" else RISK_SAFE)
    feat = {
        "ear": float(state.get("ear", 0.0)),
        "perclos": float(state.get("perclos", 0.0)),
        "blink": int(state.get("blink_count", 0)),
        "duration": float(state.get("closure_duration", 0.0)),
        "head": float(state.get("head_drop", 0.0)),
        "fatigue": float(state.get("fatigue_score", 0.0)),
        "risk": risk,
    }
    return frame_to_rgb(frame_bgr), True, bool(state.get("face_detected", False)), feat


def show_live_dashboard() -> None:
    st.markdown("## NiteDrive Canlı İzleme Paneli")
    st.caption("ai_live_arduino.py canlı çıktısı · .nitedrive_live.json / .nitedrive_live.jpg")

    if "nd_t0" not in st.session_state:
        st.session_state.nd_t0 = time.time()
    if "nd_history" not in st.session_state:
        st.session_state.nd_history = pd.DataFrame(
            columns=["time_s", "EAR", "PERCLOS", "Fatigue Score", "Blink Count", "Blink Duration", "Head Angle", "Risk"]
        )
    if "nd_predictions" not in st.session_state:
        st.session_state.nd_predictions = pd.DataFrame(
            columns=["Time", "EAR", "PERCLOS", "Head", "Prediction", "Arduino"]
        )
    @st.fragment(run_every=timedelta(milliseconds=350))
    def _loop() -> None:
        t = time.time() - st.session_state.nd_t0
        shared = _shared_ai_step()
        if shared is not None:
            frame, live, face_ok, feat = shared
            cam_idx = ""
            try:
                state = json.loads(DASHBOARD_STATE_FILE.read_text(encoding="utf-8"))
                cam_idx = f" · Kamera {state.get('camera_index', '?')}"
            except (OSError, json.JSONDecodeError):
                pass
            source_label = f"AI/Arduino CANLI{cam_idx}"
        else:
            frame = _waiting_frame("AI/Arduino bekleniyor")
            live, face_ok = False, False
            feat = {
                "ear": 0.0, "perclos": 0.0, "blink": 0, "duration": 0.0,
                "head": 0.0, "fatigue": 0.0, "risk": RISK_SAFE,
            }
            age_msg = ""
            try:
                state = json.loads(DASHBOARD_STATE_FILE.read_text(encoding="utf-8"))
                age = time.time() - float(state.get("timestamp", 0.0))
                age_msg = f" (son veri {age:.0f} sn önce)"
            except (OSError, json.JSONDecodeError):
                age_msg = " (dosya yok)"
            source_label = f"BEKLENİYOR{age_msg} — terminalde: ./run.sh phone"

        hist_row = {
            "time_s": round(t, 2),
            "EAR": feat["ear"],
            "PERCLOS": feat["perclos"] * 100.0,
            "Fatigue Score": feat["fatigue"],
            "Blink Count": feat["blink"],
            "Blink Duration": feat["duration"],
            "Head Angle": feat["head"],
            "Risk": 2 if feat["risk"] == RISK_DROWSINESS else (1 if feat["risk"] == RISK_WARNING else 0),
        }
        st.session_state.nd_history = pd.concat(
            [st.session_state.nd_history, pd.DataFrame([hist_row])], ignore_index=True
        ).tail(150).reset_index(drop=True)

        pred_row = {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "EAR": f"{feat['ear']:.2f}",
            "PERCLOS": f"{feat['perclos']:.2f}",
            "Head": f"{feat['head']:.2f}",
            "Prediction": _prediction_label(feat["risk"]),
            "Arduino": _arduino_out(feat["risk"]),
        }
        st.session_state.nd_predictions = pd.concat(
            [st.session_state.nd_predictions, pd.DataFrame([pred_row])], ignore_index=True
        ).tail(8)

        hist = st.session_state.nd_history.copy()
        col_cam, col_m = st.columns([1.55, 1], gap="medium")

        with col_cam:
            st.markdown("**Telefon Kamerası / Face Mesh**")
            st.image(frame, use_container_width=True, channels="RGB")
            status = source_label if live else "KAMERA YOK"
            face_status = "AKTİF" if face_ok else "YÜZ YOK"
            dot = "nd-dot-on" if live and face_ok else "nd-dot-warn"
            st.markdown(
                f'<div class="nd-health-row"><span class="nd-dot {dot}"></span>'
                f"Kamera: <b>{status}</b> · MediaPipe: <b>{face_status}</b></div>",
                unsafe_allow_html=True,
            )

        with col_m:
            st.markdown("**Canlı Metrikler (Live Metrics)**")
            r1, r2 = st.columns(2)
            with r1:
                st.markdown(_metric_card("EAR", f"{feat['ear']:.3f}"), unsafe_allow_html=True)
                st.markdown(_metric_card("Göz Kırpma (Blink)", str(feat["blink"])), unsafe_allow_html=True)
                st.markdown(_metric_card("Baş Oranı (Head)", f"{feat['head']:.3f}"), unsafe_allow_html=True)
            with r2:
                st.markdown(_metric_card("PERCLOS", f"{feat['perclos'] * 100.0:.1f}%"), unsafe_allow_html=True)
                st.markdown(_metric_card("Kapalı Süre", f"{feat['duration']:.2f}s"), unsafe_allow_html=True)
                st.markdown(_metric_card("Yorgunluk Skoru", f"{feat['fatigue']:.0f}"), unsafe_allow_html=True)

            st.markdown("**Risk Durumu**")
            st.markdown(_risk_html(feat["risk"]), unsafe_allow_html=True)
            if feat["risk"] == RISK_DROWSINESS:
                st.markdown(
                    '<div class="nd-alert-box">'
                    "Arduino Signal: <b>SENT</b><br>"
                    "LED: <b>ON</b><br>"
                    "BUZZER: <b>ACTIVE</b><br>"
                    "Serial Output: <b>1</b>"
                    "</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            fig = go.Figure()
            if not hist.empty:
                fig.add_trace(go.Scatter(x=hist["time_s"], y=hist["EAR"], line=dict(color="#34d399", width=2.5)))
            fig.update_layout(template="plotly_dark", height=220, title="EAR Geçmişi", margin=dict(t=40, b=30, l=40, r=20))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with g2:
            fig = go.Figure()
            if not hist.empty:
                fig.add_trace(go.Scatter(x=hist["time_s"], y=hist["Fatigue Score"],
                                         fill="tozeroy", line=dict(color="#f97316", width=2)))
            fig.update_layout(template="plotly_dark", height=220, title="Yorgunluk Skoru", margin=dict(t=40, b=30, l=40, r=20))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with g3:
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=feat["perclos"] * 100.0, number=dict(suffix="%"),
                title="PERCLOS", gauge=dict(axis=dict(range=[0, 65]), bar=dict(color="#38bdf8"))))
            fig.update_layout(paper_bgcolor="#0f172a", height=220, margin=dict(t=50, b=10, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with g4:
            fig = go.Figure()
            if not hist.empty and "Risk" in hist.columns:
                fig.add_trace(go.Scatter(x=hist["time_s"], y=hist["Risk"], mode="lines+markers",
                                         line=dict(color="#ef4444", width=2), marker=dict(size=4)))
            fig.update_layout(template="plotly_dark", height=220, title="Risk Zaman Çizelgesi",
                              yaxis=dict(tickvals=[0, 1, 2], ticktext=["SAFE", "WARN", "DROWSY"]),
                              margin=dict(t=40, b=30, l=40, r=20))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("**Son Tahminler (Recent Predictions)**")
        st.dataframe(st.session_state.nd_predictions.iloc[::-1], use_container_width=True, hide_index=True)

    _loop()
