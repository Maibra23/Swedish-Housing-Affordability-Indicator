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

Normalization convention
------------------------
Two independent choices decide how a raw index value becomes a z-score. Both are
locked decisions in ``docs/REVITALIZATION_PLAN.md`` §1.

**Window (D5, decision O2) — within year.** Each year's municipalities are
scored against that year's national distribution. The class is a statement about
a municipality's position relative to its peers *in that year*, not about the
country's affordability over time.

Note this applies to ``z_*`` only. Version B's own construction in
``affordability.py`` stays **pooled across the whole panel**, deliberately: B is
a macro-pressure measure and the pooling is what lets its level carry a time
trend (its panel mean runs −0.37 in 2015 to +0.86 in 2023, tracking the rate
shock). Normalising B within year would pin that at zero every year and delete
the signal B exists to measure.

**Transform (D6, decision O4) — log for A and C.** Versions A and C are *ratios*
of positive quantities — ``income / (price × rate)`` — and are therefore
log-normal, not normal. They were z-scored raw, which put the ±0.67σ cut on a
variable whose normality is rejected at p < 6e-15 in every year, and produced a
≈19 / 51 / 30 class split nobody chose. Taking logs first makes the variable
normal in all eleven years independently (p = 0.34 … 0.83) and moves the split to
≈23 / 48 / 28.

Version B is a weighted *sum* of z-scores, not a ratio: it is negative in 1919 of
3190 rows, so a log is undefined for it. B is z-scored raw.

Because a log is monotonic, the transform leaves every ``rank_*`` untouched — it
changes only ``z_*`` and, for 16 of 290 municipalities, ``risk_*``.

A consequence worth stating plainly: the ±0.67σ boundaries put a near-fixed
share of municipalities in each class every year by construction, so the national
*count* in each class carries no trend information.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

VERSIONS = ("a", "b", "c")

# Versions whose raw value runs opposite to risk and therefore need inverting.
_HIGHER_IS_BETTER = ("a", "c")

#: Versions that are ratios, and so are log-normal rather than normal. These are
#: log-transformed before z-scoring (D6). Version B is a weighted sum of
#: z-scores and takes negative values, so a log is undefined for it.
LOG_TRANSFORMED = ("a", "c")

# Class boundaries in standard deviations. ±0.67σ are the quartiles of a normal
# distribution, so the split is approximately 25 / 50 / 25 by construction.
_CLASS_BOUNDS = [-float("inf"), -0.67, 0.67, float("inf")]
_CLASS_LABELS = ["lag", "medel", "hog"]


def _log_for_scoring(values: pd.Series, version: str) -> pd.Series:
    """Return ``log(values)`` for z-scoring a ratio-valued version.

    Args:
        values: Raw index values for one year.
        version: Version letter, used only for the error message.

    Returns:
        The natural log of the values.

    Raises:
        ValueError: If any value is non-positive. A and C are quotients of
            positive quantities with a floored denominator, so this cannot happen
            with the shipped formulas — it would mean the formula changed, and
            silently falling back to a raw z-score would hide that behind a
            slightly different class split.
    """
    if (values <= 0).any():
        bad = int((values <= 0).sum())
        raise ValueError(
            f"version_{version} has {bad} non-positive value(s); it is treated as "
            f"log-normal (see LOG_TRANSFORMED) and cannot be log-transformed. "
            f"If the formula now admits non-positive values, revisit decision O4."
        )
    return np.log(values)


def _score_one_year(group: pd.DataFrame) -> pd.DataFrame:
    """Add z, rank and risk columns for a single year's municipalities.

    Returns a new frame; the input is not modified.
    """
    computed: dict[str, pd.Series] = {}

    for version in VERSIONS:
        values = group[f"version_{version}"].astype(float)

        if version in LOG_TRANSFORMED:
            values = _log_for_scoring(values, version)

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
