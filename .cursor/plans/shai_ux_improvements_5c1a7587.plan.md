---
name: SHAI UX Improvements
overview: Page-by-page UX audit of the SHAI Streamlit dashboard, identifying concrete improvement areas for each of the 7 pages based on code review and live browser testing.
todos:
  - id: fix-default-year
    content: Fix default year to 2024 (or latest with data) instead of 2026 to prevent broken pages on first load
    status: pending
  - id: fix-kontantinsats-empty
    content: Add graceful empty-state handling on Kontantinsats when selected year has no data
    status: pending
  - id: nav-cards-clickable
    content: Make landing page navigation cards clickable links to their respective pages
    status: pending
  - id: lan-chart-highlight
    content: Add county multi-select/highlight to Lan Jamforelse chart so users can compare specific counties
    status: pending
  - id: tab-order-arima
    content: Swap tab order on Kommun Djupanalys so ARIMA (recommended) is the default first tab
    status: pending
  - id: year-pills-marking
    content: Visually mark imputed/future years (2025-2026) in sidebar year pills with asterisk or muted style
    status: pending
  - id: hide-risk-filter
    content: Hide or disable the risk filter pills on pages that do not use them (all except Riksoversikt)
    status: pending
  - id: preset-buttons-ux
    content: Shorten Scenario preset button labels and add tooltips for the full description
    status: pending
  - id: consolidate-kpi-rows
    content: Consolidate the two KPI card rows on Kontantinsats into a single summary row
    status: pending
  - id: methodology-toc
    content: Add a clickable table of contents to the Metodologi page
    status: pending
isProject: false
---

# SHAI Dashboard UX Improvement Audit

## Critical Functional Issues (Blocking)

### 1. Default Year 2026 Causes Broken Pages
The sidebar defaults to the current calendar year (`date.today().year` = 2026), but actual SCB data only goes through 2024. Imputed data exists for 2025 (forward-filled at +3%/year), but 2026 often has no data or produces `nan` results.

**Impact:** Kontantinsats page shows "No options" in the kommun dropdown; Scenario page shows `nan` in all KPI cards; Riksoversikt shows "Inga data tillgangliga" warning.

**Fix:** Change `_DATA_START_YEAR` or the default pill selection in [src/ui/sidebar.py](src/ui/sidebar.py) so the default year is `min(date.today().year, _LAST_ACTUAL_DATA_YEAR)` (i.e. 2024), or disable/gray out years with no data.

```python
# sidebar.py line 77-83
default_year = min(YEAR_RANGE[-1], _LAST_ACTUAL_DATA_YEAR)
selected_year = st.pills(
    "Valj ar",
    options=YEAR_RANGE,
    default=default_year,  # was YEAR_RANGE[-1]
    ...
)
```

### 2. No Graceful Handling of Empty Data on Kontantinsats
When the selected year has no data, the kommun dropdown shows "No options to select" with no explanation. The user sees a controls panel that does nothing.

**Fix:** Add an early check: if `mun_year` is empty after filtering, show a clear warning ("Inga data for [year]. Valj ett ar mellan 2020 och 2024.") and `st.stop()` before rendering controls.

---

## Page-by-Page UX Improvements

### Startsida (Landing Page) - [app.py](app.py)

| Issue | Severity | Description |
|-------|----------|-------------|
| Nav cards not clickable | Medium | The 6 navigation cards (`lp-nav-card`) look interactive (hover effect, cursor) but are just static HTML. They should link to the actual pages via `st.page_link` or wrapping in `<a>` tags. |
| Stat strip shows hardcoded data | Low | The stat strip always says "2014-2024" and "11 ar" regardless of data state. Consider making this dynamic or adding the version from `APP_VERSION`. |
| No CTA button | Medium | Hero section has no call-to-action. Adding a "Utforska riksoversikten" button linking to Riksoversikt would improve the flow. |
| Pipeline steps section height | Low | The `st.html()` rendering for pipeline steps creates a fixed-height iframe that may clip content or leave excess whitespace on different screen sizes. |

### Riksoversikt (Page 01) - [pages/01_Riksoversikt.py](pages/01_Riksoversikt.py)

