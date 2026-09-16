"""Sida 03 — Kommun djupanalys.

Prognos och detaljanalys per kommun med Prophet och ARIMA.
Historisk SHAI över indexets hela period + prognos sex år framåt.
"""

import streamlit as st

from src.ui.labels import L

st.set_page_config(
    page_title="SHAI · Kommun djupanalys",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
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
    format_pct,
    kpi_card,
    page_title,
    render_kpi_row,
    vintage_badge,
)
from src.ui.chart_theme import get_chart_layout, CHART_PALETTE

inject_css()
selections = render_sidebar(page_key="kd")

# Period and panel size come from the provenance artifact: a literal
# "2014–2024" keeps asserting itself after the panel has moved on. See T1.10.
PERIOD_START, PERIOD_END = first_year(), complete_case_max_year()
PERIOD = f"{PERIOD_START}–{PERIOD_END}"
N_YEARS = PERIOD_END - PERIOD_START + 1

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = load_artifact("affordability_municipal.parquet")

        try:
            forecast_prophet = load_artifact("forecast_prophet.parquet")
        except FileNotFoundError:
            forecast_prophet = pd.DataFrame()

        try:
            forecast_arima = load_artifact("forecast_arima.parquet")
        except FileNotFoundError:
            forecast_arima = pd.DataFrame()
except Exception as e:
    st.error(L("kd.kunde_inte_hamta_data_forsok_igen_senare"))
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 03 · Kommunanalys",
    title="Kommun djupanalys",
    subtitle="Historisk analys och prognos per kommun",
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
            value=f"{lat['version_c']:.1f}".replace(".", ","),
            unit=L("kd.poang"),
            delta=f"{vc_delta_pct:+.1f}%".replace(".", ",") if len(prev) > 0 else "",
            delta_direction="down" if vc_delta > 0 else "up" if vc_delta < 0 else "flat",
            variant="accent",
            tooltip=L("kd.realversion_inkomst_pris_max_r_0_5_hogre"),
        ),
        kpi_card(
            label="Medianinkomst",
            value=f"{lat['median_income']:,.0f}".replace(",", "\u00A0"),
            unit="SEK",
            variant="default",
            tooltip=L("kd.sammanraknad_forvarvsinkomst_medelvarde_per"),
        ),
        kpi_card(
            label="K/T-kvot",
            value=f"{lat['kt_ratio']:.2f}".replace(".", ","),
            variant="default",
            tooltip=L("kd.kopeskillingskoefficient_kopeskilling"),
        ),
        kpi_card(
            label=L("kd.styrranta"),
            value=f"{lat['policy_rate']:.2f}%".replace(".", ","),
            variant="default",
            tooltip=L("kd.riksbankens_styrranta_arsgenomsnitt"),
        ),
    ])

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Caveat callout ───────────────────────────────────────────────────
st.warning(
    L("kd.prognoser_baseras_pa_v0_arliga_observationer", v0=N_YEARS, v1=PERIOD)
)


def _build_forecast_chart(
    hist_data: pd.DataFrame,
    forecast_df: pd.DataFrame,
    lan_code: str,
    model_name: str,
) -> go.Figure:
    """Build combined historical + forecast chart for Version C."""
    fig = go.Figure()

    # Historical line
    fig.add_trace(go.Scatter(
        x=hist_data["year"],
        y=hist_data["version_c"],
        mode="lines+markers",
        name="Historisk",
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=6, color=COLORS["primary"]),
        hovertemplate="<b>%{x}</b><br>SHAI: %{y:,.1f}<extra>Historisk</extra>",
    ))

    # Mark imputed years
    if "is_imputed_income" in hist_data.columns:
        imputed = hist_data[hist_data["is_imputed_income"] == True]
        if len(imputed) > 0:
            fig.add_trace(go.Scatter(
                x=imputed["year"],
                y=imputed["version_c"],
                mode="markers",
                name="Framskriven inkomst",
                marker=dict(size=10, color=COLORS["accent"], symbol="diamond"),
                hovertemplate=L("kd.x_framskrivet_fran_2024"),
            ))

    # Forecast
    if len(forecast_df) > 0:
        fc = forecast_df[
            (forecast_df["county_kod"] == lan_code)
            & (forecast_df["variable"] == "affordability_c")
        ].sort_values("target_year")

        if len(fc) > 0:
            last_hist_year = hist_data["year"].max()
            last_hist_val = hist_data[hist_data["year"] == last_hist_year]["version_c"].iloc[0]

            fc_years = [last_hist_year] + fc["target_year"].tolist()
            fc_mean = [last_hist_val] + fc["mean"].tolist()
            fc_lower = [last_hist_val] + fc["lower_80"].tolist()
            fc_upper = [last_hist_val] + fc["upper_80"].tolist()

            # Confidence band
            fig.add_trace(go.Scatter(
                x=fc_years + fc_years[::-1],
                y=fc_upper + fc_lower[::-1],
                fill="toself",
                fillcolor="rgba(74, 111, 165, 0.12)",
                line=dict(width=0),
                name="80% konfidensintervall",
                hoverinfo="skip",
            ))

            # Mean forecast line
            fig.add_trace(go.Scatter(
                x=fc_years,
                y=fc_mean,
                mode="lines+markers",
                name=f"Prognos ({model_name})",
                line=dict(color=COLORS["secondary"], width=2, dash="dash"),
                marker=dict(size=5, color=COLORS["secondary"]),
                hovertemplate=f"<b>%{{x}}</b><br>Prognos: %{{y:,.1f}}<extra>{model_name}</extra>",
            ))

    layout = get_chart_layout(
        height=380,
        xaxis_title=L("kd.ar"),
        yaxis_title="SHAI (Version C)",
    )
    layout["xaxis"]["dtick"] = 1
    fig.update_layout(**layout)
    return fig


