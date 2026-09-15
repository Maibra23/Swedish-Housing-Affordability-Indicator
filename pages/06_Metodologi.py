"""Sida 06 — Metodologi och källor.

Formler, datakällor, begränsningar (F1–F10) och validering.
Sections 1–3 always visible, 4–8 in expanders.
"""

import streamlit as st

from src.ui.labels import L

st.set_page_config(
    page_title="SHAI · Metodologi",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None},
)

from src.provenance import complete_case_max_year, first_year, n_kommuner
from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar, APP_VERSION
from src.ui.components import page_title, card_header, footer_note

inject_css()
selections = render_sidebar(page_key="mt")

# Period and panel size come from the provenance artifact: a literal
# "2014–2024" keeps asserting itself after the panel has moved on. See T1.10.
PERIOD_START, PERIOD_END = first_year(), complete_case_max_year()
PERIOD = f"{PERIOD_START}–{PERIOD_END}"
N_YEARS = PERIOD_END - PERIOD_START + 1
N_KOMMUNER = n_kommuner()

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
        card_header("1. Teoretisk grund", L("mt.tre_perspektiv_pa_bostadsoverkomlighet"), "TEORI"),
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

    st.markdown(L("mt.variabel_symbol_kalla_upplosning_frekvens"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 3 — Formler (always visible)
# ══════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header("3. Formler", "Tre ekonometriska formler", "FORMLER"),
        unsafe_allow_html=True,
    )

    st.markdown("### Version A: Bankmodell (affordability ratio)")
    st.latex(r"\text{Affordability}_A(i,t) = \frac{I(i,t)}{P_{\text{SEK}}(i,t) \times R(t)}")
    st.markdown(L("mt.mater_flodesoverkomlighet_hushallets_inkomst"))

    st.markdown(L("mt.version_b_makrokomposit_tryckmatt"))
    st.latex(r"\text{Risk}_B(i,t) = 0{,}35 \cdot z\!\left(\frac{P_{\text{SEK}}}{I}\right) + 0{,}25 \cdot z(R) + 0{,}20 \cdot z(U) + 0{,}20 \cdot z(\pi)")
    st.markdown(L("mt.sammansatt_riskindikator_som_viktar_pris"))

    st.markdown("### Version C: Realversion (rekommenderad)")
    st.latex(r"\text{Affordability}_C(i,t) = \frac{I(i,t)}{P_{\text{SEK}}(i,t) \times \max(R(t) - \pi(t),\; 0{,}005)}")
    st.markdown(L("mt.justerar_for_inflation_genom_realrantan"))

    st.markdown("### Normalisering, rangordning och riskklass")
    st.markdown(L("mt.formlerna_ger_ett_nivavarde_per_kommun_och", v0=N_KOMMUNER))

    st.markdown(L("mt.varfor_transaktionspris_i_sek_inte_k_t_eller"))
    st.markdown(L("mt.tre_alternativa_prismatt_overvagdes"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 4 — Prognoser (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("4. Prognoser (Prophet vs ARIMA)"):
    st.markdown(L("mt.prophet_standard_i_granssnittet_bibliotek", v0=N_YEARS, v1=PERIOD))

# ══════════════════════════════════════════════════════════════════════
# SECTION 5 — Kontantinsats (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("5. Kontantinsats — regimhistorik"):
    st.markdown("Fem regulatoriska regimer modelleras:")

    # Timeline visual
    st.markdown(L("mt.fore_2010_inget_formellt_krav_okt_2010", v0=COLORS['border'], v1=COLORS['text_tertiary'], v2=COLORS['text_secondary'], v3=COLORS['accent'], v4=COLORS['text_secondary'], v5=COLORS['medium_risk'], v6=COLORS['text_secondary'], v7=COLORS['high_risk'], v8=COLORS['text_secondary'], v9=COLORS['low_risk'], v10=COLORS['accent'], v11=COLORS['text_secondary']), unsafe_allow_html=True)

    st.markdown(L("mt.regelverk_period_kontantinsats"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 6 — Begränsningar F1–F10 (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander(L("mt.6_begransningar_f1f15")):
    st.markdown(L("mt.id_begransning_atgard_f1_kommunal"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 7 — Datavalidering (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("7. Datavalidering"):
    st.markdown(L("mt.foljande_valideringskontroller_kors_innan"))

# ══════════════════════════════════════════════════════════════════════
# SECTION 8 — Referenser (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("8. Referenser"):
    st.markdown(L("mt.scb_bo0501_fastighetspriser_och_lagfarter"))

footer_note(version=L("mt.shai_v_v0_metodologi_baserad_pa_methodology", v0=APP_VERSION))
