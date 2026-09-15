"""The index must be computed on observed data, never on the imputed tail.

Income ends a year before prices, unemployment and the policy rate. `build_panel`
forward-fills it so the panel stays rectangular, flagging every filled row with
`is_imputed_income`. Those rows are never displayed: the sidebar stops at
`complete_case_max_year()`.

They were still being *scored*, and that is not harmless. `compute_version_b`
z-scores its components — price-index ratio, policy rate, unemployment, CPI —
**pooled across every row of the panel it is handed**. Admit one imputed year and
the pooled mean and standard deviation shift, which moves `version_b` for every
historical year. Measured when the 2025 refresh first landed: `z_b` moved on all
3190 rows (max 0.051), 1816 changed `rank_b`, and 19 changed `risk_b` class.

So a year built on forward-filled income, which no page will ever render, was
re-basing published numbers for years that are rendered. Version A and C are
immune — D5 made them within-year — which is why this stayed invisible until the
component series advanced far enough for an imputed row to survive into the index.

See task T2.4 and decisions D1 and D5 in docs/REVITALIZATION_PLAN.md.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.indices.affordability import complete_case, compute_all
from src.provenance import complete_case_max_year

ROOT = Path(__file__).resolve().parents[1]
RANKED = ROOT / "data" / "processed" / "affordability_ranked.parquet"
PANEL = ROOT / "data" / "processed" / "panel_municipal.parquet"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(RANKED)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


# ── The shipped artifact ─────────────────────────────────────────────


def test_ranked_artifact_carries_no_imputed_income(ranked: pd.DataFrame) -> None:
    imputed = int(ranked["is_imputed_income"].sum())
    assert imputed == 0, (
        f"{imputed} scored rows rest on forward-filled income; they cannot be "
        "displayed and they perturb Version B for the years that can"
    )


def test_index_stops_at_the_complete_case(ranked: pd.DataFrame) -> None:
    assert int(ranked["year"].max()) == complete_case_max_year()


# ── The property that makes it matter ────────────────────────────────


def test_shipped_index_is_scored_on_the_complete_case_only(
    panel: pd.DataFrame, ranked: pd.DataFrame
) -> None:
    """The regression this file exists to prevent.

    `compute_all` is *deliberately* sensitive to panel composition — Version B
    pools, see the test below. So the guard cannot be "scoring is insensitive";
    it has to be "the pipeline fed it the observed rows". The artifact must match
    the complete-case computation and must **not** match the whole-panel one.
    """
    keys = ["region_code", "year"]
    observed = complete_case(panel)
    years = sorted(observed["year"].unique())

    shipped = ranked.sort_values(keys).reset_index(drop=True)
    correct = compute_all(observed).sort_values(keys).reset_index(drop=True)
    contaminated = (
        compute_all(panel)[lambda d: d["year"].isin(years)]
        .sort_values(keys)
        .reset_index(drop=True)
    )

    assert len(shipped) == len(correct) == len(contaminated)

    for column in ("version_a", "version_b", "version_c"):
        assert np.allclose(
            shipped[column].astype(float), correct[column].astype(float), equal_nan=True
        ), f"the shipped {column} is not the complete-case computation"

    assert not np.allclose(
        correct["version_b"].astype(float),
        contaminated["version_b"].astype(float),
        equal_nan=True,
    ), (
        "scoring the whole panel now gives the same version_b as scoring the "
        "complete case — the imputed tail is gone, or B stopped pooling. Either "
        "way this guard no longer guards anything; re-read it."
    )


def test_pooled_construction_is_the_reason_this_guard_exists(panel: pd.DataFrame) -> None:
    """Demonstrate the mechanism, so the guard above is not cargo cult.

    Version B pools; feeding it a genuinely different panel must move it. If this
    ever stops being true the pooling was removed, and the guard should be
    re-read rather than trusted.
    """
    observed = complete_case(panel)
    half = observed[observed["year"] <= observed["year"].median()]

    full_b = compute_all(observed)
    half_b = compute_all(half)

    shared = half_b[["region_code", "year"]].merge(
        full_b[["region_code", "year", "version_b"]], on=["region_code", "year"]
    )
    merged = shared.merge(
        half_b[["region_code", "year", "version_b"]],
        on=["region_code", "year"],
        suffixes=("_full", "_half"),
    )
    assert not np.allclose(
        merged["version_b_full"].astype(float),
        merged["version_b_half"].astype(float),
        equal_nan=True,
    ), "version_b no longer depends on panel composition — is it still pooled?"


# ── The helper ───────────────────────────────────────────────────────


def test_complete_case_drops_only_imputed_rows(panel: pd.DataFrame) -> None:
    observed = complete_case(panel)
    assert len(observed) < len(panel), "nothing was dropped; is the flag still set?"
    assert int(observed["is_imputed_income"].sum()) == 0
    assert set(observed.columns) == set(panel.columns)


def test_complete_case_is_a_no_op_without_the_flag() -> None:
    """County and national panels may not carry the column at all."""
    frame = pd.DataFrame({"region_code": ["01"], "year": [2024], "median_income": [400.0]})
    assert len(complete_case(frame)) == 1
