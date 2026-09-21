"""SCB PxWeb table definitions for SHAI data extraction.

*Which* table and *which* selection. The transport that makes the request lives
in `pxweb.py`; what a column means lives in `variable_contracts.py`.

Base URL: https://api.scb.se/OV0104/v1/doris/sv/ssd/
Rate limit: 30 calls per 10 seconds, max 150 000 cells per query.
All results cached to data/raw/{table_id}.parquet.
"""

from __future__ import annotations

import logging

import pandas as pd

from src.data.pxweb import (
    _cache_is_fresh,
    _cache_path,
    _chunked_fetch,
    _get_table_metadata,
    _save_and_return,
)
from src.data.variable_contracts import INCOME_CONTRACT, assert_table_matches

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public extraction functions
# ---------------------------------------------------------------------------

def fetch_income(force: bool = False) -> pd.DataFrame:
    """Median *sammanräknad förvärvsinkomst* per individual, municipal, annual.

    Source: SCB HE0110A/SamForvInk1. Individual gross earned income before tax,
    ages 20 and over, both sexes. **Replaced HE0110G/TabVX4bDispInkN**, which
    returned household disposable income while every page described individual
    gross; see `docs/ADR/0001-income-series.md` for the candidates considered,
    the measured cost of the switch and the guards that now prevent a repeat.

    The selection *is* the definition and lives in `INCOME_CONTRACT`, which is
    asserted against the live table before anything is fetched.
    """
    cache = _cache_path("HE0110_income")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    contract = INCOME_CONTRACT
    meta = _get_table_metadata(contract.table_path)
    assert_table_matches(meta, contract)
    variables = meta["variables"]

    overrides = contract.as_overrides()
    years = contract.year_selection(
        [v["values"] for v in variables if v["code"] == "Tid"][0]
    )
    if years is not None:
        overrides["Tid"] = years

    df = _chunked_fetch(contract.table_path, variables, overrides, chunk_var="Region")
    return _save_and_return(df, "HE0110_income")


def fetch_price_index(force: bool = False) -> pd.DataFrame:
    """Real estate price index (fastighetsprisindex) for småhus, county level, annual.

    Source: SCB BO0501 — FastpiPSLanAr
    https://www.scb.se/bo0501-en

    NOTE: County-level data is annual only. Quarterly data is only available
    at riksområde level (12 regions). We use the annual county table.
    """
    cache = _cache_path("BO0501_price_index")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "BO/BO0501/BO0501A/FastpiPSLanAr"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    overrides: dict[str, list[str]] = {
        "ContentsCode": ["BO0501R5"],  # Fastighetsprisindex, 1990=100
    }

    df = _chunked_fetch(table_path, variables, overrides)
    return _save_and_return(df, "BO0501_price_index")


def fetch_kt_ratio(force: bool = False) -> pd.DataFrame:
    """K/T ratio (köpeskillingskoefficient) for småhus.

    Two datasets combined:
    - Municipal level (annual): BO0501B/FastprisSHRegionAr — 312 regions
    - County level (quarterly): BO0501B/FastprisPSRegKv — 33 regions

    Source: SCB BO0501
    https://www.scb.se/bo0501-en
    """
    cache = _cache_path("BO0501_kt_ratio")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    frames: list[pd.DataFrame] = []

    # 1) Municipal + county annual K/T
    table_path_annual = "BO/BO0501/BO0501B/FastprisSHRegionAr"
    meta_a = _get_table_metadata(table_path_annual)
    vars_a = meta_a["variables"]
    overrides_a: dict[str, list[str]] = {
        "Fastighetstyp": ["220"],      # permanentbostad (ej tomträtt)
        "ContentsCode": ["BO0501C4"],  # K/T ratio
    }
    df_annual = _chunked_fetch(table_path_annual, vars_a, overrides_a, chunk_var="Region")
    df_annual["frequency"] = "annual"
    frames.append(df_annual)

    # 2) County quarterly K/T
    table_path_qtr = "BO/BO0501/BO0501B/FastprisPSRegKv"
    meta_q = _get_table_metadata(table_path_qtr)
    vars_q = meta_q["variables"]
    overrides_q: dict[str, list[str]] = {
        "ContentsCode": ["BO0501L5"],  # K/T ratio
    }
    df_qtr = _chunked_fetch(table_path_qtr, vars_q, overrides_q)
    df_qtr["frequency"] = "quarterly"
    frames.append(df_qtr)

    df = pd.concat(frames, ignore_index=True)
    return _save_and_return(df, "BO0501_kt_ratio")


def fetch_unemployment(force: bool = False) -> pd.DataFrame:
    """Unemployment rate, municipal level, monthly.

    Source: SCB AM0210 — ArbStatusM (preliminary monthly data)
    https://www.scb.se/am0210

    NOTE: The prompts reference AM0101 but the correct table for municipal
    monthly unemployment is AM0210.
    """
    cache = _cache_path("AM0210_unemployment")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "AM/AM0210/AM0210A/ArbStatusM"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    overrides: dict[str, list[str]] = {
        "Kon": ["1+2"],                # totalt
        "Alder": ["20-64"],            # working-age population
        "Fodelseregion": ["tot"],      # totalt
        "ContentsCode": ["000006II"],  # arbetslöshet %
    }

    df = _chunked_fetch(table_path, variables, overrides, chunk_var="Region")
    return _save_and_return(df, "AM0210_unemployment")


