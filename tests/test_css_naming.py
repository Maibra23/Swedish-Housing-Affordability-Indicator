"""One CSS naming convention, and no class that styles nothing.

SHAI's stylesheet had grown four naming conventions at once: KRI-era `.sidebar-brand`
and `.brand-mark`, Swedish `.riskklass-*`, landing-page `.lp-*`, and the newer
`.shai-*`. Finding M is that gap. A reader cannot tell which prefix is current, so
each new component picks one at random and the drift compounds.

T3.2 normalised everything to `.shai-*`, prefix-preserving: `.lp-hero` became
`.shai-lp-hero` rather than `.shai-hero`, so the grouping that made `lp-` and
`riskklass-` readable survives and no rename could collide with an existing name.

Two classes were used in markup and defined nowhere — `lp-explain-card` and
`lp-visual`, both sitting beside the `lp-card-light` that actually did the styling.
They were removed rather than given invented styles. A class that styles nothing is
how a design system stops being trustworthy: the next reader cannot tell whether it
is dead or whether its rule was lost.

Modifier classes interpolated at render time (`{delta_direction}` → `up`/`down`/
`flat`, `{level}` → `lag`/`medel`/`hog`, `variant-{variant}`) are exempt. They are
never written alone; CSS reaches them as `.shai-kpi-delta.up`, scoped under a
`shai-` parent.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The composed stylesheet, not one file: T3.3 split it into tokens/layout/
# components/landing, and `css.py` is now only the composer.
from src.ui.css import GLOBAL_CSS

SOURCES = (
    [ROOT / "app.py"]
    + sorted((ROOT / "pages").glob("*.py"))
    + sorted((ROOT / "src" / "ui").glob("*.py"))
)

# Bare modifiers, only ever applied alongside a shai- class.
MODIFIERS = {"up", "down", "flat", "lag", "medel", "hog", "positive", "negative"}


def _used_classes() -> dict[str, set[str]]:
    """class -> the files that use it, ignoring render-time interpolations."""
    found: dict[str, set[str]] = {}
    for path in SOURCES:
        for match in re.finditer(r'class=(["\'])([^"\']+)\1', path.read_text(encoding="utf-8")):
            for token in match.group(2).split():
                if "{" in token or token in MODIFIERS:
                    continue
                found.setdefault(token, set()).add(path.name)
    return found


# Selectors the stylesheet must reach but does not own.
#
# Streamlit renders its own DOM and these are its class names; renaming them would
# simply stop the rule applying. `variant-*` are our modifiers, applied only
# alongside `.shai-kpi-card`, so they carry no prefix by design.
FOREIGN = {
    "stApp", "stMarkdown", "stRadio", "stSelectbox", "stButton", "stMetric",
    "block-container", "main", "markdown", "pills",
}
OUR_MODIFIERS = {"variant-default", "variant-accent", "variant-danger", "variant-success"}


def _defined_classes() -> set[str]:
    """Class selectors the stylesheet defines, excluding URL fragments.

    `url(https://fonts.googleapis.com/...)` contains dot-separated hostnames that
    a naive selector regex reads as `.com` and `.googleapis`.
    """
    css = re.sub(r"https?://\S+", " ", GLOBAL_CSS)
    return set(re.findall(r"\.([a-zA-Z][\w-]*)", css))


def test_every_class_uses_the_shai_prefix() -> None:
    offenders = {
        name: sorted(files)
        for name, files in _used_classes().items()
        if not name.startswith("shai-")
    }
    assert not offenders, (
        f"classes outside the shai- convention: {offenders}. Finding M is four naming "
        "conventions coexisting; adding a fifth is how it came about."
    )


def test_no_stylesheet_selector_uses_another_convention() -> None:
    """The CSS side of the same rule, across every composed sheet."""
    legacy = sorted(
        name
        for name in _defined_classes()
        if not name.startswith("shai-")
        and name not in MODIFIERS | FOREIGN | OUR_MODIFIERS
    )
    assert not legacy, f"stylesheet still defines non-shai classes: {legacy}"


def test_every_used_class_is_defined() -> None:
    """Markup referencing a class that styles nothing is dead weight."""
    defined = _defined_classes()
    undefined = {
        name: sorted(files)
        for name, files in _used_classes().items()
        if name not in defined
    }
    assert not undefined, (
        f"classes used in markup but absent from the stylesheet: {undefined}. Either "
        "define them or remove them; a reader cannot tell a dead hook from a lost rule."
    )


def test_no_kri_era_infix_survives() -> None:
    """The plan's second criterion, read for intent rather than literally.

    It asks that `grep "lp-\|riskklass-\|brand-mark\|nav-section" src/` return
    nothing. Taken literally that is unsatisfiable: the same task *prescribes*
    `.brand-mark` -> `.shai-brand-mark`, which still contains `brand-mark`. What
    the criterion is protecting is that no KRI-era name survives *unprefixed* and
    that the `lp-` / `riskklass-` groupings are gone, which is what is asserted.
    """
    defined = _defined_classes()
    for infix in ("lp-", "riskklass-"):
        offenders = sorted(n for n in defined if infix in n)
        assert not offenders, f"{infix!r} still appears in class names: {offenders}"
    for legacy in ("brand-mark", "nav-section", "sidebar-brand"):
        assert legacy not in defined, f"{legacy} survives unprefixed"


def test_the_removed_dead_hooks_have_not_returned() -> None:
    for name in ("lp-explain-card", "lp-visual", "shai-explain-card", "shai-visual"):
        assert name not in _used_classes(), (
            f"{name} styled nothing and was removed in T3.2; it is back"
        )


def test_the_guard_can_see_a_foreign_prefix() -> None:
    """A detector matching nothing would pass every file above."""
    sample = '<div class="legacy-thing shai-card">'
    tokens = [t for t in re.findall(r'class="([^"]+)"', sample)[0].split()]
    assert [t for t in tokens if not t.startswith("shai-")] == ["legacy-thing"]
