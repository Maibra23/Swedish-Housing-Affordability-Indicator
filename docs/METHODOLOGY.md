# SHAI Methodology Reference (v2)
## Theoretical Framework, Variables, Sources, Limitations

**Version:** 3.0
**App version:** 1.3.0
**Companion to:** ENGINE.md, APP_REFERENCE.md (Part I), DEPLOYMENT.md
**Status:** Cash-flow index (2026-10-20)
**Last updated:** 2026-10-20

### Changelog v2.x → v3.0 (2026-10-20): the index becomes a cash-flow share

- **Version C** is now the yearly cost of an 85 % loan on the mean small house, net
  interest after the 30 % deduction plus the amortisation required that year, as a
  percentage of two median incomes. It replaced `I / (P × max(R − π, 0,5))`. See §3.
- **Version A** is the gross interest on the same loan, as a percentage of the same income.
- **Version B** reads the mortgage rate and KPIF in place of the policy rate and KPI.
  Its frozen reference was re-based deliberately (`version_b_reference.json`, version 2).
- **The rate** is SCB's mean rate on new household mortgages across all fixation
  periods (FM5001, RantaT04N, "Samtliga lån"). The floating rate is used only on Sida 04.
- **All three versions now run higher = worse.** Nothing is sign-inverted in §4.
- **No rate floor remains.** F17 is closed; F18 records the new assumptions.
- **Unchanged:** every rank and risk class, for all three versions, on all 3 190
  municipality-years. Within a year the old and new A and C are reciprocals up to a
  national constant, which the within-year z-score on logs removes exactly.
- **Changed:** levels, the projection (§5), the simulator (§7) and Version B's level.

### Changelog 2026-10-05: calculator correctness (no formula or artifact change)
- **Kontantinsats: the mortgage rate is floored at zero (§6).** Policy rate plus bank
  margin went negative in 2015 to 2020 when the margin slider sat below the size of the
  negative rate, and the engine credited interest to the borrower. Commit `4859813`.
- **Both calculators refuse impossible inputs (§6, §7).** Zero, negative or missing
  income or price, and a rate passed as a percent instead of a decimal, now raise an
  error instead of returning 0 years to save or a NaN index. Commit `4859813`.
- **Scenario interpretation corrected (§7).** Floor absorption is named instead of
  reported as "oförändrad", the Riksbanken 2022 preset is explained, a baseline just
  above the floor is flagged as fragile, and the national median shift is shown beside
  the saturating class counts. Commit `9e806a3`.
- **§7 corrected:** it listed three sliders; the page has had four since the CPI shock
  was added. Full record, with evidence and the tests that guard each item:
  `docs/APP_REFERENCE.md` (Part I) section 12.

### Changelog v2.2 → v2.3 (2026-09-15)
- **Normalization convention settled on both axes (§4 rewritten).** Versions A and C are
  now **log-transformed before z-scoring**; Version B is not. Version B's own construction
  remains **pooled across the panel**, deliberately (decisions D5 and D6).
- **Why:** A and C are ratios of positive quantities and so are log-normal. Z-scoring them
  raw put the ±0.67σ class boundaries — quartiles *of a normal distribution* — on a variable
  whose normality is rejected at p < 6e-15 in every year 2014–2024. The resulting class split
  was ≈19/51/30, an asymmetry that was an artifact rather than a choice. Under the log the
  variable is normal in all eleven years independently (p = 0.34–0.83) and the split is
  ≈23/48/28.
- **Effect on published numbers:** a log is monotonic, so **all ranks are unchanged**. Only
  z-scores and, for 16 of 290 municipalities (6%), risk classes move — every one of them a
  single step toward the middle (5 hog→medel, 11 medel→lag).
- **Correction:** earlier material described the class split as "25/50/25 by construction".
  That holds only under normality, which did not obtain. Measured, it was ≈19/51/30 with
  83–89 high-risk municipalities, not ~72.
- **F9 corrected:** the limitation register stated that income imputation assumed zero
  growth. The pipeline applies 3% nominal growth per year; zero growth was the assumption F9
  *replaced*. Those years are no longer selectable in the UI in any case.
- **F16 added:** the fixed-quantile class boundaries mean the national count per risk class
  is near-constant by construction and cannot carry a trend.

### Changelog v2.1 → v2.2 (2026-04-21)
- **Bostadsrätt data source corrected:** SCB BO0701 does not exist in the API. The
  correct table is `BO/BO0501/BO0501C/FastprisBRFRegionAr` (content code BO0501R7 —
  Medelpris i tkr). All references to BO0701 in code and docs updated to BO0501C.
- **Bostadsrätt coverage clarified:** BO0501C is county-level only (21 counties +
  national). No municipality-level bostadsrätt prices exist from SCB. All municipalities
  inherit their county's mean price; the panel no longer carries the misleading
  `has_native_bostadsratt_price` flag (was always False).
