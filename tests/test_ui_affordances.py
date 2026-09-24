"""The explanation, glossary, vintage badge, filter and table components.

Finding M listed capabilities Skattekraftspanelen has and SHAI did not: prose
under every bare number, a glossary affordance, a visible data vintage, shared
filter logic and one table renderer. T3.4 through T3.9 added them. This file keeps
them wired, because a component nobody calls is the same as no component.

The reference repository is not available on this machine (see §0 of the plan), so
these were built from the task descriptions rather than matched against
Skattekraftspanelen's markup. What is asserted here is therefore *behaviour* — an
explanation exists under each number, the glossary is keyboard-reachable, the
vintage comes from the artifact — and not visual equivalence, which cannot be
checked without the reference.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd
import pytest

from src.ui.css import GLOBAL_CSS
from src.ui.data_table import Column, render_table
from src.ui.filters import RISK_CODES, RISK_LABEL_TO_CODE, RISK_LABELS, by_risk, risk_codes
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "app.py"] + sorted((ROOT / "pages").glob("*.py"))
EXPLAINED = {"app.py", "01_Riksoversikt.py", "02_Lan_jamforelse.py", "03_Kommun_djupanalys.py"}
WITH_EXPANDERS = {"01_Riksoversikt.py", "02_Lan_jamforelse.py", "03_Kommun_djupanalys.py"}


def _calls(path: Path, name: str) -> int:
    """Count calls to `name`, whether bare (`explanation(...)`) or attribute
    (`st.expander(...)`)."""
    total = 0
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == name:
            total += 1
        elif isinstance(func, ast.Attribute) and func.attr == name:
            total += 1
    return total


# ── T3.4 · explanation under every bare number ───────────────────────


@pytest.mark.parametrize(
    "page", [p for p in PAGES if p.name in EXPLAINED], ids=lambda p: p.name
)
def test_page_explains_its_numbers(page: Path) -> None:
    assert _calls(page, "explanation") >= 1, (
        f"{page.name} shows figures with no prose saying what they mean or what "
        "they cannot show"
    )


def test_explanation_style_exists() -> None:
    assert ".shai-explanation" in GLOBAL_CSS


def test_explanations_interpolate_rather_than_state_their_numbers() -> None:
    """A number typed into an explanation is T4.1's defect one layer down."""
    offenders = [
        key
        for key, value in SWEDISH_LABELS.items()
        if ("forklaring_kpi" in key or "forklaring_statistik" in key)
        and re.search(r"\b\d{3,4}\b", value)
    ]
    assert not offenders, f"explanation states a literal figure: {offenders}"


# ── T3.5 · glossary badge ────────────────────────────────────────────


def test_help_badge_renders_a_definition_list() -> None:
    from src.ui.components import help_badge

    html = help_badge("zpoang", "riskklass")
    assert "shai-help-mark" in html and "<dl>" in html
    assert SWEDISH_LABELS["glossary.zpoang.term"] in html
    assert SWEDISH_LABELS["glossary.riskklass.def"] in html


def test_help_badge_is_keyboard_reachable_and_labelled() -> None:
    """The `title=` tooltips this replaces are reachable by neither."""
    from src.ui.components import help_badge

    html = help_badge("zpoang")
    assert "<button" in html, "must be focusable, so not a bare span"
    assert "aria-label=" in html
    assert ":focus" in GLOBAL_CSS, "the popover must open on focus, not only hover"


def test_help_badge_is_empty_without_terms() -> None:
    from src.ui.components import help_badge

    assert help_badge() == ""


def test_unknown_glossary_term_fails_loudly() -> None:
    """A silent miss renders a question mark that explains nothing."""
    from src.ui.components import help_badge

    with pytest.raises(KeyError):
        help_badge("not_a_real_term")


def test_glossary_is_applied_to_the_map_distribution_and_ranking_cards() -> None:
    """T3.5 names three cards. Two was the state before this test existed."""
    page = (ROOT / "pages" / "01_Riksoversikt.py").read_text(encoding="utf-8")
    assert page.count("help_badge(") >= 3, (
        "the map, the distribution and the ranking tables each need the affordance"
    )


