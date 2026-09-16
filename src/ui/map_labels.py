"""Geometry helpers for the municipality name labels on the choropleth.

Split out of `choropleth.py` when the caching work pushed it past the 400-line
limit. These are pure functions over GeoJSON geometry with no Streamlit and no
folium dependency, which makes them the natural seam and independently testable.
"""

from __future__ import annotations

import html


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
