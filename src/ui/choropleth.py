"""Choropleth map component using streamlit-echarts.

Scatter-on-geo pattern matching the KRI design system.
Each municipality is a scatter point colored by SHAI value, sized by absolute deviation.
Enhanced interactivity: zoom, hover effects, tooltips with full data.
"""

from __future__ import annotations

import pandas as pd
from streamlit_echarts import st_echarts, JsCode

from src.ui.css import COLORS


def render_choropleth(
    data: pd.DataFrame,
    value_col: str = "z_c",
    name_col: str = "region_name",
    lat_col: str = "lat",
    lon_col: str = "lon",
    risk_col: str = "risk_c",
    height: int = 500,
    key: str = "shai_choropleth",
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
        key: Unique key for the echarts component.
    """
    risk_labels = {"lag": "Låg", "medel": "Medel", "hog": "Hög"}

    # Build data array: [lon, lat, value, name, risk_label, version_c, rank]
    scatter_data = []
    for _, row in data.iterrows():
        vc = row.get("version_c", 0)
        rank = row.get("rank_c", "—")
        scatter_data.append([
            round(float(row[lon_col]), 4),
            round(float(row[lat_col]), 4),
            round(float(row[value_col]), 3),
            str(row[name_col]),
            risk_labels.get(str(row.get(risk_col, "")), ""),
            round(float(vc), 1) if pd.notna(vc) else 0,
            int(rank) if pd.notna(rank) and rank != "—" else "—",
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
                "color": COLORS["text_primary"],
            },
            "subtextStyle": {
                "fontFamily": "Source Sans 3, Source Sans Pro, sans-serif",
                "fontSize": 12,
                "color": COLORS["text_secondary"],
            },
        },
        "tooltip": {
            "trigger": "item",
            "backgroundColor": COLORS["primary"],
            "borderColor": COLORS["primary"],
            "borderWidth": 1,
            "padding": [12, 16],
            "textStyle": {
                "color": "#FFFFFF",
                "fontFamily": "Source Sans 3, Source Sans Pro, sans-serif",
                "fontSize": 12,
            },
            "formatter": JsCode(
                "function(params) {"
                "  var d = params.data;"
                "  var name = d[3];"
                "  var z = d[2].toFixed(2);"
                "  var risk = d[4];"
                "  var vc = d[5];"
                "  var rank = d[6];"
                "  var riskColor = risk === 'Låg' ? '#6EE7A0' : risk === 'Medel' ? '#FCD34D' : '#FCA5A5';"
                "  return '<div style=\"font-weight:700;font-size:14px;margin-bottom:6px;\">' + name + '</div>'"
                "       + '<div style=\"display:flex;gap:12px;margin-bottom:4px;\">'"
                "       + '<span style=\"color:rgba(255,255,255,0.7);\">Z-poäng:</span> '"
                "       + '<span style=\"font-family:IBM Plex Mono,monospace;\">' + z + '</span></div>'"
                "       + '<div style=\"display:flex;gap:12px;margin-bottom:4px;\">'"
                "       + '<span style=\"color:rgba(255,255,255,0.7);\">SHAI:</span> '"
                "       + '<span style=\"font-family:IBM Plex Mono,monospace;\">' + vc + '</span></div>'"
                "       + '<div style=\"display:flex;gap:12px;margin-bottom:4px;\">'"
                "       + '<span style=\"color:rgba(255,255,255,0.7);\">Rank:</span> '"
                "       + '<span style=\"font-family:IBM Plex Mono,monospace;\">' + rank + '</span></div>'"
                "       + '<div style=\"margin-top:6px;\">'"
                "       + '<span style=\"background:' + riskColor + ';color:#0B1F3F;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;\">' + risk + ' risk</span>'"
                "       + '</div>';"
                "}"
            ),
        },
        "geo": {
            "map": "world",
            "roam": True,
            "center": [16, 62.5],
            "zoom": 4.5,
            "silent": True,
            "itemStyle": {
                "areaColor": "#F7F8FA",
                "borderColor": "#D1D5DB",
                "borderWidth": 0.5,
            },
            "emphasis": {
                "disabled": True,
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
                "color": COLORS["text_secondary"],
            },
            "inRange": {
                "color": [
                    "#2E7D5B",
                    "#5B9E78",
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
                    "  return 6 + Math.min(Math.abs(val[2]) * 4, 14);"
                    "}"
                ),
                "data": scatter_data,
                "itemStyle": {
                    "borderColor": "rgba(255,255,255,0.7)",
                    "borderWidth": 0.5,
                },
                "emphasis": {
                    "itemStyle": {
                        "borderColor": COLORS["text_primary"],
                        "borderWidth": 2,
                        "shadowBlur": 8,
                        "shadowColor": "rgba(0,0,0,0.15)",
                    },
                    "scale": 1.4,
                },
            }
        ],
        "animationDuration": 400,
        "animationEasing": "cubicOut",
    }

    st_echarts(option, height=f"{height}px", key=key)
