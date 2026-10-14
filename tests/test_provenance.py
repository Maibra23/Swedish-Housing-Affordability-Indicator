"""The provenance artifact must describe the data that actually shipped.

SHAI's panel is ragged at the top end: the policy rate and CPI reach 2026,
the price index 2025, while income, prices and unemployment stop at 2024. All
three affordability formulas need income, so the composite index cannot exceed
2024 no matter how fresh the other series are.

Two years are therefore needed and they are not interchangeable:

  * ``complete_case_max_year`` — the latest year carrying every index input.
    The year selector, the KPIs and the map all key off this.
  * ``panel_max_year`` — the latest year present in the panel at all.

Before this module those years were hardcoded in the sidebar, and the footer
printed ``date.today()`` over 2024 data. See Findings B, C and H.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src import provenance

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACT = DATA_DIR / "data_provenance.json"

# Inputs every affordability formula needs; see indices/affordability.compute_all.
INDEX_INPUTS = (
    "median_income",
    "transaction_price_sek",
    "policy_rate",
    "unemployment_rate",
    "cpi_yoy_pct",
)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "panel_municipal.parquet")


@pytest.fixture(scope="module")
def payload() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


# ── The artifact exists and is committed ─────────────────────────────


def test_artifact_is_committed():
    assert ARTIFACT.exists(), (
        f"{ARTIFACT} is missing. It is written by scripts/refresh_data.py and "
        f"must be committed — the app reads it at import time."
    )


def test_artifact_records_every_required_key(payload: dict):
    required = {
        "generated_at",
        "sources",
        "panel_min_year",
        "panel_max_year",
        "complete_case_max_year",
        "index_min_year",
        "index_max_year",
        "n_kommuner",
        "balanced",
        "note",
    }
    assert required <= set(payload), f"missing keys: {sorted(required - set(payload))}"


# ── Public API ───────────────────────────────────────────────────────


def test_complete_case_max_year_is_2024():
    """Income is the binding constraint and stops at 2024 (Finding E)."""
    assert provenance.complete_case_max_year() == 2024


def test_panel_max_year_is_2026():
    assert provenance.panel_max_year() == 2026


def test_first_year_is_the_index_start():
    """The hero stat strip reads '2014–2024' from these two calls."""
    assert provenance.first_year() == 2014


def test_n_kommuner_is_290():
    assert provenance.n_kommuner() == 290


def test_complete_case_never_exceeds_panel_max():
    assert provenance.complete_case_max_year() <= provenance.panel_max_year()


def test_load_provenance_is_cached():
    assert provenance.load_provenance() is provenance.load_provenance()


def test_source_coverage_returns_every_index_input():
    coverage = provenance.source_coverage()
    missing = [c for c in INDEX_INPUTS if c not in coverage]
    assert not missing, f"provenance omits index inputs: {missing}"


# ── The artifact agrees with the panel it describes ──────────────────


def test_source_coverage_matches_the_panel(panel: pd.DataFrame):
    """Every recorded per-source window must be re-derivable from the panel."""
    coverage = provenance.source_coverage()
    mismatches = []
    for name, recorded in coverage.items():
        if name not in panel.columns:
            mismatches.append(f"{name}: not a panel column")
            continue
        present = panel[panel[name].notna()]
        flag = provenance._IMPUTATION_FLAGS.get(name)
        if flag:
            # Income and apartment prices are forward-filled past their true
            # vintage; the honest max is the last year SCB actually published.
            present = present[~present[flag].astype(bool)]
        if present.empty:
            mismatches.append(f"{name}: no non-null rows")
            continue
        expected = (int(present["year"].min()), int(present["year"].max()))
        actual = (int(recorded["min_year"]), int(recorded["max_year"]))
        if expected != actual:
            mismatches.append(f"{name}: artifact {actual} vs panel {expected}")
    assert not mismatches, "provenance disagrees with the panel:\n  " + "\n  ".join(mismatches)


def test_panel_max_year_matches_the_panel(panel: pd.DataFrame):
    assert provenance.panel_max_year() == int(panel["year"].max())


def test_n_kommuner_matches_the_panel(panel: pd.DataFrame):
    assert provenance.n_kommuner() == int(panel["region_code"].nunique())


def test_complete_case_max_year_is_derivable_from_the_panel(panel: pd.DataFrame):
    """Re-derive the complete-case year independently of how it was written."""
    usable = panel[panel[list(INDEX_INPUTS)].notna().all(axis=1)]
    usable = usable[~usable["is_imputed_income"].astype(bool)]
    assert provenance.complete_case_max_year() == int(usable["year"].max())


def test_index_years_match_the_ranked_artifact():
    ranked = pd.read_parquet(DATA_DIR / "affordability_ranked.parquet")
    assert provenance.first_year() == int(ranked["year"].min())
    assert provenance.load_provenance()["index_max_year"] == int(ranked["year"].max())


def test_panel_is_recorded_as_ragged(payload: dict):
    """The ragged tail is the whole reason this artifact exists."""
    assert payload["balanced"] is False
    assert payload["note"].strip(), "the note must explain the ragged tail"


def test_generated_at_is_an_iso_timestamp(payload: dict):
    from datetime import datetime

    datetime.fromisoformat(payload["generated_at"])


# ── Failure modes ────────────────────────────────────────────────────


def test_missing_artifact_raises_with_a_helpful_message(tmp_path: Path):
    absent = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError) as exc:
        provenance.load_provenance(absent)
    message = str(exc.value)
    assert str(absent) in message
    assert "refresh_data" in message, "the message must name the script that writes it"


def test_missing_key_raises_keyerror(tmp_path: Path):
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"generated_at": "2026-01-01T00:00:00+00:00"}))
    with pytest.raises(KeyError):
        provenance.complete_case_max_year(partial)


# ── N-4 · forward-filled apartment prices are not coverage ───────────


def test_apartment_price_coverage_stops_where_scb_does(panel: pd.DataFrame):
    """The panel carries the last apartment price into later years; provenance
    must not count those rows. It reported BO0501C through 2026 while SCB had
    published through 2025 (October 2026 audit, N-4)."""
    flag = "is_filled_bostadsratt_price"
    assert flag in panel.columns, "the panel no longer marks forward-filled apartment prices"
    observed = panel.loc[panel["bostadsratt_price_sek"].notna() & ~panel[flag], "year"]
    reported = provenance.source_coverage()["bostadsratt_price_sek"]["max_year"]
    assert reported == int(observed.max())
    assert reported < int(panel.loc[panel["bostadsratt_price_sek"].notna(), "year"].max())


def test_forward_fill_flags_only_the_filled_rows():
    from src.data.clean_sources import forward_fill_flagged

    frame = pd.DataFrame({"r": ["a"] * 3, "year": [2024, 2025, 2026],
                          "bostadsratt_price_sek": [1.0, 2.0, None]})
    out = forward_fill_flagged(frame, "r")
    assert list(out["bostadsratt_price_sek"]) == [1.0, 2.0, 2.0]
    assert list(out["is_filled_bostadsratt_price"]) == [False, False, True]
    assert frame["bostadsratt_price_sek"].isna().sum() == 1, "input was mutated"
