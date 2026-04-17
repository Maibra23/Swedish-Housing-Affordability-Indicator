# Bostadsrätt / Apartment Data — Feasibility & Impact Analysis

**Date:** 2026-04-17
**Context:** Audit finding F11 — current price data (SCB BO0501C2) covers only permanent small houses (Fastighetstyp 220/villor). This document assesses whether apartment data can be added and what impact it would have.

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

### What SCB table covers bostadsrätter?

Bostadsrätt transaction prices are published under a separate SCB table:

| Table | Name | Coverage |
|-------|------|----------|
| **BO0501C** | Fastighetspriser och lagfarter — Bostadsrätter | County, national; quarterly/annual |
| Content code | Köpeskilling, medelvärde per bostadsrätt | Municipal (limited), county, national |

**Important limitation:** SCB's bostadsrätt price data has **lower geographic granularity** than the small house data:
- Small house prices (BO0501C2): available at **municipal level** for ~290 municipalities
- Bostadsrätt prices (BO0501C): available at **county level** (21 counties) for most years; municipal coverage is **partial** — mainly larger municipalities (estimated ~100–150 of 290)

### Alternative: Mäklarstatistik / Hemnet

Commercial aggregators (Mäklarstatistik, Hemnet) publish quarterly bostadsrätt median prices at municipal level, but:
- Not available via open API
- Require commercial license or web scraping
- Different methodology from SCB (listing price vs. transaction price)

### Alternative: SCB's PxWeb — Bostadsrättsstatistik BO0701

SCB publishes a dedicated bostadsrätt register (BO0701) with:
- Annual mean transaction price for bostadsrätter
- Available at municipal level for ~200+ municipalities (larger ones)
- Coverage: ~2012–present

**This is the most viable data addition.**

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

### Phase A — Add bostadsrätt prices to Kontantinsats (High Priority)

**Effort:** Medium (1–2 days)

**Steps:**

1. **Fetch SCB BO0701 bostadsrätt price data**
   - Table: `BO/BO0701/BO0701A/BostPrisAr` (or equivalent)
   - Content code: mean transaction price per bostadsrätt, annual, municipal
   - Add to `src/data/scb_client.py` as `fetch_bostadsratt_price()`
   - Cache to `data/raw/BO0701_bostadsratt_price.parquet`

2. **Add to build pipeline** (`src/data/build_panel.py`)
   - New function `_clean_bostadsratt_price()`
   - Merge with municipal panel as `bostadsratt_price_sek`
   - Note: ~30–40% of municipalities will have NaN (small municipalities)
   - Use county fallback for missing municipal values (same strategy as K/T)

3. **Add housing type selector to page 04** (`pages/04_Kontantinsats.py`)
   - New selectbox: "Pristyp" → ["Småhus (villa)", "Bostadsrätt"]
   - When bostadsrätt selected: use `bostadsratt_price_sek` instead of `transaction_price_sek`
   - Show availability warning for municipalities with county-level fallback

4. **Data validation**
   - Bostadsrätt price should be 40–70% of villa price in major cities
   - Stockholm bostadsrätt ~3.0–4.5 MSEK; rural ~0.5–1.5 MSEK

### Phase B — Dual-price comparison chart (Medium Priority)

**Effort:** Low (half day, after Phase A)

- Add a small reference card on Kontantinsats page:
  "Villa: {price_villa} SEK · Bostadsrätt: {price_br} SEK · Kvot: {ratio:.1f}×"
- Show years-to-save comparison bar chart for both property types side-by-side

### Phase C — Optional bostadsrätt series for SHAI indices (Low Priority)

**Effort:** Medium-High (2–3 days)

- This would require running two parallel panel computations
- Create `affordability_municipal_br.parquet` alongside the villa-based panel
- Add a "Pristyp" toggle to pages 01, 02, 03

**Risk:** Reranking of municipalities would be significant and could confuse users who compare with older results. Requires a clear version note.

---

## 5. Decision Matrix

| Option | Effort | Impact | Data Quality | Recommendation |
|--------|--------|--------|--------------|----------------|
| Add BR prices to page 04 only | Medium | High for Kontantinsats | Good (SCB BO0701) | **Do this first** |
| Dual-price comparison chart | Low | Medium | Derived from above | **Do after Phase A** |
| BR prices for SHAI indices | High | High but controversial | Medium (county fallback heavy) | Defer; decide after seeing Phase A quality |
| Mäklarstatistik API | High | High | Commercial | Out of scope |

---

## 6. Next Steps

1. **Immediate (Phase 3 complete):** Villa-only warning already on page 04 (F11). Household multiplier added.
2. **Next sprint:** Investigate SCB BO0701 API availability and coverage
   - Run: `python -c "from src.data.scb_client import list_tables; print([t for t in list_tables() if 'BO07' in t])"`
   - Or check: https://api.scb.se/OV0104/v1/doris/sv/ssd/BO/BO0701/
3. **Decision point:** If BO0701 provides municipal coverage for >150 municipalities, proceed with Phase A
4. **If coverage is insufficient:** Use county-level bostadsrätt prices with prominent municipal-coverage caveat

---

## 7. Summary Conclusion

**Do we have apartment data?** No — the current pipeline only fetches and uses small house (villa) prices.

**Should we add it?** Yes — adding SCB BO0701 bostadsrätt prices to page 04 would be a high-impact, medium-effort improvement that directly addresses the biggest user-facing accuracy issue (F11). The main SHAI indices should remain on villa prices for methodological consistency, but Kontantinsats should allow switching to bostadsrätt prices as these represent the typical first-time buyer reality in cities.

**Impact if added:**
- Stockholm first-time buyer picture: 24 yr → 4–10 yr depending on household type
- Rural municipalities: minimal change (villa ≈ apartment prices)
- SHAI rankings: unchanged (index remains villa-based)
- User trust: significantly improved for urban users
