"""SHAI — Swedish Housing Affordability Indicator.

Entry point for the Streamlit multi-page dashboard.
Landing page with hero, stat strip, explanation, index visual, steps, nav cards, credibility.
"""

import streamlit as st

from src.ui.labels import L

st.set_page_config(
    page_title=L("landing.shai_bostadsekonomisk_hallbarhet"),
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": L("landing.shai_bostadsekonomisk_hallbarhet_data_scb"),
    },
)

from src.provenance import complete_case_max_year, first_year, n_kommuner
from src.ui.css import inject_css
from src.ui.sidebar import render_sidebar, APP_VERSION
from src.ui.components import footer_note
from src.ui.landing import (
    render_landing_hero,
    render_landing_stat_strip,
    render_landing_what_is_block,
    render_index_visual_block,
    render_landing_steps,
    render_landing_nav_card,
    render_landing_credibility,
)

inject_css()
selections = render_sidebar(page_key="main")

# ── Hero ──────────────────────────────────────────────────────────────
render_landing_hero()

# ── Stat strip (connected to hero) ───────────────────────────────────
# Panel dimensions come from the provenance artifact, so the strip cannot keep
# advertising a period the index no longer covers. See Finding H / T1.10.
N_KOMMUNER = n_kommuner()
PERIOD_START, PERIOD_END = first_year(), complete_case_max_year()
N_YEARS = PERIOD_END - PERIOD_START + 1

render_landing_stat_strip([
    {
        "label": "Analysperiod",
        "value": f"{PERIOD_START}–{PERIOD_END}",
        "unit": L("landing.v0_ar_v_v1", v0=N_YEARS, v1=APP_VERSION),
    },
    {"label": "Kommuner", "value": str(N_KOMMUNER), "unit": "analyserade"},
    {"label": L("landing.lan"), "value": "21", "unit": L("landing.jamforda")},
    {"label": "Formler", "value": "3", "unit": "ekonometriska versioner"},
])

# ── What is SHAI? ────────────────────────────────────────────────────
render_landing_what_is_block()

# ── Index overview (weights + flow SVG) ──────────────────────────────
render_index_visual_block()

# ── Pipeline steps ───────────────────────────────────────────────────
render_landing_steps()

# ── Navigation cards ─────────────────────────────────────────────────
st.markdown(L("landing.vad_hittar_du_har"), unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(render_landing_nav_card(
        L("landing.riksoversikt"),
        L("landing.nationell_overblick_med_karta_histogram_och", v0=N_KOMMUNER),
        tag="SIDA 01",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        L("landing.lan_jamforelse"),
        L("landing.21_lan_jamforda_under_tre_ekonometriska"),
        tag="SIDA 02",
    ), unsafe_allow_html=True)
with col2:
    st.markdown(render_landing_nav_card(
        "Kommun djupanalys",
        "Historisk analys och prognos per kommun med Prophet och ARIMA.",
        tag="SIDA 03",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "Kontantinsats",
        L("landing.jamfor_insatskrav_under_fem_regulatoriska"),
        tag="SIDA 04",
    ), unsafe_allow_html=True)
with col3:
    st.markdown(render_landing_nav_card(
        "Scenariosimulator",
        L("landing.stresstesta_med_ranta_inkomst_och"),
        tag="SIDA 05",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "Metodologi",
        L("landing.formler_datakallor_begransningar_f1f10_och"),
        tag="SIDA 06",
    ), unsafe_allow_html=True)

# ── Credibility block ────────────────────────────────────────────────
render_landing_credibility(version=APP_VERSION)

# ── Footer ───────────────────────────────────────────────────────────
footer_note()
