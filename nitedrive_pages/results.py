"""Sayfa 6 — Sonuçlar ve Performans."""
from __future__ import annotations

import streamlit as st

from nitedrive_components import glass_card, metric_performance_cards


def show_results_performance() -> None:
    st.markdown('<div class="nd-section-title">Sonuçlar ve Performans</div>', unsafe_allow_html=True)

    st.markdown("#### 1. Sistem Çıktıları")
    outputs = [
        "Gerçek zamanlı yüz takibi (face tracking)",
        "Göz kapanma analizi (eye closure)",
        "Baş eğimi tespiti (head pose)",
        "Yorgunluk skoru üretimi (fatigue score)",
        "Arduino uyarı aktivasyonu (hardware alert)",
    ]
    cols = st.columns(5)
    for col, o in zip(cols, outputs):
        with col:
            glass_card(f"<p>✓ {o}</p>")

    st.markdown("#### 2. Performans Göstergeleri (Demo)")
    perf = [
        ("Ortalama FPS", "28–30"),
        ("Alarm Tepki Süresi", "< 1 sn"),
        ("Model Doğruluğu", "%92"),
        ("Karar Sınıfları", "Safe / Warning / Drowsy"),
    ]
    pcols = st.columns(4)
    for col, (k, v) in zip(pcols, perf):
        with col:
            st.markdown(
                f'<div class="nd-glass" style="text-align:center;padding:1.2rem;">'
                f'<div class="nd-metric-lbl">{k}</div>'
                f'<div class="nd-metric-xl" style="color:#22d3ee;">{v}</div></div>',
                unsafe_allow_html=True,
            )
    metric_performance_cards()
    st.markdown(
        '<div class="nd-note">Performans değerleri test ortamı ve kullanılan veri setine göre değişebilir.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 3. Güçlü Yönler")
    strengths = [
        "Düşük maliyetli donanım",
        "Gerçek zamanlı çalışabilir mimari",
        "Görüntü işleme + makine öğrenmesi birleşimi",
        "Arduino ile fiziksel uyarı katmanı",
        "Genişletilebilir modüler yapı",
    ]
    for s in strengths:
        glass_card(f"<p>▸ {s}</p>")

    st.markdown("#### 4. Gelecek Geliştirmeler")
    future = [
        "Mobil uygulama entegrasyonu",
        "Sesli asistan uyarısı",
        "Araç içi CAN-BUS entegrasyonu",
        "Daha büyük veri seti ile model eğitimi",
        "Derin öğrenme modeli (deep learning)",
        "Gece görüş optimizasyonu",
    ]
    fcols = st.columns(3)
    for i, f in enumerate(future):
        with fcols[i % 3]:
            glass_card(f"<p>→ {f}</p>")

    st.markdown(
        '<div class="nd-glass" style="margin-top:1.5rem;padding:1.5rem;">'
        "<p style='font-size:1.05rem;color:#e2e8f0;'>"
        "NiteDrive sadece sürücüyü izleyen bir sistem değil; kazayı oluşmadan önce "
        "önlemeyi hedefleyen akıllı bir güvenlik katmanıdır (proactive safety layer)."
        "</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="nd-quote-final">
            <p class="nd-quote-line">Uyanık kal.</p>
            <p class="nd-quote-line">Güvende kal.</p>
            <p class="nd-quote-line">Eve sağ salim var.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
