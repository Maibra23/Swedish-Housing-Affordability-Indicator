"""Chart construction for the Kontantinsats page.

Extracted from the page by T3.11 (Finding K). Building a Plotly figure is not
layout, and a 56-line figure builder inside a page script cannot be exercised
without starting Streamlit. This module takes values and returns a `go.Figure`.

`src.ui.chart_theme.get_chart_layout` still owns the shared visual language; this
only assembles the traces and the reference lines.
"""

from __future__ import annotations

import plotly.graph_objects as go

from src.kontantinsats.engine import REGIMES
from src.kontantinsats.regions import REGIME_ACCENT_COLORS, REGIME_KEYS
from src.ui.chart_theme import get_chart_layout
from src.ui.components import format_sek
from src.ui.labels import L
from src.ui.tokens import COLORS

def fmt_delta_sek(delta: float) -> str | None:
    """Format a SEK delta: hide zeros, round to tkr when >= 10 000."""
    if abs(delta) < 1:
        return None
    if abs(delta) >= 10_000:
        tkr = round(delta / 1_000)
        sign = "+" if tkr > 0 else ""
        return f"{sign}{tkr}\u00A0tkr"
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:,.0f}\u00A0SEK".replace(",", "\u00A0")




def comparison_barchart(
    *,
    y_values: list[float],
    yaxis_title: str,
    value_fmt: str,
    best_key: str,
    worst_key: str,
    regime_keys: list[str] | None = None,
    ref_lines: list[dict] | None = None,
) -> go.Figure:
    """Build the regime comparison bar chart.

    Args:
        y_values: One value per regime, in `regime_keys` order.
        yaxis_title: Axis label.
        value_fmt: "sek", "years", or anything else for `str()`.
        best_key: Regime to colour as the low-risk outcome.
        worst_key: Regime to colour as the high-risk outcome.
        regime_keys: Regime order. Defaults to `REGIME_KEYS`.
        ref_lines: Horizontal reference lines, each a dict with at least `y`.

    Returns:
        A themed Plotly figure.

    The highlighted regimes are passed in rather than read from module state: the
    page computes them per metric (cheapest by monthly cost is not the same regime
    as fastest to save for), and the extraction in T3.11 turned three page globals
    into silent NameErrors when they were read from here.
    """
    keys = regime_keys if regime_keys is not None else REGIME_KEYS
    fig = go.Figure()

    labels = [REGIMES[k]["label"] for k in keys]
    bar_colors: list[str] = []
    for k in keys:
        if k == best_key:
            bar_colors.append(COLORS["low_risk"])
        elif k == worst_key:
            bar_colors.append(COLORS["high_risk"])
        else:
            bar_colors.append(REGIME_ACCENT_COLORS.get(k, COLORS["secondary"]))

    text = []
    for v in y_values:
        if value_fmt == "sek":
            text.append(f"{v:,.0f} SEK".replace(",", "\u00A0"))
        elif value_fmt == "years":
            text.append(f"{v:.1f}".replace(".", ",") + L("ki.ar"))
        else:
            text.append(str(v))

    fig.add_trace(
        go.Bar(
            x=labels,
            y=y_values,
            marker_color=bar_colors,
            marker_line_width=0,
            text=text,
            textposition="outside",
            textfont=dict(family="IBM Plex Mono, monospace", size=12),
            hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
        )
    )

    if ref_lines:
        for rl in ref_lines:
            fig.add_hline(
                y=rl["y"],
                line_dash=rl.get("dash", "dot"),
                line_color=rl.get("color", COLORS["text_secondary"]),
                line_width=rl.get("width", 1.5),
                annotation_text=rl.get("label", ""),
                annotation_position=rl.get("annotation_position", "top left"),
                annotation_font_size=11,
                annotation_font_color=rl.get(
                    "annotation_font_color", COLORS["text_secondary"]
                ),
            )

    layout = get_chart_layout(height=380, yaxis_title=yaxis_title, showlegend=False)
    fig.update_layout(**layout)
    return fig


