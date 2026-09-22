"""The year selector must offer exactly the years the index can compute.

`YEAR_RANGE` used to run `range(2020, date.today().year + 1)` — 2020 through
2026 — while the affordability index stops at 2024. Picking 2025 or 2026 sent
every page to `st.stop()` with "Inga data tillgängliga", so two of seven
selectable years were dead (Finding B). The sidebar footer separately printed
`date.today()`, so a visitor read "Senast uppdaterad: 2026-09-15" above data
built from 2024 figures (Finding C).

Both ends of the range and the vintage now come from the provenance artifact.
These tests pin that: they re-derive the range from the artifacts the pages
actually read, so adding a year of data moves the selector with no code edit,
and failing to add one cannot leave a dead year on screen.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from sourcetools import executable_source

from src import provenance
from src.ui import sidebar

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
SIDEBAR_PATH = PROJECT_ROOT / "src" / "ui" / "sidebar.py"
SIDEBAR_SOURCE = SIDEBAR_PATH.read_text(encoding="utf-8")


SIDEBAR_CODE = executable_source(SIDEBAR_SOURCE)

#: Artifacts a page filters by the selected year. If any lacks the year, that
#: page renders empty or stops.
YEAR_GATED_ARTIFACTS = (
    "affordability_ranked",      # 01_Riksoversikt
    "affordability_municipal",   # 02, 03, 04
    "panel_county",              # 02, 04, 05
)


# ── T1.4 — the range comes from provenance ───────────────────────────


def test_year_range_spans_the_index():
    assert sidebar.YEAR_RANGE == list(
        range(provenance.first_year(), provenance.complete_case_max_year() + 1)
    )


def test_year_range_ends_at_the_complete_case_year():
    assert sidebar.YEAR_RANGE[-1] == provenance.complete_case_max_year()


@pytest.mark.parametrize("dead_year", [2025, 2026])
def test_dead_years_are_not_offered(dead_year: int):
    """The panel reaches these years but the index cannot compute them."""
    assert dead_year <= provenance.panel_max_year(), "test premise stale"
    assert dead_year not in sidebar.YEAR_RANGE


def test_no_literal_year_remains_in_sidebar():
    """A hardcoded year is how the range drifted away from the data before."""
    literals = re.findall(r"\b(?:19|20)\d{2}\b", SIDEBAR_CODE)
    assert not literals, (
        f"sidebar.py still hardcodes {sorted(set(literals))}; read the years "
        f"from src.provenance instead."
    )


@pytest.mark.parametrize("artifact", YEAR_GATED_ARTIFACTS)
def test_every_offered_year_has_data(artifact: str):
    """No offered year may be missing from an artifact a page filters."""
    frame = pd.read_parquet(DATA_DIR / f"{artifact}.parquet")
    available = set(frame["year"].unique())
    missing = [y for y in sidebar.YEAR_RANGE if y not in available]
    assert not missing, (
        f"{artifact}.parquet has no rows for {missing}, but the sidebar offers "
        f"those years. Selecting one renders an empty page."
    )


def test_offered_years_are_fully_populated():
    """Every offered year must carry all 290 municipalities, not a partial slice."""
    ranked = pd.read_parquet(DATA_DIR / "affordability_ranked.parquet")
    counts = ranked[ranked["year"].isin(sidebar.YEAR_RANGE)].groupby("year").size()
    expected = provenance.n_kommuner()
    short = counts[counts != expected]
    assert short.empty, f"years with fewer than {expected} municipalities:\n{short}"


def test_no_offered_year_carries_imputed_income():
    """Every selectable year is observed data, not forward-filled.

    This is what makes the "Imputerat inkomstår" banners dead code: imputation
    starts the year after the last published income, and the selector now stops
    there.
    """
    panel = pd.read_parquet(DATA_DIR / "panel_municipal.parquet")
    offered = panel[panel["year"].isin(sidebar.YEAR_RANGE)]
    imputed = sorted(offered.loc[offered["is_imputed_income"].astype(bool), "year"].unique())
    assert not imputed, f"the selector offers forward-filled years: {imputed}"


def test_default_year_is_the_latest_offered():
    assert sidebar.default_year() == sidebar.YEAR_RANGE[-1]
    assert sidebar.default_year() == provenance.complete_case_max_year()


# ── T1.5 — the footer states the data vintage ────────────────────────


def test_sidebar_never_calls_date_today():
    assert "date.today()" not in SIDEBAR_CODE, (
        "the footer must show when the data was generated, not when the page "
        "was rendered"
    )


def test_data_vintage_comes_from_the_artifact():
    assert sidebar.data_vintage() == provenance.generated_at()[:10]


def test_footer_shows_the_vintage_not_today():
    html = sidebar.footer_html()
    assert sidebar.data_vintage() in html
    today = date.today().strftime("%Y-%m-%d")
    if today != sidebar.data_vintage():
        assert today not in html, "footer is printing the render date"


def test_footer_drops_the_forward_fill_note():
    """Imputed years are unreachable once T1.4 lands, so the note misleads."""
    html = sidebar.footer_html()
    for stale in ("modellberäknad", "+3%/år", "Inkomst 2025"):
        assert stale not in html, f"footer still claims {stale!r}"


def test_footer_still_credits_the_sources():
    html = sidebar.footer_html()
    for source in ("SCB", "Riksbanken", "Kolada"):
        assert source in html


# ---------------------------------------------------------------------------
# R2: no page derives its own year list
# ---------------------------------------------------------------------------

#: A page asking a dataframe which years exist. The sidebar has read provenance
#: since T1.4; three pages kept doing this themselves, each from whichever frame
#: happened to be loaded. On two of them the frame was a *panel*, which runs past
#: the last year the index can be computed for, so the "pick another year"
#: fallback offered years that render blank.
DERIVES_YEARS = re.compile(r"\[[\"']year[\"']\]\s*\.unique\(\)")


def test_no_page_derives_its_own_year_list() -> None:
    """R2, closed. One accessor, and prose cannot drift from it.

    `selectable_years()` resolves the index period from provenance. A page that
    computes its own is not wrong today only because the data happens to agree;
    it is wrong the moment a component series is published ahead of income,
    which is the normal state of this panel.
    """
    offenders: list[str] = []
    for path in sorted(PROJECT_ROOT.glob("pages/*.py")) + [PROJECT_ROOT / "app.py"]:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if DERIVES_YEARS.search(line):
                offenders.append(f"{path.name}:{line_no} {line.strip()}")
    assert not offenders, (
        "pages deriving their own year list: "
        + "; ".join(offenders)
        + ". Use src.provenance.selectable_years()."
    )


def test_selectable_years_is_the_index_period() -> None:
    """And it is the period, not the panel: the two differ by design."""
    from src.provenance import (
        complete_case_max_year,
        first_year,
        panel_max_year,
        selectable_years,
    )

    years = selectable_years()
    assert years[0] == first_year()
    assert years[-1] == complete_case_max_year()
    assert years == sorted(set(years)), "years must be unique and ordered"
    assert panel_max_year() >= years[-1], (
        "the panel no longer reaches at least as far as the index; if that is "
        "real, the ragged-panel reasoning in src/provenance.py needs revisiting"
    )


def test_selectable_years_covers_what_the_artifact_holds() -> None:
    """The accessor and the scored data must not disagree about the period."""
    import pandas as pd

    from src.provenance import selectable_years

    ranked = pd.read_parquet(
        PROJECT_ROOT / "data" / "processed" / "affordability_ranked.parquet"
    )
    assert set(ranked["year"].unique()) == set(selectable_years())
