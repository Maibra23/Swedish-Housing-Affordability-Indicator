"""Conditional projection: what Version C becomes under a stated mortgage rate.

Nothing here is fitted, and that is the whole design.

**Eleven annual observations cannot support a fitted model.** Backtested against
a naive carry-forward control over three expanding origins, statistical fitting
lost on every component: income 16,2 % against 6,7 %, price 19,5 % against
5,4 %, the rate 18,2 % against 17,5 %.

**And the rate is a policy outcome, not a trend.** An unconditional projection of
Version C is an unconditional projection of Riksbank policy and bank pricing six
years out, dressed in a confidence interval it has no warrant for. Version C is
linear in the mortgage rate — the interest term of a cash-flow share — so a
stated rate gives an exact, explainable answer, and the spread between the
scenarios is the distance between assumptions, not a confidence interval.

So income and price are carried forward at documented rates, following the
precedent of `IMPUTED_INCOME_GROWTH_RATE` (limitation F9), and the mortgage rate
is a scenario the reader chooses. Every input is observed or stated.

The full evidence, and the two pipelines this replaced, are recorded as R16 in
`docs/APP_REFERENCE.md` (Part II).
"""

from __future__ import annotations

import pandas as pd

from src.indices.affordability import FIRST_INDEX_YEAR
from src.indices.cost_model import cost_share

#: Nominal annual growth, stated rather than fitted. The income figure matches
#: `IMPUTED_INCOME_GROWTH_RATE` in `src/data/panel_income.py`, so the projection
#: and the panel's own forward-fill cannot disagree about income growth.
INCOME_GROWTH = 0.03
PRICE_GROWTH = 0.02

#: Annual steps projected forward.
HORIZON = 6

#: Scenario order is display order: cheapest first.
SCENARIO_KEYS: tuple[str, ...] = ("low", "current", "high")

#: The stress rate, in percent. An editorial choice, documented as one: above
#: anything in the index window (peak 4,5 % in 2023) and the 2008 peak (5,3 %),
#: and below the 7 % kalkylränta banks test new borrowers against.
HIGH_MORTGAGE_RATE = 6.0


def scenario_mortgage_rates(observed: pd.Series) -> dict[str, float]:
    """The mortgage rate each scenario assumes, in percent.

    Args:
        observed: The yearly mortgage rate over the index window, oldest first.
            Read from the panel rather than hardcoded, so `low` and `current`
            stay true after a refresh.

    Returns:
        `scenario key -> mortgage rate`: the lowest year in the window, the last
        one, and the stated stress rate.
    """
    return {
        "low": float(observed.min()),
        "current": float(observed.iloc[-1]),
        "high": HIGH_MORTGAGE_RATE,
    }


def project_county(
    *,
    last_income: float,
    last_price: float,
    last_year: int,
    mortgage_rate: float,
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """Version C for one county under one mortgage-rate assumption.

    Args:
        last_income: Most recent observed median income, SEK.
        last_price: Most recent observed transaction price, SEK.
        last_year: The year those two were observed.
        mortgage_rate: Assumed mean rate on new mortgages, percent.
        horizon: Annual steps to project.

    Returns:
        One row per year with `target_year`, `income`, `price`, `version_c`.

    Raises:
        ValueError: If `mortgage_rate` is not a positive number, via
            `cost_share`.
    """
    rows = []
    for step in range(1, horizon + 1):
        income = last_income * (1 + INCOME_GROWTH) ** step
        price = last_price * (1 + PRICE_GROWTH) ** step
        rows.append({
            "target_year": last_year + step,
            "income": income,
            "price": price,
            "version_c": cost_share(income, price, mortgage_rate, last_year + step),
        })
    return pd.DataFrame(rows)


def project_all(county_panel: pd.DataFrame) -> pd.DataFrame:
    """Every county, every scenario, from the panel's last observed year.

    Args:
        county_panel: `affordability_county.parquet`, needing `lan_code`,
            `year`, `median_income`, `transaction_price_sek`, `mortgage_rate`.

    Returns:
        `lan_code, target_year, scenario, mortgage_rate, income, price,
        version_c`.
    """
    window = county_panel[county_panel["year"] >= FIRST_INDEX_YEAR]
    national_rate = window.groupby("year")["mortgage_rate"].median().sort_index()
    rates = scenario_mortgage_rates(national_rate)

    frames = []
    for lan_code, group in window.groupby("lan_code"):
        last = group.sort_values("year").iloc[-1]
        for scenario, rate in rates.items():
            block = project_county(
                last_income=float(last["median_income"]),
                last_price=float(last["transaction_price_sek"]),
                last_year=int(last["year"]),
                mortgage_rate=rate,
            )
            block.insert(0, "scenario", scenario)
            block.insert(0, "lan_code", lan_code)
            block["mortgage_rate"] = rate
            frames.append(block)

    out = pd.concat(frames, ignore_index=True)
    return out[
        ["lan_code", "target_year", "scenario", "mortgage_rate", "income", "price", "version_c"]
    ]
