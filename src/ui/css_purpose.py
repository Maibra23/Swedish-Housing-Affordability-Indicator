"""Purpose panel CSS: the "what this page is for" block on Sida 04 and 05.

Its own sheet for the same reason `css_interpret.py` has one — the panel is a
distinct component, and folding it into `css_components.py` took that file past
the 400-line limit. Composed after the component sheet so the cascade order is
preserved: this only adds, it never overrides.
"""

from __future__ import annotations

CSS = """/* Purpose panel — the "what is this page for" block that opens Sida 04 and 05.
   Quiet by design: it is read once and then skipped past every visit after,
   so it must not compete with the controls or the result. */
.shai-purpose { padding: 2px 0; }
.shai-purpose-body {
    font-size: 14.5px;
    line-height: 1.62;
    color: #6B7280;
    margin-top: 8px;
}
.shai-purpose-body p { margin: 0 0 10px; }
.shai-purpose-body p:last-child { margin-bottom: 0; }
.shai-purpose-when-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9CA3AF;
    margin-top: 16px;
}
.shai-purpose-when {
    margin: 8px 0 0;
    padding-left: 18px;
    font-size: 14px;
    line-height: 1.6;
    color: #6B7280;
}
.shai-purpose-when li { margin-bottom: 4px; }
.shai-purpose-when li:last-child { margin-bottom: 0; }
"""
