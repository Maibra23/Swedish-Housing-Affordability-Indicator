"""The observed bank margin that Sida 04 starts its slider at.

Before October 2026 the default was a fixed 1,7 pp, while SCB's series put the
2024 margin at 0,76 pp: the default year's mortgage rate came out at 5,33 %
against an actual 4,39 %. These tests pin the derivation, the artifact and the
copy that quotes its range.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data import mortgage_margin as source
from src.kontantinsats import margin
from src.provenance import complete_case_max_year, first_year
from src.ui.labels import SWEDISH_LABELS

ROOT = Path(__file__).resolve().parents[1]


# ── Derivation (no network) ──────────────────────────────────────────


def test_annual_means_average_the_months() -> None:
    assert source.annual_means({"2024M01": 4.0, "2024M02": 5.0, "2025M01": 3.0}) == {2024: 4.5, 2025: 3.0}


def test_margin_is_mortgage_minus_policy_for_shared_years() -> None:
    assert source.margins({2023: 4.4, 2024: 4.4}, {2024: 3.6, 2025: 2.0}) == {2024: pytest.approx(0.8)}


def test_parse_response_skips_scb_blanks() -> None:
    payload = {"data": [{"key": ["1", "2c", "0100", "1.1.1", "2024M01"], "values": ["4.50"]},
                        {"key": ["1", "2c", "0100", "1.1.1", "2024M02"], "values": [".."]}]}
    assert source.parse_response(payload) == {"2024M01": 4.5}


def test_build_refuses_disjoint_series() -> None:
    with pytest.raises(ValueError):
        source.build({2010: 1.0}, {"2024M01": 4.0})


# ── The committed artifact ───────────────────────────────────────────


def test_artifact_covers_every_selectable_year() -> None:
    observed = margin.observed_margins()
    for year in range(first_year(), complete_case_max_year() + 1):
        assert year in observed, f"no observed margin for {year}; the page falls back to 1,7 pp"


def test_artifact_margin_equals_its_own_inputs() -> None:
    payload = json.loads(margin.ARTIFACT.read_text(encoding="utf-8"))
    for year, value in payload["margin_pp"].items():
        expected = payload["mortgage_rate_pct"][year] - payload["policy_rate_pct"][year]
        assert value == pytest.approx(expected, abs=1e-3)


def test_policy_rate_in_artifact_matches_the_panel() -> None:
    import pandas as pd

    national = pd.read_parquet(ROOT / "data" / "processed" / "panel_national.parquet").set_index("year")
    payload = json.loads(margin.ARTIFACT.read_text(encoding="utf-8"))
    for year, rate in payload["policy_rate_pct"].items():
        assert rate == pytest.approx(national.loc[int(year), "policy_rate"], abs=1e-3)


# ── The default the page uses ────────────────────────────────────────


@pytest.mark.parametrize("year,expected", [(2016, 2.1), (2024, 0.8)])
def test_default_snaps_the_observed_margin_onto_the_slider(year: int, expected: float) -> None:
    assert margin.default_margin_pp(year) == expected


def test_unknown_year_falls_back_to_the_old_default() -> None:
    assert margin.default_margin_pp(1990) == margin.FALLBACK_PP
    assert not margin.is_observed(1990)


def test_copy_quotes_the_observed_range() -> None:
    """The tooltip and F12 both say 0,8 to 2,1 pp; the data must agree."""
    low, high = margin.margin_range(2014, 2026)
    quoted = f"mellan {low:.1f} och {high:.1f} procentenheter".replace(".", ",")
    assert quoted in SWEDISH_LABELS["ki.faktisk_bolaneranta_styrranta_rantepaslag_0"]
    assert quoted in SWEDISH_LABELS["mt.id_begransning_atgard_f1_kommunal"], "F12 in Metodologi"
