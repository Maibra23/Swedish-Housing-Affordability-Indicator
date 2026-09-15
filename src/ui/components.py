"""Reusable UI components for SHAI dashboard.

All components return HTML strings for use with st.markdown(unsafe_allow_html=True).
Design tokens match the KRI design system exactly.
"""

from __future__ import annotations

import re
import streamlit as st

from src.provenance import complete_case_max_year, first_year, n_kommuner
from src.ui.css import COLORS


def _panel_facts(
    kommun_count: int | None = None,
    period_start: int | None = None,
    period_end: int | None = None,
) -> tuple[int, int, int]:
    """Resolve the panel's dimensions, reading the artifact for anything omitted.

    Landing copy used to state `290 kommuner` and `2014–2024` as literals, which
    made the sentences independent of the data they describe — see Finding H.
    Resolution happens per call rather than at import so a refresh mid-session
    is picked up, and the explicit arguments exist so tests can vary the panel
    without writing a file.
    """
    return (
        n_kommuner() if kommun_count is None else kommun_count,
        first_year() if period_start is None else period_start,
        complete_case_max_year() if period_end is None else period_end,
    )


def _compact(html: str) -> str:
    """Remove blank/whitespace-only lines from HTML to prevent the markdown
    parser from splitting HTML blocks at blank lines, which causes subsequent
    indented tags to be rendered as code blocks (raw text on screen)."""
    return re.sub(r'\n[ \t]*\n', '\n', html)


# ── Formatting utilities ──────────────────────────────────────────────


def format_sek(value: float, decimals: int = 0) -> str:
    """Format a SEK value with non-breaking space thousand separators."""
    if decimals == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "\u00A0").replace(".", ",")


def format_pct(value: float, decimals: int = 1) -> str:
    """Format a percentage value Swedish style."""
    return f"{value:,.{decimals}f}".replace(".", ",") + "%"


def format_swedish_int(value: int) -> str:
    """Format integer with non-breaking space thousands separator."""
    return f"{value:,}".replace(",", "\u00A0")


# ── Page header ───────────────────────────────────────────────────────


def page_title(
    eyebrow: str,
    title: str,
    subtitle: str = "",
    year: int | str = "",
) -> None:
    """Render the standard SHAI page title block with optional year display."""
    year_html = ""
    if year:
        year_html = f"""
        <div class="shai-header-meta">
            <div class="shai-year-display">{year}</div>
            <div class="shai-year-label">Analysår</div>
        </div>
        """
    html = f"""
    <div class="shai-page-header">
        <div>
            <div class="shai-eyebrow">{eyebrow}</div>
            <div class="shai-page-title">{title}</div>
            {"<div class='shai-page-subtitle'>" + subtitle + "</div>" if subtitle else ""}
        </div>
        {year_html}
    </div>
    """
    st.markdown(_compact(html), unsafe_allow_html=True)


# ── KPI card ──────────────────────────────────────────────────────────


def kpi_card(
    label: str,
    value: str,
    unit: str = "",
    delta: str = "",
    delta_direction: str = "flat",
    variant: str = "default",
    tooltip: str | None = None,
) -> str:
    """Return HTML for a KPI card.

    Args:
        label: Uppercase label text.
        value: Main display value.
        unit: Optional unit suffix.
        delta: Delta text (e.g. "+2.3%").
        delta_direction: "up", "down", or "flat".
        variant: "default", "accent", "danger", or "success".
        tooltip: Optional tooltip text shown on hover.
    """
    delta_html = ""
    if delta:
        arrows = {"up": "\u25B2", "down": "\u25BC", "flat": "\u25C6"}
        arrow = arrows.get(delta_direction, "")
        delta_html = f'<div class="shai-kpi-delta {delta_direction}">{arrow} {delta}</div>'

    unit_html = f'<span class="shai-kpi-unit">{unit}</span>' if unit else ""
    tip_attr = f'title="{tooltip}"' if tooltip else ""
    tip_class = " shai-kpi-card--tipped" if tooltip else ""

    return f"""
    <div class="shai-kpi-card variant-{variant}{tip_class}" {tip_attr}>
        <div class="shai-kpi-label">{label}</div>
        <div class="shai-kpi-value">{value}{unit_html}</div>
        {delta_html}
    </div>
    """


def render_kpi_row(cards: list[str]) -> None:
    """Render a row of KPI cards using Streamlit columns."""
    cols = st.columns(len(cards))
    for col, card_html in zip(cols, cards):
        with col:
            st.markdown(card_html, unsafe_allow_html=True)


# ── Generic card ──────────────────────────────────────────────────────


def card(title: str, subtitle: str = "", tag: str = "", content: str = "") -> str:
    """Return HTML for a generic card with header."""
    tag_html = f'<span class="shai-card-tag">{tag}</span>' if tag else ""

    return f"""
    <div class="shai-card">
        <div class="shai-card-header">
            <div>
                <div class="shai-card-title">{title}</div>
                {"<div class='shai-card-subtitle'>" + subtitle + "</div>" if subtitle else ""}
            </div>
            {tag_html}
        </div>
        {content}
    </div>
    """


def card_header(title: str, subtitle: str = "", tag: str = "") -> str:
    """Return just the card header HTML (for use inside st.container)."""
    tag_html = f'<span class="shai-card-tag">{tag}</span>' if tag else ""
    return f"""
    <div class="shai-card-header">
        <div>
            <div class="shai-card-title">{title}</div>
            {"<div class='shai-card-subtitle'>" + subtitle + "</div>" if subtitle else ""}
        </div>
        {tag_html}
    </div>
    """


# ── Risk pill ─────────────────────────────────────────────────────────


def risk_pill(level: str) -> str:
    """Return HTML for a risk classification pill.

    Args:
        level: "lag", "medel", or "hog".
    """
    labels = {"lag": "Låg", "medel": "Medel", "hog": "Hög"}
    label = labels.get(level, level.capitalize())
    return f'<span class="shai-risk-pill {level}">{label}</span>'


# ── Footer ────────────────────────────────────────────────────────────


def footer_note(
    source: str = "SCB, Riksbanken, Kolada",
    version: str = "SHAI v1.3",
) -> None:
    """Render the standard page footer."""
    html = f"""
    <div class="shai-footer-note">
        <span><strong>KÄLLA:</strong> {source}</span>
        <span><code>{version}</code></span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
