"""Split a year-on-year move in the index into the rate and the rest.

Qualifying a claim is not the same as answering the question behind it. Sida 01
used to tell a reader to judge Sweden's direction from the mean index; that was
withdrawn because the rate floor moves the level without affordability moving.
Withdrawing it left the question unanswered, and it is a reasonable question.

It is answerable exactly, because the rate is national. Writing the national
mean of Version C for year `t` over the `N` scored municipalities:

    mean C_t = (1/N) · Σ  I_it / (P_it · r_t/100)
             = (100 / r_t) · (1/N) · Σ  I_it / P_it
             = (100 / r_t) · m_t

`r_t` is the floored real rate, the same number for every municipality in the
year, so it leaves the sum entirely. What remains, `m_t`, is the mean ratio of
income to price — **the index with the interest rate taken out**. On the shipped
artifact the identity holds to 2·10⁻¹⁶ relative error in every year, for Version
A as well with its own floored rate.

Two things follow, and both are what the pages needed:

**A series that does compare across years.** `m_t` carries no rate and therefore
no floor. It runs 22,9 % to 17,7 % over this panel: a median income bought 22,9
% of a house in 2014 and 17,7 % in 2024, a fall of 22 % with no artefact in it.

**An exact attribution for any pair of years.** The ratio of the levels is the
product of the two parts, so 2023 to 2024's −36,5 % splits into −35,1 % from the
rate denominator and −2,2 % from income against price. They multiply rather than
add, which the copy says.

**What this does not claim.** `m_t` is free of the formula's rate term, not of
the rate's effect on the economy: house prices respond to interest rates, so a
rate cycle reaches `m_t` through `P`. It removes a mechanical artefact of the
floor, not monetary policy. See F17 and METHODOLOGY section 3.
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
    `(1 + rate) · (1 + income_to_price)` up to float noise. Presenting them as
    additive would overstate whichever part is smaller.

    Args:
        from_year: The earlier year.
        to_year: The later year.
        total_pct: Change in the mean index, in percent.
        rate_pct: The part contributed by the rate each formula divided by.
        income_to_price_pct: The part contributed by income against price —
            the half of the move that is about affordability rather than policy.
        residual: How far the product of the parts misses the whole, relative.
    """

    from_year: int
    to_year: int
    total_pct: float
    rate_pct: float
    income_to_price_pct: float
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
        """Whether the rate moved the level more than income against price did."""
        return abs(self.rate_pct) > abs(self.income_to_price_pct)


def decompose_change(history: pd.DataFrame, from_year: int, to_year: int) -> LevelChange | None:
    """Attribute the move in the mean index between two years.

    Args:
        history: A frame from :func:`src.indices.agreement.floor_history`,
            carrying `year`, `rate_used_c`, `income_to_price` and `mean_index`.
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
    if min(float(start["mean_index"]), float(start["income_to_price"]), float(end["rate_used_c"])) <= 0:
        return None

    total = float(end["mean_index"]) / float(start["mean_index"])
    # The rate enters as 100/r, so a *higher* rate lowers the level: the ratio
    # is the old rate over the new one, not the other way round.
    rate = float(start["rate_used_c"]) / float(end["rate_used_c"])
    income_to_price = float(end["income_to_price"]) / float(start["income_to_price"])

    return LevelChange(
        from_year=int(from_year),
        to_year=int(to_year),
        total_pct=(total - 1.0) * 100.0,
        rate_pct=(rate - 1.0) * 100.0,
        income_to_price_pct=(income_to_price - 1.0) * 100.0,
        residual=abs(rate * income_to_price / total - 1.0),
    )
