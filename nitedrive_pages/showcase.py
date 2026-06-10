"""Sayfa 1 — Proje Vitrini."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from nitedrive_components import glass_card, stat_cards

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_IMAGE = PROJECT_ROOT / "assets" / "nitedrive-logo.png"
SAFE_IMAGE = PROJECT_ROOT / "assets" / "nitedrive-hardware-safe.png"
WARNING_IMAGE = PROJECT_ROOT / "assets" / "nitedrive-hardware-warning.png"


def _image_data_uri(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def show_project_showcase(live_page) -> None:
    logo_uri = _image_data_uri(LOGO_IMAGE)
    st.markdown(
        f"""
        <div class="nd-hero-mega">
            <img class="nd-hero-logo" src="{logo_uri}" alt="NiteDrive AI logo">
            <p class="nd-tagline">Sürücü yorgunluğunu kazaya dönüşmeden önce algılayan akıllı güvenlik sistemi.</p>
            <p class="nd-lead">
                NiteDrive, kamera görüntüsünden yüz işaret noktalarını (face landmarks) çıkarır; göz kapanma
                davranışını, kırpma süresini, baş eğimini ve yorgunluk göstergelerini analiz eder. Elde edilen
                özellikler Random Forest modeli ile değerlendirilir ve risk algılandığında Arduino tabanlı
                LED + buzzer uyarısı tetiklenir.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link(live_page, label="Canlı İzleme Paneline Git →", icon="📡", use_container_width=True)

    stat_cards([
        "Gerçek Zamanlı Analiz (Real-Time)",
        "Bilgisayarlı Görü (Computer Vision)",
        "Makine Öğrenmesi (ML)",
        "Arduino Uyarı (Embedded Alert)",
    ])

    st.markdown('<div class="nd-section-title">Problem</div>', unsafe_allow_html=True)
    st.markdown('<p class="nd-section-sub">Sürücü yorgunluğu ciddi bir trafik güvenliği riskidir.</p>', unsafe_allow_html=True)
    problems = [
        "Uzun yolculuklarda sürücü yorgunluğu artar",
        "Göz kapanma süresi (eye closure) uzar",
        "Başın öne veya yanlara düşmesi (head drop) gözlenir",
        "Tepki süresi (reaction time) azalır",
        "Kaza riski yükselir",
    ]
    cols = st.columns(5)
    for i, p in enumerate(problems):
        with cols[i]:
            glass_card(f"<p>⚠ {p}</p>")

    st.markdown('<div class="nd-section-title">Çözümümüz</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        glass_card("<h4>1. Gör (Perceive)</h4><p>Kamera + OpenCV + MediaPipe Face Mesh ile yüz ve göz takibi.</p>")
    with c2:
        glass_card("<h4>2. Analiz Et (Analyze)</h4><p>EAR, PERCLOS, Blink, Head Pose özellik çıkarımı (feature extraction).</p>")
    with c3:
        glass_card("<h4>3. Uyar (Alert)</h4><p>Random Forest sınıflandırma + Arduino seri haberleşme + LED + Buzzer.</p>")

    st.markdown('<div class="nd-section-title">Donanım Prototipi</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="nd-section-sub">Telefon kamerası, canlı analiz paneli ve Arduino uyarı modülü aynı prototip üzerinde birlikte çalışır.</p>',
        unsafe_allow_html=True,
    )
    img_safe, img_warn = st.columns(2, gap="large")
    with img_safe:
        st.markdown('<div class="nd-hardware-shot">', unsafe_allow_html=True)
        st.image(str(SAFE_IMAGE), use_container_width=True)
        st.markdown(
            '<div class="nd-img-caption"><b>Güvenli durum:</b> göz takibi aktif, sürücü yüzü algılanıyor ve sistem SAFE seviyesinde kalıyor.</div></div>',
            unsafe_allow_html=True,
        )
    with img_warn:
        st.markdown('<div class="nd-hardware-shot">', unsafe_allow_html=True)
        st.image(str(WARNING_IMAGE), use_container_width=True)
        st.markdown(
            '<div class="nd-img-caption"><b>Uyarı durumu:</b> göz kapanması ve risk metrikleri yükseldiğinde Arduino LED + buzzer katmanı tetikleniyor.</div></div>',
            unsafe_allow_html=True,
        )
