"""Writing the provenance artifact, as opposed to reading it.

Split from `provenance.py` when that module crossed the 400-line limit. The seam
was already marked in it by a section comment, and the two halves have different
audiences: every page imports the readers at render time, while these run once
per refresh, from `scripts/refresh_data.py`.

The artifact records two different kinds of fact, and conflating them is what
the income defect of 2026-09-21 exploited:

  - **vintage** — how far each source reaches, derived from the panel
  - **definition** — what each source actually *is*, taken from
    `src/data/variable_contracts.py`

Coverage years say when a number is from. They never say what it is. The record
showed `median_income` running 2011 to 2024, which was true, while the column
held household disposable income and every page called it individual gross.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data.variable_contracts import CONTRACTS
from src.provenance import (
    INDEX_INPUTS,
    _IMPUTATION_FLAGS,
    _NOTE,
    _PROVENANCE_PATH,
    _TRACKED_SOURCES,
    load_provenance,
)

logger = logging.getLogger(__name__)


# ── Building ─────────────────────────────────────────────────────────


def _observed(panel: pd.DataFrame, column: str) -> pd.DataFrame:
    """Rows where ``column`` is a real observation rather than a filled one."""
    present = panel[panel[column].notna()]
    flag = _IMPUTATION_FLAGS.get(column)
    if flag and flag in present.columns:
        present = present[~present[flag].astype(bool)]
    return present


def _source_window(panel: pd.DataFrame, column: str) -> dict | None:
    """Summarise one source's coverage, or ``None`` if it has no observations."""
    present = _observed(panel, column)
    if present.empty:
        logger.warning("Source %s has no observed rows; omitting from provenance", column)
        return None
    return {
        "min_year": int(present["year"].min()),
        "max_year": int(present["year"].max()),
        "n_regions": int(present["region_code"].nunique()),
    }


def _definitions() -> dict:
    """Every contracted variable's definition, for the provenance record.

    Coverage years say when a number is from. They do not say *what* it is, and
    on 2026-09-21 that was the gap that mattered: the record showed
    `median_income` running 2011 to 2024, which was true, while the column held
    household disposable income and every page called it individual gross.

    Writing the table path and the exact value selections into the artifact means
    a displayed figure traces to a specific SCB query without anyone reading
    Python. It also means a changed selection shows up in an artifact diff, which
    a reviewer reads, rather than only in a source diff, which they may not.
    """
    return {
        contract.name: {
            "table_path": contract.table_path,
            "filters": {code: list(values) for code, values in contract.filters},
            "unit_of_analysis": contract.unit_of_analysis,
            "concept": contract.concept,
            "statistic": contract.statistic,
            "unit": contract.unit,
            "min_year_requested": contract.min_year,
        }
        for contract in CONTRACTS.values()
    }


def build_provenance(panel: pd.DataFrame, index_frame: pd.DataFrame) -> dict:
    """Derive the provenance record from the data that was just built.

    Args:
        panel: The municipal panel (``panel_municipal.parquet``).
        index_frame: The scored index (``affordability_ranked.parquet``), used
            for the index's own year range.

    Returns:
        A JSON-serialisable provenance dict.

    Raises:
        ValueError: If no year carries every index input, which means the panel
            cannot support an affordability index at all.
    """
    sources = {
        name: window
        for name in _TRACKED_SOURCES
        if name in panel.columns and (window := _source_window(panel, name)) is not None
    }

    complete = panel[panel[list(INDEX_INPUTS)].notna().all(axis=1)]
    for column, flag in _IMPUTATION_FLAGS.items():
        if column in INDEX_INPUTS and flag in complete.columns:
            complete = complete[~complete[flag].astype(bool)]
    if complete.empty:
        raise ValueError(
            "No year in the panel carries every index input "
            f"({', '.join(INDEX_INPUTS)}); the affordability index cannot be built."
        )

    index_max_years = {name: window["max_year"] for name, window in sources.items()}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": sources,
        "definitions": _definitions(),
        "panel_min_year": int(panel["year"].min()),
        "panel_max_year": int(panel["year"].max()),
        "complete_case_max_year": int(complete["year"].max()),
        "index_min_year": int(index_frame["year"].min()),
        "index_max_year": int(index_frame["year"].max()),
        "index_inputs": list(INDEX_INPUTS),
        "n_kommuner": int(panel["region_code"].nunique()),
        "panel_rows": int(len(panel)),
        "index_rows": int(len(index_frame)),
        "balanced": len(set(index_max_years.values())) <= 1,
        "note": _NOTE,
    }


def write_provenance(
    panel: pd.DataFrame, index_frame: pd.DataFrame, path: Path | None = None
) -> Path:
    """Build the provenance record and write it as JSON.

    Clears the read cache so a caller that reads back in the same process sees
    what was just written.

    Args:
        panel: The municipal panel.
        index_frame: The scored index.
        path: Override for the output location.

    Returns:
        The path written.
    """
    target = Path(path) if path is not None else _PROVENANCE_PATH
    payload = build_provenance(panel, index_frame)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    load_provenance.cache_clear()

    logger.info(
        "Wrote %s — index %d–%d, panel through %d, %d municipalities",
        target.name,
        payload["index_min_year"],
        payload["complete_case_max_year"],
        payload["panel_max_year"],
        payload["n_kommuner"],
    )
    return target


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    write_provenance(
        pd.read_parquet(_DATA_DIR / "panel_municipal.parquet"),
        pd.read_parquet(_DATA_DIR / "affordability_ranked.parquet"),
    )
    print(json.dumps(load_provenance(), indent=2, ensure_ascii=False))