def comparison_tab_specs(*, monthly_income: float) -> tuple[dict, ...]:
    """Specs for the three regime-comparison tabs.

    The page rendered these as three near-identical 38-line blocks. Collapsed to a
    spec and one loop in T3.11, and moved here because reference lines and axis
    labels are presentation data for the chart, not page wiring.

    Args:
        monthly_income: Gross monthly income, for the 30 % affordability line.

    Returns:
        One dict per tab: tab label, heading, `results` key, axis title, value
        format, caption and reference lines.
    """
    return (
        {
            "tab": L("ki.manadskostnad"),
            "heading": L("ki.manadskostnad_per_regelverk"),
            "metric": "monthly_total",
            "yaxis": L("ki.manadskostnad_sek"),
            "value_fmt": "sek",
            "caption": L("ki.lagre_manadskostnad_innebar_mindre_lopande"),
            "ref_lines": [
                {
                    "y": monthly_income * 0.30,
                    "color": COLORS["text_secondary"],
                    "dash": "dot",
                    "width": 1.5,
                    "label": L("ki.30_av_manadsink_v0_sek", v0=format_sek(monthly_income * 0.30)),
                }
            ],
        },
        {
            "tab": L("ki.ar_att_spara"),
            "heading": L("ki.ar_att_spara_kontantinsats"),
            "metric": "years_to_save",
            "yaxis": L("ki.ar_att_spara"),
            "value_fmt": "years",
            "caption": L("ki.sparkvoten_paverkar_framst_sparar"),
            "ref_lines": [
                {
                    "y": 5,
                    "color": COLORS["low_risk"],
                    "dash": "dot",
                    "width": 1.5,
                    "label": L("ki.5_ar_tillganglig"),
                    "annotation_position": "bottom right",
                    "annotation_font_color": COLORS["low_risk"],
                },
                {
                    "y": 10,
                    "color": COLORS["high_risk"],
                    "dash": "dot",
                    "width": 1.5,
                    "label": L("ki.10_ar_otillganglig"),
                    "annotation_position": "top left",
                    "annotation_font_color": COLORS["high_risk"],
                },
            ],
        },
        {
            "tab": "Kvarvarande inkomst",
            "heading": "Kvarvarande inkomst per regelverk",
            "metric": "residual_income",
            "yaxis": L("ki.kvarvarande_inkomst_sek_ar"),
            "value_fmt": "sek",
            "caption": L("ki.hogre_kvarvarande_inkomst_innebar_mer"),
            "ref_lines": [
                {
                    "y": 0,
                    "color": COLORS["high_risk"],
                    "dash": "dash",
                    "width": 1.5,
                    "label": L("ki.nollgrans"),
                }
            ],
        },
    )


def affordability_gap_chart(
    *,
    price: float,
    income: float,
    lending_ceiling: float,
    min_down_pct: float,
) -> go.Figure:
    """Maximum supportable price against the price actually being asked.

    The page reports how long a deposit takes to save. It does not report whether
    the purchase is reachable at all, which for the expensive half of the panel is
    the question that governs the answer. This inverts the loan arithmetic: at the
    lending ceiling, and with this regime's deposit, the largest price this income
    supports is

        max_price = income * ceiling / (1 - min_down_pct)

    Drawn as two bars rather than a ratio because the gap between them is the
    quantity a buyer acts on, and a gap is easier to read as a length than as a
    multiple.

    Args:
        price: The region's actual transaction price.
        income: Household income used by the calculation.
        lending_ceiling: Loan-to-income multiple a bank will normally lend to.
        min_down_pct: Deposit share under the regime being shown.

    Returns:
        A horizontal bar figure.
    """
    max_price = income * lending_ceiling / (1 - min_down_pct)
    reachable = price <= max_price
    gap = price - max_price

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[L("ki.gap_faktiskt_pris"), L("ki.gap_max_pris")],
        x=[price, max_price],
        orientation="h",
        marker_color=[
            COLORS["low_risk"] if reachable else COLORS["high_risk"],
            COLORS["secondary"],
        ],
        marker_line_width=0,
        text=[f"{format_sek(price)} SEK", f"{format_sek(max_price)} SEK"],
        textposition="auto",
        textfont=dict(family="IBM Plex Mono, monospace", size=12),
        hovertemplate="%{y}<br>%{x:,.0f} SEK<extra></extra>",
        width=0.55,
    ))

    # The shortfall is the actionable number, so it is annotated rather than left
    # to be inferred from two bar lengths.
    fig.add_annotation(
        x=max(price, max_price),
        y=0 if not reachable else 1,
        text=(
            L("ki.gap_saknas_v0", v0=format_sek(abs(gap)))
            if not reachable
            else L("ki.gap_marginal_v0", v0=format_sek(abs(gap)))
        ),
        showarrow=False,
        xanchor="right",
        yshift=26,
        font=dict(
            size=12,
            color=COLORS["high_risk"] if not reachable else COLORS["low_risk"],
        ),
    )

    layout = get_chart_layout(height=210, showlegend=False)
    layout["xaxis"]["title"] = L("ki.gap_axel_pris")
    # The category labels are full sentences, so the left margin is measured
    # rather than guessed; a fixed value clipped "Högsta pris inkomsten bär".
    layout["yaxis"]["automargin"] = True
    layout["margin"] = dict(r=10, t=30, b=40)
    fig.update_layout(**layout)
    return fig
