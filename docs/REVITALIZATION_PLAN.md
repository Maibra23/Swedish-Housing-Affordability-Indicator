# SHAI Revitalization Plan

Resumable work plan for bringing the Swedish Housing Affordability Indicator back to a
correct, deployable, and visually consistent state after five months of drift.

**Created:** 2026-09-15
**Baseline commit:** `1b17dab` (fix: sidebar always visible — hide toggle buttons, responsive on mobile)
**Branch:** `revitalization/phase-1` — **not `main`.** All Phase 1 work lives here.
**Status:** IN PROGRESS — Phases 1 and 2 complete · T4.4, T3.1 done · 19 / 34 tasks
**Current phase:** Phase 3 · next task **T4.1** (now unblocked) — then §0 on the missing reference repos
**Test suite:** 323 passed, 0 failed, 1 skipped (renders now inside the suite)

---

## 0. Working state — read this first

Everything below assumes you are set up as follows. Two of these cost real time this session.

| | |
|---|---|
| **Branch** | `revitalization/phase-1`. `main` is five commits behind and still has the 2024 defects. `git checkout revitalization/phase-1` before anything. |
| **Python** | **`python3.11`**, always. The machine's default `python3` is 3.9 and cannot import `tomllib`, which `src/ui/sidebar.py` needs. Under 3.9 `pytest` still reports green — it silently fails to collect the UI tests, so a 3.9 pass is not evidence. |
| **Test command** | `python3.11 -m pytest tests/ -q` → expect **117 passed, 0 failed, 1 skipped**. |
| **Render check** | `streamlit.testing.v1.AppTest` driven from `app.py` with `switch_page` — 6 pages × 11 years + landing = **67 renders**, all clean. Driving a page as its own entrypoint fails on `st.page_link("app.py")`; that is an AppTest artifact, not a defect. |
| **Refresh** | `python3.11 -c "import sys;sys.path.insert(0,'.');from scripts.refresh_data import step_compute_indices;step_compute_indices()"` rebuilds the affordability parquets **and** the provenance artifact. No API calls. |

### ⚠ This file gets overwritten from outside the session

Edits applied to this document have been observed **reverting**: a header line, a
progress-table status cell and an entire session-log row present in `git show HEAD` vanished
from the working tree, and the markdown tables came back re-aligned with padded cells the
committed version does not have. No Claude Code hooks are configured, so it is external —
most likely this file is open in an editor with format-on-save writing a stale buffer.

**Consequences:** verify edits to this file immediately after making them, and commit without
delay. If content goes missing, `git checkout HEAD -- docs/REVITALIZATION_PLAN.md` and
re-apply the whole post-commit set in one pass rather than patching a half-clobbered file.
Any script editing these tables must match table rows on the first cell (`startswith`/regex),
never on an exact space count — `HEAD` is unpadded, the working tree may be padded.

### ⚠ Phase 3 cannot be done as written on this machine

Both reference repositories in §1 are macOS paths and **neither exists here**:

| Repo | Path in §1 | Status |
|---|---|---|
| Skattekraftspanelen | `/Users/Brook/Downloads/kommun-skattekraft-stress` | **absent** |
| KRI | `/Users/Brook/Desktop/Kommunal-Finansiell-Riskindikator` | **absent** |

Every Phase 3 task names Skattekraftspanelen's `src/ui/` as its primary reference, and D2's
whole rationale is *converging* on it. Seven of the twelve tasks borrow specific patterns
(T3.4–T3.9, T3.12); without the source, those would be reconstructions from prose — plausible,
and still not matching, which is the one outcome a convergence goal cannot accept.

Five tasks are genuinely self-contained and need no reference: **T3.1** (extract SHAI's own
Swedish copy), **T3.2** (normalise CSS names to `.shai-*`), **T3.3** (split `css.py`, 902
lines), **T3.10** (split `components.py`), **T3.11** (split `04_Kontantinsats.py`, 885 lines).

**T3.1 also unblocks T4.1**, which this plan calls its highest-value test. So the workable
order is T3.1 → T4.1, then stop and get the reference repo available before the visual tasks.

---

### Where the work stopped

**Phase 1 is complete.** T1.1–T1.10 are all `DONE`, with T4.2 and T4.5 landed early alongside
them. The app no longer presents a number it cannot support: risk classes are right way up,
every offered year renders, the vintage is the artifact's rather than the clock's, the map
scale comes from the data, both normalisation axes are settled, the one KPI that carried a
meaningless trend has lost it, and no displayed count or period is typed into the source.

Start at **T2.1** (runtime-only `requirements.txt`). Phase 2 has no blocked tasks; **O1** is
the only open decision and only T2.4 depends on it, with a documented default of `SKIPPED`.

---

## How to resume this work

If you are picking this up cold, read in this order:

1. **§1 Locked decisions** — settled; do not relitigate.
2. **§2 Open decisions** — must be answered before the tasks that depend on them.
3. **§3 Evidence** — the audit findings with file:line references. Every task traces to one.
   Findings **N**, **O**, **P** and **Q** were discovered *during* the work, not in the
   original audit; N and Q are the substantive ones and both concern orientation or
   distribution of the index.
4. **§4 Progress** — the single table showing where work stopped.
5. **`docs/OPEN_RISKS.md`** — hazards and pending decisions that outlive this plan.
   R1 (Version B re-bases on every refresh) and R7 (unpinned majors reach production)
   are both High and both currently held shut by a guard rather than fixed.
5. The phase section for the first task whose status is not `DONE`.

**What the tests now guard**, so you know what will catch you:

| File | Guards |
|---|---|
| `test_ranked_artifact.py` (15) | the artifact carries `z_*`/`rank_*`/`risk_*` for every year, with the orientation contract |
| `test_pages_no_recompute.py` (14) | no page re-derives a z-score, rank or risk class |
| `test_provenance.py` (18) | the vintage artifact matches the panel it describes |
| `test_year_range.py` (16) | the selector offers exactly the years the index can compute |
| `test_choropleth.py` (21) | the map's colour domain comes from data; the tile host is reachable |
| `test_normalization_convention.py` (16) | both normalisation axes (D5 window, D6 transform) |

Three of these assert against **executable source** via `tests/sourcetools.py`, which strips
comments and docstrings — prose explaining a fixed defect must not trip a guard against that
defect.

**Update protocol:** when a task completes, change its status marker in both the phase
section and the §4 progress table, and append a line to §9 Session log. Keep the header
`Status:` line in sync. Never mark a task `DONE` without the evidence its acceptance
criteria demands.

**Status markers:** `TODO` · `WIP` · `DONE` · `BLOCKED` · `SKIPPED`

---

## 1. Locked decisions

| # | Decision | Chosen | Rationale |
|---|----------|--------|-----------|
| D1 | Data vintage strategy | **Honest vintage, no forced refresh** | Composite index cannot move past 2024 regardless (see §3 Finding E). Make the app truthful first; refresh is a separate, gated task (T2.4). |
| D2 | UI design target | **Converge on Skattekraftspanelen** | It already uses SHAI's own `shai-` class prefix and `src/ui/` layout — it is the next generation of this design system, not a different one. Keeps Plotly. Borrow selected patterns from KRI. |
| D3 | Sequencing | **Correctness → deployment → UI → tests/docs** | Each phase independently shippable. The app stops serving wrong numbers before it gets re-skinned. |
| D4 | Shared design system package | **No — copy into SHAI, repos stay independent** | Zero Streamlit Cloud deployment risk, no cross-repo release coupling. Structure `src/ui/` so later extraction stays easy. |
| D5 | Normalisation **window** (answers O2) | **Within year for `z_*`; Version B's own construction stays pooled** | A and C ask "where does this kommun stand among its peers this year"; B asks "how much macro pressure is there now versus history". B's pooled level is the only time trend in the index — its panel mean runs −0.37 (2015) to +0.86 (2023), tracking the rate cycle. Within-year normalisation would pin that at zero every year and delete the signal B exists to measure. Finding G is resolved by documenting the difference as deliberate, not by erasing it. |
| D6 | Normalisation **transform** (answers O4) | **Log-transform A and C before z-scoring; B stays raw** | A and C are ratios of positive quantities, so log-normal. Z-scoring them raw put the ±0.67σ cut — quartiles *of a normal distribution* — on a variable whose normality is rejected at p < 6e-15 in every year, yielding a ≈19/51/30 split nobody chose. Under the log the variable is normal in all eleven years (p = 0.34–0.83) and the split is ≈23/48/28. B is a weighted sum of z-scores and goes negative in 1919 of 3190 rows, so a log is undefined for it. Monotonic, so **no rank changes**. See Finding Q. |

### Reference repositories

| Repo | Local path | Role |
|------|-----------|------|
| Skattekraftspanelen | `/Users/Brook/Downloads/kommun-skattekraft-stress` | **Primary UI/architecture target** (D2) |
| Kommunal Finansiell Riskindikator (KRI) | `/Users/Brook/Desktop/Kommunal-Finansiell-Riskindikator` | Source of `data_table.py`, contextual-help expanders, empirical map scale |

---

## 2. Open decisions

| # | Question | Blocks | Default if unanswered |
|---|----------|--------|----------------------|
| ~~O1~~ | **ANSWERED — run it.** Include the optional 2025 data refresh (T2.4)? Prices, unemployment and the price index have 2025; **income does not**, so the composite index stays at 2024 either way. | T2.4 only | `SKIPPED` — proceed without it. Phase 1 makes the app honest about 2024 regardless. |
| ~~O2~~ | **ANSWERED → D5.** **Normalisation window.** A and C are z-scored within year; B is pooled across the whole panel (Finding G). Unify on within-year? Note B's pooled level is what lets it carry a time trend — within-year normalisation *removes* that trend by construction, so this is a real trade-off, not a tidy-up. | **T1.8**, T4.1 | Within-year for all three, and document B's loss of trend in METHODOLOGY. |
| ~~O4~~ | **ANSWERED → D6.** **Normalisation transform.** `version_c` (and `version_a`) are ratios, so they are log-normal, not normal — yet they are z-scored raw and cut at ±0.67σ. Log-transform before z-scoring? See Finding Q for the measurements. Ranks do not change at all; 16 of 290 municipalities (6 %) change risk class, all one step toward the middle. B cannot be logged (it goes negative). | **T1.8**, T1.9, T4.1 | **Not defaulted — this one needs an answer.** Changing it alters every published `z_*`; leaving it keeps a ±0.67σ cut whose stated meaning the data does not support. |
| O3 | Migrate SCB client from PxWeb v1 to v2? v1 retires end-2026/2027; v2beta now answers HTTP 200. | Nothing in this plan | Out of scope here — track separately. |

---

## 3. Evidence — audit findings

Captured 2026-09-15. Each finding has a stable ID referenced by tasks.

### A. Ranked artifact is out of sync with the code that reads it — CRITICAL

`data/processed/affordability_ranked.parquet` carries `rank_a/b/c` but **no `z_*` and no
`risk_*`** columns, and spans all 11 years (3190 rows). `src/indices/normalize.py:normalize_and_rank()`
produces a *single-year* frame *with* those columns. The artifact was regenerated by a
different path; `normalize.py` is effectively dead code.

Fallout at `pages/01_Riksoversikt.py:60`:

```python
if selected_year == ranked["year"].iloc[0]:   # iloc[0] == 2014
    df_ranked = ranked.copy()                  # no risk_c column exists
```

