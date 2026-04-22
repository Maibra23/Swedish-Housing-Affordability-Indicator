# SHAI Design System Reference

Single source of visual truth for the Swedish Housing Affordability Indicator dashboard.
All Streamlit pages must match these tokens. Implementation lives in `src/ui/`.

---

## 1. Color tokens

Defined in `src/ui/css.py` — import `COLORS` from there.

```python
COLORS = {
    "primary":       "#0B1F3F",   # Navy — KPI bars, sidebar bg, SHAI box
    "primary_light": "#1B2A4A",   # Lighter navy — hero gradient mid
    "secondary":     "#4A6FA5",   # Blue — chart series 1, input indicators
    "accent":        "#C4A35A",   # Gold — eyebrows, active states, brand bar
    "low_risk":      "#2E7D5B",   # Green
    "medium_risk":   "#D4A03C",   # Amber
    "high_risk":     "#B94A48",   # Red
    "bg":            "#F7F8FA",   # Page background
    "card_bg":       "#FFFFFF",   # Card / chart background
    "text_primary":  "#1A1A2E",   # Default body text
    "text_secondary":"#6B7280",   # Subdued text, axis labels
    "text_tertiary": "#9CA3AF",   # Placeholder, tags, disabled
    "border":        "#EEF0F3",   # Card borders, dividers
    "grid":          "#E5E7EB",   # Chart grid lines
    "hover":         "#F9FAFB",   # Table row hover
}
```

### Diverging scale (7-stop, for choropleth / heatmaps)

```python
DIVERGING_SCALE = [
    "#2E7D5B", "#5B9E78", "#A8C4A4",   # green → neutral
    "#E5E7EB",                          # neutral
    "#E8BE7C", "#D4A03C", "#B94A48",   # neutral → red
]
```

---

## 2. Typography

Google Fonts loaded via `@import` inside the injected `<style>` block:

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@300;400;600;700&display=swap');
```

| Use | Family | Weight | Size |
|-----|--------|--------|------|
| Page title | Source Sans 3 | 700 | 28px |
| Hero headline | Source Sans 3 | 700 | clamp(24px, 3vw, 36px) |
| Card title | Source Sans 3 | 700 | 15px |
| Eyebrow / label | Source Sans 3 | 600 | 11px — uppercase, 1.5px tracking |
| Body primary | Source Sans 3 | 400 | 14–15px |
| Body secondary | Source Sans 3 | 400 | 13–14px |
| KPI value | Source Sans 3 | 700 | 32px — tabular-nums |
| Year display | Source Sans 3 | 300 | 36px |
| Numeric data | IBM Plex Mono | 400–500 | 11–12px |
| Table headers | Source Sans 3 | 600 | 10.5px — uppercase, 1px tracking |
| Card tag | IBM Plex Mono | 400 | 9.5px — uppercase, 0.5px tracking |
| Step number | IBM Plex Mono | 600 | 10px |

> **Note:** The font is "Source Sans 3" (the 2022 rename of Source Sans Pro). Both names are listed in the CSS fallback stack for backward compatibility.

---

## 3. CSS custom properties

Defined in `:root` inside `GLOBAL_CSS`:

```css
:root {
    --shai-pad-x:          1.5rem;   /* sidebar horizontal padding */
    --shai-pad-y:          2rem;     /* sidebar vertical padding */
    --shai-label-upper:    11px;     /* eyebrow / control-label font-size */
    --shai-label-track:    1.5px;    /* eyebrow letter-spacing */
    --shai-brand-bar-offset: 14px;   /* left indent past the gold brand bar */
    --shai-hero-pad-top:   0.35rem;  /* hero top padding */
}
```

---

## 4. Layout & spacing

| Token | Value |
|-------|-------|
| Page container padding | `32px 40px` |
| Page container max-width | `1480px` |
| Section gap | 24px |
| Card padding | `22px 24px` |
| KPI card gap | 16px |
| Card border radius | 4px |
| Card border | `1px solid #EEF0F3` |
| Card header bottom border | 14px below header, 1px solid border |
| Nav card min-height | 140px |

---

## 5. Streamlit setup & chrome hiding

Every page must include at the top:

```python
st.set_page_config(
    page_title="SHAI · <Page Name>",
    page_icon=None,
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None},
)
```

Then call `inject_css()` from `src.ui.css` once per page.

The injected CSS hides Streamlit's default chrome:

```css
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header[data-testid="stHeader"] { visibility: hidden; height: 0; padding: 0; margin: 0; min-height: 0; }

/* Keep the sidebar collapse toggle visible */
[data-testid="collapsedControl"] {
    visibility: visible !important;
    position: fixed;
    top: 8px;
    left: 8px;
    z-index: 999;
}
```

`st.container(border=True)` is automatically styled as a white card via:

```css
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #EEF0F3 !important;
    border-radius: 4px;
}
```

---

## 6. Sidebar

Rendered by `src/ui/sidebar.py` → `render_sidebar(page_key)`. Call once per page.

**Dimensions:** Fixed `260px` wide, dark navy background `#0B1F3F`.

**Returns** a dict: `{ selected_year, risk_filter, selected_risks }`.

### Brand block (`.sidebar-brand`)

- Gold accent bar: `4px wide × 16px tall`, left-positioned, `border-radius: 1px`
- `.brand-mark`: 10px, uppercase, 1.5px tracking, gold `#C4A35A`
- `.brand-title`: 17px, 700 weight, white
- `.brand-sub`: 12px, `#9CA3AF`
- Separated from nav by `border-bottom: 1px solid rgba(255,255,255,0.1)`

### Navigation links

Styled via `st.page_link()`. Active page gets:

```css
background: rgba(196, 163, 90, 0.12);
color: #FFFFFF;
border-left: 3px solid #C4A35A;
```

Inactive: `color: rgba(255,255,255,0.65)`, hover adds `rgba(255,255,255,0.08)` bg.

### Controls

- `.control-label`: 10px, uppercase, 1.5px tracking, gold in sidebar context
- Year selector: `st.pills()` — single selection, default = last actual data year (2024)
- Risk filter: `st.pills()` with `selection_mode="multi"`, options: "Hög", "Medel", "Låg"
- Empty risk selection = show all three

**Pill styling (active):** Gold bg `#C4A35A`, navy text `#0B1F3F`, weight 500.
**Pill styling (inactive):** `rgba(255,255,255,0.10)` bg, white 85% text.

### Risk legend (`.riskklass-legend`)

Inline dot + label rows:

```css
.riskklass-punkt { width: 8px; height: 8px; border-radius: 50%; }
```
Colors: `#2E7D5B` (låg), `#D4A03C` (medel), `#B94A48` (hög).

### Sidebar footer (`.sidebar-footer`)

- 10px font, `#6B7280`
- `border-top: 1px solid rgba(255,255,255,0.1)`, `margin-top: 32px`
- Shows: data source, last-updated date (dynamic), imputed income note (amber), version

---

## 7. Component patterns

All components live in `src/ui/components.py` and return HTML strings for use with
`st.markdown(unsafe_allow_html=True)`.

### `page_title(eyebrow, title, subtitle, year)`

Renders the full-width page header block. Layout: left block (eyebrow + title + subtitle) + right block (year display).

```html
<div class="shai-page-header">         <!-- border-bottom 1.5px, pb 20px, mb 24px -->
  <div>
    <div class="shai-eyebrow">…</div>  <!-- gold, 11px uppercase -->
    <div class="shai-page-title">…</div> <!-- 28px, navy-dark -->
    <div class="shai-page-subtitle">…</div> <!-- 14px, text_secondary -->
  </div>
  <div class="shai-header-meta">
    <div class="shai-year-display">…</div> <!-- 36px, weight 300, tertiary -->
    <div class="shai-year-label">Analysår</div> <!-- 10px mono uppercase -->
  </div>
</div>
```

### `kpi_card(label, value, unit, delta, delta_direction, variant, tooltip)`

```html
<div class="shai-kpi-card variant-{variant}">  <!-- left 3px accent bar -->
  <div class="shai-kpi-label">…</div>           <!-- 10.5px uppercase -->
  <div class="shai-kpi-value">…<span class="shai-kpi-unit">…</span></div>
  <div class="shai-kpi-delta {direction}">▲/▼/◆ …</div>
</div>
```

**Variants** (left bar color):

| Variant | Color |
|---------|-------|
| `default` | Navy `#0B1F3F` |
| `accent` | Gold `#C4A35A` |
| `danger` | Red `#B94A48` |
| `success` | Green `#2E7D5B` |

**Delta direction semantics** (housing affordability domain):

