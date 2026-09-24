"""Panel construction — join the cleaned sources into municipality × year panels.

Produces:
- data/processed/panel_municipal.parquet  (kommun_kod × year)
- data/processed/panel_county.parquet     (lan_kod × year)
- data/processed/panel_national.parquet   (year)

The raw-table cleaners live in `clean_sources.py`; this module is the joins and
the documented approximations they carry.

Handles the 12–18 month income lag by forward-filling the latest known income
year with an explicit `is_imputed_income` flag.

Per METHODOLOGY.md (F1): county price index is used for ALL municipalities.
Per METHODOLOGY.md (F2): national interest rate is used at all geographic levels.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Extracted in T-D2: the same forward-fill was written three times, once per
# panel level. Re-exported so existing importers keep working.
from src.data.panel_summary import summarise  # noqa: E402
from src.data.panel_income import (  # noqa: E402
    IMPUTED_INCOME_GROWTH_RATE,
    impute_income_forward,
)

# Cleaners, split out in the R10 work. Imported by name and re-exported, because
# `build_all` and the tests both reach for them through this module.
from src.data.clean_sources import (  # noqa: E402
    RAW_DIR,
    _clean_bostadsratt_price,
    _clean_construction,
    _clean_cpi,
    _clean_income,
    _clean_kt_ratio,
    _clean_policy_rate,
    _clean_population,
    _clean_price_index,
    _clean_transaction_price,
    _clean_unemployment,
    _parse_month_tid,
    _parse_quarter_tid,
    _read,
)

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def _kommun_to_lan(kod: str) -> str:
    """Map a 4-digit municipality code to its 2-digit county code."""
    return kod[:2]




# ---------------------------------------------------------------------------
# Panel builders
# ---------------------------------------------------------------------------

def _identify_regions(income: pd.DataFrame):
    """Categorize region codes into municipalities, counties, national."""
    all_codes = income["region_code"].unique()
    national = [c for c in all_codes if c == "00"]
    counties = sorted([c for c in all_codes if len(c) == 2 and c != "00"])
    municipalities = sorted([c for c in all_codes if len(c) == 4])
    return national, counties, municipalities


def build_municipal_panel() -> pd.DataFrame:
    """Build the municipality × year panel with all variables."""
    logger.info("Loading and cleaning raw tables ...")
    income = _clean_income()
    price_idx = _clean_price_index()
    kt = _clean_kt_ratio()
    txn_price = _clean_transaction_price()
    br_price = _clean_bostadsratt_price()  # None if BO0501C cache missing
    unemp = _clean_unemployment()
    pop = _clean_population()
    constr = _clean_construction()
    cpi = _clean_cpi()
    rate = _clean_policy_rate()

    _, counties, municipalities = _identify_regions(income)
    logger.info("Found %d municipalities, %d counties", len(municipalities), len(counties))

    # --- Filter to municipalities only ---
    muni_income = income[income["region_code"].isin(municipalities)].copy()
    muni_unemp = unemp[unemp["region_code"].isin(municipalities)].copy()
    muni_pop = pop[pop["region_code"].isin(municipalities)].copy()
    muni_constr = constr[constr["region_code"].isin(municipalities)].copy()
    muni_kt = kt[kt["region_code"].isin(municipalities)].copy()

    # --- Start from income as the spine (determines year range) ---
    panel = muni_income[["region_code", "region_name", "year", "median_income", "median_income_tkr"]].copy()

    # --- Forward-fill income for current year if missing (income lag) ---
    # Apply 3% nominal growth per year (conservative Swedish wage growth assumption).
    # Zero-growth was a pessimistic assumption per audit finding F9.
    max_income_year = panel["year"].max()
    current_year = pd.Timestamp.now().year
    panel = impute_income_forward(panel, through_year=current_year)
    panel["is_imputed_income"] = panel.get("is_imputed_income", False)
    panel["is_imputed_income"] = panel["is_imputed_income"].fillna(False).astype(bool)

    # --- Map municipality → county for price index join ---
    panel["lan_code"] = panel["region_code"].apply(_kommun_to_lan)

    # --- Merge price index (county level → all municipalities, F1 mitigation) ---
    price_for_join = price_idx[price_idx["lan_code"] != "00"][["lan_code", "year", "price_index"]]
    panel = panel.merge(price_for_join, on=["lan_code", "year"], how="left")

    # --- Merge K/T ratio ---
    # Mark which municipalities have native K/T data
    kt_muni = muni_kt[["region_code", "year", "kt_ratio"]]
    panel = panel.merge(kt_muni, on=["region_code", "year"], how="left")

    # Also get county-level K/T for fallback
    county_kt = kt[kt["region_code"].isin(counties)][["region_code", "year", "kt_ratio"]].copy()
    county_kt.rename(columns={"region_code": "lan_code", "kt_ratio": "kt_ratio_county"}, inplace=True)
    panel = panel.merge(county_kt, on=["lan_code", "year"], how="left")

    # Flag native K/T
    panel["has_native_kt"] = panel["kt_ratio"].notna()
    # Fill missing municipal K/T with county K/T
    panel["kt_ratio"] = panel["kt_ratio"].fillna(panel["kt_ratio_county"])
    panel.drop(columns=["kt_ratio_county"], inplace=True)

    # --- Merge transaction price (BO0501C2, SEK level) ---
    muni_txn = txn_price[txn_price["region_code"].isin(municipalities)].copy()
    panel = panel.merge(
        muni_txn[["region_code", "year", "transaction_price_sek"]],
        on=["region_code", "year"], how="left",
    )
    # County-level fallback for municipalities without native transaction price
    county_txn = txn_price[txn_price["region_code"].isin(counties)].copy()
    county_txn = county_txn.rename(columns={
        "region_code": "lan_code",
        "transaction_price_sek": "txn_price_county",
    })
    panel = panel.merge(county_txn[["lan_code", "year", "txn_price_county"]],
                        on=["lan_code", "year"], how="left")
    panel["has_native_price"] = panel["transaction_price_sek"].notna()
    panel["transaction_price_sek"] = panel["transaction_price_sek"].fillna(
        panel["txn_price_county"]
    )
    panel.drop(columns=["txn_price_county"], inplace=True)

    # --- Merge bostadsrätt (apartment) transaction price — county level (F11 mitigation) ---
    # SCB BO0501C only publishes county-level data. Every municipality inherits
    # its county's mean bostadsrätt price; no municipality-specific data exists.
    if br_price is not None:
        county_br = br_price[br_price["region_code"].isin(counties)].copy()
        county_br = county_br.rename(columns={"region_code": "lan_code"})
        panel = panel.merge(
            county_br[["lan_code", "year", "bostadsratt_price_sek"]],
            on=["lan_code", "year"], how="left",
        )
        # Forward-fill BR prices into imputed years (data lags like income)
        panel = panel.sort_values(["region_code", "year"])
        panel["bostadsratt_price_sek"] = (
            panel.groupby("region_code")["bostadsratt_price_sek"].ffill()
        )
    else:
        panel["bostadsratt_price_sek"] = np.nan

    # --- Merge unemployment ---
    unemp_for_join = muni_unemp[["region_code", "year", "unemployment_rate"]]
    panel = panel.merge(unemp_for_join, on=["region_code", "year"], how="left")

    # --- Merge population ---
    pop_for_join = muni_pop[["region_code", "year", "population"]]
    panel = panel.merge(pop_for_join, on=["region_code", "year"], how="left")

    # --- Merge construction ---
    constr_for_join = muni_constr[["region_code", "year", "completions"]]
    panel = panel.merge(constr_for_join, on=["region_code", "year"], how="left")

    # --- Merge national-level variables: CPI, policy rate (F2 mitigation) ---
    panel = panel.merge(cpi, on="year", how="left")
    panel = panel.merge(rate, on="year", how="left")

    # --- Sort and reorder ---
    panel = panel.sort_values(["region_code", "year"]).reset_index(drop=True)
    col_order = [
        "region_code", "region_name", "lan_code", "year",
        "median_income", "median_income_tkr", "is_imputed_income",
        "price_index", "kt_ratio", "has_native_kt",
        "transaction_price_sek", "has_native_price",
        "bostadsratt_price_sek",
        "unemployment_rate", "population", "completions",
        "cpi_index", "cpi_yoy_pct", "policy_rate",
    ]
    panel = panel[[c for c in col_order if c in panel.columns]]

    return panel


def build_county_panel() -> pd.DataFrame:
    """Build the county × year panel by aggregating municipal data."""
    income = _clean_income()
    price_idx = _clean_price_index()
    kt = _clean_kt_ratio()
    txn_price = _clean_transaction_price()
    br_price = _clean_bostadsratt_price()
    unemp = _clean_unemployment()
    pop = _clean_population()
    constr = _clean_construction()
    cpi = _clean_cpi()
    rate = _clean_policy_rate()

    _, counties, _ = _identify_regions(income)

    # County-level income (direct from SCB, not aggregated)
    county_income = income[income["region_code"].isin(counties)].copy()
    county_income.rename(columns={"region_code": "lan_code"}, inplace=True)
    panel = county_income[["lan_code", "region_name", "year", "median_income", "median_income_tkr"]].copy()

    # Forward-fill income (same 3% nominal growth as municipal panel)
    max_income_year = panel["year"].max()
    current_year = pd.Timestamp.now().year
    panel = impute_income_forward(panel, through_year=current_year)
    panel["is_imputed_income"] = panel.get("is_imputed_income", False)
    panel["is_imputed_income"] = panel["is_imputed_income"].fillna(False).astype(bool)

    # Price index
    price_for_join = price_idx[price_idx["lan_code"] != "00"][["lan_code", "year", "price_index"]]
    panel = panel.merge(price_for_join, on=["lan_code", "year"], how="left")

    # K/T at county level
    county_kt = kt[kt["region_code"].isin(counties)][["region_code", "year", "kt_ratio"]].copy()
    county_kt.rename(columns={"region_code": "lan_code"}, inplace=True)
    panel = panel.merge(county_kt, on=["lan_code", "year"], how="left")

    # Transaction price at county level
    county_txn = txn_price[txn_price["region_code"].isin(counties)].copy()
    county_txn = county_txn.rename(columns={"region_code": "lan_code"})
    panel = panel.merge(county_txn[["lan_code", "year", "transaction_price_sek"]],
                        on=["lan_code", "year"], how="left")

    # Bostadsrätt price at county level (apartment prices, F11 mitigation)
    if br_price is not None:
        county_br = br_price[br_price["region_code"].isin(counties)].copy()
        county_br = county_br.rename(columns={"region_code": "lan_code"})
        panel = panel.merge(county_br[["lan_code", "year", "bostadsratt_price_sek"]],
                            on=["lan_code", "year"], how="left")
        # Forward-fill BR prices into imputed years (data lags like income)
        panel = panel.sort_values(["lan_code", "year"])
        panel["bostadsratt_price_sek"] = (
            panel.groupby("lan_code")["bostadsratt_price_sek"].ffill()
        )
    else:
        panel["bostadsratt_price_sek"] = np.nan

    # Unemployment at county level (Kolada uses 4-digit codes: "0001" for county "01")
    # Read full Kolada dataset including county aggregates
    unemp_all = _read("kolada_unemployment_all")
    # Kolada county codes: "00XX" → SCB "XX"
    kolada_county_codes = [f"00{c}" for c in counties]
    county_unemp = unemp_all[unemp_all["municipality_code"].isin(kolada_county_codes)].copy()
    county_unemp["lan_code"] = county_unemp["municipality_code"].str[2:]  # "0001" → "01"
    county_unemp = county_unemp[["lan_code", "year", "unemployment_rate"]].copy()
    county_unemp["year"] = county_unemp["year"].astype(int)
    panel = panel.merge(county_unemp, on=["lan_code", "year"], how="left")

    # Population at county level
    county_pop = pop[pop["region_code"].isin(counties)][["region_code", "year", "population"]].copy()
    county_pop.rename(columns={"region_code": "lan_code"}, inplace=True)
    panel = panel.merge(county_pop, on=["lan_code", "year"], how="left")

    # Construction at county level
    county_constr = constr[constr["region_code"].isin(counties)][["region_code", "year", "completions"]].copy()
    county_constr.rename(columns={"region_code": "lan_code"}, inplace=True)
    panel = panel.merge(county_constr, on=["lan_code", "year"], how="left")

    # National-level variables
    panel = panel.merge(cpi, on="year", how="left")
    panel = panel.merge(rate, on="year", how="left")

    panel = panel.sort_values(["lan_code", "year"]).reset_index(drop=True)
    return panel


def build_national_panel() -> pd.DataFrame:
    """Build the national × year panel."""
    income = _clean_income()
    price_idx = _clean_price_index()
    kt = _clean_kt_ratio()
    txn_price = _clean_transaction_price()
    br_price = _clean_bostadsratt_price()
    unemp_all = _read("kolada_unemployment_all")
    pop = _clean_population()
    constr = _clean_construction()
    cpi = _clean_cpi()
    rate = _clean_policy_rate()

    # National income
    nat_income = income[income["region_code"] == "00"][["year", "median_income", "median_income_tkr"]].copy()

    panel = nat_income.copy()

    # Forward-fill income (same 3% nominal growth as municipal panel)
    max_income_year = panel["year"].max()
    current_year = pd.Timestamp.now().year
    panel = impute_income_forward(panel, through_year=current_year)
    panel["is_imputed_income"] = panel.get("is_imputed_income", False)
    panel["is_imputed_income"] = panel["is_imputed_income"].fillna(False).astype(bool)

    # National price index (lan_code == "00")
    nat_price = price_idx[price_idx["lan_code"] == "00"][["year", "price_index"]]
    panel = panel.merge(nat_price, on="year", how="left")

    # National K/T
    nat_kt = kt[kt["region_code"] == "00"][["year", "kt_ratio"]]
    panel = panel.merge(nat_kt, on="year", how="left")

    # National transaction price
    nat_txn = txn_price[txn_price["region_code"] == "00"][["year", "transaction_price_sek"]]
    panel = panel.merge(nat_txn, on="year", how="left")

    # National bostadsrätt price (F11 mitigation)
    if br_price is not None:
        nat_br = br_price[br_price["region_code"] == "00"][["year", "bostadsratt_price_sek"]]
        panel = panel.merge(nat_br, on="year", how="left")
        # Forward-fill BR prices into imputed years (data lags like income)
        panel = panel.sort_values("year")
        panel["bostadsratt_price_sek"] = panel["bostadsratt_price_sek"].ffill()
    else:
        panel["bostadsratt_price_sek"] = np.nan

    # National unemployment (Kolada code "0000")
    nat_unemp = unemp_all[unemp_all["municipality_code"] == "0000"][["year", "unemployment_rate"]].copy()
    nat_unemp["year"] = nat_unemp["year"].astype(int)
    panel = panel.merge(nat_unemp, on="year", how="left")

    # National population
    nat_pop = pop[pop["region_code"] == "00"][["year", "population"]]
    panel = panel.merge(nat_pop, on="year", how="left")

    # National construction
    nat_constr = constr[constr["region_code"] == "00"][["year", "completions"]]
    panel = panel.merge(nat_constr, on="year", how="left")

    # CPI and rate
    panel = panel.merge(cpi, on="year", how="left")
    panel = panel.merge(rate, on="year", how="left")

    panel = panel.sort_values("year").reset_index(drop=True)
    return panel


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_all() -> dict[str, pd.DataFrame]:
    """Build all three panels and save to data/processed/."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Building municipal panel ...")
    muni = build_municipal_panel()
    muni.to_parquet(OUT_DIR / "panel_municipal.parquet", index=False)

    logger.info("Building county panel ...")
    county = build_county_panel()
    county.to_parquet(OUT_DIR / "panel_county.parquet", index=False)

    logger.info("Building national panel ...")
    national = build_national_panel()
    national.to_parquet(OUT_DIR / "panel_national.parquet", index=False)

    panels = {"municipal": muni, "county": county, "national": national}
    print(summarise(panels))
    return panels


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    build_all()
