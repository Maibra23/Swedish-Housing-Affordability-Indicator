"""SHAI affordability formulas A, B, C.

Price variable: transaction_price_sek (SCB BO0501 content code BO0501C2).
Not price_index (growth measure) and not kt_ratio (markup measure).

See METHODOLOGY_v2.md section 3 "Why median transaction price" for rationale.

Version A: Income / (Price * Rate)           -- bank-style ratio
Version B: weighted z-score composite        -- macro pressure index
Version C: Income / (Price * max(R-pi, 0.5)) -- real affordability
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


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
    price = panel["transaction_price_sek"]
    rate = panel["policy_rate"]

    # Rate is in percentage points, convert to decimal for the ratio
    rate_decimal = rate / 100.0

    # Avoid division by zero where rate is 0 or negative
    rate_safe = rate_decimal.clip(lower=0.001)

    return income / (price * rate_safe)


def compute_version_b(panel: pd.DataFrame) -> pd.Series:
    """Version B: Macro composite pressure index.

    Risk_B = 0.35*z(P/I) + 0.25*z(R) + 0.20*z(U) + 0.20*z(pi)

    Higher value = worse affordability (more risk).
    Requires: median_income, transaction_price_sek, policy_rate,
              unemployment_rate, cpi_yoy_pct.
    """
    # Price-to-income ratio using transaction price in SEK
    pi_ratio = panel["transaction_price_sek"] / panel["median_income"]

    z_pi_ratio = _zscore(pi_ratio)
    z_rate = _zscore(panel["policy_rate"])
    z_unemp = _zscore(panel["unemployment_rate"])
    z_cpi = _zscore(panel["cpi_yoy_pct"])

    return 0.35 * z_pi_ratio + 0.25 * z_rate + 0.20 * z_unemp + 0.20 * z_cpi


def compute_version_c(panel: pd.DataFrame) -> pd.Series:
    """Version C: Real affordability (primary, recommended).

    Affordability_C = Income / (TransactionPrice * max(R - pi, 0.005))

    Higher value = more affordable.
    The max() floor prevents division explosion when real rates are near zero.
    Requires: median_income, transaction_price_sek, policy_rate, cpi_yoy_pct.
    """
    income = panel["median_income"]
    price = panel["transaction_price_sek"]
    rate = panel["policy_rate"]       # percentage points
    inflation = panel["cpi_yoy_pct"]  # percentage points

    # Real rate in percentage points, floored at 0.5 pp
    real_rate = (rate - inflation).clip(lower=0.5)

    # Convert to decimal for the ratio
    real_rate_decimal = real_rate / 100.0

    return income / (price * real_rate_decimal)


def compute_all(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute all three affordability versions.

    Filters to rows where all required inputs are non-null,
    then computes A, B, C.

    Returns DataFrame with original panel columns plus version_a, version_b, version_c.
    """
    required = ["median_income", "transaction_price_sek", "policy_rate",
                 "unemployment_rate", "cpi_yoy_pct"]
    mask = panel[required].notna().all(axis=1)
    df = panel[mask].copy()

    logger.info("Computing affordability on %d rows (dropped %d with nulls)",
                len(df), len(panel) - len(df))

    df["version_a"] = compute_version_a(df)
    df["version_b"] = compute_version_b(df)
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
