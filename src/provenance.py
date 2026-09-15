"""Data vintage, read from the pipeline's provenance artifact.

SHAI's panel is **ragged** at the top end. The Riksbank policy rate and SCB's
CPI run to the current month; the small-house price index reaches 2025; income,
transaction prices and unemployment stop at 2024. Every one of the three
affordability formulas divides by ``median_income`` (see
``indices/affordability.compute_all``), so the composite index cannot exceed the
last year income was actually published — no matter how fresh the other series
look.

Two years are needed and they are not interchangeable:

  * :func:`complete_case_max_year` — the latest year carrying *every* index
    input. The year selector, the KPI row and the choropleth all key off this.
  * :func:`panel_max_year` — the latest year present in the panel at all. Useful
    for component series that stand on their own, and for saying honestly how
    far the raw data reaches.

Before this module those years were hardcoded in three places and the sidebar
footer printed ``date.today()`` over 2024 data, so a visitor in 2026 read
"Senast uppdaterad: 2026-09-15" above a two-year-old index. See Findings B, C
and H in ``docs/REVITALIZATION_PLAN.md``.

A note on income imputation: ``build_panel`` forward-fills ``median_income``
past its true vintage at +3 %/yr and flags those rows with
``is_imputed_income``. A forward-filled value is a modelling assumption, not an
observation, so this module reports income's ``max_year`` as the last
*non-imputed* year. That is what makes ``complete_case_max_year`` land on 2024
rather than on the panel's nominal end.

The artifact is written by ``scripts/refresh_data.py`` and is committed, because
the app reads it at import time.
"""

from __future__ import annotations

import copy
import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DATA_DIR = _PROJECT_ROOT / "data" / "processed"
_PROVENANCE_PATH: Path = _DATA_DIR / "data_provenance.json"

#: Columns every affordability formula needs. Kept in step with
#: ``indices.affordability.compute_all``, which drops rows missing any of them.
INDEX_INPUTS: tuple[str, ...] = (
    "median_income",
    "transaction_price_sek",
    "policy_rate",
    "unemployment_rate",
    "cpi_yoy_pct",
)

#: Panel columns whose vintage is worth recording. Index inputs first, then the
#: context series the pages show alongside them.
_TRACKED_SOURCES: tuple[str, ...] = (
    *INDEX_INPUTS,
    "bostadsratt_price_sek",
    "price_index",
    "kt_ratio",
    "population",
    "completions",
    "cpi_index",
)

#: Columns carrying a companion boolean marking forward-filled rows. Such rows
#: are excluded when deciding a source's real max year.
_IMPUTATION_FLAGS: dict[str, str] = {"median_income": "is_imputed_income"}

_NOTE = (
    "The panel is ragged at the top end: sources end in different years. "
    "Every affordability formula requires median_income, so the composite index "
    "cannot move past complete_case_max_year even when prices, the price index "
    "or the policy rate are fresher. Use complete_case_max_year for anything "
    "that displays an index value or offers a year to the user; use "
    "panel_max_year only when talking about a component series on its own. "
    "median_income is forward-filled beyond its recorded max_year and those "
    "rows are flagged with is_imputed_income."
)


# ── Reading ──────────────────────────────────────────────────────────


@lru_cache(maxsize=8)
def load_provenance(path: Path | None = None) -> dict:
    """Read and cache the provenance artifact.

    The returned dict is the cached object and must be treated as read-only;
    use :func:`source_coverage` when a mutable copy is wanted.

    Args:
        path: Override for the artifact location. Defaults to
            ``data/processed/data_provenance.json``.

    Returns:
        The parsed artifact.

    Raises:
        FileNotFoundError: If the artifact does not exist. It is written by the
            refresh pipeline, so its absence means the pipeline never ran.
    """
    target = Path(path) if path is not None else _PROVENANCE_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"Data provenance artifact not found: {target}. It is written by "
            f"scripts/refresh_data.py; run `python scripts/refresh_data.py "
            f"--no-fetch --no-forecast` to regenerate it."
        )
    return json.loads(target.read_text(encoding="utf-8"))


def _require(payload: dict, key: str, source: Path | None) -> object:
    if key not in payload:
        raise KeyError(
            f"{key!r} is missing from the provenance artifact "
            f"({source or _PROVENANCE_PATH}). Re-run scripts/refresh_data.py to "
            f"regenerate it."
        )
    return payload[key]


def _require_int(payload: dict, key: str, source: Path | None) -> int:
    return int(_require(payload, key, source))  # type: ignore[arg-type]


def complete_case_max_year(path: Path | None = None) -> int:
    """Return the latest year carrying every affordability-index input.

    This is the ceiling for anything the user can select or that displays an
    index value.

    Args:
        path: Override for the artifact location.

    Returns:
        The complete-case year, currently 2024.

    Raises:
        FileNotFoundError: If the artifact is missing.
        KeyError: If the artifact does not record the year.
    """
    return _require_int(load_provenance(path), "complete_case_max_year", path)


def panel_max_year(path: Path | None = None) -> int:
    """Return the latest year present in the panel at all.

    Higher than :func:`complete_case_max_year` whenever a component series has
    been published ahead of income.

    Args:
        path: Override for the artifact location.

    Returns:
        The panel's maximum year, currently 2026.

    Raises:
        FileNotFoundError: If the artifact is missing.
        KeyError: If the artifact does not record the year.
    """
    return _require_int(load_provenance(path), "panel_max_year", path)


def first_year(path: Path | None = None) -> int:
    """Return the first year the affordability index covers.

    Paired with :func:`complete_case_max_year` this gives the period the hero
    stat strip quotes, with no literal years in the page.

    Args:
        path: Override for the artifact location.

    Returns:
        The index's first year, currently 2014.

    Raises:
        FileNotFoundError: If the artifact is missing.
        KeyError: If the artifact does not record the year.
    """
    return _require_int(load_provenance(path), "index_min_year", path)


def n_kommuner(path: Path | None = None) -> int:
    """Return the number of municipalities in the panel.

    Args:
        path: Override for the artifact location.

    Returns:
        The municipality count, currently 290.

    Raises:
        FileNotFoundError: If the artifact is missing.
        KeyError: If the artifact does not record the count.
    """
    return _require_int(load_provenance(path), "n_kommuner", path)


def generated_at(path: Path | None = None) -> str:
    """Return the ISO-8601 timestamp of the last pipeline run.

    This is when the *data* was built, never when a page was rendered.

    Args:
        path: Override for the artifact location.

    Returns:
        An ISO-8601 timestamp string.

    Raises:
        FileNotFoundError: If the artifact is missing.
        KeyError: If the artifact does not record the timestamp.
    """
    return str(_require(load_provenance(path), "generated_at", path))


def source_coverage(path: Path | None = None) -> dict[str, dict]:
    """Return each source's year window and region count.

    Args:
        path: Override for the artifact location.

    Returns:
        A fresh mapping of column name to ``{min_year, max_year, n_regions}``.
        Deep-copied, so mutating it cannot corrupt the cached artifact.

    Raises:
        FileNotFoundError: If the artifact is missing.
        KeyError: If the artifact does not record the sources.
    """
    sources = _require(load_provenance(path), "sources", path)
    return copy.deepcopy(sources)  # type: ignore[arg-type]


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
