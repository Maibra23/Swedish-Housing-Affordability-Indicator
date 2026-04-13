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

Use ECharts via `streamlit-echarts`:

```python
{
    "backgroundColor": "#FFFFFF",
    "geo": {
        "map": "world",
        "roam": False,
        "center": [16, 62],
        "zoom": 4.2,
        "itemStyle": {
            "areaColor": "#F7F8FA",
            "borderColor": "#D1D5DB",
            "borderWidth": 0.5
        }
    },
    "visualMap": {
        "min": -2.5, "max": 2.5,
        "left": 20, "bottom": 20,
        "orient": "horizontal",
        "inRange": {
            "color": ["#2E7D5B","#A8C4A4","#E5E7EB","#E8BE7C","#D4A03C","#B94A48"]
        },
        "dimension": 2
    },
    "series": [{
        "type": "scatter",
        "coordinateSystem": "geo",
        "symbolSize": "function(val) { return 6 + Math.abs(val[2])*4; }",
        "data": [...]  # [lon, lat, value, name]
    }]
}
```

Each municipality plotted as a scatter point colored by SHAI value, sized by absolute deviation. This avoids needing GeoJSON polygons for all 290 municipalities while preserving the visual signature.

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