Selecting 2014 silently no-ops the risk filter, forces `n_hog = 0`, and renders the
"Högrisk kommuner" KPI as 0 with a fabricated delta. Every other year takes the `else`
branch, which **re-implements normalize.py inline in the page** (`01_Riksoversikt.py:62-80`).

### N. Risk classes were inverted on the live app — CRITICAL (found during T1.1, FIXED)

Two further defects surfaced while fixing Finding A.

**N1 — inverted risk classes.** `src/indices/normalize.py` inverts the z-score for versions
A and C (`z = -z`) so that "higher z = worse" before cutting at ±0.67σ. The inline copy at
`pages/01_Riksoversikt.py:62-77` **omitted that inversion but reused the same bin labels.**
Because 2014 was the only year that read the artifact, every other year — including the
2024 default — rendered inverted:

| Kommun | version_c (higher = more affordable) | class before | class after |
|--------|--------------------------------------|--------------|-------------|
| Solna | 6,5 — among the least affordable | `lag` (green) | `hog` (red) |
| Sundbyberg | 7,0 | `lag` | `hog` |
| Stockholm | 8,1 | `lag` | `hog` |
| Åsele | 92,2 — the most affordable | `hog` (red) | `lag` (green) |
| Ragunda | 91,9 | `hog` | `lag` |

Class means before the fix: `lag` = 14,6 and `hog` = 56,9 — exactly reversed. The national
map was green over Stockholm and red over inland Norrland.

**N2 — inverted rank for version B.** `scripts/refresh_data.py` ranked the raw version value
`ascending=False` without inverting B, so rank 1 meant "most affordable" for A and C but
"least affordable" for B. Latent rather than user-visible: only `_c` columns reach the UI.
Fixed by the same change.

**N3 — the prose still stated the old orientation.** (Found during T1.2, FIXED.) T1.1 corrected
the classes but not the copy describing them. `pages/01_Riksoversikt.py` captioned the
distribution chart *"Högre z = bättre överkomlighet"* and its expander restated the cut as
*"grön (z ≤ −0,67) … röd (z > 0,67)"*. Both are backwards under the orientation contract:
`corr(z_c, version_c) = -1.0` on the 2024 artifact, so a **lower** z is the more affordable
municipality. The colours were already correct, so the chart rendered right while its own
legend told the reader to read it the other way round. This is precisely the class of defect
T4.1 (`test_copy_matches_artifacts.py`) exists to catch.

### O. `test_skane_worst_v_c` fails on data, not code — PRE-EXISTING (RESOLVED in T1.8)

`tests/test_validation.py:102` asserts Skåne (`12`) is among the five least affordable
counties under Version C. It is not: the five are `01, 09, 13, 04, 03`. Verified failing
against the pre-T1.1 artifact as well, so it is a stale expectation, not a regression.
**Resolved in T1.8.** The transform did not move it — a log is monotonic and this test compares
medians of the raw `version_c`. The expectation was drawn too tight: Skåne is the **6th** least
affordable of 21 counties, 0.7 index points behind Uppsala (36.5 vs 35.8) in a distribution
spanning 20.8 to 102.8. Rank 5 versus rank 6 at that margin is noise, not a claim about Swedish
housing. Renamed `test_skane_among_least_affordable_v_c`, asserting the least-affordable third —
the substantive claim worth defending.

### P. Metodologi page documents the superseded imputation rule — MEDIUM (found during T1.5, RESOLVED in T1.8)

`pages/06_Metodologi.py:247` records audit finding F9 as *"`is_imputed_income`-flagga;
**nolltillväxt** antagen"* — zero growth assumed. The pipeline does the opposite:
`src/data/build_panel.py:30` sets `IMPUTED_INCOME_GROWTH_RATE = 0.03` and the comment at
`:308` states plainly that *"Zero-growth was a pessimistic assumption per audit finding F9"* —
i.e. zero growth is the rule that F9 **replaced**. The methodology page documents the
behaviour that was removed.

**Resolved in T1.8.** Corrected in both places it appeared — `pages/06_Metodologi.py` and
`docs/METHODOLOGY_v2.md` — to state the 3 %/yr rule and note that imputed years are no longer
reachable from the UI at all. `docs/AUDIT_methodology_assumptions.md` still describes zero
growth, correctly: it is a dated audit record of the state that prompted the change, and
rewriting it would falsify the record.

### B. Two of seven selectable years have no data — CRITICAL

`src/ui/sidebar.py:27` — `YEAR_RANGE = range(2020, date.today().year + 1)` → 2020–2026.
Affordability data ends at 2024. Selecting 2025 or 2026 reaches `st.stop()` with
"Inga data tillgängliga" on every page. The panel forward-fills 2025–26 income at +3 %/yr
but leaves `transaction_price_sek` and `unemployment_rate` as `NaN`, so nothing downstream
can compute.

### C. False freshness claim — CRITICAL

`src/ui/sidebar.py:144` prints `Senast uppdaterad: {date.today()}` regardless of data
vintage. A visitor today reads "updated 2026-09-15" over 2024 data.

### D. Map defects already fixed in KRI — CRITICAL

- `src/ui/choropleth.py:211` uses `tiles="CartoDB.PositronNoLabels"`. KRI's design doc §9.3
  records that `basemaps.cartocdn.com` now watermarks anonymous requests with
  "API KEY REQUIRED"; KRI moved to Esri `World_Light_Gray_Base`.
- `src/ui/choropleth.py:201` hardcodes `vmin=-2.5, vmax=2.5`. KRI §9.3: *"A fixed ±2.5
  domain is wrong… it compressed all 290 municipalities into one shade."* KRI replaced it
  with empirical 25th/75th-percentile stops.

  Measured on SHAI during T1.7, the fault is **worse than KRI's and differently shaped**.
  SHAI's `z_c` is strongly left-skewed — across the eleven years it reaches −6.10 but never
  exceeds +1.47 — so the fixed domain fails at both ends at once:

  | | Effect |
  |---|---|
  | Green end | **clips** 104 municipality-years. In 2024 the ten most affordable municipalities all render `#2e7d5b`: Åsele (−3.76) and Överkalix (−3.08) are the same pixel colour. |
  | Red end | **wastes** the top 43 % of the ramp. Solna, the least affordable municipality in Sweden, renders mid-amber `#daa94f` because +1.42 is only 57 % of the way to `vmax=2.5`. |

  So the map understated the extremes in both directions simultaneously.

### E. Upstream data availability — probed live 2026-09-15

All APIs answer. The panel is **ragged**: income is the binding constraint.

| Source | Endpoint | Max year available | SHAI ships |
|--------|----------|--------------------|-----------|
| Income | SCB `HE/HE0110/HE0110G/TabVX4bDispInkN` | **2024** | 2024 |
| Småhus price | SCB `BO/BO0501/BO0501B/FastprisSHRegionAr` | **2025** | 2024 |
| Bostadsrätt price | SCB `BO/BO0501/BO0501C/FastprisBRFRegionAr` | **2025** | 2024 |
| Price index | SCB `BO/BO0501/BO0501A/FastpiPSLanAr` | **2025** | 2024 |
| Population | SCB `BE/BE0101/BE0101A/BefolkningNy` | **2024** | 2024 |
| CPI | SCB `PR/PR0101/PR0101A/KPI2020M` | **2026M08** | 2026 |
| Unemployment | Kolada v3 KPI `N03937` | **2025** | 2024 |
| Policy rate | Riksbanken SWEA `SECBREPOEFF` | **live (2026-09-15 = 1,75 %)** | 2026 |

All three formulas require `median_income`, so the composite index cannot exceed **2024**.
This is exactly the `panel_max_year` vs `complete_case_max_year` distinction that
Skattekraftspanelen's `src/provenance.py` exists to express.

Incidental: SCB PxWeb **v2beta now returns HTTP 200**, contradicting `docs/DEVIATIONS.md` D1
which recorded all v2 data endpoints as 404. See O3.

### F. Risk class is a fixed split by construction — HIGH

*(Corrected 2026-09-15 during T1.7. The original wording of this finding was itself wrong;
see Finding Q.)*

`src/indices/normalize.py` cuts within-year z-scores at ±0.67σ. The national high-risk count
is therefore near-constant, yet Riksöversikt renders it with a year-over-year delta arrow as
though national affordability improved or worsened. The number cannot carry that meaning —
that part stands, and T1.9 remains correct.

**What was wrong:** this finding claimed the split is "25/50/25 by construction" with the
high-risk count "pinned near 72". ±0.67σ are the quartiles *of a normal distribution*, and
`z_c` is not normal. Measured across all eleven years the split is **≈19 / 51 / 30** and the
high-risk count sits at **83–89, never near 72**. The claim was theory, not measurement. See
Finding Q.

### Q. The index is z-scored on a raw ratio, which is not normal — HIGH (found during T1.7)

Chasing the map's colour domain exposed something larger than the map. `version_c` is
`income / (price × real_rate)` — a **ratio of positive quantities**, which is log-normal, not
normal. `normalize.py` z-scores it directly and then cuts at ±0.67σ, a boundary whose meaning
depends entirely on the normality it does not have.

Measured on the committed artifact, every year 2014–2024:

| | raw `version_c` | `log(version_c)` |
|---|---|---|
| Skewness | **+1.26 … +1.92** | −0.17 … +0.15 |
| D'Agostino–Pearson normality | **rejected, p < 6e-15 every year** | **not rejected, p = 0.34 … 0.83 every year** |

The log transform does not merely improve things; it makes the variable textbook normal in all
eleven years independently. Same for `version_a`. Three consequences:

1. **The class split is asymmetric by accident.** ≈30 % of municipalities are labelled *hög
   risk* and only ≈19 % *låg risk*. Nobody chose that asymmetry — it is the left tail of the
   inverted ratio falling past −0.67σ. Under a log transform the split moves to ≈23 / 48 / 28.
2. **The UI's stated interpretation is unsound.** Riksöversikt captions the histogram
   "Z-poäng = standardavvikelser från riksgenomsnittet". On a variable this skewed, a standard
   deviation does not carry the meaning that sentence implies, and the mean is not the typical
   municipality: 2024's mean `version_c` is 28.6 against a median of 26.8.
3. **The map fix was the right shape anyway.** T1.7 anchors the colour domain on empirical
   percentiles rather than σ multiples, so the map is already robust to this. Had it been left
   on ±2.5σ this finding would have made it worse still.

**Blast radius is small and precisely bounded.** A log transform is monotonic, so **`rank_a`,
`rank_b` and `rank_c` do not change at all** — verified identical on 2024. Only `z_*` and
`risk_*` move, and only for **16 of 290 municipalities (6 %)**, all of them one step toward the
middle:

| Move | Count | Examples |
|---|---|---|
| `hog` → `medel` | 5 | Staffanstorp, Håbo, Strömstad, Skövde, Tjörn |
| `medel` → `lag` | 11 | Ovanåker, Torsås, Dals-Ed, Arjeplog, Lycksele |
| unchanged | 274 | — |

**Version B does not fit this pattern and must be handled separately.** It is a weighted sum of
z-scores, not a ratio: it takes negative values in 1919 of 3190 rows, so a log is undefined for
it. It is also right-skewed (+1.4 … +1.7) *and* pooled across the whole panel, so its
within-year mean drifts from −0.37 (2015) to +0.86 (2023) — that drift is Finding G, and for B
it is arguably the point, since B is meant to carry a time trend.

**How to manage it:** this is a methodology change, not a defect fix — it changes every
published `z_*` and the class of 16 municipalities. It is therefore a decision (**O4**), not a
task, and it belongs to **T1.8**, which already owns the normalisation convention. T1.8's scope
is widened to cover the transform as well as the window. Do not change the transform ahead of
that decision: the numbers are currently self-consistent, and a partial change would be worse
than either endpoint.

