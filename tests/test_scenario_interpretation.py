"""What Sida 05 says about a scenario must agree with what the engine did.

The engine is exact; the validation run of 2026-10-05 found the problems in the
sentences around it:

1. **Floor absorption went unexplained.** On a floored baseline (every year
   2015–2023) a rate or CPI shock that leaves the real rate on the 0,5 pp floor
   changes nothing. The page said "oförändrad" and then warned that "hela
   ändringen räknas som real" — the opposite of what happened.
2. **The Riksbanken 2022 preset shows an improvement** with no explanation,
   which `docs/APP_GUIDE.md` section 5 item 2 asked to be captioned.
3. **A baseline just above the floor is fragile.** In 2024 the real rate is
   0,77 pp, so 0,1 pp of CPI revision moves Version C by about 13 %.
4. **The hög-risk count saturates**, so the national section needs a continuous
   measure beside it.

Baselines are written out rather than read from the artifact so the cases stay
in their regime when the data is refreshed. They are Stockholms län's values.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.scenario.panel_scenario import shock_panel
from src.scenario.presets import RIKSBANKEN_2022
from src.scenario.sections import explain_national_median
from src.scenario.simulator import simulate
from src.ui.interpret import interpret_scenario
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]

FLOORED = {  # 2022: R - pi = -7,58 pp
    "income": 370_200.0, "transaction_price_sek": 7_136_000.0,
    "policy_rate": 0.7678, "cpi_yoy_pct": 8.35,
}
NEAR_FLOOR = {  # 2024: R - pi = +0,77 pp
    "income": 400_500.0, "transaction_price_sek": 6_748_000.0,
    "policy_rate": 3.6285, "cpi_yoy_pct": 2.8583,
}
CLEAR_OF_FLOOR = dict(NEAR_FLOOR, cpi_yoy_pct=2.2)  # R - pi = +1,43 pp, like 2025


def _texts(baseline: dict, rate=0.0, income=0, price=0, cpi=0.0) -> list[str]:
    result = simulate("01", rate, income / 100, price / 100, baseline, cpi_shock=cpi)
    findings = interpret_scenario(
        result=result, rate_shock=rate, income_shock_pct=income,
        price_shock_pct=price, cpi_shock=cpi,
    )
    return [f.text for f in findings]


def _says(texts: list[str], key: str) -> bool:
    """Whether any finding was built from `key`, matched on its fixed lead-in."""
    lead = SWEDISH_LABELS[key].split("{")[0]
    return any(t.startswith(lead) for t in texts)


# ── 1. Floor absorption ──────────────────────────────────────────────


def test_a_shock_the_floor_absorbs_is_named_as_such() -> None:
    texts = _texts(FLOORED, rate=4.0)
    assert _says(texts, "sc.tolk_golv_absorberar")


def test_the_real_change_warning_is_not_shown_when_nothing_changed() -> None:
    """The warning claims the whole move counts as real; under the floor none does."""
    assert not _says(_texts(FLOORED, rate=4.0), "sc.tolk_ranta_utan_inflation")


def test_the_real_change_warning_still_shows_off_the_floor() -> None:
    texts = _texts(NEAR_FLOOR, rate=4.0)
    assert _says(texts, "sc.tolk_ranta_utan_inflation")
    assert not _says(texts, "sc.tolk_golv_absorberar")


def test_a_shock_that_lifts_the_rate_off_the_floor_is_not_called_absorbed() -> None:
    # -7,58 + 5 + 5 = +2,42 pp, clear of the floor.
    texts = _texts(FLOORED, rate=5.0, cpi=-5.0)
    assert not _says(texts, "sc.tolk_golv_absorberar")
    assert _says(texts, "sc.tolk_realranta")


def test_an_income_shock_alone_says_nothing_about_the_floor() -> None:
    assert not _says(_texts(FLOORED, income=5), "sc.tolk_golv_absorberar")


def test_the_absorption_note_quotes_the_unfloored_scenario_rate() -> None:
    texts = _texts(FLOORED, rate=4.0)
    # 0,7678 + 4 - 8,35 = -3,58
    assert any("−3,58" in t for t in texts)


# ── 2. The Riksbanken 2022 preset ────────────────────────────────────


def _preset_texts(baseline: dict) -> list[str]:
    p = RIKSBANKEN_2022
    return _texts(baseline, rate=p["rate"], income=p["income"], price=p["price"], cpi=p["cpi"])


@pytest.mark.parametrize("baseline", [FLOORED, NEAR_FLOOR], ids=["2022", "2024"])
def test_the_2022_preset_explains_its_improvement(baseline: dict) -> None:
    assert _says(_preset_texts(baseline), "sc.tolk_preset_2022")


def test_the_preset_note_needs_the_preset_exactly() -> None:
    p = RIKSBANKEN_2022
    texts = _texts(NEAR_FLOOR, rate=p["rate"], price=p["price"], cpi=p["cpi"] - 0.5)
    assert not _says(texts, "sc.tolk_preset_2022")


def test_the_preset_still_improves_affordability() -> None:
    """The caption explains an improvement; if the preset stops producing one, it is wrong."""
    p = RIKSBANKEN_2022
    for baseline in (FLOORED, NEAR_FLOOR):
        result = simulate("01", p["rate"], p["income"] / 100, p["price"] / 100,
                          baseline, cpi_shock=p["cpi"])
        assert result["delta"] > 0


def test_the_page_uses_the_shared_preset_values() -> None:
    page = (ROOT / "pages" / "05_Scenario.py").read_text()
    assert '"riksbanken_2022": RIKSBANKEN_2022' in page


# ── 3. Near-floor fragility ──────────────────────────────────────────


def test_a_baseline_just_above_the_floor_is_flagged() -> None:
    texts = _texts(NEAR_FLOOR, income=1)
    assert _says(texts, "sc.tolk_nara_golvet")
    # 0,1 / 0,77 = 13 %
    assert any("13 %" in t for t in texts)


def test_the_fragility_warning_shows_before_any_slider_moves() -> None:
    assert _says(_texts(NEAR_FLOOR), "sc.tolk_nara_golvet")


@pytest.mark.parametrize("baseline", [FLOORED, CLEAR_OF_FLOOR], ids=["floored", "clear"])
def test_other_baselines_are_not_flagged(baseline: dict) -> None:
    assert not _says(_texts(baseline, income=1), "sc.tolk_nara_golvet")
    assert not _says(_texts(baseline), "sc.tolk_nara_golvet")


# ── 4. The national median beside the class counts ───────────────────


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(ROOT / "data" / "processed" / "affordability_ranked.parquet")


def test_the_median_moves_when_the_counts_have_saturated(ranked: pd.DataFrame) -> None:
    outcome = shock_panel(ranked, 2024, rate_shock=5.0)
    assert outcome.after["hog"] == outcome.n_kommuner  # saturated
    text = explain_national_median(outcome)
    assert text is not None
    assert "−" in text  # a fall, written with a typographic minus


def test_the_median_is_silent_without_a_shock(ranked: pd.DataFrame) -> None:
    assert explain_national_median(shock_panel(ranked, 2024)) is None


def test_the_median_is_silent_when_the_floor_absorbs_the_shock(ranked: pd.DataFrame) -> None:
    assert explain_national_median(shock_panel(ranked, 2022, rate_shock=4.0)) is None
