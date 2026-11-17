# SHAI UX/UI modernization plan

Status: **proposal, awaiting approval**. No source file has been changed.
Prepared 2026-11-17 against `main` at `fac2b4f` (v1.3.0).

---

## 0. How this plan was produced, and the baseline it starts from

**Branch.** `main` is the latest version. `feature/conditional-projection` and
`revitalization/phase-1` are both fully merged into it (`git log main..<branch>` is
empty for each), `main` is level with `origin/main`, and the `backup/*` branches are
older snapshots. All work in Part B branches from `main`.

**What was inspected.**
- All 171 tracked files were listed. The following were read in full: `app.py`, every
  page in `pages/`, every module in `src/ui/`, `src/kontantinsats/`, `src/scenario/`
  and `src/lan/`, `.streamlit/config.toml`, `requirements.txt`, `pyproject.toml`,
  `README.md` and `docs/DESIGN_SYSTEM.md`.
- `docs/APP_REFERENCE.md` was read for its index and risk register.
- The test guards that constrain UI work were read: `test_file_sizes`,
  `test_css_naming`, `test_design_system_doc`, `test_no_inline_copy`,
  `test_ui_affordances`, `test_chart_theme_guard`, `test_browser_render`,
  `test_pages_render` and `test_pages_text_fit`.
- The app was run locally on Streamlit 1.56.0, Plotly 6.7.0, Folium 0.20.0 and
  pandas 3.0.2. Every page was screenshotted at full height at 1440 px and at 390 px.
- WCAG contrast ratios were computed for every text/background token pair in use.

**Baseline test result.** `pytest -m "not browser and not network"`: **1376 passed,
1 skipped**, 40 s. The browser suite (`test_browser_render`, `test_pages_text_fit`)
was not part of that run. UX-00 runs it to complete the baseline.

**Technology confirmed.** The app is Streamlit, with a classic multipage layout:
`app.py` is the landing page, `pages/0N_*.py` hold the pages, and
`client.showSidebarNavigation = false` is replaced by a custom `st.page_link` rail.
Plotly draws the charts and Folium the map, inside `components.html`. The app has no
database, no authentication and no runtime API calls. It reads seven committed Parquet
artifacts through `@st.cache_data`. The only network requests at runtime are Google
Fonts and the Esri map tiles.

---

# PART A: UX/UI MODERNIZATION PROPOSAL

## A1. Executive summary

**What the product is.** SHAI is a Swedish-language analytical dashboard. It answers
one question: *how much of a normal household's income does it take to carry a
typical house loan in this kommun, this year, compared with everywhere else in Sweden?*
It covers 290 kommuner and 21 län from 2014 to 2024, built from SCB, Riksbanken and
Kolada data. Its distinguishing quality is **analytical honesty**. Every figure is
re-derived from the data by a test. Every number on screen carries an explanation, and
caveats are stated where a misreading would form. The audience is analytical rather
than transactional: economists, journalists, students, municipal and county planners,
and informed would-be buyers.

**Current assessment.** The product is substantively strong and visually competent.
It has a coherent navy-and-gold identity, a documented and test-enforced design system
(`docs/DESIGN_SYSTEM.md`), and unusually careful copy. It is not a prototype, and this
plan treats it as mature.

Its UX/UI weaknesses are systemic rather than cosmetic:

1. **Accessibility failures in the palette.** Gold `#C4A35A` is used as *text* on
   white at **2.4:1**: eyebrows, section titles, the active tab label and slider values.
   "MEDEL" risk-pill text `#D4A03C` is **2.36:1**. Tertiary grey `#9CA3AF` text (year
   display, card tags, footer, stat units) is **2.54:1**. The white labels on the
   regulatory timeline are **2.4:1**. All of these fail WCAG AA (4.5:1).
2. **Controls that do nothing where they appear.**
   - The sidebar risk filter sits on all seven pages but changes output only on Sida 01.
   - The year pills appear on the landing page and on Metodologi, where nothing reads
     them.
   - The six landing navigation cards lift on hover like links but are not clickable
     (`src/ui/css_landing.py:243-249`).
3. **Encoding collisions in colour.**
   - The risk palette (green/amber/red = låg/medel/hög) is reused as a *categorical*
     palette for regulatory regimes (`src/kontantinsats/regions.py:52`).
   - On Sida 04's comparison charts green and red *also* mean best and worst
     (`src/kontantinsats/charts.py:83-90`), so a red bar can mean "Amorteringskrav 2.0"
     or "the worst regime on this metric". Nothing on the chart says which.
   - KPI-card stripe colours are applied decoratively. Befolkningsförändring gets the
     "success" green stripe and K/T gets gold, so the stripe carries no meaning.
4. **Hierarchy and density problems on the two tool pages.**
   - Sida 04 is 4 600 px tall on desktop and 8 400 px on a phone. It shows two separate
     four-card KPI rows, and the same down payment appears in five places.
   - Its headline answer arrives only after a purpose panel, an info banner and the
     control card.
   - Sida 05 places its explanatory scope note between the purpose panel and the
     controls.
5. **Inconsistent component rendering.**
   - Three table technologies are in use: `.shai-table` HTML, `st.dataframe` with a
     smaller default font, and Markdown tables on Metodologi.
   - `render_table` wraps its output in a `.shai-card` that pages place inside
     `st.container(border=True)`, which draws a card inside a card (Sida 02 ranking and
     Robusthet).
   - `st.info` banners render in Streamlit's default blue, outside the palette.
6. **Hardcoded styling.** The stylesheets hold 130 hex literals across seven CSS
   modules. `src/ui/css_components.py:118` says tokens cannot be interpolated into the
   CSS strings. They can, through generated CSS custom properties. There are also 18
   ad-hoc `<div style='height:Npx'>` spacers.
7. **Typography of figures.**
   - Numbers in tables, KPI deltas, chart bar labels and the stat strip use IBM Plex
     Mono. With non-breaking-space digit grouping this renders as wide "31  726  SEK"
     strings.
   - Chart axes use Plotly's SI suffixes ("50k", "1M"), while every other figure on the
     site is Swedish-formatted ("50 000", "1 Mkr").

**Modernization objectives.**

1. Reach WCAG 2.1 AA contrast for all text, and make every interactive element do what
   its affordance promises.
2. Give colour one meaning per hue: **risk/status** (green, amber, red), **brand and
   selection** (navy, gold), and **categories and chronology** (neutral data hues).
3. Move the design system from "documented hex values copied by hand" to "tokens
   generated once into CSS variables".
4. Lead each tool page with its answer and keep all of its detail.
5. Present financial figures in one typographic voice: tabular sans-serif figures,
   Swedish formatting, explicit units.

**Expected improvements.** An AA-compliant interface. No dead or misleading controls.
Shorter, answer-first tool pages, with Sida 04 about 30 % shorter and no metric
removed. Consistent tables and callouts. A palette a contributor can change in one
file. All of this keeps the 1 376 tests green and the feature set intact.

**What this plan deliberately does not do.**
- It does not rebuild the app or change a formula, a calculation, an artifact, a
  widget key or a URL.
- It does not change the Swedish copy beyond the strings new components need.
- It does not adopt a new frontend framework or add a new runtime dependency. Every
  change uses Streamlit 1.56 and Plotly as installed.

---

## A2. Existing application assessment

### Architecture

| Layer | Where | Notes |
|---|---|---|
| Entry and landing | `app.py` (116 lines) | Hero, stat strip, explainer blocks, nav cards |
| Pages | `pages/01_…06_*.py` (179–386 lines each) | Each calls `st.set_page_config`, `inject_css()` and `render_sidebar()` |
| UI kit | `src/ui/` (29 modules) | Components, tokens, 7 CSS slices, chart theme, table renderer, formatters, copy (`labels.py`, 799 lines) and markup (`templates.py`) |
| Page sections | `src/kontantinsats/`, `src/scenario/`, `src/lan/` | Display sections and chart builders split out to keep pages under 400 lines |
| Domain logic | `src/indices/`, `src/projection.py`, `src/kontantinsats/engine.py`, `src/scenario/simulator.py` | **Out of scope. Not touched.** |
| Data | `data/processed/*.parquet` and `*.json` | Read through `src/ui/data.py::load` (cached) and `src/provenance.py` |
| Guards | `tests/` (59 files) | Copy-vs-artifact, CSS naming, doc-vs-stylesheet, file size ≤ 400, chart tokens, 67 AppTest renders, Chromium at 1440 and 390 px |

**State.**
- `shai_selected_year` and `shai_selected_risks` are plain session_state mirrors,
  which carry the selection across pages. `sidebar.py:105-119` explains why the widget
  key alone does not.
- Page-local widget keys: `kd_kommun_select`, `ki_pristyp`, `ki_lan_select`,
  `ki_kommun_select`, `ki_household_type`, `ki_savings_slider`,
  `ki_bank_margin_slider` (reset per year through `ki_bank_margin_year`),
  `sc_county_select`, `sc_rate_slider`, `sc_income_slider`, `sc_price_slider`,
  `sc_preset_*` and `lj_counties`.
- The Sida 05 preset buttons write to the slider keys and call `st.rerun()`.

### Navigation

There is a dark navy sidebar with seven flat `st.page_link` entries, all at one level.
Under them sit the year pills (11 options) and the risk filter (legend plus 3 pills),
then a footer. On ≤ 768 px the sidebar becomes an overlay opened by a fixed navy
button. The landing page repeats the navigation as six cards, which are not links.

### Visual identity

- **Colours:** navy `#0B1F3F` sidebar, gold `#C4A35A` accent, off-white `#F7F8FA`
  canvas, white cards with a 1 px `#EEF0F3` border and a 4 px radius.
- **Typography:** Source Sans 3 for UI, IBM Plex Mono for figures and tags.
- **Section titles:** uppercase gold "eyebrow" labels.
- **Character:** restrained and institutional, appropriate for an economic statistics
  product. It is a sound base, and the plan evolves it rather than replacing it.

### Component patterns in use

- **Header and cards:** `page_title`, `kpi_card` with `render_kpi_row`, `card` and
  `card_header` (title, subtitle and a mono tag such as "KOROPLETKARTA"),
  `st.container(border=True)` as the card body.
- **Status and data:** `risk_pill`, `render_table`, `explanation`, `help_badge` (a
  CSS-only glossary popover), `vintage_badge`, `footer_note`, `purpose_panel` and
  `render_findings` (the severity-dot interpretation panel).
- **Streamlit widgets:** `st.metric` (Sida 04 regime cards, villa vs bostadsrätt),
  `st.dataframe` (two places), `st.tabs`, `st.expander` (19), `st.latex`,
  `st.select_slider`, `st.radio`, `st.selectbox` and `st.multiselect`.

### Interaction patterns

- Global filters live in the sidebar.
- Page-local controls sit at the top of their page.
- Detail and methodology are progressively disclosed in expanders titled "Om …".
- Tool pages recompute on every widget change, with a full-script rerun.
- There are no forms, dialogs or fragments.

### Main usability problems (evidence-based)

| # | Problem | Evidence | Severity |
|---|---|---|---|
| U1 | Gold, amber and tertiary-grey **text fails contrast** | Contrast ratios in A1; 20 gold, 13 tertiary and 2 amber literals in CSS | High (accessibility) |
| U2 | **Landing nav cards look clickable but are not** | `css_landing.py:243` sets `cursor: default` and `:hover { transform … }`; `app.py:81-114` uses plain markup | High (dead control) |
| U3 | **Risk filter is global but local in effect.** Only `pages/01` reads `selected_risks`, and the year is unused on the landing page and Sida 06 | `grep selected_risks` matches only Sida 01 | High (inert control) |
| U4 | **Risk colours reused for regimes and for best/worst**, so a red bar is ambiguous | `regions.py:52`, `charts.py:83-90` | High (misleading encoding) |
| U5 | KPI stripe colours carry no consistent meaning | Sida 01: population is "success", K/T is "accent"; Sida 03: SHAI is "accent", others "default" | Medium |
| U6 | Sida 04: duplicated KPI rows, the answer arrives late, 4 600 px tall | Screenshots; `sections.py` renders 8 KPI cards in two rows separated by a chart and a villa/BR card | Medium |
| U7 | Card nested inside card, and three table styles | Sida 02 ranking and Robusthet; `st.dataframe` on Sida 05; Markdown tables on Sida 06 | Medium |
| U8 | Off-palette Streamlit blue `st.info` banners | Sida 04 price-type note, Sida 05 scope note | Low–Medium |
| U9 | Monospace figures with wide grouping; SI axis suffixes | Bar labels "31  726  SEK", axes "50k" and "1M" (Sida 04) | Medium |
| U10 | Page year shown as 36 px light grey `#9CA3AF`, which reads as disabled | `css_components.py:22-28` | Low–Medium |
| U11 | Page titles are `<div>`s, not headings, so the semantic structure is missing for screen readers | `components.py::page_title` | Medium (accessibility) |
| U12 | KPI tooltips use the `title=` attribute: invisible on touch, not focusable | `kpi_card(tooltip=…)`; the codebase replaced this pattern elsewhere with `help_badge` | Medium (accessibility) |
| U13 | Data vintage appears in up to 3 places per page (badge, page footer, sidebar footer), with inconsistent placement (top, middle or bottom) | Screenshots | Low |
| U14 | The landing page leads with the *product*, not the *finding*: no headline figure. The weight bars it shows are Version B's, which is not the version that runs the site | `landing.py::render_index_visual_block`; `labels.py:110` | Medium |
| U15 | 18 ad-hoc inline spacer divs, so vertical rhythm differs page to page | grep count | Low |
| U16 | Phone: KPI values shrink to 18 px on full-width stacked cards, and each top-15 table needs ~720 px | `clamp(18px, 2.3vw, 32px)`; phone screenshots | Medium |
| U17 | Sida 01 shows two near-identical colour-scale explanations under the map | `rv.fargskala_*` caption plus `rv.forklaring_karta` | Low |
| U18 | No way to see or export the full 290-kommun ranking: only top and bottom 15 | Sida 01 | Medium (analytical capability) |

### Existing strengths to preserve

- **Copy and honesty:** every number has an explanation, and the interpretation
  panels and caveats are well written.
- **Guards:** the copy-vs-artifact tests, the design-doc test and the browser tests.
- **Formatting:** decimal comma, true minus and nbsp, centralized in `formatting.py`.
- **Charts:** the chart theme guard, the empirical map scale, and the in-page legends
  that survive phone widths.
- **Robustness:** cross-page year persistence, and empty or error states on every
  page.

---

## A3. Feature and functionality inventory

The classification is **C**ore, **S**upporting, **A**dvanced, **Ad**ministrative and
**E**xperimental. "Mod." states whether this plan modifies the feature's presentation.
Behaviour is never modified unless the row says so.

### Global, all pages

| ID | Feature | Class | Location | Dependencies | UX issue | Mod. |
|---|---|---|---|---|---|---|
| G1 | Sidebar page navigation (7 links) | C | `src/ui/sidebar.py::PAGES` | `st.page_link` | Flat list, no grouping, no visible focus style | Yes (grouping, styling) |
| G2 | Year selector 2014–2024, persisted across pages | C | `sidebar.py:97-127` | `provenance.complete_case_max_year`, `shai_selected_year` | Inert on landing and Sida 06 | Yes (shown where used) |
| G3 | Risk filter (multi, empty = all), persisted | S | `sidebar.py:132-170`, `filters.py` | `RISK_LABELS`, `shai_selected_risks` | Inert on 6 of 7 pages | Yes (shown on Sida 01 only) **REVIEW** |
| G4 | Risk legend | S | `sidebar.py:135-150` | tokens | Duplicates the map legend | Yes (moves with G3) |
| G5 | Sidebar footer: vintage and version | S | `sidebar.py::footer_html` | `provenance.generated_at` | Grey on navy is 3.39:1 | Yes (contrast) |
| G6 | Data vintage badge | S | `components.vintage_badge` | provenance | Placement varies | Yes (placement) |
| G7 | Page footer (vintage, version, sources on Sida 06) | S | `components.footer_note` | provenance | none | Style only |
| G8 | Glossary help badges "?" | S | `components.help_badge` | `glossary.*` labels | Gold ring at 2.4:1 | Style only |
| G9 | Explanation lines under numbers | C | `components.explanation` | labels | none | Style only |
| G10 | Contextual "Om …" expanders | S | every page | labels | none | No |
| G11 | Cost history panel ("Ränta, amortering och pris år för år") | A | `src/ui/cost_panel.py`, on Sida 01, 02 and 06 | `indices.agreement.cost_history`, `decompose` | Card within card | Style only |
| G12 | Load-error and empty-year states | S | every page | `st.error`, `st.warning`, `st.stop` | Default styling, raw exception text | Style only |
| G13 | Mobile sidebar open button | S | `css_layout.py:78-102` | Streamlit DOM test-ids | none | No |
| G14 | Cached artifact loading | S | `src/ui/data.py` | `st.cache_data` | none | No |