- **Kontantinsats regime engine extended to 5 regimes:** Added `latt_2026`
  ("Lättnad 2026") reflecting the new Swedish mortgage law effective 1 April 2026:
  bolånetak raised from 85% to 90% (min down payment 10%), skärpt amorteringskrav
  (LTI > 4.5× → +1% amort) removed. `amort_2` period updated to "Mar 2018 – mar 2026".
  New regime is now the default baseline on Sida 04.
- **UI county-name display:** Sida 04 now shows the county name alongside the
  bostadsrätt price (e.g. "Bostadsrätt — Stockholms län (SCB BO0501C)") so users
  understand the data is at county level, not municipality level.
- **refresh_data.py import fix:** `compute_affordability` renamed to `compute_all`
  to match the actual function name in `src/indices/affordability.py`.

### Changelog v2.0 → v2.1
- County and national panels now apply the same 3% nominal income growth when
  forward-filling imputed years (was applying zero growth — audit fix)
- Bostadsrätt prices forward-filled into imputed years for all three panel levels
- The projection reads its base year dynamically from the panel
- Sidebar year range is now dynamic (always includes current calendar year)
- Version string read from `pyproject.toml` — single source of truth

---

## 1. Theoretical foundation

Housing affordability is the relationship between a household's capacity to pay and the cost of housing. Banks operationalize this through three lenses:

1. **Flow affordability** (can the household service the monthly payment?)
2. **Stock affordability** (can the household assemble the down payment?)
3. **Risk affordability** (what happens under stress?)

SHAI implements all three through the formula triplet (A, B, C), the kontantinsats engine, and the scenario simulator respectively.

## 2. Variable register (as built)

| Variable | Symbol | Source | Table / Endpoint | Resolution | Frequency | Coverage |
|----------|--------|--------|------------------|------------|-----------|----------|
| Median sammanräknad förvärvsinkomst (individual, gross) | I | SCB HE0110 | HE/HE0110/HE0110A/SamForvInk1 | Municipal, county, national | Annual | 2011 to 2024 |
| House price index | P_idx | SCB BO0501 | BO/BO0501/BO0501A/FastpiPSLanAr | County, national | Annual | 1990 to 2025 |
| Mean transaction price, småhus (arithmetic avg) | P_sek | SCB BO0501 | BO/BO0501/BO0501B/FastprisSHRegionAr (BO0501C2) | Municipal, county, national | Annual | 1981 to 2024 |
| Mean transaction price, bostadsrätt (apartment) | P_BR | SCB BO0501C | BO/BO0501/BO0501C/FastprisBRFRegionAr (BO0501R7) | **County only** (21 counties + national; no municipal data in SCB) | Annual | 2000 to 2024 |
| K/T ratio (descriptive) | KT | SCB BO0501 | Same table (BO0501C4) | Municipal, county | Annual | 1981 to 2024 |
| Mortgage rate, new household loans, all fixation periods | r | SCB FM5001 | FM/FM5001/FM5001C/RantaT04N (Rantebindningstid 1, Avtal 0100) | National | Monthly → annual avg | 2005 to present |
| KPIF YoY change | π | SCB PR0101 | PR/PR0101/PR0101G/KPIF2020 (000007ZM) | National | Monthly → annual avg | 1988 to present |
| Amortisation requirement | a(t) | Derived | 0 before June 2016, 2 % of the loan after; 2016 is 7/12 of 2 % | National | Annual | 2014 to present |
| Policy rate (Sida 04 only) | R | Riksbanken Swea | /Observations/SECBREPOEFF/{from}/{to} | National | Daily → annual avg | 2014 to present |
| CPI (real-income check only) | | SCB PR0101 | PR/PR0101/PR0101A/KPI2020M (00000807, 00000804) | National | Monthly → annual avg | 1980 to present |
| Unemployment | U | Kolada N03937 | api.kolada.se/v3/data/kpi/N03937/year/ | Municipal, county, national | Annual | 2010 to 2024 |
| Population | N | SCB BE0101 | BE/BE0101/BE0101A/BefolkningNy | Municipal, county, national | Annual | 1968 to 2024 |
| Housing completions | H | SCB BO0101 | BO/BO0101/BO0101A/LghReHustypAr | Municipal, county, national | Annual | 1975 to 2024 |

### Notes

- **Unemployment is openly registered unemployment** (Arbetsförmedlingen definition), not AKU/ILO survey unemployment. The measures differ: the registered measure excludes persons in labor market programmes. Banking commentary in Sweden typically references AKU. We use Kolada N03937 because it provides consistent municipal coverage from 2010, which AKU does not.
- **Price variable:** the formulas use mean (arithmetic average) transaction price in SEK (BO0501C2) as the Price variable, not the price index or K/T ratio. BO0501C2 is labeled "Köpeskilling, medelvärde i tkr" — this is the MEAN, not the median. In thin markets (small municipalities) a single expensive sale can pull the mean above a representative level. See section 3 for full rationale. K/T remains in the panel as a descriptive market indicator.
- **The index starts in 2014** (`FIRST_INDEX_YEAR`). The policy rate used to set that
  start, because the Swea series in use begins in 2014. It is no longer an index input,
  and the mortgage rate reaches back to 2005, so the start is now stated rather than
  imposed by data. Extending it to 2011 is a separate, deliberate decision: it would
  re-base Version B and every cross-year figure.
