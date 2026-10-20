"""How much the three formulas actually disagree, which is less than it looks.

Sida 02 exists to make a credibility argument: that a municipality's standing is
not an artefact of one formula. The ranked artifact carries nine scoring columns
to support it, `z`, `rank` and `risk` for each of A, B and C, and until now the
interface read only the three `_c` ones. Six columns were computed on every
refresh, committed, and displayed nowhere.

Checking them before displaying them turned up the reason the argument was
weaker than advertised.

**Version A and Version C rank identically. Always, by construction.**

    A = k · (P / I) · r
    C = k · (P / I) · (r · (1 − 0,30) + amortisation)

Within one year `r` and the amortisation rate are national constants, so A and C
differ by a constant factor across every municipality in that year. Z-scores are
computed within year on `ln(value)`, and a constant factor is an additive shift
in logs, which the z-score removes exactly. The artifact bears it out: `z_a`
equals `z_c` to 10⁻¹⁵ on all 3 190 rows, and `rank_a`, `risk_a` are identical.

So a panel showing "A, B and C agree" would present an arithmetic identity as
corroboration, which is worse than showing nothing. **Version B is the only
formula that can disagree**, because its z-scores are pooled across the whole
panel and it mixes in unemployment. It disagrees with C on 73 of 290
municipalities in 2024, and on as many as 133 in 2015.

That is the honest version of the argument and the one worth showing: not "three
methods agree" but "the one method that *could* rank differently does so for a
quarter of the country, and here is where".

Where A and C do differ is in **level**, not ranking. A is the bank's gross view
of the loan, interest only; C is what the household pays out, after the interest
deduction and with amortisation. `cost_adjustment` returns that gap as a single
figure for a year — `version_c / version_a`, which reduces to
`(r · 0,7 + 100 · amortisation) / r` and is therefore the same for every
municipality in that year. Sida 02 states it in the comparison expander instead
of giving A a row in the Robusthet class table.

**The figure means the same thing in every year.** It used to be the "inflation
adjustment" `max(R, 0,1) / max(R − π, 0,5)`, and because both of those rates were
floored it meant four different things across the panel and was two constants
divided for seven years running. Neither cost formula has a floor, so the factor
is always deduction plus amortisation against gross interest: below 1 before the
amortisation requirement (0,70 in 2014 and 2015), about 1,9 in the low-rate
years, and 1,17 in 2024.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.indices.cost_model import INTEREST_DEDUCTION, amortisation_rate
from src.indices.kommun_components import cost_rate

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


#: How far apart the per-municipality C/A ratios may sit before a single stated
#: factor stops describing all of them. The identity is exact arithmetic, so
#: this is a float-noise tolerance rather than a judgement about what counts as
#: close enough: the observed spread is around 1e-16.
CONSTANT_TOLERANCE = 1e-9

@dataclass(frozen=True)
class CostAdjustment:
    """What the household's view adds to the bank's view in one year.

    Args:
        year: The year measured.
        factor: `version_c / version_a`.
        spread: Widest relative distance between a municipality's own ratio and
            `factor`. Zero up to float noise while the rate stays national.
        n_rows: Municipalities the ratio was taken over.
        mortgage_rate: The year's mean rate on new mortgages, percent.
        amortisation_pct: Amortisation in force, percent of the loan a year.
    """

    year: int
    factor: float
    spread: float
    n_rows: int
    mortgage_rate: float
    amortisation_pct: float

    @property
    def is_national_constant(self) -> bool:
        """Whether one factor honestly describes every municipality in the year.

        Sida 02 states the factor as a single number, and that sentence is only
        true while this holds. The page therefore asks before stating it.
        """
        return self.n_rows > 0 and self.spread <= CONSTANT_TOLERANCE

    @property
    def net_interest_pct(self) -> float:
        """Interest after the deduction, percent of the loan a year."""
        return self.mortgage_rate * (1.0 - INTEREST_DEDUCTION)


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


def cost_adjustment(frame: pd.DataFrame, year: int) -> CostAdjustment:
    """How much larger Version C reads than Version A in one year.

    A and C differ by `(r · 0,7 + 100 · amortisation) / r` and by nothing else:
    the rate and the amortisation rule are national, so the quotient is
    identical for every municipality in the year.

    Args:
        frame: Any scored frame carrying `year`, `version_a`, `version_c` and
            `mortgage_rate`.
        year: Year to measure.

    Returns:
        A :class:`CostAdjustment` for that year. A year with no scored rows
        comes back with `n_rows == 0` instead of a factor, so a caller cannot
        render a number for a year that has none.

    Raises:
        KeyError: If a required column is missing.
    """
    required = ("version_a", "version_c", "mortgage_rate")
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise KeyError(
            f"the frame is missing {missing}. The cost adjustment is the ratio "
            f"between Versions A and C, read together with the rate that "
            f"produces it; without all three columns Sida 02 has to drop the "
            f"figure rather than show one it cannot characterise."
        )

    rows = frame[frame["year"] == year]
    numerator = rows["version_c"].astype(float)
    denominator = rows["version_a"].astype(float)
    ratios = (numerator / denominator).where(denominator > 0).dropna()
    amortisation_pct = amortisation_rate(int(year)) * 100.0
    if ratios.empty:
        return CostAdjustment(
            year=int(year), factor=0.0, spread=0.0, n_rows=0,
            mortgage_rate=float("nan"), amortisation_pct=amortisation_pct,
        )

    factor = float(ratios.median())
    spread = float((ratios / factor - 1.0).abs().max()) if factor else float("inf")
    return CostAdjustment(
        year=int(year),
        factor=factor,
        spread=spread,
        n_rows=len(ratios),
        # National series, repeated on every municipal row.
        mortgage_rate=float(rows["mortgage_rate"].astype(float).median()),
        amortisation_pct=amortisation_pct,
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


def cost_history(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per year: the rate, the amortisation, and what they produced.

    Version C is `k · (P / I) · q`, with `q` the national cost per krona
    borrowed. The national mean therefore factors exactly into `q` and the mean
    price-to-income ratio, and this table carries both, so any move in the mean
    index can be read as "the rate and the rules" against "prices against
    incomes". METHODOLOGY section 3 carries the same table, derived rather than
    typed, so a refresh moves the page and the document together.

    Args:
        frame: A scored frame carrying `year`, both version columns, the inputs
            and `mortgage_rate`.

    Returns:
        A frame ordered by year with columns `year`, `mortgage_rate`,
        `amortisation_pct`, `cost_rate`, `factor`, `mean_index` and
        `price_to_income` — the last being the mean of price over income, in
        years of median income, which is the mean index with the cost rate
        divided out.

    Raises:
        KeyError: Via :func:`cost_adjustment`, if a required column is gone.
    """
    rows = []
    for year in sorted(frame["year"].unique()):
        adjustment = cost_adjustment(frame, int(year))
        if adjustment.n_rows == 0:
            continue
        scored = frame[frame["year"] == year]
        rows.append(
            {
                "year": int(year),
                "mortgage_rate": adjustment.mortgage_rate,
                "amortisation_pct": adjustment.amortisation_pct,
                "cost_rate": float(cost_rate(scored.head(1)).iloc[0]),
                "factor": adjustment.factor,
                "mean_index": float(scored["version_c"].astype(float).mean()),
                "price_to_income": float(
                    (
                        scored["transaction_price_sek"].astype(float)
                        / scored["median_income"].astype(float)
                    ).mean()
                ),
            }
        )
    return pd.DataFrame(rows)