### Landing page (`app.py`)

| ID | Feature | Class | UX issue | Mod. |
|---|---|---|---|---|
| L1 | Hero (title, lead) | S | Product before finding | Yes (tightened) |
| L2 | Stat strip: period, kommuner, län, formler | S | Mono figures | Style |
| L3 | Coverage explanation and vintage | S | none | No |
| L4 | "Vad är SHAI?" block | S | none | No |
| L5 | Index overview: Version B weight bars and flow SVG | S | Shows B's weights under "Indexet i överblick", although C runs the site; hardcoded hex in SVG | Yes (relabel, demote, tokens) |
| L6 | Three-step pipeline | S | none | Style |
| L7 | Six navigation cards | C | **Not clickable** | **Yes (made links)** |
| L8 | Credibility strip | S | none | No |

### Sida 01 · Riksöversikt (`pages/01_Riksoversikt.py`)

| ID | Feature | Class | Dependencies | UX issue | Mod. |
|---|---|---|---|---|---|
| R1 | KPI row: mean SHAI + Δ%, högrisk count, mean K/T + Δ%, population change | C | `affordability_ranked.parquet`, `delta_meta` | Decorative stripes, `title=` tooltips | Yes (variant rule, help) |
| R2 | KPI explanation | C | labels | none | No |
| R3 | Cost history expander | A | G11 | none | No |
| R4 | Choropleth: Folium, empirical scale, zoom-gated labels, tooltips, page legend | C | `choropleth.py`, `map_legend.py`, geojson, Esri tiles | Duplicated scale explanation | Copy de-dup only |
| R5 | Distribution histogram stacked by risk, median line, filter-aware | C | Plotly | none | No |
| R6 | Top-15 least/most affordable tables, filter-aware subtitle | C | `render_table`, `by_risk` | ~720 px tall each on phone | Yes (phone) |
| R7 | Three "Om …" expanders | S | labels | none | No |
| R8 | **New:** full sortable 290-row table with CSV export | A (new) | `st.dataframe`, `st.download_button` | Closes U18 | **Additive (P2)** |

### Sida 02 · Länsjämförelse

| ID | Feature | Class | UX issue | Mod. |
|---|---|---|---|---|
| J1 | County multiselect (in expander) plus count caption | S | none | No |
| J2 | Tabs C and B: 21-county trend (log axis) and HTML legend | C | none | No |
| J3 | County ranking (mean of kommuner plus county level) | C | Card within card | Yes (frame) |
| J4 | Formula expander (LaTeX) | S | none | No |
| J5 | "Varför skiljer sig versionerna åt?" (version table, A formula, cost factor, top and bottom 5 per tab) | A | Top and bottom 5 as Markdown bullets with an inline-styled header | Yes (render_table) |
| J6 | Cost history expander | A | none | No |
| J7 | Robusthet card: class counts C vs B, disagreement sentence, divergent kommuner table | A | Card within card | Yes (frame) |
| J8 | "Om länsjämförelsen" expander | S | none | No |

### Sida 03 · Kommunanalys

| ID | Feature | Class | UX issue | Mod. |
|---|---|---|---|---|
| K1 | Kommun selectbox (default Stockholm) | C | Full width; detached from the KPIs | Layout |
| K2 | KPI row: SHAI + Δ, income, K/T, mortgage rate | C | Decorative stripes | Variant rule |
| K3 | Projection chart (history, county, 3 rate scenarios to 2030), caption, explanation, expander | C | Legend padding hack (keep) | No |
| K4 | Component breakdown (3 mini charts, driver highlight, attribution sentence) | A | Mini-chart titles in 15 px bold compete with the card title | Style |
| K5 | "Om komponenterna" expander | S | none | No |

### Sida 04 · Kontantinsatsanalys

| ID | Feature | Class | UX issue | Mod. |
|---|---|---|---|---|
| I1 | Purpose panel | S | Long; pushes the answer down | Compact |
| I2 | Price-type availability info or warning | S | Off-palette banner | Callout styling |
| I3 | Controls: price type (BR switches to län), region, household, savings rate + SEK/yr, advanced bank margin (resets per year) | C | Good | No (keys unchanged) |
| I4 | Snapshot KPIs: P/I, kontantinsatsbörda, boendekostnadsbörda, tillgänglighet | C | Split from I9 | **Regrouped** |
| I5 | Reachability gap chart | C | SI axis | Axis format |
| I6 | Interpretation findings | C | none | No |
| I7 | Context captions (nuläge, income definition, fallback) | S | none | No |
| I8 | Villa vs bostadsrätt comparison | A | 8 large `st.metric`s, tall | Compact table-style layout |
| I9 | Baseline KPIs: kontantinsats, år att spara, månadskostnad, kvarvarande | C | Split from I4 | **Regrouped** |
| I10 | Regulatory timeline | S | White on gold 2.4:1, 10 px labels | Contrast |
| I11 | Five regime cards with Δ vs today | C | Cramped at < 1400 px; colour collision | Wrap rule |
| I12 | Comparison tabs (3 bar charts, reference lines, best/worst) | C | **Colour collision (U4)** | **Palette REVIEW** |
| I13 | Nyckelinsikt synthesis | C | none | No |
| I14 | "Detaljer och antaganden" (inputs, 15-column styled dataframe with help) | A | none | No |

### Sida 05 · Scenariosimulator

| ID | Feature | Class | UX issue | Mod. |
|---|---|---|---|---|
| S1 | Purpose panel | S | Long | Compact |
| S2 | Scope note (Version C only) | S | Off-palette, between purpose and controls | Callout, moved under purpose |
| S3 | County selectbox (default Stockholms län) | C | none | Into controls card |
| S4 | Four preset buttons writing slider state + rerun | C | "Återställ" has the same weight as the scenarios | Återställ becomes tertiary |
| S5 | Three select sliders: rate pp, income %, price % | C | none | Into controls card |
| S6 | Result KPIs: base, scenario, change (Δ%) | C | none | No |
| S7 | Interpretation findings | C | none | No |
| S8 | Rate × price surface, caption, expander | A | none | No |
| S9 | National outcome: class counts, movement sentence, median | A | none | No |
| S10 | Base vs scenario bar chart | S | Restates S6 | Kept, paired with S11 |
| S11 | Comparison table (`st.dataframe`) | S | Different table style | `render_table` |
| S12 | "Förklaring" expander | S | none | No |

### Sida 06 · Metodologi och källor

| ID | Feature | Class | UX issue | Mod. |
|---|---|---|---|---|
| M1 | Sections 1–4 always open (theory, sources with provenance coverage years, formulas plus cost history, normalisation) | C | Long scroll, no in-page index | Add TOC (P2) |
| M2 | Expanders 5–9 (projection, regime history timeline, limitations F1–F18, validation, references) | C | Timeline contrast | Contrast |
| M3 | Footer with sources | S | none | No |

### Administrative (no UI, not touched)

`scripts/refresh_data.py` (fetch, rebuild, recompute, reproject), `scripts/audit.py`,
`scripts/math_check.py`, `src/data/*` (SCB, Riksbanken and Kolada clients),
`src/provenance_build.py`. These run on a developer's machine. **Experimental:** none
shipped.

---

## A4. Proposed design direction

**Name:** *Nordic institutional.* The working image is a central-bank financial
stability report crossed with a modern fintech ledger.

**Rationale.** SHAI's value is credibility. Its users act on numbers: they quote them,
plan with them or argue about them. The interface should feel like an instrument:

- **calm**, with low chroma and colour spent only on meaning;
- **precise**, with tabular figures, explicit units, aligned columns and Swedish
  formatting;
- **legible**, with AA contrast and a clear heading hierarchy;
- **honest**, with no element that looks interactive and is not, and no colour that
  means two things.

**Reference products.** These are quality benchmarks, not templates.

| Reference | What we take | What we do not |
|---|---|---|
| Stripe Dashboard | Tabular sans figures, quiet tables with strong numeric alignment, muted labels above values | Purple gradient, marketing gloss |
| Mercury | Restraint: white cards on an off-white canvas, hairline borders, almost no shadow | Consumer-banking warmth |
| Linear | Compact, grouped sidebar navigation; clear active state; keyboard focus rings | Dark-first theme |
| Wise | Plain-language explanation beside every money figure (SHAI already does this) | Bright green brand |
| Riksbanken / SCB publications | Institutional typography, source citation, chart annotation discipline | Print-era density |
| Modern Fortnox | Swedish number conventions; status chips with text, never colour alone | Accounting-workflow chrome |

**Design principles** (each change in Part B must satisfy all five):

1. **One meaning per colour.** Risk and status use green, amber and red. Brand and
   selection use navy and gold. Categories and time use neutral data hues.
2. **Answer first, then why, then how.** Headline, explanation, evidence, method.
3. **Every affordance is real.** If it lifts, underlines or changes the cursor, it
   acts.
4. **Figures are typeset, not printed.** Tabular, right-aligned, Swedish, with units
   beside them.
5. **No new decoration.** No gradients beyond the existing hero, no new shadows,
   radius ≤ 8 px, motion only on hover and focus (and none under
   `prefers-reduced-motion`).

**Industry suitability.** A public-statistics product for an analytical audience
needs credibility over delight. The direction keeps the existing identity, so returning
users recognise the product, and removes the defects that undercut its precision.

---

## A5. Proposed information architecture

### Sidebar (G1–G4)

```
SHAI · Bostadsekonomisk hållbarhet        (brand, unchanged)
──────────────────────────────────
Startsida
ANALYS
  Riksöversikt
  Länsjämförelse
  Kommunanalys
VERKTYG
  Kontantinsatsanalys
  Scenariosimulator
REFERENS
  Metodologi och källor
──────────────────────────────────
URVAL                                      (only on pages that read it)
  Valt år            [pills 2014 … 2024]   (landing, 01–05)
  Riskfilter         [Hög][Medel][Låg]     (Sida 01 only)
──────────────────────────────────
Data uppdaterad 2026-10-20 · v1.3.0
```

- **Grouping** follows the user's mental model: *look* (analysis), *calculate*
  (tools), *check* (reference).
- **Labels and order are unchanged**, so muscle memory survives.
- **URLs are unchanged.** `st.page_link` targets stay the same files.
- **Context-aware controls** (REVIEW, see A10): a control appears only where it
  changes something. The persisted session values (`shai_selected_year`,
  `shai_selected_risks`) remain untouched when a page does not render the control, so
  the selection still carries across navigation. That carrying is exactly the existing
  mirror mechanism.
- **Metodologi** shows no year pills, because it describes the whole period. Its page
  header already says "2014–2024".

### Page template (applies to 01–06)

```
[Eyebrow · SIDA 0N · AREA]
[H1 Title]                                   [chip: Analysår 2024] [chip: Data 2026-10-20]
[Subtitle]
────────────────────────────────────────────────────────────────────────────
(tools only) Intro: one-paragraph purpose, with a "När ska jag använda sidan?" disclosure
(tools only) Urval card: every input
Headline: KPI row (≤ 4) + explanation
Primary evidence: chart or map
Detail: tables, secondary charts
Reference: "Om …" expanders, formulas
Footer
```

### User journeys improved

| Journey | Today | Proposed |
|---|---|---|
| First visit, "how bad is it?" | Hero, stats, three explainer blocks; the first finding is on Sida 01 | Landing shows **"Läget 2024"** (mean index, number of hög-risk kommuner, least and most affordable kommun) with a link straight to Riksöversikt (P2, UX-18) |
| Landing to a page | Read a card, then find the same name in the sidebar | Click the card (UX-05) |
| "Can my household afford X?" (Sida 04) | Purpose, banner, controls, 4 KPIs, chart, findings, captions, villa/BR, 4 more KPIs, timeline, regimes, tabs, insight | Intro, controls, **one answer block** (8 KPIs in 2 tiers), findings, reachability, regimes (timeline, cards, tabs), villa/BR, insight, details |
| "Find my kommun's rank" | Only top and bottom 15 | Full sortable table plus CSV (P2, UX-14b); or Kommunanalys |

---

## A6. Page-by-page redesign specification

The following applies to every page and is not repeated per page:
- tokens, contrast, header and chips (UX-01, UX-02, UX-08);
- tabular sans figures (UX-03);
- callout styling (UX-10);
- KPI variant rule (UX-09);
- chart axis formatting (UX-11).

Each page section lists only what is specific to that page.

### Landing (`app.py`, `src/ui/landing.py`)

**Current.** Hero, a 4-cell stat strip, an explanation and vintage, "Vad är SHAI?",
"Indexet i överblick" (Version B weight bars and a flow SVG), 3 steps, 6 inert nav
cards in a 3 × 2 grid, and a credibility strip.

**Problems.** U2, U14, plus hardcoded hex values in the SVG and inline `style=`.

**Proposed layout.**
1. Hero (unchanged copy, tightened padding) with the stat strip attached.
2. **Läget {year}** (P2, UX-18). Three KPI cards read from
   `affordability_ranked.parquet` for the year selected in the sidebar:
   - "Genomsnittligt SHAI" (% av inkomsten);
   - "Högriskkommuner" (N av 290);
   - "Störst och minst ansträngt" (Lidingö / Åsele).

   They are followed by an `explanation()` and a `st.page_link` to Riksöversikt
   labelled "Öppna Riksöversikt". All figures are interpolated, never typed (guarded
   by `test_copy_matches_artifacts`).
3. "Vad hittar du här?" — the **six nav cards become real links** (UX-05). Each card is
   a bordered container holding the tag, title and description, plus an
   `st.page_link` stretched over the card. The cards are grouped by the same three
   sidebar groups.
4. "Vad är SHAI?" (unchanged).
5. "Så räknas indexet": the three steps, then the **flow SVG** with colours from
   tokens. The **Version B weight bars** move under a sub-heading that states they
   are Version B's (`landing.vikter_version_b` already says so). They no longer sit
   under a section implying they *are* the index.
6. Credibility strip and footer.

**Responsive.** The nav grid goes from 3 to 2 columns at 900 px and to 1 at 520 px.
Läget KPIs stack.

**Must remain unchanged.** Every block and every string, the nav targets, the
`_panel_facts` resolution, and `st.html` for the steps (it avoids the Markdown
code-block bug).

### Sida 01 · Riksöversikt

**Current layout.**
- KPI row of 4 cards, with an explanation.
- Cost-history expander and vintage.
- The map (3/5 width) beside the histogram (2/5), each in a bordered card with a
  caption, an explanation and an "Om …" expander.
- Top-15 tables, 2 columns, with an explanation and an expander.

**Problems.** U3/U5/U12/U16/U17/U18.

**Proposed.**
- **KPI variants:**
  - mean SHAI: neutral;
  - högrisk count: *danger*, since it is a count of a risk status;
  - K/T: neutral;
  - population: neutral.
- KPI tooltips become `help_badge` terms in the label where a glossary entry exists.
  The `title=` attribute stays as a fallback.
- **Map card:** keep the in-page legend. Merge the two scale captions into one: keep
  `rv.forklaring_karta` as the `explanation()` and drop the near-duplicate `st.caption`
  `rv.fargskala_*` *only if* the explanation guard still passes. Otherwise keep both,
  styled as one block.
- **Risk filter (REVIEW).** It renders in the sidebar on this page only (UX-07),
  unchanged in behaviour. Above the tables, a one-line status reads "Filtrerat:
  Hög, Medel" whenever a filter is active. It uses `_table_subtitle`, which already
  exists.