- **The mortgage rate is the all-fixation mean**, the rate new borrowers actually agreed
  that year, weighted by volume across floating and fixed loans. It is not the rate the
  stock of outstanding loans pays, which lags because fixed loans reprice only when they
  are refixed (F12).
- **KPIF, not KPI.** KPI prices the interest cost of owner-occupied housing, so a rate rise
  lifts KPI by itself; the Riksbank targets KPIF for that reason. Version B is the only
  formula that reads inflation.

## 3. Formulas

Versions A and C price one loan. A household of **two earners on the municipality's median
income** borrows **85 % of the mean small-house price** (the bolånetak in force from 2010 to
March 2026) at the year's **mean rate on new mortgages**. Both versions state the yearly cost of
that loan as a **percentage of the household's income**, so **higher is worse**. The code is
`src/indices/cost_model.py`.

### Version A — Bankversion (gross interest)

```
A(i, t) = 100 × 0,85 × P_sek(i, t) × r(t) / (2 × I(i, t))
```

**Use case:** the bank's view of the loan: interest only, before the tax deduction.
**Strength:** one rate, one loan, no assumption beyond the loan share.
**Weakness:** ignores the deduction and amortisation, so it understates what leaves the
household's account after June 2016 and overstates net interest before it.

### Version B — Makroversion (macro composite pressure index)

```
Risk_B(i, t) = 0.35 × z(P_sek/I) + 0.25 × z(r) + 0.20 × z(U) + 0.20 × z(π_KPIF)
```

Where z() denotes z score normalization against a frozen reference for the whole panel.

**Use case:** Multi factor pressure monitoring, mirrors central bank macroprudential dashboards.
**Strength:** Captures multiple risk channels simultaneously.
**Weakness:** Weights are subjective, z scores require stable reference period.
**Why KPIF:** KPI would count the rate twice, once as `r` and again through the mortgage
interest inside KPI.

### Version C — Kassaflödesversion (household cash flow; primary, recommended)

```
C(i, t) = 100 × 0,85 × P_sek(i, t) × (r(t) × (1 − 0,30) + a(t)) / (2 × I(i, t))
```

`r(t) × 0,7` is interest after ränteavdrag (30 % up to 100 000 SEK a year). `a(t)` is the
amortisation the requirement demands of a loan above 70 % of value: 0 before 1 June 2016,
2 % after, and 7/12 of 2 % in 2016 because every rate in the panel is an annual mean.

**Use case:** what a typical buyer's loan takes out of the household's income each year.
**Strength:** the rate enters as a multiplier, so the formula is defined and linear for any
positive rate, and no floor is needed: the mortgage rate stayed between 1,5 and 4,5 % across
the whole index period.
**Weakness:** amortisation is a cash outflow but builds the household's equity, so C measures
a cash-flow burden rather than a consumed cost (F18). Version A shows interest alone.

#### Why the formula changed

Until v3.0 Version C was `I / (P × max(R − π, 0,005))`, with R the policy rate and π KPI
inflation. Three things were wrong with it. Households pay the mortgage rate, which sat 0,8 to
2,1 pp above the policy rate and never went negative. KPI rises mechanically when rates rise.
And because `R − π` sat at or below zero for most of 2015 to 2023, the 0,5 pp floor bound in
nine of eleven years: in those years the rate contributed nothing to C, which reduced to
`200 × I / P`; the national mean fell 36 % in 2024, the year the floor released, with no
change in affordability; and a +2 pp shock cut Stockholms län's value by 72 %, because it
divided by a real rate of 0,77.

Changing the inputs alone would not have been enough. With the mortgage rate and KPIF in the
same real-rate formula, the denominator is still under the floor in seven of the eleven years
(bold below), because Swedish real mortgage rates were negative through most of the low-rate
period:

| Year | Policy rate − KPI | Mortgage rate − KPIF |
|---|---|---|
| 2014 | 0,63 | 2,01 |
| 2015 | **−0,23** | 0,98 |
| 2016 | **−1,46** | **0,34** |
| 2017 | **−2,31** | **−0,22** |
| 2018 | **−2,45** | **−0,42** |
| 2019 | **−2,06** | **−0,04** |
| 2020 | **−0,49** | 1,16 |
| 2021 | **−2,17** | **−0,89** |
| 2022 | **−7,58** | **−5,13** |
| 2023 | **−5,19** | **−1,51** |
| 2024 | 0,77 | 2,39 |

