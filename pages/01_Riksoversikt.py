"""Sida 01 — Riksöversikt.

Nationell överblick med KPI-kort, karta, histogram och rankingtabeller.
"""

import streamlit as st

st.set_page_config(
    page_title="SHAI · Riksöversikt",
    page_icon="🏠",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None},
)

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
    card_header,
    footer_note,
)
from src.ui.choropleth import render_choropleth
from src.ui.chart_theme import get_chart_layout

inject_css()
selections = render_sidebar(page_key="rv")

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
selected_risks = selections["selected_risks"]

# Filter to selected year from municipal panel
mun_year = municipal[municipal["year"] == selected_year].copy()
mun_prev = municipal[municipal["year"] == selected_year - 1].copy()

# Use ranked data (always 2024, latest) for rankings/z-scores
if selected_year == ranked["year"].iloc[0]:
    df_ranked = ranked.copy()
else:
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

# Apply risk filter from multi-select pills
risk_label_map = {"Hög": "hog", "Medel": "medel", "Låg": "lag"}
if "risk_c" in df_ranked.columns and len(selected_risks) < 3:
    allowed = [risk_label_map[r] for r in selected_risks if r in risk_label_map]
    df_ranked = df_ranked[df_ranked["risk_c"].isin(allowed)]

# Empty state
if len(mun_year) == 0:
    st.warning("Inga data tillgängliga för den valda perioden.")
    st.stop()

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 01 · Nationell översikt",
    title="Riksöversikt",
    subtitle=f"Strukturell bostadsekonomisk hållbarhet i Sveriges 290 kommuner · {selected_year}",
    year=selected_year,
)

# ── KPI cards ────────────────────────────────────────────────────────
mean_vc = mun_year["version_c"].mean() if len(mun_year) > 0 else 0
mean_vc_prev = mun_prev["version_c"].mean() if len(mun_prev) > 0 else mean_vc
delta_vc = mean_vc - mean_vc_prev
delta_vc_pct = (delta_vc / mean_vc_prev * 100) if mean_vc_prev != 0 else 0

n_hog = len(df_ranked[df_ranked["risk_c"] == "hog"]) if "risk_c" in df_ranked.columns else 0
if len(mun_prev) > 0 and "version_c" in mun_prev.columns:
    mean_prev = mun_prev["version_c"].mean()
    std_prev = mun_prev["version_c"].std()
    if std_prev > 0:
        z_prev = (mun_prev["version_c"] - mean_prev) / std_prev
        n_hog_prev = int((z_prev > 0.67).sum())
    else:
        n_hog_prev = 0
else:
    n_hog_prev = n_hog
delta_hog = n_hog - n_hog_prev

mean_kt = mun_year["kt_ratio"].mean() if "kt_ratio" in mun_year.columns and len(mun_year) > 0 else 0
mean_kt_prev = mun_prev["kt_ratio"].mean() if "kt_ratio" in mun_prev.columns and len(mun_prev) > 0 else mean_kt
delta_kt_pct = ((mean_kt / mean_kt_prev - 1) * 100) if mean_kt_prev != 0 else 0

pop_now = mun_year["population"].sum() if "population" in mun_year.columns else 0
pop_prev = mun_prev["population"].sum() if "population" in mun_prev.columns else pop_now
pop_change_pct = ((pop_now / pop_prev - 1) * 100) if pop_prev > 0 else 0

