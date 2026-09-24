"""Synthetic raw tables in the shapes `clean_sources` expects.

Separated from `test_build_panel.py` for the same reason `tests/sourcetools.py`
exists: fixtures are not assertions, and a test module that holds both stops
being read as either.

Everything here mimics one source's published shape — SCB's flat JSON-stat2
columns, Kolada's municipality codes — with values small enough that a broken
join shows up as a wrong number rather than a wrong row count. Three
municipalities across two counties is the minimum that makes the county
broadcasts and the county fallbacks observable at once.
"""

from __future__ import annotations

import pandas as pd

YEARS = (2022, 2023)

#: Two counties. 01 has two municipalities, 08 has one, which is what makes the
#: county-level broadcasts and fallbacks observable.
MUNICIPALITIES = {"0180": "Stockholm", "0181": "Södertälje", "0880": "Kalmar"}
COUNTIES = {"01": "Stockholms län", "08": "Kalmar län"}


def _scb_rows(codes: dict[str, str], values: dict[tuple[str, int], float]) -> pd.DataFrame:
    """A frame in SCB's flat JSON-stat2 shape: code, label, period, value."""
    return pd.DataFrame(
        [
            {
                "Region_code": code,
                "Region": name,
                "Tid_code": str(year),
                "Tid": str(year),
                "value": values[(code, year)],
            }
            for code, name in codes.items()
            for year in YEARS
            if (code, year) in values
        ]
    )


def _income_raw() -> pd.DataFrame:
    values = {
        ("00", 2022): 300.0, ("00", 2023): 310.0,
        ("01", 2022): 380.0, ("01", 2023): 390.0,
        ("08", 2022): 320.0, ("08", 2023): 330.0,
        ("0180", 2022): 400.0, ("0180", 2023): 410.0,
        ("0181", 2022): 350.0, ("0181", 2023): 360.0,
        ("0880", 2022): 330.0, ("0880", 2023): 340.0,
    }
    codes = {"00": "Riket", **COUNTIES, **MUNICIPALITIES}
    return _scb_rows(codes, values)


def _price_index_raw() -> pd.DataFrame:
    """Price index is published per county, with Kalmar and Gotland combined."""
    return pd.DataFrame(
        [
            {"Lan_code": code, "Lan": name, "Tid_code": str(year), "value": value}
            for code, name, value in (
                ("01", "Stockholms län", 200.0),
                ("08+09", "Kalmar och Gotlands län", 150.0),
            )
            for year in YEARS
        ]
    )


def _kt_raw() -> pd.DataFrame:
    """K/T exists for one municipality and both counties, so the fallback shows."""
    rows = [
        {"Region_code": "0180", "Region": "Stockholm", "Tid_code": str(y),
         "value": 3.0, "frequency": "annual"} for y in YEARS
    ]
    rows += [
        {"Region_code": code, "Region": name, "Tid_code": str(y),
         "value": 2.0, "frequency": "annual"}
        for code, name in COUNTIES.items() for y in YEARS
    ]
    # A quarterly row that must be filtered out rather than averaged in.
    rows.append({"Region_code": "0180", "Region": "Stockholm", "Tid_code": "2023K1",
                 "value": 99.0, "frequency": "quarterly"})
    return pd.DataFrame(rows)


def _transaction_price_raw() -> pd.DataFrame:
    """Small-house prices. 0181 is missing so the county fallback is exercised."""
    rows = []
    for code, name, value in (
        ("0180", "Stockholm", 8000.0),
        ("0880", "Kalmar", 2000.0),
        ("01", "Stockholms län", 7000.0),
        ("08+09", "Kalmar och Gotlands län", 1800.0),
    ):
        for year in YEARS:
            rows.append({
                "Region_code": code, "Region": name, "Tid_code": str(year),
                "Fastighetstyp_code": "220", "value": value,
            })
    # Another property type that must be filtered out.
    rows.append({"Region_code": "0180", "Region": "Stockholm", "Tid_code": "2023",
                 "Fastighetstyp_code": "210", "value": 1.0})
    return pd.DataFrame(rows)


def _bostadsratt_raw() -> pd.DataFrame:
    rows = []
    for code in ("01", "08"):
        for year in YEARS:
            rows.append({"Region_code": code, "Region": COUNTIES[code],
                         "Tid_code": str(year), "value": 5000.0 if code == "01" else 1500.0})
    # A storstadsområde code, which must not survive into a county panel.
    rows.append({"Region_code": "0010", "Region": "Storstockholm",
                 "Tid_code": "2023", "value": 9999.0})
    return pd.DataFrame(rows)


def _unemployment_raw() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"municipality_code": code, "year": year, "unemployment_rate": 3.0}
            for code in MUNICIPALITIES
            for year in YEARS
        ]
    )


def _unemployment_all_raw() -> pd.DataFrame:
    """Kolada's all-regions table, which codes counties as "00" + the SCB code.

    The county builder reads this rather than the municipal table, so the prefix
    convention is a second place the county code can be got wrong.
    """
    rows = [
        {"municipality_code": code, "year": year, "unemployment_rate": 3.0}
        for code in MUNICIPALITIES
        for year in YEARS
    ]
    rows += [
        {"municipality_code": f"00{code}", "year": year, "unemployment_rate": 2.5}
        for code in COUNTIES
        for year in YEARS
    ]
    return pd.DataFrame(rows)


def _population_raw() -> pd.DataFrame:
    codes = {"00": "Riket", **COUNTIES, **MUNICIPALITIES}
    values = {(c, y): 1000.0 for c in codes for y in YEARS}
    return _scb_rows(codes, values)


def _construction_raw() -> pd.DataFrame:
    codes = {"00": "Riket", **COUNTIES, **MUNICIPALITIES}
    values = {(c, y): 10.0 for c in codes for y in YEARS}
    return _scb_rows(codes, values)


def _cpi_raw() -> pd.DataFrame:
    """Monthly CPI: a level series and a year-on-year series, fetched together."""
    rows = []
    for year in YEARS:
        for month in range(1, 13):
            tid = f"{year}M{month:02d}"
            rows.append({"Tid_code": tid, "ContentsCode_code": "00000807", "value": 100.0 + year - 2022})
            rows.append({"Tid_code": tid, "ContentsCode_code": "00000804", "value": 2.0})
    return pd.DataFrame(rows)


def _policy_rate_raw() -> pd.DataFrame:
    rows = []
    for year in YEARS:
        for month in (1, 7):
            rows.append({"date": f"{year}-{month:02d}-01", "rate": 1.0 + (year - 2022)})
    return pd.DataFrame(rows)


RAW = {
    "HE0110_income": _income_raw,
    "BO0501_price_index": _price_index_raw,
    "BO0501_kt_ratio": _kt_raw,
    "BO0501_transaction_price": _transaction_price_raw,
    "BO0501C_bostadsratt_price": _bostadsratt_raw,
    "kolada_unemployment": _unemployment_raw,
    "kolada_unemployment_all": _unemployment_all_raw,
    "BE0101_population": _population_raw,
    "BO0101_construction": _construction_raw,
    "PR0101_cpi": _cpi_raw,
    "policy_rate": _policy_rate_raw,
}
