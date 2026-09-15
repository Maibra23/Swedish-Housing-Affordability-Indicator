"""Pages must not recompute z-scores, ranks or risk classes.

`src/indices/normalize.py` owns the orientation contract (rank 1 = best,
hog = least affordable) and writes `affordability_ranked.parquet`. When a page
re-derives any of those columns it can — and once did — drop the sign inversion
that A and C require, which rendered the national map with green over Stockholm
and red over inland Norrland for every year except 2014. See Finding N in
docs/REVITALIZATION_PLAN.md.

These are source-level assertions rather than behavioural ones because the
defect is structural: the moment a page owns a second copy of this logic, the
two copies can disagree. The only way to keep them in agreement is for there to
be one.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PAGES_DIR = Path(__file__).resolve().parents[1] / "pages"

# The class boundary in normalize.py. A page that mentions it is re-deriving a
# classification the artifact already carries.
CLASS_BOUNDARY = "0.67"

# Signatures of the three computations the artifact owns.
#
# These target the contract, not descriptive statistics in general. A page may
# legitimately call .std() or .mean() — 03_Kommun_djupanalys computes a
# coefficient of variation across one municipality's own time series to pick
# the most volatile component. What it may not do is build a cross-sectional
# z-score, a rank, or a risk class, because those three carry an orientation
# that only normalize.py applies.
RECOMPUTE_PATTERNS = {
    "rank": re.compile(r"\.rank\s*\(", re.MULTILINE),
    "risk binning": re.compile(r"pd\.cut\s*\(", re.MULTILINE),
    # The (value - mean) / std shape, in either spelling.
    "z-score": re.compile(r"-\s*[\w\[\]\"'.]*\.?mean\s*\(\s*\)\s*\)?\s*/", re.MULTILINE),
    # Writing any contract column directly.
    "contract column assignment": re.compile(
        r"""\[\s*["'](?:z|rank|risk)_[abc]["']\s*\]\s*=(?!=)""", re.MULTILINE
    ),
}


def _page_files() -> list[Path]:
    return sorted(p for p in PAGES_DIR.glob("*.py") if not p.name.startswith("_"))


def _strip_comments(source: str) -> str:
    """Drop whole-line and trailing comments.

    Prose explaining why a page does *not* recompute is not a recomputation,
    and must not trip these assertions.
    """
    return "\n".join(re.sub(r"#.*$", "", line) for line in source.splitlines())


def test_pages_directory_is_not_empty():
    """Guard the guard: an empty glob would make every test below vacuous."""
    assert _page_files(), f"No page modules found under {PAGES_DIR}"


@pytest.mark.parametrize("page", _page_files(), ids=lambda p: p.name)
def test_page_does_not_mention_class_boundary(page: Path):
    code = _strip_comments(page.read_text(encoding="utf-8"))
    assert CLASS_BOUNDARY not in code, (
        f"{page.name} hardcodes the {CLASS_BOUNDARY} class boundary. Risk "
        f"classes live in the `risk_*` columns of affordability_ranked.parquet; "
        f"read them instead of re-deriving the cut."
    )


@pytest.mark.parametrize("page", _page_files(), ids=lambda p: p.name)
def test_page_does_not_recompute_scores(page: Path):
    code = _strip_comments(page.read_text(encoding="utf-8"))
    found = [name for name, pat in RECOMPUTE_PATTERNS.items() if pat.search(code)]
    assert not found, (
        f"{page.name} appears to recompute {', '.join(found)}. "
        f"src/indices/normalize.py is the only producer of z_*, rank_* and "
        f"risk_*; pages read them from affordability_ranked.parquet."
    )


def test_normalize_is_not_imported_by_any_page():
    """Pages read the artifact; they do not invoke the scorer themselves."""
    offenders = [
        page.name
        for page in _page_files()
        if "indices.normalize" in page.read_text(encoding="utf-8")
    ]
    assert not offenders, (
        f"{offenders} import indices.normalize. Scoring happens once, in the "
        f"refresh pipeline; pages consume affordability_ranked.parquet."
    )
