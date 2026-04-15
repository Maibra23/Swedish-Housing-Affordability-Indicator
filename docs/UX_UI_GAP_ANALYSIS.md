# SHAI UX/UI Gap Analysis — Matching the KRI Design System

This document identifies every gap between the current SHAI dashboard and the KRI Kontrollpanel design system (reference: `ux-ui-design-system.md`). Each section includes **what is missing**, **why it matters**, and **exact implementation instructions** to achieve visual parity.

---

## Table of Contents

1. [Application Shell & Chrome](#1-application-shell--chrome)
2. [Sidebar — Brand Block & Navigation](#2-sidebar--brand-block--navigation)
3. [Sidebar — Year Selector (Pills vs Slider)](#3-sidebar--year-selector-pills-vs-slider)
4. [Sidebar — Risk Filter (Pills vs Radio)](#4-sidebar--risk-filter-pills-vs-radio)
5. [Sidebar — Footer](#5-sidebar--footer)
6. [Landing Page (app.py) — Hero Section](#6-landing-page-apppy--hero-section)
7. [Landing Page — Stat Strip](#7-landing-page--stat-strip)
8. [Landing Page — "What Is SHAI?" Block](#8-landing-page--what-is-shai-block)
9. [Landing Page — Index Overview (Weights + Flow SVG)](#9-landing-page--index-overview-weights--flow-svg)
10. [Landing Page — Pipeline Steps](#10-landing-page--pipeline-steps)
11. [Landing Page — Navigation Cards](#11-landing-page--navigation-cards)
12. [Landing Page — Credibility Block](#12-landing-page--credibility-block)
13. [Page Header Component](#13-page-header-component)
14. [KPI Card — Tooltip Support](#14-kpi-card--tooltip-support)
15. [Card Header — Alignment with KRI](#15-card-header--alignment-with-kri)
16. [Chart System — ECharts vs Plotly](#16-chart-system--echarts-vs-plotly)
17. [Chart Theme — Shared ECharts Base Options](#17-chart-theme--shared-echarts-base-options)
18. [Choropleth — Folium vs ECharts Scatter](#18-choropleth--folium-vs-echarts-scatter)
19. [Tables — HTML Table Enhancements](#19-tables--html-table-enhancements)
20. [CSS Custom Properties (`:root` Variables)](#20-css-custom-properties-root-variables)
21. [Chrome Hiding (Header, Footer, MainMenu)](#21-chrome-hiding-header-footer-mainmenu)
22. [Responsive Breakpoints](#22-responsive-breakpoints)
23. [Accessibility & Reduced Motion](#23-accessibility--reduced-motion)
24. [Typography — Font Weight Gaps](#24-typography--font-weight-gaps)
25. [Streamlit Config — showSidebarNavigation](#25-streamlit-config--showsidebarnavigation)
26. [Session State Architecture](#26-session-state-architecture)
27. [Footer Note Component](#27-footer-note-component)
28. [Number Formatting — Swedish Conventions](#28-number-formatting--swedish-conventions)
29. [Sidebar Width](#29-sidebar-width)
30. [Per-Page Sidebar Duplication Pattern](#30-per-page-sidebar-duplication-pattern)

---

## 1. Application Shell & Chrome

### Current State (SHAI)
- `st.set_page_config` is set per page with basic params.
- No `menu_items` configuration (Help, Report a Bug, About all visible with defaults).
- Streamlit header bar, footer, and main menu are **all visible** (default).

### KRI Reference
- `menu_items`: `Get Help` and `Report a bug` set to `None` (hidden); `About` contains short Swedish text and data attribution.
- `#MainMenu`, `footer`, `header[data-testid="stHeader"]` are **all hidden via CSS**.
- `[data-testid="collapsedControl"]` remains visible so sidebar can be toggled.

### What to Do

**File: `src/ui/css.py`** — Add to `GLOBAL_CSS`:

```css
/* ---- Hide Streamlit chrome ---- */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
    padding: 0;
    margin: 0;
    min-height: 0;
}
/* Keep sidebar toggle visible */
[data-testid="collapsedControl"] {
    visibility: visible !important;
    position: fixed;
    top: 8px;
    left: 8px;
    z-index: 999;
}
```

**File: `app.py`** — Update `set_page_config`:

```python
st.set_page_config(
    page_title="SHAI — Bostadsekonomisk hållbarhet",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "SHAI v1.3 — Bostadsekonomisk hållbarhet. Data: SCB, Riksbanken, Kolada.",
    },
)
```

Do the same for every page file in `pages/*.py`.

### Why
The KRI design hides all default Streamlit chrome to present a clean, professional banking/analytics aesthetic. Visible chrome breaks the illusion of a custom application.

---

## 2. Sidebar — Brand Block & Navigation

### Current State (SHAI)
- Brand block uses `.shai-sidebar-brand` with a **left gold bar** (3px), eyebrow, title, subtitle.
- Navigation uses Streamlit's default multipage mechanism (file-based `pages/` folder). No custom `st.page_link` calls.
- No `.brand-mark` with `::before` pseudo-element gold bar.
- No "Navigation" section label (`.nav-section`).

### KRI Reference
- `.sidebar-brand` with bottom border and spacing.
- `.brand-mark` with `::before` pseudo-element: **4×16px gold bar** via CSS.
- `.brand-title` — white, 17px bold.
- `.brand-sub` — muted line.
- `.nav-section` — uppercase "Navigation" label.
- Custom `st.sidebar.page_link()` for each page with CSS styling (hover background, active gold left border).

### What to Do

**File: `src/ui/sidebar.py`** — Replace the brand block HTML:

```python
# Brand block — KRI style
st.markdown("""
<div class="sidebar-brand">
    <div class="brand-mark">SHAI KONTROLLPANEL</div>
    <div class="brand-title">Bostadsekonomisk<br>hållbarhet</div>
    <div class="brand-sub">Sverige · 2014 till 2024</div>
</div>
<div class="nav-section">Navigation</div>
""", unsafe_allow_html=True)
```

Then add `st.page_link()` for each page:

```python
st.page_link("app.py", label="Startsida")
st.page_link("pages/01_Riksoversikt.py", label="Riksöversikt")
st.page_link("pages/02_Lan_jamforelse.py", label="Län jämförelse")
st.page_link("pages/03_Kommun_djupanalys.py", label="Kommun djupanalys")
st.page_link("pages/04_Kontantinsats.py", label="Kontantinsats analys")
st.page_link("pages/05_Scenario.py", label="Scenariosimulator")
st.page_link("pages/06_Metodologi.py", label="Metodologi och källor")
```

**File: `src/ui/css.py`** — Add sidebar brand and nav CSS:

```css
/* ---- Sidebar brand (KRI-style) ---- */
.sidebar-brand {
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 16px;
    margin-bottom: 16px;
}
.brand-mark {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    font-weight: 600;
    padding-left: 14px;
    position: relative;
}
.brand-mark::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 4px;
    height: 16px;
    background: #C4A35A;
}
.brand-title {
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    margin: 6px 0 2px 0;
    line-height: 1.3;
}
.brand-sub {
    font-size: 12px;
    color: #9CA3AF;
}
.nav-section {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #9CA3AF;
    font-weight: 600;
    margin-bottom: 8px;
}

/* ---- Sidebar page links (KRI-style) ---- */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
section[data-testid="stSidebarContent"] a[href] {
    display: block;
    padding: 8px 12px;
    color: rgba(255,255,255,0.65) !important;
    text-decoration: none !important;
    font-size: 13px;
    border-radius: 4px;
    margin-bottom: 2px;
    transition: background 0.15s, color 0.15s;
    border-left: 3px solid transparent;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
section[data-testid="stSidebarContent"] a[href]:hover {
    background: rgba(255,255,255,0.08);
    color: #FFFFFF !important;
}
/* Active/current page link */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
section[data-testid="stSidebarContent"] a[href][aria-current="page"] {
    background: rgba(196, 163, 90, 0.12);
    color: #FFFFFF !important;
    border-left-color: #C4A35A;
}
```

### Why
The KRI sidebar is a branded navigation panel, not Streamlit defaults. Custom `page_link` with CSS gives active-page highlighting with a gold left border, matching the banking aesthetic.

---

## 3. Sidebar — Year Selector (Pills vs Slider)

### Current State (SHAI)
- Uses `st.select_slider` for year selection.
- Slider is a horizontal scrubber, not pills/chips.

### KRI Reference
- Uses `st.sidebar.pills` with `label_visibility="collapsed"`.
- Pills are styled as chips: semi-transparent white background, IBM Plex Mono ~11px.
- **Selected pill** (`aria-pressed="true"`) uses gold background + border with navy text.
- A `.control-label` HTML element above the pills acts as the visible label.

### What to Do

**File: `src/ui/sidebar.py`** — Replace the select_slider:

```python
# Year pills — KRI style
st.markdown(
    '<div class="control-label">Valt år</div>',
    unsafe_allow_html=True,
)
selected_year = st.pills(
    "Välj år",
    options=YEAR_RANGE,
    default=YEAR_RANGE[-1],
    label_visibility="collapsed",
    key="shai_year_pills",
)
```

**File: `src/ui/css.py`** — Add pill styling:

```css
/* ---- Control label (sidebar) ---- */
.control-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #9CA3AF;
    font-weight: 600;
    margin-bottom: 6px;
}

/* ---- Sidebar pills/chips ---- */
section[data-testid="stSidebar"] button[role="tab"],
section[data-testid="stSidebar"] [data-baseweb="tab"] button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: rgba(255,255,255,0.7) !important;
    border-radius: 4px !important;
    padding: 5px 10px !important;
    transition: background 0.15s !important;
}
section[data-testid="stSidebar"] button[role="tab"]:hover {
    background: rgba(255,255,255,0.12) !important;
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] button[role="tab"][aria-pressed="true"],
section[data-testid="stSidebar"] button[role="tab"][aria-selected="true"] {
    background: #C4A35A !important;
    border-color: #C4A35A !important;
    color: #0B1F3F !important;
    font-weight: 500 !important;
}
```

### Why
Pill chips are more compact, visually consistent, and match the banking dashboard look. The slider feels like a range input, not a year picker.

---

## 4. Sidebar — Risk Filter (Pills vs Radio)

### Current State (SHAI)
- Uses `st.radio` with options `["Alla", "Låg risk", "Medel risk", "Hög risk"]`.
- No colored legend dots.

### KRI Reference
- Uses HTML `.sidebar-control` with `.riskklass-legend` showing colored dots:
  - `#2E7D5B` — Låg risk
  - `#D4A03C` — Medel risk
  - `#B94A48` — Hög risk
- Then `st.sidebar.pills` with multi-select: `selection_mode="multi"`, options `["Hög", "Medel", "Låg"]`.
- Empty selection = show all.

### What to Do

**File: `src/ui/sidebar.py`** — Replace radio with colored legend + pills:

```python
# Risk filter — KRI style
st.markdown("""
<div class="control-label">Riskfilter</div>
<div class="riskklass-legend">
    <div class="riskklass-rad">
        <span class="riskklass-punkt" style="background:#2E7D5B;"></span>
        <span>Låg risk</span>
    </div>
    <div class="riskklass-rad">
        <span class="riskklass-punkt" style="background:#D4A03C;"></span>
        <span>Medel risk</span>
    </div>
    <div class="riskklass-rad">
        <span class="riskklass-punkt" style="background:#B94A48;"></span>
        <span>Hög risk</span>
    </div>
</div>
""", unsafe_allow_html=True)

selected_risks = st.pills(
    "Riskfilter",
    options=["Hög", "Medel", "Låg"],
    selection_mode="multi",
    label_visibility="collapsed",
    key="shai_risk_pills",
)
# Empty = show all
if not selected_risks:
    selected_risks = ["Hög", "Medel", "Låg"]
```

**File: `src/ui/css.py`** — Add legend CSS:

```css
/* ---- Risk legend (sidebar) ---- */
.riskklass-legend {
    margin: 8px 0 10px 0;
}
.riskklass-rad {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: rgba(255,255,255,0.7);
    margin-bottom: 4px;
}
.riskklass-punkt {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
```

### Why
Colored legend dots give immediate visual mapping to the risk categories. Multi-select pills allow filtering by multiple risk levels simultaneously, matching KRI's more flexible filtering.

---

## 5. Sidebar — Footer

### Current State (SHAI)
- Basic `.shai-sidebar-footer` with source and date.

### KRI Reference
- `.sidebar-footer` with same basic info but consistent on all pages except Riskdekomposition.

### What to Do
Current implementation is close. Ensure the footer is rendered on all pages consistently from `render_sidebar()`. No major change needed — the current approach already matches.

---

## 6. Landing Page (app.py) — Hero Section

### Current State (SHAI)
- Landing page is a plain `page_title()` + markdown text list + 4 basic KPI cards.
- No gradient hero section.
- No visual impact.

### KRI Reference
- `.lp-hero` with linear gradient (`primary` → `primary_light` → deep blue), gold border.
- `.lp-eyebrow` gold, `h1.lp-headline` white (clamp 24–36px), `.lp-hero-lead` translucent white.
- Max-width 720px, left-aligned inner content.

### What to Do

**File: `src/ui/components.py`** — Add new function:

```python
def render_landing_hero() -> None:
    """Render the KRI-style landing hero section."""
    html = f"""
    <div class="lp-hero">
        <div class="lp-hero-inner">
            <div class="lp-eyebrow">Bostadsekonomisk hållbarhetsanalys</div>
            <h1 class="lp-headline">Swedish Housing<br>Affordability Indicator</h1>
            <p class="lp-hero-lead">
                Strukturell bostadsekonomisk hållbarhet i Sveriges 290 kommuner
                och 21 län — med tre ekonometriska formler, prognoser och scenariosimulering.
            </p>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add hero CSS:

```css
/* ---- Landing hero ---- */
.lp-hero {
    background: linear-gradient(135deg, #0B1F3F 0%, #1B2A4A 60%, #0F2847 100%);
    border: 1px solid #C4A35A;
    border-radius: 6px;
    padding: 0.35rem 2rem 2rem 2rem;
    margin-bottom: 24px;
}
.lp-hero-inner {
    max-width: 720px;
}
.lp-eyebrow {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    padding-left: 14px;
    margin-bottom: 12px;
    margin-top: 20px;
}
.lp-headline {
    font-family: 'Source Sans 3', sans-serif;
    font-weight: 700;
    font-size: clamp(24px, 3vw, 36px);
    color: #FFFFFF;
    margin: 0 0 12px 0;
    line-height: 1.15;
}
.lp-hero-lead {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.6;
    max-width: 600px;
    margin: 0;
}
```

**File: `app.py`** — Replace the plain page_title + markdown with:

```python
from src.ui.components import render_landing_hero
render_landing_hero()
```

### Why
The hero is the first thing users see. The gradient navy hero with gold accent immediately communicates professional financial analytics. The current plain text landing looks like a README, not a dashboard.

---

## 7. Landing Page — Stat Strip

### Current State (SHAI)
- 4 simple KPI cards rendered via `render_kpi_row()` showing year, count of municipalities, counties, and risk filter.
- No visual connection to the hero.

### KRI Reference
- `.lp-stat-strip`: CSS grid 4 columns (responsive: 2→1); connects under hero (`margin-top: -1px`); gold top border (3px accent).
- `.lp-stat-cell` with divider borders; `.lp-stat-label`, `.lp-stat-value` (mono), `.lp-stat-unit`.

### What to Do

**File: `src/ui/components.py`** — Add:

```python
def render_landing_stat_strip(stats: list[dict]) -> None:
    """Render a stat strip connected to the hero.

    Args:
        stats: List of dicts with keys: label, value, unit.
    """
    cells = ""
    for s in stats:
        cells += f"""
        <div class="lp-stat-cell">
            <div class="lp-stat-label">{s['label']}</div>
            <div class="lp-stat-value">{s['value']}</div>
            <div class="lp-stat-unit">{s.get('unit', '')}</div>
        </div>
        """
    html = f'<div class="lp-stat-strip">{cells}</div>'
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add:

```css
/* ---- Stat strip ---- */
.lp-stat-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border: 1px solid #EEF0F3;
    border-top: 3px solid #C4A35A;
    border-radius: 0 0 6px 6px;
    background: #FFFFFF;
    margin-top: -1px;
    margin-bottom: 32px;
}
.lp-stat-cell {
    padding: 20px 24px;
    border-right: 1px solid #EEF0F3;
}
.lp-stat-cell:last-child { border-right: none; }
.lp-stat-label {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #6B7280;
    margin-bottom: 6px;
}
.lp-stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    color: #1A1A2E;
    line-height: 1.1;
}
.lp-stat-unit {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}
```

**File: `app.py`** — Use after hero:

```python
render_landing_stat_strip([
    {"label": "Analysperiod", "value": "2014–2024", "unit": "11 år"},
    {"label": "Kommuner", "value": "290", "unit": "analyserade"},
    {"label": "Län", "value": "21", "unit": "jämförda"},
    {"label": "Formler", "value": "3", "unit": "ekonometriska versioner"},
])
```

### Why
The stat strip provides at-a-glance KPIs in a compact, visually connected format. It bridges the hero to the content below and looks far more polished than standalone KPI cards.

---

## 8. Landing Page — "What Is SHAI?" Block

### Current State (SHAI)
- Plain markdown text describing the six pages.
- No card-style presentation.

### KRI Reference
- `.lp-section` + `.lp-section-title` (gold uppercase) + `.lp-card-light.lp-explain-card` with body text, max-width ~68ch.

### What to Do

**File: `src/ui/components.py`** — Add:

```python
def render_landing_what_is_block() -> None:
    """Render the 'What is SHAI?' explanation block."""
    html = """
    <div class="lp-section">
        <div class="lp-section-title">Vad är SHAI?</div>
        <div class="lp-card-light lp-explain-card">
            <div class="lp-body">
                SHAI (Swedish Housing Affordability Indicator) mäter strukturell
                bostadsekonomisk hållbarhet genom tre ekonometriska formler som
                kombinerar inkomst, bostadspriser, räntor och inflation.
            </div>
            <div class="lp-body-secondary">
                Indikatorn analyserar Sveriges 290 kommuner och 21 län med data
                från SCB, Riksbanken och Kolada. Utöver indexet erbjuds prognoser
                (Prophet och ARIMA), kontantinsatsanalys under fyra regelverk,
                och en scenariosimulator för stresstester.
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add:

```css
/* ---- Landing sections ---- */
.lp-section {
    margin-bottom: 32px;
}
.lp-section-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #C4A35A;
    margin-bottom: 12px;
}
.lp-card-light {
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 24px 28px;
}
.lp-body {
    font-size: 15px;
    color: #1A1A2E;
    line-height: 1.65;
    max-width: 68ch;
    margin-bottom: 12px;
}
.lp-body-secondary {
    font-size: 14px;
    color: #6B7280;
    line-height: 1.6;
    max-width: 68ch;
}
```

### Why
A styled explanation card with a gold section title is visually distinct from body text. It signals "important context" and follows the KRI's modular section pattern.

---

## 9. Landing Page — Index Overview (Weights + Flow SVG)

### Current State (SHAI)
- No index overview block at all.
- No visual representation of formula weights or data flow.

### KRI Reference
- `render_index_visual_block()` containing:
  - **Weight bars:** horizontal bars showing each indicator's weight percentage.
  - **Flow SVG:** five indicators → composite index → three risk classes.

### What to Do

**File: `src/ui/components.py`** — Add:

```python
def render_index_visual_block() -> None:
    """Render the index overview block with weight bars and flow diagram."""
    weights = [
        ("K/T-kvot (prisnivå)", 40),
        ("Medianinkomst", 25),
        ("Styrränta", 15),
        ("Inflation (KPI)", 10),
        ("Arbetslöshet", 10),
    ]

    bars_html = ""
    for name, pct in weights:
        bars_html += f"""
        <div class="lp-weight-row">
            <span class="lp-weight-name">{name}</span>
            <div class="lp-weight-bar-wrap">
                <div class="lp-weight-bar" style="width:{pct}%;"></div>
            </div>
            <span class="lp-weight-pct">{pct}%</span>
        </div>
        """

    flow_svg = """
    <div class="lp-flow-svg-wrap">
        <svg viewBox="0 0 600 120" class="lp-flow-svg" aria-hidden="true">
            <!-- Indicators -->
            <rect x="0" y="10" width="100" height="24" rx="3" fill="#4A6FA5" opacity="0.15" stroke="#4A6FA5" stroke-width="1"/>
            <text x="50" y="26" text-anchor="middle" fill="#4A6FA5" font-size="9" font-family="Source Sans 3">Inkomst</text>
            <rect x="0" y="40" width="100" height="24" rx="3" fill="#4A6FA5" opacity="0.15" stroke="#4A6FA5" stroke-width="1"/>
            <text x="50" y="56" text-anchor="middle" fill="#4A6FA5" font-size="9" font-family="Source Sans 3">K/T-kvot</text>
            <rect x="0" y="70" width="100" height="24" rx="3" fill="#4A6FA5" opacity="0.15" stroke="#4A6FA5" stroke-width="1"/>
            <text x="50" y="86" text-anchor="middle" fill="#4A6FA5" font-size="9" font-family="Source Sans 3">Ränta & Inflation</text>

            <!-- Arrows -->
            <line x1="105" y1="22" x2="220" y2="55" stroke="#C4A35A" stroke-width="1.5" marker-end="url(#arrow)"/>
            <line x1="105" y1="52" x2="220" y2="55" stroke="#C4A35A" stroke-width="1.5" marker-end="url(#arrow)"/>
            <line x1="105" y1="82" x2="220" y2="55" stroke="#C4A35A" stroke-width="1.5" marker-end="url(#arrow)"/>

            <!-- SHAI box -->
            <rect x="225" y="35" width="120" height="40" rx="4" fill="#0B1F3F" stroke="#C4A35A" stroke-width="1.5"/>
            <text x="285" y="58" text-anchor="middle" fill="#FFFFFF" font-size="12" font-weight="bold" font-family="Source Sans 3">SHAI Index</text>

            <!-- Output arrows -->
            <line x1="350" y1="45" x2="440" y2="22" stroke="#2E7D5B" stroke-width="1.5" marker-end="url(#arrow-g)"/>
            <line x1="350" y1="55" x2="440" y2="55" stroke="#D4A03C" stroke-width="1.5" marker-end="url(#arrow-y)"/>
            <line x1="350" y1="65" x2="440" y2="88" stroke="#B94A48" stroke-width="1.5" marker-end="url(#arrow-r)"/>

            <!-- Risk classes -->
            <rect x="445" y="10" width="100" height="24" rx="3" fill="rgba(46,125,91,0.15)" stroke="#2E7D5B" stroke-width="1"/>
            <text x="495" y="26" text-anchor="middle" fill="#2E7D5B" font-size="10" font-weight="600" font-family="Source Sans 3">Låg risk</text>
            <rect x="445" y="43" width="100" height="24" rx="3" fill="rgba(212,160,60,0.15)" stroke="#D4A03C" stroke-width="1"/>
            <text x="495" y="59" text-anchor="middle" fill="#D4A03C" font-size="10" font-weight="600" font-family="Source Sans 3">Medel risk</text>
            <rect x="445" y="76" width="100" height="24" rx="3" fill="rgba(185,74,72,0.15)" stroke="#B94A48" stroke-width="1"/>
            <text x="495" y="92" text-anchor="middle" fill="#B94A48" font-size="10" font-weight="600" font-family="Source Sans 3">Hög risk</text>

            <!-- Arrow markers -->
            <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#C4A35A"/>
                </marker>
                <marker id="arrow-g" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#2E7D5B"/>
                </marker>
                <marker id="arrow-y" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#D4A03C"/>
                </marker>
                <marker id="arrow-r" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#B94A48"/>
                </marker>
            </defs>
        </svg>
    </div>
    """

    html = f"""
    <div class="lp-section">
        <div class="lp-section-title">Indexet i överblick</div>
        <div class="lp-card-light lp-visual">
            {bars_html}
            <div style="height:24px;"></div>
            {flow_svg}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add:

```css
/* ---- Weight bars ---- */
.lp-weight-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}
.lp-weight-name {
    font-size: 13px;
    color: #1A1A2E;
    min-width: 160px;
}
.lp-weight-bar-wrap {
    flex: 1;
    height: 10px;
    background: #EEF0F3;
    border-radius: 3px;
    overflow: hidden;
}
.lp-weight-bar {
    height: 100%;
    background: #4A6FA5;
    border-radius: 3px;
    transition: width 0.4s ease;
}
.lp-weight-pct {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #6B7280;
    min-width: 36px;
    text-align: right;
}
.lp-flow-svg-wrap {
    text-align: center;
    max-width: 600px;
    margin: 0 auto;
}
.lp-flow-svg { width: 100%; height: auto; }
```

### Why
This is a signature KRI visual that explains the index methodology at a glance. Without it, users have no intuition for how the index is composed.

---

## 10. Landing Page — Pipeline Steps

### Current State (SHAI)
- No pipeline/steps section at all.

### KRI Reference
- `.lp-steps` flex row with `.lp-step` cards (gold left border, hover shadow).
- Step number, title with inline SVG icon, description text.
- Horizontal arrow connectors between steps.

### What to Do

**File: `src/ui/components.py`** — Add:

```python
def render_landing_steps() -> None:
    """Render the 3-step pipeline explanation."""
    steps = [
        ("01", "Datainsamling", "SCB, Riksbanken och Kolada levererar kommunal inkomst, K/T-kvot, styrränta, inflation och arbetslöshet."),
        ("02", "Normalisering", "Värden z-standardiseras över hela panelen (2014–2024, 290 kommuner) för jämförbar ranking."),
        ("03", "Klassificering", "Tre formler (A, B, C) beräknas och kommuner klassas som låg, medel eller hög risk."),
    ]

    steps_html = ""
    for i, (num, title, text) in enumerate(steps):
        connector = ""
        if i < len(steps) - 1:
            connector = """
            <div class="lp-step-connector">
                <svg class="lp-step-arrow-svg" viewBox="0 0 40 24" aria-hidden="true">
                    <path d="M0 12h30l-6-6M30 12l-6 6" fill="none" stroke="#C4A35A" stroke-width="2"/>
                </svg>
            </div>
            """
        steps_html += f"""
        <div class="lp-step">
            <div class="lp-step-num">{num}</div>
            <div class="lp-step-title">{title}</div>
            <div class="lp-step-text">{text}</div>
        </div>
        {connector}
        """

    html = f"""
    <div class="lp-section">
        <div class="lp-section-title">Så fungerar det i korthet</div>
        <div class="lp-steps">{steps_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add:

```css
/* ---- Pipeline steps ---- */
.lp-steps {
    display: flex;
    align-items: flex-start;
    gap: 0;
    margin-bottom: 32px;
}
.lp-step {
    flex: 1;
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-left: 3px solid #C4A35A;
    border-radius: 4px;
    padding: 20px;
    transition: box-shadow 0.2s;
}
.lp-step:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.lp-step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #C4A35A;
    font-weight: 600;
    margin-bottom: 8px;
}
.lp-step-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 8px;
}
.lp-step-text {
    font-size: 13px;
    color: #6B7280;
    line-height: 1.5;
}
.lp-step-connector {
    display: flex;
    align-items: center;
    padding: 0 8px;
}
.lp-step-arrow-svg {
    width: 40px;
    height: 24px;
}

@media (max-width: 900px) {
    .lp-steps { flex-direction: column; gap: 12px; }
    .lp-step-connector { transform: rotate(90deg); padding: 4px 0; }
}
```

### Why
The step cards visually explain the index pipeline. Users understand the process at a glance without reading dense methodology text.

---

## 11. Landing Page — Navigation Cards

### Current State (SHAI)
- Plain markdown numbered list describing pages.
- No visual navigation cards.

### KRI Reference
- `.lp-nav-card` with min-height, gold left border, hover elevation.
- Icon (SVG), optional tag, title, description.
- Wrapped in `st.container(border=True)` with a "Vad hittar du här?" heading.

### What to Do

**File: `src/ui/components.py`** — Add:

```python
def render_landing_nav_card(icon: str, title: str, desc: str, tag: str = "") -> str:
    """Return HTML for a landing navigation card.

    Args:
        icon: SVG path or emoji.
        title: Card title (page name).
        desc: Short description.
        tag: Optional badge text.
    """
    tag_html = f'<span class="lp-nav-tag">{tag}</span>' if tag else ""
    return f"""
    <div class="lp-nav-card">
        <div class="lp-nav-card-head">
            <div class="lp-nav-icon">{icon}</div>
            {tag_html}
        </div>
        <div class="lp-nav-title">{title}</div>
        <div class="lp-nav-desc">{desc}</div>
    </div>
    """
```

**File: `src/ui/css.py`** — Add:

```css
/* ---- Navigation cards (landing) ---- */
.lp-nav-card {
    background: #FFFFFF;
    border: 1px solid #EEF0F3;
    border-left: 3px solid #C4A35A;
    border-radius: 4px;
    padding: 20px;
    min-height: 140px;
    transition: box-shadow 0.2s, transform 0.15s;
    cursor: default;
}
.lp-nav-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.lp-nav-card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.lp-nav-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}
.lp-nav-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    color: #9CA3AF;
    letter-spacing: 0.5px;
}
.lp-nav-title {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 6px;
}
.lp-nav-desc {
    font-size: 13px;
    color: #6B7280;
    line-height: 1.5;
}
```

**File: `app.py`** — Use nav cards:

```python
st.markdown("""
<div class="lp-section">
    <div class="lp-section-title">Vad hittar du här?</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(render_landing_nav_card(
        "🗺️", "Riksöversikt",
        "Nationell överblick med karta, histogram och rankingtabeller.",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "📊", "Län jämförelse",
        "21 län jämförda under tre ekonometriska formler.",
    ), unsafe_allow_html=True)
with col2:
    st.markdown(render_landing_nav_card(
        "🔍", "Kommun djupanalys",
        "Historisk analys och prognos per kommun med Prophet och ARIMA.",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "💰", "Kontantinsats",
        "Jämför insatskrav under fyra regulatoriska regimer.",
    ), unsafe_allow_html=True)
with col3:
    st.markdown(render_landing_nav_card(
        "⚡", "Scenariosimulator",
        "Stresstesta med ränta-, inkomst- och prisförändringar.",
    ), unsafe_allow_html=True)
    st.markdown(render_landing_nav_card(
        "📖", "Metodologi",
        "Formler, datakällor, begränsningar och validering.",
    ), unsafe_allow_html=True)
```

### Why
Navigation cards give users a visual overview of what the dashboard offers, guiding them to the right page. The KRI version uses these as a visual sitemap.

---

## 12. Landing Page — Credibility Block

### Current State (SHAI)
- No credibility block.

### KRI Reference
- `.lp-cred` — bordered card, centered.
- `.lp-cred-pills` with data source badges.
- `.lp-cred-meta` subtitle line.

### What to Do

**File: `src/ui/components.py`** — Add:

```python
def render_landing_credibility() -> None:
    """Render the credibility/data source block."""
    html = """
    <div class="lp-cred">
        <div class="lp-cred-pills">
            <span class="lp-cred-pill">SCB</span>
            <span class="lp-cred-pill">Riksbanken</span>
            <span class="lp-cred-pill">Kolada</span>
            <span class="lp-cred-pill">Finansinspektionen</span>
        </div>
        <div class="lp-cred-meta">
            SHAI v1.3 · Öppen data · 290 kommuner · 2014–2024
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add:

```css
/* ---- Credibility block ---- */
.lp-cred {
    border: 1px solid #EEF0F3;
    border-radius: 4px;
    padding: 24px;
    text-align: center;
    margin: 32px 0;
}
.lp-cred-pills {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.lp-cred-pill {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    background: #F7F8FA;
    border: 1px solid #EEF0F3;
    border-radius: 3px;
    padding: 4px 12px;
    color: #6B7280;
    letter-spacing: 0.3px;
}
.lp-cred-meta {
    font-size: 12px;
    color: #9CA3AF;
}
```

### Why
The credibility block signals trustworthiness by showing official data sources. It's a confidence-building element for a financial analytics tool.

---

## 13. Page Header Component

### Current State (SHAI)
- `page_title()` renders eyebrow + title + subtitle as a simple stack.
- No **year display** on the right side.
- No bottom border/divider line.

### KRI Reference
- `.page-header` with `display: flex; justify-content: space-between`.
- Left: eyebrow, h1 title, subtitle.
- Right: `.header-meta` with `.year-display` (large light-weight year) + "Analysår" label in mono uppercase.
- Bottom border on the header container.

### What to Do

**File: `src/ui/components.py`** — Update `page_title()`:

```python
def page_title(eyebrow: str, title: str, subtitle: str = "", year: int | str = "") -> None:
    """Render the standard SHAI page title block with optional year display."""
    year_html = ""
    if year:
        year_html = f"""
        <div class="shai-header-meta">
            <div class="shai-year-display">{year}</div>
            <div class="shai-year-label">Analysår</div>
        </div>
        """
    html = f"""
    <div class="shai-page-header">
        <div>
            <div class="shai-eyebrow">{eyebrow}</div>
            <div class="shai-page-title">{title}</div>
            {"<div class='shai-page-subtitle'>" + subtitle + "</div>" if subtitle else ""}
        </div>
        {year_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add/update:

```css
/* ---- Page header (full row) ---- */
.shai-page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1px solid #EEF0F3;
    padding-bottom: 20px;
    margin-bottom: 24px;
}
.shai-header-meta {
    text-align: right;
}
.shai-year-display {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 36px;
    font-weight: 300;
    color: #9CA3AF;
    line-height: 1;
}
.shai-year-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #9CA3AF;
    margin-top: 4px;
}
```

Then update every page call to include `year=selections["selected_year"]`.

### Why
The year display on the right provides instant context. The bottom border separates the header from content. This is a core KRI pattern used on every analysis page.

---

## 14. KPI Card — Tooltip Support

### Current State (SHAI)
- `kpi_card()` has no tooltip parameter.
- No hover cursor or `title` attribute.

### KRI Reference
- Optional `tooltip` parameter adds `title` attribute + `kpi-card--tipped` class for `cursor: help`.
- Used on Riksöversikt KPI row with Swedish explanations.

### What to Do

**File: `src/ui/components.py`** — Add `tooltip` param:

```python
def kpi_card(
    label, value, unit="", delta="", delta_direction="flat",
    variant="default", tooltip=None,
) -> str:
    tip_attr = f'title="{tooltip}"' if tooltip else ""
    tip_class = " kpi-card--tipped" if tooltip else ""
    # ... use in the container div:
    # <div class="shai-kpi-card variant-{variant}{tip_class}" {tip_attr}>
```

**File: `src/ui/css.py`** — Add:

```css
.kpi-card--tipped { cursor: help; }
```

### Why
Tooltips provide contextual explanations for technical KPI labels without cluttering the interface.

---

## 15. Card Header — Alignment with KRI

### Current State (SHAI)
- `card()` in components.py is close to KRI but the outer container uses `.shai-card` not `.card`.
- Missing the `border-bottom` on `.shai-card-header` interaction with `st.container(border=True)`.

### KRI Reference
- CSS targets `[data-testid="stVerticalBlockBorderWrapper"]` in main for white card bg, border, radius, padding — aligned with KPI card look.

### What to Do

**File: `src/ui/css.py`** — Add:

```css
/* ---- Streamlit container as card ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #EEF0F3 !important;
    border-radius: 4px;
    padding: 4px;
}
```

### Why
Ensures `st.container(border=True)` looks identical to custom `.shai-card` elements, maintaining visual consistency.

---

## 16. Chart System — ECharts vs Plotly

### Current State (SHAI)
- All charts use **Plotly** (`plotly.graph_objects`).
- Choropleth uses `streamlit-echarts`.

### KRI Reference
- All charts use **Apache ECharts** via `streamlit-echarts`.
- Unified theme via `get_echarts_base_options()`.
- Plotly is not used.

### What to Do

This is the **largest single change**. You have two options:

**Option A (Recommended): Keep Plotly but match the KRI visual style exactly.**
- Already using same color tokens, fonts, and grid colors.
- Add matching tooltip styling, axis formatting, and animation settings.
- This avoids rewriting all chart code.

**Option B (Full parity): Migrate all charts to ECharts.**
- Rewrite all `go.Figure()` calls as ECharts options dicts.
- Use `st_echarts()` for rendering.
- Requires significant refactoring.

**If choosing Option A**, ensure every Plotly chart has:

```python
fig.update_layout(
    font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=12),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    xaxis=dict(
        gridcolor="#E5E7EB",
        zeroline=False,
        title_font=dict(size=12),
    ),
    yaxis=dict(
        gridcolor="#E5E7EB",
        zeroline=False,
        gridwidth=1,
        griddash="dash",  # KRI uses dashed splitLines
    ),
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#EEF0F3",
        font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=12),
    ),
    margin=dict(l=50, r=20, t=30, b=50),
)
```

**If choosing Option B**, create `src/ui/echarts_theme.py`:

```python
def get_tooltip_style():
    return {
        "backgroundColor": "#FFFFFF",
        "borderColor": "#EEF0F3",
        "borderWidth": 1,
        "textStyle": {
            "fontFamily": "Source Sans 3, Source Sans Pro, sans-serif",
            "fontSize": 12,
            "color": "#1A1A2E",
        },
        "axisPointer": {
            "lineStyle": {"color": "#C4A35A", "type": "dashed"},
        },
    }

def get_axis_style(axis_type="category"):
    base = {
        "axisLabel": {"fontFamily": "Source Sans 3, Source Sans Pro, sans-serif", "fontSize": 11},
        "axisLine": {"lineStyle": {"color": "#E5E7EB"}},
    }
    if axis_type == "value":
        base["splitLine"] = {"lineStyle": {"color": "#E5E7EB", "type": "dashed"}}
        base["axisLabel"]["fontFamily"] = "IBM Plex Mono, monospace"
    return base

def get_echarts_base_options():
    return {
        "backgroundColor": "#FFFFFF",
        "grid": {"left": 60, "right": 20, "top": 40, "bottom": 50},
        "animationDuration": 400,
        "tooltip": get_tooltip_style(),
    }
```

### Why
KRI uses ECharts exclusively for a unified chart experience. If you keep Plotly, you must ensure the visual output (fonts, colors, grid style, tooltips) is indistinguishable from ECharts.

---

## 17. Chart Theme — Shared ECharts Base Options

### Current State (SHAI)
- No shared chart theme function. Each chart individually sets fonts, colors, margins.
- Dashed grid lines not used consistently.

### KRI Reference
- `get_echarts_base_options()` returns a dict that every chart merges.
- `get_tooltip_style()` and `get_axis_style()` ensure consistent tooltips and axes.
- Animation duration locked to 400ms.

### What to Do
Create a shared chart configuration function (see section 16 above). Then use it in every chart:

```python
from src.ui.chart_theme import get_chart_base_layout

# For Plotly:
fig.update_layout(**get_chart_base_layout())
```

### Why
Prevents style drift between charts. One change to the theme function updates all charts.

---

## 18. Choropleth — Folium vs ECharts Scatter

### Current State (SHAI)
- Uses ECharts scatter-on-geo (world map background).
- Good — matches KRI's choropleth concept.
- Missing: Folium with GeoJSON polygon fills for actual municipality shapes.

### KRI Reference
- **Folium** + `streamlit_folium` for the primary map UX.
- GeoJSON polygons with `LinearColormap` from `branca`.
- `CartoDB positron` tiles; sticky tooltips; highlight stroke.
- ECharts geo scatter is available as a secondary option.

### What to Do

**Option A (Current approach is acceptable):** The ECharts scatter is fine for SHAI since municipality GeoJSON may not be available. Ensure the visual settings match:
- `zoom: 4.5` (already done).
- `center: [16, 62.5]` (already done).
- Match tooltip styling to the card aesthetic.

**Option B (Full parity with Folium):** Add a Folium map:

```python
import folium
from branca.colormap import LinearColormap
from streamlit_folium import folium_static

def render_folium_choropleth(geojson_path, data, value_col):
    cmap = LinearColormap(
        colors=["#2E7D5B", "#A8C4A4", "#E5E7EB", "#E8BE7C", "#D4A03C", "#B94A48"],
        vmin=-2.5, vmax=2.5,
        caption="SHAI Poäng · Lägre = bättre överkomlighet",
    )
    m = folium.Map(
        location=[62.5, 16],
        zoom_start=5,
        tiles="CartoDB positron",
        scrollWheelZoom=False,
    )
    # Add GeoJSON with style_function and tooltip
    folium_static(m, height=440)
```

Requires: `data/geo/kommuner.geojson` file with municipality boundaries.

### Why
Folium with GeoJSON provides actual municipality shapes, which is more informative than scatter dots. But the scatter approach is acceptable if GeoJSON is unavailable.

---

## 19. Tables — HTML Table Enhancements

### Current State (SHAI)
- `.shai-table` with proper thead/tbody styling.
- Missing: `.kommun-name` class for bold navy names.
- Missing: `.rank-cell` narrow column.
- Missing: `font-variant-numeric: tabular-nums` on `.num` cells.

### KRI Reference
- `.kommun-name` — semibold navy.
- `.rank-cell` — narrow.
- `font-variant-numeric: tabular-nums` on `.kpi-value` and table numeric cells.

### What to Do

**File: `src/ui/css.py`** — Add:

```css
.shai-table td.kommun-name {
    font-weight: 600;
    color: #0B1F3F;
}
.shai-table td.rank-cell {
    width: 40px;
    text-align: center;
}
.shai-table tbody td.num {
    font-variant-numeric: tabular-nums;
}
```

### Why
Tabular numerics align decimal points in columns. Bold navy names make municipality names scannable. These are small but important details.

---

## 20. CSS Custom Properties (`:root` Variables)

### Current State (SHAI)
- No CSS custom properties. All values are hardcoded.

### KRI Reference
- `:root` defines `--kri-pad-x`, `--kri-pad-y`, `--kri-label-upper`, `--kri-label-track`, `--kri-brand-bar-offset`, `--kri-hero-pad-top`.

### What to Do

**File: `src/ui/css.py`** — Add to beginning of `GLOBAL_CSS`:

```css
:root {
    --shai-pad-x: 1.5rem;
    --shai-pad-y: 2rem;
    --shai-label-upper: 11px;
    --shai-label-track: 1.5px;
    --shai-brand-bar-offset: 14px;
    --shai-hero-pad-top: 0.35rem;
}
```

Then replace hardcoded values throughout the CSS with these variables.

### Why
CSS variables enable global spacing/sizing changes from one place. KRI uses them to keep sidebar and main content aligned.

---

## 21. Chrome Hiding (Header, Footer, MainMenu)

Covered in Section 1. See that section for complete implementation.

---

## 22. Responsive Breakpoints

### Current State (SHAI)
- No `@media` queries at all.

### KRI Reference
- `max-width: 900px`: stat strip → 2 cols; steps → column; nav cards → 1 col.
- `max-width: 520px`: stat strip → 1 col; hero padding reduced.

### What to Do

**File: `src/ui/css.py`** — Add at end of `GLOBAL_CSS`:

```css
/* ---- Responsive ---- */
@media (max-width: 900px) {
    .lp-stat-strip { grid-template-columns: repeat(2, 1fr); }
    .lp-steps { flex-direction: column; gap: 12px; }
    .lp-step-connector {
        transform: rotate(90deg);
        padding: 4px 0;
    }
}
@media (max-width: 520px) {
    .lp-stat-strip { grid-template-columns: 1fr; }
    .lp-stat-cell {
        border-right: none;
        border-bottom: 1px solid #EEF0F3;
    }
    .lp-stat-cell:last-child { border-bottom: none; }
    .lp-hero { padding-left: 1rem; padding-right: 1rem; }
}
```

### Why
Without breakpoints, landing page components break on tablets/phones. The stat strip and step cards need to reflow at narrow widths.

---

## 23. Accessibility & Reduced Motion

### Current State (SHAI)
- No `prefers-reduced-motion` media query.
- No `aria-hidden` on decorative SVGs.

### KRI Reference
- `prefers-reduced-motion: reduce` disables transitions on steps, nav cards, and arrow SVGs.
- Decorative SVGs use `aria-hidden="true"`.

### What to Do

**File: `src/ui/css.py`** — Add:

```css
@media (prefers-reduced-motion: reduce) {
    .lp-step,
    .lp-nav-card,
    .lp-step-arrow-svg {
        transition: none !important;
    }
}
```

Ensure all decorative SVGs in components include `aria-hidden="true"`.

### Why
Accessibility compliance. Users with motion sensitivity should not experience animations.

---

## 24. Typography — Font Weight Gaps

### Current State (SHAI)
- Uses Source Sans 3 weights 400, 600, 700.
- Missing weight **300** (used in KRI for year display and hero lead text).

### KRI Reference
- Source Sans Pro weights: 300, 400, 600, 700.

### What to Do

**File: `src/ui/css.py`** — Update the Google Fonts import:

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@300;400;600;700&display=swap');
```

Note the added `300` weight for Source Sans 3.

### Why
Weight 300 is needed for the light-weight year display in page headers and other decorative text.

---

## 25. Streamlit Config — showSidebarNavigation

### Current State (SHAI)
- No `[client]` section in `.streamlit/config.toml`.
- Streamlit's default multipage navigation header is **visible** in the sidebar.

### KRI Reference
```toml
[client]
showSidebarNavigation = false
```

### What to Do

**File: `.streamlit/config.toml`** — Add:

```toml
[client]
showSidebarNavigation = false
```

### Why
Hides Streamlit's auto-generated page links in the sidebar so only your custom `st.page_link` entries appear under the branded block. Without this, users see duplicate navigation.

---

## 26. Session State Architecture

### Current State (SHAI)
- `render_sidebar()` returns a dict with `selected_year` and `risk_filter`.
- No `st.session_state` persistence of selections.
- No `kri_df` equivalent shared state.

### KRI Reference
- Shared session state keys: `kri_df`, `selected_year`, `selected_risks`, `selected_municipality`.
- Sidebar writes to session state; pages read from it.

### What to Do

**File: `src/ui/sidebar.py`** — Write to session state:

```python
st.session_state["selected_year"] = selected_year
st.session_state["selected_risks"] = selected_risks
```

**All page files** — Read from session state with fallback:

```python
selected_year = st.session_state.get("selected_year", 2024)
```

### Why
Session state persists selections across page navigation. Without it, the year resets when switching pages.

---

## 27. Footer Note Component

### Current State (SHAI)
- Each page has inline HTML for the footer. Not a reusable component.
- No `.footer-note` class.

### KRI Reference
- `.footer-note` — top border, flex wrap, small tertiary text; optional `code` styling for version badges.

### What to Do

**File: `src/ui/components.py`** — Add:

```python
def footer_note(source: str = "SCB, Riksbanken, Kolada", version: str = "SHAI v1.3") -> None:
    """Render the standard page footer."""
    html = f"""
    <div class="shai-footer-note">
        <span><strong>KÄLLA:</strong> {source}</span>
        <span><code>{version}</code></span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
```

**File: `src/ui/css.py`** — Add:

```css
/* ---- Footer note ---- */
.shai-footer-note {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
    font-size: 11px;
    color: #9CA3AF;
    padding: 12px 0;
    border-top: 1px solid #EEF0F3;
    margin-top: 32px;
}
.shai-footer-note code {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    background: #F7F8FA;
    border: 1px solid #EEF0F3;
    padding: 2px 6px;
    border-radius: 3px;
}
```

Then replace all inline footer HTML across pages with `footer_note()`.

### Why
DRY principle. One component, consistent look, change once to update everywhere.

---

## 28. Number Formatting — Swedish Conventions

### Current State (SHAI)
- `format_sek()` uses non-breaking space thousands separator and comma decimal.
- `format_pct()` uses comma decimal.
- No `format_swedish_int()` equivalent.

### KRI Reference
- `format_swedish_int()` uses non-breaking space (`\u00A0`) as thousands separator.
- Pages use `_fmt_decimal` with Swedish comma and narrow no-break space (`\u202F`).

### What to Do

**File: `src/ui/components.py`** — Update `format_sek` to use non-breaking space:

```python
def format_sek(value: float, decimals: int = 0) -> str:
    if decimals == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "\u00A0").replace(".", ",")
```

Also add:

```python
def format_swedish_int(value: int) -> str:
    """Format integer with non-breaking space thousands separator."""
    return f"{value:,}".replace(",", "\u00A0")
```

### Why
Non-breaking spaces prevent line breaks within numbers, which is critical for KPI cards and table cells. Standard spaces can cause "1 234" to break across lines.

---

## 29. Sidebar Width

### Current State (SHAI)
- Sidebar uses Streamlit default width (~300px).

### KRI Reference
- Sidebar `min-width` and `width` are **260px**.

### What to Do

**File: `src/ui/css.py`** — Add:

```css
section[data-testid="stSidebar"] {
    min-width: 260px !important;
    width: 260px !important;
}
section[data-testid="stSidebar"] > div {
    width: 260px !important;
}
```

### Why
260px is the KRI standard. Narrower than Streamlit default, giving more room to the main content area.

---

## 30. Per-Page Sidebar Duplication Pattern

### Current State (SHAI)
- `render_sidebar()` is called once from each page — correct pattern.
- But no per-page unique pill keys to avoid collisions.

### KRI Reference
- Sidebar pill keys differ per page: `main_year_pills`, `rv_year_pills`, `rd_year_pills`, etc.

### What to Do

**File: `src/ui/sidebar.py`** — Accept a page prefix:

```python
def render_sidebar(page_key: str = "main") -> dict:
    # ...
    selected_year = st.pills(
        "Välj år",
        options=YEAR_RANGE,
        default=YEAR_RANGE[-1],
        label_visibility="collapsed",
        key=f"{page_key}_year_pills",
    )
```

Then each page passes its prefix:

```python
selections = render_sidebar(page_key="rv")  # riksoversikt
selections = render_sidebar(page_key="lj")  # lan_jamforelse
```

### Why
Unique widget keys prevent `DuplicateWidgetID` errors and ensure each page's sidebar state is independent.

---

## Summary — Priority Order

| Priority | Gap | Effort | Impact |
|----------|-----|--------|--------|
| **P0** | Chrome hiding (§1) | Low | High — removes Streamlit branding |
| **P0** | Sidebar brand + page_link nav (§2) | Medium | High — defines app identity |
| **P0** | showSidebarNavigation=false (§25) | Trivial | High — removes duplicate nav |
| **P0** | Landing hero (§6) | Medium | High — first impression |
| **P1** | Year pills (§3) | Low | Medium — matches KRI input pattern |
| **P1** | Risk legend + pills (§4) | Low | Medium — visual mapping |
| **P1** | Page header with year display (§13) | Low | Medium — context on every page |
| **P1** | Stat strip (§7) | Medium | Medium — landing visual impact |
| **P1** | Responsive breakpoints (§22) | Low | Medium — mobile/tablet support |
| **P1** | CSS variables (§20) | Low | Medium — maintainability |
| **P2** | "What is SHAI?" block (§8) | Low | Low-medium |
| **P2** | Pipeline steps (§10) | Medium | Medium — methodology at a glance |
| **P2** | Navigation cards (§11) | Medium | Medium — visual sitemap |
| **P2** | Index overview + flow SVG (§9) | High | Medium — methodology visual |
| **P2** | Credibility block (§12) | Low | Low |
| **P2** | Footer note component (§27) | Low | Low — DRY cleanup |
| **P2** | KPI tooltips (§14) | Trivial | Low |
| **P2** | Table enhancements (§19) | Low | Low |
| **P3** | Chart system migration (§16, §17) | Very High | Medium — visual consistency |
| **P3** | Folium choropleth (§18) | High | Low — scatter is acceptable |
| **P3** | Session state arch (§26) | Medium | Medium — page persistence |
| **P3** | Number formatting (§28) | Trivial | Low |
| **P3** | Sidebar width (§29) | Trivial | Low |
| **P3** | Per-page pill keys (§30) | Low | Low — prevents edge-case bugs |
| **P3** | Font weight 300 (§24) | Trivial | Low |
| **P3** | Accessibility/motion (§23) | Low | Low |
| **P3** | Container card CSS (§15) | Trivial | Low |

---

## Files to Modify

| File | Sections Affected |
|------|-------------------|
| `src/ui/css.py` | §1, §2, §3, §4, §6–12, §15, §19–24, §27, §29 |
| `src/ui/components.py` | §6–12, §13, §14, §27, §28 |
| `src/ui/sidebar.py` | §2, §3, §4, §26, §30 |
| `app.py` | §1, §6, §7, §8, §9, §10, §11, §12 |
| `pages/01_Riksoversikt.py` | §1, §13, §14, §27 |
| `pages/02_Lan_jamforelse.py` | §1, §13, §27 |
| `pages/03_Kommun_djupanalys.py` | §1, §13, §27 |
| `pages/04_Kontantinsats.py` | §1, §13, §27 |
| `pages/05_Scenario.py` | §1, §13, §27 |
| `pages/06_Metodologi.py` | §1, §13, §27 |
| `.streamlit/config.toml` | §25 |
| `src/ui/echarts_theme.py` (new, only if Option B) | §16, §17 |

---

*Generated by comparing SHAI codebase against KRI `ux-ui-design-system.md` as of 2026-04-15.*
