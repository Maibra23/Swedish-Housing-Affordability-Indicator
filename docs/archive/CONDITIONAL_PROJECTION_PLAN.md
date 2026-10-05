# Conditional Projection Implementation Plan

**Goal:** Replace Sida 03's six-year ARIMA/Prophet forecast, which is provably
broken for every county, with a conditional projection that states its
assumptions instead of predicting monetary policy.

**Architecture:** Delete both statistical forecast pipelines. Income and price
are carried forward at documented growth rates; the real interest rate is not
forecast at all but becomes three explicit, labelled scenarios. The page shows
one chart with three conditional lines rather than two model tabs with
confidence bands.

**Tech Stack:** Python 3.11, pandas, Plotly, Streamlit, pytest. Removes
`prophet`, `pmdarima` and `statsmodels` from the project entirely.

**Spec:** Part 1 of this document. It is self-contained — you need no prior
conversation to execute this plan.

---

## Global Constraints

Project-wide rules. Every task's requirements implicitly include these. Breaking
any of them fails the test suite.

- **Run tests with `python3.11 -m pytest`.** The machine's default `python3` is
  3.9 and cannot import `tomllib`; it silently skips the UI tests, so a green
  run under `python3` is not evidence.
- **All user-facing Swedish text lives in `SWEDISH_LABELS`** (`src/ui/labels.py`)
  and is reached through `L("key")`. `tests/test_no_inline_copy.py` fails on a
  Swedish string literal in a page. It also fails on **orphaned labels** — a key
  defined but never used.
- **Strings carrying HTML tags live in `TEMPLATES`** (`src/ui/templates.py`),
  reached through `T("key")`. Prose with no tags stays in `SWEDISH_LABELS`.
  Plotly hover templates are exempt (they carry `%{...}`).
- **No em-dashes in rendered copy.** Use commas, colons or parentheses.
- **Swedish decimal comma** in all displayed numbers: `7,7` not `7.7`.
- **No file over 400 lines** except `src/ui/labels.py`.
  `tests/test_file_sizes.py` enforces it, and `EXEMPT_CEILINGS` is empty.
- **Charts go through `get_chart_layout`** (`src/ui/chart_theme.py`), take
  colours from `COLORS` / `CHART_PALETTE` / `DIVERGING_SCALE`
  (`src/ui/tokens.py`), and pass `config={"displayModeBar": "hover"}`.
  `tests/test_chart_theme_guard.py` enforces all three and rejects hex literals.
- **CSS modules are plain strings, not f-strings** — CSS braces make f-strings
  impossible. Write hex literals and keep them in step with `tokens.py` by hand.
  `tests/test_css_naming.py` fails if `{COLORS[` survives into the stylesheet.
- **Every `.shai-*` class must be listed in `docs/DESIGN_SYSTEM.md` section 3**,
  and the stated count updated. `tests/test_design_system_doc.py` checks both
  directions.
- **Numbers quoted in copy must be interpolated from the artifacts**, never
  typed. `tests/test_copy_matches_artifacts.py` enforces it for
  `SWEDISH_LABELS` + `TEMPLATES`; `tests/test_prose_matches_artifacts.py` does
  the same for docstrings and markdown.
- **`docs/REVITALIZATION_PLAN.md` cites per-file test counts** like
  `` `tests/test_foo.py` (12) ``. They are asserted against live collection.
  After adding or removing tests, re-sync them.
- **Every maintained doc must be linked from `README.md`**'s doc table.
- **After any pipeline change, run `python3.11 scripts/audit.py`** — 27 checks
  re-derived from the committed artifacts, deliberately not importing the test
  suite so it can disagree with it.

---

# Part 1 — Spec: what is broken and why

## 1.1 What this project is

SHAI (Swedish Housing Affordability Indicator) is a Streamlit dashboard over
Sweden's 290 municipalities and 21 counties, 2014 to 2024, built on SCB,
Riksbanken and Kolada data. It publishes three affordability formulas; **Version
C is the one the site runs on**:

```
Version C = Income / (Price × max(R − π, 0.5) / 100)
```

where `R` is the Riksbank policy rate and `π` is CPI inflation, both in
percentage points. `max(…, 0.5)` is a floor on the **real interest rate**, and it
is the single most important detail in this document.

Six pages. **Sida 03 (`pages/03_Kommun_djupanalys.py`) is the only one with a
forecast**, and that forecast is what this plan replaces.

## 1.2 The defect (recorded as R16 in `docs/OPEN_RISKS.md`)

Sida 03 offers two model tabs, ARIMA and Prophet. **ARIMA's first forecast year
is implausible for all 21 counties** — every one collapses to roughly a quarter
of its last observed value in 2025 and rebounds the year after.

| Län | 2024 observed | 2025 forecast |
|---|---|---|
| 01 Stockholm | 7,7 | **1,9** |
| 03 Uppsala | 12,1 | **3,0** |
| 06 Jönköping | 17,0 | **4,1** |

Stockholm's full path: **7,7 → 1,9 → 13,1 → 13,8 → 14,5 → 15,0 → 15,5**.

