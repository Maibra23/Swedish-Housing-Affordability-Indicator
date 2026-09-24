"""Displayed counts and periods must come from the data, not from the source.

`290 kommuner` and `2014–2024` were typed into nineteen places across the app.
Both are facts about the panel that the provenance artifact already records, and
both silently become lies the moment the panel changes: a municipality merger
moves the first, every refresh moves the second. The app would keep asserting
the old numbers with total confidence, because nothing connects the sentence to
the data it describes.

See Finding H in docs/REVITALIZATION_PLAN.md, and task T1.10.

Two kinds of assertion live here. The source-level ones prove the literals are
gone; the behavioural one proves what replaced them actually tracks the
artifact — a literal moved into a constant at the top of a module would satisfy
the first and fail the second.

Upstream *source coverage* windows (`1981–2024` for the price series, `2011–2024`
for income) are deliberately out of scope. Those describe what SCB publishes,
not what this index computes, and they are governed by the `sources` block of the
provenance artifact rather than by its index period.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests.sourcetools import executable_source

ROOT = Path(__file__).resolve().parents[1]

# The index period, in every spelling the codebase uses: an en dash, a hyphen,
# the escaped `–`, and the HTML entity.
PERIOD = re.compile(r"2014\s*(?:&ndash;|&#8211;|\\u2013|[-–—])\s*2024")

# "11 år", "11 årliga observationer" — the length of that period, written out.
PERIOD_LENGTH = re.compile(r"\b11\s+år")

# The municipality count. `\b` keeps this off "290px" and similar.
KOMMUN_COUNT = re.compile(r"\b290\b")


def _display_modules() -> list[Path]:
    return sorted(
        [ROOT / "app.py"]
        + [p for p in (ROOT / "pages").glob("*.py") if not p.name.startswith("_")]
        + [p for p in (ROOT / "src" / "ui").glob("*.py") if not p.name.startswith("_")]
    )


def _hits(path: Path, pattern: re.Pattern[str]) -> list[str]:
    """Matches in the module's executable source, as `line: text` for the report."""
    source = executable_source(path.read_text(encoding="utf-8"))
    return [
        f"{path.relative_to(ROOT).as_posix()}:{i}: {line.strip()}"
        for i, line in enumerate(source.splitlines(), start=1)
        if pattern.search(line)
    ]


# ── Source-level: the literals are gone ──────────────────────────────


@pytest.mark.parametrize("module", _display_modules(), ids=lambda p: p.name)
def test_no_literal_municipality_count(module: Path) -> None:
    hits = _hits(module, KOMMUN_COUNT)
    assert not hits, "municipality count hardcoded:\n" + "\n".join(hits)


@pytest.mark.parametrize("module", _display_modules(), ids=lambda p: p.name)
def test_no_literal_index_period(module: Path) -> None:
    hits = _hits(module, PERIOD)
    assert not hits, "index period hardcoded:\n" + "\n".join(hits)


@pytest.mark.parametrize("module", _display_modules(), ids=lambda p: p.name)
def test_no_literal_period_length(module: Path) -> None:
    hits = _hits(module, PERIOD_LENGTH)
    assert not hits, "number of observation years hardcoded:\n" + "\n".join(hits)


def test_the_guard_can_see_a_reintroduced_literal() -> None:
    """A guard that matches nothing would pass this file even when it should not."""
    assert KOMMUN_COUNT.search('unit="av 290"')
    assert PERIOD.search('value="2014–2024"')
    assert PERIOD.search("2014&ndash;2024")
    assert PERIOD_LENGTH.search("11 årliga observationer")
    assert not KOMMUN_COUNT.search("width:290px")


# ── Behavioural: what replaced them follows the artifact ─────────────


@pytest.fixture
def relabelled_panel(tmp_path, monkeypatch):
    """Point the provenance accessors at a panel with different dimensions.

    Values chosen to be unmistakable: no real Swedish panel has 277
    municipalities running 2009–2019.
    """
    from src import provenance

    payload = json.loads((ROOT / "data" / "processed" / "data_provenance.json").read_text("utf-8"))
    payload["n_kommuner"] = 277
    payload["index_min_year"] = 2009
    payload["index_max_year"] = 2019
    payload["complete_case_max_year"] = 2019

    artifact = tmp_path / "data_provenance.json"
    artifact.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(provenance, "_PROVENANCE_PATH", artifact)
    provenance.load_provenance.cache_clear()
    yield
    provenance.load_provenance.cache_clear()


@pytest.fixture
def rendered(monkeypatch):
    """Capture the HTML a landing component emits.

    T3.10 moved these out of `components` into `src/ui/landing.py`; the sinks are
    patched on that module.

    Both sinks are patched. `render_landing_steps` writes through `st.html`
    rather than `st.markdown` — capturing only the latter returned an empty
    string, which quietly satisfied every "the old literal is absent" assertion
    below without rendering anything at all.
    """

    def _render(component, *args, **kwargs) -> str:
        from src.ui import landing

        captured: list[str] = []
        for sink in ("markdown", "html"):
            monkeypatch.setattr(
                landing.st, sink, lambda payload, **_: captured.append(str(payload))
            )
        getattr(landing, component)(*args, **kwargs)
        assert captured, f"{component} rendered nothing — the capture missed its sink"
        return "\n".join(captured)

    return _render


LANDING_COMPONENTS = [
    "render_landing_hero",
    "render_landing_what_is_block",
    "render_landing_steps",
    "render_landing_credibility",
]


@pytest.mark.parametrize("component", LANDING_COMPONENTS)
def test_landing_copy_quotes_the_real_panel(component, rendered) -> None:
    from src.provenance import n_kommuner

    html = rendered(component)
    if "kommun" not in html.lower():
        pytest.skip(f"{component} does not quote the municipality count")
    assert str(n_kommuner()) in html


@pytest.mark.parametrize("component", LANDING_COMPONENTS)
def test_landing_copy_follows_a_changed_panel(component, relabelled_panel, rendered) -> None:
    """The acceptance criterion: change the data, the page changes, no code edit."""
    html = rendered(component)
    assert "290" not in html, f"{component} still renders the old municipality count"
    assert not PERIOD.search(html), f"{component} still renders the old index period"


def test_changed_panel_reaches_the_rendered_count(relabelled_panel, rendered) -> None:
    html = rendered("render_landing_hero")
    assert "277" in html, "the hero does not read the municipality count from provenance"


def test_changed_panel_reaches_the_rendered_period(relabelled_panel, rendered) -> None:
    html = rendered("render_landing_credibility")
    assert "2009" in html and "2019" in html, (
        "the credibility strip does not read the index period from provenance"
    )
