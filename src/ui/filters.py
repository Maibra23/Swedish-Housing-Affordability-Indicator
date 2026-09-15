"""Year and risk-class filtering, owned in one place.

The sidebar returns Swedish display labels ("Hög", "Medel", "Låg") and the
artifact stores the codes (`hog`, `medel`, `lag`). Every page that filtered by
risk wrote its own mapping between the two, and its own rule for what an empty
selection means. Three copies of a two-line convention is how the convention
stops being one.

The empty-selection rule in particular is load-bearing. An empty set of pills
means *all* classes, not *no* classes — the opposite reading sends an empty frame
to a chart, which is how Finding A rendered a fabricated KPI. That decision is
made here, once.

See task T3.7 and Finding M in docs/REVITALIZATION_PLAN.md.
"""

from __future__ import annotations

import pandas as pd

# Display label to stored code. The artifact never stores the Swedish.
#
# This mapping is the single source of both halves: `src/ui/sidebar.py` builds its
# pills from RISK_LABELS rather than repeating the strings, so the labels the user
# picks and the labels this module can translate cannot drift apart. A pill whose
# label this dict does not know would silently filter to "all".
RISK_LABEL_TO_CODE = {"Hög": "hog", "Medel": "medel", "Låg": "lag"}
RISK_LABELS = tuple(RISK_LABEL_TO_CODE)
RISK_CODES = tuple(RISK_LABEL_TO_CODE.values())


def risk_codes(selected_labels: list[str] | None) -> tuple[str, ...]:
    """Translate selected pill labels to stored risk codes.

    Args:
        selected_labels: Labels from the sidebar, possibly empty or None.

    Returns:
        The codes to keep. An empty or unrecognised selection means *all* codes:
        a filter nobody set must not hide everything.
    """
    if not selected_labels:
        return RISK_CODES
    codes = tuple(
        RISK_LABEL_TO_CODE[label]
        for label in selected_labels
        if label in RISK_LABEL_TO_CODE
    )
    return codes or RISK_CODES


def by_risk(
    frame: pd.DataFrame,
    selected_labels: list[str] | None,
    column: str = "risk_c",
) -> pd.DataFrame:
    """Filter `frame` to the selected risk classes.

    Args:
        frame: Any frame carrying `column`.
        selected_labels: Labels from the sidebar.
        column: Which version's class to filter on. Defaults to Version C, the
            one the map and rankings use.

    Returns:
        The filtered frame, or `frame` unchanged when every class is selected —
        so a full selection costs no copy.
    """
    codes = risk_codes(selected_labels)
    if set(codes) == set(RISK_CODES) or column not in frame.columns:
        return frame
    return frame[frame[column].isin(codes)]


def by_year(frame: pd.DataFrame, year: int, column: str = "year") -> pd.DataFrame:
    """Filter `frame` to a single year.

    Args:
        frame: Any frame carrying `column`.
        year: The year to keep.
        column: Year column name.

    Returns:
        The rows for that year.
    """
    return frame[frame[column] == year]
