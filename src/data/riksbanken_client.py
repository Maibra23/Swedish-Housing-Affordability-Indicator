"""Riksbanken Swea v1 REST API client for SHAI.

Base URL: https://api.riksbank.se/swea/v1/
Pulls SECBREPOEFF (policy rate) daily series since 2014.
Result cached to data/raw/policy_rate.parquet.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.riksbank.se/swea/v1"
SERIES_ID = "SECBREPOEFF"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CACHE_MAX_AGE_HOURS = 24


def _cache_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "policy_rate.parquet"


def _cache_is_fresh() -> bool:
    path = _cache_path()
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < CACHE_MAX_AGE_HOURS


def fetch_policy_rate(
    start: str = "2014-01-01",
    end: str | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Fetch daily policy rate (repo rate) from Riksbanken Swea API.

    Parameters
    ----------
    start : str
        Start date in YYYY-MM-DD format. Default 2014-01-01.
    end : str | None
        End date. Defaults to today.
    force : bool
        If True, skip cache and re-fetch.

    Returns
    -------
    pd.DataFrame
        Columns: date (datetime64), rate (float64).
    """
    cache = _cache_path()
    if not force and _cache_is_fresh():
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    if end is None:
        end = date.today().isoformat()

    url = f"{BASE_URL}/Observations/{SERIES_ID}/{start}/{end}"
    logger.info("GET %s", url)

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data)
    df.rename(columns={"date": "date", "value": "rate"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df.dropna(subset=["rate"]).sort_values("date").reset_index(drop=True)

    df.to_parquet(cache, index=False)
    logger.info("Saved %s  (%d rows, %s to %s)", cache, len(df),
                df["date"].min().date(), df["date"].max().date())
    return df


# ---------------------------------------------------------------------------
# Resampling helpers
# ---------------------------------------------------------------------------

def to_quarterly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily policy rate to quarterly mean."""
    ts = df.set_index("date")["rate"].resample("QS").mean().reset_index()
    ts.columns = ["date", "rate"]
    ts["year"] = ts["date"].dt.year
    ts["quarter"] = ts["date"].dt.quarter
    return ts


def to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily policy rate to monthly mean."""
    ts = df.set_index("date")["rate"].resample("MS").mean().reset_index()
    ts.columns = ["date", "rate"]
    ts["year"] = ts["date"].dt.year
    ts["month"] = ts["date"].dt.month
    return ts


def to_annual(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily policy rate to annual mean."""
    ts = df.set_index("date")["rate"].resample("YS").mean().reset_index()
    ts.columns = ["date", "rate"]
    ts["year"] = ts["date"].dt.year
    return ts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    daily = fetch_policy_rate()
    print(f"\nDaily: {daily.shape}")
    print(daily.head())
    print(daily.tail())

    qtr = to_quarterly(daily)
    print(f"\nQuarterly: {qtr.shape}")
    print(qtr.tail(8))
