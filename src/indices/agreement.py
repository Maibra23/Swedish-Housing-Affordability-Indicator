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
one the site uses. A ratio's level matters when a reader asks how bad things
are; its ranking is what a map colours.

That level gap is the one thing Version A tells a reader that Version C does
not, so it is what A is now presented as. `inflation_adjustment` returns it as a
single figure for a year — `version_c / version_a`, which reduces to
`max(R, 0.1) / max(R - pi, 0.5)` and is therefore the same for every
municipality in that year. Sida 02 states that figure in the comparison expander
instead of giving A a row in the Robusthet class table, where a column identical
to C's by construction read as corroboration.

**The figure is only an inflation adjustment in two of the eleven years.** Both
formulas clip their rate, and on this panel the clips bind almost everywhere:

    year   R      pi     R - pi   A floored   C floored   factor
    2014    0.46  -0.17    0.63     no          no         0.735
    2015    -0.25 -0.03   -0.23     yes         yes        0.200
    2016..2021  negative or zero rates         yes  yes    0.200
    2022    0.77   8.35   -7.58     no          yes        1.536
    2023    3.46   8.65   -5.19     no          yes        6.928
    2024    3.63   2.86    0.77     no          no         4.711

In 2015–2021 the factor is 0.1/0.5: two constants divided, saying nothing about
inflation. In 2022–2023 it is the nominal rate over C's floor, so inflation
enters only by having pushed the real rate under it. Only 2014 and 2024 give
`R / (R - pi)` — and 2014's is below 1, because inflation was negative and the
real rate therefore exceeded the nominal one.

So `InflationAdjustment` carries the rates alongside the factor, and
`is_an_inflation_adjustment` says which of those three situations a year is in.
A caller that states the number without stating that would be making a smaller
version of the mistake this module exists to document.
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


#: How far apart the per-municipality C/A ratios may sit before a single stated
#: factor stops describing all of them. The identity is exact arithmetic, so
#: this is a float-noise tolerance rather than a judgement about what counts as
#: close enough: the observed spread is around 1e-16.
CONSTANT_TOLERANCE = 1e-9

#: The rate floors the two formulas clip to, in percentage points. A clips the
#: nominal rate (`compute_version_a` clips 0.001 as a decimal); C clips the real
#: rate, the same 0.5 pp the projection calls `REAL_RATE_FLOOR`. They are stated
#: here because whether each one binds decides what the A-to-C factor *means* in
#: a given year, and `tests/test_formula_agreement.py` pins both against the
#: formulas rather than trusting the copy.
NOMINAL_RATE_FLOOR_PP = 0.1
REAL_RATE_FLOOR_PP = 0.5


@dataclass(frozen=True)
class InflationAdjustment:
    """What Version C's inflation correction is worth in one year.

    The rates come with it because the factor alone does not say what it is. In
    seven of this panel's eleven years both formulas are clipped to their floors
    and the ratio is 0.1/0.5 — two constants divided, carrying no information
    about inflation at all. A caller that states the factor has to state which
    of those situations it is in.

    Args:
        year: The year measured.
        factor: `version_c / version_a` — the correction as a multiplier.
        spread: Widest relative distance between a municipality's own ratio and
            `factor`. Zero up to float noise while the rate stays national.
        n_rows: Municipalities the ratio was taken over.
        nominal_rate: The year's policy rate in percentage points, unclipped.
        real_rate: Policy rate less CPI inflation, in percentage points,
            unclipped — so a reader can see how far under the floor it sat.
    """

    year: int
    factor: float
    spread: float
    n_rows: int
    nominal_rate: float
    real_rate: float

    @property
    def is_national_constant(self) -> bool:
        """Whether one factor honestly describes every municipality in the year.

        Sida 02 states the factor as a single number, and that sentence is only
        true while this holds. The page therefore asks before stating it.
        """
        return self.n_rows > 0 and self.spread <= CONSTANT_TOLERANCE

    @property
    def nominal_floor_binds(self) -> bool:
        """Whether Version A is dividing by its floor instead of by the rate."""
        return self.nominal_rate < NOMINAL_RATE_FLOOR_PP

    @property
    def real_floor_binds(self) -> bool:
        """Whether Version C is dividing by its floor instead of by the real rate."""
        return self.real_rate < REAL_RATE_FLOOR_PP

    @property
    def is_an_inflation_adjustment(self) -> bool:
        """Whether the factor is `R / (R - pi)` and nothing else.

        Only true when neither floor binds. When C's floor binds the factor is
        the nominal rate over a constant; when both bind it is one constant over
        another. Calling either of those "the inflation adjustment" would be the
        same class of mistake as giving Version A a column of its own.
        """
        return not (self.nominal_floor_binds or self.real_floor_binds)


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


