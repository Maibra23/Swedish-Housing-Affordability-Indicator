"""Quality checks on the Kontantinsats engine, before it is trusted in production.

`test_readme_figures.py` pins a handful of outputs to the README. That proves the
engine still returns the numbers it returned when the README was written; it does
not prove those numbers are right. This file checks the engine against what the
regulations say and against properties any correct mortgage calculation must
have, and then runs it over every row the page can actually select.

Three groups:

1. **Hand-worked cases.** Each regime once, on round numbers a reader can check
   with a calculator, against the rules in METHODOLOGY section 6.
2. **Properties.** Monotonicity, reconciliation and ordering that must hold for
   every input, checked over a grid rather than one point.
3. **Inputs the page can produce.** Every kommun, county and year in the shipped
   artifacts, at the extremes of every control. This is where the two defects
   this file was written to catch lived: a negative policy rate (2015 to 2019)
   with the margin slider at zero produced a negative interest cost, and a zero
   income reported zero years to save rather than an impossible purchase.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from src.kontantinsats.engine import (
    BASELINE_REGIME,
    REGIMES,
    apply_regime,
    compare_regimes,
)
from src.provenance import selectable_years

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

PRICE = 4_000_000.0
INCOME = 500_000.0
RATE = 0.03  # decimal, as the page passes it


# ── 1 · Hand-worked cases ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "regime,down,amort",
    [
        # No minimum deposit, no amortisation: the whole price is borrowed.
        ("pre_2010", 0.00, 0.00),
        # 15 % deposit, still no amortisation requirement.
        ("bolanetak", 0.15, 0.00),
        # LTV 85 % > 70 %: 2 %. LTI 3 400 000 / 500 000 = 6,8 has no rule yet.
        ("amort_1", 0.15, 0.02),
        # As amort_1, plus 1 % because LTI 6,8 > 4,5.
        ("amort_2", 0.15, 0.03),
        # 10 % deposit, LTV 90 % > 70 %: 2 %. The LTI rule is gone.
        ("latt_2026", 0.10, 0.02),
    ],
)
def test_each_regime_matches_its_rules_by_hand(regime: str, down: float, amort: float) -> None:
    r = apply_regime(PRICE, INCOME, RATE, regime)
    loan = PRICE * (1 - down)
    assert r["required_cash"] == pytest.approx(PRICE * down)
    assert r["loan_amount"] == pytest.approx(loan)
    assert r["amort_pct"] == pytest.approx(amort)
    assert r["annual_interest"] == pytest.approx(loan * RATE)
    assert r["annual_amort"] == pytest.approx(loan * amort)
    assert r["monthly_total"] == pytest.approx(loan * (RATE + amort) / 12)


def test_the_lti_rule_is_strictly_above_four_and_a_half() -> None:
    """FI's rule applies to debt *over* 4,5 times income, not at it."""
    loan = PRICE * 0.85
    at = apply_regime(PRICE, loan / 4.5, RATE, "amort_2")
    above = apply_regime(PRICE, loan / 4.5 * 0.999, RATE, "amort_2")
    assert at["amort_pct"] == pytest.approx(0.02)
    assert above["amort_pct"] == pytest.approx(0.03)


def test_bank_margin_is_added_to_the_policy_rate() -> None:
    r = apply_regime(PRICE, INCOME, 0.03, "bolanetak", bank_margin=0.017)
    assert r["effective_rate"] == pytest.approx(0.047)
    assert r["annual_interest"] == pytest.approx(PRICE * 0.85 * 0.047)


def test_years_to_save_is_cash_over_annual_savings() -> None:
    r = apply_regime(PRICE, INCOME, RATE, "latt_2026", savings_rate=0.10)
    assert r["years_to_save"] == pytest.approx(400_000 / 50_000)


# ── 2 · Properties ────────────────────────────────────────────────────

PRICES = [500_000.0, 2_000_000.0, 8_000_000.0, 20_000_000.0]
INCOMES = [150_000.0, 400_000.0, 1_200_000.0]
RATES = [-0.005, 0.0, 0.02, 0.05]
MARGINS = [0.0, 0.017, 0.03]


def _grid():
    for p in PRICES:
        for i in INCOMES:
            for r in RATES:
                for m in MARGINS:
                    yield p, i, r, m


