"""The default bank margin for Sida 04: the one SCB observed in that year.

The slider used to start at a fixed 1,7 pp. That matched the negative-rate years
but not the recent ones (0,76 pp in 2024), so the default year overstated the
mortgage rate by almost a percentage point. The default now follows the
selected year; the reader can still move the slider.

Data comes from ``data/processed/mortgage_margin.json``, written by
:mod:`src.data.mortgage_margin` during the refresh.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ARTIFACT = Path(__file__).resolve().parents[2] / "data" / "processed" / "mortgage_margin.json"

#: Used only for a year the artifact does not cover; the old fixed default.
FALLBACK_PP = 1.7

#: The slider's bounds and step, which the default must land on.
SLIDER_MIN, SLIDER_MAX, SLIDER_STEP = 0.0, 3.0, 0.1


@lru_cache(maxsize=1)
def observed_margins(path: Path = ARTIFACT) -> dict[int, float]:
    """Year -> observed margin in pp, or empty if the artifact is missing."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {int(year): float(value) for year, value in payload["margin_pp"].items()}


def default_margin_pp(year: int) -> float:
    """The slider's starting value for `year`, rounded onto the slider's grid."""
    observed = observed_margins().get(year, FALLBACK_PP)
    snapped = round(round(observed / SLIDER_STEP) * SLIDER_STEP, 1)
    return min(max(snapped, SLIDER_MIN), SLIDER_MAX)


def is_observed(year: int) -> bool:
    """Whether the default for `year` comes from data rather than the fallback."""
    return year in observed_margins()


def margin_range(first: int, last: int) -> tuple[float, float]:
    """Lowest and highest observed margin over `first`..`last`, in pp."""
    values = [v for y, v in observed_margins().items() if first <= y <= last]
    if not values:
        raise ValueError(f"no observed margin between {first} and {last}")
    return min(values), max(values)