The page's own copy recommends ARIMA while opening on Prophet. That
contradiction was left standing deliberately, because resolving it the obvious
way would show every reader the broken forecast on first load.

## 1.3 Root cause, layer 1: eleven observations cannot support ARIMA

Backtest protocol: expanding origin over the county panel, fit on 2014→T,
forecast T+1→2024, cutoffs at 2021, 2022 and 2023, giving 63 county-horizons.
Control: `naive`, carry the last observed value forward.

**Per-component accuracy (MAPE, lower is better):**

| Series | ARIMA | Naive | ARIMA wins? |
|---|---|---|---|
| income / price | 9,9 % | **8,4 %** | no |
| income | 16,2 % | **6,7 %** | no, 2,4× worse |
| real rate | 18,2 % | **17,5 %** | no |
| price | 19,5 % | **5,4 %** | no, 3,6× worse |

`auto_arima` loses to a constant on **every single component**. With eleven
annual points it cannot identify an order, so it fits noise and extrapolates it.

**Whole-index accuracy:**

| Method | MAPE | No forecast | Implausible |
|---|---|---|---|
| naive | **25,9 %** | 0 % | 0 % |
| forecast Version C directly | 30,5 % | 0 % | 0 % |
| forecast the real rate, recombine | 32,1 % | 7,9 % | 14,3 % |
| current (recombine components) | 32,9 % | 7,9 % | 13,5 % |

No method beats naive. The 7,9 % "no forecast" column is a separate latent
defect: the **price forecast goes non-positive** at two-year horizon, and
`arima_pipeline.py` guards it to `NaN`, so the projection silently vanishes.

## 1.4 Root cause, layer 2: the formula amplifies that error into absurdity

Stockholm's real rate, 2014 to 2024:

```
0.63, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.77
```

**At the 0,5 pp floor in 9 of 11 years.** During those nine years Version C is
*exactly* `200 × (Income / Price)` — the rate contributes nothing. This identity
holds to four decimal places in the committed artifact.

Variance decomposition of year-on-year changes in `log C`:

- **real rate: 99 %**
- income / price: 18 %

So Version C is a reciprocal of a variable that carries essentially all of its
dynamics, sits clamped for 82 % of the record, and is a **policy instrument
rather than a stochastic process**. Escaping the floor from 0,5 to 3,2 pp
divides C by 6,4. ARIMA's 2025 component forecast for Stockholm was rate 2,56 %
and CPI **−0,64 %**, giving a real rate of 3,20 pp — six times the value that
had prevailed for four years.

## 1.5 The statement that explains every failure

> **An unconditional forecast of Version C is an unconditional forecast of
> Riksbank policy six years out, delivered with a confidence interval implying
> statistical warrant it does not have.**

That is why naive wins: *"the floor keeps binding"* has been right 9 times in 11.
And why each alternative fails:

- **recombine components** — extrapolates rate and CPI, fails loudly, 21/21.
- **forecast the real rate** — same mechanism, fails less often (15/63 in
  backtest) but is not reliable; its failures cluster at the 2022 and 2023
  cutoffs, i.e. whenever the training window contains the inflation spike.
- **forecast Version C directly** — the same extrapolation one step removed.
  Never implausible, but its 80 % intervals cover only **37 %** of outcomes,
  because it inherits none of the input uncertainty. It fails quietly, which is
  worse.

## 1.6 The decision

**Stop forecasting anything ARIMA cannot beat a constant on. Make the real rate
an axis the reader chooses rather than a number the model invents.**

- Income and price: carried forward at **documented growth rates**, not fitted.
  The project already has this precedent — `IMPUTED_INCOME_GROWTH_RATE = 0.03`
  in `src/data/panel_income.py`, limitation F9.
- Real rate: **three explicit scenarios**, not a prediction.
- The word changes from *Prognos* to *Projektion*. That is doing real work: one
  claims to know the future, the other states a conditional.

**Result for Stockholms län (observed 2024 = 7,7):**

| År | Golvet, 0,5 pp | Dagens nivå, 0,77 pp | Normaliserad, 2,0 pp |
|---|---|---|---|
| 2025 | 12,0 | 7,8 | 3,0 |
| 2027 | 12,2 | 7,9 | 3,1 |
| 2030 | 12,6 | 8,2 | 3,1 |

Across all 21 counties the first year moves by exactly **1,56× / 1,01× / 0,39×**
— identical everywhere, because the real rate is national. That uniformity is a
feature: it shows the reader at a glance that the spread is about monetary
policy, not about their municipality.

## 1.7 Why this is reliable in every context

1. **Nothing is fitted**, so no training window can be unlucky. The 2022 shock
   that broke every model cannot break this.
2. **Bounded by construction.** An absurd value is unreachable: every input is
   either observed or a stated assumption.
3. **Degrades gracefully.** The three lines still mean something in 2030.
4. **Honest about where uncertainty lives** — 99 % of it in one variable, now
   the reader's dial instead of a hidden guess.
