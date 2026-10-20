"""The conditional projection, and the identity it rests on.

Version C is a cash-flow share and is linear in the mortgage rate: the interest
term scales with it, amortisation does not. The rate is a policy outcome, not a
trend, so nothing here extrapolates it. Income and price are carried forward at
documented rates; the mortgage rate is a stated scenario. These tests pin the
arithmetic and, more importantly, the property that made the withdrawn pipelines
unusable: no input can produce an absurd output.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.indices.cost_model import cost_share
from src.projection import (
    HIGH_MORTGAGE_RATE,
    HORIZON,
    INCOME_GROWTH,
    PRICE_GROWTH,
    SCENARIO_KEYS,
    project_all,
    project_county,
    scenario_mortgage_rates,
)

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "affordability_county.parquet"


def test_a_projected_year_is_the_cost_model_on_projected_inputs() -> None:
    """The identity the design rests on: the projection is Version C applied to
    carried-forward income and price, with nothing else in between."""
    out = project_county(
        last_income=400_000.0, last_price=8_000_000.0, last_year=2024,
        mortgage_rate=4.0, horizon=1,
    )
    row = out.iloc[0]
    assert row["version_c"] == pytest.approx(cost_share(row["income"], row["price"], 4.0, 2025))


def test_growth_compounds_from_the_last_observed_year() -> None:
    out = project_county(
        last_income=100.0, last_price=1000.0, last_year=2024,
        mortgage_rate=1.0, horizon=3,
    )
    assert out["target_year"].tolist() == [2025, 2026, 2027]
    assert out["income"].tolist() == pytest.approx(
        [100 * (1 + INCOME_GROWTH) ** n for n in (1, 2, 3)]
    )
    assert out["price"].tolist() == pytest.approx(
        [1000 * (1 + PRICE_GROWTH) ** n for n in (1, 2, 3)]
    )


def test_version_c_is_linear_in_the_rate() -> None:
    """Equal rate steps move the cost by equal amounts. This is what makes a
    stated rate safe to project, where the old reciprocal was not."""
    common = dict(last_income=400_000.0, last_price=8_000_000.0, last_year=2024, horizon=1)
    c2, c4, c6 = (
        project_county(mortgage_rate=r, **common).iloc[0]["version_c"] for r in (2.0, 4.0, 6.0)
    )
    assert c6 - c4 == pytest.approx(c4 - c2)
    assert c2 < c4 < c6


def test_a_rate_that_is_not_positive_is_refused() -> None:
    with pytest.raises(ValueError, match="mortgage_rate"):
        project_county(
            last_income=400_000.0, last_price=8_000_000.0, last_year=2024,
            mortgage_rate=0.0, horizon=1,
        )


def test_scenarios_are_the_lowest_the_latest_and_the_stress_rate() -> None:
    rates = scenario_mortgage_rates(pd.Series([2.5, 1.5, 4.5, 4.3]))
    assert list(rates) == list(SCENARIO_KEYS)
    assert rates == {"low": 1.5, "current": 4.3, "high": HIGH_MORTGAGE_RATE}


@pytest.fixture(scope="module")
def county_panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


def test_every_county_and_scenario_is_projected(county_panel: pd.DataFrame) -> None:
    out = project_all(county_panel)
    assert out["lan_code"].nunique() == 21
    assert set(out["scenario"]) == set(SCENARIO_KEYS)
    per_series = out.groupby(["lan_code", "scenario"]).size()
    assert (per_series == HORIZON).all()


def test_no_projection_is_absurd(county_panel: pd.DataFrame) -> None:
    """The property the withdrawn pipelines could not hold.

    The withdrawn pipelines put 21 of 21 counties outside 0,5x..2x of their last
    observed value in the first projected year. Nothing here is fitted, so nothing
    can. See R16.
    """
    out = project_all(county_panel)
    last = county_panel[county_panel["year"] == county_panel["year"].max()]
    last = last.set_index("lan_code")["version_c"]
    first = out[out["target_year"] == out["target_year"].min()]
    ratio = first["version_c"].to_numpy() / last.loc[first["lan_code"]].to_numpy()
    assert np.isfinite(ratio).all(), "a projection produced inf or NaN"
    assert (ratio > 0.25).all() and (ratio < 4.0).all(), (
        f"projection ratios run {ratio.min():.2f}x to {ratio.max():.2f}x"
    )


def test_the_current_scenario_barely_moves(county_panel: pd.DataFrame) -> None:
    """Holding the rate at today's level should reproduce roughly today's
    value, moved only by the income and price growth assumptions."""
    out = project_all(county_panel)
    last = county_panel[county_panel["year"] == county_panel["year"].max()]
    last = last.set_index("lan_code")["version_c"]
    first = out[(out["scenario"] == "current") & (out["target_year"] == out["target_year"].min())]
    ratio = first["version_c"].to_numpy() / last.loc[first["lan_code"]].to_numpy()
    assert ratio.min() > 0.9 and ratio.max() < 1.1


def test_the_low_scenario_is_the_cheapest(county_panel: pd.DataFrame) -> None:
    """Lower rate, lower cost share. If this inverts, the orientation contract
    has been broken somewhere."""
    out = project_all(county_panel)
    wide = out.pivot_table(index=["lan_code", "target_year"], columns="scenario", values="version_c")
    assert ((wide["low"] < wide["current"]) & (wide["current"] < wide["high"])).all()


def test_the_committed_projection_matches_the_committed_panel(
    county_panel: pd.DataFrame,
) -> None:
    """The artifact the page reads must be the one this module produces.

    Nothing is fitted, so this is a pure function of the panel: if the two
    disagree, the artifact is stale and the refresh needs re-running.
    """
    artifact = ROOT / "data" / "processed" / "projection.parquet"
    assert artifact.exists(), "run: python3.11 scripts/refresh_data.py --no-fetch"

    stored = pd.read_parquet(artifact).sort_values(
        ["lan_code", "scenario", "target_year"]
    ).reset_index(drop=True)
    fresh = project_all(county_panel).sort_values(
        ["lan_code", "scenario", "target_year"]
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(stored, fresh, check_dtype=False, rtol=1e-9)
