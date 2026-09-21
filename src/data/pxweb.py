"""PxWeb transport: rate limiting, querying, caching, and JSON-stat2 parsing.

Split out of `scb_client.py` so that module holds only *which table, which
selection* and this one holds *how a PxWeb request is made*. The two change for
different reasons: a table definition changes when SCB republishes something,
this changes when the API does.

The split was deferred once, deliberately. `docs/OPEN_RISKS.md` R10 recorded that
`scb_client.py` sat at 0 % coverage and that splitting an untested module is the
riskiest refactor available, so it should wait for tests. It now has them:
`tests/test_variable_contracts.py` exercises the metadata path against the live
API and against fixtures. The move itself was verified by re-fetching the income
table afterwards and comparing the result to the cache byte for byte.

Nothing here knows what any table means. That lives in `variable_contracts.py`.
"""

from __future__ import annotations

import itertools
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


