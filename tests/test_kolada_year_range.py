"""The Kolada client must ask for every year that exists, not a year someone typed.

`fetch_unemployment` defaulted to `end_year: int = 2024`. Kolada publishes KPI
N03937 for 2025 — probed live, 312 municipal records, national rate 3.14 % against
2.946 % in 2024 — and SHAI never saw it, because the client never asked. A full
refresh ran to completion and silently left unemployment a year behind while the
SCB series advanced on their own.

That asymmetry is the tell. `src/data/scb_client.py` requests *all* values of
every dimension it does not explicitly override, so its series move forward
without anyone editing code; `riksbanken_client.py` ends its window at
`date.today()`. Only Kolada had a year literal, and only Kolada stalled.

This is Finding H one layer down. T1.10 removed hardcoded years from what the app
*displays*; this removes one from what the pipeline *fetches*, where the failure
is quieter — nothing renders wrong, the number is simply old.

A future year with no data is not an error: Kolada answers HTTP 200 with zero
records for 2026. Asking for more than exists is the correct behaviour here,
which is why the ceiling can safely track the clock. Note the contrast with
T1.5: the clock must never decide what the app *claims* about vintage, only how
far the fetcher *reaches*.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.data import kolada_client
from tests.sourcetools import executable_source

CLIENT = Path(kolada_client.__file__)


@pytest.fixture
def captured_urls(monkeypatch, tmp_path):
    """Run the fetch offline, recording the URLs it would have requested."""
    urls: list[str] = []

    def fake_fetch(url: str, timeout: int = 30) -> list[dict]:
        urls.append(url)
        # One realistic record so the frame-shaping code downstream is exercised.
        return [
            {
                "municipality": "0180",
                "period": 2024,
                "values": [{"gender": "T", "value": 3.0}],
            }
        ]

    monkeypatch.setattr(kolada_client, "_fetch_paginated", fake_fetch)
    monkeypatch.setattr(kolada_client, "DATA_DIR", tmp_path)
    return urls


# ── The ceiling must not be a literal ────────────────────────────────


def test_no_hardcoded_terminal_year_in_the_client() -> None:
    source = executable_source(CLIENT.read_text(encoding="utf-8"))
    literals = re.findall(r"end_year[^=\n]*=\s*(\d{4})", source)
    assert not literals, (
        f"terminal year hardcoded in the fetcher: {literals}. Kolada gains a year "
        "every spring and this line would have to be edited to notice."
    )


def test_requested_range_reaches_the_current_year(captured_urls) -> None:
    kolada_client.fetch_unemployment(force=True)
    assert captured_urls, "no request was made"
    assert str(date.today().year) in captured_urls[0], (
        f"the request stops short of the current year: {captured_urls[0][:160]}"
    )


def test_requested_range_still_starts_at_the_documented_floor(captured_urls) -> None:
    """2010 is a real boundary — the KPI's methodology is consistent from there."""
    kolada_client.fetch_unemployment(force=True)
    assert "2010" in captured_urls[0]


def test_explicit_end_year_is_still_honoured(captured_urls) -> None:
    """The default moves; the parameter must keep working for a pinned backfill."""
    kolada_client.fetch_unemployment(start_year=2015, end_year=2018, force=True)
    url = captured_urls[0]
    assert "2018" in url and "2015" in url
    assert "2019" not in url


# ── Asking for a year that does not exist yet must be harmless ───────


def test_a_year_with_no_data_does_not_break_the_fetch(monkeypatch, tmp_path) -> None:
    """Kolada answers 200 with zero records for an unpublished year."""
    monkeypatch.setattr(kolada_client, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        kolada_client,
        "_fetch_paginated",
        lambda url, timeout=30: [
            {"municipality": "0180", "period": 2024, "values": [{"gender": "T", "value": 3.0}]},
            {"municipality": "0180", "period": 2026, "values": [{"gender": "T", "value": None}]},
        ],
    )
    df = kolada_client.fetch_unemployment(force=True)
    assert list(df["year"]) == [2024], "a null future year leaked into the panel"


def test_an_entirely_empty_response_does_not_raise(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(kolada_client, "DATA_DIR", tmp_path)
    monkeypatch.setattr(kolada_client, "_fetch_paginated", lambda url, timeout=30: [])
    df = kolada_client.fetch_unemployment(force=True)
    assert df.empty
    assert "unemployment_rate" in df.columns, (
        "an empty response must still return the documented columns, or callers "
        "downstream fail on a missing key rather than on missing data"
    )


# ── The docstring must not promise a coverage it cannot keep ─────────


def test_module_docstring_states_no_fixed_terminal_year() -> None:
    doc = kolada_client.__doc__ or ""
    spans = re.findall(r"\b(20\d{2})\s*[–—-]\s*(20\d{2})\b", doc)
    assert not spans, (
        f"the module docstring pins a coverage window {spans}; it goes stale every "
        "spring and nothing fails when it does"
    )
