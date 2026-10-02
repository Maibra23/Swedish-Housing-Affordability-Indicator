"""The index level, split into the rate and the rest, exactly.

Sida 01 withdrew its instruction to read Sweden's direction from the mean index,
because the rate floor moves that level without affordability moving. Withdrawing
it left a fair question unanswered, and the answer is available in closed form:

    mean C_t = (100 / r_t) · mean(I/P)_t

`r_t` is national, so it leaves the mean entirely. What remains carries no rate
and therefore no floor, and compares across every year in the panel.

These tests hold the identity to the artifact rather than to the algebra — the
algebra is only true while the rate really is one number per year, which is
exactly the property `test_formula_agreement.py` pins for A and C. If a regional
rate ever arrived, the split would stop reconciling and the copy that states it
has to go.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.indices.agreement import floor_history
from src.indices.decompose import EXACTNESS_TOLERANCE, decompose_change
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_ranked.parquet"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(ARTIFACT)


@pytest.fixture(scope="module")
def history(ranked: pd.DataFrame) -> pd.DataFrame:
    return floor_history(ranked)


# ── The identity the whole answer rests on ───────────────────────────


def test_the_mean_index_is_the_rate_free_series_over_the_used_rate(
    history: pd.DataFrame,
) -> None:
    """`mean C = income_to_price / r`, in every year, to float precision."""
    for row in history.itertuples():
        assert row.mean_index == pytest.approx(
            row.income_to_price / row.rate_used_c, rel=1e-12
        ), (
            f"{row.year}: the rate no longer factors out of the mean. Either the "
            f"formula changed or the rate stopped being national, and the rate-free "
            f"column on Sida 01 is no longer the index with the rate divided out."
        )


def test_the_same_identity_holds_for_version_a(
    history: pd.DataFrame, ranked: pd.DataFrame
) -> None:
    """A's mean is the same rate-free series over A's own floored rate.

    Which is the second way of seeing why A and C cannot rank differently: they
    share every term except a national constant.
    """
    for row in history.itertuples():
        observed = ranked[ranked["year"] == row.year]["version_a"].astype(float).mean()
        assert observed == pytest.approx(row.income_to_price / row.rate_used_a, rel=1e-12)


def test_the_rate_free_column_is_the_mean_of_income_over_price(
    history: pd.DataFrame, ranked: pd.DataFrame
) -> None:
    """Stated in the units the panel shows: percent of a house per median income."""
    for row in history.itertuples():
        year = ranked[ranked["year"] == row.year]
        expected = (
            year["median_income"].astype(float) / year["transaction_price_sek"].astype(float)
        ).mean() * 100.0
        assert row.income_to_price == pytest.approx(expected, rel=1e-12)


# ── The split reconciles, for any pair of years ──────────────────────


def test_every_consecutive_pair_reconciles(history: pd.DataFrame) -> None:
    years = [int(y) for y in history["year"]]
    for earlier, later in zip(years, years[1:]):
        change = decompose_change(history, earlier, later)
        assert change is not None, f"no split available for {earlier}->{later}"
        assert change.is_exact, (
            f"{earlier}->{later}: the parts miss the whole by {change.residual:.2e}, "
            f"over the {EXACTNESS_TOLERANCE:.0e} tolerance. The panel states the split "
            f"as complete and would be overstating one of the two parts."
        )


def test_the_whole_period_reconciles(history: pd.DataFrame) -> None:
    change = decompose_change(history, int(history.iloc[0]["year"]), int(history.iloc[-1]["year"]))
    assert change is not None and change.is_exact
    combined = (1 + change.rate_pct / 100) * (1 + change.income_to_price_pct / 100)
    assert combined == pytest.approx(1 + change.total_pct / 100, rel=1e-9)


def test_the_floor_release_is_attributed_to_the_rate_not_to_affordability(
    history: pd.DataFrame,
) -> None:
    """The misreading this answer exists to prevent, measured.

    Across the floor release the mean index falls by far more than income
    against price does. If the rate ever stopped dominating that move, the copy
    telling a reader to prefer the rate-free column would be overstating.
    """
    released = history[~history["real_floored"]]
    bound = history[history["real_floored"]]
    if released.empty or bound.empty:
        pytest.skip("this panel has no transition between floor states")

    later = int(released["year"].max())
    if later - 1 not in set(int(y) for y in bound["year"]):
        pytest.skip("the released year does not directly follow a bound one")

    change = decompose_change(history, later - 1, later)
    assert change is not None and change.rate_dominates, (
        f"{later - 1}->{later}: income against price moved "
        f"{change.income_to_price_pct:+.1f} % against the rate's {change.rate_pct:+.1f} %. "
        f"The level fall is no longer mostly the floor releasing."
    )


# ── Absent years return nothing, rather than a figure ────────────────


@pytest.mark.parametrize("pair", [(1999, 2024), (2024, 2099), (1999, 2099)])
def test_a_year_outside_the_panel_yields_no_split(
    history: pd.DataFrame, pair: tuple[int, int]
) -> None:
    assert decompose_change(history, *pair) is None


# ── The copy points at the column, and the column exists ─────────────


def test_the_copy_names_the_column_it_sends_the_reader_to() -> None:
    """A pointer to a column that is not rendered is worse than no pointer."""
    header = SWEDISH_LABELS["fl.inkomst_pris"]
    pointing = [
        key
        for key in ("rv.antal_kommuner_med_z_poang_0_67", "fl.svaret")
        if header in SWEDISH_LABELS[key]
    ]
    assert len(pointing) == 2, (
        f"copy that should name the {header!r} column no longer does: "
        f"{sorted({'rv.antal_kommuner_med_z_poang_0_67', 'fl.svaret'} - set(pointing))}"
    )


def test_the_answer_states_its_own_limitation() -> None:
    """The rate-free series is free of the formula's rate, not of the economy."""
    caveat = SWEDISH_LABELS["fl.forbehall"]
    for token in ("bostadspriser", "ränta"):
        assert token in caveat.lower(), (
            f"the rate-free column is offered without saying that prices themselves "
            f"respond to rates; {token!r} is missing from the caveat"
        )


