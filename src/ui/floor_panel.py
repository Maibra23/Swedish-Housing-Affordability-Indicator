"""The rate-floor history, as one collapsed panel three pages can open.

Two statements the app makes are only safe to read beside this table.

Sida 01 tells a reader to judge whether Sweden became more or less affordable
from the mean index, because it is a level series. Sida 02 says the county
curves can be compared across years for the same reason. Both are true about the
*arithmetic* and misleading about the *panel*: Version C divides by a real rate
floored at 0,5 pp, that floor bound in nine of the eleven observed years, and it
released in 2024. The national mean fell from 36,3 to 23,0 between 2023 and
2024 — a 36 % drop that is the floor letting go, not affordability collapsing by
a third.

So the claim is qualified where it is made, and the evidence sits one click away
rather than in a paragraph nobody reads. The panel is collapsed by default and
renders the same derived table on every page that opens it: whether each
formula was dividing by the market or by its floor, what the A-to-C factor came
to, and the level that produced.

The figures are derived by `floor_history`, never typed, so a refresh moves the
page, METHODOLOGY section 3 and this panel together. See F17.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.indices.agreement import (
    NOMINAL_RATE_FLOOR_PP,
    REAL_RATE_FLOOR_PP,
    floor_history,
)
from src.ui.data_table import Column, render_table
from src.ui.labels import L


def _sv(value: float, decimals: int = 2) -> str:
    """Swedish decimal comma, with a typographic minus."""
    return f"{value:.{decimals}f}".replace("-", "−").replace(".", ",")


def _which_floor(row: pd.Series) -> str:
    """Name the formulas that were dividing by a floor, not by a rate."""
    if row["nominal_floored"] and row["real_floored"]:
        return L("fl.golv_a_och_c")
    if row["real_floored"]:
        return L("fl.golv_c")
    if row["nominal_floored"]:
        return L("fl.golv_a")
    return L("fl.golv_inget")


def render_floor_history(scored: pd.DataFrame, *, highlight_year: int | None = None) -> None:
    """Render the floor history inside a collapsed expander.

    Args:
        scored: A frame carrying `year`, both version columns and the rates —
            the ranked or municipal artifact.
        highlight_year: Year to name in the caption, so a reader knows which row
            is the one the page is currently showing. Omitted when the page has
            no single year on display.
    """
    history = floor_history(scored)
    if history.empty:
        return

    with st.expander(L("fl.rubrik")):
        st.markdown(
            L(
                "fl.inledning",
                v0=_sv(REAL_RATE_FLOOR_PP, 1),
                v1=_sv(NOMINAL_RATE_FLOOR_PP, 1),
                v2=str(int(history["real_floored"].sum())),
                v3=str(len(history)),
            )
        )
        st.markdown(
            render_table(
                history,
                [
                    Column(L("fl.ar"), lambda row: str(int(row["year"])), kind="name"),
                    Column(L("fl.styrranta"), lambda row: _sv(row["policy_rate"]), numeric=True),
                    Column(L("fl.inflation"), lambda row: _sv(row["inflation"]), numeric=True),
                    Column(L("fl.realranta"), lambda row: _sv(row["real_rate"]), numeric=True),
                    Column(L("fl.golv_binder"), _which_floor),
                    Column(L("fl.faktor"), lambda row: _sv(row["factor"]) + "×", numeric=True),
                    Column(L("fl.snittindex"), lambda row: _sv(row["mean_index"], 1), numeric=True),
                ],
            ),
            unsafe_allow_html=True,
        )
        if highlight_year is not None:
            st.caption(L("fl.vald_rad", v0=str(highlight_year)))
        st.markdown(L("fl.slutsats"))