def fetch_population(force: bool = False) -> pd.DataFrame:
    """Total population per municipality, annual.

    Source: SCB BE0101 — BefolkningNy
    https://www.scb.se/be0101
    """
    cache = _cache_path("BE0101_population")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "BE/BE0101/BE0101A/BefolkningNy"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    overrides: dict[str, list[str]] = {
        "Alder": ["tot"],               # total age
        "Kon": ["1", "2"],              # both genders (will sum)
        "Civilstand": ["OG", "G", "SK", "ÄNKL"],  # all civil statuses
        "ContentsCode": ["BE0101N1"],   # Folkmängd
    }

    df = _chunked_fetch(table_path, variables, overrides, chunk_var="Region")
    return _save_and_return(df, "BE0101_population")


def fetch_construction(force: bool = False) -> pd.DataFrame:
    """Housing completions per municipality, annual.

    Source: SCB BO0101 — LghReHustypAr
    """
    cache = _cache_path("BO0101_construction")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "BO/BO0101/BO0101A/LghReHustypAr"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    overrides: dict[str, list[str]] = {
        "ContentsCode": ["BO0101A5"],  # Färdigställda lägenheter i nybyggda hus
    }

    df = _chunked_fetch(table_path, variables, overrides, chunk_var="Region")
    return _save_and_return(df, "BO0101_construction")


def fetch_transaction_price(force: bool = False) -> pd.DataFrame:
    """Mean transaction price in SEK for småhus, municipal + county level, annual.

    The content code publishes *köpeskilling, medelvärde*, an arithmetic mean, so a
    few large sales can move it. This docstring said "median" until 2026-09-21
    while quoting the averaging content code two lines below; the UI said it too.

    Source: SCB BO0501 — FastprisSHRegionAr
    Content code: BO0501C2 (Purchase price, average in 1 000 SEK)
    Property type: 220 (permanent small house / permanentbostad ej tomträtt)
    Coverage: All 312 regions (290 muni + 21 county + 1 national), annual, 1981–2024
    """
    cache = _cache_path("BO0501_transaction_price")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "BO/BO0501/BO0501B/FastprisSHRegionAr"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    overrides: dict[str, list[str]] = {
        "Fastighetstyp": ["220"],      # permanentbostad (ej tomträtt)
        "ContentsCode": ["BO0501C2"],  # Purchase price, average in 1 000 SEK
    }

    df = _chunked_fetch(table_path, variables, overrides, chunk_var="Region")
    return _save_and_return(df, "BO0501_transaction_price")


def fetch_bostadsratt_price(force: bool = False) -> pd.DataFrame:
    """Mean transaction price in SEK for bostadsrätter (housing co-op apartments),
    county + national level, annual.

    Source: SCB BO0501C — Bostadsrätter
    Table: BO/BO0501/BO0501C/FastprisBRFRegionAr
    Content code: BO0501R7 — Medelpris i tkr (mean purchase price in thousands SEK).

    Coverage: 21 counties (01–25) + national (00). No municipality-level data exists
    in SCB for bostadsrätt prices — all municipalities receive their county's value
    as a fallback (see build_panel._clean_bostadsratt_price). Annual series 2000–present.

    This is the apartment analog of `fetch_transaction_price()` (which covers only
    småhus / Fastighetstyp 220). Adding it addresses audit finding F11 — the villa
    price used in affordability computations overstates typical first-time buyer
    costs in urban municipalities.
    """
    cache = _cache_path("BO0501C_bostadsratt_price")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "BO/BO0501/BO0501C/FastprisBRFRegionAr"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    # BO0501R7 = Medelpris i tkr (mean price). Fixed content code — no scanning needed.
    overrides: dict[str, list[str]] = {"ContentsCode": ["BO0501R7"]}

    df = _chunked_fetch(table_path, variables, overrides, chunk_var="Region")
    return _save_and_return(df, "BO0501C_bostadsratt_price")


def fetch_cpi(force: bool = False) -> pd.DataFrame:
    """Consumer Price Index (KPI), national, monthly. Base year 2020=100.

    Source: SCB PR0101 — KPI2020M
    """
    cache = _cache_path("PR0101_cpi")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "PR/PR0101/PR0101A/KPI2020M"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    overrides: dict[str, list[str]] = {
        "ContentsCode": ["00000807", "00000804"],  # KPI shadow index + YoY %
    }

    df = _chunked_fetch(table_path, variables, overrides)
    return _save_and_return(df, "PR0101_cpi")


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def fetch_all(force: bool = False) -> dict[str, pd.DataFrame]:
    """Execute all 7 SCB extraction functions and return results."""
    results = {}
    funcs = [
        ("income", fetch_income),
        ("price_index", fetch_price_index),
        ("kt_ratio", fetch_kt_ratio),
        ("transaction_price", fetch_transaction_price),
        ("bostadsratt_price", fetch_bostadsratt_price),
        ("unemployment", fetch_unemployment),
        ("population", fetch_population),
        ("construction", fetch_construction),
        ("cpi", fetch_cpi),
    ]
    for name, func in funcs:
        logger.info("Fetching %s ...", name)
        results[name] = func(force=force)
        logger.info("  → %d rows", len(results[name]))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    dfs = fetch_all()
    for name, df in dfs.items():
        print(f"\n{'='*60}")
        print(f"{name}: {df.shape}")
        print(df.head(3).to_string())
