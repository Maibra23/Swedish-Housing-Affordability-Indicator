---
name: Fix SHAI Dashboard Bugs
overview: "Fix all identified bugs across the 7 pages of the SHAI Streamlit dashboard: broken map on Riksoversikt, wrong SHAI values on Scenario page, rendering issues on Kontantinsats, deprecation warnings, and the phantom BidiComponent error from streamlit-echarts."
todos:
  - id: fix-echarts
    content: Remove streamlit-echarts from pyproject.toml and pip uninstall it to eliminate BidiComponent error on Riksoversikt
    status: pending
  - id: fix-scenario-formula
    content: Rewrite simulator.py to use transaction_price_sek and percentage-point rates matching affordability.py compute_version_c
    status: pending
  - id: fix-scenario-page
    content: Update pages/05_Scenario.py to pass transaction_price_sek and correct rate units to the simulator
    status: pending
  - id: fix-kontantinsats-cards
    content: Restructure regime card HTML in pages/04_Kontantinsats.py to avoid Streamlit HTML sanitization issues
    status: pending
  - id: fix-choropleth
    content: Improve scatter dot visibility in src/ui/choropleth.py (larger dots, better opacity, clearer visual)
    status: pending
  - id: verify-all-pages
    content: Restart Streamlit and click through all 7 pages in the browser to verify all fixes work
    status: pending
isProject: false
---

# Fix All SHAI Dashboard Bugs

## Bug Inventory (by page)

### BUG 1: Riksoversikt -- BidiComponent Error (red error box on map)

**Root cause:** `streamlit-echarts` is listed as a dependency in [pyproject.toml](pyproject.toml) (line 21) but is never imported or used anywhere in Python code. The choropleth map was rewritten to use Plotly (`src/ui/choropleth.py`). However, Streamlit still loads the `streamlit-echarts` frontend component (BidiComponent) automatically when it is installed, and the component crashes because it receives no valid ECharts config with a `regions` property.

**Fix:** Remove `streamlit-echarts` from `pyproject.toml` dependencies, then `pip uninstall streamlit-echarts` to remove the installed package. This eliminates the BidiComponent error entirely.

### BUG 2: Scenario page -- SHAI Version C value is wildly wrong (~41,187,400 instead of ~41)

**Root cause:** The scenario simulator in [src/scenario/simulator.py](src/scenario/simulator.py) computes Version C as:

```
V_C = Income / (kt_ratio * real_rate)
```

But the **actual** Version C formula in [src/indices/affordability.py](src/indices/affordability.py) (line 75-92) uses `transaction_price_sek` (e.g. 8,597,000 SEK) not `kt_ratio` (e.g. 1.36):

```
V_C = Income / (transaction_price_sek * real_rate_decimal)
```

Additionally, the affordability module keeps the rate in percentage points (e.g. 3.63) and uses `.clip(lower=0.5)` then divides by 100. The simulator instead works in decimal from the start and uses `max(rate - cpi, 0.005)`. These are incompatible formulas.

**Fix:** Rewrite `simulate()` in `src/scenario/simulator.py` and update `pages/05_Scenario.py` to:
- Pass `transaction_price_sek` instead of `kt_ratio` to the simulator
- Align the formula exactly with `compute_version_c` from `affordability.py`:
  - Use `real_rate = max(rate_pp - cpi_pp, 0.5)` in percentage points
  - Then `real_rate_decimal = real_rate / 100.0`
  - Then `V_C = income / (price * real_rate_decimal)`
- The county panel includes `transaction_price_sek` (verify from county data), or compute it from `kt_ratio * taxeringsvarde` if needed
- Update the page UI to pass the corrected baseline_panel with `transaction_price_sek`
- Keep `rate_shock` as percentage points (slider 0-5 pp), do NOT divide by 100 before passing

### BUG 3: Kontantinsats page -- regime cards show raw HTML

**Root cause:** In [pages/04_Kontantinsats.py](pages/04_Kontantinsats.py) lines 135-163, the four regime cards are rendered via `st.markdown(..., unsafe_allow_html=True)`. The HTML contains inline style attributes with embedded `<div>` tags. On Streamlit 1.56, the nested `<div>` elements inside `st.markdown` are being sanitized/escaped in some rendering paths, causing raw `<div>` tags to appear as text.

The specific issue is likely the f-string formatting of the `badge_html` variable and the deeply nested inline-styled `<div>` blocks within the `st.markdown` call. Streamlit's HTML sanitizer may be stripping or escaping some of these.

**Fix:** Restructure the regime cards to use simpler HTML without deeply nested styled divs. Use the existing `kpi_card()` component or a new helper function that builds the card HTML in a single clean block. Test that all four cards render correctly.

### BUG 4: Deprecation warnings -- `use_container_width` replaced by `width`

**Root cause:** Streamlit 1.56 deprecated `use_container_width` in favor of `width="stretch"` or `width="content"`. The codebase already uses `width="stretch"` in `st.plotly_chart()` calls, which is correct. But the `st.dataframe()` call in [pages/05_Scenario.py](pages/05_Scenario.py) line 239-241 uses `width="stretch"` which generates the deprecation warning.

Actually, re-checking: the server log shows the warnings come from `st.dataframe(use_container_width=True)` -- but grep found no matches for `use_container_width` in `.py` files. These warnings may come from internal Streamlit components (like `st.dataframe` defaulting to `use_container_width=True` internally). No action needed on this specific item -- these are Streamlit internal deprecation warnings, not from our code.

### BUG 5: Map has no choropleth coloring / just scattered dots

**Root cause:** The map in [src/ui/choropleth.py](src/ui/choropleth.py) uses `go.Scattergeo` (scatter points on a map), not a true choropleth (filled polygons). This means:
- Municipalities are shown as dots, not colored regions
- There is no GeoJSON boundary file in the project
- The dots are sized by z-score magnitude and colored by risk class (3 colors only)

The visual result is sparse dots on a map of Europe -- not the rich "painted map" the user expects.

**Fix:** Enhance the map visualization. Since there is no municipality GeoJSON file (and Sweden has 290 municipalities making boundary data complex), the best pragmatic approach is:
- Increase dot sizes so municipalities are more visible
- Add a title and subtitle to the legend
- Ensure the map is zoomed correctly to Sweden (current settings look correct: lat 55-70, lon 8-26)
- Consider using `go.Choropleth` with a Sweden GeoJSON file at the county level (21 regions, much simpler) if county-level boundaries can be sourced -- but this is a larger change to discuss with the user

For now, the quick fix is to make the scatter dots bigger, more opaque, and add clearer labeling.

## Files to modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Remove `streamlit-echarts` dependency |
| `src/scenario/simulator.py` | Align formula with `affordability.py` (use `transaction_price_sek`, rate in pp) |
| `pages/05_Scenario.py` | Pass `transaction_price_sek` in baseline_panel, fix rate_shock units |
| `pages/04_Kontantinsats.py` | Simplify regime card HTML to avoid Streamlit sanitization |
| `src/ui/choropleth.py` | Increase dot sizes, improve visual clarity |
