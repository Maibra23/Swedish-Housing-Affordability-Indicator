"""The bank-margin control in Sida 04's advanced settings."""

from __future__ import annotations

import streamlit as st

from src.kontantinsats.margin import (
    FALLBACK_PP,
    SLIDER_MAX,
    SLIDER_MIN,
    SLIDER_STEP,
    default_margin_pp,
    is_observed,
)
from src.ui.formatting import format_dec
from src.ui.labels import L

KEY = "ki_bank_margin_slider"
_YEAR_KEY = "ki_bank_margin_year"


def render_margin_control(year: int) -> float:
    """Draw the expander and return the margin in percentage points.

    The slider starts at the margin SCB observed in `year` and resets when the
    year changes; within a year it keeps whatever the reader set. A fixed 1,7 pp
    overstated 2024's mortgage rate by almost a point (see margin.py).
    """
    if st.session_state.get(_YEAR_KEY) != year:
        st.session_state[KEY] = default_margin_pp(year)
        st.session_state[_YEAR_KEY] = year
    with st.expander(L("ki.avancerade_installningar_rantepaslag")):
        st.caption(L("ki.riksbankens_styrranta_anvands_som_bas"))
        value = st.slider(
            L("ki.bankens_rantepaslag_pp_ovan_styrrantan"),
            min_value=SLIDER_MIN,
            max_value=SLIDER_MAX,
            step=SLIDER_STEP,
            key=KEY,
            help=L("ki.faktisk_bolaneranta_styrranta_rantepaslag_0"),
        )
        st.caption(
            L("ki.paslag_forval_v0_v1", v0=format_dec(default_margin_pp(year)), v1=year)
            if is_observed(year)
            else L("ki.paslag_forval_saknas_v0", v0=format_dec(FALLBACK_PP))
        )
    return value
