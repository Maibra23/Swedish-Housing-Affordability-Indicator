"""Every page must render for every year the selector offers.

This is the check that actually proves the app works, and until now it lived in a
session scratch directory — run at every step of Phases 1 and 2, passing 67/67
each time, and re-runnable by nobody. See R6 in docs/OPEN_RISKS.md. Phase 3 is
twelve tasks of UI change to exactly the surface this covers, so it lands first.

**Pages are driven through `app.py` and `switch_page`, never as their own
entrypoint.** A page run directly fails on `st.page_link("app.py")`, because the
landing script is not part of that run's page registry. That is an AppTest
artifact, not a defect — the sidebar navigation works in the real app. Driving
from the entrypoint is also what a user does.

The sweep is 6 pages x 11 years plus the landing page = 67 renders, about 12
seconds. Cheap enough to stay in the default suite, which is the point: a guard
that has to be remembered is not a guard.

Findings this class of test would have caught: A (selecting 2014 silently
no-opped the risk filter and rendered a fabricated KPI) and B (two selectable
years had no data at all).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.ui.sidebar import YEAR_RANGE

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app.py")

# AppTest resolves a relative script path against the *calling* file, so every
# path here is absolute.
PAGES = {
    "pages/01_Riksoversikt.py": "rv",
    "pages/02_Lan_jamforelse.py": "lj",
    "pages/03_Kommun_djupanalys.py": "kd",
    "pages/04_Kontantinsats.py": "ki",
    "pages/05_Scenario.py": "sc",
    "pages/06_Metodologi.py": "mt",
}

TIMEOUT = 180


def _run(page: str | None = None, key: str | None = None, **state) -> AppTest:
    """Render the landing page, then optionally switch to `page`."""
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for name, value in state.items():
        at.session_state[f"{key}_{name}" if key else name] = value
    at.run()
    if page is not None:
        at.switch_page(page)
        at.run()
    return at


def _assert_clean(at: AppTest, what: str) -> None:
    if at.exception:
        pytest.fail(f"{what} raised: {at.exception[0].message}")
    # A page that returned early without rendering would otherwise pass silently.
    assert len(at.markdown) or len(at.dataframe) or len(at.metric), (
        f"{what} rendered no content at all"
    )


# ── The landing page ─────────────────────────────────────────────────


def test_landing_page_renders() -> None:
    _assert_clean(_run(), "app.py")


# ── Every page, every offered year ───────────────────────────────────


@pytest.mark.parametrize("page,key", PAGES.items(), ids=lambda v: v if isinstance(v, str) else v)
@pytest.mark.parametrize("year", YEAR_RANGE)
def test_page_renders_for_every_offered_year(page: str, key: str, year: int) -> None:
    """The selector must not offer a year the page cannot render.

    Parametrised on `YEAR_RANGE` rather than a literal list, so the day
    provenance widens the selector this sweep widens with it.
    """
    _assert_clean(_run(page, key, year_pills=year), f"{page} at {year}")


# ── The states a user can put the sidebar into ────────────────────────


@pytest.mark.parametrize("page,key", PAGES.items())
def test_page_renders_with_an_empty_risk_selection(page: str, key: str) -> None:
    """Deselecting every risk pill must not break a page.

    The sidebar normalises an empty selection back to all three classes. That is
    a behaviour worth pinning: the alternative is an empty dataframe reaching a
    chart, which is how Finding A produced a fabricated KPI.
    """
    _assert_clean(_run(page, key, risk_pills=[]), f"{page} with no risk selected")


@pytest.mark.parametrize("page,key", PAGES.items())
def test_page_renders_with_a_single_risk_class(page: str, key: str) -> None:
    _assert_clean(_run(page, key, risk_pills=["Hög"]), f"{page} with only Hög selected")


# ── The guard must be able to fail ───────────────────────────────────


def test_the_harness_detects_a_raising_script(tmp_path: Path) -> None:
    """Without this, 67 green ticks could mean 67 renders or a broken harness."""
    broken = tmp_path / "broken_app.py"
    broken.write_text(
        "import streamlit as st\n"
        "st.markdown('before')\n"
        "raise ValueError('deliberate')\n",
        encoding="utf-8",
    )
    at = AppTest.from_file(str(broken), default_timeout=TIMEOUT)
    at.run()
    assert at.exception, "AppTest did not surface an exception the script raised"
    assert "deliberate" in at.exception[0].message


def test_the_harness_detects_an_empty_script(tmp_path: Path) -> None:
    """The content assertion in `_assert_clean` must also be able to fail."""
    empty = tmp_path / "empty_app.py"
    empty.write_text("import streamlit as st\n", encoding="utf-8")
    at = AppTest.from_file(str(empty), default_timeout=TIMEOUT)
    at.run()
    assert not at.exception
    assert not (len(at.markdown) or len(at.dataframe) or len(at.metric))
