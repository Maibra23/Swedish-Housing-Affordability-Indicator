"""How much the three formulas actually disagree, which is less than it looks.

Sida 02 exists to make a credibility argument: that a municipality's standing is
not an artefact of one formula. The ranked artifact carries nine scoring columns
to support it, `z`, `rank` and `risk` for each of A, B and C, and until now the
interface read only the three `_c` ones. Six columns were computed on every
refresh, committed, and displayed nowhere.

Checking them before displaying them turned up the reason the argument was
weaker than advertised.

**Version A and Version C rank identically. Always, by construction.**

    A = I / (P · R)
    C = I / (P · max(R − π, 0.5))

Within one year `R` and `π` are national constants, so A and C differ by a
constant factor across every municipality in that year. Z-scores are computed
within year on `ln(value)`, and a constant factor is an additive shift in logs,
which the z-score removes exactly. The artifact bears it out: `z_a` equals `z_c`
to 2·10⁻¹⁵ on all 3 190 rows, and `rank_a`, `risk_a` are identical.

So a panel showing "A, B and C agree" would present an arithmetic identity as
corroboration, which is worse than showing nothing. **Version B is the only
formula that can disagree**, because its z-scores are pooled across the whole
panel and it mixes in unemployment. It disagrees with C on 73 of 290
municipalities in 2024, and on as many as 133 in 2015.

That is the honest version of the argument and the one worth showing: not "three
methods agree" but "the one method that *could* rank differently does so for a
quarter of the country, and here is where".

Where A and C do differ is in **level**, not ranking, which is what makes C the
one the site uses: at 2024's real rate the same municipality reads about five
times higher on C than on A. A ratio's level matters when a reader asks how bad
things are; its ranking is what a map colours.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

#: Risk classes, worst first, so a rendered table reads in severity order.
RISK_CLASSES: tuple[str, ...] = ("hog", "medel", "lag")


@dataclass(frozen=True)
class Agreement:
    """How B and C classify one year's municipalities, and where they part.

    Args:
        year: The year measured.
        n_kommuner: Municipalities scored that year.
        counts: `version key -> risk class -> count`.
        b_differs_from_c: Municipalities B and C put in different classes.
        a_equals_c: Whether A and C agreed on every row, which they should.
    """

    year: int
    n_kommuner: int
    counts: dict[str, dict[str, int]]
    b_differs_from_c: int
    a_equals_c: bool

    @property
    def b_differs_pct(self) -> float:
        """B's disagreement with C as a percentage of the year's municipalities."""
        if self.n_kommuner == 0:
            return 0.0
        return 100.0 * self.b_differs_from_c / self.n_kommuner


def measure_agreement(ranked: pd.DataFrame, year: int) -> Agreement:
    """Compare the three formulas' risk classifications for one year.

    Args:
        ranked: The scored artifact, needing `year` and `risk_a/_b/_c`.
        year: Year to measure.

    Returns:
        An :class:`Agreement` for that year.

    Raises:
        KeyError: If a risk column is missing, which would mean the artifact
            stopped carrying the columns this page reads.
    """
    missing = [c for c in ("risk_a", "risk_b", "risk_c") if c not in ranked.columns]
    if missing:
        raise KeyError(
            f"the ranked artifact is missing {missing}. Sida 02 reads the A and B "
            f"risk classes; if they were dropped, this section must go too rather "
            f"than silently showing only C."
        )

    rows = ranked[ranked["year"] == year]
    counts = {
        key: {
            cls: int((rows[f"risk_{key}"] == cls).sum()) for cls in RISK_CLASSES
        }
        for key in ("a", "b", "c")
    }
    return Agreement(
        year=int(year),
        n_kommuner=len(rows),
        counts=counts,
        b_differs_from_c=int((rows["risk_b"] != rows["risk_c"]).sum()),
        a_equals_c=bool((rows["risk_a"] == rows["risk_c"]).all()),
    )


def where_b_and_c_disagree(ranked: pd.DataFrame, year: int, limit: int = 8) -> pd.DataFrame:
    """The municipalities B and C classify differently, worst gap first.

    Args:
        ranked: The scored artifact.
        year: Year to inspect.
        limit: How many rows to return.

    Returns:
        A frame of `region_name`, both risk classes and both ranks, ordered by
        how far apart the two rankings put the municipality.
    """
    rows = ranked[(ranked["year"] == year) & (ranked["risk_b"] != ranked["risk_c"])].copy()
    if rows.empty:
        return rows
    rows["rank_gap"] = (rows["rank_b"].astype(int) - rows["rank_c"].astype(int)).abs()
    columns = ["region_name", "risk_c", "risk_b", "rank_c", "rank_b", "rank_gap"]
    return rows.nlargest(limit, "rank_gap")[columns].reset_index(drop=True)
