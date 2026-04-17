"""Reusable UI components for SHAI dashboard.

All components return HTML strings for use with st.markdown(unsafe_allow_html=True).
Design tokens match the KRI design system exactly.
"""

from __future__ import annotations

import re
import streamlit as st

from src.ui.css import COLORS


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
    tip_class = " kpi-card--tipped" if tooltip else ""

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


# ══════════════════════════════════════════════════════════════════════
# LANDING PAGE COMPONENTS
# ══════════════════════════════════════════════════════════════════════


def render_landing_hero() -> None:
    """Render the KRI-style landing hero section."""
    html = """
    <div class="lp-hero">
        <div class="lp-hero-inner">
            <div class="lp-eyebrow">Bostadsekonomisk hållbarhetsanalys</div>
            <h1 class="lp-headline">Swedish Housing<br>Affordability Indicator</h1>
            <p class="lp-hero-lead">
                Strukturell bostadsekonomisk hållbarhet i Sveriges 290 kommuner
                och 21 län &mdash; med tre ekonometriska formler, prognoser och scenariosimulering.
            </p>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_landing_stat_strip(stats: list[dict]) -> None:
    """Render a stat strip connected to the hero.

    Args:
        stats: List of dicts with keys: label, value, unit.
    """
    cells = ""
    for s in stats:
        cells += f"""
        <div class="lp-stat-cell">
            <div class="lp-stat-label">{s['label']}</div>
            <div class="lp-stat-value">{s['value']}</div>
            <div class="lp-stat-unit">{s.get('unit', '')}</div>
        </div>
        """
    html = f'<div class="lp-stat-strip">{cells}</div>'
    st.markdown(_compact(html), unsafe_allow_html=True)


def render_landing_what_is_block() -> None:
    """Render the 'Vad ar SHAI?' explanation block."""
    html = """
    <div class="lp-section">
        <div class="lp-section-title">Vad är SHAI?</div>
        <div class="lp-card-light lp-explain-card">
            <div class="lp-body">
                SHAI (Swedish Housing Affordability Indicator) mäter strukturell
                bostadsekonomisk hållbarhet genom tre ekonometriska formler som
                kombinerar inkomst, bostadspriser, räntor och inflation.
            </div>
            <div class="lp-body-secondary">
                Indikatorn analyserar Sveriges 290 kommuner och 21 län med data
                från SCB, Riksbanken och Kolada. Utöver indexet erbjuds prognoser
                (Prophet och ARIMA), kontantinsatsanalys under fyra regelverk,
                och en scenariosimulator för stresstester.
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_index_visual_block() -> None:
    """Render the index overview block with weight bars and flow diagram."""
    weights = [
        ("K/T-kvot (prisnivå)", 35, COLORS["secondary"]),
        ("Medianinkomst", 25, "#3D8B6E"),
        ("Styrränta (nominal)", 20, COLORS["accent"]),
        ("Inflation (KPI)", 10, "#D4785A"),
        ("Arbetslöshet", 10, "#7B68A8"),
    ]

    bars_html = ""
    for name, pct, color in weights:
        bars_html += f"""
        <div class="lp-weight-row">
            <span class="lp-weight-name">{name}</span>
            <div class="lp-weight-bar-wrap">
                <div class="lp-weight-bar" style="width:{pct}%;background:{color};"></div>
            </div>
            <span class="lp-weight-pct">{pct}%</span>
        </div>
        """

    flow_svg = """
    <div class="lp-flow-svg-wrap">
        <svg viewBox="0 0 580 130" class="lp-flow-svg" aria-hidden="true">
            <defs>
                <marker id="arr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#C4A35A"/>
                </marker>
                <marker id="arr-g" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#2E7D5B"/>
                </marker>
                <marker id="arr-y" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#D4A03C"/>
                </marker>
                <marker id="arr-r" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#B94A48"/>
                </marker>
            </defs>

            <!-- Input indicators -->
            <rect x="0" y="8" width="110" height="26" rx="4" fill="rgba(74,111,165,0.1)" stroke="#4A6FA5" stroke-width="1"/>
            <text x="55" y="25" text-anchor="middle" fill="#4A6FA5" font-size="10" font-family="Source Sans 3, sans-serif" font-weight="600">Inkomst</text>

            <rect x="0" y="42" width="110" height="26" rx="4" fill="rgba(61,139,110,0.1)" stroke="#3D8B6E" stroke-width="1"/>
            <text x="55" y="59" text-anchor="middle" fill="#3D8B6E" font-size="10" font-family="Source Sans 3, sans-serif" font-weight="600">K/T-kvot</text>

            <rect x="0" y="76" width="110" height="26" rx="4" fill="rgba(196,163,90,0.1)" stroke="#C4A35A" stroke-width="1"/>
            <text x="55" y="93" text-anchor="middle" fill="#C4A35A" font-size="10" font-family="Source Sans 3, sans-serif" font-weight="600">Ränta &amp; Inflation</text>

            <!-- Arrows to center -->
            <line x1="115" y1="21" x2="210" y2="55" stroke="#C4A35A" stroke-width="1.5" marker-end="url(#arr)"/>
            <line x1="115" y1="55" x2="210" y2="55" stroke="#C4A35A" stroke-width="1.5" marker-end="url(#arr)"/>
            <line x1="115" y1="89" x2="210" y2="55" stroke="#C4A35A" stroke-width="1.5" marker-end="url(#arr)"/>

            <!-- SHAI box -->
            <rect x="215" y="32" width="130" height="46" rx="5" fill="#0B1F3F" stroke="#C4A35A" stroke-width="1.5"/>
            <text x="280" y="52" text-anchor="middle" fill="#FFFFFF" font-size="13" font-weight="bold" font-family="Source Sans 3, sans-serif">SHAI Index</text>
            <text x="280" y="68" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="9" font-family="IBM Plex Mono, monospace">A · B · C</text>

            <!-- Arrows to outputs -->
            <line x1="350" y1="42" x2="420" y2="21" stroke="#2E7D5B" stroke-width="1.5" marker-end="url(#arr-g)"/>
            <line x1="350" y1="55" x2="420" y2="55" stroke="#D4A03C" stroke-width="1.5" marker-end="url(#arr-y)"/>
            <line x1="350" y1="68" x2="420" y2="89" stroke="#B94A48" stroke-width="1.5" marker-end="url(#arr-r)"/>

            <!-- Risk class outputs -->
            <rect x="425" y="8" width="110" height="26" rx="4" fill="rgba(46,125,91,0.12)" stroke="#2E7D5B" stroke-width="1"/>
            <text x="480" y="25" text-anchor="middle" fill="#2E7D5B" font-size="10" font-weight="600" font-family="Source Sans 3, sans-serif">Låg risk</text>

            <rect x="425" y="42" width="110" height="26" rx="4" fill="rgba(212,160,60,0.12)" stroke="#D4A03C" stroke-width="1"/>
            <text x="480" y="59" text-anchor="middle" fill="#D4A03C" font-size="10" font-weight="600" font-family="Source Sans 3, sans-serif">Medel risk</text>

            <rect x="425" y="76" width="110" height="26" rx="4" fill="rgba(185,74,72,0.12)" stroke="#B94A48" stroke-width="1"/>
            <text x="480" y="93" text-anchor="middle" fill="#B94A48" font-size="10" font-weight="600" font-family="Source Sans 3, sans-serif">Hög risk</text>
        </svg>
    </div>
    """

    html = f"""
    <div class="lp-section">
        <div class="lp-section-title">Indexet i överblick</div>
        <div class="lp-card-light lp-visual">
            {bars_html}
            <div style="height:24px;"></div>
            {flow_svg}
        </div>
    </div>
    """
    st.markdown(_compact(html), unsafe_allow_html=True)


