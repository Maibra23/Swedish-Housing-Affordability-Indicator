"""Reusable UI components for SHAI dashboard.

All components return HTML strings for use with st.markdown(unsafe_allow_html=True).
Design tokens match DESIGN_SYSTEM.md exactly.
"""

from __future__ import annotations

import streamlit as st


def page_title(eyebrow: str, title: str, subtitle: str = "") -> None:
    """Render the standard SHAI page title block."""
    html = f"""
    <div style="margin-bottom: 24px;">
        <div class="shai-eyebrow">{eyebrow}</div>
        <div class="shai-page-title">{title}</div>
        {"<div class='shai-page-subtitle'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def kpi_card(
    label: str,
    value: str,
    unit: str = "",
    delta: str = "",
    delta_direction: str = "flat",
    variant: str = "default",
) -> str:
    """Return HTML for a KPI card.

    Args:
        label: Uppercase label text.
        value: Main display value.
        unit: Optional unit suffix.
        delta: Delta text (e.g. "+2.3%").
        delta_direction: "up", "down", or "flat".
        variant: "default", "accent", "danger", or "success".
    """
    delta_html = ""
    if delta:
        arrows = {"up": "\u25B2", "down": "\u25BC", "flat": "\u25C6"}
        arrow = arrows.get(delta_direction, "")
        delta_html = f'<div class="shai-kpi-delta {delta_direction}">{arrow} {delta}</div>'

    unit_html = f'<span class="shai-kpi-unit">{unit}</span>' if unit else ""

    return f"""
    <div class="shai-kpi-card variant-{variant}">
        <div class="shai-kpi-label">{label}</div>
        <div class="shai-kpi-value">{value}{unit_html}</div>
        {delta_html}
    </div>
    """


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


def risk_pill(level: str) -> str:
    """Return HTML for a risk classification pill.

    Args:
        level: "lag", "medel", or "hog".
    """
    labels = {"lag": "Låg", "medel": "Medel", "hog": "Hög"}
    label = labels.get(level, level.capitalize())
    return f'<span class="shai-risk-pill {level}">{label}</span>'


def render_kpi_row(cards: list[str]) -> None:
    """Render a row of KPI cards using Streamlit columns."""
    cols = st.columns(len(cards))
    for col, card_html in zip(cols, cards):
        with col:
            st.markdown(card_html, unsafe_allow_html=True)


def format_sek(value: float, decimals: int = 0) -> str:
    """Format a SEK value with space thousand separators."""
    if decimals == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", " ").replace(".", ",")


def format_pct(value: float, decimals: int = 1) -> str:
    """Format a percentage value Swedish style."""
    return f"{value:,.{decimals}f}".replace(".", ",") + "%"
