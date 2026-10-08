"""CSS that keeps chart and map text inside its box at any width.

Its own module rather than a block inside `css_components.py`, which the
file-size guard pushed past 400 lines. Everything here exists for one reason:
text that a chart cannot wrap is moved to page content that can, and a column
holding a chart is never squeezed below the width its text needs. Composed
after the component sheet, as the block it came from was.
"""

from __future__ import annotations

CSS = """/* ---- Chart legend in the page, not in the figure ---- */
/* A Plotly legend lives inside a figure of fixed height, so 21 entries on a
   phone were squeezed into a scroll box and cut off. As page content the
   entries wrap onto as many lines as the width needs, at any width. */
.shai-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 14px;
    margin: 4px 0 2px 0;
    font-size: 12px;
    line-height: 1.4;
    color: #4B5563;
}
.shai-legend-item { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
.shai-legend-swatch { width: 14px; height: 3px; border-radius: 2px; flex-shrink: 0; }

/* ---- Map colour scale in the page, not in the map ---- */
/* branca's legend is a fixed 450 px SVG; on a narrower map both ends and the
   caption were cut. This bar takes the map's width and the caption wraps. */
.shai-map-legend { margin: 8px 0 2px 0; font-size: 12px; line-height: 1.4; color: #4B5563; }
.shai-map-legend-bar { height: 10px; border-radius: 2px; }
.shai-map-legend-ticks { position: relative; height: 18px; font-variant-numeric: tabular-nums; }
.shai-map-legend-ticks span { position: absolute; top: 2px; white-space: nowrap; }
.shai-map-legend-caption { margin-top: 2px; }

/* ---- Chart columns stack before they get too narrow ---- */
/* Streamlit keeps columns side by side down to a 640 px viewport, so with the
   sidebar open a tablet gave each of three charts about 140 px and their
   titles, tick labels and annotations ran off the edge. A column holding a
   chart or a map now keeps at least this width and wraps to its own row when
   the row is too narrow; above that, Streamlit's ratios are unchanged. */
[data-testid="stHorizontalBlock"]:has([data-testid="stPlotlyChart"], iframe) { flex-wrap: wrap; }
[data-testid="stHorizontalBlock"]:has([data-testid="stPlotlyChart"], iframe) > [data-testid="stColumn"] {
    min-width: min(100%, 260px);
}
"""
