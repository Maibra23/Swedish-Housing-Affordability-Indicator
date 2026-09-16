"""`DESIGN_SYSTEM.md` must describe the stylesheet that actually ships.

Its previous version documented a Plotly `go.Scattergeo` map that commit `4f98a23`
had already replaced with Folium, and a `.lp-*` / `.riskklass-*` / `.shai-*` class
mix that T3.2 normalised away. That is Finding L: documentation confidently
describing code that no longer exists, with nothing to tell a reader which half to
believe.

The fix is not a better rewrite — it is a rewrite that cannot silently rot. The
inventory is compared against the composed stylesheet in **both** directions: a
documented class that no longer exists fails, and a class in the stylesheet that
nobody documented fails too.

See task T4.7.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.ui.css import GLOBAL_CSS
from src.ui.tokens import COLORS, DIVERGING_SCALE

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "DESIGN_SYSTEM.md"


def _documented() -> set[str]:
    """Classes listed in the inventory table, as `` `.shai-x` `` cells."""
    return set(re.findall(r"\|\s*`\.(shai-[\w-]+)`\s*\|", DOC.read_text(encoding="utf-8")))


def _in_stylesheet() -> set[str]:
    """`shai-` classes the composed stylesheet defines, URL fragments excluded."""
    css = re.sub(r"https?://\S+", " ", GLOBAL_CSS)
    return {n for n in re.findall(r"\.([a-zA-Z][\w-]*)", css) if n.startswith("shai-")}


# ── The inventory must match the stylesheet, both ways ────────────────


def test_every_documented_class_exists_in_the_stylesheet() -> None:
    ghosts = sorted(_documented() - _in_stylesheet())
    assert not ghosts, (
        f"DESIGN_SYSTEM.md documents classes that no longer exist: {ghosts}. This is "
        "how the old version came to describe a Plotly map."
    )


def test_every_stylesheet_class_is_documented() -> None:
    undocumented = sorted(_in_stylesheet() - _documented())
    assert not undocumented, (
        f"these classes ship but are not in the inventory: {undocumented}. Add them to "
        "section 3, or a reader has to grep the stylesheet to find out what exists."
    )


def test_the_inventory_states_its_own_count_correctly() -> None:
    text = DOC.read_text(encoding="utf-8")
    stated = re.search(r"(\d+)\s+in total", text)
    assert stated, "the inventory does not state how many classes it lists"
    assert int(stated.group(1)) == len(_in_stylesheet()), (
        f"the document claims {stated.group(1)} classes; the stylesheet has "
        f"{len(_in_stylesheet())}"
    )


# ── Tokens ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("token", sorted(COLORS))
def test_every_colour_token_is_documented(token: str) -> None:
    text = DOC.read_text(encoding="utf-8")
    assert f"`{token}`" in text, f"colour token {token!r} is missing from the token table"
    assert f"`{COLORS[token]}`" in text, (
        f"the documented value for {token!r} does not match {COLORS[token]}"
    )


def test_the_diverging_scale_is_documented_in_order() -> None:
    """Scoped to the scale line: several of these hex values are also tokens."""
    text = DOC.read_text(encoding="utf-8")
    line = next(
        (l for l in text.splitlines() if "Diverging scale" in l),
        None,
    )
    assert line, "the diverging scale is not documented"
    positions = [line.find(f"`{colour}`") for colour in DIVERGING_SCALE]
    assert all(p >= 0 for p in positions), (
        f"not every scale colour appears on the scale line: {line}"
    )
    assert positions == sorted(positions), (
        "the scale is documented out of order; its direction is its meaning"
    )


def test_the_accent_token_is_tied_to_the_streamlit_theme() -> None:
    """T3.12: `primaryColor` must track `COLORS["accent"]`, and the doc must say so."""
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert COLORS["accent"] in config, (
        "primaryColor no longer matches the accent token; a selected pill will not "
        "read as selected"
    )
    assert "primaryColor" in DOC.read_text(encoding="utf-8")


# ── The map section must describe what ships ─────────────────────────


def test_map_section_describes_folium_and_the_empirical_scale() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "Folium" in text, "the map section must name the library that renders it"
    assert "go.Scattergeo" not in text or "replaced" in text, (
        "Scattergeo may only appear as history, never as the current implementation"
    )
    assert "empirical" in text.lower(), "the colour domain is data-derived; say so"
    assert "Esri" in text, "the basemap host is not named"


def test_map_section_agrees_with_the_choropleth_module() -> None:
    """The document's claims, checked against the code rather than trusted.

    Against *executable* source: `choropleth.py` carries a comment recording the
    tile host that had to be abandoned, and a guard that cannot tell prose from
    code would punish the explanation. Same reasoning as `tests/sourcetools.py`.
    """
    from tests.sourcetools import executable_source

    module = executable_source(
        (ROOT / "src" / "ui" / "choropleth.py").read_text(encoding="utf-8")
    )
    assert "arcgisonline" in module, "the doc says Esri; the module does not use it"
    assert "cartocdn" not in module, "the doc says CARTO was dropped; it is still wired up"


# ── The checklist has to exist and point at real guards ──────────────


def test_contributor_checklist_exists() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "## 6. Contributor checklist" in text
    assert text.count("- [ ]") >= 6, "a checklist with two items is a suggestion"


def test_checklist_references_tests_that_exist() -> None:
    text = DOC.read_text(encoding="utf-8")
    for name in re.findall(r"`tests/(test_[\w]+\.py)`", text):
        assert (ROOT / "tests" / name).exists(), (
            f"the checklist points at {name}, which does not exist"
        )


def test_the_document_states_what_it_cannot_verify() -> None:
    """D2's goal is visual convergence, which no test here can check."""
    text = DOC.read_text(encoding="utf-8")
    assert "unverified" in text.lower(), (
        "the document must say that visual equivalence with Skattekraftspanelen is "
        "unchecked; claiming D2 is met would be the same defect Finding L describes"
    )
