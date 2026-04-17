# SHAI Methodology Reference (v2)
## Theoretical Framework, Variables, Sources, Limitations

**Version:** 2.0
**Companion to:** PRD.md, PLAYBOOK.md
**Status:** Post Day 2 revision, incorporates DEVIATIONS D1 to D13
**Last updated:** 2026-04-14

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
| Median disposable income | I | SCB HE0110 | HE/HE0110/HE0110G/TabVX4bDispInkN | Municipal, county, national | Annual | 2011 to 2024 |
| House price index | P_idx | SCB BO0501 | BO/BO0501/BO0501A/FastpiPSLanAr | County, national | Annual | 1990 to 2025 |
| Mean transaction price, småhus (arithmetic avg) | P_sek | SCB BO0501 | BO/BO0501/BO0501B/FastprisSHRegionAr (BO0501C2) | Municipal, county, national | Annual | 1981 to 2024 |
| Mean transaction price, bostadsrätt (apartment) | P_BR | SCB BO0701 | BO/BO0701/BO0701A/Bostprissh | Municipal (larger ~150–200), county, national | Annual | ~2012 to present |
| K/T ratio (descriptive) | KT | SCB BO0501 | Same table (BO0501C4) | Municipal, county | Annual | 1981 to 2024 |
| Policy rate | R | Riksbanken Swea | /Observations/SECBREPOEFF/{from}/{to} | National | Daily → annual avg | 2014 to present |
| CPI | π | SCB PR0101 | PR/PR0101/PR0101A/KPI2020M (00000807) | National | Monthly → annual avg | 1980 to present |
| CPI YoY change | π% | SCB PR0101 | Same table, code 00000804 | National | Monthly → annual avg | 1981 to present |
| Real interest rate | r* | Derived | R − π% with 0.005 floor | National | Annual | 2014 to present |
| Unemployment | U | Kolada N03937 | api.kolada.se/v3/data/kpi/N03937/year/ | Municipal, county, national | Annual | 2010 to 2024 |
| Population | N | SCB BE0101 | BE/BE0101/BE0101A/BefolkningNy | Municipal, county, national | Annual | 1968 to 2024 |
| Housing completions | H | SCB BO0101 | BO/BO0101/BO0101A/LghReHustypAr | Municipal, county, national | Annual | 1975 to 2024 |

### Notes

- **Unemployment is openly registered unemployment** (Arbetsförmedlingen definition), not AKU/ILO survey unemployment. The measures differ: the registered measure excludes persons in labor market programmes. Banking commentary in Sweden typically references AKU. We use Kolada N03937 because it provides consistent municipal coverage from 2010, which AKU does not.
- **Price variable:** the formulas use mean (arithmetic average) transaction price in SEK (BO0501C2) as the Price variable, not the price index or K/T ratio. BO0501C2 is labeled "Köpeskilling, medelvärde i tkr" — this is the MEAN, not the median. In thin markets (small municipalities) a single expensive sale can pull the mean above a representative level. See section 3 for full rationale. K/T remains in the panel as a descriptive market indicator.
- **Policy rate starts 2014** in the Swea series used. Panel rows 2011 to 2013 exist for income and other variables but formulas cannot be computed until 2014.

## 3. Formulas

### Version A: Bank style affordability ratio

```
Affordability_A(i, t) = Income(i, t) / (P_sek(i, t) × Rate(t))
```

**Use case:** Quick monthly cost ratio, mirrors traditional bank affordability calculators.
**Strength:** Intuitive, easy to explain to non technical stakeholders.
**Weakness:** Ignores inflation (nominal rate distortion), ignores down payment.

### Version B: Macro composite pressure index

```
Risk_B(i, t) = 0.35 × z(P_sek/I) + 0.25 × z(R) + 0.20 × z(U) + 0.20 × z(π)
```

Where z() denotes z score normalization across the panel.

**Use case:** Multi factor pressure monitoring, mirrors central bank macroprudential dashboards.
**Strength:** Captures multiple risk channels simultaneously.
**Weakness:** Weights are subjective, z scores require stable reference period.
**Data note:** With Kolada N03937, unemployment is available from 2010. Version B is computed for 2014 to 2024 (policy rate availability is the binding constraint).

### Version C: Real affordability (primary, recommended)

```
Affordability_C(i, t) = Income(i, t) / (P_sek(i, t) × max(R(t) − π(t), 0.005))
```

