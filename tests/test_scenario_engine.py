"""Quality checks on the scenario simulator, before it is trusted in production.

The simulator re-implements Version C as a scalar function rather than calling
`compute_version_c`, so the first thing worth proving is that the two agree on
every county-year the page can select. A silent divergence would mean Sida 05's
baseline is not the number every other page shows.

Then the behaviour the page teaches: only R - pi reaches the formula, the floor
at 0,5 pp makes rate moves below it inert, and income and price act
proportionally. Finally, inputs that would otherwise return a confident wrong
number are refused.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from src.indices.affordability import compute_version_c
from src.scenario.simulator import simulate

ROOT = Path(__file__).resolve().parents[1]
COUNTY = ROOT / "data" / "processed" / "panel_county.parquet"

BASE = {
    "income": 500_000.0,
    "transaction_price_sek": 5_000_000.0,
    "policy_rate": 4.0,   # pp
    "cpi_yoy_pct": 1.0,   # pp  → real rate 3,0 pp, above the floor
}


def _run(**shocks) -> dict:
    args = {"rate_shock": 0.0, "income_shock": 0.0, "price_shock": 0.0, "cpi_shock": 0.0} | shocks
    return simulate(county_kod="01", baseline_panel=BASE, **args)


# ── 1 · Agreement with the index every other page shows ──────────────


@pytest.fixture(scope="module")
def county() -> pd.DataFrame:
    return pd.read_parquet(COUNTY).dropna(
        subset=["median_income", "transaction_price_sek", "policy_rate", "cpi_yoy_pct"]
    )


def test_baseline_equals_compute_version_c_on_every_county_year(county: pd.DataFrame) -> None:
    expected = compute_version_c(county)
    assert len(county) >= 21 * 10
    for (_, row), want in zip(county.iterrows(), expected):
        got = simulate(
            county_kod=row["lan_code"],
            rate_shock=0.0,
            income_shock=0.0,
            price_shock=0.0,
            baseline_panel={
                "income": row["median_income"],
                "transaction_price_sek": row["transaction_price_sek"],
                "policy_rate": row["policy_rate"],
                "cpi_yoy_pct": row["cpi_yoy_pct"],
            },
        )
        assert got["baseline_v_c"] == pytest.approx(want, rel=1e-12), (
            f"{row['region_name']} {row['year']}"
        )
        assert got["delta"] == 0


# ── 2 · The behaviour the page teaches ───────────────────────────────


def test_no_shock_is_no_change() -> None:
    r = _run()
    assert r["scenario_v_c"] == r["baseline_v_c"]
    assert r["delta_pct"] == 0


@pytest.mark.parametrize("shift", [-1.0, 1.0, 2.5, 5.0])
def test_equal_rate_and_inflation_shocks_cancel(shift: float) -> None:
    """The page's central claim: only R - pi reaches the formula."""
    r = _run(rate_shock=shift, cpi_shock=shift)
    assert r["scenario_v_c"] == pytest.approx(r["baseline_v_c"])


def test_index_is_inversely_proportional_to_the_real_rate_above_the_floor() -> None:
    r = _run(rate_shock=3.0)  # real rate 3 → 6 pp
    assert r["real_rate_scen"] == pytest.approx(6.0)
    assert r["scenario_v_c"] == pytest.approx(r["baseline_v_c"] / 2)


def test_income_and_price_act_proportionally() -> None:
    assert _run(income_shock=0.10)["delta_pct"] == pytest.approx(10.0)
    assert _run(price_shock=-0.20)["delta_pct"] == pytest.approx(25.0)


def test_the_floor_makes_rate_moves_below_it_inert() -> None:
    """With R - pi at -5 pp, the whole slider range stays under 0,5 pp — the 2023
    case the reading guide documents."""
    base = BASE | {"policy_rate": 3.46, "cpi_yoy_pct": 8.65}
    for shock in (-2.0, 0.0, 2.0, 5.0):
        r = simulate("01", shock, 0.0, 0.0, base)
        assert r["real_rate_scen"] == 0.5
        assert r["scenario_v_c"] == r["baseline_v_c"]


def test_the_floor_caps_the_improvement_from_falling_rates() -> None:
    r = _run(rate_shock=-10.0)
    assert r["real_rate_scen"] == 0.5
    assert r["scenario_v_c"] == pytest.approx(r["baseline_v_c"] * 3.0 / 0.5)


def test_higher_rates_never_improve_affordability() -> None:
    values = [_run(rate_shock=s)["scenario_v_c"] for s in (-2, -1, 0, 1, 2, 3, 4, 5)]
    assert values == sorted(values, reverse=True)


def test_reported_fields_reconcile() -> None:
    r = _run(rate_shock=1.0, income_shock=0.05, price_shock=-0.10, cpi_shock=2.0)
    assert r["scenario_income"] == pytest.approx(BASE["income"] * 1.05)
    assert r["scenario_price"] == pytest.approx(BASE["transaction_price_sek"] * 0.90)
    assert r["scenario_rate"] == pytest.approx(5.0)
    assert r["scenario_cpi"] == pytest.approx(3.0)
    assert r["delta"] == pytest.approx(r["scenario_v_c"] - r["baseline_v_c"])
    assert r["delta_pct"] == pytest.approx(r["delta"] / r["baseline_v_c"] * 100)


def test_every_slider_extreme_on_every_county_year_is_finite(county: pd.DataFrame) -> None:
    """The page's slider ranges: rate -2..5, income -10..10 %, price -25..25 %,
    CPI -5..10."""
    corners = [
        (rate, inc, price, cpi)
        for rate in (-2.0, 5.0)
        for inc in (-0.10, 0.10)
        for price in (-0.25, 0.25)
        for cpi in (-5.0, 10.0)
    ]
    for _, row in county.iterrows():
        base = {
            "income": row["median_income"],
            "transaction_price_sek": row["transaction_price_sek"],
            "policy_rate": row["policy_rate"],
            "cpi_yoy_pct": row["cpi_yoy_pct"],
        }
        for rate, inc, price, cpi in corners:
            r = simulate(row["lan_code"], rate, inc, price, base, cpi)
            assert math.isfinite(r["scenario_v_c"]) and r["scenario_v_c"] > 0
            assert r["real_rate_scen"] >= 0.5


# ── 3 · Inputs are validated rather than silently computed ────────────


@pytest.mark.parametrize(
    "panel_override,shocks,fragment",
    [
        ({"income": 0.0}, {}, "income"),
        ({"income": float("nan")}, {}, "income"),
        ({"transaction_price_sek": 0.0}, {}, "price"),
        ({"transaction_price_sek": -1.0}, {}, "price"),
        ({"policy_rate": float("nan")}, {}, "policy_rate"),
        ({"cpi_yoy_pct": float("nan")}, {}, "cpi_yoy_pct"),
        ({}, {"income_shock": -1.0}, "income_shock"),
        ({}, {"price_shock": -1.0}, "price_shock"),
        ({}, {"rate_shock": float("nan")}, "rate_shock"),
    ],
)
def test_bad_input_fails_loudly(panel_override: dict, shocks: dict, fragment: str) -> None:
    args = {"rate_shock": 0.0, "income_shock": 0.0, "price_shock": 0.0, "cpi_shock": 0.0} | shocks
    with pytest.raises(ValueError, match=fragment):
        simulate(county_kod="01", baseline_panel=BASE | panel_override, **args)
