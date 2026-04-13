# SHAI Task Execution Playbook
## 6 Day Build Plan

**Companion to:** PRD.md, METHODOLOGY.md, DESIGN_SYSTEM.md, PROMPTS.md
**Tooling key:** [CC] = Claude Code, [CR] = Cursor Pro+

---

## Day 1 — Data pipeline foundation [CC]

### Task 1.1 [CC] Project scaffold
**Context:** New repo. Python 3.11. Streamlit + lifelines style structure from survival project.
**Deliverable:** `pyproject.toml`, `src/`, `data/{raw,processed,cache}/`, `pages/`, `tests/`, `.gitignore`
**Acceptance:** `pip install -e .` works, all dirs exist, `.streamlit/config.toml` configured

### Task 1.2 [CC] SCB extraction module
**Context:** PxWebApi 2 released October 2025. Limit: 30 calls per 10 sec, 150,000 cells per query. Use chunked pulls, retry with exponential backoff. Cache to parquet.
**Deliverable:** `src/data/scb_client.py` with functions: `fetch_income()`, `fetch_price_index()`, `fetch_kt_ratio()`, `fetch_unemployment()`, `fetch_population()`, `fetch_construction()`, `fetch_cpi()`. Each writes to `data/raw/{table_id}.parquet`.
**Acceptance:** All 7 functions execute, parquet files created, no rate limit errors

### Task 1.3 [CC] Riksbanken extraction module
**Context:** Swea v1 REST API at `https://api.riksbank.se/swea/v1/`. Pull policy rate (SECBREPOEFF) daily series since 2014.
**Deliverable:** `src/data/riksbanken_client.py` with `fetch_policy_rate()`, writes `data/raw/policy_rate.parquet`
**Acceptance:** Daily series from 2014 to today, no gaps

### Task 1.4 [CC] Panel construction
**Context:** Merge all 7 SCB tables + Riksbanken into a single municipality x year panel. Handle the 12 to 18 month income lag by forward filling latest year for current quarter analysis with explicit `is_imputed` flag.
**Deliverable:** `src/data/build_panel.py` produces `data/processed/panel_municipal.parquet`, `panel_county.parquet`, `panel_national.parquet`
**Acceptance:** All 290 municipalities present, all 21 counties, national series complete, no silent NaN drops

---

## Day 2 — Index computation [CC]

### Task 2.1 [CC] Real interest rate computation
**Context:** Real rate = nominal − CPI YoY. Apply 0.5% floor to avoid division explosion in Version C.
**Deliverable:** `src/indices/real_rate.py`
**Acceptance:** Quarterly real rate series, no negative blowups, floor applied where needed

### Task 2.2 [CC] Affordability formulas
**Context:** Implement Versions A, B, C exactly as specified in METHODOLOGY.md section 3. Output dataframe with all three for every (municipality, quarter) row.
**Deliverable:** `src/indices/affordability.py` with `compute_version_a()`, `compute_version_b()`, `compute_version_c()`, plus a master `compute_all()` returning unified frame
**Acceptance:** All 3 columns populated, Stockholm in top 5 worst under Version C, Norrbotten in top 5 best under Version A

### Task 2.3 [CC] Z score normalization and ranking
**Context:** Each formula gets a z score column and a rank column. Version B is already a risk index. Versions A and C are inverted so all three display "higher equals worse" consistently.
**Deliverable:** `src/indices/normalize.py`
**Acceptance:** All municipalities ranked 1 to 290 under each formula

### Task 2.4 [CC] Validation suite
**Context:** Run the 6 checks from METHODOLOGY.md section 9. Fail loudly with helpful messages.
**Deliverable:** `tests/test_validation.py` runnable via `pytest`
**Acceptance:** All 6 checks pass on the built panel

---

## Day 3 — Forecasting and kontantinsats [CC]

### Task 3.1 [CC] Prophet forecasting pipeline
**Context:** Forecast income, price index, rate separately for each county. 8 quarter horizon. Compose into Version C affordability forecast.
**Deliverable:** `src/forecast/prophet_pipeline.py`. Outputs `data/processed/forecast_prophet.parquet` with columns: county, target_quarter, mean, lower_80, upper_80
**Acceptance:** 21 counties × 8 quarters × 3 variables = 504 forecast rows

### Task 3.2 [CC] ARIMA forecasting pipeline
**Context:** Use pmdarima auto_arima for order selection per series. Same output schema as Prophet.
**Deliverable:** `src/forecast/arima_pipeline.py`. Outputs `data/processed/forecast_arima.parquet`
**Acceptance:** Same row count as Prophet, confidence intervals widen monotonically with horizon

### Task 3.3 [CC] Kontantinsats regime engine
**Context:** Four regimes per METHODOLOGY.md section 6. For a given (municipality, regime), compute: required cash, years to save, monthly cost, residual income.
**Deliverable:** `src/kontantinsats/engine.py` with `apply_regime(municipality, regime, savings_rate=0.10)`
**Acceptance:** All 4 regimes produce different results for same input, monthly costs ordered correctly (Amort 2.0 > Amort 1.0 > Bolånetak > Pre 2010)

### Task 3.4 [CC] Scenario simulator engine
**Context:** Pure function: takes (county, rate_shock, income_shock, price_shock) returns recalculated Version C.
**Deliverable:** `src/scenario/simulator.py`
**Acceptance:** Baseline (0,0,0) matches stored Version C exactly

