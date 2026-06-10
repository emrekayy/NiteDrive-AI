"""Sayfa 5 — Arduino Uyarı Sistemi."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from nitedrive_components import code_block, glass_card

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAFE_IMAGE = PROJECT_ROOT / "assets" / "nitedrive-hardware-safe.png"
WARNING_IMAGE = PROJECT_ROOT / "assets" / "nitedrive-hardware-warning.png"
WIRING_FLOW_IMAGE = PROJECT_ROOT / "assets" / "nitedrive-wiring-flow.png"


def show_arduino_system() -> None:
    st.markdown('<div class="nd-section-title">Gömülü Uyarı Sistemi (Embedded Alert)</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="nd-section-sub">Fiziksel prototipte telefon kamerası sürücüyü izler; Python çıktısı Arduino LED ve buzzer uyarısına dönüşür.</p>',
        unsafe_allow_html=True,
    )

    demo_a, demo_b = st.columns(2, gap="large")
    with demo_a:
        st.markdown('<div class="nd-hardware-shot">', unsafe_allow_html=True)
        st.image(str(SAFE_IMAGE), use_container_width=True)
        st.markdown(
            '<div class="nd-img-caption"><b>SAFE:</b> yüz ve gözler takip edilir, risk düşük kaldığında fiziksel uyarı pasiftir.</div></div>',
            unsafe_allow_html=True,
        )
    with demo_b:
        st.markdown('<div class="nd-hardware-shot">', unsafe_allow_html=True)
        st.image(str(WARNING_IMAGE), use_container_width=True)
        st.markdown(
            '<div class="nd-img-caption"><b>WARNING:</b> göz kapanma/risk durumu yükseldiğinde kırmızı uyarı ve buzzer hattı aktifleşir.</div></div>',
            unsafe_allow_html=True,
        )

    col_a, col_b = st.columns([1.25, 1], gap="large")

    with col_a:
        st.markdown('<div class="nd-hardware-shot">', unsafe_allow_html=True)
        st.image(str(WIRING_FLOW_IMAGE), use_container_width=True)
        st.markdown(
            '<div class="nd-img-caption"><b>Bağlantı akışı:</b> kamera görüntüsü AI modelinde işlenir; seri komut Arduino Uno üzerinden LED ve buzzer çıkışlarına aktarılır.</div></div>',
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown("#### Seri Haberleşme Mantığı (Serial Communication)")
        glass_card(
            "<p>Python tarafında risk durumu hesaplandıktan sonra Arduino'ya seri port "
            "üzerinden komut gönderilir.</p>"
            "<p><b>Komutlar:</b><br>"
            "• <code>SAFE</code> → LED ve buzzer kapalı<br>"
            "• <code>WARNING</code> → sarı/kırmızı uyarı modu<br>"
            "• <code>DANGER</code> → güçlü buzzer + kırmızı uyarı</p>"
        )
        st.markdown("**Python (pyserial)**")
        code_block("""if eyes_closed_seconds >= 1.7:
    serial.write(b"DANGER\\n")
else:
    serial.write(b"SAFE\\n")""")

        st.markdown("**Arduino (C++)**")
        code_block("""if (strcmp(cmd, "DANGER") == 0) {
    mode = MODE_DANG;
} else if (strcmp(cmd, "WARNING") == 0) {
    mode = MODE_WARN;
} else if (strcmp(cmd, "SAFE") == 0) {
    mode = MODE_SAFE;
}""")

    st.markdown('<div class="nd-section-title">Uyarı Mekanizması</div>', unsafe_allow_html=True)
    glass_card(
        "<p><b>Akış:</b> Telefon kamerası görüntüyü verir → Python AI göz ve baş hareketlerini analiz eder → "
        "risk seviyesi USB Serial ile Arduino'ya gönderilir → Arduino LED ve buzzer çıkışlarını gerçek zamanlı yönetir.</p>"
    )
