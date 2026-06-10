"""NiteDrive — premium automotive-AI theme (jüri sunumu / 1920×1080)."""

NITEDRIVE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #060b14;
}
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 1.5rem;
    max-width: 100%;
}
.stApp {
    background:
        linear-gradient(rgba(6,11,20,0.97), rgba(6,11,20,0.97)),
        repeating-linear-gradient(0deg, transparent, transparent 49px, rgba(30,58,95,0.12) 50px),
        repeating-linear-gradient(90deg, transparent, transparent 49px, rgba(30,58,95,0.12) 50px);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070d18 0%, #0c1525 100%);
    border-right: 1px solid rgba(56,189,248,0.25);
}
section[data-testid="stSidebar"] img {
    border-radius: 10px;
    border: 1px solid rgba(212, 181, 132, 0.26);
    box-shadow: 0 12px 34px rgba(0,0,0,0.35);
}

/* Glass cards */
.nd-glass {
    background: rgba(15, 23, 42, 0.72);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.22);
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
}
.nd-glass:hover { border-color: rgba(56,189,248,0.45); }

.nd-hero-mega {
    background: linear-gradient(135deg, #071018 0%, #0c1a2e 35%, #101935 70%, #0a1628 100%);
    border: 1px solid rgba(56,189,248,0.3);
    border-radius: 22px;
    padding: 3rem 2.8rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.nd-hero-mega::after {
    content: '';
    position: absolute; right: -80px; top: -80px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(14,165,233,0.18) 0%, transparent 70%);
}
.nd-logo {
    font-size: 4rem; font-weight: 900; margin: 0;
    background: linear-gradient(135deg, #22d3ee, #38bdf8, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
}
.nd-hero-logo {
    display: block;
    width: min(620px, 58vw);
    max-height: 280px;
    object-fit: contain;
    object-position: left center;
    margin: -1.2rem 0 0.8rem 0;
    border-radius: 14px;
    border: 1px solid rgba(212, 181, 132, 0.22);
    box-shadow: 0 18px 46px rgba(0,0,0,0.32);
}
.nd-tagline { font-size: 1.35rem; color: #94a3b8; margin: 0.6rem 0 0 0; font-weight: 500; }
.nd-lead { font-size: 1.02rem; color: #cbd5e1; line-height: 1.7; margin-top: 1.2rem; max-width: 900px; }

.nd-section-title {
    font-size: 1.75rem; font-weight: 800; color: #f1f5f9;
    border-left: 5px solid #22d3ee;
    padding-left: 16px; margin: 2rem 0 1rem 0;
    letter-spacing: -0.01em;
}
.nd-section-sub { color: #64748b; font-size: 0.95rem; margin: -0.5rem 0 1.2rem 0; }

.nd-stat-big {
    text-align: center; padding: 1.4rem 1rem;
}
.nd-stat-big .num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem; font-weight: 800; color: #22d3ee;
}
.nd-stat-big .lbl {
    font-size: 0.82rem; color: #94a3b8; text-transform: uppercase;
    letter-spacing: 0.1em; margin-top: 0.4rem; font-weight: 600;
}

.nd-card h4 {
    color: #38bdf8; font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem; text-transform: uppercase; letter-spacing: 0.08em;
    margin: 0 0 0.5rem 0;
}
.nd-card p, .nd-card li { color: #94a3b8; font-size: 0.9rem; line-height: 1.55; margin: 0; }
.nd-card { composes: nd-glass; }

.nd-hardware-shot {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(56, 189, 248, 0.22);
    border-radius: 16px;
    padding: 0.75rem;
    box-shadow: 0 12px 36px rgba(0,0,0,0.36);
}
.nd-hardware-shot img {
    border-radius: 10px;
    display: block;
}
.nd-img-caption {
    color: #94a3b8;
    font-size: 0.82rem;
    line-height: 1.45;
    margin-top: 0.65rem;
}
.nd-img-caption b { color: #e2e8f0; }

.nd-pipeline-box {
    background: rgba(30,41,59,0.85);
    border: 1px solid rgba(59,130,246,0.5);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    min-width: 140px;
    text-align: center;
}
.nd-pipeline-box .title {
    color: #e2e8f0; font-weight: 700; font-size: 0.82rem;
    font-family: 'JetBrains Mono', monospace;
}
.nd-pipeline-box .desc {
    color: #64748b; font-size: 0.72rem; margin-top: 0.35rem; line-height: 1.35;
}
.nd-pipe-arrow { color: #22d3ee; font-size: 1.4rem; font-weight: 800; padding: 0 0.2rem; }

.nd-code {
    background: #0a0f1a;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #a5f3fc;
    line-height: 1.6;
    white-space: pre-wrap;
    overflow-x: auto;
}

.nd-metric-xl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.1rem; font-weight: 800; color: #f8fafc;
    line-height: 1;
}
.nd-metric-lbl {
    color: #38bdf8; font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 0.35rem;
}

.nd-risk-safe {
    background: linear-gradient(135deg,#064e3b,#0f766e);
    border: 1px solid #34d399; border-radius: 14px;
    padding: 1.1rem; text-align: center; font-weight: 800; font-size: 1.25rem; color: #ecfdf5;
}
.nd-risk-warn {
    background: linear-gradient(135deg,#78350f,#b45309);
    border: 1px solid #fbbf24; border-radius: 14px;
    padding: 1.1rem; text-align: center; font-weight: 800; font-size: 1.25rem; color: #fffbeb;
}
.nd-risk-danger {
    background: linear-gradient(135deg,#7f1d1d,#dc2626);
    border: 1px solid #f87171; border-radius: 14px;
    padding: 1.3rem; text-align: center; font-weight: 800; font-size: 1.4rem; color: #fef2f2;
    animation: nd-pulse 1.2s ease-in-out infinite;
}
@keyframes nd-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
    50% { box-shadow: 0 0 24px 6px rgba(239,68,68,0.35); }
}
.nd-alert-box {
    background: rgba(69,10,10,0.9); border: 2px solid #ef4444;
    border-radius: 12px; padding: 1rem; margin-top: 0.8rem;
    font-family: 'JetBrains Mono', monospace; color: #fecaca; font-size: 0.88rem;
}

.nd-health-row {
    display: flex; align-items: center; gap: 0.55rem;
    color: #cbd5e1; font-size: 0.88rem; margin: 0.4rem 0;
}
.nd-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.nd-dot-on { background: #22c55e; box-shadow: 0 0 10px #22c55e; }
.nd-dot-warn { background: #eab308; box-shadow: 0 0 10px #eab308; }
.nd-dot-off { background: #475569; }

.nd-arduino-board {
    background: linear-gradient(145deg, #0d5c2e, #1a7a3e);
    border: 3px solid #22c55e;
    border-radius: 16px;
    padding: 2rem 1.5rem;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    color: #ecfdf5;
    min-height: 280px;
}
.nd-pin { background: #14532d; border: 1px solid #4ade80; border-radius: 6px;
    padding: 0.4rem 0.7rem; margin: 0.3rem; display: inline-block; font-size: 0.78rem; }

.nd-wiring-diagram {
    background:
        linear-gradient(135deg, rgba(8,13,24,0.96), rgba(15,23,42,0.92)),
        radial-gradient(circle at 18% 12%, rgba(56,189,248,0.16), transparent 34%);
    border: 1px solid rgba(56,189,248,0.28);
    border-radius: 18px;
    padding: 1.25rem;
    box-shadow: 0 12px 36px rgba(0,0,0,0.36), inset 0 1px 0 rgba(255,255,255,0.04);
}
.nd-wire-grid {
    display: grid;
    grid-template-columns: 1fr 56px 1fr;
    gap: 0.75rem;
    align-items: center;
}
.nd-device-node {
    min-height: 96px;
    border-radius: 14px;
    border: 1px solid rgba(56,189,248,0.28);
    background: rgba(15,23,42,0.78);
    padding: 0.9rem;
    position: relative;
}
.nd-device-node .icon {
    font-size: 1.5rem;
    line-height: 1;
    margin-bottom: 0.45rem;
}
.nd-device-node .title {
    color: #f8fafc;
    font-weight: 800;
    font-size: 0.92rem;
}
.nd-device-node .desc {
    color: #94a3b8;
    font-size: 0.74rem;
    line-height: 1.4;
    margin-top: 0.3rem;
}
.nd-device-node.ai { border-color: rgba(129,140,248,0.48); }
.nd-device-node.arduino { border-color: rgba(34,197,94,0.48); }
.nd-device-node.alert { border-color: rgba(248,113,113,0.55); }
.nd-device-node .pin {
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.18rem 0.45rem;
    border-radius: 999px;
    background: rgba(56,189,248,0.12);
    color: #a5f3fc;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
}
.nd-wire-arrow {
    color: #38bdf8;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    text-align: center;
}
.nd-wire-arrow::before {
    content: '';
    display: block;
    height: 2px;
    background: linear-gradient(90deg, rgba(56,189,248,0.15), #38bdf8, rgba(56,189,248,0.15));
    margin-bottom: 0.32rem;
}
.nd-wire-branch {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.7rem;
}
.nd-wire-caption {
    color: #64748b;
    font-size: 0.78rem;
    line-height: 1.45;
    margin-top: 0.9rem;
}

.nd-quote-final {
    background: linear-gradient(90deg, #0c4a6e, #1e3a8a, #312e81);
    border-radius: 20px; padding: 2.8rem; text-align: center; margin-top: 2rem;
    border: 1px solid rgba(56,189,248,0.3);
}
.nd-quote-line { font-size: 2.2rem; font-weight: 900; color: #f8fafc; margin: 0.25rem 0; }

.nd-note {
    background: rgba(30,58,95,0.35); border-left: 3px solid #38bdf8;
    padding: 0.8rem 1rem; border-radius: 0 8px 8px 0;
    color: #94a3b8; font-size: 0.85rem; margin-top: 1rem;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
"""
