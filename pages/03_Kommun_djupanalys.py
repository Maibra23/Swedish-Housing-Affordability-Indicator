"""Sida 03 — Kommunanalys.

Detaljanalys per kommun: historisk SHAI över indexets hela period, följd av en
villkorad projektion sex år framåt under tre uttalade antaganden om realräntan.
Ingenting modellanpassas. Se R16 i docs/APP_REFERENCE.md (Part II).
"""

import streamlit as st

from src.ui.labels import L
from src.ui.templates import T

st.set_page_config(
    page_title="SHAI · " + L("kd.titel"),
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get Help": None, "Report a bug": None},
)

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.provenance import complete_case_max_year, first_year, n_kommuner
from src.ui.data import load as load_artifact
from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import (
    card_header,
    explanation,
    footer_note,
    format_dec,
    format_pct,
    delta_meta,
    kpi_card,
    page_title,
    render_kpi_row,
    vintage_badge,
)
from src.ui.chart_theme import get_chart_layout, CHART_PALETTE
from src.indices.kommun_components import attribute_change, cost_rate
from src.projection import HIGH_MORTGAGE_RATE, INCOME_GROWTH, PRICE_GROWTH

inject_css()
selections = render_sidebar()

# Period and panel size come from the provenance artifact: a literal
# "2014–2024" keeps asserting itself after the panel has moved on. See T1.10.
PERIOD_START, PERIOD_END = first_year(), complete_case_max_year()
PERIOD = f"{PERIOD_START}–{PERIOD_END}"

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = load_artifact("affordability_municipal.parquet")
        # The projection is computed at county level, so the chart needs the
        # county history to continue rather than the municipality's.
        county_hist = load_artifact("affordability_county.parquet")

        projection = load_artifact("projection.parquet")
except Exception as e:
    st.error(L("kd.kunde_inte_hamta_data_forsok_igen_senare"))
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow=L("kd.eyebrow"),
    title=L("kd.titel"),
    subtitle=L("kd.undertitel"),
    year=selected_year,
)

# ── Kommun selector ──────────────────────────────────────────────────
kommun_list = sorted(municipal["region_name"].unique())
selected_kommun = st.selectbox(
    L("kd.valj_kommun"),
    kommun_list,
    index=kommun_list.index("Stockholm") if "Stockholm" in kommun_list else 0,
    key="kd_kommun_select",
)

kommun_data = municipal[municipal["region_name"] == selected_kommun].sort_values("year")

if len(kommun_data) == 0:
    st.warning(L("kd.inga_data_tillgangliga_for_den_valda"))
    st.stop()

lan_code = kommun_data["lan_code"].iloc[0]
_county_hist = county_hist[county_hist["lan_code"] == lan_code].sort_values("year")

# ── KPI summary for selected kommun ─────────────────────────────────
latest = kommun_data[kommun_data["year"] == selected_year]
prev = kommun_data[kommun_data["year"] == selected_year - 1]

if len(latest) > 0:
    lat = latest.iloc[0]
    prv = prev.iloc[0] if len(prev) > 0 else lat

    vc_delta = lat["version_c"] - prv["version_c"] if len(prev) > 0 else 0
    vc_delta_pct = (vc_delta / prv["version_c"] * 100) if len(prev) > 0 and prv["version_c"] != 0 else 0

    render_kpi_row([
        kpi_card(
            label="SHAI (Version C)",
            value=format_dec(lat["version_c"]),
            unit=L("kd.procent_av_inkomsten"),
            delta=format_pct(vc_delta_pct, signed=True) if len(prev) > 0 else "",
            # A cost share: a rise is bad, and the arrow follows the number.
            **delta_meta(vc_delta, higher_is_better=False),
            variant="accent",
            tooltip=L("kd.kassaflodesversion_tooltip"),
        ),
        kpi_card(
            label="Medianinkomst",
            value=format_dec(lat["median_income"], 0),
            unit="SEK",
            variant="default",
            tooltip=L("kd.sammanraknad_forvarvsinkomst_medelvarde_per"),
        ),
        kpi_card(
            label="K/T-kvot",
            value=format_dec(lat["kt_ratio"], 2),
            variant="default",
            tooltip=L("kd.kopeskillingskoefficient_kopeskilling"),
        ),
        kpi_card(
            label=L("kd.bolaneranta"),
            value=format_pct(lat["mortgage_rate"], 2),
            variant="default",
            tooltip=L("kd.bolaneranta_tooltip"),
        ),
    ])

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

