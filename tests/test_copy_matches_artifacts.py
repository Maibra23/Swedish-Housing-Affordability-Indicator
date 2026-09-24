"""Every number the UI states must be re-derivable from the committed artifacts.

Findings A, C and H were one defect wearing three coats: prose asserting a number
the data no longer supported. A said 2014 had no risk classes while the page
rendered a count for it; C claimed freshness from `date.today()`; H typed `290`
and `2014–2024` into nineteen places. Each was fixed. None of those fixes stops
the *next* sentence going stale, because prose has no way of noticing that the
data moved underneath it.

This file is that mechanism, and it found live drift on its first run: the T2.4
refresh advanced four component series to 2025 while the methodology source table
still said 2024 for all four. Nothing else in the suite noticed, because nothing
else was reading prose.

**Two kinds of assertion, because there are two kinds of number.**

*Derivable* values — per-source coverage years, the index period, municipality
counts — are now interpolated from provenance at render time. For those,
comparing copy to data would be tautological, so what is guarded instead is that
they stay derived: a re-introduced literal fails `test_*_is_not_hardcoded`. This
is the stronger position. Drift becomes impossible rather than merely detected.

*Non-derivable* values — a forecast horizon, a regulatory threshold, an editorial
aside like "typisk 2024 bankmarknad" — cannot be read from an artifact. Those are
compared where an artifact knows something adjacent, and otherwise classified by
`NOT_A_VINTAGE` so a new one cannot quietly join them unexamined.
"""

from __future__ import annotations

import re
import string
from pathlib import Path

import pytest

from src.provenance import (
    complete_case_max_year,
    first_year,
    n_kommuner,
    source_coverage,
)
from src.ui.labels import SWEDISH_LABELS
from src.ui.templates import TEMPLATES

#: Everything a reader sees, both dictionaries. R9 moved ten markup blocks out of
#: `SWEDISH_LABELS` and into `TEMPLATES`, and two of them are the regime tables,
#: which are dense with years. Scanning only the copy dictionary after that split
#: would have quietly narrowed this guard to the strings that happen not to carry
#: markup — prose wrapped in a `<div>` goes stale exactly as easily.
ALL_COPY: dict[str, str] = {**SWEDISH_LABELS, **TEMPLATES}

ARTIFACT = Path(__file__).resolve().parents[1] / "data" / "processed" / "affordability_ranked.parquet"

TABLE_KEY = "mt.variabel_symbol_kalla_upplosning_frekvens"

# Series whose upper bound the table states and the artifact records.
#
# `bostadsratt_price_sek` is deliberately absent: its panel column is
# forward-filled into the imputed tail, so its artifact max year (2026) is not a
# publication date and the table honestly says "2000–present" instead.
SOURCE_ROWS = {
    "median_income": ("Medianinkomst", "income_max"),
    "transaction_price_sek": ("Transaktionspris småhus", "price_max"),
    "price_index": ("Fastighetsprisindex", "price_index_max"),
    "kt_ratio": ("Köpeskillingskoefficient", "kt_max"),
    "unemployment_rate": ("Arbetslöshet", "unemployment_max"),
    "population": ("Befolkning", "population_max"),
    "completions": ("Bostadsbyggande", "completions_max"),
}


def _placeholders(value: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(value) if field}


def _rendered_table() -> str:
    """The source table as a reader sees it, filled from the artifact."""
    coverage = source_coverage()
    values = {
        placeholder: coverage[column]["max_year"]
        for column, (_, placeholder) in SOURCE_ROWS.items()
    }
    return SWEDISH_LABELS[TABLE_KEY].format(**values)


def _row(text: str, needle: str) -> str:
    for line in text.splitlines():
        if needle in line:
            return line
    raise AssertionError(f"no table row mentioning {needle!r}")


# ── Derivable values must stay derived ───────────────────────────────


@pytest.mark.parametrize("column,spec", SOURCE_ROWS.items())
def test_source_row_upper_bound_is_not_hardcoded(column: str, spec: tuple[str, str]) -> None:
    """A literal year here is the defect; a placeholder makes drift impossible."""
    needle, placeholder = spec
    row = _row(SWEDISH_LABELS[TABLE_KEY], needle)
    assert "{" + placeholder + "}" in row, (
        f"the {needle!r} row states its upper bound as a literal: {row.strip()[:120]}. "
        f"Use {{{placeholder}}} so it is read from the provenance artifact."
    )
    assert placeholder in _placeholders(SWEDISH_LABELS[TABLE_KEY])


