"""Display sections for the Scenariosimulator page.

Same reasoning as `src/kontantinsats/sections.py`: a page script that both wires
up state and renders every card stops being read and starts being scrolled. This
holds the sections that draw themselves from a computed result, so the page keeps
the sliders and the layout and nothing else.

Added when the national outcome section took `pages/05_Scenario.py` past the
400-line limit.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.scenario.panel_scenario import shock_panel
from src.ui.components import (
    card_header,
    delta_meta,
    kpi_card,
    purpose_panel,
    render_kpi_row,
)
from src.ui.labels import L


def render_national_outcome(
    ranked: pd.DataFrame,
    year: int,
    *,
    rate_shock: float,
    cpi_shock: float,
    income_shock: float,
    price_shock: float,
    n_kommuner: int,
) -> None:
    """The same scenario applied to every municipality, not just one county.

    "What happens to this län" is the question the simulator above can answer.
    "How much of the country crosses into hög risk" is usually the one being
    asked, and it needs the whole panel.

    The class boundaries are held fixed at the baseline year's distribution;
    `src/scenario/panel_scenario.py` explains why re-ranking instead would report
    no movement under any scenario the sliders can produce.

    Args:
        ranked: The scored artifact, all municipalities.
        year: Year being shocked.
        rate_shock: Policy rate change, percentage points.
        cpi_shock: Inflation change, percentage points.
        income_shock: Income change, relative.
        price_shock: Price change, relative.
        n_kommuner: Panel size, read from provenance rather than typed.
    """
    with st.container(border=True):
        st.markdown(
            card_header(
                L("sc.riket_rubrik"),
                L("sc.riket_underrubrik", v0=str(n_kommuner)),
                L("sc.riket_tagg"),
            ),
            unsafe_allow_html=True,
        )
        outcome = shock_panel(
            ranked,
            year,
            rate_shock=rate_shock,
            cpi_shock=cpi_shock,
            income_shock=income_shock,
            price_shock=price_shock,
        )

        # Through render_kpi_row like every other KPI strip on the site.
        render_kpi_row([
            kpi_card(
                label=label,
                value=str(after),
                unit=L("sc.riket_kommuner"),
                delta=(f"{after - before:+d}" if after != before else ""),
                # More municipalities in hög risk is bad; more in låg risk is
                # good; the middle class carries no direction of its own.
                **delta_meta(after - before, higher_is_better=better),
                variant=variant,
                tooltip=L("sc.riket_tooltip_v0", v0=str(before)),
            )
            for label, before, after, variant, better in (
                (L("sc.riket_hog"), outcome.before["hog"], outcome.after["hog"], "accent", False),
                (L("sc.riket_medel"), outcome.before["medel"], outcome.after["medel"], "default", None),
                (L("sc.riket_lag"), outcome.before["lag"], outcome.after["lag"], "default", True),
            )
        ])

        # One sentence naming the movement, because three changed counts do not
        # by themselves say which way the country went.
        if outcome.crossed_into_hog:
            st.markdown(L("sc.riket_in_i_hog_v0", v0=str(outcome.crossed_into_hog)))
        elif outcome.crossed_out_of_hog:
            st.markdown(L("sc.riket_ut_ur_hog_v0", v0=str(outcome.crossed_out_of_hog)))
        else:
            st.markdown(L("sc.riket_ingen_rorelse"))

        st.caption(L("sc.riket_forklaring"))


def render_purpose() -> None:
    """What the page is for, before any caveat about which formula it uses.

    The scope note underneath explains that the simulator computes Version C
    only. That is worth saying, and it means nothing until a reader knows why
    they would run a simulation at all. Purpose first, methodology second.

    The copy is `docs/ANALYSIS_GUIDE.md` section 2, which has carried "Why it
    exists" and "When to use it" since the guide was written without either ever
    reaching the page they describe.
    """
    with st.container(border=True):
        st.markdown(
            purpose_panel(
                L("sc.syfte_rubrik"),
                [L("sc.syfte_p1"), L("sc.syfte_p2")],
                L("sc.syfte_nar_rubrik"),
                [L("sc.syfte_nar_1"), L("sc.syfte_nar_2"), L("sc.syfte_nar_3")],
            ),
            unsafe_allow_html=True,
        )
