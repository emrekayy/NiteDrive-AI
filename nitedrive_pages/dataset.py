"""Sayfa 3 — Veri Seti ve Eğitim Süreci."""
from __future__ import annotations

import streamlit as st

from nitedrive_components import (
    confusion_matrix_demo,
    demo_training_table,
    glass_card,
    metric_performance_cards,
    pipeline_row,
)


def show_dataset_training() -> None:
    st.markdown('<div class="nd-section-title">Veri Seti ve Model Eğitim Süreci</div>', unsafe_allow_html=True)

    st.markdown("#### 1. Veri Kaynakları (Data Sources)")
    sources = [
        ("Gerçek Zamanlı Kamera", "Canlı webcam frame'leri"),
        ("Simüle Senaryolar", "Uykululuk davranış simülasyonu"),
        ("Açık Kaynak Veri Setleri", "Driver drowsiness datasets"),
        ("Sınıf Örnekleri", "Normal / yorgun / uykulu sürüş"),
    ]
    cols = st.columns(4)
    for col, (t, d) in zip(cols, sources):
        with col:
            glass_card(f"<h4>{t}</h4><p>{d}</p>")

    st.markdown("#### 2. Veri Etiketleme (Labeling)")
    glass_card(
        "<p>Veriler üç sınıfa ayrılır: <b>SAFE</b>, <b>WARNING</b>, <b>DROWSY</b></p>"
        "<p>• Düşük PERCLOS + normal baş açısı → SAFE<br>"
        "• Artan göz kapanma + uzayan kırpma → WARNING<br>"
        "• Uzun süreli göz kapanması + yüksek baş eğimi → DROWSY</p>"
    )

    st.markdown("#### 3. Ön İşleme Adımları (Preprocessing)")
    pipeline_row([
        ("Video Frame", "Ham kare"),
        ("Yüz Tespiti", "Face detection"),
        ("Landmark Çıkarımı", "MediaPipe mesh"),
        ("Göz Bölgesi", "Eye ROI analizi"),
        ("Gürültü Filtreleme", "Smoothing / hysteresis"),
        ("Zaman Penceresi", "Sliding window"),
        ("Özellik Vektörü", "Feature vector"),
    ])

    st.markdown("#### 4. Özellik Çıkarımı Detayları")
    feats = [
        ("EAR", "Göz açıklık oranı (Eye Aspect Ratio)"),
        ("PERCLOS", "Zaman penceresinde göz kapalı kalma %"),
        ("Blink Count", "Kırpma sayısı"),
        ("Blink Duration", "Göz kapalı kalma süresi"),
        ("Head Pose", "Baş eğim açısı"),
        ("Fatigue Score", "Birleşik risk skoru"),
    ]
    fcols = st.columns(3)
    for i, (t, d) in enumerate(feats):
        with fcols[i % 3]:
            glass_card(f"<h4>{t}</h4><p>{d}</p>")

    st.markdown("#### 5. Model Eğitimi (Random Forest)")
    glass_card(
        "<p>Random Forest modeli, çıkarılan özellik vektörleri ve etiketlenmiş sınıflar "
        "kullanılarak eğitilir. Birden fazla karar ağacının çıktısı birleştirilerek "
        "daha kararlı sınıflandırma sağlanır.</p>"
    )
    pipeline_row([
        ("Dataset", "Etiketli veri"),
        ("Train/Test Split", "%80 / %20"),
        ("Feature Scaling", "Normalizasyon"),
        ("RF Training", "Ensemble trees"),
        ("Evaluation", "Metrik hesabı"),
        ("Real-Time Prediction", "Canlı çıkarım"),
    ])

    st.markdown("#### 6. Örnek Eğitim Tablosu")
    st.dataframe(demo_training_table(), use_container_width=True, hide_index=True)

    st.markdown("#### 7. Model Performansı (Demo)")
    metric_performance_cards()
    st.plotly_chart(confusion_matrix_demo(), use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        '<div class="nd-note">Bu paneldeki değerler sunum demosu için temsili olarak gösterilmiştir. '
        "Gerçek eğitim çıktıları proje veri seti ile güncellenebilir.</div>",
        unsafe_allow_html=True,
    )
