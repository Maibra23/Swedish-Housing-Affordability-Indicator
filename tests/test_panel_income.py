"""Income imputation: the behaviour three shipped decisions rest on.

`is_imputed_income` is what `complete_case()` filters on, and T2.4 found that an
unfiltered imputed row re-based Version B for every historical year — 1816 rank
changes caused by a year no page can render. F9 sets the growth rate. D1's honest
vintage depends on the flag being right.

None of it had a test, because the logic was inlined three times inside functions
that cannot run without `data/raw/`, which is gitignored. D2 extracted it; this
covers it.

See Task D3 in docs/OPTIMIZATION_PLAN.md and R5 in docs/OPEN_RISKS.md.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data.panel_income import IMPUTED_INCOME_GROWTH_RATE, impute_income_forward


def observed() -> pd.DataFrame:
    """Two municipalities, income observed through 2024."""
    return pd.DataFrame({
        "region_code": ["0180", "2463"],
        "year": [2024, 2024],
        "median_income": [400.0, 300.0],
    })


def test_growth_rate_is_three_percent() -> None:
    """F9. Changing this changes every imputed year in the panel."""
    assert IMPUTED_INCOME_GROWTH_RATE == pytest.approx(0.03)


def test_filled_rows_are_flagged_and_observed_rows_are_not() -> None:
    """The flag `complete_case()` filters on. T2.4 is what happens when it lies."""
    result = impute_income_forward(observed(), through_year=2026)
    assert result[result["year"] <= 2024]["is_imputed_income"].eq(False).all()
    assert result[result["year"] > 2024]["is_imputed_income"].eq(True).all()


def test_growth_compounds_from_the_last_observed_year() -> None:
    result = impute_income_forward(observed(), through_year=2026)
    stockholm = result[result["region_code"] == "0180"].set_index("year")["median_income"]
    assert float(stockholm[2025]) == pytest.approx(412.0)
    assert float(stockholm[2026]) == pytest.approx(424.36)


def test_observed_values_are_never_modified() -> None:
    result = impute_income_forward(observed(), through_year=2027)
    kept = result[~result["is_imputed_income"]].sort_values("region_code")
    assert kept["median_income"].tolist() == [400.0, 300.0]


def test_the_anchor_year_is_global_not_per_region() -> None:
    """Pins the behaviour that exists, not the one that sounds right.

    The original takes `panel["year"].max()` once and copies every row at that
    year, so a region whose series ended earlier is **not** filled. That is
    arguably a flaw — but it is the shipped behaviour, and on current data every
    region ends at the same year, so an artifact diff cannot tell the two apart.
    Changing it is a decision for `docs/OPEN_RISKS.md`, not a detail to fix while
    extracting.
    """
    ragged = pd.DataFrame({
        "region_code": ["0180", "2463"],
        "year": [2024, 2022],
        "median_income": [400.0, 300.0],
    })
    result = impute_income_forward(ragged, through_year=2025)
    filled = result[result["is_imputed_income"]]

    assert filled["region_code"].tolist() == ["0180"], (
        "a region below the global anchor year was filled; that is a behaviour "
        "change, not an extraction"
    )
    assert float(filled["median_income"].iloc[0]) == pytest.approx(412.0)


def test_the_thousands_column_is_scaled_with_the_income() -> None:
    """Omitting this leaves median_income_tkr ungrown and breaks the 1000x ratio."""
    frame = pd.DataFrame({
        "region_code": ["0180"],
        "year": [2024],
        "median_income": [533800.0],
        "median_income_tkr": [533.8],
    })
    result = impute_income_forward(frame, through_year=2025)
    filled = result[result["is_imputed_income"]].iloc[0]
    assert float(filled["median_income"]) == pytest.approx(549814.0)
    assert float(filled["median_income_tkr"]) == pytest.approx(549.814)


def test_nothing_is_added_when_the_target_year_is_already_covered() -> None:
    result = impute_income_forward(observed(), through_year=2024)
    assert len(result) == 2
    assert result["is_imputed_income"].eq(False).all()


def test_an_empty_frame_is_returned_unchanged() -> None:
    empty = pd.DataFrame(columns=["region_code", "year", "median_income"])
    assert impute_income_forward(empty, through_year=2026).empty


def test_the_input_frame_is_not_mutated() -> None:
    """Pure, so it runs on a fresh clone where data/raw is empty."""
    frame = observed()
    before = frame.copy()
    impute_income_forward(frame, through_year=2026)
    pd.testing.assert_frame_equal(frame, before)


def test_it_reproduces_the_shipped_artifact() -> None:
    """The extraction's real proof: same rows, same values, as the committed panel.

    Synthetic frames check the rules; this checks that the rules are the ones the
    shipped data was actually built with.
    """
    import numpy as np

    real = pd.read_parquet("data/processed/panel_municipal.parquet")
    columns = [
        "region_code", "region_name", "year",
        "median_income", "median_income_tkr", "is_imputed_income",
    ]
    observed_rows = real[~real["is_imputed_income"]][columns].copy()

    rebuilt = impute_income_forward(observed_rows, through_year=int(real["year"].max()))
    mine = (
        rebuilt[rebuilt["is_imputed_income"]]
        .sort_values(["region_code", "year"])
        .reset_index(drop=True)
    )
    theirs = (
        real[real["is_imputed_income"]][columns]
        .sort_values(["region_code", "year"])
        .reset_index(drop=True)
    )

    assert len(mine) == len(theirs), f"{len(mine)} imputed rows against {len(theirs)}"
    for column in ("median_income", "median_income_tkr"):
        assert np.allclose(mine[column].astype(float), theirs[column].astype(float)), (
            f"{column} differs from the committed panel"
        )
