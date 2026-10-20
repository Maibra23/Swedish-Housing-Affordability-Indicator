"""What moved one municipality's Version C between two years, exactly.

Sida 03 used to plot median income, K/T and the policy rate, pick the one with the
largest coefficient of variation, and call it the driver of the index. That was
wrong three ways: K/T is not in the formula, the policy rate's mean sits near zero
so its coefficient of variation is always the largest, and variation is not
contribution.

Version C is a product, so the change between any two years splits exactly:

    C_end / C_start = (I_start / I_end) · (P_end / P_start) · (q_end / q_start)

where `q` is the yearly cost per krona borrowed — the mortgage rate after the
interest deduction, plus the amortisation in force (`cost_rate`). Each factor is
one input's contribution, and the three multiply to the whole. They are reported
as percentages that multiply, as `src/indices/decompose.py` does for the national
mean. C is a cost share, so a negative part is one that made housing cheaper.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from src.indices.cost_model import INTEREST_DEDUCTION, amortisation_by_year

#: The three inputs, in the order the page draws them.
COMPONENTS = ("income", "price", "cost_rate")


@dataclass(frozen=True)
class ComponentChange:
    """One municipality's index change and the part each input played.

    Args:
        from_year: First scored year.
        to_year: Last scored year.
        total_pct: Change in Version C, percent.
        parts_pct: Contribution of each input, percent, keyed by `COMPONENTS`.
            The factors `1 + p/100` multiply to `1 + total_pct/100`.
        driver: The input whose factor moved furthest from one.
    """

    from_year: int
    to_year: int
    total_pct: float
    parts_pct: dict[str, float]
    driver: str


def cost_rate(rows: pd.DataFrame) -> pd.Series:
    """Yearly cost per krona borrowed, in percent: net interest plus amortisation."""
    amortisation = amortisation_by_year(rows["year"]).set_axis(rows.index)
    return rows["mortgage_rate"] * (1.0 - INTEREST_DEDUCTION) + 100.0 * amortisation


def attribute_change(kommun: pd.DataFrame) -> ComponentChange | None:
    """Split a municipality's change in Version C into its three inputs.

    Args:
        kommun: One municipality's rows, with `year`, `version_c`,
            `median_income`, `transaction_price_sek` and `mortgage_rate`.

    Returns:
        The split between the first and last scored year, or None when fewer
        than two years are scored.
    """
    scored = kommun.dropna(subset=["version_c"]).sort_values("year")
    if len(scored) < 2:
        return None
    first, last = scored.iloc[0], scored.iloc[-1]
    rates = cost_rate(scored)

    factors = {
        "income": first["median_income"] / last["median_income"],
        "price": last["transaction_price_sek"] / first["transaction_price_sek"],
        "cost_rate": rates.iloc[-1] / rates.iloc[0],
    }
    total = last["version_c"] / first["version_c"]
    return ComponentChange(
        from_year=int(first["year"]),
        to_year=int(last["year"]),
        total_pct=(total - 1) * 100,
        parts_pct={k: (f - 1) * 100 for k, f in factors.items()},
        driver=max(factors, key=lambda k: abs(math.log(factors[k]))),
    )
