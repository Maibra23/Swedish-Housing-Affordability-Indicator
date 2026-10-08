"""The national map's colour scale, drawn as page content.

branca's own legend is a 450 px SVG with no viewBox. On any map narrower than
that, every phone and a tablet with the sidebar open, it was cut at both ends
and lost its caption. This draws the same scale as HTML that takes the width it
is given, so `choropleth.py` no longer adds branca's legend to the map.
"""

from __future__ import annotations

import html

import branca.colormap as cm

from src.ui.labels import L
from src.ui.tokens import DIVERGING_SCALE


def _sv_number(value: float) -> str:
    """A score as the page writes it: two decimals, comma, true minus sign."""
    return f"{value:.2f}".replace(".", ",").replace("-", "\u2212")


#: Keep the middle tick this far, in % of the bar, from either end so it cannot
#: sit on top of the end labels.
_MID_TICK_CLAMP_PCT = (22.0, 78.0)


def colormap_legend_html(colormap: cm.LinearColormap) -> str:
    """The map's colour scale as page content that fits any width.

    The gradient stops sit at the colormap's own index, so the bar shows exactly
    the scale the polygons are painted with. Below it: the lowest score, the
    median (the neutral colour) and the highest, then the caption, which wraps.

    Args:
        colormap: From :func:`build_colormap`.

    Returns:
        HTML for a `.shai-map-legend` block, to render with `unsafe_allow_html`.
    """
    low, high = float(colormap.vmin), float(colormap.vmax)
    span = (high - low) or 1.0
    stops = ", ".join(
        f"{colour} {100 * (value - low) / span:.1f}%"
        for colour, value in zip(DIVERGING_SCALE, colormap.index)
    )
    middle = float(colormap.index[len(colormap.index) // 2])
    lo_clamp, hi_clamp = _MID_TICK_CLAMP_PCT
    mid_pct = min(max(100 * (middle - low) / span, lo_clamp), hi_clamp)
    return (
        '<div class="shai-map-legend">'
        f'<div class="shai-map-legend-bar" style="background:linear-gradient(to right, {stops})"></div>'
        '<div class="shai-map-legend-ticks">'
        f'<span style="left:0">{_sv_number(low)}</span>'
        f'<span style="left:{mid_pct:.1f}%;transform:translateX(-50%)">{_sv_number(middle)}</span>'
        f'<span style="right:0">{_sv_number(high)}</span>'
        "</div>"
        f'<div class="shai-map-legend-caption">{html.escape(L("rv.kartlegend_rubrik"))}</div>'
        "</div>"
    )
