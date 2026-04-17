# SHAI — Comprehensive Methodology & Assumption Audit

**Version:** 1.0
**Date:** 2026-04-17
**Scope:** Full codebase review — all pages, engines, data pipeline, and displayed formulas
**Data inspected:** `affordability_municipal.parquet`, `panel_national.parquet`, `BO0501_transaction_price.parquet`

---

## Executive Summary

This audit identifies **4 critical issues**, **4 moderate issues**, and a systematic gap in tooltip/help-text coverage across all dashboard pages. The most important finding is that the Kontantinsats page produces shock-ingly high numbers not due to a calculation bug, but because three compounding assumptions push the output in the same direction. The second most important finding is that the formulas displayed to users are factually wrong — they show the K/T variable but the code computes with transaction price in SEK.

---

## 1. Critical Issues

### C1 — Formula display shows K/T but code uses transaction_price_sek

**File locations:**
- Display: `pages/02_Lan_jamforelse.py:63–98` and `pages/06_Metodologi.py:93–107`
- Computation: `src/indices/affordability.py:31–92`

**What the UI shows:**

```
Version A:  Affordability_A = Income / (KT(i,t) × R(t))
Version C:  Affordability_C = Income / (KT(i,t) × max(R − π, 0.005))
```

**What the code actually computes:**

```python
# src/indices/affordability.py — Version A
price = panel["transaction_price_sek"]   # e.g. 8,597,000 SEK for Stockholm
rate_safe = rate_decimal.clip(lower=0.001)
return income / (price * rate_safe)

# src/indices/affordability.py — Version C
real_rate = (rate - inflation).clip(lower=0.5)
real_rate_decimal = real_rate / 100.0
return income / (price * real_rate_decimal)
```

**The gap:** K/T (köpeskillingskoefficient) is a dimensionless ratio typically ranging 1.0–4.0.
`transaction_price_sek` is an absolute price in SEK, ranging 518,000–13,095,000.
These are completely different variables. The LaTeX displayed to users is factually wrong.

**Root cause:** METHODOLOGY_v2.md correctly documents that the code switched from K/T to
transaction_price_sek (see section 3: "Why median transaction price"), but the formula
display strings on pages 02 and 06 were never updated to reflect the change.

**Impact:** Any technically literate user who reads the formula and tries to reproduce the
numbers will get wildly different results. It undermines the credibility of the dashboard.

**Fix:** Update all LaTeX formula strings to replace `KT(i,t)` with `P_{\text{SEK}}(i,t)`
and update the "Varför K/T, inte prisindex?" section on the Metodologi page accordingly —
the rationale text explains _why_ K/T was rejected, which is the correct story to tell, but
the formula itself must reflect what is actually computed.

---

### C2 — SCB BO0501C2 is the mean (medelvärde), not the median

**File location:** `src/data/build_panel.py:152–185`

**Evidence from raw data:**
```
ContentsCode_code: BO0501C2
ContentsCode:      Köpeskilling, medelvärde i tkr   ← "medelvärde" = arithmetic mean
```

**What the code and documentation say:** Every comment, docstring, and the METHODOLOGY_v2.md
variable register call this the "median transaction price" — which it is not.

```python
# build_panel.py line 152 docstring (wrong):
"""Median transaction price in SEK per region x year."""

# METHODOLOGY_v2.md Section 2 (wrong):
# Median transaction price in SEK (P_sek) — SCB BO0501C2, 1981–2024
```

**Impact of mean vs. median:** In housing markets, a small number of very expensive
transactions pulls the mean well above the median. In Stockholm 2024, the mean villa price is
~8.6 MSEK. Swedish Mäklarstatistik reports the median villa price in Stockholm at approximately
7.5–8.0 MSEK — so the gap is modest for villas but can be larger in markets with thin trading
volume (small municipalities) where a single expensive sale distorts the mean significantly.

**Recommended fix:**
1. Update all docstrings and METHODOLOGY_v2.md to say "mean (medelvärde)" not "median".
2. Investigate whether SCB BO0501 offers a median content code at municipal granularity; if
   so, consider switching. If not, document this clearly as limitation F11.