### G. Two incompatible normalisation conventions — HIGH

`src/indices/affordability.py:_zscore` pools **across the whole panel** (all years) for
Version B; `src/indices/normalize.py` z-scores **within year**. Version B's level is not
comparable to A's and C's.

### H. Hardcoded constants that drift silently — HIGH

`290` appears in 9 locations (`app.py:43,68`; `pages/01_Riksoversikt.py:92,140,145`;
`pages/04_Kontantinsats.py:90,114`; `src/ui/components.py:204,244,359,430`).
`2014–2024` is hardcoded in the hero stat strip. `_LAST_ACTUAL_DATA_YEAR = 2024` at
`src/ui/sidebar.py:31`.

### I. Deployment fragility — HIGH

- **No `requirements.txt`.** Streamlit Community Cloud looks for it first. The
  `[tool.poetry] package-mode = false` block in `pyproject.toml` (commit `f744df8`) is a
  scar from that fight; setuptools and Poetry config now coexist.
- **Build-only dependencies ship into the runtime.** `prophet`, `pmdarima`, `statsmodels`
  and `requests` sit in `[project.dependencies]`, but **no page imports them** — pages read
  pre-computed `forecast_*.parquet`. Prophet pulls cmdstanpy; pmdarima needs compilation
  and breaks on NumPy 2.x. Slow, failure-prone cold start for zero runtime benefit.
- `README.md` troubleshooting tells the reader to uninstall `streamlit-echarts`, which is
  not a dependency. Dead advice.

### J. Test coverage far below the 80 % project rule — MEDIUM

Three test files: package-import smoke tests, data validation, one real-rate test. No
page-render tests, no label tests, no copy-matches-data test. Skattekraftspanelen has 23
test files including `test_copy_matches_artifacts.py`, which re-derives every number quoted
in UI prose from the artifacts and asserts it appears verbatim.

### K. Files over the project's own limits — MEDIUM

`pages/04_Kontantinsats.py` = 880 lines and `src/ui/css.py` = 902 lines, both over the
800-line maximum. `src/ui/components.py` = 434 lines mixes generic components with
landing-page-only ones.

### L. Documentation duplicated and partly false — MEDIUM

17 files, 6,933 lines, with four superseded v1/v2 pairs both still present:
`METHODOLOGY.md`+`METHODOLOGY_v2.md`, `PLAYBOOK.md`+`PLAYBOOK_v2.md`,
`prompts.md`+`PROMPTS_v2.md`, `patch_post_day2.md`+`PATCH_POST_DAY2_v2.md`.

`docs/DESIGN_SYSTEM.md` §10 states the map is *"Plotly `go.Scattergeo` … avoids shipping
GeoJSON for 290 municipalities"* — but commit `4f98a23` moved it to Folium and
`data/geo/kommuner.geojson` is committed. The design doc documents a map that no longer exists.

### M. UI generation gap — the core of D2

Skattekraftspanelen already uses the `shai-` CSS prefix and the
`src/ui/{css,components,sidebar,chart_theme,labels,filters}.py` layout.

| Capability | KRI | Skattekraftspanelen | SHAI |
|---|---|---|---|
| `.shai-explanation` — prose under every bare number | — | yes | **no** |
| `.shai-help` + `help_badge(*terms)` glossary | expanders | yes | **no** |
| `.shai-vintage` data-vintage badge | — | yes | **no** |
| `src/ui/labels.py` centralised Swedish copy | in `config.py` | yes, 196 keys | **no, inline** |
| `src/provenance.py` — no hardcoded years | — | yes | **no** |
| `src/ui/filters.py` shared filter logic | — | yes | **no, duplicated** |
| Shared table component | yes (`data_table.py`) | — | **no, per-page HTML** |
| "Om kartan / Om grafen" expanders | yes | yes | **no** |
| Empirical-percentile map scale | yes | yes | **no, fixed ±2.5** |

SHAI's CSS still mixes KRI-era names (`.sidebar-brand`, `.brand-mark`, `.riskklass-*`,
`.nav-section`, `.lp-*`) with newer `.shai-*` ones. Skattekraftspanelen normalised
everything to `.shai-*`.

---

## 4. Progress

| Task | Title | Phase | Status |
|------|-------|-------|--------|
| T1.1 | Regenerate ranked artifact through `normalize.py` | 1 | **DONE** |
| T1.2 | Remove inline z/rank/risk recomputation from pages | 1 | **DONE** |
| T1.3 | Add `src/provenance.py` + provenance artifact | 1 | **DONE** |
| T1.4 | Drive `YEAR_RANGE` from provenance; kill dead years | 1 | **DONE** |
| T1.5 | Replace `date.today()` with real data vintage | 1 | **DONE** |
| T1.6 | Fix map basemap (CARTO → Esri) | 1 | **DONE** |
| T1.7 | Fix map colour domain (fixed ±2.5 → empirical percentiles) | 1 | **DONE** |
| T1.8 | Unify normalisation convention across A/B/C (window **and** transform) | 1 | **DONE** |
| T1.9 | Reframe the risk-class KPI (drop meaningless YoY delta) | 1 | **DONE** |
| T1.10 | Derive hardcoded `290` / `2014–2024` from data | 1 | **DONE** |
| T2.1 | Add runtime-only `requirements.txt` | 2 | **DONE** |
| T2.2 | Split build-only deps into optional group; clean `pyproject.toml` | 2 | **DONE** |
| T2.3 | Fix README troubleshooting + deployment docs | 2 | **DONE** |
| T2.4 | **OPTIONAL (O1)** refresh component series to 2025 | 2 | **DONE** |
| T2.5 | Verify clean-environment deploy | 2 | **DONE** |
| T3.1 | Add `src/ui/labels.py`; extract all Swedish strings | 3 | **DONE** |
| T3.2 | Normalise all CSS classes to `.shai-*` | 3 | TODO |
| T3.3 | Split `css.py` (902 lines) into token/layout/component modules | 3 | TODO |
| T3.4 | Add `.shai-explanation` under every bare number | 3 | TODO |
| T3.5 | Add `help_badge()` glossary component | 3 | TODO |
| T3.6 | Add `.shai-vintage` badge component | 3 | TODO |
| T3.7 | Add `src/ui/filters.py`; de-duplicate page filter logic | 3 | TODO |
| T3.8 | Add shared `src/ui/data_table.py` (KRI pattern) | 3 | TODO |
| T3.9 | Add "Om kartan / Om grafen" contextual expanders | 3 | TODO |
| T3.10 | Split `components.py`; extract landing components | 3 | TODO |
| T3.11 | Split `04_Kontantinsats.py` (880 lines) | 3 | TODO |
| T3.12 | Align `.streamlit/config.toml` with Skattekraftspanelen | 3 | TODO |
| T4.1 | `test_copy_matches_artifacts.py` | 4 | TODO |
| T4.2 | `test_provenance.py` | 4 | **DONE** (landed early, with T1.3) |
| T4.3 | `test_labels.py` | 4 | TODO |
| T4.4 | `test_pages_render.py` | 4 | **DONE** (pulled forward) |
| T4.5 | `test_choropleth.py` | 4 | **DONE** (landed early, with T1.6/T1.7) |
| T4.6 | Delete superseded docs; consolidate | 4 | TODO |
| T4.7 | Rewrite `DESIGN_SYSTEM.md` to match shipped code | 4 | TODO |

---

## 5. Phase 1 — Correctness

**Goal:** the app stops presenting wrong or unsupportable numbers.
**Exit criterion:** every year offered in the sidebar renders; no displayed number is
fabricated, stale-but-labelled-fresh, or structurally incapable of the meaning assigned to it.
**Shippable:** yes, independently.

TDD applies throughout: write the failing test first, confirm it fails against the current
tree, then implement.

---

### T1.1 — Regenerate the ranked artifact through `normalize.py` · DONE

**Fixes:** Finding A
**Files:** `src/indices/normalize.py`, `data/processed/affordability_ranked.parquet`, `scripts/refresh_data.py`

The committed artifact and the code that produces it disagree. Decide the contract first:
the artifact should carry **all years** (pages need historical risk classes) **with** `z_*`
and `risk_*` columns. That means `normalize_and_rank()` must gain a per-year grouped mode
rather than collapsing to a single year.

**Steps**
1. Failing test `test_ranked_artifact_has_risk_columns` asserting `z_a/z_b/z_c` and
   `risk_a/risk_b/risk_c` exist in the committed parquet. Confirm it fails now.
2. Change `normalize_and_rank()` to group by `year` and emit all years.
3. Regenerate the artifact and commit it.
4. Confirm `scripts/refresh_data.py` invokes this path, so a future refresh reproduces it.

**Acceptance**
- [x] `affordability_ranked.parquet` has 3190 rows, 11 years, and all nine `z_*`/`rank_*`/`risk_*` columns
- [x] `normalize.py` is the only producer of these columns anywhere in the tree (`scripts/refresh_data.py` now calls it; the page path is removed in T1.2)
- [x] `tests/test_ranked_artifact.py` — 15 tests, all passing (11 failed before the fix)

**Outcome:** the inline ranking in `scripts/refresh_data.py:114-121` was the source of
the drift. It has been replaced by a call to `normalize_and_rank()`. `normalize.py` was
rewritten to score every year rather than collapsing to one, and it now documents the
orientation contract. See Finding N — the fix corrected a live inverted-risk defect.

---

### T1.2 — Remove inline z/rank/risk recomputation from pages · DONE

**Fixes:** Findings A, N3
**Files:** `pages/01_Riksoversikt.py`, NEW `tests/test_pages_no_recompute.py`
**Depends on:** T1.1

Delete the `if selected_year == ranked["year"].iloc[0] / else` block entirely and read the
selected year straight from the ranked artifact.

**Acceptance**
- [x] No page computes a z-score, rank or risk class
- [x] `grep -rn "0.67\|rank(method" pages/` returns nothing
- [x] Selecting **2014** shows a working risk filter and a non-zero "Högrisk kommuner" count —
  verified at the data layer (2014: 89 `hog` / 145 `medel` / 56 `lag`, filter returns 89).
  Not yet reachable through the UI: the selector starts at 2020 until **T1.4**.

**Outcome:** four changes, three of them beyond the block the task named.

1. The `if/else` recompute and the second inline re-scoring of the previous year in the KPI
   block are gone. `mun_year` / `mun_prev` are now plain year slices of the ranked artifact,
   and the page no longer loads `affordability_municipal.parquet` at all — every column it
   reads is present on `affordability_ranked.parquet`.
2. The distribution histogram was still cutting the z-scale at a locally hardcoded ±0.67 to
   pick its colours. It now groups on the artifact's own `risk_c` column, so the chart cannot
   disagree with the KPI above it.
3. **Finding N3** — the chart caption and expander stated the orientation backwards. Corrected
   to "Lägre z = bättre överkomlighet", and the expander no longer restates the numeric
   boundary; that detail lives in `normalize.py`'s docstring, which is its only correct home.
4. `tests/test_pages_no_recompute.py` (14 tests) asserts at source level that no page ranks,
   cuts, builds a cross-sectional z-score, assigns a `z_*`/`rank_*`/`risk_*` column, or
   imports `indices.normalize`. Source-level because the defect is structural — a second copy
   of this logic anywhere is free to drift from the first.

