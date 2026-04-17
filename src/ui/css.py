"""Global CSS injection for SHAI dashboard.

All design tokens from the KRI design system are encoded here.
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
    "hover": "#F9FAFB",
}

DIVERGING_SCALE = [
    "#2E7D5B", "#5B9E78", "#A8C4A4",
    "#E5E7EB",
    "#E8BE7C", "#D4A03C", "#B94A48",
]

GLOBAL_CSS = """
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
[data-testid="collapsedControl"] {
    visibility: visible !important;
    position: fixed;
    top: 8px;
    left: 8px;
    z-index: 999;
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
.sidebar-brand {
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 16px;
    margin-bottom: 16px;
}
.brand-mark {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    font-weight: 600;
    padding-left: var(--shai-brand-bar-offset);
    position: relative;
}
.brand-mark::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 4px;
    height: 16px;
    background: #C4A35A;
    border-radius: 1px;
}
.brand-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    margin: 6px 0 2px 0;
    line-height: 1.3;
}
.brand-sub {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    color: #9CA3AF;
}
.nav-section {
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
.control-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: var(--shai-label-track);
    color: #9CA3AF;
    font-weight: 600;
    margin-bottom: 6px;
}
/* Streamlit wraps label copy in <span>; sidebar span { white } was overriding these */
section[data-testid="stSidebar"] .control-label,
section[data-testid="stSidebar"] .control-label span {
    color: #C4A35A !important;
}
section[data-testid="stSidebar"] .riskklass-rad span:not(.riskklass-punkt) {
    color: rgba(255, 255, 255, 0.92) !important;
}

/* ---- Sidebar pills/chips ---- */
section[data-testid="stSidebar"] [data-testid="stPills"] button,
section[data-testid="stSidebar"] button[role="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: rgba(255,255,255,0.7) !important;
    border-radius: 4px !important;
    padding: 5px 10px !important;
    transition: background 0.15s !important;
}
section[data-testid="stSidebar"] [data-testid="stPills"] button:hover,
section[data-testid="stSidebar"] button[role="tab"]:hover {
    background: rgba(255,255,255,0.12) !important;
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] [data-testid="stPills"] button[aria-pressed="true"],
section[data-testid="stSidebar"] [data-testid="stPills"] button[aria-selected="true"],
section[data-testid="stSidebar"] button[role="tab"][aria-pressed="true"],
section[data-testid="stSidebar"] button[role="tab"][aria-selected="true"] {
    background: #C4A35A !important;
    border-color: #C4A35A !important;
    color: #0B1F3F !important;
    font-weight: 500 !important;
}

/* ---- Risk legend (sidebar) ---- */
.riskklass-legend {
    margin: 8px 0 10px 0;
}
.riskklass-rad {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: rgba(255,255,255,0.92);
    margin-bottom: 4px;
}
.riskklass-punkt {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

/* ---- Sidebar footer ---- */
.sidebar-footer {
    font-size: 10px;
    color: #6B7280;
    margin-top: 32px;
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.1);
}

/* ---- Page header (full row) ---- */
.shai-page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1.5px solid #EEF0F3;
    padding-bottom: 20px;
    margin-bottom: 24px;
}
.shai-header-meta {
    text-align: right;
    flex-shrink: 0;
}
.shai-year-display {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 36px;
    font-weight: 300;
    color: #9CA3AF;
    line-height: 1;
}
.shai-year-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #9CA3AF;
    margin-top: 4px;
}

