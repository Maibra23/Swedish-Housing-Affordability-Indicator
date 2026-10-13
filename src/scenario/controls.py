"""The four shock sliders on the Scenariosimulator page.

Select sliders rather than ``st.slider``: ``st.slider`` prints its value with a
printf format ("0.00"), so the one place a reader sets a number showed dot
decimals on a page that writes "0,77" everywhere else. The bounds are the
surface chart's, so the chart's axes and the controls cannot disagree.

Widget keys are unchanged: the preset buttons write to them.
"""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from src.scenario.charts import CPI_MAX, CPI_MIN, RATE_MAX, RATE_MIN
from src.ui.formatting import format_dec
from src.ui.labels import L


def shock_options(low: float, high: float, step: float, cast: type = float) -> list:
    """Every slider stop from `low` to `high` inclusive, rounded for display."""
    n = int(round((high - low) / step))
    return [cast(round(low + i * step, 2)) for i in range(n + 1)]


def _signed(decimals: int) -> Callable[[float], str]:
    return lambda v: format_dec(v, decimals, signed=v != 0)


def render_shock_sliders() -> tuple[float, int, int, float]:
    """Draw the sliders and return (rate pp, income %, price %, CPI pp)."""
    col_rate, col_income, col_price, col_cpi = st.columns(4)
    with col_rate:
        rate = st.select_slider(
            L("sc.rantechock_pp"),
            options=shock_options(RATE_MIN, RATE_MAX, 0.25),
            value=float(st.session_state.get("sc_rate_slider", 0.0)),
            format_func=_signed(2),
            key="sc_rate_slider",
            help=L("sc.4_pp_riksbankens_hojningscykel_20222023"),
        )
    with col_income:
        income = st.select_slider(
            L("sc.inkomsttillvaxt"),
            options=shock_options(-10, 10, 1, int),
            value=int(st.session_state.get("sc_income_slider", 0)),
            format_func=_signed(0),
            key="sc_income_slider",
            help=L("sc.34_ett_ars_normal_loneutveckling_i_sverige_5"),
        )
    with col_price:
        price = st.select_slider(
            "Prischock (%)",
            options=shock_options(-25, 25, 5, int),
            value=int(st.session_state.get("sc_price_slider", 0)),
            format_func=_signed(0),
            key="sc_price_slider",
            help=L("sc.prischock_hjalp"),
        )
    with col_cpi:
        cpi = st.select_slider(
            "KPI-chock (pp)",
            options=shock_options(CPI_MIN, CPI_MAX, 0.5),
            value=float(st.session_state.get("sc_cpi_slider", 0.0)),
            format_func=_signed(1),
            key="sc_cpi_slider",
            help=L("sc.8_pp_svensk_inflationstopp_2022_paverkar"),
        )
    return rate, income, price, cpi
