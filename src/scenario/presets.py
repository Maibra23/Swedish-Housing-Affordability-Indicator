"""Preset scenarios whose values something other than the page depends on.

The Riksbanken 2022 preset lives here, not in the page's `_presets` dict,
because `interpret_scenario` has to recognise it to explain the result. Two
copies of the same four numbers would drift apart without anyone noticing, and
the explanation would then silently stop appearing.

The values are the approximate moves of the 2022–23 tightening cycle, measured
from the peak to the trough. They are **not** the annual-mean changes the index is
built on (about +0,8 pp rate, +6,2 pp CPI and +6 % price from 2021 to 2022), and
`docs/APP_REFERENCE.md` (Part I) section 5 item 2 keeps them as they are on purpose: under
Version C the preset shows an improvement, and the caption explaining why is the
page's clearest lesson about the real rate.
"""

from __future__ import annotations

#: Rate and CPI in percentage points, income and price in percent, matching the
#: slider units on Sida 05.
RIKSBANKEN_2022 = {"rate": 4.0, "income": 0, "price": -15, "cpi": 8.0}


def is_riksbanken_2022(
    rate_shock: float, income_shock_pct: float, price_shock_pct: float, cpi_shock: float
) -> bool:
    """Whether the sliders sit exactly on the Riksbanken 2022 preset.

    Args:
        rate_shock: Policy rate change, percentage points.
        income_shock_pct: Income change, percent.
        price_shock_pct: Price change, percent.
        cpi_shock: CPI change, percentage points.

    Returns:
        True only for an exact match. A user who presses the preset and then
        moves a slider is running their own scenario, and the caption no longer
        describes it.
    """
    return (rate_shock, income_shock_pct, price_shock_pct, cpi_shock) == (
        RIKSBANKEN_2022["rate"],
        RIKSBANKEN_2022["income"],
        RIKSBANKEN_2022["price"],
        RIKSBANKEN_2022["cpi"],
    )
