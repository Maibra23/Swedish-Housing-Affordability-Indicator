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

from src.ui.css import DIVERGING_SCALE

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
