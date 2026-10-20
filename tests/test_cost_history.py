"""The year-by-year cost history, the A-to-C factor and the level split.

Version C is `k · (P / I) · q`, where `q` — the yearly cost per krona borrowed —
is national. Three things follow, and each is shown on a page:

1. **The national mean factors exactly** into `q` and the mean price-to-income
   ratio, so a move in the mean index splits into financing and prices
   (`decompose_change`, the panel on Sidor 01, 02 and 06).
2. **C over A is one number per year**, `(r · 0,7 + 100 · a) / r`, stated on
   Sida 02 (`cost_adjustment`).
3. **The table in METHODOLOGY section 3** is this history, so a test compares
   them rather than trusting the document.

These replaced the floor-history tests. The old Version C divided by a real rate
floored at 0,5 pp, which bound in nine of eleven years and made the mean index
fall by a third the year it released. Neither cost formula has a floor.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd
import pytest

from src.indices.agreement import CostAdjustment, cost_adjustment, cost_history
from src.indices.cost_model import EARNERS, INTEREST_DEDUCTION, LOAN_TO_VALUE, amortisation_rate
from src.indices.decompose import EXACTNESS_TOLERANCE, decompose_change
from src.ui.interpret import explain_cost_adjustment
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_ranked.parquet"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(ARTIFACT)


@pytest.fixture(scope="module")
def history(ranked: pd.DataFrame) -> pd.DataFrame:
    return cost_history(ranked)


# ── 1. The history itself ────────────────────────────────────────────


def test_one_row_per_scored_year(history: pd.DataFrame, ranked: pd.DataFrame) -> None:
    assert history["year"].tolist() == sorted(ranked["year"].unique())


def test_the_cost_rate_is_net_interest_plus_amortisation(history: pd.DataFrame) -> None:
    for _, row in history.iterrows():
        expected = row["mortgage_rate"] * (1 - INTEREST_DEDUCTION) + 100 * amortisation_rate(
            int(row["year"])
        )
        assert row["cost_rate"] == pytest.approx(expected)


def test_no_rate_in_the_window_was_near_zero(history: pd.DataFrame) -> None:
    """The reason no floor is needed. If a refresh ever brings a rate under
    1 %, the absence of a floor needs revisiting before anything is published."""
    assert history["mortgage_rate"].min() > 1.0


def test_the_mean_index_is_the_cost_rate_times_price_to_income(history: pd.DataFrame) -> None:
    """The identity behind every split on the pages, held to the artifact."""
    k = 100 * LOAN_TO_VALUE / EARNERS / 100
    for _, row in history.iterrows():
        assert row["mean_index"] == pytest.approx(k * row["cost_rate"] * row["price_to_income"], rel=1e-12)


def test_the_same_identity_holds_for_version_a(ranked: pd.DataFrame, history: pd.DataFrame) -> None:
    k = 100 * LOAN_TO_VALUE / EARNERS / 100
    for _, row in history.iterrows():
        mean_a = ranked.loc[ranked["year"] == row["year"], "version_a"].mean()
        assert mean_a == pytest.approx(k * row["mortgage_rate"] * row["price_to_income"], rel=1e-12)


# ── 2. The split ─────────────────────────────────────────────────────


def test_every_consecutive_pair_reconciles(history: pd.DataFrame) -> None:
    years = history["year"].tolist()
    for a, b in zip(years, years[1:]):
        change = decompose_change(history, a, b)
        assert change is not None and change.is_exact, (a, b)
        assert change.residual <= EXACTNESS_TOLERANCE


def test_the_parts_multiply_rather_than_add(history: pd.DataFrame) -> None:
    change = decompose_change(history, 2021, 2023)
    product = (1 + change.rate_pct / 100) * (1 + change.price_to_income_pct / 100)
    assert product == pytest.approx(1 + change.total_pct / 100)


def test_the_2022_2023_rise_came_from_rates_and_prices_fell(history: pd.DataFrame) -> None:
    """The cycle the page is most often asked about, attributed the right way."""
    change = decompose_change(history, 2021, 2023)
    assert change.rate_pct > 0
    assert change.price_to_income_pct < 0
    assert change.rate_dominates


@pytest.mark.parametrize("pair", [(1999, 2024), (2024, 2099), (1999, 2099)])
def test_a_year_outside_the_panel_yields_no_split(history: pd.DataFrame, pair) -> None:
    assert decompose_change(history, *pair) is None


# ── 3. C over A ──────────────────────────────────────────────────────


def test_the_factor_is_one_number_per_year(ranked: pd.DataFrame) -> None:
    for year in sorted(ranked["year"].unique()):
        adjustment = cost_adjustment(ranked, int(year))
        assert adjustment.is_national_constant, year


def test_the_factor_is_deduction_and_amortisation_over_gross_interest(
    ranked: pd.DataFrame,
) -> None:
    for year in sorted(ranked["year"].unique()):
        a = cost_adjustment(ranked, int(year))
        expected = (a.mortgage_rate * (1 - INTEREST_DEDUCTION) + a.amortisation_pct) / a.mortgage_rate
        assert a.factor == pytest.approx(expected, rel=1e-9), year


def test_before_amortisation_the_factor_is_the_deduction_alone(ranked: pd.DataFrame) -> None:
    for year in (2014, 2015):
        assert cost_adjustment(ranked, year).factor == pytest.approx(1 - INTEREST_DEDUCTION)


def test_an_unscored_year_states_no_factor(ranked: pd.DataFrame) -> None:
    assert cost_adjustment(ranked, 1899).n_rows == 0


def test_a_missing_column_is_refused() -> None:
    with pytest.raises(KeyError, match="mortgage_rate"):
        cost_adjustment(pd.DataFrame({"year": [2024], "version_a": [1.0], "version_c": [1.0]}), 2024)


def test_the_sentence_states_the_parts_that_make_the_factor(ranked: pd.DataFrame) -> None:
    text = explain_cost_adjustment(cost_adjustment(ranked, 2024))
    assert text.lstrip().startswith("**Kassaflödesversionen är")
    assert "4,30 %" in text and "3,01 %" in text and "2,00 %" in text


def test_a_factor_that_is_not_national_is_reported_as_a_defect() -> None:
    broken = CostAdjustment(
        year=2024, factor=1.17, spread=0.2, n_rows=290, mortgage_rate=4.3, amortisation_pct=2.0
    )
    text = explain_cost_adjustment(broken)
    assert text.lstrip().startswith("**Skillnaden mellan A och C varierar")


# ── 4. The copy and the documents ────────────────────────────────────


def test_no_label_mentions_the_withdrawn_floor_as_current() -> None:
    """The floor survives in copy only as history, named as closed."""
    for key, text in SWEDISH_LABELS.items():
        if "golv" not in text.lower():
            continue
        assert key in {
            "mt.kassaflode_version_c_text",    # the formula's history
            "mt.id_begransning_atgard_f1_kommunal",  # F17, closed
        }, f"{key} still describes a rate floor"


def _methodology_table() -> list[list[str]]:
    text = (ROOT / "docs" / "METHODOLOGY.md").read_text(encoding="utf-8")
    start = text.index("| Year | Mortgage rate | Amortisation | Cost per krona | C / A | Mean C | Price / income |")
    rows = []
    for line in text[start:].splitlines()[2:]:
        if not line.startswith("|"):
            break
        rows.append([c.strip().strip("*") for c in line.strip("|").split("|")])
    return rows


def test_the_methodology_table_is_the_derived_history(history: pd.DataFrame) -> None:
    def sv(value: float, decimals: int) -> str:
        return f"{value:.{decimals}f}".replace(".", ",")

    table = _methodology_table()
    assert len(table) == len(history)
    for cells, (_, row) in zip(table, history.iterrows()):
        assert cells == [
            str(int(row["year"])),
            sv(row["mortgage_rate"], 2),
            sv(row["amortisation_pct"], 2),
            sv(row["cost_rate"], 2),
            sv(row["factor"], 2),
            sv(row["mean_index"], 1),
            sv(row["price_to_income"], 1),
        ], f"METHODOLOGY §3 row for {int(row['year'])} is stale"