The structure was the problem. A cash-flow share multiplies by the nominal rate, which is
what a household actually pays out of nominal income, and it needs no inflation term at all:
income, price and cost are all in kronor of the same year. The same +2 pp shock now raises
Stockholms län's cost by 28 %.

**Rankings did not move.** Within a year `r`, `a` and the deduction are national, so old and
new C are both `const × (I/P)^±1`. The within-year z-score on `ln(C)` removes the constant and
the sign is the orientation flip in §4, so every rank and risk class is identical before and
after on all 3 190 municipality-years, to within 10⁻¹⁵ in z.

#### The national mean, year by year

`r` and `a` are national, so the national mean of C factors exactly:

```
mean C_t = (100 × 0,85 / 2) × q_t / 100 × mean(P/I)_t,    q_t = r_t × 0,7 + 100 × a_t
```

`q_t` is the yearly **cost per krona borrowed**, in percent of the loan. What remains,
`mean(P/I)`, is the **price-to-income ratio** in years of median income: the index with the
rate and the rules taken out. Derived by `agreement.cost_history()` and pinned to this table by
`tests/test_cost_history.py`:

| Year | Mortgage rate | Amortisation | Cost per krona | C / A | Mean C | Price / income |
|---|---|---|---|---|---|---|
| 2014 | 2,47 | 0,00 | 1,73 | 0,70 | 4,7 | 6,4 |
| 2015 | 1,85 | 0,00 | 1,30 | 0,70 | 3,7 | 6,8 |
| 2016 | 1,76 | 1,17 | 2,40 | 1,36 | 7,3 | 7,1 |
| 2017 | 1,74 | 2,00 | 3,22 | 1,85 | 10,3 | 7,5 |
| 2018 | 1,68 | 2,00 | 3,18 | 1,89 | 10,0 | 7,4 |
| 2019 | 1,66 | 2,00 | 3,16 | 1,91 | 10,0 | 7,5 |
| 2020 | 1,64 | 2,00 | 3,15 | 1,92 | 10,4 | 7,8 |
| 2021 | 1,53 | 2,00 | 3,07 | 2,01 | 11,4 | 8,8 |
| 2022 | 2,57 | 2,00 | 3,80 | 1,48 | 14,2 | 8,8 |
| 2023 | 4,53 | 2,00 | 5,17 | 1,14 | 16,9 | 7,7 |
| 2024 | 4,30 | 2,00 | 5,01 | 1,17 | 16,3 | 7,7 |

Read across: the 2016–2017 jump is the amortisation requirement (cost per krona 1,30 → 3,22
with a nearly flat rate); 2019–2021 is prices outrunning incomes at a flat rate (price/income
7,5 → 8,8); 2022–2023 is the rate cycle (cost per krona 3,07 → 5,17) partly offset by falling
prices (8,8 → 7,7). `decompose_change` splits any pair of years exactly into these two
factors, which multiply, and Sidor 01, 02 and 06 show the split in a collapsed panel
(`src/ui/cost_panel.py`).

**What the split does not claim.** `mean(P/I)` is free of the formula's rate term, not of
the rate's effect on the economy: house prices respond to rates, so a rate cycle reaches it
through `P`.

#### C over A

A and C differ by `(r × 0,7 + 100 × a) / r` and nothing else, so the quotient is one national
number per year (column C / A above): 0,70 before amortisation (the deduction alone), 1,8 to
2,0 in 2017–2021 when amortisation exceeded net interest, 1,17 in 2024. Sida 02 states it for
the selected year (`cost_adjustment`, `explain_cost_adjustment`). It used to be called the
"inflation adjustment" and meant four different things depending on which floor bound.

### Why mean transaction price in SEK, not price index or K/T ratio

Three candidate Price variables exist in SCB BO0501:

1. **Fastighetsprisindex** (1990=100): growth index, measures rate of change since a base year. Not comparable across regions because two counties with identical index values can have different absolute price levels.

2. **Köpeskillingskoefficient (K/T)**: ratio of transaction price to assessed value. Measures markup, not level. Rural counties have higher K/T because their assessed values lag market values more than urban areas do.

3. **Mean köpeskilling in SEK (BO0501C2)**: arithmetic mean transaction price in absolute SEK. Level measure, directly comparable across regions. Note: SCB labels this variable "Köpeskilling, medelvärde i tkr" — it is the MEAN, not the median. In thin markets the mean can be pulled above a representative level by a single high-value transaction.

SHAI uses option 3 (mean transaction price in SEK). An earlier iteration tried options 1 and 2 and both produced the counterintuitive result that Stockholm ranked most affordable. Transaction price in SEK produces the expected ordering (Stockholm least affordable, Norrbotten most affordable) because Stockholm's roughly 40 percent income advantage over Norrbotten is dominated by roughly 200 percent higher transaction prices.

K/T remains in the panel as a descriptive market indicator but does not enter any affordability formula.

## 4. Index normalization and ranking

Each formula yields a *level* per municipality-year. Converting that level into a z-score,
a rank and a risk class involves two independent choices. Both are locked decisions.

