"""Figures quoted in docstrings and markdown, re-derived from the artifacts.

`test_copy_matches_artifacts.py` polices `SWEDISH_LABELS`. That is where the copy
a user reads lives, so it was the right place to start, and it works: it caught
the Version B panel means the moment the income source changed on 2026-09-21.

**It caught exactly one of six.** The same figures were quoted in
`src/indices/normalize.py`'s module docstring, in `docs/METHODOLOGY.md`, twice in
`docs/REVITALIZATION_PLAN.md`, and — least comfortably — twice inside
`test_copy_matches_artifacts.py`'s own docstring and comments. All five survived
the refresh, silently, because nothing reads prose outside the label dictionary.

That is the same defect this project has been chasing since Findings A, C and H,
which were "prose asserting a number the data no longer supported". The label
dictionary was hardened and the rest of the repository was not.

**What this guards, and what it cannot.** A general prose checker is not
possible: most numbers in a docstring are parameters, thresholds or worked
examples with no artifact behind them. What is checkable is a *shape* that only
ever means one thing here — a signed decimal attached to a year, as in the D5
panel-mean claim. Every occurrence of that shape, anywhere in the repository, is
re-derived from `affordability_ranked.parquet`.

Verified when written: the pattern matches the Version B claims and nothing else
across every markdown file and Python module in the project.

**Historical entries are exempt by construction.** The session log in
`docs/REVITALIZATION_PLAN.md` records what was true on a past date, and rewriting
it would destroy the record. Those rows are excluded by their table shape rather
than by an allowlist, so a new log entry needs no maintenance here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_ranked.parquet"

#: A signed decimal bound to a year: "-0.31 (2015)", "+0,78 (2023)",
#: "-0.31 in 2015". In this repository that shape is always a claim about
#: Version B's panel mean for that year.
PANEL_MEAN_CLAIM = re.compile(
    r"([−+\-]\d+[.,]\d+)\s*(?:\((\d{4})\)|in\s+(\d{4}))"
)

#: Lines that record what was true on a date. Rewriting them would destroy the
#: record rather than correct it. Matched by shape — a session-log table row —
#: so adding a log entry needs no change here.
HISTORICAL_ROW = re.compile(r"^\s*\|\s*20\d{2}-\d{2}-\d{2}\s*\|")

#: Where prose lives. `docs/archive/` is excluded for the same reason as the
#: session log: it is a record of superseded documents.
def _scanned_files() -> list[Path]:
    paths = (
        [ROOT / "README.md"]
        + sorted(ROOT.glob("docs/*.md"))
        + sorted(ROOT.glob("src/**/*.py"))
        + sorted(ROOT.glob("pages/*.py"))
        + sorted(ROOT.glob("tests/*.py"))
    )
    return [p for p in paths if "archive" not in p.parts and "__pycache__" not in p.parts]


def _prose(path: Path) -> str:
    """File text with history dropped and wrapped lines rejoined.

    Rejoining matters: `labels.py` wraps the D5 sentence mid-claim, so a
    line-by-line scan saw "-0,31 (2015)" and missed "+0,78 (2023)" entirely. A
    guard that reads half a sentence is worse than none, because it looks like
    coverage.
    """
    kept = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not HISTORICAL_ROW.match(line)
    ]
    return re.sub(r"\s+", " ", " ".join(kept))


@pytest.fixture(scope="module")
def panel_means() -> pd.Series:
    """Version B's panel mean per year, from the committed artifact."""
    ranked = pd.read_parquet(ARTIFACT)
    return ranked.groupby("year")["version_b"].mean()


def _as_float(text: str) -> float:
    return float(text.replace("−", "-").replace(",", "."))


def _claims() -> list[tuple[Path, str, str]]:
    found = []
    for path in _scanned_files():
        for match in PANEL_MEAN_CLAIM.finditer(_prose(path)):
            value, year_paren, year_in = match.groups()
            found.append((path, value, year_paren or year_in))
    return found


def test_the_pattern_still_finds_the_claims_it_was_written_for() -> None:
    """A scanner that matches nothing passes every assertion beneath it.

    If the D5 sentence is ever rewritten out of the project this test fails, and
    that is the right outcome: it means the guard below is inert and someone
    should decide whether it still earns its place.
    """
    claims = _claims()
    assert len(claims) >= 6, (
        f"found only {len(claims)} panel-mean claims in prose; the pattern has "
        f"stopped matching the text it guards"
    )
    files = {path.name for path, _, _ in claims}
    assert "METHODOLOGY.md" in files
    assert "labels.py" in files


@pytest.mark.parametrize(
    "path,value,year",
    _claims(),
    ids=lambda v: v.name if isinstance(v, Path) else str(v),
)
def test_a_quoted_panel_mean_matches_the_artifact(
    path: Path, value: str, year: str, panel_means: pd.Series
) -> None:
    """Every "signed decimal (year)" in the repo is checked against the data.

    The precision of the claim sets the tolerance: prose quoting two decimals is
    held to two decimals, so tightening a sentence does not silently loosen its
    guard.
    """
    year_int = int(year)
    assert year_int in panel_means.index, (
        f"{path.relative_to(ROOT)} quotes a panel mean for {year}, which the "
        f"index does not cover"
    )

    decimals = len(value.replace("−", "-").replace(",", ".").split(".")[1])
    actual = round(float(panel_means[year_int]), decimals)
    claimed = _as_float(value)
    assert claimed == pytest.approx(actual, abs=10 ** -decimals / 2), (
        f"{path.relative_to(ROOT)} says Version B's panel mean was {value} in "
        f"{year}; the artifact says {actual:+.{decimals}f}. Prose outside "
        f"SWEDISH_LABELS is not interpolated, so it has to be corrected by hand "
        f"when the data moves."
    )


def test_the_guard_would_catch_a_drifted_figure(panel_means: pd.Series) -> None:
    """The negative control, since every assertion above currently passes.

    Constructed rather than sampled: the check must fail on a wrong figure, not
    merely pass on the right ones.
    """
    year = int(panel_means.index.max())
    actual = round(float(panel_means[year]), 2)
    drifted = f"{actual + 0.5:+.2f}".replace("+", "+")
    assert _as_float(drifted) != pytest.approx(actual, abs=0.005)
    assert PANEL_MEAN_CLAIM.search(f"panel mean ran {drifted} ({year})"), (
        "the pattern no longer recognises the shape it is meant to catch"
    )
