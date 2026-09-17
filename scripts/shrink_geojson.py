"""Shrink data/geo/kommuner.geojson without changing its shape.

    python scripts/shrink_geojson.py

Coordinates arrived from the source at 9 to 15 decimal places. Five decimals is
~1.1 m; at national zoom one screen pixel is roughly 400 m, so everything past
the fifth decimal is payload nobody can see. Minifying the JSON separators
removes the rest.

Measured: 842 KB -> 428 KB, -49 %, with all 290 features and every property
intact. Verified by tests/test_geojson_payload.py.

Deliberately *not* topology simplification. That needs shapely or mapshaper, and
adding a runtime dependency to shrink a committed build artifact is backwards --
see L1 in docs/OPTIMIZATION_PLAN.md and T2.1 in docs/REVITALIZATION_PLAN.md.

Idempotent: running it twice produces the same bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

DECIMALS = 5
GEOJSON = Path(__file__).resolve().parents[1] / "data" / "geo" / "kommuner.geojson"


def round_coordinates(node: object, decimals: int = DECIMALS) -> object:
    """Round every coordinate in a GeoJSON coordinate tree.

    Args:
        node: A coordinate, a position, or any nesting of them.
        decimals: Decimal places to keep.

    Returns:
        The same structure with every number rounded.
    """
    if isinstance(node, list):
        if node and isinstance(node[0], (int, float)):
            return [round(value, decimals) for value in node]
        return [round_coordinates(child, decimals) for child in node]
    return node


def main() -> None:
    before = GEOJSON.stat().st_size
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))

    for feature in geo["features"]:
        feature["geometry"]["coordinates"] = round_coordinates(
            feature["geometry"]["coordinates"]
        )
        # `geo_point_2d` is a coordinate too -- it anchors the municipality name
        # labels (`src/ui/map_labels._label_latlon`). Rounding the geometry but
        # not this leaves 580 high-precision values in the file, which fails
        # tests/test_geojson_payload.py because that scans the whole document.
        point = feature["properties"].get("geo_point_2d")
        if point is not None:
            feature["properties"]["geo_point_2d"] = round_coordinates(point)

    GEOJSON.write_text(
        json.dumps(geo, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    after = GEOJSON.stat().st_size
    print(
        f"{GEOJSON.name}: {before/1024:.0f} KB -> {after/1024:.0f} KB "
        f"({100*(1-after/before):.1f}% smaller), {len(geo['features'])} features"
    )


if __name__ == "__main__":
    main()
