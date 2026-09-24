"""Landing-page CSS: hero, stat strip, weight bars, pipeline steps, nav cards.

    Reached only through `app.py`, so the landing page can change without
    touching the sheet every data page loads.

Split out of the 902-line `css.py` by T3.3 (Finding K). The slices are contiguous
and **order-preserving**: CSS resolves equal-specificity conflicts by source
order, so re-ordering these sheets would change the rendering. `css.inject_css()`
concatenates them in the order documented in that module.
"""

from __future__ import annotations

CSS = """/* ==== LANDING PAGE COMPONENTS ==== */

/* ---- Hero ---- */
.shai-hero {
    background: linear-gradient(135deg, #0B1F3F 0%, #1B2A4A 55%, #0F2847 100%);
    border: 1px solid #C4A35A;
    border-radius: 6px;
    padding: var(--shai-hero-pad-top) 2rem 2rem 2rem;
}
.shai-hero-inner {
    max-width: 720px;
}
.shai-hero .shai-hero-eyebrow {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    padding-left: var(--shai-brand-bar-offset);
    margin-bottom: 12px;
    margin-top: 20px;
}
.shai-headline {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 700;
    font-size: clamp(24px, 3vw, 36px);
    color: #FFFFFF;
    margin: 0 0 12px 0;
    line-height: 1.15;
}
.shai-hero-lead {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.6;
    max-width: 600px;
    margin: 0;
}

/* Hero: override stMain / Streamlit markdown h1+p colors on dark gradient */
[data-testid="stMain"] [data-testid="stMarkdown"] .shai-hero,
[data-testid="stMain"] .shai-hero {
    color: rgba(255, 255, 255, 0.92) !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .shai-hero .shai-hero-eyebrow,
[data-testid="stMain"] .shai-hero .shai-hero-eyebrow {
    color: #C4A35A !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .shai-hero h1.shai-headline,
[data-testid="stMain"] .shai-hero h1.shai-headline {
    color: #FFFFFF !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .shai-hero .shai-hero-lead,
[data-testid="stMain"] .shai-hero .shai-hero-lead {
    color: rgba(255, 255, 255, 0.85) !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .shai-hero a,
[data-testid="stMain"] .shai-hero a {
    color: #E8D5A0 !important;
}

/* ---- Stat strip ---- */
.shai-stat-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border: 1px solid #EEF0F3;
    border-top: 3px solid #C4A35A;
    border-radius: 0 0 6px 6px;
    background: #FFFFFF;
    margin-top: -1px;
    margin-bottom: 32px;
}
.shai-stat-cell {
    padding: 20px 24px;
    border-right: 1px solid #EEF0F3;
}
.shai-stat-cell:last-child { border-right: none; }
.shai-stat-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #6B7280;
    margin-bottom: 6px;
}
.shai-stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    color: #1A1A2E;
    line-height: 1.1;
}
.shai-stat-unit {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}

/* ---- Landing sections ---- */
.shai-section {
    margin-bottom: 32px;
}
.shai-section-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: var(--shai-label-upper);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: var(--shai-label-track);
    color: #C4A35A;
    margin-bottom: 12px;
}
.shai-card-light {
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 24px 28px;
}
.shai-body {
    font-size: 15px;
    color: #1A1A2E;
    line-height: 1.65;
    max-width: 68ch;
    margin-bottom: 12px;
}
.shai-body-secondary {
    font-size: 14px;
    color: #6B7280;
    line-height: 1.6;
    max-width: 68ch;
}

/* ---- Weight bars ---- */
.shai-weight-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}
.shai-weight-name {
    font-size: 13px;
    color: #1A1A2E;
    min-width: 180px;
    font-weight: 500;
}
.shai-weight-bar-wrap {
    flex: 1;
    height: 10px;
    background: #EEF0F3;
    border-radius: 3px;
    overflow: hidden;
}
.shai-weight-bar {
    height: 100%;
    border-radius: 3px;
    transition: width 0.4s ease;
}
.shai-weight-pct {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #6B7280;
    min-width: 36px;
    text-align: right;
}
.shai-flow-svg-wrap {
    text-align: center;
    max-width: 620px;
    margin: 0 auto;
}
.shai-flow-svg { width: 100%; height: auto; }

/* ---- Pipeline steps ---- */
.shai-steps {
    display: flex;
    align-items: flex-start;
    gap: 0;
}
.shai-step {
    flex: 1;
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-left: 3px solid #C4A35A;
    border-radius: 4px;
    padding: 20px;
    transition: box-shadow 0.2s;
}
.shai-step:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.shai-step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #C4A35A;
    font-weight: 600;
    margin-bottom: 8px;
}
.shai-step-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 8px;
}
.shai-step-text {
    font-size: 13px;
    color: #6B7280;
    line-height: 1.5;
}
.shai-step-connector {
    display: flex;
    align-items: center;
    padding: 0 8px;
}
.shai-step-arrow-svg {
    width: 40px;
    height: 24px;
}

/* ---- Navigation cards (landing) ---- */
.shai-nav-card {
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-left: 3px solid #C4A35A;
    border-radius: 4px;
    padding: 20px;
    min-height: 140px;
    transition: box-shadow 0.2s, transform 0.15s;
    cursor: default;
    margin-bottom: 12px;
}
.shai-nav-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.shai-nav-card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.shai-nav-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    background: #F7F8FA;
    border-radius: 6px;
}
.shai-nav-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    color: #9CA3AF;
    letter-spacing: 0.5px;
}
.shai-nav-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 6px;
}
.shai-nav-desc {
    font-size: 13px;
    color: #6B7280;
    line-height: 1.5;
}

/* ---- Credibility block ---- */
.shai-cred {
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 24px;
    text-align: center;
    margin: 32px 0;
    background: #FFFFFF;
}
.shai-cred-pills {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.shai-cred-pill {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    background: #F7F8FA;
    border: 1px solid #EEF0F3;
    border-radius: 3px;
    padding: 4px 12px;
    color: #6B7280;
    letter-spacing: 0.3px;
}
.shai-cred-meta {
    font-size: 12px;
    color: #9CA3AF;
}

"""
