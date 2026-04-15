"""Scenario simulator — Version C only (per DEVIATIONS.md D12).

Pure function, no I/O. Used by the Scenariosimulator Streamlit page.
"""

from __future__ import annotations


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
        rate_shock: Absolute change in policy rate (percentage points).
        income_shock: Relative change in income (e.g. 0.05 = +5%).
        price_shock: Relative change in price/K/T (e.g. -0.10 = -10%).
        baseline_panel: dict with keys: income, kt_ratio, policy_rate, cpi_yoy_pct.

    Returns:
        dict with baseline_v_c, scenario_v_c, delta, delta_pct, scope_note.
    """
    income = baseline_panel["income"]
    kt = baseline_panel["kt_ratio"]
    rate = baseline_panel["policy_rate"]
    cpi = baseline_panel["cpi_yoy_pct"]

    # Baseline Version C
    real_rate_base = max(rate - cpi, 0.005)
    baseline_v_c = income / (kt * real_rate_base)

    # Scenario
    s_income = income * (1 + income_shock)
    s_kt = kt * (1 + price_shock)
    s_rate = rate + rate_shock
    real_rate_scen = max(s_rate - cpi, 0.005)
    scenario_v_c = s_income / (s_kt * real_rate_scen)

    delta = scenario_v_c - baseline_v_c
    delta_pct = (delta / baseline_v_c * 100) if baseline_v_c != 0 else 0.0

    return {
        "baseline_v_c": baseline_v_c,
        "scenario_v_c": scenario_v_c,
        "delta": delta,
        "delta_pct": delta_pct,
        "baseline_income": income,
        "scenario_income": s_income,
        "baseline_kt": kt,
        "scenario_kt": s_kt,
        "baseline_rate": rate,
        "scenario_rate": s_rate,
        "real_rate_base": real_rate_base,
        "real_rate_scen": real_rate_scen,
        "scope_note": "Simulatorn beräknar endast Version C (realversion)",
    }
