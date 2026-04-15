# SHAI Prompts File
## Copy ready prompts per task

**Tooling key:** [CC] = paste into Claude Code terminal, [CR] = paste into Cursor chat
**Always paste the [CONTEXT] block first, then the [TASK] block.**

---

## Universal context block (paste at start of every Claude Code or Cursor session)

```
[PROJECT CONTEXT]
You are working on SHAI (Swedish Housing Affordability Indicator), a 6 day Streamlit portfolio dashboard.

Reference documents in /docs/:
- PRD.md (product requirements)
- METHODOLOGY.md (theoretical framework, formulas, limitations)
- DESIGN_SYSTEM.md (visual tokens from KRI mockup)
- PLAYBOOK.md (full task list)

Key constraints:
- Swedish UI from day 4 onward, no English leakage
- All data cached as parquet, no live API calls from Streamlit
- Design must match KRI mockup at /docs/kri_dashboard_mockup.html
- Use Source Sans Pro and IBM Plex Mono fonts
- Color palette: navy #0B1F3F, accent gold #C4A35A
- 290 municipalities, 21 counties, national layer
- 8 documented limitations (F1 to F8) must be visible on Metodologi page

Always read METHODOLOGY.md before implementing any formula.
Always read DESIGN_SYSTEM.md before implementing any UI component.
```

---

## Day 1 prompts

### Task 1.1 [CC] Project scaffold

```
[TASK 1.1] Project scaffold

Create a Python 3.11 project structure:

- pyproject.toml with dependencies: streamlit, pandas, numpy, requests, prophet, pmdarima, statsmodels, plotly, pyarrow, pytest (do not add streamlit-echarts unless you standardize on ECharts)
- src/ with subdirs: data, indices, forecast, kontantinsats, scenario, ui
- data/ with subdirs: raw, processed, cache
- pages/ (Streamlit multi page)
- tests/
- .gitignore (Python standard plus data/raw/ and data/cache/)
- .streamlit/config.toml (wide layout, custom theme matching DESIGN_SYSTEM.md primary navy)
- README.md placeholder

Verify pip install -e . succeeds.
```

### Task 1.2 [CC] SCB extraction module

```
[TASK 1.2] SCB extraction module  [COMPLETED — SEE DEVIATIONS.md]

Implemented: src/data/scb_client.py using SCB PxWebApi v1 (v2beta returned 404).
Also: src/data/kolada_client.py for unemployment (Kolada N03937 replaces AM0101).

Base URL (actual): https://api.scb.se/OV0104/v1/doris/sv/ssd/

Functions implemented (6 in scb_client.py + 1 in kolada_client.py):
- fetch_income() -> HE0110 disposable income, municipal level, annual, 2011-2024
- fetch_price_index() -> BO0501 real estate price index, county level, ANNUAL (not quarterly), 1990-2025
- fetch_kt_ratio() -> BO0501 K/T ratio, municipal+county, annual+quarterly
- fetch_population() -> BE0101 population, municipal, annual
- fetch_construction() -> BO0101 completions, municipal, annual
- fetch_cpi() -> PR0101 CPI (skuggindex 00000807 + YoY 00000804), national, monthly
- fetch_unemployment() [kolada_client.py] -> Kolada N03937 (Arbetsförmedlingen), municipal, annual, 2010-2024

Each function: chunked, rate-limited, cached to data/raw/*.parquet.
```

### Task 1.3 [CC] Riksbanken extraction

```
[TASK 1.3] Riksbanken extraction module

Implement src/data/riksbanken_client.py using Swea v1 REST API.

Base URL: https://api.riksbank.se/swea/v1/

Function:
- fetch_policy_rate() -> SECBREPOEFF series, daily, from 2014-01-01 to today
  Endpoint: /Observations/{seriesId}/{from}/{to}
  Cache to data/raw/policy_rate.parquet
  Returns DataFrame with columns: date, rate

Add resampling helpers:
- to_quarterly(df) -> quarterly mean
- to_monthly(df) -> monthly mean
- to_annual(df) -> annual mean
```

### Task 1.4 [CC] Panel construction