@pytest.mark.parametrize("regime", list(REGIMES))
def test_outputs_reconcile_for_every_input(regime: str) -> None:
    """Every derived field must follow from the others, on the whole grid."""
    for p, i, r, m in _grid():
        out = apply_regime(p, i, r, regime, savings_rate=0.10, bank_margin=m)
        assert out["required_cash"] + out["loan_amount"] == pytest.approx(p)
        assert out["annual_total"] == pytest.approx(out["annual_interest"] + out["annual_amort"])
        assert out["monthly_total"] == pytest.approx(out["annual_total"] / 12)
        assert out["residual_income"] == pytest.approx(i - out["annual_total"])
        assert out["ltv"] == pytest.approx(out["loan_amount"] / p)
        assert out["lti"] == pytest.approx(out["loan_amount"] / i)
        for key, value in out.items():
            assert math.isfinite(value), f"{regime} {key} is {value} at {(p, i, r, m)}"


@pytest.mark.parametrize("regime", list(REGIMES))
def test_no_cost_is_ever_negative(regime: str) -> None:
    """A mortgage never pays the borrower. Swedish policy rates were negative from
    2015 to 2019; mortgage rates were not, so the engine floors the effective rate
    at zero rather than crediting interest."""
    for p, i, r, m in _grid():
        out = apply_regime(p, i, r, regime, bank_margin=m)
        assert out["effective_rate"] >= 0
        assert out["annual_interest"] >= 0
        assert out["monthly_total"] >= 0


@pytest.mark.parametrize("regime", list(REGIMES))
def test_cost_rises_with_price_and_rate(regime: str) -> None:
    for i in INCOMES:
        costs = [apply_regime(p, i, 0.03, regime)["monthly_total"] for p in PRICES]
        assert costs == sorted(costs)
        costs = [apply_regime(PRICE, i, r, regime)["monthly_total"] for r in RATES]
        assert costs == sorted(costs)


@pytest.mark.parametrize("regime", list(REGIMES))
def test_more_saving_means_fewer_years(regime: str) -> None:
    years = [
        apply_regime(PRICE, INCOME, RATE, regime, savings_rate=s)["years_to_save"]
        for s in (0.05, 0.10, 0.25)
    ]
    assert years == sorted(years, reverse=True)


def test_regimes_with_the_same_deposit_order_by_strictness() -> None:
    """Same loan, rules only ever added: cost can only rise."""
    for p, i, r, m in _grid():
        res = compare_regimes(p, i, r, bank_margin=m)
        assert (
            res["bolanetak"]["monthly_total"]
            <= res["amort_1"]["monthly_total"]
            <= res["amort_2"]["monthly_total"]
        )


def test_the_2026_relief_lowers_the_deposit_against_every_15_percent_regime() -> None:
    res = compare_regimes(PRICE, INCOME, RATE)
    for key in ("bolanetak", "amort_1", "amort_2"):
        assert res["latt_2026"]["required_cash"] < res[key]["required_cash"]


def test_couple_income_halves_years_and_debt_ratio() -> None:
    """What the page's Par help text promises, checked rather than trusted."""
    single = apply_regime(PRICE, INCOME, RATE, BASELINE_REGIME)
    couple = apply_regime(PRICE, INCOME * 2, RATE, BASELINE_REGIME)
    assert couple["years_to_save"] == pytest.approx(single["years_to_save"] / 2)
    assert couple["lti"] == pytest.approx(single["lti"] / 2)


def test_compare_regimes_is_apply_regime_for_each_key() -> None:
    res = compare_regimes(PRICE, INCOME, RATE, savings_rate=0.12, bank_margin=0.02)
    assert set(res) == set(REGIMES)
    for key, out in res.items():
        assert out == apply_regime(PRICE, INCOME, RATE, key, 0.12, 0.02)


# ── 3 · Inputs are validated rather than silently computed ────────────


