"""Applying one scenario to all 290 municipalities instead of one county.

Item 9 of `docs/ANALYSIS_GUIDE.md` asked for this as "the more useful policy
question": the simulator answers *what happens to this län*, when what a reader
usually wants is *how many municipalities cross into hög risk under this
scenario*.

Implementing it the obvious way, by re-running the shock across the panel and
re-ranking, produces a number that is **always zero**, and understanding why is
the whole design of this module.

**Why a re-ranked panel cannot move.** Version C is

    C = I / (P · max(R − π, 0.5))

The sliders apply the rate and CPI shocks in percentage points nationally, and
the income and price shocks as *relative* changes. Every one of those multiplies
each municipality's C by the **same constant**. Risk classes come from a z-score
taken within year on `ln(C)`, and in logs a constant factor is an additive shift
that the z-score subtracts away exactly. Measured on the committed panel, the
largest z change under a +4 pp rate shock, a +10 % income shock or a -25 % price
shock is 9·10⁻¹⁶: floating-point noise, not an effect.

This is the same property that makes Version A and Version C rank identically
(see `src/indices/agreement.py`). It is worth stating plainly because it is
easy to build the feature, see a table of unchanged counts, and conclude the
code is broken.

**What this module does instead.** It holds the class boundaries fixed at the
baseline year's distribution and moves the country against them. The z-score
reference, the log mean and standard deviation, is computed once from the
unshocked year and then reused, so a national shock shifts every municipality's
z by the same amount and the counts either side of the ±0.67σ cuts change.

That is the only construction in which the question has an answer, and it also
changes what the answer *means*. A within-year class says "this municipality
against its peers this year". A fixed-boundary class says "this municipality
against the country as it was before the shock", which is the comparison a
scenario is asking for. The two must not be mixed in one sentence, and the copy
on Sida 05 says which one it is showing.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

#: Same cuts as `src/indices/normalize.py`. Stated again rather than imported
#: because they are used here against a *fixed* reference rather than a
#: within-year one, and a future change to one should be a deliberate decision
#: about the other, not an inherited surprise.
CLASS_BOUNDS = [-float("inf"), -0.67, 0.67, float("inf")]
CLASS_LABELS = ["lag", "medel", "hog"]

#: Percentage points, matching `simulate` and `src/indices/affordability.py`.
REAL_RATE_FLOOR = 0.5


@dataclass(frozen=True)
class PanelShockOutcome:
    """How a scenario moves the whole panel against fixed class boundaries.

    Args:
        year: Year shocked.
        n_kommuner: Municipalities scored.
        before: Risk class counts before the shock.
        after: Risk class counts after it.
        crossed_into_hog: Municipalities entering hög risk.
        crossed_out_of_hog: Municipalities leaving it.
        median_c_before: Median Version C before the shock.
        median_c_after: Median Version C after it.
        real_rate_before: Baseline real rate, percentage points.
        real_rate_after: Scenario real rate, percentage points.
    """

    year: int
    n_kommuner: int
    before: dict[str, int]
    after: dict[str, int]
    crossed_into_hog: int
    crossed_out_of_hog: int
    median_c_before: float
    median_c_after: float
    real_rate_before: float
    real_rate_after: float

    @property
    def net_into_hog(self) -> int:
        """Net change in the hög risk count. Negative means the country improved."""
        return self.after["hog"] - self.before["hog"]


def _classify(z: pd.Series) -> pd.Series:
    return pd.cut(z, bins=CLASS_BOUNDS, labels=CLASS_LABELS).astype("object")


def shock_panel(
    ranked: pd.DataFrame,
    year: int,
    *,
    rate_shock: float = 0.0,
    cpi_shock: float = 0.0,
    income_shock: float = 0.0,
    price_shock: float = 0.0,
) -> PanelShockOutcome:
    """Apply one scenario to every municipality and count the crossings.

    Args:
        ranked: The scored artifact, needing `year`, `median_income`,
            `transaction_price_sek`, `policy_rate` and `cpi_yoy_pct`.
        year: Year to shock.
        rate_shock: Policy rate change, percentage points.
        cpi_shock: Inflation change, percentage points.
        income_shock: Income change, relative (0.05 is +5 %).
        price_shock: Price change, relative.

    Returns:
        A :class:`PanelShockOutcome` measured against the baseline year's own
        class boundaries, which are held fixed. See the module docstring for why
        re-normalising instead would return an unchanged panel every time.

    Raises:
        ValueError: If the year holds no scorable rows.
    """
    rows = ranked[ranked["year"] == year].dropna(
        subset=["median_income", "transaction_price_sek", "policy_rate", "cpi_yoy_pct"]
    )
    if rows.empty:
        raise ValueError(f"no scorable municipalities in {year}")

    rate = float(rows["policy_rate"].iloc[0])
    cpi = float(rows["cpi_yoy_pct"].iloc[0])
    real_before = max(rate - cpi, REAL_RATE_FLOOR)
    real_after = max((rate + rate_shock) - (cpi + cpi_shock), REAL_RATE_FLOOR)

    income = rows["median_income"].astype(float)
    price = rows["transaction_price_sek"].astype(float)
    c_before = income / (price * real_before / 100.0)
    c_after = (income * (1 + income_shock)) / (
        price * (1 + price_shock) * real_after / 100.0
    )

    # The fixed reference: the baseline year's own distribution. Recomputing it
    # from the shocked values is what would make every count identical.
    logs = np.log(c_before)
    mean, std = float(logs.mean()), float(logs.std())
    if not std:
        raise ValueError(f"every municipality has the same Version C in {year}")

    # Negated to match the orientation contract in normalize.py: higher z is
    # worse, and Version C runs the other way.
    z_before = -(logs - mean) / std
    z_after = -(np.log(c_after) - mean) / std

    risk_before = _classify(z_before)
    risk_after = _classify(z_after)

    return PanelShockOutcome(
        year=int(year),
        n_kommuner=len(rows),
        before={cls: int((risk_before == cls).sum()) for cls in CLASS_LABELS},
        after={cls: int((risk_after == cls).sum()) for cls in CLASS_LABELS},
        crossed_into_hog=int(((risk_before != "hog") & (risk_after == "hog")).sum()),
        crossed_out_of_hog=int(((risk_before == "hog") & (risk_after != "hog")).sum()),
        median_c_before=float(c_before.median()),
        median_c_after=float(c_after.median()),
        real_rate_before=real_before,
        real_rate_after=real_after,
    )


def renormalised_rank_changes(
    ranked: pd.DataFrame,
    year: int,
    *,
    rate_shock: float = 0.0,
    cpi_shock: float = 0.0,
    income_shock: float = 0.0,
    price_shock: float = 0.0,
) -> int:
    """How many ranks move if the shocked panel is re-normalised within year.

    The answer is zero for every uniform shock, and this function exists so that
    the claim is checked rather than asserted. If it ever returns non-zero, a
    shock has stopped being uniform across municipalities and the explanation on
    Sida 05 needs rewriting.

    Args:
        ranked: The scored artifact.
        year: Year to shock.
        rate_shock: Policy rate change, percentage points.
        cpi_shock: Inflation change, percentage points.
        income_shock: Income change, relative.
        price_shock: Price change, relative.

    Returns:
        The number of municipalities whose rank would change.
    """
    rows = ranked[ranked["year"] == year].dropna(
        subset=["median_income", "transaction_price_sek", "policy_rate", "cpi_yoy_pct"]
    )
    rate = float(rows["policy_rate"].iloc[0])
    cpi = float(rows["cpi_yoy_pct"].iloc[0])
    real_before = max(rate - cpi, REAL_RATE_FLOOR)
    real_after = max((rate + rate_shock) - (cpi + cpi_shock), REAL_RATE_FLOOR)

    income = rows["median_income"].astype(float)
    price = rows["transaction_price_sek"].astype(float)
    c_before = income / (price * real_before / 100.0)
    c_after = (income * (1 + income_shock)) / (
        price * (1 + price_shock) * real_after / 100.0
    )

    rank_before = (-np.log(c_before)).rank(method="min")
    rank_after = (-np.log(c_after)).rank(method="min")
    return int((rank_before != rank_after).sum())