One test was written too broadly at first and flagged `03_Kommun_djupanalys.py:259`, which
computes a coefficient of variation over a single municipality's own time series. That is a
descriptive statistic, not a cross-sectional score, and is legitimate; the test was narrowed
rather than the page changed.

---

### T1.3 — Add `src/provenance.py` and the provenance artifact · DONE

**Fixes:** Findings B, C, H
**Files:** NEW `src/provenance.py`, NEW `data/processed/data_provenance.json`, `scripts/refresh_data.py`
**Reference:** `/Users/Brook/Downloads/kommun-skattekraft-stress/src/provenance.py` (96 lines)

Port the pattern. The artifact must record, per source: `min_year`, `max_year`,
`n_regions`; plus top-level `generated_at`, `panel_max_year`, `complete_case_max_year`,
`balanced`, and a `note` explaining the ragged tail (§3 Finding E).

Public API: `load_provenance()`, `panel_max_year()`, `complete_case_max_year()`,
`source_coverage()`, `n_kommuner()`, `first_year()`. Cache with `lru_cache`. Raise
`FileNotFoundError` with a clear message if the artifact is missing — its absence means the
pipeline never ran.

**Acceptance**
- [x] `complete_case_max_year()` returns `2024`
- [x] `panel_max_year()` returns `2026`
- [x] `scripts/refresh_data.py` writes the artifact on every run
- [x] Artifact is committed

**Outcome:** `src/provenance.py` (359 lines) holds both the reader API and the builder, so the
definition of "complete case" exists once. Public API as specified, plus `generated_at()` for
T1.5. `load_provenance()` is `lru_cache`d and raises `FileNotFoundError` naming the command
that regenerates it; `source_coverage()` deep-copies so a caller cannot corrupt the cache.

The load-bearing detail is **income imputation**. `build_panel` forward-fills `median_income`
to 2026 at +3 %/yr and flags those rows with `is_imputed_income`, so a naive `max_year` on the
column reads 2026 and `complete_case_max_year` would have come out at 2026 — the exact false
freshness this task exists to remove. The builder excludes imputed rows when deciding a
source's real window, which is what puts income's `max_year` at 2024 and pins the complete
case there.

Recorded coverage, all 290 regions: income / prices / unemployment / population / K-T 2024;
price index 2025; policy rate and CPI 2026. `balanced: false`.

Writing happens inside `step_compute_indices()` rather than as its own step, so it cannot be
skipped while the artifacts it describes are rebuilt. Verified by running the step end to end:
all four affordability parquets regenerated **byte-content-identical** to the committed
versions (`assert_frame_equal` passes on each), so the provenance wiring introduced no data
change — they were reverted to keep the change set clean.

`tests/test_provenance.py` (18 tests) satisfies **T4.2** in full and is marked there.

---

### T1.4 — Drive `YEAR_RANGE` from provenance · DONE

**Fixes:** Finding B
**Files:** `src/ui/sidebar.py`, NEW `tests/test_year_range.py`
**Depends on:** T1.3

Replace `range(2020, date.today().year + 1)` and `_LAST_ACTUAL_DATA_YEAR = 2024` with values
read from provenance. The selector must end at `complete_case_max_year()`.

**Acceptance**
- [x] 2025 and 2026 no longer appear in the year selector
- [x] Every offered year renders every page without hitting `st.stop()`
- [x] No literal year remains in `sidebar.py`

**Outcome:** `YEAR_RANGE = list(range(first_year(), complete_case_max_year() + 1))` → **2014–2024**,
both ends from provenance. The range *widened* as well as narrowing: it dropped the two dead
years at the top and picked up 2014–2019, which the index has always covered but the selector
never offered. This is also what finally makes T1.2's 2014 criterion reachable through the UI.
`_LAST_ACTUAL_DATA_YEAR` is gone; `default_year()` is now just the last offered year.

Verified by rendering **every page at every offered year** with `streamlit.testing.v1.AppTest`
— 6 pages × 11 years plus the landing page, 67 renders, no exception and no `st.stop()`. The
first attempt drove each page as its own entrypoint and failed on `st.page_link("app.py")`;
that is an AppTest artifact, not an app defect, and the check was redone through `app.py` with
`switch_page`.

`tests/test_year_range.py` re-derives the range from the artifacts the pages actually read, so
adding a year of data moves the selector with no code edit and forgetting to cannot leave a
dead year on screen. The no-literal-year assertion runs against **executable source** —
comments and docstrings are stripped by `ast`/`tokenize` — because prose recording the old
behaviour cannot put a dead year in the selector. Mutation-checked: re-introducing a literal
year in code, a literal year in displayed markup, or `date.today()` in the footer is caught by
the stripped-source assertions in all three cases.

---

### T1.5 — Replace `date.today()` with the real data vintage · DONE

**Fixes:** Finding C
**Files:** `src/ui/sidebar.py`, `pages/01_Riksoversikt.py`, `tests/test_year_range.py`
**Depends on:** T1.3

The footer must show when the **data** was generated (from `generated_at`), never when the
page was rendered. Also remove or correct the `Inkomst 2025–2026: modellberäknad (+3%/år)`
note — once T1.4 lands those years are unreachable from the UI, so the note is misleading.

**Acceptance**
- [x] `grep -n "date.today()" src/ui/sidebar.py` returns nothing in user-facing output
- [x] Footer states the artifact's generation date
- [x] The forward-fill note is gone or accurately scoped

**Outcome:** the footer reads `Data uppdaterad: {data_vintage()}`, parsed from the artifact's
`generated_at`. `footer_html()` is split out of `render_sidebar()` so the vintage can be
asserted without a Streamlit runtime. The `date` import is gone entirely.

`generated_at` currently happens to be today's date, so an equality assertion cannot on its own
distinguish "reads the artifact" from "reads the clock". Demonstrated directly instead: pointed
the module at an artifact stamped `2024-03-11` and the footer rendered
`Data uppdaterad: 2024-03-11` on a machine whose clock says 2026-09-15.

The sidebar's forward-fill note is deleted rather than rescoped — it described a state the UI
can no longer enter. The same applies to the `Imputerat inkomstår` banner at
`01_Riksoversikt.py:83-89`, which additionally hardcoded "2024" in its prose; removed, with
`test_no_offered_year_carries_imputed_income` pinning the invariant that makes it dead.

Two similar blocks remain at `02_Lan_jamforelse.py:55-57` and `03_Kommun_djupanalys.py:148-149`.
Both are data-driven, so they correctly render nothing and mislead no one — left in place rather
than widening this change into pages these tasks do not name. Sweep them in Phase 3.

**Found in passing:** `06_Metodologi.py` documents the *superseded* imputation rule. Recorded as
**Finding P**; not fixed here.

---

### T1.6 — Fix the map basemap · DONE

**Fixes:** Finding D
**Files:** `src/ui/choropleth.py:211`
**Reference:** `/Users/Brook/Desktop/Kommunal-Finansiell-Riskindikator/app/components/sweden_choropleth.py`

Replace `tiles="CartoDB.PositronNoLabels"` with the Esri `World_Light_Gray_Base` tile URL
plus its required attribution, matching KRI's `MAP_TILES` constant.

**Acceptance**
- [x] No request to `basemaps.cartocdn.com` — confirmed in the rendered map HTML
- [x] Map renders without an "API KEY REQUIRED" watermark
- [x] Attribution string present

**Outcome:** added a `MAP_TILES` constant mirroring KRI's, pointing at Esri
`World_Light_Gray_Base` with its required attribution, plus `name`, `max_zoom` and a
`background` fill injected behind the tiles so an unreachable host degrades to a clean canvas
rather than a black void. Rendered map HTML contains `arcgisonline.com` and `Esri`, and no
`cartocdn` anywhere.

**On the watermark, honestly:** the CARTO tile still answers `HTTP 200 image/png`, so the
response status cannot confirm or refute the claim — a watermark is painted into the pixels,
not signalled in the headers. Comparing the two tiles at the same location: the CARTO tile
carries **121 dark pixels** (<120 avg luminance) across an otherwise flat light basemap and
only 23 distinct colours, while the Esri tile has **0** dark pixels. Consistent with a small
text overlay, but it was not OCR'd, so treat this as corroboration rather than proof. The
change stands on its own regardless — it is what D2 convergence with KRI calls for, the Esri
tile serves `HTTP 200` over Sweden, and attribution is now explicit instead of implicit in a
folium shorthand.

---

### T1.7 — Fix the map colour domain · DONE

**Fixes:** Finding D
**Files:** `src/ui/choropleth.py:199-205`
**Depends on:** T1.1
**Reference:** KRI `_build_colormap()`

Replace `vmin=-2.5, vmax=2.5` with empirical stops: neutral pinned at the median, green and
red breakpoints at the selected year's 25th and 75th percentiles, domain spanning that
year's actual spread.

**Acceptance**
- [x] Colormap domain derives from the selected year's data, not constants
- [x] Visible differentiation across municipalities, not one flat shade
- [x] Legend caption states direction (which end is better)

**Outcome:** extracted `build_colormap(scores)`. Stops are placed on the data — ends at the
actual min and max, neutral at the median, green and red steps at the 25th and 75th
percentiles, the same quartiles that set `risk_c`, so the map and the ranking tables tell one
story. Seven stops, one per colour in `DIVERGING_SCALE`.

2024 domain is `[-3.76, +1.42]` against the old `[-2.5, +2.5]`. What changes on screen:

| Kommun | z_c | before | after |
|--------|-----|--------|-------|
| Åsele | −3.76 | `#2e7d5b` | `#2e7d5b` |
| Överkalix | −3.08 | `#2e7d5b` — *identical to Åsele* | `#408a67` |
| Stockholm | +1.33 | `#dcac56` | `#c16244` |
| Solna | +1.42 | `#daa94f` | `#b94a48` |

Clipping goes from 10 municipalities in 2024 (104 municipality-years overall) to **zero**, and
the deepest red is now actually reached by the least affordable municipality.

A degenerate spread — one municipality selected, or every score equal — produces repeated
stops, which branca rejects outright. `build_colormap` detects the non-monotonic case and falls
back to an evenly spaced domain instead of crashing the page; empty, single-value, all-equal
and NaN-bearing inputs are each covered by a test.

`tests/test_choropleth.py` (21 tests) satisfies **T4.5** in full and is marked there. Mutation-
checked: restoring the fixed ±2.5 domain makes `test_no_municipality_is_clipped` fail with the
10 clipped municipalities named.

---

### T1.8 — Unify the normalisation convention · DONE

**Fixes:** Findings G, Q, O — and settles the premise T1.9 rests on
**Files:** `src/indices/affordability.py:22-30,51-68`, `src/indices/normalize.py`,
`data/processed/affordability_*.parquet`, `tests/test_validation.py`, METHODOLOGY
**Unblocked 2026-09-15:** O2 → **D5**, O4 → **D6**.

Scope widened 2026-09-15 after Finding Q. There are **two** independent axes here, and they
were conflated as one:

| Axis | Question | Decision |
|---|---|---|
| **Window** | Within-year, or pooled across the panel? A and C are within-year, B is pooled. | O2 |
| **Transform** | Z-score the raw ratio, or its log? Raw fails normality at p < 6e-15 every year; the log passes in all eleven. | O4 |

A choice on one does not imply the other, and the ±0.67σ class boundary is only meaningful
once **both** are settled — it is a normal-distribution quantile being applied to whatever the
two choices produce.

