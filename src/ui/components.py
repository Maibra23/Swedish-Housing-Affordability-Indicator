"""Reusable UI components for SHAI dashboard.

All components return HTML strings for use with st.markdown(unsafe_allow_html=True).
Design tokens match the KRI design system exactly.
"""

from __future__ import annotations

import re
import streamlit as st

from src.provenance import complete_case_max_year, first_year, n_kommuner
from src.provenance import generated_at
from src.ui.labels import L
from src.ui.tokens import COLORS


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


def format_sek_compact(value: float) -> str:
    """Format a SEK value short: "Mkr" from 1 000 000, "tkr" from 10 000.

    For places where the grouped form ("2 041 350 SEK") is wider than its
    container, such as the five-across regime cards on sida 04. The CSS lets a
    long value wrap rather than clip; this keeps it from needing to.
    """
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"{value / 1_000_000:.2f}".replace(".", ",") + " Mkr"
    if magnitude >= 10_000:
        return f"{value / 1_000:.0f}".replace(".", ",") + " tkr"
    return format_sek(value) + " SEK"


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
    updated: str | None = None,
) -> None:
    """Render the standard page footer.

    Args:
        source: Attribution line.
        version: App version.
        updated: ISO timestamp of the data build. Defaults to the provenance
            artifact; pass a value only to override it in a test.
    """
    stamp = (updated or generated_at())[:10]
    html = f"""
    <div class="shai-footer-note">
        <span><strong>KÄLLA:</strong> {source}</span>
        <span>{L("ui.data_uppdaterad_v0", v0=stamp)}</span>
        <span><code>{version}</code></span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Explanation, glossary and vintage ─────────────────────────────────


def explanation(text: str) -> None:
    """Render a prose line explaining the numbers directly above it.

    A dashboard's default failure is a confident number with no statement of what
    it means or what it cannot show. Every KPI row, chart and stat strip in this
    app now carries one of these. See T3.4.

    Args:
        text: The explanation, from `SWEDISH_LABELS`. Interpolate any figure it
            quotes from the data — a number typed into an explanation is the
            defect T4.1 exists to catch, one layer down.
    """
    st.markdown(f'<div class="shai-explanation">{text}</div>', unsafe_allow_html=True)


def purpose_panel(
    heading: str, paragraphs: list[str], when_label: str, when: list[str]
) -> str:
    """Return the "what this page is for" block that opens an analysis page.

    Sida 04 and Sida 05 are the two pages that are *tools* rather than views:
    the reader supplies inputs and the page answers a question. Both opened on a
    subtitle describing their contents ("Historiska och nuvarande regelverk och
    insatskrav") followed immediately by a provenance caveat about which SCB
    table is published at which geographic level. That is methodology arriving
    before purpose, and it leaves a reader who does not already know what the
    page is for with no way to find out.

    The material already existed, in `docs/ANALYSIS_GUIDE.md` sections 1 and 2
    under "Why it exists" and "When to use it". It had simply never reached the
    page it describes.

    Args:
        heading: Card title, phrased as what the page answers.
        paragraphs: Plain sentences. The component adds the markup, so the copy
            itself stays tag-free and therefore stays in `SWEDISH_LABELS` rather
            than in `TEMPLATES` — see R9.
        when_label: Heading for the list of situations.
        when: Situations in which the page is the right tool.

    Returns:
        HTML for a `.shai-card`, to be rendered inside a bordered container.
    """
    body = "".join(f"<p>{para}</p>" for para in paragraphs)
    items = "".join(f"<li>{item}</li>" for item in when)
    return _compact(f"""
    <div class="shai-purpose">
        <div class="shai-card-title">{heading}</div>
        <div class="shai-purpose-body">{body}</div>
        <div class="shai-purpose-when-label">{when_label}</div>
        <ul class="shai-purpose-when">{items}</ul>
    </div>
    """)


def help_badge(*terms: str) -> str:
    """Return a "?" affordance revealing definitions for `terms`.

    Replaces bare `title=` tooltips, which are invisible to keyboard users and to
    anyone on a touch screen. The popover is plain markup: it needs no JavaScript,
    opens on focus as well as hover, and carries an aria-label so a screen reader
    announces it as a definition list rather than a stray question mark.

    Args:
        terms: Glossary keys, each `SWEDISH_LABELS["glossary.<term>"]`.

    Returns:
        HTML for inclusion in a card header.

    Raises:
        KeyError: If a term has no glossary entry — loudly, because a silent miss
            renders a "?" that explains nothing.
    """
    if not terms:
        return ""
    items = "".join(
        f"<dt>{L(f'glossary.{term}.term')}</dt><dd>{L(f'glossary.{term}.def')}</dd>"
        for term in terms
    )
    label = L("ui.forklaring_av_begrepp")
    return (
        '<span class="shai-help">'
        f'<button class="shai-help-mark" type="button" aria-label="{label}">?</button>'
        f'<span class="shai-help-pop" role="note"><dl>{items}</dl></span>'
        "</span>"
    )


def vintage_badge(updated: str | None = None) -> None:
    """Render the data vintage as a visible badge.

    Finding C was the app claiming freshness from `date.today()`. T1.5 fixed the
    source; this makes the answer visible rather than a sidebar footnote, so a
    reader knows how old the numbers are without going looking.

    Args:
        updated: ISO timestamp. Defaults to the provenance artifact's
            `generated_at` — when the *data* was built, never when the page ran.
    """
    stamp = (updated or generated_at())[:10]
    st.markdown(
        f'<div class="shai-vintage"><span class="shai-vintage-dot"></span>'
        f'{L("ui.data_uppdaterad_v0", v0=stamp)}</div>',
        unsafe_allow_html=True,
    )
