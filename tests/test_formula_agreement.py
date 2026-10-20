"""Six scoring columns nobody displayed, and the property that explains them.

The ranked artifact carries `z`, `rank` and `risk` for each of Versions A, B and
C. Until 2026-09-21 the interface read only the `_c` three. Item 7 of
`docs/APP_REFERENCE.md` (Part I) posed the question as "display them or stop computing
them", on the reasoning that six unused columns in a committed artifact will
eventually drift or confuse.

Reading them before displaying them answered it differently than expected, and
better: **`z_a`, `rank_a` and `risk_a` are exact duplicates of the `_c` family,
in every row, by construction.**

    A = k · (P / I) · r
    C = k · (P / I) · (r · 0,7 + amortisation)

`r` and the amortisation rule are national, so within one year A and C differ by a single constant
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
    cost_adjustment,
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

    C is the household's cash flow, A the bank's gross interest. Amortisation
    puts C above A in every year since the requirement took effect.
    """
    for year in range(2017, int(ranked["year"].max()) + 1):
        assert cost_adjustment(ranked, year).factor > 1.0, year


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


# ── Neither formula has a floor ───────────────────────────────────────


def _one_row(**overrides) -> pd.DataFrame:
    base = {
        "year": [2024],
        "median_income": [400_000.0],
        "transaction_price_sek": [4_000_000.0],
        "mortgage_rate": [4.0],
    }
    base.update({k: [v] for k, v in overrides.items()})
    return pd.DataFrame(base)


@pytest.mark.parametrize("rate", [0.25, 1.0, 4.0, 9.0])
def test_both_formulas_are_linear_in_the_rate_all_the_way_down(rate: float) -> None:
    """The old A clipped the rate at 0,1 pp and the old C the real rate at
    0,5 pp. A cost share needs neither: halving the rate halves A's value."""
    a = compute_version_a(_one_row(mortgage_rate=rate)).iloc[0]
    a_half = compute_version_a(_one_row(mortgage_rate=rate / 2)).iloc[0]
    assert a_half == pytest.approx(a / 2)

    c = compute_version_c(_one_row(mortgage_rate=rate)).iloc[0]
    c_half = compute_version_c(_one_row(mortgage_rate=rate / 2)).iloc[0]
    assert c - c_half == pytest.approx(100 * 0.85 * 4_000_000 * (rate / 2 / 100) * 0.7 / 800_000)


def test_a_non_positive_rate_is_refused_rather_than_floored() -> None:
    with pytest.raises(ValueError, match="mortgage_rate"):
        compute_version_c(_one_row(mortgage_rate=0.0))


def test_a_row_that_breaks_the_identity_is_reported_not_averaged_away(
    ranked: pd.DataFrame,
) -> None:
    """One deviant municipality must withdraw the single-factor claim on Sida 02."""
    latest = int(ranked["year"].max())
    tampered = ranked[ranked["year"] == latest].copy()
    tampered.loc[tampered.index[0], "version_c"] = float(tampered["version_c"].iloc[0]) * 1.5
    assert not cost_adjustment(tampered, latest).is_national_constant
