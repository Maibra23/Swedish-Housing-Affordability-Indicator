"""Chart construction for the Scenariosimulator page.

Kept out of the page script for the same reason as the Kontantinsats charts:
a figure builder that needs a Streamlit process to exercise cannot be tested.
"""

from __future__ import annotations

import plotly.graph_objects as go

from src.scenario.simulator import simulate
from src.ui.chart_theme import get_chart_layout
from src.ui.labels import L
from src.ui.tokens import COLORS, DIVERGING_SCALE

#: The grid spans exactly the two sliders it explains, so the marked scenario is
#: always inside the plane rather than pinned to its edge. Rate: -2 to +5 pp.
#: Price: -25 to +25 %.
RATE_MIN, RATE_MAX = -2.0, 5.0
PRICE_MIN, PRICE_MAX = -25, 25

#: Grid steps, in each axis's own unit. They match the slider steps, so every
#: position a reader can set is a grid point.
RATE_STEP = 0.25
PRICE_STEP = 5


def _steps(low: float, high: float, step: float) -> tuple[float, ...]:
    """Inclusive range as a tuple, rounded so floats print cleanly on an axis."""
    return tuple(round(low + i * step, 2) for i in range(int(round((high - low) / step)) + 1))


RATE_STEPS = _steps(RATE_MIN, RATE_MAX, RATE_STEP)
PRICE_STEPS = _steps(PRICE_MIN, PRICE_MAX, PRICE_STEP)


def _surface_colorscale() -> list[list]:
    """`DIVERGING_SCALE` as Plotly colorscale stops, read the same way as the map.

    The project owns one diverging ramp, and the map spends it on a z-score where
    low is good. This surface plots a change in the cost share, where low is good
    as well, so the ramp is used unchanged and green means "cheaper for a
    household" on both pages. (The old surface plotted a change in an
    affordability ratio, where high was good, and had to reverse the ramp.)
    """
    stops = list(DIVERGING_SCALE)
    last = len(stops) - 1
    return [[i / last, colour] for i, colour in enumerate(stops)]


def rate_price_surface(
    *,
    county_kod: str,
    baseline_panel: dict,
    income_shock: float = 0.0,
    rate_shock: float | None = None,
    price_shock: float | None = None,
) -> go.Figure:
    """The change in the cost share across the rate and price plane.

    A slider shows one point and invites a one-dial conclusion. The surface
    shows how far a price fall offsets a rate rise for this county, which is
    the trade-off 2022–2023 actually ran: rates up three points, prices down.

    **Why the change and not the level.** The change from baseline has a
    meaningful midpoint at zero, ties the surface to the "Förändring" KPI
    directly above it, and cannot be mistaken for the map's score.

    Args:
        county_kod: County the page has selected.
        baseline_panel: The same dict handed to :func:`simulate`.
        income_shock: Income change, held across the grid.
        rate_shock: Current rate slider, marked on the surface when given.
        price_shock: Current price slider (relative, -0.10 is -10 %), marked
            on the surface when given.

    Returns:
        A contour figure of the change from baseline, with the current scenario
        marked.
    """
    runs = [
        [
            simulate(
                county_kod=county_kod,
                rate_shock=r,
                income_shock=income_shock,
                price_shock=p / 100.0,
                baseline_panel=baseline_panel,
            )
            for p in PRICE_STEPS
        ]
        for r in RATE_STEPS
    ]
    z = [[run["delta_pct"] for run in row] for row in runs]
    # Level and rate travel with each cell so the hover can state what the
    # colour is a change *from*, which a percentage on its own cannot.
    customdata = [[[run["scenario_v_c"], run["scenario_rate"]] for run in row] for row in runs]

    fig = go.Figure(go.Contour(
        z=z,
        x=list(PRICE_STEPS),
        y=list(RATE_STEPS),
        customdata=customdata,
        colorscale=_surface_colorscale(),
        # Fixed bounds rather than per-county autoscaling: a colour then means
        # the same change in every län, which is what makes two counties
        # comparable at a glance. Values outside the range clamp in colour only.
        zmin=-60.0,
        zmax=60.0,
        zmid=0.0,
        contours=dict(
            coloring="heatmap",
            showlines=True,
            showlabels=True,
            labelfont=dict(size=10, color=COLORS["text_secondary"]),
        ),
        line=dict(width=0.6, color=COLORS["grid"]),
        colorbar=dict(
            title=dict(text=L("sc.yta_skala"), side="right"),
            thickness=12,
            ticksuffix=" %",
        ),
        hovertemplate=L("sc.yta_hover"),
    ))

    # Where the user currently is. Without it the surface is an abstraction
    # sitting beside a result the reader cannot locate on it.
    if rate_shock is not None and price_shock is not None:
        fig.add_trace(go.Scatter(
            x=[price_shock * 100.0],
            y=[rate_shock],
            mode="markers",
            marker=dict(
                size=15,
                symbol="circle-open",
                line=dict(width=3, color=COLORS["primary"]),
            ),
            hovertemplate=L("sc.yta_du_ar_har"),
            showlegend=False,
        ))

    layout = get_chart_layout(height=380, showlegend=False)
    layout["xaxis"]["title"] = L("sc.yta_x_axel")
    layout["yaxis"]["title"] = L("sc.yta_y_axel")
    # Measured rather than guessed: a fixed left margin clipped the axis title.
    layout["yaxis"]["automargin"] = True
    layout["xaxis"]["automargin"] = True
    layout["xaxis"]["dtick"] = 5
    layout["yaxis"]["dtick"] = 1
    layout["xaxis"]["ticksuffix"] = " %"
    layout["xaxis"]["range"] = [PRICE_MIN, PRICE_MAX]
    layout["yaxis"]["range"] = [RATE_MIN, RATE_MAX]
    layout["margin"] = dict(r=10, t=20, b=40)
    fig.update_layout(**layout)
    return fig
