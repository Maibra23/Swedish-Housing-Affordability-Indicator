# SHAI Methodology Reference
## Theoretical Framework, Variables, Sources, Limitations

**Version:** 1.3
**Companion to:** PRD.md, PLAYBOOK.md
**Status:** Living document — updated after Day 1 build to reflect actual data sources
**Last updated:** 2026-04-14

---

## 1. Theoretical foundation

Housing affordability is the relationship between a household's capacity to pay and the cost of housing. Banks operationalize this through three lenses:

1. **Flow affordability** (can the household service the monthly payment?)
2. **Stock affordability** (can the household assemble the down payment?)
3. **Risk affordability** (what happens under stress?)

SHAI implements all three through the formula triplet (A, B, C), the kontantinsats engine, and the scenario simulator respectively.

## 2. Variable register

> **Note:** Table IDs, frequencies, and coverage ranges below reflect the actual data sources used in the implementation. Several differ from the original plan — see DEVIATIONS.md for full details.

| Variable | Symbol | Source | Table / Endpoint | Resolution | Frequency | Coverage |
|----------|--------|--------|------------------|------------|-----------|----------|
| Median disposable income | I | SCB HE0110 | `HE/HE0110/HE0110G/TabVX4bDispInkN` | Municipal, county, national | Annual | 2011–2024 |
| House price index | P | SCB BO0501 | `BO/BO0501/BO0501A/FastpiPSLanAr` | County (21), national | **Annual** ¹ | 1990–2025 |
| Transaction price (K/T) | KT | SCB BO0501 | `BO/BO0501/BO0501B/FastprisSHRegionAr` | Municipal (312), county | Annual | 1981–2024 |
| Policy rate | R | Riksbanken Swea | `/Observations/SECBREPOEFF/{from}/{to}` | National | Daily → annual avg | 2014–present |
| CPI | π | SCB PR0101 | `PR/PR0101/PR0101A/KPI2020M` (skuggindex `00000807`) | National | Monthly → annual avg | 1980–present |
| CPI YoY change | π% | SCB PR0101 | Same table, code `00000804` | National | Monthly → annual avg | 1981–present |
| Real interest rate | r* = R − π | Derived | — | National | Annual | 2014–present |
| Unemployment | U | **Kolada / Arbetsförmedlingen** ² | KPI **N03937** via `api.kolada.se/v3/` | Municipal, county, national | Annual | **2010–2024** |
| Population | N | SCB BE0101 | `BE/BE0101/BE0101A/BefolkningNy` | Municipal, county, national | Annual | 1968–2024 |
| Housing completions | H | SCB BO0101 | `BO/BO0101/BO0101A/LghReHustypAr` | Municipal, county, national | Annual | 1975–2024 |

**Footnotes:**

¹ **Price index is annual, not quarterly.** County-level quarterly data does not exist in SCB — quarterly series only covers 12 riksområden (large regions), not 21 counties. The panel uses the annual county index.

² **Unemployment source changed from SCB AM0210 to Kolada N03937.** The original plan referenced SCB `AM0101`/`AM0210` which only has municipal data from 2020. Kolada KPI N03937 (source: Arbetsförmedlingen) provides all 290 municipalities from 2010–2024 with a consistent methodology. This is the same source used in the KRI (Kommunal Finansiell Riskindikator) project. Definition: openly registered unemployed persons aged 18–65 as % of total population aged 18–65, annual average. Note: this is narrower than AKU/ILO unemployment (does not include persons in labour market programmes).

## 2b. Data pipeline — extraction, transformation, storage

### Architecture

```
External APIs                  Raw cache (parquet)             Processed panels
─────────────                  ──────────────────             ────────────────
SCB PxWebApi v1 ──────────┐
  HE0110 (income)         │    data/raw/
  BO0501 (price, K/T)     ├──► HE0110_income.parquet         data/processed/
  BE0101 (population)     │    BO0501_price_index.parquet     ├─ panel_municipal.parquet
  BO0101 (construction)   │    BO0501_kt_ratio.parquet        ├─ panel_county.parquet
  PR0101 (CPI)            │    BE0101_population.parquet      └─ panel_national.parquet
                          │    BO0101_construction.parquet
Kolada API v3 ────────────┤    PR0101_cpi.parquet
  N03937 (unemployment)   │    kolada_unemployment.parquet
                          │
Riksbanken Swea v1 ───────┘    policy_rate.parquet
```

### Extraction layer (`src/data/`)

