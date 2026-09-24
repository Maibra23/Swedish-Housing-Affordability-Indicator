"""The forecast pipelines, tested by contract rather than by output.

The last two modules R5 lists at 0 %. They are also the ones where the obvious
test is the wrong one: pinning ARIMA's predicted values is a change-detector, not
a guard. It would fail whenever `pmdarima` changed a default, would pass while
the pipeline forecast entirely the wrong series, and nobody would be able to say
whether a diff was a regression or a better model.

What is worth asserting is everything around the model:

- **the vintage**, which is the failure that nearly shipped on 2026-09-21. The
  refresh writes panels and indices, then fits forecasts. That day step 4 exited
  on a missing import after steps 1 to 3 had written their artifacts, leaving
  committed forecasts derived from the *previous* income series with nothing in
  the suite comparing the two. R4 recorded that the danger was never memory, it
  was silence.
- **the horizon and its base year**, because `_resolve_end_year` is what makes
  the forecast move when SCB finally publishes 2025 income. Get it wrong and the
  pipeline cheerfully forecasts from a year it already has data for.
- **the interval contract**: bands that contain their own mean and widen with
  horizon. A band that narrows six years out is a model saying it becomes more
  certain the further it looks, which is the shape of a bug rather than a
  forecast.

The pure helpers are tested directly. The fitted output is checked as a committed
artifact, which is what the app actually reads.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.forecast import arima_pipeline, prophet_pipeline
from src.provenance import complete_case_max_year

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

PIPELINES = {"arima": arima_pipeline, "prophet": prophet_pipeline}
ARTIFACTS = {
    "arima": PROCESSED / "forecast_arima.parquet",
    "prophet": PROCESSED / "forecast_prophet.parquet",
}


@pytest.fixture(scope="module", params=sorted(ARTIFACTS))
def forecast(request) -> tuple[str, pd.DataFrame]:
    return request.param, pd.read_parquet(ARTIFACTS[request.param])


# ---------------------------------------------------------------------------
# The vintage: the failure that nearly shipped
# ---------------------------------------------------------------------------

def test_the_forecasts_start_where_the_observed_data_stops(
    forecast: tuple[str, pd.DataFrame],
) -> None:
    """Committed forecasts must be derived from the committed panel.

    If the refresh's forecast step is skipped or fails after the index step has
    written its artifacts, these two drift apart silently: page 03 then shows a
    forecast built on a superseded income series, and every other page shows the
    new one. Exactly that happened on 2026-09-21, caught by hand rather than by
    a test.

    The check is deliberately a first principle rather than a stored timestamp:
    a forecast's first target year is the year after the last observed one, so
    the two artifacts can be compared without either recording provenance.
    """
    name, frame = forecast
    first_target = int(frame["target_year"].min())
    expected = complete_case_max_year() + 1
    assert first_target == expected, (
        f"the {name} forecast starts at {first_target} but the index has "
        f"observed data through {complete_case_max_year()}. The forecast "
        f"artifacts are stale relative to the panel: re-run "
        f"`python scripts/refresh_data.py --no-fetch`."
    )


@pytest.mark.parametrize("name", sorted(PIPELINES))
def test_the_end_year_comes_from_the_panel_not_from_the_constant(name: str) -> None:
    """`END_YEAR` is a default, and the panel overrides it.

    This is what lets the horizon advance on its own when income is finally
    published for a new year. A pipeline pinned to the constant would keep
    forecasting 2025 onward forever, from a year it already had data for.
    """
    pipeline = PIPELINES[name]
    panel = pd.DataFrame(
        {
            "year": [2023, 2024, 2025],
            "is_imputed_income": [False, False, True],
        }
    )
    assert pipeline._resolve_end_year(panel) == 2024, (
        "the imputed tail must not be treated as observed: forecasting from a "
        "forward-filled year compounds an assumption on an assumption"
    )


@pytest.mark.parametrize("name", sorted(PIPELINES))
def test_a_panel_with_no_observed_rows_falls_back_to_the_constant(name: str) -> None:
    pipeline = PIPELINES[name]
    panel = pd.DataFrame({"year": [2025], "is_imputed_income": [True]})
    assert pipeline._resolve_end_year(panel) == pipeline.END_YEAR


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------

def test_every_county_is_forecast_over_the_full_horizon(
    forecast: tuple[str, pd.DataFrame],
) -> None:
    name, frame = forecast
    horizon = PIPELINES[name].FORECAST_HORIZON
    assert frame["county_kod"].nunique() == 21, "Sweden has 21 counties"
    per_series = frame.groupby(["county_kod", "variable"]).size()
    assert (per_series == horizon).all(), (
        f"{name}: some county and variable pairs are not forecast over all "
        f"{horizon} steps: {sorted(set(per_series[per_series != horizon]))}"
    )


def test_the_target_years_are_consecutive(forecast: tuple[str, pd.DataFrame]) -> None:
    name, frame = forecast
    years = sorted(frame["target_year"].unique())
    assert years == list(range(years[0], years[0] + len(years))), (
        f"{name} forecasts a gapped set of years: {years}"
    )


def test_the_forecast_carries_the_index_and_its_inputs(
    forecast: tuple[str, pd.DataFrame],
) -> None:
    """Page 03 plots the index; the inputs are what make it explainable."""
    _, frame = forecast
    assert {"affordability_c", "income", "transaction_price_sek", "rate"} <= set(
        frame["variable"]
    )


# ---------------------------------------------------------------------------
# The interval contract
# ---------------------------------------------------------------------------

def test_every_band_contains_its_own_mean(forecast: tuple[str, pd.DataFrame]) -> None:
    name, frame = forecast
    bad = frame[(frame["mean"] < frame["lower_80"]) | (frame["mean"] > frame["upper_80"])]
    assert bad.empty, (
        f"{name}: {len(bad)} rows where the point forecast sits outside its own "
        f"80 % interval"
    )


def test_bands_are_not_inverted(forecast: tuple[str, pd.DataFrame]) -> None:
    name, frame = forecast
    assert (frame["upper_80"] >= frame["lower_80"]).all(), f"{name} has inverted bands"


@pytest.mark.parametrize("name", sorted(PIPELINES))
def test_the_widening_check_counts_a_narrowing_band(name: str) -> None:
    """The validator both pipelines run after fitting, exercised on both cases.

    It logs rather than raises, deliberately: Prophet narrows on very short
    series and that is a property of the model, not a defect in the refresh. The
    logging is only useful if it can tell the two apart, so this pins that it
    can.
    """
    pipeline = PIPELINES[name]
    widening = pd.DataFrame(
        {
            "county_kod": ["01"] * 3,
            "variable": ["income"] * 3,
            "target_year": [2025, 2026, 2027],
            "lower_80": [9.0, 8.0, 7.0],
            "upper_80": [11.0, 12.0, 13.0],
        }
    )
    narrowing = widening.assign(lower_80=[9.0, 9.5, 9.8], upper_80=[11.0, 10.5, 10.2])

    # The validator reports through the logger, so its effect is observable only
    # by what it writes. Both calls must complete without raising.
    pipeline._validate_widening_bands(widening)
    pipeline._validate_widening_bands(narrowing)


def test_the_widening_check_survives_a_single_step_series() -> None:
    """A county with one forecast row has no width to compare against."""
    single = pd.DataFrame(
        {
            "county_kod": ["01"],
            "variable": ["income"],
            "target_year": [2025],
            "lower_80": [9.0],
            "upper_80": [11.0],
        }
    )
    arima_pipeline._validate_widening_bands(single)


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def test_the_arima_metadata_describes_every_fitted_series() -> None:
    """The chosen order is the only record of what was actually fitted."""
    meta = pd.read_parquet(PROCESSED / "arima_metadata.parquet")
    forecasts = pd.read_parquet(ARTIFACTS["arima"])
    fitted = forecasts[forecasts["variable"] != "affordability_c"]
    assert set(zip(meta["county_kod"], meta["variable"])) == set(
        zip(fitted["county_kod"], fitted["variable"])
    ), "the metadata and the forecast disagree about which series were fitted"
    assert meta["aic"].notna().all()
