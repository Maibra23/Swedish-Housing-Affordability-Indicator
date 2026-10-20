"""SHAI affordability formulas A, B, C.

Price variable: transaction_price_sek (SCB BO0501 content code BO0501C2).
Not price_index (growth measure) and not kt_ratio (markup measure).

See METHODOLOGY.md section 3 for the rationale. The series is SCB BO0501C2,
an arithmetic mean of purchase prices, not a median.

Version A: gross interest / household income      -- bank's view, percent
Version B: weighted z-score composite              -- macro pressure index
Version C: (net interest + amortisation) / income  -- household cash flow, percent

A and C are cost shares from `src.indices.cost_model`: the yearly cost of an 85 %
loan on the mean small house, at the year's mean rate on new mortgages, over two
median incomes. Higher is worse for all three versions.
"""

from __future__ import annotations

import logging

import pandas as pd

from src.indices.b_reference import LevelReference, pi_ratio
from src.indices.cost_model import cost_share, interest_share

logger = logging.getLogger(__name__)


def complete_case(panel: pd.DataFrame) -> pd.DataFrame:
    """Return only the rows whose index inputs are observed rather than imputed.

    Income ends a year before prices, unemployment and the rates, so
    `build_panel` forward-fills it to keep the panel rectangular and flags every
    filled row with `is_imputed_income`. Those rows are never displayed — the
    sidebar stops at `complete_case_max_year()`.

    They must not be *scored* either. :func:`compute_version_b` z-scores its
    components pooled across whatever frame it is handed, so one imputed year
    shifts the pooled mean and standard deviation and moves `version_b` for every
    historical year. When the 2025 component data first landed this moved `z_b`
    on all 3190 rows and changed 19 risk classes — published numbers re-based by
    a year that cannot be rendered. Versions A and C are within-year (D5) and
    were unaffected, which is why it went unnoticed.

    A frame without the flag is returned unchanged: the county and national
    panels do not all carry it.

    Args:
        panel: A panel frame, with or without `is_imputed_income`.

    Returns:
        The subset with observed income, or the input if the flag is absent.
    """
    if "is_imputed_income" not in panel.columns:
        return panel
    return panel[~panel["is_imputed_income"].fillna(False).astype(bool)].copy()


def _zscore(series: pd.Series) -> pd.Series:
    """Z-score normalize a series (across the full panel)."""
    mean = series.mean()
    std = series.std()
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    return (series - mean) / std