**Why this is genuinely blocked rather than merely undecided.** Every other Phase 1 task fixed
something demonstrably wrong against a standard the project already held: an artifact that
disagreed with its producer, a selector offering years with no data, a footer printing the
render date. This one does not have that property. Both answers are defensible, they are not
reconcilable, and each changes numbers the app publishes:

- Choosing **within-year for B** deletes the only time trend in the index by construction.
  B's within-year mean currently runs −0.37 (2015) to +0.86 (2023), which is B doing its job
  as a macro-pressure measure. Normalising within year sets it to ~0 every year, permanently.
- Choosing **log** changes every `z_*` the app displays and moves 16 municipalities across a
  risk boundary — outward-facing numbers about named places.

Guessing would mean publishing a methodology nobody chose, which is the failure mode this whole
plan exists to correct. It is also **not blocking anything else**: T1.9 and T1.10 are
independent and can proceed first.

**Also resolve here, both waiting on the same decision:**

- **Finding O** — `test_skane_worst_v_c` has failed since before this work began. Whether Skåne
  belongs in the five least affordable counties depends on the convention chosen, so the
  expectation cannot be corrected until it is.
- **Finding P** — `06_Metodologi.py:247` documents the imputation rule that audit F9 replaced.
  Independent of O2/O4, but it lives in the methodology copy this task rewrites.

**Acceptance**
- [x] O2 and O4 both answered and recorded in §1 as locked decisions (**D5**, **D6**)
- [x] One documented convention on both axes, applied to A, B and C
- [x] METHODOLOGY states it, and states what B loses if the window changes
- [x] Artifacts regenerated; `rank_*` verified unchanged — asserted per version per year
- [x] Finding O resolved — `test_skane_among_least_affordable_v_c`, with the reason recorded
- [x] Finding P corrected in both `06_Metodologi.py` and `METHODOLOGY_v2.md`
- [x] `tests/test_ranked_artifact.py` still passes unchanged — all 15

**Outcome:** `LOG_TRANSFORMED = ("a", "c")` in `normalize.py`; `_log_for_scoring()` raises rather
than silently falling back if a version ever admits a non-positive value — a quiet fallback would
hide a formula change behind a slightly different class split.

Verified on the regenerated artifact:

