"""The household cash-flow model behind Versions A and C.

A typical buyer of a small house in a municipality: two earners on the
municipality's median income, borrowing 85 % of the mean purchase price at the
year's average rate on new mortgages. Both versions state the yearly cost of
that loan as a percentage of the household's income, so **higher is worse**.

    loan   = LOAN_TO_VALUE × price
    A      = 100 × loan × r                                    / (EARNERS × income)
    C      = 100 × loan × (r × (1 − INTEREST_DEDUCTION) + amortisation) / (EARNERS × income)

A is the bank's gross view: interest only, before tax. C is what the household
actually pays out: interest after the 30 % ränteavdrag, plus the amortisation
the requirement in force that year demands.

Why this replaced the old formulas. A used to divide by the policy rate and C by
the policy rate less KPI inflation. Those rates sat at or below zero for most of
2015 to 2023, so both formulas needed a floor, and C's bound in nine of eleven
years. Households never paid the policy rate, and KPI rises by itself when rates
rise, because it prices mortgage interest. The mortgage rate stayed between 1,5
and 4,5 % throughout, and a cost share multiplies by it instead of dividing, so
no floor is needed. METHODOLOGY section 3 has the comparison.

What it leaves out, deliberately. The extra 1 % amortisation for loans above 4,5
times income (March 2018 to March 2026) is not modelled: it would make the cost
municipality-specific, so the index would rank on the rule rather than on
income against price. The loan share is held at 85 % through the projection
even though the cap rose to 90 % in April 2026, so years stay comparable. See
F12 and F18.
"""

from __future__ import annotations

from typing import TypeVar

import numpy as np
import pandas as pd

#: Share of the purchase price borrowed: the bolånetak in force 2010 to March 2026.
LOAN_TO_VALUE = 0.85

#: Share of interest paid back through ränteavdrag (30 % up to 100 000 SEK a year).
INTEREST_DEDUCTION = 0.30

#: Earners per household. Median income is per person; a house is bought by a household.
EARNERS = 2

#: Yearly amortisation on a loan above 70 % of the property's value.
AMORTISATION_RATE = 0.02

#: The amortisation requirement took effect on 1 June 2016.
AMORTISATION_START_YEAR = 2016
AMORTISATION_START_MONTH = 6

Number = TypeVar("Number", float, pd.Series)


def amortisation_rate(year: int) -> float:
    """The amortisation rate in force, averaged over the calendar year.

    Every rate in the panel is an annual mean, so 2016 gets the seven months the
    requirement applied for rather than all or nothing.
    """
    if year < AMORTISATION_START_YEAR:
        return 0.0
    if year == AMORTISATION_START_YEAR:
        months = 12 - AMORTISATION_START_MONTH + 1
        return AMORTISATION_RATE * months / 12
    return AMORTISATION_RATE


def amortisation_by_year(years: pd.Series) -> pd.Series:
    """`amortisation_rate` for every row of a year column."""
    return years.astype(int).map(amortisation_rate).astype(float)


def _validate_rate(mortgage_rate) -> None:
    values = np.atleast_1d(np.asarray(mortgage_rate, dtype=float))
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError(
            f"mortgage_rate must be a positive, finite percentage, got {mortgage_rate!r}"
        )


def _loan_per_income(income: Number, price: Number) -> Number:
    return LOAN_TO_VALUE * price / (EARNERS * income)


def interest_share(income: Number, price: Number, mortgage_rate) -> Number:
    """Version A: gross yearly interest as a percentage of household income.

    Args:
        income: Median income per person, SEK.
        price: Mean purchase price, SEK.
        mortgage_rate: Percent, e.g. 4.3.
    """
    _validate_rate(mortgage_rate)
    return 100.0 * _loan_per_income(income, price) * mortgage_rate / 100.0


def cost_share(income: Number, price: Number, mortgage_rate, year) -> Number:
    """Version C: net interest plus amortisation as a percentage of household income.

    Args:
        income: Median income per person, SEK.
        price: Mean purchase price, SEK.
        mortgage_rate: Percent, e.g. 4.3.
        year: The year, or a year column, deciding the amortisation rate.
    """
    _validate_rate(mortgage_rate)
    amortisation = (
        amortisation_by_year(year) if isinstance(year, pd.Series) else amortisation_rate(int(year))
    )
    if isinstance(amortisation, pd.Series) and isinstance(income, pd.Series):
        amortisation = amortisation.set_axis(income.index)
    yearly_rate = mortgage_rate / 100.0 * (1.0 - INTEREST_DEDUCTION) + amortisation
    return 100.0 * _loan_per_income(income, price) * yearly_rate


__all__ = [
    "AMORTISATION_RATE",
    "EARNERS",
    "INTEREST_DEDUCTION",
    "LOAN_TO_VALUE",
    "amortisation_by_year",
    "amortisation_rate",
    "cost_share",
    "interest_share",
]
