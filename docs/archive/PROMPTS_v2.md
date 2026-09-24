# SHAI Prompts File (v2)
## Post Day 2 revision

**Version:** 2.0
**Supersedes:** PROMPTS.md v1
**Key changes:** K/T instead of price_index, annual instead of quarterly, 6 step forecast horizon, Kolada unemployment, imputation transparency

Tasks 1.1 to 2.4 already executed. Start from Task 3.1 for new runs.

---

## Universal context block (paste at start of every session)

```
[PROJECT CONTEXT]
You are working on SHAI (Swedish Housing Affordability Indicator), a 6 day Streamlit portfolio dashboard.

Reference documents in /docs/:
- PRD.md (product requirements)
- METHODOLOGY_v2.md (theoretical framework, formulas, limitations F1 to F10)
- DESIGN_SYSTEM.md (visual tokens from KRI mockup)
- PLAYBOOK_v2.md (full task list)
- DEVIATIONS.md (log of implementation vs plan divergences)

Key constraints:
- Swedish UI from Day 4 onward, no English leakage
- All data cached as parquet, no live API calls from Streamlit
- Design must match KRI mockup at /docs/kri_dashboard_mockup.html
- Use Source Sans Pro and IBM Plex Mono fonts
- Colors: navy #0B1F3F, accent gold #C4A35A, risk palette in DESIGN_SYSTEM.md
- 290 municipalities, 21 counties, national layer
- 10 documented limitations (F1 to F10) visible on Metodologi page
- Panel is ANNUAL frequency (2014 to 2024 = 11 observations)
- Price variable is KT_RATIO, not price_index
- Forecast horizon: 6 annual steps

Always read METHODOLOGY_v2.md before implementing any formula.
Always read DESIGN_SYSTEM.md before implementing any UI component.
Use the swedish-translation skill for all Swedish strings.
```

---

## Retroactive corrections to completed tasks

### Task 2.2 correction (apply before Task 3.1)

```
[TASK 2.2 CORRECTION] Replace price_index with kt_ratio in affordability formulas

Context: cross regional rankings with price_index produced the counterintuitive
result that Stockholm ranks most affordable. The cause is that price_index is a
growth measure (1990=100) not a level, so it is not comparable across regions.
K/T ratio is a level measure and is appropriate for cross sectional comparison.

Open src/indices/affordability.py.

Replace these three places:
1. compute_version_a: Income / (kt_ratio * policy_rate)
2. compute_version_b: z(kt_ratio / income) in the P/I term
3. compute_version_c: Income / (kt_ratio * max(rate - cpi_yoy_pct, 0.005))

Rerun the pipeline to regenerate data/processed/affordability_ranked.parquet.

Rerun tests/test_validation.py. Expected changes:
- Stockholm should now rank in top 5 WORST under Version C (was top 5 best with price_index)
- Skåne likely also worst half
- Norrbotten should remain top 5 best under Version A

If Stockholm does NOT move to worst half, stop and investigate the income
variable (check if median is household or individual, pre tax or post tax).
```

### Task 2.4 correction

```
[TASK 2.4 CORRECTION] Update validation tests

Edit tests/test_validation.py:

test_income_monotonic_nominal:
- Relax threshold from ≤2 to ≤3 nominal decreases
- Add assertion message explaining expected 2019, 2022, 2023 decreases

test_stockholm_worst_v_c:
- Assert Stockholm is in top 5 worst (not best)
- If this fails after the K/T fix, halt the build

Run pytest. All 6 checks must pass before starting Task 3.1.
```

---

## Day 3 prompts (revised)

### Task 3.1 [CC] Prophet forecasting (6 annual steps)

```
[TASK 3.1 REVISED] Prophet forecasting pipeline

Frequency: ANNUAL (not quarterly).
Horizon: 6 annual steps (2024 base → 2030).
Why: only 11 annual observations per series, longer horizons have no interpretive value.

Implement src/forecast/prophet_pipeline.py.

For each of the 21 counties, forecast 3 series separately:
- Median income (annual)
- K/T ratio (annual)
- Policy rate (national, same for all counties)

Prophet config:
- yearly_seasonality=False (annual data, no yearly seasonality)
- weekly_seasonality=False
- daily_seasonality=False
- interval_width=0.80
- freq='YE' (year end)

Horizon: 6 annual steps.

Compose forecasts into Version C affordability per METHODOLOGY_v2.md section 3.

Output: data/processed/forecast_prophet.parquet with columns:
- county_kod (str)
- target_year (int)
- variable (str: income, kt_ratio, rate, affordability_c)
- mean (float)
- lower_80 (float)
- upper_80 (float)

Also compute affordability_c by composing the three forecasts:
affordability_c = income / (kt_ratio * max(rate - cpi_yoy_pct, 0.005))

Total rows: 21 counties × 6 years × 4 variables = 504

Validate: confidence bands widen monotonically with horizon.
```

