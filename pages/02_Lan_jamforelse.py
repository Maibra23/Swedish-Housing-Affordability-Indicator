"""Sida 02 — Län jämförelse.

Jämför 21 län under tre formelversioner (A, B, C) med trendlinjer och rankingtabeller.
"""

import streamlit as st

st.set_page_config(page_title="SHAI · Län jämförelse", layout="wide")

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
        county_panel = pd.read_parquet("data/processed/panel_county.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

# Compute county-level versions by averaging municipal values
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
    },
    "Makroversion (B)": {
        "formula": r"\text{Risk}_B = 0{,}35 \cdot z(P/I) + 0{,}25 \cdot z(R) + 0{,}20 \cdot z(U) + 0{,}20 \cdot z(\pi)",
        "desc": (
            "En sammansatt riskindikator som viktar fyra makrovariabler: pris/inkomst, "
            "ränta, arbetslöshet och inflation. Speglar centralbankens makrotillsynsperspektiv. "
            "Högre värde = högre risk."
        ),
        "col": "version_b",
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
    },
}

# ── Tabs ─────────────────────────────────────────────────────────────
tabs = st.tabs(list(FORMULA_INFO.keys()))

for tab, (tab_name, info) in zip(tabs, FORMULA_INFO.items()):
    with tab:
        st.latex(info["formula"])
        st.markdown(
            f"<div style='font-size:14px;color:#6B7280;margin-bottom:20px;'>{info['desc']}</div>",
            unsafe_allow_html=True,
        )
        if "footnote" in info:
            st.caption(f"ℹ️ {info['footnote']}")

        col_chart, col_table = st.columns([3, 2])

        with col_chart:
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
                        width=2.5 if is_sthlm else 1,
                        color=COLORS["high_risk"] if is_sthlm else COLORS["grid"],
                    ),
                    opacity=1.0 if is_sthlm else 0.5,
                    hovertemplate=f"<b>{name}</b><br>År: %{{x}}<br>Värde: %{{y:,.2f}}<extra></extra>",
                ))

            fig.update_layout(
                title=dict(text=f"{tab_name} — Länsutveckling 2014–2024", font=dict(size=15)),
                xaxis_title="År",
                yaxis_title="Indexvärde",
                font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=12),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                margin=dict(l=50, r=20, t=50, b=50),
                height=420,
                showlegend=False,
                xaxis=dict(gridcolor=COLORS["grid"], dtick=1),
                yaxis=dict(gridcolor=COLORS["grid"]),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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
                        <td class="num">{row['rank']}</td>
                        <td>{row['region_name']}</td>
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
                            <tr><th class="num">#</th><th>Län</th><th class="num">Värde</th></tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
                """, unsafe_allow_html=True)

# ── Cross-formula comparison ─────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.markdown(
    card(
        title="Varför skiljer sig versionerna åt?",
        subtitle="Topp 5 och botten 5 län under varje formel",
        tag="JÄMFÖRELSE",
    ),
    unsafe_allow_html=True,
)

year_data = county_versions[county_versions["year"] == selected_year].copy()

if len(year_data) > 0:
    cols = st.columns(3)
    for col_idx, (name, info) in enumerate(FORMULA_INFO.items()):
        with cols[col_idx]:
            st.markdown(f"**{name}**")
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

st.markdown(
    """<div style="font-size:11px;color:#9CA3AF;text-align:center;padding:12px 0;
    border-top:1px solid #EEF0F3;margin-top:32px;">
    <strong>KÄLLA:</strong> SCB, Riksbanken, Kolada &nbsp;·&nbsp; SHAI v1.3
    </div>""",
    unsafe_allow_html=True,
)
