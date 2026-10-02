"""The README's demo table, re-derived from the artifacts it describes.

The README invites a reader to set the year to 2024 and check that their install
shows the same numbers. That promise is only worth making if the numbers are the
ones the app actually produces.

They were not, before this guard existed. Two saving times in the old worked
example were wrong by 4,7 and 2,9 years, and an apartment figure was 800 SEK
stale, while the cash and monthly figures beside them were correct. Nothing
re-derived any of them, so nobody noticed.

Every figure here is computed from `data/processed/` and from the same engine the
page calls, then looked for in the README as it is rendered there. A refresh that
moves a number fails this test rather than leaving the README quietly wrong.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.indices.agreement import inflation_adjustment, measure_agreement
from src.kontantinsats.engine import apply_regime
from src.scenario.simulator import simulate

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
PROCESSED = ROOT / "data" / "processed"

#: The year the README's demo table is written against.
DEMO_YEAR = 2024


def _artifact(name: str) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / name)


def _sv(value: float, decimals: int) -> str:
    """Swedish rendering: comma decimal, space thousands, as the README writes it."""
    text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return text


def _assert_in_readme(rendered: str, what: str) -> None:
    assert rendered in README, (
        f"the README no longer states {what} as {rendered!r}. The artifacts moved; "
        f"update the demo table in README.md to match."
    )


# ── Sida 01, the national KPI row ────────────────────────────────────


def test_national_mean_index_and_risk_count() -> None:
    year = _artifact("affordability_ranked.parquet").query("year == @DEMO_YEAR")

    _assert_in_readme(_sv(year["version_c"].mean(), 1), "the mean index")
    _assert_in_readme(
        f"{int((year['risk_c'] == 'hog').sum())} of {len(year)}", "the hög risk count"
    )
    _assert_in_readme(_sv(year["kt_ratio"].mean(), 2), "the mean K/T ratio")


@pytest.mark.parametrize("end", ["least", "most"])
def test_the_named_extremes_are_the_actual_extremes(end: str) -> None:
    """Named kommuner, not just counts: a sign flip would keep the counts intact."""
    year = _artifact("affordability_ranked.parquet").query("year == @DEMO_YEAR")
    # Higher z_c is worse, so the least affordable are the largest z.
    subset = year.nlargest(3, "z_c") if end == "least" else year.nsmallest(3, "z_c")

    for name in subset["region_name"]:
        _assert_in_readme(str(name), f"{name} among the {end} affordable")


# ── Sida 02, the agreement panel ─────────────────────────────────────


def test_formula_agreement_counts() -> None:
    agreement = measure_agreement(_artifact("affordability_ranked.parquet"), DEMO_YEAR)

    assert agreement.a_equals_c, (
        "A and C no longer produce the identical ranking. The README, Sida 02 and "
        "docs/ENGINE.md all explain why they must; revisit that copy first."
    )
    _assert_in_readme(str(agreement.counts["c"]["hog"]), "the C hög count")
    _assert_in_readme(str(agreement.counts["b"]["hog"]), "the B hög count")
    _assert_in_readme(
        f"{agreement.b_differs_from_c} of {agreement.n_kommuner}",
        "how often B disagrees with C",
    )


def test_the_inflation_adjustment_the_comparison_expander_states() -> None:
    """The factor replacing Version A's class-table row, re-derived.

    The README calls it the inflation adjustment, which is only what it is while
    neither rate floor binds — true for 2024, false for 2015 to 2023. If the demo
    year ever moves to a floored year, the wording has to move with it.
    """
    adjustment = inflation_adjustment(
        _artifact("affordability_municipal.parquet"), DEMO_YEAR
    )

    assert adjustment.is_national_constant, (
        "the C/A ratio is no longer one factor for the whole country, so neither "
        "the README nor Sida 02 may state it as a single number"
    )
    assert adjustment.is_an_inflation_adjustment, (
        f"in {DEMO_YEAR} a rate floor binds (R={adjustment.nominal_rate:.2f}, "
        f"real={adjustment.real_rate:.2f}), so C/A is a quotient of constants and "
        f"the README must stop calling it the inflation adjustment."
    )
    _assert_in_readme(f"{_sv(adjustment.factor, 2)}×", "the inflation adjustment")


# ── Sida 03, one kommun and its county projection ────────────────────


def test_stockholm_headline_figures() -> None:
    municipal = _artifact("affordability_municipal.parquet")
    row = municipal.query("region_name == 'Stockholm' and year == @DEMO_YEAR").iloc[0]

    _assert_in_readme(_sv(row["version_c"], 1), "Stockholm's index")
    _assert_in_readme(f"{_sv(row['median_income'], 0)} SEK", "Stockholm's median income")
    _assert_in_readme(_sv(row["kt_ratio"], 2), "Stockholm's K/T ratio")


def test_the_three_projection_scenarios_for_stockholms_lan() -> None:
    projection = _artifact("projection.parquet")
    first = DEMO_YEAR + 1

    stockholm = projection[
        (projection["lan_code"] == "01") & (projection["target_year"] == first)
    ]
    rendered = " / ".join(
        _sv(float(stockholm[stockholm["scenario"] == scenario]["version_c"].iloc[0]), 1)
        for scenario in ("floor", "current", "normalised")
    )
    _assert_in_readme(rendered, f"the three {first} projection scenarios")


# ── Sida 04, the mortgage engine ─────────────────────────────────────


def _kontantinsats(price: float, income: float) -> dict:
    national = _artifact("panel_national.parquet").query("year == @DEMO_YEAR").iloc[0]
    return apply_regime(
        price_sek=price,
        income_sek=income,
        rate=float(national["policy_rate"]) / 100.0,
        regime_key="latt_2026",
        savings_rate=0.10,
        bank_margin=0.017,
    )


def test_the_house_purchase_walkthrough() -> None:
    row = (
        _artifact("affordability_municipal.parquet")
        .query("region_name == 'Stockholm' and year == @DEMO_YEAR")
        .iloc[0]
    )
    result = _kontantinsats(
        float(row["transaction_price_sek"]), float(row["median_income"])
    )

    _assert_in_readme(f"{_sv(result['required_cash'], 0)} SEK", "the cash needed")
    _assert_in_readme(f"{_sv(result['years_to_save'], 1)} years", "the saving time")
    _assert_in_readme(f"{_sv(result['monthly_total'], 0)} SEK", "the monthly cost")


def test_the_apartment_purchase_moves_to_county_level() -> None:
    """Sida 04 switches geography for Bostadsrätt; the README says so and shows it."""
    county = (
        _artifact("affordability_county.parquet")
        .query("lan_code == '01' and year == @DEMO_YEAR")
        .iloc[0]
    )
    result = _kontantinsats(
        float(county["bostadsratt_price_sek"]), float(county["median_income"])
    )

    _assert_in_readme(f"{_sv(result['required_cash'], 0)} SEK", "the apartment cash")
    _assert_in_readme(
        f"{_sv(result['years_to_save'], 1)} years", "the apartment saving time"
    )


# ── Sida 05, the simulator ───────────────────────────────────────────


def test_the_two_percentage_point_rate_shock() -> None:
    county = (
        _artifact("panel_county.parquet")
        .query("lan_code == '01' and year == @DEMO_YEAR")
        .iloc[0]
    )
    result = simulate(
        county_kod="01",
        rate_shock=2.0,
        income_shock=0.0,
        price_shock=0.0,
        baseline_panel={
            "income": float(county["median_income"]),
            "transaction_price_sek": float(county["transaction_price_sek"]),
            "policy_rate": float(county["policy_rate"]),
            "cpi_yoy_pct": float(county["cpi_yoy_pct"]),
        },
    )

    _assert_in_readme(_sv(result["baseline_v_c"], 2), "the simulator baseline")
    _assert_in_readme(_sv(result["scenario_v_c"], 2), "the shocked value")