def _build_projection_chart(
    hist_data: pd.DataFrame,
    county_hist: pd.DataFrame,
    projection: pd.DataFrame,
    lan_code: str,
    scenario_labels: dict[str, str],
) -> go.Figure:
    """Observed history for the municipality and its county, then three
    conditional projections.

    Nothing here is fitted. The three lines differ only in their assumed
    mortgage rate, so the spread between them is a statement about rates rather
    than about this municipality. That is deliberate: the rate is an outcome of
    policy and bank pricing, so it belongs to the reader rather than to a model.

    The municipality's own line is the page's subject. The county's is drawn too
    because the projection extends the county, and because a projection stitched
    onto a different geography is the defect this chart used to have.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist_data["year"], y=hist_data["version_c"],
        mode="lines+markers", name=L("kd.serie_kommunen"),
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=6, color=COLORS["primary"]),
        hovertemplate=L("kd.projektion_hover"),
    ))

    fig.add_trace(go.Scatter(
        x=county_hist["year"], y=county_hist["version_c"],
        mode="lines", name=L("kd.serie_lanet"),
        line=dict(color=COLORS["secondary"], width=1.5, dash="dot"),
        hovertemplate=L("kd.lanet_hover"),
    ))

    # Cheapest first. The low-rate line sits lowest on the chart now that
    # Version C is a cost share, so the legend reads bottom-up from the lines.
    scenario_colours = {
        "low": COLORS["low_risk"],
        "current": COLORS["secondary"],
        "high": COLORS["high_risk"],
    }
    anchor_year = int(county_hist["year"].max())
    anchor_value = float(
        county_hist.loc[county_hist["year"] == anchor_year, "version_c"].iloc[0]
    )
    for scenario, colour in scenario_colours.items():
        block = projection[
            (projection["lan_code"] == lan_code) & (projection["scenario"] == scenario)
        ].sort_values("target_year")
        if block.empty:
            continue
        fig.add_trace(go.Scatter(
            x=[anchor_year] + block["target_year"].tolist(),
            y=[anchor_value] + block["version_c"].tolist(),
            mode="lines", name=scenario_labels[scenario],
            line=dict(color=colour, width=2, dash="dash"),
            hovertemplate=L("kd.projektion_hover"),
        ))

    layout = get_chart_layout(
        height=420,
        xaxis_title=L("kd.ar"),
        yaxis_title=L("kd.projektion_y_axel"),
    )
    layout["xaxis"]["dtick"] = 1
    # Vertical, and deliberately not the project's horizontal default.
    #
    # Plotly sizes each horizontal legend item as `swatch + measured text`, but it
    # measures while the fallback font is still active; Source Sans Pro then swaps
    # in about 18 % wider and nothing recomputes. Every item therefore overruns its
    # allocation by ~18 % of its own label width, and the next item's colour swatch
    # is painted over the tail of the previous label. With five entries it ate the
    # "pp" off two of the three scenario names.
    #
    # `itemwidth` cannot fix it (it governs only the swatch region), and shortening
    # the labels only shrinks the overlap proportionally rather than removing it.
    # Stacking the entries removes the failure mode instead of tuning around it.
    layout["legend"] = dict(
        orientation="v", yanchor="top", y=1.0,
        xanchor="left", x=1.01, font=dict(size=11),
    )
    # The right margin holds the legend. It is set explicitly and generously for
    # the same reason the legend is vertical: Plotly reserves outside-legend space
    # from its own short text measurement, so the longest label overran the plot
    # edge and was clipped. Measured in the browser, not guessed.
    layout["margin"] = dict(l=50, r=190, t=30, b=50)
    fig.update_layout(**layout)
    return fig


# ── Conditional projection ───────────────────────────────────────────
_anchor_year = int(_county_hist["year"].iloc[-1])
_county_name = str(_county_hist["region_name"].iloc[-1])
_rates = (
    projection.drop_duplicates("scenario").set_index("scenario")["mortgage_rate"].to_dict()
)
# Plotly clips the legend to a width it derives from its own text measurement,
# and that measurement is taken before the `Source Sans 3` webfont loads. The
# real glyphs then render about 18 % wider than the box allowed, so the longest
# entry loses its tail: "Dagens nivå, 0,77 pp" once rendered as "Dagens nivå, 0,77".
# No legend option fixes it (`itemwidth` governs only the swatch, `entrywidth`
# does not resize the clip), and the clip is sized from the longest label, so
# shortening the labels moves the problem rather than solving it. Padding the
# strings gives the clip whitespace to eat instead of characters. Non-breaking
# spaces, because SVG collapses ordinary trailing ones. The width is measured in
# a browser, not reasoned about: at 20 the clip clears the longest label by ~15 px.
_LEGEND_PAD = "\u00a0" * 20

_scenario_labels = {
    "low": L("kd.scenario_lag", v0=format_dec(_rates["low"], 2)) + _LEGEND_PAD,
    # Labelled with the year its rate comes from. "Dagens nivå" called the 2024
    # rate today's while the panel already held 2025 rates.
    "current": L("kd.scenario_dagens", v0=format_dec(_rates["current"], 2), v1=_anchor_year) + _LEGEND_PAD,
    "high": L("kd.scenario_hog", v0=format_dec(HIGH_MORTGAGE_RATE, 1)) + _LEGEND_PAD,
}

with st.container(border=True):
    st.markdown(
        card_header(
            # The lines are the county's, so the title names the county.
            L("kd.projektion_rubrik", v0=_county_name),
            L("kd.projektion_underrubrik"),
            L("kd.projektion_tagg"),
        ),
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        _build_projection_chart(
            kommun_data, _county_hist, projection, lan_code, _scenario_labels
        ),
        width="stretch",
        config={"displayModeBar": "hover"},
    )
    st.caption(
        L("kd.projektion_antaganden",
          v0=f"{INCOME_GROWTH * 100:.0f}", v1=f"{PRICE_GROWTH * 100:.0f}", v2=_anchor_year)
    )
    explanation(L("kd.projektion_forklaring"))
    with st.expander(L("kd.projektion_mer_rubrik")):
        st.markdown(L("kd.projektion_mer_text"))

# ── Component breakdown ──────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header(L("kd.komp_rubrik"), f"{selected_kommun} · {PERIOD}", "KOMPONENTER"),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    # The three inputs Version C is built from, not K/T or the policy rate.
    # The split below is exact; see src/indices/kommun_components.py.
    component_data = kommun_data.assign(cost_rate=cost_rate(kommun_data))
    component_configs = [
        ("income", L("kd.komp_inkomst"), "median_income", "SEK", col1, CHART_PALETTE[6]),
        ("price", L("kd.komp_pris"), "transaction_price_sek", "SEK", col2, CHART_PALETTE[0]),
        ("cost_rate", L("kd.komp_kostnadsranta"), "cost_rate", "%", col3, CHART_PALETTE[5]),
    ]
    change = attribute_change(kommun_data)
    driver = change.driver if change else ""

    for key, label, col_name, unit, col_container, base_color in component_configs:
        with col_container:
            is_driver = key == driver
            chart_color = COLORS["accent"] if is_driver else base_color

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=component_data["year"],
                y=component_data[col_name],
                mode="lines+markers",
                line=dict(color=chart_color, width=2.5 if is_driver else 2),
                marker=dict(size=5, color=chart_color),
                fill="tozeroy",
                fillcolor=f"rgba({int(chart_color[1:3],16)},{int(chart_color[3:5],16)},{int(chart_color[5:7],16)},0.06)",
                hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:,.2f}} {unit}<extra></extra>",
            ))

            layout = get_chart_layout(
                title=label,
                height=250,
                yaxis_title=unit,
                showlegend=False,
            )
            layout["xaxis"]["dtick"] = 2
            # Whole kronor with spaces ("400 000"), not Plotly's SI "400k".
            if unit == "SEK":
                layout["yaxis"]["tickformat"] = ",.0f"
            layout["margin"] = {"l": 50, "r": 10, "t": 40, "b": 40}
            fig.update_layout(**layout)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": "hover"})

    if change:
        names = {key: label for key, label, *_ in component_configs}
        pct = {k: f"{v:+.0f}".replace("-", "\u2212") for k, v in change.parts_pct.items()}
        st.markdown(L(
            "kd.komp_uppdelning",
            v0=selected_kommun, v1=change.from_year, v2=change.to_year,
            v3=f"{change.total_pct:+.0f}".replace("-", "\u2212"),
            v4=pct["income"], v5=pct["price"], v6=pct["cost_rate"],
            v7=names[driver].lower(),
        ))

with st.expander(L("kd.om_komponenterna")):
    st.markdown(L("kd.om_komponenterna_text"))

vintage_badge()
footer_note()