---

### C3 — Why Kontantinsats numbers are so high: three compounding factors

**Page:** `pages/04_Kontantinsats.py` · Engine: `src/kontantinsats/engine.py`

Observed output for Stockholm 2024 (default settings, 10% savings rate):

```
transaction_price_sek:  8,597,000 SEK
median_income:            533,800 SEK
Kontantinsats (15%):    1,289,550 SEK
Years to save:               24.2 years
```

This is not a calculation bug — the arithmetic is correct. The numbers are high because three
independent assumptions each push in the same direction:

#### Factor 1: Price data covers small houses (villor) only — not apartments

`build_panel.py:163` filters the raw data to `Fastighetstyp_code == "220"`, which means
"permanentbostad, ej tomträtt" — essentially detached and semi-detached houses (småhus/villor).

In Swedish cities, this is **not** the typical housing purchase. In Stockholm, Göteborg, and
Malmö, the overwhelming majority of first-time buyers purchase **bostadsrätter** (apartments/
condos), which trade at roughly 2–4 MSEK versus 7–9 MSEK for villas.

| Municipality | Villa price (used) | Typical bostadsrätt | Overstatement factor |
|---|---|---|---|
| Stockholm | 8,597,000 | ~3,500,000 | ~2.5× |
| Göteborg | 6,741,000 | ~2,800,000 | ~2.4× |
| Malmö | 6,059,000 | ~2,200,000 | ~2.8× |
| Kiruna | 2,299,000 | ~1,000,000 | ~2.3× |

For rural municipalities (Norsjö: 741k SEK, Dorotea: 559k SEK) the difference is smaller
since rural villa and apartment prices are closer together.

**Consequence:** The Kontantinsats page correctly describes what it does, but does not tell the
user that "transaction price" means villa prices. A Stockholm user sees "24 years to save" and
draws a conclusion about their own apartment purchase, which is a 2.5× less expensive asset.

#### Factor 2: Income is individual, but housing is typically bought as a couple

`HE0110_income` contains "sammanräknad förvärvsinkomst" (combined earned income) per individual.
This is essentially gross earned income per person.

A single person earning 533,800 SEK (Stockholm median) saves 53,380 SEK/year at 10%.
A couple with two median incomes saves 106,760 SEK/year — exactly halving the time.

For Stockholm:
- Single person buying a villa: **24.2 years**
- Couple buying a villa: **12.1 years**
- Couple buying a typical apartment (3.5 MSEK): **4.9 years**

The Kontantinsats page shows only the single-person figure with no caveat.

#### Factor 3: Pre-tax vs. disposable income (ambiguous, less critical)

"Sammanräknad förvärvsinkomst" is gross earned income before income tax. Disposable income
(after tax) is approximately 65–70% of this in Sweden. However, whether 10% of gross or 10%
of disposable is more realistic depends on how users interpret "sparkvot":

- If users think sparkvot = % of take-home pay → they would set ~14–15% gross to get
  10% of take-home, meaning the page slightly understates saving difficulty.
- If users think sparkvot = % of gross income → the current calculation is consistent.

The help text added in the recent polish round says "andel av bruttoinkomsten" (share of gross
income), which makes the current calculation internally consistent. However, 10% of gross
income as a savings rate is extremely ambitious in practice.

#### Realistic reference scenario

For a typical Stockholm couple buying a bostadsrätt at 3.5 MSEK:
```
Kontantinsats (15%):    525,000 SEK
Combined savings/yr:    106,760 SEK (2 × 533,800 × 10%)
Years to save:             4.9 years  ← Ansträngd, not Otillgänglig
```

**Recommended fixes:**
1. Add a `st.warning` on page 04 stating that price data covers small houses (Fastighetstyp
   220) and does not include bostadsrätter/apartments.
2. Add a "Hushållstyp" control (1 or 2 income earners) that multiplies savings capacity.
3. Add a reference sidebar or footnote showing typical apartment prices vs. villa prices for
   the selected municipality.