@pytest.mark.parametrize("column,spec", SOURCE_ROWS.items())
def test_rendered_source_row_states_the_artifact_value(column: str, spec: tuple[str, str]) -> None:
    """Round-trip: the filled template must actually show the artifact's year."""
    needle, _ = spec
    expected = source_coverage()[column]["max_year"]
    row = _row(_rendered_table(), needle)
    spans = re.findall(r"(\d{4})\s*[–—-]\s*(\d{4}|idag|present)", row)
    assert spans, f"row for {needle!r} states no coverage span: {row.strip()[:120]}"
    _, upper = spans[-1]
    assert upper.isdigit() and int(upper) == expected, (
        f"the rendered table says {needle} ends {upper}; the artifact says {expected}"
    )


def test_every_source_placeholder_is_supplied_by_the_page() -> None:
    """A placeholder the page forgets is a KeyError when someone opens Metodologi."""
    import ast

    page = Path(__file__).resolve().parents[1] / "pages" / "06_Metodologi.py"
    tree = ast.parse(page.read_text(encoding="utf-8"))
    supplied: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            supplied |= {
                k.value
                for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
    missing = _placeholders(SWEDISH_LABELS[TABLE_KEY]) - supplied
    assert not missing, f"page 06 never supplies: {sorted(missing)}"


# ── Non-derivable values, compared where the artifact knows ──────────


def test_index_period_spans_in_copy_match_provenance() -> None:
    """Any `<first_year>–<yyyy>` span is the index period and must end where it does."""
    start, end = first_year(), complete_case_max_year()
    offenders = []
    for key, value in ALL_COPY.items():
        for lower, upper in re.findall(r"(\d{4})\s*[–—-]\s*(\d{4})", value):
            if int(lower) == start and int(upper) != end:
                offenders.append((key, f"{lower}–{upper}"))
    assert not offenders, (
        f"copy states an index period ending elsewhere than {end}: {offenders}"
    )


def test_forecast_base_year_matches_the_index_end() -> None:
    """"Framskrivet från X" must name the last year the index actually covers."""
    end = complete_case_max_year()
    offenders = [
        (key, match.group(1))
        for key, value in ALL_COPY.items()
        for match in re.finditer(r"[Ff]ramskrivet från\s*(\d{4})", value)
        if int(match.group(1)) != end
    ]
    assert not offenders, (
        f"copy projects from a year other than the index end ({end}): {offenders}. "
        "The forecast trains to complete_case_max_year()."
    )


def test_municipality_counts_in_copy_match_the_panel() -> None:
    """A bare count of municipalities must be the panel's count.

    Parenthesised source-table counts like `Kommun (312)` are excluded: they
    record how many regions SCB publishes for that series, not how many the
    index covers.
    """
    expected = n_kommuner()
    offenders = [
        (key, match.group(1))
        for key, value in ALL_COPY.items()
        for match in re.finditer(r"(?<!\()\b(\d{3})\s+kommun", value)
        if int(match.group(1)) != expected
    ]
    assert not offenders, (
        f"copy states a municipality count other than {expected}: {offenders}"
    )


def test_the_d5_panel_mean_statistic_still_holds() -> None:
    """Methodology prose cites measured extremes as the evidence for D5.

    "panelmedelvärdet går från −0,31 (2015) till +0,78 (2023)" is the argument for
    keeping Version B's construction pooled — it is what shows B carrying a time
    trend at all. Cited numbers are the weakest kind of prose: correct when
    written, silently wrong after any refresh, and load-bearing for a locked
    decision. So they are re-derived rather than trusted.

    See R1 in docs/OPEN_RISKS.md: B's values move whenever the panel changes,
    which makes this the sentence most likely to go stale in the whole document.
    """
    import pandas as pd

    ranked = pd.read_parquet(ARTIFACT)
    means = ranked.groupby("year")["version_b"].mean().round(2)

    value = SWEDISH_LABELS["mt.formlerna_ger_ett_nivavarde_per_kommun_och"]
    quoted = re.findall(r"([+−-]\d+,\d+)\s*\((\d{4})\)", value)
    assert len(quoted) == 2, f"expected two quoted extremes, found {quoted}"

    def as_float(text: str) -> float:
        return float(text.replace("−", "-").replace(",", "."))

    (low_text, low_year), (high_text, high_year) = quoted
    assert int(low_year) == means.idxmin() and int(high_year) == means.idxmax(), (
        f"copy cites {low_year}/{high_year} as Version B's panel-mean extremes; the "
        f"data says {means.idxmin()}/{means.idxmax()}"
    )
    assert as_float(low_text) == pytest.approx(means.min(), abs=0.005), (
        f"copy cites {low_text} for {low_year}; the data says {means.min():+.2f}"
    )
    assert as_float(high_text) == pytest.approx(means.max(), abs=0.005), (
        f"copy cites {high_text} for {high_year}; the data says {means.max():+.2f}"
    )


# ── Coverage: a new vintage-shaped number cannot join unexamined ─────
#
# Scoped to *vintage-shaped* numbers — bare four-digit years — rather than every
# digit in the copy. Thresholds, regime rules, slider ranges, SCB dataset codes
# and money examples are parameters of the domain: enumerating all ~54 of them
# would add maintenance noise, not safety, and none of them moves when the data
# refreshes. Years do, which is why they are the ones policed.

VINTAGE_SHAPED = re.compile(r"\b(19[6-9]\d|20[0-4]\d)\b")

# Why each remaining year literal is not a data vintage.
NOT_A_VINTAGE = {
    "regulatory regime start": r"\b(?:sedan\s+)?(?:2010|2016|2018|2026)\b",
    "upstream series start year": r"\b(?:19[6-9]\d|198\d|199\d|200\d|2011)\s*[–—-]",
    "forecast horizon end": r"\b202[5-9]\s*[–—-]\s*203\d\b",
    "historical rate-cycle reference": r"\b202[23]\b",
    "editorial market reference": r"typisk\s+\d{4}\s+bankmarknad",
    # "Prisindex (1990=100)", "KPI (2020=100)" — an index's base period, a
    # property of the series definition rather than of this panel's vintage.
    "index base period": r"\b(?:19|20)\d{2}\s*=\s*100\b",
    # "Åren 2020–2021 har negativ realränta" — a statement about the rate cycle
    # that stays true regardless of how far the data now reaches.
    "historical episode reference": r"Åren\s+(?:19|20)\d{2}\s*[–—-]\s*(?:19|20)\d{2}",
    # "−0,31 (2015) till +0,78 (2023)" — measured extremes, re-derived in
    # test_the_d5_panel_mean_statistic_still_holds rather than classified away.
    "D5 panel-mean extremes, checked above": r"[+−-]\d+,\d+\s*\(\d{4}\)",
    "index period, checked above": rf"\b{first_year()}\b|\b{complete_case_max_year()}\b",
}


def test_no_unexamined_year_literal_in_copy() -> None:
    """Force a decision on every year the copy states."""
    unexplained = {}
    for key, value in ALL_COPY.items():
        if key == TABLE_KEY:
            continue
        masked = value
        for pattern in NOT_A_VINTAGE.values():
            masked = re.sub(pattern, " ", masked)
        found = VINTAGE_SHAPED.findall(masked)
        if found:
            unexplained[key] = sorted(set(found))
    assert not unexplained, (
        "these labels state a year that is neither derived from provenance nor "
        "classified in NOT_A_VINTAGE. Either interpolate it, or add a rule saying "
        f"what kind of year it is: {unexplained}"
    )


# ── The guard must be able to fail ───────────────────────────────────


def test_a_hardcoded_year_in_a_source_row_is_caught() -> None:
    """The acceptance criterion: editing a number in the copy fails the check."""
    needle, placeholder = SOURCE_ROWS["unemployment_rate"]
    tampered = SWEDISH_LABELS[TABLE_KEY].replace("{" + placeholder + "}", "2024")
    assert tampered != SWEDISH_LABELS[TABLE_KEY], "tampering had no effect"

    row = _row(tampered, needle)
    assert "{" + placeholder + "}" not in row
    spans = re.findall(r"(\d{4})\s*[–—-]\s*(\d{4})", row)
    assert spans and int(spans[-1][1]) != source_coverage()["unemployment_rate"]["max_year"], (
        "a hardcoded 2024 would still have matched the artifact — pick a stale value"
    )


def test_the_vintage_detector_sees_an_unexplained_year() -> None:
    """A detector matching nothing would pass every label above."""
    masked = "Data till och med 2019 saknas"
    for pattern in NOT_A_VINTAGE.values():
        masked = re.sub(pattern, " ", masked)
    assert VINTAGE_SHAPED.findall(masked) == ["2019"]