| Module | API | Rate limits | Caching |
|--------|-----|-------------|---------|
| `scb_client.py` | SCB PxWebApi v1 (`api.scb.se/OV0104/v1/doris/sv/ssd/`) | 30 calls/10s, 150k cells/query. Chunked by region (50 per batch). Exponential backoff on 429 and connection errors. | Parquet in `data/raw/`, 24h TTL. |
| `kolada_client.py` | Kolada v3 (`api.kolada.se/v3/`) | No documented limit. Paginated (5000 records/page, follows `next_url`). | Parquet in `data/raw/`, 24h TTL. |
| `riksbanken_client.py` | Riksbanken Swea v1 (`api.riksbank.se/swea/v1/`) | Single request for full series. | Parquet in `data/raw/`, 24h TTL. |

### Raw data inventory

| File | Source | Rows | Key columns | Geographic scope | Time range |
|------|--------|------|-------------|-----------------|------------|
| `HE0110_income.parquet` | SCB | 4,368 | `Region_code`, `Tid_code`, `value` (median income tkr) | 312 regions (290 muni + 21 county + 1 national) | 2011–2024 |
| `BO0501_price_index.parquet` | SCB | 756 | `Lan_code`, `Tid_code`, `value` (index 1990=100) | 21 counties + national. Note: combined code `08+09` for Kalmar+Gotland split into separate rows. | 1990–2025 |
| `BO0501_kt_ratio.parquet` | SCB | 17,424 | `Region_code`, `Tid_code`, `value` (K/T ratio), `frequency` | Annual: 312 regions. Quarterly: 33 regions (county+riksområde). | 1981–2024 (annual), 1998K1–2025K4 (quarterly) |
| `kolada_unemployment.parquet` | Kolada | 4,680 | `municipality_code`, `year`, `unemployment_rate` (%) | 312 codes (290 muni + 21 county + 1 national, all 4-digit in Kolada) | 2010–2024 |
| `BE0101_population.parquet` | SCB | 142,272 | `Region_code`, `Civilstand_code`, `Kon_code`, `Tid_code`, `value` | 312 regions × 4 civil statuses × 2 genders | 1968–2024 |
| `BO0101_construction.parquet` | SCB | 31,200 | `Region_code`, `Hustyp_code`, `Tid_code`, `value` | 312 regions × 2 house types (småhus, flerbostadshus) | 1975–2024 |
| `PR0101_cpi.parquet` | SCB | 1,108 | `ContentsCode_code`, `Tid_code`, `value` | National only. Two series: `00000807` (skuggindex, 2020=100), `00000804` (YoY %). | 1980M01–2026M02 |
| `policy_rate.parquet` | Riksbanken | 3,082 | `date`, `rate` (%) | National (daily) | 2014-01-02–2026-04-13 |

### Transformation layer (`src/data/build_panel.py`)

Each raw table is cleaned, filtered, and aggregated before merging:

| Variable | Raw → Clean transformation | Aggregation |
|----------|---------------------------|-------------|
| **Income** | Filter to `ContentsCode=000006SY` (median, tkr). Multiply by 1000 → SEK. | None (already per region × year). Forward-fill 2025–2026 with `is_imputed_income=True`. |
| **Price index** | Filter to `ContentsCode=BO0501R5`. Split combined county code `08+09` into separate `08` and `09` rows. | None (per county × year). |
| **K/T ratio** | Filter annual data to `Fastighetstyp=220` (permanentbostad) and `ContentsCode=BO0501C4`. | Municipal K/T used where available; fallback to county K/T. `has_native_kt` flag set. |
| **Unemployment** | From Kolada: filter to `gender=T` (total). | Already annual average (Arbetsförmedlingen computes this). Kolada county codes `00XX` mapped to SCB 2-digit `XX`. |
| **Population** | Filter to `Alder=tot`, `ContentsCode=BE0101N1`. | Sum across Civilstånd (4 categories) and Kön (2 genders) → total per region × year. |
| **Construction** | Filter to `ContentsCode=BO0101A5` (completions in new buildings). | Sum across Hustyp (småhus + flerbostadshus) → total per region × year. |
| **CPI** | Split into skuggindex (`00000807`) and YoY (`00000804`). | Monthly → annual average. |
| **Policy rate** | Parse date, extract year. | Daily → annual average. |

### Panel structure

**Decision: Annual frequency (Option A).** All panels use one row per geographic unit per year.

| Panel | File | Rows | Spine | Year range | Full data range |
|-------|------|------|-------|------------|-----------------|
| Municipal | `panel_municipal.parquet` | 4,640 | 290 municipalities × 16 years | 2011–2026 | **2014–2024** (100% complete for all formulas) |
| County | `panel_county.parquet` | 336 | 21 counties × 16 years | 2011–2026 | **2014–2024** (100% complete) |
| National | `panel_national.parquet` | 16 | 1 × 16 years | 2011–2026 | **2014–2024** (100% complete) |

### Panel columns (municipal)

