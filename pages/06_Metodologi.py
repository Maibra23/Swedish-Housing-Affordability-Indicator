"""Sida 06 — Metodologi och källor.

What the index measures, its sources, formulas and normalisation (sections
1–4, always visible), then projection, regulation, limitations F1–F17,
validation and references (sections 5–9, in expanders).
"""

import streamlit as st

from src.ui.labels import L
from src.ui.templates import T

st.set_page_config(
    page_title="SHAI · Metodologi",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None},
)

from src.provenance import (
    complete_case_max_year,
    first_year,
    n_kommuner,
    source_coverage,
)
from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar, APP_VERSION
from src.ui.components import card_header, footer_note, page_title, vintage_badge
from src.ui.data import load as load_artifact
from src.ui.floor_panel import render_floor_history

inject_css()
selections = render_sidebar()

# Period and panel size come from the provenance artifact: a literal
# "2014–2024" keeps asserting itself after the panel has moved on. See T1.10.
PERIOD_START, PERIOD_END = first_year(), complete_case_max_year()
PERIOD = f"{PERIOD_START}–{PERIOD_END}"
N_YEARS = PERIOD_END - PERIOD_START + 1
N_KOMMUNER = n_kommuner()

# The source table states, per variable, how far upstream publication reaches.
# Those years are recorded in the provenance artifact, so the table reads them
# rather than restating them: the T2.4 refresh advanced four series to 2025 while
# the prose still said 2024, and nothing noticed until T4.1 compared the two.
_COVERAGE = source_coverage()


def _max_year(column: str) -> int:
    """Last observed year for `column`, as the artifact records it."""
    return _COVERAGE[column]["max_year"]


SOURCE_MAX = {
    "income_max": _max_year("median_income"),
    "price_max": _max_year("transaction_price_sek"),
    "price_index_max": _max_year("price_index"),
    "kt_max": _max_year("kt_ratio"),
    "unemployment_max": _max_year("unemployment_rate"),
    "population_max": _max_year("population"),
    "completions_max": _max_year("completions"),
}

page_title(
    eyebrow="Sida 06 · Metodologi",
    title=L("mt.metodologi_och_kallor"),
    subtitle=L("mt.teoretisk_grund_formler_datakallor_och"),
    year=PERIOD,
)

# ══════════════════════════════════════════════════════════════════════
# SECTION 1 — Teoretisk grund (always visible)
# ══════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown(
        card_header(L("mt.1_vad_shai_mater"), L("mt.tre_perspektiv_pa_bostadsoverkomlighet"), "TEORI"),
        unsafe_allow_html=True,
    )

    st.markdown(L("mt.bostadsoverkomlighet_housing_affordability"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 2 — Variabler och datakällor (always visible)
# ══════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header(L("mt.2_variabler_och_datakallor"), L("mt.10_variabler_fran_officiella_svenska_kallor"), "DATA"),
        unsafe_allow_html=True,
    )

    st.markdown(L("mt.variabel_symbol_kalla_upplosning_frekvens", **SOURCE_MAX))

# ══════════════════════════════════════════════════════════════════════
# SECTION 3 — Formler (always visible)
# ══════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header(L("mt.3_formler"), L("mt.tre_satt_att_mata"), "FORMLER"),
        unsafe_allow_html=True,
    )

    st.markdown(L("mt.beteckningar"))

    st.markdown(L("mt.version_a_rubrik"))
    st.latex(r"A(i,t) = \frac{I(i,t)}{P(i,t) \times \max(R(t),\; 0{,}001)}")
    st.markdown(L("mt.mater_flodesoverkomlighet_hushallets_inkomst"))

    st.markdown(L("mt.version_b_makrokomposit_tryckmatt"))
    st.latex(r"B(i,t) = 0{,}35 \cdot z\!\left(\frac{P}{I}\right) + 0{,}25 \cdot z(R) + 0{,}20 \cdot z(U) + 0{,}20 \cdot z(\pi)")
    st.markdown(L("mt.sammansatt_riskindikator_som_viktar_pris"))

    st.markdown(L("mt.version_c_rubrik"))
    st.latex(r"C(i,t) = \frac{I(i,t)}{P(i,t) \times \max(R(t) - \pi(t),\; 0{,}005)}")
    st.markdown(L("mt.justerar_for_inflation_genom_realrantan"))

    # F17, with the data rather than a description of it. A documentation page
    # must not die for a missing artifact, so the panel is skipped with a reason
    # rather than allowed to raise through the rest of the methodology.
    try:
        render_floor_history(load_artifact("affordability_ranked.parquet"))
    except Exception as exc:  # noqa: BLE001 — reported, not swallowed
        st.caption(L("mt.rantegolvspanelen_kunde_inte_laddas", v0=str(exc)))

# ══════════════════════════════════════════════════════════════════════
# SECTION 4 — Från värde till riskklass (always visible)
# ══════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header(L("mt.4_fran_varde_till_riskklass"), L("mt.normalisering_rang_och_riskklass"), "NORMALISERING"),
        unsafe_allow_html=True,
    )
    st.markdown(L("mt.formlerna_ger_ett_nivavarde_per_kommun_och"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 5 — Projektion (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander(L("mt.expander_4_projektion_villkorad")):
    st.markdown(L("mt.projektion_tre_scenarier_realranta", v0=N_YEARS, v1=PERIOD))

# ══════════════════════════════════════════════════════════════════════
# SECTION 6 — Kontantinsats (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander(L("mt.expander_5_kontantinsats_regimhistorik")):
    # Timeline visual
    st.markdown(T("mt.fore_2010_inget_formellt_krav_okt_2010", v0=COLORS['border'], v1=COLORS['text_tertiary'], v2=COLORS['text_secondary'], v3=COLORS['accent'], v4=COLORS['text_secondary'], v5=COLORS['medium_risk'], v6=COLORS['text_secondary'], v7=COLORS['high_risk'], v8=COLORS['text_secondary'], v9=COLORS['low_risk'], v10=COLORS['accent'], v11=COLORS['text_secondary']), unsafe_allow_html=True)

    st.markdown(L("mt.regelverk_period_kontantinsats"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 7 — Begränsningar F1–F17 (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander(L("mt.6_begransningar_f1f15")):
    st.markdown(L("mt.id_begransning_atgard_f1_kommunal", v0=N_YEARS))

# ══════════════════════════════════════════════════════════════════════
# SECTION 8 — Datavalidering (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander(L("mt.expander_7_datavalidering")):
    st.markdown(L("mt.foljande_valideringskontroller_kors_innan"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 9 — Referenser (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander(L("mt.expander_8_referenser")):
    st.markdown(L("mt.scb_bo0501_fastighetspriser_och_lagfarter"))

vintage_badge()
footer_note(
    source=L("mt.kalla_sidfot"),
    version=L("mt.shai_v_v0_metodologi_baserad_pa_methodology", v0=APP_VERSION),
)
