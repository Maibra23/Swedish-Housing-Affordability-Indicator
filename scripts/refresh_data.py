"""SHAI — End-to-end data refresh script.

Run this script whenever new source data is available (typically after SCB/Kolada
publish annual updates, usually Q1 of each year for the prior year's data).

Steps executed:
  1. Fetch all raw data from SCB PxWeb, Riksbanken Swea, and Kolada APIs
  2. Rebuild the three panel parquets (municipal, county, national)
  3. Compute affordability indices A/B/C and save affordability parquets
  4. Run ARIMA and Prophet forecast pipelines and save forecast parquets

Usage:
    python scripts/refresh_data.py            # full refresh
    python scripts/refresh_data.py --no-fetch # skip API calls, rebuild from cached raw data
    python scripts/refresh_data.py --no-forecast  # skip forecast step (fastest)

Note on BO0701 (bostadsrätt prices):
    SCB BO0701 apartment price data is fetched as part of step 1 via
    scb_client.fetch_bostadsratt_price(). The parquet is saved to
    data/raw/BO0701_bostadsratt_price.parquet. Until this file is present,
    the Kontantinsats page (sida 04) falls back to villa prices for all
    municipalities. Run a full refresh to activate the apartment price feature.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on the path when run as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("shai.refresh")


def step_fetch(force: bool = True) -> None:
    """Fetch all raw data from external APIs."""
    logger.info("=" * 60)
    logger.info("STEP 1 — Fetching raw data from APIs")
    logger.info("=" * 60)

    from src.data.scb_client import fetch_all as scb_fetch_all
    from src.data.riksbanken_client import fetch_policy_rate
    from src.data.kolada_client import fetch_unemployment

    t0 = time.time()

    logger.info("Fetching SCB datasets (income, prices, K/T, CPI, population, construction, bostadsrätt)...")
    results = scb_fetch_all(force=force)
    for name, df in results.items():
        logger.info("  %-30s  %d rows", name, len(df))

    logger.info("Fetching Riksbanken policy rate...")
    rate_df = fetch_policy_rate(force=force)
    logger.info("  %-30s  %d rows", "policy_rate", len(rate_df))

    logger.info("Fetching Kolada unemployment (N03937)...")
    unemp_df = fetch_unemployment(force=force)
    logger.info("  %-30s  %d rows", "unemployment", len(unemp_df))

    logger.info("Step 1 done in %.1f s", time.time() - t0)


def step_build_panels() -> None:
    """Rebuild all three panel parquets from raw data."""
    logger.info("=" * 60)
    logger.info("STEP 2 — Building panels (municipal / county / national)")
    logger.info("=" * 60)

    from src.data.build_panel import build_all

    t0 = time.time()
    panels = build_all()
    for name, panel in panels.items():
        logger.info(
            "  %-12s  %d rows  year %d–%d",
            name,
            len(panel),
            panel["year"].min(),
            panel["year"].max(),
        )
    logger.info("Step 2 done in %.1f s", time.time() - t0)


def step_compute_indices() -> None:
    """Compute affordability indices A/B/C and save parquets."""
    logger.info("=" * 60)
    logger.info("STEP 3 — Computing affordability indices")
    logger.info("=" * 60)

    import pandas as pd
    from src.indices.affordability import compute_all as compute_affordability

    DATA_DIR = PROJECT_ROOT / "data" / "processed"
    t0 = time.time()

    for level in ("municipal", "county", "national"):
        panel = pd.read_parquet(DATA_DIR / f"panel_{level}.parquet")
        aff = compute_affordability(panel)
        out = DATA_DIR / f"affordability_{level}.parquet"
        aff.to_parquet(out, index=False)
        logger.info("  Saved %s  (%d rows)", out.name, len(aff))

    # Also produce affordability_ranked (municipal with rank columns)
    muni_aff = pd.read_parquet(DATA_DIR / "affordability_municipal.parquet")
    for col in ("version_a", "version_b", "version_c"):
        if col in muni_aff.columns:
            rank_col = col.replace("version", "rank")
            muni_aff[rank_col] = muni_aff.groupby("year")[col].rank(
                ascending=False, method="min"
            ).astype("Int64")
    muni_aff.to_parquet(DATA_DIR / "affordability_ranked.parquet", index=False)
    logger.info("  Saved affordability_ranked.parquet  (%d rows)", len(muni_aff))

    logger.info("Step 3 done in %.1f s", time.time() - t0)


def step_forecasts() -> None:
    """Run ARIMA and Prophet forecast pipelines."""
    logger.info("=" * 60)
    logger.info("STEP 4 — Running forecast pipelines (ARIMA + Prophet)")
    logger.info("=" * 60)

    import pandas as pd
    from src.forecast import arima_pipeline, prophet_pipeline

    DATA_DIR = PROJECT_ROOT / "data" / "processed"
    t0 = time.time()

    county_panel = pd.read_parquet(DATA_DIR / "panel_county.parquet")
    national_panel = pd.read_parquet(DATA_DIR / "panel_national.parquet")

    logger.info("Running ARIMA forecasts ...")
    arima_result, arima_meta = arima_pipeline.run_all(county_panel, national_panel)
    arima_result.to_parquet(DATA_DIR / "forecast_arima.parquet", index=False)
    arima_meta.to_parquet(DATA_DIR / "arima_metadata.parquet", index=False)
    logger.info("  Saved forecast_arima.parquet  (%d rows)", len(arima_result))

    logger.info("Running Prophet forecasts (this may take a few minutes) ...")
    prophet_result = prophet_pipeline.run_all(county_panel, national_panel)
    prophet_result.to_parquet(DATA_DIR / "forecast_prophet.parquet", index=False)
    logger.info("  Saved forecast_prophet.parquet  (%d rows)", len(prophet_result))

    logger.info("Step 4 done in %.1f s", time.time() - t0)


def main() -> None:
    parser = argparse.ArgumentParser(description="SHAI — full data refresh pipeline")
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip API calls; rebuild from existing data/raw/ files",
    )
    parser.add_argument(
        "--no-forecast",
        action="store_true",
        help="Skip forecast step (saves ~5–15 min)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=True,
        help="Force re-download even if cache is fresh (default: True)",
    )
    args = parser.parse_args()

    wall_start = time.time()
    logger.info("SHAI data refresh — started")

    if not args.no_fetch:
        step_fetch(force=args.force)
    else:
        logger.info("Skipping STEP 1 (--no-fetch)")

    step_build_panels()
    step_compute_indices()

    if not args.no_forecast:
        step_forecasts()
    else:
        logger.info("Skipping STEP 4 (--no-forecast)")

    logger.info("=" * 60)
    logger.info("Refresh complete in %.1f s", time.time() - wall_start)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
