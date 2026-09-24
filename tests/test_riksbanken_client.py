"""The policy rate: fetched once, then divided by on every page.

R5's narrowed recommendation named this module next, and the reason is leverage
rather than size. At 67 statements it is the smallest untested thing in the
refresh pipeline, and the series it produces is a denominator in Version A and,
through the real rate, in Version C. Every affordability number on the site is
divided by something this module resampled.

**What actually needs guarding here.** Not the HTTP call — that is one
`requests.get` and a `raise_for_status`. The risk is in the two lines around it
and in the resampling:

- the API returns `value` as text, and a silent `errors="coerce"` turns anything
  unparseable into `NaN` rather than failing
- daily observations become an annual mean, and *which* days are present decides
  what that mean is. The Riksbank publishes on business days, so a year is not
  365 equal-weighted observations, and a naive average is not the same as a
  time-weighted one. That is a modelling choice the panel inherits silently

The resamplers are pure functions over a frame, so they are tested directly. The
fetch is tested with the network stubbed, because a test that needs the Riksbank
to be up is a test that fails for reasons unrelated to this repository.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.data import riksbanken_client as rb

ROOT = Path(__file__).resolve().parents[1]


def _daily(rates: dict[str, float]) -> pd.DataFrame:
    """A daily rate frame in the shape `fetch_policy_rate` returns."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(list(rates)),
            "rate": list(rates.values()),
        }
    )


