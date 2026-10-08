"""The "Nyckelinsikt" card on Sida 04: what today's rules mean for this household.

The card it replaces compared the cheapest regime with the dearest, called the
gap a saving against today, quoted the percentage on the wrong base ("56 %
billigare" where the cheaper option was 36 % cheaper), and named the regime
without amortisation "förmånligaste". That last word was the deeper error: the
whole gap was amortisation, which repays the household's own loan and is saving,
not cost, and the "cheapest" regime needed a 50 % larger down payment.

This version states today's requirement, splits the monthly payment into interest
and amortisation, says plainly when the payment exceeds the income, and compares
with the rules that applied immediately before, which is the comparison a reader
in 2026 actually faces.
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from src.kontantinsats.engine import BASELINE_REGIME, REGIMES
from src.ui.components import card_header, format_sek
from src.ui.labels import L

#: The regime in force before today's. The comparison that matters to a buyer.
PREVIOUS_REGIME = "amort_2"

#: Conventional budgeting guideline, as in `src/ui/interpret.py`.
HOUSING_COST_SHARE_GUIDELINE = 30.0


@dataclass(frozen=True)
class InsightInputs:
    """What the card needs, independent of Streamlit.

    Args:
        results: `compare_regimes` output, keyed by regime.
        household_label: "singelhushåll" or "par".
        region: Selected municipality or county.
        year: Analysis year the price and rate come from.
        savings_rate: Share of gross income saved, as a decimal.
        monthly_income: Gross household income per month, SEK.
    """

    results: dict
    household_label: str
    region: str
    year: int
    savings_rate: float
    monthly_income: float


def _num(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def _signed_sek(value: float) -> str:
    sign = "+" if value > 0 else "−" if value < 0 else "±"
    return f"{sign}{format_sek(abs(value))}"


def insight_paragraphs(inputs: InsightInputs) -> list[str]:
    """The card's text, one string per paragraph.

    Args:
        inputs: See :class:`InsightInputs`.

    Returns:
        Finished Swedish paragraphs, in reading order.
    """
    today = inputs.results[BASELINE_REGIME]
    before = inputs.results[PREVIOUS_REGIME]
    # Rounded independently, as the table and chart on the same page do, so the
    # card never shows a figure the table contradicts. The parts can then differ
    # from the total by a krona, which is rounding, not arithmetic.
    monthly_interest = today["annual_interest"] / 12
    monthly_amort = today["annual_amort"] / 12
    share = today["monthly_total"] / inputs.monthly_income * 100

    paragraphs = [
        L(
            "ki.insikt_idag",
            v0=inputs.household_label, v1=inputs.region,
            v2=format_sek(today["required_cash"]), v3=_num(today["years_to_save"]),
            v4=f"{inputs.savings_rate * 100:.0f}",
        ),
        L(
            "ki.insikt_betalning",
            v0=format_sek(today["monthly_total"]), v1=format_sek(monthly_interest),
            v2=_num(today["effective_rate"] * 100, 2), v3=format_sek(monthly_amort),
            v4=f"{share:.0f}",
        ),
    ]
    if share > 100:
        paragraphs.append(L("ki.insikt_over_inkomst"))
    elif share > HOUSING_COST_SHARE_GUIDELINE:
        paragraphs.append(L("ki.insikt_over_riktvarde", v0=f"{HOUSING_COST_SHARE_GUIDELINE:.0f}"))

    paragraphs.append(L(
        "ki.insikt_jamforelse",
        v0=REGIMES[PREVIOUS_REGIME]["label"], v1=REGIMES[PREVIOUS_REGIME]["period"].lower(),
        v2=format_sek(before["required_cash"]),
        v3=_signed_sek(before["required_cash"] - today["required_cash"]),
        v4=_num(before["years_to_save"] - today["years_to_save"]),
        v5=format_sek(before["monthly_total"]),
        v6=_signed_sek(before["monthly_total"] - today["monthly_total"]),
        v7=format_sek(before["annual_amort"] / 12),
    ))
    paragraphs.append(L("ki.insikt_forbehall", v0=str(inputs.year)))
    return paragraphs


def render_insight(ctx) -> None:
    """Draw the card from the page's shared context."""
    inputs = InsightInputs(
        results=ctx.results,
        household_label="par" if ctx.household_multiplier == 2 else L("ki.singelhushall_2"),
        region=ctx.selected_name,
        year=ctx.selected_year,
        savings_rate=ctx.savings_rate,
        monthly_income=ctx.monthly_income,
    )
    with st.container(border=True):
        st.markdown(
            card_header(L("ki.insikt_rubrik"), L("ki.insikt_underrubrik"), "SYNTES"),
            unsafe_allow_html=True,
        )
        for paragraph in insight_paragraphs(inputs):
            st.markdown(paragraph)
