"""The rate-floor panel, and the claims it exists to qualify.

Two pages told a reader to judge Sweden's direction from the mean index,
because it is a level series rather than a within-year rank. That is true about
the arithmetic and misleading about this panel: Version C divides by a real rate
floored at 0,5 pp, the floor bound in nine of eleven observed years, and it
released in the last one. The national mean fell by over a third in that year
with no change in anyone's income or price.

So the copy now qualifies the claim and `src/ui/floor_panel.py` carries the
evidence, collapsed, on the three pages where it bears. These tests hold the
derived table to the rates and hold the copy to the qualification — an
unqualified "can be compared between years" is the defect, not a wording choice.

See F17, and METHODOLOGY section 3.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.indices.agreement import (
    NOMINAL_RATE_FLOOR_PP,
    REAL_RATE_FLOOR_PP,
    floor_history,
    inflation_adjustment,
)
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_ranked.parquet"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(ARTIFACT)


@pytest.fixture(scope="module")
def history(ranked: pd.DataFrame) -> pd.DataFrame:
    return floor_history(ranked)


# ── The table is derived, row by row ─────────────────────────────────


def test_one_row_per_scored_year(history: pd.DataFrame, ranked: pd.DataFrame) -> None:
    assert list(history["year"]) == sorted(int(y) for y in ranked["year"].unique())


def test_each_row_states_the_rate_its_formula_actually_divided_by(
    history: pd.DataFrame,
) -> None:
    """`rate_used_*` is the clipped rate, which is the column's whole point."""
    for row in history.itertuples():
        assert row.rate_used_a == pytest.approx(max(row.policy_rate, NOMINAL_RATE_FLOOR_PP))
        assert row.rate_used_c == pytest.approx(max(row.real_rate, REAL_RATE_FLOOR_PP))
        assert row.nominal_floored == (row.policy_rate < NOMINAL_RATE_FLOOR_PP)
        assert row.real_floored == (row.real_rate < REAL_RATE_FLOOR_PP)


def test_the_factor_column_is_the_two_used_rates_divided(history: pd.DataFrame) -> None:
    for row in history.itertuples():
        assert row.factor == pytest.approx(row.rate_used_a / row.rate_used_c, rel=1e-9)


def test_the_factor_column_agrees_with_the_figure_the_page_states(
    history: pd.DataFrame, ranked: pd.DataFrame
) -> None:
    """The table and the sentence above it must not be able to disagree."""
    for row in history.itertuples():
        stated = inflation_adjustment(ranked, int(row.year)).factor
        assert row.factor == pytest.approx(stated, rel=1e-12)


def test_the_mean_index_column_is_the_panel_mean(
    history: pd.DataFrame, ranked: pd.DataFrame
) -> None:
    for row in history.itertuples():
        expected = ranked[ranked["year"] == row.year]["version_c"].astype(float).mean()
        assert row.mean_index == pytest.approx(expected)


def test_the_inflation_column_is_read_not_reconstructed(
    history: pd.DataFrame, ranked: pd.DataFrame
) -> None:
    """`policy_rate - real_rate` would re-round; the panel column must be the CPI."""
    for row in history.itertuples():
        published = ranked[ranked["year"] == row.year]["cpi_yoy_pct"].astype(float).median()
        assert row.inflation == pytest.approx(published, abs=1e-12)


# ── The level series carries the floor, which is why the copy changed ──


def test_the_floor_releasing_moves_the_level_more_than_affordability_does(
    history: pd.DataFrame,
) -> None:
    """The reason an unqualified cross-year reading is unsafe, measured.

    Between the last year the real-rate floor binds and the first year it does
    not, the national mean moves by a double-digit percentage with no change in
    any municipality's income or price. If that ever stops being true the copy
    can be relaxed — but it must be a measurement, not an assumption.
    """
    released = history[~history["real_floored"]]
    bound = history[history["real_floored"]]
    if released.empty or bound.empty:
        pytest.skip("this panel has no transition between floor states")

    last_bound = bound[bound["year"] < released["year"].max()]
    if last_bound.empty:
        pytest.skip("no bound year precedes the released one")

    before = float(last_bound.iloc[-1]["mean_index"])
    after = float(released.iloc[-1]["mean_index"])
    change = abs(after - before) / before * 100
    assert change > 10, (
        f"the mean index moves only {change:.1f} % across the floor release. If the "
        f"floor no longer dominates the level series, revisit the qualification the "
        f"copy on sidorna 01 and 02 now carries."
    )


