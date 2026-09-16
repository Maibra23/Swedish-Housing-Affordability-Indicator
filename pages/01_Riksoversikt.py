"""Sida 01 — Riksöversikt.

Nationell överblick med KPI-kort, karta, histogram och rankingtabeller.
"""

import streamlit as st

from src.ui.labels import L

st.set_page_config(
    page_title=L("rv.shai_riksoversikt"),
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None},
)

import re

import pandas as pd
import plotly.graph_objects as go

from src.provenance import n_kommuner
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
    explanation,
    footer_note,
    help_badge,
    vintage_badge,
)
from src.ui.choropleth import render_choropleth
from src.ui.data_table import Column, render_table
from src.ui.filters import by_risk
from src.ui.chart_theme import get_chart_layout

inject_css()
selections = render_sidebar(page_key="rv")

# ── Load data ────────────────────────────────────────────────────────
# affordability_ranked carries every column of the municipal affordability
# panel plus z_*, rank_* and risk_*. `indices/normalize.py` is the only
# producer of those columns — nothing on this page recomputes them. An earlier
# inline copy here omitted the sign inversion that normalize.py applies to
# versions A and C, which rendered the risk classes upside down for every year
# except 2014. See tests/test_ranked_artifact.py.
try:
    with st.spinner("Laddar data..."):
        ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
except Exception as e:
    st.error(L("rv.kunde_inte_hamta_data_forsok_igen_senare"))
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
selected_risks = selections["selected_risks"]

# The panel's own municipality count — never a literal 290, which stops being
# true the moment a merger or a coverage gap changes the panel. See T1.10.
N_KOMMUNER = n_kommuner()

mun_year = ranked[ranked["year"] == selected_year]
mun_prev = ranked[ranked["year"] == selected_year - 1]

# Empty state — checked before anything reads these frames.
if mun_year.empty:
    st.warning(L("rv.inga_data_tillgangliga_for_den_valda"))
    st.stop()

# Apply risk filter from the multi-select pills. An empty selection is
# normalised to "all three" by the sidebar, so len < 3 means a real filter.
df_ranked = by_risk(mun_year, selected_risks)

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow=L("rv.sida_01_nationell_oversikt"),
    title=L("rv.riksoversikt"),
    subtitle=L("rv.strukturell_bostadsekonomisk_hallbarhet_i", v0=N_KOMMUNER, v1=selected_year),
    year=selected_year,
)

# ── KPI cards ────────────────────────────────────────────────────────
mean_vc = mun_year["version_c"].mean() if len(mun_year) > 0 else 0
mean_vc_prev = mun_prev["version_c"].mean() if len(mun_prev) > 0 else mean_vc
delta_vc = mean_vc - mean_vc_prev
delta_vc_pct = (delta_vc / mean_vc_prev * 100) if mean_vc_prev != 0 else 0

# Risk class is a *within-year* quantile: normalize.py z-scores the municipalities
# against each other inside each year and cuts at ±0.67σ, so the share landing in
# "hog" is near-constant by construction and its year-on-year change measures
# wobble around a fixed boundary, not a change in affordability. The delta is
# therefore gone (T1.9); the national trend belongs to the level series above.
#
# Counted on mun_year, not on the risk-filtered frame: this card says "N of all
# municipalities", so it must not turn into a readout of the sidebar pills.
n_hog = int((mun_year["risk_c"] == "hog").sum())

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
        unit=L("rv.poang"),
        delta=f"{delta_vc_pct:+.1f}%".replace(".", ","),
        delta_direction="up" if delta_vc > 0 else "down" if delta_vc < 0 else "flat",
        variant="default",
        tooltip=L("rv.genomsnittlig_version_c_poang_rakvot_inkomst", v0=N_KOMMUNER),
    ),
    kpi_card(
        label=L("rv.hogrisk_kommuner"),
        value=str(n_hog),
        unit=f"av {N_KOMMUNER} · relativ position {selected_year}",
        variant="danger",
        tooltip=(
            L("rv.antal_kommuner_med_z_poang_0_67")
        ),
    ),
    kpi_card(
        label="K/T-kvot (genomsnitt)",
        value=f"{mean_kt:.2f}".replace(".", ","),
        unit="genomsnitt",
        delta=f"{delta_kt_pct:+.1f}%".replace(".", ","),
        delta_direction="up" if delta_kt_pct > 0 else "down" if delta_kt_pct < 0 else "flat",
        variant="accent",
        tooltip=L("rv.genomsnittlig_kopeskillingskoefficient_k_t"),
    ),
    kpi_card(
        label=L("rv.befolkningsforandring"),
        value=format_pct(pop_change_pct),
        delta=f"{(pop_now - pop_prev):+,.0f}".replace(",", "\u00A0"),
        delta_direction="up" if pop_change_pct > 0 else "down" if pop_change_pct < 0 else "flat",
        variant="success",
        tooltip=L("rv.procentuell_befolkningsforandring_jamfort"),
    ),
])

