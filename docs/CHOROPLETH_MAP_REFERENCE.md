# Choropleth map — complete reference (SHAI project)

Short explanation: a **Folium + GeoJSON** choropleth (filled municipality polygons) colored by Version C z-score, embedded in **Streamlit** via **streamlit-folium**. The sections below use **Why / What / How / When**; the **entire executable code** needed to reproduce the same map is in the “Complete program listings” section (no out-of-doc references). Boundary data is not source code: you still need the GeoJSON file and Parquet data on disk.

---

## Why

- **Spatial view**: Complements KPIs and tables with *where* risks concentrate across 290 Swedish kommuner.
- **Polygons**: Real boundaries (not only centroid dots) show adjacency and regional patterns.
- **Folium + branca**: Leaflet-based map, `LinearColormap` for continuous z-score → fill color.
- **Diverging palette**: Green–gray–red matches the rest of the SHAI / KRI-style design.

## What

- **Languages / libraries**: Python 3.11, Streamlit, pandas, folium, branca, streamlit-folium.
- **Map behavior**: `folium.GeoJson` with `style_function` / `highlight_function`, `GeoJsonTooltip`, optional `DivIcon` labels for kommun names, zoom-gated label layer, CartoDB Positron (no labels) basemap, scroll zoom disabled for the map widget.

## How

- Load GeoJSON (`@st.cache_data`), merge a metric dict keyed by zero-padded `region_code` into each feature’s `properties`, set `_z` for styling, `LinearColormap` with `vmin`/`vmax` ±2.5, add layer + legend, `folium_static`.
- Join: DataFrame `region_code` and GeoJSON `properties.id` both normalized with `zfill(4)`.

## When

- The production UI calls the renderer after building `df_ranked` (year and risk filters applied on national overview). Labels appear on the map when zoom level reaches the configured minimum (default: zoom 6 with start zoom 5).

---

## Complete program listings (copy as-is)

Save files using the paths shown in each heading so imports match, or change imports to match your layout. Set the working directory to the project root when running Streamlit if paths are relative.

### 1) `pyproject.toml` — relevant dependency block

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "shai"
version = "1.3.0"
description = "Swedish Housing Affordability Indicator (SHAI) — Streamlit dashboard"
readme = "README.md"
requires-python = ">=3.11,<3.12"
dependencies = [
    "streamlit",
    "pandas",
    "numpy",
    "requests",
    "prophet",
    "pmdarima",
    "statsmodels",
    "plotly",
    "folium",
    "streamlit-folium",
    "branca",
    "pyarrow",
    "pytest",
]