- **Tables.**
  - Keep the two side-by-side top-15 cards.
  - On ≤ 640 px they stack, and the table body becomes horizontally scrollable inside
    its card instead of the page.
  - Rank column 32 px. Kommun names stay links-free.
- **New (P2, UX-14b).** An expander "Alla {N} kommuner" with
  `st.dataframe(hide_index=True)`. The columns are rank, kommun, län, SHAI (% av
  inkomsten), z, risk (text), median income and mean price, and every column is
  sortable. It ships with a `st.download_button` "Ladda ner CSV" (UTF-8 with BOM,
  `;` separator and a decimal comma, so it opens correctly in Swedish Excel). It is
  built from `mun_year`, *not* the filtered frame, and its caption states that the
  risk filter does not apply.

**Must remain unchanged.**
- The map is always drawn from `mun_year`, never the filtered frame.
- The histogram and tables are drawn from `df_ranked`, the filtered frame.
- The empty state.
- The 2014 "no previous year" handling.
- `render_cost_history` placement.

### Sida 02 · Länsjämförelse

**Current.**
- A county picker in an expander, with a count caption.
- Tabs C and B, each holding a trend chart with an HTML legend, a ranking table and a
  formula expander.
- The comparison expander and the cost history.
- The Robusthet card and an "Om" expander.

**Problems.** U7 (card in card, twice); J5 Markdown lists with inline styles.

**Proposed.**
- `render_table(..., framed=False)` wherever the table already sits inside
  `st.container(border=True)`. This applies to the ranking, both Robusthet tables and
  the cost-history table. It removes the double frame.
- J5's top and bottom 5 per tab become two compact `render_table`s ("Lägst kostnad" and
  "Högst kostnad", rank / län / värde). This replaces the bullets and the inline
  `style=` header.
- **Tabs:** the active tab label uses `accent_strong` text (AA) with the gold underline.

**Must remain unchanged.**
- Two tabs, not three.
- The colour per county keyed by code.
- An empty county selection hides the chart only.
- Every figure in the Robusthet section.

### Sida 03 · Kommunanalys

**Current.** A full-width kommun selectbox, then a KPI row, the projection card, the
components card and an "Om" expander.

**Proposed.**
- The **selectbox sits in a two-column row**: selector (2/5) and a short context line
  (3/5), "{kommun} · {län} · Analysår {year}". The selector no longer stretches
  1 000 px for a 12-character name.
- **KPI variants:** SHAI is *neutral*; its Δ already carries the sentiment colour.
- **Component mini-charts:**
  - the chart `title` font drops to 13/600 `text_secondary`, so it ranks below the card
    title;
  - the driver highlight stays (accent colour plus a thicker line), and the driver
    chart gets a "Störst påverkan" text badge, so the highlight is not colour-only.

**Must remain unchanged.**
- `_LEGEND_PAD` and the vertical-legend workaround (measured browser behaviour).
- Projection anchoring at the county's last year.
- The `attribute_change` sentence.

### Sida 04 · Kontantinsatsanalys

**Current order.** Purpose, price-type banner, controls card, snapshot KPIs, gap
chart, findings, 2–3 captions, villa vs BR, baseline KPIs, timeline, regime cards,
comparison tabs, insight, details, footer.

**Problems.** U4, U6, U8, U9, plus the timeline contrast (I10).

**Proposed order** (no section removed; only `render_*` call order and grouping
change):
1. **Intro** (compact purpose panel). This is the first paragraph plus the "Använd
   sidan för att" list, inside a closed `st.expander("Mer om sidan")` holding the
   second paragraph. The price-type note becomes a callout *inside* the controls card,
   under the Pristyp radio, where it explains the radio.
2. **Urval** card (unchanged controls and keys).
3. **Svaret** (answer) card: one bordered container holding two KPI tiers.
   - *Tier 1* (large): Kontantinsats (idag), År att spara, Månadskostnad (idag),
     Tillgänglighet.
   - *Tier 2* (compact, smaller type, one row): Pris/inkomst-kvot,
     Kontantinsatsbörda, Boendekostnadsbörda, Kvarvarande inkomst.

   All eight metrics, labels and tooltips are kept; `render_snapshot` and
   `render_baseline_kpis` are re-composed, not rewritten. The context captions (I7)
   sit at the foot of this card.
4. **Tolkning:** the findings panel (I6), unchanged.
5. **Räckvidd:** the gap chart (I5) with Swedish axis ticks.
6. **Regelverken:** one section heading over the timeline (I10, AA labels), the regime
   cards (I11) and the comparison tabs (I12).
   - Regime cards: 5 across at ≥ 1280 px, 3 + 2 below that, 1 per row on a phone. The
     CSS min-width rule already exists for chart columns and is extended to this row.
   - **Regime palette (REVIEW, see A10):** the regimes take a chronological
     slate-to-navy ramp, and the current regime (Lättnad 2026) takes gold. In the
     comparison tabs, best and worst are marked with a **text annotation**
     ("Lägst" / "Högst") and a bar outline rather than with a green or red fill.
     Risk colours then mean only risk.
7. **Villa vs bostadsrätt** (I8). Two columns of label/value rows, using a compact
   `render_table` with 4 rows × 3 columns (Mått / Småhus / Bostadsrätt) instead of
   8 large `st.metric`s. The same figures appear and the card is about 60 % shorter.
8. **Nyckelinsikt** (I13), unchanged.
9. **Detaljer och antaganden** (I14), unchanged.

**Responsive.** On a phone the page shortens from about 8 400 px to roughly
5 500–6 000 px (estimate; measured in UX-17). The gains come from the compacted intro,
the villa/BR table and the tier-2 KPI strip.

**Must remain unchanged.**
- Every computed figure.
- `compare_regimes`, `apply_regime` and `_best_and_worst` logic.
- The margin-slider reset per year.
- The BR → län switch and fallback note.
- The styled 15-column dataframe with its best/worst highlighting. That highlighting
  is *background tint plus explicit column help* and is kept, because the table
  carries no risk meaning.

### Sida 05 · Scenariosimulator

**Current order.**
- Purpose, then the scope info.
- The county select, a "Förinställda scenarier:" label, 4 equal buttons and 3 sliders.
- The KPI row, findings, the surface, the national outcome, the bar chart with the
  dataframe, and the Förklaring expander.

**Proposed.**
1. **Intro:** compact purpose; the scope note becomes a `note` callout directly under
   it.
2. **Scenario** card (bordered) holding:
   - the county select (2/5 width);
   - "Förinställda scenarier" as a label, with the three scenario buttons as
     `type="secondary"` and **Återställ as `type="tertiary"`**, right-aligned;
   - the three sliders.

   The keys are unchanged, and so are the preset → session_state → `st.rerun()` flow.
3. **Resultat:** KPI row plus findings (unchanged).
4. **Ränta och pris tillsammans:** the surface (unchanged).
5. **Samma scenario för hela riket** (unchanged).
6. **Basfall mot scenario:** the bar chart (3/5) and the comparison table (2/5) via
   `render_table`. This replaces `st.dataframe`, gives the same 4 rows × 3 columns,
   and puts the numeric columns right-aligned.
7. Förklaring expander.

**Must remain unchanged.**
- The simulator call.
- `interpret_scenario`.
- `shock_panel` with its fixed class boundaries.
- Slider option grids, which the chart guard asserts lie on the surface grid.

### Sida 06 · Metodologi och källor

**Proposed.**
- **(P2) Table of contents** under the header: a horizontal list of anchor links
  "1 Vad SHAI mäter · 2 Data och källor · … · 9 Referenser" to `id`s on the section
  card headers.
- Markdown tables (sections 1 and 2) get the `.shai-table` look via a scoped CSS rule
  on `[data-testid="stMarkdown"] table` inside the main area. This uses the same
  header rule, padding and hover, and changes no markup.
- Timeline labels (expander 6) are made AA.

**Must remain unchanged.** Every section and its order, the expanders, every figure
read from provenance, and the `render_cost_history` try/except.

---

## A7. Component and design-system changes

### Colour tokens (`src/ui/tokens.py`; documented in `docs/DESIGN_SYSTEM.md` §2)

| Token | Value | Use | Change |
|---|---|---|---|
| `primary` | `#0B1F3F` | Sidebar, primary marks, hover-label background | — |
| `primary_light` | `#1B2A4A` | Hero gradient | — |
| `secondary` | `#4A6FA5` | Data blue, info | — |
| `accent` | `#C4A35A` | Gold **fills only**: active pill, underline, brand bar, bar fills | Rule change |
| `accent_strong` | `#8A6A1F` | **New.** Gold *text* on light (5.05:1); Streamlit `primaryColor` | New |
| `low_risk` / `medium_risk` / `high_risk` | unchanged | Risk fills, dots, stripes | — |
| `medium_risk_text` | `#8A5A00` | **New.** "MEDEL" pill text (5.93:1) | New |
| `bg` / `card_bg` | unchanged | Canvas, cards | — |
| `text_primary` | `#1A1A2E` | Body, values | — |
| `text_secondary` | `#4B5563` | Secondary body (7.56:1) | **Was `#6B7280`** |
| `text_muted` | `#6B7280` | **New.** Labels, captions, tags, units (4.83:1) | New |
| `text_tertiary` | `#9CA3AF` | **Decorative only**: rules, dots, disabled. **Never text.** | Rule change |
| `border` | `#E3E6EC` | Card and container border | **Was `#EEF0F3`** |
| `border_subtle` | `#EEF0F3` | Table row rules, dividers | New name for the old value |
| `grid` / `hover` | unchanged | Chart grid / row hover | — |
| `focus` | `#4A6FA5` | **New.** 2 px focus ring on light (5.0:1); gold on navy | New |
| `sidebar_muted` | `#A3AAC2` | **New.** Sidebar footer and labels on navy (≥ 6:1) | New |
| `REGIME_RAMP` | `#8592A8 #6B7FA0 #566C91 #2A4068` + `accent` | **New.** Chronological regimes (REVIEW); each ramp step ≥ 3:1 on white | New |

Tints are derived, not new hues: `low_risk_bg`, `medium_risk_bg` and `high_risk_bg`
at 12 %, and `info_bg` (secondary at 8 %).

**`primaryColor`** in `.streamlit/config.toml` moves from `accent` to
`accent_strong`. This makes the active tab label, the slider thumb and value text, and
the radio dots AA-compliant. Sidebar pills are custom-styled and keep solid gold.
`tests/test_design_system_doc.py::test_the_accent_token_is_tied_to_the_streamlit_theme`
is updated to tie `primaryColor` to `accent_strong` (a deliberate, documented change).

**Mechanism (UX-01).**
1. `css.py` generates a `:root{ --shai-c-<token>: <hex>; … }` block from `COLORS`
   and places it first in `GLOBAL_CSS`, after the `@import`.
2. Every `#hex` in `css_*.py` becomes `var(--shai-c-<token>)`.
3. A new test asserts that `css_*.py` contains no 6-digit hex literal.

`css_landing.py`'s gradient stops are `primary` and `primary_light`; the third stop
(`#0F2847`) becomes `primary`.

### Typography

| Role | Family | Size / weight / line-height | Notes |
|---|---|---|---|
| Display (KPI value) | Source Sans 3 | `clamp(24px, 2.3vw, 32px)` / 700 / 1.15; **28 px at ≤ 640 px** | `tabular-nums lining-nums` |
| H1 page title | Source Sans 3 | 28 / 700 / 1.2 | Rendered as `<h1>` |
| H2 section | Source Sans 3 | 18 / 700 / 1.3 | New `.shai-section-heading` for grouped sections (Sida 04 "Regelverken") |
| H3 card title | Source Sans 3 | 15 / 700 | `.shai-card-title` |
| Body | Source Sans 3 | 14–15 / 400 / 1.6 | — |
| Small / caption | Source Sans 3 | 12.5–13 / 400 | `text_muted` |
| Label (uppercase) | Source Sans 3 | **11 / 600, tracking 0.08em** | Minimum 11 px; card tags rise from 9.5 px and move off mono |
| Figures in tables and deltas | **Source Sans 3**, `tabular-nums` | 13 / 500 | **Replaces IBM Plex Mono** |
| Code (version string only) | IBM Plex Mono | 11 / 400 | Footer `<code>` |

Plotly bar text labels switch from `MONO_FONT` to `CHART_FONT`. The `MONO_FONT`
constant stays exported, so imports do not break.

### Spacing, radius, elevation

- **Scale (CSS vars):** `--shai-space-1…7` = 4, 8, 12, 16, 24, 32, 48 px.
- **Section gap:** 24 px between top-level blocks. Card padding is 20 px × 24 px.
- **Spacer helper:** `src/ui/components.py::spacer(size: "sm"|"md"|"lg")` emits
  `st.space`, which exists in 1.56. It replaces all 18 inline spacer divs.
- **Radius:** `--shai-radius-sm` 4 px (pills, inputs, tags) and `--shai-radius-md`
  6 px (cards, containers, callouts, hero).
- **Elevation:** none on cards. Only the help popover keeps its shadow.
- **Hover:** a lift happens only on real links (landing nav cards after UX-05).

### Components

| Component | Rule | Change |
|---|---|---|
| **KPI card** | Stripe = **meaning, not decoration**. `default` (navy) for neutral figures; `danger`, `success` or `accent` only when the *value itself is a status* (a risk-class count, Tillgänglighet). Δ colour comes from `delta_meta` sentiment (unchanged). | Variant usage audited on all pages; new `size="compact"` for tier-2 rows; `help=` terms render a `help_badge` in the label |
| **Card header tag** | Uppercase label, 11 px, `text_muted`, Source Sans | Off mono, larger, AA |
| **Table** (`render_table`) | The only producer of `.shai-table`; `framed: bool = True` | New `framed=False` emits no `.shai-card` wrapper; wrapped in `.shai-table-scroll` (overflow-x auto) for phones |
| **Risk pill** | Always text plus colour | Medel text uses `medium_risk_text` |
| **Callout** | `st.info`, `st.warning`, `st.error` and `st.success` restyled by CSS on `[data-testid="stAlert"]` (`stAlertContainer` in 1.56 — verify): white background, 3 px left stripe in the semantic colour, `text_primary` body | No call-site changes needed |
| **Buttons** | Primary actions `secondary`; resets and undo `tertiary` | Sida 05 Återställ |
| **Tabs** | Active: `accent_strong` text, gold 2 px underline | Through `primaryColor` + CSS |
| **Page header** | `<h1>`; right side shows **chips**: "Analysår 2024" and "Data 2026-10-20" | Replaces the 36 px grey year; the vintage chip replaces the separate `vintage_badge()` call (the test is updated to accept either) |
| **Sidebar link** | Visible `:focus-visible` (2 px gold outline on navy); active = gold left bar (existing) | Focus style added |
| **Section heading** | New `section_heading(title, subtitle="")` → `<h2 class="shai-section-heading">` | Sida 04 "Regelverken", Sida 05 "Resultat" |
| **Help badge** | Mark border and text `accent_strong` | Contrast |
| **Empty / error** | `st.error(L(...))` + `with st.expander(L("ui.tekniska_detaljer")): st.code(str(e))` | Replaces the raw `st.caption(f"Detaljer: {e}")` on 8 call sites |
| **Loading** | `st.spinner(L("ui.laddar_data"))` | Same text, from labels |

### Charts (`src/ui/chart_theme.py`)

- **New helpers:**
  - `sek_axis(layout, axis="y")`: tickformat `",.0f"` with the Swedish separators
    already set by `separators`. "8 000 000", not "8M".
  - `pct_axis(layout, axis)`: ticksuffix `" %"`.
- **Applied to:** `affordability_gap_chart` (x axis), `comparison_barchart` (y axis,
  when SEK), and Sida 03's component charts (already set by hand; migrated to the
  helper).
- **Bar text labels:** `CHART_FONT`, tabular, size 12.
- **Regime colours:** `REGIME_RAMP` (REVIEW). Best and worst are shown with an
  annotation and a 2 px `primary` outline instead of a fill override.

### Navigation

Covered in A5. The CSS adds `.shai-sidebar-section-label` usage per group (the class
exists) and a `:focus-visible` rule.

---

## A8. Industry-specific improvements