### 4.1 Window — within year (D5)

Each year's municipalities are scored against that year's national distribution. A risk class
is therefore a statement about a municipality's standing *relative to its contemporaries*, not
about Sweden's affordability over time.

**Deliberate exception — Version B stays pooled.** The z-scores *inside* B's own formula
(§3, Version B) are computed across the whole panel, not within year. B is a macro-pressure
measure, and that pooling is precisely what allows its level to carry a time trend: B's panel
mean runs from −0.27 (2019) to +0.72 (2023), tracking the rate cycle.

**The pooled moments are frozen.** They are derived once and stored in
`data/processed/version_b_reference.json`, and new data is scored against them. Pooling
against the panel being scored made every published B value a function of panel composition:
appending one ordinary year moved all 3190 historical rows and changed 947 ranks, and the
2026-09-21 income-source change moved 225 risk classes. A fixed reference also makes the
trend itself more honest — under the moving reference, adding a high-rate year inflated the
pooled standard deviation and pushed earlier high-rate years back toward zero, so the
yardstick shrank as the thing it measured grew. Recorded as R1 in `docs/APP_REFERENCE.md` (Part II).

*What within-year normalization would cost.* Applying the within-year window to B's
construction would set its mean to ~0 in every year by definition. The 2022–2023 rate shock —
currently B's clearest signal — would become invisible, and B would degenerate into a third
cross-sectional ranking rather than a distinct measure. The two conventions are kept, and
documented as different on purpose, because the two measures answer different questions:
A and C ask "where does this municipality stand among its peers this year", B asks "how much
macro pressure is there now compared with history".

### 4.2 Transform — log for A and C (D6)

Versions A and C are **products and ratios of positive quantities** (`price × rate / income`)
and are therefore log-normally distributed. Their z-scores are computed on `ln(value)`.

| | raw `version_c` | `log(version_c)` |
|---|---|---|
| Skewness, 2014–2024 | +1.32 … +1.92 | −0.11 … +0.17 |
| D'Agostino–Pearson normality | rejected, p < 3e-16 every year | not rejected, p = 0.24 … 0.66 every year |

This matters because the class boundaries in §4.3 are quantiles of a normal distribution.
Applied to the untransformed cost share they would produce a ≈26/54/21 split — an asymmetry
nobody chose, arising from the long right tail of the most expensive municipalities.

**Version B is not log-transformed.** It is a weighted *sum* of z-scores and takes negative
values in 1877 of 3190 rows, so the log is undefined for it.

Because the log is monotonic, this transform **does not change any ranking**. `rank_a`,
`rank_b` and `rank_c` are identical with and without it. Only z-scores and risk classes move.

### 4.3 Risk class

Boundaries at ±0.67σ, the quartiles of a normal distribution:

| z-score | Class |
|---|---|
| ≤ −0.67 | `lag` (low risk) |
| −0.67 … +0.67 | `medel` (medium) |
| > +0.67 | `hog` (high risk) |

Orientation is common to all three versions: **higher z = worse affordability**, rank 1 =
best. Since v3.0 the raw values run the same way too (A and C are cost shares, B a risk
measure), so nothing is sign-inverted. Before v3.0 A and C were affordability ratios and were
inverted here; the z-scores came out identical.

Because the boundaries are fixed quantiles, roughly a quarter of municipalities fall in each
outer class every year *by construction* (F16). The national **count** per class therefore
carries no trend information; only the shape of the distribution and individual
municipalities' movement between classes are informative.

### 4.4 Coverage

All years 2014–2024 are scored, not only the latest. 290 municipalities in the municipal
panel, 21 counties in the county panel. `src/indices/normalize.py` is the sole producer of
every `z_*`, `rank_*` and `risk_*` column.

## 5. Projection approach

The index is projected, not predicted. Statistical model fitting was evaluated
against a naive carry-forward control and lost on every component of Version C,
while the old real-rate formula amplified the residual error into implausible first-year
values for all 21 counties. It was withdrawn rather than repaired; the measurements are
recorded as **R16** in `docs/APP_REFERENCE.md` (Part II).

### How it works

`src/projection.py`. Nothing is fitted.

```
income(n)  = last_observed_income × (1 + 0.03)ⁿ
price(n)   = last_observed_price  × (1 + 0.02)ⁿ
C(n)       = 100 × 0,85 × price(n) × (r × 0,7 + 2 %) / (2 × income(n))
```

Income growth matches `IMPUTED_INCOME_GROWTH_RATE` in `src/data/panel_income.py`
(limitation F9), so the projection and the panel's own forward-fill cannot
disagree. Price growth is stated on the same footing.

### The mortgage rate is not projected

It is the axis the reader chooses. It is the largest driver of year-on-year change in
`log C` (about 60 % of the variance since 2017, against 40 % for price, checked by
`tests/test_methodology_claims.py`) and an outcome of policy and bank pricing rather than
a stochastic process. Three scenarios:

| Key | Mortgage rate | Meaning |
|---|---|---|
| `low` | the lowest annual mean in the index window (1,53 % in 2021) | Rates return to the bottom of the cycle |
| `current` | the last index year (4,30 % in 2024) | Today's rate persists |
| `high` | 6,0 % | Stress: above the 2008 peak (5,3 %), below the ~7 % kalkylränta banks test against |

`low` and `current` are resolved from the panel rather than hardcoded, so they stay true
after a refresh. `high` is an editorial decision and is documented as one. C is linear in
the rate, so the three lines sit a fixed distance apart. Amortisation is held at 2 % and
the loan at 85 % of price through the horizon, although the cap rose to 90 % in April 2026,
so that projected years compare with observed ones (F18).

### Level and horizon

County level, six annual steps. SCB publishes nothing supporting a municipal
projection, so Sida 03 draws the county history as its own labelled series and
anchors the projection to it rather than to the municipality's last value.

There are no confidence intervals. The spread between scenarios is the distance
between three assumptions, not a probability statement, and the page says so.


## 6. Kontantinsats regime engine

Five regulatory regimes modeled (updated 2026-04-21 to include the new mortgage law):

| Regime key | Label | Period | Down payment | Amortization rule |
|------------|-------|--------|--------------|-------------------|
| `pre_2010` | Före 2010 | Until Oct 2010 | No formal min | None mandatory |
| `bolanetak` | Bolånetak | Oct 2010 to Jun 2016 | 15% min (LTV cap 85%) | None mandatory |
| `amort_1` | Amorteringskrav 1.0 | Jun 2016 to Mar 2018 | 15% min | 2% if LTV>70%, 1% if LTV>50% |
| `amort_2` | Amorteringskrav 2.0 | Mar 2018 to **Mar 2026** | 15% min | Above + 1% extra if LTI>4.5x |
| `latt_2026` | Lättnad 2026 | **Apr 2026 to present** | **10% min (LTV cap 90%)** | 2% if LTV>70%, 1% if LTV>50% (LTI rule removed) |

**Regulatory basis for `latt_2026`:** New Swedish mortgage law effective 1 April 2026
(prop. to riksdag Feb 2026, voted Mar 2026; FI no longer issues regulations — codified in law):
- Bolånetak raised from 85% → 90% of market value
- Kontantinsats lowered from 15% → 10%
- Skärpt amorteringskrav (LTI > 4.5× → +1% extra amort) fully removed
- LTV-based amortization tiers unchanged (same as Amortization 1.0)
- Tilläggslån cap separately lowered from 85% → 80% (not modeled on Sida 04)

Sources: Regeringen.se 2025-12, Riksdag 2026-03, Handelsbanken/SEB/Nordea 2026-04.

The `latt_2026` regime is now the **default baseline** on Sida 04. Δ-columns on the
comparison table show differences relative to current rules, not the 2018 rules.

For each regime applied to today's median price and median income per municipality:

- Required cash (kontantinsats absolute amount)
- Years of saving needed at 10% savings rate
- Effective monthly cost (interest plus amortization)
- Residual income after housing cost

**Effective rate.** Policy rate plus bank margin, **floored at zero**. The policy rate
was negative from 2015 to 2020 and the margin is user-adjustable down to 0; Swedish
mortgage rates did not go negative, so the engine does not credit interest. Sida 04
displays the rate the engine used, not its own sum. (2026-10-05)

**Inputs are validated.** Price and income must be positive and finite, the savings
rate in (0, 1], the margin non-negative, and the rate a decimal no larger than 0,25 in
absolute value. Anything else raises `ValueError` rather than returning a plausible
number, and the page shows a message. (2026-10-05)

## 7. Scenario simulator

Three sliders:

| Slider | Range | Step | Default |
|--------|-------|------|---------|
| Mortgage rate shock | -2 to +5 pp | 0.25 pp | 0 |
| Income growth shock | -10% to +10% | 1% | 0% |
| Price shock | -25% to +25% | 5% | 0% |

Output: recalculated Version C for the selected county, the cost share in percent of
income, with the change from baseline. A positive change is a higher cost.

**The rate slider moves the mean new-mortgage rate, not the policy rate.** How much of a
policy move reaches households in a year depends on the fixation mix: a floating loan
follows within three months, a fixed one only when refixed. In 2021–2023 the policy rate
rose 3,5 pp on annual means and the all-fixation new-mortgage rate 3,0 pp. The slider
states the outcome the household faces rather than guessing the pass-through, and the
interpretation panel says so whenever the rate moves. The scenario rate is held at no less
than 0,5 %, below anything observed, and the page names it when that binds.

**There is no inflation slider.** C is a cash-flow share in kronor of the same year, so
inflation reaches it only through income, prices and the rate, which the three sliders set.
The 2021–23 preset replays the panel's annual means: +3,0 pp rate, +9 % income, −5 % price.

