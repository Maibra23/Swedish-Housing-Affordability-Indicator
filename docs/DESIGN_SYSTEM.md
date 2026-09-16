# SHAI design system

What the code actually renders, as of Phase 3.

The previous version of this document described a Plotly `go.Scattergeo` map that
commit `4f98a23` had already replaced with Folium, and a `.lp-*` / `.riskklass-*` /
`.shai-*` class mix that T3.2 normalised away. A design document that disagrees with
the code is worse than no document: it is confidently wrong, and a reader has no way
to tell.

So this one is **checked**. `tests/test_design_system_doc.py` fails if a class listed
here is absent from the stylesheet, or a class in the stylesheet is absent here.

---

## 1. Where things live

| Module | Holds |
|--------|-------|
| `src/ui/tokens.py` | `COLORS`, `DIVERGING_SCALE` |
| `src/ui/css_layout.py` | Font import, custom properties, Streamlit chrome, sidebar |
| `src/ui/css_components.py` | Page header, KPI, card, pill, table, explanation, help, vintage |
| `src/ui/css_landing.py` | Hero, stat strip, weight bars, steps, nav cards, credibility |
| `src/ui/css_responsive.py` | Breakpoints and accessibility, plus the closing style tag |
| `src/ui/css.py` | Composes the above **in cascade order** and injects once |

**The order is load-bearing.** The webfont import must precede every rule or the
browser drops it, and the responsive and accessibility overrides must come last or
equal-specificity rules above them win. `GLOBAL_CSS` concatenates the sheets in that
order. Do not sort them.

**One injection point.** Streamlit re-runs a page top to bottom, so two `inject_css()`
calls means two style blocks racing to define the same rule. Guarded by
`tests/test_file_sizes.py`.

---

## 2. Tokens

| Token | Value |
|-------|-------|
| `primary` | `#0B1F3F` |
| `primary_light` | `#1B2A4A` |
| `secondary` | `#4A6FA5` |
| `accent` | `#C4A35A` |
| `low_risk` | `#2E7D5B` |
| `medium_risk` | `#D4A03C` |
| `high_risk` | `#B94A48` |
| `bg` | `#F7F8FA` |
| `card_bg` | `#FFFFFF` |
| `text_primary` | `#1A1A2E` |
| `text_secondary` | `#6B7280` |
| `text_tertiary` | `#9CA3AF` |
| `border` | `#EEF0F3` |
| `grid` | `#E5E7EB` |
| `hover` | `#F9FAFB` |

`COLORS["accent"]` is also `primaryColor` in `.streamlit/config.toml`, which drives
Streamlit's own widget accents: pills, sliders, focus rings. Keep the two in step.
Before T3.12 `primaryColor` was the brand navy, which left a selected pill
indistinguishable from an unselected one.

**Diverging scale**, low risk to high: `#2E7D5B` `#5B9E78` `#A8C4A4` `#E5E7EB` `#E8BE7C` `#D4A03C` `#B94A48`

The choropleth does **not** apply this scale at fixed breakpoints. See section 4.

---

## 3. Class inventory

Every `.shai-*` class in the composed stylesheet. 79 in total.

| Class | Purpose |
|-------|---------|
| `.shai-body` | Landing body copy. |
| `.shai-body-secondary` | Muted secondary paragraph. |
| `.shai-brand-mark` | Sidebar wordmark. |
| `.shai-brand-sub` | Sidebar sub-line (country, period). |
| `.shai-brand-title` | Sidebar product name. |
| `.shai-card` | Generic bordered container. |
| `.shai-card-header` | Card title row. |
| `.shai-card-light` | Card on the light landing ground. |
| `.shai-card-subtitle` | Card sub-line. |
| `.shai-card-tag` | Uppercase tag chip in a card header. |
| `.shai-card-title` | Card heading. |
| `.shai-control-label` | Sidebar control caption. |
| `.shai-cred` | Credibility strip. |
| `.shai-cred-meta` | Credibility meta line. |
| `.shai-cred-pill` | Single source pill. |
| `.shai-cred-pills` | Source pill row. |
| `.shai-explanation` | Prose under a bare number (T3.4). |
| `.shai-eyebrow` | Page-header eyebrow. |
| `.shai-flow-svg` | Index flow diagram. |
| `.shai-flow-svg-wrap` | Flow diagram wrapper. |
| `.shai-footer-note` | Page footer: source, vintage, version. |
| `.shai-header-meta` | Page-header right column (year display). |
| `.shai-headline` | Landing headline. |
| `.shai-help` | Glossary affordance wrapper (T3.5). |
| `.shai-help-mark` | The focusable question-mark button. |
| `.shai-help-pop` | Definition popover. |
| `.shai-hero` | Landing hero band. |
| `.shai-hero-eyebrow` | Hero eyebrow. Distinct from `.shai-eyebrow`, different type scale. |
| `.shai-hero-inner` | Hero content column. |
| `.shai-hero-lead` | Hero lead paragraph. |
| `.shai-kommun-name` | Municipality name cell. |
| `.shai-kpi-card` | KPI tile. |
| `.shai-kpi-card--tipped` | KPI tile carrying a tooltip. |
| `.shai-kpi-delta` | KPI change indicator. |
| `.shai-kpi-label` | KPI caption. |
| `.shai-kpi-unit` | KPI unit suffix. |
| `.shai-kpi-value` | KPI figure. |
| `.shai-nav-card` | Landing navigation card. |
| `.shai-nav-card-head` | Nav card header row. |
| `.shai-nav-desc` | Nav card description. |
| `.shai-nav-icon` | Nav card icon slot. |
| `.shai-nav-tag` | Nav card page tag. |
| `.shai-nav-title` | Nav card title. |
| `.shai-num` | Numeric cell or header. Right-aligned, tabular figures. |
| `.shai-page-header` | Page header band. |
| `.shai-page-subtitle` | Page subtitle. |
| `.shai-page-title` | Page title. |
| `.shai-rank-cell` | Ranking position cell. |
| `.shai-risk-legend` | Sidebar risk legend. |
| `.shai-risk-legend-dot` | Legend colour dot. |
| `.shai-risk-legend-row` | Legend row. |
| `.shai-risk-pill` | Risk class pill. |
| `.shai-section` | Landing section block. |
| `.shai-section-title` | Landing section heading. |
| `.shai-sidebar-brand` | Sidebar brand block. |
| `.shai-sidebar-footer` | Sidebar footer. |
| `.shai-sidebar-section-label` | Sidebar section label. |
| `.shai-stat-cell` | Stat strip cell. |
| `.shai-stat-label` | Stat caption. |
| `.shai-stat-strip` | Landing stat strip. |
| `.shai-stat-unit` | Stat unit. |
| `.shai-stat-value` | Stat figure. |
| `.shai-step` | Pipeline step card. |
| `.shai-step-arrow-svg` | Step connector arrow. |
| `.shai-step-connector` | Step connector slot. |
| `.shai-step-num` | Step number. |
| `.shai-step-text` | Step description. |
| `.shai-step-title` | Step title. |
| `.shai-steps` | Pipeline step row. |
| `.shai-table` | The one table style. Produced only by `data_table.py` (T3.8). |
| `.shai-vintage` | Data vintage badge (T3.6). |
| `.shai-vintage-dot` | Vintage badge status dot. |
| `.shai-weight-bar` | Index weight bar fill. |
| `.shai-weight-bar-wrap` | Weight bar track. |
| `.shai-weight-name` | Weight variable name. |
| `.shai-weight-pct` | Weight percentage. |
| `.shai-weight-row` | Weight row. |
| `.shai-year-display` | Selected-year figure. |
| `.shai-year-label` | Selected-year caption. |