explanation(L("rv.forklaring_kpi", v0=N_KOMMUNER, v1=selected_year))
vintage_badge()

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Chart row: Choropleth + Distribution histogram ───────────────────
col_map, col_hist = st.columns([3, 2])

with col_map:
    with st.container(border=True):
        st.markdown(
            card_header(
                L("rv.geografisk_fordelning") + help_badge("zpoang", "riskklass"),
                f"Version C · {selected_year}",
                "KOROPLETKARTA",
            ),
            unsafe_allow_html=True,
        )
        if len(df_ranked) > 0:
            render_choropleth(df_ranked, key="rv_choropleth")
            st.caption(L("rv.fargskala_gron_lag_risk_z_0_67_gul_medel"))
            explanation(L("rv.forklaring_karta"))
        else:
            st.info(L("rv.ingen_data_tillganglig_for_kartvisning"))
        with st.expander(L("rv.om_kartan")):
            st.markdown(
                L("rv.varje_kommun_visas_som_ett_ifyllt_polygon"),
            )

with col_hist:
    with st.container(border=True):
        st.markdown(
            card_header(
                L("rv.fordelning_av_shai_poang") + help_badge("zpoang", "version_c"),
                f"Version C · {selected_year}",
                "HISTOGRAM",
            ),
            unsafe_allow_html=True,
        )
        st.caption(L("rv.z_poang_standardavvikelser_pa_logaritmisk"))
        explanation(L("rv.forklaring_histogram", v0=N_KOMMUNER))
        if "z_c" in df_ranked.columns and len(df_ranked) > 0:
            z_vals = df_ranked["z_c"].dropna()

            fig = go.Figure()

            # Colour by the artifact's own risk_c column rather than re-cutting
            # the z-scale here. normalize.py owns the class boundaries; keeping a
            # second copy of them in this page is exactly how the classes drifted
            # out of sync before (Finding N).
            for risk_class, color, name in [
                ("lag", COLORS["low_risk"], L("rv.lag_risk")),
                ("medel", COLORS["medium_risk"], "Medel risk"),
                ("hog", COLORS["high_risk"], L("rv.hog_risk")),
            ]:
                subset = df_ranked.loc[df_ranked["risk_c"] == risk_class, "z_c"].dropna()
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
                xaxis_title=L("rv.shai_poang_z_poang"),
                yaxis_title="Antal kommuner",
            )
            layout["barmode"] = "stack"
            fig.update_layout(**layout)

            st.plotly_chart(fig, width="stretch", config={"displayModeBar": "hover"})

        with st.expander(L("rv.om_fordelningsgrafen")):
            st.markdown(
                L("rv.histogrammet_visar_hur_shai_poangen_z_poang"),
            )

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Table row: Top 15 worst + Top 15 best ────────────────────────────


def _ranking_table(df: pd.DataFrame, ascending: bool, title: str) -> str:
    """Render the top or bottom fifteen municipalities by Version C.

    Args:
        df: The filtered year frame.
        ascending: True for the most affordable end, False for the least.
        title: Card title.

    Returns:
        HTML for one `.shai-table` card, built by the shared renderer so the
        rank cell, name cell, numeric alignment and risk pill are decided in one
        place rather than per page. See T3.8.
    """
    subset = (df.nsmallest(15, "z_c") if ascending else df.nlargest(15, "z_c")).copy()
    subset["_rank"] = range(1, len(subset) + 1)
    return render_table(
        subset,
        [
            Column("#", lambda row: str(row["_rank"]), kind="rank"),
            Column(L("rv.kommun"), lambda row: str(row.get("region_name", "")), kind="name"),
            Column(L("rv.z_poang"), lambda row: f"{row.get('z_c', 0):.2f}", numeric=True),
            Column(L("rv.shai"), lambda row: f"{row.get('version_c', 0):.1f}", numeric=True),
            Column(L("rv.risk"), lambda row: risk_pill(row.get("risk_c", "medel")), kind="pill"),
        ],
        title=title + help_badge("rang", "version_c", "riskklass"),
        subtitle=f"Version C · {selected_year}",
        tag=L("rv.ranking"),
    )


if "z_c" in df_ranked.columns and len(df_ranked) >= 15:
    col_worst, col_best = st.columns(2)

    with col_worst:
        st.markdown(
            _ranking_table(
                df_ranked, ascending=False, title=L("rv.samst_overkomlighet_topp_15")
            ),
            unsafe_allow_html=True,
        )

    with col_best:
        st.markdown(
            _ranking_table(
                df_ranked, ascending=True, title=L("rv.bast_overkomlighet_topp_15")
            ),
            unsafe_allow_html=True,
        )

    explanation(L("rv.forklaring_tabell", v0=selected_year))

    with st.expander(L("rv.om_rankningstabellerna")):
        st.markdown(
            L("rv.tabellerna_visar_de_15_kommuner_med_samst")
        )

# ── Footer ───────────────────────────────────────────────────────────
footer_note()