| Requirement | How the redesign meets it |
|---|---|
| Consistent currency | Every SEK on screen goes through `format_sek` or `format_tkr`. Chart axes move from SI to Swedish grouping (UX-11). Units sit beside values ("SEK", "SEK/år", "% av inkomsten", "pp"). |
| Percentages and precision | Existing policy is kept: SHAI to 1 dp, z to 2 dp, rates to 2 dp. "%" and "procentenheter" stay distinct (Sida 05 already does this). |
| Negative values | True minus `−` (existing). Tabular figures (UX-03) keep minus signs aligned in columns. Never colour alone: Δ has an arrow plus sign plus colour. |
| Actual vs projected | Sida 03 keeps the solid observed line and dashed projections. The "Projektion" tag and the "inte en förutsägelse" explanation stay adjacent. |
| Units and dates | Header chips state the analysis year and the data vintage on every page (UX-08). |
| Colour for outcome | One meaning per hue (U4, U5). The risk pill always carries text. The driver highlight on Sida 03 gets a text badge. |
| Numeric alignment | Right-aligned tabular sans in every table, including Metodologi's Markdown tables (UX-19). |
| Table capability | Full sortable table plus a CSV export in a Swedish-Excel-safe format (UX-14b). The 15-column regime table keeps its column help. |
| Trust and clarity | Header chip "Data {date}". Scope notes become consistent callouts, positioned beside the control or result they qualify (Sida 04 Pristyp, Sida 05 scope). Sources stay cited on Metodologi only (existing deliberate decision). |
| Next action | Landing cards become links. Läget KPIs link to Riksöversikt. The Sida 04 findings already end with an action ("Välj Par ovan…"). |

---

## A9. Performance and technical improvements

1. **CSS variables from tokens.**
   - One source of truth.
   - The injected sheet stays about 24 KB (R13 accepted). The `:root` block adds about
     1 KB and replaces repeated literals, so the net size is about the same.
2. **Shared helpers** (`spacer`, `section_heading`, the `render_table(framed=False)`
   parameter, `sek_axis`) remove duplicated inline styles.
3. **No new dependencies.**
   - AgGrid was evaluated and rejected: `st.dataframe` with `column_config` already
     gives sorting, column help, number formats and CSV.
   - A Lucide/icon library was evaluated and rejected: the product uses text labels.
     Streamlit's built-in Material icons (`:material/…:`) are available if a page link
     needs one, with no install. They are not used by default, because icons add
     little to six text links.
4. **Reruns.**
   - The Sida 01 risk filter re-renders the Folium iframe on every click. Moving the
     filter into an `st.fragment` would isolate it, but fragments cannot write into
     columns created outside them, and the histogram shares a row with the map. This is
     deferred (P3, UX-21) because it needs a layout change to do safely.
   - Sida 05's sliders rerun the whole page in about 300 ms, which is acceptable.
     A fragment is deferred (P3).
5. **`st.navigation` migration** was evaluated. It would give native grouping and URL
   control through `st.Page(url_path=…)`. It is **deferred (P3, UX-22)** because:
   - it moves the landing content out of `app.py`;
   - it changes how `AppTest` drives pages (`test_pages_render` relies on
     `switch_page` from `app.py`);
   - the custom `st.page_link` rail already achieves grouping.
6. **Semantics.** `<h1>`/`<h2>` headings and `aria-label`s on chips improve
   screen-reader navigation at no runtime cost. Streamlit's auto header anchors on
   raw-HTML headings are hidden by CSS
   (`[data-testid="stHeaderActionElements"]{display:none}`).

---

## A10. Feature preservation matrix

The default is **preserve**. Rows marked **REVIEW** change visible behaviour and need
explicit approval. Each has a safer fallback.

| Existing feature | Current implementation | Proposed change | Functionality preserved? | Risk |
|---|---|---|---|---|
| G1 Sidebar nav | 7 flat `st.page_link` | Grouped under 3 labels, focus style | Yes (same targets, same order) | Low |
| G2 Year selector | Pills on every page, mirrored to `shai_selected_year` | **REVIEW:** not rendered on Metodologi (which ignores it). Still rendered on landing, because UX-18 makes landing read it; if UX-18 is deferred, also hidden there | Yes: the mirror value persists when the widget is absent, so the selection carries to the next page | Low–Med. Fallback: render on every page with a caption "Gäller inte denna sida" |
| G3 Risk filter | Pills on every page, read only by Sida 01 | **REVIEW:** rendered only on Sida 01, still in the sidebar, same key and semantics | Yes: `shai_selected_risks` persists; Sida 01 output identical | Low–Med. Fallback: keep on all pages with a caption "Påverkar endast Riksöversikt" |
| G4 Risk legend | Sidebar on every page | Moves with G3 (Sida 01 only); the map legend and pills carry the meaning elsewhere | Yes (informational) | Low |
| G6 Vintage badge | `vintage_badge()` at varying positions | A chip in the page header; the standalone call is removed and the test accepts `page_title(..., vintage=True)` | Yes (same source, `generated_at()`) | Low |
| L5 Weight bars | Under "Indexet i överblick" | Same bars under a sub-heading naming Version B | Yes | Low |
| L7 Nav cards | Inert HTML | Clickable `st.page_link` cards | Yes, improved; session state preserved by `page_link` | Low |
| R1, K2, I4/I9, S6 KPI rows | `kpi_card` with mixed variants | Variant rule; `help_badge` for terms | Yes (same values and Δ) | Low |
| R4 Map captions | Caption plus explanation (near-duplicate) | One explanation | Yes (content kept in the remaining text) | Low |
| R8 Full table / CSV | None | **New**, additive | n/a | Low |
| J3/J7 Tables | `.shai-card` inside a bordered container | `framed=False` | Yes | Low |
| J5 Top/bottom 5 | Markdown bullets | `render_table` | Yes (same rows and values) | Low |
| I1 / S1 Purpose panels | Full panel | First paragraph and list visible; second paragraph in "Mer om sidan" | Yes (all text reachable) | Low |
| I4 + I9 KPI rows | Two rows separated by other sections | One answer card, two tiers | Yes (all 8 metrics, tooltips) | Low |
| I8 Villa vs BR | 8 `st.metric` | 4 × 3 `render_table` | Yes (same 8 values) | Low |
| I11/I12 Regime colours | Risk palette as categories; green/red also best/worst | **REVIEW:** chronological `REGIME_RAMP` with the current regime in gold; best/worst by annotation and outline | Yes: same bars, values, ranking logic and reference lines. Changes the visual message that "Amort 2.0 = red = bad" | Med. Fallback: keep regime colours, drop only the best/worst fill override (annotation only) |
| S4 Presets | 4 equal buttons | Återställ becomes tertiary | Yes (same keys and handler) | Low |
| S11 Comparison table | `st.dataframe` | `render_table` | Yes (same 4 × 3 values); loses `st.dataframe`'s column-resize and copy, which have no use on 4 rows | Low |
| `primaryColor` | `accent` `#C4A35A` | `accent_strong` `#8A6A1F` | Yes (visual only); a test is updated | Low |
| Error states | `st.caption(f"Detaljer: {e}")` | Details in a collapsed expander | Yes (same information) | Low |
| Every calculation, artifact, widget key, URL and Swedish label | — | **Unchanged** | Yes | — |

---

## A11. Expected outcomes

| Improvement | Usability | Consistency | Accessibility | Productivity | Maintainability |
|---|---|---|---|---|---|
| Contrast tokens (UX-02) | Readable labels and tags | One text hierarchy | **AA for all text** | — | Rules encoded in tokens and a test |
| CSS variables (UX-01) | — | Exact colour parity CSS ↔ Plotly | — | — | **130 literals → 1 generated block**; palette change in one file |
| Clickable nav cards (UX-05) | One click from landing | Affordance = action | Keyboard-focusable links | Fewer steps | — |
| Context-aware sidebar (UX-07) | No inert controls | — | Shorter focus order | Less to scan | — |
| Regime palette (UX-12) | Unambiguous charts | One meaning per hue | Not colour-only | Faster reading | Palette in tokens |
| Sida 04 restructure (UX-12) | Answer in the first screen after the controls | Same template as other pages | — | ~30 % less scrolling | Sections re-composed, not rewritten |
| Tabular sans figures (UX-03) | Easier column scanning | One numeric voice | — | — | — |
| Tables `framed` + scroll (UX-09/16) | No double frames; phones scroll the table, not the page | One table style | — | — | One renderer |
| Full table + CSV (UX-14b) | Find any kommun's rank | — | Sortable by keyboard | Export for analysis | Built on native `st.dataframe` |
| Semantic headings, focus, help badges (UX-08/16) | — | — | Screen-reader landmarks, keyboard, touch | — | — |

---

# PART B: STEP-BY-STEP IMPLEMENTATION ROADMAP

## B1. Implementation principles

1. **Preserve behaviour.**
   - No change to `src/indices/`, `src/data/`, `src/projection.py`,
     `src/kontantinsats/engine.py`, `src/scenario/simulator.py`,
     `src/scenario/panel_scenario.py` or any artifact.
   - No widget key renamed. No URL changed.
2. **One task, one commit** (or a short series), message `ux(<id>): …`, on branch
   `ux/modernization`.
3. **Respect the existing guards; never weaken one to pass.**
   - **Copy:** user-facing Swedish goes in `src/ui/labels.py`, and HTML blocks in
     `src/ui/templates.py`. Figures are interpolated, never typed.
   - **CSS classes:** every new class is prefixed `shai-` and added to
     `docs/DESIGN_SYSTEM.md` §3, with the stated count updated.
   - **Files:** ≤ 400 lines per module (except `labels.py`).
   - **Charts:** use `get_chart_layout` with token colours and
     `displayModeBar: "hover"`.
   - **Pages:** keep `explanation()` and "Om …" expanders on every page.
   - **Tests:** a test is changed only where this plan says so, and the reason goes in
     the commit message.
4. **Test after every task.**
   - Run `pytest -m "not browser and not network" -q`. It takes about 1 minute and
     must stay at ≥ 1376 passed, plus any new tests.
   - After a task that changes visible layout, also run
     `pytest tests/test_browser_render.py tests/test_pages_text_fit.py -q`.
5. **Screenshot after every visual task** with the baseline script (UX-00). Compare
   the screenshots side by side.
6. **Reversible.** No task depends on a later one. Each commit can be reverted alone,
   except where B2 lists a dependency.
7. **Stop on red.** If a task breaks a test that the plan does not anticipate, stop,
   diagnose the cause and report it. Do not adjust the test to match.

## B2. Prioritized task breakdown

| ID | Title | Pri. | Depends on | Est. | Risk |
|---|---|---|---|---|---|
| UX-00 | Branch, full baseline, screenshot tool | P0 | — | 1 h | Low |
| UX-01 | Token layer: CSS custom properties, spacing scale, `spacer()` | P0 | 00 | 4 h | Med |
| UX-02 | Contrast-compliant text tokens and `primaryColor` | P0 | 01 | 1.5 h | Low |
| UX-03 | Tabular sans figures; type scale | P1 | 01 | 2 h | Low |
| UX-05 | Clickable landing navigation cards | P0 | 01 | 1.5 h | Low |
| UX-06 | Grouped sidebar navigation and focus states | P1 | 02 | 1.5 h | Low |
| UX-07 | Context-aware sidebar controls (**REVIEW**) | P0 | 06 | 2 h | Med |
| UX-08 | Page header: `<h1>`, year and vintage chips | P1 | 02 | 1.5 h | Low |
| UX-09 | Card/table framing, KPI variant rule, compact KPI, help in KPI labels | P1 | 03 | 2 h | Low |
| UX-10 | Callout theming for alerts; error-detail expander | P1 | 02 | 1 h | Low |
| UX-11 | Chart number formatting and bar-label font | P1 | 03 | 2 h | Low |
| UX-12 | Sida 04 restructure and regime palette (**REVIEW**) | P1 | 09, 10, 11 | 4 h | Med |
| UX-13 | Sida 05 restructure | P1 | 09, 10 | 2.5 h | Low |
| UX-14a | Sida 01 refinements | P1 | 09 | 1 h | Low |
| UX-16 | Responsive and accessibility pass | P1 | 01–14a | 2.5 h | Med |
| UX-17 | QA, regression, docs, final report | P0 | all | 6 h | — |
| **P0 + P1 subtotal** | | | | **36 h** | |
| UX-14b | Sida 01 full sortable table and CSV export | P2 | 14a | 1.5 h | Low |
| UX-15 | Sida 02 and 03 tidy-up | P2 | 09 | 2 h | Low |
| UX-18 | Landing "Läget {year}" snapshot and section regroup | P2 | 05, 07 | 2.5 h | Low |
| UX-19 | Metodologi TOC and Markdown-table styling | P2 | 01 | 1.5 h | Low |
| UX-20 | Loading label unification | P3 | 10 | 0.5 h | Low |
| UX-21 | `st.fragment` for the Sida 01 filter and Sida 05 sliders | P3 | 07, 13 | 3 h | Med |
| UX-22 | `st.navigation` migration | P3 | — | 4 h+ | High |
| UX-23 | Dark theme | P3 | 01 | 6 h+ | Med |

The **committed scope is P0 + P1 (36 h)**. The P2 items are 7.5 h together; about 4 h
fit in the Day 4–5 buffer, in the order UX-14b, UX-18, UX-15, UX-19. Anything that
does not fit is reported as deferred. **P3 is deferred**, listed for completeness.

The B4 prompts give each task's description, objective, files, instructions, expected
outcome, acceptance criteria and estimate. Each prompt is self-contained.

## B3. Five-day implementation schedule

| Day | Hours | Tasks | Exit check |
|---|---|---|---|
| **1 · Foundation** | 8.5 | UX-00 (1) · UX-01 (4) · UX-02 (1.5) · UX-03 (2) | Suite green. Screenshots show identical layout with darker gold/grey text and sans figures. No hex left in `css_*.py`. |
| **2 · Shell and navigation** | 8.5 | UX-05 (1.5) · UX-06 (1.5) · UX-07 (2) · UX-08 (1.5) · UX-09 (2) | Landing cards navigate and keep the selected year. Sidebar is grouped. Risk filter only on Sida 01. Headers carry chips. No card-in-card. |
| **3 · Main pages** | 8 | UX-10 (1) · UX-11 (2) · UX-12 (4) · UX-13 start (1) | Sida 04 in the new order with all 8 KPIs present. Swedish axes. Callouts on-palette. |
| **4 · Remaining pages and responsive** | 8 | UX-13 finish (1.5) · UX-14a (1) · UX-16 (2.5) · buffer for P2: UX-14b (1.5), UX-18 start (1.5) | Browser and text-fit suites green at 1440, tablet and 390 px. |
| **5 · QA and refinement** | 8 | UX-18 finish if started (1) · UX-17 (6) · fixes (1) | Full suite, including browser, green. Regression checklist B5 complete. Docs updated. Final report written. |

If Day 3 overruns, UX-12's regime palette (REVIEW) drops to the fallback in A10
(annotation-only best/worst). If Day 4 overruns, all P2 work is deferred. QA (UX-17)
is never shortened.

---

## B4. Implementation prompts

Each prompt below is self-contained. Give them to Claude Code in this order. Every
prompt implicitly includes the **standing constraints** below. Paste them with the
first prompt of a session.

