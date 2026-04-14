"""Panel construction — merge all raw sources into municipality × year panels.

Reads parquet files from data/raw/ and produces:
- data/processed/panel_municipal.parquet  (kommun_kod × year)
- data/processed/panel_county.parquet     (lan_kod × year)
- data/processed/panel_national.parquet   (year)

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

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(name: str) -> pd.DataFrame:
    path = RAW_DIR / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing raw file: {path}")
    return pd.read_parquet(path)


def _kommun_to_lan(kod: str) -> str:
    """Map a 4-digit municipality code to its 2-digit county code."""
    return kod[:2]


def _parse_month_tid(tid: str) -> tuple[int, int]:
    """Parse '2024M03' → (2024, 3)."""
    parts = tid.split("M")
    return int(parts[0]), int(parts[1])


def _parse_quarter_tid(tid: str) -> tuple[int, int]:
    """Parse '2024K3' → (2024, 3)."""
    parts = tid.split("K")
    return int(parts[0]), int(parts[1])


# ---------------------------------------------------------------------------
# Individual table cleaners
# ---------------------------------------------------------------------------

def _clean_income() -> pd.DataFrame:
    """Median disposable income (tkr) per region × year."""
    df = _read("HE0110_income")
    df = df[["Region_code", "Region", "Tid_code", "value"]].copy()
    df.rename(columns={"Region_code": "region_code", "Region": "region_name",
                        "Tid_code": "year", "value": "median_income_tkr"}, inplace=True)
    df["year"] = df["year"].astype(int)
    # Convert tkr to SEK
    df["median_income"] = df["median_income_tkr"] * 1000
    return df


def _clean_price_index() -> pd.DataFrame:
    """Fastighetsprisindex (1990=100) per county × year.

    The Län code '08+09' (Kalmar+Gotland combined) is split so both
    county 08 and county 09 get the same index value.
    """
    df = _read("BO0501_price_index")
    df = df[["Lan_code", "Lan", "Tid_code", "value"]].copy()
    df.rename(columns={"Lan_code": "lan_code", "Lan": "lan_name",
                        "Tid_code": "year", "value": "price_index"}, inplace=True)
    df["year"] = df["year"].astype(int)

    # Split combined 08+09 into separate rows for 08 and 09
    combined = df[df["lan_code"] == "08+09"].copy()
    if not combined.empty:
        row_08 = combined.copy()
        row_08["lan_code"] = "08"
        row_08["lan_name"] = row_08["lan_name"]  # keep same name
        row_09 = combined.copy()
        row_09["lan_code"] = "09"
        df = pd.concat([df[df["lan_code"] != "08+09"], row_08, row_09], ignore_index=True)

    return df


def _clean_kt_ratio() -> pd.DataFrame:
    """K/T ratio — annual per municipality and county."""
    df = _read("BO0501_kt_ratio")
    # Use annual municipal data
    annual = df[df["frequency"] == "annual"].copy()
    annual = annual[["Region_code", "Region", "Tid_code", "value"]].copy()
    annual.rename(columns={"Region_code": "region_code", "Region": "region_name",
                            "Tid_code": "year", "value": "kt_ratio"}, inplace=True)
    annual["year"] = annual["year"].astype(int)
    return annual


def _clean_unemployment() -> pd.DataFrame:
    """Unemployment rate (%) per municipality × year.

    Source: Kolada KPI N03937 (Arbetsförmedlingen) via kolada_client.py.
    Öppet arbetslösa av befolkningen, 18–65 år, andel (%).
    Coverage: All 290 municipalities, 2010–2024.
    """
    df = _read("kolada_unemployment")
    df = df[["municipality_code", "year", "unemployment_rate"]].copy()
    df.rename(columns={"municipality_code": "region_code"}, inplace=True)
    df["year"] = df["year"].astype(int)
    return df


def _clean_population() -> pd.DataFrame:
    """Total population per region × year (summed across gender and civil status)."""
    df = _read("BE0101_population")
    df = df[["Region_code", "Region", "Tid_code", "value"]].copy()
    df.rename(columns={"Region_code": "region_code", "Region": "region_name",
                        "Tid_code": "year", "value": "population"}, inplace=True)
    df["year"] = df["year"].astype(int)

    # Sum across Civilstånd and Kön
    pop = (df.groupby(["region_code", "region_name", "year"], as_index=False)
           ["population"].sum())
    return pop


def _clean_construction() -> pd.DataFrame:
    """Housing completions per region × year (sum of all house types)."""
    df = _read("BO0101_construction")
    df = df[["Region_code", "Region", "Tid_code", "value"]].copy()
    df.rename(columns={"Region_code": "region_code", "Region": "region_name",
                        "Tid_code": "year", "value": "completions"}, inplace=True)
    df["year"] = df["year"].astype(int)

    # Sum across house types (småhus + flerbostadshus)
    constr = (df.groupby(["region_code", "region_name", "year"], as_index=False)
              ["completions"].sum())
    return constr


def _clean_cpi() -> pd.DataFrame:
    """CPI index (2020=100) and YoY change per year (annual average of monthly)."""
    df = _read("PR0101_cpi")

    # Split the two content codes
    idx = df[df["ContentsCode_code"] == "00000807"][["Tid_code", "value"]].copy()
    idx.rename(columns={"value": "cpi_index"}, inplace=True)
    yoy = df[df["ContentsCode_code"] == "00000804"][["Tid_code", "value"]].copy()
    yoy.rename(columns={"value": "cpi_yoy_pct"}, inplace=True)

    cpi = idx.merge(yoy, on="Tid_code", how="outer")

    parsed = cpi["Tid_code"].apply(_parse_month_tid)
    cpi["year"] = [p[0] for p in parsed]
    cpi["month"] = [p[1] for p in parsed]

    # Annual average
    annual = cpi.groupby("year", as_index=False).agg(
        cpi_index=("cpi_index", "mean"),
        cpi_yoy_pct=("cpi_yoy_pct", "mean"),
    )
    return annual


def _clean_policy_rate() -> pd.DataFrame:
    """Policy rate — annual average from daily data."""
    df = _read("policy_rate")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year

    annual = df.groupby("year", as_index=False)["rate"].mean()
    annual.rename(columns={"rate": "policy_rate"}, inplace=True)
    return annual


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
    max_income_year = panel["year"].max()
    current_year = pd.Timestamp.now().year
    if max_income_year < current_year:
        logger.info("Income lag detected: latest income year %d, current year %d. Forward-filling.",
                     max_income_year, current_year)
        for fill_year in range(max_income_year + 1, current_year + 1):
            fill = panel[panel["year"] == max_income_year].copy()
            fill["year"] = fill_year
            fill["is_imputed_income"] = True
            panel = pd.concat([panel, fill], ignore_index=True)
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

    # Forward-fill income
    max_income_year = panel["year"].max()
    current_year = pd.Timestamp.now().year
    if max_income_year < current_year:
        for fill_year in range(max_income_year + 1, current_year + 1):
            fill = panel[panel["year"] == max_income_year].copy()
            fill["year"] = fill_year
            fill["is_imputed_income"] = True
            panel = pd.concat([panel, fill], ignore_index=True)
    panel["is_imputed_income"] = panel.get("is_imputed_income", False)
    panel["is_imputed_income"] = panel["is_imputed_income"].fillna(False).astype(bool)

    # Price index
    price_for_join = price_idx[price_idx["lan_code"] != "00"][["lan_code", "year", "price_index"]]
    panel = panel.merge(price_for_join, on=["lan_code", "year"], how="left")

    # K/T at county level
    county_kt = kt[kt["region_code"].isin(counties)][["region_code", "year", "kt_ratio"]].copy()
    county_kt.rename(columns={"region_code": "lan_code"}, inplace=True)
    panel = panel.merge(county_kt, on=["lan_code", "year"], how="left")

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
    unemp_all = _read("kolada_unemployment_all")
    pop = _clean_population()
    constr = _clean_construction()
    cpi = _clean_cpi()
    rate = _clean_policy_rate()

    # National income
    nat_income = income[income["region_code"] == "00"][["year", "median_income", "median_income_tkr"]].copy()

    panel = nat_income.copy()

    # Forward-fill income
    max_income_year = panel["year"].max()
    current_year = pd.Timestamp.now().year
    if max_income_year < current_year:
        for fill_year in range(max_income_year + 1, current_year + 1):
            fill = panel[panel["year"] == max_income_year].copy()
            fill["year"] = fill_year
            fill["is_imputed_income"] = True
            panel = pd.concat([panel, fill], ignore_index=True)
    panel["is_imputed_income"] = panel.get("is_imputed_income", False)
    panel["is_imputed_income"] = panel["is_imputed_income"].fillna(False).astype(bool)

    # National price index (lan_code == "00")
    nat_price = price_idx[price_idx["lan_code"] == "00"][["year", "price_index"]]
    panel = panel.merge(nat_price, on="year", how="left")

    # National K/T
    nat_kt = kt[kt["region_code"] == "00"][["year", "kt_ratio"]]
    panel = panel.merge(nat_kt, on="year", how="left")

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

    # --- Validation outputs ---
    panels = {"municipal": muni, "county": county, "national": national}
    for name, p in panels.items():
        print(f"\n{'='*60}")
        print(f"Panel: {name}")
        print(f"  Rows: {len(p):,}")
        print(f"  Columns: {len(p.columns)}")
        print(f"  Year range: {p['year'].min()} – {p['year'].max()}")

        if "region_code" in p.columns:
            muni_codes = [c for c in p["region_code"].unique() if len(c) == 4]
            print(f"  Municipalities: {len(muni_codes)}")
        if "lan_code" in p.columns:
            lan_codes = [c for c in p["lan_code"].unique() if len(c) == 2 and c != "00"]
            print(f"  Counties: {len(lan_codes)}")

        # Null percentages
        print("  Null %:")
        for col in p.columns:
            pct = p[col].isna().mean() * 100
            if pct > 0:
                print(f"    {col}: {pct:.1f}%")

    return panels


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    build_all()
