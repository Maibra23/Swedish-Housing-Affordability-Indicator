"""Six scoring columns nobody displayed, and the property that explains them.

The ranked artifact carries `z`, `rank` and `risk` for each of Versions A, B and
C. Until 2026-09-21 the interface read only the `_c` three. Item 7 of
`docs/APP_GUIDE.md` posed the question as "display them or stop computing
them", on the reasoning that six unused columns in a committed artifact will
eventually drift or confuse.

Reading them before displaying them answered it differently than expected, and
better: **`z_a`, `rank_a` and `risk_a` are exact duplicates of the `_c` family,
in every row, by construction.**

    A = I / (P · R)
    C = I / (P · max(R − π, 0.5))

`R` and `π` are national, so within one year A and C differ by a single constant
factor across all 290 municipalities. Z-scores are computed within year on
`ln(value)`, where a constant factor is an additive shift that the z-score
removes exactly.

That makes the A columns worth keeping and worth *testing* rather than
displaying. Rendering them beside C would present an arithmetic identity as
corroboration, which is a worse failure than showing nothing: a reader would
take two agreeing columns as evidence when only one of them carries information.
Version B, pooled across the panel and mixing in unemployment, is the only
formula that can disagree.

So the six columns stop being dead by becoming the subject of an assertion. If
the identity ever breaks, something in the normalisation changed and the copy on
Sida 02 that explains it is wrong.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.indices.affordability import compute_version_a, compute_version_c
from src.indices.agreement import (
    NOMINAL_RATE_FLOOR_PP,
    REAL_RATE_FLOOR_PP,
    inflation_adjustment,
    measure_agreement,
    where_b_and_c_disagree,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_ranked.parquet"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(ARTIFACT)


def test_version_a_and_c_produce_the_same_z_score(ranked: pd.DataFrame) -> None:
    """The identity behind the whole section, asserted rather than asserted *in prose*."""
    assert np.allclose(
        ranked["z_a"].astype(float), ranked["z_c"].astype(float), atol=1e-12
    ), (
        "z_a and z_c have stopped being identical. Within a year A and C differ "
        "by a national constant, which a within-year z-score on logs removes. If "
        "that is no longer true, either the transform or the normalisation window "
        "changed, and the copy on Sida 02 explaining why A cannot disagree is now "
        "wrong."
    )


def test_version_a_and_c_produce_the_same_ranking(ranked: pd.DataFrame) -> None:
    assert (ranked["rank_a"] == ranked["rank_c"]).all()
    assert (ranked["risk_a"] == ranked["risk_c"]).all()


def test_version_a_and_c_still_differ_in_level(ranked: pd.DataFrame) -> None:
    """Identical ranking is not identical value, and the difference is the point.

    C is A corrected for inflation. When the real rate is far below the nominal
    rate the two are far apart in level, which is exactly what makes C the one
    the site reports. If they converged, Version C would have stopped doing
    anything.
    """
    ratio = inflation_adjustment(ranked, int(ranked["year"].max())).factor
    assert ratio > 1.5, (
        f"Version C reads only {ratio:.2f}x Version A. The two differ by "
        f"R / max(R - pi, 0.5); at that ratio the inflation correction has "
        f"stopped mattering and C's separate existence needs re-arguing."
    )


def test_version_b_is_the_only_one_that_can_disagree(ranked: pd.DataFrame) -> None:
    """The robustness claim the comparison page makes, held to the data.

    If B agreed with C everywhere, the page would be showing three views of one
    ranking and calling it corroboration. It does not: B disagrees on a quarter
    of the country.
    """
    for year in sorted(ranked["year"].unique()):
        agreement = measure_agreement(ranked, int(year))
        assert agreement.a_equals_c, f"A and C disagree in {year}"
        assert agreement.b_differs_from_c > 0, (
            f"Version B classifies every municipality exactly as C does in {year}. "
            f"Either B stopped being pooled, or it stopped carrying unemployment; "
            f"either way the comparison on Sida 02 no longer compares anything."
        )


def test_the_class_counts_add_up(ranked: pd.DataFrame) -> None:
    """A count table that does not sum to the panel is silently dropping rows."""
    agreement = measure_agreement(ranked, int(ranked["year"].max()))
    for key, counts in agreement.counts.items():
        assert sum(counts.values()) == agreement.n_kommuner, (
            f"version {key} classes sum to {sum(counts.values())}, not "
            f"{agreement.n_kommuner}; a municipality has no risk class"
        )


def test_the_disagreement_table_is_ordered_by_distance(ranked: pd.DataFrame) -> None:
    rows = where_b_and_c_disagree(ranked, int(ranked["year"].max()), limit=5)
    assert len(rows) == 5
    gaps = rows["rank_gap"].tolist()
    assert gaps == sorted(gaps, reverse=True)
    assert (rows["risk_b"] != rows["risk_c"]).all()


def test_measure_agreement_says_so_when_the_columns_are_gone() -> None:
    """Dropping the A and B columns must break loudly, not degrade to showing C."""
    frame = pd.DataFrame({"year": [2024], "risk_c": ["hog"]})
    with pytest.raises(KeyError, match="risk_a"):
        measure_agreement(frame, 2024)


# ── What the inflation adjustment is worth ───────────────────────────
#
# Sida 02 stopped giving Version A a row in the Robusthet class table, because a
# row that is identical to C's by construction invites the exact misreading the
# table exists to prevent. What replaced it is a single figure in the comparison
# expander: the inflation adjustment is worth N times in the selected year, and
# that is the whole difference between A and C.
#
# One stated number carries more weight than a duplicated column, so it is held
# to more: that it is the same for every municipality in the year, and that it
# equals the rate arithmetic it claims to summarise.


@pytest.fixture(scope="module")
def national() -> pd.DataFrame:
    return pd.read_parquet(ROOT / "data" / "processed" / "panel_national.parquet")


def test_the_inflation_adjustment_is_one_factor_for_every_municipality(
    ranked: pd.DataFrame,
) -> None:
    """A single figure may only be stated while a single figure is true."""
    for year in sorted(ranked["year"].unique()):
        adjustment = inflation_adjustment(ranked, int(year))
        assert adjustment.n_rows > 0, f"no scored rows in {year}"
        assert adjustment.is_national_constant, (
            f"in {year} the C/A ratio spreads {adjustment.spread:.2e} across "
            f"municipalities, so no single factor describes it. Sida 02 states one "
            f"figure for the whole country; if the rate or inflation ever became "
            f"regional, that sentence has to become a range."
        )


def test_the_inflation_adjustment_is_the_rate_over_the_floored_real_rate(
    ranked: pd.DataFrame, national: pd.DataFrame
) -> None:
    """Re-derived from the rate and the inflation, not from the ratio columns.

    `version_c / version_a` reduces to `max(R, 0.1) / max(R - pi, 0.5)` and
    nothing else. Deriving the expected value from the national series instead of
    from the same two columns is what makes this a check rather than a restatement.
    """
    for year in sorted(ranked["year"].unique()):
        row = national[national["year"] == int(year)]
        assert len(row) == 1, f"the national panel has no single row for {year}"

        rate = float(row["policy_rate"].iloc[0])
        inflation = float(row["cpi_yoy_pct"].iloc[0])
        expected = max(rate, 0.1) / max(rate - inflation, 0.5)

        assert inflation_adjustment(ranked, int(year)).factor == pytest.approx(
            expected, rel=1e-9
        ), (
            f"the factor stated for {year} is not R / max(R - pi, floor). Either a "
            f"formula changed or the panel's rate no longer reaches the scored rows."
        )


def test_a_row_that_breaks_the_identity_is_reported_not_averaged_away(
    ranked: pd.DataFrame,
) -> None:
    """The acceptance criterion: one deviant municipality must withdraw the claim."""
    latest = int(ranked["year"].max())
    tampered = ranked[ranked["year"] == latest].copy()
    tampered.loc[tampered.index[0], "version_c"] = (
        float(tampered["version_c"].iloc[0]) * 1.5
    )

    adjustment = inflation_adjustment(tampered, latest)
    assert not adjustment.is_national_constant, (
        "a municipality 50 % off the common ratio left the single-factor claim "
        "standing; the median would hide it and the page would state it anyway"
    )


def test_the_inflation_adjustment_says_so_when_the_columns_are_gone() -> None:
    """Dropping Version A must break loudly, not degrade to a factor of 1."""
    frame = pd.DataFrame({"year": [2024], "version_c": [6.2]})
    with pytest.raises(KeyError, match="version_a"):
        inflation_adjustment(frame, 2024)


def test_a_year_with_no_rows_claims_no_factor(ranked: pd.DataFrame) -> None:
    """An unscored year must not render as a factor of nothing."""
    adjustment = inflation_adjustment(ranked, int(ranked["year"].min()) - 1)
    assert adjustment.n_rows == 0
    assert not adjustment.is_national_constant


# ── Which floor binds, and what that does to the figure ──────────────
#
# Both formulas clip their rate, and on this panel the clips bind in nine of the
# eleven years. Where they bind the factor stops being an inflation adjustment:
# with both clipped it is 0,1/0,5, two constants divided. The page has to say so,
# which means the floors have to be where `agreement.py` says they are.


def _one_row(**columns: float) -> pd.DataFrame:
    return pd.DataFrame({name: [value] for name, value in columns.items()})


@pytest.mark.parametrize("rate", [NOMINAL_RATE_FLOOR_PP - 0.05, 0.0, -1.0])
def test_version_a_clips_where_agreement_says_it_does(rate: float) -> None:
    """The nominal floor named in `agreement.py`, pinned to the formula itself."""
    value = compute_version_a(
        _one_row(median_income=100.0, transaction_price_sek=1000.0, policy_rate=rate)
    )
    expected = 100.0 / (1000.0 * NOMINAL_RATE_FLOOR_PP / 100.0)
    assert float(value.iloc[0]) == pytest.approx(expected), (
        f"Version A does not clip a {rate} pp rate at {NOMINAL_RATE_FLOOR_PP} pp. "
        f"agreement.NOMINAL_RATE_FLOOR_PP decides whether Sida 02 calls the factor "
        f"an inflation adjustment, so it has to match compute_version_a."
    )


def test_version_a_leaves_a_rate_above_the_floor_alone() -> None:
    rate = NOMINAL_RATE_FLOOR_PP + 0.05
    value = compute_version_a(
        _one_row(median_income=100.0, transaction_price_sek=1000.0, policy_rate=rate)
    )
    assert float(value.iloc[0]) == pytest.approx(100.0 / (1000.0 * rate / 100.0))


@pytest.mark.parametrize("real_rate", [REAL_RATE_FLOOR_PP - 0.1, -7.58])
def test_version_c_clips_where_agreement_says_it_does(real_rate: float) -> None:
    """The real-rate floor, pinned the same way."""
    value = compute_version_c(
        _one_row(
            median_income=100.0,
            transaction_price_sek=1000.0,
            policy_rate=3.0,
            cpi_yoy_pct=3.0 - real_rate,
        )
    )
    expected = 100.0 / (1000.0 * REAL_RATE_FLOOR_PP / 100.0)
    assert float(value.iloc[0]) == pytest.approx(expected), (
        f"Version C does not clip a {real_rate} pp real rate at "
        f"{REAL_RATE_FLOOR_PP} pp; agreement.REAL_RATE_FLOOR_PP is now wrong."
    )


def test_version_c_leaves_a_real_rate_above_the_floor_alone() -> None:
    real_rate = REAL_RATE_FLOOR_PP + 0.1
    value = compute_version_c(
        _one_row(
            median_income=100.0,
            transaction_price_sek=1000.0,
            policy_rate=3.0,
            cpi_yoy_pct=3.0 - real_rate,
        )
    )
    assert float(value.iloc[0]) == pytest.approx(100.0 / (1000.0 * real_rate / 100.0))


def test_each_year_knows_which_of_its_floors_bind(
    ranked: pd.DataFrame, national: pd.DataFrame
) -> None:
    """The classification the page branches on, checked against the rates."""
    for year in sorted(ranked["year"].unique()):
        adjustment = inflation_adjustment(ranked, int(year))
        row = national[national["year"] == int(year)].iloc[0]
        rate = float(row["policy_rate"])
        real_rate = rate - float(row["cpi_yoy_pct"])

        assert adjustment.nominal_rate == pytest.approx(rate, abs=1e-9)
        assert adjustment.real_rate == pytest.approx(real_rate, abs=1e-9)
        assert adjustment.nominal_floor_binds == (rate < NOMINAL_RATE_FLOOR_PP)
        assert adjustment.real_floor_binds == (real_rate < REAL_RATE_FLOOR_PP)
        assert adjustment.is_an_inflation_adjustment == (
            rate >= NOMINAL_RATE_FLOOR_PP and real_rate >= REAL_RATE_FLOOR_PP
        ), f"{year} is characterised wrongly: the page would caption it as the wrong kind"


def test_where_both_floors_bind_the_factor_is_two_constants_divided(
    ranked: pd.DataFrame,
) -> None:
    """The reason the page cannot state one sentence for every year.

    2015–2021 all come back 0,20 — `NOMINAL_RATE_FLOOR_PP / REAL_RATE_FLOOR_PP`
    and nothing else. A page calling that "the inflation adjustment" would be
    reporting the ratio of two constants as an economic result.
    """
    both_floored = [
        adjustment
        for adjustment in (
            inflation_adjustment(ranked, int(year))
            for year in sorted(ranked["year"].unique())
        )
        if adjustment.nominal_floor_binds and adjustment.real_floor_binds
    ]
    if not both_floored:
        pytest.skip("no year in this panel has both rate floors binding")

    quotient = NOMINAL_RATE_FLOOR_PP / REAL_RATE_FLOOR_PP
    for adjustment in both_floored:
        assert adjustment.factor == pytest.approx(quotient, rel=1e-9), (
            f"{adjustment.year} has both floors binding but reads "
            f"{adjustment.factor:.3f}x rather than {quotient:.3f}x"
        )
        assert not adjustment.is_an_inflation_adjustment