> **Standing constraints for every SHAI UX task.**
>
> **Context.**
> - This is a Streamlit 1.56 app (Python 3.11).
> - `app.py` is the landing page and `pages/01–06` are the pages.
> - The shared UI kit is in `src/ui/`. Page sections are in `src/kontantinsats/`,
>   `src/scenario/` and `src/lan/`.
> - Work on branch `ux/modernization`.
>
> **Never change:**
> - calculations or the domain modules (`src/indices/`, `src/data/`,
>   `src/projection.py`, `src/kontantinsats/engine.py`, `src/scenario/simulator.py`,
>   `src/scenario/panel_scenario.py`);
> - artifacts in `data/`;
> - widget `key=` values;
> - page filenames or URLs;
> - existing Swedish label text, unless the task says so.
>
> **Guards that must stay green, and how to satisfy them:**
> - New user-facing Swedish strings go in `SWEDISH_LABELS` in `src/ui/labels.py`, read
>   through `L()`. HTML blocks go in `src/ui/templates.py`, read through `T()`
>   (`tests/test_no_inline_copy.py`, `tests/test_labels.py`). Any figure in copy is
>   interpolated from data (`tests/test_copy_matches_artifacts.py`).
> - Every CSS class is prefixed `shai-` and listed in `docs/DESIGN_SYSTEM.md` §3 with
>   the stated count updated (`tests/test_css_naming.py`,
>   `tests/test_design_system_doc.py`).
> - Modules stay ≤ 400 lines (`tests/test_file_sizes.py`).
> - Charts use `get_chart_layout`, colours from `src/ui/tokens.py` or
>   `src/ui/chart_theme.py` only, and `config={"displayModeBar": "hover"}`
>   (`tests/test_chart_theme_guard.py`).
> - Every page keeps an `explanation()` call, an "Om …" expander whose title comes
>   from labels, and the data vintage (`tests/test_ui_affordances.py`).
> - `inject_css()` remains the single injection point.
>
> **Verify:**
> - Run `pytest -m "not browser and not network" -q` (baseline 1376 passed,
>   1 skipped).
> - For layout changes, also run
>   `pytest tests/test_browser_render.py tests/test_pages_text_fit.py -q`.
> - Run `python scripts/ux_screenshots.py --tag <task-id>` and inspect the PNGs.
> - If an unrelated test fails, stop and report it. Do not edit tests beyond what the
>   task names.
>
> **Finish:** commit as `ux(<task-id>): <summary>` and tick the task's rows in
> `docs/UX_CHECKLIST.md`.

---

### UX-00 · Branch, full baseline and screenshot tool (P0, 1 h)

**Objective.** Create a safe working branch and record a reproducible baseline before
any change.

**Context.** `main` at `fac2b4f` is the latest version. The fast suite is green
(1376 passed); the browser suite has not been run in this session.

**Files.**
- New: `scripts/ux_screenshots.py`
- New: `docs/UX_CHECKLIST.md`
- `.gitignore`: add `screenshots/`

**Instructions.**
1. Run `git checkout main && git pull && git checkout -b ux/modernization`, then
   `git tag ux-baseline`.
2. Run the full suite: `pytest -q`. This needs Chromium; install it with
   `python -m playwright install chromium` if it is missing. Record the
   passed/skipped/failed counts in `docs/UX_CHECKLIST.md` under "Baseline".
3. Write `scripts/ux_screenshots.py`:
   - It starts `streamlit run app.py --server.headless true --server.port <free>` as a
     subprocess and waits for `/_stcore/health`.
   - For each path in `["", "Riksoversikt", "Lan_jamforelse", "Kommun_djupanalys",
     "Kontantinsats", "Scenario", "Metodologi"]` and each viewport (1440 × 900,
     1024 × 900, 390 × 844):
     - load the page and wait for `networkidle` plus 4 s;
     - read `document.querySelector('[data-testid="stMain"]').scrollHeight`, resize
       the viewport to that height + 40, and wait 3 s;
     - save `screenshots/<tag>/<viewport>_<page>.png`.
   - It terminates the server at the end.
   - It takes `--tag` (default `adhoc`).
   - It uses Playwright, which is already a dev dependency. It must not import from
     `src`.
   - Keep it under 120 lines.
4. Run `python scripts/ux_screenshots.py --tag baseline`.
5. Create `docs/UX_CHECKLIST.md`:
   - a "Baseline" section;
   - one heading per task UX-01 to UX-19 with an unchecked box;
   - a copy of the B5 regression checklist from `UX_UI_MODERNIZATION_PLAN.md`.

**Must remain intact.** Everything; this task changes no app code.

**Acceptance.**
- The branch and tag exist.
- The baseline counts are recorded.
- 21 PNGs are written.
- `scripts/` holds a new script that the test suite does not collect. Check that
  `pytest --collect-only -q | grep ux_screenshots` is empty.

**Done when** the commit `ux(UX-00): baseline and screenshot tool` is on the branch.

---

### UX-01 · Token layer: generated CSS custom properties, spacing scale, `spacer()` (P0, 4 h)

**Objective.** Make `src/ui/tokens.py` the only place colour values live, for CSS as
well as Plotly. Introduce a spacing and radius scale. Replace the inline spacer divs.

**Context.**
- `src/ui/css_layout.py`, `css_components.py`, `css_charts.py`, `css_interpret.py`,
  `css_purpose.py`, `css_landing.py` and `css_responsive.py` are plain strings with
  130 hex literals.
- `css_components.py:118` claims tokens cannot be interpolated. CSS custom properties
  solve this.
- `src/ui/css.py` concatenates the slices in a load-bearing order: the `@import` must
  stay first, and the responsive rules last.
- 18 inline spacers of the form `st.markdown("<div style='height:24px'></div>", …)`
  exist in pages 01, 02, 03, 05 and 06 and in `src/ui/sidebar.py`.
- Streamlit 1.56 has `st.space`. Verify its signature with
  `python -c "import streamlit as st, inspect; print(inspect.signature(st.space))"`.

**Instructions.**
1. In `tokens.py`, add:
   - `SPACING = {"1": 4, "2": 8, "3": 12, "4": 16, "5": 24, "6": 32, "7": 48}`;
   - `RADIUS = {"sm": 4, "md": 6}`;
   - `def css_root() -> str`, which returns
     `":root{" + "".join(f"--shai-c-{k.replace('_','-')}:{v};" for k, v in COLORS.items())`
     plus `--shai-space-N` and `--shai-radius-*` entries, plus `"}"`.

   Do **not** change any colour value in this task.
2. In `css.py`, build `GLOBAL_CSS` so the `:root` block sits **immediately after**
   the opening `<style>` and `@import` line, which are both in `css_layout.CSS`.
   Split `css_layout.CSS` at the end of the `@import` line, or move the existing
   `:root{…}` there and extend it. Document why in the module docstring.
3. Replace every 6-digit hex literal in the seven `css_*.py` modules with
   `var(--shai-c-<token>)` for the token whose value it equals. Use a script to list
   them, then review by hand. Literals that match no token:
   - `#E3E6EC`: add token `border_strong` (it becomes `border` in UX-02);
   - `#4B5563`: add token `text_body_secondary` (renamed in UX-02);
   - `#E8D5A0`: add token `accent_light`;
   - `#0F2847`: replace with `primary`;
   - `#F9FAFB`: this is `hover`.

   Keep `rgba(…)` tints as they are in this task.
4. Add `tests/test_css_tokens.py`. It asserts:
   - no `#[0-9A-Fa-f]{6}\b` appears in any `src/ui/css_*.py` module;
   - every `var(--shai-c-…)` used names a key of `COLORS`;
   - `GLOBAL_CSS.index(":root") < GLOBAL_CSS.index(".shai-")` and the `@import`
     precedes `:root`.
5. Add `def spacer(size: str = "md") -> None` to `src/ui/components.py`, mapping
   `sm → 8`, `md → 16`, `lg → 24`, `xl → 32` px. It uses `st.space` if the signature
   accepts pixel heights; otherwise it emits
   `<div class="shai-spacer shai-spacer--{size}"></div>` with CSS heights from the
   vars, and those classes are added to the DESIGN_SYSTEM inventory. Replace all 18
   inline spacers with `spacer()`, mapping 8 → sm, 16 → md, 20/24 → lg and
   32 → xl.
6. Update `docs/DESIGN_SYSTEM.md`:
   - §1: `tokens.py` now also generates `:root`;
   - §2: the new tokens, plus a short "CSS variables" subsection;
   - §3: new classes, if any, and the count;
   - §7: a checklist line: "New colour? Add it to `COLORS`; CSS reads it as
     `var(--shai-c-…)`."

   Replace the claim at `css_components.py:118` with a pointer to the mechanism.

**Must remain intact.** The rendered colours must be pixel-identical. Compare the
`UX-01` screenshots with the baseline: any visible difference other than ±1 px
spacing from the spacer mapping is a defect. The cascade order must hold, and the
single injection point too.

**Technical constraints.** No f-strings around whole CSS blocks, because the braces
conflict. Only `css_root()` builds strings dynamically. CSS variables need no browser
support caveat (all evergreen browsers).

**Testing.** Fast suite, the browser suite, and screenshots tagged `UX-01`.

**Acceptance.**
- `grep -E "#[0-9A-Fa-f]{6}" src/ui/css_*.py` returns nothing.
- `test_css_tokens.py` passes.
- The screenshots match the baseline.
- `grep -rn "height:[0-9]*px'></div>" app.py pages src` returns nothing.

**Done when** it is committed and the checklist is ticked.

---

### UX-02 · Contrast-compliant text tokens and `primaryColor` (P0, 1.5 h)

**Objective.** Make every text/background pair meet WCAG AA (≥ 4.5:1; ≥ 3:1 for
≥ 18.66 px bold), without changing the brand.

**Context.** The failures, with ratios against white unless stated:
- gold text `#C4A35A`, 2.4:1 (eyebrows, `.shai-section-title`, `.shai-help-mark`,
  active tab and slider value through `primaryColor`);
- `#D4A03C` "MEDEL" pill text, 2.36:1;
- `#9CA3AF` text (year display and label, card tags, stat unit, footer, nav tag),
  2.54:1;
- white on gold/amber/grey timeline segments (`templates.py`
  `ki.fore_2010_bolanetak_amorteringskrav_skarpt` and the matching
  `mt.fore_2010_…` timeline), 2.4:1;
- the sidebar footer `#6B7280` on navy, 3.39:1.

**Instructions.**
1. `tokens.py`:
   - add `accent_strong="#8A6A1F"`, `medium_risk_text="#8A5A00"`,
     `text_muted="#6B7280"`, `border_subtle="#EEF0F3"`, `focus="#4A6FA5"` and
     `sidebar_muted="#A3AAC2"`;
   - change `text_secondary` to `#4B5563` and `border` to `#E3E6EC`;
   - remove the UX-01 temporary names (`border_strong`, `text_body_secondary`),
     pointing their uses at `border` and `text_secondary`;
   - keep `text_tertiary="#9CA3AF"` and document it as **decorative only, never text**.
2. CSS:
   - every place that colours **text** with `accent` uses `accent_strong` (fills,
     bars, borders and the sidebar on navy keep `accent`);
   - text in `text_tertiary` → `text_muted`;
   - `.shai-risk-pill.medel { color: var(--shai-c-medium-risk-text) }`;
   - `.shai-table tbody td` borders → `border_subtle`;
   - `.shai-sidebar-footer` and the inline `#8A8FA8` in `sidebar.py::footer_html`
     → `sidebar_muted`. Move that inline style into a class
     `.shai-sidebar-version`, documented.
3. Timeline templates in `templates.py`:
   - segment labels become `text_primary` on `accent` and `medium_risk` segments;
   - they stay white on `high_risk`, `low_risk` and `primary` (≥ 5:1);
   - the `pre_2010` segment uses `text_muted` fill with white text (4.83:1);
   - raise the font to 11 px.

   Pass the new values through the existing `v0…vN` placeholders from the call sites
   in `pages/04_Kontantinsats.py` and `pages/06_Metodologi.py`.
4. `.streamlit/config.toml`: `primaryColor = "#8A6A1F"`, with an updated comment.
   Update `tests/test_design_system_doc.py::test_the_accent_token_is_tied_to_the_streamlit_theme`
   to assert `COLORS["accent_strong"]` appears in the config, and update its docstring
   and `DESIGN_SYSTEM.md` §2 to say that `primaryColor` tracks `accent_strong`
   because it colours text (tab labels, slider values).
5. Add `tests/test_contrast.py`, using WCAG relative luminance. It asserts ≥ 4.5 for
   these pairs:
   - (`text_primary`, `card_bg`), (`text_primary`, `bg`);
   - (`text_secondary`, `card_bg`), (`text_secondary`, `bg`);
   - (`text_muted`, `card_bg`), (`text_muted`, `bg`);
   - (`accent_strong`, `card_bg`), (`accent_strong`, `bg`);
   - (`medium_risk_text`, `card_bg`);
   - (`low_risk`, `card_bg`), (`high_risk`, `card_bg`);
   - (`sidebar_muted`, `primary`);
   - (`accent`, `primary`) — gold on navy in the sidebar.

**Must remain intact.**
- The navy sidebar's appearance; the gold active pill fill and active-link bar.
- All risk colours used as fills.
- Plotly charts: they use `COLORS[...]` by key, so check that axis-title colour
  (`text_secondary`) darkens without other effect.

**Testing.** Fast suite (including the updated design-doc test and the new contrast
test), the browser suite, and screenshots `UX-02`.

**Acceptance.**
- `test_contrast.py` passes.
- No CSS rule sets `color:` to `accent`, `medium_risk` or `text_tertiary`. Assert this
  in `test_css_tokens.py` by scanning `color:\s*var\(--shai-c-(accent|medium-risk|text-tertiary)\)`.
- Screenshots show darker gold and grey text with an otherwise identical layout.

---

### UX-03 · Tabular sans figures and type scale (P1, 2 h)

**Objective.** Put every figure in one typographic voice: Source Sans 3 with tabular,
lining numerals. Raise small labels to at least 11 px.

**Context.**
- `IBM Plex Mono` is used in `css_components.py` (`.shai-kpi-delta`,
  `.shai-year-label`, `.shai-card-tag`, `.shai-table tbody td.shai-num`,
  `.shai-footer-note code`), `css_landing.py` (stat value, step number, nav tag,
  weight pct) and `css_layout.py` (sidebar pills).
- `MONO_FONT` is used for bar text in `src/kontantinsats/charts.py:109,271` and
  `pages/05_Scenario.py`.

**Instructions.**
1. CSS:
   - replace `font-family: 'IBM Plex Mono'…` with the Source Sans stack, adding
     `font-variant-numeric: tabular-nums lining-nums;` everywhere **except**
     `.shai-footer-note code`, which keeps mono for the version string;
   - sidebar year pills: Source Sans 13 px, weight 500, tabular;
   - `.shai-card-tag` and `.shai-nav-tag`: 11 px, 600, `letter-spacing: 0.08em`,
     colour `text_muted`;
   - `.shai-kpi-label`: 11 px;
   - `.shai-table thead th`: 11 px.
2. KPI value: `font-size: clamp(24px, 2.3vw, 32px)`, and in `css_responsive.py`
   `@media (max-width: 640px) { .shai-kpi-value { font-size: 28px; } }`.
3. Charts: switch `textfont=dict(family=MONO_FONT, …)` to `CHART_FONT` in
   `src/kontantinsats/charts.py` and `pages/05_Scenario.py`. Keep `MONO_FONT` defined
   and exported in `chart_theme.py`.
4. `@import` in `css_layout.py`: keep the IBM Plex Mono 400 weight only, since only
   `code` uses it, and drop weight 500. Keep Source Sans 3 at 300/400/600/700.
5. Add to `DESIGN_SYSTEM.md` a "§2b Typography" table with the A7 type scale and the
   rule "figures are Source Sans tabular; mono only for code".

**Must remain intact.**
- Text-fit tests: wider sans digits can change chart text widths, so run
  `tests/test_pages_text_fit.py`.
- `_LEGEND_PAD` on Sida 03 is not touched.

**Acceptance.**
- `grep -n "IBM Plex Mono" src/ui/css_*.py` shows only the `@import` and
  `.shai-footer-note code`.
- The browser and text-fit suites are green.
- Screenshots show "31 726 SEK" with normal spacing.

---

### UX-05 · Clickable landing navigation cards (P0, 1.5 h)

**Objective.** The six landing cards navigate to their pages. Fix the affordance, not
just the look.

**Context.**
- `app.py:79-114` renders `render_landing_nav_card(...)` HTML in a 3-column grid.
- `css_landing.py` gives `.shai-nav-card` a hover lift with `cursor: default`.
- Navigation must use `st.page_link`, which preserves `st.session_state` (the selected
  year). A raw `<a href>` would reload the app and lose it.
- Page paths are in `src/ui/sidebar.py::PAGES`.

