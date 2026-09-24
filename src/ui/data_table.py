"""One renderer for every `.shai-table` in the app.

Each page built its ranking tables by concatenating HTML in a loop. The markup
drifted: rank cells, municipality names and numeric alignment were re-specified
per page, and a class renamed in the stylesheet had to be chased through every
copy of the loop. T3.2 found two classes that styled nothing partly because of
this.

This module owns the shape. A caller describes its columns; the alignment, the
rank cell, the name cell and the risk pill are decided here.

See task T3.8 and Finding M in docs/REVITALIZATION_PLAN.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from src.ui.components import risk_pill


@dataclass(frozen=True)
class Column:
    """One column of a rendered table.

    Attributes:
        header: Column heading.
        value: Callable taking a row and returning the cell's text.
        numeric: Right-align and use the tabular figure treatment.
        kind: "rank", "name", "pill" or "" — selects the cell class, so the
            stylesheet is referenced here and nowhere else.
    """

    header: str
    value: Callable[[pd.Series], str]
    numeric: bool = False
    kind: str = ""


_CELL_CLASS = {"rank": "shai-rank-cell", "name": "shai-kommun-name", "pill": ""}


def render_table(
    frame: pd.DataFrame,
    columns: list[Column],
    *,
    title: str = "",
    subtitle: str = "",
    tag: str = "",
) -> str:
    """Return HTML for a table.

    Args:
        frame: Rows to render, already sorted and truncated by the caller.
        columns: Column specs, in display order.
        title: Card title. Omitted when empty.
        subtitle: Card subtitle.
        tag: Card tag, e.g. "RANKING".

    Returns:
        A `.shai-card` containing a `.shai-table`.
    """
    head = "".join(
        f'<th class="shai-num">{c.header}</th>' if c.numeric else f"<th>{c.header}</th>"
        for c in columns
    )

    body = ""
    for _, row in frame.iterrows():
        cells = ""
        for column in columns:
            classes = []
            if column.numeric:
                classes.append("shai-num")
            cell_class = _CELL_CLASS.get(column.kind, "")
            if cell_class:
                classes.append(cell_class)
            attr = f' class="{" ".join(classes)}"' if classes else ""
            cells += f"<td{attr}>{column.value(row)}</td>"
        body += f"<tr>{cells}</tr>"

    header_html = ""
    if title:
        tag_html = f'<span class="shai-card-tag">{tag}</span>' if tag else ""
        subtitle_html = (
            f'<div class="shai-card-subtitle">{subtitle}</div>' if subtitle else ""
        )
        header_html = (
            '<div class="shai-card-header"><div>'
            f'<div class="shai-card-title">{title}</div>{subtitle_html}'
            f"</div>{tag_html}</div>"
        )

    return (
        '<div class="shai-card">'
        f"{header_html}"
        f'<table class="shai-table"><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def ranking_columns(*, rank_header: str, name_header: str, headers: list[str]) -> list[Column]:
    """Columns for the standard municipality ranking table.

    Args:
        rank_header: Heading for the position column.
        name_header: Heading for the municipality column.
        headers: Headings for z-score, index value and risk class, in order.

    Returns:
        Five columns: rank, name, z-score, Version C, risk pill.
    """
    z_header, value_header, risk_header = headers
    return [
        Column(rank_header, lambda row: str(row["_rank"]), kind="rank"),
        Column(name_header, lambda row: str(row.get("region_name", "")), kind="name"),
        Column(z_header, lambda row: f"{row.get('z_c', 0):.2f}", numeric=True),
        Column(value_header, lambda row: f"{row.get('version_c', 0):.1f}", numeric=True),
        Column(risk_header, lambda row: risk_pill(row.get("risk_c", "medel")), kind="pill"),
    ]
