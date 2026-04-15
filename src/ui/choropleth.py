"""Choropleth map component using streamlit-echarts.

Scatter-on-geo pattern from DESIGN_SYSTEM.md section 5.
Each municipality is a scatter point colored by SHAI value, sized by absolute deviation.
"""

from __future__ import annotations

import pandas as pd
from streamlit_echarts import st_echarts, JsCode


def render_choropleth(
    data: pd.DataFrame,
    value_col: str = "z_c",
    name_col: str = "region_name",
    lat_col: str = "lat",
    lon_col: str = "lon",
    risk_col: str = "risk_c",
    height: int = 500,
) -> None:
    """Render a scatter-on-geo choropleth of Swedish municipalities.

    Args:
        data: One row per municipality with coordinates and SHAI values.
        value_col: Column with the numeric value to visualize.
        name_col: Column with the municipality name.
        lat_col: Latitude column.
        lon_col: Longitude column.
        risk_col: Risk class column (lag/medel/hog).
        height: Chart height in pixels.
    """
    risk_labels = {"lag": "Låg", "medel": "Medel", "hog": "Hög"}

    # Build data array: [lon, lat, value, name, risk_label]
    scatter_data = []
    for _, row in data.iterrows():
        scatter_data.append([
            round(float(row[lon_col]), 4),
            round(float(row[lat_col]), 4),
            round(float(row[value_col]), 3),
            str(row[name_col]),
            risk_labels.get(str(row.get(risk_col, "")), ""),
        ])

    option = {
        "backgroundColor": "#FFFFFF",
        "title": {
            "text": "Geografisk fördelning",
            "subtext": "SHAI poäng per kommun (Version C)",
            "left": 16,
            "top": 10,
            "textStyle": {
                "fontFamily": "Source Sans 3, Source Sans Pro, sans-serif",
                "fontWeight": "bold",
                "fontSize": 15,
                "color": "#1A1A2E",
            },
            "subtextStyle": {
                "fontFamily": "Source Sans 3, Source Sans Pro, sans-serif",
                "fontSize": 12,
                "color": "#6B7280",
            },
        },
        "tooltip": {
            "trigger": "item",
            "backgroundColor": "#0B1F3F",
            "borderColor": "#0B1F3F",
            "textStyle": {
                "color": "#FFFFFF",
                "fontFamily": "Source Sans 3, Source Sans Pro, sans-serif",
                "fontSize": 12,
            },
            "formatter": JsCode(
                "function(params) {"
                "  var d = params.data;"
                "  var name = d[3];"
                "  var val = d[2].toFixed(2);"
                "  var risk = d[4];"
                "  return '<strong>' + name + '</strong><br/>'"
                "       + 'SHAI poäng: ' + val + '<br/>'"
                "       + 'Riskklass: ' + risk;"
                "}"
            ),
        },
        "geo": {
            "map": "world",
            "roam": False,
            "center": [16, 62.5],
            "zoom": 4.5,
            "silent": True,
            "itemStyle": {
                "areaColor": "#F7F8FA",
                "borderColor": "#D1D5DB",
                "borderWidth": 0.5,
            },
        },
        "visualMap": {
            "min": -4.0,
            "max": 2.0,
            "left": 20,
            "bottom": 20,
            "orient": "horizontal",
            "text": ["Hög risk", "Låg risk"],
            "textStyle": {
                "fontFamily": "Source Sans 3, Source Sans Pro, sans-serif",
                "fontSize": 10,
                "color": "#6B7280",
            },
            "inRange": {
                "color": [
                    "#2E7D5B",
                    "#A8C4A4",
                    "#E5E7EB",
                    "#E8BE7C",
                    "#D4A03C",
                    "#B94A48",
                ],
            },
            "dimension": 2,
        },
        "series": [
            {
                "type": "scatter",
                "coordinateSystem": "geo",
                "symbolSize": JsCode(
                    "function(val) {"
                    "  return 5 + Math.min(Math.abs(val[2]) * 3, 12);"
                    "}"
                ),
                "data": scatter_data,
                "itemStyle": {"borderColor": "rgba(255,255,255,0.6)", "borderWidth": 0.5},
            }
        ],
    }

    st_echarts(option, height=f"{height}px", key="shai_choropleth")