# ── T3.6 · data vintage badge ────────────────────────────────────────


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_every_page_shows_the_data_vintage(page: Path) -> None:
    assert _calls(page, "vintage_badge") >= 1, (
        f"{page.name} never shows how old its data is (Finding C)"
    )


def test_vintage_badge_reads_the_artifact_not_the_clock(monkeypatch) -> None:
    import src.ui.components as components
    from src.provenance import generated_at

    captured: list[str] = []
    monkeypatch.setattr(components.st, "markdown", lambda html, **_: captured.append(html))
    components.vintage_badge()
    assert generated_at()[:10] in captured[0]


def test_footer_note_takes_an_updated_argument() -> None:
    """Signature parity with the reference (T3.6)."""
    import inspect

    from src.ui.components import footer_note

    assert list(inspect.signature(footer_note).parameters) == ["source", "version", "updated"]


# ── T3.7 · one owner for filtering ───────────────────────────────────


def test_empty_risk_selection_means_all_in_one_place() -> None:
    assert risk_codes([]) == RISK_CODES
    assert risk_codes(None) == RISK_CODES
    assert risk_codes(["nonsense"]) == RISK_CODES, (
        "an unrecognised label must not filter everything away — that is how "
        "Finding A came to render a fabricated KPI"
    )


def test_risk_filter_selects_the_requested_classes() -> None:
    frame = pd.DataFrame({"risk_c": ["hog", "medel", "lag"]})
    assert list(by_risk(frame, ["Hög"])["risk_c"]) == ["hog"]
    assert len(by_risk(frame, list(RISK_LABELS))) == 3


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_no_page_maps_risk_labels_itself(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    assert not re.search(r"Hög[\"']\s*:\s*[\"']hog", text), (
        f"{page.name} repeats the risk label mapping; it belongs to filters.py"
    )


def test_the_sidebar_offers_exactly_the_labels_the_filter_understands() -> None:
    """A pill the filter cannot translate would silently mean 'all'."""
    sidebar = (ROOT / "src" / "ui" / "sidebar.py").read_text(encoding="utf-8")
    assert "RISK_LABELS" in sidebar, "the sidebar still hardcodes its own labels"
    assert set(RISK_LABELS) == set(RISK_LABEL_TO_CODE)


# ── T3.8 · one table renderer ────────────────────────────────────────


def test_render_table_produces_the_shared_markup() -> None:
    frame = pd.DataFrame({"n": [1], "name": ["Solna"]})
    html = render_table(
        frame,
        [
            Column("#", lambda row: str(row["n"]), kind="rank"),
            Column("Kommun", lambda row: row["name"], kind="name"),
            Column("Värde", lambda row: "1,0", numeric=True),
        ],
        title="T",
        tag="RANKING",
    )
    assert 'class="shai-table"' in html
    assert "shai-rank-cell" in html and "shai-kommun-name" in html
    assert html.count("shai-num") >= 2, "numeric header and cell both need alignment"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_no_page_builds_table_html_inline(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    assert "<table" not in text, f"{page.name} still builds table markup inline"
    assert "shai-rank-cell" not in text, (
        f"{page.name} names a table cell class; that belongs to data_table.py"
    )


# ── T3.9 · contextual expanders ──────────────────────────────────────


@pytest.mark.parametrize(
    "page", [p for p in PAGES if p.name in WITH_EXPANDERS], ids=lambda p: p.name
)
def test_page_has_contextual_expanders(page: Path) -> None:
    assert _calls(page, "expander") >= 1, f"{page.name} has no contextual expander"


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_expander_titles_come_from_labels(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    inline = re.findall(r"st\.expander\([\"']([^\"']+)[\"']", text)
    assert not inline, (
        f"{page.name} has inline expander titles {inline}; they belong in SWEDISH_LABELS"
    )