[tool.setuptools.packages.find]
where = ["src"]
```

**Minimum to run only the map and data prep (subset):** `streamlit`, `pandas`, `numpy`, `folium`, `streamlit-folium`, `branca`, `pyarrow`.

### 2) `src/ui/choropleth.py` — full map module (self-contained; `DIVERGING_SCALE` included here)

```python
"""Choropleth map component using Folium + GeoJSON.

Each municipality polygon is filled by SHAI z-score using a diverging
green-yellow-red scale.  Mirrors the KRI design system approach.
Requires folium, branca, and streamlit-folium.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from branca.element import MacroElement
from folium.features import DivIcon
from folium.template import Template
from streamlit_folium import folium_static

# Diverging 7-stop scale (green → neutral → red). Same as previous src/ui/css.py.
DIVERGING_SCALE = [
    "#2E7D5B", "#5B9E78", "#A8C4A4",
    "#E5E7EB",
    "#E8BE7C", "#D4A03C", "#B94A48",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GEOJSON_PATH = PROJECT_ROOT / "data" / "geo" / "kommuner.geojson"

# Initial map zoom; labels appear only after this many zoom-in steps from here.
_MAP_ZOOM_START = 5
_LABEL_ZOOM_STEPS = 1  # show labels one zoom step earlier for better UX
_LABEL_MIN_ZOOM = _MAP_ZOOM_START + _LABEL_ZOOM_STEPS


class _ZoomGatedKommunLabels(MacroElement):
    """Show the kommun label layer only when map zoom >= label_min_zoom."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function () {
            var map_ = {{ this._parent.get_name() }};
            var labels_ = {{ this.labels_fg.get_name() }};
            var minZ = {{ this.label_min_zoom }};
            function syncKommunLabels() {
                var z = map_.getZoom();
                if (z >= minZ) {
                    if (!map_.hasLayer(labels_)) { labels_.addTo(map_); }
                } else {
                    if (map_.hasLayer(labels_)) { map_.removeLayer(labels_); }
                }
            }
            map_.on("zoomend", syncKommunLabels);
            map_.whenReady(syncKommunLabels);
        })();
        {% endmacro %}
        """
    )

    def __init__(self, labels_fg: folium.FeatureGroup, label_min_zoom: int) -> None:
        super().__init__()
        self._name = "ZoomGatedKommunLabels"
        self.labels_fg = labels_fg
        self.label_min_zoom = int(label_min_zoom)


@st.cache_data(show_spinner=False)
def _load_geojson() -> dict | None:
    if not GEOJSON_PATH.exists():
        return None
    try:
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        st.error(f"Kunde inte läsa kartdata: {exc}")
        return None


def _mean_latlon_from_geometry(geometry: dict) -> tuple[float, float] | None:
    """Mean coordinate of GeoJSON Polygon/MultiPolygon rings (lon,lat → lat,lon)."""
    if not geometry or "coordinates" not in geometry:
        return None
    lats: list[float] = []
    lons: list[float] = []

    def walk(node: object) -> None:
        if isinstance(node, (list, tuple)) and node:
            if isinstance(node[0], (int, float)) and len(node) >= 2:
                lon, lat = float(node[0]), float(node[1])
                lons.append(lon)
                lats.append(lat)
            else:
                for child in node:
                    walk(child)

    walk(geometry["coordinates"])
    if not lats:
        return None
    return sum(lats) / len(lats), sum(lons) / len(lons)


def _label_latlon(feature: dict) -> tuple[float, float] | None:
    props = feature.get("properties") or {}
    gp = props.get("geo_point_2d")
    if isinstance(gp, (list, tuple)) and len(gp) >= 2:
        return float(gp[0]), float(gp[1])
    geom = feature.get("geometry")
    if geom:
        return _mean_latlon_from_geometry(geom)
    return None


def _municipality_label_div(name: str) -> str:
    """Small always-on label; halo keeps text legible on any fill colour."""
    safe = html.escape(name or "", quote=True)
    return (
        '<div style="font-size:7.5px;line-height:1.05;color:#1A1A2E;'
        "text-align:center;font-family:'Source Sans Pro',sans-serif;"
        "font-weight:600;white-space:nowrap;max-width:96px;"
        "overflow:hidden;text-overflow:ellipsis;"
        "text-shadow:-1px -1px 0 #fff,1px -1px 0 #fff,-1px 1px 0 #fff,1px 1px 0 #fff,"
        '0 0 4px #fff;pointer-events:none;">'
        + safe
        + "</div>"
    )


def render_choropleth(
    data: pd.DataFrame,
    value_col: str = "z_c",
    name_col: str = "region_name",
    risk_col: str = "risk_c",
    height: int = 480,
    key: str = "shai_choropleth",
) -> None:
    """Render a full polygon choropleth of Swedish municipalities.

    Args:
        data: One row per municipality with region_code and SHAI values.
        value_col: Column with the numeric z-score to visualize.
        name_col: Column with the municipality name.
        risk_col: Risk class column (lag/medel/hog).
        height: Map height in pixels.
        key: Unique key for the component.
    """
    risk_labels = {"lag": "Låg", "medel": "Medel", "hog": "Hög"}

    # Build per-code lookup with pre-formatted display strings
    sub = data.copy()
    sub["_code"] = sub["region_code"].astype(str).str.zfill(4)

    data_dict: dict[str, dict] = {}
    for _, row in sub.iterrows():
        code = str(row["_code"])
        z_val = float(row.get(value_col, 0))
        vc = float(row.get("version_c", 0))
        rank = row.get("rank_c", "—")
        risk = str(row.get(risk_col, "medel"))
        price = float(row.get("transaction_price_sek", 0))
        income = float(row.get("median_income", 0))
        unemp = float(row.get("unemployment_rate", 0))

        data_dict[code] = {
            "kommun_name": str(row.get(name_col, "") or "").strip(),
            "z_score": z_val,
            "risk_class": risk_labels.get(risk, risk),
            "z_fmt": f"{z_val:+.2f}".replace(".", ","),
            "shai_fmt": f"{vc:.1f}".replace(".", ","),
            "rank_fmt": f"{rank} / {len(sub)}" if rank != "—" else "—",
            "price_fmt": f"{int(price):,}".replace(",", "\u202f") + " SEK",
            "income_fmt": f"{int(income):,}".replace(",", "\u202f") + " SEK",
            "unemp_fmt": f"{unemp:.1f}".replace(".", ",") + " %",
        }

    # Load and enrich GeoJSON
    _raw = _load_geojson()
    if _raw is None:
        st.warning("Kartfilen saknas (data/geo/kommuner.geojson). Kartan kan inte visas.")
        return
    geojson = json.loads(json.dumps(_raw))

    for feat in geojson["features"]:
        code = feat["properties"].get("id", "").zfill(4)
        d = data_dict.get(code, {})
        feat["properties"]["Kommun"] = (
            d.get("kommun_name")
            or feat["properties"].get("kom_namn")
            or code
        )
        feat["properties"]["Riskklass"] = d.get("risk_class", "Saknas")
        feat["properties"]["SHAI Poäng"] = d.get("shai_fmt", "Saknas")
        feat["properties"]["Z-poäng"] = d.get("z_fmt", "Saknas")
        feat["properties"]["Rang"] = d.get("rank_fmt", "Saknas")
        feat["properties"]["Medianpris"] = d.get("price_fmt", "Saknas")
        feat["properties"]["Medianinkomst"] = d.get("income_fmt", "Saknas")
        feat["properties"]["Arbetslöshet"] = d.get("unemp_fmt", "Saknas")
        feat["properties"]["_z"] = d.get("z_score", 0.0)

    # Color scale — diverging green→neutral→red, matching KRI design
    colormap = cm.LinearColormap(
        colors=list(DIVERGING_SCALE),
        vmin=-2.5,
        vmax=2.5,
        caption="SHAI Poäng  ·  Lägre = bättre överkomlighet",
    )

    # Basemap — light polygons only (no OSM placenames: Positron "with labels"
    # shows cities worldwide and reads as unrelated to SHAI).
    m = folium.Map(
        location=[63.0, 17.5],
        zoom_start=_MAP_ZOOM_START,
        tiles="CartoDB.PositronNoLabels",
        prefer_canvas=True,
        zoom_control=True,
        scrollWheelZoom=False,
    )

    def _style(feature: dict) -> dict:
        z_val = feature["properties"].get("_z", 0.0)
        return {
            "fillColor": colormap(z_val),
            "color": "#CCCCCC",
            "weight": 0.5,
            "fillOpacity": 0.82,
        }

    def _highlight(feature: dict) -> dict:
        return {
            "color": "#1A1A2E",
            "weight": 2.0,
            "fillOpacity": 0.95,
        }

    tooltip_css = (
        "font-family: 'Source Sans Pro', sans-serif;"
        "font-size: 13px;"
        "line-height: 1.5;"
        "background: #ffffff;"
        "border: 1px solid #E5E7EB;"
        "border-radius: 6px;"
        "padding: 12px 14px;"
        "box-shadow: 0 4px 16px rgba(0,0,0,0.10);"
        "color: #1A1A2E;"
    )

    folium.GeoJson(
        geojson,
        style_function=_style,
        highlight_function=_highlight,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "Kommun", "Riskklass", "SHAI Poäng", "Z-poäng", "Rang",
                "Medianpris", "Medianinkomst", "Arbetslöshet",
            ],
            aliases=[
                "<b>Kommun</b>", "<b>Riskklass</b>", "SHAI Poäng", "Z-poäng", "Rang",
                "Medianpris", "Medianinkomst", "Arbetslöshet",
            ],
            sticky=True,
            style=tooltip_css,
        ),
    ).add_to(m)

    # Kommun names (GeoJSON `geo_point_2d`); layer is off-map until zoom >= default+2.
    labels = folium.FeatureGroup(name="Kommunnamn", show=False, control=False)
    for feat in geojson["features"]:
        name = (feat.get("properties") or {}).get("Kommun") or ""
        if not str(name).strip():
            continue
        pos = _label_latlon(feat)
        if pos is None:
            continue
        lat, lon = pos
        folium.Marker(
            location=[lat, lon],
            icon=DivIcon(
                html=_municipality_label_div(str(name)),
                icon_size=(100, 14),
                icon_anchor=(50, 7),
                class_name="shai-muni-label",
            ),
            interactive=False,
        ).add_to(labels)
    labels.add_to(m)
    _ZoomGatedKommunLabels(labels, _LABEL_MIN_ZOOM).add_to(m)

    colormap.add_to(m)

    folium_static(m, width=None, height=height)
```

### 3) `stand_alone_choropleth_page.py` — project root, minimal app (map + same `df_ranked` logic as production page)

Use this to run a map-only demo without the rest of the dashboard UI:

```python
"""
Minimal Streamlit entry: only data load, df_ranked build (same rules as
pages/01_Riksoversikt.py), and render_choropleth + caption + expander.