5. **Consistent with the app's own lesson.** Sida 05 exists to teach that only
   `R − π` reaches the formula. The current forecast contradicts that two pages
   away.
6. **Matches institutional practice.** Riksbanken and FI publish scenario
   outlooks, not six-year point forecasts of their own policy rate.
7. **Removes `prophet` and `pmdarima`**, the fragile half of R3 and all of R4.

## 1.8 What this costs, stated honestly

- It looks less sophisticated. "Three assumption lines" reads as simpler than
  "ARIMA (auto-AIC)" even though it is more defensible.
- **Someone must own the three scenario values.** This plan sets them at 0,5 /
  last observed / 2,0; that is an editorial decision, not a derived fact.
- Confidence bands disappear, replaced by the spread between scenarios. More
  honest, but different, and the widening-band check becomes moot.
- ~560 lines of pipeline are deleted.

---

# Part 2 — What we are building

## 2.1 The projection

For each county, for each of six years 2025 to 2030, and for each of three
scenarios:

```
income(n)  = last_observed_income × (1 + 0.03)ⁿ
price(n)   = last_observed_price  × (1 + 0.02)ⁿ
C(n)       = income(n) / (price(n) × real_rate_pp / 100)
```

`real_rate_pp` is constant within a scenario and never below the 0,5 floor.

## 2.2 The three scenarios

| Key | Real rate | Meaning |
|---|---|---|
| `floor` | 0,5 pp | The floor binds, as it has in 9 of 11 observed years |
| `current` | last observed | Today's real rate persists |
| `normalised` | 2,0 pp | The real rate returns to a pre-2015 norm |

`current` is resolved from the data, not hardcoded, so it stays true after a
refresh.

## 2.3 What Sida 03 shows afterwards

One chart, no tabs:

- **Kommunen** — the municipality's observed Version C, solid, `COLORS["primary"]`
- **Länet** — the county's observed Version C, dotted, `COLORS["secondary"]`
- **Three projection lines** from the county's last observed year, dashed:
  `low_risk` (floor, most affordable), `secondary` (current),
  `high_risk` (normalised, least affordable)

Plus a caption naming the growth assumptions, and an explanation of why the real
rate is an assumption rather than a forecast.

---

# Part 3 — File structure

**Created**

| File | Responsibility |
|---|---|
| `src/forecast/projection.py` | The projection arithmetic and scenario definitions. Pure functions, no I/O. |
| `tests/test_projection.py` | Its tests, including the floor identity and the absurdity bound. |

**Modified**

| File | Change |
|---|---|
| `scripts/refresh_data.py` | `step_forecasts` becomes `step_projection`; writes one artifact. |
| `pages/03_Kommun_djupanalys.py` | Tabs replaced by one conditional chart. |
| `src/ui/labels.py` | New projection copy; old forecast copy removed. |
| `pyproject.toml` | `prophet`, `pmdarima`, `statsmodels` dropped from the `pipeline` extra. |
| `docs/APP_GUIDE.md` | Section 3 rewritten. |
| `docs/OPEN_RISKS.md` | R16 closed. |
| `docs/METHODOLOGY.md` | Limitation F6 rewritten. |
| `docs/DEPLOYMENT.md` | Artifact inventory updated. |
| `docs/REVITALIZATION_PLAN.md` | Session log row; test counts re-synced. |
| `README.md` | Doc table gains this plan. |
| `tests/test_smoke.py` | Forecast import check retargeted. |
| `tests/test_copy_matches_artifacts.py` | Forecast base-year test retargeted. |

**Deleted**

| File | Why |
|---|---|
| `src/forecast/arima_pipeline.py` | 261 lines. Root cause. |
| `src/forecast/prophet_pipeline.py` | 296 lines. Same mechanism, quieter. |
| `tests/test_forecast_pipelines.py` | Tests the deleted modules. |
| `data/processed/forecast_arima.parquet` | Replaced. |
| `data/processed/forecast_prophet.parquet` | Replaced. |
| `data/processed/arima_metadata.parquet` | Replaced. |

---

# Part 4 — Tasks

### Task 1: The projection module

**Files:**
- Create: `src/forecast/projection.py`
- Test: `tests/test_projection.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `REAL_RATE_FLOOR: float = 0.5`
  - `INCOME_GROWTH: float = 0.03`, `PRICE_GROWTH: float = 0.02`
  - `HORIZON: int = 6`
  - `SCENARIO_KEYS: tuple[str, ...] = ("floor", "current", "normalised")`
  - `scenario_real_rates(last_real_rate: float) -> dict[str, float]`
  - `project_county(*, last_income: float, last_price: float, last_year: int, real_rate_pp: float, horizon: int = HORIZON) -> pd.DataFrame` with columns
    `target_year, income, price, version_c`
  - `project_all(county_panel: pd.DataFrame) -> pd.DataFrame` with columns
    `lan_code, target_year, scenario, real_rate_pp, income, price, version_c`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_projection.py`:

