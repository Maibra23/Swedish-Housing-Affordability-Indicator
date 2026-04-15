"""Shared Plotly chart theme for SHAI dashboard.

Ensures all charts have consistent fonts, colors, grids, tooltips, and margins
matching the KRI design system.
"""

from __future__ import annotations

from src.ui.css import COLORS

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
            "family": "Source Sans 3, Source Sans Pro, sans-serif",
            "size": 12,
            "color": COLORS["text_primary"],
        },
        "plot_bgcolor": COLORS["card_bg"],
        "paper_bgcolor": COLORS["card_bg"],
        "margin": {"l": 50, "r": 20, "t": 40 if title else 20, "b": 50},
        "height": height,
        "showlegend": showlegend,
        "xaxis": {
            "gridcolor": COLORS["grid"],
            "zeroline": False,
            "linecolor": COLORS["grid"],
            "title": {
                "text": xaxis_title,
                "font": {"size": 12, "color": COLORS["text_secondary"]},
            } if xaxis_title else None,
        },
        "yaxis": {
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
                "family": "Source Sans 3, Source Sans Pro, sans-serif",
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