**Instructions.**
1. In `src/ui/landing.py`, add `render_landing_nav_link_card(page: str, title: str,
   desc: str, tag: str) -> None`. It opens `st.container(border=True,
   key=f"shai_nav_{tag_slug}")` and, inside it:
   - renders the tag, title and description markup (reusing the
     `render_landing_nav_card` markup minus the outer `.shai-nav-card` frame);
   - calls `st.page_link(page, label=L("landing.oppna_v0", v0=title))`, a new label
     "Öppna {v0}".
2. CSS (`css_landing.py`):
   - target `.st-key-shai_nav_*`, the class Streamlit 1.56 puts on keyed containers.
     **Verify the class name in the DOM first**; if it differs, use a wrapper element
     the container renders;
   - make the container `position: relative`;
   - stretch the page-link anchor over the card with
     `a[data-testid="stPageLink-NavLink"]::after { content: ""; position: absolute;
     inset: 0; }` (**verify the testid**);
   - add the hover lift and a `:focus-within` outline in `focus`;
   - remove the old `.shai-nav-card:hover` transform, and remove `cursor: default`.
3. In `app.py`, replace the six `st.markdown(render_landing_nav_card(...))` calls with
   the new function. Keep the 3-column grid and the same titles, descriptions and tags.
   The page targets are the six non-landing entries of `PAGES`.
4. If `render_landing_nav_card` becomes unused, keep it if a test imports it (grep
   `tests/`); otherwise delete it, and delete classes left without a user from CSS and
   DESIGN_SYSTEM §3.
5. Add a browser test in `tests/test_browser_render.py`:
   - open `/`;
   - click the card titled "Kommunanalys";
   - assert the URL ends with `/Kommun_djupanalys` and the header shows "Kommunanalys";
   - also set the year to 2019 on `/` before clicking and assert the header chip or
     year display shows 2019 after navigation.

**Must remain intact.**
- Same six destinations and copy.
- Year persistence across navigation.
- `test_pages_render` drives pages through `app.py`. `st.page_link` already works
  there, since the sidebar uses it.

**Acceptance.** The new browser test passes. Keyboard: Tab reaches each card link
and Enter navigates. Hover shows the lift only on real links.

---

### UX-06 · Grouped sidebar navigation and focus states (P1, 1.5 h)

**Objective.** Group the navigation as Analys / Verktyg / Referens, add visible
keyboard focus, and move the sidebar's inline copy into labels.

**Context.**
- `src/ui/sidebar.py` defines `PAGES` and renders the "Navigation", "Valt år" and
  "Riskfilter" strings inline.
- `css_layout.py` styles links via `section[data-testid="stSidebarContent"] a[href]`.

**Instructions.**
1. Restructure `PAGES` into
   `NAV_GROUPS: list[tuple[str | None, list[tuple[str, str]]]]`:
   - `None` → Startsida;
   - `"sb.grupp_analys"` → 01, 02, 03;
   - `"sb.grupp_verktyg"` → 04, 05;
   - `"sb.grupp_referens"` → 06.

   Keep `PAGES` as a derived flat list, because tests may import it (grep). Add labels
   `sb.grupp_analys = "Analys"`, `sb.grupp_verktyg = "Verktyg"`,
   `sb.grupp_referens = "Referens"`, `sb.valt_ar = "Valt år"` and
   `sb.riskfilter = "Riskfilter"`, and move the remaining sidebar strings to `L()`
   keys under `sb.`.
2. Render each group label with the existing `.shai-sidebar-section-label`, styled in
   `sidebar_muted`, 11 px, with 16 px top margin, and drop the single "Navigation"
   label.
3. CSS: a sidebar link `:focus-visible` rule draws a 2 px `accent` outline with 2 px
   offset; the `[aria-current="page"]` style is unchanged.
4. Brand block: keep the content. Set `.shai-brand-sub` to `sidebar_muted`.

**Must remain intact.** Link order and targets, labels, the active style, the mobile
overlay and its open button.

**Acceptance.**
- The fast suite passes (`test_pages_render` still drives all pages).
- Tab through the sidebar shows a visible ring on each link.
- The screenshot shows three group labels.

---

### UX-07 · Context-aware sidebar controls (P0, 2 h) — **REVIEW item**

**Objective.** Show the year and risk controls only on pages where they change the
output, and keep the selection across pages.

**Context.**
- `render_sidebar()` in `src/ui/sidebar.py` always renders the year pills
  (`key="shai_year_pills"`) and the risk pills (`key="shai_risk_pills"`). It mirrors
  them to `shai_selected_year` and `shai_selected_risks`, and returns
  `{"selected_year", "selected_risks"}`.
- Only `pages/01_Riksoversikt.py` reads `selected_risks`.
- `app.py` and `pages/06_Metodologi.py` read neither value. If UX-18 is approved,
  `app.py` will read the year.
- Streamlit discards a widget's own key when the widget is not rendered, but the plain
  mirror keys survive. `sidebar.py:105-119` documents this.

**Instructions.**
1. Change the signature to `render_sidebar(*, year: bool = True, risk: bool = False)
   -> dict`.
   - When `year` is False, skip the pills but still return
     `selected_year = st.session_state.get("shai_selected_year", default_year())`,
     validated against `YEAR_RANGE` exactly as now.
   - When `risk` is False, skip the legend and pills but still return
     `selected_risks` computed from the mirror, with empty meaning all, exactly as now.
2. Callers:
   - `pages/01`: `render_sidebar(risk=True)`;
   - `pages/02` to `05`: `render_sidebar()`;
   - `pages/06`: `render_sidebar(year=False)`;
   - `app.py`: `render_sidebar(year=<True if UX-18 is approved and done, else False>)`.
     Default to `False` now; UX-18 flips it.
3. When a control is hidden, show nothing in its place. The Metodologi header already
   shows the period.
4. Tests:
   - add to `tests/test_ui_affordances.py`: `selected_risks` is read only on pages
     that call `render_sidebar(risk=True)` (an AST check), and vice versa;
   - add an AppTest in `tests/test_pages_render.py` style:
     - start at `app.py`;
     - switch to Sida 01 and set the risk pills to `["Hög"]`;
     - switch to Sida 06 and then back to Sida 01;
     - assert the risk pills' value is still `["Hög"]`;
     - do the same for the year via Sida 06.
   - Update `test_the_sidebar_offers_exactly_the_labels_the_filter_understands` if it
     assumes the pills always render.

**Fallback if not approved.** Keep the controls on every page, and under each add
`st.caption(L("sb.galler_inte_sidan"))` ("Gäller inte den här sidan") where it is
inert. Use the same `year`/`risk` flags to decide where the caption shows.

**Must remain intact.**
- The persistence of both selections across every navigation path.
- Empty risk selection = all.
- Year range validation.
- Sida 01 output identical for the same selection.

**Acceptance.**
- The new AppTests pass and all 67 renders pass.
- Manual check: on Sida 01 set Hög, go to Sida 03, return, and Hög is still selected.
  On Sida 03 set 2019, open Metodologi, open Sida 01, and 2019 is still selected.

---

### UX-08 · Page header: semantic `<h1>`, year and vintage chips (P1, 1.5 h)

**Objective.** Give every page a real heading and replace the faint 36 px year with
explicit, legible context chips. Consolidate the data vintage into the header.

**Context.**
- `src/ui/components.py::page_title(eyebrow, title, subtitle, year)` renders `<div>`s.
- `vintage_badge()` is called separately on every page at varying positions.
- `tests/test_ui_affordances.py::test_every_page_shows_the_data_vintage` counts
  `vintage_badge` calls per page via `_calls(page, "vintage_badge")`.

**Instructions.**
1. Change the signature to `page_title(eyebrow, title, subtitle="", year="", *,
   vintage: bool = True)`.
   - Render `<h1 class="shai-page-title">`.
   - The right column becomes `<div class="shai-header-chips">` with:
     - `<span class="shai-chip">` "Analysår {year}" when `year` is set (Metodologi
       passes the period string, labelled with a new key
       `ui.period_chip = "Period {v0}"`);
     - when `vintage` is set, a chip with the green dot (reusing
       `.shai-vintage-dot`) and `L("ui.data_uppdaterad_v0", v0=stamp)`, with `stamp`
       from `generated_at()`.
   - Chips: 12 px, `text_secondary` on `card_bg`, a 1 px `border`, radius sm, padding
     4 px × 10 px, and `aria-label`s.
2. Remove the separate `vintage_badge()` calls from pages 01–06. Keep the one on the
   landing page, which has no `page_title`. Keep the function.
3. Update `test_every_page_shows_the_data_vintage` to pass if the page calls
   `vintage_badge` **or** calls `page_title` without `vintage=False`. Explain why in
   its docstring.
4. CSS:
   - hide Streamlit's header anchors:
     `[data-testid="stMain"] [data-testid="stHeaderActionElements"] { display: none; }`
     (**verify the testid**);
   - `.shai-page-title` keeps its look and sets `margin: 0` on the `h1`;
   - remove the unused `.shai-year-display` and `.shai-year-label` rules and their
     inventory rows, or keep them if anything still references them (grep).
5. On ≤ 640 px the chips wrap under the title (`flex-wrap: wrap`).

**Must remain intact.** The eyebrow, title and subtitle copy, and the same year value
as the sidebar.

**Acceptance.**
- Every page has exactly one `h1`. Assert this in `test_browser_render.py` with
  `page.locator('[data-testid="stMain"] h1').count() == 1`.
- The year chip matches the sidebar year.
- The vintage chip date equals `generated_at()[:10]`.

---

### UX-09 · Card and table framing, KPI variant rule, compact KPI, help in KPI labels (P1, 2 h)

**Objective.** Remove the double frames, make the KPI stripe colour meaningful, and
make KPI definitions reachable by touch and keyboard.

**Context.**
- `src/ui/data_table.py::render_table` always wraps in `.shai-card`. Callers inside
  `st.container(border=True)`:
  - `src/lan/ranking.py` (Sida 02, inside a bordered container);
  - `pages/02` (Robusthet, both tables);
  - `src/ui/cost_panel.py` (inside an expander, also framed).
- `kpi_card(..., variant, tooltip)` puts the tooltip in `title=`.

**Instructions.**
1. Add `framed: bool = True` to `render_table`. When it is `False`, return the
   `<table>` with the optional header but no `.shai-card` wrapper, wrapped in
   `<div class="shai-table-scroll">` (`overflow-x: auto`). When it is `True`, also put
   the table inside `.shai-table-scroll`. Pass `framed=False` at:
   - the `county_ranking_html` call inside the bordered container;
   - both Robusthet tables (pages/02);
   - the cost history table (`cost_panel.py`);
   - the version table in the J5 expander.
2. **KPI variant rule.** Add it to `kpi_card`'s docstring and `DESIGN_SYSTEM.md` §6:
   `default` for neutral figures, and `danger`, `success` or `accent` only when the
   value is a status. Apply it:
   - Sida 01: mean SHAI `default`, högrisk `danger`, K/T `default`, population
     `default`;
   - Sida 03: all `default`;
   - Sida 04 `render_snapshot`: P/I `default`, kontantinsatsbörda `default`,
     boendekostnadsbörda `accent` if ≥ 30 % else `default` (unchanged),
     Tillgänglighet as-is (a status);
   - Sida 04 `render_baseline_kpis`: all `default`, with kontantinsats `default`
     instead of `accent`;
   - Sida 05: base `default`, scenario `default`, change as-is (status by sign);
   - national outcome as-is (risk classes).
3. Add `size: str = "regular" | "compact"` to `kpi_card`. Compact uses
   `.shai-kpi-card--compact` with padding 14 px × 16 px and a value size of 20 px. It
   is used in UX-12.
4. Add `help_terms: tuple[str, ...] = ()` to `kpi_card`. When it is given, append
   `help_badge(*help_terms)` to the label. Keep `tooltip` (`title=`) as is. Wire terms
   where glossary keys exist: grep `glossary.` in `labels.py` for `version_c`, `kt`,
   `riskklass` and so on. Do not invent glossary entries; add one only with its
   Swedish definition copied from the existing tooltip label text.
5. CSS: `.shai-table-scroll`, `.shai-kpi-card--compact`, and the `.shai-help` popover
   inside a KPI label (avoid clipping: the card's `overflow: hidden` must not cut the
   popover. Move the stripe to `box-shadow: inset 3px 0 0 var(--…)` and remove
   `overflow: hidden`). Add the inventory rows.

**Must remain intact.** All values, deltas and Δ colours (via `delta_meta`), and the
table content and order.

**Acceptance.**
- No `.shai-card` is nested in a bordered container in the Sida 02 DOM. Add a browser
  assertion: `page.locator('[data-testid="stVerticalBlockBorderWrapper"] .shai-card').count() == 0`
  on `/Lan_jamforelse`.
- The help popover opens on focus inside the KPI cards.

---

### UX-10 · Callout theming and error-detail expander (P1, 1 h)

**Objective.** Bring `st.info`, `st.warning`, `st.error` and `st.success` onto the
palette, and stop printing raw exception text inline.

**Context.**
- `st.info` is used for the Sida 04 price-type note, the Sida 05 scope note and empty
  states. `st.warning` and `st.error` are used for the empty-year and load-failure
  states on every page.
- Each error state is followed by `st.caption(f"Detaljer: {e}")`.

**Instructions.**
1. Inspect the DOM in Streamlit 1.56 for `st.info` (likely `[data-testid="stAlert"]`
   containing `[data-testid="stAlertContainer"]`). Add CSS to a new
   `src/ui/css_feedback.py` slice, composed after `_INTERPRET`:
   - white background, 1 px `border`, radius md;
   - a 3 px left stripe via `box-shadow: inset 3px 0 0` in the kind's colour: info
     `secondary`, warning `medium_risk`, error `high_risk`, success `low_risk`;
   - body text `text_primary`, icon in the stripe colour.

   Distinguish the kinds through the alert's kind attribute or its icon.
   **Verify the selectors in the browser**; fall back to icon colour only if the kind
   is not exposed.
2. Add `def error_state(message_key: str, exc: Exception) -> None` to
   `components.py`. It calls `st.error(L(message_key))`, then
   `with st.expander(L("ui.tekniska_detaljer")): st.code(str(exc))`, then
   `st.stop()`. The new label is "Tekniska detaljer". Replace the 8 `try/except`
   handlers on the pages. The Sida 06 cost-history caption is not a stop; leave it.
3. Add the `css_feedback` slice to `css.py`'s ordered concatenation, and add a row to
   `DESIGN_SYSTEM.md` §1.

**Must remain intact.** Every message's text, and the `st.stop()` semantics.

**Acceptance.**
- Screenshots of Sida 04 and 05 show white callouts with coloured stripes.
- Simulate an error by temporarily renaming an artifact locally (do not commit): the
  page shows the message and a collapsed "Tekniska detaljer".

---

### UX-11 · Chart number formatting and bar-label font (P1, 2 h)

**Objective.** Use Swedish number formatting on every chart axis and keep chart text
in one typeface.

**Context.**
- `src/ui/chart_theme.py::get_chart_layout` sets `separators: ", "`.
- Plotly SI-abbreviates large numbers: Sida 04 gap chart "1M … 9M", comparison bars
  "10k … 50k".
- Sida 03 component charts already set `tickformat=",.0f"` inline.

**Instructions.**
1. In `chart_theme.py`, add
   `def sek_axis(layout: dict, axis: str = "yaxis") -> dict`, which sets
   `layout[axis]["tickformat"] = ",.0f"` and returns `layout`, and
   `def pct_axis(layout, axis="yaxis")`, which sets `ticksuffix = " %"` (nbsp) and
   leaves the format alone.
2. Apply `sek_axis`:
   - `src/kontantinsats/charts.py::affordability_gap_chart` on `xaxis`;
   - `comparison_barchart` on `yaxis` **when** the spec's unit is SEK (pass a
     `value_unit` from `comparison_tab_specs`; months and years use no helper);
   - `pages/03` component charts, replacing the inline `tickformat`.
3. If the gap chart's x ticks then collide at 390 px, set `nticks=5` on that axis and
   re-run `test_pages_text_fit.py`.
4. Hover templates keep their formats. Check that they render with a comma decimal
   after the change.

**Must remain intact.** The chart theme guard: no literals, and the shared layout.
Reference lines and the `bar_names_above` behaviour.

