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
#: CPI: -5 to +10 pp.
RATE_MIN, RATE_MAX = -2.0, 5.0
CPI_MIN, CPI_MAX = -5.0, 10.0

#: One step, in percentage points, on **both** axes. The earlier grid moved 1 pp
#: per rate cell and 2 pp per CPI cell, which tilted every line of constant
#: `R - pi` to two cells up for one across while the caption called them
#: diagonals. Equal steps plus `scaleanchor` below make the caption true.
GRID_STEP = 0.5

#: The real-rate floor, in percentage points. Mirrors `simulate`, which applies
#: it independently; see the caution in docs/APP_GUIDE.md section 7 about
#: the floor living in two files in two different units.
REAL_RATE_FLOOR = 0.5


def _steps(low: float, high: float, step: float = GRID_STEP) -> tuple[float, ...]:
    """Inclusive range as a tuple, rounded so floats print cleanly on an axis."""
    return tuple(round(low + i * step, 2) for i in range(int(round((high - low) / step)) + 1))


RATE_STEPS = _steps(RATE_MIN, RATE_MAX)
CPI_STEPS = _steps(CPI_MIN, CPI_MAX)


def _surface_colorscale() -> list[list]:
    """`DIVERGING_SCALE`, reversed, as Plotly colorscale stops.

    The project owns one diverging ramp and the map spends it on a z-score where
    low is good. This surface plots a change in affordability where **high** is
    good, so the same ramp is read from the other end. Reversing keeps green
    meaning "better for a household" on both pages, which is the property that
    matters; using Plotly's own `RdYlGn` here put a second, more saturated
    red-to-green legend two pages from the map's and is why item 17 exists.
    """
    stops = list(reversed(DIVERGING_SCALE))
    last = len(stops) - 1
    return [[i / last, colour] for i, colour in enumerate(stops)]


def rate_inflation_surface(
    *,
    county_kod: str,
    baseline_panel: dict,
    income_shock: float = 0.0,
    price_shock: float = 0.0,
    rate_shock: float | None = None,
    cpi_shock: float | None = None,
) -> go.Figure:
    """Affordability across the rate and inflation plane, against the baseline.

    The page's central lesson is that only the real rate, `R - pi`, reaches the
    formula. A slider shows one point on that plane and invites the conclusion
    that rate rises destroy affordability, which is true only when inflation is
    held still. The surface shows the whole plane at once.

    **Why the change and not the level.** Plotting raw Version C spent most of
    the colour range on a region the grid barely visits: Version C is a
    reciprocal of the real rate, so past the floor every cell returns one
    repeated number while the interesting variation crushes into a corner. On the
    old 8 x 8 grid 36 of 64 cells were identical and 20 of the remaining 28 sat
    below 4.1. The change from baseline has a meaningful midpoint at zero, ties
    the surface to the "Förändring" KPI directly above it, and cannot be mistaken
    for the map's score.

    **Contours rather than cells.** Iso-lines of constant real rate say "these two
    dials collapse into one" more directly than colour bands, and they remove the
    quantisation artefact that made the old heatmap's diagonals look like stairs.

    Args:
        county_kod: County the page has selected.
        baseline_panel: The same dict handed to :func:`simulate`.
        income_shock: Income change, held across the grid.
        price_shock: Price change, held across the grid.
        rate_shock: Current rate slider, marked on the surface when given.
        cpi_shock: Current CPI slider, marked on the surface when given.

    Returns:
        A contour figure: change from baseline, with the floor boundary drawn and
        the current scenario marked.
    """
    runs = [
        [
            simulate(
                county_kod=county_kod,
                rate_shock=r,
                income_shock=income_shock,
                price_shock=price_shock,
                baseline_panel=baseline_panel,
                cpi_shock=c,
            )
            for c in CPI_STEPS
        ]
        for r in RATE_STEPS
    ]
    z = [[run["delta_pct"] for run in row] for row in runs]
    # Level and real rate travel with each cell so the hover can state what the
    # colour is a change *from*, which a percentage on its own cannot.
    customdata = [
        [[run["scenario_v_c"], run["real_rate_scen"]] for run in row] for row in runs
    ]

    fig = go.Figure(go.Contour(
        z=z,
        x=list(CPI_STEPS),
        y=list(RATE_STEPS),
        customdata=customdata,
        colorscale=_surface_colorscale(),
        # Fixed bounds rather than per-county autoscaling: a colour then means
        # the same change in every län, which is what makes two counties
        # comparable at a glance. Values outside the range clamp in colour only.
        zmin=-100.0,
        zmax=100.0,
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

    _add_floor_boundary(fig, baseline_panel)

    # Where the user currently is. Without it the surface is an abstraction
    # sitting beside a result the reader cannot locate on it. The axes are
    # numeric now, so the marker sits on the exact scenario rather than snapping
    # to the nearest cell centre.
    if rate_shock is not None and cpi_shock is not None:
        fig.add_trace(go.Scatter(
            x=[cpi_shock],
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
    layout["xaxis"]["dtick"] = 1
    layout["yaxis"]["dtick"] = 1
    # One percentage point is the same distance on both axes, so a line of equal
    # real rate is drawn at 45 degrees and the caption describing it is true of
    # the picture rather than of the arithmetic behind it.
    layout["yaxis"]["scaleanchor"] = "x"
    layout["yaxis"]["scaleratio"] = 1
    layout["margin"] = dict(r=10, t=20, b=40)
    fig.update_layout(**layout)
    return fig


def floor_boundary_intercept(baseline_panel: dict) -> float:
    """Rate shock at which the floor starts to bind when the CPI shock is zero.

    The scenario real rate is `(R - pi) + rate_shock - cpi_shock`, so the floor
    binds along the line `rate_shock = cpi_shock + (floor - (R - pi))`. That is a
    45 degree line whose intercept is returned here, separately from the figure,
    so the geometry can be asserted without building a chart.
    """
    baseline_real = baseline_panel["policy_rate"] - baseline_panel["cpi_yoy_pct"]
    return REAL_RATE_FLOOR - baseline_real


def _add_floor_boundary(fig: go.Figure, baseline_panel: dict) -> None:
    """Draw the `R - pi = 0.5` line, which limitation M4 previously only claimed.

    Below and to the right of it the index stops responding: further easing
    cannot lower a real rate that is already at its floor. Drawing it turns a
    caption assertion about which corner is flat into something the reader can
    see, and it was that assertion that was wrong on screen (item 13).
    """
    intercept = floor_boundary_intercept(baseline_panel)
    xs = [CPI_MIN, CPI_MAX]
    ys = [x + intercept for x in xs]

    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line=dict(color=COLORS["text_secondary"], width=1.5, dash="dash"),
        hovertemplate=L("sc.yta_golv_hover"),
        showlegend=False,
    ))

    # Anchored at the midpoint of the visible part of the line rather than at an
    # end, where it would sit outside the plot for most baselines.
    lo = max(CPI_MIN, RATE_MIN - intercept)
    hi = min(CPI_MAX, RATE_MAX - intercept)
    if lo < hi:
        mid_x = (lo + hi) / 2
        fig.add_annotation(
            x=mid_x,
            y=mid_x + intercept,
            text=L("sc.yta_golv_linje"),
            showarrow=False,
            yshift=-14,
            font=dict(size=11, color=COLORS["text_secondary"]),
        )
