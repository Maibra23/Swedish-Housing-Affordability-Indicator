"""The ranked artifact is the contract between the pipeline and the pages.

`data/processed/affordability_ranked.parquet` is the only place z-scores, ranks
and risk classes are supposed to come from.  Three separate implementations of
that ranking existed when these tests were written — in `indices/normalize.py`,
in `scripts/refresh_data.py`, and inline in `pages/01_Riksoversikt.py` — and they
disagreed with each other:

  * the shipped artifact carried `rank_*` but neither `z_*` nor `risk_*`, so the
    page recomputed them on every load;
  * the page's copy omitted the sign inversion that `normalize.py` applies to
    versions A and C, which put Stockholm and Solna in "låg risk" and Åsele in
    "hög risk" — the exact opposite of what the numbers say;
  * `refresh_data.py` ranked the raw version value descending without inverting
    B, so rank 1 meant "most affordable" for A and C but "least affordable" for B.

These tests pin the contract so none of the three can drift again.

Contract
--------
For every version, across every year in the panel:
  * rank 1 is the *best* affordability (lowest risk)
  * `hog` is the *least* affordable class, `lag` the most affordable
  * `z_*` is oriented so that higher = worse, for all three versions
"""

from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
RANKED_PATH = DATA_DIR / "affordability_ranked.parquet"

VERSIONS = ["a", "b", "c"]
# Higher raw value means more affordable for A and C, more risk for B.
HIGHER_IS_BETTER = {"a": True, "b": False, "c": True}


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    if not RANKED_PATH.exists():
        pytest.fail(f"Missing artifact: {RANKED_PATH}. Run scripts/refresh_data.py.")
    return pd.read_parquet(RANKED_PATH)


@pytest.fixture(scope="module")
def municipal() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "affordability_municipal.parquet")


# ---------------------------------------------------------------------------
# Shape of the artifact
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version", VERSIONS)
def test_artifact_carries_z_rank_and_risk(ranked, version):
    """Pages must never recompute these; the artifact must supply them."""
    for prefix in ("z", "rank", "risk"):
        col = f"{prefix}_{version}"
        assert col in ranked.columns, (
            f"Missing column {col!r}. The pages fall back to recomputing it "
            f"inline when it is absent, and their copy of the logic is wrong."
        )


def test_artifact_covers_every_year_in_the_panel(ranked, municipal):
    """Historical years need risk classes too, not just the latest year."""
    assert set(ranked["year"]) == set(municipal["year"]), (
        "Ranked artifact and municipal panel cover different years."
    )


def test_artifact_has_one_row_per_municipality_per_year(ranked):
    dupes = ranked.duplicated(subset=["region_code", "year"]).sum()
    assert dupes == 0, f"{dupes} duplicate region/year rows in the ranked artifact."


# ---------------------------------------------------------------------------
# Orientation: the bug that shipped
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("version", VERSIONS)
def test_rank_one_is_the_most_affordable(ranked, version):
    """Rank 1 means best affordability for all three versions.

    Before this test, `refresh_data.py` ranked the raw value descending without
    inverting B, so rank 1 meant "most affordable" for A and C and "least
    affordable" for B — two opposite meanings in one table.
    """
    for year, group in ranked.groupby("year"):
        best = group.loc[group[f"rank_{version}"].idxmin()]
        worst = group.loc[group[f"rank_{version}"].idxmax()]
        b, w = best[f"version_{version}"], worst[f"version_{version}"]
        if HIGHER_IS_BETTER[version]:
            assert b > w, (
                f"{year} version_{version}: rank 1 went to {best['region_name']} "
                f"({b:.2f}) but the last rank went to {worst['region_name']} ({w:.2f}); "
                f"higher is more affordable, so rank 1 should hold the higher value."
            )
        else:
            assert b < w, (
                f"{year} version_{version}: rank 1 went to {best['region_name']} "
                f"({b:.2f}) but the last rank went to {worst['region_name']} ({w:.2f}); "
                f"higher means more risk for version B, so rank 1 should hold the lower value."
            )


@pytest.mark.parametrize("version", VERSIONS)
def test_high_risk_class_is_the_least_affordable(ranked, version):
    """`hog` must be the least affordable group, `lag` the most.

    The page's inline copy omitted the sign inversion for A and C, which put
    Stockholm, Solna and Sundbyberg — the least affordable municipalities in the
    country — into "låg risk", and Åsele and Ragunda into "hög risk".
    """
    col = f"version_{version}"
    for year, group in ranked.groupby("year"):
        means = group.groupby(f"risk_{version}", observed=True)[col].mean()
        if not {"lag", "hog"}.issubset(means.index):
            continue
        if HIGHER_IS_BETTER[version]:
            assert means["lag"] > means["hog"], (
                f"{year} version_{version}: 'lag' averages {means['lag']:.1f} and "
                f"'hog' averages {means['hog']:.1f}, but higher is more affordable — "
                f"the classes are inverted."
            )
        else:
            assert means["lag"] < means["hog"], (
                f"{year} version_{version}: 'lag' averages {means['lag']:.1f} and "
                f"'hog' averages {means['hog']:.1f}, but higher means more risk — "
                f"the classes are inverted."
            )


@pytest.mark.parametrize("version", VERSIONS)
def test_z_is_oriented_so_higher_is_worse(ranked, version):
    """All three z-scores share one orientation, so they can be compared."""
    col = f"version_{version}"
    for year, group in ranked.groupby("year"):
        corr = group[f"z_{version}"].corr(group[col])
        if HIGHER_IS_BETTER[version]:
            assert corr < 0, (
                f"{year}: z_{version} correlates {corr:+.2f} with version_{version}; "
                f"higher is more affordable, so z should run the other way."
            )
        else:
            assert corr > 0, (
                f"{year}: z_{version} correlates {corr:+.2f} with version_{version}; "
                f"higher means more risk, so z should agree with it."
            )


# ---------------------------------------------------------------------------
# A named regression, so the failure reads plainly
# ---------------------------------------------------------------------------

def test_stockholm_is_not_classified_low_risk(ranked):
    """Stockholm is among the least affordable municipalities in Sweden.

    It was rendered green on the national map for every year except 2014.
    """
    latest = ranked[ranked["year"] == ranked["year"].max()]
    row = latest[latest["region_name"] == "Stockholm"]
    if row.empty:
        pytest.skip("Stockholm not present in the ranked artifact.")
    assert row.iloc[0]["risk_c"] != "lag", (
        "Stockholm is classified 'låg risk' — the risk classes are inverted."
    )
