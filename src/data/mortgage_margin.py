"""The banks' mortgage margin over the policy rate, per year, from SCB.

Sida 04 models a mortgage rate as the policy rate plus a margin the reader can
set. The default used to be a fixed 1,7 pp. SCB's own series puts the margin on
new floating-rate household mortgages at 0,76 pp in 2024, so for the default
year the page modelled 5,33 % against an actual 4,39 % and overstated the
monthly cost by roughly 6 000 SEK in Stockholm (release audit, October 2026).

The default is now the margin observed in the selected year: the annual mean of
SCB's monthly rate on new floating-rate (up to three months) mortgages to
households, minus the annual mean policy rate the panel already carries. It is
written to ``data/processed/mortgage_margin.json`` by the refresh and read by
:mod:`src.kontantinsats.margin`.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

TABLE_PATH = "FM/FM5001/FM5001C/RantaT04N"
API_URL = f"https://api.scb.se/OV0104/v1/doris/sv/ssd/{TABLE_PATH}"

#: New and renegotiated contracts, households, all lenders, floating rate.
QUERY = {
    "query": [
        {"code": "Referenssektor", "selection": {"filter": "item", "values": ["1"]}},
        {"code": "Motpartssektor", "selection": {"filter": "item", "values": ["2c"]}},
        {"code": "Avtal", "selection": {"filter": "item", "values": ["0100"]}},
        {"code": "Rantebindningstid", "selection": {"filter": "item", "values": ["1.1.1"]}},
    ],
    "response": {"format": "json"},
}

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "mortgage_margin.json"


def annual_means(monthly: dict[str, float]) -> dict[int, float]:
    """Average monthly observations ("2024M03" -> value) into calendar years."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for period, value in monthly.items():
        buckets[int(period[:4])].append(value)
    return {year: sum(values) / len(values) for year, values in sorted(buckets.items())}


def margins(mortgage_rate: dict[int, float], policy_rate: dict[int, float]) -> dict[int, float]:
    """Mortgage rate minus policy rate, in percentage points, for years with both."""
    return {
        year: mortgage_rate[year] - policy_rate[year]
        for year in sorted(mortgage_rate)
        if year in policy_rate
    }


def parse_response(payload: dict) -> dict[str, float]:
    """Monthly rates from a PxWeb JSON response, skipping SCB's ".." blanks."""
    out: dict[str, float] = {}
    for row in payload["data"]:
        value = row["values"][0]
        if value in ("..", ""):
            continue
        out[row["key"][-1]] = float(value)
    return out


def fetch_monthly() -> dict[str, float]:  # pragma: no cover - network
    """Download the monthly series from SCB."""
    import requests

    from src.data.pxweb import SCB_TIMEOUT

    response = requests.post(API_URL, json=QUERY, timeout=SCB_TIMEOUT)
    response.raise_for_status()
    return parse_response(response.json())


def build(policy_rate: dict[int, float], monthly: dict[str, float]) -> dict:
    """The artifact: per-year margin plus the two series it was derived from."""
    mortgage = annual_means(monthly)
    margin = margins(mortgage, policy_rate)
    if not margin:
        raise ValueError("no year has both a mortgage rate and a policy rate")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "SCB, Bolåneräntor till hushåll, nya och omförhandlade avtal, rörlig ränta (t.o.m. 3 mån)",
        "table_path": TABLE_PATH,
        "unit": "percentage points, annual means",
        "margin_pp": {str(y): round(v, 4) for y, v in margin.items()},
        "mortgage_rate_pct": {str(y): round(v, 4) for y, v in mortgage.items()},
        "policy_rate_pct": {str(y): round(policy_rate[y], 4) for y in margin},
    }


def write(artifact: dict, path: Path = OUTPUT_PATH) -> Path:
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %s (%d years)", path, len(artifact["margin_pp"]))
    return path