---

## Day 4 — Streamlit shell in Swedish [CR]

### Task 4.1 [CR] Streamlit app skeleton
**Context:** Use `st.navigation` or pages directory pattern. 6 pages per PRD section 9. Apply DESIGN_SYSTEM.md tokens via injected CSS. Swedish from this task forward, no English in UI.
**Deliverable:** `app.py`, `pages/01_Riksoversikt.py` through `pages/06_Metodologi.py`, `src/ui/css.py` (CSS injection), `src/ui/components.py` (KPI card, risk pill, card header components)
**Acceptance:** App runs, all 6 pages navigable, design matches KRI mockup visually

### Task 4.2 [CR] Sidebar with year selector and risk filter
**Context:** Match KRI mockup sidebar exactly: brand block, navigation, year chips, risk filter dots, footer with source attribution.
**Deliverable:** `src/ui/sidebar.py`
**Acceptance:** Visual diff against mockup is minimal

### Task 4.3 [CR] Choropleth component
**Context:** Use streamlit-echarts. Implement the scatter on geo pattern from DESIGN_SYSTEM.md section 5. Plot all 290 municipalities.
**Deliverable:** `src/ui/choropleth.py` with `render_choropleth(data: pd.DataFrame)` function
**Acceptance:** Map renders, hover tooltips work in Swedish, color scale matches mockup

### Task 4.4 [CR] Riksöversikt page
**Context:** Top section: 4 KPI cards (genomsnittligt SHAI, högrisk kommuner, medianskuld per capita, befolkningsförändring). Middle: choropleth + distribution histogram. Bottom: top 15 worst + top 15 best tables.
**Deliverable:** Fully functional `pages/01_Riksoversikt.py`
**Acceptance:** Matches KRI mockup layout, all data live from parquet, Swedish throughout

---

## Day 5 — Remaining pages [CR]

### Task 5.1 [CR] Län jämförelse page (3 formula tabs)
**Context:** Three tabs labeled "Bankversion", "Makroversion", "Realversion". Each shows: county ranking table, line chart of trend, "Why these differ" panel.
**Deliverable:** `pages/02_Lan_jamforelse.py`
**Acceptance:** All 3 tabs load, comparison panel visible

### Task 5.2 [CR] Kommun djupanalys page (forecast tabs)
**Context:** Municipality selector at top. Two tabs: "Prophet (standard)" and "ARIMA (rekommenderad)". Each shows forecast curve with confidence bands, 8 quarter horizon.
**Deliverable:** `pages/03_Kommun_djupanalys.py`
**Acceptance:** Both forecasts render, confidence bands widen with horizon

### Task 5.3 [CR] Kontantinsats analys page
**Context:** Four columns or four cards, one per regime. Each shows: required cash, years to save, monthly cost, residual income. Highlight most affordable regime.
**Deliverable:** `pages/04_Kontantinsats.py`
**Acceptance:** All 4 regimes side by side, visually clear which is most/least affordable

### Task 5.4 [CR] Scenariosimulator page
**Context:** Three sliders (rate shock, income shock, price shock). Real time recalculation. Show baseline vs scenario as side by side bar chart per county.
**Deliverable:** `pages/05_Scenario.py`
**Acceptance:** Sliders responsive, charts update in under 500ms

### Task 5.5 [CR] Metodologi page
**Context:** Render METHODOLOGY.md content as Streamlit page in Swedish. Include all 8 limitations, all formulas with LaTeX rendering.
**Deliverable:** `pages/06_Metodologi.py`
**Acceptance:** All 8 limitations visible, formulas render correctly

---

## Day 6 — Polish and deployment [CR]

### Task 6.1 [CR] Swedish translation pass with skill
**Context:** Use the swedish-translation skill to audit every UI string. Fix banking terminology with the glossary. Test for layout breaks (Swedish words longer than English).
**Deliverable:** All UI strings reviewed, no English leakage, no layout overflow
**Acceptance:** A native Swedish reader could navigate without confusion

### Task 6.2 [CR] Loading and error states
**Context:** Add skeleton loaders, Swedish error messages from DESIGN_SYSTEM.md section 8.
**Deliverable:** All pages handle loading and error gracefully
**Acceptance:** No raw exceptions visible to user

### Task 6.3 [CR] Streamlit Community Cloud deployment
**Context:** Push to GitHub, connect to Streamlit Community Cloud, configure secrets if needed (none should be needed since data is cached).
**Deliverable:** Public URL accessible
**Acceptance:** App loads under 5 seconds, all pages work

### Task 6.4 [CR] README and portfolio polish
**Context:** GitHub README with screenshots, methodology summary, link to live app, link to METHODOLOGY.md.
**Deliverable:** `README.md` in repo root
**Acceptance:** A recruiter can understand the project in 60 seconds from the README

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SCB API changes during build | Low | High | Cache early, work from cache |
| Prophet install fails on Streamlit Cloud | Medium | Medium | Pin version, test deployment day 5 |
| Swedish translation introduces UI breaks | High | Medium | Build Swedish from day 4, not day 6 |
| Forecasting takes too long to compute | Low | Medium | Pre compute and cache as parquet |
| Choropleth rendering slow with 290 points | Low | Low | ECharts handles this fine, tested in KRI |