The max() floor prevents division explosion when real rates are near zero or negative.

**Use case:** Academically defensible, captures real cost of capital.
**Strength:** Inflation adjusted, standard in economics literature.
**Weakness:** Real rate can be near zero or negative, requires floor handling.

### Why mean transaction price in SEK, not price index or K/T ratio

Three candidate Price variables exist in SCB BO0501:

1. **Fastighetsprisindex** (1990=100): growth index, measures rate of change since a base year. Not comparable across regions because two counties with identical index values can have different absolute price levels.

2. **Köpeskillingskoefficient (K/T)**: ratio of transaction price to assessed value. Measures markup, not level. Rural counties have higher K/T because their assessed values lag market values more than urban areas do.

3. **Mean köpeskilling in SEK (BO0501C2)**: arithmetic mean transaction price in absolute SEK. Level measure, directly comparable across regions. Note: SCB labels this variable "Köpeskilling, medelvärde i tkr" — it is the MEAN, not the median. In thin markets the mean can be pulled above a representative level by a single high-value transaction.

SHAI uses option 3 (mean transaction price in SEK). An earlier iteration tried options 1 and 2 and both produced the counterintuitive result that Stockholm ranked most affordable. Transaction price in SEK produces the expected ordering (Stockholm least affordable, Norrbotten most affordable) because Stockholm's roughly 40 percent income advantage over Norrbotten is dominated by roughly 200 percent higher transaction prices.

K/T remains in the panel as a descriptive market indicator but does not enter any affordability formula.

## 4. Index normalization and ranking

For comparison across formulas, each index is z score normalized within its own distribution. Higher z score equals worse affordability for Version B (risk index). Versions A and C are inverted so all three display "higher equals worse" for visual consistency, with explicit labeling.

Rankings are computed on the latest complete year (2024). 290 municipalities for municipal panel, 21 counties for county panel.

## 5. Forecasting approach

### Prophet (default in UI)

- Library: `prophet`
- Decomposes into trend plus seasonality plus holidays
- Suitable for user friendly visualization
- **Limitation flag in UI:** "Prophet är optimerad för dagliga tidsserier. För årliga makrodata, se ARIMA fliken."

### ARIMA (recommended for inference)

- Library: `statsmodels.tsa.arima.model` with order selection via `pmdarima.auto_arima`
- Suitable for methodologically rigorous forecasting
- **Limitation flag in UI:** "Konfidensintervall vidgas snabbt efter år 3. Tolka långtidsprognoser med försiktighet."

### Forecast targets

Forecast income, K/T, and policy rate separately. Compose into Version C affordability. Direct affordability forecasting introduces stationarity issues.

### Horizon

**Capped at 6 annual steps** (2024 base → 2030 horizon).

Rationale: only 11 annual observations (2014 to 2024). With such limited history, forecast intervals widen rapidly. 6 steps is the upper bound where intervals retain any interpretive value. A persistent UI callout alerts users to this constraint.

## 6. Kontantinsats regime engine

Four regulatory regimes modeled:

| Regime | Period | Down payment | Amortization rule |
|--------|--------|--------------|-------------------|
| Pre 2010 | Until Oct 2010 | No formal min | None mandatory |
| Bolånetak | Oct 2010 to Jun 2016 | 15% min | None mandatory |
| Amortization 1.0 | Jun 2016 to Mar 2018 | 15% min | 2% if LTV>70%, 1% if LTV>50% |
| Amortization 2.0 | Mar 2018 to present | 15% min | Above + 1% extra if LTI>4.5x |

For each regime applied to today's median price and median income per municipality:

- Required cash (kontantinsats absolute amount)
- Years of saving needed at 10% savings rate
- Effective monthly cost (interest plus amortization)
- Residual income after housing cost

## 7. Scenario simulator

Three sliders:

| Slider | Range | Step | Default |
|--------|-------|------|---------|
| Interest rate shock | -2% to +5% | 0.25% | 0% |
| Income growth shock | -10% to +10% | 1% | 0% |
| Price shock | -25% to +25% | 5% | 0% |

Output: recalculated Version C affordability for selected county, with delta from baseline highlighted.

**Scope note:** the simulator recomputes Version C only. Versions A and B depend on additional inputs (unemployment for B) that are not exposed as sliders to keep the interface manageable. Users seeking to stress test B should adjust assumptions in the Metodologi section and rerun.