class _Response:
    """The slice of `requests.Response` this client uses."""

    def __init__(self, payload, status: int = 200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return json.loads(json.dumps(self._payload))


@pytest.fixture
def isolated_cache(monkeypatch, tmp_path):
    """Point the cache at a temp dir so a test never reads or writes data/raw."""
    monkeypatch.setattr(rb, "DATA_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def test_the_api_payload_becomes_a_typed_frame(isolated_cache, monkeypatch) -> None:
    """Swea returns dates and values as strings; the panel needs neither."""
    payload = [
        {"date": "2024-01-02", "value": "4.00"},
        {"date": "2024-01-03", "value": "4.00"},
    ]
    monkeypatch.setattr(rb.requests, "get", lambda url, timeout: _Response(payload))

    frame = rb.fetch_policy_rate(force=True)

    assert list(frame.columns) == ["date", "rate"]
    assert pd.api.types.is_datetime64_any_dtype(frame["date"])
    assert pd.api.types.is_float_dtype(frame["rate"])
    assert frame["rate"].tolist() == [4.0, 4.0]


def test_an_unparseable_rate_is_dropped_rather_than_carried(
    isolated_cache, monkeypatch
) -> None:
    """`errors="coerce"` turns junk into NaN, and the dropna is what stops it.

    Worth pinning precisely because it is silent: without the drop, a NaN rate
    reaches `compute_version_a`, where it divides into every affordability value
    for that year.
    """
    payload = [
        {"date": "2024-01-02", "value": "4.00"},
        {"date": "2024-01-03", "value": "n/a"},
        {"date": "2024-01-04", "value": "3.75"},
    ]
    monkeypatch.setattr(rb.requests, "get", lambda url, timeout: _Response(payload))

    frame = rb.fetch_policy_rate(force=True)

    assert len(frame) == 2
    assert frame["rate"].notna().all()


def test_observations_are_sorted_by_date(isolated_cache, monkeypatch) -> None:
    """The resamplers index on date; an unsorted frame resamples to nonsense."""
    payload = [
        {"date": "2024-03-01", "value": "3.75"},
        {"date": "2024-01-02", "value": "4.00"},
        {"date": "2024-02-01", "value": "4.00"},
    ]
    monkeypatch.setattr(rb.requests, "get", lambda url, timeout: _Response(payload))

    frame = rb.fetch_policy_rate(force=True)

    assert frame["date"].is_monotonic_increasing


def test_a_failed_request_raises_rather_than_returning_empty(
    isolated_cache, monkeypatch
) -> None:
    """A refresh that half-succeeds is worse than one that stops."""
    monkeypatch.setattr(rb.requests, "get", lambda url, timeout: _Response([], status=503))
    with pytest.raises(RuntimeError):
        rb.fetch_policy_rate(force=True)


def test_a_fresh_cache_is_used_instead_of_the_network(
    isolated_cache, monkeypatch
) -> None:
    """The rate limit exists; so does working on a train."""
    cached = _daily({"2024-01-02": 4.0})
    cached.to_parquet(isolated_cache / "policy_rate.parquet", index=False)

    def _forbidden(*args, **kwargs):
        raise AssertionError("the network was called despite a fresh cache")

    monkeypatch.setattr(rb.requests, "get", _forbidden)
    frame = rb.fetch_policy_rate()
    assert frame["rate"].tolist() == [4.0]


def test_force_bypasses_a_fresh_cache(isolated_cache, monkeypatch) -> None:
    cached = _daily({"2024-01-02": 4.0})
    cached.to_parquet(isolated_cache / "policy_rate.parquet", index=False)
    monkeypatch.setattr(
        rb.requests,
        "get",
        lambda url, timeout: _Response([{"date": "2024-01-02", "value": "2.25"}]),
    )
    assert rb.fetch_policy_rate(force=True)["rate"].tolist() == [2.25]


def test_the_requested_series_is_the_effective_repo_rate() -> None:
    """SECBREPOEFF is the effective rate, not the announced one.

    They differ, and the methodology's variable register names this series. A
    changed constant would fetch cleanly and quietly shift every real rate.
    """
    assert rb.SERIES_ID == "SECBREPOEFF"
    assert "swea" in rb.BASE_URL


# ---------------------------------------------------------------------------
# Resampling, which is where the modelling choice lives
# ---------------------------------------------------------------------------

def test_the_annual_rate_is_the_mean_of_the_days_present() -> None:
    """Not a time-weighted average, and not 365 days: the mean of what exists.

    The Riksbank publishes on business days, so a year holds roughly 250
    observations, and a rate that changes in July is weighted by how many
    business days follow it rather than by how much of the year it covered. The
    panel inherits that. Asserted here so the choice is visible rather than
    accidental.
    """
    frame = _daily({"2024-01-02": 4.0, "2024-01-03": 4.0, "2024-07-01": 1.0})
    annual = rb.to_annual(frame)

    assert len(annual) == 1
    assert annual["year"].tolist() == [2024]
    assert annual["rate"].iloc[0] == pytest.approx((4.0 + 4.0 + 1.0) / 3)


def test_quarterly_and_monthly_carry_their_period_labels() -> None:
    frame = _daily({"2024-01-02": 4.0, "2024-04-01": 3.0})

    quarterly = rb.to_quarterly(frame)
    assert quarterly["quarter"].tolist() == [1, 2]
    assert quarterly["rate"].tolist() == [4.0, 3.0]

    monthly = rb.to_monthly(frame)
    assert monthly["month"].tolist()[0] == 1
    assert monthly["month"].tolist()[-1] == 4


def test_resampling_fills_gaps_with_empty_periods_not_with_carried_values() -> None:
    """A month with no observation resamples to NaN, not to the previous rate.

    That is the safe direction: a NaN is dropped by `complete_case`, while a
    silently carried rate would be presented as observed.
    """
    frame = _daily({"2024-01-02": 4.0, "2024-04-01": 3.0})
    monthly = rb.to_monthly(frame)

    february = monthly[monthly["month"] == 2]
    assert len(february) == 1
    assert february["rate"].isna().all()


def test_the_resamplers_do_not_mutate_their_input() -> None:
    """They set an index on the frame they are handed; a caller reusing it after
    would otherwise find it changed underneath."""
    frame = _daily({"2024-01-02": 4.0, "2024-02-01": 3.0})
    before = frame.copy(deep=True)

    rb.to_annual(frame)
    rb.to_quarterly(frame)
    rb.to_monthly(frame)

    pd.testing.assert_frame_equal(frame, before)


# ---------------------------------------------------------------------------
# Against the committed panel
# ---------------------------------------------------------------------------

def test_the_panel_rate_is_a_plausible_policy_rate() -> None:
    """A unit slip is the failure this cannot otherwise see.

    The API publishes percentage points, and `src/scenario/simulator.py` and
    `compute_version_c` both assume that. A decimal fraction would look like a
    perfectly ordinary column.
    """
    panel = pd.read_parquet(ROOT / "data" / "processed" / "panel_national.parquet")
    rates = panel["policy_rate"].dropna()
    assert not rates.empty
    assert rates.between(-2.0, 15.0).all(), (
        f"policy rates run {rates.min()} to {rates.max()}; that is not "
        f"percentage points"
    )
    assert rates.abs().max() > 0.5, (
        "every policy rate is below 0.5; the column may be a decimal fraction "
        "where the formulas expect percentage points"
    )
