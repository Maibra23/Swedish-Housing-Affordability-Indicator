"""The map depends on the year, and on nothing else.

Two defects in one. An excluded municipality used to reach `_style` with
`_z = 0.0`, which `colormap` paints `#e6e5e6` — indistinguishable from a real
median's `#e5e7eb`. So filtering to "Hög" showed 82 high-risk municipalities and
208 others claiming to be average. And because `build_colormap` was fed the
*filtered* subset, the legend rescaled whenever a pill moved: Stockholm went from
`#c56f43` to `#b94a48` without its `z_c` changing at all.

Making the map take the whole year fixes both, and collapses the cache input
space from 11 years × 7 risk combinations to 11. See Decision Q1, answered No.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_ranked.parquet"


@pytest.fixture(scope="module")
def year_frame() -> pd.DataFrame:
    ranked = pd.read_parquet(ARTIFACT)
    return ranked[ranked["year"] == ranked["year"].max()]


def test_a_filtered_frame_produces_a_different_map(year_frame: pd.DataFrame) -> None:
    """`_map_html` renders what it is handed — that is correct and worth pinning.

    An earlier draft of this test asserted the opposite: that filtering could not
    change the output. It can, and it should. The function is not where the fix
    lives; the fix is that the *page* stops handing it a filtered frame, which
    `test_the_page_does_not_hand_the_map_a_filtered_frame` asserts structurally.

    Keeping this the right way round matters: if it ever starts passing,
    `_map_html` has begun ignoring its input.
    """
    from src.ui.choropleth import _map_html

    full = _map_html(year_frame)
    high_only = _map_html(year_frame[year_frame["risk_c"] == "hog"])
    assert full != high_only, "_map_html ignored its data argument"


def test_every_municipality_is_drawn(year_frame: pd.DataFrame) -> None:
    """All 290, not just the ones surviving a filter.

    Names are compared in their JSON-escaped form as well as literally: folium
    embeds the GeoJSON with `ensure_ascii=True`, so "Upplands Väsby" appears in
    the document as "Upplands V\u00e4sby". The browser decodes it correctly —
    checking only the literal form would fail on every name with a diacritic,
    which is most of them.
    """
    import json

    from src.ui.choropleth import _map_html

    html = _map_html(year_frame)
    missing = [
        name
        for name in year_frame["region_name"]
        if str(name) not in html and json.dumps(str(name))[1:-1] not in html
    ]
    assert not missing, f"{len(missing)} municipalities are absent: {missing[:5]}"


def test_no_municipality_is_painted_without_data(year_frame: pd.DataFrame) -> None:
    """The colour that caused this task: a real median, not a stand-in for absent."""
    from src.ui.choropleth import _map_html

    html = _map_html(year_frame)
    assert "Saknas" not in html, (
        'a feature carries "Saknas" placeholders, so it was drawn without data'
    )


def test_one_cache_entry_per_year() -> None:
    """The point of Q1: eleven inputs, not seventy-seven."""
    from src.ui.choropleth import _map_html

    ranked = pd.read_parquet(ARTIFACT)
    years = sorted(ranked["year"].unique())
    documents = {_map_html(ranked[ranked["year"] == year]) for year in years}
    assert len(documents) == len(years), (
        "two years rendered identically; the map is not varying with its data"
    )


def test_the_page_does_not_hand_the_map_a_filtered_frame() -> None:
    """Structural, because the behavioural tests above cannot see the call site.

    This is where Q1's answer actually lives. `_map_html` will happily render a
    filtered frame; the decision is that the page must not ask it to.
    """
    page = ROOT / "pages" / "01_Riksoversikt.py"
    tree = ast.parse(page.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "render_choropleth"
        ):
            first = ast.unparse(node.args[0]) if node.args else ""
            assert "df_ranked" not in first, (
                f"the map is passed {first!r}, which the risk pills have filtered"
            )
            return
    raise AssertionError("no render_choropleth call found on page 01")
