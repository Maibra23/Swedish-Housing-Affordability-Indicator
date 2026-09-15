# Bostadsrätt / Apartment Data — Feasibility & Impact Analysis

**Date:** 2026-04-17
**Updated:** 2026-04-21 — Implementation complete; findings corrected after live API verification.
**Context:** Audit finding F11 — current price data (SCB BO0501C2) covers only permanent small houses (Fastighetstyp 220/villor). This document assesses whether apartment data can be added and what impact it would have.

---

## Implementation Status (as of 2026-04-21)

| Phase | Status | Notes |
|-------|--------|-------|
| Phase A — Fetch + panel integration | ✅ Complete | Source corrected to BO0501C (see §2 correction below) |
| Phase B — Villa vs. bostadsrätt comparison card | ✅ Complete | Shows county name, ratio, and linked regime |
| Phase C — Parallel SHAI indices on BR prices | ⏸ Deferred | Decision unchanged: keep indices on villa prices |

**Key correction from original plan:** SCB BO0701 does not exist in the API (HTTP 400).
The actual bostadsrätt price table is `BO/BO0501/BO0501C/FastprisBRFRegionAr` (content
code `BO0501R7` — Medelpris i tkr). See §2 corrected findings below.

---

## 1. Current State

### What we have

| Variable | Source | Property type | Coverage |
|----------|--------|---------------|----------|
| `transaction_price_sek` | SCB BO0501C2 | Fastighetstyp 220 (permanentbostad ej tomträtt = small houses/villor) | Municipal, 1981–2024 |

**Key problem:** In Swedish cities, first-time buyers overwhelmingly buy **bostadsrätter** (housing cooperatives/condos), not villor. The price gap is large:

| Municipality | Villa price 2024 | Typical bostadsrätt | Overstatement |
|---|---|---|---|
| Stockholm | 8,597,000 SEK | ~3,500,000 SEK | ~2.5× |
| Göteborg | 6,741,000 SEK | ~2,800,000 SEK | ~2.4× |
| Malmö | 6,059,000 SEK | ~2,200,000 SEK | ~2.8× |
| Kiruna | 2,299,000 SEK | ~1,000,000 SEK | ~2.3× |
| Norsjö (rural) | 741,000 SEK | ~600,000 SEK | ~1.2× |

The current Kontantinsats page overstates barriers by 2–3× for urban apartment buyers.

---

## 2. Data Availability

### SCB BO0501 — What content codes exist?

SCB's BO0501 table (FastprisSHRegionAr) contains multiple content codes:

| Code | Description | Property type |
|------|-------------|---------------|
| BO0501C2 | Köpeskilling, medelvärde i tkr | Fastighetstyp 220 (small houses — **currently used**) |
| BO0501C4 | Köpeskillingskoefficient | Fastighetstyp 220 (K/T ratio — **already fetched**) |
| BO0501A2 | Fastighetsprisindex | Small houses — already in panel as `price_index` |

**Critical finding:** SCB's BO0501 FastprisSHRegionAr table covers **Fastighetspriser för Småhus** (small house prices). The "SH" in the table name stands for Småhus. This table does NOT contain bostadsrätt prices.

### What SCB table covers bostadsrätter? (Corrected 2026-04-21)

**Original plan was wrong about BO0701.** Live API verification on 2026-04-21 confirmed:

| Claim in original plan | Actual finding |
|------------------------|---------------|
| BO0701 table exists at `BO/BO0701/BO0701A/Bostprissh` | **HTTP 400 — table does not exist** |
| BO0701 covers ~200+ municipalities | **No municipal data exists anywhere in SCB for bostadsrätt prices** |
| Coverage from ~2012 | **BO0501C covers 2000–2024** |

The correct table is:

| Table | API path | Content code | Coverage |
|-------|----------|-------------|----------|
| **BO0501C** / FastprisBRFRegionAr | `BO/BO0501/BO0501C/FastprisBRFRegionAr` | `BO0501R7` (Medelpris i tkr) | **County level only**: 21 counties + 4 storstadsområden + national (26 regions total). **No municipal data.** Annual 2000–2024. |

**Geographic granularity — verified:**
- Small house prices (BO0501C2): municipal level (~290 municipalities)
- Bostadsrätt prices (BO0501C): **county level only** — all 290 municipalities inherit their county's mean price

