"""SHAI affordability formulas A, B, C.

Price variable: transaction_price_sek (SCB BO0501 content code BO0501C2).
Not price_index (growth measure) and not kt_ratio (markup measure).

See METHODOLOGY.md section 3 for the rationale. The series is SCB BO0501C2,
an arithmetic mean of purchase prices, not a median.

Version A: Income / (Price * Rate)           -- bank-style ratio
Version B: weighted z-score composite        -- macro pressure index
Version C: Income / (Price * max(R-pi, 0.5)) -- real affordability
"""

from __future__ import annotations

import logging

import pandas as pd

from src.indices.b_reference import LevelReference, pi_ratio

logger = logging.getLogger(__name__)


def complete_case(panel: pd.DataFrame) -> pd.DataFrame:
    """Return only the rows whose index inputs are observed rather than imputed.

    Income ends a year before prices, unemployment and the policy rate, so
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


def compute_version_a(panel: pd.DataFrame) -> pd.Series:
    """Version A: Bank-style affordability ratio.

    Affordability_A = Income / (TransactionPrice * Rate)

    Higher value = more affordable.
    Requires: median_income, transaction_price_sek, policy_rate.
    """
    income = panel["median_income"]
    # R12: yield NaN rather than inf on an impossible price. `scorable_rows`
    # already drops these before scoring; this guards the direct call, which the
    # property tests make and which a future caller might.
    price = panel["transaction_price_sek"].where(lambda p: p > 0)
    rate = panel["policy_rate"]

    # Rate is in percentage points, convert to decimal for the ratio
    rate_decimal = rate / 100.0

    # Avoid division by zero where rate is 0 or negative
    rate_safe = rate_decimal.clip(lower=0.001)

    return income / (price * rate_safe)


def compute_version_b(
    panel: pd.DataFrame, reference: LevelReference | None = None
) -> pd.Series:
    """Version B: Macro composite pressure index.

    Risk_B = 0.35*z(P/I) + 0.25*z(R) + 0.20*z(U) + 0.20*z(pi)

    Higher value = worse affordability (more risk).
    Requires: median_income, transaction_price_sek, policy_rate,
              unemployment_rate, cpi_yoy_pct.

    The four z-scores are pooled across the panel rather than taken within year,
    which is what lets B's level carry a time trend (decision D5). Pooling them
    against *this* panel, however, made every published value a function of panel
    composition: R1 in `docs/OPEN_RISKS.md`. Pass a stored `reference` and the
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
        z_rate = _zscore(panel["policy_rate"])
        z_unemp = _zscore(panel["unemployment_rate"])
        z_cpi = _zscore(panel["cpi_yoy_pct"])
    else:
        z_pi_ratio = reference.zscore(pi_ratio(panel), "pi_ratio")
        z_rate = reference.zscore(panel["policy_rate"], "policy_rate")
        z_unemp = reference.zscore(panel["unemployment_rate"], "unemployment_rate")
        z_cpi = reference.zscore(panel["cpi_yoy_pct"], "cpi_yoy_pct")

    return 0.35 * z_pi_ratio + 0.25 * z_rate + 0.20 * z_unemp + 0.20 * z_cpi


def compute_version_c(panel: pd.DataFrame) -> pd.Series:
    """Version C: Real affordability (primary, recommended).

    Affordability_C = Income / (TransactionPrice * max(R - pi, 0.005))

    Higher value = more affordable.
    The max() floor prevents division explosion when real rates are near zero.
    Requires: median_income, transaction_price_sek, policy_rate, cpi_yoy_pct.
    """
    income = panel["median_income"]
    # R12: see compute_version_a. An infinite value here would propagate through
    # the within-year z-score and NaN out every other municipality in the year.
    price = panel["transaction_price_sek"].where(lambda p: p > 0)
    rate = panel["policy_rate"]       # percentage points
    inflation = panel["cpi_yoy_pct"]  # percentage points

    # Real rate in percentage points, floored at 0.5 pp
    real_rate = (rate - inflation).clip(lower=0.5)

    # Convert to decimal for the ratio
    real_rate_decimal = real_rate / 100.0

    return income / (price * real_rate_decimal)


INDEX_INPUTS = ("median_income", "transaction_price_sek", "policy_rate",
                "unemployment_rate", "cpi_yoy_pct")


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

    best_a = county.nlargest(5, "version_a")
    print("\nTop 5 BEST affordability under Version A (higher = better):")
    print(best_a[["version_a"]])

    worst_c = county.nsmallest(5, "version_c")
    print("\nTop 5 WORST affordability under Version C (lower = worse):")
    print(worst_c[["version_c"]])
