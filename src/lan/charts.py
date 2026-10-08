"""Chart construction for the Län jämförelse page.

Kept out of the page script for the same reason as the Kontantinsats and
Scenario charts: a figure builder that needs a Streamlit process to exercise
cannot be tested, and the page was approaching the 400-line limit.

The county trend chart used to draw all 21 counties in one muted colour with
Stockholm highlighted and the legend switched off. A reader could see the shape
of the spread but not which line was which, which made the chart decorative
rather than readable. Every county now carries its own colour from
`COUNTY_PALETTE`, the page draws the legend beneath the chart
(`county_legend_html`) so it wraps at any width, and the page offers a selection
so the reader can cut 21 lines down to the handful they care about.
"""

from __future__ import annotations

from html import escape

import pandas as pd
import plotly.graph_objects as go

from src.ui.chart_theme import get_chart_layout
from src.ui.labels import L
from src.ui.tokens import COLORS, COUNTY_PALETTE

#: Log ticks for the two ratio versions. Plotly's log minors label 9 and 90
#: identically, which is ambiguous over a range spanning one to several hundred.
_LOG_TICKS = (1, 2, 5, 10, 20, 50, 100, 200, 500)

#: Versions A and C are ratios with the policy rate in the denominator, so when
#: the rate approached zero they ran to 400+ and squashed recent years flat on a
#: linear axis. A log axis is the same treatment decision D6 applies to these two
#: for z-scoring, and for the same reason. B is a weighted sum of z-scores that
#: goes negative, where a log is undefined.
LOG_SCALED = ("version_a", "version_c")


def county_colours(lan_codes: list[str]) -> dict[str, str]:
    """Assign each county a stable colour.

    Args:
        lan_codes: Every county code in the panel, in a stable order.

    Returns:
        `lan_code -> hex colour`. Keyed by code rather than by position in the
        current selection, so a county keeps its colour when the reader filters
        the chart or switches formula tab. A colour that moved between renders
        would be worse than no colour at all.
    """
    ordered = sorted(lan_codes)
    return {code: COUNTY_PALETTE[i % len(COUNTY_PALETTE)] for i, code in enumerate(ordered)}


def county_trend_chart(
    county_versions: pd.DataFrame,
    *,
    value_column: str,
    selected: list[str],
    colours: dict[str, str],
    title: str = "",
) -> go.Figure:
    """One line per county over the index period.

    Args:
        county_versions: `lan_code`, `region_name`, `year` and the value column.
        value_column: `version_a`, `version_b` or `version_c`.
        selected: County codes to draw in colour. Everything else is drawn as
            faint context so the reader keeps a sense of the full spread.
        colours: From :func:`county_colours`.
        title: Chart title. The page leaves it empty and writes the title in
            the card header instead: a Plotly title is one line that cannot
            wrap, and "Realversion · Länsutveckling 2014–2024" ran past the
            edge of a phone.

    Returns:
        A themed Plotly figure.
    """
    fig = go.Figure()
    chosen = set(selected)

    # Context first so the selected lines sit on top of it.
    for lan_code, group in county_versions.groupby("lan_code"):
        if lan_code in chosen:
            continue
        group = group.sort_values("year")
        fig.add_trace(go.Scatter(
            x=group["year"], y=group[value_column],
            mode="lines", name=str(group["region_name"].iloc[0]),
            line=dict(width=1, color=COLORS["grid"]),
            opacity=0.55, showlegend=False, hoverinfo="skip",
        ))

    for lan_code, group in county_versions.groupby("lan_code"):
        if lan_code not in chosen:
            continue
        group = group.sort_values("year")
        name = str(group["region_name"].iloc[0])
        # Every entry is a county, so the repeated " län" suffix buys nothing and
        # cost the end of the longer names to truncation. The hover keeps it.
        short = name[: -len(" län")] if name.endswith(" län") else name
        fig.add_trace(go.Scatter(
            x=group["year"], y=group[value_column],
            mode="lines", name=short, showlegend=False,
            line=dict(width=2.2, color=colours[lan_code]),
            hovertemplate=L("lj.v0_ar_x_varde_y_2f", v0=name),
        ))

    layout = get_chart_layout(
        title=title,
        height=460,
        xaxis_title=L("lj.ar"),
        yaxis_title=L("lj.indexvarde"),
        showlegend=False,
    )
    layout["xaxis"]["dtick"] = 1
    layout["xaxis"]["title"] = {"text": L("lj.ar"), "standoff": 12}
    # No Plotly legend: the page draws one beneath the chart with
    # `county_legend_html`. Inside a fixed-height figure, 21 entries on a phone
    # became a cramped scroll box with names cut off; as page content they wrap.
    layout["margin"] = dict(l=50, r=20, t=48 if title else 16, b=50)

    if value_column in LOG_SCALED:
        layout["yaxis"]["type"] = "log"
        values = county_versions[value_column].dropna()
        ceiling = float(values.max()) if len(values) else 100.0
        ticks = [t for t in _LOG_TICKS if t <= ceiling * 1.6]
        layout["yaxis"]["tickmode"] = "array"
        layout["yaxis"]["tickvals"] = ticks
        layout["yaxis"]["ticktext"] = [str(t) for t in ticks]

    fig.update_layout(**layout)
    return fig


def county_legend_html(
    selected: list[str], colours: dict[str, str], names: dict[str, str]
) -> str:
    """The trend chart's legend, as page content that wraps at any width.

    Args:
        selected: County codes drawn in colour, in display order.
        colours: From :func:`county_colours`.
        names: County code to full name; the " län" suffix is dropped, as in
            the chart's hover-free trace names.

    Returns:
        HTML for a `.shai-legend` row, to render with `unsafe_allow_html`.
    """
    items = []
    for code in selected:
        name = names[code]
        short = name[: -len(" län")] if name.endswith(" län") else name
        items.append(
            f'<span class="shai-legend-item">'
            f'<span class="shai-legend-swatch" style="background:{colours[code]}"></span>'
            f"{escape(short)}</span>"
        )
    return f'<div class="shai-legend">{"".join(items)}</div>'