**Observed price values (2024, medelpris):**

| County | BR medelpris | Villa medelpris | Ratio villa/BR |
|--------|-------------|----------------|---------------|
| Stockholms län | 4,206,000 SEK | 6,850,000 SEK | 1.63× |
| Västra Götalands län | 2,524,000 SEK | 2,891,000 SEK | 1.15× |
| Skåne län | 2,181,000 SEK | 3,423,000 SEK | 1.57× |
| Norrbottens län | 1,453,000 SEK | 1,457,000 SEK | 1.00× |
| Riket | 2,821,000 SEK | — | — |

### Alternative: Mäklarstatistik / Hemnet

Commercial aggregators (Mäklarstatistik, Hemnet) publish quarterly bostadsrätt median prices at municipal level, but:
- Not available via open API
- Require commercial license or web scraping
- Different methodology from SCB (listing price vs. transaction price)

**Status: out of scope.** County-level SCB data is sufficient for the Pristyp toggle purpose.

---

## 3. Impact Assessment

### Affordability improvement by adding bostadsrätt data

If we add bostadsrätt prices alongside villa prices, the Kontantinsats page could offer a **housing type selector**:

**Scenario: Stockholm 2024, Amorteringskrav 2.0, 10% savings rate, single household**

| Housing type | Price | Required cash | Years to save | Monthly cost |
|---|---|---|---|---|
| Villa (current) | 8,597,000 SEK | 1,289,550 SEK | 24.2 yr | 40,374 SEK |
| Bostadsrätt (~3.5M) | 3,500,000 SEK | 525,000 SEK | 9.8 yr | 16,450 SEK |
| Bostadsrätt (couple, ~3.5M) | 3,500,000 SEK | 525,000 SEK | 4.9 yr | 16,450 SEK |

Adding bostadsrätt data would move Stockholm from **"Otillgänglig"** (>10 yr) to **"Ansträngd"** (5–10 yr) for couples — a meaningful and more accurate representation.

### Impact on SHAI affordability indices (Version A, B, C)

The SHAI affordability indices currently use villa prices for all municipalities. Adding bostadsrätt prices would:

1. **Lower the denominator** in urban municipalities → **higher SHAI scores** (better affordability)
2. **Reduce the urban/rural gap** — rural municipalities primarily have small houses anyway, so their scores change little
3. **Rerank municipalities** significantly: Stockholm would move from worst to middle tier for first-time apartment buyers
4. **Validity question:** Which price series is more relevant for affordability measurement?
   - For systemic financial risk: villa prices (larger credit exposure per transaction)
   - For first-time buyer analysis: bostadsrätt prices (typical purchase)
   - For rental market pressure: neither directly

**Recommendation:** Keep the primary SHAI index on villa prices (systemic perspective), but add bostadsrätt as an optional view on Sida 04 (Kontantinsats).

---

## 4. Implementation Plan

### Phase A — Add bostadsrätt prices to Kontantinsats ✅ COMPLETE (2026-04-21)

**Actual implementation:**

1. **Fetch SCB BO0501C bostadsrätt price data** ✅
   - Table: `BO/BO0501/BO0501C/FastprisBRFRegionAr`, content code `BO0501R7`
   - `src/data/scb_client.py`: `fetch_bostadsratt_price()` updated with correct path
   - Cached to `data/raw/BO0501C_bostadsratt_price.parquet` (650 rows, 26 regions × 25 years)

2. **Build pipeline updated** (`src/data/build_panel.py`) ✅
   - `_clean_bostadsratt_price()`: reads `BO0501C_bostadsratt_price`, filters to 2-char codes
     (county codes 01–25 + national "00"), excludes storstadsområden
   - Municipal merge: removed dead municipality-level attempt (no such data exists).
     All municipalities merged directly via `lan_code` → county's mean BR price
   - `has_native_bostadsratt_price` flag removed (was always False — misleading)
   - Result: `bostadsratt_price_sek` populated for all 290 municipalities, 0% null

