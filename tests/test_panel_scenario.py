"""The national scenario view, and the property that forced its design.

Item 9 of `docs/ANALYSIS_GUIDE.md` asked for the scenario to be applied across
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
    "rate and inflation together": {"rate_shock": 4.0, "cpi_shock": 8.0},
    "inflation only": {"cpi_shock": 10.0},
    "income down": {"income_shock": -0.10},
    "price down": {"price_shock": -0.25},
    "everything at once": {
        "rate_shock": 5.0,
        "cpi_shock": -5.0,
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
    relative change to income or price. All four multiply each municipality's
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


def test_a_rate_rise_alone_pushes_the_country_into_hog(
    ranked: pd.DataFrame, year: int
) -> None:
    """Holding inflation still makes the whole nominal move a real one."""
    outcome = shock_panel(ranked, year, rate_shock=4.0)
    assert outcome.real_rate_after > outcome.real_rate_before
    assert outcome.net_into_hog > 0
    assert outcome.crossed_out_of_hog == 0


def test_the_same_rate_rise_with_inflation_improves_the_country(
    ranked: pd.DataFrame, year: int
) -> None:
    """The page's whole lesson, now at national scale.

    Identical nominal rate rise, opposite national outcome, because the second
    scenario moves inflation with it. A reader who only ever moves the rate
    slider sees the first and concludes rate rises destroy affordability.
    """
    rate_only = shock_panel(ranked, year, rate_shock=4.0)
    with_inflation = shock_panel(ranked, year, rate_shock=4.0, cpi_shock=8.0)

    assert rate_only.net_into_hog > 0
    assert with_inflation.net_into_hog < 0
    assert with_inflation.real_rate_after < rate_only.real_rate_after


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
