"""The national map must use a reachable basemap and a scale the data fills.

Two defects KRI already fixed and SHAI had not (Finding D):

* `tiles="CartoDB.PositronNoLabels"` — `basemaps.cartocdn.com` now stamps
  "API KEY REQUIRED" across anonymous requests.
* `vmin=-2.5, vmax=2.5` — a fixed domain, chosen before anyone looked at the
  spread. SHAI's `z_c` is strongly left-skewed: across the eleven years it runs
  as low as -6.10 but never above +1.47. The fixed domain therefore did both
  possible wrongs at once. It **clipped** 104 municipality-years off the green
  end, so Åsele (-3.76) and Överkalix (-3.08) rendered as the same flat shade,
  and it **wasted** the top 43 % of the red ramp, which no municipality ever
  reached.

The colour scale must therefore come from the data being drawn.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from sourcetools import executable_source

from src.ui import choropleth
from src.ui.css import DIVERGING_SCALE

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "affordability_ranked.parquet")


@pytest.fixture(scope="module")
def scores_2024(ranked: pd.DataFrame) -> pd.Series:
    return ranked.loc[ranked["year"] == 2024, "z_c"].astype(float)


# ── T1.6 — the basemap ───────────────────────────────────────────────


def test_tiles_are_not_served_by_carto():
    assert "cartocdn" not in choropleth.MAP_TILES["url"].lower()
    assert "carto" not in choropleth.MAP_TILES["url"].lower()


def test_no_module_level_reference_to_carto():
    """Prose about the old tile host is fine; a live reference to it is not."""
    code = executable_source(Path(choropleth.__file__).read_text(encoding="utf-8"))
    assert "CartoDB" not in code, "a CartoDB tile shorthand is still wired up"
    assert "cartocdn" not in code.lower()


def test_tile_url_is_a_template():
    url = choropleth.MAP_TILES["url"]
    for placeholder in ("{z}", "{y}", "{x}"):
        assert placeholder in url, f"tile URL is missing {placeholder}"


def test_attribution_is_present_and_credits_the_provider():
    attribution = choropleth.MAP_TILES["attribution"]
    assert attribution.strip(), "tile providers require attribution"
    assert "Esri" in attribution


def test_map_declares_a_background_fallback():
    """If the tile host is unreachable the map degrades to a canvas, not a void."""
    assert choropleth.MAP_TILES["background"].startswith("#")


# ── T1.7 — the colour domain ─────────────────────────────────────────


def test_domain_spans_the_actual_spread(scores_2024: pd.Series):
    colormap = choropleth.build_colormap(scores_2024)
    assert colormap.vmin == pytest.approx(scores_2024.min())
    assert colormap.vmax == pytest.approx(scores_2024.max())


def test_no_municipality_is_clipped(ranked: pd.DataFrame):
    """Every year: no value falls outside its own colour domain."""
    clipped = {}
    for year, group in ranked.groupby("year"):
        scores = group["z_c"].astype(float)
        colormap = choropleth.build_colormap(scores)
        outside = ((scores < colormap.vmin) | (scores > colormap.vmax)).sum()
        if outside:
            clipped[int(year)] = int(outside)
    assert not clipped, f"municipalities clipped off the scale: {clipped}"


def test_domain_is_not_a_constant(ranked: pd.DataFrame):
    """Different years must produce different domains, or it is still hardcoded."""
    domains = {
        int(year): (
            choropleth.build_colormap(group["z_c"].astype(float)).vmin,
            choropleth.build_colormap(group["z_c"].astype(float)).vmax,
        )
        for year, group in ranked.groupby("year")
    }
    assert len(set(domains.values())) > 1, f"every year shares one domain: {domains}"


@pytest.mark.parametrize("forbidden", [-2.5, 2.5])
def test_the_old_fixed_bounds_are_gone(scores_2024: pd.Series, forbidden: float):
    colormap = choropleth.build_colormap(scores_2024)
    assert colormap.vmin != forbidden and colormap.vmax != forbidden


def test_neutral_colour_sits_at_the_median(scores_2024: pd.Series):
    colormap = choropleth.build_colormap(scores_2024)
    neutral_index = len(DIVERGING_SCALE) // 2
    assert colormap.index[neutral_index] == pytest.approx(scores_2024.median())


def test_breakpoints_sit_at_the_quartiles(scores_2024: pd.Series):
    colormap = choropleth.build_colormap(scores_2024)
    assert colormap.index[2] == pytest.approx(scores_2024.quantile(0.25))
    assert colormap.index[4] == pytest.approx(scores_2024.quantile(0.75))


def test_stops_are_strictly_increasing(ranked: pd.DataFrame):
    """branca rejects a non-monotonic index; a skewed year must not produce one."""
    for year, group in ranked.groupby("year"):
        stops = choropleth.build_colormap(group["z_c"].astype(float)).index
        assert all(b > a for a, b in zip(stops, stops[1:])), f"{year}: {stops}"


def test_one_stop_per_colour(scores_2024: pd.Series):
    colormap = choropleth.build_colormap(scores_2024)
    assert len(colormap.index) == len(DIVERGING_SCALE)


def test_lower_scores_are_greener(scores_2024: pd.Series):
    """Orientation: lower z = more affordable = the green end."""
    colormap = choropleth.build_colormap(scores_2024)
    assert colormap(scores_2024.min()) == colormap(colormap.vmin)
    assert colormap(float(scores_2024.min())) != colormap(float(scores_2024.max()))


def test_previously_clipped_municipalities_are_now_distinguishable(ranked: pd.DataFrame):
    """Åsele and Överkalix both sat past -2.5 and rendered identically."""
    year = ranked[ranked["year"] == 2024]
    colormap = choropleth.build_colormap(year["z_c"].astype(float))
    def colour_of(name: str) -> str:
        return colormap(float(year.loc[year["region_name"] == name, "z_c"].iloc[0]))
    assert colour_of("Åsele") != colour_of("Överkalix")


# ── Degenerate input ─────────────────────────────────────────────────


def test_identical_scores_do_not_crash():
    colormap = choropleth.build_colormap(pd.Series([0.4] * 10))
    assert all(b > a for a, b in zip(colormap.index, colormap.index[1:]))


def test_single_value_does_not_crash():
    colormap = choropleth.build_colormap(pd.Series([1.25]))
    assert all(b > a for a, b in zip(colormap.index, colormap.index[1:]))


def test_empty_series_does_not_crash():
    colormap = choropleth.build_colormap(pd.Series([], dtype=float))
    assert all(b > a for a, b in zip(colormap.index, colormap.index[1:]))


def test_nan_values_are_ignored():
    colormap = choropleth.build_colormap(pd.Series([-1.0, float("nan"), 1.0]))
    assert colormap.vmin == pytest.approx(-1.0)
    assert colormap.vmax == pytest.approx(1.0)


# ── T4.5 — missing map data degrades gracefully ──────────────────────


def test_missing_geojson_warns_instead_of_crashing(ranked, monkeypatch):
    """An absent GeoJSON must not take the page down with it."""
    monkeypatch.setattr(choropleth, "_load_geojson", lambda: None)
    warnings: list[str] = []
    monkeypatch.setattr(choropleth.st, "warning", lambda msg, *a, **k: warnings.append(msg))

    choropleth.render_choropleth(ranked[ranked["year"] == 2024])

    assert warnings, "a missing GeoJSON produced no warning"
    assert "kommuner.geojson" in warnings[0]
