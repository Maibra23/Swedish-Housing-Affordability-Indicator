"""Every factual claim on Sida 06 that the data or the code can settle, settled.

The methodology page is the one place a reader goes to check the others, so it
cannot carry a sentence that was true on the day it was written. A review on
2026-10-07 found six that no longer were: a K/T coverage share, a "99 %" variance
figure, normality p-values, the years the (since withdrawn) real-rate floor bound, a limitation
saying the simulator held inflation constant after a CPI slider was added, and
a reference link that had started returning 404. Each claim below is re-derived
rather than restated.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src import projection
from src.kontantinsats.engine import REGIMES
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]
RANKED = ROOT / "data" / "processed" / "affordability_ranked.parquet"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(RANKED)


def test_the_cash_flow_formula_has_no_floor_to_quote(ranked: pd.DataFrame) -> None:
    """The page says the mortgage rate stayed between 1,5 and 4,5 %; that range
    is why no floor is needed, so it is checked rather than trusted."""
    text = SWEDISH_LABELS["mt.kassaflode_version_c_text"]
    low, high = re.search(r"mellan (\d,\d) och (\d,\d) %", text).groups()
    rates = ranked.groupby("year")["mortgage_rate"].first()
    assert float(low.replace(",", ".")) == round(rates.min(), 1)
    assert float(high.replace(",", ".")) == round(rates.max(), 1)


def test_the_log_transform_claim_holds_every_year(ranked: pd.DataFrame) -> None:
    """Raw ratios fail normality every year; logged ratios fail it in none (5 %)."""
    for year, group in ranked.groupby("year"):
        assert stats.shapiro(group.version_c).pvalue < 0.05, f"raw C looks normal in {year}"
        assert stats.shapiro(np.log(group.version_c)).pvalue >= 0.05, (
            f"log C is rejected as normal in {year}"
        )


def test_the_rate_is_the_largest_driver_of_year_on_year_change(ranked: pd.DataFrame) -> None:
    """The projection text says so, with shares; check them against a variance
    decomposition of log C from the first full amortisation year on."""
    from src.indices.kommun_components import cost_rate

    data = ranked[ranked["year"] >= 2017].sort_values(["region_code", "year"]).copy()
    data["q"] = cost_rate(data)
    by_muni = data.groupby("region_code")
    parts = pd.DataFrame({
        "income": -by_muni.median_income.transform(lambda s: np.log(s).diff()),
        "price": by_muni.transaction_price_sek.transform(lambda s: np.log(s).diff()),
        "rate": by_muni.q.transform(lambda s: np.log(s).diff()),
    }).dropna()
    total = parts.sum(axis=1)
    shares = {k: np.cov(parts[k], total)[0, 1] / total.var() for k in parts}
    assert max(shares, key=shares.get) == "rate", shares
    text = SWEDISH_LABELS["kd.projektion_mer_text"]
    assert f"ungefär {round(shares['rate'], 1) * 100:.0f} procent" in text, shares
    assert f"mot {round(shares['price'], 1) * 100:.0f} för priset" in text, shares


def test_projection_parameters_match_the_page() -> None:
    text = SWEDISH_LABELS["mt.projektion_tre_scenarier_bolaneranta"]
    assert f"{projection.INCOME_GROWTH:.0%}".replace("%", " %") in text
    assert f"{projection.PRICE_GROWTH:.0%}".replace("%", " %") in text
    assert "sex år" in text and projection.HORIZON == 6
    assert f"{projection.HIGH_MORTGAGE_RATE:.0f} %" in text


def test_the_regime_table_matches_the_engine() -> None:
    table = SWEDISH_LABELS["mt.regelverk_period_kontantinsats"]
    for regime in REGIMES.values():
        row = next((line for line in table.splitlines() if f"| {regime['label']} |" in line), None)
        assert row, f"regime {regime['label']!r} missing from the methodology table"
        assert regime["period"] in row, f"{regime['label']}: period differs from the engine"
        down = regime["min_down_pct"]
        if down:
            assert f"{down:.0%}".replace("%", " %") in row, f"{regime['label']}: down payment differs"


#: An SCB or Kolada table code, as the pages used to print them.
TABLE_CODE = re.compile(r"\b(?:BO0[15]0\d\w*|HE0110\w*|PR0101\w*|BE0101\w*|N03937)\b")


@pytest.mark.parametrize("prefix", ["ki.", "kd.", "sc.", "rv.", "lj."])
def test_table_codes_appear_only_on_the_methodology_page(prefix: str) -> None:
    offenders = {
        key: TABLE_CODE.findall(value)
        for key, value in SWEDISH_LABELS.items()
        if key.startswith(prefix) and TABLE_CODE.search(value)
    }
    assert not offenders, f"source table codes belong on Sida 06 only: {offenders}"
