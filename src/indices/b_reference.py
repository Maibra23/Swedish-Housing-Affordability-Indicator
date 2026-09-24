"""The fixed yardstick Version B is measured against.

R1 in `docs/OPEN_RISKS.md`: `compute_version_b` z-scored its four components
pooled across whatever panel it was handed, so B's published values were a
function of panel composition. Add a row anywhere and every historical year
moved, silently, with nothing announcing it.

That pooling is deliberate and worth keeping. Decision D5 chose it because the
pooled *level* is the only time trend the index carries: Versions A and C are
normalised within year and are therefore silent about whether Sweden as a whole
got better or worse. The defect was never the pooling. It was that the reference
distribution was recomputed from scratch on every refresh.

**So the reference is computed once and stored.** New data is scored against the
stored mean and standard deviation rather than against itself.

## What this fixes, measured

Two refreshes, both real:

| Refresh | `version_b` rows moved | `rank_b` changed | `risk_b` changed |
|---|---|---|---|
| One ordinary year added (2025 simulated) | 3 190 of 3 190 | 947, up to 4 places | 7 |
| The income source switch of 2026-09-21 | 3 190 of 3 190 | 2 971, up to 117 places | **225** |

The register asked whether the churn was small enough to accept with a note, on
the precedent of a 19-row incident. It is not. The second row above is what
happens when a *source definition* changes rather than a year being appended, and
it is the case that actually occurred.

Version C, normalised within year, moved on zero rows in the first refresh. The
instability was never in the data. It was in the yardstick.

## Why this preserves the trend rather than deleting it

Normalising B within year, like A and C, would remove the re-basing and also
remove the trend, which is what D5 rejected. Freezing does neither.

It is in fact a *better* trend measure than the moving reference was. Under the
old behaviour, adding a high-rate year inflated the pooled standard deviation and
so pushed earlier high-rate years back toward zero: the yardstick shrank as the
thing it measured grew. A fixed reference means "2.3 standard deviations above
the 2014 to 2024 norm" keeps meaning the same thing in 2030 as it does today.

## Adoption cost: none

The reference is derived from the panel as it currently stands, so scoring
against it reproduces today's values exactly. Freezing is value-neutral on the
day it is adopted, and `tests/test_version_b_reference.py` asserts that.

## When to re-base deliberately

A reference is a published decision, not a cache. Bump `version` and record why
in `docs/OPEN_RISKS.md` when the panel changes enough that the old norm stops
describing anything useful, and expect every B value to move when you do.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH: Path = _PROJECT_ROOT / "data" / "processed" / "version_b_reference.json"

#: The four component series Version B z-scores, in formula order. `pi_ratio` is
#: derived rather than a panel column; the rest are read directly.
COMPONENTS: tuple[str, ...] = (
    "pi_ratio",
    "policy_rate",
    "unemployment_rate",
    "cpi_yoy_pct",
)

#: Panel levels scored separately. Their distributions differ, so a county
#: reference applied to municipalities would be the same defect in a new place.
LEVELS: tuple[str, ...] = ("municipal", "county", "national")


@dataclass(frozen=True)
class LevelReference:
    """Frozen mean and standard deviation per component, for one panel level.

    Args:
        level: "municipal", "county" or "national".
        derived_from: Which panel produced it, for the record.
        moments: `component -> {"mean": float, "std": float}`.
    """

    level: str
    derived_from: dict
    moments: dict[str, dict[str, float]]

    def zscore(self, values: pd.Series, component: str) -> pd.Series:
        """Z-score `values` against the stored moments for `component`.

        Args:
            values: The component series for the panel being scored.
            component: Which component these values are.

        Returns:
            The z-scored series.

        Raises:
            KeyError: If the reference has no moments for this component, which
                means the formula gained a term the stored reference predates.
        """
        if component not in self.moments:
            raise KeyError(
                f"the stored Version B reference has no moments for {component!r} "
                f"at level {self.level!r}. If the formula gained a component, the "
                f"reference must be re-derived and its version bumped; see "
                f"src/indices/b_reference.py."
            )
        moments = self.moments[component]
        std = float(moments["std"])
        if std == 0:
            return pd.Series(0.0, index=values.index)
        return (values - float(moments["mean"])) / std


def pi_ratio(panel: pd.DataFrame) -> pd.Series:
    """Price to income, the one Version B component that is derived.

    Stated here rather than inline in `compute_version_b` so that deriving the
    reference and applying it cannot drift apart: both call this.
    """
    return panel["transaction_price_sek"] / panel["median_income"]


def _component_series(panel: pd.DataFrame, component: str) -> pd.Series:
    return pi_ratio(panel) if component == "pi_ratio" else panel[component]


def derive(panel: pd.DataFrame, level: str) -> LevelReference:
    """Compute a fresh reference from a panel.

    Used once to bootstrap, and again only on a deliberate re-base. Not called
    during an ordinary refresh, which is the entire point.

    Args:
        panel: The scored rows for this level, already complete-case filtered.
        level: Which level this is.

    Returns:
        A :class:`LevelReference`.
    """
    moments = {}
    for component in COMPONENTS:
        series = _component_series(panel, component).astype(float)
        moments[component] = {
            "mean": float(series.mean()),
            "std": float(series.std()),
        }
    return LevelReference(
        level=level,
        derived_from={
            "min_year": int(panel["year"].min()),
            "max_year": int(panel["year"].max()),
            "rows": int(len(panel)),
        },
        moments=moments,
    )


def load(path: Path | None = None) -> dict[str, LevelReference]:
    """Read the stored reference for every level.

    Args:
        path: Override for the artifact location.

    Returns:
        `level -> LevelReference`, empty if the artifact does not exist yet.
    """
    target = Path(path) if path is not None else REFERENCE_PATH
    if not target.exists():
        return {}
    payload = json.loads(target.read_text(encoding="utf-8"))
    return {
        level: LevelReference(
            level=level,
            derived_from=body["derived_from"],
            moments=body["moments"],
        )
        for level, body in payload["levels"].items()
    }


def save(references: dict[str, LevelReference], path: Path | None = None) -> Path:
    """Write the reference artifact.

    Args:
        references: `level -> LevelReference`.
        path: Override for the output location.

    Returns:
        The path written.
    """
    target = Path(path) if path is not None else REFERENCE_PATH
    payload = {
        "version": 1,
        "note": (
            "Frozen z-score reference for Version B. Scoring against stored "
            "moments is what stops a refresh re-basing every historical value; "
            "see R1 in docs/OPEN_RISKS.md and src/indices/b_reference.py. Do not "
            "regenerate this file as part of an ordinary refresh."
        ),
        "levels": {
            level: {"derived_from": ref.derived_from, "moments": ref.moments}
            for level, ref in sorted(references.items())
        },
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def reference_for(
    panel: pd.DataFrame, level: str, path: Path | None = None
) -> LevelReference:
    """The stored reference for `level`, bootstrapping it if none exists.

    Bootstrapping is loud on purpose. Creating a reference is a decision about
    what "normal" means for the whole index, and it should never happen as a
    quiet side effect of running a refresh on a machine where the artifact was
    not checked out.

    Args:
        panel: Rows for this level, used only if a reference must be created.
        level: Which level.
        path: Override for the artifact location.

    Returns:
        The reference to score against.
    """
    stored = load(path)
    if level in stored:
        return stored[level]

    logger.warning(
        "No stored Version B reference for level %r. Deriving one from the "
        "current panel and writing %s. Every Version B value is now measured "
        "against this panel; if the artifact was simply missing from the "
        "checkout, restore it and re-run rather than keeping this one.",
        level,
        (path or REFERENCE_PATH).name,
    )
    stored[level] = derive(panel, level)
    save(stored, path)
    return stored[level]
