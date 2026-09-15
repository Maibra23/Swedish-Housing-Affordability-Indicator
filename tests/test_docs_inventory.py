"""The docs directory must have one document per subject, all of them reachable.

Finding L was documentation duplicated and partly false: `METHODOLOGY.md` beside
`METHODOLOGY_v2.md`, `PLAYBOOK.md` beside `PLAYBOOK_v2.md`, four build-time
artifacts with no reader, and a `DESIGN_SYSTEM.md` describing a Plotly map that
Folium replaced. A reader opening the wrong one of a pair gets confidently wrong
answers, and nothing in the repo indicated which was current.

T4.6 resolved it by deleting the superseded halves, renaming the survivors to
drop `_v2`, and moving artifacts with no reader to `docs/archive/`. This guards
the result: a `_v2` suffix cannot come back, every maintained document is linked
from the README, and nothing outside the archive points into it as current
guidance.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARCHIVE = DOCS / "archive"
README = ROOT / "README.md"


def _maintained() -> list[Path]:
    return sorted(p for p in DOCS.glob("*.md"))


def test_no_version_suffix_remains() -> None:
    """A `_v2` file implies a `_v1` somewhere, which is the ambiguity itself."""
    suffixed = [p.name for p in DOCS.rglob("*.md") if re.search(r"_v\d+\.md$", p.name)]
    assert not suffixed or all(ARCHIVE in p.parents for p in DOCS.rglob("*_v*.md")), (
        f"versioned filenames outside the archive: {suffixed}"
    )


def test_every_maintained_doc_is_linked_from_the_readme() -> None:
    """A document nobody can find is a document nobody updates."""
    readme = README.read_text(encoding="utf-8")
    unlinked = [p.name for p in _maintained() if f"docs/{p.name}" not in readme]
    assert not unlinked, f"maintained docs missing from the README index: {unlinked}"


def test_readme_links_no_document_that_does_not_exist() -> None:
    readme = README.read_text(encoding="utf-8")
    broken = [
        ref
        for ref in re.findall(r"docs/(?:archive/)?[A-Za-z0-9_]+\.md", readme)
        if not (ROOT / ref).exists()
    ]
    assert not broken, f"the README links documents that do not exist: {broken}"


def test_no_maintained_doc_is_superseded_by_another() -> None:
    """Two files whose names differ only by a version marker describe one subject."""
    stems = {}
    for path in _maintained():
        base = re.sub(r"_v\d+$", "", path.stem).lower()
        stems.setdefault(base, []).append(path.name)
    duplicated = {k: v for k, v in stems.items() if len(v) > 1}
    assert not duplicated, f"more than one document per subject: {duplicated}"


@pytest.mark.parametrize(
    "path",
    [p for p in (ROOT / "src").rglob("*.py")] + [p for p in (ROOT / "scripts").rglob("*.py")],
    ids=lambda p: p.name,
)
def test_code_never_cites_an_archived_or_deleted_document(path: Path) -> None:
    """A docstring pointing at a deleted file is worse than no pointer."""
    text = path.read_text(encoding="utf-8")
    dangling = [
        ref
        for ref in re.findall(r"docs/(?:archive/)?[A-Za-z0-9_]+\.md", text)
        if not (ROOT / ref).exists()
    ]
    assert not dangling, f"{path.name} cites missing documents: {dangling}"


def test_the_archive_is_marked_as_unmaintained() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "docs/archive/" in readme and "not maintained" in readme, (
        "the README must say the archive is not current guidance, or a reader will "
        "treat a superseded analysis as live"
    )
