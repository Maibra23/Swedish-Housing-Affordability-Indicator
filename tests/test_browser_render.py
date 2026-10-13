"""What the browser shows, checked in the browser.

AppTest sees the Markdown a page sends, not what a browser makes of it. The
October 2026 audit found the footer printing ``<span>Data uppdaterad …</span>``
as literal text on six of seven pages while 1 303 tests passed, because a blank
line inside an HTML string is harmless to AppTest and fatal to the Markdown
renderer. This module starts the app, opens every page in Chromium at desktop
and phone width, and asserts on the rendered DOM.

Skipped when Playwright or its Chromium build is not installed, or when
``SHAI_SKIP_BROWSER=1``. About 90 seconds.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

if os.environ.get("SHAI_SKIP_BROWSER") == "1":
    pytest.skip("SHAI_SKIP_BROWSER=1", allow_module_level=True)
sync_api = pytest.importorskip("playwright.sync_api")

PAGES = {
    "start": "/",
    "rv": "/Riksoversikt",
    "lj": "/Lan_jamforelse",
    "kd": "/Kommun_djupanalys",
    "ki": "/Kontantinsats",
    "sc": "/Scenario",
    "mt": "/Metodologi",
}
DESKTOP = {"width": 1440, "height": 900}
PHONE = {"width": 390, "height": 844}
SETTLE_MS = 6000

# Leaf elements whose text is wider than their box and cut off.
CLIPPED_JS = """
() => [...document.querySelectorAll('[data-testid="stMain"] *')]
  .filter(el => {
    if (el.children.length || !el.textContent.trim()) return false;
    const cs = getComputedStyle(el);
    const clips = cs.overflow === 'hidden' || cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis';
    return clips && el.scrollWidth > el.clientWidth + 2 && el.offsetParent !== null;
  })
  .map(el => el.textContent.trim().slice(0, 60))
"""

LITERAL_MARKUP_JS = """
() => [...document.querySelectorAll('[data-testid="stMain"] pre, [data-testid="stMain"] code')]
  .map(el => el.innerText).filter(t => /<\\/?(span|div|code|strong)\\b/.test(t))
"""


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def base_url():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true",
         "--server.port", str(port), "--browser.gatherUsageStats", "false"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(url + "/_stcore/health", timeout=1)
                break
            except OSError:
                time.sleep(1)
        else:
            pytest.fail("streamlit did not start within 60 s")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=20)


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            chromium = p.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - a missing browser build is a skip, not a failure
            pytest.skip(f"Chromium not available: {exc}")
        yield chromium
        chromium.close()


def _open(browser, base_url: str, path: str, viewport: dict):
    page = browser.new_page(viewport=viewport)
    page.goto(base_url + path, wait_until="networkidle")
    page.wait_for_selector('[data-testid="stMain"]', timeout=60_000)
    page.wait_for_timeout(SETTLE_MS)
    return page


@pytest.mark.parametrize("key", PAGES)
def test_desktop_page_renders_clean(browser, base_url: str, key: str) -> None:
    page = _open(browser, base_url, PAGES[key], DESKTOP)
    try:
        assert not page.query_selector_all('[data-testid="stException"]'), "page raised"
        assert page.evaluate(LITERAL_MARKUP_JS) == [], "HTML is shown as text (A-01)"
        assert page.evaluate(CLIPPED_JS) == [], "text clipped by its container (A-21)"
        footer = page.inner_text(".shai-footer-note")
        assert "Data uppdaterad" in footer and "<span" not in footer
    finally:
        page.close()


@pytest.mark.parametrize("key", PAGES)
def test_phone_page_opens_on_content(browser, base_url: str, key: str) -> None:
    page = _open(browser, base_url, PAGES[key], PHONE)
    try:
        width = page.evaluate("() => document.documentElement.scrollWidth")
        assert width <= PHONE["width"] + 2, f"page scrolls sideways ({width}px)"
        sidebar = page.query_selector('[data-testid="stSidebar"]')
        expanded = sidebar.get_attribute("aria-expanded") if sidebar else "false"
        assert expanded != "true", "sidebar covers the page on first load (A-08)"
    finally:
        page.close()


def test_phone_can_open_the_sidebar(browser, base_url: str) -> None:
    """With the sidebar collapsed on phones, its reopen button must be reachable.

    The button lives in Streamlit's header, which the app hides. Opening on the
    content (A-08) is only safe if a visitor can still reach the navigation and
    the year selector.
    """
    page = _open(browser, base_url, PAGES["rv"], PHONE)
    try:
        toggle = page.query_selector('[data-testid="stExpandSidebarButton"]')
        assert toggle is not None and toggle.is_visible(), "no visible way to open the sidebar"
        toggle.click()
        page.wait_for_timeout(1500)
        sidebar = page.query_selector('[data-testid="stSidebar"]')
        assert sidebar.get_attribute("aria-expanded") == "true"
        assert page.is_visible("text=Kontantinsatsanalys")
    finally:
        page.close()
