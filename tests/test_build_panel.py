"""The panel builder, which had no tests and builds everything else.

R5 and R10, which are one problem wearing two hats. `build_panel.py` is where
ten raw SCB and Kolada tables become the three panels every page, index and
forecast reads. It held 0 % coverage while being the largest module in the
project, and the register's standing recommendation was "tests before splitting,
in that order... the way out is coverage, not courage".

This is that coverage. `scb_client.py` took the same route on 2026-09-21: it
gained tests, the split became safe, and it left the file-size exemption.

**Why this module deserves tests specifically.** Everything it does is a *join*,
and a wrong join produces a well-formed panel. Both defects found on 2026-09-21
lived one layer up, in what was fetched, and were invisible to a suite that
checked shape. The joins here are worse in one respect: they are where a
deliberate approximation happens. County price indices are broadcast to every
municipality (F1), the national policy rate is used at all three levels (F2),
K/T and transaction prices fall back to county values when a municipality has
none, and income is forward-filled past its vintage at 3 %/yr (F9). Each is a
documented decision, and each is exactly the kind of thing that silently becomes
something else when a merge key or a fillna moves.

**How these tests work.** `_read` is the single I/O seam: every cleaner goes
through it, and `data/raw/` is gitignored, so the tests cannot depend on it.
Patching that one function with synthetic frames in SCB's own column shapes lets
the whole builder run in-process with data whose every value is known. The
fixtures are deliberately small — three municipalities across two counties — so
that a broken join is visible as a wrong number rather than a wrong row count.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data import build_panel as bp
from src.data import clean_sources as cs
from tests.panel_fixtures import COUNTIES, MUNICIPALITIES, RAW, YEARS

# ---------------------------------------------------------------------------
# The single I/O seam
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_raw(monkeypatch, tmp_path):
    """Patch the module's single I/O seam.

    `_read` is the only door to `data/raw/`, which is gitignored, so this is what
    makes the builder testable at all. `RAW_DIR` is redirected too because
    `_clean_bostadsratt_price` probes the filesystem directly to decide whether
    apartment prices exist yet.
    """
    # Patched on **both** modules, and the reason is the R10 split itself.
    # `clean_sources` owns `_read`, so the cleaners resolve it there. But
    # `build_county_panel` also calls `_read` directly, for Kolada's all-regions
    # table, and resolves the re-exported name in `build_panel`'s own namespace.
    # Patching one and not the other leaves half the builder reading the real
    # `data/raw/`. These tests caught that the moment the split landed, which is
    # what they were written for.
    reader = lambda name: RAW[name]().copy()  # noqa: E731
    monkeypatch.setattr(cs, "_read", reader)
    monkeypatch.setattr(bp, "_read", reader)
    monkeypatch.setattr(cs, "RAW_DIR", tmp_path)
    (tmp_path / "BO0501C_bostadsratt_price.parquet").write_bytes(b"")
    return tmp_path


@pytest.fixture
def municipal(fake_raw) -> pd.DataFrame:
    return bp.build_municipal_panel()


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def test_build_panel_still_re_exports_the_cleaners() -> None:
    """The split kept one import surface. Anything importing a cleaner from
    `build_panel` — `build_all`, and these tests — must keep working."""
    for name in ("_read", "_clean_income", "_clean_cpi", "_parse_month_tid"):
        assert getattr(bp, name) is getattr(cs, name), f"{name} is not re-exported"


@pytest.mark.parametrize("kod,expected", [("0180", "01"), ("2584", "25"), ("0880", "08")])
def test_a_municipality_maps_to_its_county_by_prefix(kod: str, expected: str) -> None:
    assert bp._kommun_to_lan(kod) == expected


def test_period_codes_parse() -> None:
    assert bp._parse_month_tid("2024M03") == (2024, 3)
    assert bp._parse_quarter_tid("2024K3") == (2024, 3)


def test_regions_are_split_by_code_length() -> None:
    """Two-digit codes are counties, four-digit are municipalities, 00 is Sweden.

    The whole panel's shape follows from this, because income is the spine: a
    code that lands in the wrong bucket becomes a municipality that is really a
    county, carrying county-level values into a municipal ranking.
    """
    national, counties, municipalities = bp._identify_regions(
        pd.DataFrame({"region_code": ["00", "01", "08", "0180", "0181", "0880"]})
    )
    assert national == ["00"]
    assert counties == ["01", "08"]
    assert municipalities == ["0180", "0181", "0880"]


# ---------------------------------------------------------------------------
# Cleaners
# ---------------------------------------------------------------------------

def test_income_is_converted_from_tkr_to_kronor(fake_raw) -> None:
    income = bp._clean_income()
    row = income[(income["region_code"] == "0180") & (income["year"] == 2023)]
    assert float(row["median_income_tkr"].iloc[0]) == 410.0
    assert float(row["median_income"].iloc[0]) == 410_000.0


def test_the_combined_kalmar_gotland_price_index_is_split(fake_raw) -> None:
    """SCB publishes 08+09 as one row. Both counties must receive it.

    Left unsplit, every municipality in two counties joins to nothing and loses
    its price index silently.
    """
    price_index = bp._clean_price_index()
    assert "08+09" not in set(price_index["lan_code"])
    for code in ("08", "09"):
        values = price_index[price_index["lan_code"] == code]["price_index"]
        assert len(values) == len(YEARS)
        assert (values == 150.0).all()


def test_only_annual_kt_rows_survive(fake_raw) -> None:
    """The raw table carries quarterly rows too, and averaging them in would
    move every K/T ratio without changing a single row count."""
    kt = bp._clean_kt_ratio()
    assert 99.0 not in set(kt["kt_ratio"])
    assert set(kt["year"]) == set(YEARS)


def test_transaction_price_filters_to_permanent_houses_and_scales_to_kronor(
    fake_raw,
) -> None:
    txn = bp._clean_transaction_price()
    row = txn[(txn["region_code"] == "0180") & (txn["year"] == 2023)]
    assert float(row["transaction_price_sek"].iloc[0]) == 8_000_000.0
    # Fastighetstyp 210 was in the raw table and must not appear.
    assert 1_000.0 not in set(txn["transaction_price_sek"])


def test_bostadsratt_is_county_only(fake_raw) -> None:
    """SCB publishes no municipal apartment prices, and the storstad codes are
    aggregates that would double-count."""
    br = bp._clean_bostadsratt_price()
    assert set(br["region_code"]) == {"01", "08"}


def test_monthly_cpi_becomes_an_annual_average(fake_raw) -> None:
    cpi = bp._clean_cpi()
    assert set(cpi["year"]) == set(YEARS)
    assert float(cpi[cpi["year"] == 2023]["cpi_yoy_pct"].iloc[0]) == pytest.approx(2.0)


def test_the_policy_rate_becomes_an_annual_average(fake_raw) -> None:
    rate = bp._clean_policy_rate()
    assert float(rate[rate["year"] == 2023]["policy_rate"].iloc[0]) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# The municipal panel: the joins and the documented approximations
# ---------------------------------------------------------------------------

def test_every_municipality_and_year_appears_exactly_once(municipal: pd.DataFrame) -> None:
    """Income is the spine, so a duplicated merge key shows up here first."""
    assert not municipal.duplicated(subset=["region_code", "year"]).any()
    observed = municipal[~municipal["is_imputed_income"]]
    assert set(observed["region_code"]) == set(MUNICIPALITIES)
    assert set(observed["year"]) == set(YEARS)


def test_counties_do_not_leak_into_the_municipal_panel(municipal: pd.DataFrame) -> None:
    assert (municipal["region_code"].str.len() == 4).all()


def test_the_county_price_index_reaches_every_municipality(
    municipal: pd.DataFrame,
) -> None:
    """Limitation F1, asserted rather than described.

    There is no municipal price index, so each municipality carries its county's.
    Stockholm's two municipalities must both read 200; Kalmar's must read the
    value that only existed as a combined 08+09 row upstream.
    """
    observed = municipal[~municipal["is_imputed_income"]]
    for code, expected in (("0180", 200.0), ("0181", 200.0), ("0880", 150.0)):
        values = observed[observed["region_code"] == code]["price_index"]
        assert (values == expected).all(), f"{code} has price index {set(values)}"


def test_the_national_rate_and_cpi_reach_every_municipality(
    municipal: pd.DataFrame,
) -> None:
    """Limitation F2. One national rate at all three levels."""
    observed = municipal[~municipal["is_imputed_income"]]
    for year, rate in ((2022, 1.0), (2023, 2.0)):
        rows = observed[observed["year"] == year]
        assert (rows["policy_rate"] == rate).all()
        assert (rows["cpi_yoy_pct"] == 2.0).all()


def test_a_municipality_without_its_own_kt_inherits_its_county(
    municipal: pd.DataFrame,
) -> None:
    """And the flag says which is which, so the fallback is visible downstream."""
    observed = municipal[~municipal["is_imputed_income"]]
    native = observed[observed["region_code"] == "0180"]
    fallback = observed[observed["region_code"] == "0181"]
    assert native["has_native_kt"].all()
    assert (native["kt_ratio"] == 3.0).all()
    assert not fallback["has_native_kt"].any()
    assert (fallback["kt_ratio"] == 2.0).all()


def test_a_municipality_without_its_own_price_inherits_its_county(
    municipal: pd.DataFrame,
) -> None:
    observed = municipal[~municipal["is_imputed_income"]]
    native = observed[observed["region_code"] == "0180"]
    fallback = observed[observed["region_code"] == "0181"]
    assert native["has_native_price"].all()
    assert (native["transaction_price_sek"] == 8_000_000.0).all()
    assert not fallback["has_native_price"].any()
    assert (fallback["transaction_price_sek"] == 7_000_000.0).all()


def test_every_municipality_inherits_its_county_apartment_price(
    municipal: pd.DataFrame,
) -> None:
    observed = municipal[~municipal["is_imputed_income"]]
    for code, expected in (("0180", 5_000_000.0), ("0181", 5_000_000.0), ("0880", 1_500_000.0)):
        values = observed[observed["region_code"] == code]["bostadsratt_price_sek"]
        assert (values == expected).all()


# ---------------------------------------------------------------------------
# F9: the income forward-fill
# ---------------------------------------------------------------------------

def test_income_is_forward_filled_past_its_vintage_and_flagged(
    municipal: pd.DataFrame,
) -> None:
    """Limitation F9. The flag is what keeps imputed rows out of the index.

    `complete_case()` filters on it before scoring, and the year selector stops
    at `complete_case_max_year()`. An unflagged imputed row would be scored and
    rendered as though it were observed.
    """
    imputed = municipal[municipal["is_imputed_income"]]
    assert not imputed.empty, "income was not extended past its last observed year"
    assert imputed["year"].min() > max(YEARS)
    assert not municipal[municipal["year"].isin(YEARS)]["is_imputed_income"].any()


def test_the_forward_fill_compounds_at_the_documented_rate(
    municipal: pd.DataFrame,
) -> None:
    """3 %/yr, and `median_income_tkr` must move with `median_income`.

    The two columns hold the same quantity in different units. Letting them
    drift apart would leave anything reading the thousands column quoting an
    ungrown figure.
    """
    stockholm = municipal[municipal["region_code"] == "0180"].sort_values("year")
    anchor = stockholm[stockholm["year"] == max(YEARS)].iloc[0]
    for _, row in stockholm[stockholm["year"] > max(YEARS)].iterrows():
        steps = int(row["year"]) - max(YEARS)
        expected = anchor["median_income"] * (1 + bp.IMPUTED_INCOME_GROWTH_RATE) ** steps
        assert row["median_income"] == pytest.approx(expected)
        assert row["median_income_tkr"] * 1000 == pytest.approx(row["median_income"])


# ---------------------------------------------------------------------------
# County and national panels
# ---------------------------------------------------------------------------

def test_the_county_panel_holds_counties_only(fake_raw) -> None:
    county = bp.build_county_panel()
    assert (county["lan_code"].str.len() == 2).all()
    assert set(county[~county["is_imputed_income"]]["lan_code"]) == set(COUNTIES)


def test_kolada_county_codes_are_translated_to_scb_codes(fake_raw) -> None:
    """Kolada writes county 01 as "0001". Getting the slice wrong joins nothing
    and leaves every county's unemployment null, which no row count would show."""
    county = bp.build_county_panel()
    observed = county[~county["is_imputed_income"]]
    assert observed["unemployment_rate"].notna().all()
    assert (observed["unemployment_rate"] == 2.5).all()


