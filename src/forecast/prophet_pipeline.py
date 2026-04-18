"""Prophet forecasting pipeline for SHAI.

Forecasts 4 component series per county, then composes into Version C affordability.

Frequency: ANNUAL (11 observations per series, 2014-2024).
Horizon: 6 annual steps (2025-2030).

Per METHODOLOGY_v2.md section 5: Prophet is the default UI model.
Limitation: Prophet is optimized for daily/weekly data; with 11 annual
observations, treat results as indicative trend projections.
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FORECAST_HORIZON = 6  # annual steps
BASE_YEAR = 2014
END_YEAR = 2024  # default; overridden at runtime from the panel's last non-imputed year
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def _resolve_end_year(panel: pd.DataFrame) -> int:
    """Return the last year with actual (non-imputed) data from the panel."""
    actual = panel[~panel.get("is_imputed_income", pd.Series(False, index=panel.index))]
    if len(actual) > 0:
        return int(actual["year"].max())
    return END_YEAR


def _fit_and_forecast(
    series: pd.Series,
    years: pd.Series,
    horizon: int = FORECAST_HORIZON,
    interval_width: float = 0.80,
    end_year: int = END_YEAR,
) -> pd.DataFrame:
    """Fit Prophet on annual data and forecast `horizon` steps ahead.

    Returns DataFrame with columns: target_year, mean, lower_80, upper_80.
    """
    from prophet import Prophet

    # Prophet expects a DataFrame with 'ds' (datetime) and 'y' columns
    df = pd.DataFrame({
        "ds": pd.to_datetime(years.astype(int), format="%Y"),
        "y": series.values,
    })

    # Drop rows where y is NaN
    df = df.dropna(subset=["y"])

    if len(df) < 3:
        logger.warning("Too few observations (%d) for Prophet, returning NaN forecast", len(df))
        future_years = list(range(end_year + 1, end_year + 1 + horizon))
        return pd.DataFrame({
            "target_year": future_years,
            "mean": [np.nan] * horizon,
            "lower_80": [np.nan] * horizon,
            "upper_80": [np.nan] * horizon,
        })

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        m = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=interval_width,
        )
        m.fit(df)

        # Create future dataframe for horizon years
        future_dates = pd.DataFrame({
            "ds": pd.to_datetime(
                [y for y in range(end_year + 1, end_year + 1 + horizon)],
                format="%Y",
            )
        })

        forecast = m.predict(future_dates)

    result = pd.DataFrame({
        "target_year": list(range(end_year + 1, end_year + 1 + horizon)),
        "mean": forecast["yhat"].values,
        "lower_80": forecast["yhat_lower"].values,
        "upper_80": forecast["yhat_upper"].values,
    })

    return result


def forecast_county(
    county_panel: pd.DataFrame,
    county_code: str,
    national_panel: pd.DataFrame,
    end_year: int = END_YEAR,
) -> pd.DataFrame:
    """Forecast all component variables for one county.

    Forecasts:
    - median_income (county-level)
    - transaction_price_sek (county-level)
    - policy_rate (national, same for all counties)
    - cpi_yoy_pct (national, needed for Version C real rate)

    Then composes Version C affordability from the component forecasts.
    """
    county = county_panel[
        (county_panel["lan_code"] == county_code)
        & (county_panel["year"] >= BASE_YEAR)
        & (county_panel["year"] <= end_year)
    ].sort_values("year")

    national = national_panel[
        (national_panel["year"] >= BASE_YEAR)
        & (national_panel["year"] <= end_year)
    ].sort_values("year")

    rows = []

    # 1. Forecast income
    fc_income = _fit_and_forecast(county["median_income"], county["year"], end_year=end_year)
    for _, r in fc_income.iterrows():
        rows.append({
            "county_kod": county_code,
            "target_year": int(r["target_year"]),
            "variable": "income",
            "mean": r["mean"],
            "lower_80": r["lower_80"],
            "upper_80": r["upper_80"],
        })

    # 2. Forecast transaction price
    fc_price = _fit_and_forecast(
        county["transaction_price_sek"], county["year"], end_year=end_year
    )
    for _, r in fc_price.iterrows():
        rows.append({
            "county_kod": county_code,
            "target_year": int(r["target_year"]),
            "variable": "transaction_price_sek",
            "mean": r["mean"],
            "lower_80": r["lower_80"],
            "upper_80": r["upper_80"],
        })

    # 3. Forecast policy rate (national)
    fc_rate = _fit_and_forecast(national["policy_rate"], national["year"], end_year=end_year)
    for _, r in fc_rate.iterrows():
        rows.append({
            "county_kod": county_code,
            "target_year": int(r["target_year"]),
            "variable": "rate",
            "mean": r["mean"],
            "lower_80": r["lower_80"],
            "upper_80": r["upper_80"],
        })

    # 4. Forecast CPI YoY (national, needed for real rate in V.C)
    fc_cpi = _fit_and_forecast(national["cpi_yoy_pct"], national["year"], end_year=end_year)
    for _, r in fc_cpi.iterrows():
        rows.append({
            "county_kod": county_code,
            "target_year": int(r["target_year"]),
            "variable": "cpi_yoy_pct",
            "mean": r["mean"],
            "lower_80": r["lower_80"],
            "upper_80": r["upper_80"],
        })

    df = pd.DataFrame(rows)

    # 5. Compose Version C affordability from component means
    for year in range(end_year + 1, end_year + 1 + FORECAST_HORIZON):
        yr_data = df[df["target_year"] == year]
        income_mean = yr_data.loc[yr_data["variable"] == "income", "mean"].iloc[0]
        price_mean = yr_data.loc[yr_data["variable"] == "transaction_price_sek", "mean"].iloc[0]
        rate_mean = yr_data.loc[yr_data["variable"] == "rate", "mean"].iloc[0]
        cpi_mean = yr_data.loc[yr_data["variable"] == "cpi_yoy_pct", "mean"].iloc[0]

        # Version C: Income / (Price * max(R - pi, 0.005))
        # Rate is in percentage points, convert to decimal
        real_rate = max(rate_mean - cpi_mean, 0.5) / 100.0
        vc_mean = income_mean / (price_mean * real_rate) if price_mean > 0 else np.nan

        # Rough uncertainty propagation: use income and price bounds
        income_lo = yr_data.loc[yr_data["variable"] == "income", "lower_80"].iloc[0]
        income_hi = yr_data.loc[yr_data["variable"] == "income", "upper_80"].iloc[0]
        price_lo = yr_data.loc[yr_data["variable"] == "transaction_price_sek", "lower_80"].iloc[0]
        price_hi = yr_data.loc[yr_data["variable"] == "transaction_price_sek", "upper_80"].iloc[0]

        # Worst case: low income, high price → low affordability
        vc_lower = income_lo / (max(price_hi, 1) * real_rate) if price_hi > 0 else np.nan
        # Best case: high income, low price → high affordability
        vc_upper = income_hi / (max(price_lo, 1) * real_rate) if price_lo > 0 else np.nan

        rows.append({
            "county_kod": county_code,
            "target_year": year,
            "variable": "affordability_c",
            "mean": vc_mean,
            "lower_80": vc_lower,
            "upper_80": vc_upper,
        })

    return pd.DataFrame(rows)


def run_all(
    county_panel: pd.DataFrame | None = None,
    national_panel: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Run Prophet forecasts for all 21 counties.

    Returns combined DataFrame with columns:
    county_kod, target_year, variable, mean, lower_80, upper_80
    """
    if county_panel is None:
        county_panel = pd.read_parquet(DATA_DIR / "panel_county.parquet")
    if national_panel is None:
        national_panel = pd.read_parquet(DATA_DIR / "panel_national.parquet")

    end_year = _resolve_end_year(county_panel)
    logger.info("Forecast training end year: %d", end_year)

    counties = sorted(county_panel["lan_code"].unique())
    logger.info("Running Prophet forecasts for %d counties ...", len(counties))

    frames = []
    for i, code in enumerate(counties):
        logger.info("  [%d/%d] County %s", i + 1, len(counties), code)
        fc = forecast_county(county_panel, code, national_panel, end_year=end_year)
        frames.append(fc)

    result = pd.concat(frames, ignore_index=True)

    # Validate: confidence bands should widen monotonically
    _validate_widening_bands(result)

    return result


