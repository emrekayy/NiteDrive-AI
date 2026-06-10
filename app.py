"""
NiteDrive – Yapay Zeka Tabanlı Gerçek Zamanlı Sürücü Uykululuk Tespiti ve Uyarı Sistemi

Üniversite mühendislik projesi · Jüri sunumu ve tanıtım videosu

Çalıştırma:
    pip install -r requirements.txt
    streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from nitedrive_pages.architecture import show_technical_architecture
from nitedrive_pages.arduino_page import show_arduino_system
from nitedrive_pages.dataset import show_dataset_training
from nitedrive_pages.live import show_live_dashboard
from nitedrive_pages.results import show_results_performance
from nitedrive_pages.showcase import show_project_showcase
from nitedrive_sim import render_camera_simulation, simulate_metrics
from nitedrive_theme import NITEDRIVE_CSS

__all__ = [
    "show_project_showcase",
    "show_technical_architecture",
    "show_dataset_training",
    "show_live_dashboard",
    "show_arduino_system",
    "show_results_performance",
    "simulate_metrics",
    "render_camera_simulation",
    "main",
]

_PAGE_LIVE = st.Page(show_live_dashboard, title="Canlı İzleme Paneli", icon="📡")
PROJECT_ROOT = Path(__file__).resolve().parent
LOGO_IMAGE = PROJECT_ROOT / "assets" / "nitedrive-logo.png"


def _wrap_showcase() -> None:
    show_project_showcase(live_page=_PAGE_LIVE)


def main() -> None:
    st.set_page_config(
        page_title="NiteDrive",
        page_icon="🌙",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(NITEDRIVE_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.image(str(LOGO_IMAGE), use_container_width=True)
        st.caption("Yapay Zeka Tabanlı Sürücü İzleme Sistemi")
        st.divider()
        st.markdown(
            "**Gerçek Zamanlı Uykululuk Tespiti**  \n"
            "Computer Vision · ML · Arduino"
        )
        st.divider()
        st.markdown(
            '<div style="font-size:0.75rem;color:#64748b;">'
            "Demo platform · 1920×1080 sunum uyumlu"
            "</div>",
            unsafe_allow_html=True,
        )

    pages = [
        st.Page(_wrap_showcase, title="Proje Vitrini", icon="🏠", default=True),
        st.Page(show_technical_architecture, title="Teknik Mimari", icon="⚙️"),
        st.Page(show_dataset_training, title="Veri Seti ve Eğitim", icon="📊"),
        _PAGE_LIVE,
        st.Page(show_arduino_system, title="Arduino Uyarı Sistemi", icon="🔌"),
        st.Page(show_results_performance, title="Sonuçlar ve Performans", icon="🏆"),
    ]
    st.navigation({"NiteDrive": pages}).run()


if __name__ == "__main__":
    main()
