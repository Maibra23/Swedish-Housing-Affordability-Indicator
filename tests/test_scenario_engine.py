"""Quality checks on the scenario simulator, before it is trusted in production.

The simulator computes Version C for one county as a scalar function rather than
calling `compute_version_c`, so the first thing worth proving is that the two
agree on every county-year the page can select. A silent divergence would mean
Sida 05's baseline is not the number every other page shows.

Then the behaviour the page teaches: the rate acts through its interest term
only, so equal rate steps move the cost by equal amounts and amortisation
dampens the relative effect; income and price act proportionally. Finally,
inputs that would otherwise return a confident wrong number are refused.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from src.indices.affordability import complete_case, compute_version_c, scorable_rows
from src.indices.cost_model import cost_share
from src.scenario.simulator import MIN_SCENARIO_RATE, simulate

ROOT = Path(__file__).resolve().parents[1]
COUNTY = ROOT / "data" / "processed" / "panel_county.parquet"

BASE = {
    "income": 500_000.0,
    "transaction_price_sek": 5_000_000.0,
    "mortgage_rate": 4.0,
    "year": 2024,
}


def _run(**shocks) -> dict:
    args = {"rate_shock": 0.0, "income_shock": 0.0, "price_shock": 0.0} | shocks
    return simulate(county_kod="01", baseline_panel=BASE, **args)


def _base(row: pd.Series) -> dict:
    return {
        "income": row["median_income"],
        "transaction_price_sek": row["transaction_price_sek"],
        "mortgage_rate": row["mortgage_rate"],
        "year": row["year"],
    }


# ── 1 · Agreement with the index every other page shows ──────────────


@pytest.fixture(scope="module")
def county() -> pd.DataFrame:
    return scorable_rows(complete_case(pd.read_parquet(COUNTY)))


def test_baseline_equals_compute_version_c_on_every_county_year(county: pd.DataFrame) -> None:
    expected = compute_version_c(county)
    assert len(county) == 21 * 11
    for (_, row), want in zip(county.iterrows(), expected):
        got = simulate(row["lan_code"], 0.0, 0.0, 0.0, _base(row))
        assert got["baseline_v_c"] == pytest.approx(want, rel=1e-12), (
            f"{row['region_name']} {row['year']}"
        )
        assert got["delta"] == 0


# ── 2 · The behaviour the page teaches ───────────────────────────────


def test_no_shock_is_no_change() -> None:
    r = _run()
    assert r["scenario_v_c"] == r["baseline_v_c"]
    assert r["delta_pct"] == 0


def test_equal_rate_steps_move_the_cost_by_equal_amounts() -> None:
    """Linear in the rate, where the old reciprocal of the real rate was not."""
    steps = [_run(rate_shock=s)["scenario_v_c"] for s in (0.0, 1.0, 2.0, 3.0)]
    gaps = [b - a for a, b in zip(steps, steps[1:])]
    assert gaps == pytest.approx([gaps[0]] * 3)


def test_two_points_on_four_percent_is_the_interest_term_alone() -> None:
    """+2 pp adds 2 × 0,7 % of the loan, and amortisation does not move."""
    r = _run(rate_shock=2.0)
    loan_per_income = 0.85 * BASE["transaction_price_sek"] / (2 * BASE["income"])
    assert r["delta"] == pytest.approx(100 * loan_per_income * 0.02 * 0.7)
    # 4 % × 0,7 + 2 % amortisation = 4,8 % of the loan; +1,4 makes 6,2.
    assert r["delta_pct"] == pytest.approx((6.2 / 4.8 - 1) * 100)


def test_income_and_price_act_proportionally() -> None:
    """A cost share: 10 % more income is 1/1,1 of the cost; 20 % lower prices 0,8."""
    assert _run(income_shock=0.10)["delta_pct"] == pytest.approx((1 / 1.1 - 1) * 100)
    assert _run(price_shock=-0.20)["delta_pct"] == pytest.approx(-20.0)


def test_higher_rates_never_lower_the_cost() -> None:
    values = [_run(rate_shock=s)["scenario_v_c"] for s in (-2, -1, 0, 1, 2, 3, 4, 5)]
    assert values == sorted(values)


def test_a_rate_pushed_below_the_minimum_is_held_there_and_says_so() -> None:
    r = _run(rate_shock=-5.0)
    assert r["scenario_rate"] == MIN_SCENARIO_RATE
    assert r["rate_held_at_minimum"]
    assert r["scenario_v_c"] == pytest.approx(
        cost_share(BASE["income"], BASE["transaction_price_sek"], MIN_SCENARIO_RATE, 2024)
    )
    assert not _run(rate_shock=-2.0)["rate_held_at_minimum"]


def test_reported_fields_reconcile() -> None:
    r = _run(rate_shock=1.0, income_shock=0.05, price_shock=-0.10)
    assert r["scenario_income"] == pytest.approx(BASE["income"] * 1.05)
    assert r["scenario_price"] == pytest.approx(BASE["transaction_price_sek"] * 0.90)
    assert r["scenario_rate"] == pytest.approx(5.0)
    assert r["delta"] == pytest.approx(r["scenario_v_c"] - r["baseline_v_c"])
    assert r["delta_pct"] == pytest.approx(r["delta"] / r["baseline_v_c"] * 100)


def test_every_slider_extreme_on_every_county_year_is_finite(county: pd.DataFrame) -> None:
    """The page's slider ranges: rate -2..5, income -10..10 %, price -25..25 %."""
    corners = [
        (rate, inc, price)
        for rate in (-2.0, 5.0)
        for inc in (-0.10, 0.10)
        for price in (-0.25, 0.25)
    ]
    for _, row in county.iterrows():
        for rate, inc, price in corners:
            r = simulate(row["lan_code"], rate, inc, price, _base(row))
            assert math.isfinite(r["scenario_v_c"]) and r["scenario_v_c"] > 0


# ── 3 · Inputs are validated rather than silently computed ────────────


@pytest.mark.parametrize(
    "panel_override,shocks,fragment",
    [
        ({"income": 0.0}, {}, "income"),
        ({"income": float("nan")}, {}, "income"),
        ({"transaction_price_sek": 0.0}, {}, "price"),
        ({"transaction_price_sek": -1.0}, {}, "price"),
        ({"mortgage_rate": float("nan")}, {}, "mortgage_rate"),
        ({"mortgage_rate": 0.0}, {}, "mortgage_rate"),
        ({}, {"income_shock": -1.0}, "income_shock"),
        ({}, {"price_shock": -1.0}, "price_shock"),
        ({}, {"rate_shock": float("nan")}, "rate_shock"),
    ],
)
def test_bad_input_fails_loudly(panel_override: dict, shocks: dict, fragment: str) -> None:
    args = {"rate_shock": 0.0, "income_shock": 0.0, "price_shock": 0.0} | shocks
    with pytest.raises(ValueError, match=fragment):
        simulate(county_kod="01", baseline_panel=BASE | panel_override, **args)


def test_the_stockholm_figure_in_the_readme(county: pd.DataFrame) -> None:
    """README quotes Stockholms län's 2024 baseline and its +2 pp scenario."""
    row = county[(county["lan_code"] == "01") & (county["year"] == 2024)].iloc[0]
    r = simulate("01", 2.0, 0.0, 0.0, _base(row))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"**{r['baseline_v_c']:.1f}".replace(".", ",") in readme
    assert f"**{r['scenario_v_c']:.1f}".replace(".", ",") in readme
    assert f"up {r['delta_pct']:.0f} %" in readme
