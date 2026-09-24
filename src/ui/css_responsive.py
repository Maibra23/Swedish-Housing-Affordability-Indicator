"""Responsive breakpoints and accessibility rules, plus the closing `</style>`.

    Last in the composed sheet by necessity: these override the rules above, and
    CSS resolves ties by source order. Moving this earlier silently disables it.

Split out of the 902-line `css.py` by T3.3 (Finding K). The slices are contiguous
and **order-preserving**: CSS resolves equal-specificity conflicts by source
order, so re-ordering these sheets would change the rendering. `css.inject_css()`
concatenates them in the order documented in that module.
"""

from __future__ import annotations

CSS = """/* ==== RESPONSIVE ==== */
@media (max-width: 900px) {
    .shai-stat-strip { grid-template-columns: repeat(2, 1fr); }
    .shai-steps { flex-direction: column; gap: 12px; }
    .shai-step-connector {
        transform: rotate(90deg);
        padding: 4px 0;
        justify-content: center;
    }
}
@media (max-width: 520px) {
    .shai-stat-strip { grid-template-columns: 1fr; }
    .shai-stat-cell {
        border-right: none;
        border-bottom: 1px solid #EEF0F3;
    }
    .shai-stat-cell:last-child { border-bottom: none; }
    .shai-hero { padding-left: 1rem; padding-right: 1rem; }
}

/* ==== ACCESSIBILITY ==== */
@media (prefers-reduced-motion: reduce) {
    .shai-step,
    .shai-nav-card,
    .shai-step-arrow-svg,
    .shai-weight-bar {
        transition: none !important;
    }
}
</style>
"""


def inject_css() -> None:
    """Inject global CSS into the current Streamlit page."""
