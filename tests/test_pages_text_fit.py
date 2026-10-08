"""No chart or map text on any page may run past its edge, at any width.

`test_chart_text_fits.py` draws the figures that live in `src/` on a bare page.
That misses what only the running app shows: charts built inside the page files,
the map, and above all the column a chart is given. At 768 px with the sidebar
open, Streamlit still laid three charts side by side at about 140 px each, and
their titles, tick labels and the histogram's median label were cut. The map's
legend, a fixed 450 px wide, was cut on every phone. Every figure passed on its
own; the page did not.

So this test runs the app, opens every page at desktop, tablet and phone widths,
and checks each glyph of every Plotly chart and of the map legend against the
box it belongs to.

Opt-in like `test_rendered_chart.py`: it skips when Playwright or its Chromium
is not installed.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api", reason="Playwright is not installed")

from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

#: URL paths of the pages that draw charts or the map.
PAGES = ("Riksoversikt", "Lan_jamforelse", "Kommun_djupanalys", "Kontantinsats", "Scenario")

#: Desktop, tablet, large phone, phone.
WIDTHS = (1280, 768, 390, 320)

#: Time for Plotly and the page's CSS to settle after a resize.
_SETTLE_MS = 1200

#: Glyph extents, not element boxes: a label's trailing padding may be clipped,
#: its characters may not. One pixel of tolerance for sub-pixel rounding.
_CUT_TEXT_JS = r"""
() => {
  const out = [];
  const outside = (b, box) => b.left < box.left - 1 || b.right > box.right + 1;
  document.querySelectorAll('div.js-plotly-plot').forEach((plot, i) => {
    const box = plot.getBoundingClientRect();
    if (box.width === 0) return;
    // A chart that fits its own box but sticks out of the page is cut too.
    const page = {left: 0, right: document.documentElement.clientWidth};
    if (outside(box, page)) out.push(`chart ${i}: wider than the page`);
    plot.querySelectorAll('svg text').forEach(t => {
      const raw = t.textContent || '';
      if (!raw.trim()) return;
      const first = raw.search(/\S/);
      const last = raw.length - 1 - raw.split('').reverse().join('').search(/\S/);
      try {
        const m = t.getScreenCTM(), a = t.getExtentOfChar(first), b = t.getExtentOfChar(last);
        const p1 = new DOMPoint(a.x, a.y).matrixTransform(m);
        const p2 = new DOMPoint(b.x + b.width, b.y + b.height).matrixTransform(m);
        const ext = {left: Math.min(p1.x, p2.x), right: Math.max(p1.x, p2.x)};
        if (outside(ext, box)) out.push(`chart ${i}: ${raw.trim().slice(0, 50)}`);
      } catch (e) { /* text not laid out, e.g. a hidden trace */ }
    });
  });
  document.querySelectorAll('.shai-map-legend').forEach(legend => {
    const box = legend.getBoundingClientRect();
    legend.querySelectorAll('span, .shai-map-legend-caption').forEach(e => {
      if (outside(e.getBoundingClientRect(), box)) out.push(`map legend: ${e.textContent}`);
    });
  });
  return out;
}
"""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server() -> str:
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", str(port), "--server.headless", "true"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(60):
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(1)
        else:
            pytest.skip("Streamlit did not start in time")
        yield f"http://127.0.0.1:{port}"
    finally:
        proc.terminate()
        proc.wait(timeout=30)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        try:
            chromium = pw.chromium.launch()
        except Exception as exc:  # browser binary not installed
            pytest.skip(f"Playwright Chromium is not available: {exc}")
        yield chromium
        chromium.close()


def _cut_text_by_width(browser, url: str) -> tuple[int, dict[int, list[str]]]:
    """Load `url` once, resize through every width, return what was cut."""
    page = browser.new_page(viewport={"width": WIDTHS[0], "height": 1000})
    try:
        page.goto(url, wait_until="networkidle", timeout=90_000)
        page.wait_for_selector(
            '[data-testid="stApp"][data-test-script-state="notRunning"]', timeout=90_000
        )
        page.wait_for_timeout(_SETTLE_MS)
        charts = page.locator("div.js-plotly-plot").count()
        cut = {}
        for width in WIDTHS:
            page.set_viewport_size({"width": width, "height": 1000})
            page.wait_for_timeout(_SETTLE_MS)
            found = page.evaluate(_CUT_TEXT_JS)
            if found:
                cut[width] = found
        return charts, cut
    finally:
        page.close()


@pytest.mark.parametrize("path", PAGES)
def test_no_text_is_cut_on_the_page(path: str, server: str, browser) -> None:
    charts, cut = _cut_text_by_width(browser, f"{server}/{path}")
    assert charts > 0, f"/{path} drew no chart, so nothing was checked"
    assert not cut, f"/{path}: text past its chart's edge, by viewport width: {cut}"


def test_the_map_page_draws_the_page_legend(server: str, browser) -> None:
    page = browser.new_page(viewport={"width": 390, "height": 1000})
    try:
        page.goto(f"{server}/Riksoversikt", wait_until="networkidle", timeout=90_000)
        page.wait_for_selector(".shai-map-legend", timeout=90_000)
    finally:
        page.close()