| | before | after |
|---|---|---|
| `z_c` normality (D'Agostino–Pearson) | rejected, p < 6e-15 every year | not rejected, p = 0.34–0.83 every year |
| 2024 class split | 19.7 / 50.3 / 30.0 | **23.4 / 48.3 / 28.3** |
| 2024 class counts | 57 / 146 / 87 | **68 / 140 / 82** |
| `rank_a`, `rank_b`, `rank_c` | — | **identical, all versions, all years** |

`tests/test_normalization_convention.py` (16 tests) pins both axes. It asserts the transform by
**re-deriving** `z` from the artifact's own raw values rather than trusting a flag, includes a
guard-the-guard test that raw `version_c` really is non-normal so the premise cannot go stale
silently, and asserts B still carries a pooled trend so a future "tidy-up" cannot quietly
flatten it.

**Copy followed the convention.** The histogram caption read "Z-poäng = standardavvikelser från
riksgenomsnittet. Noll = rikssnitt." On a log scale `z = 0` is the geometric mean — 26.26 in
2024, which for a log-normal is the median (26.84), not the arithmetic mean (30.08). Updated to
say so: the Finding N3 lesson applied prospectively.

---

### T1.9 — Reframe the risk-class KPI · DONE

**Fixes:** Finding F
**Files:** `pages/01_Riksoversikt.py:110-150`

Because ±0.67σ on within-year z-scores produces a near-fixed split, the national high-risk
**count** is near-constant and its YoY delta is noise. (The split is **≈19 / 51 / 30**, not the
25/50/25 this originally claimed — see Findings F and Q. The correction does not weaken the
task: a near-constant count is exactly as unfit to carry a trend at 30 % as at 25 %. The
*labels* here must not quote a split figure, though, since O4 would move it.) Remove the delta arrow and relabel the
metric as a relative position. If an absolute measure of national affordability is wanted,
it must come from a level series (e.g. median Version C in real terms), not from the class counts.

**Acceptance**
- [x] No YoY delta on any count derived from the ±0.67σ cut — the previous-year count is
      not computed at all, so there is nothing left to subtract
- [x] Label and tooltip state that the class is a relative position within the year, with no
      split figure quoted (D6)
- [x] If a national trend KPI is added, it reads from a level series — asserted for every
      card on the row, not just this one

`tests/test_risk_kpi.py` (8). The name tracking closes over assignment: `delta = n_hog -
n_hog_prev` never mentions `risk_c` itself, and a guard stopping at the direct binding waved
through exactly the subtraction this task removes.

Widened once during the work. The count was read from `df_ranked`, the frame the risk pills
had **already filtered**, while the other three cards on the row read the unfiltered year —
so deselecting "Hög" rendered the national high-risk count as 0. A filter state was being
presented as a fact about Sweden. Now counted on `mun_year`.

---

### T1.10 — Derive hardcoded constants from data · DONE

**Fixes:** Finding H
**Files:** `app.py:43,68`, `pages/01_Riksoversikt.py:92,140,145`, `pages/04_Kontantinsats.py:90,114`, `src/ui/components.py:204,244,359,430`
**Depends on:** T1.3

Replace every literal `290` and `2014–2024` with provenance-derived values.

**Acceptance**
- [x] `grep -rn "\b290\b" app.py pages/ src/ui/` returns two hits, both comments
      explaining the fix — `tests/sourcetools.py` strips those, so the guard can tell
      prose from code
- [x] Hero stat strip period reads from provenance, as does its year *count* ("11 år")
- [x] Changing the data changes the displayed counts with no code edit — asserted
      behaviourally against a relabelled panel (277 municipalities, 2009–2019), not by
      reading the source

`tests/test_no_hardcoded_counts.py` (47). Nineteen literals across nine files. Scope
reached beyond the listed lines: `02_Lan_jamforelse.py` held the span as an empty-data
fallback, and `03`/`06` stated "11 årliga observationer (2014–2024)" — the period's
*length*, which drifts on the same refresh. Upstream source-coverage windows (`1981–2024`
for prices, `2011–2024` for income) are deliberately untouched: they describe what SCB
publishes, not what this index computes.

Two things the behavioural test caught that a source-level one could not.
`render_landing_steps` writes through `st.html`, not `st.markdown`, so the first capture
fixture returned an empty string and satisfied every "the old literal is absent"
assertion without rendering anything; the fixture now patches both sinks and fails on
empty output. And that same step's copy claimed values are z-standardised "över hela
panelen", which D5 made false — corrected to "inom varje år" while the literals were
being removed.

---

## 6. Phase 2 — Deployment hardening

**Goal:** the app installs and cold-starts reliably on Streamlit Community Cloud.
**Exit criterion:** a clean environment installs only what the running app needs, and the
app boots. — **MET.** Verified 2026-09-15: 39 distributions, no compilers, 67/67 renders
inside the clean venv. The remaining gap is confirmation on Streamlit Cloud itself, which
needs the account owner.
**Shippable:** yes, independently.

---

### T2.1 — Add a runtime-only `requirements.txt` · DONE

**Fixes:** Finding I
**Files:** NEW `requirements.txt`

Verified runtime imports across `app.py` and `pages/*.py`: streamlit, pandas, numpy, plotly,
folium, streamlit-folium, branca, pyarrow. Nothing else. Pin lower bounds.

**Acceptance**
- [x] `requirements.txt` exists with runtime deps only — eight packages
- [x] `prophet`, `pmdarima`, `statsmodels`, `requests` absent, and asserted *unreachable*
      from any page rather than merely absent from the file
- [ ] Fresh venv install from it can run `streamlit run app.py` — **deferred to T2.5**,
      which owns the clean-environment check

`tests/test_runtime_dependencies.py` (8). The expected set is not written down: it is walked
from `app.py` and `pages/*.py` through first-party code, so adding `import scipy` to a page
fails the suite until `requirements.txt` catches up. The plan's list was right, including
`pyarrow`, which appears in no import statement at all — `pd.read_parquet` needs it. That
entry has to justify itself in a test rather than sit there as folklore.

---

### T2.2 — Split build-only deps; clean `pyproject.toml` · DONE

**Fixes:** Finding I
**Files:** `pyproject.toml`

Move `prophet`, `pmdarima`, `statsmodels`, `requests` into
`[project.optional-dependencies] pipeline`. Remove the `[tool.poetry]` block — it exists only
to suppress a Poetry behaviour that setuptools does not need.

**Acceptance**
- [x] `[project.dependencies]` matches `requirements.txt`, asserted both ways
- [x] `pip install -e ".[pipeline]"` resolves and builds editable metadata (dry run on
      3.12; the full clean install is T2.5)
- [x] No Poetry configuration remains

`tests/test_packaging.py` (8). Three things widened this task.

**`requires-python` was `>=3.11,<3.12`.** Not a compatibility statement — the suite and all
67 renders pass on 3.12.10 — but it made `pip install -e .` refuse on the interpreter the app
is verified against, which would have blocked this task's own acceptance criterion. Now
`>=3.11`; the floor is real, because `sidebar.py` imports stdlib `tomllib`.

**`packages.find` said `where = ["src"]`**, describing a src-layout this project does not
use. It would have installed `ui`, `data` and `indices` as top-level packages that nothing
imports — every page and test spells them `src.*`. Now `where = ["."], include = ["src*"]`,
which resolves to exactly the seven `src.*` packages.

**Bare `pytest` could not collect the suite** — six files errored. It worked only under
`python -m pytest`, which injects the working directory, and §0 happens to document that
form. Editors and CI runners call the bare console script. `pythonpath` now carries both
`.` (for `src.provenance`, `tests.sourcetools`) and `src` (for `indices.real_rate`), and a
subprocess test runs the bare invocation so the fix cannot silently regress.

`pytest` also left `[project.dependencies]` — a test runner on the serving host is pure
install cost — and now sits in a `dev` extra with `pytest-cov` and `scipy`, the last of which
backs the normality tests behind D6 and was previously undeclared entirely.

---

### T2.3 — Fix README and deployment docs · DONE

**Fixes:** Finding I
**Files:** `README.md`, `docs/DEPLOYMENT.md`

Delete the `streamlit-echarts` troubleshooting note (not a dependency). Document the
two-tier install: `requirements.txt` for running, `.[pipeline]` for refreshing. State the
real data vintage and the ragged-panel constraint from §3 Finding E.

**Acceptance**
- [x] No reference to `streamlit-echarts` in `README.md` or `docs/DEPLOYMENT.md`
- [x] Both install paths documented in both files, and the bare `pip install -e .` that is
      neither path is gone
- [x] Data vintage and the income constraint stated, with Finding E's ragged-panel table
      reproduced in `DEPLOYMENT.md`

`tests/test_docs_install_paths.py` (16). The vintage assertions read `complete_case_max_year()`
and `n_kommuner()` from the artifact and require the prose to agree, so a refresh that moves
the data fails the docs rather than quietly outdating them — the same guard T1.10 put on the
UI. A stated `Python 3.x` must also satisfy `requires-python`, which caught `README.md`
promising 3.11 flat after T2.2 widened the floor to `>=3.11`.

Deliberately out of scope: `docs/prompts.md` and `docs/UX_UI_GAP_ANALYSIS.md` still mention
ECharts. Both are build-time artifacts slated for deletion in T4.6.

---

### T2.4 — OPTIONAL: refresh component series to 2025 · DONE

**Gated by:** O1 — **do not start until answered**
**Fixes:** partially addresses Finding E
**Files:** `data/processed/*.parquet`, `data/processed/data_provenance.json`
**Depends on:** T1.3, T2.2

Prices, price index and unemployment have 2025; income does not. A refresh advances the
component series and `panel_max_year` while `complete_case_max_year` — and therefore the
composite index — stays at 2024.

Requires the `[pipeline]` extras to actually install and run; `prophet` and `pmdarima` are
the risk. Verify before committing to this task.

**Acceptance**
- [x] The pipeline runs. Steps 1–3 completed; step 4 (forecasts) was killed by the OS for
      memory, not by a toolchain failure — see below, it is verifiably benign
- [x] Refreshed parquet files committed
- [x] `complete_case_max_year()` still returns 2024; the sidebar still offers 2014–2024
- [x] Provenance artifact reflects the new per-source max years

**The task found two defects and closing them is most of its value.**

**Kolada was never asked for 2025.** `fetch_unemployment` defaulted to
`end_year: int = 2024`, so a full refresh ran to completion and left unemployment a year
behind while every SCB series advanced on its own. Probed live: KPI N03937 has 2025, 312
municipal records, national rate 3.14 % against 2.946 % in 2024. The asymmetry was the tell —
`scb_client` requests *all* values of any dimension it does not override, and
`riksbanken_client` ends at `date.today()`; only Kolada carried a year literal, and only
Kolada stalled. This is Finding H one layer down: T1.10 removed hardcoded years from what the
app *displays*, this removes one from what the pipeline *fetches*, where the failure is
quieter — nothing renders wrong, the number is simply old. The ceiling now resolves at fetch
time. Over-asking is free: Kolada answers HTTP 200 with zero records for an unpublished year.
`tests/test_kolada_year_range.py` (7).

**An imputed year was re-basing published numbers.** With prices, kt-ratio and unemployment
all carrying 2025, the only missing input was income — which `build_panel` forward-fills — so
a 2025 row survived into the index for the first time (3190 → 3480 rows). It cannot be
displayed: the selector stops at `complete_case_max_year()`, still 2024. But
`compute_version_b` z-scores its components **pooled across every row it is handed**, so that
one invisible year shifted the pooled mean and standard deviation: `z_b` moved on all 3190
rows (max 0.051), 1816 changed `rank_b`, 19 changed `risk_b` class. A and C were untouched —
D5 made them within-year, which is exactly why this stayed hidden until now. `step_compute_indices`
now filters each panel through `complete_case()` before scoring. With that in place the
refresh is **purely additive**: `INDEX CONTRACT COLUMNS CHANGED: NONE`.
`tests/test_index_complete_case.py` (6).

**What actually changed in the data.** Component series gained 2025 (`transaction_price_sek`,
`kt_ratio`, `completions`, `unemployment_rate`); `price_index` 2025 and CPI 2026 revised
slightly. The only change inside the index range is SCB revising its own 2024 bostadsrätt
prices by −1.49 % to +1.21 % — an upstream correction, visible on page 04. Every
`version_*`, `z_*`, `rank_*` and `risk_*` value for 2014–2024 is bit-identical to `HEAD`.

**Forecasts were not regenerated, and do not need to be.** The pipeline trains on `BASE_YEAR`
2014 through `_resolve_end_year()`, which still returns 2024 because it keys off non-imputed
income. Inside that window the only column that moved is `bostadsratt_price_sek`, and
`src/forecast/` never references it — it forecasts `affordability_c`, `cpi_yoy_pct`, `income`,
`rate` and `transaction_price_sek`. Re-running step 4 would train on identical inputs.

---

### T2.5 — Verify a clean-environment deploy · DONE

**Depends on:** T2.1, T2.2

**Acceptance**
- [x] Fresh venv, `pip install -r requirements.txt` — installs clean, 39 distributions,
      no compilers invoked. `prophet`, `pmdarima`, `statsmodels` and `pytest` all absent
- [x] Every page navigates without error — **67/67 renders clean inside that venv**
- [x] Map renders with tiles — the Esri basemap host answers HTTP 200 from the clean venv
      and `render_choropleth` builds without error on every page render. (A headless check
      cannot prove the browser paints them; this is as far as it reaches.)
- [ ] **Deployed Streamlit Cloud app confirmed working** — needs the account owner. Everything
      testable locally passes; this is the one criterion I cannot reach.

This also closes T2.1's deferred third criterion: a fresh install from `requirements.txt`
does run the app.

**It found a High-severity issue — recorded as R7 in `docs/OPEN_RISKS.md`.** The bounds are
lower-only, so a clean install today resolves to **pandas 3.0.5** and **numpy 2.5.3** against
the 2.3.3 / 1.26.2 the app is verified on — both major-version boundaries — plus streamlit
1.64.0, plotly 7.1.0 and pyarrow 25.0.1. All 67 renders pass on that set, so nothing is
broken. But a deploy today runs against versions no test here has exercised, and the next
resolver shift happens without anyone choosing it. The failure mode is the bad one: works
for the maintainer on pandas 2.3.3, breaks in production on a rebuild nobody triggered.
Recommendation in R7 is to cap the majors and make this check part of the release routine.

`requests` is present in the clean venv as a transitive dependency of streamlit. That is
correct — T2.1's criterion is absence from `requirements.txt`, not from the environment.

---

## 7. Phase 3 — UI convergence with Skattekraftspanelen

**Goal:** SHAI reads as the same product family as Skattekraftspanelen and KRI.
**Exit criterion:** one CSS naming convention, all copy centralised, every bare number
explained, no file over the project limits.
**Shippable:** yes, but best delivered as one visual release.

Primary reference for every task: `/Users/Brook/Downloads/kommun-skattekraft-stress/src/ui/`.

---

### T3.1 — Add `src/ui/labels.py` · DONE

**Fixes:** Finding M
**Files:** NEW `src/ui/labels.py`
**Reference:** Skattekraftspanelen `src/ui/labels.py` (1137 lines, 196 keys)

One `SWEDISH_LABELS` dict holding every user-facing string, plus formatting helpers
(`format_effect`, `format_interval` equivalents). Code identifiers, comments and docstrings
stay English; user-facing strings are Swedish.

**Acceptance**
- [x] `SWEDISH_LABELS` exists and is the only source of user-facing copy — 269 keys,
      672 lines, reached through `L(key, **values)`
- [x] No Swedish string literal remains inline in `app.py` or `pages/*.py` — **0 remaining**,
      down from 332 across seven files
- [x] Every key non-empty, every key used, every referenced key defined

`tests/test_no_inline_copy.py` (20). No reference repo was needed for this task.

**Proven inert rather than assumed so.** 269 call sites is too many to eyeball, so before
touching anything I captured every string rendered by all 67 page/year states — 5709 of them —
then re-captured after. **0 of 67 render states differ.** The extraction changed no output.

Two bugs the migration hit, both worth recording because both are silent:

**`ast` `col_offset` is a UTF-8 *byte* offset, not a character index.** These files are full of
å/ä/ö, so slicing the source by character shifted every extracted expression right by one per
multibyte character earlier on the line — `APP_VERSION` came out as `P_VERSION}"`. Caught by
reading the generated plan before applying it; the collector now works on the encoded bytes.

**Literal braces must be doubled in anything `str.format` will touch.** One label is a Plotly
hover template (`<b>{v0}</b><br>År: %{{x}}<br>Värde: %{{y:,.2f}}`), and several are HTML blocks
carrying inline CSS. Unescaped, `format` reads `{x}` as a field and raises `KeyError` on
render. All 40 templates are now round-trip checked in the suite.

The guard also found a genuine weakness in an **existing** test: `test_risk_kpi.py` matched the
substring `risk_`, which the new label key `rv.hogrisk_kommuner` contains, so it began firing
on copy instead of on a computation. Tightened to `risk_[abc]`. Its copy assertions now resolve
`L("key")` through the dict — otherwise they would have asserted against key *names* and
passed on strings nobody reads.

Side effect worth having: `06_Metodologi.py` went 350 → 129 lines and `04_Kontantinsats.py`
885 → 794, which is most of T3.3's and T3.11's motivation already banked.

**Unblocks T4.1 and T4.3.**

---

### T3.2 — Normalise all CSS classes to `.shai-*` · TODO

**Fixes:** Finding M
**Files:** `src/ui/css.py`, `src/ui/components.py`, `src/ui/sidebar.py`, `app.py`, `pages/*.py`

Rename the KRI-era leftovers: `.lp-*` → `.shai-*`, `.sidebar-brand` → `.shai-sidebar-brand`,
`.brand-mark` → `.shai-brand-mark`, `.riskklass-*` → `.shai-risk-legend-*`,
`.nav-section` → `.shai-sidebar-section-label`. Match Skattekraftspanelen's names exactly
where an equivalent exists.

**Acceptance**
- [ ] Every project-defined class starts `shai-`
- [ ] `grep -rn "lp-\|riskklass-\|brand-mark\|nav-section" src/ ` returns nothing
- [ ] Visual output unchanged apart from intended improvements

---

### T3.3 — Split `css.py` · TODO

**Fixes:** Finding K
**Files:** `src/ui/css.py` (902 lines) → `src/ui/tokens.py`, `src/ui/css_layout.py`, `src/ui/css_components.py`

Tokens (`COLORS`, `DIVERGING_SCALE`, CSS custom properties) separate from layout/shell CSS
separate from component CSS. `inject_css()` composes them.

**Acceptance**
- [ ] No resulting file over 400 lines
- [ ] `COLORS` and `DIVERGING_SCALE` importable from one tokens module
- [ ] Single CSS injection point preserved

---

### T3.4 — Add `.shai-explanation` under every bare number · TODO

**Fixes:** Finding M
**Files:** `src/ui/components.py`, `src/ui/css_components.py`, `app.py`, `pages/*.py`

Skattekraftspanelen's commit `0e38331` — *"docs: explain every section that showed a bare
number"*. Add an `explanation(text)` helper and a prose block under the landing stat strip,
each KPI row, and each chart.

**Acceptance**
- [ ] `explanation()` component exists and is styled
- [ ] Landing stat strip, every KPI row and every chart has one
- [ ] Copy comes from `labels.py`, and its numbers are format-interpolated from data, not typed

---

### T3.5 — Add the `help_badge()` glossary component · TODO

**Fixes:** Finding M
**Files:** `src/ui/components.py`, `src/ui/css_components.py`, `src/ui/labels.py`
**Reference:** Skattekraftspanelen `components.py:118 help_badge()`, CSS `.shai-help`, `.shai-help-mark`, `.shai-help-pop`

A "?" affordance in card headings that reveals definitions for the terms that card uses,
replacing bare `title=` attribute tooltips. Include `help_aria` labelling.

**Acceptance**
- [ ] `help_badge(*terms)` renders a "?" with a popover
- [ ] Glossary terms live in `labels.py`
- [ ] Applied to at least the map, distribution and ranking cards
- [ ] Keyboard accessible with an aria label

---

### T3.6 — Add the `.shai-vintage` badge · TODO

**Fixes:** Findings C, M
**Files:** `src/ui/components.py`, `src/ui/css_components.py`
**Depends on:** T1.3, T1.5

Promote the data vintage from sidebar footnote to a visible badge, as Skattekraftspanelen
does. `footer_note()` gains an `updated` parameter to match its signature there.

**Acceptance**
- [ ] `vintage_badge()` exists, reads from provenance
- [ ] Visible on the landing page and every data page
- [ ] `footer_note(source, version, updated)` signature matches the reference

---

### T3.7 — Add `src/ui/filters.py` · TODO

**Fixes:** Finding M
**Files:** NEW `src/ui/filters.py`; `pages/01-05`
**Reference:** Skattekraftspanelen `src/ui/filters.py` (33 lines)

Year and risk filtering is currently written out in each page. Extract it.

**Acceptance**
- [ ] One module owns year and risk filtering
- [ ] No page maps `{"Hög": "hog", ...}` itself
- [ ] Empty risk selection means "all" in exactly one place

---

### T3.8 — Add shared `src/ui/data_table.py` · TODO

**Fixes:** Finding M
**Files:** NEW `src/ui/data_table.py`; `pages/01-03`
**Reference:** KRI `app/components/data_table.py` (221 lines), commit `d2f2058`

KRI's *"render every dashboard table through one shared component"*. Replace the hand-rolled
per-page HTML table strings.

**Acceptance**
- [ ] One renderer produces every `.shai-table`
- [ ] No page builds table HTML inline
- [ ] Rank cell, municipality name, numeric alignment and risk pill all handled centrally

---

### T3.9 — Add contextual "Om …" expanders · TODO

**Fixes:** Finding M
**Files:** `pages/01_Riksoversikt.py`, `pages/02_Lan_jamforelse.py`, `pages/03_Kommun_djupanalys.py`
**Reference:** KRI `riksoversikt.py` — "Om kartan", "Om fördelningsgrafen", "Om rankningstabellerna"

**Acceptance**
- [ ] Map, distribution chart and ranking tables each have an explanatory expander
- [ ] Copy from `labels.py`
- [ ] Each states what the reader can and cannot conclude

---

### T3.10 — Split `components.py` · TODO

**Fixes:** Finding K
**Files:** `src/ui/components.py` (434 lines) → generic + NEW `src/ui/landing.py`

Landing-only functions (`render_landing_hero`, `render_landing_stat_strip`,
`render_landing_what_is_block`, `render_index_visual_block`, `render_landing_steps`,
`render_landing_nav_card`, `render_landing_credibility`) move out.

**Acceptance**
- [ ] `components.py` holds only components used by more than one page
- [ ] Neither file over 400 lines
- [ ] `app.py` imports landing components from `landing.py`

---

### T3.11 — Split `04_Kontantinsats.py` · TODO

**Fixes:** Finding K
**Files:** `pages/04_Kontantinsats.py` (880 lines), `src/kontantinsats/`

Move regime definitions, calculation and chart construction into `src/kontantinsats/`; the
page keeps layout and wiring only.

**Acceptance**
- [ ] Page under 400 lines
- [ ] No regulatory constant defined in a page file
- [ ] Regime logic unit-testable without Streamlit

---

### T3.12 — Align `.streamlit/config.toml` · TODO

**Files:** `.streamlit/config.toml`

Skattekraftspanelen uses `primaryColor = "#C4A35A"` (gold) and
`font = "Source Sans 3, sans-serif"`; SHAI uses navy and `"sans serif"`. Gold is correct —
`primaryColor` drives Streamlit's own widget accents, which should match the accent token,
not the brand navy.

**Acceptance**
- [ ] `primaryColor` and `font` match the reference
- [ ] Streamlit-native widgets (pills, sliders) pick up the gold accent

---

## 8. Phase 4 — Tests and documentation

**Goal:** the Phase 1 defects become structurally unable to recur, and the docs describe the
code that actually ships.
**Exit criterion:** the copy-vs-data test passes, pages render under test, superseded docs gone.

---

### T4.1 — `tests/test_copy_matches_artifacts.py` · TODO

**Fixes:** Findings A, C, H, J — **the highest-value test in this plan**
**Reference:** Skattekraftspanelen `tests/test_copy_matches_artifacts.py`
**Depends on:** T1.3, T3.1

Re-derive every number quoted in UI prose from the committed artifacts, in the same wording
and rounding the copy uses, and assert the fragment appears verbatim in `SWEDISH_LABELS`. A
failure means copy and data disagree, and the message shows what the data now says. This is
the guard that prevents Findings A, C and H from returning.

**Acceptance**
- [ ] Every `labels.py` string containing a number is covered
- [ ] Deliberately editing one number in the copy makes the suite fail
- [ ] Failure messages state the current data value

---

### T4.2 — `tests/test_provenance.py` · DONE

**Depends on:** T1.3

Written as the TDD artifact for T1.3 rather than deferred to Phase 4 — the module was built
against it, so it landed early. 18 tests.

**Acceptance**
- [x] `complete_case_max_year()` and `panel_max_year()` asserted against the artifact
- [x] Missing artifact raises `FileNotFoundError` with a helpful message (asserts the message
      names `refresh_data`); a missing key raises `KeyError`
- [x] Per-source coverage matches the panel — every recorded window is re-derived from
      `panel_municipal.parquet` independently of how it was written, including the
      imputed-income exclusion, and `complete_case_max_year` is re-derived from the raw
      `notna()` mask rather than read back

---

### T4.3 — `tests/test_labels.py` · TODO

**Depends on:** T3.1

**Acceptance**
- [ ] Every referenced key exists and is non-empty
- [ ] Load-bearing wording asserted verbatim (headings the methodology specifies)
- [ ] Caveat strings assert the limitation they exist to state

---

### T4.4 — `tests/test_pages_render.py` · DONE (pulled forward, out of phase order)

**Reference:** Skattekraftspanelen `tests/test_pages_render.py`

**Acceptance**
- [x] Every page imports and executes without raising — and rendered *something*: a page
      that returned early used to satisfy a bare exception check silently
- [x] Every year offered by the selector renders every page — parametrised off `YEAR_RANGE`,
      so the sweep widens the day provenance does
- [x] Empty risk selection renders, and so does a single-class selection, on all six pages

**Pulled forward out of phase order** (R6). This was scheduled second-to-last while being
the check that actually proves the app works — and Phase 3 is twelve tasks of UI change to
exactly the surface it covers. Landing it after that would have meant making those changes
with the verification still sitting in a session scratch directory, re-runnable by nobody.

`tests/test_pages_render.py` — **81 tests in 14 s**, in the default suite. Two of them are
meta-tests against a temp script that raises and one that renders nothing: without those,
81 green ticks could mean 81 renders or a broken harness.

It also found **R8** immediately: every map render emits a `DeprecationWarning` that
`folium_static` will be removed. Recorded, not fixed — the migration to `st_folium` changes
rerun behaviour and belongs with T3.9, which already touches the map.

---

### T4.5 — `tests/test_choropleth.py` · DONE

**Depends on:** T1.6, T1.7

Written as the TDD artifact for T1.6/T1.7 rather than deferred to Phase 4 — the module was
built against it, so it landed early. 21 tests, 20 of which failed first.

**Acceptance**
- [x] Colormap domain derives from data, not constants — asserted by *varying*: the eleven
      years must not share one domain, and the old ±2.5 bounds must not appear
- [x] Tile URL is not `cartocdn.com`
- [x] Missing GeoJSON degrades to a warning, not a crash

Source-level assertions run against **executable source** via the shared
`tests/sourcetools.py` helper, which blanks comments and docstrings. A comment naming the tile
host that had to be abandoned cannot reintroduce it, and a guard that cannot tell prose from
code punishes the explanation. The same helper now backs `tests/test_year_range.py`.

---

### T4.6 — Delete superseded docs · TODO

**Fixes:** Finding L
**Files:** `docs/`

Remove the four superseded v1 files whose v2 successors exist: `METHODOLOGY.md`,
`PLAYBOOK.md`, `prompts.md`, `patch_post_day2.md`. Rename the `_v2` survivors to drop the
suffix. Follow Skattekraftspanelen's `bcf31df` — *"reduce docs to three, and remove every
file with no reader"* — and fold build-time artifacts (`PROMPTS`, `PATCH_POST_DAY2`,
`APARTMENT_DATA_ANALYSIS_PLAN`, `translation_audit`) into an archive or delete them.

