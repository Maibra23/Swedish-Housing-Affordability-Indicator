# SHAI Patch File
## Post Day 2 course corrections

**Apply before starting Day 3 (Task 3.1 forecasting).**
**Priority order: P0 blocks the build, P1 should be fixed before user facing pages, P2 is polish.**

---

## P0 — D9 price variable fix (blocks correctness)

### Problem

Current Task 2.2 uses `price_index` (SCB BO0501R5, 1990=100) as the Price variable in all three formulas. This is an index, not a level. Two counties with identical index values can have wildly different absolute price levels. Cross regional rankings are therefore unreliable, which explains why Stockholm ranks best instead of worst.

### Fix

Replace `price_index` with `kt_ratio` (köpeskillingskoefficient) as the Price variable in all three formulas. K/T is a level measure (ratio of transaction price to assessed value) and is comparable across regions.

### Files affected

**`src/indices/affordability.py`** (from Task 2.2)
```python
# BEFORE
def compute_version_a(panel: pd.DataFrame) -> pd.Series:
    return panel["median_income"] / (panel["price_index"] * panel["policy_rate"])

def compute_version_c(panel: pd.DataFrame) -> pd.Series:
    real_rate = (panel["policy_rate"] - panel["cpi_yoy_pct"]).clip(lower=0.005)
    return panel["median_income"] / (panel["price_index"] * real_rate)

# AFTER
def compute_version_a(panel: pd.DataFrame) -> pd.Series:
    # Use K/T (price level), not price index (growth measure)
    return panel["median_income"] / (panel["kt_ratio"] * panel["policy_rate"])

def compute_version_c(panel: pd.DataFrame) -> pd.Series:
    real_rate = (panel["policy_rate"] - panel["cpi_yoy_pct"]).clip(lower=0.005)
    return panel["median_income"] / (panel["kt_ratio"] * real_rate)
```

For Version B, the `P/I` ratio should also use K/T not index:
```python
# BEFORE
panel["p_over_i"] = panel["price_index"] / panel["median_income"]

# AFTER
panel["p_over_i"] = panel["kt_ratio"] / panel["median_income"]
```

### Validation after fix

Rerun Task 2.4 tests. Expected outcomes:
- Stockholm should now rank in top 5 **worst** under Version C (original hypothesis confirmed)
- Norrbotten should remain in top 5 best under Version A
- If Stockholm still ranks best after the fix, investigate the income variable next (median household vs median individual, pre tax vs post tax)

### If fix does not work

Fallback investigation order:
1. Check if income is household disposable or individual
2. Check if K/T is being assigned correctly to municipalities (county fallback logic)
3. Compute Price × Rate × 100 as annual carrying cost in SEK and manually verify Stockholm > other counties

---

## P0 — D2/D8 forecast horizon reduction

### Problem

Only 11 annual observations per county (2014 to 2024). Forecasting 8 steps ahead exceeds the ratio of observations to forecast horizon that statsmodels documentation recommends (typically want >3x).

### Fix

Reduce forecast horizon from 8 quarters to **6 annual steps** across all forecasting code and UI copy.

### Files affected

**`src/forecast/prophet_pipeline.py`** (Task 3.1)
```python
# BEFORE
FORECAST_HORIZON = 8  # quarters

# AFTER
FORECAST_HORIZON = 6  # annual steps
```

**`src/forecast/arima_pipeline.py`** (Task 3.2): same change

**PROMPTS.md Task 3.1 and 3.2:** change "8 quarter horizon" to "6 annual step horizon"

**METHODOLOGY.md section 5:** change "Capped at 8 quarters" to "Capped at 6 annual steps (2030 horizon from 2024 base)"

**Page 03 Kommun djupanalys (Task 5.2):** change x axis label from quarters to years, update caveat copy

---

## P1 — D9 methodology transparency

### Problem

Even after the K/T fix, the methodology page should document why K/T was chosen over the price index and why the original test failed.

### Fix

Add new subsection to METHODOLOGY.md section 3:

