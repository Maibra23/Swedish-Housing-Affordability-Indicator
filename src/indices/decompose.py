"""Split a year-on-year move in the index into the cost rate and the rest.

The rate and the amortisation rule are national, so the national mean of
Version C factors exactly. Writing it for year `t` over the `N` scored
municipalities, with `k = 100 · 0,85 / 2`:

    mean C_t = (1/N) · Σ  k · (P_it / I_it) · q_t / 100
             = (k · q_t / 100) · (1/N) · Σ  P_it / I_it
             = (k · q_t / 100) · m_t

`q_t` is the yearly cost per krona borrowed — the mortgage rate after the
interest deduction plus the amortisation in force — the same number for every
municipality in the year, so it leaves the sum entirely. What remains, `m_t`, is
the mean ratio of price to income: **the index with the rate and the rules taken
out**, in years of median income.

Two things follow, and both are what the pages need:

**A series that compares across years on prices alone.** `m_t` carries no rate
and no amortisation rule. It is the answer to "did houses get dearer relative to
what people earn", with the financing taken out.

**An exact attribution for any pair of years.** The ratio of the levels is the
product of the two parts, so a year's change splits into a part from `q` and a
part from price against income. They multiply rather than add, which the copy
says.

**What this does not claim.** `m_t` is free of the formula's rate term, not of
the rate's effect on the economy: house prices respond to interest rates, so a
rate cycle reaches `m_t` through `P`.

Until 2026-10-20 this split separated a *floored real rate* from income against
price, because the old Version C's level moved by a third in one year when its
floor released. The cost share has no floor, so the split is now an ordinary
attribution rather than an artefact detector.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

#: How far the two parts may miss the whole before the split stops being exact.
#: The identity is algebra, so this is float noise and not a tolerance for error.
EXACTNESS_TOLERANCE = 1e-9


@dataclass(frozen=True)
class LevelChange:
    """What moved the national mean index between two years, and by how much.

    The three percentages are multiplicative: `1 + total` equals
    `(1 + rate) · (1 + price_to_income)` up to float noise. Presenting them as
    additive would overstate whichever part is smaller.

    Args:
        from_year: The earlier year.
        to_year: The later year.
        total_pct: Change in the mean index, in percent.
        rate_pct: The part contributed by the cost per krona borrowed — the
            mortgage rate after the deduction, plus amortisation.
        price_to_income_pct: The part contributed by price against income —
            the half of the move that is about the housing market rather than
            its financing.
        residual: How far the product of the parts misses the whole, relative.
    """

    from_year: int
    to_year: int
    total_pct: float
    rate_pct: float
    price_to_income_pct: float
    residual: float

    @property
    def is_exact(self) -> bool:
        """Whether the two parts account for the whole move.

        They must, by construction. A caller states the split only while this
        holds, for the same reason Sida 02 measures the spread of the A-to-C
        ratio before stating its median.
        """
        return self.residual <= EXACTNESS_TOLERANCE

    @property
    def rate_dominates(self) -> bool:
        """Whether the cost rate moved the level more than price against income did."""
        return abs(self.rate_pct) > abs(self.price_to_income_pct)


def decompose_change(history: pd.DataFrame, from_year: int, to_year: int) -> LevelChange | None:
    """Attribute the move in the mean index between two years.

    Args:
        history: A frame from :func:`src.indices.agreement.cost_history`,
            carrying `year`, `cost_rate`, `price_to_income` and `mean_index`.
        from_year: The earlier year.
        to_year: The later year.

    Returns:
        A :class:`LevelChange`, or None when either year is absent from the
        history or carries a value the ratio cannot be taken against — a caller
        asking about an unscored year gets nothing rather than a figure.
    """
    rows = history.set_index("year")
    if from_year not in rows.index or to_year not in rows.index:
        return None

    start, end = rows.loc[from_year], rows.loc[to_year]
    if min(float(start["mean_index"]), float(start["price_to_income"]), float(start["cost_rate"])) <= 0:
        return None

    total = float(end["mean_index"]) / float(start["mean_index"])
    # The cost rate multiplies the level, so a higher rate raises it.
    rate = float(end["cost_rate"]) / float(start["cost_rate"])
    price_to_income = float(end["price_to_income"]) / float(start["price_to_income"])

    return LevelChange(
        from_year=int(from_year),
        to_year=int(to_year),
        total_pct=(total - 1.0) * 100.0,
        rate_pct=(rate - 1.0) * 100.0,
        price_to_income_pct=(price_to_income - 1.0) * 100.0,
        residual=abs(rate * price_to_income / total - 1.0),
    )
