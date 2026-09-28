"""What the browser actually paints, which no other test in this suite sees.

Every other guard here reads source or asks `AppTest` for element *values*.
Neither looks at glyphs. That gap shipped a real defect: Sida 03's legend read
"Dagens nivå, 0,77" because Plotly sized the legend's clip rectangle from a text
measurement taken before the `Source Sans 3` webfont loaded, and the real glyphs
render about 18 % wider. The unit was missing from a number whose entire point is
that it is a rate in percentage points, and the suite was green throughout.

The failure mode is specific and worth naming, because it is invisible to the
DOM: the text node holds the full string and reports a full bounding box, while
an ancestor `<g class="scrollbox">` carries a clip-path narrower than the text.
Nothing short of comparing the two catches it.

**This test is opt-in.** Playwright is not a project dependency and is not
declared in `pyproject.toml`, because a 150 MB browser download does not belong
in the install path of a dashboard that ships committed Parquet. It skips
cleanly when Playwright is absent, so it is a local and pre-release check rather
than a gate. That is a deliberate trade: a guard that runs sometimes beats a
dependency that everyone pays for, given the defect class is rare and visual.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time

import pytest

pytest.importorskip("playwright.sync_api", reason="Playwright is not installed")

from pathlib import Path  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

#: Legend geometry, read out of the SVG. `50` is the width Plotly reserves for
#: the colour swatch before the label starts.
_SWATCH_W = 50

_MEASURE_LEGEND = """() => {
  const p = document.querySelector('.js-plotly-plot');
  if (!p) return null;
  const sb = p.querySelector('g.scrollbox');
  const id = (sb.getAttribute('clip-path') || '').replace(/url\\(#|\\)/g, '');
  const el = id ? document.getElementById(id) : null;
  const clip = el ? +el.querySelector('rect').getAttribute('width') : Infinity;
  const rows = [];
  p.querySelectorAll('g.traces text.legendtext').forEach(t => {
    // Trailing padding is allowed to be clipped; the glyphs are not.
    const glyphs = t.textContent.replace(/\\u00a0+$/, '');
    const r = document.createRange();
    r.setStart(t.firstChild, 0);
    r.setEnd(t.firstChild, glyphs.length);
    rows.push({label: glyphs, width: r.getBoundingClientRect().width});
  });
  return {clip, rows};
}"""


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


def test_no_legend_label_is_clipped(server: str) -> None:
    """Every legend glyph must fit inside the box Plotly clipped it to."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1500, "height": 1000})
        try:
            page.goto(f"{server}/Kommun_djupanalys", wait_until="networkidle", timeout=90_000)
            page.wait_for_selector(".js-plotly-plot g.traces text.legendtext", timeout=60_000)
            page.wait_for_timeout(3000)
            measured = page.evaluate(_MEASURE_LEGEND)
        finally:
            browser.close()

    assert measured, "no Plotly chart rendered on Sida 03"
    assert len(measured["rows"]) == 5, (
        f"expected 5 legend entries (municipality, county, 3 scenarios), "
        f"got {[r['label'] for r in measured['rows']]}"
    )

    clip = measured["clip"]
    cut = [
        (r["label"], round(_SWATCH_W + r["width"] - clip))
        for r in measured["rows"]
        if _SWATCH_W + r["width"] > clip
    ]
    assert not cut, (
        "legend labels are clipped, losing their final characters: "
        + ", ".join(f"{lbl!r} by {px} px" for lbl, px in cut)
        + f" (clip width {clip} px). Plotly measures legend text before the "
        "webfont loads and sizes the clip too small; widen _LEGEND_PAD in "
        "pages/03_Kommun_djupanalys.py until every entry fits."
    )
