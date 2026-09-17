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

from src.ui.labels import L
from src.ui.map_labels import (
    _label_latlon,
    _mean_latlon_from_geometry,
    _municipality_label_div,
)
from branca.element import MacroElement
from folium.features import DivIcon
from folium.template import Template
import streamlit.components.v1 as components

from src.ui.css import DIVERGING_SCALE

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GEOJSON_PATH = PROJECT_ROOT / "data" / "geo" / "kommuner.geojson"

# Basemap. Was ``tiles="CartoDB.PositronNoLabels"`` until basemaps.cartocdn.com
# began stamping "API KEY REQUIRED" across anonymous requests — the watermark
# renders on top of the choropleth. KRI hit this first and moved to Esri's
# light-grey canvas; this matches its MAP_TILES constant.
MAP_TILES = {
    "url": (
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
        "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
    ),
    "attribution": "Tiles &copy; Esri: Esri, DeLorme, NAVTEQ",
    "name": "Ljus gråskala",
    "max_zoom": 16,
    # Drawn behind the tiles so an unreachable host degrades to a clean canvas
    # rather than a black void.
    "background": "#F2F3F5",
}

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








def build_colormap(scores: pd.Series) -> cm.LinearColormap:
    """Diverging colour scale anchored on the spread of the scores being drawn.

    The domain used to be a fixed ``vmin=-2.5, vmax=2.5``. SHAI's ``z_c`` is
    strongly left-skewed — across the eleven years it reaches -6.10 but never
    exceeds +1.47 — so that domain was wrong at both ends at once. It clipped
    104 municipality-years off the green end, rendering Åsele (-3.76) and
    Överkalix (-3.08) as the same flat shade, while the top 43 % of the red ramp
    went unused because no municipality ever got there.

    Stops are placed on the data instead: the ends at the actual minimum and
    maximum, the neutral colour at the median, and the green and red steps at
    the 25th and 75th percentiles — the same quartiles that set ``risk_c``, so
    the map and the ranking tables tell one story.

    Orientation follows ``indices/normalize.py``: lower z is more affordable, so
    the low end is green.

    Args:
        scores: The values about to be drawn. NaNs are ignored.

    Returns:
        A colormap whose domain covers every score passed in.
    """
    clean = pd.Series(scores, dtype=float).dropna()
    if clean.empty:
        clean = pd.Series([-1.0, 1.0])

    low = float(clean.min())
    high = float(clean.max())
    q25 = float(clean.quantile(0.25))
    median = float(clean.median())
    q75 = float(clean.quantile(0.75))

    stops = [low, (low + q25) / 2, q25, median, q75, (q75 + high) / 2, high]

    # A degenerate spread — one municipality selected, or every score equal —
    # yields repeated stops, which branca rejects. Fall back to an evenly spaced
    # domain around the value rather than crashing the page.
    if any(b <= a for a, b in zip(stops, stops[1:])):
        centre = median
        extent = max(high - low, abs(centre), 1.0) / 2
        step = 2 * extent / (len(DIVERGING_SCALE) - 1)
        stops = [centre - extent + i * step for i in range(len(DIVERGING_SCALE))]

    return cm.LinearColormap(
        colors=list(DIVERGING_SCALE),
        index=stops,
        vmin=stops[0],
        vmax=stops[-1],
        caption="SHAI Poäng  ·  Lägre = bättre överkomlighet",
    )


# 24 entries x ~1.2 MB = ~29 MB, which is the deliberate ceiling. The full input
# space is 11 years x 7 risk combinations = 77; caching all of it would cost
# ~116 MB, too much to spend on a 1 GB Streamlit Cloud instance for an
# interaction nobody performs exhaustively. Year changes — the common move — fit
# comfortably; unusual risk combinations pay the rebuild once.
@st.cache_data(show_spinner=False, max_entries=24)
def _map_html(
    data: pd.DataFrame,
    value_col: str = "z_c",
    name_col: str = "region_name",
    risk_col: str = "risk_c",
    height: int = 480,
) -> str:
    """Build the map and return it as a standalone HTML document.

    Cached because this is where the time goes: folium renders the map through
    Jinja2 into a ~1.2 MB document, measured at 83 % of the choropleth cost, and
    Streamlit re-executes the whole script on any widget change — so toggling a
    risk pill used to rebuild a megabyte of HTML. Keyed on the dataframe, so a
    year change rebuilds and nothing else does.

    The frame arrives already risk-filtered, so each filter combination is its
    own entry. That is the trade-off behind `max_entries`; see the note above.

    Args:
        data: One row per municipality with region_code and SHAI values.
        value_col: Column holding the numeric z-score to visualise.
        name_col: Column holding the municipality name.
        risk_col: Risk class column (lag/medel/hog).
        height: Map height in pixels.

    Returns:
        The rendered map document, or an empty string when the GeoJSON is
        missing — the caller turns that into a warning.
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
        return ""
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

    # This must be the whole year, not a filtered subset. When it was the subset,
    # moving a risk pill rescaled the legend and the same colour meant different
    # things before and after the click — Stockholm went #c56f43 to #b94a48 with
    # its z_c unchanged. See Q1 in docs/OPTIMIZATION_PLAN.md.
    colormap = build_colormap(sub[value_col].astype(float))

    # Basemap — light polygons only (no OSM placenames: a labelled basemap shows
    # cities worldwide and reads as unrelated to SHAI).
    m = folium.Map(
        location=[63.0, 17.5],
        zoom_start=_MAP_ZOOM_START,
        tiles=MAP_TILES["url"],
        attr=MAP_TILES["attribution"],
        name=MAP_TILES["name"],
        max_zoom=MAP_TILES["max_zoom"],
        prefer_canvas=True,
        zoom_control=True,
        scrollWheelZoom=False,
    )
    m.get_root().header.add_child(
        folium.Element(
            f"<style>.folium-map {{ background: {MAP_TILES['background']}; }}</style>"
        )
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

    return m.get_root().render()


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
    html = _map_html(data, value_col, name_col, risk_col, height)
    if not html:
        st.warning(L("rv.kartfilen_saknas"))
        return
    # `st.components.v1.html` directly, rather than `folium_static`, which is
    # deprecated and scheduled for removal (R8). This is what it did anyway.
    components.html(html, height=height, scrolling=False)
