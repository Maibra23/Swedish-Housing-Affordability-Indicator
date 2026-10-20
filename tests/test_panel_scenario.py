"""The national scenario view, and the property that forced its design.

Item 9 of `docs/APP_REFERENCE.md` (Part I) asked for the scenario to be applied across
all 290 municipalities rather than one county, so the page could answer "how many
kommuner cross into hög risk under this scenario".

Built the obvious way, by re-running the shock and re-ranking, the answer is
always **zero**. Every slider on Sida 05 multiplies each municipality's Version C
by the same constant, and a within-year z-score on logs removes a constant
factor exactly. `src/scenario/panel_scenario.py` therefore holds the class
boundaries fixed at the baseline year's distribution.

Two things need guarding, and the second is the unusual one:

1. That the fixed-boundary counts respond to a shock in the right direction and
   for the right reason.
2. **That the re-normalised version really is a no-op.** That is the premise the
   whole design rests on. If a future change made a shock non-uniform across
   municipalities, the fixed-boundary framing would become the wrong choice and
   the explanation shown to readers would be false. A property this load-bearing
   should not live only in a docstring.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.scenario.panel_scenario import (
    CLASS_LABELS,
    PanelShockOutcome,
    renormalised_rank_changes,
    shock_panel,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_ranked.parquet"

#: Every shock the page can apply, at its slider extremes.
SHOCKS = {
    "rate up": {"rate_shock": 4.0},
    "rate down": {"rate_shock": -2.0},
    "rate down to the minimum": {"rate_shock": -5.0},
    "income down": {"income_shock": -0.10},
    "price down": {"price_shock": -0.25},
    "everything at once": {
        "rate_shock": 5.0,
        "income_shock": -0.10,
        "price_shock": 0.25,
    },
}


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(ARTIFACT)


@pytest.fixture(scope="module")
def year(ranked: pd.DataFrame) -> int:
    return int(ranked["year"].max())


@pytest.mark.parametrize("name,shock", SHOCKS.items())
def test_a_uniform_shock_moves_no_rank_when_renormalised(
    ranked: pd.DataFrame, year: int, name: str, shock: dict
) -> None:
    """The premise behind holding the boundaries fixed.

    Every slider applies either a national rate in percentage points or a
    relative change to income or price. All three multiply each municipality's
    Version C by one constant, which a within-year z-score subtracts away. If
    this ever fails, a shock has become municipality-specific and
    `panel_scenario` needs redesigning rather than patching.
    """
    assert renormalised_rank_changes(ranked, year, **shock) == 0, (
        f"the {name} shock moved a rank under re-normalisation. Shocks are "
        f"supposed to be uniform across municipalities; one is no longer."
    )


def test_no_shock_leaves_the_panel_exactly_where_it_started(
    ranked: pd.DataFrame, year: int
) -> None:
    outcome = shock_panel(ranked, year)
    assert outcome.before == outcome.after
    assert outcome.crossed_into_hog == 0
    assert outcome.crossed_out_of_hog == 0
    assert outcome.median_c_before == pytest.approx(outcome.median_c_after)


def test_a_rate_rise_pushes_the_country_into_hog(
    ranked: pd.DataFrame, year: int
) -> None:
    outcome = shock_panel(ranked, year, rate_shock=4.0)
    assert outcome.rate_after == pytest.approx(outcome.rate_before + 4.0)
    assert outcome.median_c_after > outcome.median_c_before
    assert outcome.net_into_hog > 0
    assert outcome.crossed_out_of_hog == 0


def test_a_rate_cut_takes_municipalities_out_of_hog(
    ranked: pd.DataFrame, year: int
) -> None:
    outcome = shock_panel(ranked, year, rate_shock=-2.0)
    assert outcome.median_c_after < outcome.median_c_before
    assert outcome.net_into_hog < 0
    assert outcome.crossed_into_hog == 0


def test_income_against_the_rate_is_a_question_of_size(ranked: pd.DataFrame, year: int) -> None:
    """In 2024 the household pays 4,3 % × 0,7 + 2 % = 5,0 % of the loan a year.
    +0,5 pp adds 7 % to that, which 10 % more income outweighs; +1 pp adds 14 %,
    which it does not."""
    small = shock_panel(ranked, year, rate_shock=0.5, income_shock=0.10)
    large = shock_panel(ranked, year, rate_shock=1.0, income_shock=0.10)
    assert small.median_c_after < small.median_c_before
    assert large.median_c_after > large.median_c_before


@pytest.mark.parametrize("name,shock", SHOCKS.items())
def test_the_counts_always_describe_the_whole_panel(
    ranked: pd.DataFrame, year: int, name: str, shock: dict
) -> None:
    outcome = shock_panel(ranked, year, **shock)
    for counts in (outcome.before, outcome.after):
        assert sum(counts[cls] for cls in CLASS_LABELS) == outcome.n_kommuner, (
            f"{name}: risk classes do not account for every municipality"
        )


@pytest.mark.parametrize("name,shock", SHOCKS.items())
def test_crossings_and_net_movement_agree(
    ranked: pd.DataFrame, year: int, name: str, shock: dict
) -> None:
    """A municipality cannot both enter and leave under one uniform shock.

    Since every municipality's score moves the same direction by the same
    amount in logs, the crossings are one-way. Both directions appearing would
    mean the shock stopped being uniform.
    """
    outcome = shock_panel(ranked, year, **shock)
    assert not (outcome.crossed_into_hog and outcome.crossed_out_of_hog), name
    assert outcome.net_into_hog == outcome.crossed_into_hog - outcome.crossed_out_of_hog


def test_a_year_with_no_data_is_refused(ranked: pd.DataFrame) -> None:
    """Better an error than a confident count over zero municipalities."""
    with pytest.raises(ValueError, match="no scorable municipalities"):
        shock_panel(ranked, 1899)


def test_the_outcome_is_immutable(ranked: pd.DataFrame, year: int) -> None:
    outcome = shock_panel(ranked, year)
    assert isinstance(outcome, PanelShockOutcome)
    with pytest.raises(Exception):
        outcome.year = 1999  # type: ignore[misc]