---

### C4 — Policy rate ≠ mortgage rate (systematic understatement of borrowing costs)

**Files:** `src/indices/affordability.py:42–48`, `src/kontantinsats/engine.py:99`,
`src/scenario/simulator.py:40–50`

All three engines use `policy_rate` (Riksbankens styrränta, the base rate) directly as the
borrowing rate. Swedish banks charge a mortgage rate of approximately:

```
mortgage_rate ≈ policy_rate + bank_margin
bank_margin   ≈ 1.5–2.5%  (typically ~1.7% for standard 3-month fixed)
```

In 2024 with policy_rate = 3.63%, actual mortgage rates were ~4.5–5.0%.

**Impact on affordability formulas:** Using 3.63% instead of ~4.8% makes the denominator
smaller, making affordability scores ~32% higher than they should be. The ranking of municipalities
is preserved (all use the same national rate), but absolute values and the scenario simulator
results are optimistic.

**Impact on Kontantinsats monthly cost:** The engine computes:
```python
annual_interest = loan_amount * rate   # rate = policy_rate / 100
```
For Stockholm at 85% LTV on 8.6 MSEK: loan = 7.3 MSEK.
- At policy rate (3.63%): annual interest = 265k SEK → monthly 22k SEK
- At mortgage rate (4.8%): annual interest = 350k SEK → monthly 29k SEK

The page **understates monthly housing cost by ~7,000 SEK/month** for Stockholm.

**Recommended fix:**
Add a `bank_margin_pct` parameter to the Kontantinsats engine (default 1.7%) and expose it as
an optional advanced slider on page 04. For the affordability formulas, document this as a new
limitation (F11 or F12) and note that rankings are unaffected but absolute values are
understated.

---

## 2. Moderate Issues

### M1 — Version B z-scores mix cross-time and cross-municipality variation

**File:** `src/indices/affordability.py:52–69`

```python
def compute_version_b(panel: pd.DataFrame) -> pd.Series:
    pi_ratio = panel["transaction_price_sek"] / panel["median_income"]
    z_pi_ratio = _zscore(pi_ratio)          # normalized across ALL rows (all years × all muni)
    z_rate = _zscore(panel["policy_rate"])  # national rate → only varies by year, not by muni
    z_unemp = _zscore(panel["unemployment_rate"])
    z_cpi = _zscore(panel["cpi_yoy_pct"])   # national CPI → only varies by year, not by muni
    return 0.35 * z_pi_ratio + 0.25 * z_rate + 0.20 * z_unemp + 0.20 * z_cpi
```

Since `policy_rate` and `cpi_yoy_pct` are national variables (same for all municipalities in
a given year), their z-scores only encode the year — not any municipality-specific information.
Within a single year, z(R) and z(π) are constants, contributing only an additive shift to all
municipalities' Version B scores.

This means **45% of the Version B weights** (rate 25% + CPI 20%) carry no cross-municipal
discrimination in a single-year view. The ranking on Sida 01 and 02 is determined almost
entirely by z(P/I) (35%) and z(unemployment) (20%).

**This is documented nowhere and is not visible to users.**

**Recommended fix:**
1. Document this in F-list as F11.
2. Consider computing z_rate and z_cpi as deviations from the panel-wide year-level mean
   (year fixed effects), so they contribute temporal variation to the composite without
   dominating cross-municipal variation.

---

### M2 — Income forward-fill with zero nominal growth

**File:** `src/data/build_panel.py:262–274`

```python
if max_income_year < current_year:
    for fill_year in range(max_income_year + 1, current_year + 1):
        fill = panel[panel["year"] == max_income_year].copy()
        fill["year"] = fill_year
        fill["is_imputed_income"] = True
        panel = pd.concat([panel, fill], ignore_index=True)
```

2025 and 2026 income is forward-filled from 2024 with zero growth. Swedish nominal wage growth
has averaged ~3–4%/year in recent years. This makes 2025–2026 affordability appear worse than
it will likely be.

