"""The household cash-flow model behind Versions A and C.

Both formulas used to divide by an interest rate — A by the policy rate, C by
the policy rate less KPI inflation — and both needed a floor, because those
rates sat at or below zero for most of 2015 to 2023. C's floor bound in nine of
eleven years. A cost share has no such problem: the mortgage rate stayed between
1,5 and 4,5 % across the panel, and the formula multiplies by it rather than
dividing.

These tests pin the arithmetic and the stated assumptions, so a change to any
of them is a decision with a failing test attached rather than a drift.
"""

from __future__ import annotations

import math

import pytest

from src.indices import cost_model as cm


def test_the_stated_assumptions() -> None:
    """The four assumptions the methodology quotes, pinned to the code."""
    assert cm.LOAN_TO_VALUE == 0.85
    assert cm.INTEREST_DEDUCTION == 0.30
    assert cm.EARNERS == 2
    assert cm.AMORTISATION_RATE == 0.02


@pytest.mark.parametrize(
    "year,expected",
    [
        (2014, 0.0),
        (2015, 0.0),
        # In force from 1 June 2016: seven of twelve months, because every rate
        # in the panel is an annual mean.
        (2016, 0.02 * 7 / 12),
        (2017, 0.02),
        (2024, 0.02),
        (2030, 0.02),
    ],
)
def test_amortisation_follows_the_requirement_in_force(year: int, expected: float) -> None:
    assert cm.amortisation_rate(year) == pytest.approx(expected)


def test_interest_share_is_gross_interest_over_household_income() -> None:
    """A 4 MSEK house at 4 %, two earners on 400 000: 3,4 MSEK loan, 136 000
    interest, over 800 000 of income."""
    share = cm.interest_share(income=400_000, price=4_000_000, mortgage_rate=4.0)
    assert share == pytest.approx(100 * 0.85 * 4_000_000 * 0.04 / 800_000)
    assert share == pytest.approx(17.0)


def test_cost_share_deducts_interest_and_adds_amortisation() -> None:
    """Same household in 2024: interest after a 30 % deduction plus 2 %
    amortisation on the loan."""
    share = cm.cost_share(income=400_000, price=4_000_000, mortgage_rate=4.0, year=2024)
    loan = 0.85 * 4_000_000
    expected = 100 * loan * (0.04 * 0.70 + 0.02) / 800_000
    assert share == pytest.approx(expected)
    assert share == pytest.approx(20.4)


def test_before_amortisation_the_cost_is_net_interest_alone() -> None:
    gross = cm.interest_share(income=400_000, price=4_000_000, mortgage_rate=2.0)
    net = cm.cost_share(income=400_000, price=4_000_000, mortgage_rate=2.0, year=2015)
    assert net == pytest.approx(gross * 0.70)


def test_a_rate_shock_moves_the_cost_in_proportion_to_its_rate_term() -> None:
    """+2 pp at 4 % raises net interest by half, and the whole cost by less,
    because amortisation does not move with the rate."""
    base = cm.cost_share(income=400_000, price=4_000_000, mortgage_rate=4.0, year=2024)
    shocked = cm.cost_share(income=400_000, price=4_000_000, mortgage_rate=6.0, year=2024)
    rate_part = 100 * 0.85 * 4_000_000 * 0.02 * 0.70 / 800_000
    assert shocked - base == pytest.approx(rate_part)
    assert 0 < shocked / base - 1 < 0.5


def test_it_works_elementwise_on_series() -> None:
    import pandas as pd

    income = pd.Series([400_000.0, 300_000.0])
    price = pd.Series([4_000_000.0, 1_000_000.0])
    shares = cm.cost_share(income, price, 4.0, 2024)
    assert shares.tolist() == pytest.approx(
        [cm.cost_share(400_000, 4_000_000, 4.0, 2024), cm.cost_share(300_000, 1_000_000, 4.0, 2024)]
    )


def test_amortisation_by_year_accepts_a_series() -> None:
    import pandas as pd

    rates = cm.amortisation_by_year(pd.Series([2015, 2016, 2024]))
    assert rates.tolist() == pytest.approx([0.0, 0.02 * 7 / 12, 0.02])


@pytest.mark.parametrize("rate", [0.0, -0.5, math.nan, math.inf])
def test_a_rate_that_is_not_a_positive_number_is_refused(rate: float) -> None:
    """A mortgage rate at or below zero never happened in Sweden. Accepting one
    would hand the formulas exactly the input the old floor existed to hide."""
    with pytest.raises(ValueError, match="mortgage_rate"):
        cm.cost_share(income=400_000, price=4_000_000, mortgage_rate=rate, year=2024)