# ── The documents that quote the split ───────────────────────────────

#: Everywhere the rate-free series or the attribution is written out. All three
#: are read by someone deciding whether to trust the index, which is the worst
#: place for a figure nothing re-derives.
DOCS_QUOTING_THE_SPLIT = ("README.md", "docs/APP_GUIDE.md", "docs/METHODOLOGY.md")


def _sv(value: float, decimals: int) -> str:
    text = f"{value:.{decimals}f}"
    if float(text) == 0:
        text = text.lstrip("-")
    return text.replace("-", "−").replace(".", ",")


@pytest.mark.parametrize("document", DOCS_QUOTING_THE_SPLIT)
def test_a_document_quoting_the_rate_free_series_quotes_the_derived_one(
    document: str, history: pd.DataFrame
) -> None:
    """The endpoints of the comparable series, as the documents state them."""
    text = (ROOT / document).read_text(encoding="utf-8")
    for row in (history.iloc[0], history.iloc[-1]):
        rendered = f"{_sv(float(row['income_to_price']), 1)} %"
        assert rendered in text, (
            f"{document} no longer states the rate-free series for "
            f"{int(row['year'])} as {rendered}. The artifacts moved; the prose has to."
        )


@pytest.mark.parametrize("document", DOCS_QUOTING_THE_SPLIT)
def test_a_document_quoting_the_attribution_quotes_the_derived_one(
    document: str, history: pd.DataFrame
) -> None:
    """The headline split — the last two years — wherever it is written out."""
    years = [int(y) for y in history["year"]]
    change = decompose_change(history, years[-2], years[-1])
    assert change is not None and change.is_exact

    text = (ROOT / document).read_text(encoding="utf-8")
    for part, value in (
        ("rate", change.rate_pct),
        ("income against price", change.income_to_price_pct),
    ):
        rendered = f"{_sv(value, 1)} %"
        assert rendered in text, (
            f"{document} states the {part} part of the {years[-2]}–{years[-1]} move as "
            f"something other than {rendered}"
        )
