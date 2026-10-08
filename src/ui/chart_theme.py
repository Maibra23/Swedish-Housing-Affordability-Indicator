"""Shared Plotly chart theme for SHAI dashboard.

Ensures all charts have consistent fonts, colors, grids, tooltips, and margins
matching the KRI design system.
"""

from __future__ import annotations

from src.ui.css import COLORS

#: Font stacks for chart text, quoted. CSS reads an unquoted family name that
#: ends in a number, such as Source Sans 3, as invalid and drops the whole
#: declaration. Plotly measured label widths in one font and drew them in
#: another, about 18 % wider, so axis labels, legend entries and annotations ran
#: past the space reserved for them and were cut at the chart edge, worst on a
#: phone. Quoted, measurement and drawing use the same font.
CHART_FONT = "'Source Sans 3', 'Source Sans Pro', sans-serif"
MONO_FONT = "'IBM Plex Mono', monospace"

# Chart color palette — 8 distinct colors for multi-series charts
CHART_PALETTE = [
    "#4A6FA5",  # blue (secondary)
    "#2E7D5B",  # green (low risk)
    "#C4A35A",  # gold (accent)
    "#B94A48",  # red (high risk)
    "#7B68A8",  # purple
    "#D4785A",  # coral
    "#3D8B6E",  # teal
    "#5A7FBD",  # light blue
]


def get_chart_layout(
    title: str = "",
    height: int = 400,
    xaxis_title: str = "",
    yaxis_title: str = "",
    showlegend: bool = True,
) -> dict:
    """Return a Plotly layout dict matching the KRI theme.

    Args:
        title: Chart title text.
        height: Chart height in px.
        xaxis_title: X-axis label.
        yaxis_title: Y-axis label.
        showlegend: Whether to show the legend.
    """
    layout = {
        "font": {
            "family": CHART_FONT,
            "size": 12,
            "color": COLORS["text_primary"],
        },
        "plot_bgcolor": COLORS["card_bg"],
        "paper_bgcolor": COLORS["card_bg"],
        "margin": {"l": 50, "r": 20, "t": 40 if title else 20, "b": 50},
        "height": height,
        "showlegend": showlegend,
        # automargin on both axes: tick labels and axis titles take the room
        # they need instead of being cut at the figure edge, which on a narrow
        # screen is where long category names (regime names) ended up.
        "xaxis": {
            "automargin": True,
            "gridcolor": COLORS["grid"],
            "zeroline": False,
            "linecolor": COLORS["grid"],
            "title": {
                "text": xaxis_title,
                "font": {"size": 12, "color": COLORS["text_secondary"]},
            } if xaxis_title else None,
        },
        "yaxis": {
            "automargin": True,
            "gridcolor": COLORS["grid"],
            "griddash": "dot",
            "zeroline": False,
            "linecolor": COLORS["grid"],
            "title": {
                "text": yaxis_title,
                "font": {"size": 12, "color": COLORS["text_secondary"]},
            } if yaxis_title else None,
        },
        "hoverlabel": {
            "bgcolor": COLORS["primary"],
            "bordercolor": COLORS["primary"],
            "font": {
                "family": CHART_FONT,
                "size": 12,
                "color": "#FFFFFF",
            },
        },
    }

    if title:
        layout["title"] = {
            "text": title,
            "font": {"size": 15, "color": COLORS["text_primary"]},
            "x": 0.02,
            "xanchor": "left",
        }

    if showlegend:
        layout["legend"] = {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11},
        }

    return layout


#: Vertical gap, in px, between a bar's name and the top edge of its bar.
_BAR_NAME_OFFSET_PX = 4


def bar_names_above(fig, names: list[str], bar_width: float) -> None:
    """Write each horizontal bar's name above the bar instead of on the y-axis.

    A category label on the y-axis takes its width out of the plot. Plotly's
    `automargin` grows the margin to fit, but only while enough plot is left,
    so on a phone a long label is cut from the left: "Högsta pris inkomsten
    bär" rendered as "sta pris inkomsten bär" at 360 px. Text above the bar
    starts at the plot's left edge and uses the plot's full width, so it fits
    at any width the bars themselves fit.

    Modifies `fig` in place, as Plotly's own `update_layout` does.

    Args:
        fig: A figure whose bars are horizontal and whose y categories are
            exactly `names`, in order.
        names: The category labels, as passed to the trace's `y`.
        bar_width: The trace's bar `width`, in category units, so the label
            clears the bar regardless of chart height.
    """
    fig.update_yaxes(showticklabels=False, automargin=False)
    for index, name in enumerate(names):
        fig.add_annotation(
            # Category axes place category i at y = i, so the bar's top edge is
            # half a bar width above it.
            x=0, xref="paper", xanchor="left",
            y=index + bar_width / 2, yref="y", yanchor="bottom",
            yshift=_BAR_NAME_OFFSET_PX,
            text=name, showarrow=False, align="left",
            font=dict(size=12, color=COLORS["text_secondary"]),
        )