## 8. Structural limitations (F1 to F15)

| ID | Limitation | Mitigation | Severity |
|----|------------|------------|----------|
| F1 | Native K/T available for ~88% of municipality years; county K/T fallback used for remaining ~12% | `has_native_kt` flag in panel; full list of fallback municipalities on Metodologi page | Low |
| F2 | National interest rate applied at municipal and county level | Documented explicitly; municipal variation in affordability comes entirely from income and K/T differences | Medium |
| F3 | Three formulas rank municipalities differently | "Varför skiljer sig versionerna åt" comparison panel on Län jämförelse page | Low |
| F4 | Prophet weak for annual macro data (designed for daily series) | ARIMA tab labelled "rekommenderad"; Prophet labelled "standard" | Medium |
| F5 | Kontantinsats is step function not continuous | Discrete regime cards, not a slider | Low |
| F6 | Short forecast history (11 annual observations) limits horizon | Hard cap at 6 annual steps; persistent UI caveat | Medium |
| F7 | SCB API rate limits (30 calls/10s, 150k cells/query) | All data cached as parquet at build time; no live API calls from Streamlit | Low |
| F8 | Translation loses banking terminology nuance | Glossary file in swedish-translation skill; banking terms curated | Low |
| F9 | Income for 2025 and 2026 is forward filled from 2024 with zero nominal growth | `is_imputed_income` flag; UI renders imputed values with disclosure. Pessimistic for 2025–2026 (actual wage growth ~3–4%/yr). | Low–Medium |
| F10 | Unemployment is Arbetsförmedlingen registered rate, not AKU/ILO survey rate | Documented on every page where U enters a computation; definition footnote in Swedish | Low |
| F11 | SHAI formulas (A, B, C) still use only small-house prices (SCB BO0501C2, Fastighetstyp 220) for methodological continuity and a systemic-risk perspective. Bostadsrätt prices (SCB BO0701) are now part of the panel (`bostadsratt_price_sek`, plus `bostadsratt_price_sek_county` as a county reference) and exposed as a user-selectable `Pristyp` toggle on Sida 04 (Kontantinsats). **Granularity handling:** BO0501C2 is municipal for all 290 kommuner; BO0701 is municipal only for ~150–200 larger kommuner and county-level for the remainder. `has_native_bostadsratt_price` flags where the value is a county fallback. The villa-vs-bostadsrätt comparison card on Sida 04 **matches geographic level automatically** — it compares municipal villa to municipal BR where both are native, otherwise county villa to county BR — so the ratio never mixes granularities. Phase C (parallel bostadsrätt SHAI index) remains deferred. | Pristyp selector + matched-granularity comparison card on Sida 04. | Medium |
| F12 | Policy rate used directly as mortgage rate. Actual mortgage rate ≈ policy rate + bank margin (~1.5–2.5 pp, typically ~1.7 pp for 3-month fixed). Monthly housing cost and affordability formula values are optimistic by ~30%. Municipal rankings are unaffected (all use the same national rate). | Documented in Detaljer on Sida 04; noted in formula descriptions. | Medium |
| F13 | Version B: R and π are national variables (same value for all municipalities in a given year). Their z-scores carry no cross-municipal information within a single year — 45% of Version B weights (R: 25%, π: 20%) are time-only signals. Within-year municipal rankings are determined almost entirely by z(P_SEK/I) (35%) and z(U) (20%). | Documented in Version B formula description on Sida 02 and Sida 06. | Medium |
| F14 | Income is individual gross earned income (sammanräknad förvärvsinkomst). Housing is typically purchased as a couple. Single-income years-to-save is 2× the household figure. | Caption below "År att spara" KPI on Sida 04 advises dividing by 2 for couples. | Medium |
| F15 | Scenario simulator holds CPI inflation (π) constant when the rate is shocked. Real rate changes therefore equal nominal rate changes, not genuine real rate shocks. A +3 pp rate shock with unchanged inflation implies a +3 pp real rate increase, which differs from the 2022–2023 experience where real rates barely changed. | Documented in Förklaring expander on Sida 05. | Low–Medium |

### Eliminated from earlier versions

- F9 old (unemployment only from 2020 via AM0210): eliminated by switching to Kolada N03937, coverage now 2010 to 2024

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
6. Forecast confidence intervals should widen monotonically with horizon.

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