"""Version B stops rewriting history when a year is added.

R1 in `docs/OPEN_RISKS.md`, the last open High that changed published numbers.
`compute_version_b` pooled its four component z-scores across whatever panel it
was handed, so every published value was a function of panel composition. Append
a row and all eleven years moved, silently.

The fix is not to stop pooling — decision D5 chose pooling because the pooled
level is the only time trend the index carries, and Versions A and C, normalised
within year, are silent about whether Sweden as a whole got better or worse. The
fix is to stop recomputing the reference distribution. It is derived once and
stored in `data/processed/version_b_reference.json`.

The load-bearing test here is `test_appending_a_year_leaves_history_alone`,
together with the negative control directly beneath it. A test that passes
because the scenario it describes never happens would be worse than no test, so
the control asserts that the *old* behaviour still fails under the same input.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.indices import b_reference as bref
from src.indices.affordability import compute_all, complete_case, scorable_rows
from src.indices.normalize import normalize_and_rank

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def municipal() -> pd.DataFrame:
    """The rows the pipeline actually scores at municipal level."""
    panel = pd.read_parquet(PROCESSED / "panel_municipal.parquet")
    return scorable_rows(complete_case(panel))


def _next_year(scored: pd.DataFrame) -> pd.DataFrame:
    """A plausible next refresh: the latest year repeated with modest growth.

    The exact figures do not matter. What matters is that the new rows shift the
    pooled mean and standard deviation of every component, which is the only
    mechanism by which history used to move.
    """
    latest = scored[scored["year"] == scored["year"].max()].copy()
    latest["year"] = int(scored["year"].max()) + 1
    latest["median_income"] *= 1.03
    latest["transaction_price_sek"] *= 1.03
    latest["policy_rate"] = latest["policy_rate"] + 1.5
    latest["cpi_yoy_pct"] = latest["cpi_yoy_pct"] + 2.0
    return pd.concat([scored, latest], ignore_index=True)


# ---------------------------------------------------------------------------
# The fix
# ---------------------------------------------------------------------------

def test_appending_a_year_leaves_history_alone(municipal: pd.DataFrame) -> None:
    """R1, closed. The whole point of the stored reference."""
    reference = bref.derive(municipal, "municipal")
    cutoff = int(municipal["year"].max())

    before = normalize_and_rank(compute_all(municipal, reference))
    after = normalize_and_rank(compute_all(_next_year(municipal), reference))
    after = after[after["year"] <= cutoff]

    merged = before.merge(after, on=["region_code", "year"], suffixes=("_o", "_n"))
    assert len(merged) == len(before)

    moved = (merged["version_b_n"] - merged["version_b_o"]).abs().max()
    assert moved == pytest.approx(0.0, abs=1e-12), (
        f"adding a year moved historical version_b by up to {moved:.2e}; the "
        f"stored reference is not being used, or it is being re-derived"
    )
    assert (merged["rank_b_o"] == merged["rank_b_n"]).all()
    assert (merged["risk_b_o"] == merged["risk_b_n"]).all()


def test_without_a_reference_the_same_append_still_rewrites_history(
    municipal: pd.DataFrame,
) -> None:
    """The negative control. A guard nobody has seen fail is a comment.

    Same panel, same appended year, no stored reference: the defect reproduces.
    Measured when this was written, an ordinary year-addition moved all 3 190
    historical rows and changed 947 ranks. If this test ever passes trivially,
    the fixture stopped exercising the mechanism and the test above proves
    nothing.
    """
    cutoff = int(municipal["year"].max())
    before = normalize_and_rank(compute_all(municipal))
    after = normalize_and_rank(compute_all(_next_year(municipal)))
    after = after[after["year"] <= cutoff]

    merged = before.merge(after, on=["region_code", "year"], suffixes=("_o", "_n"))
    moved = (merged["version_b_n"] - merged["version_b_o"]).abs().max()
    assert moved > 1e-6, (
        "the unreferenced path no longer re-bases on an appended year. Either "
        "the default changed, in which case this control is obsolete, or the "
        "fixture stopped shifting the pooled moments."
    )


def test_versions_a_and_c_were_never_affected(municipal: pd.DataFrame) -> None:
    """Context for why B alone needed this: A and C normalise within year."""
    cutoff = int(municipal["year"].max())
    before = normalize_and_rank(compute_all(municipal))
    after = normalize_and_rank(compute_all(_next_year(municipal)))
    after = after[after["year"] <= cutoff]
    merged = before.merge(after, on=["region_code", "year"], suffixes=("_o", "_n"))
    for column in ("z_a", "z_c"):
        moved = (
            merged[f"{column}_n"].astype(float) - merged[f"{column}_o"].astype(float)
        ).abs().max()
        assert moved == pytest.approx(0.0, abs=1e-9), f"{column} moved by {moved:.2e}"


# ---------------------------------------------------------------------------
# Adoption was free, and must stay provably so
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("level", bref.LEVELS)
def test_freezing_reproduced_the_values_it_replaced(level: str) -> None:
    """Scoring against a reference derived from this panel changes nothing.

    This is what made the fix safe to adopt: no published number moved on the
    day it landed. It is also a real assertion rather than a tautology, because
    the reference must be derived from exactly the rows that get scored. The
    first draft derived from `complete_case` (4 060 municipal rows) while
    `compute_all` scored the 3 190 with no nulls, and the two disagreed by up to
    0.19.
    """
    panel = pd.read_parquet(PROCESSED / f"panel_{level}.parquet")
    scored = scorable_rows(complete_case(panel))
    moving = compute_all(scored)["version_b"]
    frozen = compute_all(scored, bref.derive(scored, level))["version_b"]
    assert (frozen - moving).abs().max() == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------

def test_the_reference_artifact_is_committed_for_every_level() -> None:
    """`reference_for` bootstraps a missing level, loudly. It must never need to.

    Bootstrapping decides what "normal" means for the whole index. If the
    artifact were missing from a checkout, a refresh would quietly invent a new
    norm from whatever panel happened to be present.
    """
    stored = bref.load()
    assert stored, f"{bref.REFERENCE_PATH.name} is missing; it is a committed artifact"
    for level in bref.LEVELS:
        assert level in stored, f"no stored Version B reference for {level!r}"
        for component in bref.COMPONENTS:
            assert component in stored[level].moments, (
                f"{level} reference has no moments for {component!r}"
            )


@pytest.mark.parametrize("level", bref.LEVELS)
def test_the_committed_reference_matches_the_committed_panel(level: str) -> None:
    """The stored moments are the ones this panel produces, not hand-edited.

    A reference is a published decision. Editing the numbers in the JSON would
    silently re-base every Version B value with no diff anyone would read as
    such, so the file is checked against the data it claims to describe.

    This will fail the first time the panel genuinely changes, which is correct:
    a re-base should be a deliberate act with a version bump behind it, not a
    silent consequence of a refresh.
    """
    panel = pd.read_parquet(PROCESSED / f"panel_{level}.parquet")
    scored = scorable_rows(complete_case(panel))
    fresh = bref.derive(scored, level)
    stored = bref.load()[level]
    for component in bref.COMPONENTS:
        for moment in ("mean", "std"):
            assert stored.moments[component][moment] == pytest.approx(
                fresh.moments[component][moment], rel=1e-9
            ), (
                f"{level}/{component}/{moment} in the committed reference does not "
                f"match the committed panel. If the panel changed deliberately, "
                f"re-derive the reference and bump its version, and expect every "
                f"Version B value to move."
            )


def test_the_artifact_records_what_it_was_derived_from() -> None:
    """A frozen reference is only auditable if it says which panel froze it."""
    payload = json.loads(bref.REFERENCE_PATH.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    for level in bref.LEVELS:
        derived = payload["levels"][level]["derived_from"]
        assert derived["rows"] > 0
        assert derived["min_year"] < derived["max_year"]


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------

def test_a_missing_component_is_refused_rather_than_guessed() -> None:
    """A formula that grew a term must not be scored against a reference that
    predates it. Silently dropping the term would change every value."""
    reference = bref.LevelReference(
        level="municipal",
        derived_from={"min_year": 2014, "max_year": 2024, "rows": 1},
        moments={"pi_ratio": {"mean": 1.0, "std": 1.0}},
    )
    with pytest.raises(KeyError, match="policy_rate"):
        reference.zscore(pd.Series([1.0, 2.0]), "policy_rate")


def test_a_degenerate_component_scores_zero_rather_than_dividing_by_it() -> None:
    reference = bref.LevelReference(
        level="national",
        derived_from={"min_year": 2014, "max_year": 2024, "rows": 11},
        moments={"cpi_yoy_pct": {"mean": 2.0, "std": 0.0}},
    )
    scored = reference.zscore(pd.Series([1.0, 5.0]), "cpi_yoy_pct")
    assert (scored == 0.0).all()