### Task 3.2 [CC] ARIMA forecasting (6 annual steps)

```
[TASK 3.2 REVISED] ARIMA forecasting pipeline

Frequency: ANNUAL.
Horizon: 6 annual steps.

Implement src/forecast/arima_pipeline.py.

Same I/O schema as Prophet. Output to data/processed/forecast_arima.parquet.

Use pmdarima.auto_arima for order selection per series:
- seasonal=False (annual data, no seasonal component)
- stepwise=True for speed
- suppress_warnings=True
- max_p=3, max_q=3, max_d=2

Capture order and AIC in data/processed/arima_metadata.parquet.

Critical caveat to log: with only 11 observations, auto_arima may select trivial
orders like (0,1,0) (random walk). This is acceptable and will be documented in
the UI. Print selected orders to console for transparency.

Validate: confidence intervals widen monotonically.
```

### Task 3.3 [CC] Kontantinsats engine (unchanged)

```
[TASK 3.3] Kontantinsats regime engine

Read METHODOLOGY_v2.md section 6 carefully.

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

apply_regime(price_sek, income_sek, rate, regime_key, savings_rate=0.10) -> dict
Returns:
- required_cash (SEK)
- years_to_save (cash / (income * savings_rate))
- monthly_interest_annual (SEK/year)
- monthly_amort_annual (SEK/year)
- monthly_total (SEK/year divided by 12)
- residual_income (income - annual housing cost)

Note: since the panel uses K/T not price in SEK, you need to convert K/T to a
SEK price level. Use: price_sek = kt_ratio * taxeringsvärde_proxy
where taxeringsvärde_proxy is ~75% of market value by convention. Document
this conversion in the function docstring.

Alternative: use median municipal transaction price from SCB BO0501B directly
if available. Check the parquet schema.

Validate: monthly_total ordering should be amort_2 >= amort_1 >= bolanetak >= pre_2010
holding price, income, rate constant.
```

### Task 3.4 [CC] Scenario simulator (Version C only)

```
[TASK 3.4 REVISED] Scenario simulator

Implement src/scenario/simulator.py.

Pure function:
simulate(county_kod, rate_shock, income_shock, price_shock,
         baseline_panel) -> dict

Computes Version C ONLY (per DEVIATIONS.md D12).

Returns:
- baseline_v_c
- scenario_v_c
- delta
- delta_pct
- scope_note: "Simulatorn beräknar endast Version C (realversion)"

Test: simulate with all shocks = 0 should return delta = 0 exactly.
```

---

## Day 4 prompts (revised where needed)

### Task 4.4 [CR] Riksöversikt (with imputation styling)

```
[TASK 4.4 REVISED] Riksöversikt page

Implement pages/01_Riksoversikt.py.

Same layout as v1 PROMPTS.md. Changes:

1. KPI card #3 label: "Medianpris (K/T ratio)" not "Medianpris per kvm"
   Value shows unweighted mean K/T across 290 municipalities for current year.
   This is more honest than a fake "price per kvm".

2. Year display: if current year is imputed (2025 or 2026), show a small
   "framskriven" badge next to the year number.

3. Choropleth tooltip in Swedish:
   - Kommun name
   - SHAI poäng (Version C)
   - Riskklass (Låg / Medel / Hög)
   - Ingår i Version C: Inkomst, K/T, Realränta
   - If has_native_kt=False: note "K/T data från län"

4. Distribution histogram:
   - x axis: SHAI poäng (z score)
   - y axis: Antal kommuner
   - Median line with label "Median"
   - Color bands: green (low), amber (medium), red (high) per DESIGN_SYSTEM

5. Top 15 tables: use the updated rankings from the K/T fix.
   Expected: Stockholm or Göteborg kommuner in worst list (not best).

6. Footer: include "Senast uppdaterad" with latest panel year, and a note
   if any variables are imputed.
```

### Other Day 4 tasks unchanged from v1 PROMPTS.md.

---

## Day 5 prompts (revised where needed)

### Task 5.1 [CR] Län jämförelse (annual x axis)

```
[TASK 5.1 REVISED] Län jämförelse page

Implement pages/02_Lan_jamforelse.py.

Three tabs: "Bankversion (A)", "Makroversion (B)", "Realversion (C)"

Each tab contains:
- Formula description card (use METHODOLOGY_v2 section 3 text)
- Line chart: 21 county trends 2014 to 2024, x axis is YEAR not quarter
- Ranking table sorted by latest year value
- Version B tab: add unemployment footnote
  "Arbetslöshet avser öppet arbetslösa enligt Arbetsförmedlingen (18 till 65 år),
   inte AKU."

Bottom of page: "Varför skiljer sig versionerna åt?" comparison panel.
Show top 5 and bottom 5 counties under each formula side by side.
Expected: Stockholm appears in worst under C and A, unclear under B.
```