```
[TASK 1.4] Panel construction

Implement src/data/build_panel.py.

Read all parquet files from data/raw/. Produce three panels:
- panel_municipal.parquet: row per (kommun_kod, year, quarter) with all variables
- panel_county.parquet: row per (lan_kod, year, quarter)
- panel_national.parquet: row per (year, quarter)

Handle the 12 to 18 month income lag:
- Forward fill latest known income year for current quarters
- Add boolean column is_imputed_income flag
- Never silently drop NaN rows, log them

For municipal price data: use county price index for ALL municipalities (F1 mitigation per METHODOLOGY.md). Add column has_native_kt boolean for the ~39 large municipalities where actual K/T exists.

For interest rate at municipal level: use national rate (F2 mitigation), document this in column comments.

Validation outputs at end:
- Print row counts per panel
- Print column null percentages
- Print year coverage range

Save panels to data/processed/.
```

---

## Day 2 prompts

### Task 2.1 [CC] Real interest rate

```
[TASK 2.1] Real interest rate computation

Implement src/indices/real_rate.py.

Function compute_real_rate(panel_national: pd.DataFrame) -> pd.DataFrame
- real_rate = nominal_policy_rate - cpi_yoy_pct
- Apply floor: max(real_rate, 0.005) to prevent Version C explosion
- Add column is_floored boolean
- Return annual series (panel is annual, not quarterly — see DEVIATIONS.md D2/D8)

Add unit tests in tests/test_real_rate.py:
- 2022 should have negative real rate (inflation > policy rate)
- 2024 should have positive real rate
- Floor activates correctly when applied
```

### Task 2.2 [CC] Affordability formulas

```
[TASK 2.2] Affordability formulas

Read METHODOLOGY.md section 3 carefully.

Implement src/indices/affordability.py with three functions:

compute_version_a(panel) -> Series
  Income / (Price * Rate)

compute_version_b(panel) -> Series
  0.35*z(P/I) + 0.25*z(R) + 0.20*z(U) + 0.20*z(pi)
  z scores computed across the full panel
  NOTE: Unemployment (U) now comes from Kolada N03937, available 2010-2024.
  Version B is valid for all years where policy_rate exists (2014-2024).

compute_version_c(panel) -> Series
  Income / (Price * max(R - pi, 0.005))

compute_all(panel) -> DataFrame with columns version_a, version_b, version_c

Run on municipal panel. Panel is annual (one row per municipality per year,
not quarterly — see DEVIATIONS.md D2/D8). Output has columns for every
(municipality, year) row.

Save result to data/processed/affordability_municipal.parquet.

Validate:
- Stockholm county should appear in top 5 worst under Version C
- Norrbotten county should appear in top 5 best under Version A
- All 3 columns populated for years where all inputs exist (2014-2024)
- Print these rankings to console for sanity check
```

### Task 2.3 [CC] Z score normalization and ranking

```
[TASK 2.3] Normalization and ranking

Implement src/indices/normalize.py.

For each formula version:
- Compute z score within latest complete year (2024)
- Compute rank 1 to 290 (1 = best affordability)
- For Versions A and C: invert sign so higher z = worse affordability (matches Version B convention)
- Add risk_class column: "lag" (z < -0.67), "medel" (-0.67 to 0.67), "hog" (z > 0.67)
- Rankings are annual (not quarterly — see DEVIATIONS.md D2/D8)

Output: data/processed/affordability_ranked.parquet
```

### Task 2.4 [CC] Validation suite

```
[TASK 2.4] Validation tests

Implement tests/test_validation.py covering METHODOLOGY.md section 9:

1. test_income_monotonic_nominal: median income increases year over year nominally
2. test_real_income_stable: real income roughly stable
3. test_stockholm_worst_v_c: Stockholm in top 5 worst under Version C
4. test_norrbotten_best_v_a: Norrbotten in top 5 best under Version A
5. test_kt_range: all K/T values between 1.0 and 4.0
6. test_forecast_intervals_widen: confidence bands widen with horizon (run after Day 3)

Each test uses pytest. Halt the build if any fail.
```

---

## Day 3 prompts

### Task 3.1 [CC] Prophet forecasting