| Column | Type | Description | Source | Null reason if any |
|--------|------|-------------|--------|-------------------|
| `region_code` | str | 4-digit municipality code (e.g., "0180" = Stockholm) | SCB | — |
| `region_name` | str | Municipality name in Swedish | SCB | — |
| `lan_code` | str | 2-digit county code (first 2 digits of region_code) | Derived | — |
| `year` | int | Calendar year | — | — |
| `median_income` | float | Median disposable household income in SEK | SCB HE0110 | — |
| `median_income_tkr` | float | Same in thousands of SEK | SCB HE0110 | — |
| `is_imputed_income` | bool | True for years where income is forward-filled | Derived | — |
| `price_index` | float | County fastighetsprisindex for permanenta småhus (1990=100) | SCB BO0501 | 2026: not yet published |
| `kt_ratio` | float | Köpeskillingskoefficient (K/T). Municipal if available, else county. | SCB BO0501 | 2025–2026: not yet published |
| `has_native_kt` | bool | True if this municipality has its own K/T data (not county fallback) | Derived | — |
| `unemployment_rate` | float | Openly unemployed 18–65 as % of population 18–65 | Kolada N03937 | 2025–2026: not yet published |
| `population` | float | Total population (sum of all gender × civil status) | SCB BE0101 | 2025–2026: not yet published |
| `completions` | float | Housing completions (sum of småhus + flerbostadshus) | SCB BO0101 | 2025–2026: not yet published |
| `cpi_index` | float | KPI skuggindex (2020=100), annual average | SCB PR0101 | — |
| `cpi_yoy_pct` | float | KPI year-on-year change (%), annual average | SCB PR0101 | — |
| `policy_rate` | float | Riksbanken repo rate (%), annual average of daily | Riksbanken | 2011–2013: series starts 2014 |

### Key design decisions

1. **F1 — County price for all municipalities:** Every municipality inherits its county's price index. Municipalities with their own K/T ratio data are flagged with `has_native_kt=True` (88% of panel rows have native K/T).

2. **F2 — National rate everywhere:** All municipalities share the same `policy_rate` in a given year. Municipal affordability variation comes entirely from income and county-level price differences.

3. **Income forward-fill:** 2025 and 2026 rows carry 2024 income values with `is_imputed_income=True`. This enables current-year analysis while marking the imputation clearly.

4. **Formula-ready window: 2014–2024.** All three formulas (A, B, C) have 100% non-null inputs for 290 municipalities × 11 years = 3,190 rows. Years 2011–2013 lack policy rate; 2025–2026 lack several variables.

## 3. Formulas

### Version A: Bank style affordability ratio

```
Affordability_A(i, t) = Income(i, t) / (Price(i, t) × Rate(t))
```

**Use case:** Quick monthly cost ratio, mirrors traditional bank affordability calculators.
**Strength:** Intuitive, easy to explain to non technical stakeholders.
**Weakness:** Ignores inflation (nominal rate distortion), ignores down payment.
**Data note:** Price(i,t) = county price index assigned to all municipalities in that county (F1). Rate(t) = national annual average policy rate (F2).

### Version B: Macro composite pressure index

```
Risk_B(i, t) = 0.35 × z(P/I) + 0.25 × z(R) + 0.20 × z(U) + 0.20 × z(π)
```

Where z() denotes z score normalization across the panel.

**Use case:** Multi factor pressure monitoring, mirrors central bank macroprudential dashboards.
**Strength:** Captures multiple risk channels simultaneously.
**Weakness:** Weights are subjective, z scores require stable reference period.
**Data note:** With Kolada N03937, unemployment is now available from 2010 onward. Version B can be computed for all panel years where policy rate exists (2014–2024).

### Version C: Real affordability (primary, recommended)

```
Affordability_C(i, t) = Income(i, t) / (Price(i, t) × max(R(t) − π(t), 0.005))
```

The max() floor prevents division explosion when real rates are near zero or negative.

**Use case:** Academically defensible, captures real cost of capital.
**Strength:** Inflation adjusted, standard in economics literature.
**Weakness:** Real rate can be near zero or negative, requires floor handling.
**Data note:** π(t) = annual average CPI YoY % from PR0101 skuggindex.

## 4. Index normalization and ranking

For comparison across formulas, each index is z score normalized within its own distribution. Higher z score equals worse affordability for Version B (it is a risk index), better affordability for Versions A and C (they are capacity indices). The Riksöversikt page inverts A and C so all three display "higher equals worse" for visual consistency, with explicit labeling.

**Ranking scope:** 290 municipalities for municipal panel; 21 counties for county panel. Rankings computed on latest complete year (2024).

## 5. Forecasting approach

### Prophet (default in UI)

