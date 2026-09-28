"""The conditional projection, and the identity it rests on.

Version C is a reciprocal of the real interest rate, floored at 0,5 pp. In the
committed panel that floor binds in 9 of 11 years, during which Version C is
exactly 200 x (income / price) and the rate contributes nothing. The real rate
carries 99 % of the variance in year-on-year changes of log C.

That is why nothing here extrapolates it. Income and price are carried forward at
documented rates; the real rate is a stated scenario. These tests pin the
arithmetic and, more importantly, the property that made the withdrawn pipelines
unusable: no input can produce an absurd output.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.projection import (
    HORIZON,
    INCOME_GROWTH,
    PRICE_GROWTH,
    REAL_RATE_FLOOR,
    SCENARIO_KEYS,
    project_all,
    project_county,
    scenario_real_rates,
)

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "affordability_county.parquet"


def test_at_the_floor_version_c_is_two_hundred_times_income_over_price() -> None:
    """The identity the whole design rests on.

    While the floor binds, the rate drops out of the formula entirely:
    C = I / (P * 0.005) = 200 * I / P. If this ever fails, either the floor
    moved or the formula did, and the projection's premise needs revisiting.
    """
    out = project_county(
        last_income=400_000.0, last_price=8_000_000.0, last_year=2024,
        real_rate_pp=REAL_RATE_FLOOR, horizon=1,
    )
    row = out.iloc[0]
    assert row["version_c"] == pytest.approx(200 * row["income"] / row["price"])


def test_growth_compounds_from_the_last_observed_year() -> None:
    out = project_county(
        last_income=100.0, last_price=1000.0, last_year=2024,
        real_rate_pp=1.0, horizon=3,
    )
    assert out["target_year"].tolist() == [2025, 2026, 2027]
    assert out["income"].tolist() == pytest.approx(
        [100 * (1 + INCOME_GROWTH) ** n for n in (1, 2, 3)]
    )
    assert out["price"].tolist() == pytest.approx(
        [1000 * (1 + PRICE_GROWTH) ** n for n in (1, 2, 3)]
    )


def test_version_c_is_a_reciprocal_of_the_real_rate() -> None:
    """Doubling the real rate halves affordability. This is the sensitivity that
    made an extrapolated denominator unusable."""
    common = dict(last_income=400_000.0, last_price=8_000_000.0, last_year=2024, horizon=1)
    low = project_county(real_rate_pp=1.0, **common).iloc[0]["version_c"]
    high = project_county(real_rate_pp=2.0, **common).iloc[0]["version_c"]
    assert high == pytest.approx(low / 2)


def test_a_real_rate_below_the_floor_is_refused() -> None:
    """The floor is part of the formula, not a display convention. Accepting a
    lower rate here would silently publish a value the index cannot produce."""
    with pytest.raises(ValueError, match="floor"):
        project_county(
            last_income=400_000.0, last_price=8_000_000.0, last_year=2024,
            real_rate_pp=0.1, horizon=1,
        )


def test_scenarios_carry_the_floor_and_the_observed_rate() -> None:
    rates = scenario_real_rates(0.77)
    assert set(rates) == set(SCENARIO_KEYS)
    assert rates["floor"] == REAL_RATE_FLOOR
    assert rates["current"] == 0.77
    assert rates["normalised"] == 2.0


def test_an_observed_rate_under_the_floor_is_raised_to_it() -> None:
    """`current` is read from data, and the data can sit below the floor."""
    assert scenario_real_rates(0.2)["current"] == REAL_RATE_FLOOR


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
    """Holding the real rate at today's level should reproduce roughly today's
    value, moved only by the income and price growth assumptions."""
    out = project_all(county_panel)
    last = county_panel[county_panel["year"] == county_panel["year"].max()]
    last = last.set_index("lan_code")["version_c"]
    first = out[(out["scenario"] == "current") & (out["target_year"] == out["target_year"].min())]
    ratio = first["version_c"].to_numpy() / last.loc[first["lan_code"]].to_numpy()
    assert ratio.min() > 0.9 and ratio.max() < 1.15


def test_the_floor_scenario_is_the_most_affordable(county_panel: pd.DataFrame) -> None:
    """Lower real rate, higher Version C. If this inverts, the orientation
    contract has been broken somewhere."""
    out = project_all(county_panel)
    wide = out.pivot_table(index=["lan_code", "target_year"], columns="scenario", values="version_c")
    assert (wide["floor"] > wide["normalised"]).all()


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