```
[TASK 3.1] Prophet forecasting pipeline

Implement src/forecast/prophet_pipeline.py.

NOTE: All input data is annual (see DEVIATIONS.md D2/D8). Forecasts operate
at annual frequency.

For each county, forecast 3 series separately:
- Income (annual)
- Price index (annual, county level)
- Policy rate (national, same for all counties)

Use prophet defaults except:
- yearly_seasonality=False (annual data, no sub-annual seasonality)
- weekly_seasonality=False
- daily_seasonality=False
- interval_width=0.80

Horizon: 8 annual steps (years).

Compose forecasts into Version C affordability per METHODOLOGY.md section 3.

Output: data/processed/forecast_prophet.parquet with columns:
county_kod, target_year, variable, mean, lower_80, upper_80

Also output a composed affordability forecast: same schema but variable="affordability_c".

Acceptance: 21 counties × 8 years × 3 variables = 504 forecast rows
```

### Task 3.2 [CC] ARIMA forecasting

```
[TASK 3.2] ARIMA forecasting pipeline

Implement src/forecast/arima_pipeline.py.

Same I/O schema as Prophet (annual frequency).

Use pmdarima.auto_arima for order selection per series:
- seasonal=False (annual data, no quarterly seasonality)
- stepwise=True for speed
- suppress_warnings=True

Horizon: 8 annual steps (matching Prophet).

Capture AIC and selected order in a separate metadata table data/processed/arima_metadata.parquet.

Output: data/processed/forecast_arima.parquet with same schema as Prophet output.

Validate: confidence intervals widen monotonically with horizon.
```

### Task 3.3 [CC] Kontantinsats engine

```
[TASK 3.3] Kontantinsats regime engine

Read METHODOLOGY.md section 6 carefully.

Implement src/kontantinsats/engine.py:

REGIMES = {
    "pre_2010": {"min_down_pct": 0.0, "amort_rules": []},
    "bolanetak": {"min_down_pct": 0.15, "amort_rules": []},
    "amort_1": {"min_down_pct": 0.15, "amort_rules": [
        {"ltv_threshold": 0.70, "amort_pct": 0.02},
        {"ltv_threshold": 0.50, "amort_pct": 0.01},
    ]},
    "amort_2": {"min_down_pct": 0.15, "amort_rules": [
        {"ltv_threshold": 0.70, "amort_pct": 0.02},
        {"ltv_threshold": 0.50, "amort_pct": 0.01},
        {"lti_threshold": 4.5, "amort_pct": 0.01},
    ]},
}

apply_regime(price, income, rate, regime_key, savings_rate=0.10) -> dict
Returns:
- required_cash (SEK)
- years_to_save (cash / (income * savings_rate))
- monthly_interest (annual)
- monthly_amort (annual)
- monthly_total
- residual_income (income - 12*monthly_total)

Validate: monthly_total ordering should be amort_2 >= amort_1 >= bolanetak >= pre_2010
(holding price, income, rate constant).
```

### Task 3.4 [CC] Scenario simulator

```
[TASK 3.4] Scenario simulator

Implement src/scenario/simulator.py.

simulate(county_kod, rate_shock, income_shock, price_shock,
         baseline_panel) -> dict
Returns:
- baseline_v_c
- scenario_v_c
- delta
- delta_pct

Pure function, no I/O. Used by Streamlit page later.

Test: simulate with all shocks = 0 should return delta = 0 exactly.
```

---

## Day 4 prompts

### Task 4.1 [CR] Streamlit app skeleton

```
[TASK 4.1] Streamlit app skeleton in Swedish

Read DESIGN_SYSTEM.md and the KRI mockup HTML carefully.

Create:
- app.py (entry point with st.set_page_config and global CSS)
- src/ui/css.py (returns CSS string with all design tokens)
- src/ui/components.py with functions:
    - kpi_card(label, value, unit, delta, variant) -> html
    - risk_pill(level) -> html
    - card_header(title, subtitle, tag) -> html
    - page_title(eyebrow, title, subtitle) -> html
- pages/01_Riksoversikt.py through pages/06_Metodologi.py (placeholders for now)

All UI strings in Swedish. Use the swedish-translation skill at /skills/swedish-translation/.

Page titles in Swedish:
1. Riksöversikt
2. Län jämförelse
3. Kommun djupanalys
4. Kontantinsats analys
5. Scenariosimulator
6. Metodologi och källor

Verify the app runs and visually matches KRI mockup.
```

