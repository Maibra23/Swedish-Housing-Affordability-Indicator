"""Global CSS injection for SHAI dashboard.

All design tokens from DESIGN_SYSTEM.md are encoded here.
Call inject_css() once per page to apply.
"""

import streamlit as st

COLORS = {
    "primary": "#0B1F3F",
    "primary_light": "#1B2A4A",
    "secondary": "#4A6FA5",
    "accent": "#C4A35A",
    "low_risk": "#2E7D5B",
    "medium_risk": "#D4A03C",
    "high_risk": "#B94A48",
    "bg": "#F7F8FA",
    "card_bg": "#FFFFFF",
    "text_primary": "#1A1A2E",
    "text_secondary": "#6B7280",
    "text_tertiary": "#9CA3AF",
    "border": "#EEF0F3",
    "grid": "#E5E7EB",
}

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600;700&display=swap');

/* ---- Root overrides ---- */
html, body, [class*="css"] {
    font-family: 'Source Sans 3', 'Source Sans Pro', sans-serif;
    color: #1A1A2E;
}
.main .block-container {
    padding: 32px 40px;
    max-width: 1280px;
}

/* ---- Sidebar dark navy ---- */
section[data-testid="stSidebar"] {
    background-color: #0B1F3F;
    color: #FFFFFF;
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

/* ---- Page title block ---- */
.shai-eyebrow {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    margin-bottom: 4px;
}
.shai-page-title {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 700;
    font-size: 28px;
    color: #1A1A2E;
    margin: 0 0 4px 0;
    line-height: 1.2;
}
.shai-page-subtitle {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 400;
    font-size: 14px;
    color: #6B7280;
    margin-bottom: 24px;
}

/* ---- KPI card ---- */
.shai-kpi-card {
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
}
.shai-kpi-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
}
.shai-kpi-card.variant-default::before { background: #0B1F3F; }
.shai-kpi-card.variant-accent::before  { background: #C4A35A; }
.shai-kpi-card.variant-danger::before  { background: #B94A48; }
.shai-kpi-card.variant-success::before { background: #2E7D5B; }

.shai-kpi-label {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #6B7280;
    margin-bottom: 8px;
}
.shai-kpi-value {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 700;
    font-size: 32px;
    color: #1A1A2E;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
}
.shai-kpi-unit {
    font-size: 14px;
    font-weight: 400;
    color: #6B7280;
    margin-left: 4px;
}
.shai-kpi-delta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    margin-top: 6px;
}
.shai-kpi-delta.up   { color: #B94A48; }
.shai-kpi-delta.down { color: #2E7D5B; }
.shai-kpi-delta.flat { color: #6B7280; }

/* ---- Generic card ---- */
.shai-card {
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 22px 24px;
    margin-bottom: 16px;
}
.shai-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1px solid #EEF0F3;
    padding-bottom: 14px;
    margin-bottom: 16px;
}
.shai-card-title {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 700;
    font-size: 15px;
    color: #1A1A2E;
}
.shai-card-subtitle {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 400;
    font-size: 12px;
    color: #6B7280;
    margin-top: 2px;
}
.shai-card-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9.5px;
    text-transform: uppercase;
    color: #9CA3AF;
    letter-spacing: 0.5px;
}

/* ---- Risk pill ---- */
.shai-risk-pill {
    display: inline-block;
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    padding: 3px 10px;
    border-radius: 3px;
}
.shai-risk-pill.lag {
    background: rgba(46, 125, 91, 0.12);
    border: 1px solid rgba(46, 125, 91, 0.30);
    color: #2E7D5B;
}
.shai-risk-pill.medel {
    background: rgba(212, 160, 60, 0.12);
    border: 1px solid rgba(212, 160, 60, 0.30);
    color: #D4A03C;
}
.shai-risk-pill.hog {
    background: rgba(185, 74, 72, 0.12);
    border: 1px solid rgba(185, 74, 72, 0.30);
    color: #B94A48;
}

/* ---- Table styling ---- */
.shai-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Source Sans 3', sans-serif;
    font-size: 13px;
}
.shai-table thead th {
    font-weight: 600;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #6B7280;
    border-bottom: 1.5px solid #0B1F3F;
    padding: 8px 12px;
    text-align: left;
}
.shai-table thead th.num {
    text-align: right;
}
.shai-table tbody td {
    padding: 8px 12px;
    border-bottom: 1px solid #EEF0F3;
    color: #1A1A2E;
}
.shai-table tbody td.num {
    text-align: right;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
}
.shai-table tbody tr:hover {
    background: #F9FAFB;
}

/* ---- Sidebar nav ---- */
.shai-sidebar-brand {
    border-left: 3px solid #C4A35A;
    padding-left: 12px;
    margin-bottom: 24px;
}
.shai-sidebar-eyebrow {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    font-weight: 600;
}
.shai-sidebar-title {
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
    margin: 4px 0 2px 0;
}
.shai-sidebar-subtitle {
    font-size: 12px;
    color: #9CA3AF;
}
.shai-sidebar-nav a {
    display: block;
    padding: 8px 12px;
    color: #9CA3AF;
    text-decoration: none;
    font-size: 13px;
    border-radius: 4px;
    margin-bottom: 2px;
    transition: background 0.15s;
}
.shai-sidebar-nav a:hover,
.shai-sidebar-nav a.active {
    background: rgba(255,255,255,0.08);
    color: #FFFFFF;
}
.shai-sidebar-footer {
    font-size: 10px;
    color: #6B7280;
    margin-top: 32px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.1);
}
</style>
"""


def inject_css() -> None:
    """Inject global CSS into the current Streamlit page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
