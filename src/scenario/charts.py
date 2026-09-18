"""Chart construction for the Scenariosimulator page.

Kept out of the page script for the same reason as the Kontantinsats charts:
a figure builder that needs a Streamlit process to exercise cannot be tested.
"""

from __future__ import annotations

import plotly.graph_objects as go

from src.scenario.simulator import simulate
from src.ui.chart_theme import get_chart_layout
from src.ui.labels import L

#: Slider ranges, coarser than the sliders themselves. A grid fine enough to
#: match the 0.25 pp rate step would be 29 x 31 simulations for no extra insight.
RATE_STEPS = (-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0)
CPI_STEPS = (-4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0, 10.0)


def rate_inflation_surface(
    *,
    county_kod: str,
    baseline_panel: dict,
    income_shock: float = 0.0,
    price_shock: float = 0.0,
    rate_shock: float | None = None,
    cpi_shock: float | None = None,
) -> go.Figure:
    """Version C across the rate and inflation plane.

    The page's central lesson is that only the real rate, `R - pi`, reaches the
    formula. A slider shows one point on that plane and invites the conclusion
    that rate rises destroy affordability, which is true only when inflation is
    held still. The surface shows the whole plane, where equal values of
    `R - pi` form diagonal bands and make the point without prose.

    The upper right of the plane is flat because the real rate floor of 0.5 pp
    binds there. That is limitation M4 drawn rather than described: past the
    floor the index stops responding to further easing.

    Args:
        county_kod: County the page has selected.
        baseline_panel: The same dict handed to :func:`simulate`.
        income_shock: Income change, held across the grid.
        price_shock: Price change, held across the grid.
        rate_shock: Current rate slider, marked on the surface when given.
        cpi_shock: Current CPI slider, marked on the surface when given.

    Returns:
        A heatmap figure with the current scenario marked.
    """
    z = [
        [
            simulate(
                county_kod=county_kod,
                rate_shock=r,
                income_shock=income_shock,
                price_shock=price_shock,
                baseline_panel=baseline_panel,
                cpi_shock=c,
            )["scenario_v_c"]
            for c in CPI_STEPS
        ]
        for r in RATE_STEPS
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[f"{c:+.0f}" for c in CPI_STEPS],
        y=[f"{r:+.0f}" for r in RATE_STEPS],
        colorscale="RdYlGn",
        colorbar=dict(title=dict(text=L("sc.yta_skala"), side="right"), thickness=12),
        hovertemplate=L("sc.yta_hover"),
    ))

    # Where the user currently is. Without it the surface is an abstraction
    # sitting beside a result the reader cannot locate on it.
    if rate_shock is not None and cpi_shock is not None:
        fig.add_trace(go.Scatter(
            x=[f"{_nearest(cpi_shock, CPI_STEPS):+.0f}"],
            y=[f"{_nearest(rate_shock, RATE_STEPS):+.0f}"],
            mode="markers",
            marker=dict(size=15, symbol="circle-open", line=dict(width=3, color="#0B1F3F")),
            hovertemplate=L("sc.yta_du_ar_har"),
            showlegend=False,
        ))

    layout = get_chart_layout(height=330, showlegend=False)
    layout["xaxis"]["title"] = L("sc.yta_x_axel")
    layout["yaxis"]["title"] = L("sc.yta_y_axel")
    # Measured rather than guessed: a fixed left margin clipped the axis title.
    layout["yaxis"]["automargin"] = True
    layout["xaxis"]["automargin"] = True
    layout["margin"] = dict(r=10, t=20, b=40)
    fig.update_layout(**layout)
    return fig


def _nearest(value: float, steps: tuple[float, ...]) -> float:
    """The grid step closest to `value`, so the marker lands on a cell centre."""
    return min(steps, key=lambda s: abs(s - value))