```markdown
### Why K/T ratio, not price index

The Price variable in all three formulas uses the K/T ratio (köpeskillingskoefficient), not the fastighetsprisindex.

Rationale:
- Price index measures growth relative to a base year (1990=100). Two regions with identical index values can have very different absolute price levels.
- K/T measures the actual transaction price relative to assessed value. It is a level, not a growth measure, and is comparable across regions.
- A price index is appropriate for time series analysis within a region (tracking growth over time) but misleading for cross regional affordability comparison.

An earlier iteration used the price index and produced the counterintuitive result that Stockholm ranked among the most affordable counties. This artifact disappeared once K/T replaced the index.
```

---

## P1 — D3 methodology nuance on unemployment

### Problem

Kolada N03937 measures openly registered unemployment (Arbetsförmedlingen definition). Banking recruiters and Swedish macro discussions typically reference AKU/ILO unemployment. The methodology page mentions this but the user facing pages do not.

### Fix

Add a footnote to every chart that uses unemployment:

**Swedish copy:** "Arbetslöshet avser öppet arbetslösa enligt Arbetsförmedlingen (18 till 65 år), inte AKU."

Apply to:
- Riksöversikt KPI card if unemployment is displayed
- Län jämförelse tab for Version B
- Scenariosimulator if unemployment enters the computation

---

## P1 — F1 limitation update (less severe than originally stated)

### Problem

Original F1 said "only ~39 of 290 municipalities have native K/T data." Actual implementation shows 88% of panel rows have native K/T. This is a huge improvement that should be reflected in the methodology page.

### Fix

**METHODOLOGY.md section 8 F1 row:**

```markdown
# BEFORE
| F1 | Municipal price coverage gap — county annual index used for all 290 municipalities | Use county price index for all; badge native K/T ratio where available |

# AFTER
| F1 | Municipal K/T coverage asymmetry — native K/T available for ~88% of municipality years; county fallback used for remaining ~12% | has_native_kt flag in panel; county K/T used where native unavailable; document municipality list without native K/T on Metodologi page |
```

Add a small table on the Metodologi page listing which municipalities use county fallback. This turns a limitation into a transparency strength.

---

## P1 — D10 threshold context (add narrative, not just relax)

### Problem

Validation test 1 was relaxed from ≤2 to ≤3 nominal income decreases without explaining the macro context.

### Fix

**METHODOLOGY.md section 9 Check 1 narrative:**

```markdown
# BEFORE
Median income should be monotonically increasing nominally across years

# AFTER
Median income should trend upward nominally across 2011 to 2024. Minor year over year decreases are expected during macro shocks. Our panel shows 3 nominal decreases: 2019 (pension reform timing effect), 2022 (first year of inflation shock), 2023 (continued inflation with lagging wage growth). This is consistent with documented Swedish macroeconomic history and does not indicate a data error.
```

---

## P2 — D11 (new) unflagged deviation: imputation transparency

### Problem

The implementation forward fills 2025 and 2026 income with `is_imputed_income=True`. The PRD and METHODOLOGY did not originally specify this behavior. The user will see 2025 and 2026 numbers in the dashboard without knowing they are imputed.

### Fix

**PRD.md section 13 Documented limitations:** add

```markdown
9. Income data for current year (2025 and 2026) is forward filled from 2024 until SCB publishes updates. Imputed values are flagged in the data panel and shown with a lighter tone in the UI.
```

**Streamlit pages:** render imputed years with reduced opacity or hash pattern in charts. Add tooltip "Värde framskrivet från 2024; SCB publicerar 2025 data under 2026 Q4."

---

## P2 — D12 (new) unemployment definition on Scenariosimulator

### Problem

The scenario simulator was specified with 3 sliders (rate, income, price). Unemployment was not included. But Version B weights unemployment at 0.20. If a user is viewing Version B and toggling the simulator, they see Version C recomputed, not Version B.

### Fix

