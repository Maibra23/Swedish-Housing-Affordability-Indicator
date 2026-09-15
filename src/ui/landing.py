"""Components used only by the landing page.

Split out of `components.py` by T3.10 (Finding K). `components.py` now holds what
more than one page uses — the KPI card, the generic card, the risk pill, the
formatters — and this module holds the hero, stat strip, explanation block, index
visual, pipeline steps, nav cards and credibility strip, all of which appear once,
on `app.py`.

The split is not only about line count. The landing page is the part of this app
most likely to be restyled, and having its markup in the same file as the KPI card
meant every landing tweak sat in a diff beside the component every data page
renders. Its stylesheet is separated for the same reason — see `css_landing.py`.

Panel facts (municipality count, index period) are resolved per call from the
provenance artifact via `_panel_facts`, never written into the copy: see T1.10.
"""

from __future__ import annotations

import streamlit as st

from src.ui.components import _compact, _panel_facts
from src.ui.labels import L
from src.ui.tokens import COLORS


def render_landing_hero(kommun_count: int | None = None) -> None:
    """Render the KRI-style landing hero section.

    Args:
        kommun_count: Municipality count. Defaults to the provenance artifact.
    """
    kommuner, _, _ = _panel_facts(kommun_count)
    html = f"""
    <div class="shai-hero">
        <div class="shai-hero-inner">
            <div class="shai-hero-eyebrow">Bostadsekonomisk hållbarhetsanalys</div>
            <h1 class="shai-headline">Swedish Housing<br>Affordability Indicator</h1>
            <p class="shai-hero-lead">
                Strukturell bostadsekonomisk hållbarhet i Sveriges {kommuner} kommuner
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
        <div class="shai-stat-cell">
            <div class="shai-stat-label">{s['label']}</div>
            <div class="shai-stat-value">{s['value']}</div>
            <div class="shai-stat-unit">{s.get('unit', '')}</div>
        </div>
        """
    html = f'<div class="shai-stat-strip">{cells}</div>'
    st.markdown(_compact(html), unsafe_allow_html=True)


def render_landing_what_is_block(kommun_count: int | None = None) -> None:
    """Render the 'Vad ar SHAI?' explanation block.

    Args:
        kommun_count: Municipality count. Defaults to the provenance artifact.
    """
    kommuner, _, _ = _panel_facts(kommun_count)
    html = f"""
    <div class="shai-section">
        <div class="shai-section-title">Vad är SHAI?</div>
        <div class="shai-card-light">
            <div class="shai-body">
                SHAI (Swedish Housing Affordability Indicator) mäter strukturell
                bostadsekonomisk hållbarhet genom tre ekonometriska formler som
                kombinerar inkomst, bostadspriser, räntor och inflation.
            </div>
            <div class="shai-body-secondary">
                Indikatorn analyserar Sveriges {kommuner} kommuner och 21 län med data
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
        <div class="shai-weight-row">
            <span class="shai-weight-name">{name}</span>
            <div class="shai-weight-bar-wrap">
                <div class="shai-weight-bar" style="width:{pct}%;background:{color};"></div>
            </div>
            <span class="shai-weight-pct">{pct}%</span>
        </div>
        """

    flow_svg = """
    <div class="shai-flow-svg-wrap">
        <svg viewBox="0 0 580 130" class="shai-flow-svg" aria-hidden="true">
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
    <div class="shai-section">
        <div class="shai-section-title">Indexet i överblick</div>
        <div class="shai-card-light">
            {bars_html}
            <div style="height:24px;"></div>
            {flow_svg}
        </div>
    </div>
    """
    st.markdown(_compact(html), unsafe_allow_html=True)


def render_landing_steps(
    kommun_count: int | None = None,
    period_start: int | None = None,
    period_end: int | None = None,
) -> None:
    """Render the 3-step pipeline explanation.

    Args:
        kommun_count: Municipality count. Defaults to the provenance artifact.
        period_start: First year of the index. Defaults to provenance.
        period_end: Last year of the index. Defaults to provenance.
    """
    kommuner, start, end = _panel_facts(kommun_count, period_start, period_end)
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
            f"Värden z-standardiseras inom varje år "
            f"({start}–{end}, {kommuner} kommuner) för jämförbar ranking.",
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
            <div class="shai-step-connector">
                <svg class="shai-step-arrow-svg" viewBox="0 0 40 24" aria-hidden="true">
                    <path d="M0 12h30l-6-6M30 12l-6 6" fill="none" stroke="#C4A35A" stroke-width="2"/>
                </svg>
            </div>
            """
        steps_html += f"""
        <div class="shai-step">
            <div class="shai-step-num">{num}</div>
            <div class="shai-step-title">{title}</div>
            <div class="shai-step-text">{text}</div>
        </div>
        {connector}
        """

    html = f"""
    <div class="shai-section">
        <div class="shai-section-title">Så fungerar det i korthet</div>
        <div class="shai-steps">{steps_html}</div>
    </div>
    """
    # st.markdown parses as Markdown; indented HTML is treated as code blocks and
    # the first step loses its tags (plain text inside .shai-steps). st.html is raw HTML.
    st.html(_compact(html))


def render_landing_nav_card(
    title: str,
    desc: str,
    tag: str = "",
) -> str:
    """Return HTML for a landing navigation card."""
    tag_html = f'<span class="shai-nav-tag">{tag}</span>' if tag else ""
    return f"""
    <div class="shai-nav-card">
        <div class="shai-nav-card-head">
            {tag_html}
        </div>
        <div class="shai-nav-title">{title}</div>
        <div class="shai-nav-desc">{desc}</div>
    </div>
    """


def render_landing_credibility(
    version: str = "",
    kommun_count: int | None = None,
    period_start: int | None = None,
    period_end: int | None = None,
) -> None:
    """Render the credibility/data source block.

    Args:
        version: App version string. Omitted when empty.
        kommun_count: Municipality count. Defaults to the provenance artifact.
        period_start: First year of the index. Defaults to provenance.
        period_end: Last year of the index. Defaults to provenance.
    """
    kommuner, start, end = _panel_facts(kommun_count, period_start, period_end)
    version_str = f"SHAI v{version} &middot; " if version else ""
    html = f"""
    <div class="shai-cred">
        <div class="shai-cred-pills">
            <span class="shai-cred-pill">SCB</span>
            <span class="shai-cred-pill">Riksbanken</span>
            <span class="shai-cred-pill">Kolada</span>
            <span class="shai-cred-pill">Finansinspektionen</span>
        </div>
        <div class="shai-cred-meta">
            {version_str}Öppen data &middot; {kommuner} kommuner &middot; {start}&ndash;{end}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
