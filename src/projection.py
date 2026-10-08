"""Conditional projection: what Version C becomes under a stated real rate.

Nothing here is fitted, and that is the whole design.

**Eleven annual observations cannot support a fitted model.** Backtested against
a naive carry-forward control over three expanding origins, statistical fitting
lost on every component: income 16,2 % against 6,7 %, price 19,5 % against
5,4 %, the real rate 18,2 % against 17,5 %.

**And the formula amplifies the resulting error.** Version C is a reciprocal of
`max(R - pi, 0.5)`. That floor binds in 9 of the 11 observed years, during which
C is exactly `200 * income / price` and the rate contributes nothing at all. The
real rate carries most of the variance in year-on-year changes of `log C`, so a
model that lets the rate escape the floor moves C by a multiple.

The conclusion is not that a better model is needed. It is that an unconditional
projection of Version C is an unconditional projection of Riksbank policy six
years out, dressed in a confidence interval that implies warrant it does not
have.

So income and price are carried forward at documented rates, following the
precedent of `IMPUTED_INCOME_GROWTH_RATE` (limitation F9), and the real rate is
a scenario the reader chooses. No regime can make this produce an absurd number,
because every input is observed or stated.

The full evidence, and the two pipelines this replaced, are recorded as R16 in
`docs/APP_REFERENCE.md` (Part II).
"""

from __future__ import annotations

import pandas as pd

#: Percentage points. Mirrors the floor in `src/indices/affordability.py` and
#: `src/scenario/simulator.py`, which apply it independently.
REAL_RATE_FLOOR = 0.5

#: Nominal annual growth, stated rather than fitted. The income figure matches
#: `IMPUTED_INCOME_GROWTH_RATE` in `src/data/panel_income.py`, so the projection
#: and the panel's own forward-fill cannot disagree about income growth.
INCOME_GROWTH = 0.03
PRICE_GROWTH = 0.02

#: Annual steps projected forward.
HORIZON = 6

#: Scenario order is display order: most affordable first.
SCENARIO_KEYS: tuple[str, ...] = ("floor", "current", "normalised")

#: The real rate a normalisation scenario assumes, in percentage points. Chosen
#: as a round pre-2015 norm rather than derived; it is an editorial decision and
#: is documented as one.
NORMALISED_REAL_RATE = 2.0


def scenario_real_rates(last_real_rate: float) -> dict[str, float]:
    """The real rate each scenario assumes, in percentage points.

    Args:
        last_real_rate: The most recently observed real rate, in percentage
            points. Read from the panel rather than hardcoded so the "current"
            scenario stays true after a refresh.

    Returns:
        `scenario key -> real rate`. The observed rate is raised to the floor if
        it sits below it, because the index cannot express a lower one.
    """
    return {
        "floor": REAL_RATE_FLOOR,
        "current": max(float(last_real_rate), REAL_RATE_FLOOR),
        "normalised": NORMALISED_REAL_RATE,
    }


def project_county(
    *,
    last_income: float,
    last_price: float,
    last_year: int,
    real_rate_pp: float,
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """Version C for one county under one real-rate assumption.

    Args:
        last_income: Most recent observed median income, SEK.
        last_price: Most recent observed transaction price, SEK.
        last_year: The year those two were observed.
        real_rate_pp: Assumed real rate, percentage points, at or above the
            floor.
        horizon: Annual steps to project.

    Returns:
        One row per year with `target_year`, `income`, `price`, `version_c`.

    Raises:
        ValueError: If `real_rate_pp` is below the floor. The index cannot
            produce such a value, so accepting one here would publish a number
            no page could reproduce.
    """
    if real_rate_pp < REAL_RATE_FLOOR:
        raise ValueError(
            f"real_rate_pp={real_rate_pp} is below the {REAL_RATE_FLOOR} pp floor "
            f"that Version C applies; the index cannot express it"
        )

    rows = []
    for step in range(1, horizon + 1):
        income = last_income * (1 + INCOME_GROWTH) ** step
        price = last_price * (1 + PRICE_GROWTH) ** step
        rows.append({
            "target_year": last_year + step,
            "income": income,
            "price": price,
            "version_c": income / (price * real_rate_pp / 100.0),
        })
    return pd.DataFrame(rows)


def project_all(county_panel: pd.DataFrame) -> pd.DataFrame:
    """Every county, every scenario, from the panel's last observed year.

    Args:
        county_panel: `affordability_county.parquet`, needing `lan_code`,
            `year`, `median_income`, `transaction_price_sek`, `policy_rate`,
            `cpi_yoy_pct`.

    Returns:
        `lan_code, target_year, scenario, real_rate_pp, income, price,
        version_c`.
    """
    frames = []
    for lan_code, group in county_panel.groupby("lan_code"):
        group = group.sort_values("year")
        last = group.iloc[-1]
        observed_real = max(
            float(last["policy_rate"]) - float(last["cpi_yoy_pct"]), REAL_RATE_FLOOR
        )
        for scenario, rate in scenario_real_rates(observed_real).items():
            block = project_county(
                last_income=float(last["median_income"]),
                last_price=float(last["transaction_price_sek"]),
                last_year=int(last["year"]),
                real_rate_pp=rate,
            )
            block.insert(0, "scenario", scenario)
            block.insert(0, "lan_code", lan_code)
            block["real_rate_pp"] = rate
            frames.append(block)

    out = pd.concat(frames, ignore_index=True)
    return out[
        ["lan_code", "target_year", "scenario", "real_rate_pp", "income", "price", "version_c"]
    ]