- Library: `prophet` (Meta)
- Decomposes into trend + seasonality + holidays
- Suitable for: user friendly visualization, non technical audiences
- **Limitation flag in UI:** "Prophet is optimized for daily business series. For annual macro data, see ARIMA tab."

### ARIMA (recommended for inference)

- Library: `statsmodels.tsa.arima.model`
- Order selection via auto_arima from `pmdarima`
- Suitable for: methodologically rigorous forecasting
- **Limitation flag in UI:** "Confidence intervals widen rapidly beyond 2–3 years. Interpret accordingly."

### Forecast targets

Forecast each component separately (income, price index, rate), then compose the affordability index. Direct affordability forecasting introduces stationarity issues.

**Note on data frequency for forecasting:** Income and price index are annual series. Forecasting models will operate at annual frequency. The original "8 quarter horizon" translates to approximately 2 annual forecast steps. Consider extending to 4–8 annual steps for a meaningful forecast horizon.

### Horizon

Capped at 8 steps (annual). Beyond this, confidence intervals exceed useful interpretation.

## 6. Kontantinsats regime engine

Four regulatory regimes modeled:

| Regime | Period | Down payment | Amortization rule |
|--------|--------|--------------|-------------------|
| Pre 2010 | Until Oct 2010 | No formal min | None mandatory |
| Bolånetak | Oct 2010 to Jun 2016 | 15% min | None mandatory |
| Amortization 1.0 | Jun 2016 to Mar 2018 | 15% min | 2% if LTV>70%, 1% if LTV>50% |
| Amortization 2.0 | Mar 2018 to present | 15% min | Above + 1% extra if LTI>4.5x |

For each regime applied to today's median price and median income:
- Required cash (kontantinsats absolute amount)
- Years of saving needed at 10% savings rate
- Effective monthly cost (interest + amortization)
- Disposable income remaining after housing

## 7. Scenario simulator

Three sliders:

| Slider | Range | Step | Default |
|--------|-------|------|---------|
| Interest rate shock | -2% to +5% | 0.25% | 0% |
| Income growth shock | -10% to +10% | 1% | 0% |
| Price shock | -25% to +25% | 5% | 0% |

Output: recalculated Version C affordability for selected county, with delta from baseline highlighted.

## 8. Structural limitations (F1 to F8)

| ID | Limitation | Mitigation |
|----|------------|------------|
| F1 | Municipal price coverage gap — county annual index used for all 290 municipalities | Use county price index for all; badge native K/T ratio where available |
| F2 | National interest rate applied at municipal and county level | Document explicitly; municipal variation in affordability comes entirely from income differences |
| F3 | Three formulas rank municipalities differently | "Why these differ" panel with cross-formula comparison table |
| F4 | Prophet weak for annual macro data (designed for daily series) | ARIMA tab labelled "rekommenderad"; Prophet labelled "standard" |
| F5 | Kontantinsats is step function not continuous | Discrete regime cards, not a slider |
| F6 | Long horizon forecasts mislead — annual data means fewer data points | Hard cap at 8 annual steps; caveat callout in UI |
| F7 | SCB API rate limits (30 calls/10 s, 150k cells/query) | All data cached as parquet at build time; no live API calls from Streamlit |
| F8 | Translation loses banking terminology nuance | Glossary file in swedish-translation skill; banking terms curated |

> **F9 eliminated:** The original AM0210 source only had unemployment from 2020, which would have made Version B invalid pre-2020. Switching to Kolada N03937 (coverage 2010–2024) removed this limitation entirely.

## 9. Data validation checks

Before publishing each computation:

1. Median income should be monotonically increasing nominally across years (2011–2024)
2. Real income (deflated by CPI YoY) should be roughly stable or slowly rising
3. Stockholm county should rank in top 5 worst affordability under Version C
4. Norrbotten county should rank in top 5 best affordability under Version A
5. K/T values should be between 1.0 and 4.0 for all included municipalities
6. Forecast intervals should widen monotonically

If any check fails, halt and investigate before proceeding.

## 10. References

- SCB BO0501 product page: https://www.scb.se/bo0501-en
- SCB HE0110 product page: https://www.scb.se/he0110-en
- SCB BE0101 product page: https://www.scb.se/be0101
- SCB PR0101 product page: https://www.scb.se/pr0101
- SCB BO0101 product page: https://www.scb.se/bo0101
- SCB PxWebApi v1 documentation: https://www.scb.se/api/ *(v2beta endpoints not yet functional)*
- Kolada API v3: https://api.kolada.se/v3/ *(unemployment KPI N03937)*
- Kolada documentation: https://www.kolada.se/
- Riksbanken Swea API: https://www.riksbank.se/en-gb/statistics/interest-rates-and-exchange-rates/
- Finansinspektionen amortization rules: https://www.fi.se/en/our-registers/the-amortisation-requirement/