/* ---- Page title block ---- */
.shai-eyebrow {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 600;
    font-size: var(--shai-label-upper);
    text-transform: uppercase;
    letter-spacing: var(--shai-label-track);
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
    margin-bottom: 0;
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
    font-variant-numeric: tabular-nums;
}
.shai-kpi-delta.up   { color: #B94A48; }
.shai-kpi-delta.down { color: #2E7D5B; }
.shai-kpi-delta.flat { color: #6B7280; }
.kpi-card--tipped { cursor: help; }

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

/* ---- Streamlit container as card ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #EEF0F3 !important;
    border-radius: 4px;
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
    font-variant-numeric: tabular-nums;
}
.shai-table tbody td.kommun-name {
    font-weight: 600;
    color: #0B1F3F;
}
.shai-table tbody td.rank-cell {
    width: 40px;
    text-align: center;
}
.shai-table tbody tr:hover {
    background: #F9FAFB;
}

/* ---- Footer note ---- */
.shai-footer-note {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
    font-size: 11px;
    color: #9CA3AF;
    padding: 12px 0;
    border-top: 1px solid #EEF0F3;
    margin-top: 32px;
}
.shai-footer-note code {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    background: #F7F8FA;
    border: 1px solid #EEF0F3;
    padding: 2px 6px;
    border-radius: 3px;
}

/* ==== LANDING PAGE COMPONENTS ==== */

/* ---- Hero ---- */
.lp-hero {
    background: linear-gradient(135deg, #0B1F3F 0%, #1B2A4A 55%, #0F2847 100%);
    border: 1px solid #C4A35A;
    border-radius: 6px;
    padding: var(--shai-hero-pad-top) 2rem 2rem 2rem;
}
.lp-hero-inner {
    max-width: 720px;
}
.lp-hero .lp-eyebrow {
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
.lp-headline {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 700;
    font-size: clamp(24px, 3vw, 36px);
    color: #FFFFFF;
    margin: 0 0 12px 0;
    line-height: 1.15;
}
.lp-hero-lead {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.6;
    max-width: 600px;
    margin: 0;
}

/* Hero: override stMain / Streamlit markdown h1+p colors on dark gradient */
[data-testid="stMain"] [data-testid="stMarkdown"] .lp-hero,
[data-testid="stMain"] .lp-hero {
    color: rgba(255, 255, 255, 0.92) !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .lp-hero .lp-eyebrow,
[data-testid="stMain"] .lp-hero .lp-eyebrow {
    color: #C4A35A !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .lp-hero h1.lp-headline,
[data-testid="stMain"] .lp-hero h1.lp-headline {
    color: #FFFFFF !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .lp-hero .lp-hero-lead,
[data-testid="stMain"] .lp-hero .lp-hero-lead {
    color: rgba(255, 255, 255, 0.85) !important;
}
[data-testid="stMain"] [data-testid="stMarkdown"] .lp-hero a,
[data-testid="stMain"] .lp-hero a {
    color: #E8D5A0 !important;
}

/* ---- Stat strip ---- */
.lp-stat-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border: 1px solid #EEF0F3;
    border-top: 3px solid #C4A35A;
    border-radius: 0 0 6px 6px;
    background: #FFFFFF;
    margin-top: -1px;
    margin-bottom: 32px;
}
.lp-stat-cell {
    padding: 20px 24px;
    border-right: 1px solid #EEF0F3;
}
.lp-stat-cell:last-child { border-right: none; }
.lp-stat-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #6B7280;
    margin-bottom: 6px;
}
.lp-stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    color: #1A1A2E;
    line-height: 1.1;
}
.lp-stat-unit {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}

/* ---- Landing sections ---- */
.lp-section {
    margin-bottom: 32px;
}
.lp-section-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: var(--shai-label-upper);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: var(--shai-label-track);
    color: #C4A35A;
    margin-bottom: 12px;
}
.lp-card-light {
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 24px 28px;
}
.lp-body {
    font-size: 15px;
    color: #1A1A2E;
    line-height: 1.65;
    max-width: 68ch;
    margin-bottom: 12px;
}
.lp-body-secondary {
    font-size: 14px;
    color: #6B7280;
    line-height: 1.6;
    max-width: 68ch;
}

/* ---- Weight bars ---- */
.lp-weight-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}
.lp-weight-name {
    font-size: 13px;
    color: #1A1A2E;
    min-width: 180px;
    font-weight: 500;
}
.lp-weight-bar-wrap {
    flex: 1;
    height: 10px;
    background: #EEF0F3;
    border-radius: 3px;
    overflow: hidden;
}
.lp-weight-bar {
    height: 100%;
    border-radius: 3px;
    transition: width 0.4s ease;
}
.lp-weight-pct {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #6B7280;
    min-width: 36px;
    text-align: right;
}
.lp-flow-svg-wrap {
    text-align: center;
    max-width: 620px;
    margin: 0 auto;
}
.lp-flow-svg { width: 100%; height: auto; }

/* ---- Pipeline steps ---- */
.lp-steps {
    display: flex;
    align-items: flex-start;
    gap: 0;
}
.lp-step {
    flex: 1;
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-left: 3px solid #C4A35A;
    border-radius: 4px;
    padding: 20px;
    transition: box-shadow 0.2s;
}
.lp-step:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.lp-step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #C4A35A;
    font-weight: 600;
    margin-bottom: 8px;
}
.lp-step-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 8px;
}
.lp-step-text {
    font-size: 13px;
    color: #6B7280;
    line-height: 1.5;
}
.lp-step-connector {
    display: flex;
    align-items: center;
    padding: 0 8px;
}
.lp-step-arrow-svg {
    width: 40px;
    height: 24px;
}

/* ---- Navigation cards (landing) ---- */
.lp-nav-card {
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
.lp-nav-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.lp-nav-card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.lp-nav-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    background: #F7F8FA;
    border-radius: 6px;
}
.lp-nav-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    color: #9CA3AF;
    letter-spacing: 0.5px;
}
.lp-nav-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 6px;
}
.lp-nav-desc {
    font-size: 13px;
    color: #6B7280;
    line-height: 1.5;
}

/* ---- Credibility block ---- */
.lp-cred {
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 24px;
    text-align: center;
    margin: 32px 0;
    background: #FFFFFF;
}
.lp-cred-pills {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.lp-cred-pill {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    background: #F7F8FA;
    border: 1px solid #EEF0F3;
    border-radius: 3px;
    padding: 4px 12px;
    color: #6B7280;
    letter-spacing: 0.3px;
}
.lp-cred-meta {
    font-size: 12px;
    color: #9CA3AF;
}

/* ==== RESPONSIVE ==== */
@media (max-width: 900px) {
    .lp-stat-strip { grid-template-columns: repeat(2, 1fr); }
    .lp-steps { flex-direction: column; gap: 12px; }
    .lp-step-connector {
        transform: rotate(90deg);
        padding: 4px 0;
        justify-content: center;
    }
}
@media (max-width: 520px) {
    .lp-stat-strip { grid-template-columns: 1fr; }
    .lp-stat-cell {
        border-right: none;
        border-bottom: 1px solid #EEF0F3;
    }
    .lp-stat-cell:last-child { border-bottom: none; }
    .lp-hero { padding-left: 1rem; padding-right: 1rem; }
}

/* ==== ACCESSIBILITY ==== */
@media (prefers-reduced-motion: reduce) {
    .lp-step,
    .lp-nav-card,
    .lp-step-arrow-svg,
    .lp-weight-bar {
        transition: none !important;
    }
}
</style>
"""


def inject_css() -> None:
    """Inject global CSS into the current Streamlit page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