def test_the_national_panel_has_one_row_per_year(fake_raw) -> None:
    national = bp.build_national_panel()
    assert not national.duplicated(subset=["year"]).any()
    observed = national[~national["is_imputed_income"]]
    assert set(observed["year"]) == set(YEARS)


def test_the_three_levels_agree_on_the_national_series(fake_raw) -> None:
    """The policy rate and CPI are national, so all three panels must carry the
    same value for a given year. They are joined separately at each level, which
    is three chances to diverge."""
    municipal = bp.build_municipal_panel()
    county = bp.build_county_panel()
    national = bp.build_national_panel()
    for year in YEARS:
        rates = {
            float(frame[frame["year"] == year]["policy_rate"].dropna().iloc[0])
            for frame in (municipal, county, national)
        }
        assert len(rates) == 1, f"{year} has policy rates {rates} across levels"


# ---------------------------------------------------------------------------
# The refresh summary
# ---------------------------------------------------------------------------

def test_the_summary_reports_what_was_actually_built(fake_raw) -> None:
    """The first thing anyone reads after a rebuild, and until the R10 split it
    was 23 print statements inside build_all that nothing could exercise."""
    from src.data.panel_summary import summarise

    panels = {
        "municipal": bp.build_municipal_panel(),
        "county": bp.build_county_panel(),
        "national": bp.build_national_panel(),
    }
    report = summarise(panels)

    assert f"Rows: {len(panels['municipal']):,}" in report
    assert f"Municipalities: {len(MUNICIPALITIES)}" in report
    assert f"Counties: {len(COUNTIES)}" in report
    for name in panels:
        assert f"Panel: {name}" in report


def test_the_summary_hides_columns_with_no_nulls(fake_raw) -> None:
    """A wall of zeroes is what stopped anyone reading the percentages that
    matter, which is why only non-zero ones are listed."""
    from src.data.panel_summary import summarise

    panel = bp.build_municipal_panel()
    report = summarise({"municipal": panel})
    full = [c for c in panel.columns if panel[c].notna().all()]
    assert full, "the fixture has a null in every column; it cannot test this"
    for column in full:
        assert f"    {column}:" not in report