3. **Sida 04 UI updated** (`pages/04_Kontantinsats.py`) ✅
   - `Pristyp` radio: "Småhus (villa)" / "Bostadsrätt"
   - County name lookup dict (`_LAN_NAMES`) added to page
   - `price_source_label` shows county: e.g. "Bostadsrätt — Stockholms län (SCB BO0501C)"
   - Info banner updated: explains county-level data, references BO0501C not BO0701
   - Pristyp help text updated to explain county-level fallback mechanism

4. **Data validation — observed values** ✅
   - Stockholm: BR 4.21 MSEK vs villa 8.60 MSEK → ratio 2.04× (within expected range)
   - Uppsala: BR 2.32 MSEK vs villa 4.76 MSEK → ratio 2.05×
   - Kiruna: BR 1.45 MSEK vs villa 2.30 MSEK → ratio 1.58×
   - All values plausible; 0 nulls in panel

### Phase B — Dual-price comparison card ✅ COMPLETE (already implemented prior session)

- Villa vs. bostadsrätt side-by-side card on Sida 04 showing price, kontantinsats (10%),
  years to save, and monthly cost for both property types
- Caption now shows county name and notes that BR price is county-level (SCB BO0501C)
- Uses `latt_2026` regime (10% down) as the reference regime for both comparisons

### Phase C — Optional bostadsrätt series for SHAI indices ⏸ DEFERRED

**Effort:** Medium-High (2–3 days)

- Would require running two parallel panel computations
- Create `affordability_municipal_br.parquet` alongside the villa-based panel
- Add a "Pristyp" toggle to pages 01, 02, 03

**Risk:** Reranking of municipalities would be significant and could confuse users who compare with older results. Additionally, since bostadsrätt data is county-level only, all municipalities within a county would share the same BR price — urban/suburban differentiation within a county would be lost. Requires a clear version note.

**Decision (unchanged):** Defer. The county-granularity limitation makes Phase C less compelling than originally assessed.

---

## 5. Decision Matrix (updated 2026-04-21)

| Option | Effort | Impact | Data Quality | Status |
|--------|--------|--------|--------------|--------|
| Add BR prices to page 04 only (Phase A) | Medium | High for Kontantinsats | Good (SCB BO0501C, county-level) | ✅ Done |
| Dual-price comparison card (Phase B) | Low | Medium | Derived from above | ✅ Done |
| BR prices for SHAI indices (Phase C) | High | High but controversial | Medium — county-only, no intra-county differentiation | ⏸ Deferred |
| Mäklarstatistik API | High | High | Commercial | Out of scope |

---

## 6. Remaining Open Items

1. **Phase C decision:** County-level limitation makes BR SHAI indices less valuable than
   originally assessed. Revisit if SCB adds municipal bostadsrätt statistics in a future release.
2. **BO0501C update cadence:** SCB updates FastprisBRFRegionAr annually. Run
   `python scripts/refresh_data.py` once per year to pick up the latest year's data.
3. **Storstadsområden data excluded:** Codes 0010 (Stor-Stockholm), 0020 (Stor-Göteborg),
   0030 (Stor-Malmö), 0060 (Riket exkl storstadsområden) are fetched but filtered out in
   `_clean_bostadsratt_price()` to avoid duplication with the county codes. If a future
   use case needs sub-county storstadsregion breakdowns, these codes are available in the
   raw parquet `BO0501C_bostadsratt_price.parquet`.

---

## 7. Summary Conclusion (updated 2026-04-21)

**Do we have apartment data?** Yes — `bostadsratt_price_sek` is now in
`affordability_municipal.parquet` for all 290 municipalities (0% null) and exposed as
the `Pristyp` toggle on Sida 04.

**Data source:** SCB BO0501C (not BO0701 as originally planned — BO0701 does not exist).
Coverage is **county-level only**. All municipalities in the same county share one BR price.

**Impact observed (Stockholm 2024, Lättnad 2026, 10% savings rate):**
- Villa: 8.60 MSEK → kontantinsats 860k SEK → ~20 yr to save (singel)
- Bostadsrätt (länsnivå): 4.21 MSEK → kontantinsats 421k SEK → ~10 yr to save (singel)
- Par (bostadsrätt): ~5 yr to save → "Ansträngd" rather than "Otillgänglig"

**SHAI rankings:** unchanged (indices remain villa-based)
**User trust:** significantly improved for urban users who are told which county's BR data is shown