**Acceptance**
- [ ] No `_v2` suffix remains
- [ ] No two documents describe the same thing
- [ ] Every surviving doc is linked from `README.md`

---

### T4.7 — Rewrite `DESIGN_SYSTEM.md` · TODO

**Fixes:** Finding L
**Files:** `docs/DESIGN_SYSTEM.md`
**Depends on:** all of Phase 3

§10 currently documents a Plotly `go.Scattergeo` map that was replaced by Folium in commit
`4f98a23`. Rewrite against the shipped code, including the new `.shai-*` names, the new
components (`help_badge`, `explanation`, `vintage_badge`, `data_table`) and the empirical
map scale. Add a maintenance rule requiring this document to change with the CSS.

**Acceptance**
- [ ] Every documented class exists in the CSS
- [ ] Every CSS class is documented
- [ ] Map section describes Folium and the empirical colormap
- [ ] Contributor verification checklist included

---

## 9. Session log

Append one line per work session: date, tasks touched, outcome, anything the next session needs.

| Date | Tasks | Outcome | Notes for next session |
|------|-------|---------|------------------------|
| 2026-09-15 | — | Audit completed, plan written. No code changed. | Answer O1 before T2.4. Start at T1.1. |
| 2026-09-16 | T3.1 | **DONE, no reference repo needed.** 269 keys in `src/ui/labels.py`; **0 Swedish literals left** in `app.py` or `pages/*.py`, down from 332. Verified by fingerprinting all 5709 rendered strings across 67 page/year states before and after — **0 states differ**, so the extraction is provably inert rather than hopefully so. Two silent traps: `ast.col_offset` is a UTF-8 **byte** offset, so character slicing shifted every extracted expression (`APP_VERSION` → `P_VERSION}"`) — caught by reading the plan before applying it; and literal braces must be doubled for `str.format`, or the Plotly hover template and the inline-CSS blocks raise `KeyError` on render. `tests/test_no_inline_copy.py` (20) guards all of it. Also fixed an existing test weakness: `test_risk_kpi.py` matched the substring `risk_`, which `rv.hogrisk_kommuner` contains, and its copy assertions were reading key *names* rather than copy. **Suite: 323 passed, 0 failed, 1 skipped.** | Next: **T4.1**, now unblocked and described in this plan as its highest-value test — re-derive every number in the copy from the artifacts. T4.3 is also unblocked. Then the remaining Phase 3 work, which still needs the reference repo (§0). New **R9**: `labels.py` now holds HTML and LaTeX blocks as well as copy — correct per the acceptance, wrong as a long-term home. |
| 2026-09-16 | T4.4, R7 | **Pre-Phase-3 work. T4.4 DONE, pulled forward.** The 67-render check is now `tests/test_pages_render.py` — 81 tests, 14 s, in the default suite, wider than the scratch script it replaces (empty and single risk selections, years off `YEAR_RANGE`, a content assertion, plus two meta-tests proving the harness can fail). Closes R6. It immediately found **R8**: `folium_static` is deprecated and scheduled for removal, 13 warnings per sweep — recorded, not fixed, because migrating to `st_folium` changes rerun behaviour and belongs with T3.9. **R7 accepted, option B**: major-version caps in `requirements.txt`, mirrored into `pyproject.toml`, plus a test that the two agree on specifiers rather than just names. Caps sit *above* what T2.5 verified — a clean install still resolves pandas 3.0.5 / numpy 2.5.3 / streamlit 1.64.0, byte-identical to before, so no downgrade. Residual risk kept open: 0.x packages get `<1`, which still admits breaking minor bumps, and `folium` is what draws the map. **Suite: 299 passed, 0 failed, 1 skipped.** | **Before T3.1, read §0 — neither reference repo exists on this machine.** Five Phase 3 tasks are self-contained (T3.1, T3.2, T3.3, T3.10, T3.11); the seven pattern-borrowing ones need Skattekraftspanelen's `src/ui/` or they become guesswork. Recommended order: T3.1 → T4.1 (T3.1 unblocks it), then pause for repo access. Still unaddressed and arguably above most of Phase 3: **R5** — `src/indices/affordability.py` computes all three versions and has zero tests. |
| 2026-09-15 | T2.5 | **DONE — Phase 2 closed.** Clean venv, `requirements.txt` only: 39 distributions, no compilers, pipeline packages absent, **67/67 renders clean inside it**, Esri tile host HTTP 200. Also closes T2.1's deferred third criterion. The check earned its keep immediately: lower-only bounds resolve a fresh deploy to **pandas 3.0.5** and **numpy 2.5.3** against the 2.3.3 / 1.26.2 this app is verified on — two major-version boundaries. Everything passes on them, so nothing is broken, but production runs versions no test here has exercised and the next resolver shift is nobody's decision. Logged as **R7 (High)**. Started `docs/OPEN_RISKS.md` for this class of finding — seven entries, R1 and R7 High. | Next: **T3.1**, Phase 3. Read `docs/OPEN_RISKS.md` first: **R2** (three pages read year lists from data, not `YEAR_RANGE`) belongs with T3.7, and **R6** (the 67-render check is still a scratch script) argues for pulling **T4.4** forward before Phase 3 starts changing the UI it verifies. One criterion is genuinely open: nobody has confirmed the deployed Streamlit Cloud app, which needs the account owner. |
| 2026-09-15 | T2.4, O1 | **DONE.** O1 answered: run it. The refresh itself was the small part. Two defects it exposed: (1) `kolada_client.fetch_unemployment` defaulted to `end_year=2024` and so never asked for 2025, which Kolada has had all along — ceiling now resolved at fetch time, `tests/test_kolada_year_range.py` (7); (2) once unemployment 2025 landed, a forward-filled-income 2025 row survived into the index and, because `compute_version_b` pools its component z-scores across the whole frame, re-based `version_b` for every historical year — 1816 rank changes, 19 class changes, from a year no page can render. `step_compute_indices` now filters through `complete_case()`; `tests/test_index_complete_case.py` (6). With both fixed the refresh is purely additive: **INDEX CONTRACT COLUMNS CHANGED: NONE**. Step 4 was killed by the OS for memory and is verifiably unnecessary — the forecast training window ends at 2024 and none of the forecast variables moved inside it. **Suite: 217 passed, 0 failed, 1 skipped. 67/67 renders clean.** | Next: **T2.5**, clean-venv deploy check; scripts are staged. Carry forward: pages 02, 04 and 05 read their year lists from the data rather than from `YEAR_RANGE`. Harmless today because `complete_case()` keeps the index at 2024, but it is the same class of leak and belongs in Phase 3. Also unverified: whether `[pipeline]` installs from scratch — prophet/pmdarima were already present here. |
| 2026-09-15 | T2.1, T2.2, T2.3 | **All DONE.** Runtime set split from the pipeline toolchain: `requirements.txt` is eight packages with no compilers, and `prophet`, `pmdarima`, `statsmodels`, `requests` moved to a `pipeline` extra. `tests/test_runtime_dependencies.py` (8) derives the expected set by walking the import graph from `app.py` and `pages/*.py`, so a new import on a page fails the suite rather than the next cold start. Three defects surfaced beyond the listed scope: `requires-python` was `>=3.11,<3.12`, which would have refused this task's own `pip install -e` on the verified interpreter; `packages.find` described a src-layout the project does not use; and **bare `pytest` could not collect the suite at all** (6 errors) — it worked only under `python -m pytest`, the form §0 documents, which injects the CWD. `pythonpath` now carries `.` and `src`, with a subprocess test on the bare invocation. `pytest` left the runtime deps for a `dev` extra alongside `pytest-cov` and `scipy` (previously undeclared). Docs: both install paths in both files, Finding E's ragged-panel table in `DEPLOYMENT.md`, echarts note gone; `tests/test_docs_install_paths.py` (16) reads the vintage from provenance so the prose cannot outlive the data. **Suite: 204 passed, 0 failed, 1 skipped. 67/67 renders clean.** | **T2.4 is gated on O1 and I have not started it.** T2.5 does not depend on it. Note the `[pipeline]` install is only dry-run verified so far; T2.4's own first acceptance criterion is that those extras genuinely install, and T2.5 is the clean-venv check for the runtime set. `docs/prompts.md` and `docs/UX_UI_GAP_ANALYSIS.md` still name ECharts — left for T4.6. |
| 2026-09-15 | T1.9, T1.10 | **Both DONE — Phase 1 closed.** T1.9: dropped the YoY delta on the high-risk count and relabelled it a relative position within the year, with no split figure in the copy (D6). Widened mid-task — the count was read from the *risk-filtered* frame while the row's other three cards read the unfiltered year, so deselecting "Hög" showed the national high-risk count as 0; now counted on `mun_year`. `tests/test_risk_kpi.py` (8). T1.10: nineteen literal `290` / `2014–2024` / "11 år" across nine files replaced with provenance reads; `_panel_facts()` resolves them per call in `components.py`. `tests/test_no_hardcoded_counts.py` (47), including a behavioural check against a relabelled panel (277 kommuner, 2009–2019). Fixed a false-green in my own fixture: `render_landing_steps` emits via `st.html`, so a markdown-only capture returned an empty string and passed every absence assertion vacuously. Also corrected the step's claim that values are z-standardised "över hela panelen" — D5 made that false. **Suite: 172 passed, 0 failed, 1 skipped. 67/67 renders clean.** | Next: **T2.1**. Note for this machine: the §0 `python3.11` rule is macOS-specific — on Windows the default `python` is 3.12.10 and collects the full suite, though `pyproject.toml` still declares `requires-python = ">=3.11,<3.12"`, which T2.2 should reconcile. Deferred, not done: `21 län` is still a literal (provenance carries no county count), and `06_Metodologi.py` still hardcodes the measured "16 av N kommuner" class-change figure — both belong to T4.1. |
| 2026-09-15 | T1.8, Findings O + P | **DONE.** O2 → D5 (within-year `z_*`; B's construction stays pooled), O4 → D6 (log-transform A and C). Implemented in `normalize.py`, artifacts regenerated, `rank_*` verified identical across all versions and years. `z_c` normality now holds every year (p = 0.34–0.83); 2024 split 19.7/50.3/30.0 → 23.4/48.3/28.3. METHODOLOGY §4 rewritten into window/transform/class subsections stating what B would lose under within-year. Finding O resolved (a near-tie boundary — Skåne is 6th by 0.7 points); Finding P corrected in both files. Histogram caption updated: on a log scale z = 0 is the median, not the mean. `tests/test_normalization_convention.py` (16). **Suite: 117 passed, 0 failed, 1 skipped — green for the first time.** 67/67 renders clean. | Next: **T1.9** — drop the YoY delta on the high-risk count; its labels must not quote a split figure, since D6 moved it. Then **T1.10**. Phase 1 has no blocked tasks left. |
| 2026-09-15 | T1.8 (analysis only) | **BLOCKED, no code changed.** Investigating T1.7's colour domain exposed a larger issue: `version_c` is a ratio and therefore log-normal, but is z-scored raw and cut at ±0.67σ. Normality is rejected at p < 6e-15 in every year; under a log it passes in all eleven (p = 0.34–0.83). Recorded as **Finding Q**. This also proved **Finding F's own arithmetic wrong** — the split is ≈19/51/30 with 83–89 high-risk, not the "25/50/25, near 72" it claimed; F corrected in place. Split the normalisation question into two axes, window (**O2**) and transform (**O4**), widened T1.8 to own both, and marked it `BLOCKED`. Blast radius measured for the decision: ranks unchanged, 16 of 290 municipalities (6 %) change class. | **Answer O2 and O4 to unblock T1.8.** Until then the next workable task is **T1.9** (unblocked), then **T1.10**. Do not change the transform piecemeal — the numbers are currently self-consistent and a partial change is worse than either endpoint. |
| 2026-09-15 | T1.6, T1.7, T4.5 | **All DONE.** Basemap moved to Esri `World_Light_Gray_Base` with attribution and a background fallback. Colour domain now built from the data: ends at min/max, neutral at the median, steps at the quartiles. Fixes a fault worse than KRI's — SHAI's `z_c` is left-skewed, so ±2.5 clipped 104 municipality-years off the green end *and* left the top 43 % of the red ramp unused. Clipping now zero. `tests/test_choropleth.py` (21) satisfies T4.5; extracted `tests/sourcetools.py` so the prose-vs-code stripper is shared. Suite: **100 passed, 1 failed, 1 skipped**; all 67 page renders still clean. | Next: **T1.8**, which is **blocked on O2** — confirm within-year normalisation for A/B/C. If O2 stays unanswered the documented default is within-year. T1.8 also owns two loose ends: Finding O (`test_skane_worst_v_c`, failing since before this work) and Finding P (`06_Metodologi.py:247` documents the imputation rule F9 replaced). T1.9 and T1.10 are unblocked if you would rather not wait on O2. |
| 2026-09-15 | T1.4, T1.5 | **Both DONE.** Selector now spans 2014–2024 from provenance — drops the two dead years and gains 2014–2019, which the index always covered. Footer shows the artifact's `generated_at`, proven independent of the clock. Removed the sidebar forward-fill note and the unreachable imputed-income banner on page 01. `tests/test_year_range.py` (16), mutation-checked. Verified all 6 pages × 11 years render via `AppTest` (67 renders, clean). Suite: **79 passed, 1 failed, 1 skipped** — failure is Finding O, unchanged. | Next: **T1.6** (map basemap, no dependencies) then **T1.7**. New **Finding P**: `06_Metodologi.py:247` documents the imputation rule that F9 replaced — fix during T1.8 or T4.1. Note the repo's tests must run under **python3.11**; the system `python3` is 3.9 and cannot import `tomllib`. |
| 2026-09-15 | T1.2, T1.3, T4.2 | **All DONE.** T1.2: removed both inline recomputes, repointed the page at the ranked artifact only, recoloured the histogram from `risk_c`, fixed Finding N3 (caption stated the orientation backwards), added `tests/test_pages_no_recompute.py` (14). T1.3: added `src/provenance.py` + committed `data/processed/data_provenance.json`, wired into `step_compute_indices()`; income's imputed tail is excluded so the complete case lands on 2024. T4.2 satisfied by `tests/test_provenance.py` (18). Suite: **63 passed, 1 failed, 1 skipped** — the failure is Finding O, unchanged. | Next: **T1.4** — `YEAR_RANGE` from `complete_case_max_year()`. Note T1.2's 2014 criterion is verified at the data layer only; it becomes reachable in the UI once T1.4 lands. `generated_at()` is already in place for T1.5. |
| 2026-09-15 | T1.1 | **DONE.** Rewrote `normalize.py` (per-year scoring, documented orientation contract); routed `refresh_data.py` through it; regenerated the artifact; added `tests/test_ranked_artifact.py` (15 tests, 11 were failing). Uncovered and fixed Finding N — risk classes were inverted on the live app. | Next: **T1.2**, delete the inline recompute at `01_Riksoversikt.py:58-80`. Note pre-existing failure `test_skane_worst_v_c` (Finding O) — not a regression, defer to T1.8. |
