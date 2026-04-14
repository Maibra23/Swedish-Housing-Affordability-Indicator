# SHAI Task Execution Playbook (v2)
## Post Day 2 revision

**Version:** 2.0
**Supersedes:** PLAYBOOK.md v1
**Status:** Days 1 and 2 complete. Start from Day 3 with K/T corrections applied first.
**Tooling key:** [CC] = Claude Code, [CR] = Cursor Pro+

---

## Status checklist

- [x] Day 1 complete (data pipeline, all parquet caches built)
- [x] Day 2 complete (index computation)
- [ ] **Pre Day 3: apply PATCH_POST_DAY2.md P0 fixes**
- [ ] **Pre Day 3: rerun Task 2.2 with kt_ratio, rerun Task 2.4 validation**
- [ ] Day 3 (forecasting + kontantinsats + scenario)
- [ ] Day 4 (Streamlit shell in Swedish, Riksöversikt)
- [ ] Day 5 (remaining 5 pages)
- [ ] Day 6 (translation audit, deployment, README)

---

## Pre Day 3 correction sequence

Run these in order before starting Day 3 tasks.

### Correction 1: K/T substitution in formulas

See PROMPTS_v2.md "Task 2.2 correction" block. ~30 min.

### Correction 2: Validation re run

See PROMPTS_v2.md "Task 2.4 correction" block. ~15 min.

### Correction 3: Checkpoint

If Stockholm now ranks top 5 worst under Version C: proceed to Day 3.
If Stockholm does NOT move: halt, investigate income variable. Do not continue to Day 3 with ambiguous ranking data.

---

## Day 3 — Forecasting and engines [CC]

### Task 3.1 [CC] Prophet forecasting (annual, 6 step horizon)

**Context:** Panel is annual, 11 observations (2014 to 2024). Forecasts extend 6 steps to 2030. Prophet's yearly_seasonality is disabled since data has no sub annual structure.

**Deliverable:** `src/forecast/prophet_pipeline.py`, output `data/processed/forecast_prophet.parquet`

**Acceptance:** 21 counties × 6 years × 4 variables = 504 rows. Confidence bands widen monotonically.

**Prompt reference:** PROMPTS_v2.md Task 3.1

### Task 3.2 [CC] ARIMA forecasting (annual, 6 step horizon)

**Context:** Same frequency and horizon as Prophet. Auto ARIMA order selection. Accept that trivial orders like (0,1,0) may be selected given only 11 observations.

**Deliverable:** `src/forecast/arima_pipeline.py`, output `data/processed/forecast_arima.parquet`, metadata in `arima_metadata.parquet`

**Acceptance:** Same row count as Prophet, orders logged, intervals widen.

**Prompt reference:** PROMPTS_v2.md Task 3.2

### Task 3.3 [CC] Kontantinsats engine

**Context:** Four regulatory regimes per METHODOLOGY_v2 section 6. Converts K/T to SEK price level using taxeringsvärde proxy (~75% of market value).

**Deliverable:** `src/kontantinsats/engine.py`

**Acceptance:** Monthly total ordering: amort_2 ≥ amort_1 ≥ bolanetak ≥ pre_2010

**Prompt reference:** PROMPTS_v2.md Task 3.3

### Task 3.4 [CC] Scenario simulator (Version C only)

**Context:** Pure function, recomputes Version C only per DEVIATIONS D12.

**Deliverable:** `src/scenario/simulator.py`

**Acceptance:** Zero shocks return zero delta exactly.

**Prompt reference:** PROMPTS_v2.md Task 3.4

---

## Day 4 — Streamlit shell in Swedish [CR]

### Task 4.1 [CR] Streamlit app skeleton

Same as v1 PLAYBOOK. Add:
- `src/ui/formatting.py` with Swedish number/date helpers (from swedish-translation skill references/number_formatting.md)
- `src/ui/imputation.py` helper to render imputed values with reduced opacity

**Prompt reference:** PROMPTS v1 Task 4.1

### Task 4.2 [CR] Sidebar

Unchanged from v1. **Prompt reference:** PROMPTS v1 Task 4.2

### Task 4.3 [CR] Choropleth component

Add support for tooltip displaying `has_native_kt` status.

**Prompt reference:** PROMPTS v1 Task 4.3 with modification noted in PROMPTS_v2

### Task 4.4 [CR] Riksöversikt page

**Changes from v1:**
- KPI #3 label: "Medianpris (K/T ratio)" not per kvm
- Imputation badge on current year if imputed
- Tooltip shows native vs county fallback K/T
- Rankings use post K/T fix data

**Prompt reference:** PROMPTS_v2.md Task 4.4

---

## Day 5 — Remaining pages [CR]

### Task 5.1 [CR] Län jämförelse

Annual x axis. Version B tab needs Arbetsförmedlingen footnote.
**Prompt reference:** PROMPTS_v2.md Task 5.1

### Task 5.2 [CR] Kommun djupanalys

Annual x axis, 6 step horizon, persistent 11 observation caveat.
**Prompt reference:** PROMPTS_v2.md Task 5.2

### Task 5.3 [CR] Kontantinsats

Unchanged from v1. **Prompt reference:** PROMPTS v1 Task 5.3

### Task 5.4 [CR] Scenariosimulator

Add scope note that only Version C is recomputed.
**Prompt reference:** PROMPTS_v2.md Task 5.4

### Task 5.5 [CR] Metodologi

10 limitations not 8. K/T vs price index rationale prominent. 11 observation caveat on forecasting.
**Prompt reference:** PROMPTS_v2.md Task 5.5

---

## Day 6 — Polish and deployment [CR]

### Task 6.1 [CR] Swedish translation audit

Extended checks: imputation tooltip, unemployment footnote, K/T explainer.
**Prompt reference:** PROMPTS_v2.md Task 6.1

### Task 6.2 [CR] Loading and error states

Unchanged. **Prompt reference:** PROMPTS v1 Task 6.2

### Task 6.3 [CR] Deployment

Unchanged. **Prompt reference:** PROMPTS v1 Task 6.3

### Task 6.4 [CR] README

Include a paragraph about the K/T methodology choice and the annual panel constraint.
**Prompt reference:** PROMPTS v1 Task 6.4 with added paragraph

---

## Risk register (updated)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| K/T fix does not resolve Stockholm anomaly | Medium | High | Investigate income variable; worst case, use Version A as the headline formula with caveats |
| ARIMA auto selects trivial orders | High | Low | Document in UI; this is expected with 11 observations |
| Prophet install fails on Streamlit Cloud | Medium | Medium | Pin prophet>=1.1.5; test deployment Day 5 |
| 6 step forecasts look too uncertain | High | Low | Persistent caveat; limit is data, not implementation |
| Imputed years confuse users | Medium | Low | Visual styling plus tooltip |
| Unemployment definition creates confusion | Low | Low | Footnote on every page using U |

---

## Quality gates

Before moving from Day N to Day N+1, confirm:

**Day 2 → 3 gate:** Stockholm ranks top 5 worst under Version C after K/T fix. All 6 validation checks pass.

**Day 3 → 4 gate:** All 4 parquet outputs present. Kontantinsats produces monotonic ordering. Scenario zero test passes.

**Day 4 → 5 gate:** App runs, sidebar matches mockup, Riksöversikt renders all 290 municipalities.

**Day 5 → 6 gate:** All 6 pages navigate without error. No English strings visible. All formulas display.

**Day 6 → Done gate:** Deployed URL loads under 5 seconds. README exists. Screenshots captured.