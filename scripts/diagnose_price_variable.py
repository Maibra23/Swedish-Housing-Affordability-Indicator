"""Mandatory sanity check before modifying affordability formulas.

Verifies BO0501C2 (transaction price in SEK) is present and ordered correctly.
Stockholm must be roughly 3x Norrbotten for the affordability formulas to
produce economically sensible rankings.

Exit codes:
  0 = PASS (proceed to Step 2)
  1 = no raw file found
  2 = BO0501C2 not in raw file
  3 = ordering check failed
  4 = missing county data
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main():
    new_file = RAW / "BO0501_transaction_price.parquet"
    old_file = RAW / "BO0501_kt_ratio.parquet"

    if new_file.exists():
        print(f"Using dedicated transaction price file: {new_file}")
        df = pd.read_parquet(new_file)
    elif old_file.exists():
        print(f"Using existing raw file (may need BO0501C2 filter): {old_file}")
        df = pd.read_parquet(old_file)
    else:
        print("ERROR: No raw BO0501 file found")
        sys.exit(1)

    cc_col = next((c for c in ["ContentsCode_code", "ContentsCode"] if c in df.columns), None)
    ft_col = next((c for c in ["Fastighetstyp_code", "Fastighetstyp"] if c in df.columns), None)
    region_col = next((c for c in ["Region_code", "Region"] if c in df.columns), None)
    time_col = next((c for c in ["Tid_code", "Tid", "year"] if c in df.columns), None)

    print(f"\nColumn detection: CC={cc_col}, FT={ft_col}, Region={region_col}, Time={time_col}")
    print(f"Row count: {len(df):,}")
    print(f"Unique ContentsCode values: {sorted(str(v) for v in df[cc_col].unique())}")

    has_bo0501c2 = "BO0501C2" in df[cc_col].unique()
    if not has_bo0501c2:
        print("\nWARNING: BO0501C2 (transaction price) not in raw file.")
        print("You need to pull it. See PATCH_POST_DAY2_v2.md Task 1.C.")
        sys.exit(2)

    prices = df[
        (df[cc_col] == "BO0501C2")
        & (df[ft_col] == "220")
        & (df[time_col].astype(str) == "2024")
    ].copy()

    prices["value_msek"] = prices["value"] / 1000

    key_counties = [("01", "Stockholm"), ("14", "Vastra Gotaland"),
                    ("12", "Skane"), ("25", "Norrbotten")]

    print("\n" + "=" * 55)
    print(f"{'County':25} {'Code':5} {'Median price 2024':20}")
    print("=" * 55)
    results = {}
    for code, name in key_counties:
        rows = prices[prices[region_col] == code]
        if len(rows) > 0:
            val = rows["value_msek"].mean()
            results[code] = val
            print(f"{name:25} {code:5} {val:6.2f} MSEK")
        else:
            print(f"{name:25} {code:5} NOT FOUND")

    print("\n" + "=" * 55)
    if "01" in results and "25" in results:
        ratio = results["01"] / results["25"]
        print(f"Stockholm / Norrbotten ratio: {ratio:.2f}x")
        if 2.5 <= ratio <= 4.5:
            print("SANITY CHECK PASSED. Proceed to Step 2.")
            sys.exit(0)
        else:
            print(f"SANITY CHECK FAILED. Expected ratio 2.5x to 4.5x, got {ratio:.2f}x.")
            print("Do NOT modify affordability.py. Investigate data first.")
            sys.exit(3)
    else:
        print("Cannot compute ratio, one or both counties missing")
        sys.exit(4)


if __name__ == "__main__":
    main()
