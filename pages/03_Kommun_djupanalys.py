"""Sida 03 — Kommun djupanalys.

Prognos och detaljanalys per kommun med Prophet och ARIMA.
Historisk SHAI 2014–2024 + prognos 2025–2030.
"""

import streamlit as st

st.set_page_config(page_title="SHAI · Kommun djupanalys", layout="wide")

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title, card

inject_css()
selections = render_sidebar()

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

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 03 · Kommunanalys",
    title="Kommun djupanalys",
    subtitle="Historisk analys och prognos per kommun",
)

# ── Kommun selector ──────────────────────────────────────────────────
kommun_list = sorted(municipal["region_name"].unique())
selected_kommun = st.selectbox("Välj kommun", kommun_list, index=kommun_list.index("Stockholm") if "Stockholm" in kommun_list else 0)

kommun_data = municipal[municipal["region_name"] == selected_kommun].sort_values("year")

if len(kommun_data) == 0:
    st.warning("Inga data tillgängliga för den valda kommunen.")
    st.stop()

lan_code = kommun_data["lan_code"].iloc[0]

# ── Caveat callout ───────────────────────────────────────────────────
st.warning(
    "⚠️ **Prognoser baseras på 11 årliga observationer (2014–2024).** "
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
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=5),
    ))

    # Mark imputed years with different style
    imputed = hist_data[hist_data["is_imputed_income"] == True]
    if len(imputed) > 0:
        fig.add_trace(go.Scatter(
            x=imputed["year"],
            y=imputed["version_c"],
            mode="markers",
            name="Framskriven inkomst",
            marker=dict(size=8, color=COLORS["accent"], symbol="diamond"),
            hovertemplate="<b>%{x}</b><br>Värde framskrivet från 2024<extra></extra>",
        ))

    # Forecast
    if len(forecast_df) > 0:
        fc = forecast_df[
            (forecast_df["county_kod"] == lan_code) &
            (forecast_df["variable"] == "affordability_c")
        ].sort_values("target_year")

        if len(fc) > 0:
            # Connect historical to forecast
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
                fillcolor="rgba(75, 111, 165, 0.15)",
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
                marker=dict(size=4),
            ))

    fig.update_layout(
        xaxis_title="År",
        yaxis_title="SHAI (Version C)",
        font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=12),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=50, r=20, t=30, b=50),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(gridcolor=COLORS["grid"], dtick=1),
        yaxis=dict(gridcolor=COLORS["grid"]),
    )
    return fig


# ── Forecast tabs ────────────────────────────────────────────────────
tab_prophet, tab_arima = st.tabs(["Prophet (standard)", "ARIMA (rekommenderad)"])

with tab_prophet:
    if len(forecast_prophet) > 0:
        fig = _build_forecast_chart(kommun_data, forecast_prophet, lan_code, "Prophet")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Prognosdata (Prophet) saknas.")

with tab_arima:
    if len(forecast_arima) > 0:
        fig = _build_forecast_chart(kommun_data, forecast_arima, lan_code, "ARIMA")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Prognosdata (ARIMA) saknas.")

# ── Component breakdown ──────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown(
    card(
        title="Komponentuppdelning",
        subtitle=f"{selected_kommun} · 2014–2024",
        tag="KOMPONENTER",
    ),
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

component_configs = [
    ("Medianinkomst", "median_income", "SEK", col1),
    ("K/T-kvot", "kt_ratio", "kvot", col2),
    ("Styrränta", "policy_rate", "%", col3),
]

# Compute which component has highest coefficient of variation
cv_scores = {}
for label, col_name, unit, _ in component_configs:
    vals = kommun_data[col_name].dropna()
    if len(vals) > 1 and vals.mean() != 0:
        cv_scores[label] = vals.std() / abs(vals.mean())
    else:
        cv_scores[label] = 0

driver = max(cv_scores, key=cv_scores.get) if cv_scores else ""

for label, col_name, unit, col_container in component_configs:
    with col_container:
        is_driver = label == driver
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=kommun_data["year"],
            y=kommun_data[col_name],
            mode="lines+markers",
            line=dict(
                color=COLORS["accent"] if is_driver else COLORS["secondary"],
                width=2,
            ),
            marker=dict(size=4),
            hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:,.2f}} {unit}<extra></extra>",
        ))
        fig.update_layout(
            title=dict(
                text=f"{'⭐ ' if is_driver else ''}{label}",
                font=dict(size=13),
            ),
            xaxis=dict(gridcolor=COLORS["grid"], dtick=2),
            yaxis=dict(gridcolor=COLORS["grid"], title=unit),
            font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=11),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=50, r=10, t=40, b=40),
            height=250,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

if driver:
    st.markdown(
        f"<div style='font-size:13px;color:#6B7280;text-align:center;'>"
        f"⭐ <strong>{driver}</strong> har störst relativ variation och driver mest av SHAI-förändringen "
        f"för {selected_kommun}.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    """<div style="font-size:11px;color:#9CA3AF;text-align:center;padding:12px 0;
    border-top:1px solid #EEF0F3;margin-top:32px;">
    <strong>KÄLLA:</strong> SCB, Riksbanken, Kolada &nbsp;·&nbsp; SHAI v1.3
    </div>""",
    unsafe_allow_html=True,
)
