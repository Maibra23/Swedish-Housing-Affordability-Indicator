"""The three shock sliders on the Scenariosimulator page.

Select sliders rather than ``st.slider``: ``st.slider`` prints its value with a
printf format ("0.00"), so the one place a reader sets a number showed dot
decimals on a page that writes "0,77" everywhere else. The bounds are the
surface chart's, so the chart's axes and the controls cannot disagree.

Widget keys are unchanged: the preset buttons write to them.
"""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from src.scenario.charts import PRICE_MAX, PRICE_MIN, PRICE_STEP, RATE_MAX, RATE_MIN
from src.ui.formatting import format_dec
from src.ui.labels import L


def shock_options(low: float, high: float, step: float, cast: type = float) -> list:
    """Every slider stop from `low` to `high` inclusive, rounded for display."""
    n = int(round((high - low) / step))
    return [cast(round(low + i * step, 2)) for i in range(n + 1)]


def _signed(decimals: int) -> Callable[[float], str]:
    return lambda v: format_dec(v, decimals, signed=v != 0)


def _initial(key: str, default) -> dict:
    """`value=` only for a slider the session has not set yet.

    A preset writes straight to the widget's session-state key. Passing a
    default as well makes Streamlit warn on screen that the widget "was created
    with a default value but also had its value set via the Session State API",
    so the default is given only the first time.
    """
    return {} if key in st.session_state else {"value": default}


def render_shock_sliders() -> tuple[float, int, int]:
    """Draw the sliders and return (mortgage rate pp, income %, price %).

    There is no inflation slider. Version C is a cash-flow share in kronor of
    the same year, so inflation does not enter it; it reaches the result only
    through what it does to income, prices and the rate, which the three
    sliders already set.
    """
    col_rate, col_income, col_price = st.columns(3)
    with col_rate:
        rate = st.select_slider(
            L("sc.rantechock_pp"),
            options=shock_options(RATE_MIN, RATE_MAX, 0.25),
            **_initial("sc_rate_slider", 0.0),
            format_func=_signed(2),
            key="sc_rate_slider",
            help=L("sc.rantechock_hjalp"),
        )
    with col_income:
        income = st.select_slider(
            L("sc.inkomsttillvaxt"),
            options=shock_options(-10, 10, 1, int),
            **_initial("sc_income_slider", 0),
            format_func=_signed(0),
            key="sc_income_slider",
            help=L("sc.34_ett_ars_normal_loneutveckling_i_sverige_5"),
        )
    with col_price:
        price = st.select_slider(
            L("sc.prischock_pct"),
            options=shock_options(PRICE_MIN, PRICE_MAX, PRICE_STEP, int),
            **_initial("sc_price_slider", 0),
            format_func=_signed(0),
            key="sc_price_slider",
            help=L("sc.prischock_hjalp"),
        )
    return rate, income, price