def inflation_adjustment(frame: pd.DataFrame, year: int) -> InflationAdjustment:
    """How much larger Version C reads than Version A in one year.

    A and C differ by `max(R, 0.1) / max(R - pi, 0.5)` and by nothing else: the
    rate and the inflation are national, so the quotient is identical for every
    municipality in the year. That quotient *is* the inflation adjustment.

    Args:
        frame: Any scored frame carrying `year`, `version_a` and `version_c`.
        year: Year to measure.

    Returns:
        An :class:`InflationAdjustment` for that year. A year with no scored
        rows comes back with `n_rows == 0` instead of a factor, so a caller
        cannot render a number for a year that has none.

    Raises:
        KeyError: If either version column is missing, which would mean the
            artifact stopped carrying a formula whose difference this measures.
    """
    required = ("version_a", "version_c", "policy_rate", "cpi_yoy_pct")
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise KeyError(
            f"the frame is missing {missing}. The inflation adjustment is the "
            f"ratio between Versions A and C, read together with the rates that "
            f"produce it; without all four columns Sida 02 has to drop the "
            f"figure rather than show one it cannot characterise."
        )

    rows = frame[frame["year"] == year]
    numerator = rows["version_c"].astype(float)
    denominator = rows["version_a"].astype(float)
    ratios = (numerator / denominator).where(denominator > 0).dropna()
    if ratios.empty:
        return InflationAdjustment(
            year=int(year),
            factor=0.0,
            spread=0.0,
            n_rows=0,
            nominal_rate=float("nan"),
            real_rate=float("nan"),
        )

    # National series, repeated on every municipal row. The median is the
    # year's value and is indifferent to a missing row.
    nominal_rate = float(rows["policy_rate"].astype(float).median())
    inflation = float(rows["cpi_yoy_pct"].astype(float).median())

    factor = float(ratios.median())
    # A zero median would mean Version C collapsed; report it as unusable rather
    # than dividing by it.
    spread = (
        float((ratios / factor - 1.0).abs().max()) if factor else float("inf")
    )
    return InflationAdjustment(
        year=int(year),
        factor=factor,
        spread=spread,
        n_rows=len(ratios),
        nominal_rate=nominal_rate,
        real_rate=nominal_rate - inflation,
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


def floor_history(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per year: which rate each formula used, and what that produced.

    The single figure Sida 02 states is true for the year on screen and tells a
    reader nothing about the other ten. This is the table that does: the rate A
    divided by, the rate C divided by, whether either was a floor rather than the
    market, the resulting A-to-C factor, and the national mean index that came
    out of it.

    It is the same table METHODOLOGY section 3 carries, derived rather than
    typed, so a refresh moves the page and the document together.

    Args:
        frame: A scored frame carrying `year`, both version columns and the rates.

    Returns:
        A frame ordered by year with columns `year`, `policy_rate`, `inflation`,
        `real_rate`, `rate_used_a`, `rate_used_c`, `nominal_floored`,
        `real_floored`, `factor`, `mean_index` and `income_to_price` — the last
        being the mean of income over price in percent, which is the mean index
        with the rate divided out and the only column here that can be read
        straight across years.

    Raises:
        KeyError: Via :func:`inflation_adjustment`, if a required column is gone.
    """
    rows = []
    for year in sorted(frame["year"].unique()):
        adjustment = inflation_adjustment(frame, int(year))
        if adjustment.n_rows == 0:
            continue
        scored = frame[frame["year"] == year]
        rows.append(
            {
                "year": int(year),
                "policy_rate": adjustment.nominal_rate,
                # Read, not reconstructed: `nominal - real` reintroduces the
                # rounding it was built from and shows 2015 as -0,02 against
                # the panel's -0,03.
                "inflation": float(scored["cpi_yoy_pct"].astype(float).median()),
                "real_rate": adjustment.real_rate,
                "rate_used_a": max(adjustment.nominal_rate, NOMINAL_RATE_FLOOR_PP),
                "rate_used_c": max(adjustment.real_rate, REAL_RATE_FLOOR_PP),
                "nominal_floored": adjustment.nominal_floor_binds,
                "real_floored": adjustment.real_floor_binds,
                "factor": adjustment.factor,
                "mean_index": float(scored["version_c"].astype(float).mean()),
                # The index with the rate taken out. `r` is national, so it
                # leaves the mean entirely and what remains is the mean ratio
                # of income to price — the one column here that compares
                # straight across years. See src/indices/decompose.py.
                "income_to_price": float(
                    (
                        scored["median_income"].astype(float)
                        / scored["transaction_price_sek"].astype(float)
                    ).mean()
                    * 100.0
                ),
            }
        )
    return pd.DataFrame(rows)
