"""Sida 02 — Län jämförelse.

Jämför 21 län under tre formelversioner (A, B, C) med trendlinjer och rankingtabeller.
"""

import streamlit as st

st.set_page_config(
    page_title="SHAI · Län jämförelse",
    page_icon="🏠",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None},
)

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title, card, card_header, footer_note
from src.ui.chart_theme import get_chart_layout, CHART_PALETTE

inject_css()
selections = render_sidebar(page_key="lj")

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")
        county_panel = pd.read_parquet("data/processed/panel_county.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

county_versions = (
    municipal.groupby(["lan_code", "year"])
    .agg(
        version_a=("version_a", "mean"),
        version_b=("version_b", "mean"),
        version_c=("version_c", "mean"),
    )
    .reset_index()
)

county_names = county_panel[["lan_code", "region_name"]].drop_duplicates()
county_versions = county_versions.merge(county_names, on="lan_code", how="left")

selected_year = selections["selected_year"]

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 02 · Regional jämförelse",
    title="Län jämförelse",
    subtitle="21 län jämförda under tre bostadsekonomiska formler",
    year=selected_year,
)

# ── Formula config ───────────────────────────────────────────────────
FORMULA_INFO = {
    "Bankversion (A)": {
        "formula": r"\text{Affordability}_A = \frac{\text{Inkomst}}{\text{K/T} \times \text{Ränta}}",
        "desc": (
            "Den enklaste versionen — mäter hushållets betalningsförmåga relativt "
            "bostadens pris och aktuell ränta. Speglar en traditionell bankbedömning. "
            "Högre värde = bättre överkomlighet."
        ),
        "col": "version_a",
        "color_highlight": "#B94A48",
        "color_others": "#4A6FA5",
    },
    "Makroversion (B)": {
        "formula": r"\text{Risk}_B = 0{,}35 \cdot z(P/I) + 0{,}25 \cdot z(R) + 0{,}20 \cdot z(U) + 0{,}20 \cdot z(\pi)",
        "desc": (
            "En sammansatt riskindikator som viktar fyra makrovariabler: pris/inkomst, "
            "ränta, arbetslöshet och inflation. Speglar centralbankens makrotillsynsperspektiv. "
            "Högre värde = högre risk."
        ),
        "col": "version_b",
        "color_highlight": "#C4A35A",
        "color_others": "#7B68A8",
        "footnote": (
            "Arbetslöshet avser öppet arbetslösa enligt Arbetsförmedlingen (18–65 år), "
            "inte AKU."
        ),
    },
    "Realversion (C)": {
        "formula": r"\text{Affordability}_C = \frac{\text{Inkomst}}{\text{K/T} \times \max(R - \pi,\; 0{,}005)}",
        "desc": (
            "Den rekommenderade versionen — justerar för inflation genom att använda "
            "realräntan istället för nominalräntan. Akademiskt förankrad. "
            "Högre värde = bättre överkomlighet."
        ),
        "col": "version_c",
        "color_highlight": "#2E7D5B",
        "color_others": "#D4785A",
    },
}

# ── Tabs ─────────────────────────────────────────────────────────────
tabs = st.tabs(list(FORMULA_INFO.keys()))

for tab, (tab_name, info) in zip(tabs, FORMULA_INFO.items()):
    with tab:
        st.latex(info["formula"])
        st.markdown(
            f"<div style='font-size:14px;color:{COLORS['text_secondary']};margin-bottom:20px;'>"
            f"{info['desc']}</div>",
            unsafe_allow_html=True,
        )
        if "footnote" in info:
            st.caption(f"ℹ️ {info['footnote']}")

        col_chart, col_table = st.columns([3, 2])

        with col_chart:
            with st.container(border=True):
                fig = go.Figure()
                for _, county_row in county_names.iterrows():
                    lk = county_row["lan_code"]
                    name = county_row["region_name"]
                    cdata = county_versions[county_versions["lan_code"] == lk].sort_values("year")
                    if len(cdata) == 0:
                        continue

                    is_sthlm = lk == "01"
                    fig.add_trace(go.Scatter(
                        x=cdata["year"],
                        y=cdata[info["col"]],
                        name=name,
                        mode="lines",
                        line=dict(
                            width=3 if is_sthlm else 1.2,
                            color=info["color_highlight"] if is_sthlm else info["color_others"],
                        ),
                        opacity=1.0 if is_sthlm else 0.35,
                        hovertemplate=f"<b>{name}</b><br>År: %{{x}}<br>Värde: %{{y:,.2f}}<extra></extra>",
                    ))

                layout = get_chart_layout(
                    title=f"{tab_name} — Länsutveckling 2014–2024",
                    height=420,
                    xaxis_title="År",
                    yaxis_title="Indexvärde",
                    showlegend=False,
                )
                layout["xaxis"]["dtick"] = 1
                fig.update_layout(**layout)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        with col_table:
            year_data = county_versions[county_versions["year"] == selected_year].copy()
            vcol = info["col"]

            if len(year_data) > 0:
                ascending = vcol != "version_b"
                year_data = year_data.sort_values(vcol, ascending=ascending)
                year_data["rank"] = range(1, len(year_data) + 1)

                rows_html = ""
                for _, row in year_data.iterrows():
                    rows_html += f"""
                    <tr>
                        <td class="rank-cell">{row['rank']}</td>
                        <td class="kommun-name">{row['region_name']}</td>
                        <td class="num">{f"{row[vcol]:.2f}".replace(".", ",")}</td>
                    </tr>"""

                st.markdown(f"""
                <div class="shai-card">
                    <div class="shai-card-header">
                        <div>
                            <div class="shai-card-title">Länsranking {selected_year}</div>
                            <div class="shai-card-subtitle">{tab_name}</div>
                        </div>
                        <span class="shai-card-tag">RANKING</span>
                    </div>
                    <table class="shai-table">
                        <thead>
                            <tr><th>#</th><th>Län</th><th class="num">Värde</th></tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

# ── Cross-formula comparison ─────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header(
            "Varför skiljer sig versionerna åt?",
            "Topp 5 och botten 5 län under varje formel",
            "JÄMFÖRELSE",
        ),
        unsafe_allow_html=True,
    )

    year_data = county_versions[county_versions["year"] == selected_year].copy()

    if len(year_data) > 0:
        cols = st.columns(3)
        formula_colors = ["#4A6FA5", "#7B68A8", "#3D8B6E"]
        for col_idx, (name, info) in enumerate(FORMULA_INFO.items()):
            with cols[col_idx]:
                st.markdown(
                    f"<div style='font-weight:700;font-size:14px;color:{formula_colors[col_idx]};margin-bottom:8px;'>"
                    f"{name}</div>",
                    unsafe_allow_html=True,
                )
                vcol = info["col"]
                ascending = vcol != "version_b"

                worst = year_data.nsmallest(5, vcol) if ascending else year_data.nlargest(5, vcol)
                st.markdown("*Sämst överkomlighet:*")
                for _, r in worst.iterrows():
                    st.markdown(f"- {r['region_name']}: **{f'{r[vcol]:.2f}'.replace('.', ',')}**")

                best = year_data.nlargest(5, vcol) if ascending else year_data.nsmallest(5, vcol)
                st.markdown("*Bäst överkomlighet:*")
                for _, r in best.iterrows():
                    st.markdown(f"- {r['region_name']}: **{f'{r[vcol]:.2f}'.replace('.', ',')}**")

footer_note()
