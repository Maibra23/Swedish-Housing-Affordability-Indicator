"""The chart layer, held to the design system the way the stylesheet already is.

`test_design_system_doc.py` checks the CSS class inventory in both directions,
`test_css_naming.py` rejects a class outside the `shai-` convention, and
`test_no_inline_copy.py` keeps user strings out of pages. **Nothing checked a
Plotly figure**, and that asymmetry is not hypothetical: the two charts added in
`60e150d` drifted on three axes at once and the suite stayed green. They passed
Plotly's built-in `RdYlGn`, which put a second and more saturated red-to-green
legend two pages from the map's; they hardcoded the primary navy as a hex
literal; and they set `displayModeBar` to `False` where the seven charts before
them set it to `"hover"`.

This file is the missing guard. It closes R14 in `docs/OPEN_RISKS.md` and item 18
in `docs/APP_GUIDE.md`.

**Three kinds of assertion, because there are three ways to drift.**

*Built figures* are exercised directly: every builder that can be called without
a Streamlit process is called, and the layout it returns is compared against
`get_chart_layout`. That catches a builder that assembles its own layout.

*Source text* is scanned for the two drifts a built figure cannot show. A colour
written as `"#B94A48"` produces the same pixel as `COLORS["high_risk"]`, so only
the source can tell them apart, and the point of a token is that changing it
moves every use. A built-in colorscale name is the same problem one level up.

*Call sites* are scanned for `displayModeBar`, which lives in the page rather
than in the figure and so is invisible to both of the above.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from src.kontantinsats.charts import affordability_gap_chart, comparison_barchart
from src.scenario.charts import (
    CPI_STEPS,
    RATE_STEPS,
    floor_boundary_intercept,
    rate_inflation_surface,
)
from src.ui.chart_theme import CHART_PALETTE, get_chart_layout
from src.ui.tokens import COLORS, DIVERGING_SCALE

ROOT = Path(__file__).resolve().parents[1]

#: Every file that builds a Plotly figure. Kept explicit rather than globbed so
#: that adding a chart module is a deliberate act that shows up in a diff.
FIGURE_SOURCES = (
    "src/kontantinsats/charts.py",
    "src/scenario/charts.py",
    "pages/01_Riksoversikt.py",
    "pages/02_Lan_jamforelse.py",
    "pages/03_Kommun_djupanalys.py",
    "pages/05_Scenario.py",
)

#: `chart_theme.py` defines the palette and `tokens.py` defines the colours, so
#: the literals there are the definition rather than a copy of it.
TOKEN_DEFINITION_SOURCES = ("src/ui/chart_theme.py", "src/ui/tokens.py")

HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")
COLORSCALE_LITERAL = re.compile(r"colorscale\s*=\s*[\"']([^\"']+)[\"']")
DISPLAY_MODE_BAR = re.compile(r"\"displayModeBar\":\s*([^,}\s]+)")

#: White is the hover label's text colour and comes from the shared layout.
ALLOWED_COLOURS = (
    set(COLORS.values()) | set(DIVERGING_SCALE) | set(CHART_PALETTE) | {"#FFFFFF"}
)


# ---------------------------------------------------------------------------
# Fixtures: the smallest real inputs each builder needs
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def county_baseline() -> dict:
    """A real county row, so the surface is exercised on real magnitudes.

    A synthetic baseline would work for the layout assertions and would quietly
    stop exercising the floor, which binds only when `R - pi` is small. It is
    small in the committed panel, which is the case worth guarding.
    """
    panel = pd.read_parquet(ROOT / "data" / "processed" / "panel_county.parquet")
    # The panel is ragged at the top: prices and income end before the policy
    # rate does, so `year.max()` is an imputed row with a missing price. Take the
    # last year where every input the simulator reads actually exists.
    complete = panel.dropna(
        subset=["median_income", "transaction_price_sek", "policy_rate", "cpi_yoy_pct"]
    )
    row = complete[complete["year"] == complete["year"].max()].iloc[0]
    return {
        "income": float(row["median_income"]),
        "transaction_price_sek": float(row["transaction_price_sek"]),
        "policy_rate": float(row["policy_rate"]),
        "cpi_yoy_pct": float(row["cpi_yoy_pct"]),
    }


def _figures(county_baseline: dict) -> dict:
    """Every builder callable without Streamlit, built once."""
    return {
        "comparison_barchart": comparison_barchart(
            y_values=[1.0, 2.0, 3.0, 4.0, 5.0],
            yaxis_title="Test",
            value_fmt="sek",
            best_key="latt_2026",
            worst_key="pre_2010",
        ),
        "affordability_gap_chart": affordability_gap_chart(
            price=4_000_000.0,
            income=500_000.0,
            lending_ceiling=5.5,
            min_down_pct=0.10,
        ),
        "rate_inflation_surface": rate_inflation_surface(
            county_kod="01",
            baseline_panel=county_baseline,
            rate_shock=2.0,
            cpi_shock=0.0,
        ),
    }


# ---------------------------------------------------------------------------
# Built figures
# ---------------------------------------------------------------------------

def test_every_builder_uses_the_shared_layout(county_baseline: dict) -> None:
    """A builder assembles traces. `get_chart_layout` owns the visual language."""
    theme = get_chart_layout()
    for name, fig in _figures(county_baseline).items():
        layout = fig.layout
        assert layout.font.family == theme["font"]["family"], f"{name} sets its own font"
        assert layout.font.color == theme["font"]["color"], f"{name} sets its own text colour"
        assert layout.plot_bgcolor == theme["plot_bgcolor"], f"{name} sets its own plot background"
        assert layout.paper_bgcolor == theme["paper_bgcolor"], f"{name} sets its own paper background"
        assert layout.hoverlabel.bgcolor == theme["hoverlabel"]["bgcolor"], (
            f"{name} sets its own hover label, so its tooltip will not match the site's"
        )


def _colour_strings(obj, found: list[str]) -> None:
    """Every `#rrggbb` anywhere in a figure's nested dicts and tuples."""
    if isinstance(obj, str):
        found.extend(HEX.findall(obj))
    elif isinstance(obj, dict):
        for value in obj.values():
            _colour_strings(value, found)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            _colour_strings(value, found)