### Task 4.2 [CR] Sidebar

```
[TASK 4.2] Sidebar matching KRI mockup

Implement src/ui/sidebar.py.

Reference: KRI mockup HTML, .sidebar section.

Components:
- Brand block: gold accent bar, "SHAI Dashboard" eyebrow, "Bostadsekonomisk hållbarhet" title, "Sverige · 2014 till 2025" subtitle
- Navigation: 6 page links with numbered prefix (01 to 06)
- Year selector: chips for 2020 to 2025, current year active
- Risk filter: 3 dots with labels "Låg risk", "Medel risk", "Hög risk"
- Footer: "KÄLLA: SCB, Riksbanken" and last update date

Use Streamlit st.sidebar with custom HTML. Match dark navy background from mockup.
```

### Task 4.3 [CR] Choropleth component

```
[TASK 4.3] Choropleth map component

Implement src/ui/choropleth.py.

Use Plotly `go.Scattergeo` (see DESIGN_SYSTEM.md section 5 and `src/ui/choropleth.py`). Implement scatter-on-map: one trace per risk class, Swedish tooltips.

Function signature:
render_choropleth(data: pd.DataFrame, value_col: str, name_col: str,
                  lat_col: str, lon_col: str, height: int = 440)

Data should have one row per municipality with lat lon coordinates.

Color by risk class (lag/medel/hog); size markers by absolute z-score as in the implementation.

Tooltips in Swedish:
- Show: kommun name, SHAI poäng, riskklass

Test with mock data covering all 290 municipalities. Verify rendering performance under 1 second.
```

### Task 4.4 [CR] Riksöversikt page

```
[TASK 4.4] Riksöversikt page in Swedish

Implement pages/01_Riksoversikt.py to match KRI mockup exactly.

Read data from data/processed/affordability_ranked.parquet.

Layout:
- Page title block: eyebrow "Sida 01 · Nationell översikt", title "Riksöversikt", subtitle "Strukturell bostadsekonomisk hållbarhet i Sveriges 290 kommuner"
- Year display top right (current year)
- KPI row (4 cards):
    1. "Genomsnittligt SHAI" (value, std unit, delta vs prior year)
    2. "Högrisk kommuner" (count out of 290, delta) - danger variant
    3. "Medianpris per kvm" (SEK, delta pct) - accent variant
    4. "Befolkningsförändring" (pct, delta) - success variant
- Chart row: choropleth (left) + distribution histogram (right)
- Table row: top 15 worst (left) + top 15 best (right)
- Footer: source attribution

All Swedish. Use components from src/ui/components.py.
```

---

## Day 5 prompts

### Task 5.1 [CR] Län jämförelse

```
[TASK 5.1] Län jämförelse page

Implement pages/02_Lan_jamforelse.py.

Three tabs: "Bankversion (A)", "Makroversion (B)", "Realversion (C)"

Each tab contains:
- Description card explaining the formula in Swedish (read METHODOLOGY.md section 3)
- Line chart: county trend over time using Plotly
- Ranking table: 21 counties sorted by current SHAI value
- Bottom of page: "Varför skiljer sig versionerna åt?" panel comparing rankings across all 3 formulas for top 5 and bottom 5 counties

Use design tokens. Swedish throughout.
```

### Task 5.2 [CR] Kommun djupanalys

```
[TASK 5.2] Kommun djupanalys page

Implement pages/03_Kommun_djupanalys.py.

Top: st.selectbox for kommun selection (290 options sorted alphabetically).

Two tabs: "Prophet (standard)" and "ARIMA (rekommenderad)"

Each tab shows:
- Historical SHAI line + forecast extension with confidence band (use Plotly fill_between equivalent)
- 8 quarter horizon
- Caveat callout box in Swedish explaining model limitations

Below tabs:
- Component breakdown: 3 mini charts showing income, price, rate forecasts side by side
- Risk decomposition: which factor drives this kommun's SHAI score most

Read forecasts from data/processed/forecast_prophet.parquet and forecast_arima.parquet.
```