| Direction | Color | Arrow | Meaning |
|-----------|-------|-------|---------|
| `up` | Red `#B94A48` | ▲ | Prices / costs rose — worse |
| `down` | Green `#2E7D5B` | ▼ | Prices / costs fell — better |
| `flat` | Gray `#6B7280` | ◆ | No significant change |

Use `render_kpi_row(cards)` to lay out a list of `kpi_card()` HTML strings in equal-width columns.

### `card_header(title, subtitle, tag)` / `card(title, subtitle, tag, content)`

Used inside `st.container(border=True)` blocks. Returns header-only HTML or a full card.

```html
<div class="shai-card-header">  <!-- border-bottom, pb 14px, mb 16px -->
  <div>
    <div class="shai-card-title">…</div>    <!-- 15px, 700 -->
    <div class="shai-card-subtitle">…</div> <!-- 12px, text_secondary -->
  </div>
  <span class="shai-card-tag">…</span>     <!-- 9.5px mono, uppercase, tertiary -->
</div>
```

### `risk_pill(level)`

```html
<span class="shai-risk-pill {level}">Låg | Medel | Hög</span>
```

| Level | Bg opacity | Border opacity | Text |
|-------|-----------|---------------|------|
| `lag` | 12% green | 30% green | `#2E7D5B` |
| `medel` | 12% amber | 30% amber | `#D4A03C` |
| `hog` | 12% red | 30% red | `#B94A48` |

Styles: `10.5px`, uppercase, `0.7px` tracking, `border-radius: 3px`, padding `3px 10px`.

### Table (`.shai-table`)

```html
<table class="shai-table">
  <thead>
    <tr><th>…</th><th class="num">…</th></tr>
  </thead>
  <tbody>
    <tr>
      <td class="rank-cell">1</td>          <!-- 40px, centered -->
      <td class="kommun-name">Stockholm</td> <!-- 600 weight, navy -->
      <td class="num">42,3</td>             <!-- right-align, IBM Plex Mono 12px -->
    </tr>
  </tbody>
</table>
```

- Header border-bottom: `1.5px solid #0B1F3F`
- Row border-bottom: `1px solid #EEF0F3`
- Row hover: `#F9FAFB`

### `footer_note(source, version)`

Centered flex row with "KÄLLA" label, source string, and version `<code>` chip.

```css
.shai-footer-note { border-top: 1px solid #EEF0F3; margin-top: 32px; padding: 12px 0; }
.shai-footer-note code { font-family: IBM Plex Mono; background: #F7F8FA; border: 1px solid #EEF0F3; }
```

---

## 8. Chart theme

Defined in `src/ui/chart_theme.py`. Use `get_chart_layout()` for all Plotly charts.

### Chart color palette (8 series)

```python
CHART_PALETTE = [
    "#4A6FA5",  # blue (secondary)
    "#2E7D5B",  # green (low risk)
    "#C4A35A",  # gold (accent)
    "#B94A48",  # red (high risk)
    "#7B68A8",  # purple
    "#D4785A",  # coral
    "#3D8B6E",  # teal
    "#5A7FBD",  # light blue
]
```

### `get_chart_layout(title, height, xaxis_title, yaxis_title, showlegend)`

Key properties:

| Property | Value |
|----------|-------|
| Font family | Source Sans 3, sans-serif |
| Font size (base) | 12px |
| Plot/paper bgcolor | `#FFFFFF` (card_bg) |
| Margins | `l:50, r:20, t:40 (with title) / 20, b:50` |
| X grid color | `#E5E7EB` |
| Y grid color | `#E5E7EB`, **dotted** |
| Hover bg | `#0B1F3F` (navy) |
| Hover font | white, 12px, Source Sans 3 |
| Title | 15px, left-aligned (`x: 0.02`) |
| Legend | horizontal, above chart (`y: 1.02`), 11px |

---

## 9. Landing page components

Rendered by functions in `src/ui/components.py`. Used only in `app.py`.

### Hero (`.lp-hero`)

```css
background: linear-gradient(135deg, #0B1F3F 0%, #1B2A4A 55%, #0F2847 100%);
border: 1px solid #C4A35A;
border-radius: 6px;
```

- `.lp-eyebrow`: 11px, uppercase, 1.5px tracking, gold, `padding-left: 14px` (past brand bar)
- `.lp-headline`: clamp(24px, 3vw, 36px), 700, white
- `.lp-hero-lead`: 15px, `rgba(255,255,255,0.75)`, 1.6 line-height, max-width 600px