| Issue | Severity | Description |
|-------|----------|-------------|
| Choropleth map load time | Medium | Folium map with 290 kommun polygons is heavy. No loading skeleton or placeholder while it renders. Users see a blank space. |
| Map-histogram ratio | Low | The 3:2 column split gives the map more space, but on narrower screens the histogram gets cramped. Consider making it responsive or allowing full-width toggle. |
| Ranking tables not sortable | Medium | The top-15 / bottom-15 ranking tables are static HTML. Users cannot sort by different columns or see beyond 15 rows. Consider using `st.dataframe` with sorting for the full dataset, with the HTML table as a "quick view". |
| No search/filter for kommun | Medium | Users who want to find a specific kommun in the ranking must scan the tables manually. A search box or a full sortable table would help. |
| KPI card tooltip discovery | Low | Tooltips on KPI cards use native `title` attribute which has a delay. A small "i" icon or question mark would make discoverability better. |
| Imputed year warning | Low | The yellow warning for imputed income years is verbose. Consider a more compact info banner or inline annotation on the KPI cards. |

### Lan Jamforelse (Page 02) - [pages/02_Lan_jamforelse.py](pages/02_Lan_jamforelse.py)

| Issue | Severity | Description |
|-------|----------|-------------|
| 21 overlapping lines | High | The trend chart shows all 21 counties as lines. Only Stockholm is highlighted; the other 20 lines overlap at low opacity (0.35), making it nearly impossible to compare specific counties. **Suggestion:** Add a multi-select to highlight specific counties, or use a "small multiples" grid layout. |
| No county selector | Medium | There is no way for users to select/highlight a specific county in the chart. They must hover over individual lines. A selectbox or multi-select filter would make comparison meaningful. |
| Ranking table limited to selected year | Low | The ranking table only shows one year at a time. A sparkline or trend column showing change over time would add value. |
| Cross-formula section uses plain markdown lists | Low | The "Varfor skiljer sig versionerna at?" section at the bottom uses simple bullet lists. This could be a visual comparison card or a diverging bar chart. |
| LaTeX formula rendering | Low | The LaTeX formula at the top of each tab is small and may not render well on all browsers. Consider a larger, styled version or a companion plain-text summary. |

### Kommun Djupanalys (Page 03) - [pages/03_Kommun_djupanalys.py](pages/03_Kommun_djupanalys.py)

| Issue | Severity | Description |
|-------|----------|-------------|
| No kommun search | Medium | The selectbox has 290 options. Streamlit selectboxes are searchable by default, but there is no type-ahead hint or grouped list (e.g., by county). Consider grouping by lan or adding a "popular" shortlist. |
| Prophet tab shown first despite ARIMA being recommended | Medium | The tab order is Prophet then ARIMA, but ARIMA is marked "rekommenderad". The recommended model should be the default/first tab. |
| Warning bar is always visible | Low | The caveat warning about 11 observations is always shown, even before any forecast is displayed. It could be placed inside the forecast tab instead. |
| Component breakdown star driver | Low | The star annotation for the "driver" component is subtle. Consider using a card or callout to make the key driver insight more prominent. |
| No comparison between kommuner | Medium | Users can only view one kommun at a time. A comparison mode (select 2-3 kommuner) would be valuable for buyers deciding between locations. |

### Kontantinsats (Page 04) - [pages/04_Kontantinsats.py](pages/04_Kontantinsats.py)

| Issue | Severity | Description |
|-------|----------|-------------|
| Controls layout density | Medium | Four columns of controls (kommun, pristyp, household type, savings slider) plus an expander for advanced settings creates a dense control panel. On smaller screens, these columns get very narrow. Consider a 2x2 grid or an accordion approach. |
| Two KPI rows back-to-back | Medium | There are two `render_kpi_row` calls (affordability snapshot + baseline strip) with similar metrics. This creates 8 KPI cards in sequence, which is overwhelming. Consider consolidating to one row of 4-5 key metrics. |
| Regime cards all look the same | Low | The four regime cards (pre-2010, bolanetak, amort 1, amort 2) all use the same visual weight. The current regime (Amort 2.0) should be visually emphasized (e.g., a highlighted border or "NUVARANDE" tag). |
| Detailed table hidden in expander | Low | The full comparison dataframe is inside an expander. Consider making it a visible section since it is the most data-rich view on the page. |
| Villa vs bostadsratt comparison | Low | The side-by-side comparison uses `st.metric` which does not match the KRI card style used elsewhere. Should use KPI cards for consistency. |
| Long insight block text | Low | The "Nyckelinsikt" card has dense text. Consider using bullet points or a structured summary instead of a paragraph. |

