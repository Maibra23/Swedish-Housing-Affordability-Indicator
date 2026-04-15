"""Choropleth map component using Folium + GeoJSON.

Each municipality polygon is filled by SHAI z-score using a diverging
green-yellow-red scale.  Mirrors the KRI design system approach.
Requires folium, branca, and streamlit-folium.
"""

from __future__ import annotations

import json
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

from src.ui.css import COLORS, DIVERGING_SCALE

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GEOJSON_PATH = PROJECT_ROOT / "data" / "geo" / "kommuner.geojson"


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
        feat["properties"]["Kommun"] = d.get("kommun_name", feat["properties"].get("kom_namn", code))
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

    # Basemap — CartoDB positron, centered on Sweden
    m = folium.Map(
        location=[63.0, 17.5],
        zoom_start=5,
        tiles="CartoDB positron",
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

    colormap.add_to(m)

    folium_static(m, width=None, height=height)