The surface beside the result is the rate × price plane: a contour is a price change that
exactly offsets a rate change for the selected county. Inputs are validated as in §6:
income, price and rate positive, every value finite, relative shocks above −100 %.

**Scope note:** the simulator recomputes Version C only. Versions A and B depend on additional inputs (unemployment for B) that are not exposed as sliders to keep the interface manageable. Users seeking to stress test B should adjust assumptions in the Metodologi section and rerun.

## 8. Structural limitations (F1 to F18)

| ID | Limitation | Mitigation | Severity |
|----|------------|------------|----------|
| F1 | Native K/T missing for some municipality years (none in the index period); county K/T used as fallback | `has_native_kt` flag in panel; full list of fallback municipalities on Metodologi page | Low |
| F2 | National mortgage rate and amortisation rule applied at municipal and county level | Documented explicitly; municipal variation in affordability comes entirely from income and price differences | Medium |
| F3 | Only Makroversion (B) can rank municipalities differently. Bankversion (A) and Kassaflödesversion (C) rank identically in every year by construction: the mortgage rate and the amortisation rule are national, so within a year A and C differ by a single constant factor, which a within-year z-score on logs removes exactly | Stated in the "Varför skiljer sig versionerna åt" comparison panel on the Län jämförelse page, which tabs only C and B; `tests/test_formula_agreement.py` pins the identity so the copy is revisited if it ever breaks | Low |
| F4 | Eleven annual observations cannot support a fitted statistical model | Model fitting withdrawn; conditional projection instead (R16) | Medium |
| F5 | Kontantinsats is step function not continuous | Discrete regime cards, not a slider | Low |
| F6 | The projection is conditional: it states what it assumes, and the spread between scenarios is not a confidence interval | Every line labelled with its own mortgage-rate assumption; six annual steps | Medium |
| F7 | SCB API rate limits (30 calls/10s, 150k cells/query) | All data cached as parquet at build time; no live API calls from Streamlit | Low |
| F8 | Translation loses banking terminology nuance | Glossary file in swedish-translation skill; banking terms curated | Low |
| F9 | Income beyond the last published year is forward filled with **3% nominal growth per year** (`IMPUTED_INCOME_GROWTH_RATE`, `src/data/panel_income.py`). Zero growth was the earlier, pessimistic assumption that F9 replaced. | `is_imputed_income` flag. Imputed rows are held back from the index entirely — `step_compute_indices` filters through `complete_case()` before scoring — and the year selector stops at `complete_case_max_year()`. Both matter: the selector stops an imputed year being *displayed*, the filter stops it being *pooled into Version B*, which would re-base published values for every real year. | Low |
| F10 | Unemployment is Arbetsförmedlingen registered rate, not AKU/ILO survey rate | Documented on every page where U enters a computation; definition footnote in Swedish | Low |
| F11 | SHAI formulas (A, B, C) still use only small-house prices (SCB BO0501C2, Fastighetstyp 220) for methodological continuity and a systemic-risk perspective. Bostadsrätt prices (SCB BO0501C, `FastprisBRFRegionAr`, content code BO0501R7) are now part of the panel (`bostadsratt_price_sek`) and are exposed as a user-selectable `Pristyp` toggle on Sida 04 (Kontantinsats), together with a side-by-side villa vs. bostadsrätt comparison card. **Important:** SCB publishes bostadsrätt prices at county level only — no municipal granularity exists. All 290 municipalities inherit their county's mean bostadsrätt price. The UI displays the county name (e.g. "Bostadsrätt — Stockholms län") to make this clear. The `has_native_bostadsratt_price` flag has been removed from the panel schema as it was always False. | Pristyp selector + county-name display + comparison card on Sida 04; F11 retained to document the index-scope and county-granularity limitation. | Medium |
| F12 | The index uses SCB's mean rate on **new** household mortgages across all fixation periods, not the rate a given household pays. Fixed loans reprice only when refixed, so the rate the stock of loans pays lags it, and a household on a fixed rate meets a rate change later than the index shows. Sida 04 instead models a **floating** loan: policy rate + a bank margin on a slider that defaults to the margin SCB observed that year (RantaT04N, floating ≤ 3 months, minus the policy rate; 0,8–2,1 pp since 2014, in `data/processed/mortgage_margin.json`). Municipal rankings are unaffected (all use the same national rate). | Sida 01–03 and 06 name the rate as the all-fixation mean; Sida 04 says it models a floating loan and why; Sida 05's rate slider is labelled as the mortgage rate and the interpretation panel explains fixation whenever it moves. | Medium |
| F16 | Risk class boundaries are fixed at ±0.67σ of each year's own distribution (the quartiles of a normal), so the share in each class is near-constant every year by construction: about 24 % low, 47 % medium, 29 % high (high count 80–84 of 290 in every year 2014–2024). The national count of high-risk municipalities cannot carry a trend. | Documented in §4.3; no year-over-year delta is displayed on the count. | Medium |
| F13 | Version B: r and π are national variables (same value for all municipalities in a given year). Their z-scores carry no cross-municipal information within a single year — 45% of Version B weights (r: 25%, π: 20%) are time-only signals. Within-year municipal rankings are determined almost entirely by z(P_SEK/I) (35%) and z(U) (20%). | Documented in Version B formula description on Sida 02 and Sida 06. | Medium |
| F14 | Income is individual gross earned income (sammanräknad förvärvsinkomst, SCB HE0110A/SamForvInk1), so the **Par** option models two median earners rather than the median couple. Where many households are single or retired that overstates a typical household; in dual-earner commuter municipalities it lands close. Checked against the household series it replaced: Danderyd's two median earners come to 1 020 600 SEK against a household median of 902 000, while Dorotea's come to 627 800 against 346 800. | **Hushållstyp** selector on Sida 04 offers both cases; the interpretation panel names the single-income assumption when it is what makes the result look severe. | Medium |
| F17 | **Closed 2026-10-20.** Both old formulas floored their rate (A the policy rate at 0,1 pp, C the policy rate less KPI at 0,5 pp); at least one floor bound in 9 of 11 years, so index levels did not compare across years and the A-to-C factor meant four different things. | The cash-flow formulas multiply by the mortgage rate, which never fell below 1,5 %, so no floor exists. History in §3. | — |
| F18 | The cash-flow model's assumptions: amortisation counts as an outflow although it builds equity; the extra 1 % for loans above 4,5 × income (Mar 2018 – Mar 2026) is left out because it would make the cost municipality-specific; the loan share is held at 85 % after the cap rose to 90 % in April 2026; ränteavdrag is a flat 30 % (the reduced rate above 100 000 SEK of interest is ignored). | Version A shows interest alone, without amortisation or deduction. Every assumption is a named constant in `src/indices/cost_model.py`, pinned by `tests/test_cost_model.py`. | Medium |
| F15 | Scenario shocks apply uniformly to all municipalities; regional differences in rate or price paths are not modelled. The rate shock is a change in the mean new-mortgage rate, so it describes new borrowers rather than the stock of fixed-rate loans. | Sida 05 measures the national outcome against the baseline year's fixed class boundaries, and names the fixation limit in its interpretation panel. | Low |

