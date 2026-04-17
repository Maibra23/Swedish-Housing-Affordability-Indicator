"""Sida 03 — Kommun djupanalys.

Prognos och detaljanalys per kommun med Prophet och ARIMA.
Historisk SHAI 2014–2024 + prognos 2025–2030.
"""

import streamlit as st

st.set_page_config(
    page_title="SHAI · Kommun djupanalys",
    page_icon="🏠",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None},
)

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title, card_header, footer_note, kpi_card, render_kpi_row, format_pct
from src.ui.chart_theme import get_chart_layout, CHART_PALETTE

inject_css()
selections = render_sidebar(page_key="kd")

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")

        try:
            forecast_prophet = pd.read_parquet("data/processed/forecast_prophet.parquet")
        except FileNotFoundError:
            forecast_prophet = pd.DataFrame()

        try:
            forecast_arima = pd.read_parquet("data/processed/forecast_arima.parquet")
        except FileNotFoundError:
            forecast_arima = pd.DataFrame()
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
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
    "Välj kommun",
    kommun_list,
    index=kommun_list.index("Stockholm") if "Stockholm" in kommun_list else 0,
    key="kd_kommun_select",
)

kommun_data = municipal[municipal["region_name"] == selected_kommun].sort_values("year")

if len(kommun_data) == 0:
    st.warning("Inga data tillgängliga för den valda kommunen.")
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
            unit="poäng",
            delta=f"{vc_delta_pct:+.1f}%".replace(".", ",") if len(prev) > 0 else "",
            delta_direction="down" if vc_delta > 0 else "up" if vc_delta < 0 else "flat",
            variant="accent",
            tooltip="Realversion. Inkomst / (Pris × max(R−π, 0,5%)). Högre = bättre överkomlighet. Råkvot, ej ett 0–100 index.",
        ),
        kpi_card(
            label="Medianinkomst",
            value=f"{lat['median_income']:,.0f}".replace(",", "\u00A0"),
            unit="SEK",
            variant="default",
            tooltip="Sammanräknad förvärvsinkomst, medelvärde per individ (SCB HE0110). Individuell bruttoinkomst — ej hushållsinkomst.",
        ),
        kpi_card(
            label="K/T-kvot",
            value=f"{lat['kt_ratio']:.2f}".replace(".", ","),
            variant="default",
            tooltip="Köpeskillingskoefficient: köpeskilling / taxeringsvärde. Speglar relativ prisnivå. Obs: K/T ingår ej i SHAI-formeln — transaktionspriset i SEK används.",
        ),
        kpi_card(
            label="Styrränta",
            value=f"{lat['policy_rate']:.2f}%".replace(".", ","),
            variant="default",
            tooltip="Riksbankens styrränta, årsgenomsnitt. Nationell — samma värde för alla kommuner. Bolåneränta ≈ styrränta + 1,5–2,5 pp bankens marginal (Begränsning F12).",
        ),
    ])

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Caveat callout ───────────────────────────────────────────────────
st.warning(
    "**Prognoser baseras på 11 årliga observationer (2014–2024).** "
    "Konfidensintervall vidgas snabbt efter år 3. "
    "Tolka långtidsprognoser med försiktighet."
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
                hovertemplate="<b>%{x}</b><br>Framskrivet från 2024<extra></extra>",
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
        xaxis_title="År",
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
        st.caption("Prophet är optimerat för dagliga affärsserier. För analys av makroekonomisk årlig data rekommenderas ARIMA-fliken.")
        if len(forecast_prophet) > 0:
            fig = _build_forecast_chart(kommun_data, forecast_prophet, lan_code, "Prophet")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
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
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        else:
            st.info("Prognosdata (ARIMA) saknas.")

# ── Component breakdown ──────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header("Komponentuppdelning", f"{selected_kommun} · 2014–2024", "KOMPONENTER"),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    component_configs = [
        ("Medianinkomst", "median_income", "SEK", col1, "#3D8B6E"),
        ("K/T-kvot", "kt_ratio", "kvot", col2, "#4A6FA5"),
        ("Styrränta", "policy_rate", "%", col3, "#D4785A"),
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

            title_prefix = "★ " if is_driver else ""
            layout = get_chart_layout(
                title=f"{title_prefix}{label}",
                height=250,
                yaxis_title=unit,
                showlegend=False,
            )
            layout["xaxis"]["dtick"] = 2
            layout["margin"] = {"l": 50, "r": 10, "t": 40, "b": 40}
            fig.update_layout(**layout)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    if driver:
        st.markdown(
            f"<div style='font-size:13px;color:{COLORS['text_secondary']};text-align:center;padding:8px 0;'>"
            f"★ <strong>{driver}</strong> har störst relativ variation och driver mest av "
            f"SHAI-förändringen för {selected_kommun}.</div>",
            unsafe_allow_html=True,
        )

footer_note()
