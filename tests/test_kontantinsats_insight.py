"""The Nyckelinsikt card must state the engine's numbers and compare like with like.

Its predecessor compared the cheapest regime with the dearest, quoted "56 %
billigare" where the cheaper option was 36 % cheaper, and called the regime with
no amortisation the most favourable. See `src/kontantinsats/insight.py`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.kontantinsats.engine import BASELINE_REGIME, compare_regimes
from src.kontantinsats.insight import PREVIOUS_REGIME, InsightInputs, insight_paragraphs
from src.ui.components import format_sek
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def stockholm() -> pd.Series:
    data = pd.read_parquet(ROOT / "data" / "processed" / "affordability_municipal.parquet")
    return data[(data.region_name == "Stockholm") & (data.year == 2024)].iloc[0]


def _inputs(row: pd.Series, earners: int = 1) -> InsightInputs:
    income = row.median_income * earners
    results = compare_regimes(row.transaction_price_sek, income, row.policy_rate / 100, 0.10, 0.017)
    return InsightInputs(
        results=results, household_label="singelhushåll", region="Stockholm",
        year=2024, savings_rate=0.10, monthly_income=income / 12,
    )


def test_every_figure_is_the_engines(stockholm: pd.Series) -> None:
    inputs = _inputs(stockholm)
    text = " ".join(insight_paragraphs(inputs))
    today, before = inputs.results[BASELINE_REGIME], inputs.results[PREVIOUS_REGIME]
    for value in (
        today["required_cash"], today["monthly_total"], today["annual_interest"] / 12,
        today["annual_amort"] / 12, before["required_cash"], before["monthly_total"],
        before["annual_amort"] / 12,
    ):
        assert format_sek(value) in text, f"{format_sek(value)} missing from the card"


def test_interest_and_amortisation_add_up_to_the_payment(stockholm: pd.Series) -> None:
    today = _inputs(stockholm).results[BASELINE_REGIME]
    assert today["annual_interest"] + today["annual_amort"] == pytest.approx(today["annual_total"])


def test_an_unaffordable_payment_is_called_unaffordable(stockholm: pd.Series) -> None:
    """Stockholm, one income: the payment is about 137 % of gross income."""
    paragraphs = insight_paragraphs(_inputs(stockholm))
    lead = SWEDISH_LABELS["ki.insikt_over_inkomst"][:40]
    assert any(p.startswith(lead) for p in paragraphs)


def test_a_payment_within_income_is_not_called_unaffordable(stockholm: pd.Series) -> None:
    paragraphs = insight_paragraphs(_inputs(stockholm, earners=2))
    lead = SWEDISH_LABELS["ki.insikt_over_inkomst"][:40]
    assert not any(p.startswith(lead) for p in paragraphs)


def test_the_withdrawn_claims_are_gone() -> None:
    copy = " ".join(v for k, v in SWEDISH_LABELS.items() if k.startswith("ki.insikt"))
    assert "förmånligaste" not in copy and "billigare" not in copy
    assert "sparande, inte en kostnad" in copy
