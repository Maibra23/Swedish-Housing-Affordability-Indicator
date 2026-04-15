"""Sida 01 — Riksöversikt.

Nationell överblick med KPI-kort, karta, histogram och rankingtabeller.
"""

import streamlit as st

st.set_page_config(page_title="SHAI · Riksöversikt", layout="wide")

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import (
    page_title,
    kpi_card,
    render_kpi_row,
    format_sek,
    format_pct,
    risk_pill,
    card,
)
from src.ui.choropleth import render_choropleth

inject_css()
selections = render_sidebar()

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")

        try:
            coords = pd.read_csv("data/processed/municipality_coords.csv", dtype={"region_code": str})
        except FileNotFoundError:
            coords = None
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
risk_filter = selections["risk_filter"]

# Filter to selected year from municipal panel
mun_year = municipal[municipal["year"] == selected_year].copy()
mun_prev = municipal[municipal["year"] == selected_year - 1].copy()

# Use ranked data (always 2024, latest) for rankings/z-scores
# If selected year matches ranked year, use it directly; otherwise compute from municipal
if selected_year == ranked["year"].iloc[0]:
    df_ranked = ranked.copy()
else:
    # For other years, compute z-scores from municipal panel
    df_ranked = mun_year.copy()
    if "version_c" in df_ranked.columns and len(df_ranked) > 0:
        mean_c = df_ranked["version_c"].mean()
        std_c = df_ranked["version_c"].std()
        if std_c > 0:
            df_ranked["z_c"] = (df_ranked["version_c"] - mean_c) / std_c
        else:
            df_ranked["z_c"] = 0.0
        df_ranked["rank_c"] = df_ranked["z_c"].rank(method="min").astype(int)
        df_ranked["risk_c"] = pd.cut(
            df_ranked["z_c"],
            bins=[-np.inf, -0.67, 0.67, np.inf],
            labels=["lag", "medel", "hog"],
        )

# Apply risk filter
if risk_filter != "Alla":
    risk_map = {"Låg risk": "lag", "Medel risk": "medel", "Hög risk": "hog"}
    filter_key = risk_map.get(risk_filter)
    if filter_key and "risk_c" in df_ranked.columns:
        df_ranked = df_ranked[df_ranked["risk_c"] == filter_key]

# Empty state check
if len(mun_year) == 0:
    st.warning("Inga data tillgängliga för den valda perioden.")
    st.stop()

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 01 · Nationell översikt",
    title="Riksöversikt",
    subtitle=f"Strukturell bostadsekonomisk hållbarhet i Sveriges 290 kommuner · {selected_year}",
)

# ── KPI cards ────────────────────────────────────────────────────────
# 1) Average SHAI (Version C)
mean_vc = mun_year["version_c"].mean() if len(mun_year) > 0 else 0
mean_vc_prev = mun_prev["version_c"].mean() if len(mun_prev) > 0 else mean_vc
delta_vc = mean_vc - mean_vc_prev
delta_vc_pct = (delta_vc / mean_vc_prev * 100) if mean_vc_prev != 0 else 0

# 2) High-risk municipalities
n_hog = len(df_ranked[df_ranked["risk_c"] == "hog"]) if "risk_c" in df_ranked.columns else 0
# For delta, compute from previous year
if len(mun_prev) > 0 and "version_c" in mun_prev.columns:
    mean_prev = mun_prev["version_c"].mean()
    std_prev = mun_prev["version_c"].std()
    if std_prev > 0:
        z_prev = (mun_prev["version_c"] - mean_prev) / std_prev
        n_hog_prev = (z_prev > 0.67).sum()
    else:
        n_hog_prev = 0
else:
    n_hog_prev = n_hog
delta_hog = n_hog - n_hog_prev

# 3) Mean K/T ratio
mean_kt = mun_year["kt_ratio"].mean() if "kt_ratio" in mun_year.columns and len(mun_year) > 0 else 0
mean_kt_prev = mun_prev["kt_ratio"].mean() if "kt_ratio" in mun_prev.columns and len(mun_prev) > 0 else mean_kt
delta_kt_pct = ((mean_kt / mean_kt_prev - 1) * 100) if mean_kt_prev != 0 else 0

# 4) Population change
pop_now = mun_year["population"].sum() if "population" in mun_year.columns else 0
pop_prev = mun_prev["population"].sum() if "population" in mun_prev.columns else pop_now
pop_change_pct = ((pop_now / pop_prev - 1) * 100) if pop_prev > 0 else 0

render_kpi_row([
    kpi_card(
        label="Genomsnittligt SHAI",
        value=f"{mean_vc:,.1f}".replace(",", " ").replace(".", ","),
        unit="poäng",
        delta=f"{delta_vc_pct:+.1f}%".replace(".", ","),
        delta_direction="up" if delta_vc > 0 else "down" if delta_vc < 0 else "flat",
        variant="default",
    ),
    kpi_card(
        label="Högrisk kommuner",
        value=str(n_hog),
        unit="av 290",
        delta=f"{delta_hog:+d}" if delta_hog != 0 else "oförändrat",
        delta_direction="up" if delta_hog > 0 else "down" if delta_hog < 0 else "flat",
        variant="danger",
    ),
    kpi_card(
        label="Medianpris (K/T ratio)",
        value=f"{mean_kt:.2f}".replace(".", ","),
        unit="genomsnitt",
        delta=f"{delta_kt_pct:+.1f}%".replace(".", ","),
        delta_direction="up" if delta_kt_pct > 0 else "down" if delta_kt_pct < 0 else "flat",
        variant="accent",
    ),
    kpi_card(
        label="Befolkningsförändring",
        value=format_pct(pop_change_pct),
        delta=f"{(pop_now - pop_prev):+,.0f}".replace(",", " "),
        delta_direction="up" if pop_change_pct > 0 else "down" if pop_change_pct < 0 else "flat",
        variant="success",
    ),
])

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Chart row: Choropleth + Distribution histogram ───────────────────
col_map, col_hist = st.columns([3, 2])

