"""Raw source tables to tidy frames: one cleaner per SCB or Kolada table.

Split out of `build_panel.py` so that module holds only the *joins* and this one
holds the *shapes*. The two change for different reasons: a cleaner changes when
a source republishes a column, a builder changes when the panel's structure
does.

The split was deferred deliberately. `docs/OPEN_RISKS.md` R10 recorded that
`build_panel.py` sat at 0 % coverage and that splitting an untested module is the
riskiest refactor available, so it should wait for tests. It now has them:
`tests/test_build_panel.py` covers 87 % of the original module, including every
cleaner here and the documented approximations they feed. `scb_client.py` took
the same route a day earlier.

Each cleaner is where one source's quirks are absorbed, and those quirks are the
reason this file is worth reading:

  - income arrives in tkr and leaves in kronor
  - the price index and small-house prices publish Kalmar and Gotland as one
    combined `08+09` row, which is split so both counties join
  - K/T arrives with annual and quarterly rows in one table
  - CPI arrives monthly, as two content codes that must be paired by period
  - Kolada codes a county as "00" plus its SCB code
  - bostadsrätt prices exist at county level only, and the storstadsområde
    aggregates would double-count if kept

`_read` is the single door to `data/raw/`, which is gitignored. Tests patch it
rather than the filesystem, so the whole builder runs in-process on frames whose
every value is known.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def _read(name: str) -> pd.DataFrame:
    path = RAW_DIR / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing raw file: {path}")
    return pd.read_parquet(path)


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
    """Median sammanräknad förvärvsinkomst (tkr) per region × year. Individual, gross."""
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


def _clean_transaction_price() -> pd.DataFrame:
    """Mean (arithmetic average) transaction price in SEK per region x year.

    Source: SCB BO0501 content code BO0501C2 (köpeskilling medelvärde, 1000 SEK).
    Note: BO0501C2 is labeled 'Köpeskilling, medelvärde i tkr' — this is the MEAN,
    not the median. All documentation and comments should reflect this.
    Fastighetstyp 220 (permanent small house / permanentbostad ej tomträtt).
    Bostadsrätter are NOT included.

    The combined 08+09 code (Kalmar+Gotland) is split so both counties
    get the same price.
    """
    df = _read("BO0501_transaction_price")
    # Filter to permanent housing only
    ft_col = "Fastighetstyp_code" if "Fastighetstyp_code" in df.columns else "Fastighetstyp"
    df = df[df[ft_col] == "220"].copy()

    region_col = "Region_code" if "Region_code" in df.columns else "Region"
    time_col = "Tid_code" if "Tid_code" in df.columns else "Tid"

    df = df[[region_col, time_col, "value"]].copy()
    df.rename(columns={region_col: "region_code", time_col: "year",
                        "value": "transaction_price_ksek"}, inplace=True)
    df["year"] = df["year"].astype(int)
    df["transaction_price_sek"] = df["transaction_price_ksek"] * 1000
    df.drop(columns=["transaction_price_ksek"], inplace=True)

    # Split combined 08+09 into separate rows
    combined = df[df["region_code"] == "08+09"].copy()
    if not combined.empty:
        row_08 = combined.copy()
        row_08["region_code"] = "08"
        row_09 = combined.copy()
        row_09["region_code"] = "09"
        df = pd.concat([df[df["region_code"] != "08+09"], row_08, row_09], ignore_index=True)

    return df


def _clean_bostadsratt_price() -> pd.DataFrame | None:
    """Mean transaction price in SEK per bostadsrätt (housing co-op apartment),
    county × year. Returns None if the raw BO0501C file is not present yet.

    Source: SCB BO0501C/FastprisBRFRegionAr, content code BO0501R7 (Medelpris i tkr).
    Complements small-house prices (BO0501C2) for audit finding F11.

    Coverage: 21 counties (01–25) + national (00). SCB publishes NO municipality-level
    bostadsrätt prices — every municipality receives its county's value as fallback.
    Storstadsområden codes (0010, 0020, 0030, 0060) are excluded to avoid duplicates.
    """
    path = RAW_DIR / "BO0501C_bostadsratt_price.parquet"
    if not path.exists():
        logger.info("BO0501C bostadsrätt price not cached yet — skipping apartment merge")
        return None

    df = _read("BO0501C_bostadsratt_price")

    region_col = "Region_code" if "Region_code" in df.columns else "Region"
    time_col = "Tid_code" if "Tid_code" in df.columns else "Tid"

    df = df[[region_col, time_col, "value"]].copy()
    df.rename(columns={region_col: "region_code", time_col: "year",
                       "value": "bostadsratt_price_ksek"}, inplace=True)
    # SCB publishes the mean price in tkr → convert to SEK.
    df["year"] = df["year"].astype(int)
    df["bostadsratt_price_sek"] = df["bostadsratt_price_ksek"] * 1000
    df.drop(columns=["bostadsratt_price_ksek"], inplace=True)

    # Keep only 2-char codes: counties (01–25) + national (00).
    # This excludes storstadsområden (0010, 0020, 0030, 0060) which are subsets of counties.
    df = df[df["region_code"].str.len() == 2].copy()

    return df


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

