"""The map's geometry file is the largest asset the app sends. Keep it small.

842 KB of the 1 234 KB rendered map document was this file, carried into the
browser inside folium's HTML. It stored coordinates at 9 to 15 decimal places —
sub-millimetre precision for polygons drawn at national zoom, where one screen
pixel is roughly 400 m.

Truncating to 5 decimals (~1.1 m) and minifying costs nothing visible and removes
49 % of the file. It is a build step, not a request-time one: the output is
committed, because `data/geo/` exists so the server does no work.

See Task B1 in docs/OPTIMIZATION_PLAN.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

GEOJSON = Path(__file__).resolve().parents[1] / "data" / "geo" / "kommuner.geojson"
CEILING_KB = 450
MAX_DECIMALS = 5


@pytest.fixture(scope="module")
def geo() -> dict:
    return json.loads(GEOJSON.read_text(encoding="utf-8"))


def test_file_is_under_the_ceiling() -> None:
    kb = GEOJSON.stat().st_size / 1024
    assert kb < CEILING_KB, (
        f"kommuner.geojson is {kb:.0f} KB, over the {CEILING_KB} KB ceiling. Run "
        "`python scripts/shrink_geojson.py`."
    )


def test_no_coordinate_carries_more_precision_than_needed() -> None:
    """Scans the whole document, properties included.

    `geo_point_2d` is a coordinate too — it anchors the municipality name labels —
    so rounding the geometry and leaving the properties alone would fail here, as
    it should.
    """
    text = GEOJSON.read_text(encoding="utf-8")
    over = set(re.findall(r"-?\d+\.(\d{6,})", text))
    assert not over, (
        f"{len(over)} distinct coordinates carry more than {MAX_DECIMALS} decimals; "
        "precision beyond ~1 m is invisible at national zoom and costs payload"
    )


def test_every_municipality_survived(geo: dict) -> None:
    """Shrinking must not drop a feature — the whole point is 290 polygons."""
    assert len(geo["features"]) == 290


def test_every_feature_keeps_the_properties_the_map_needs(geo: dict) -> None:
    for feature in geo["features"]:
        props = feature["properties"]
        for key in ("id", "kom_namn", "lan_code", "geo_point_2d"):
            assert key in props, f"feature lost {key!r}"


def test_no_geometry_became_degenerate(geo: dict) -> None:
    """Rounding can collapse a ring. A polygon needs at least four positions."""
    thin = []
    for feature in geo["features"]:
        for ring in _rings(feature["geometry"]["coordinates"]):
            if len(ring) < 4:
                thin.append(feature["properties"].get("kom_namn"))
    assert not thin, f"rounding collapsed rings in: {sorted(set(thin))}"


def _rings(node: object) -> list[list]:
    """Every linear ring in a Polygon or MultiPolygon coordinate tree."""
    if not isinstance(node, list) or not node:
        return []
    if isinstance(node[0], (int, float)):
        return []
    if isinstance(node[0], list) and node[0] and isinstance(node[0][0], (int, float)):
        return [node]
    rings: list[list] = []
    for child in node:
        rings.extend(_rings(child))
    return rings


def test_the_rendered_map_document_shrank_with_it() -> None:
    """The file matters because it is embedded in what crosses to the browser.

    folium inlines the GeoJSON into the map HTML, so this is not an asset the
    browser fetches once and caches — it rides inside every distinct render.
    """
    import pandas as pd

    from src.ui.choropleth import _map_html

    ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
    html = _map_html(ranked[ranked["year"] == ranked["year"].max()])
    kb = len(html.encode("utf-8")) / 1024
    assert kb < 900, (
        f"the rendered map is {kb:.0f} KB. It was 1 234 KB before B1 and should be "
        "roughly 800 KB after; if it has grown back, check whether something is "
        "re-adding precision or embedding the geometry twice."
    )
