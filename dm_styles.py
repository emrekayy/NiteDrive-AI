"""Dark cyber-automotive theme for Streamlit dashboard (1920×1080 demo recording)."""

DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0a0e17;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
    max-width: 100%;
}

h1 {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #e8f4ff !important;
    font-size: 2.2rem !important;
}

.subtitle {
    color: #6b8aab;
    font-size: 1rem;
    margin-bottom: 1.2rem;
}

.panel-card {
    background: linear-gradient(145deg, #111827 0%, #0d1320 100%);
    border: 1px solid #1e3a5f;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
    margin-bottom: 0.8rem;
}

.panel-title {
    color: #5eead4;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #f0f9ff;
    line-height: 1.1;
}

.metric-label {
    color: #7dd3fc;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.status-safe {
    background: linear-gradient(90deg, #064e3b, #0f766e);
    border: 1px solid #34d399;
    color: #ecfdf5;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-size: 1.4rem;
    font-weight: 700;
    text-align: center;
}

.status-warning {
    background: linear-gradient(90deg, #78350f, #b45309);
    border: 1px solid #fbbf24;
    color: #fffbeb;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-size: 1.4rem;
    font-weight: 700;
    text-align: center;
}

.status-danger {
    background: linear-gradient(90deg, #7f1d1d, #b91c1c);
    border: 1px solid #f87171;
    color: #fef2f2;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-size: 1.4rem;
    font-weight: 700;
    text-align: center;
}

.alert-box {
    background: #450a0a;
    border: 2px solid #ef4444;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-top: 0.8rem;
    color: #fecaca;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
}

.pipeline-wrap {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 1rem;
    background: #0f172a;
    border: 1px solid #1e40af;
    border-radius: 14px;
}

.pipeline-step {
    background: #1e293b;
    border: 1px solid #3b82f6;
    color: #bfdbfe;
    padding: 0.55rem 1rem;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 600;
}

.pipeline-arrow {
    color: #38bdf8;
    font-size: 1.2rem;
    font-weight: 700;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""

PIPELINE_STEPS = [
    "Camera",
    "OpenCV",
    "MediaPipe",
    "Feature Extraction",
    "Random Forest",
    "Arduino Alert",
]