Run from project root:  streamlit run stand_alone_choropleth_page.py
Requires: data/processed/affordability_ranked.parquet,
          data/processed/affordability_municipal.parquet,
          data/geo/kommuner.geojson
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.ui.choropleth import render_choropleth

st.set_page_config(
    page_title="SHAI · Kartdemo",
    page_icon=None,
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None},
)

try:
    with st.spinner("Laddar data..."):
        ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

years = sorted(municipal["year"].dropna().unique().tolist(), reverse=True)
if not years:
    st.error("Inga år i data.")
    st.stop()

default_year = int(ranked["year"].iloc[0]) if "year" in ranked.columns else int(years[0])
if default_year not in years:
    default_year = int(years[0])

col_a, col_b = st.columns(2)
with col_a:
    selected_year = st.selectbox("År", options=years, index=years.index(default_year) if default_year in years else 0)
with col_b:
    risk_opts = ("Låg", "Medel", "Hög")
    selected_risks = st.multiselect("Riskklass (tom = alla)", options=risk_opts, default=risk_opts)

# Filter to selected year from municipal panel
mun_year = municipal[municipal["year"] == selected_year].copy()
mun_prev = municipal[municipal["year"] == selected_year - 1].copy()

# Use ranked data for baseline year, else recompute z_c within year
if "year" in ranked.columns and selected_year == int(ranked["year"].iloc[0]):
    df_ranked = ranked.copy()
