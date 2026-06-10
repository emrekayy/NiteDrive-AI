"""NiteDrive — yeniden kullanılabilir UI bileşenleri."""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def glass_card(html: str) -> None:
    st.markdown(f'<div class="nd-glass nd-card">{html}</div>', unsafe_allow_html=True)


def code_block(text: str) -> None:
    st.markdown(f'<div class="nd-code">{text}</div>', unsafe_allow_html=True)


def pipeline_row(steps: list[tuple[str, str]], horizontal: bool = True) -> None:
    """[(title, description), ...]"""
    arrow = "➜" if horizontal else "↓"
    parts = []
    for i, (title, desc) in enumerate(steps):
        parts.append(
            f'<div class="nd-pipeline-box"><div class="title">{title}</div>'
            f'<div class="desc">{desc}</div></div>'
        )
        if i < len(steps) - 1:
            parts.append(f'<span class="nd-pipe-arrow">{arrow}</span>')
    wrap = "display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:0.45rem;"
    st.markdown(f'<div style="{wrap}">{"".join(parts)}</div>', unsafe_allow_html=True)


def stat_cards(labels: list[str], cols_per_row: int = 4) -> None:
    cols = st.columns(cols_per_row)
    for i, lbl in enumerate(labels):
        with cols[i % cols_per_row]:
            st.markdown(
                f'<div class="nd-glass nd-stat-big"><div class="num">●</div>'
                f'<div class="lbl">{lbl}</div></div>',
                unsafe_allow_html=True,
            )


def confusion_matrix_demo() -> go.Figure:
    labels = ["SAFE", "WARNING", "DROWSY"]
    z = [[118, 6, 2], [5, 94, 8], [1, 7, 89]]
    fig = go.Figure(data=go.Heatmap(
        z=z, x=labels, y=labels,
        colorscale=[[0, "#0f172a"], [0.5, "#1d4ed8"], [1, "#22d3ee"]],
        text=[[str(v) for v in row] for row in z],
        texttemplate="%{text}",
        showscale=False,
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#0f172a", plot_bgcolor="#111827",
        height=280, margin=dict(l=60, r=20, t=40, b=40),
        title="Confusion Matrix (Karmaşıklık Matrisi)",
        xaxis_title="Tahmin", yaxis_title="Gerçek",
    )
    return fig


def metric_performance_cards() -> None:
    metrics = [
        ("Accuracy (Doğruluk)", "92.4%", "#22d3ee"),
        ("Precision (Kesinlik)", "90.1%", "#38bdf8"),
        ("Recall (Duyarlılık)", "88.7%", "#818cf8"),
        ("F1-Score", "89.3%", "#a78bfa"),
    ]
    cols = st.columns(4)
    for col, (name, val, color) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="nd-glass" style="text-align:center;padding:1.2rem;">'
                f'<div class="nd-metric-lbl">{name}</div>'
                f'<div class="nd-metric-xl" style="color:{color};">{val}</div></div>',
                unsafe_allow_html=True,
            )


def demo_training_table() -> pd.DataFrame:
    return pd.DataFrame({
        "Frame_ID": ["001", "002", "003", "004", "005", "006"],
        "EAR": [0.31, 0.24, 0.17, 0.29, 0.21, 0.16],
        "PERCLOS": [0.08, 0.22, 0.51, 0.12, 0.35, 0.58],
        "Blink_Count": [4, 11, 19, 6, 14, 22],
        "Head_Angle": [3.2, 9.8, 26.4, 5.1, 15.2, 28.7],
        "Label": ["SAFE", "WARNING", "DROWSY", "SAFE", "WARNING", "DROWSY"],
    })