```python
"""The conditional projection, and the identity it rests on.

Version C is a reciprocal of the real interest rate, floored at 0,5 pp. In the
committed panel that floor binds in 9 of 11 years, during which Version C is
exactly 200 x (income / price) and the rate contributes nothing. The real rate
carries 99 % of the variance in year-on-year changes of log C.

That is why nothing here forecasts it. Income and price are carried forward at
documented rates; the real rate is a stated scenario. These tests pin the
arithmetic and, more importantly, the property that made the old forecast
unusable: no input can produce an absurd output.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.forecast.projection import (
    HORIZON,
    INCOME_GROWTH,
    PRICE_GROWTH,
    REAL_RATE_FLOOR,
    SCENARIO_KEYS,
    project_all,
    project_county,
    scenario_real_rates,
)

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "affordability_county.parquet"


def test_at_the_floor_version_c_is_two_hundred_times_income_over_price() -> None:
    """The identity the whole design rests on.

    While the floor binds, the rate drops out of the formula entirely:
    C = I / (P * 0.005) = 200 * I / P. If this ever fails, either the floor
    moved or the formula did, and the projection's premise needs revisiting.
    """
    out = project_county(
        last_income=400_000.0, last_price=8_000_000.0, last_year=2024,
        real_rate_pp=REAL_RATE_FLOOR, horizon=1,
    )
    row = out.iloc[0]
    assert row["version_c"] == pytest.approx(200 * row["income"] / row["price"])


def test_growth_compounds_from_the_last_observed_year() -> None:
    out = project_county(
        last_income=100.0, last_price=1000.0, last_year=2024,
        real_rate_pp=1.0, horizon=3,
    )
    assert out["target_year"].tolist() == [2025, 2026, 2027]
    assert out["income"].tolist() == pytest.approx(
        [100 * (1 + INCOME_GROWTH) ** n for n in (1, 2, 3)]
    )
    assert out["price"].tolist() == pytest.approx(
        [1000 * (1 + PRICE_GROWTH) ** n for n in (1, 2, 3)]
    )


def test_version_c_is_a_reciprocal_of_the_real_rate() -> None:
    """Doubling the real rate halves affordability. This is the sensitivity that
    made an extrapolated denominator unusable."""
    common = dict(last_income=400_000.0, last_price=8_000_000.0, last_year=2024, horizon=1)
    low = project_county(real_rate_pp=1.0, **common).iloc[0]["version_c"]
    high = project_county(real_rate_pp=2.0, **common).iloc[0]["version_c"]
    assert high == pytest.approx(low / 2)


def test_a_real_rate_below_the_floor_is_refused() -> None:
    """The floor is part of the formula, not a display convention. Accepting a
    lower rate here would silently publish a value the index cannot produce."""
    with pytest.raises(ValueError, match="floor"):
        project_county(
            last_income=400_000.0, last_price=8_000_000.0, last_year=2024,
            real_rate_pp=0.1, horizon=1,
        )


def test_scenarios_carry_the_floor_and_the_observed_rate() -> None:
    rates = scenario_real_rates(0.77)
    assert set(rates) == set(SCENARIO_KEYS)
    assert rates["floor"] == REAL_RATE_FLOOR
    assert rates["current"] == 0.77
    assert rates["normalised"] == 2.0


def test_an_observed_rate_under_the_floor_is_raised_to_it() -> None:
    """`current` is read from data, and the data can sit below the floor."""
    assert scenario_real_rates(0.2)["current"] == REAL_RATE_FLOOR


@pytest.fixture(scope="module")
def county_panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


def test_every_county_and_scenario_is_projected(county_panel: pd.DataFrame) -> None:
    out = project_all(county_panel)
    assert out["lan_code"].nunique() == 21
    assert set(out["scenario"]) == set(SCENARIO_KEYS)
    per_series = out.groupby(["lan_code", "scenario"]).size()
    assert (per_series == HORIZON).all()


def test_no_projection_is_absurd(county_panel: pd.DataFrame) -> None:
    """The property the old forecast could not hold.

    ARIMA put 21 of 21 counties outside 0,5x..2x of their last observed value in
    the first projected year. Nothing here is fitted, so nothing can.
    """
    out = project_all(county_panel)
    last = county_panel[county_panel["year"] == county_panel["year"].max()]
    last = last.set_index("lan_code")["version_c"]
    first = out[out["target_year"] == out["target_year"].min()]
    ratio = first["version_c"].to_numpy() / last.loc[first["lan_code"]].to_numpy()
    assert np.isfinite(ratio).all(), "a projection produced inf or NaN"
    assert (ratio > 0.25).all() and (ratio < 4.0).all(), (
        f"projection ratios run {ratio.min():.2f}x to {ratio.max():.2f}x"
    )


def test_the_current_scenario_barely_moves(county_panel: pd.DataFrame) -> None:
    """Holding the real rate at today's level should reproduce roughly today's
    value, moved only by the income and price growth assumptions."""
    out = project_all(county_panel)
    last = county_panel[county_panel["year"] == county_panel["year"].max()]
    last = last.set_index("lan_code")["version_c"]
    first = out[(out["scenario"] == "current") & (out["target_year"] == out["target_year"].min())]
    ratio = first["version_c"].to_numpy() / last.loc[first["lan_code"]].to_numpy()
    assert ratio.min() > 0.9 and ratio.max() < 1.15


def test_the_floor_scenario_is_the_most_affordable(county_panel: pd.DataFrame) -> None:
    """Lower real rate, higher Version C. If this inverts, the orientation
    contract has been broken somewhere."""
    out = project_all(county_panel)
    wide = out.pivot_table(index=["lan_code", "target_year"], columns="scenario", values="version_c")
    assert (wide["floor"] > wide["normalised"]).all()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3.11 -m pytest tests/test_projection.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'src.forecast.projection'`