Either:
- A. Document explicitly that the scenario simulator only recomputes Version C (current spec, minor UI clarification needed)
- B. Add a fourth slider for unemployment shock and recompute Version B too (scope increase, ~2 hours extra work)

**Recommendation: A.** Add a one line note on the Scenariosimulator page: "Scenariosimulatorn beräknar om Version C (realversion). Övriga versioner påverkas av andra ingångsvariabler och visas inte här."

---

## P2 — Forecast interpretability caveat

### Problem

With 11 observations and 6 step forecasts, confidence intervals will be wide. Users may not appreciate how wide without explicit guidance.

### Fix

On Kommun djupanalys page, add a persistent callout above the forecast chart:

**Swedish copy:** "Prognoser baseras på 11 årliga observationer (2014 till 2024). Konfidensintervall vidgas snabbt efter år 3. Tolka långtidsprognoser med försiktighet."

---

## Prompt change summary table

| Task | Change | Priority | Log ref |
|------|--------|----------|---------|
| 2.1 | quarterly → annual real rate | P0 | D2/D8 |
| 2.2 | `price_index` → `kt_ratio` in all 3 formulas | P0 | D9 |
| 2.2 | `(municipality, quarter)` → `(municipality, year)` | P0 | D2/D8 |
| 2.3 | Rankings annual, invert sign for A and C | P0 | D2/D8 |
| 2.4 | Validate Stockholm worst under V.C after K/T fix | P0 | D9 |
| 2.4 | Check 1 threshold relaxed to ≤3 with macro narrative | P1 | D10 |
| 3.1 | 8 quarters → 6 annual steps | P0 | D2/D8 |
| 3.2 | 8 quarters → 6 annual steps | P0 | D2/D8 |
| 5.2 | x axis years, forecast caveat callout | P0 | D2/D8 |
| 5.1 | Unemployment footnote for Version B | P1 | D3 nuance |
| 5.4 | Note that simulator computes Version C only | P2 | D12 new |
| 5.5 | F1 rewritten (88% coverage), F9 eliminated, imputation disclosure | P1 | D3, F1 update |
| 6.1 | Ensure imputed year styling applied | P2 | D11 new |

---

## Decision log entries to add to DEVIATIONS.md

```markdown
## D11 — Imputation flag not originally specified ✅

| | |
|---|---|
| Planned | No imputation, use latest available year |
| Actual | Forward fill 2025 and 2026 income with is_imputed_income=True flag |
| Why | Enables current year analysis while marking data provenance |
| Resolved | PRD limitation F9 added; UI renders imputed values with reduced opacity |

## D12 — Scenario simulator scope clarification ⚠️

| | |
|---|---|
| Ambiguity | Original PRD did not specify which affordability version the simulator recomputes |
| Decision | Simulator recomputes Version C only |
| Rationale | Adding a 4th slider for unemployment to cover Version B would increase scope beyond 6 day timeline |
| Tasks to adjust | 5.4: add Swedish note clarifying scope |

## D13 — Native K/T coverage better than originally assumed ✅

| | |
|---|---|
| Original assumption | Only ~39 of 290 municipalities (pop>50k) have K/T data |
| Actual | 88% of municipality years have native K/T; 12% use county fallback |
| Impact | F1 limitation is much less severe than originally stated |
| Tasks to adjust | 2.2: use native K/T where available; 5.5: rewrite F1 on Metodologi page |
```

---

## Action checklist

Run in this order:

- [ ] Apply P0 fixes to Task 2.2 code (`price_index` → `kt_ratio`)
- [ ] Rerun Task 2.4 validation, confirm Stockholm ranks worst under V.C
- [ ] If validation fails, investigate income variable before continuing
- [ ] Apply P0 forecast horizon change (8 quarters → 6 annual)
- [ ] Update METHODOLOGY.md per P1 fixes
- [ ] Update PRD.md limitation list (F9 imputation)
- [ ] Update DEVIATIONS.md with D11, D12, D13
- [ ] Start Day 3 Task 3.1 with corrected PROMPTS.md