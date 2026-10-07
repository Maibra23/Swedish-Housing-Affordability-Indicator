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


#: One colour per county, for the Län jämförelse trend chart.
#:
#: That chart drew all 21 counties in a single muted colour with Stockholm
#: highlighted, which made every other line anonymous: a reader could see the
#: shape of the spread but could not tell which county was which. These are 21
#: evenly spaced hues at controlled lightness, generated rather than picked so
#: the set is reproducible, then darkened individually until each clears 3:1
#: contrast against the white card — the point at which a 2px line stays legible.
#:
#: Muted on purpose. The palette has to sit under the navy and gold without
#: competing, and a chart with 21 saturated lines is unreadable however
#: distinct the colours are. Order is stable, so a county keeps its colour
#: between renders and between formula tabs.
COUNTY_PALETTE = (
    "#8F4532", "#AD7E52", "#9F8A41",
    "#8A8F32", "#809C49", "#649F41",
    "#3A8F32", "#4EA660", "#419F6F",
    "#328F7A", "#4EA1A6", "#417F9F",
    "#32558F", "#5259AD", "#54419F",
    "#60328F", "#9852AD", "#9F419A",
    "#8F3270", "#AD5274", "#9F4149",
)