def render_landing_steps() -> None:
    """Render the 3-step pipeline explanation."""
    steps = [
        (
            "01",
            "Datainsamling",
            "SCB, Riksbanken och Kolada levererar kommunal inkomst, "
            "K/T-kvot, styrränta, inflation och arbetslöshet.",
        ),
        (
            "02",
            "Normalisering",
            "Värden z-standardiseras över hela panelen "
            "(2014\u20132024, 290 kommuner) för jämförbar ranking.",
        ),
        (
            "03",
            "Klassificering",
            "Tre formler (A, B, C) beräknas och kommuner klassas "
            "som låg, medel eller hög risk.",
        ),
    ]

    steps_html = ""
    for i, (num, title, text) in enumerate(steps):
        connector = ""
        if i < len(steps) - 1:
            connector = """
            <div class="lp-step-connector">
                <svg class="lp-step-arrow-svg" viewBox="0 0 40 24" aria-hidden="true">
                    <path d="M0 12h30l-6-6M30 12l-6 6" fill="none" stroke="#C4A35A" stroke-width="2"/>
                </svg>
            </div>
            """
        steps_html += f"""
        <div class="lp-step">
            <div class="lp-step-num">{num}</div>
            <div class="lp-step-title">{title}</div>
            <div class="lp-step-text">{text}</div>
        </div>
        {connector}
        """

    html = f"""
    <div class="lp-section">
        <div class="lp-section-title">Så fungerar det i korthet</div>
        <div class="lp-steps">{steps_html}</div>
    </div>
    """
    # st.markdown parses as Markdown; indented HTML is treated as code blocks and
    # the first step loses its tags (plain text inside .lp-steps). st.html is raw HTML.
    st.html(_compact(html))


def render_landing_nav_card(
    icon: str,
    title: str,
    desc: str,
    tag: str = "",
) -> str:
    """Return HTML for a landing navigation card."""
    tag_html = f'<span class="lp-nav-tag">{tag}</span>' if tag else ""
    return f"""
    <div class="lp-nav-card">
        <div class="lp-nav-card-head">
            <div class="lp-nav-icon">{icon}</div>
            {tag_html}
        </div>
        <div class="lp-nav-title">{title}</div>
        <div class="lp-nav-desc">{desc}</div>
    </div>
    """


def render_landing_credibility() -> None:
    """Render the credibility/data source block."""
    html = """
    <div class="lp-cred">
        <div class="lp-cred-pills">
            <span class="lp-cred-pill">SCB</span>
            <span class="lp-cred-pill">Riksbanken</span>
            <span class="lp-cred-pill">Kolada</span>
            <span class="lp-cred-pill">Finansinspektionen</span>
        </div>
        <div class="lp-cred-meta">
            SHAI v1.3 &middot; Öppen data &middot; 290 kommuner &middot; 2014&ndash;2024
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
