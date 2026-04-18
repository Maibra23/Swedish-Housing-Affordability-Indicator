"""ARIMA forecasting pipeline for SHAI.

Same I/O schema as prophet_pipeline.py. Uses pmdarima.auto_arima for
automatic order selection per series.

Frequency: ANNUAL (11 observations per series, 2014-2024).
Horizon: 6 annual steps (2025-2030).

Per METHODOLOGY_v2.md section 5: ARIMA is recommended for inference.
With only 11 observations, auto_arima may select trivial orders like
(0,1,0) (random walk). This is acceptable and documented.
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
    horizon: int = FORECAST_HORIZON,
    alpha: float = 0.20,  # 80% CI
) -> tuple[pd.DataFrame, dict]:
    """Fit auto_arima and forecast `horizon` steps ahead.

    Returns:
        (forecast_df, metadata_dict)
        forecast_df has columns: mean, lower_80, upper_80
        metadata_dict has: order, seasonal_order, aic
    """
    import pmdarima as pm

    values = series.dropna().values

    if len(values) < 3:
        logger.warning("Too few observations (%d), returning NaN forecast", len(values))
        return (
            pd.DataFrame({
                "mean": [np.nan] * horizon,
                "lower_80": [np.nan] * horizon,
                "upper_80": [np.nan] * horizon,
            }),
            {"order": None, "seasonal_order": None, "aic": np.nan},
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = pm.auto_arima(
            values,
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            max_p=3,
            max_q=3,
            max_d=2,
            error_action="ignore",
        )

    fc, conf_int = model.predict(n_periods=horizon, return_conf_int=True, alpha=alpha)

    forecast_df = pd.DataFrame({
        "mean": fc,
        "lower_80": conf_int[:, 0],
        "upper_80": conf_int[:, 1],
    })

    metadata = {
        "order": model.order,
        "seasonal_order": model.seasonal_order,
        "aic": model.aic(),
    }

    return forecast_df, metadata


def forecast_county(
    county_panel: pd.DataFrame,
    county_code: str,
    national_panel: pd.DataFrame,
    end_year: int = END_YEAR,
) -> tuple[pd.DataFrame, list[dict]]:
    """Forecast all component variables for one county.

    Returns (forecast_rows_df, metadata_list).
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

    target_years = list(range(end_year + 1, end_year + 1 + FORECAST_HORIZON))
    rows = []
    meta_rows = []

    variables = [
        ("income", county["median_income"]),
        ("transaction_price_sek", county["transaction_price_sek"]),
        ("rate", national["policy_rate"]),
        ("cpi_yoy_pct", national["cpi_yoy_pct"]),
    ]

    for var_name, series in variables:
        fc_df, meta = _fit_and_forecast(series)
        for i, year in enumerate(target_years):
            rows.append({
                "county_kod": county_code,
                "target_year": year,
                "variable": var_name,
                "mean": fc_df["mean"].iloc[i],
                "lower_80": fc_df["lower_80"].iloc[i],
                "upper_80": fc_df["upper_80"].iloc[i],
            })
        meta_rows.append({
            "county_kod": county_code,
            "variable": var_name,
            "order": str(meta["order"]),
            "seasonal_order": str(meta["seasonal_order"]),
            "aic": meta["aic"],
        })

    df = pd.DataFrame(rows)

    # Compose Version C affordability from component means
    for year in target_years:
        yr_data = df[df["target_year"] == year]
        income_mean = yr_data.loc[yr_data["variable"] == "income", "mean"].iloc[0]
        price_mean = yr_data.loc[yr_data["variable"] == "transaction_price_sek", "mean"].iloc[0]
        rate_mean = yr_data.loc[yr_data["variable"] == "rate", "mean"].iloc[0]
        cpi_mean = yr_data.loc[yr_data["variable"] == "cpi_yoy_pct", "mean"].iloc[0]

        # Version C: Income / (Price * max(R - pi, 0.5pp) / 100)
        real_rate = max(rate_mean - cpi_mean, 0.5) / 100.0
        vc_mean = income_mean / (price_mean * real_rate) if price_mean > 0 else np.nan

        # Rough uncertainty bounds
        income_lo = yr_data.loc[yr_data["variable"] == "income", "lower_80"].iloc[0]
        income_hi = yr_data.loc[yr_data["variable"] == "income", "upper_80"].iloc[0]
        price_lo = yr_data.loc[yr_data["variable"] == "transaction_price_sek", "lower_80"].iloc[0]
        price_hi = yr_data.loc[yr_data["variable"] == "transaction_price_sek", "upper_80"].iloc[0]

        vc_lower = income_lo / (max(price_hi, 1) * real_rate) if price_hi > 0 else np.nan
        vc_upper = income_hi / (max(price_lo, 1) * real_rate) if price_lo > 0 else np.nan

        rows.append({
            "county_kod": county_code,
            "target_year": year,
            "variable": "affordability_c",
            "mean": vc_mean,
            "lower_80": vc_lower,
            "upper_80": vc_upper,
        })

    return pd.DataFrame(rows), meta_rows


def run_all(
    county_panel: pd.DataFrame | None = None,
    national_panel: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run ARIMA forecasts for all 21 counties.

    Returns (forecast_df, metadata_df).
    """
    if county_panel is None:
        county_panel = pd.read_parquet(DATA_DIR / "panel_county.parquet")
    if national_panel is None:
        national_panel = pd.read_parquet(DATA_DIR / "panel_national.parquet")

    end_year = _resolve_end_year(county_panel)
    logger.info("Forecast training end year: %d", end_year)

    counties = sorted(county_panel["lan_code"].unique())
    logger.info("Running ARIMA forecasts for %d counties ...", len(counties))

    all_forecasts = []
    all_meta = []

    for i, code in enumerate(counties):
        logger.info("  [%d/%d] County %s", i + 1, len(counties), code)
        fc, meta = forecast_county(county_panel, code, national_panel, end_year=end_year)
        all_forecasts.append(fc)
        all_meta.extend(meta)

    result = pd.concat(all_forecasts, ignore_index=True)
    metadata = pd.DataFrame(all_meta)

    _validate_widening_bands(result)

    return result, metadata


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
                if widths[j] < widths[j - 1] - 0.01:
                    violations += 1

    if violations > 0:
        logger.warning("CI widening check: %d violations", violations)
    else:
        logger.info("CI widening check: PASSED")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    result, metadata = run_all()

    out_fc = DATA_DIR / "forecast_arima.parquet"
    out_meta = DATA_DIR / "arima_metadata.parquet"
    result.to_parquet(out_fc, index=False)
    metadata.to_parquet(out_meta, index=False)

    print(f"\nSaved {out_fc}  ({len(result)} rows)")
    print(f"Saved {out_meta}  ({len(metadata)} rows)")

    # Print selected orders for transparency
    print("\nSelected ARIMA orders:")
    for _, row in metadata.iterrows():
        print(f"  {row['county_kod']} / {row['variable']:30s}  order={row['order']}  AIC={row['aic']:.1f}")

    # Spot check
    sthlm_vc = result[
        (result["county_kod"] == "01") & (result["variable"] == "affordability_c")
    ].sort_values("target_year")
    print("\nStockholm Version C forecast (ARIMA):")
    print(sthlm_vc[["target_year", "mean", "lower_80", "upper_80"]].to_string(index=False))
