"""User-facing Swedish copy belongs in `SWEDISH_LABELS`, not in a page script.

T3.1 moved 269 strings out of `app.py` and `pages/*.py`. The point was never
tidiness: `tests/test_copy_matches_artifacts.py` (T4.1) has to re-derive every
number quoted in the UI from the committed artifacts, and it cannot do that while
the copy is scattered across seven scripts. Findings A, C and H were all copy
disagreeing with data.

Extraction is the kind of work that decays. The next person to add a `st.warning`
will type the Swedish inline, because that is the shorter path, and nothing would
notice. This is what notices.

Detection is by Swedish diacritic. That deliberately under-reaches — a
pure-ASCII Swedish string like "Medel" or "Analys" slips through — but it never
false-positives on English, so it can run over every page with no allowlist to
maintain. The stricter structural check (no literal reaching a `st.*` display
call) is left to T4.3, which can assert against the labels module itself.

Docstrings and comments are exempt and must stay English-friendly: they are
stripped by `tests/sourcetools.py` before matching, so an explanation that quotes
the Swedish copy it is describing cannot trip the guard against inline copy.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ui.labels import SWEDISH_LABELS
from tests.sourcetools import executable_source

ROOT = Path(__file__).resolve().parents[1]
DIACRITICS = set("åäöÅÄÖéüÉÜ")


def _page_files() -> list[Path]:
    return [ROOT / "app.py"] + sorted(
        p for p in (ROOT / "pages").glob("*.py") if not p.name.startswith("_")
    )


def _swedish_literals(path: Path) -> list[str]:
    """Every string constant carrying a Swedish diacritic, docstrings excluded."""
    tree = ast.parse(executable_source(path.read_text(encoding="utf-8")))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and DIACRITICS & set(node.value)
    ]


@pytest.mark.parametrize("page", _page_files(), ids=lambda p: p.name)
def test_no_inline_swedish_copy(page: Path) -> None:
    found = _swedish_literals(page)
    assert not found, (
        f"{page.name} carries {len(found)} inline Swedish string(s); move them to "
        f"SWEDISH_LABELS and reach them through L(). First: {found[0][:90]!r}"
    )


# ── Every key a page asks for must exist ─────────────────────────────


def _referenced_keys(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "L"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }


@pytest.mark.parametrize("page", _page_files(), ids=lambda p: p.name)
def test_every_referenced_label_exists(page: Path) -> None:
    """A typo in a key is a blank space on a rendered page, not a crash."""
    missing = sorted(_referenced_keys(page) - set(SWEDISH_LABELS))
    assert not missing, f"{page.name} references undefined labels: {missing}"


def test_no_label_is_empty() -> None:
    blank = sorted(k for k, v in SWEDISH_LABELS.items() if not v.strip())
    assert not blank, f"empty label values render as nothing: {blank}"


def test_no_label_is_orphaned() -> None:
    """Copy nobody displays is copy nobody reviews.

    All of `src/` is scanned: keys are consumed by `src/ui/` components and, since
    T3.11, by `src/kontantinsats/` as well.
    """
    referenced: set[str] = set()
    for path in _page_files() + sorted((ROOT / "src").rglob("*.py")):
        if path.name == "labels.py":
            continue
        referenced |= _referenced_keys(path)

    orphans = sorted(set(SWEDISH_LABELS) - referenced)
    assert not orphans, (
        f"{len(orphans)} labels are defined but never used: {orphans[:8]}"
    )


# ── The templates must be usable ─────────────────────────────────────
#
# Only the values actually passed through `str.format` need to be valid format
# strings. Applying that rule to every label would be wrong, not merely strict:
# `sc.version_c_realversion_beraknas_som_text` is a LaTeX formula whose braces
# are unparseable as a format string and perfectly correct as copy, because
# nothing ever formats it.


def _call_sites() -> tuple[set[str], set[str]]:
    """Split label keys by how they are called: with format values, or bare."""
    templated: set[str] = set()
    bare: set[str] = set()
    for path in _page_files() + sorted((ROOT / "src").rglob("*.py")):
        if path.name == "labels.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "L"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                (templated if node.keywords else bare).add(node.args[0].value)
    return templated, bare


def test_every_template_parses_and_names_its_fields() -> None:
    """A template that cannot format is a page that raises when someone opens it."""
    import string

    templated, _ = _call_sites()
    assert templated, "no templated labels found — has the call convention changed?"

    offenders = []
    for key in sorted(templated):
        try:
            fields = [field for _, field, _, _ in string.Formatter().parse(SWEDISH_LABELS[key])]
        except ValueError as exc:
            offenders.append((key, str(exc)))
            continue
        if any(field == "" for field in fields):
            offenders.append((key, "positional {} — breaks with two placeholders"))
    assert not offenders, f"unusable template: {offenders}"


def test_every_template_supplies_every_placeholder_it_declares() -> None:
    """A missing kwarg is a KeyError on render, not a blank."""
    import string

    templated, _ = _call_sites()
    declared: dict[str, set[str]] = {}
    for key in templated:
        declared[key] = {
            field.split(":")[0].split(".")[0].split("[")[0]
            for _, field, _, _ in string.Formatter().parse(SWEDISH_LABELS[key])
            if field
        }

    supplied: dict[str, set[str]] = {}
    dynamic: set[str] = set()
    for path in _page_files() + sorted((ROOT / "src").rglob("*.py")):
        if path.name == "labels.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "L"
                and node.keywords
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                key = node.args[0].value
                if any(kw.arg is None for kw in node.keywords):
                    # `L(key, **mapping)` — the names are not knowable from the
                    # syntax. Page 06 fills the methodology source table this way,
                    # and test_copy_matches_artifacts.py checks that call against
                    # the dict literal it unpacks. Nothing to assert here.
                    dynamic.add(key)
                    continue
                names = {kw.arg for kw in node.keywords if kw.arg}
                supplied.setdefault(key, set()).update(names)

    offenders = {
        key: sorted(declared[key] - supplied.get(key, set()))
        for key in declared
        if key not in dynamic and declared[key] - supplied.get(key, set())
    }
    assert not offenders, f"placeholder never supplied at any call site: {offenders}"


def test_labels_with_raw_braces_are_never_formatted() -> None:
    """The hazard the LaTeX formula represents, pinned.

    A value holding unescaped braces is fine while it is rendered directly. The
    day someone calls it with a value, `str.format` reads `{	ext{Inkomst}}` as a
    field name and raises. This catches that pairing rather than banning either
    half.
    """
    import string

    templated, _ = _call_sites()
    unparseable = set()
    for key, value in SWEDISH_LABELS.items():
        try:
            list(string.Formatter().parse(value))
        except ValueError:
            unparseable.add(key)

    collision = sorted(unparseable & templated)
    assert not collision, (
        f"these labels contain raw braces and are also formatted: {collision}"
    )


def test_the_guard_can_see_inline_copy(tmp_path: Path) -> None:
    """A detector that matches nothing would pass every page above."""
    sample = tmp_path / "page.py"
    sample.write_text(
        '"""A docstring mentioning Högrisk must NOT count."""\n'
        "import streamlit as st\n"
        "# A comment about Högrisk must not count either\n"
        'st.warning("Inga data tillgängliga")\n',
        encoding="utf-8",
    )
    found = _swedish_literals(sample)
    assert found == ["Inga data tillgängliga"], (
        f"expected exactly the inline string, got {found}"
    )
