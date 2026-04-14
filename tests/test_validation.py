"""Validation suite per METHODOLOGY.md section 9 (Task 2.4).

These tests validate the built data and computed affordability indices.
All checks must pass before proceeding to Day 3.
"""

import pandas as pd
import pytest
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture
def municipal_panel():
    return pd.read_parquet(DATA_DIR / "panel_municipal.parquet")


@pytest.fixture
def affordability():
    return pd.read_parquet(DATA_DIR / "affordability_municipal.parquet")


@pytest.fixture
def ranked():
    return pd.read_parquet(DATA_DIR / "affordability_ranked.parquet")


@pytest.fixture
def county_panel():
    return pd.read_parquet(DATA_DIR / "panel_county.parquet")


@pytest.fixture
def affordability_county():
    return pd.read_parquet(DATA_DIR / "affordability_county.parquet")


# -----------------------------------------------------------------------
# Check 1: Median income increases nominally year over year
# -----------------------------------------------------------------------
def test_income_monotonic_nominal(municipal_panel):
    """National median income should generally increase year over year nominally."""
    national_income = (
        municipal_panel[~municipal_panel["is_imputed_income"]]
        .groupby("year")["median_income"]
        .median()
        .sort_index()
    )
    # Allow at most 3 year-over-year decreases (recessions, inflation shocks)
    diffs = national_income.diff().dropna()
    decreases = (diffs < 0).sum()
    assert decreases <= 3, (
        f"Median income decreased in {decreases} years (expected <= 3): "
        f"{diffs[diffs < 0].to_dict()}"
    )


# -----------------------------------------------------------------------
# Check 2: Real income roughly stable or slowly rising
# -----------------------------------------------------------------------
def test_real_income_stable(municipal_panel):
    """Real income (deflated by CPI) should not swing more than +/-30% over the period."""
    df = municipal_panel[
        (municipal_panel["year"] >= 2014) & (municipal_panel["year"] <= 2024)
    ].copy()
    agg = df.groupby("year").agg(
        income=("median_income", "median"),
        cpi=("cpi_index", "first"),
    )
    # Deflate to base year (2020=100)
    agg["real_income"] = agg["income"] / (agg["cpi"] / 100)
    min_real = agg["real_income"].min()
    max_real = agg["real_income"].max()
    ratio = max_real / min_real
    assert ratio < 1.35, f"Real income swung too much: ratio {ratio:.2f}"


# -----------------------------------------------------------------------
# Check 3: Stockholm worst under Version C (transaction price fix)
# -----------------------------------------------------------------------
def test_stockholm_worst_v_c(ranked):
    """Stockholm county (lan_code '01') should be in top 5 worst under V.C.

    After using transaction_price_sek (absolute price level in SEK),
    Stockholm's high housing costs correctly place it among the least
    affordable counties.
    """
    county_vc = ranked.groupby("lan_code")["version_c"].median()
    worst_5 = county_vc.nsmallest(5).index.tolist()
    assert "01" in worst_5, (
        f"Stockholm county (01) not in top 5 worst Version C. "
        f"Worst 5 counties: {worst_5}. "
        f"Check that transaction_price_sek is populated correctly."
    )


def test_skane_worst_v_c(ranked):
    """Skane county (lan_code '12') should be in top 5 worst under V.C."""
    county_vc = ranked.groupby("lan_code")["version_c"].median()
    worst_5 = county_vc.nsmallest(5).index.tolist()
    assert "12" in worst_5, (
        f"Skane county (12) not in top 5 worst Version C. "
        f"Worst 5 counties: {worst_5}"
    )


# -----------------------------------------------------------------------
# Check 4: Norrbotten in top 5 best under Version A
# -----------------------------------------------------------------------
def test_norrbotten_best_v_a(ranked):
    """Norrbotten county (lan_code '25') should be in top 5 best under V.A."""
    county_va = ranked.groupby("lan_code")["version_a"].median()
    best_5 = county_va.nlargest(5).index.tolist()
    assert "25" in best_5, (
        f"Norrbotten county (25) not in top 5 best Version A. "
        f"Best 5 counties: {best_5}"
    )


# -----------------------------------------------------------------------
# Check 5: K/T values between 1.0 and 4.0
# -----------------------------------------------------------------------
def test_kt_range(municipal_panel):
    """All K/T values should be between 1.0 and 4.0."""
    kt = municipal_panel["kt_ratio"].dropna()
    assert kt.min() >= 1.0, f"K/T too low: {kt.min():.2f}"
    assert kt.max() <= 4.0, f"K/T too high: {kt.max():.2f}"


# -----------------------------------------------------------------------
# Check 6: Transaction price ordering sanity
# -----------------------------------------------------------------------
def test_transaction_price_ordering(county_panel):
    """Stockholm median transaction price should be at least 2.5x Norrbotten.

    This is the direct sanity check that feeds the affordability formulas.
    """
    latest_year = county_panel[county_panel["transaction_price_sek"].notna()]["year"].max()
    latest = county_panel[county_panel["year"] == latest_year]
    stockholm = latest[latest["lan_code"] == "01"]["transaction_price_sek"].iloc[0]
    norrbotten = latest[latest["lan_code"] == "25"]["transaction_price_sek"].iloc[0]
    ratio = stockholm / norrbotten
    assert ratio >= 2.5, (
        f"Stockholm ({stockholm/1e6:.2f} MSEK) / Norrbotten ({norrbotten/1e6:.2f} MSEK) "
        f"ratio is {ratio:.2f}x, expected >= 2.5x. Check transaction_price_sek data."
    )


# -----------------------------------------------------------------------
# Check 7: Forecast intervals widen (placeholder — run after Day 3)
# -----------------------------------------------------------------------
@pytest.mark.skip(reason="Run after Day 3 when forecast data exists")
def test_forecast_intervals_widen():
    """Confidence bands should widen monotonically with horizon."""
    pass
