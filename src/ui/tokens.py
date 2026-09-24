"""Design tokens: the palette and the diverging scale.

Split out of `css.py` (902 lines) by T3.3 so the values can be imported without
pulling in three hundred lines of stylesheet, and so a colour change has one
obvious home. `COLORS["accent"]` is also what `.streamlit/config.toml` sets as
`primaryColor`, which drives Streamlit's own widget accents — keep the two in step.

Finding K: files over the project's own limits.
"""

from __future__ import annotations

COLORS = {
    "primary": "#0B1F3F",
    "primary_light": "#1B2A4A",
    "secondary": "#4A6FA5",
    "accent": "#C4A35A",
    "low_risk": "#2E7D5B",
    "medium_risk": "#D4A03C",
    "high_risk": "#B94A48",
    "bg": "#F7F8FA",
    "card_bg": "#FFFFFF",
    "text_primary": "#1A1A2E",
    "text_secondary": "#6B7280",
    "text_tertiary": "#9CA3AF",
    "border": "#EEF0F3",
    "grid": "#E5E7EB",
    "hover": "#F9FAFB",
}

DIVERGING_SCALE = [
    "#2E7D5B", "#5B9E78", "#A8C4A4",
    "#E5E7EB",
    "#E8BE7C", "#D4A03C", "#B94A48",
]

