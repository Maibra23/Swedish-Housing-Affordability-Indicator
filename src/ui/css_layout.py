"""Shell CSS: the font import, custom properties, Streamlit chrome and the sidebar.

    Carries the opening `<style>` tag and the Google Fonts `@import`, which must
    come first in the composed sheet — an `@import` after any rule is ignored.

Split out of the 902-line `css.py` by T3.3 (Finding K). The slices are contiguous
and **order-preserving**: CSS resolves equal-specificity conflicts by source
order, so re-ordering these sheets would change the rendering. `css.inject_css()`
concatenates them in the order documented in that module.
"""

from __future__ import annotations

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@300;400;600;700&display=swap');

/* ---- CSS custom properties ---- */
:root {
    --shai-pad-x: 1.5rem;
    --shai-pad-y: 2rem;
    --shai-label-upper: 11px;
    --shai-label-track: 1.5px;
    --shai-brand-bar-offset: 14px;
    --shai-hero-pad-top: 0.35rem;
}

/* ---- Root overrides ---- */
html, body, [class*="css"] {
    font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif;
    color: #1A1A2E;
}
.main .block-container {
    padding: 32px 40px;
    max-width: 1480px;
}

/* ---- Hide Streamlit chrome ---- */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
    padding: 0;
    margin: 0;
    min-height: 0;
}

/* ════ SIDEBAR — always visible, responsive ════════════════════════════ */

/* Desktop (≥ 769px): sidebar permanently open, all toggle buttons hidden */
@media (min-width: 769px) {
    /* Exterior button: the ">" that reopens a collapsed sidebar */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    /* Interior buttons: the close/collapse arrow inside the sidebar */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] button[aria-label="Close sidebar"],
    section[data-testid="stSidebar"] button[aria-label="Collapse sidebar"] {
        display: none !important;
    }
    /* Keep sidebar on-screen even if Streamlit applies a hide transform */
    section[data-testid="stSidebar"] {
        transform: translateX(0) !important;
        min-width: 260px !important;
        width: 260px !important;
    }
}

/* Mobile / tablet (≤ 768px): natural Streamlit overlay toggle */
@media (max-width: 768px) {
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 1000;
    }
    section[data-testid="stSidebar"] {
        width: min(280px, 85vw) !important;
        min-width: unset !important;
    }
    .main .block-container {
        padding: 16px !important;
    }
}

/* ---- App background ---- */
.stApp { background-color: #F7F8FA; }

/* ---- Main content text color ---- */
[data-testid="stMain"],
[data-testid="stMain"] .block-container {
    color: #1A1A2E;
}
[data-testid="stMain"],
[data-testid="stSidebar"] {
    padding-top: 0;
    margin-top: 0;
}

/* ---- Sidebar dark navy ---- */
section[data-testid="stSidebar"] {
    background-color: #0B1F3F;
    color: #FFFFFF;
    min-width: 260px !important;
    width: 260px !important;
    border-right: 1px solid #EEF0F3;
}
section[data-testid="stSidebar"] > div {
    width: 260px !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding: var(--shai-pad-x) var(--shai-pad-y);
}
section[data-testid="stSidebar"] .block-container {
    padding-left: 0;
    padding-right: 0;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label {
    color: #9CA3AF !important;
}

/* ---- Sidebar brand (KRI-style) ---- */
.shai-sidebar-brand {
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 16px;
    margin-bottom: 16px;
}
.shai-brand-mark {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    font-weight: 600;
    padding-left: var(--shai-brand-bar-offset);
    position: relative;
}
.shai-brand-mark::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 4px;
    height: 16px;
    background: #C4A35A;
    border-radius: 1px;
}
.shai-brand-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    margin: 6px 0 2px 0;
    line-height: 1.3;
}
.shai-brand-sub {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    color: #9CA3AF;
}
.shai-sidebar-section-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #9CA3AF;
    font-weight: 600;
    margin-bottom: 8px;
}

