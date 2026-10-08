"""Chart text must fit inside its chart, at every width the site is read at.

On a phone the reachability chart on Sida 04 showed its longest bar name as
"sta pris inkomsten bär". Two causes, one local and one shared by every chart:

1. **The bar names sat on the y-axis.** Plotly's `automargin` grows the left
   margin to fit them, but only while enough plot is left, so on a narrow screen
   the label was cut from the left. The names now sit above their bars, which use
   the plot's full width (`bar_names_above`).
2. **The chart font was unquoted.** CSS treats an unquoted family name ending in
   a number, `Source Sans 3`, as invalid. Plotly measured text in one font and
   drew it in another, wider one, so legend entries, annotations and tick labels
   overran the room reserved for them on every page. The fonts are now quoted
   constants in `chart_theme.py`.

Three kinds of check: the source cannot carry an unquoted multi-word font name
again, the reachability chart keeps its names off the axis, and every figure a
builder returns is drawn in a real browser at phone, tablet and desktop widths
with no text past its edge. The browser check is skipped where Playwright's
Chromium is not installed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from src.kontantinsats.charts import affordability_gap_chart, comparison_barchart
from src.lan.charts import county_colours, county_trend_chart
from src.scenario.charts import rate_inflation_surface
from src.ui.chart_theme import CHART_FONT, MONO_FONT, get_chart_layout
from src.ui.labels import L

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

#: Every file that writes a font family into a chart or an inline SVG.
FONT_SOURCES = (
    "src/ui/chart_theme.py",
    "src/ui/landing.py",
    "src/kontantinsats/charts.py",
    "src/scenario/charts.py",
    "src/lan/charts.py",
    "pages/01_Riksoversikt.py",
    "pages/02_Lan_jamforelse.py",
    "pages/03_Kommun_djupanalys.py",
    "pages/04_Kontantinsats.py",
    "pages/05_Scenario.py",
)

#: A font-family value written as a string literal: Plotly's `family=` keyword,
#: a `"family":` dict key, or an SVG `font-family=` attribute.
FAMILY_LITERAL = re.compile(
    r"""(?:family\s*=\s*|"family"\s*:\s*|font-family=)(["'])(?P<value>[^"']*?)\1"""
)

#: Desktop, tablet, large phone, phone. Widest first, so the narrow cases are
#: reached by resizing, the way a rotated phone or a narrowed window gets there.
WIDTHS = (1280, 768, 390, 320)


# ── 1 · Fonts are quoted ──────────────────────────────────────────────


def _unquoted_multiword(value: str) -> list[str]:
    """Family names in a CSS font stack that contain a space and are not quoted."""
    names = [part.strip() for part in value.split(",")]
    return [n for n in names if " " in n and not (n[0] in "'\"" and n[-1] == n[0])]


def test_the_shared_font_stacks_are_quoted() -> None:
    assert not _unquoted_multiword(CHART_FONT)
    assert not _unquoted_multiword(MONO_FONT)
    assert get_chart_layout()["font"]["family"] == CHART_FONT


@pytest.mark.parametrize("source", FONT_SOURCES)
def test_no_unquoted_multiword_font_name(source: str) -> None:
    text = (ROOT / source).read_text(encoding="utf-8")
    offenders = [
        m.group("value")
        for m in FAMILY_LITERAL.finditer(text)
        if _unquoted_multiword(m.group("value"))
    ]
    assert not offenders, (
        f"{source} writes {offenders}: a family name with a space must be quoted, "
        "or CSS drops the declaration and Plotly measures in a different font than "
        "it draws. Use CHART_FONT or MONO_FONT from src/ui/chart_theme.py."
    )


def test_the_guard_sees_an_unquoted_name() -> None:
    sample = 'textfont=dict(family="IBM Plex Mono, monospace")'
    assert [m.group("value") for m in FAMILY_LITERAL.finditer(sample)] == ["IBM Plex Mono, monospace"]
    assert _unquoted_multiword("IBM Plex Mono, monospace") == ["IBM Plex Mono"]


# ── 2 · The reachability chart keeps its names off the axis ───────────


def test_bar_names_sit_above_the_bars_not_on_the_axis() -> None:
    fig = affordability_gap_chart(
        price=8_597_000.0, income=413_600.0, lending_ceiling=5.5, min_down_pct=0.10
    )
    assert fig.layout.yaxis.showticklabels is False
    texts = [a.text for a in fig.layout.annotations]
    for name in (L("ki.gap_faktiskt_pris"), L("ki.gap_max_pris")):
        assert name in texts, f"{name!r} is no longer drawn above its bar"
    for ann in fig.layout.annotations:
        assert ann.xanchor == "left" and ann.align == "left", (
            f"{ann.text!r} is not left-aligned; centred or right-aligned text "
            "spills past the edge when the browser draws it wider than Plotly measured"
        )


# ── 3 · Drawn in a browser, at every width ────────────────────────────


def _builders() -> dict:
    county = pd.read_parquet(PROCESSED / "panel_county.parquet")
    complete = county.dropna(
        subset=["median_income", "transaction_price_sek", "policy_rate", "cpi_yoy_pct"]
    )
    row = complete[complete["year"] == complete["year"].max()].iloc[0]
    baseline = {k: float(row[c]) for k, c in (
        ("income", "median_income"), ("transaction_price_sek", "transaction_price_sek"),
        ("policy_rate", "policy_rate"), ("cpi_yoy_pct", "cpi_yoy_pct"),
    )}
    versions = pd.read_parquet(PROCESSED / "affordability_county.parquet")
    codes = sorted(versions["lan_code"].unique())
    return {
        "gap, out of reach": affordability_gap_chart(
            price=8_597_000.0, income=413_600.0, lending_ceiling=5.5, min_down_pct=0.10
        ),
        "gap, within reach": affordability_gap_chart(
            price=1_500_000.0, income=413_600.0, lending_ceiling=5.5, min_down_pct=0.10
        ),
        "regime comparison": comparison_barchart(
            y_values=[44_516.0, 41_000.0, 47_000.0, 50_717.0, 47_252.0],
            yaxis_title=L("ki.gap_axel_pris"), value_fmt="sek",
            best_key="bolanetak", worst_key="amort_2",
        ),
        "rate and inflation surface": rate_inflation_surface(
            county_kod="01", baseline_panel=baseline, rate_shock=2.0, cpi_shock=0.0
        ),
        "county trends, every county selected": county_trend_chart(
            county_versions=versions, value_column="version_c", selected=codes,
            colours=county_colours(codes),
        ),
    }


#: Report text whose drawn glyphs fall outside the chart. Measured on the visible
#: characters, so a label's trailing padding does not count as overflow.
_OVERFLOW_JS = r"""
() => {
  const plot = document.querySelector('div.js-plotly-plot');
  const box = plot.getBoundingClientRect();
  const out = [];
  plot.querySelectorAll('svg text').forEach(t => {
    const raw = t.textContent || '';
    if (!raw.trim()) return;
    const first = raw.search(/\S/);
    const last = raw.length - 1 - raw.split('').reverse().join('').search(/\S/);
    let l, r, top, bottom;
    try {
      const m = t.getScreenCTM(), a = t.getExtentOfChar(first), b = t.getExtentOfChar(last);
      const p1 = new DOMPoint(a.x, a.y).matrixTransform(m);
      const p2 = new DOMPoint(b.x + b.width, b.y + b.height).matrixTransform(m);
      l = Math.min(p1.x, p2.x); r = Math.max(p1.x, p2.x);
      top = Math.min(p1.y, p2.y); bottom = Math.max(p1.y, p2.y);
    } catch (e) { return; }
    if (l < box.left - 1 || r > box.right + 1 || top < box.top - 1 || bottom > box.bottom + 1)
      out.push(raw.trim().slice(0, 50));
  });
  return out;
}
"""


@pytest.fixture(scope="module")
def browser():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            chromium = p.chromium.launch()
        except Exception as exc:  # browser binary not installed
            pytest.skip(f"Playwright Chromium is not available: {exc}")
        yield chromium
        chromium.close()


def _cut_by_width(fig, browser, tmp_path: Path) -> dict[int, list[str]]:
    """Draw `fig` responsively and return the text cut at each width."""
    page_file = tmp_path / "chart.html"
    page_file.write_text(
        fig.to_html(include_plotlyjs=True, full_html=True,
                    config={"responsive": True}, default_width="100%"),
        encoding="utf-8",
    )
    height = int(fig.layout.height or 450) + 40
    page = browser.new_page(viewport={"width": WIDTHS[0], "height": height})
    page.goto(page_file.as_uri())
    page.wait_for_selector("div.js-plotly-plot .main-svg")
    cut = {}
    # One load, then resized: the figure is responsive, so Plotly re-lays it out
    # on each window resize exactly as it does when a phone rotates.
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": height})
        page.wait_for_timeout(400)
        found = page.evaluate(_OVERFLOW_JS)
        if found:
            cut[width] = found
    page.close()
    return cut


@pytest.mark.parametrize("name", list(_builders()))
def test_no_chart_text_is_cut_at_any_width(name: str, browser, tmp_path: Path) -> None:
    cut = _cut_by_width(_builders()[name], browser, tmp_path)
    assert not cut, f"{name}: text cut at the chart edge, by width: {cut}"


def test_the_guard_sees_a_label_cut_on_a_phone(browser, tmp_path: Path) -> None:
    """The defect this file exists for, rebuilt: a long name on the y-axis with no
    room to grow. It fits on a desktop and must be caught on a phone."""
    import plotly.graph_objects as go

    fig = go.Figure(go.Bar(x=[1, 2], y=["Kort", "Högsta pris inkomsten bär"], orientation="h"))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=30))
    fig.update_yaxes(automargin=False)
    cut = _cut_by_width(fig, browser, tmp_path)
    assert 320 in cut and "Högsta pris inkomsten bär" in cut[320]