def test_built_figures_only_contain_token_colours(county_baseline: dict) -> None:
    """Every colour in a rendered figure traces back to `COLORS` or a scale.

    `layout.template` is excluded deliberately: it is Plotly's own default
    template, carried on every figure whether or not the builder touched it, and
    it holds a full palette for trace types this project never draws. Asserting
    against it would test Plotly, not us.
    """
    for name, fig in _figures(county_baseline).items():
        payload = fig.to_plotly_json()
        payload["layout"] = {
            k: v for k, v in payload.get("layout", {}).items() if k != "template"
        }
        found: list[str] = []
        _colour_strings(payload, found)
        stray = sorted({c for c in found if c not in ALLOWED_COLOURS})
        assert not stray, (
            f"{name} renders {stray}, which is not a design token. A colour that "
            f"is not a token does not move when the palette moves."
        )


def test_the_surface_reads_the_diverging_scale_from_the_other_end(
    county_baseline: dict,
) -> None:
    """The one diverging ramp, reversed, because high is good here and low is
    good on the map. Reversal is the point: green must mean "better for a
    household" on both pages.
    """
    surface = _figures(county_baseline)["rate_inflation_surface"]
    scale = [colour for _, colour in surface.data[0].colorscale]
    assert scale == list(reversed(DIVERGING_SCALE)), (
        "the surface is no longer on the project's diverging scale"
    )
    assert surface.data[0].zmid == 0, "a diverging scale needs a meaningful midpoint"


# ---------------------------------------------------------------------------
# Source text
# ---------------------------------------------------------------------------