@pytest.mark.parametrize(
    "kwargs,fragment",
    [
        ({"price_sek": 0.0}, "price"),
        ({"price_sek": -1.0}, "price"),
        ({"price_sek": float("nan")}, "price"),
        ({"income_sek": 0.0}, "income"),
        ({"income_sek": float("nan")}, "income"),
        ({"rate": float("nan")}, "rate"),
        # 3,46 instead of 0,0346: a percent passed where a decimal belongs.
        ({"rate": 3.46}, "decimal"),
        ({"savings_rate": 0.0}, "savings_rate"),
        ({"savings_rate": 1.5}, "savings_rate"),
        ({"bank_margin": -0.01}, "bank_margin"),
        ({"regime_key": "nope"}, "Unknown regime"),
    ],
)
def test_bad_input_fails_loudly(kwargs: dict, fragment: str) -> None:
    args = {
        "price_sek": PRICE,
        "income_sek": INCOME,
        "rate": RATE,
        "regime_key": BASELINE_REGIME,
        "savings_rate": 0.10,
        "bank_margin": 0.017,
    } | kwargs
    with pytest.raises(ValueError, match=fragment):
        apply_regime(**args)


# ── 4 · Every input the page can produce ──────────────────────────────


def _page_rows() -> list[tuple[str, float, float, float]]:
    """(label, price, individual income, policy rate %) for every selectable row."""
    rows = []
    mun = pd.read_parquet(PROCESSED / "affordability_municipal.parquet")
    for r in mun.itertuples():
        rows.append((f"{r.region_name} {r.year}", r.transaction_price_sek, r.median_income, r.policy_rate))
    county = pd.read_parquet(PROCESSED / "panel_county.parquet")
    # Only years the sidebar offers: the county panel runs from 2011, before
    # the policy-rate series starts, and those rows are unreachable.
    county = county[
        county["year"].isin(selectable_years())
        & county["bostadsratt_price_sek"].notna()
        & county["median_income"].notna()
    ]
    for r in county.itertuples():
        rows.append((f"BR {r.region_name} {r.year}", r.bostadsratt_price_sek, r.median_income, r.policy_rate))
    return rows


def test_every_selectable_row_at_every_control_extreme_is_sane() -> None:
    rows = _page_rows()
    assert len(rows) > 3000, "the artifact sweep found too few rows to mean anything"
    checked = 0
    for label, price, income, rate_pct in rows:
        for earners in (1, 2):
            for savings in (0.05, 0.25):
                for margin in (0.0, 0.03):
                    res = compare_regimes(price, income * earners, rate_pct / 100, savings, margin)
                    for key, out in res.items():
                        for field, value in out.items():
                            assert math.isfinite(value), f"{label} {key} {field}={value}"
                        assert out["monthly_total"] >= 0, f"{label} {key} negative cost"
                        assert out["years_to_save"] >= 0
                        assert 0 <= out["ltv"] <= 1
                    checked += 1
    assert checked == len(rows) * 8


# ── 5 · The figures the audit record quotes ───────────────────────────


def _sek(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def test_the_negative_rate_example_in_the_docs_is_the_engine_s() -> None:
    """APP_GUIDE section 12.1 and ENGINE section 7 quote Stockholm 2017 before and
    after the zero floor. "Before" is the unfloored sum the engine used to apply."""
    mun = pd.read_parquet(PROCESSED / "affordability_municipal.parquet")
    row = mun[(mun["region_name"] == "Stockholm") & (mun["year"] == 2017)].iloc[0]
    rate = row["policy_rate"] / 100
    assert rate < 0, "2017 is quoted as a negative-rate year"

    after = apply_regime(row["transaction_price_sek"], row["median_income"], rate, BASELINE_REGIME)
    before = (after["loan_amount"] * rate + after["annual_amort"]) / 12
    default = apply_regime(
        row["transaction_price_sek"], row["median_income"], rate, BASELINE_REGIME, bank_margin=0.017
    )

    guide = (ROOT / "docs" / "APP_GUIDE.md").read_text(encoding="utf-8")
    engine_doc = (ROOT / "docs" / "ENGINE.md").read_text(encoding="utf-8")
    for figure in (_sek(before), _sek(after["monthly_total"]), _sek(default["monthly_total"])):
        assert figure in guide, f"APP_GUIDE 12.1 no longer quotes {figure}"
    for figure in (_sek(before), _sek(after["monthly_total"])):
        assert figure in engine_doc, f"ENGINE section 7 no longer quotes {figure}"
