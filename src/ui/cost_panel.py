"""The rate-and-price history, as one collapsed panel three pages can open.

Version C is a cost share: `k · (P / I) · q`, with `q` the national cost per
krona borrowed. Its national mean therefore splits exactly into `q` and the mean
price-to-income ratio, and this panel shows both for every year, so a reader who
sees the index move can tell whether financing or prices moved it.

It replaced a panel about the rate *floor*. The old Version C divided by a real
rate floored at 0,5 pp, the floor bound in nine of eleven years, and the
national mean fell by a third in the year it released without affordability
changing. The cost share has no floor, so the panel now explains a level that
can be compared across years instead of warning against comparing it.

The figures are derived by `cost_history`, never typed, so a refresh moves the
page, METHODOLOGY section 3 and this panel together.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.indices.agreement import cost_history
from src.indices.cost_model import EARNERS, INTEREST_DEDUCTION, LOAN_TO_VALUE
from src.indices.decompose import decompose_change
from src.ui.data_table import Column, render_table
from src.ui.labels import L

_EARNER_WORDS = {1: "en", 2: "två", 3: "tre"}


def _sv(value: float, decimals: int = 2) -> str:
    """Swedish decimal comma, with a typographic minus."""
    text = f"{value:.{decimals}f}"
    if float(text) == 0:  # "-0,00" is rounding, not a negative value
        text = text.lstrip("-")
    return text.replace("-", "−").replace(".", ",")


def _pct(value: float, decimals: int = 1) -> str:
    """A signed percentage, so a reader sees the direction without parsing it."""
    sign = "+" if value > 0 else ""
    return sign + _sv(value, decimals) + " %"


def _change_for(history: pd.DataFrame, year: int | None):
    """The year-on-year split for the year on screen, when there is one.

    Returns None when the page shows no single year, when the preceding year is
    outside the panel, or when the split does not reconcile — a figure that does
    not add up is not shown with a caveat, it is not shown.
    """
    if year is None:
        return None
    change = decompose_change(history, int(year) - 1, int(year))
    return change if change is not None and change.is_exact else None


def render_cost_history(scored: pd.DataFrame, *, highlight_year: int | None = None) -> None:
    """Render the rate-and-price history inside a collapsed expander.

    Args:
        scored: A frame carrying `year`, both version columns, the inputs and
            `mortgage_rate` — the ranked or municipal artifact.
        highlight_year: Year to name in the caption, so a reader knows which row
            is the one the page is currently showing. Omitted when the page has
            no single year on display.
    """
    history = cost_history(scored)
    if history.empty:
        return

    with st.expander(L("kp.rubrik")):
        st.markdown(
            L(
                "kp.inledning",
                v0=_sv(LOAN_TO_VALUE * 100, 0),
                v1=_EARNER_WORDS.get(EARNERS, str(EARNERS)),
                v2=_sv(INTEREST_DEDUCTION * 100, 0),
            )
        )
        st.markdown(
            render_table(
                history,
                [
                    Column(L("kp.ar"), lambda row: str(int(row["year"])), kind="name"),
                    Column(L("kp.bolaneranta"), lambda row: _sv(row["mortgage_rate"]), numeric=True),
                    Column(L("kp.amortering"), lambda row: _sv(row["amortisation_pct"]), numeric=True),
                    Column(L("kp.kostnad_per_krona"), lambda row: _sv(row["cost_rate"]), numeric=True),
                    Column(L("kp.faktor"), lambda row: _sv(row["factor"]) + "×", numeric=True),
                    Column(L("kp.snittindex"), lambda row: _sv(row["mean_index"], 1) + " %", numeric=True),
                    Column(L("kp.pris_inkomst"), lambda row: _sv(row["price_to_income"], 1), numeric=True),
                ],
            ),
            unsafe_allow_html=True,
        )
        if highlight_year is not None:
            st.caption(L("kp.vald_rad", v0=str(highlight_year)))

        first, last = history.iloc[0], history.iloc[-1]
        over_period = decompose_change(history, int(first["year"]), int(last["year"]))
        st.markdown(
            L(
                "kp.svaret",
                v0=_sv(float(first["price_to_income"]), 1),
                v1=_sv(float(last["price_to_income"]), 1),
                v2=str(int(first["year"])),
                v3=str(int(last["year"])),
                v4=_pct(over_period.price_to_income_pct) if over_period else "",
            )
        )

        # The split for the year on screen against the one before it, which is
        # the comparison a reader is most likely to be making.
        change = _change_for(history, highlight_year)
        if change is not None:
            st.markdown(
                L(
                    "kp.uppdelning",
                    v0=str(change.from_year),
                    v1=str(change.to_year),
                    v2=_pct(change.total_pct),
                    v3=_pct(change.rate_pct),
                    v4=_pct(change.price_to_income_pct),
                )
            )

        st.markdown(L("kp.slutsats"))
        st.caption(L("kp.forbehall"))