**Naming.** One convention: everything this project defines starts `shai-`. Streamlit's
own DOM classes (`stApp`, `block-container`) are not ours to rename, and the
`variant-*`, `up`, `down`, `flat`, `lag`, `medel`, `hog` modifiers are only ever applied
alongside a `shai-` parent, never alone.

---

## 4. The map

**Folium**, not Plotly. `src/ui/choropleth.py` renders `data/geo/kommuner.geojson`.

**Basemap:** Esri `World_Light_Gray_Base`, with attribution and a background fallback.
CARTO was dropped in T1.6 because its tiles were not reliably reachable.

**Colour scale: empirical, not fixed.** The domain is built from the data each year.
It ends at the minimum and maximum, sits neutral at the median, and steps at the
quartiles. The previous fixed bounds of plus or minus 2.5 clipped 104
municipality-years off the green end while leaving the top 43 percent of the red ramp
unused, because `z_c` is left-skewed.

**Consequence for readers**, stated on the page itself: the scale is re-fitted every
year, so a colour means "among this year's most stretched", not a fixed price level.

> `folium_static` is deprecated upstream and scheduled for removal. See R8 in
> `docs/OPEN_RISKS.md`. Migrating to `st_folium` changes rerun behaviour and has not
> been done.

---

## 5. Components

| Component | Module | Notes |
|-----------|--------|-------|
| `page_title` | `components.py` | Header band with the year display |
| `kpi_card`, `render_kpi_row` | `components.py` | Omit `delta` when the metric cannot carry a trend (T1.9) |
| `card`, `card_header` | `components.py` | Generic container |
| `risk_pill` | `components.py` | Class pill. Orientation: `hog` is least affordable |
| `explanation` | `components.py` | Prose under a bare number |
| `help_badge` | `components.py` | Glossary popover. A real button, opens on focus |
| `vintage_badge` | `components.py` | Reads `generated_at()`, never the clock |
| `footer_note` | `components.py` | Source, vintage, version |
| `render_table` | `data_table.py` | The **only** producer of `.shai-table` |
| `by_risk`, `risk_codes` | `filters.py` | The **only** risk-label mapping |
| landing components | `landing.py` | Used by `app.py` alone |

---

## 6. Contributor checklist

Before opening a pull request that touches the interface:

- [ ] **New class?** Add it to section 3. `tests/test_design_system_doc.py` fails otherwise.
- [ ] **Removed a class?** Remove it from section 3 too, and check nothing still
      references it. `tests/test_css_naming.py` fails on a class used but not defined,
      and on one defined outside the `shai-` convention.
- [ ] **New user-facing string?** It goes in `SWEDISH_LABELS`, not inline.
- [ ] **String quotes a number?** Interpolate it from the artifact. A typed figure is
      Findings A, C and H returning. `tests/test_copy_matches_artifacts.py` is the guard.
- [ ] **New table?** Through `render_table`. No page builds table markup.
- [ ] **Filtering by risk?** Through `filters.py`. An empty selection means *all*.
- [ ] **Added a bare number to a page?** Add an `explanation()` beneath it.
- [ ] **File over 400 lines?** Split it, or justify the exemption in
      `tests/test_file_sizes.py` with a ceiling.
- [ ] `pytest tests/` passes, including the 81 page renders.

---

## 7. What this document does not cover

Visual equivalence with Skattekraftspanelen. D2 set convergence on that design as the
goal, and the components in section 5 were built from the task descriptions in
`docs/REVITALIZATION_PLAN.md`, because the reference repository is not available on the
machine this work was done on. The capabilities are present and tested. **Whether they
look the same is unverified.** Re-check section 5 against the reference before treating
D2 as met.
