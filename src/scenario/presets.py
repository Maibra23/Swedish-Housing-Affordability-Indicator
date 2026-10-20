"""Preset scenarios for Sida 05, and the one something other than the page reads.

The rate-cycle preset lives here rather than only in the page, because
`interpret_scenario` has to recognise it to say where its numbers come from.
Two copies of the same three numbers would drift apart without anyone noticing.

The rate-cycle values are the annual-mean moves from 2021 to 2023 in the panel,
rounded to the slider steps: the mean rate on new mortgages rose 3,0 pp, median
income 9,1 % and the mean small-house price fell 5,7 %.
`tests/test_scenario_interpretation.py` checks them against the panel, so a
refresh that moves the history fails a test instead of leaving the preset stale.

Until 2026-10-20 this preset was "Riksbanken 2022": +4 pp policy rate and +8 pp
CPI, peak to trough. Under the real-rate formula it *improved* affordability,
because inflation outran the rate. Under the cash-flow formula the same history
raises the cost share, which is what households experienced.
"""

from __future__ import annotations

#: Rate in percentage points, income and price in percent, matching the slider
#: units on Sida 05.
RATE_CYCLE_2021_23 = {"rate": 3.0, "income": 9, "price": -5}
LOW_RATE_BOOM_2019_21 = {"rate": 0.0, "income": 5, "price": 25}
WAGE_BOOM = {"rate": 1.0, "income": 5, "price": 10}
RESET = {"rate": 0.0, "income": 0, "price": 0}


def is_rate_cycle_preset(rate_shock: float, income_shock_pct: float, price_shock_pct: float) -> bool:
    """Whether the sliders sit exactly on the 2021–23 rate-cycle preset.

    Args:
        rate_shock: Mortgage rate change, percentage points.
        income_shock_pct: Income change, percent.
        price_shock_pct: Price change, percent.

    Returns:
        True only for an exact match. A user who presses the preset and then
        moves a slider is running their own scenario, and the caption no longer
        describes it.
    """
    return (rate_shock, income_shock_pct, price_shock_pct) == (
        RATE_CYCLE_2021_23["rate"],
        RATE_CYCLE_2021_23["income"],
        RATE_CYCLE_2021_23["price"],
    )