### Scenariosimulator (Page 05) - [pages/05_Scenario.py](pages/05_Scenario.py)

| Issue | Severity | Description |
|-------|----------|-------------|
| Preset buttons text too long | Medium | The preset buttons contain multi-line text ("Riksbanken 2022 +4pp ranta, +8pp KPI, -15% pris") that gets clipped on smaller screens. Consider shorter labels with a tooltip for the full description. |
| Bar chart too simple | Medium | The basfall vs scenario comparison is a 2-bar chart which wastes a lot of space and provides little visual information. A before/after gauge, a waterfall chart, or a more detailed breakdown would be more informative. |
| No visual feedback when sliders change | Low | When users adjust sliders, the page reruns and the KPI cards update, but there is no transition or highlight to draw attention to what changed. Consider color-coding the delta or adding a brief animation. |
| Comparison table uses `st.dataframe` | Low | The comparison table uses Streamlit's default dataframe styling which clashes with the custom HTML table styling used on other pages. Should use a styled HTML table for consistency. |
| Only county-level simulation | Low | The simulator works at county level, not municipality level. This is documented but could be clearer in the UI, perhaps with a note under the county selector. |
| Empty column wastes space | Low | `col_county, col_empty = st.columns([2, 1])` creates an empty right column. Use the space for a quick summary or remove it. |

### Metodologi (Page 06) - [pages/06_Metodologi.py](pages/06_Metodologi.py)

| Issue | Severity | Description |
|-------|----------|-------------|
| Dense markdown tables | Medium | The variables table and limitations table are rendered as markdown tables which can overflow horizontally on smaller screens. Consider using `st.dataframe` or HTML tables with proper overflow handling. |
| No table of contents | Medium | The page is long with 8 sections (3 visible, 5 in expanders). A clickable table of contents or anchor links at the top would improve navigation. |
| Expanders default closed | Low | Sections 4-8 are in expanders, meaning users must click to see important content like limitations and validation. Consider having the "Begransningar" section open by default since it is critical for interpreting results. |
| No visual hierarchy between always-visible and expandable sections | Low | The transition from visible sections (1-3) to expandable sections (4-8) is abrupt. A section divider or label ("Ytterligare dokumentation") would help. |

---

## Global UX Improvements (Cross-Page)

| Issue | Severity | Description |
|-------|----------|-------------|
| **Year pills include 2025-2026 without clear marking** | High | Users selecting 2025 or 2026 get imputed/missing data. The sidebar footer shows a small warning, but the pills themselves should visually indicate imputed years (e.g., italic, asterisk, or muted color). |
| **Risk filter has no effect on most pages** | Medium | The sidebar risk pills only affect the Riksoversikt page. On other pages, they appear in the sidebar but do nothing, creating confusion. Hide the risk filter on pages that don't use it. |
| **No breadcrumb or current page indicator in main area** | Low | The eyebrow text ("Sida 01 Nationell oversikt") serves this purpose, but it could be more prominent. |
| **Sidebar footer imputation warning is tiny** | Low | The amber warning about imputed income ("Inkomst 2025-2026 ar modellberaknad +3%/ar") is 10px font and easy to miss. |
| **No loading skeleton** | Low | Pages show `st.spinner("Laddar data...")` but no skeleton UI for the overall page layout. Users see a blank page until data loads. |
| **Footer version is hardcoded in some places** | Low | `footer_note` defaults to "SHAI v1.3" but `APP_VERSION` is read dynamically from `pyproject.toml`. Some footer calls don't pass the dynamic version. |
