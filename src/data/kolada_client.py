"""Kolada API v3 client for SHAI unemployment data.

Base URL: https://api.kolada.se/v3/
Pulls KPI N03937: Öppet arbetslösa av befolkningen, 18–65 år, andel (%).
Source provider: Arbetsförmedlingen (Swedish Public Employment Service).
Distribution channel: Kolada (RKA — Rådet för kommunal analys).

Coverage: all municipalities, from 2010 (the first year of the current
methodology) through whatever Kolada has most recently published. The upper bound
is resolved at fetch time, never written down — see fetch_unemployment.
Result cached to data/raw/kolada_unemployment.parquet.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

BASE_URL = "https://api.kolada.se/v3"
KPI_ID = "N03937"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CACHE_MAX_AGE_HOURS = 24

# The first year of the KPI's current methodology. A real boundary, unlike the
# upper one, which is whatever Kolada has published by now.
FIRST_YEAR = 2010


def _latest_possible_year() -> int:
    """Upper bound for the request window.

    Deliberately optimistic: Kolada answers HTTP 200 with zero records for a year
    it has not published, so over-asking costs one empty page and under-asking
    costs a year of data nobody notices is missing. The previous default of 2024
    meant a full refresh ran to completion while silently leaving unemployment a
    year behind the SCB series.

    The clock decides how far the *fetcher reaches*, never what the app claims
    about vintage — that comes from the artifact. See T1.5.
    """
    return date.today().year


def _cache_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "kolada_unemployment.parquet"


def _cache_is_fresh() -> bool:
    path = _cache_path()
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < CACHE_MAX_AGE_HOURS


def _fetch_paginated(url: str, timeout: int = 30) -> list[dict]:
    """Fetch all pages from a Kolada paginated endpoint."""
    all_values: list[dict] = []
    page = 1
    while url:
        logger.info("Kolada page %d: %s", page, url[:120])
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read().decode("utf-8"))
        all_values.extend(data.get("values", []))
        url = data.get("next_url")
        page += 1
    return all_values


def fetch_unemployment(
    start_year: int = FIRST_YEAR,
    end_year: int | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Fetch municipal unemployment rate from Kolada KPI N03937.

    Source: Arbetsförmedlingen via Kolada API v3.
    KPI: N03937 — Öppet arbetslösa av befolkningen, 18–65 år, andel (%).
    Definition: Openly registered unemployed persons aged 18–65 as % of
    total population aged 18–65. Annual average of monthly figures.

    Returns
    -------
    pd.DataFrame
        Columns: municipality_code, year, unemployment_rate
    """
    if end_year is None:
        end_year = _latest_possible_year()

    cache = _cache_path()
    if not force and _cache_is_fresh():
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    years_str = ",".join(str(y) for y in range(start_year, end_year + 1))
    url = f"{BASE_URL}/data/kpi/{KPI_ID}/year/{years_str}"
    records = _fetch_paginated(url)

    rows = []
    for rec in records:
        muni = rec.get("municipality", "")
        year = rec.get("period")
        # Extract total gender value (gender == "T")
        for v in rec.get("values", []):
            if v.get("gender") == "T" and v.get("value") is not None:
                rows.append({
                    "municipality_code": muni,
                    "year": year,
                    "unemployment_rate": v["value"],
                })
    # Named columns even when empty: callers index by key, and a bare
    # DataFrame() would fail on the column rather than on the missing data.
    df = pd.DataFrame(rows, columns=["municipality_code", "year", "unemployment_rate"])

    # Filter to 4-digit municipality codes (exclude county/national aggregates)
    df_muni = df[df["municipality_code"].astype(str).str.len() == 4].copy()
    df_muni = df_muni.sort_values(["municipality_code", "year"]).reset_index(drop=True)

    df_muni.to_parquet(cache, index=False)
    if len(df_muni):
        logger.info("Saved %s  (%d rows, %d municipalities, years %d–%d)",
                    cache, len(df_muni), df_muni["municipality_code"].nunique(),
                    df_muni["year"].min(), df_muni["year"].max())
    else:
        logger.warning("Saved %s but Kolada returned no municipal values for "
                       "%d–%d — check KPI %s upstream", cache, start_year,
                       end_year, KPI_ID)

    # Also save the full dataset (including county/national) for reference
    df.to_parquet(DATA_DIR / "kolada_unemployment_all.parquet", index=False)

    return df_muni


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = fetch_unemployment(force=True)
    print(f"\nShape: {df.shape}")
    print(f"Municipalities: {df['municipality_code'].nunique()}")
    print(f"Years: {sorted(df['year'].unique())}")
    print(df.head(5).to_string())
    print("...")
    print(df.tail(5).to_string())
