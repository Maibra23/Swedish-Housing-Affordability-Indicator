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

"""
