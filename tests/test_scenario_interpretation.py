"""What Sida 05 says about a scenario must agree with what the engine did.

The engine is exact; the sentences around it are where a page goes wrong. Until
2026-10-20 most of this file guarded the real-rate floor: shocks the floor
absorbed, a baseline that sat just above it, and a "Riksbanken 2022" preset that
improved affordability because inflation outran the rate. Version C is now a
cash-flow share with no floor, so those cases are gone and what is left to guard
is:

1. **Direction.** C is a cost share, so a rise must be called a rise in cost,
   in the warning colour, never an improvement.
2. **The rate slider's limit.** It moves the mean rate on new mortgages, not
   the policy rate, and the page must say so whenever the rate moves (F12).
3. **The 2021–23 preset** must still match the panel's annual means.
4. **The hög-risk count saturates**, so the national section needs a
   continuous measure beside it.

Baselines are written out rather than read from the artifact so the cases stay
put when the data is refreshed. They are Stockholms län's 2024 values.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.scenario.panel_scenario import shock_panel
from src.scenario.presets import RATE_CYCLE_2021_23
from src.scenario.sections import explain_national_median
from src.scenario.simulator import simulate
from src.ui.interpret import interpret_scenario
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]

STOCKHOLM_2024 = {
    "income": 400_500.0, "transaction_price_sek": 6_748_000.0,
    "mortgage_rate": 4.2962, "year": 2024,
}


def _findings(baseline: dict, rate=0.0, income=0, price=0):
    result = simulate("01", rate, income / 100, price / 100, baseline)
    return interpret_scenario(
        result=result, rate_shock=rate, income_shock_pct=income, price_shock_pct=price,
    )


def _texts(baseline: dict, **shocks) -> list[str]:
    return [f.text for f in _findings(baseline, **shocks)]


def _says(texts: list[str], key: str) -> bool:
    """Whether any finding was built from `key`, matched on its fixed lead-in."""
    lead = SWEDISH_LABELS[key].split("{")[0]
    return any(t.startswith(lead) for t in texts)


# ── 1. Direction ─────────────────────────────────────────────────────


def test_a_rate_rise_is_a_rise_in_cost_and_a_warning() -> None:
    first = _findings(STOCKHOLM_2024, rate=2.0)[0]
    assert first.level == "warning"
    assert first.text.startswith(SWEDISH_LABELS["sc.tolk_riktning_upp"].split("{")[0])


def test_a_price_fall_is_a_fall_in_cost_and_good() -> None:
    first = _findings(STOCKHOLM_2024, price=-10)[0]
    assert first.level == "good"
    assert first.text.startswith(SWEDISH_LABELS["sc.tolk_riktning_ner"].split("{")[0])


def test_no_scenario_says_so_and_nothing_else() -> None:
    assert _texts(STOCKHOLM_2024) == [SWEDISH_LABELS["sc.tolk_inget_scenario"]]


# ── 2. The rate slider's limit ───────────────────────────────────────


def test_a_rate_shock_names_the_rate_it_moves() -> None:
    texts = _texts(STOCKHOLM_2024, rate=1.0)
    assert _says(texts, "sc.tolk_bindningstid")
    assert any("4,30 %" in t and "5,30 %" in t for t in texts)


def test_an_income_shock_alone_says_nothing_about_fixation() -> None:
    assert not _says(_texts(STOCKHOLM_2024, income=5), "sc.tolk_bindningstid")


def test_a_rate_held_at_the_minimum_is_named() -> None:
    texts = _texts(STOCKHOLM_2024, rate=-5.0)
    assert any(t.startswith("Räntan hålls på 0,5 %") for t in texts)


# ── 3. The 2021–23 preset ────────────────────────────────────────────


def _preset_texts() -> list[str]:
    p = RATE_CYCLE_2021_23
    return _texts(STOCKHOLM_2024, rate=p["rate"], income=p["income"], price=p["price"])


def test_the_preset_says_where_its_numbers_come_from() -> None:
    assert _says(_preset_texts(), "sc.tolk_preset_cykel")


def test_the_preset_note_needs_the_preset_exactly() -> None:
    p = RATE_CYCLE_2021_23
    texts = _texts(STOCKHOLM_2024, rate=p["rate"] - 0.25, income=p["income"], price=p["price"])
    assert not _says(texts, "sc.tolk_preset_cykel")


def test_the_preset_raises_the_cost() -> None:
    """What households lived through. The old real-rate preset showed the opposite."""
    p = RATE_CYCLE_2021_23
    result = simulate("01", p["rate"], p["income"] / 100, p["price"] / 100, STOCKHOLM_2024)
    assert result["delta"] > 0


def test_the_preset_matches_the_panel_rounded_to_slider_steps() -> None:
    national = pd.read_parquet(ROOT / "data" / "processed" / "panel_national.parquet")
    n = national.set_index("year")
    rate = n.loc[2023, "mortgage_rate"] - n.loc[2021, "mortgage_rate"]
    income = (n.loc[2023, "median_income"] / n.loc[2021, "median_income"] - 1) * 100
    price = (n.loc[2023, "transaction_price_sek"] / n.loc[2021, "transaction_price_sek"] - 1) * 100
    assert RATE_CYCLE_2021_23["rate"] == round(rate * 4) / 4
    assert RATE_CYCLE_2021_23["income"] == round(income)
    assert RATE_CYCLE_2021_23["price"] == 5 * round(price / 5)


def test_the_page_uses_the_shared_preset_values() -> None:
    page = (ROOT / "pages" / "05_Scenario.py").read_text()
    assert "RATE_CYCLE_2021_23)" in page


# ── 4. The national median beside the class counts ───────────────────


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(ROOT / "data" / "processed" / "affordability_ranked.parquet")


def test_the_median_rises_under_a_rate_shock(ranked: pd.DataFrame) -> None:
    outcome = shock_panel(ranked, 2024, rate_shock=5.0)
    text = explain_national_median(outcome)
    assert text is not None
    assert "+" in text


def test_the_median_is_silent_without_a_shock(ranked: pd.DataFrame) -> None:
    assert explain_national_median(shock_panel(ranked, 2024)) is None
