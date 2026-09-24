"""The normalisation convention, pinned on both of its axes.

Two decisions define how a raw index value becomes a z-score, a rank and a risk
class. They are independent, and the ±0.67σ class boundary is only meaningful
once both are settled — it is a normal-distribution quantile applied to whatever
they produce.

**Transform (decision O4).** `version_a` and `version_c` are ratios of positive
quantities, so they are log-normal. Z-scoring them raw put a ±0.67σ cut on a
variable whose normality is rejected at p < 6e-15 in every year, and produced a
≈19/51/30 class split that nobody chose. They are log-transformed first.
`version_b` is a weighted *sum* of z-scores, negative in 1919 of 3190 rows, so a
log is undefined for it — it is z-scored raw.

**Window (decision O2).** `z_*` is computed within year: it answers "where does
this municipality stand among its peers this year". But `version_b`'s own
construction in `affordability.py` stays pooled across the panel, because B is a
macro-pressure measure and that pooling is what lets its level carry a time
trend. Finding G is resolved by documenting the difference as deliberate, not by
erasing it.

See Findings F, G and Q.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src.indices.normalize import LOG_TRANSFORMED, VERSIONS, normalize_and_rank

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "affordability_ranked.parquet")


@pytest.fixture(scope="module")
def municipal() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "affordability_municipal.parquet")


# ── O4 — the transform ───────────────────────────────────────────────


def test_ratio_versions_are_the_logged_ones():
    """A and C are ratios; B is a sum of z-scores and cannot be logged."""
    assert set(LOG_TRANSFORMED) == {"a", "c"}


@pytest.mark.parametrize("version", ["a", "c"])
def test_z_is_computed_on_the_log(ranked: pd.DataFrame, version: str):
    """Re-derive z from the artifact's own raw values and compare."""
    for year, group in ranked.groupby("year"):
        raw = group[f"version_{version}"].astype(float)
        logged = np.log(raw)
        expected = -((logged - logged.mean()) / logged.std())
        actual = group[f"z_{version}"].astype(float)
        assert np.allclose(actual, expected), f"z_{version} is not log-based in {year}"


def test_version_b_is_not_logged(ranked: pd.DataFrame):
    for year, group in ranked.groupby("year"):
        raw = group["version_b"].astype(float)
        expected = (raw - raw.mean()) / raw.std()
        actual = group["z_b"].astype(float)
        assert np.allclose(actual, expected), f"z_b is not raw-based in {year}"


@pytest.mark.parametrize("version", ["a", "c"])
def test_logged_z_passes_a_normality_test(ranked: pd.DataFrame, version: str):
    """The ±0.67σ cut borrows its meaning from normality; check we have it."""
    failures = {}
    for year, group in ranked.groupby("year"):
        p = stats.normaltest(group[f"z_{version}"].astype(float)).pvalue
        if p < 0.01:
            failures[int(year)] = float(p)
    assert not failures, f"z_{version} is not normal in {failures}"


def test_raw_version_c_would_fail_that_test(ranked: pd.DataFrame):
    """Guard the guard: the untransformed variable must actually be non-normal."""
    for year, group in ranked.groupby("year"):
        p = stats.normaltest(group["version_c"].astype(float)).pvalue
        assert p < 0.01, f"{year}: raw version_c looks normal, premise of O4 is stale"


def test_class_split_is_close_to_the_quartiles(ranked: pd.DataFrame):
    """±0.67σ on a normal variable should give roughly 25/50/25."""
    for year, group in ranked.groupby("year"):
        share = group["risk_c"].value_counts(normalize=True) * 100
        assert 20 <= share.get("lag", 0) <= 30, f"{year}: lag {share.get('lag', 0):.0f}%"
        assert 20 <= share.get("hog", 0) <= 30, f"{year}: hog {share.get('hog', 0):.0f}%"


# ── The transform must not disturb the ordering ──────────────────────


@pytest.mark.parametrize("version", VERSIONS)
def test_rank_still_agrees_with_the_raw_value(ranked: pd.DataFrame, version: str):
    """A log is monotonic, so ranks must match the raw ordering exactly."""
    higher_is_better = version in ("a", "c")
    for year, group in ranked.groupby("year"):
        raw = group[f"version_{version}"].astype(float)
        expected = raw.rank(method="min", ascending=not higher_is_better).astype(int)
        actual = group[f"rank_{version}"].astype(int)
        assert (actual.values == expected.values).all(), f"rank_{version} moved in {year}"


# ── O2 — the window ──────────────────────────────────────────────────


def test_z_is_scored_within_year(ranked: pd.DataFrame):
    """Each year is scored against its own distribution, so each z centres on 0."""
    for version in VERSIONS:
        means = ranked.groupby("year")[f"z_{version}"].mean()
        assert np.allclose(means, 0, atol=1e-9), f"z_{version} is not within-year"


def test_version_b_keeps_its_pooled_level(municipal: pd.DataFrame):
    """B's construction stays pooled, so its level must still carry a trend.

    This is the decision recorded as O2: within-year normalisation would pin B's
    mean at zero every year and delete the macro signal it exists to measure.
    """
    means = municipal.groupby("year")["version_b"].mean()
    assert means.std() > 0.2, (
        f"version_b no longer varies across years (std {means.std():.3f}); "
        f"its pooled construction has been lost."
    )
    assert means.max() - means.min() > 0.5, "B's macro trend has been flattened"


@pytest.mark.parametrize("version", ["a", "c"])
def test_ac_levels_are_not_forced_to_zero(municipal: pd.DataFrame, version: str):
    """A and C are index levels, not z-scores; only their z_* is normalised."""
    means = municipal.groupby("year")[f"version_{version}"].mean()
    assert means.std() > 0, f"version_{version} level is constant across years"


# ── Determinism ──────────────────────────────────────────────────────


def test_rescoring_reproduces_the_artifact(municipal: pd.DataFrame, ranked: pd.DataFrame):
    """The committed artifact must be exactly what normalize.py produces now."""
    rescored = normalize_and_rank(municipal)
    for version in VERSIONS:
        for prefix in ("z", "rank"):
            col = f"{prefix}_{version}"
            assert np.allclose(
                rescored.sort_values(["year", "region_code"])[col].astype(float).values,
                ranked.sort_values(["year", "region_code"])[col].astype(float).values,
            ), f"{col} in the artifact does not match a fresh run"
        col = f"risk_{version}"
        assert (
            rescored.sort_values(["year", "region_code"])[col].values
            == ranked.sort_values(["year", "region_code"])[col].values
        ).all(), f"{col} in the artifact does not match a fresh run"
