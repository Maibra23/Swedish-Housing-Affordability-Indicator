"""The risk-class KPI must not be dressed up as a national trend.

Risk classes are cut at ±0.67 standard deviations of a *within-year* z-score
(D5), so the share of municipalities in each class is near-constant by
construction — the 2024 split is roughly 23/48/28 and every other year lands
within a few points of it. A year-on-year delta on that count therefore measures
sampling wobble around a fixed boundary, not whether Sweden became more or less
affordable. Rendering it with an arrow told the reader the opposite.

See Finding F and Finding Q in docs/REVITALIZATION_PLAN.md, and task T1.9.

These are source-level assertions. The defect is not a wrong number that a
behavioural test could pin down — the count itself is correct. The defect is
attaching a *comparison* to a quantity that cannot support one, which lives in
the shape of the call, so that is what is asserted.

One constraint comes from D6: the copy here must not quote a class-split figure.
The log transform moved the split once already (≈19/51/30 → ≈23/48/28) and any
number hardcoded into a label will drift again the next time the transform or
the panel changes.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from tests.sourcetools import executable_source

PAGE = Path(__file__).resolve().parents[1] / "pages" / "01_Riksoversikt.py"


@pytest.fixture(scope="module")
def tree() -> ast.Module:
    return ast.parse(executable_source(PAGE.read_text(encoding="utf-8")))


# ── Locating the KPI without hardcoding its wording ───────────────────


def _risk_count_names(tree: ast.Module) -> set[str]:
    """Names bound to — or derived from — a count of municipalities by risk class.

    Found structurally rather than by name so the test keeps working when the
    variable is renamed: any assignment whose right-hand side both mentions a
    `risk_*` column and reduces it to a number.

    The set is then closed over assignment: `delta = n_hog - n_hog_prev` never
    mentions `risk_c` itself, and a guard that stopped at the direct binding
    would wave through exactly the subtraction this task exists to remove.
    """
    assignments = [
        (
            {t.id for t in node.targets if isinstance(t, ast.Name)},
            ast.unparse(node.value),
            {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)},
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
    ]

    names = {
        target
        for targets, source, _ in assignments
        for target in targets
        if "risk_" in source and re.search(r"\.(sum|count)\s*\(|\blen\s*\(", source)
    }

    grew = True
    while grew:
        grew = False
        for targets, _, referenced in assignments:
            if referenced & names and not targets <= names:
                names |= targets
                grew = True
    return names


def _kpi_calls(tree: ast.Module) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "kpi_card"
    ]


def _kwarg(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _risk_kpi(tree: ast.Module) -> ast.Call:
    """The one KPI card whose value is a risk-class count."""
    counts = _risk_count_names(tree)
    assert counts, "no variable on the page counts municipalities by risk class"

    matches = [
        call
        for call in _kpi_calls(tree)
        if (value := _kwarg(call, "value")) is not None
        and counts & {n.id for n in ast.walk(value) if isinstance(n, ast.Name)}
    ]
    assert len(matches) == 1, (
        f"expected exactly one KPI card built from a risk-class count, found {len(matches)}"
    )
    return matches[0]


def _literal(node: ast.expr | None) -> str:
    """Flatten a kwarg to text, tolerating f-strings and implicit concatenation."""
    if node is None:
        return ""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return " ".join(
        n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )


# ── Acceptance: no YoY delta on any count from the ±0.67σ cut ─────────


def test_risk_class_kpi_carries_no_delta(tree: ast.Module) -> None:
    delta = _kwarg(_risk_kpi(tree), "delta")
    assert delta is None or (isinstance(delta, ast.Constant) and not delta.value), (
        "the high-risk count must not render a delta: the class boundary is a "
        "within-year quantile, so the count cannot move for the reason an arrow implies"
    )


def test_page_never_reads_a_risk_class_for_the_previous_year(tree: ast.Module) -> None:
    """Without last year's classes there is no delta to accidentally reintroduce."""
    offenders = [
        source
        for node in ast.walk(tree)
        if isinstance(node, (ast.Compare, ast.Subscript, ast.Call))
        and "risk_" in (source := ast.unparse(node))
        and "prev" in source
    ]
    assert not offenders, (
        "the page still derives a previous-year risk class: " + "; ".join(sorted(set(offenders))[:3])
    )