/* ---- Sidebar page links ---- */
section[data-testid="stSidebarContent"] a[href] {
    display: block;
    padding: 8px 12px;
    color: rgba(255,255,255,0.65) !important;
    text-decoration: none !important;
    font-size: 13px;
    border-radius: 4px;
    margin-bottom: 2px;
    transition: background 0.15s, color 0.15s;
    border-left: 3px solid transparent;
}
section[data-testid="stSidebarContent"] a[href]:hover {
    background: rgba(255,255,255,0.08);
    color: #FFFFFF !important;
}
section[data-testid="stSidebarContent"] a[href][aria-current="page"] {
    background: rgba(196, 163, 90, 0.12);
    color: #FFFFFF !important;
    border-left-color: #C4A35A;
}

/* ---- Control label (sidebar) ---- */
.shai-control-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: var(--shai-label-track);
    color: #9CA3AF;
    font-weight: 600;
    margin-bottom: 6px;
}
/* Streamlit wraps label copy in <span>; sidebar span { white } was overriding these */
section[data-testid="stSidebar"] .shai-control-label,
section[data-testid="stSidebar"] .shai-control-label span {
    color: #C4A35A !important;
}
section[data-testid="stSidebar"] .shai-risk-legend-row span:not(.shai-risk-legend-dot) {
    color: rgba(255, 255, 255, 0.92) !important;
}

/* ---- Sidebar pills/chips ---- */
/* Broad selectors to cover st.pills across Streamlit versions */
section[data-testid="stSidebar"] [data-testid="stPills"] button,
section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button,
section[data-testid="stSidebar"] [role="tablist"] button,
section[data-testid="stSidebar"] button[role="tab"],
section[data-testid="stSidebar"] button[kind="pills"],
section[data-testid="stSidebar"] button[data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    color: rgba(255,255,255,0.85) !important;
    border-radius: 4px !important;
    padding: 5px 10px !important;
    transition: background 0.15s !important;
}
section[data-testid="stSidebar"] [data-testid="stPills"] button:hover,
section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button:hover,
section[data-testid="stSidebar"] [role="tablist"] button:hover,
section[data-testid="stSidebar"] button[role="tab"]:hover,
section[data-testid="stSidebar"] button[kind="pills"]:hover,
section[data-testid="stSidebar"] button[data-baseweb="tab"]:hover {
    background: rgba(255,255,255,0.18) !important;
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] [data-testid="stPills"] button[aria-pressed="true"],
section[data-testid="stSidebar"] [data-testid="stPills"] button[aria-selected="true"],
section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-pressed="true"],
section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] button[aria-selected="true"],
section[data-testid="stSidebar"] [role="tablist"] button[aria-pressed="true"],
section[data-testid="stSidebar"] [role="tablist"] button[aria-selected="true"],
section[data-testid="stSidebar"] [role="tablist"] button[aria-checked="true"],
section[data-testid="stSidebar"] button[role="tab"][aria-pressed="true"],
section[data-testid="stSidebar"] button[role="tab"][aria-selected="true"],
section[data-testid="stSidebar"] button[data-baseweb="tab"][aria-selected="true"] {
    background: #C4A35A !important;
    border-color: #C4A35A !important;
    color: #0B1F3F !important;
    font-weight: 500 !important;
}
/* Catch-all: force any remaining button-like elements in the sidebar to dark theme */
section[data-testid="stSidebar"] [data-testid="stPills"] [role="tablist"],
section[data-testid="stSidebar"] [data-testid="stSegmentedControl"] [role="tablist"] {
    background: transparent !important;
    border: none !important;
    gap: 4px !important;
}

/* ---- Risk legend (sidebar) ---- */
.shai-risk-legend {
    margin: 8px 0 10px 0;
}
.shai-risk-legend-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: rgba(255,255,255,0.92);
    margin-bottom: 4px;
}
.shai-risk-legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

/* ---- Sidebar footer ---- */
.shai-sidebar-footer {
    font-size: 10px;
    color: #6B7280;
    margin-top: 32px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.1);
}

"""