### Task 5.3 [CR] Kontantinsats

```
[TASK 5.3] Kontantinsats analys page

Implement pages/04_Kontantinsats.py.

Top: kommun selector + savings rate slider (5% to 25%).

Four cards side by side, one per regime:
- Pre 2010
- Bolånetak (2010-2016)
- Amorteringskrav 1.0 (2016-2018)
- Amorteringskrav 2.0 (2018-nu)

Each card shows:
- Required cash (SEK, formatted with space thousand separator)
- Years to save
- Monthly cost
- Residual income
- Visual indicator for most/least affordable

Bottom: comparison bar chart showing monthly cost across all 4 regimes.

Use src/kontantinsats/engine.py.
```

### Task 5.4 [CR] Scenariosimulator

```
[TASK 5.4] Scenariosimulator page

Implement pages/05_Scenario.py.

Layout:
- County selector (21 options)
- Three sliders:
    - Räntechock: -2% to +5%, step 0.25%
    - Inkomsttillväxt: -10% to +10%, step 1%
    - Prischock: -25% to +25%, step 5%
- Results panel:
    - Baseline vs scenario SHAI as side by side bars
    - Delta highlighted (green if better, red if worse)
    - Comparison table showing baseline and scenario values for income, price, rate
- "Förklaring" expander with methodology callback

Use src/scenario/simulator.py. Recompute on slider change.
```

### Task 5.5 [CR] Metodologi

```
[TASK 5.5] Metodologi och källor page

Implement pages/06_Metodologi.py.

Render METHODOLOGY.md content as a Streamlit page in Swedish. Sections:

1. Teoretisk grund
2. Variabler och datakällor (table)
3. Formler (with LaTeX rendering via st.latex)
4. Prognoser (Prophet vs ARIMA)
5. Kontantinsats regim historia (timeline visual)
6. Begränsningar (8 documented limitations F1 to F8)
7. Datavalidering
8. Referenser (with external links)

Use st.expander for each section. All Swedish. Use the swedish-translation skill glossary for banking terms.
```

---

## Day 6 prompts

### Task 6.1 [CR] Swedish translation pass

```
[TASK 6.1] Swedish translation audit

Use the swedish-translation skill at /skills/swedish-translation/.

Walk through every page (01 to 06) and check:
1. No English strings leaked
2. Banking terminology matches glossary.md
3. Long Swedish words do not break layouts (test with longest terms)
4. Date and number formatting matches Swedish locale (space thousand separator, comma decimal)
5. All chart labels, tooltips, and axis titles in Swedish

Produce a translation_audit.md log with any fixes applied.
```

### Task 6.2 [CR] Loading and error states

```
[TASK 6.2] Loading and error states

For every page, add:
- st.spinner("Laddar data...") around data loads
- try/except around computations with Swedish error messages from DESIGN_SYSTEM.md section 8
- Empty state cards when filters return no data

Test by deliberately corrupting a parquet file and verifying graceful degradation.
```

### Task 6.3 [CR] Deployment

```
[TASK 6.3] Streamlit Community Cloud deployment

1. Push repo to GitHub (public)
2. Connect to streamlit.io
3. Configure: Python 3.11, requirements from pyproject.toml
4. Deploy
5. Test all 6 pages on the live URL
6. Measure load time, target under 5 seconds for first paint

If deployment fails, common fixes:
- Pin prophet version (>=1.1.5)
- Add packages.txt for system deps if needed
- Reduce parquet file sizes if memory limit hit
```

### Task 6.4 [CR] README

```
[TASK 6.4] Portfolio README

Write README.md in repo root. Sections:

1. Hero: project name, one line description, screenshot of Riksöversikt
2. Live demo: URL link
3. What this shows: bullet list of competencies (credit risk, forecasting, macro literacy, etc)
4. Methodology summary: 3 paragraphs linking to METHODOLOGY.md
5. Tech stack
6. Local development: clone, install, run
7. Data sources with attribution
8. Limitations: link to F1 to F8 list
9. License

Include 3 screenshots: Riksöversikt, Län jämförelse, Scenariosimulator.

A recruiter should understand the project value in 60 seconds.
```