- [ ] **Step 3: Write the implementation**

Create `src/forecast/projection.py`:

```python
"""Conditional projection: what Version C becomes under a stated real rate.

This replaced ARIMA and Prophet on 2026-09-25. Both forecast the components of
Version C and recombined them, and both were unusable for the same reason.

**Eleven annual observations cannot support a fitted model.** Backtested against
a naive carry-forward control over three expanding origins, `auto_arima` lost on
every component: income 16,2 % against 6,7 %, price 19,5 % against 5,4 %, the
real rate 18,2 % against 17,5 %.

**And the formula amplifies the resulting error.** Version C is a reciprocal of
`max(R - pi, 0.5)`. That floor binds in 9 of the 11 observed years, during which
C is exactly `200 * income / price` and the rate contributes nothing at all. The
real rate carries 99 % of the variance in year-on-year changes of `log C`. So a
model that lets the rate escape the floor moves C by a multiple: ARIMA put the
2025 real rate at 3,20 pp against a floor of 0,50 and divided Stockholm's index
by four.

The conclusion is not that a better model is needed. It is that an unconditional
forecast of Version C is an unconditional forecast of Riksbank policy six years
out, dressed in a confidence interval that implies warrant it does not have.

So nothing here is fitted. Income and price are carried forward at documented
rates, following the precedent of `IMPUTED_INCOME_GROWTH_RATE` (limitation F9),
and the real rate is a scenario the reader chooses. No regime can make this
produce an absurd number, because every input is observed or stated.

See `docs/CONDITIONAL_PROJECTION_PLAN.md` for the full evidence.
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3.11 -m pytest tests/test_projection.py -q`
Expected: PASS, 10 tests.

- [ ] **Step 5: Commit**

```bash
git add src/forecast/projection.py tests/test_projection.py
git commit -m "feat: conditional projection, which states its assumptions instead of fitting them"
```

---

### Task 2: Write the projection artifact from the refresh pipeline

**Files:**
- Modify: `scripts/refresh_data.py` (`step_forecasts`, around line 158, and the
  `--no-forecast` flag around line 195)
- Test: `tests/test_projection.py` (append)

