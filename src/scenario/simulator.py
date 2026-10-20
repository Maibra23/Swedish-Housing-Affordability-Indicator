"""Scenario simulator — Version C only.

Pure function, no I/O. Used by the Scenariosimulator Streamlit page.

Formula aligned with src/indices/affordability.py compute_version_c, through the
same `cost_model.cost_share`:
    V_C = 100 · 0,85 · P · (r · 0,7 / 100 + amortisation) / (2 · I)

The rate shock moves `r`, the mean rate on **new** mortgages across every
fixation period, not the policy rate. That is a deliberate limit. A policy-rate
change reaches a floating loan within about three months but a fixed loan only
when it is refixed, so how much of a policy move reaches households in a year
depends on the fixation mix. In 2021 to 2023 the policy rate rose 3,5 pp on
annual means and the new-mortgage rate 3,0 pp. The slider states the outcome the
household faces instead of guessing the pass-through.
"""

from __future__ import annotations

import math

from src.indices.cost_model import cost_share


def _validate(**values: float) -> None:
    """Refuse inputs that would return NaN, infinity or a negative index.

    Income and price must be positive, every value finite, and a relative shock
    of -100 % or below would leave nothing to divide by.

    Raises:
        ValueError: Naming the argument and the value it received.
    """
    for name, value in values.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number, got {value!r}")
    for name in ("income", "price", "mortgage_rate"):
        if values[name] <= 0:
            raise ValueError(f"{name} must be positive, got {values[name]!r}")
    for name in ("income_shock", "price_shock"):
        if values[name] <= -1:
            raise ValueError(f"{name} must be above -1 (-100 %), got {values[name]!r}")


#: The lowest scenario rate the simulator will price, in percent. Sweden's
#: lowest annual mean on new mortgages was 1,5 % (2021); a shock below this
#: would describe lending that has never existed, so it is held here and the
#: page says so.
MIN_SCENARIO_RATE = 0.5


def simulate(
    county_kod: str,
    rate_shock: float,
    income_shock: float,
    price_shock: float,
    baseline_panel: dict,
) -> dict:
    """Compute Version C under a scenario shock.

    Args:
        county_kod: 2-digit county code.
        rate_shock: Absolute change in the mean new-mortgage rate, percentage points.
        income_shock: Relative change in income (e.g. 0.05 = +5%).
        price_shock: Relative change in price (e.g. -0.10 = -10%).
        baseline_panel: dict with keys income (SEK), transaction_price_sek
            (SEK), mortgage_rate (percent) and year.

    Returns:
        dict with baseline_v_c, scenario_v_c, delta, delta_pct and the inputs
        on both sides. Version C is a cost share, so a positive delta is worse.
    """
    income = baseline_panel["income"]
    price = baseline_panel["transaction_price_sek"]
    rate = baseline_panel["mortgage_rate"]
    year = int(baseline_panel["year"])
    _validate(
        income=income, price=price, mortgage_rate=rate,
        rate_shock=rate_shock, income_shock=income_shock, price_shock=price_shock,
    )

    baseline_v_c = cost_share(income, price, rate, year)

    s_income = income * (1 + income_shock)
    s_price = price * (1 + price_shock)
    s_rate = max(rate + rate_shock, MIN_SCENARIO_RATE)
    scenario_v_c = cost_share(s_income, s_price, s_rate, year)

    delta = scenario_v_c - baseline_v_c
    delta_pct = delta / baseline_v_c * 100

    return {
        "baseline_v_c": baseline_v_c,
        "scenario_v_c": scenario_v_c,
        "delta": delta,
        "delta_pct": delta_pct,
        "baseline_income": income,
        "scenario_income": s_income,
        "baseline_price": price,
        "scenario_price": s_price,
        "baseline_rate": rate,
        "scenario_rate": s_rate,
        "rate_held_at_minimum": rate + rate_shock < MIN_SCENARIO_RATE,
        "year": year,
        "scope_note": "Simulatorn beräknar endast Version C (kassaflödesversion)",
    }
