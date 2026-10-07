"""Every factual claim on Sida 06 that the data or the code can settle, settled.

The methodology page is the one place a reader goes to check the others, so it
cannot carry a sentence that was true on the day it was written. A review on
2026-10-07 found six that no longer were: a K/T coverage share, a "99 %" variance
figure, normality p-values, the years the real-rate floor bound, a limitation
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
FLOOR_PP = 0.5


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(RANKED)


def test_the_floor_years_quoted_for_version_c_are_the_floored_years(ranked: pd.DataFrame) -> None:
    text = SWEDISH_LABELS["mt.justerar_for_inflation_genom_realrantan"]
    first, last = map(int, re.search(r"Åren\s+(\d{4})–(\d{4})", text).groups())
    national = ranked.groupby("year")[["policy_rate", "cpi_yoy_pct"]].first()
    floored = sorted(national.index[(national.policy_rate - national.cpi_yoy_pct) < FLOOR_PP])
    assert floored == list(range(first, last + 1)), (
        f"the page says the floor bound {first}–{last}; the data says {floored}"
    )


def test_the_log_transform_claim_holds_every_year(ranked: pd.DataFrame) -> None:
    """Raw ratios fail normality every year; logged ratios fail it in none (5 %)."""
    for year, group in ranked.groupby("year"):
        assert stats.shapiro(group.version_c).pvalue < 0.05, f"raw C looks normal in {year}"
        assert stats.shapiro(np.log(group.version_c)).pvalue >= 0.05, (
            f"log C is rejected as normal in {year}"
        )


def test_the_real_rate_is_the_largest_driver_of_year_on_year_change(ranked: pd.DataFrame) -> None:
    """The projection text says so; check it against a variance decomposition."""
    data = ranked.sort_values(["region_code", "year"]).copy()
    data["rr"] = (data.policy_rate - data.cpi_yoy_pct).clip(lower=FLOOR_PP)
    by_muni = data.groupby("region_code")
    parts = pd.DataFrame({
        "income": by_muni.median_income.transform(lambda s: np.log(s).diff()),
        "price": -by_muni.transaction_price_sek.transform(lambda s: np.log(s).diff()),
        "real_rate": -by_muni.rr.transform(lambda s: np.log(s).diff()),
    }).dropna()
    total = parts.sum(axis=1)
    shares = {k: np.cov(parts[k], total)[0, 1] / total.var() for k in parts}
    assert max(shares, key=shares.get) == "real_rate", shares


def test_projection_parameters_match_the_page() -> None:
    text = SWEDISH_LABELS["mt.projektion_tre_scenarier_realranta"]
    assert f"{projection.INCOME_GROWTH:.0%}".replace("%", " %") in text
    assert f"{projection.PRICE_GROWTH:.0%}".replace("%", " %") in text
    assert "sex år" in text and projection.HORIZON == 6
    assert f"{projection.NORMALISED_REAL_RATE:.1f}".replace(".", ",") in text
    assert f"{projection.REAL_RATE_FLOOR:.1f}".replace(".", ",") in text


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