The `is_imputed_income` flag is correctly set and the forecast page shows a visual warning,
but the Riksöversikt (page 01) and Lan jämförelse (page 02) show 2025–2026 data without any
visual differentiation for imputed years.

**Recommended fix:**
1. Apply a conservative forward-fill growth rate (e.g. 3% nominal) rather than zero.
2. Or: visually mark imputed-income years on pages 01 and 02 (e.g. reduced opacity on bars,
   "★ Imputerad inkomst" annotation on trend charts).

---

### M3 — Scenario simulator treats rate and CPI as independent

**File:** `src/scenario/simulator.py:44–50`

```python
s_rate = rate + rate_shock                 # rate changes
real_rate_scen = max(s_rate - cpi, 0.5)   # cpi stays at baseline — never shocked
```

In practice, rate hikes are either responses to high inflation or precursors to lower inflation.
A scenario of "+3 pp rate shock" with unchanged CPI implies a real rate jump of +3 pp, which
is very different from a "+3 pp rate shock" that follows a "+3 pp CPI spike" (real rate unchanged).

The 2022–2023 Swedish rate hike cycle was driven by inflation peaking at ~10%, meaning the
real rate barely changed while nominal rates tripled. The simulator would model this incorrectly.

**Recommended fix:** Add an optional "inflation change" slider (currently only rate, income,
and price). Or add two preset scenario buttons: "Riksbanken 2022 (rate +4, CPI +8)" and
"Deflation risk (rate −1, CPI −2)" to demonstrate the distinction.

---

### M4 — Real rate floor at 0.5 pp is undocumented and sensitive

**File:** `src/indices/affordability.py:87`, `src/indices/real_rate.py:36`

```python
real_rate = (rate - inflation).clip(lower=0.5)
```

The floor of 0.5 percentage points prevents Version C from exploding when real rates are near
zero or negative (2020–2021: policy rate ~0%, CPI ~1–2% → real rate ~ −1%).

When the floor binds, all municipalities receive the same denominator factor (0.005), meaning
Version C collapses entirely to `Income / (Price × 0.005)` — a pure price-to-income ratio
with a constant multiplier. The ranking in floor years is entirely driven by P/I ratio.

The choice of 0.5 pp is never justified. A floor of 0.25 pp would produce values 2× higher in
floor years; a floor of 1.0 pp would produce values 2× lower.

**Recommended fix:**
1. Add a line to the Metodologi page explaining that 2020–2021 values are affected by the
   floor and what that means for interpretation.
2. Show which years hit the floor in the time-series charts (e.g. a background band or
   annotation).

---

## 3. Tooltip & Help Text Gaps (Page-by-Page)

Below is a complete gap analysis. Items marked **[ADD]** are missing; **[FIX]** have incorrect
or misleading content.

### Page 01 — Riksöversikt

| Component | Issue | Recommendation |
|-----------|-------|----------------|
| KPI "Medianpris (K/T ratio)" | **[FIX]** Label says "Medianpris" but value is K/T ratio — these are not the same. K/T is dimensionless (1.0–4.0), not a price. | Rename label to "K/T-kvot (genomsnitt)" or replace with actual median price |
| KPI "Genomsnittligt SHAI" | tooltip exists but brief | **[ADD]** Note that higher = better and clarify it is a raw ratio, not a 0–100 index |
| Choropleth legend | No color scale explanation inline | **[ADD]** Caption: "Grön = låg risk (z < −0,67), gul = medel, röd = hög risk (z > 0,67)" |
| Histogram x-axis "SHAI poäng (z-poäng)" | z-score not explained | **[ADD]** Expander note: "Z-poäng = standardavvikelser från genomsnittet. Noll = rikssnitt." |
| Ranking table "Z-poäng" column | no help | **[ADD]** Column header tooltip: "Standardavvikelser från riksgenomsnitt (år {year})" |
| Ranking table "SHAI" column | no help | **[ADD]** Tooltip: "Raw Version C-värde (Inkomst / (Pris × Realränta))" |

### Page 02 — Län jämförelse

