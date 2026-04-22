"""Kontantinsats regime engine per METHODOLOGY_v2.md section 6.

Models five Swedish regulatory regimes for housing down payments and
amortization requirements. Uses transaction_price_sek directly from
the panel (no K/T proxy conversion needed).

Regimes:
  pre_2010   : No formal minimum down payment, no mandatory amortization
  bolanetak  : 15% minimum down payment (Oct 2010)
  amort_1    : + 2% amort if LTV>70%, 1% if LTV>50% (Jun 2016)
  amort_2    : + 1% extra amort if LTI>4.5x (Mar 2018 – Mar 2026)
  latt_2026  : Bolånetak raised to 90% (10% down), LTI rule removed (Apr 2026)
"""

from __future__ import annotations

REGIMES = {
    "pre_2010": {
        "label": "Före 2010",
        "period": "Till okt 2010",
        "min_down_pct": 0.0,
        "amort_rules": [],
    },
    "bolanetak": {
        "label": "Bolånetak",
        "period": "Okt 2010 – jun 2016",
        "min_down_pct": 0.15,
        "amort_rules": [],
    },
    "amort_1": {
        "label": "Amorteringskrav 1.0",
        "period": "Jun 2016 – mar 2018",
        "min_down_pct": 0.15,
        "amort_rules": [
            {"ltv_threshold": 0.70, "amort_pct": 0.02},
            {"ltv_threshold": 0.50, "amort_pct": 0.01},
        ],
    },
    "amort_2": {
        "label": "Amorteringskrav 2.0",
        "period": "Mar 2018 – mar 2026",
        "min_down_pct": 0.15,
        "amort_rules": [
            {"ltv_threshold": 0.70, "amort_pct": 0.02},
            {"ltv_threshold": 0.50, "amort_pct": 0.01},
            {"lti_threshold": 4.5, "amort_pct": 0.01},
        ],
    },
    "latt_2026": {
        "label": "Lättnad 2026",
        "period": "Apr 2026 – nuvarande",
        "min_down_pct": 0.10,
        "amort_rules": [
            {"ltv_threshold": 0.70, "amort_pct": 0.02},
            {"ltv_threshold": 0.50, "amort_pct": 0.01},
        ],
    },
}


def apply_regime(
    price_sek: float,
    income_sek: float,
    rate: float,
    regime_key: str,
    savings_rate: float = 0.10,
    bank_margin: float = 0.0,
) -> dict:
    """Compute kontantinsats requirements under a given regulatory regime.

    Args:
        price_sek: Mean transaction price in SEK (from panel transaction_price_sek).
        income_sek: Household income in SEK (individual or combined for couple).
        rate: Policy rate as decimal (e.g. 0.036 = 3.6%).
        regime_key: One of "pre_2010", "bolanetak", "amort_1", "amort_2", "latt_2026".
        savings_rate: Fraction of income saved annually (default 10%).
        bank_margin: Bank's interest rate margin above policy rate, as decimal
            (e.g. 0.017 = 1.7 pp). Default 0.0 (policy rate only, for backward compat).

    Returns:
        dict with:
          required_cash     - down payment in SEK
          years_to_save     - years to save the down payment
          loan_amount       - loan size in SEK
          ltv               - loan-to-value ratio
          lti               - loan-to-income ratio
          effective_rate    - actual borrowing rate used (policy + margin)
          annual_interest   - annual interest cost in SEK
          annual_amort      - annual amortization in SEK
          annual_total      - annual housing cost (interest + amort)
          monthly_total     - monthly housing cost in SEK
          residual_income   - annual income minus annual housing cost
          amort_pct         - effective amortization rate applied
    """
    if regime_key not in REGIMES:
        raise ValueError(f"Unknown regime: {regime_key}. Valid: {list(REGIMES.keys())}")

    regime = REGIMES[regime_key]

    # Down payment
    required_cash = price_sek * regime["min_down_pct"]
    loan_amount = price_sek - required_cash

    # Ratios — based on household income (may be individual or combined)
    ltv = loan_amount / price_sek if price_sek > 0 else 0.0
    lti = loan_amount / income_sek if income_sek > 0 else 0.0

    # Years to save — based on household savings capacity
    annual_savings = income_sek * savings_rate
    years_to_save = required_cash / annual_savings if annual_savings > 0 else 0.0

    # Interest cost — effective rate = policy rate + bank margin
    effective_rate = rate + bank_margin
    annual_interest = loan_amount * effective_rate

    # Amortization — rules are cumulative thresholds
    amort_pct = 0.0
    for rule in regime["amort_rules"]:
        if "ltv_threshold" in rule and ltv > rule["ltv_threshold"]:
            amort_pct = max(amort_pct, rule["amort_pct"])
        if "lti_threshold" in rule and lti > rule["lti_threshold"]:
            amort_pct += rule["amort_pct"]

    annual_amort = loan_amount * amort_pct

    # Totals
    annual_total = annual_interest + annual_amort
    monthly_total = annual_total / 12
    residual_income = income_sek - annual_total

    return {
        "required_cash": required_cash,
        "years_to_save": years_to_save,
        "loan_amount": loan_amount,
        "ltv": ltv,
        "lti": lti,
        "effective_rate": effective_rate,
        "annual_interest": annual_interest,
        "annual_amort": annual_amort,
        "annual_total": annual_total,
        "monthly_total": monthly_total,
        "residual_income": residual_income,
        "amort_pct": amort_pct,
    }