render_kpi_row([
    kpi_card(
        label="Genomsnittligt SHAI",
        value=f"{mean_vc:,.1f}".replace(",", "\u00A0").replace(".", ","),
        unit="poäng",
        delta=f"{delta_vc_pct:+.1f}%".replace(".", ","),
        delta_direction="up" if delta_vc > 0 else "down" if delta_vc < 0 else "flat",
        variant="default",
        tooltip="Genomsnittlig Version C-poäng för alla 290 kommuner. Högre = bättre överkomlighet.",
    ),
    kpi_card(
        label="Högrisk kommuner",
        value=str(n_hog),
        unit="av 290",
        delta=f"{delta_hog:+d}" if delta_hog != 0 else "oförändrat",
        delta_direction="up" if delta_hog > 0 else "down" if delta_hog < 0 else "flat",
        variant="danger",
        tooltip="Antal kommuner med z-poäng > 0,67 standardavvikelser (riskklass Hög).",
    ),
    kpi_card(
        label="Medianpris (K/T ratio)",
        value=f"{mean_kt:.2f}".replace(".", ","),
        unit="genomsnitt",
        delta=f"{delta_kt_pct:+.1f}%".replace(".", ","),
        delta_direction="up" if delta_kt_pct > 0 else "down" if delta_kt_pct < 0 else "flat",
        variant="accent",
        tooltip="Genomsnittlig köpeskillingskoefficient. Högre = dyrare bostäder relativt taxeringsvärde.",
    ),
    kpi_card(
        label="Befolkningsförändring",
        value=format_pct(pop_change_pct),
        delta=f"{(pop_now - pop_prev):+,.0f}".replace(",", "\u00A0"),
        delta_direction="up" if pop_change_pct > 0 else "down" if pop_change_pct < 0 else "flat",
        variant="success",
        tooltip="Procentuell befolkningsförändring jämfört med föregående år.",
    ),
])

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Chart row: Choropleth + Distribution histogram ───────────────────
col_map, col_hist = st.columns([3, 2])

with col_map:
    with st.container(border=True):
        st.markdown(
            card_header("Geografisk fördelning", f"Version C · {selected_year}", "KOROPLETKARTA"),
            unsafe_allow_html=True,
        )
        if len(df_ranked) > 0:
            render_choropleth(df_ranked, key="rv_choropleth")
        else:
            st.info("Ingen data tillgänglig för kartvisning.")
        with st.expander("Om kartan"):
            st.markdown(
                "Varje kommun visas som ett ifyllt polygon. Färgen baseras på "
                "z-poängen (Version C). Grön = låg risk, röd = hög risk. "
                "Håll musen över en kommun för att se detaljer. "
                "Små kommunnamn visas först när du zoomat in två steg från "
                "startläget (zoomkontrollen +). De är förankrade i kartfilens "
                "centrum. Bakgrundskartan visar inga världsstäder — övrig text "
                "kommer från SHAI-data.",
            )

with col_hist:
    with st.container(border=True):
        st.markdown(
            card_header("Fördelning av SHAI poäng", f"Version C · {selected_year}", "HISTOGRAM"),
            unsafe_allow_html=True,
        )
        if "z_c" in df_ranked.columns and len(df_ranked) > 0:
            z_vals = df_ranked["z_c"].dropna()

            fig = go.Figure()

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
                        hovertemplate="<b>%{x:.2f}</b><br>Antal: %{y}<extra></extra>",
                    ))

            median_z = z_vals.median()
            fig.add_vline(
                x=median_z,
                line_dash="dash",
                line_color=COLORS["primary"],
                line_width=1.5,
                annotation_text=f"Median: {median_z:.2f}",
                annotation_position="top",
                annotation_font=dict(size=11, color=COLORS["primary"]),
            )

            layout = get_chart_layout(
                height=400,
                xaxis_title="SHAI poäng (z-poäng)",
                yaxis_title="Antal kommuner",
            )
            layout["barmode"] = "stack"
            fig.update_layout(**layout)

            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        with st.expander("Om fördelningsgrafen"):
            st.markdown(
                "Histogrammet visar hur SHAI-poängen (z-poäng) fördelar sig bland kommunerna. "
                "Färgerna speglar riskklasserna: grön (z ≤ −0,67), gul (−0,67 < z ≤ 0,67), "
                "röd (z > 0,67). Den streckade linjen visar medianen.",
            )

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
            <td class="rank-cell">{i}</td>
            <td class="kommun-name">{name}</td>
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
            _build_ranking_table(
                df_ranked, ascending=False, title="Sämst överkomlighet (topp 15)"
            ),
            unsafe_allow_html=True,
        )

    with col_best:
        st.markdown(
            _build_ranking_table(
                df_ranked, ascending=True, title="Bäst överkomlighet (topp 15)"
            ),
            unsafe_allow_html=True,
        )

    with st.expander("Om rankningstabellerna"):
        st.markdown(
            "Tabellerna visar de 15 kommuner med sämst respektive bäst överkomlighet "
            "enligt Version C (realversion). Z-poängen anger hur långt kommunen avviker "
            "från riksgenomsnittet i standardavvikelser."
        )

# ── Footer ───────────────────────────────────────────────────────────
footer_note()
