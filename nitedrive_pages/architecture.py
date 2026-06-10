"""Sayfa 2 — Teknik Mimari."""
from __future__ import annotations

import streamlit as st

from nitedrive_components import code_block, pipeline_row, glass_card


def show_technical_architecture() -> None:
    st.markdown('<div class="nd-section-title">Sistem Mimarisi (System Architecture)</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="nd-section-sub">Uçtan uca gerçek zamanlı görüntü işleme, özellik çıkarımı ve gömülü uyarı hattı.</p>',
        unsafe_allow_html=True,
    )

    pipeline_row([
        ("Kamera Girişi", "USB / webcam frame capture"),
        ("OpenCV Ön İşleme", "Resize, flip, BGR→RGB"),
        ("MediaPipe Face Mesh", "468 facial landmarks"),
        ("Landmark Normalizasyonu", "Koordinat ölçekleme"),
        ("Özellik Çıkarımı", "EAR, PERCLOS, blink, head"),
        ("Feature Vector", "ML girdi vektörü"),
        ("Random Forest", "Çoklu karar ağacı"),
        ("Risk Skoru", "Fatigue score 0–100"),
        ("Seri Haberleşme", "pyserial UART"),
        ("Arduino LED+Buzzer", "Fiziksel uyarı"),
    ])

    col_l, col_r = st.columns([1.4, 1])
    with col_l:
        st.markdown('<div class="nd-section-title" style="font-size:1.2rem;">Feature Vector Preview</div>', unsafe_allow_html=True)
        code_block("""[
  EAR = 0.21,
  PERCLOS = 0.42,
  Blink_Count = 18,
  Blink_Duration = 0.38,
  Head_Angle = 24.5,
  Fatigue_Score = 82
]""")

    with col_r:
        st.markdown('<div class="nd-section-title" style="font-size:1.2rem;">Gerçek Zamanlı Veri Akışı</div>', unsafe_allow_html=True)
        flow_items = [
            ("Frame yakalama", "30 FPS hedef"),
            ("Yüz tespiti", "468 MediaPipe landmark"),
            ("Göz analizi", "Sol + sağ göz landmarkları"),
            ("Özellik vektörü", "EAR, PERCLOS, blink, duration, head angle"),
            ("Karar", "Safe / Warning / Drowsy"),
            ("Çıkış", "Serial command: 0 veya 1"),
        ]
        for title, desc in flow_items:
            glass_card(f"<h4>{title}</h4><p>{desc}</p>")

    st.markdown(
        '<div class="nd-note">Bu yapı sayesinde sistem yalnızca tek bir belirtiye değil, '
        "birden fazla biyometrik ve davranışsal göstergeye (multi-modal indicators) göre karar verir.</div>",
        unsafe_allow_html=True,
    )
