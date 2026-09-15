"""Z-score normalization, ranking and risk classification for SHAI.

This module is the **only** place z-scores, ranks and risk classes are computed.
Three implementations of this logic used to coexist — here, in
``scripts/refresh_data.py``, and inline in ``pages/01_Riksoversikt.py`` — and they
disagreed on orientation, which put the least affordable municipalities in the
"låg risk" class on the national map.  See ``tests/test_ranked_artifact.py``.

Orientation contract
--------------------
Versions A and C are *affordability* measures: a higher raw value means more
affordable.  Version B is a *risk* measure: a higher raw value means more risk.
To make the three comparable, A and C are sign-inverted before classification, so
that afterwards, for all three versions:

    higher z  =  worse affordability  =  higher risk
    rank 1    =  best affordability   =  lowest risk
    lag < medel < hog  in order of decreasing affordability

Normalization is **within year**: each year's municipalities are scored against
that year's national distribution.  A consequence worth stating plainly is that
the ±0.67σ class boundaries put roughly 25 % / 50 % / 25 % of municipalities in
lag / medel / hog every year by construction, so the national *count* in each
class is close to constant and carries no trend information.  The class is a
statement about a municipality's position relative to its peers in that year,
not about the country's affordability over time.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

VERSIONS = ("a", "b", "c")

# Versions whose raw value runs opposite to risk and therefore need inverting.
_HIGHER_IS_BETTER = ("a", "c")

# Class boundaries in standard deviations. ±0.67σ are the quartiles of a normal
# distribution, so the split is approximately 25 / 50 / 25 by construction.
_CLASS_BOUNDS = [-float("inf"), -0.67, 0.67, float("inf")]
_CLASS_LABELS = ["lag", "medel", "hog"]


def _score_one_year(group: pd.DataFrame) -> pd.DataFrame:
    """Add z, rank and risk columns for a single year's municipalities.

    Returns a new frame; the input is not modified.
    """
    computed: dict[str, pd.Series] = {}

    for version in VERSIONS:
        values = group[f"version_{version}"]
        std = values.std()

        if std and std > 0:
            z = (values - values.mean()) / std
        else:
            z = pd.Series(0.0, index=group.index)

        # Put every version on one orientation: higher z = worse.
        if version in _HIGHER_IS_BETTER:
            z = -z

        computed[f"z_{version}"] = z
        # Rank 1 = lowest z after inversion = best affordability.
        computed[f"rank_{version}"] = z.rank(method="min").astype("int64")
        computed[f"risk_{version}"] = pd.cut(
            z, bins=_CLASS_BOUNDS, labels=_CLASS_LABELS
        ).astype("object")

    return group.assign(**computed)


def normalize_and_rank(
    affordability: pd.DataFrame, rank_year: int | None = None
) -> pd.DataFrame:
    """Score, rank and classify municipalities within each year.

    Parameters
    ----------
    affordability:
        Output of ``affordability.compute_all()``. Must carry ``region_code``,
        ``year`` and ``version_a`` / ``version_b`` / ``version_c``.
    rank_year:
        Restrict the output to a single year. ``None`` (the default) scores every
        year in the input, which is what the dashboard needs — historical years
        need risk classes too.

    Returns
    -------
    pd.DataFrame
        Every input column, plus ``z_*``, ``rank_*`` and ``risk_*`` for each
        version. One row per municipality per year.
    """
    required = ["region_code", "year", *(f"version_{v}" for v in VERSIONS)]
    missing = [c for c in required if c not in affordability.columns]
    if missing:
        raise ValueError(f"normalize_and_rank is missing required columns: {missing}")

    frame = affordability
    if rank_year is not None:
        frame = frame[frame["year"] == rank_year]
        if frame.empty:
            raise ValueError(f"No rows for year {rank_year} in the affordability panel.")

    scored = pd.concat(
        [_score_one_year(group) for _, group in frame.groupby("year", sort=True)],
        ignore_index=True,
    )

    logger.info(
        "Scored %d municipality-years across %d years (%d–%d)",
        len(scored),
        scored["year"].nunique(),
        scored["year"].min(),
        scored["year"].max(),
    )
    return scored


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from pathlib import Path

    DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
    aff = pd.read_parquet(DATA_DIR / "affordability_municipal.parquet")
    ranked = normalize_and_rank(aff)

    out = DATA_DIR / "affordability_ranked.parquet"
    ranked.to_parquet(out, index=False)
    print(f"Saved {out}  ({len(ranked)} rows, {ranked['year'].nunique()} years)")

    latest = ranked[ranked["year"] == ranked["year"].max()]
    for v in VERSIONS:
        print(f"\nVersion {v.upper()} — {latest['year'].iloc[0]} risk distribution:")
        counts = latest[f"risk_{v}"].value_counts()
        for cls in _CLASS_LABELS:
            print(f"  {cls}: {counts.get(cls, 0)}")
        best = latest.nsmallest(3, f"rank_{v}")[["region_name", f"version_{v}", f"rank_{v}"]]
        print(f"  best (rank 1–3):\n{best.to_string(index=False)}")
