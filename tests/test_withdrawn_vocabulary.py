"""The withdrawn statistical vocabulary must not reach a live surface.

R16 removed two fitted pipelines from the project. Removing the code was the easy
half. The hard half was that the vocabulary had leaked into places nobody thought
to grep: a page description in `app.py` that still announced the models by name, a
sentence on the landing page still advertising the capability, and a validation
checklist in `SWEDISH_LABELS` still promising confidence bands whose test had been
deleted. Each was found by a human reading the file, which is exactly the method
that had already missed them twice.

So this is the guard that method needed. It is deliberately blunt: a word list, and
a split between the surface a reader takes as current and the records that describe
what the project used to be.

**Historical records are exempt, but must prove they are historical.** A file cannot
buy its exemption by sitting in the list; `test_every_exempt_record_is_marked_as_one`
asserts each one carries a banner saying so. Without that, the exemption list would
become the place stale claims go to hide, which is the defect this file exists to
stop rather than a reasonable cost of preventing it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: The vocabulary of the withdrawn pipelines. `prognos` is the Swedish half: the
#: page's whole point is that it shows a *projektion* and not a *prognos*, so the
#: word appearing in rendered copy is a claim the project no longer makes.
WITHDRAWN = re.compile(
    r"forecast|arima|prophet|pmdarima|statsmodels|prognos", re.IGNORECASE
)

#: Records of what the project used to be. Each must carry a banner marking it as
#: such, which the test below enforces. `docs/archive/` is exempt wholesale, by the
#: same convention `test_prose_matches_artifacts.py` already applies to it.
EXEMPT_RECORDS = {
    "docs/PRD.md": "Superseded in part",
    "docs/PLAYBOOK.md": "Superseded in part",
    "docs/REVITALIZATION_PLAN.md": "Historical work record",
    "docs/OPTIMIZATION_PLAN.md": "Historical work record",
}


def _live_surface() -> list[Path]:
    """Everything a reader encounters as a statement about the project today."""
    paths = (
        sorted(ROOT.glob("*.py"))
        + sorted((ROOT / "src").rglob("*.py"))
        + sorted((ROOT / "pages").glob("*.py"))
        + sorted((ROOT / "tests").glob("*.py"))
        + sorted((ROOT / "scripts").glob("*.py"))
        + [ROOT / "README.md", ROOT / "pyproject.toml", ROOT / "requirements.txt"]
        + sorted(ROOT.glob("docs/*.md"))
    )
    exempt = {ROOT / p for p in EXEMPT_RECORDS}
    exempt.add(Path(__file__))  # this file has to name the words it forbids
    return [
        p for p in paths
        if p.exists() and p not in exempt and "archive" not in p.parts
    ]


@pytest.mark.parametrize("path", _live_surface(), ids=lambda p: p.name)
def test_no_withdrawn_vocabulary_on_the_live_surface(path: Path) -> None:
    offenders = [
        f"{n}: {line.strip()[:90]}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if WITHDRAWN.search(line)
    ]
    assert not offenders, (
        f"{path.relative_to(ROOT)} names a withdrawn statistical pipeline:\n  "
        + "\n  ".join(offenders)
        + "\n\nThe models were removed in R16. If this is a historical record rather "
        "than a current claim, it belongs in docs/archive/ or in EXEMPT_RECORDS with "
        "a banner."
    )


@pytest.mark.parametrize("relpath,marker", sorted(EXEMPT_RECORDS.items()))
def test_every_exempt_record_is_marked_as_one(relpath: str, marker: str) -> None:
    """An exemption without a banner is a stale document with a licence."""
    head = (ROOT / relpath).read_text(encoding="utf-8")[:1200]
    assert marker in head, (
        f"{relpath} is exempt from the vocabulary guard but carries no "
        f"'{marker}' banner near the top, so a reader has no way to know it "
        "describes a project state that no longer exists"
    )


def test_the_guard_would_catch_a_regression() -> None:
    """A negative control, because a word-list guard that matches nothing looks
    identical to one whose word list is wrong."""
    for probe in (
        'page_description = "Prognos per kommun med Prophet och ARIMA"',
        "pipeline = [\"pmdarima>=2.0.4\"]",
        "**Prognosintervall vidgas:** Konfidensband vidgas monotont.",
    ):
        assert WITHDRAWN.search(probe), f"the guard would not catch: {probe}"
