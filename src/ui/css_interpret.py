"""Component CSS for the result interpretation panel.

Its own module rather than a block inside `css_components.py`, which the
file-size guard pushed past 400 lines. Composed after the component sheet so
equal-specificity rules resolve in the documented order.
"""

from __future__ import annotations

CSS = """/* ---- Result interpretation panel ----
   Severity is carried by a dot, not by the sentence. Colouring 13px body text
   costs more legibility than the signal is worth, and the rest of the site
   already separates indicator from prose this way: the risk legend and the risk
   pills both pair a coloured mark with dark text.
   Colours are the existing three risk tokens rather than a parallel scale, so
   green, gold and red keep meaning the same thing here as on the map. */
.shai-interpret {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    font-size: 13.5px;
    line-height: 1.6;
    color: #1A1A2E;
    padding: 8px 0;
    border-bottom: 1px solid #EEF0F3;
}
.shai-interpret:last-child { border-bottom: none; }
.shai-interpret:first-child { padding-top: 2px; }
.shai-interpret-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
    margin-top: 7px;
}
.shai-interpret--critical .shai-interpret-dot { background: #B94A48; }
.shai-interpret--warning  .shai-interpret-dot { background: #D4A03C; }
.shai-interpret--good     .shai-interpret-dot { background: #2E7D5B; }
.shai-interpret--note     .shai-interpret-dot { background: #9CA3AF; }
.shai-interpret--critical { font-weight: 500; }
"""