| Component | Issue | Recommendation |
|-----------|-------|----------------|
| Version A formula | **[FIX]** Shows KT, should show P_SEK | Fix LaTeX to `\frac{I}{P_{\text{SEK}} \times R}` |
| Version B formula | **[FIX]** Shows KT in the ratio, should show P_SEK | Fix `\frac{KT}{I}` to `\frac{P_{\text{SEK}}}{I}` |
| Version C formula | **[FIX]** Shows KT, should show P_SEK | Fix LaTeX |
| Chart y-axis "Indexvärde" | Generic label | **[FIX]** Use "Affordability-kvot" for A/C, "Riskpoäng" for B |
| Stockholm highlight | No legend entry explaining why bold | **[ADD]** `st.caption`: "Stockholm visas som referenslän (markerat)" |
| Version B footnote | Exists for unemployment | **[ADD]** Also footnote: "R och π är nationella — bidrar ej till kommunal rangordning inom ett enskilt år" |
| Cross-formula comparison | No guidance | **[ADD]** Caption: "Att olika formler rangordnar länen olika är förväntat och inte ett fel" |

### Page 03 — Kommun djupanalys

| Component | Issue | Recommendation |
|-----------|-------|----------------|
| KPI "SHAI (Version C)" | No tooltip | **[ADD]** `tooltip="Realversion. Inkomst / (Pris × max(R−π, 0,5%)). Högre = bättre."` |
| KPI "Medianinkomst" | No tooltip | **[ADD]** `tooltip="Sammanräknad förvärvsinkomst, medianinkomst per individ (SCB HE0110)."` |
| KPI "K/T-kvot" | No tooltip | **[ADD]** `tooltip="Köpeskillingskoefficient: pris / taxeringsvärde. Speglar relativ prisnivå."` |
| KPI "Styrränta" | No tooltip | **[ADD]** `tooltip="Riksbankens styrränta, årsgenomsnitt. Nationell — samma för alla kommuner."` |
| ★ Driver indicator caption | At page bottom, easy to miss | **[FIX]** Move the "★ Indikatorn driver mest av SHAI" text to just below the component heading |
| Prophet tab | No warning about Prophet limitations | **[ADD]** `st.caption("Prophet är optimerat för dagsdata. ARIMA-fliken rekommenderas för analys.")` |
| Forecast confidence band | Good but unlabeled in legend | **[FIX]** Legend currently says "80% konfidensintervall" — confirm that's correct and keep it |
| "is_imputed_income" markers | Diamond markers exist | Good — but add tooltip to diamond: `"Inkomst 2025+ är framskriven från 2024 utan tillväxt"` |

### Page 04 — Kontantinsats

| Component | Issue | Recommendation |
|-----------|-------|----------------|
| **Housing type** | **[ADD — Critical]** Nowhere does the page say prices are for villas/småhus | Add `st.warning("Priserna avser småhus (Fastighetstyp 220 — villor). Bostadsrätter ingår ej. Insatskraven är därmed höga för städer.")` |
| **Income type** | **[ADD — Critical]** Individual income vs. couple purchase not mentioned | Add `st.caption("Inkomsten är individuell (SCB). Vid gemensamt köp: dividera spartiden med 2.")` below the years-to-save KPI |
| Mortgage rate assumption | **[ADD]** No mention that policy rate ≠ mortgage rate | Add to "Detaljer & antaganden" expander: note that actual mortgage rate = policy rate + bankens marginal (~1,7 pp) |
| Kontantinsatsbörda KPI | tooltip mentions "årsinkoster" (typo) | **[FIX]** Typo: "årsinkoster" → "årsinkoster" → correct to "årsinkoster" |

### Page 05 — Scenariosimulator

