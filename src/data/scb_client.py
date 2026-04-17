"""SCB PxWeb API v1 client for SHAI data extraction.

Base URL: https://api.scb.se/OV0104/v1/doris/sv/ssd/
Rate limit: 30 calls per 10 seconds, max 150 000 cells per query.
All results cached to data/raw/{table_id}.parquet.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.scb.se/OV0104/v1/doris/sv/ssd"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CACHE_MAX_AGE_HOURS = 24

# ---------------------------------------------------------------------------
# Rate-limiter state
# ---------------------------------------------------------------------------
_call_timestamps: list[float] = []
_RATE_LIMIT_CALLS = 30
_RATE_LIMIT_WINDOW = 10  # seconds


def _rate_limit() -> None:
    """Block if we would exceed 30 calls / 10 seconds."""
    now = time.time()
    _call_timestamps[:] = [t for t in _call_timestamps if now - t < _RATE_LIMIT_WINDOW]
    if len(_call_timestamps) >= _RATE_LIMIT_CALLS:
        sleep_for = _RATE_LIMIT_WINDOW - (now - _call_timestamps[0]) + 0.1
        logger.info("Rate-limit pause %.1f s", sleep_for)
        time.sleep(sleep_for)
    _call_timestamps.append(time.time())


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _post_scb(table_path: str, query_body: dict, max_retries: int = 5) -> dict:
    """POST a query to SCB and return the JSON-stat2 response."""
    url = f"{BASE_URL}/{table_path}"
    for attempt in range(max_retries):
        _rate_limit()
        try:
            resp = requests.post(url, json=query_body, timeout=60)
        except (requests.ConnectionError, requests.Timeout) as exc:
            wait = 2 ** attempt
            logger.warning("Connection error, backing off %d s (attempt %d): %s", wait, attempt + 1, exc)
            time.sleep(wait)
            continue
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = 2 ** attempt
            logger.warning("429 rate-limited, backing off %d s (attempt %d)", wait, attempt + 1)
            time.sleep(wait)
            continue
        resp.raise_for_status()
    raise RuntimeError(f"SCB request failed after {max_retries} retries: {url}")


def _get_table_metadata(table_path: str) -> dict:
    """GET table metadata (variables + value lists)."""
    url = f"{BASE_URL}/{table_path}"
    _rate_limit()
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _build_query(variables: list[dict], selection_overrides: dict[str, list[str]] | None = None,
                 response_format: str = "json-stat2") -> dict:
    """Build a PxWeb query body from variable metadata.

    *selection_overrides* maps variable code -> list of value codes to select.
    Variables not in the override dict will request ALL values.
    """
    query_items: list[dict] = []
    for var in variables:
        code = var["code"]
        if selection_overrides and code in selection_overrides:
            vals = selection_overrides[code]
        else:
            # PxWeb v1 requires explicit selection; omitting returns single default
            vals = var["values"]
        query_items.append({
            "code": code,
            "selection": {"filter": "item", "values": vals},
        })
    return {"query": query_items, "response": {"format": response_format}}


def _jsonstat2_to_dataframe(js: dict) -> pd.DataFrame:
    """Convert a JSON-stat2 response dict to a flat pandas DataFrame."""
    dims = list(js["dimension"].keys())
    dim_labels: dict[str, list[str]] = {}
    dim_codes: dict[str, list[str]] = {}
    for d in dims:
        cat = js["dimension"][d]["category"]
        idx = cat["index"]
        label = cat.get("label", idx)
        if isinstance(idx, dict):
            ordered = sorted(idx.items(), key=lambda kv: kv[1])
            codes = [k for k, _ in ordered]
        else:
            codes = list(idx)
        labels = [label.get(c, c) if isinstance(label, dict) else c for c in codes]
        dim_codes[d] = codes
        dim_labels[d] = labels

    values = js["value"]

    # Build multi-index from Cartesian product
    import itertools
    keys = list(itertools.product(*[dim_codes[d] for d in dims]))
    label_keys = list(itertools.product(*[dim_labels[d] for d in dims]))

    rows = []
    for i, (codes_tuple, label_tuple) in enumerate(zip(keys, label_keys)):
        row: dict[str, Any] = {}
        for j, d in enumerate(dims):
            row[f"{d}_code"] = codes_tuple[j]
            row[d] = label_tuple[j]
        row["value"] = values[i] if i < len(values) else None
        rows.append(row)

    return pd.DataFrame(rows)


def _chunked_fetch(table_path: str, variables: list[dict],
                   selection_overrides: dict[str, list[str]] | None = None,
                   chunk_var: str | None = None,
                   chunk_size: int = 50) -> pd.DataFrame:
    """Fetch data, chunking on *chunk_var* to stay under the 150k cell limit."""
    if chunk_var is None:
        query = _build_query(variables, selection_overrides)
        js = _post_scb(table_path, query)
        return _jsonstat2_to_dataframe(js)

    # Determine full value list for the chunk variable
    var_meta = next(v for v in variables if v["code"] == chunk_var)
    all_values = selection_overrides.get(chunk_var, var_meta["values"]) if selection_overrides else var_meta["values"]

    frames: list[pd.DataFrame] = []
    for start in range(0, len(all_values), chunk_size):
        chunk_vals = all_values[start : start + chunk_size]
        overrides = dict(selection_overrides) if selection_overrides else {}
        overrides[chunk_var] = chunk_vals
        query = _build_query(variables, overrides)
        js = _post_scb(table_path, query)
        frames.append(_jsonstat2_to_dataframe(js))
        logger.info("Chunked fetch %s: %d/%d", chunk_var, min(start + chunk_size, len(all_values)), len(all_values))

    return pd.concat(frames, ignore_index=True)


def _cache_path(name: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{name}.parquet"


def _cache_is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < CACHE_MAX_AGE_HOURS


def _save_and_return(df: pd.DataFrame, name: str) -> pd.DataFrame:
    path = _cache_path(name)
    df.to_parquet(path, index=False)
    logger.info("Saved %s  (%d rows, %d cols)", path, len(df), len(df.columns))
    return df


# ---------------------------------------------------------------------------
# Public extraction functions
# ---------------------------------------------------------------------------

def fetch_income(force: bool = False) -> pd.DataFrame:
    """Median disposable income per household, municipal level, annual.

    Source: SCB HE0110 — TabVX4bDispInkN
    https://www.scb.se/he0110-en
    """
    cache = _cache_path("HE0110_income")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    table_path = "HE/HE0110/HE0110G/TabVX4bDispInkN"
    meta = _get_table_metadata(table_path)
    variables = meta["variables"]

    # Select: all regions, samtliga hushåll, 18+, median value
    overrides: dict[str, list[str]] = {
        "Hushallstyp": ["E90"],       # samtliga hushåll
        "Alder": ["18+"],              # all adults
        "ContentsCode": ["000006SY"],  # Medianvärde, tkr
    }

    df = _chunked_fetch(table_path, variables, overrides, chunk_var="Region")
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
    """Median transaction price in SEK for småhus, municipal + county level, annual.

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
    """Mean transaction price in SEK for bostadsrätter (housing co-op apartments).

    Source: SCB BO0701 — Bostadsrättsstatistik.

    Granularity (confirmed by SCB BO0701 product page):
    - **Municipal** for the larger ~150–200 of 290 kommuner (those with enough
      transaction volume).
    - **County** (21 län) — all years.
    - **National** — all years.
    Smaller municipalities have no municipal BR price; callers (see
    `build_panel._clean_bostadsratt_price`) fall back to the county value and
    set `has_native_bostadsratt_price=False` so downstream consumers can
    match granularity in comparisons (muni-vs-muni, or county-vs-county).

    Time coverage: roughly 2012 onward, annual.

    Table path: the BO0701 product area has gone through minor renamings over
    the years. The first entry below is the currently documented table; if it
    returns 404 we fall through to the other known variants rather than
    hard-failing, and log which one succeeded so the resolved path is visible.

    Content code: we select the content code whose label contains "köpeskilling"
    or "pris" (mean purchase price per bostadsrätt, in tkr).
    """
    cache = _cache_path("BO0701_bostadsratt_price")
    if not force and _cache_is_fresh(cache):
        logger.info("Using cached %s", cache)
        return pd.read_parquet(cache)

    candidate_table_paths = [
        "BO/BO0701/BO0701A/Bostprissh",
        "BO/BO0701/BO0701A/BostprisAr",
        "BO/BO0701/BO0701A/Bostpris",
    ]
    last_err: Exception | None = None
    meta = None
    table_path = None
    for candidate in candidate_table_paths:
        try:
            meta = _get_table_metadata(candidate)
            table_path = candidate
            logger.info("BO0701 table path resolved to: %s", candidate)
            break
        except requests.HTTPError as exc:
            last_err = exc
            logger.info("BO0701 candidate %s not available (%s)", candidate, exc)
            continue
    if meta is None or table_path is None:
        raise RuntimeError(
            "Could not locate SCB BO0701 table under any known path. "
            "Check https://api.scb.se/OV0104/v1/doris/sv/ssd/BO/BO0701/ for the "
            f"current table id. Last error: {last_err}"
        )
    variables = meta["variables"]

    # Pick a price-like content code (labels may include 'Köpeskilling', 'Pris')
    overrides: dict[str, list[str]] = {}
    for var in variables:
        if var["code"] == "ContentsCode":
            values = var.get("values", [])
            labels = var.get("valueTexts", values)
            chosen = []
            for code, label in zip(values, labels):
                lbl = str(label).lower()
                if "köpe" in lbl or "pris" in lbl:
                    chosen.append(code)
            if chosen:
                overrides["ContentsCode"] = chosen[:1]
            break

    df = _chunked_fetch(table_path, variables, overrides, chunk_var="Region")
    return _save_and_return(df, "BO0701_bostadsratt_price")


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