def _validate_widening_bands(df: pd.DataFrame) -> None:
    """Check that confidence intervals widen with horizon."""
    violations = 0
    for county in df["county_kod"].unique():
        for var in df["variable"].unique():
            subset = df[(df["county_kod"] == county) & (df["variable"] == var)].sort_values("target_year")
            if len(subset) < 2:
                continue
            widths = (subset["upper_80"] - subset["lower_80"]).values
            for j in range(1, len(widths)):
                if widths[j] < widths[j - 1] - 0.01:  # small tolerance
                    violations += 1

    if violations > 0:
        logger.warning(
            "Confidence band widening check: %d violations found "
            "(bands narrowed at longer horizons). This can happen with "
            "Prophet on very short series.", violations
        )
    else:
        logger.info("Confidence band widening check: PASSED")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    result = run_all()

    out = DATA_DIR / "forecast_prophet.parquet"
    result.to_parquet(out, index=False)
    print(f"\nSaved {out}  ({len(result)} rows)")

    # Summary
    print(f"\nCounties: {result['county_kod'].nunique()}")
    print(f"Variables: {sorted(result['variable'].unique())}")
    print(f"Years: {sorted(result['target_year'].unique())}")
    print(f"Total rows: {len(result)}")

    # Spot check: Stockholm Version C forecast
    sthlm_vc = result[
        (result["county_kod"] == "01") & (result["variable"] == "affordability_c")
    ].sort_values("target_year")
    print("\nStockholm Version C forecast:")
    print(sthlm_vc[["target_year", "mean", "lower_80", "upper_80"]].to_string(index=False))
