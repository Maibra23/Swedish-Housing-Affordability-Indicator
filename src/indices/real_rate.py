"""Real interest rate computation for SHAI.

real_rate = nominal_policy_rate - cpi_yoy_pct
Floor at 0.5% (0.005) to prevent Version C division explosion.
"""

from __future__ import annotations

import pandas as pd


def compute_real_rate(panel_national: pd.DataFrame) -> pd.DataFrame:
    """Compute real interest rate from national panel.

    Parameters
    ----------
    panel_national : pd.DataFrame
        Must contain columns: year, policy_rate, cpi_yoy_pct.

    Returns
    -------
    pd.DataFrame
        Annual series with columns: year, policy_rate, cpi_yoy_pct,
        real_rate, real_rate_floored, is_floored.
    """
    df = panel_national[["year", "policy_rate", "cpi_yoy_pct"]].copy()
    df = df.dropna(subset=["policy_rate", "cpi_yoy_pct"])

    # CPI YoY is in percentage points (e.g., 8.65 means 8.65%)
    # Policy rate is also in percentage points (e.g., 3.63 means 3.63%)
    # Real rate = nominal - inflation (both in %)
    df["real_rate"] = df["policy_rate"] - df["cpi_yoy_pct"]

    # Floor at 0.5 percentage points to prevent Version C explosion
    FLOOR = 0.5  # 0.5 percentage points
    df["real_rate_floored"] = df["real_rate"].clip(lower=FLOOR)
    df["is_floored"] = df["real_rate"] < FLOOR

    return df.reset_index(drop=True)