else:
    df_ranked = mun_year.copy()
    if "version_c" in df_ranked.columns and len(df_ranked) > 0:
        mean_c = df_ranked["version_c"].mean()
        std_c = df_ranked["version_c"].std()
        if std_c and std_c > 0:
            df_ranked["z_c"] = (df_ranked["version_c"] - mean_c) / std_c
        else:
            df_ranked["z_c"] = 0.0
        df_ranked["rank_c"] = df_ranked["z_c"].rank(method="min").astype(int)
        df_ranked["risk_c"] = pd.cut(
            df_ranked["z_c"],
            bins=[-np.inf, -0.67, 0.67, np.inf],
            labels=["lag", "medel", "hog"],
        )
    else:
        st.error("Saknar version_c för z-beräkning.")
        st.stop()

# Risk filter
risk_label_map = {"Hög": "hog", "Medel": "medel", "Låg": "lag"}
if "risk_c" in df_ranked.columns and len(selected_risks) < 3 and len(selected_risks) > 0:
    allowed = [risk_label_map[r] for r in selected_risks if r in risk_label_map]
    df_ranked = df_ranked[df_ranked["risk_c"].isin(allowed)]

st.title("Kartdemo — geografisk fördelning")

if len(mun_year) == 0:
    st.warning("Inga data tillgängliga för den valda perioden.")
    st.stop()

with st.container(border=True):
    st.subheader("Geografisk fördelning")
    st.caption(f"Version C · {selected_year} · KOROPLETKARTA")
    if len(df_ranked) > 0:
        render_choropleth(df_ranked, key="stand_alone_choropleth")
        st.caption(
            "Färgskala: Grön = låg risk (z ≤ −0,67) · Gul = medel risk · Röd = hög risk (z > 0,67)"
        )
    else:
        st.info("Ingen data tillgänglig för kartvisning.")
    with st.expander("Om kartan"):
        st.markdown(
            "Varje kommun visas som ett ifyllt polygon. Färgen baseras på "
            "z-poängen (Version C). Grön = låg risk, röd = hög risk. "
            "Håll musen över en kommun för att se detaljer. "
            "Små kommunnamn visas när du zoomat in. "
        )
```

### 4) Production-style block — data prep, `card_header` (full helper), map + caption + expander

Copy below into a page after you have `ranked`, `municipal`, and `selections` (e.g. from your sidebar), or adapt `selections` to your own state. `inject_css()` is not required for the map to work; the header uses the same HTML structure as the rest of SHAI so it matches if global CSS is loaded.

```python
import numpy as np
import pandas as pd
import streamlit as st

from src.ui.choropleth import render_choropleth