### Eliminated from earlier versions

- F9 old (unemployment only from 2020 via AM0210): eliminated by switching to Kolada N03937. The client now resolves its upper year at fetch time rather than carrying a literal, so coverage tracks whatever Kolada has published (2010 onward).

### Severity definitions

- **Low:** documented, mitigated, unlikely to mislead a careful reader
- **Medium:** requires explicit reader attention; caveats placed on affected pages
- **High:** none remain after Day 2 revisions

## 9. Data validation checks

Before publishing each computation:

1. Median income should trend upward nominally across 2011 to 2024. The panel shows 3 nominal decreases: 2019 (pension reform timing), 2022 (inflation shock), 2023 (continued inflation with lagging wage adjustment). This reflects documented Swedish macroeconomic history and does not indicate a data error. Check passes if nominal decreases ≤ 3.
2. Real income (nominal deflated by CPI YoY) should be roughly stable or slowly rising. Ratio 2024 / 2011 < 1.35 (relaxed from 1.30 to accommodate observed inflation dynamics).
3. **Stockholm county should rank among top 5 worst affordability under Version C** (after K/T fix). Skåne expected to rank near worst as well.
4. Norrbotten county should rank among top 5 best affordability under Version A.
5. K/T values should be between 1.0 and 4.0 for all included municipalities.
6. No projected first year falls outside 0,25× to 4× of its county's last observed value.

If any check fails, halt and investigate before proceeding.

### Post K/T fix re validation

After applying the PATCH_POST_DAY2.md P0 fix (price_index → kt_ratio), rerun checks 3 and 4. Expected:
- Stockholm moves from rank 19/21 (current, with price_index) to top 5 worst (with K/T)
- Norrbotten remains top 5 best

If Stockholm does not move to worst half after the fix, investigate income variable next.

## 10. References

- SCB BO0501 product page: https://www.scb.se/bo0501-en
- SCB HE0110 product page: https://www.scb.se/he0110-en
- SCB BE0101 product page: https://www.scb.se/be0101
- SCB PR0101 product page: https://www.scb.se/pr0101
- SCB BO0101 product page: https://www.scb.se/bo0101
- SCB PxWebApi v1 documentation: https://www.scb.se/api/
- Kolada API v3: https://api.kolada.se/v3/
- Kolada documentation: https://www.kolada.se/
- Riksbanken Swea API: https://www.riksbank.se/en-gb/statistics/interest-rates-and-exchange-rates/
- Finansinspektionen amortization rules: https://www.fi.se/en/our-registers/the-amortisation-requirement/
- Arbetsförmedlingen unemployment definition: https://arbetsformedlingen.se/statistik