def test_no_colour_literals_outside_the_token_modules() -> None:
    """`"#B94A48"` and `COLORS["high_risk"]` paint the same pixel today. Only one
    of them still paints the right one after the palette moves.
    """
    offenders: list[str] = []
    for rel in FIGURE_SOURCES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for colour in HEX.findall(line):
                offenders.append(f"{rel}:{line_no} {colour}")
    assert not offenders, (
        "colour literals in a figure builder: "
        + ", ".join(offenders)
        + ". Import the token instead."
    )


def test_no_builtin_plotly_colorscale_names() -> None:
    """A built-in ramp is a second colour language the project did not choose."""
    offenders: list[str] = []
    for rel in FIGURE_SOURCES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name in COLORSCALE_LITERAL.findall(line):
                offenders.append(f"{rel}:{line_no} colorscale={name!r}")
    assert not offenders, (
        "built-in Plotly colorscales: "
        + ", ".join(offenders)
        + ". Use DIVERGING_SCALE, reversed if the quantity runs the other way."
    )


def test_the_token_modules_are_where_the_colours_live() -> None:
    """The exemption above is only honest if the definitions are actually there."""
    for rel in TOKEN_DEFINITION_SOURCES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert HEX.search(text), f"{rel} is exempt from the literal check but defines no colours"


# ---------------------------------------------------------------------------
# Call sites
# ---------------------------------------------------------------------------

def test_the_toolbar_setting_is_the_same_everywhere() -> None:
    """`displayModeBar` lives in the page, not the figure, so no built figure can
    show this drift. Two charts on one site that disagree about whether a toolbar
    appears read as a bug to the person using them.
    """
    settings: dict[str, list[str]] = {}
    for path in sorted(ROOT.glob("pages/*.py")) + sorted(ROOT.glob("src/**/*.py")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for value in DISPLAY_MODE_BAR.findall(line):
                settings.setdefault(value, []).append(
                    f"{path.relative_to(ROOT)}:{line_no}"
                )
    assert len(settings) == 1, (
        "charts disagree about the toolbar: "
        + "; ".join(f"{k} at {v}" for k, v in sorted(settings.items()))
    )


# ---------------------------------------------------------------------------
# Geometry the caption depends on
# ---------------------------------------------------------------------------

def test_both_surface_axes_move_in_the_same_unit(county_baseline: dict) -> None:
    """Equal steps plus a locked aspect are what make a line of equal real rate
    45 degrees on screen. Without both, the caption saying so is aspirational.
    """
    rate_gaps = {round(b - a, 6) for a, b in zip(RATE_STEPS, RATE_STEPS[1:])}
    cpi_gaps = {round(b - a, 6) for a, b in zip(CPI_STEPS, CPI_STEPS[1:])}
    assert rate_gaps == cpi_gaps, (
        f"rate steps {rate_gaps} against CPI steps {cpi_gaps}: unequal steps tilt "
        f"every line of constant real rate"
    )

    surface = _figures(county_baseline)["rate_inflation_surface"]
    assert surface.layout.yaxis.scaleanchor == "x"
    assert surface.layout.yaxis.scaleratio == 1


def test_the_drawn_floor_is_where_the_floor_actually_binds(county_baseline: dict) -> None:
    """The defect this replaces was a caption that named the wrong corner. Prose
    can be wrong about a picture; a line derived from the same arithmetic cannot.
    """
    from src.scenario.simulator import simulate

    intercept = floor_boundary_intercept(county_baseline)
    disagreements = 0
    for rate in RATE_STEPS:
        for cpi in CPI_STEPS:
            run = simulate(
                county_kod="01",
                rate_shock=rate,
                income_shock=0.0,
                price_shock=0.0,
                baseline_panel=county_baseline,
                cpi_shock=cpi,
            )
            floor_binds = run["real_rate_scen"] <= 0.5 + 1e-9
            below_line = rate <= cpi + intercept + 1e-9
            if floor_binds != below_line:
                disagreements += 1
    assert disagreements == 0, (
        f"{disagreements} grid cells where the drawn boundary disagrees with the "
        f"floor the simulator applies"
    )