**Acceptance.** No "k" or "M" tick suffix anywhere. Text-fit tests pass at every
width.

---

### UX-12 · Sida 04 restructure and regime palette (P1, 4 h) — **REVIEW item (palette)**

**Objective.** Put the answer first, group the eight KPIs into one card, compact the
villa/BR comparison, and give regime colours a single meaning.

**Context.**
- `pages/04_Kontantinsats.py` (386 lines; the ≤ 400 limit applies).
- `src/kontantinsats/sections.py`: `render_snapshot`, `render_villa_vs_bostadsratt`,
  `render_baseline_kpis` and `render_regime_cards`, all taking `Context`.
- `src/kontantinsats/charts.py::comparison_barchart` colours best/worst with
  `low_risk`/`high_risk` and the other regimes with `REGIME_ACCENT_COLORS`
  (`src/kontantinsats/regions.py:52`).
- Regime cards use `st.columns(5)` with `st.metric`.

**Instructions.**
1. **Split `render_snapshot`** into:
   - `render_snapshot_kpis(ctx, size)`: the four snapshot cards, unchanged values and
     labels;
   - `render_reachability(ctx)`: the gap-chart card;
   - `render_snapshot_notes(ctx)`: the findings panel and the three captions.

   Keep `render_snapshot` as a thin wrapper calling all three in the old order, in
   case a test imports it (grep `tests/`).
2. **New** `render_answer(ctx)` in `sections.py`, or in a new module
   `src/kontantinsats/answer.py` if `sections.py` would exceed 400 lines. It opens one
   `st.container(border=True)` with `card_header(L("ki.svar_rubrik"),
   L("ki.svar_underrubrik_v0_v1", v0=selected_name, v1=selected_year), "")`. Proposed
   copy: "Svaret för ditt hushåll" / "{v0} · {v1} · dagens regler". Inside it:
   - **Tier 1**, a `render_kpi_row` of regular cards: Kontantinsats (idag), År att
     spara (idag), Månadskostnad (idag), Tillgänglighet. Reuse the exact `kpi_card`
     arguments from `render_baseline_kpis` and `render_snapshot`.
   - **Tier 2**, a `render_kpi_row` of `size="compact"` cards: Pris/Inkomst-kvot,
     Kontantinsatsbörda, Boendekostnadsbörda, Kvarvarande inkomst (idag).
   - The three context captions from `render_snapshot_notes`.
3. **Purpose panel.** Add `purpose_panel(..., more: list[str] | None = None)`:
   paragraphs beyond the first move into `more`, which the caller renders in
   `st.expander(L("ui.mer_om_sidan"))` ("Mer om sidan") inside the same container.
   Sida 04 passes `[ki.syfte_p1]` and `more=[ki.syfte_p2]`.
4. **Price-type note.** Move the `st.info` / `st.warning` (`_br_available`) from above
   the controls card to inside it, directly under the columns row. The text and
   conditions are unchanged.
5. **New page order** after the controls card:
   1. `render_answer`
   2. findings (from `render_snapshot_notes`, without the captions it already
      rendered in the answer card)
   3. `render_reachability`
   4. `section_heading(L("ki.regelverken_rubrik"))` ("Regelverken"), followed by:
      - the timeline card;
      - `render_regime_cards`;
      - the comparison-tabs container.
   5. `render_villa_vs_bostadsratt`
   6. `render_insight`
   7. `render_assumptions`
   8. footer

   `section_heading` is a new helper in `components.py` that renders
   `<h2 class="shai-section-heading">`: 18 px/700, `text_primary`, margin
   32 px 0 12 px.
6. **Villa vs BR.** Replace the 8 `st.metric`s with
   `render_table(frame, cols, framed=False)`:
   - rows: Pris, Kontantinsats (10 %), År att spara, Månadskostnad;
   - columns: Mått | the Småhus label with its level | Bostadsrätt, länsnivå;
   - all values formatted exactly as now, including "SEK" and "år";
   - numeric columns right-aligned;
   - the price-ratio caption is kept.
7. **Regime cards.** Add `key="shai_regimes"` to the regime-cards container. Add CSS
   `.st-key-shai_regimes [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }` and
   give its columns `min-width: min(100%, 220px)`. **Verify the key class.**
8. **Palette (REVIEW).**
   - In `tokens.py`, add
     `REGIME_RAMP = ("#8592A8", "#6B7FA0", "#566C91", "#2A4068")` for `pre_2010`,
     `bolanetak`, `amort_1` and `amort_2`, and use `COLORS["accent"]` with a 1 px
     `accent_strong` outline for `latt_2026`. Point `REGIME_ACCENT_COLORS` in
     `regions.py` at these. Every ramp colour must clear 3:1 on white as a bar fill;
     add it to `test_contrast.py` at a 3.0 threshold. The measured values are 3.15,
     4.06, 5.32 and 10.34. Gold (2.4:1) is exempt: under WCAG 1.4.11 the bar is
     also identified by its category label and value label, and the outline gives
     it an edge.
   - In `comparison_barchart`, **stop overriding** best/worst fills. Instead:
     - add a 2 px `COLORS["primary"]` `marker.line` on the best and worst bars;
     - add an annotation above each bar, "Lägst" or "Högst", in `text_secondary`
       (new labels `ki.lagst`, `ki.hogst`);
     - for metrics where lower is better, best = "Lägst", and the reverse otherwise.

     Update the timeline template colours to the same ramp so the timeline and the
     bars agree.
   - **Fallback (if the palette is not approved):** keep `REGIME_ACCENT_COLORS` as
     is. Only remove the best/worst fill override and add the annotations and
     outline.
9. Update `docs/APP_REFERENCE.md` Part I §4 ("How it works") with the new section
   order, in one paragraph, and `DESIGN_SYSTEM.md` §5 with the regime ramp rule.

**Must remain intact.**
- All 8 KPI values and tooltips.
- The interpretation findings.
- Every caption.
- The margin control's reset per year.
- BR mode (switch to län) and the fallback note.
- The 15-column details table with its own highlighting.
- `_best_and_worst` logic.
- The tests `test_kontantinsats_*`, `test_rendered_chart`, `test_chart_text_fits` and
  `test_chart_theme_guard`.
- Page ≤ 400 lines.

**Testing.**
- AppTest renders for all 11 years in both price types, already in
  `test_pages_render`. Check whether BR mode is covered there; if not, add one render
  with `ki_pristyp` = Bostadsrätt.
- Browser and text-fit suites.
- Screenshots: confirm on a phone that the 3+2 and 1-per-row regime wrap works.

**Acceptance.**
- In the 1440 px screenshot the answer card sits directly under the controls.
- The page height drops by at least 20 % against the baseline, on both desktop and
  phone.
- All tests are green.

---

### UX-13 · Sida 05 restructure (P1, 2.5 h)

**Objective.** Put every scenario input in one card, demote the reset button, and use
one table style.

**Context.**
- `pages/05_Scenario.py` (312 lines).
- The preset buttons write `sc_rate_slider`, `sc_income_slider` and `sc_price_slider`
  and then `st.rerun()`.
- `render_shock_sliders()` is in `src/scenario/controls.py`.
- The comparison table uses `st.dataframe` (around line 302).

**Instructions.**
1. `render_purpose()` in `src/scenario/sections.py`: use `purpose_panel(...,
   more=[sc.syfte_p2])` as in UX-12. Then move the scope `st.info` (`sc.scenario…`)
   to directly after the purpose container. It is already adjacent; keep it, now
   styled by UX-10.
2. Wrap the county select, the presets and the sliders in
   `st.container(border=True)` with
   `card_header(L("sc.scenario_rubrik"), L("sc.scenario_underrubrik"), "")`, using new
   labels "Ditt scenario" and "Välj län, ett förinställt scenario eller egna
   reglage".
   - County select: in `st.columns([2, 3])`, first column.
   - Presets: label `L("sc.forinstallda_scenarier")` (existing), then
     `st.columns([1, 1, 1, 0.6])`. The three scenario buttons keep their keys and
     labels and use `type="secondary"`; Återställ uses `type="tertiary"`. The handler
     is unchanged.
   - `render_shock_sliders()` inside the same container.
3. `section_heading(L("sc.resultat_rubrik"))` ("Resultat") goes above the KPI row.
4. Replace `st.dataframe(pd.DataFrame(comparison_data)...)` with `render_table(...,
   framed=False)`:
   - columns: Variabel (name) | Basfall (numeric) | Scenario (numeric);
   - the same 4 rows and formatted strings.

   Remove the `pandas` import if it becomes unused.
5. Check the page stays ≤ 400 lines. Move the bar-chart block into
   `src/scenario/sections.py::render_base_vs_scenario(result, county_name)` if
   needed.

**Must remain intact.**
- Preset behaviour, verified by AppTest: click "Räntecykeln 2021–23", then assert the
  sliders read 3.0, 9 and −5 and the scenario KPI changes.
- `_initial()` default handling; no Streamlit "default value but also set via Session
  State" warning.
- Every result section.
- `test_scenario_*` and `test_panel_scenario`.

**Acceptance.** The AppTest for the preset passes, and so do the screenshots and the
browser suite.

---

### UX-14a · Sida 01 refinements (P1, 1 h)

**Objective.** De-duplicate the map captions and make an active filter obvious.

**Context.** `pages/01_Riksoversikt.py` lines 187-200. The map card shows
`st.caption(L("rv.fargskala_gron_lag_risk_z_0_67_gul_medel"))` and then
`explanation(L("rv.forklaring_karta"))`, two descriptions of the same scale.

**Instructions.**
1. Keep `explanation(L("rv.forklaring_karta"))`. Remove the caption **only if**
   `rv.fargskala_*` is then orphaned and the orphan test permits removal: the
   orphaned-label test requires the label be deleted too. Before deleting, confirm
   the caption's one unique fact (the class boundaries z = ±0,67) appears in the
   "Om kartan" expander text or in `rv.forklaring_karta`. If not, append it to
   `rv.forklaring_karta` (copy edit; flag it in the commit message).
2. When `len(selected_risks) < 3`, render a one-line callout above the tables:
   `st.info(L("rv.filter_aktivt_v0", v0=", ".join(selected_risks)))`, with the
   copy "Topplistorna visar bara {v0}. Kartan visar alltid alla kommuner." The table
   subtitles already name the filter; keep them.

**Must remain intact.** The map is drawn from `mun_year`; the histogram and tables
from `df_ranked`.

**Acceptance.** With "Hög" selected, the callout appears and the map is unchanged.

---

### UX-16 · Responsive and accessibility pass (P1, 2.5 h)

**Objective.** Check and fix the experience at tablet and phone widths, keyboard
operability, and the remaining accessibility gaps.

