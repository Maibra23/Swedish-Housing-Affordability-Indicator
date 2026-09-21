"""Sida 02 — Län jämförelse.

Jämför 21 län under tre formelversioner (A, B, C) med trendlinjer och rankingtabeller.
"""

import streamlit as st

from src.ui.labels import L

st.set_page_config(
    page_title=L("lj.shai_lan_jamforelse"),
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
    card,
    card_header,
    explanation,
    footer_note,
    page_title,
    vintage_badge,
)
from src.ui.chart_theme import CHART_PALETTE, get_chart_layout
from src.ui.data_table import Column, render_table

inject_css()
selections = render_sidebar()

# Period and panel size come from the provenance artifact: a literal
# "2014–2024" keeps asserting itself after the panel has moved on. See T1.10.
PERIOD_START, PERIOD_END = first_year(), complete_case_max_year()
PERIOD = f"{PERIOD_START}–{PERIOD_END}"
N_YEARS = PERIOD_END - PERIOD_START + 1

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = load_artifact("affordability_municipal.parquet")
        county_panel = load_artifact("panel_county.parquet")
except Exception as e:
    st.error(L("lj.kunde_inte_hamta_data_forsok_igen_senare"))
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

# Identify imputed-income years for visual annotation
_imputed_years = set()
if "is_imputed_income" in municipal.columns:
    _imputed_years = set(
        municipal[municipal["is_imputed_income"] == True]["year"].unique()
    )

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow=L("lj.sida_02_regional_jamforelse"),
    title=L("lj.lan_jamforelse"),
    subtitle=L("lj.21_lan_jamforda_under_tre_bostadsekonomiska"),
    year=selected_year,
)

# ── Formula config ───────────────────────────────────────────────────
FORMULA_INFO = {
    "Bankversion (A)": {
        "formula": r"\text{Affordability}_A(i,t) = \frac{I(i,t)}{P_{\text{SEK}}(i,t) \times R(t)}",
        "desc": (
            L("lj.den_enklaste_versionen_mater_hushallets")
        ),
        "col": "version_a",
        "color_highlight": COLORS["high_risk"],
        "color_others": COLORS["secondary"],
    },
    "Makroversion (B)": {
        "formula": r"\text{Risk}_B(i,t) = 0{,}35 \cdot z\!\left(\frac{P_{\text{SEK}}}{I}\right) + 0{,}25 \cdot z(R) + 0{,}20 \cdot z(U) + 0{,}20 \cdot z(\pi)",
        "desc": (
            L("lj.en_sammansatt_riskindikator_som_viktar_fyra")
        ),
        "col": "version_b",
        "color_highlight": COLORS["accent"],
        "color_others": CHART_PALETTE[4],
        "footnote": (
            L("lj.arbetsloshet_avser_oppet_arbetslosa_enligt")
        ),
    },
    "Realversion (C)": {
        "formula": r"\text{Affordability}_C(i,t) = \frac{I(i,t)}{P_{\text{SEK}}(i,t) \times \max(R(t) - \pi(t),\; 0{,}005)}",
        "desc": (
            L("lj.den_rekommenderade_versionen_justerar_for")
        ),
        "col": "version_c",
        "color_highlight": COLORS["low_risk"],
        "color_others": CHART_PALETTE[5],
        "footnote": (
            L("lj.att_olika_formler_rangordnar_lanen_olika_ar")
        ),
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

        st.caption(L("lj.stockholm_visas_som_referenslan_markerat_med"))

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
                        hovertemplate=L("lj.v0_ar_x_varde_y_2f", v0=name),
                    ))

                # Shade imputed-income years
                all_years = sorted(county_versions["year"].unique())
                max_real_year = max((y for y in all_years if y not in _imputed_years), default=None)
                if max_real_year and _imputed_years:
                    # Add a shaded rectangle from first imputed year - 0.5 to last + 0.5
                    imp_start = min(_imputed_years) - 0.5
                    imp_end = max(_imputed_years) + 0.5
                    fig.add_vrect(
                        x0=imp_start, x1=imp_end,
                        fillcolor="rgba(212, 120, 90, 0.08)",
                        line_width=0,
                        annotation_text="Imputerad inkomst",
                        annotation_position="top left",
                        annotation_font_size=10,
                        annotation_font_color=COLORS["accent"],
                    )

                # Determine title suffix
                all_yrs = sorted(county_versions["year"].unique())
                yr_range = f"{min(all_yrs)}–{max(all_yrs)}" if all_yrs else PERIOD

                layout = get_chart_layout(
                    title=L("lj.v0_lansutveckling_v1", v0=tab_name, v1=yr_range),
                    height=420,
                    xaxis_title=L("lj.ar"),
                    yaxis_title=L("lj.indexvarde"),
                    showlegend=False,
                )
                layout["xaxis"]["dtick"] = 1
                fig.update_layout(**layout)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": "hover"})

        with col_table:
            year_data = county_versions[county_versions["year"] == selected_year].copy()
            vcol = info["col"]

            if len(year_data) > 0:
                # Rank 1 = best affordability, in every tab. version_a and
                # version_c read "higher is better" so they sort descending;
                # version_b is a risk score, so it sorts ascending. Sorting all
                # three the same way put the worst county at #1 while the
                # caption above the table said the opposite.
                year_data = year_data.sort_values(
                    vcol, ascending=(vcol == "version_b")
                )
                year_data["rank"] = range(1, len(year_data) + 1)

                st.markdown(
                    render_table(
                        year_data,
                        [
                            Column("#", lambda row: str(row["rank"]), kind="rank"),
                            Column(
                                L("lj.lan"),
                                lambda row: str(row["region_name"]),
                                kind="name",
                            ),
                            Column(
                                L("lj.varde"),
                                lambda row, c=vcol: f"{row[c]:.2f}".replace(".", ","),
                                numeric=True,
                            ),
                        ],
                        title=L("lj.lansranking_v0", v0=selected_year),
                        subtitle=L("lj.ranking_subtitle_v0", v0=tab_name),
                        tag=L("lj.ranking"),
                    ),
                    unsafe_allow_html=True,
                )

# ── Cross-formula comparison ─────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header(
            L("lj.varfor_skiljer_sig_versionerna_at"),
            L("lj.topp_5_och_botten_5_lan_under_varje_formel"),
            L("lj.jamforelse"),
        ),
        unsafe_allow_html=True,
    )

    year_data = county_versions[county_versions["year"] == selected_year].copy()

    if len(year_data) > 0:
        cols = st.columns(3)
        formula_colors = [CHART_PALETTE[0], CHART_PALETTE[4], CHART_PALETTE[6]]
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
                st.markdown(L("lj.samst_overkomlighet"))
                for _, r in worst.iterrows():
                    st.markdown(f"- {r['region_name']}: **{f'{r[vcol]:.2f}'.replace('.', ',')}**")

                best = year_data.nlargest(5, vcol) if ascending else year_data.nsmallest(5, vcol)
                st.markdown(L("lj.bast_overkomlighet"))
                for _, r in best.iterrows():
                    st.markdown(f"- {r['region_name']}: **{f'{r[vcol]:.2f}'.replace('.', ',')}**")

explanation(L("lj.forklaring_kpi"))
with st.expander(L("lj.om_lansjamforelsen")):
    st.markdown(L("lj.om_lansjamforelsen_text"))

vintage_badge()
footer_note()