def test_no_kpi_delta_is_built_from_a_class_count(tree: ast.Module) -> None:
    """Any KPI that does carry a trend must read a level series instead."""
    counts = _risk_count_names(tree)
    offenders = []
    for call in _kpi_calls(tree):
        delta = _kwarg(call, "delta")
        if delta is None:
            continue
        names = {n.id for n in ast.walk(delta) if isinstance(n, ast.Name)}
        if counts & names:
            offenders.append(ast.unparse(delta))
    assert not offenders, f"KPI delta derived from a risk-class count: {offenders}"


# ── Acceptance: the label states it is a relative position ───────────


def test_risk_class_kpi_is_labelled_as_a_relative_position(tree: ast.Module) -> None:
    card = _risk_kpi(tree)
    copy = " ".join(
        _literal(_kwarg(card, key)) for key in ("label", "unit", "tooltip")
    ).lower()

    assert "relativ position" in copy, (
        "label, unit or tooltip must say the class is a relative position, not a level"
    )
    assert "året" in copy or "inom år" in copy, (
        "the copy must scope the comparison to within the year"
    )


def test_risk_class_kpi_tooltip_explains_the_within_year_cut(tree: ast.Module) -> None:
    tooltip = _literal(_kwarg(_risk_kpi(tree), "tooltip")).lower()
    assert tooltip, "the high-risk KPI must keep a tooltip"
    assert "relativ position" in tooltip, "the tooltip itself must carry the caveat"


def test_risk_class_kpi_quotes_no_split_figure(tree: ast.Module) -> None:
    """D6: any hardcoded split drifts the next time the transform changes."""
    copy = " ".join(_literal(_kwarg(_risk_kpi(tree), key)) for key in ("label", "unit", "tooltip"))

    percentages = re.findall(r"\d+(?:[.,]\d+)?\s*%", copy)
    assert not percentages, f"class-split percentage quoted in the KPI copy: {percentages}"

    splits = re.findall(r"\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{1,2}", copy)
    assert not splits, f"class-split ratio quoted in the KPI copy: {splits}"


# ── The count is national, not a readout of the sidebar filter ───────


def test_risk_count_is_not_read_from_the_risk_filtered_frame(tree: ast.Module) -> None:
    """"N of 290" has to mean N of 290.

    The other three cards in this row read the unfiltered year. This one read
    the frame the risk pills had already filtered, so deselecting "Hög" made the
    national high-risk count render as 0 — a filter state presented as a fact
    about Sweden.
    """
    filtered = {
        target
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and re.search(r"isin\s*\(|selected_risks", ast.unparse(node.value))
        for target in (t.id for t in node.targets if isinstance(t, ast.Name))
    }
    assert filtered, "could not locate the risk-filtered frame on the page"

    offenders = [
        ast.unparse(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and {t.id for t in node.targets if isinstance(t, ast.Name)} & _risk_count_names(tree)
        and filtered & {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
    ]
    assert not offenders, f"national risk count read from the filtered frame: {offenders}"


# ── Regression guard: the count itself must survive ──────────────────


def test_high_risk_count_is_still_displayed(tree: ast.Module) -> None:
    """T1.9 removes the comparison, not the cross-sectional fact."""
    value = _literal(_kwarg(_risk_kpi(tree), "value"))
    names = {
        n.id
        for n in ast.walk(_kwarg(_risk_kpi(tree), "value"))
        if isinstance(n, ast.Name)
    }
    assert names & _risk_count_names(tree), "the high-risk count is no longer rendered"
    del value
