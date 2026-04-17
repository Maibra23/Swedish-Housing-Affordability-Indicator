"""Scenario simulator — Version C only (per DEVIATIONS.md D12).

Pure function, no I/O. Used by the Scenariosimulator Streamlit page.

Formula aligned with src/indices/affordability.py compute_version_c:
    V_C = Income / (TransactionPrice * max(R - pi, 0.5) / 100)
All rates in percentage points throughout.
"""

from __future__ import annotations


def simulate(
    county_kod: str,
    rate_shock: float,
    income_shock: float,
    price_shock: float,
    baseline_panel: dict,
    cpi_shock: float = 0.0,
) -> dict:
    """Compute Version C under a scenario shock.

    Args:
        county_kod: 2-digit county code.
        rate_shock: Absolute change in policy rate (percentage points).
        income_shock: Relative change in income (e.g. 0.05 = +5%).
        price_shock: Relative change in price (e.g. -0.10 = -10%).
        baseline_panel: dict with keys:
            income (SEK), transaction_price_sek (SEK),
            policy_rate (percentage points), cpi_yoy_pct (percentage points).
        cpi_shock: Absolute change in CPI inflation (percentage points, default 0).
            When non-zero, the real rate is affected by both rate and inflation changes,
            enabling realistic scenarios like the 2022 cycle where rate +4pp & CPI +8pp
            left the real rate nearly unchanged.

    Returns:
        dict with baseline_v_c, scenario_v_c, delta, delta_pct, etc.
    """
    income = baseline_panel["income"]
    price = baseline_panel["transaction_price_sek"]
    rate = baseline_panel["policy_rate"]       # percentage points
    cpi = baseline_panel["cpi_yoy_pct"]        # percentage points

    # Baseline Version C — matches affordability.py compute_version_c
    real_rate_base = max(rate - cpi, 0.5)              # pp, floored at 0.5
    real_rate_base_dec = real_rate_base / 100.0         # decimal
    baseline_v_c = income / (price * real_rate_base_dec)

    # Scenario — CPI shock shifts inflation, affecting real rate
    s_income = income * (1 + income_shock)
    s_price = price * (1 + price_shock)
    s_rate = rate + rate_shock                         # pp
    s_cpi = cpi + cpi_shock                            # pp — CPI is now shockable
    real_rate_scen = max(s_rate - s_cpi, 0.5)          # pp, floored at 0.5
    real_rate_scen_dec = real_rate_scen / 100.0         # decimal
    scenario_v_c = s_income / (s_price * real_rate_scen_dec)

    delta = scenario_v_c - baseline_v_c
    delta_pct = (delta / baseline_v_c * 100) if baseline_v_c != 0 else 0.0

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
        "baseline_cpi": cpi,
        "scenario_cpi": s_cpi,
        "real_rate_base": real_rate_base,
        "real_rate_scen": real_rate_scen,
        "scope_note": "Simulatorn beräknar endast Version C (realversion)",
    }