| Component | Issue | Recommendation |
|-----------|-------|----------------|
| Rate shock slider | No `help=` | **[ADD]** `help="Adderas till styrräntan. +2 pp ≈ Riksbankens höjningscykel 2022–2023."` |
| Income slider | No `help=` | **[ADD]** `help="+3–4 % ≈ ett års normal löneutveckling. −5 % simulerar recession."` |
| Price slider | No `help=` | **[ADD]** `help="−20 % ≈ det svenska bostadsprisfallet 2022. +25 % simulerar en prisspiral."` |
| CPI invariance | **[ADD]** Users may not know CPI is fixed | Add note in the "Förklaring" expander: "Inflationen (π) hålls konstant i simulatorn" |
| Scope note `st.info` | Good — mentions Version C only | Keep as-is |

---

## 4. Data Pipeline Assumptions (Summary)

| Assumption | Where | Consequence | Risk |
|---|---|---|---|
| Fastighetstyp 220 only | `build_panel.py:163` | Villa prices, not apartments | High for urban analysis |
| BO0501C2 = mean price | `build_panel.py:173` | Slight upward bias in thin markets | Low–Medium |
| National rate for all municipalities | `build_panel.py:331–333` | No regional rate variation possible | Documented (F2) |
| County K/T fallback for 12% of municipalities | `build_panel.py:289–296` | County ≠ municipality pricing | Documented (F1) |
| County transaction price fallback | `build_panel.py:306–317` | Same as above | Partially documented |
| Income forward-filled, zero growth, 2025–2026 | `build_panel.py:263–273` | Pessimistic recent years | Documented (F9) |
| Policy rate used directly (no bank margin) | `engine.py:99` | ~30% understatement of cost | **Not documented** |
| CPI fixed in scenario | `simulator.py:48` | Rate-inflation independence assumed | **Not documented** |
| 10% savings rate default | `engine.py:56` | May be gross or net depending on user | Partially documented |

---

## 5. Validated Correct Assumptions (do not change)

These aspects of the codebase were specifically challenged and found to be correct:

| Item | Verdict |
|---|---|
| LTV-based amortization tiers use `max()`, not cumulative addition | **Correct** — tiers are replacement thresholds, not additive bands (FI regulation) |
| LTI-based amortization adds on top of LTV result | **Correct** — per FI amortization rules 2018 |
| Real rate floor of 0.5 pp in Version C | **Architecturally sound**, value is arbitrary (see M4) |
| Z-score normalization within ranking year | **Correct** — cross-sectional normalization for municipal comparison |
| Inverting A and C z-scores so "higher z = worse" matches B | **Correct** — convention is documented |
| 6-step forecast horizon cap | **Correct** — 11 observations cannot support longer confident forecasts |
| ARIMA recommended over Prophet | **Correct** — Prophet optimized for sub-annual frequency; macro annual data suits ARIMA |
| County-level income (direct from SCB, not aggregated from municipalities) | **Correct** — SCB publishes county income separately; aggregating municipal medians is statistically wrong |

---

## 6. New Limitations to Add to F-List

The following should be added to the Metodologi page (Section 6) and METHODOLOGY_v2.md:

| New ID | Limitation | Mitigation |
|---|---|---|
| **F11** | SHAI indices (A/B/C) still compute on villa prices only (SCB BO0501C2, Fastighetstyp 220) for a systemic view. Bostadsrätt prices (SCB BO0701) are fetched and merged into the panels as `bostadsratt_price_sek`, with the raw county value preserved as `bostadsratt_price_sek_county` and a `has_native_bostadsratt_price` flag. Granularity is asymmetric: BO0501 småhus is municipal for all 290 kommuner, BO0701 bostadsrätt is municipal for only ~150–200 larger kommuner and county-level for the rest. Page 04 exposes a `Pristyp` toggle whose label states the active granularity ("kommun" / "län"), and the villa-vs-bostadsrätt comparison card matches geographic level automatically (muni-vs-muni where both are native, otherwise county-vs-county) so the displayed ratio never mixes a municipal villa price with a county apartment average. Phase C (parallel bostadsrätt SHAI index) remains deferred pending confirmation of BO0701 municipal coverage ≥150. | Pristyp selector with level label + matched-granularity comparison card on Sida 04. |
| **F12** | Policy rate used as mortgage rate. Actual mortgage rate ≈ policy rate + 1.5–2.5 pp bank margin. Monthly cost and affordability formulas are correspondingly optimistic. | Add optional bank margin slider on page 04. |
| **F13** | Version B rate and CPI z-scores carry no cross-municipal variation in a single year (national variables). 45% of Version B weights are time-only signals. | Document in formula description on pages 02 and 06. |
| **F14** | Income is individual gross earned income. Housing is typically purchased as a couple. Single-income years-to-save is 2× the household figure. | Add household multiplier control on page 04. |
| **F15** | Scenario simulator holds CPI fixed when the rate is shocked. Real rate changes are therefore nominal rate changes, not genuine real rate shocks. | Add CPI shock slider or preset scenarios. |