**Instructions.**
1. Run the screenshot tool at 1024 and 390 px and list the defects. Expected
   candidates:
   - tables wider than the viewport (UX-09's `.shai-table-scroll` should handle these;
     confirm on Sida 01 and 02);
   - the regime cards wrap (UX-12);
   - header chips wrap (UX-08);
   - landing nav cards: 3 columns down to 2 at ≤ 900 px and 1 at ≤ 520 px (add a CSS
     rule on the landing's keyed nav columns).
2. **Keyboard.**
   - Tab through every page and confirm a visible focus indicator on links, pills,
     buttons, tabs, the help badges, expanders, selects and sliders.
   - Add a general rule: `[data-testid="stMain"] :is(button, [role="tab"], summary,
     a):focus-visible { outline: 2px solid var(--shai-c-focus); outline-offset: 2px; }`.
3. **Motion.** Extend the `prefers-reduced-motion` block to the new nav-card hover
   and any transitions added.
4. **Semantics.**
   - `card_header` titles become `<h3 class="shai-card-title">`. Check the visual
     size is unchanged, since `h3` default margins must be reset to 0.
   - The landing `.shai-section-title` becomes `<h2>`.
5. **Charts.** Every `st.plotly_chart` already has an explanation nearby. Add
   `aria-label` to the map iframe: `components.html` does not take one, so inject
   `title=` on the map's root `div` inside the generated HTML
   (`choropleth._map_html`), using `L("rv.karta_aria")` = "Karta över {N} kommuner
   färgade efter SHAI-poäng".
6. Re-run the browser suite, the text-fit suite and the screenshots.

**Acceptance.**
- No horizontal page scroll at 390 px on any page (the existing
  `test_phone_page_opens_on_content`).
- One `h1` per page.
- Every focusable element shows a ring.
- The text-fit suite is green.

---

### UX-17 · QA, regression, documentation and final report (P0, 6 h)

**Objective.** Prove nothing was lost, and document what changed.

**Instructions.**
1. Run the full suite: `pytest -q` (including browser and text-fit; not network).
   Record the counts against the baseline.
2. Run `python scripts/audit.py` and `pytest tests/test_readme_figures.py -q`. The
   README "What you will see" figures must be unchanged.
3. Run `python scripts/ux_screenshots.py --tag final` and compare it with `baseline`
   page by page.
4. Walk the whole **B5 checklist** by hand in a browser at 1440 and 390 px and tick
   it in `docs/UX_CHECKLIST.md`. Note anything that differs from the plan.
5. Update the docs:
   - `docs/DESIGN_SYSTEM.md`: §1 modules, §2 tokens and typography, §3 inventory and
     count, §5 charts, §6 components, §7 checklist;
   - `docs/APP_REFERENCE.md` Part I, wherever a section order changed (Sida 04 and
     05);
   - `README.md` only if a visible label it quotes changed. Today it quotes none of
     the changed ones.
6. Write `docs/UX_IMPLEMENTATION_REPORT.md` covering:
   - completed tasks, with commit hashes;
   - modified files;
   - the preserved-feature table (A3 IDs, each with ✓);
   - tests run, with counts;
   - screenshots compared;
   - remaining issues;
   - deferred tasks (P2/P3 not done) with the reason;
   - known limitations (for example, Streamlit DOM test-id dependencies in CSS,
     listed with the selectors used, so a Streamlit upgrade can be checked against
     them).
7. Run the `superpowers:requesting-code-review` skill or the `/code-review` command on
   the branch diff and resolve its findings.

**Acceptance.**
- The full suite is green, with a count ≥ baseline.
- Every B5 box is ticked or explicitly explained.
- The report is written.
- The branch is ready for a PR to `main` (do not merge without the owner's approval).

---

### UX-14b · Sida 01 full sortable table and CSV export (P2, 1.5 h)

**Objective.** Let analysts find any kommun's position and export the year's ranking.

**Instructions.**
1. Below the top-15 tables on `pages/01`, add `st.expander(L("rv.alla_kommuner_v0",
   v0=N_KOMMUNER))` ("Alla {v0} kommuner"). Build the frame from `mun_year`, **not**
   the filtered frame, with these columns:
   - Rang (`rank_c`, if present in the artifact; check the columns first; otherwise
     rank by `z_c`, matching the top-15 ordering);
   - Kommun;
   - Län (from `lan_code`, via `src/kontantinsats/regions._LAN_NAMES`, or move that
     mapping to `src/ui/` if importing from kontantinsats feels wrong — keep it
     minimal);
   - SHAI (% av inkomsten);
   - z-poäng;
   - Riskklass ("Hög", "Medel" or "Låg", as text);
   - Medianinkomst (SEK);
   - Medelpris småhus (SEK).
2. Render `st.dataframe(df, hide_index=True, width="stretch", height=420,
   column_config=…)`, with `NumberColumn` formats matching the site's precision and
   `help=` text from the glossary labels.
3. Add `st.download_button(L("rv.ladda_ner_csv"), data=df.to_csv(sep=";",
   decimal=",", index=False).encode("utf-8-sig"),
   file_name=f"shai_kommuner_{selected_year}.csv", mime="text/csv",
   key="rv_csv")`.
4. Add a caption stating that the table ignores the risk filter, and an
   `explanation()`.
5. Keep the page ≤ 400 lines; move the builder to `src/ui/full_table.py` if needed.
6. Test: build the frame for 2024 and assert 290 rows and that row 1 is Lidingö.
   Assert the CSV bytes start with the UTF-8 BOM and contain `;`.

---

### UX-15 · Sida 02 and 03 tidy-up (P2, 2 h)

**Instructions.**
1. **Sida 02 J5.** Replace the per-tab Markdown bullet lists and the inline-styled
   header in the "Varför skiljer sig versionerna åt?" expander with two
   `render_table(framed=False)` per tab. The rows are rank, län and value, built from
   the same `nlargest(5)`/`nsmallest(5)`, under the titles `L("lj.samst_overkomlighet")`
   and `L("lj.bast_overkomlighet")`. Remove the inline `style=` block.
2. **Sida 03.**
   - Put the kommun selectbox in `st.columns([2, 3])`, with a context line in the
     second column: `L("kd.kontext_v0_v1_v2", v0=kommun, v1=county_name,
     v2=selected_year)`.
   - In the component mini-charts, lower the in-figure title style to 13 px, 600,
     `text_secondary`.
   - On the driver chart, add a `st.badge(L("kd.storst_paverkan"), color="orange")`
     above the chart, or the token-styled `.shai-chip` if `st.badge` colours cannot
     match the tokens. Prefer the chip.
3. Run tests and take screenshots.

---

### UX-18 · Landing "Läget {year}" snapshot and section regroup (P2, 2.5 h)

**Instructions.**
1. In `app.py`, switch to `render_sidebar(year=True)` (see UX-07). Load
   `affordability_ranked.parquet` through `src/ui/data.load` with the `error_state`
   pattern.
2. In `src/ui/landing.py`, add `render_landing_snapshot(ranked, year)`:
   - `section_heading(L("landing.laget_v0", v0=year))`;
   - a `render_kpi_row` with:
     - mean `version_c` (`format_dec`, unit `L("rv.procent_av_inkomsten")`);
     - the hög count `(risk_c == "hog").sum()` "av {N}", `variant="danger"`;
     - a third card "Högst / lägst kostnad" with the value
       "{nlargest name} / {nsmallest name}" by `version_c`;
   - an `explanation(L("landing.laget_forklaring_v0", v0=year))`;
   - `st.page_link("pages/01_Riksoversikt.py",
     label=L("landing.oppna_riksoversikt"))`.

   Use the same computations as Sida 01 so the numbers match: compare with README
   "What you will see" for 2024 (16,3 / 84 / Lidingö / Åsele).
3. Place it directly after the stat strip and its explanation.
4. Rename the section `render_index_visual_block` → keep the function, but title it
   `L("landing.sa_raknas_indexet")` ("Så räknas indexet"). Place the steps first,
   then the flow SVG, then the weight bars under a sub-label using the existing
   `landing.vikter_version_b` text as the heading line.
5. Flow SVG: replace the hardcoded hex values with token values via `T()` placeholders
   or an f-string from `COLORS`.
6. Add a test asserting the snapshot figures for 2024 equal the README's, read from
   the artifact through the same helper (no literals in the test beyond the README
   comparison already done in `test_readme_figures.py`; extend that test).

---

### UX-19 · Metodologi TOC and Markdown-table styling (P2, 1.5 h)

**Instructions.**
1. Give `card_header` an optional `anchor: str = ""` that adds `id=` to the title
   element. Pass `anchor="m1"` … `"m4"` to the four section cards. Expanders cannot
   carry ids, so the TOC links only to sections 1–4, plus a final entry "5–9:
   fördjupning nedan" that links to an anchor div placed before the first expander.
2. Under the header, add a horizontal list of links
   (`<nav class="shai-toc" aria-label="Innehåll">`) as a template in `templates.py`
   with label placeholders.
3. Add CSS so Markdown tables inside `[data-testid="stMain"]` match `.shai-table`:
   header 11 px uppercase `text_muted`, a 1.5 px `primary` bottom border, row
   `border_subtle`, padding 8 × 12, and numeric columns left as is. Scope it so it
   does not affect Streamlit's own dataframes (canvas-based, so unaffected).
4. Run tests and take screenshots.

---

### Deferred (P3), listed for completeness and not scheduled

- **UX-20:** move the `"Laddar data..."` spinner text to `L("ui.laddar_data")` on
  all pages.
- **UX-21:** an `st.fragment` around the Sida 01 risk-filtered section. This requires
  moving the histogram out of the map's column row, which is a layout change, and
  moving the risk pills from the sidebar into the fragment. It is also possible around
  the Sida 05 sliders and results.
- **UX-22:** `st.navigation` with `st.Page(url_path=…)` preserving the current URLs.
  It needs the landing content moved out of `app.py`, and `test_pages_render`
  rewritten to drive pages through the router.
- **UX-23:** a dark theme. `[theme.dark]` in config plus CSS variables makes this
  tractable after UX-01, but every chart needs a dark layout variant.

---

## B5. Testing and regression checklist

Tick each item in `docs/UX_CHECKLIST.md` during UX-17, at **1440 px and 390 px**
unless stated.

### Automated

- [ ] `pytest -q` (full, including browser): passed ≥ baseline, 0 failed
- [ ] `pytest tests/test_pages_render.py`: all 67 renders (6 pages × 11 years +
      landing)
- [ ] `pytest tests/test_pages_text_fit.py`: no cut chart text at any width
- [ ] `pytest tests/test_readme_figures.py tests/test_copy_matches_artifacts.py`:
      figures unchanged
- [ ] `python scripts/audit.py`: passes
- [ ] New tests: `test_css_tokens`, `test_contrast`, landing nav click, sidebar
      persistence, one `h1` per page, no nested cards on Sida 02, preset AppTest,
      and the CSV table (if UX-14b)

### Application startup and global

- [ ] `streamlit run app.py` starts with no warnings in the terminal or the browser
      console
- [ ] Sidebar: 7 links in 3 groups, the correct one active on each page, a focus ring
      on Tab
- [ ] Year 2014 → every page shows 2014 data. 2014 has no previous-year deltas (Sida
      01 shows "–" for population)
- [ ] Year persists across all navigation paths, including through Metodologi (where
      the year control is hidden)
- [ ] Risk filter appears only on Sida 01. Hög → navigate away → back → still Hög.
      Clearing all = all classes
- [ ] Phone: the sidebar opens via the button; every link works; the sidebar closes
      on navigation
- [ ] Every page: one `h1`, header chips correct (year, data date), footer shows the
      version

### Landing

- [ ] Hero, stat strip (2014–2024, 290, 21, 3), explanation, "Vad är SHAI?", steps,
      flow, weight bars (labelled Version B), credibility
- [ ] Each of the 6 cards navigates to the right page, by mouse and keyboard
- [ ] (UX-18) Läget 2024 shows 16,3 / 84 av 290 / Lidingö / Åsele, and its link opens
      Riksöversikt

### Sida 01 · Riksöversikt (2024)

- [ ] KPIs: 16,3 % av inkomsten (▼ −3,3 %), 84 av 290, K/T 1,40 (▼ −20,9 %),
      population 0,3 % (+36 003)
- [ ] Cost history expander opens; the table is correct; 2024 is highlighted in the
      caption
- [ ] Map renders; zoom shows labels; hover tooltip; legend ends at −2,39 and 2,62;
      unchanged when the filter changes
- [ ] Histogram: three stacked classes, median line; responds to the filter
- [ ] Top 15: Lidingö first (worst), Åsele first (best); pills show text; the
      subtitle names an active filter; the callout appears when filtered
- [ ] All "Om …" expanders open
- [ ] (UX-14b) The full table has 290 rows, is sortable by every column, and the CSV
      downloads and opens in Excel with correct decimals

### Sida 02 · Länsjämförelse

- [ ] County picker: deselect all → info message, chart hidden, ranking and
      Robusthet still visible; reselect → chart back
- [ ] Tabs C and B: trend chart, in-page legend, ranking with 21 rows (Västerbottens
      län #1 for C 2024)
- [ ] Formula expander shows LaTeX; "Varför skiljer…" shows the table, A formula,
      factor sentence (1,17×) and top/bottom 5 per tab
- [ ] Robusthet: C 84/136/70, B 57/159/74; 73 of 290 disagree; the divergent table
      lists Perstorp first
- [ ] No card-in-card frames

### Sida 03 · Kommunanalys

- [ ] Default Stockholm: 44,2, 413 600 SEK, K/T 1,23, rate 4,30 %
- [ ] Changing the kommun updates the KPIs, the projection, the components and the
      sentence
- [ ] Projection: kommun, county, three scenarios to 2030; county 2025 values 21,8 /
      35,5 / 44,0; legend labels not clipped
- [ ] Component charts: Swedish axes; the driver is highlighted and labelled

### Sida 04 · Kontantinsatsanalys

- [ ] Default Stockholm, singel, 10 %, observed margin 0,8 pp: 859 700 SEK, 20,8 år,
      41 449 SEK/mån
- [ ] Bostadsrätt → län mode: 421 400 SEK, 10,5 år; the selector lists län
- [ ] Household Par, savings slider, margin slider: every figure updates; the margin
      resets on a year change
- [ ] All 8 KPIs present in the answer card; findings; reachability chart with
      Swedish axis
- [ ] Timeline legible (AA); regime cards: 5 / 3+2 / 1 by width; deltas correct
- [ ] Comparison tabs: 3 charts; best/worst marked by text; reference lines present
- [ ] Villa vs BR table matches the previous values; Nyckelinsikt; Detaljer table
      with 15 columns and column help
- [ ] Year 2014 and 2020 render with no error (negative-real-rate years)

### Sida 05 · Scenariosimulator

- [ ] Default Stockholms län: base 35,9. Rate slider +2 pp → 45,9 (+28 %)
- [ ] Each preset sets the sliders (Räntecykeln: +3,0 / +9 / −5) and the results;
      Återställ zeroes them
- [ ] Findings; surface with the marker at the current scenario; national counts and
      sentence; median sentence when moved
- [ ] Bar chart and comparison table (4 rows) agree with the KPIs
- [ ] No Streamlit session-state warning after using the presets

### Sida 06 · Metodologi

- [ ] Sections 1–4 visible; the sources table shows provenance years (income to 2024,
      price to 2025)
- [ ] Formulas A, B and C render; the cost history renders, or its caption says why
      not
- [ ] Expanders 5–9 open; limitations F1–F18 listed; timeline AA
- [ ] Footer cites the sources; no year control shown
- [ ] (UX-19) TOC links scroll to the sections

### Error and empty states

- [ ] Temporarily rename `data/processed/affordability_ranked.parquet` locally: Sida
      01 shows the error and "Tekniska detaljer". Restore it and **do not commit**
- [ ] The no-data-for-year path still shows the warning, which is unreachable by
      design but covered by AppTest

### Accessibility

- [ ] `tests/test_contrast.py` green; spot-check with a browser contrast tool on
      eyebrows, tags, MEDEL pills and the timeline
- [ ] Keyboard-only: reach and operate the sidebar, the landing cards, every select,
      slider, radio, tab, expander, button and help badge; the focus is always visible
- [ ] Zoom to 200 % at 1440 px: no clipped text, no overlapping cards
- [ ] Screen reader (NVDA or VoiceOver) heading list shows h1, then h2/h3 in order on
      Sida 04

### Browser compatibility

- [ ] Chromium (automated), plus a manual check in Firefox and Safari/WebKit of
      landing, Sida 01 (map) and Sida 04 (tabs and charts). The `:has()` selectors
      already in use need Firefox ≥ 121.

---

## B6. Rollback strategy

1. **The original is preserved.**
   - `main` is never modified during the work. Tag `ux-baseline` marks the starting
     commit.
   - Production (Streamlit Community Cloud) deploys from `main`, so it is unaffected
     until a PR is merged.
2. **Isolation.**
   - All work happens on `ux/modernization`.
   - Optionally, use a worktree (`git worktree add ../shai-ux ux/modernization`) so
     `main` stays runnable side by side for comparison.
3. **Traceability.**
   - One commit (or a short series) per task, prefixed `ux(UX-NN):`.
   - `git log --oneline --grep "ux(UX-12)"` lists a task's commits.
   - `git diff ux-baseline..HEAD -- <file>` shows the cumulative change to any file.
   - `screenshots/<task-id>/` shows the visual state after each task.
4. **Reverting one change.** `git revert <sha>` for that task's commits, in reverse
   order. Dependency notes:
   - Reverting UX-01 requires reverting UX-02, UX-03 and UX-09 first, since they use
     its CSS variables.
   - Reverting UX-09 requires reverting UX-12 and UX-13, which use
     `framed`/`compact`.
   - All other tasks revert independently.
   - Run the fast suite after any revert.
5. **The REVIEW items have built-in fallbacks** (A10). The UX-07 and UX-12 palette
   fallbacks are small follow-up commits, not reverts.
6. **Recovering from a failed task.**
   - If the suite goes red and the cause is not found within 30 minutes, run
     `git stash` or `git reset --hard HEAD` (the task is uncommitted) and re-plan the
     task smaller.
   - If a committed task is found faulty later, revert it and reopen it in
     `docs/UX_CHECKLIST.md`.
7. **Release.**
   - Open a PR from `ux/modernization` to `main` with the UX-17 report.
   - After the merge, tag `v1.4.0` (the UI version bump in `pyproject.toml`, so the
     footer shows it).
   - If production shows a problem, run `git revert -m 1 <merge-sha>` on `main` and
     redeploy. The data artifacts are untouched, so no data rollback is needed.

---

## Stage 4: internal review of this plan

| Check | Finding | Action taken |
|---|---|---|
| Missing pages | All 7 entry points are covered (A6). The admin scripts are listed as untouched. | — |
| Overlooked features | The cross-checked feature inventory has 72 IDs. Two were easy to miss: the bank-margin reset per year (I3), and the BR fallback note (I7). Both are named in the UX-12 must-keep list. | Added |
| Unnecessary changes | `st.navigation`, fragments, a dark theme, AgGrid and an icon library were each evaluated and rejected or deferred, with reasons. | Deferred (P3) |
| Unrealistic estimates | P0 + P1 = 36 h against 40 h available, with QA fixed at 6 h. UX-12 is the largest risk at 4 h, so it has a scope-down fallback. | Buffer and fallback defined |
| Conflicting decisions | (1) `primaryColor` tied to `accent` by a test vs the AA requirement: resolved by a documented test change. (2) The `vintage_badge` test vs the header chip: resolved by a documented test change. (3) The sidebar risk legend vs inert controls: it moves with the filter. | Resolved in UX-02, UX-07 and UX-08 |
| Technical incompatibilities | Several CSS hooks depend on Streamlit DOM test-ids or keyed-container classes (`.st-key-*`, `stAlert`, `stPageLink-NavLink`, `stHeaderActionElements`). Each prompt says **verify in the DOM first**, and UX-17 lists them in the report so a Streamlit upgrade can be checked against them. `st.space` exists in 1.56 (verified). `requirements.txt` allows `>=1.55`; nothing in this plan needs more than 1.55, apart from `st.space`, for which `spacer()` has a CSS fallback. | Mitigated |
| Risks to functionality | Highest: UX-07 (state persistence), UX-12 (page re-composition), UX-05 (navigation). Each has a dedicated automated test, added in its task. | Covered |
| Copy and figure guards | Every new string goes through `L()`, and figures are interpolated. The README figures are re-verified in UX-17. | Covered |

**Verdict.** The P0 + P1 scope is achievable in 4.5 working days with 0.5 day of
buffer. The P2 items are stretch goals, ordered by value: UX-14b, UX-18, UX-15,
UX-19.

---

## Items requiring explicit approval before implementation

1. **UX-07:** show the year control only where it is read (hidden on Metodologi; on
   landing only if UX-18 is approved), and the risk filter only on Riksöversikt.
   *Fallback:* keep the controls everywhere with a "Gäller inte den här sidan"
   caption.
2. **UX-12 palette:** regulatory regimes on a chronological slate-to-navy ramp with
   the current regime in gold. Best and worst are marked by text and an outline, not
   green and red. *Fallback:* keep the regime colours; remove only the best/worst
   fill override.
3. **UX-02:** `primaryColor` changes from gold `#C4A35A` to dark gold `#8A6A1F`, and
   `text_secondary` darkens from `#6B7280` to `#4B5563` (a visible but subtle change).
4. **UX-08:** the data vintage moves from a separate badge into the page-header chip
   (a test is adjusted).
5. **Scope:** committed P0 + P1 (36 h); P2 as time allows; P3 deferred.