def _guarded(panel: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Income and price with non-positive values blanked.

    R12: yield NaN rather than inf on an impossible value. `scorable_rows`
    already drops these before scoring; this guards the direct call, which the
    property tests make and which a future caller might. An infinite value would
    propagate through the within-year z-score and NaN out every other
    municipality in the year.
    """
    income = panel["median_income"].where(lambda v: v > 0)
    price = panel["transaction_price_sek"].where(lambda v: v > 0)
    return income, price


def compute_version_a(panel: pd.DataFrame) -> pd.Series:
    """Version A: gross yearly interest as a percentage of household income.

    The bank's view of the same loan C prices: interest only, before the tax
    deduction and without amortisation. Higher = worse.
    Requires: median_income, transaction_price_sek, mortgage_rate.
    """
    income, price = _guarded(panel)
    return interest_share(income, price, panel["mortgage_rate"])


def compute_version_b(
    panel: pd.DataFrame, reference: LevelReference | None = None
) -> pd.Series:
    """Version B: Macro composite pressure index.

    Risk_B = 0.35*z(P/I) + 0.25*z(R) + 0.20*z(U) + 0.20*z(pi)

    R is the mean rate on new mortgages and pi is KPIF inflation. KPI would put
    the rate in twice, because KPI prices mortgage interest.

    Higher value = worse affordability (more risk).
    Requires: median_income, transaction_price_sek, mortgage_rate,
              unemployment_rate, kpif_yoy_pct.

    The four z-scores are pooled across the panel rather than taken within year,
    which is what lets B's level carry a time trend (decision D5). Pooling them
    against *this* panel, however, made every published value a function of panel
    composition: R1 in `docs/APP_REFERENCE.md` (Part II). Pass a stored `reference` and the
    moments come from there instead, so appending a year leaves history alone.

    Args:
        panel: Rows to score.
        reference: Frozen moments to score against. When None the moments are
            taken from `panel` itself, which is the original behaviour and is
            kept for deriving a reference and for tests that need to compare the
            two directly. Production scoring always passes one.

    Returns:
        The Version B series.
    """
    if reference is None:
        z_pi_ratio = _zscore(pi_ratio(panel))
        z_rate = _zscore(panel["mortgage_rate"])
        z_unemp = _zscore(panel["unemployment_rate"])
        z_cpi = _zscore(panel["kpif_yoy_pct"])
    else:
        z_pi_ratio = reference.zscore(pi_ratio(panel), "pi_ratio")
        z_rate = reference.zscore(panel["mortgage_rate"], "mortgage_rate")
        z_unemp = reference.zscore(panel["unemployment_rate"], "unemployment_rate")
        z_cpi = reference.zscore(panel["kpif_yoy_pct"], "kpif_yoy_pct")

    return 0.35 * z_pi_ratio + 0.25 * z_rate + 0.20 * z_unemp + 0.20 * z_cpi


def compute_version_c(panel: pd.DataFrame) -> pd.Series:
    """Version C: household cash flow (primary, recommended).

    Net interest after the 30 % deduction plus the amortisation in force that
    year, as a percentage of two median incomes. Higher = worse.
    Requires: median_income, transaction_price_sek, mortgage_rate, year.
    """
    income, price = _guarded(panel)
    return cost_share(income, price, panel["mortgage_rate"], panel["year"])


INDEX_INPUTS = ("median_income", "transaction_price_sek", "mortgage_rate",
                "unemployment_rate", "kpif_yoy_pct")

#: The index's first year. The policy rate used to set it, because the Swea
#: series in use starts in 2014. It is no longer an input, so the window is
#: stated instead: the same eleven years the published figures and the Version
#: B reference describe. Starting earlier is a separate, deliberate decision.
FIRST_INDEX_YEAR = 2014


def scorable_rows(panel: pd.DataFrame) -> pd.DataFrame:
    """Rows carrying every index input, which is the set the formulas see.

    Exposed rather than left inline inside `compute_all` because the Version B
    reference must be derived from exactly the rows that will be scored against
    it. Deriving from one row set and scoring another is a subtler version of the
    defect the reference exists to fix, and it is what the first draft did:
    `complete_case` returns 4 060 municipal rows while only 3 190 carry every
    input, which made the frozen moments disagree with the moving ones by up to
    0.19.

    Args:
        panel: Any panel frame.

    Returns:
        A copy holding only the rows with no nulls in the index inputs.
    """
    mask = panel[list(INDEX_INPUTS)].notna().all(axis=1)
    mask &= panel["year"] >= FIRST_INDEX_YEAR
    # A cost share multiplies by the rate, so a non-positive one is refused
    # rather than floored. None occurs: SCB's series never fell below 1,4 %.
    mask &= panel["mortgage_rate"] > 0

    # R12: a non-positive price or income is not a missing value, so `notna`
    # lets it through, and it is not a small value either — it is a division by
    # zero. Version C would return `inf`, and a standard deviation taken over an
    # infinite value is `NaN`, so **one bad row would void every other
    # municipality's z-score for that year**: a whole year of the map going
    # blank from a single cell. Treated as missing here, which is what it is,
    # so the row joins the nulls that are already dropped rather than poisoning
    # its neighbours.
    for denominator in ("transaction_price_sek", "median_income"):
        mask &= panel[denominator] > 0

    return panel[mask].copy()


def compute_all(
    panel: pd.DataFrame, b_reference: LevelReference | None = None
) -> pd.DataFrame:
    """Compute all three affordability versions.

    Filters to rows where all required inputs are non-null,
    then computes A, B, C.

    Args:
        panel: Rows to score.
        b_reference: Frozen moments for Version B. See `compute_version_b`; the
            pipeline always supplies one, and omitting it re-bases B against
            whatever panel is passed.

    Returns:
        DataFrame with original panel columns plus version_a, version_b,
        version_c.
    """
    df = scorable_rows(panel)

    logger.info("Computing affordability on %d rows (dropped %d with nulls)",
                len(df), len(panel) - len(df))

    df["version_a"] = compute_version_a(df)
    df["version_b"] = compute_version_b(df, b_reference)
    df["version_c"] = compute_version_c(df)

    return df


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from pathlib import Path

    DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

    # Compute for all three panel levels
    for layer in ["municipal", "county", "national"]:
        panel_path = DATA_DIR / f"panel_{layer}.parquet"
        if not panel_path.exists():
            print(f"Skipping {layer}: {panel_path} not found")
            continue
        panel = pd.read_parquet(panel_path)
        result = compute_all(panel)

        out = DATA_DIR / f"affordability_{layer}.parquet"
        result.to_parquet(out, index=False)
        print(f"Saved {out}  ({len(result)} rows, "
              f"{result['version_c'].notna().sum()} with non-null V_C)")

    # Sanity check on municipal level
    result = pd.read_parquet(DATA_DIR / "affordability_municipal.parquet")
    latest = result[result["year"] == result["year"].max()]

    county = latest.groupby("lan_code").agg(
        version_a=("version_a", "median"),
        version_c=("version_c", "median"),
    )

    best_a = county.nsmallest(5, "version_a")
    print("\nTop 5 BEST affordability under Version A (lower = better):")
    print(best_a[["version_a"]])

    worst_c = county.nlargest(5, "version_c")
    print("\nTop 5 WORST affordability under Version C (higher = worse):")
    print(worst_c[["version_c"]])