def card_header(title: str, subtitle: str = "", tag: str = "") -> str:
    """Return card header HTML (same as src/ui/components.py in this project)."""
    tag_html = f'<span class="shai-card-tag">{tag}</span>' if tag else ""
    return f"""
    <div class="shai-card-header">
        <div>
            <div class="shai-card-title">{title}</div>
            {"<div class='shai-card-subtitle'>" + subtitle + "</div>" if subtitle else ""}
        </div>
        {tag_html}
    </div>
    """


# After: ranked, municipal = pd.read_parquet(...); selections = { "selected_year": ..., "selected_risks": ... }
selected_year = selections["selected_year"]
selected_risks = selections["selected_risks"]
mun_year = municipal[municipal["year"] == selected_year].copy()
mun_prev = municipal[municipal["year"] == selected_year - 1].copy()

if selected_year == ranked["year"].iloc[0]:
    df_ranked = ranked.copy()
else:
    df_ranked = mun_year.copy()
    if "version_c" in df_ranked.columns and len(df_ranked) > 0:
        mean_c = df_ranked["version_c"].mean()
        std_c = df_ranked["version_c"].std()
        if std_c > 0:
            df_ranked["z_c"] = (df_ranked["version_c"] - mean_c) / std_c
        else:
            df_ranked["z_c"] = 0.0
        df_ranked["rank_c"] = df_ranked["z_c"].rank(method="min").astype(int)
        df_ranked["risk_c"] = pd.cut(
            df_ranked["z_c"],
            bins=[-np.inf, -0.67, 0.67, np.inf],
            labels=["lag", "medel", "hog"],
        )

risk_label_map = {"Hög": "hog", "Medel": "medel", "Låg": "lag"}
if "risk_c" in df_ranked.columns and len(selected_risks) < 3:
    allowed = [risk_label_map[r] for r in selected_risks if r in risk_label_map]
    df_ranked = df_ranked[df_ranked["risk_c"].isin(allowed)]

col_map, _col_hist = st.columns([3, 2])
with col_map:
    with st.container(border=True):
        st.markdown(
            card_header("Geografisk fördelning", f"Version C · {selected_year}", "KOROPLETKARTA"),
            unsafe_allow_html=True,
        )
        if len(df_ranked) > 0:
            render_choropleth(df_ranked, key="rv_choropleth")
            st.caption("Färgskala: Grön = låg risk (z ≤ −0,67) · Gul = medel risk · Röd = hög risk (z > 0,67)")
        else:
            st.info("Ingen data tillgänglig för kartvisning.")
        with st.expander("Om kartan"):
            st.markdown(
                "Varje kommun visas som ett ifyllt polygon. Färgen baseras på "
                "z-poängen (Version C). Grön = låg risk, röd = hög risk. "
                "Håll musen över en kommun för att se detaljer. "
                "Små kommunnamn visas först när du zoomat in två steg från "
                "startläget (zoomkontrollen +). De är förankrade i kartfilens "
                "centrum. Bakgrundskartan visar inga världsstäder — övrig text "
                "kommer från SHAI-data.",
            )
```

If you already define `card_header` elsewhere, remove the duplicate `def card_header` and use your existing function. The full Riksöversikt page in this project also includes KPI row, histogram, and tables in addition to this block.

---

## Data and assets (not code)

- **GeoJSON** path (default): `data/geo/kommuner.geojson` — one feature per kommun, `properties.id` joinable to `region_code` (4-digit string), `kom_namn`, optional `geo_point_2d` as `[lat, lon]` for labels.
- **Parquet** inputs: `data/processed/affordability_ranked.parquet`, `data/processed/affordability_municipal.parquet`. Columns used by the choropleth are built from `render_choropleth` (see docstring in listing §2) — at minimum `region_code`, and for full tooltips `z_c`, `version_c`, `rank_c`, `risk_c`, `region_name`, `transaction_price_sek`, `median_income`, `unemployment_rate`.

---

## Run commands

```text
# From project root (after saving section 3 in this file to stand_alone_choropleth_page.py)
streamlit run stand_alone_choropleth_page.py
```

```text
# Your main Streamlit entry, if different
streamlit run <your_entry_script>.py
```

---

## Troubleshooting

- Missing file warning: ensure `data/geo/kommuner.geojson` is present and `GEOJSON_PATH` resolves to it from `src/ui/choropleth.py` (check `PROJECT_ROOT`).
- All gray / same color: `z_c` missing or join mismatch — align `region_code` with `properties.id`.
- Stale documentation: some older notes describe non-Folium maps; use the listings in this file as the current implementation.

---