### Stat strip (`.lp-stat-strip`)

4-column grid attached to the bottom edge of the hero (`margin-top: -1px`).

```css
border-top: 3px solid #C4A35A;   /* gold top accent */
border-radius: 0 0 6px 6px;
```

- `.lp-stat-label`: 10.5px, uppercase, 1px tracking, `#6B7280`
- `.lp-stat-value`: IBM Plex Mono, 24px, 700, `#1A1A2E`
- `.lp-stat-unit`: 12px, `#9CA3AF`

### Weight bars (`.lp-weight-row`)

Used in the index overview block. Row = label (min-width 180px) + track bar + % value.

```css
.lp-weight-bar-wrap { height: 10px; background: #EEF0F3; border-radius: 3px; }
.lp-weight-bar      { transition: width 0.4s ease; }
.lp-weight-pct      { font-family: IBM Plex Mono; font-size: 12px; min-width: 36px; }
```

Index weights: K/T-kvot 35%, Medianinkomst 25%, Styrränta 20%, Inflation 10%, Arbetslöshet 10%.

### Flow SVG

SVG `viewBox="0 0 580 130"` illustrating: 3 input boxes → SHAI Index box → 3 risk output boxes.
Arrows use named SVG `<marker>` elements in gold, green, amber, red.
SHAI box: navy fill, gold stroke 1.5px.

### Pipeline steps (`.lp-step`)

```css
border-left: 3px solid #C4A35A;
border-radius: 4px;
```

Hover: `box-shadow: 0 4px 12px rgba(0,0,0,0.06)`.
Steps connected by gold SVG arrow connectors (`.lp-step-connector`).

> **Note:** Rendered via `st.html()` (not `st.markdown()`) to prevent indented HTML being parsed as code blocks.

### Navigation cards (`.lp-nav-card`)

```css
border-left: 3px solid #C4A35A;
border-radius: 4px;
min-height: 140px;
```

Hover: `box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-1px)`.

- `.lp-nav-tag`: IBM Plex Mono, 9px, uppercase
- `.lp-nav-title`: 15px, 700
- `.lp-nav-desc`: 13px, `#6B7280`, 1.5 line-height

### Credibility block (`.lp-cred`)

White card with centered source pills (`.lp-cred-pill`): IBM Plex Mono, 11px, bg `#F7F8FA`, border `#EEF0F3`.

---

## 10. Choropleth map

**Implementation:** Plotly `go.Scattergeo` in `src/ui/choropleth.py`, rendered with `st.plotly_chart`.

- One trace per risk class (`lag` / `medel` / `hog`) — legend matches the three risk colors.
- Marker size scales with absolute z-score; marker color is fixed per class (not a continuous scale).
- Each municipality is a **point** (not a filled polygon) — avoids shipping GeoJSON for 290 municipalities.
- Basemap: Europe scope, lon/lat clamped to Sweden; land `#F7F8FA`, ocean white.

---

## 11. Responsive breakpoints

```css
@media (max-width: 900px) {
    .lp-stat-strip { grid-template-columns: repeat(2, 1fr); }
    .lp-steps { flex-direction: column; gap: 12px; }
    .lp-step-connector { transform: rotate(90deg); }
}

@media (max-width: 520px) {
    .lp-stat-strip { grid-template-columns: 1fr; }
    .lp-stat-cell  { border-right: none; border-bottom: 1px solid #EEF0F3; }
    .lp-hero       { padding-left: 1rem; padding-right: 1rem; }
}
```

---

## 12. Loading, empty, and error states

Every page that loads data must wrap the load in `st.spinner("Laddar data...")`.

| State | Swedish message |
|-------|----------------|
| No data | `"Inga data tillgängliga för den valda perioden"` |
| API / IO error | `"Kunde inte hämta data. Försök igen senare."` |
| Computation error | `"Beräkningsfel. Se metodologisidan för detaljer."` |

---

## 13. Accessibility

```css
@media (prefers-reduced-motion: reduce) {
    .lp-step, .lp-nav-card, .lp-step-arrow-svg, .lp-weight-bar {
        transition: none !important;
    }
}
```

- All Plotly charts must have a `title` set (rendered in DOM).
- Color is never the only information carrier — risk pills include a text label alongside color.
- Tab order matches visual order.
- SVG decorative elements use `aria-hidden="true"`.
- Tooltip text attached via `title=` attribute on KPI cards (`kpi-card--tipped` cursor).
