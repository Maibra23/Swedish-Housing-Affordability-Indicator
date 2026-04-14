"""Z-score normalization and ranking for SHAI affordability indices.

For each formula version:
- Compute z-score within latest year
- Compute rank 1–290 (1 = best affordability)
- Invert A and C so higher z = worse (matches Version B convention)
- Assign risk_class: lag / medel / hog
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_and_rank(affordability: pd.DataFrame, rank_year: int | None = None) -> pd.DataFrame:
    """Normalize and rank all three formula versions.

    Parameters
    ----------
    affordability : pd.DataFrame
        Output of affordability.compute_all(). Must have columns:
        region_code, year, version_a, version_b, version_c.
    rank_year : int, optional
        Year to use for ranking. Defaults to latest year in data.

    Returns
    -------
    pd.DataFrame
        One row per municipality for the ranking year, with z-scores,
        ranks, and risk classes for each version.
    """
    if rank_year is None:
        rank_year = affordability["year"].max()

    latest = affordability[affordability["year"] == rank_year].copy()
    logger.info("Ranking %d municipalities for year %d", len(latest), rank_year)

    for version in ["a", "b", "c"]:
        col = f"version_{version}"
        values = latest[col]

        # Z-score within this year
        mean = values.mean()
        std = values.std()
        z = (values - mean) / std if std > 0 else 0.0

        # Invert A and C so higher z = worse affordability (matching B)
        # A and C: higher raw value = more affordable = better
        # B: higher raw value = more risk = worse
        # After inversion, all three: higher z = worse
        if version in ("a", "c"):
            z = -z

        latest[f"z_{version}"] = z

        # Rank: 1 = best affordability (lowest z after inversion)
        latest[f"rank_{version}"] = latest[f"z_{version}"].rank(method="min").astype(int)

        # Risk class based on z-score thresholds
        latest[f"risk_{version}"] = pd.cut(
            latest[f"z_{version}"],
            bins=[-float("inf"), -0.67, 0.67, float("inf")],
            labels=["lag", "medel", "hog"],
        )

    # Reorder columns
    keep = [
        "region_code", "region_name", "lan_code", "year",
        "median_income", "price_index", "policy_rate", "unemployment_rate", "cpi_yoy_pct",
        "version_a", "version_b", "version_c",
        "z_a", "z_b", "z_c",
        "rank_a", "rank_b", "rank_c",
        "risk_a", "risk_b", "risk_c",
    ]
    latest = latest[[c for c in keep if c in latest.columns]]

    return latest.reset_index(drop=True)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from pathlib import Path

    aff = pd.read_parquet(Path(__file__).resolve().parents[2] / "data" / "processed" / "affordability_municipal.parquet")
    ranked = normalize_and_rank(aff)

    out = Path(__file__).resolve().parents[2] / "data" / "processed" / "affordability_ranked.parquet"
    ranked.to_parquet(out, index=False)
    print(f"Saved {out}  ({len(ranked)} rows)")

    # Summary
    for v in ["a", "b", "c"]:
        counts = ranked[f"risk_{v}"].value_counts()
        print(f"\nVersion {v.upper()} risk distribution:")
        for cls in ["lag", "medel", "hog"]:
            print(f"  {cls}: {counts.get(cls, 0)}")

    # Top 5 worst and best for each version
    for v in ["a", "b", "c"]:
        print(f"\nVersion {v.upper()} — Top 5 WORST (highest rank = worst):")
        worst = ranked.nlargest(5, f"rank_{v}")[["region_name", f"rank_{v}", f"z_{v}", f"risk_{v}"]].to_string(index=False)
        print(worst)
        print(f"\nVersion {v.upper()} — Top 5 BEST (lowest rank = best):")
        best = ranked.nsmallest(5, f"rank_{v}")[["region_name", f"rank_{v}", f"z_{v}", f"risk_{v}"]].to_string(index=False)
        print(best)