with col_map:
    if coords is not None and len(df_ranked) > 0:
        # Merge coordinates
        map_data = df_ranked.merge(
            coords, on="region_code", how="left"
        ).dropna(subset=["lat", "lon"])
        if len(map_data) > 0:
            render_choropleth(map_data)
        else:
            st.warning("Koordinatdata saknas för kartvisning.")
    else:
        st.info("Kartdata laddas — koordinatfil saknas ännu.")

with col_hist:
    st.markdown(
        card(
            title="Fördelning av SHAI poäng",
            subtitle=f"Version C · {selected_year}",
            tag="HISTOGRAM",
            content="",
        ),
        unsafe_allow_html=True,
    )
    if "z_c" in df_ranked.columns and len(df_ranked) > 0:
        z_vals = df_ranked["z_c"].dropna()

        fig = go.Figure()

        # Color bins matching risk thresholds
        bins_low = z_vals[z_vals <= -0.67]
        bins_mid = z_vals[(z_vals > -0.67) & (z_vals <= 0.67)]
        bins_high = z_vals[z_vals > 0.67]

        for subset, color, name in [
            (bins_low, COLORS["low_risk"], "Låg risk"),
            (bins_mid, COLORS["medium_risk"], "Medel risk"),
            (bins_high, COLORS["high_risk"], "Hög risk"),
        ]:
            if len(subset) > 0:
                fig.add_trace(go.Histogram(
                    x=subset,
                    marker_color=color,
                    opacity=0.85,
                    name=name,
                    nbinsx=20,
                ))

        # Median line
        median_z = z_vals.median()
        fig.add_vline(
            x=median_z,
            line_dash="dash",
            line_color=COLORS["primary"],
            line_width=1.5,
            annotation_text="Median",
            annotation_position="top",
            annotation_font=dict(size=11, color=COLORS["primary"]),
        )

        fig.update_layout(
            barmode="stack",
            xaxis_title="SHAI poäng (z-poäng)",
            yaxis_title="Antal kommuner",
            font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=12),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=40, r=20, t=20, b=50),
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(size=11),
            ),
            xaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
            yaxis=dict(gridcolor=COLORS["grid"], zeroline=False),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Table row: Top 15 worst + Top 15 best ────────────────────────────


def _build_ranking_table(df: pd.DataFrame, ascending: bool, title: str) -> str:
    """Build HTML table for top/bottom municipalities."""
    if ascending:
        subset = df.nsmallest(15, "z_c")
    else:
        subset = df.nlargest(15, "z_c")

    rows_html = ""
    for i, (_, row) in enumerate(subset.iterrows(), 1):
        name = row.get("region_name", "")
        z_val = row.get("z_c", 0)
        vc_val = row.get("version_c", 0)
        risk = row.get("risk_c", "medel")
        pill = risk_pill(risk)
        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td>{name}</td>
            <td class="num">{z_val:.2f}</td>
            <td class="num">{vc_val:.1f}</td>
            <td>{pill}</td>
        </tr>"""

    return f"""
    <div class="shai-card">
        <div class="shai-card-header">
            <div>
                <div class="shai-card-title">{title}</div>
                <div class="shai-card-subtitle">Version C · {selected_year}</div>
            </div>
            <span class="shai-card-tag">RANKING</span>
        </div>
        <table class="shai-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Kommun</th>
                    <th class="num">Z-poäng</th>
                    <th class="num">SHAI</th>
                    <th>Risk</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """


if "z_c" in df_ranked.columns and len(df_ranked) >= 15:
    col_worst, col_best = st.columns(2)

    with col_worst:
        st.markdown(
            _build_ranking_table(df_ranked, ascending=False, title="Sämst överkomlighet (topp 15)"),
            unsafe_allow_html=True,
        )

    with col_best:
        st.markdown(
            _build_ranking_table(df_ranked, ascending=True, title="Bäst överkomlighet (topp 15)"),
            unsafe_allow_html=True,
        )

# ── Footer ───────────────────────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

latest_year = municipal["year"].max() if len(municipal) > 0 else "—"
st.markdown(
    f"""<div style="font-size:11px;color:#9CA3AF;text-align:center;padding:12px 0;
    border-top:1px solid #EEF0F3;">
    <strong>KÄLLA:</strong> SCB, Riksbanken, Kolada &nbsp;·&nbsp;
    Senast uppdaterad: {latest_year} &nbsp;·&nbsp;
    SHAI v1.3
    </div>""",
    unsafe_allow_html=True,
)