**Interfaces:**
- Consumes: `project_all` from Task 1.
- Produces: `data/processed/projection.parquet` with the columns `project_all`
  returns.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_projection.py`:

```python
def test_the_committed_projection_matches_the_committed_panel(
    county_panel: pd.DataFrame,
) -> None:
    """The artifact the page reads must be the one this module produces.

    Nothing is fitted, so this is a pure function of the panel: if the two
    disagree, the artifact is stale and the refresh needs re-running.
    """
    artifact = ROOT / "data" / "processed" / "projection.parquet"
    assert artifact.exists(), "run: python3.11 scripts/refresh_data.py --no-fetch"

    stored = pd.read_parquet(artifact).sort_values(
        ["lan_code", "scenario", "target_year"]
    ).reset_index(drop=True)
    fresh = project_all(county_panel).sort_values(
        ["lan_code", "scenario", "target_year"]
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(stored, fresh, check_dtype=False, rtol=1e-9)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3.11 -m pytest tests/test_projection.py -k committed -q`
Expected: FAIL on the `assert artifact.exists()` line.

- [ ] **Step 3: Replace the forecast step**

In `scripts/refresh_data.py`, replace the whole `step_forecasts` function with:

```python
def step_projection() -> None:
    """Compute the conditional projection and save it."""
    logger.info("=" * 60)
    logger.info("STEP 4 — Conditional projection")
    logger.info("=" * 60)

    import pandas as pd

    from src.forecast.projection import project_all

    DATA_DIR = PROJECT_ROOT / "data" / "processed"
    county = pd.read_parquet(DATA_DIR / "affordability_county.parquet")
    out = project_all(county)
    target = DATA_DIR / "projection.parquet"
    out.to_parquet(target, index=False)
    logger.info(
        "  Saved %s  (%d rows, %d counties, %d scenarios)",
        target.name, len(out), out["lan_code"].nunique(), out["scenario"].nunique(),
    )
```

Then update the two call sites. Replace `step_forecasts()` with
`step_projection()`, and change the flag and its help text:

```python
    parser.add_argument(
        "--no-projection",
        action="store_true",
        help="skip the conditional projection step",
    )
```

```python
    if not args.no_projection:
        step_projection()
    else:
        logger.info("Skipping STEP 4 (--no-projection)")
```

Also update the module docstring at the top of the file: step 4 is no longer
"Run ARIMA and Prophet forecast pipelines" but "Compute the conditional
projection (no model fitting; see docs/CONDITIONAL_PROJECTION_PLAN.md)".

- [ ] **Step 4: Run the pipeline and the test**

```bash
python3.11 scripts/refresh_data.py --no-fetch
python3.11 -m pytest tests/test_projection.py -q
```
Expected: the pipeline logs `Saved projection.parquet (378 rows, 21 counties, 3 scenarios)`, and all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/refresh_data.py data/processed/projection.parquet tests/test_projection.py
git commit -m "feat: refresh pipeline writes the projection instead of fitting forecasts"
```

---

### Task 3: Rewire Sida 03 to the projection

**Files:**
- Modify: `pages/03_Kommun_djupanalys.py`
- Modify: `src/ui/labels.py`

**Interfaces:**
- Consumes: `data/processed/projection.parquet` from Task 2.
- Produces: no new Python interface; the page renders one chart.

- [ ] **Step 1: Add the copy**

In `src/ui/labels.py`, **remove** these now-unused keys (the orphan guard in
`tests/test_no_inline_copy.py` will fail if they are left):

```
kd.serie_intervall
kd.serie_prognos
kd.prognos_for_v0
kd.prognoserna_beraknas_pa_lansniva_v0_inte_per
kd.prognoser_baseras_pa_v0_arliga_observationer
kd.lanets_historik_hover
kd.forklaring_prognos
kd.om_prognosen
kd.om_prognosen_text
```

`kd.forklaring_prognos` is rendered by an `explanation(...)` call near the foot
of the page (around line 366) and `kd.om_prognosen` / `kd.om_prognosen_text` by
the expander directly beneath it. Delete that `explanation` call and that
expander: the projection explains itself in the card, and an expander headed
"Om prognosen" would now describe something the page no longer shows.

Then **add**, next to the remaining `kd.serie_*` keys:

```python
    "kd.projektion_rubrik": "Projektion för {v0}",
    "kd.projektion_underrubrik": "Tre antaganden om realräntan",
    "kd.projektion_tagg": "PROJEKTION",
    "kd.scenario_golvet": "Realräntan vid golvet, 0,5 pp",
    "kd.scenario_dagens": "Realräntan kvar på {v0} pp",
    "kd.scenario_normaliserad": "Realräntan normaliseras till 2,0 pp",
    "kd.projektion_hover": "<b>%{x}</b><br>SHAI %{y:,.1f}<extra>%{fullData.name}</extra>",
    "kd.lanet_hover": "<b>%{x}</b><br>SHAI %{y:,.1f}<extra>Länet</extra>",
    "kd.projektion_antaganden": "Inkomsten skrivs fram med {v0} % per år och priset med {v1} % per år. Ingenting är modellanpassat.",
    "kd.projektion_forklaring": "Det här är inte en prognos utan en projektion. Version C är en invers av realräntan, alltså styrränta minus inflation, och den räntan står för nästan hela variationen i indexet mellan år. Den är också ett penningpolitiskt beslut snarare än en statistisk process, och den har legat på golvet 0,5 procentenheter i nio av elva observerade år. Att extrapolera den från elva årsvärden är att gissa Riksbankens politik sex år fram. Därför gissar sidan inte: den visar vad indexet blir under tre uttalade antaganden, och du väljer vilket som är rimligt.",
```

- [ ] **Step 2: Replace the chart builder and the tabs**

In `pages/03_Kommun_djupanalys.py`:

Replace the data load for forecasts (around lines 56 to 66) with:

```python
        projection = load_artifact("projection.parquet")
```

Replace the whole `_build_forecast_chart` function with:

```python
def _build_projection_chart(
    hist_data: pd.DataFrame,
    county_hist: pd.DataFrame,
    projection: pd.DataFrame,
    lan_code: str,
    scenario_labels: dict[str, str],
) -> go.Figure:
    """Observed history for the municipality and its county, then three
    conditional projections.

    Nothing here is fitted. The three lines differ only in their assumed real
    rate, so the spread between them is a statement about monetary policy rather
    than about this municipality. That is deliberate: the real rate carries 99 %
    of the variance in Version C's year-on-year changes, and it is a policy
    instrument, so it belongs to the reader rather than to a model.

    The municipality's own line is the page's subject. The county's is drawn too
    because the projection extends the county, and because a projection stitched
    onto a different geography is the defect this chart used to have.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist_data["year"], y=hist_data["version_c"],
        mode="lines+markers", name=L("kd.serie_kommunen"),
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=6, color=COLORS["primary"]),
        hovertemplate=L("kd.projektion_hover"),
    ))

    fig.add_trace(go.Scatter(
        x=county_hist["year"], y=county_hist["version_c"],
        mode="lines", name=L("kd.serie_lanet"),
        line=dict(color=COLORS["secondary"], width=1.5, dash="dot"),
        hovertemplate=L("kd.lanet_hover"),
    ))

    # Most affordable to least, so the legend reads in the same order as the
    # lines sit on the chart.
    scenario_colours = {
        "floor": COLORS["low_risk"],
        "current": COLORS["secondary"],
        "normalised": COLORS["high_risk"],
    }
    anchor_year = int(county_hist["year"].max())
    anchor_value = float(
        county_hist.loc[county_hist["year"] == anchor_year, "version_c"].iloc[0]
    )
    for scenario, colour in scenario_colours.items():
        block = projection[
            (projection["lan_code"] == lan_code) & (projection["scenario"] == scenario)
        ].sort_values("target_year")
        if block.empty:
            continue
        fig.add_trace(go.Scatter(
            x=[anchor_year] + block["target_year"].tolist(),
            y=[anchor_value] + block["version_c"].tolist(),
            mode="lines", name=scenario_labels[scenario],
            line=dict(color=colour, width=2, dash="dash"),
            hovertemplate=L("kd.projektion_hover"),
        ))

    layout = get_chart_layout(
        height=420,
        xaxis_title=L("kd.ar"),
        yaxis_title="SHAI (Version C)",
    )
    layout["xaxis"]["dtick"] = 1
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.04,
        xanchor="left", x=0, font=dict(size=11),
    )
    layout["margin"] = dict(l=50, r=20, t=48, b=50)
    fig.update_layout(**layout)
    return fig
```

Replace the entire forecast-tabs block (the comment beginning
`# ── Forecast tabs`, the `st.tabs(...)` call and both `with tab_...:` blocks)
with:

```python
# ── Conditional projection ───────────────────────────────────────────
_observed_real = max(
    float(_county_hist["policy_rate"].iloc[-1]) - float(_county_hist["cpi_yoy_pct"].iloc[-1]),
    REAL_RATE_FLOOR,
)
_scenario_labels = {
    "floor": L("kd.scenario_golvet"),
    "current": L("kd.scenario_dagens", v0=f"{_observed_real:.2f}".replace(".", ",")),
    "normalised": L("kd.scenario_normaliserad"),
}

with st.container(border=True):
    st.markdown(
        card_header(
            L("kd.projektion_rubrik", v0=selected_kommun),
            L("kd.projektion_underrubrik"),
            L("kd.projektion_tagg"),
        ),
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        _build_projection_chart(
            kommun_data, _county_hist, projection, lan_code, _scenario_labels
        ),
        width="stretch",
        config={"displayModeBar": "hover"},
    )
    st.caption(
        L("kd.projektion_antaganden",
          v0=f"{INCOME_GROWTH * 100:.0f}", v1=f"{PRICE_GROWTH * 100:.0f}")
    )
    explanation(L("kd.projektion_forklaring"))
```

Add the imports the new code needs, near the other `src` imports:

```python
from src.forecast.projection import INCOME_GROWTH, PRICE_GROWTH, REAL_RATE_FLOOR
```

Ensure `explanation` is imported from `src.ui.components` (it may already be).
`_county_hist` is defined around line 98 and must carry `policy_rate` and
`cpi_yoy_pct`; it comes from `affordability_county.parquet`, which has both.

Finally update the page subtitle at line 78 from
`"Historisk analys och prognos per kommun"` to
`"Historisk analys och projektion per kommun"`.

- [ ] **Step 3: Verify the page renders**

Run: `python3.11 -m pytest tests/test_pages_render.py tests/test_no_inline_copy.py tests/test_labels.py -q`
Expected: PASS. If `test_no_label_is_orphaned` fails, a key from Step 1's removal
list is still defined, or a new key is unused.

- [ ] **Step 4: Look at it in a browser**

```bash
python3.11 -m streamlit run app.py --server.port 8600 --server.headless true &
# then open http://localhost:8600/Kommun_djupanalys
```

Confirm: no tabs; one chart with five series; the three dashed projection lines
fan out from the county's last observed point; `floor` sits above `normalised`.
Stop the server afterwards with `pkill -f "streamlit run app.py"`.

- [ ] **Step 5: Commit**

```bash
git add pages/03_Kommun_djupanalys.py src/ui/labels.py
git commit -m "feat(ui): Sida 03 shows a conditional projection, not a forecast"
```

---

### Task 4: Retire ARIMA and Prophet

**Files:**
- Delete: `src/forecast/arima_pipeline.py`, `src/forecast/prophet_pipeline.py`,
  `tests/test_forecast_pipelines.py`,
  `data/processed/forecast_arima.parquet`,
  `data/processed/forecast_prophet.parquet`,
  `data/processed/arima_metadata.parquet`
- Modify: `pyproject.toml`, `tests/test_smoke.py`,
  `tests/test_copy_matches_artifacts.py`, `tests/test_validation.py`

**Interfaces:**
- Consumes: Task 3's page no longer reads the forecast artifacts.
- Produces: nothing new.

- [ ] **Step 1: Delete the modules and artifacts**

```bash
git rm src/forecast/arima_pipeline.py src/forecast/prophet_pipeline.py
git rm tests/test_forecast_pipelines.py
git rm data/processed/forecast_arima.parquet data/processed/forecast_prophet.parquet data/processed/arima_metadata.parquet
```

- [ ] **Step 2: Drop the dependencies**

In `pyproject.toml`, the `pipeline` extra becomes:

```toml
pipeline = [
    "requests>=2.31.0",
]
```

`prophet`, `pmdarima` and `statsmodels` were only used by the deleted pipelines.
Removing them means the refresh toolchain compiles nothing.

- [ ] **Step 3: Retarget the three tests that referenced forecasts**

In `tests/test_smoke.py`, `test_import_forecast_package` still passes (the
package exists and now holds `projection.py`), but make it assert the new
contents:

```python
def test_import_forecast_package():
    """The package now holds the conditional projection and nothing fitted."""
    module = importlib.import_module("forecast.projection")
    assert hasattr(module, "project_all")
```

In `tests/test_copy_matches_artifacts.py`, replace
`test_forecast_base_year_matches_the_index_end` with:

```python
def test_projection_starts_where_the_observed_data_stops() -> None:
    """The projection extends the index; it must not overlap or skip a year."""
    import pandas as pd

    projection = pd.read_parquet(
        Path(__file__).resolve().parents[1] / "data" / "processed" / "projection.parquet"
    )
    assert int(projection["target_year"].min()) == complete_case_max_year() + 1
```

In `tests/test_validation.py`, delete the skipped
`test_forecast_intervals_widen` (lines around 171 to 172) — the projection has
no intervals, so the test can never be un-skipped.

- [ ] **Step 4: Run the whole suite**

Run: `python3.11 -m pytest -q`
Expected: PASS. Then `python3.11 scripts/audit.py` — expected `PASS 27 FAIL 0`.
If `test_file_sizes.py` complains about `03_Kommun_djupanalys.py`, move
`_build_projection_chart` into a new `src/forecast/charts.py` and import it.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: retire ARIMA and Prophet, and the compilers they needed"
```

---

### Task 5: Documentation and close R16

**Files:**
- Modify: `docs/APP_GUIDE.md` (section 3), `docs/OPEN_RISKS.md` (R16),
  `docs/METHODOLOGY.md` (limitation F6), `docs/DEPLOYMENT.md`,
  `docs/REVITALIZATION_PLAN.md`, `README.md`

- [ ] **Step 1: Rewrite APP_GUIDE section 3**

`docs/APP_GUIDE.md` section 3 is *Kommun djupanalys (Sida 03)*. Its "What the
numbers actually say" subsection currently describes the ARIMA defect as live.
Rewrite it to describe the projection: the three scenarios, the fact that the
first year moves by 1,56× / 1,01× / 0,39× identically across all 21 counties
because the real rate is national, and the floor identity. Keep the existing
"the forecast is the county's, not the municipality's" paragraph — it is still
true of the projection.

- [ ] **Step 2: Close R16**

In `docs/OPEN_RISKS.md`, change the R16 table row's status to `**CLOSED**` and
append a closure section recording: the backtest evidence (ARIMA losing to naive
on all four components), the variance decomposition (99 % real rate), the floor
binding 9 of 11 years, and that the resolution was to stop forecasting rather
than to fit a better model.

- [ ] **Step 3: Update METHODOLOGY limitation F6**

F6 currently reads about a short forecast history limiting the horizon. Replace
it with a limitation about the projection being conditional: it states what it
assumes, and the spread between scenarios is not a confidence interval.

- [ ] **Step 4: Update DEPLOYMENT**

In `docs/DEPLOYMENT.md`, the artifact inventory lists the three forecast
parquets; replace them with `projection.parquet`.

`README.md` already links this plan — that row was added when the plan was
written, because `tests/test_docs_inventory.py` requires every maintained doc to
be linked and the suite would otherwise have been left red.

- [ ] **Step 5: Re-sync test counts and log the session**

```bash
python3.11 -m pytest --collect-only -q | grep -c "^tests/"
```

Update any `` `tests/<file>.py` (N) `` citation in
`docs/REVITALIZATION_PLAN.md` whose count changed, and add a session-log row
describing this work. Then:

```bash
python3.11 -m pytest -q && python3.11 scripts/audit.py
git add -A
git commit -m "docs: record why the forecast became a projection; close R16"
```

---

## Verification checklist

Run before declaring the plan complete:

- [ ] `python3.11 -m pytest -q` — all pass
- [ ] `python3.11 scripts/audit.py` — `PASS 27 FAIL 0`
- [ ] `python3.11 scripts/refresh_data.py --no-fetch` completes and rewrites
      `projection.parquet` identically (the projection is a pure function of the
      panel, so a second run must produce the same bytes)
- [ ] Sida 03 renders in a browser with one chart and no tabs
- [ ] `grep -rn "arima\|prophet" --include=*.py src pages tests` returns nothing
      outside `docs/`
- [ ] `pip install -e ".[pipeline]"` in a clean venv installs without compiling
