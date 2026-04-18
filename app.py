"""SHAI — Swedish Housing Affordability Indicator.

Entry point for the Streamlit multi-page dashboard.
Landing page with hero, stat strip, explanation, index visual, steps, nav cards, credibility.
"""

import streamlit as st

st.set_page_config(
    page_title="SHAI — Bostadsekonomisk hållbarhet",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "SHAI — Bostadsekonomisk hållbarhet. Data: SCB, Riksbanken, Kolada.",
    },
)

from src.ui.css import inject_css
from src.ui.sidebar import render_sidebar, APP_VERSION
from src.ui.components import (
    render_landing_hero,
    render_landing_stat_strip,
    render_landing_what_is_block,
    render_index_visual_block,
    render_landing_steps,
    render_landing_nav_card,
    render_landing_credibility,
    footer_note,
)

inject_css()
selections = render_sidebar(page_key="main")

# ── Hero ──────────────────────────────────────────────────────────────
render_landing_hero()

# ── Stat strip (connected to hero) ───────────────────────────────────
render_landing_stat_strip([
    {"label": "Analysperiod", "value": "2014–2024", "unit": f"11 år  ·  v{APP_VERSION}"},
    {"label": "Kommuner", "value": "290", "unit": "analyserade"},
    {"label": "Län", "value": "21", "unit": "jämförda"},
    {"label": "Formler", "value": "3", "unit": "ekonometriska versioner"},
])

# ── What is SHAI? ────────────────────────────────────────────────────
render_landing_what_is_block()

# ── Index overview (weights + flow SVG) ──────────────────────────────
render_index_visual_block()

# ── Pipeline steps ───────────────────────────────────────────────────
render_landing_steps()

# ── Navigation cards ─────────────────────────────────────────────────
st.markdown("""
<div class="lp-section">
    <div class="lp-section-title">Vad hittar du här?</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(render_landing_nav_card(
        "🗺️", "Riksöversikt",
        "Nationell överblick med karta, histogram och rankingtabeller för 290 kommuner.",
        tag="SIDA 01",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "📊", "Län jämförelse",
        "21 län jämförda under tre ekonometriska formler (A, B, C).",
        tag="SIDA 02",
    ), unsafe_allow_html=True)
with col2:
    st.markdown(render_landing_nav_card(
        "🔍", "Kommun djupanalys",
        "Historisk analys och prognos per kommun med Prophet och ARIMA.",
        tag="SIDA 03",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "💰", "Kontantinsats",
        "Jämför insatskrav under fyra regulatoriska regimer sedan 2010.",
        tag="SIDA 04",
    ), unsafe_allow_html=True)
with col3:
    st.markdown(render_landing_nav_card(
        "⚡", "Scenariosimulator",
        "Stresstesta med ränta-, inkomst- och prisförändringar per län.",
        tag="SIDA 05",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "📖", "Metodologi",
        "Formler, datakällor, begränsningar (F1–F10) och validering.",
        tag="SIDA 06",
    ), unsafe_allow_html=True)

# ── Credibility block ────────────────────────────────────────────────
render_landing_credibility()

# ── Footer ───────────────────────────────────────────────────────────
footer_note()