# ── Forecast tabs ────────────────────────────────────────────────────
tab_prophet, tab_arima = st.tabs(["Prophet (standard)", "ARIMA (rekommenderad)"])

with tab_prophet:
    with st.container(border=True):
        st.markdown(
            card_header(f"Prognos — {selected_kommun}", "Prophet-modell", "PROPHET"),
            unsafe_allow_html=True,
        )
        st.caption(L("kd.prophet_ar_optimerat_for_dagliga"))
        st.caption(L("kd.prognoserna_beraknas_pa_lansniva_v0_inte_per", v0=kommun_data['lan_code'].iloc[0]))
        if len(forecast_prophet) > 0:
            fig = _build_forecast_chart(kommun_data, forecast_prophet, lan_code, "Prophet")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": "hover"})
        else:
            st.info("Prognosdata (Prophet) saknas.")

with tab_arima:
    with st.container(border=True):
        st.markdown(
            card_header(f"Prognos — {selected_kommun}", "ARIMA-modell (auto-AIC)", "ARIMA"),
            unsafe_allow_html=True,
        )
        if len(forecast_arima) > 0:
            fig = _build_forecast_chart(kommun_data, forecast_arima, lan_code, "ARIMA")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": "hover"})
        else:
            st.info("Prognosdata (ARIMA) saknas.")

# ── Component breakdown ──────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header("Komponentuppdelning", f"{selected_kommun} · {PERIOD}", "KOMPONENTER"),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    component_configs = [
        ("Medianinkomst", "median_income", "SEK", col1, "#3D8B6E"),
        ("K/T-kvot", "kt_ratio", "kvot", col2, "#4A6FA5"),
        (L("kd.styrranta"), "policy_rate", "%", col3, "#D4785A"),
    ]

    # Compute driver
    cv_scores = {}
    for label, col_name, unit, _, _ in component_configs:
        vals = kommun_data[col_name].dropna()
        if len(vals) > 1 and vals.mean() != 0:
            cv_scores[label] = vals.std() / abs(vals.mean())
        else:
            cv_scores[label] = 0

    driver = max(cv_scores, key=cv_scores.get) if cv_scores else ""

    for label, col_name, unit, col_container, base_color in component_configs:
        with col_container:
            is_driver = label == driver
            chart_color = COLORS["accent"] if is_driver else base_color

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=kommun_data["year"],
                y=kommun_data[col_name],
                mode="lines+markers",
                line=dict(color=chart_color, width=2.5 if is_driver else 2),
                marker=dict(size=5, color=chart_color),
                fill="tozeroy",
                fillcolor=f"rgba({int(chart_color[1:3],16)},{int(chart_color[3:5],16)},{int(chart_color[5:7],16)},0.06)",
                hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:,.2f}} {unit}<extra></extra>",
            ))

            title_prefix = ""
            layout = get_chart_layout(
                title=f"{title_prefix}{label}",
                height=250,
                yaxis_title=unit,
                showlegend=False,
            )
            layout["xaxis"]["dtick"] = 2
            layout["margin"] = {"l": 50, "r": 10, "t": 40, "b": 40}
            fig.update_layout(**layout)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": "hover"})

    if driver:
        st.markdown(
            L("kd.v1_har_storst_relativ_variation_och_driver", v0=COLORS['text_secondary'], v1=driver, v2=selected_kommun),
            unsafe_allow_html=True,
        )

explanation(L("kd.forklaring_prognos", v0=N_YEARS))
with st.expander(L("kd.om_prognosen")):
    st.markdown(L("kd.om_prognosen_text", v0=N_YEARS))

with st.expander(L("kd.om_komponenterna")):
    st.markdown(L("kd.om_komponenterna_text"))

vintage_badge()
footer_note()
