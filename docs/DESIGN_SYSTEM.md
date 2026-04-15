# SHAI Design System Reference
## Ported from KRI Dashboard mockup

This document is the single source of visual truth. All Streamlit pages must match these tokens.

---

## 1. Color tokens

```python
COLORS = {
    "primary":      "#0B1F3F",   # Navy, KPI bars, headers
    "primary_light":"#1B2A4A",
    "secondary":    "#4A6FA5",
    "accent":       "#C4A35A",   # Gold accent, eyebrow text, focus states
    "low_risk":     "#2E7D5B",   # Green
    "medium_risk":  "#D4A03C",   # Amber
    "high_risk":    "#B94A48",   # Red
    "bg":           "#F7F8FA",
    "card_bg":      "#FFFFFF",
    "text_primary": "#1A1A2E",
    "text_secondary":"#6B7280",
    "text_tertiary":"#9CA3AF",
    "border":       "#EEF0F3",
    "grid":         "#E5E7EB",
}
```

## 2. Typography

| Use | Family | Weight | Size |
|-----|--------|--------|------|
| Page title | Source Sans Pro | 700 | 28px |
| Card title | Source Sans Pro | 700 | 15px |
| Eyebrow | Source Sans Pro | 600 | 11px uppercase, 1.5px tracking |
| Body | Source Sans Pro | 400 | 14px |
| KPI value | Source Sans Pro | 700 | 32px tabular numerics |
| Numeric data | IBM Plex Mono | 400 to 500 | 11 to 12.5px |
| Table headers | Source Sans Pro | 600 | 10.5px uppercase, 1px tracking |

Load via Google Fonts in Streamlit `st.markdown` with custom CSS injection.

## 3. Spacing scale

- Section gap: 24px
- Card padding: 22px to 24px
- Page padding: 32px 40px
- KPI card gap: 16px

## 4. Component patterns

### KPI card
- Left accent bar (3px solid)
- Variants: default (navy), accent (gold), danger (red), success (green)
- Label uppercase 10.5px
- Value 32px tabular
- Delta with up/down/flat indicator in IBM Plex Mono

### Card
- White background
- 1px border `#EEF0F3`
- 4px border radius
- Header section with bottom border 14px below
- Card tag in top right (uppercase mono, 9.5px)

### Table
- Headers: 1.5px solid primary border bottom
- Rows: 1px solid border bottom
- Numeric columns right aligned with IBM Plex Mono
- Hover: `#F9FAFB` background

### Risk pill
- Three variants: hog (red), medel (amber), lag (green)
- Background 12% opacity, border 30% opacity, text full color
- Uppercase 10.5px, 0.7px tracking

## 5. Choropleth map (the Geografisk fördelning pattern)

**Implementation (SHAI):** Plotly `go.Scattergeo` in `src/ui/choropleth.py`, rendered with `st.plotly_chart`. The app does **not** use `streamlit-echarts` or Apache ECharts.

- One trace per risk class (`lag` / `medel` / `hog`) so the legend matches the three risk colors (`COLORS` in `src/ui/css.py`).
- Marker size scales with absolute z-score; marker color is fixed per risk class (not a continuous diverging scale).
- Basemap: Europe scope, lon/lat axis clamped to Sweden; land/ocean/country styling aligned with the light dashboard background (`#F7F8FA` land, white ocean).

**Reference (KRI / ECharts):** The original design doc described an ECharts scatter-on-geo option dict (visualMap, geo center ~ [16, 62]). That pattern is **conceptually** the same (points on a map, risk-colored); the production stack uses Plotly for serialization and Streamlit compatibility.

Each municipality is a point (not a filled polygon), which avoids shipping GeoJSON for all 290 municipalities while keeping a clear geographic view.

## 6. Streamlit specific implementation

- Use `st.set_page_config(layout="wide")` on every page
- Inject CSS via `st.markdown(unsafe_allow_html=True)` once per page
- Sidebar uses dark navy background (override Streamlit default with custom CSS)
- Page title block uses custom HTML, not `st.title`, to match KRI eyebrow + title + sub pattern

## 7. Loading states

Every page that loads computed data must show:
- Skeleton card with shimmer for 200ms minimum
- Swedish loading message: "Laddar data..." or specific verb form

## 8. Empty and error states

| State | Swedish message |
|-------|----------------|
| No data | "Inga data tillgängliga för den valda perioden" |
| API error | "Kunde inte hämta data. Försök igen senare." |
| Computation error | "Beräkningsfel. Se metodologisidan för detaljer." |

## 9. Accessibility minimums

- All charts have title and subtitle in DOM
- Color is never the only carrier of information (use shape, label, or pattern as backup)
- Tab order matches visual order
- Risk pills include text label, not just color