### Task 5.2 [CR] Kommun djupanalys (annual, 6 step horizon)

```
[TASK 5.2 REVISED] Kommun djupanalys page

Implement pages/03_Kommun_djupanalys.py.

Top: kommun selectbox (290 options sorted alphabetically).

Two tabs: "Prophet (standard)" and "ARIMA (rekommenderad)"

Each tab shows:
- Historical SHAI line 2014 to 2024 + forecast 2025 to 2030 with confidence band
- x axis: YEAR (not quarter)
- 6 annual step horizon

Persistent caveat callout ABOVE the forecast chart:
"Prognoser baseras på 11 årliga observationer (2014 till 2024). Konfidensintervall
vidgas snabbt efter år 3. Tolka långtidsprognoser med försiktighet."

Below tabs:
- Component breakdown: 3 mini line charts for income, K/T, rate
- Annotate which component drives most of the SHAI variation for this kommun

Read forecasts from data/processed/forecast_prophet.parquet and forecast_arima.parquet.

Also indicate on chart if any year uses imputed income (lighter line segment or
hatch pattern).
```

### Task 5.3 [CR] Kontantinsats (unchanged)

See v1 PROMPTS.md Task 5.3.

### Task 5.4 [CR] Scenariosimulator (scope clarification)

```
[TASK 5.4 REVISED] Scenariosimulator page

Implement pages/05_Scenario.py.

Layout per v1 PROMPTS.md.

ADD a scope note card at the top:
"Scenariosimulatorn beräknar om Version C (realversion) för vald län.
 Versionerna A och B innehåller ytterligare variabler (arbetslöshet) som inte
 ingår i simulatorn för att hålla gränssnittet enkelt."

Use src/scenario/simulator.py exactly as implemented in Task 3.4.
```

### Task 5.5 [CR] Metodologi (10 limitations, K/T rationale)

```
[TASK 5.5 REVISED] Metodologi och källor page

Implement pages/06_Metodologi.py.

Render METHODOLOGY_v2.md content as a Streamlit page in Swedish. Sections:

1. Teoretisk grund
2. Variabler och datakällor (table including Kolada N03937 row)
3. Formler (with LaTeX via st.latex)
   Include the "Varför K/T, inte prisindex" subsection prominently.
4. Prognoser (Prophet vs ARIMA)
   Include the 11 observation caveat.
5. Kontantinsats regim historia (timeline visual for 2010, 2016, 2018)
6. Begränsningar (10 documented limitations F1 to F10)
   F1: 88% native K/T coverage. List fallback municipalities.
   F9: imputation disclosure
   F10: unemployment definition
7. Datavalidering (including the 3 nominal income decrease narrative)
8. Referenser with external links

Use st.expander for sections 4 through 8. Keep 1 through 3 always visible.
All Swedish.
```

---

## Day 6 prompts (revised)

### Task 6.1 [CR] Swedish translation audit

```
[TASK 6.1] Swedish translation audit

Use the swedish-translation skill at /skills/swedish-translation/.

Walk through every page (01 to 06) and check:
1. No English strings leaked
2. Banking terminology matches glossary.md
3. Long Swedish words do not break layouts
4. Swedish number formatting (space separator, comma decimal) applied via
   src/ui/formatting.py helpers
5. All chart labels, tooltips, axis titles in Swedish
6. Imputed year tooltip uses: "Värde framskrivet från 2024"
7. Unemployment footnote present on Version B tab and any page using U
8. K/T vs price index explainer present on Metodologi

Produce translation_audit.md log of any fixes applied.
```

### Tasks 6.2 to 6.4 unchanged from v1 PROMPTS.md.

---

## Summary of changes from v1 to v2

| Area | v1 | v2 |
|------|-----|-----|
| Frequency | Quarterly | Annual |
| Price variable | price_index | kt_ratio |
| Forecast horizon | 8 quarters | 6 annual steps |
| Unemployment source | SCB AM0101 | Kolada N03937 |
| Limitations count | 8 (F1 to F8) | 10 (F1 to F10, with F9 and F10 new) |
| Imputation | Not addressed | Explicit flag and UI styling |
| Unemployment definition | Not specified | Arbetsförmedlingen registered, footnoted |
| Stockholm validation | Top 5 worst under C (failed with price_index) | Top 5 worst under C (expected to pass with K/T) |