def compare_regimes(
    price_sek: float,
    income_sek: float,
    rate: float,
    savings_rate: float = 0.10,
    bank_margin: float = 0.0,
) -> dict[str, dict]:
    """Compute all five regimes for a given price/income/rate combination.

    Args:
        price_sek: Mean transaction price in SEK.
        income_sek: Household income in SEK (individual or couple combined).
        rate: Policy rate as decimal.
        savings_rate: Fraction of income saved annually.
        bank_margin: Bank interest rate margin above policy rate, as decimal.

    Returns dict keyed by regime_key with apply_regime() results.
    """
    return {
        key: apply_regime(price_sek, income_sek, rate, key, savings_rate, bank_margin)
        for key in REGIMES
    }


if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path

    DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
    panel = pd.read_parquet(DATA_DIR / "panel_county.parquet")

    # Use Stockholm 2024 as example
    sthlm = panel[(panel["lan_code"] == "01") & (panel["year"] == 2024)].iloc[0]
    price = sthlm["transaction_price_sek"]
    income = sthlm["median_income"]
    rate_pct = sthlm["policy_rate"]
    rate = rate_pct / 100.0

    print(f"Stockholm 2024: price={price/1e6:.2f} MSEK, income={income/1e3:.0f} kSEK, rate={rate_pct:.2f}%")
    print()

    results = compare_regimes(price, income, rate)
    for key, res in results.items():
        regime = REGIMES[key]
        print(f"--- {regime['label']} ({regime['period']}) ---")
        print(f"  Down payment:     {res['required_cash']/1e3:>8.0f} kSEK")
        print(f"  Years to save:    {res['years_to_save']:>8.1f}")
        print(f"  Loan:             {res['loan_amount']/1e3:>8.0f} kSEK")
        print(f"  LTV:              {res['ltv']:>8.1%}")
        print(f"  LTI:              {res['lti']:>8.1f}x")
        print(f"  Monthly cost:     {res['monthly_total']:>8.0f} SEK")
        print(f"  Residual income:  {res['residual_income']/1e3:>8.0f} kSEK/yr")
        print(f"  Amort rate:       {res['amort_pct']:>8.1%}")
        print()

    # Validation: among regimes with 15% down payment, monthly cost should be
    # amort_2 >= amort_1 >= bolanetak (same loan, increasing amort requirements).
    # pre_2010 has 0% down → larger loan → higher interest, so it doesn't fit
    # the simple ordering with the others.
    costs = {k: v["monthly_total"] for k, v in results.items()}
    assert costs["amort_2"] >= costs["amort_1"] >= costs["bolanetak"], (
        f"Monthly cost ordering violated (same-loan regimes): "
        f"amort_2={costs['amort_2']:.0f} >= amort_1={costs['amort_1']:.0f} >= "
        f"bolanetak={costs['bolanetak']:.0f}"
    )
    print("VALIDATION PASSED: amort_2 >= amort_1 >= bolanetak (same down payment regimes)")
    print(f"  pre_2010 ({costs['pre_2010']:.0f} SEK/mo) has higher interest due to 0% down / larger loan")
