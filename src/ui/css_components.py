"""Component CSS: page header, KPI card, generic card, risk pill, table, footer.

    One block per component the data pages compose.

Split out of the 902-line `css.py` by T3.3 (Finding K). The slices are contiguous
and **order-preserving**: CSS resolves equal-specificity conflicts by source
order, so re-ordering these sheets would change the rendering. `css.inject_css()`
concatenates them in the order documented in that module.
"""

from __future__ import annotations

CSS = """/* ---- Page header (full row) ---- */
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
.shai-kpi-card--tipped { cursor: help; }

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
.shai-table thead th.shai-num {
    text-align: right;
}
.shai-table tbody td {
    padding: 8px 12px;
    border-bottom: 1px solid #EEF0F3;
    color: #1A1A2E;
}
.shai-table tbody td.shai-num {
    text-align: right;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
}
.shai-table tbody td.shai-kommun-name {
    font-weight: 600;
    color: #0B1F3F;
}
.shai-table tbody td.shai-rank-cell {
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

/* ---- Explanation line (T3.4) ---- */
/* Prose under a bare number. Muted and smaller than body text: it explains the
   figure above, it does not compete with it. */
.shai-explanation {
    font-size: 12.5px;
    line-height: 1.55;
    color: #6B7280;
    margin: 6px 0 2px 0;
    max-width: 78ch;
}

/* ---- Glossary badge (T3.5) ---- */
/* CSS-only popover: opens on hover AND on keyboard focus, so it is reachable
   without a pointer. `title=` attributes, which this replaces, are neither
   focusable nor visible on touch. */
.shai-help { position: relative; display: inline-block; margin-left: 6px; }

.shai-help-mark {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 1px solid #C4A35A;
    background: transparent;
    color: #C4A35A;
    font-size: 11px;
    line-height: 1;
    cursor: help;
    padding: 0;
}

.shai-help-mark:focus-visible { outline: 2px solid #C4A35A; outline-offset: 2px; }

.shai-help-pop {
    position: absolute;
    top: 22px;
    left: 0;
    z-index: 40;
    min-width: 240px;
    max-width: 340px;
    padding: 10px 12px;
    background: #FFFFFF;
    border: 1px solid #E3E6EC;
    border-radius: 6px;
    box-shadow: 0 6px 18px rgba(11, 31, 63, 0.12);
    font-size: 12px;
    line-height: 1.5;
    color: #1A1A2E;
    opacity: 0;
    visibility: hidden;
    transition: opacity 120ms ease;
}

.shai-help:hover .shai-help-pop,
.shai-help-mark:focus + .shai-help-pop,
.shai-help-mark:focus-visible + .shai-help-pop { opacity: 1; visibility: visible; }

.shai-help-pop dl { margin: 0; }
.shai-help-pop dt { font-weight: 600; margin-top: 6px; }
.shai-help-pop dt:first-child { margin-top: 0; }
.shai-help-pop dd { margin: 2px 0 0 0; color: #6B7280; }

/* ---- Data vintage badge (T3.6) ---- */
/* Finding C: the app used to claim freshness from the clock. This states the
   artifact's build date, where a reader will actually see it. */
.shai-vintage {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 3px 10px;
    border: 1px solid #E3E6EC;
    border-radius: 999px;
    background: #FFFFFF;
    font-size: 11.5px;
    color: #6B7280;
    letter-spacing: 0.01em;
}

.shai-vintage-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #2E7D5B;
}
"""
