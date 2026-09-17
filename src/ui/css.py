"""Single CSS injection point for the SHAI dashboard.

The stylesheet was one 902-line module (Finding K). T3.3 split it by role and this
module composes the pieces **in cascade order** — layout, components, landing,
responsive. That order is load-bearing twice over: the `@import` for the webfont
must precede every rule or the browser ignores it, and the responsive and
accessibility overrides must come last or equal-specificity rules above them win.

The injection point stays single on purpose. Streamlit re-runs a page top to
bottom, and two injection sites means two `<style>` blocks racing to define the
same rule.

`COLORS` and `DIVERGING_SCALE` are re-exported so existing imports keep working;
new code should take them from `src.ui.tokens`.
"""

from __future__ import annotations

import streamlit as st

from src.ui.css_components import CSS as _COMPONENTS
from src.ui.css_landing import CSS as _LANDING
from src.ui.css_layout import CSS as _LAYOUT
from src.ui.css_responsive import CSS as _RESPONSIVE
from src.ui.tokens import COLORS, DIVERGING_SCALE

__all__ = ["COLORS", "DIVERGING_SCALE", "GLOBAL_CSS", "inject_css"]

# Order is cascade order. Do not sort these.
GLOBAL_CSS = _LAYOUT + _COMPONENTS + _LANDING + _RESPONSIVE


def inject_css() -> None:
    """Inject the composed stylesheet into the current Streamlit page.

    Inlined, at ~24 KB per page load, because Streamlit cannot serve it any other
    way. Task C1 tried: `server.enableStaticServing` does serve `./static/`, but
    it returns `.css` as `Content-Type: text/plain` alongside
    `X-Content-Type-Options: nosniff`, so a browser refuses to apply the
    stylesheet and the app renders unstyled. Measured, not assumed — see C1 in
    docs/OPTIMIZATION_PLAN.md.

    `GLOBAL_CSS` already carries its own `<style>` wrapper, so it is emitted
    verbatim rather than wrapped again.
    """
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