@pytest.mark.parametrize(
    "key",
    ["rv.forklaring_kpi", "rv.antal_kommuner_med_z_poang_0_67", "lj.om_lansjamforelsen_text"],
)
def test_no_page_claims_unconditional_cross_year_comparability(key: str) -> None:
    """The exact phrasing that was wrong, banned rather than merely replaced."""
    value = SWEDISH_LABELS[key]
    banned = [
        "kan jämföras mellan år eftersom",
        "nivåserie och kan jämföras mellan år",
    ]
    found = [phrase for phrase in banned if phrase in value]
    assert not found, (
        f"{key} again claims index levels compare across years without qualification: "
        f"{found}. They compare only between years where the rate floor bound the same "
        f"way — the mean index fell by over a third the year the floor released."
    )


@pytest.mark.parametrize(
    "key", ["rv.forklaring_kpi", "rv.antal_kommuner_med_z_poang_0_67", "lj.om_lansjamforelsen_text"]
)
def test_each_qualified_claim_points_at_the_panel(key: str) -> None:
    """A qualification with nowhere to go is a hedge; this one names the evidence."""
    assert "räntegolvet" in SWEDISH_LABELS[key].lower(), (
        f"{key} qualifies the comparison but does not send the reader to the rate-floor "
        f"panel that shows why"
    )


# ── The documents that reproduce the table ───────────────────────────

#: Every document that states the floor quotient in prose. The APP_GUIDE copy of
#: the table is the one most likely to rot, being a hand-kept transcription of a
#: derived frame.
DOCS_QUOTING_THE_QUOTIENT = ("README.md", "docs/APP_GUIDE.md", "docs/METHODOLOGY.md")


@pytest.mark.parametrize("document", DOCS_QUOTING_THE_QUOTIENT)
def test_a_document_quoting_the_floor_quotient_quotes_the_derived_one(document: str) -> None:
    """0,20 is `NOMINAL_RATE_FLOOR_PP / REAL_RATE_FLOOR_PP` and nothing else."""
    quotient = NOMINAL_RATE_FLOOR_PP / REAL_RATE_FLOOR_PP
    rendered = f"{quotient:.2f}".replace(".", ",")
    text = (ROOT / document).read_text(encoding="utf-8")
    assert rendered in text, (
        f"{document} states the both-floors factor as something other than {rendered}. "
        f"Either a floor moved, in which case the panel copy and METHODOLOGY section 3 "
        f"move with it, or the prose drifted."
    )


def test_the_app_guide_table_matches_the_derived_one(history: pd.DataFrame) -> None:
    """APP_GUIDE reproduces `floor_history` as a markdown table; hold it to the frame.

    A transcribed table is exactly the kind of prose this project keeps finding
    wrong — the README's worked example was out by 4,7 years before anything
    re-derived it. Each row is checked for its year, its rounded rates, its
    factor and its mean index.
    """
    guide = (ROOT / "docs" / "APP_GUIDE.md").read_text(encoding="utf-8")
    block = guide.split("Which rate each formula actually divided by", 1)
    assert len(block) == 2, "the APP_GUIDE collapsible section has been renamed or removed"
    table = block[1].split("</details>", 1)[0]

    def sv(value: float, decimals: int) -> str:
        text = f"{value:.{decimals}f}"
        if float(text) == 0:
            text = text.lstrip("-")
        return text.replace("-", "−").replace(".", ",")

    for row in history.itertuples():
        expected = (
            f"| {row.year} | {sv(row.policy_rate, 2)} | {sv(row.inflation, 2)} | "
            f"{sv(row.real_rate, 2)} | "
        )
        assert expected in table, (
            f"APP_GUIDE's floor table no longer matches the data for {row.year}. "
            f"Expected a row beginning {expected!r}."
        )
        tail = table.split(expected, 1)[1].split("\n", 1)[0]
        assert f"{sv(row.factor, 2)}×" in tail, f"{row.year}: factor drifted in APP_GUIDE"
        assert sv(row.mean_index, 1) in tail, f"{row.year}: mean index drifted in APP_GUIDE"