---

## 7. Recommended Implementation Sequence

### Phase 1 — Correctness fixes (no UX change needed, low effort)

1. Fix formula LaTeX on pages 02 and 06: replace `KT(i,t)` with `P_{\text{SEK}}(i,t)` everywhere
2. Fix docstring in `build_panel.py:152` and METHODOLOGY_v2.md section 2: "mean" not "median"
3. Fix KPI label on page 01: "Medianpris (K/T ratio)" → "K/T-kvot (genomsnitt)"
4. Fix typo in Kontantinsats tooltip: "årsinkoster" → "årsinkoster" (verify spelling)
5. Add F11–F15 to Metodologi page section 6 and METHODOLOGY_v2.md

### Phase 2 — Clarity additions (high impact, low effort)

6. Add housing-type `st.warning` to page 04
7. Add individual-income note to page 04 (below "År att spara" KPI)
8. Add mortgage margin note to page 04 "Detaljer & antaganden" expander
9. Add `help=` tooltips to all sliders on page 05 (rate, income, price)
10. Add KPI tooltips on page 03 (SHAI, income, K/T, rate)
11. Add choropleth color legend caption on page 01
12. Add Version B national-variable caveat on page 02

### Phase 3 — Enhancements (medium effort, high analytical value)

13. Add household multiplier toggle to page 04 (single / couple)
14. Add optional bank margin slider to page 04
15. Add CPI shock slider to page 05
16. Add preset scenario buttons to page 05 ("Riksbanken 2022", "Deflation")
17. Mark imputed-income years visually on pages 01 and 02
18. Apply a 3% growth rate to forward-filled income years in `build_panel.py`

---

## 8. Appendix: Data Spot-Check Results

These values were verified directly from `affordability_municipal.parquet` and
`BO0501_transaction_price.parquet` for 2024:

```
=== Transaction price distribution 2024 (all 290 municipalities) ===
min:      518,000 SEK   (Dorotea)
p25:    1,503,750 SEK
median: 2,192,500 SEK
p75:    3,530,500 SEK
max:   13,095,000 SEK   (Danderyd)

=== Income distribution 2024 ===
min:    346,800 SEK   (Dorotea)
median: 439,200 SEK
max:    902,000 SEK   (Danderyd)

=== National panel 2024 ===
policy_rate:  3.63%
cpi_yoy_pct:  2.86%
real_rate:    0.77%  (above floor, floor did not bind in 2024)

=== Kontantinsats sanity check 2024 ===
Stockholm (villa):      price 8,597k  income 534k  KI 1,290k  yrs@10% single=24.2  couple=12.1
Malmö (villa):          price 6,059k  income 433k  KI  909k   yrs@10% single=21.0  couple=10.5
Göteborg (villa):       price 6,741k  income 456k  KI 1,011k  yrs@10% single=22.2  couple=11.1
Kiruna:                 price 2,299k  income 488k  KI  345k   yrs@10% single=7.1   couple=3.6
Norsjö:                 price   741k  income 416k  KI  111k   yrs@10% single=2.7   couple=1.4

=== Raw SCB variable confirmed ===
BO0501C2 label: "Köpeskilling, medelvärde i tkr" (MEAN, not median)
Stockholm county 2024: 6,748,000 SEK (county mean)
Stockholm municipality 2024: 8,597,000 SEK (municipal mean)
```
