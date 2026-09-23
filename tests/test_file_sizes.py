"""No module may grow past the point where nobody reads it whole.

Finding K: files over the project's own limits. `css.py` was 902 lines,
`04_Kontantinsats.py` 885, `components.py` 489. A file that long stops being read
and starts being grepped, which is how `components.py` ended up holding both the
KPI card every page renders and the landing hero that appears once.

T3.3, T3.10 and T3.11 split them. This keeps them split.

The limit is 400 for code. `labels.py` is exempt: it is a data file that happens
to be Python, and 269 copy strings cannot be made shorter by splitting them into
two dictionaries — that would only make a key harder to find. Its own guards live
in `test_no_inline_copy.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 400

EXEMPT = {
    # One dict of user-facing copy. Splitting it would scatter the thing T3.1
    # deliberately gathered.
    "labels.py",
}

# R10 is closed and this set is empty of `src/data/` modules. Both were exempt
# for the same reason — over the limit, and at 0 % coverage, which made splitting
# them the riskiest refactor available because nothing would catch a mistake.
# Both took the same route out, in the order the risk prescribed:
#
#   scb_client.py   2026-09-21  tests first, then the PxWeb transport to
#                               pxweb.py. 487 -> 328 lines.
#   build_panel.py  2026-09-22  tests first (0 % -> 87 %), then the cleaners to
#                               clean_sources.py and the refresh report to
#                               panel_summary.py. 615 -> 387 lines.
#
# Both splits were verified by rebuilding from the real cached data and
# comparing the output to the pre-split artifacts, not by a line count.

# Ceilings for exempt modules, so an exemption cannot quietly cover further
# growth. Empty now that R10 is closed: nothing is over the limit but labels.py,
# which is a data file and has its own guards in test_no_inline_copy.py.
EXEMPT_CEILINGS: dict[str, int] = {}


def _modules() -> list[Path]:
    paths = (
        [ROOT / "app.py"]
        + sorted((ROOT / "pages").glob("*.py"))
        + sorted((ROOT / "src").rglob("*.py"))
        + sorted((ROOT / "tests").glob("*.py"))
    )
    return [p for p in paths if p.name not in EXEMPT and "__pycache__" not in p.parts]


@pytest.mark.parametrize("module", _modules(), ids=lambda p: p.name)
def test_module_is_under_the_line_limit(module: Path) -> None:
    length = len(module.read_text(encoding="utf-8").splitlines())
    assert length <= LIMIT, (
        f"{module.relative_to(ROOT).as_posix()} is {length} lines, over the {LIMIT}-line "
        "limit. Finding K: past this length a file is grepped rather than read, and "
        "unrelated things start sharing it."
    )


def test_exempt_modules_do_not_grow() -> None:
    """An exemption is for the size a file already is, not a licence to expand.

    A plain loop rather than a parametrize: the dict is empty now that R10 is
    closed, and an empty parametrize reports as a permanent skip, which reads
    like something is broken rather than like something was finished.
    """
    for name, ceiling in EXEMPT_CEILINGS.items():
        path = next(p for p in (ROOT / "src").rglob(name))
        length = len(path.read_text(encoding="utf-8").splitlines())
        assert length <= ceiling, (
            f"{name} has grown from {ceiling} to {length} lines while exempt from "
            f"the {LIMIT}-line limit. Split it, or give it tests first (R5)."
        )


def test_no_source_module_still_needs_a_ceiling() -> None:
    """R10, closed. Kept as an assertion so a new exemption is a visible choice.

    If this fails, someone added a module to EXEMPT_CEILINGS. That may be right,
    but it reopens the risk and should be recorded in docs/OPEN_RISKS.md rather
    than absorbed.
    """
    assert EXEMPT_CEILINGS == {}, (
        f"modules are exempt from the line limit again: {sorted(EXEMPT_CEILINGS)}. "
        f"R10 closed when the last one was split; re-opening it is a decision."
    )


def test_the_split_modules_still_exist() -> None:
    """A split undone by re-merging would otherwise pass silently."""
    for expected in (
        # The PxWeb transport, split from scb_client.py so that module holds only
        # which table and which selection.
        "src/data/pxweb.py",
        # The R10 split of build_panel.py: shapes, joins and report.
        "src/data/clean_sources.py",
        "src/data/panel_summary.py",
        # Reading the provenance artifact and writing it have different
        # audiences: every page imports the readers, the builder runs once per
        # refresh.
        "src/provenance_build.py",
        "src/ui/tokens.py",
        "src/ui/css_purpose.py",
        "src/ui/css_layout.py",
        "src/ui/css_components.py",
        "src/ui/css_landing.py",
        "src/ui/css_responsive.py",
        "src/ui/landing.py",
        "src/kontantinsats/sections.py",
        "src/kontantinsats/assumptions.py",
        "src/kontantinsats/charts.py",
        "src/kontantinsats/regions.py",
    ):
        assert (ROOT / expected).exists(), f"{expected} is gone; was a split reverted?"


def test_tokens_are_importable_from_one_place() -> None:
    """T3.3: `COLORS` and `DIVERGING_SCALE` have a single home."""
    from src.ui.tokens import COLORS, DIVERGING_SCALE

    assert COLORS and DIVERGING_SCALE
    # Re-exported from css.py so existing imports keep working.
    from src.ui.css import COLORS as via_css

    assert via_css is COLORS


def test_css_has_a_single_injection_point() -> None:
    """Two `<style>` blocks racing to define one rule is a rendering coin toss."""
    import re

    sources = [ROOT / "app.py"] + sorted((ROOT / "pages").glob("*.py"))
    for path in sources:
        text = path.read_text(encoding="utf-8")
        assert len(re.findall(r"\binject_css\s*\(", text)) <= 1, (
            f"{path.name} injects CSS more than once"
        )
        assert "<style>" not in text, f"{path.name} emits its own style block"


def test_no_regulatory_constant_lives_in_a_page() -> None:
    """T3.11: regime rules belong to `src/kontantinsats/`, not to a page script."""
    import re

    page = (ROOT / "pages" / "04_Kontantinsats.py").read_text(encoding="utf-8")
    for pattern, what in (
        (r"REGIMES\s*=\s*\{", "the regime table"),
        (r"REGIME_ACCENT_COLORS\s*=\s*\{", "the regime colour map"),
        (r"REGIME_WHAT_CHANGED\s*=\s*\{", "the regime descriptions"),
        (r"_LAN_NAMES\s*=\s*\{", "the county lookup"),
    ):
        assert not re.search(pattern, page), (
            f"{what} is defined in the page; it cannot be unit-tested there"
        )
