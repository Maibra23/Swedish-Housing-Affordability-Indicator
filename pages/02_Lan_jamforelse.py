"""Sida 02 — Län jämförelse.

En flik per formel som kan rangordna annorlunda: Realversion (C) och
Makroversion (B), var och en med trendlinje och rankingtabell. Bankversion (A)
rangordnar identiskt med C och förklaras i jämförelseavsnittet i stället för att
få en egen flik.
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

import pandas as pd

from src.provenance import (
    complete_case_max_year,
    first_year,
    n_kommuner,
    selectable_years,
)
from src.ui.data import load as load_artifact
from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import (
    card,
    risk_pill,
    card_header,
    explanation,
    footer_note,
    page_title,
    vintage_badge,
)
from src.ui.chart_theme import CHART_PALETTE
from src.ui.data_table import Column, render_table
from src.lan.charts import county_colours, county_trend_chart
from src.indices.agreement import (
    inflation_adjustment,
    measure_agreement,
    where_b_and_c_disagree,
)
from src.ui.interpret import explain_inflation_adjustment

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
        # The risk classes live on the ranked artifact, not the municipal one.
        ranked = load_artifact("affordability_ranked.parquet")
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

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow=L("lj.sida_02_regional_jamforelse"),
    title=L("lj.lan_jamforelse"),
    subtitle=L("lj.21_lan_jamforda_under_tre_bostadsekonomiska"),
    year=selected_year,
)

# ── Formula config ───────────────────────────────────────────────────
# Two tabs, not three. Bankversion (A) used to sit here as a peer, which implied
# it corroborated C. It cannot: within a year the rate and inflation are national
# constants, so A and C differ by a single constant factor and rank *identically*
# — rank correlation 1,0000 on this page's own county figures in every year. A
# third tab showing the same ordering with different numbers is not evidence, it
# is the appearance of evidence. Version B is the only formula that can rank
# differently, and it does: rank correlation -0,96 against C.
#
# A is not dropped from the site, but it is no longer presented as a third
# formula. It had a row in the Robusthet class table, identical to C's by
# construction, which is the same misreading in a smaller font. What it has
# instead is the one thing it alone states: the size of the inflation
# adjustment, derived from the selected year in the comparison expander below.
FORMULA_INFO = {
    "Realversion": {
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
    "Makroversion": {
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
}

#: Version A's formula, kept for the comparison expander. It is not a tab; see
#: the note on FORMULA_INFO above.
VERSION_A_FORMULA = r"\text{Affordability}_A(i,t) = \frac{I(i,t)}{P_{\text{SEK}}(i,t) \times R(t)}"

# ── County colours and selection ─────────────────────────────────────
# Every county gets its own colour, keyed by code so it survives a filter change
# or a tab switch. The chart used to draw all 21 in one muted tone, which left
# every line but Stockholm anonymous.
_all_codes = sorted(county_versions["lan_code"].unique())
_colours = county_colours(_all_codes)
_names_by_code = (
    county_versions.drop_duplicates("lan_code").set_index("lan_code")["region_name"].to_dict()
)
_name_to_code = {v: k for k, v in _names_by_code.items()}

# Collapsed: 21 chips expanded is taller than the chart they filter. The count
# below stays visible, so the filter's state is never hidden even when the
# control is.
with st.expander(L("lj.valj_lan")):
    _picked_names = st.multiselect(
        L("lj.valj_lan"),
        options=sorted(_name_to_code),
        default=sorted(_name_to_code),
        key="lj_counties",
        label_visibility="collapsed",
    )
_selected = [_name_to_code[n] for n in _picked_names]
if not _selected:
    st.info(L("lj.inga_lan_valda"))
    st.stop()
st.caption(L("lj.v0_av_v1_lan_visas", v0=len(_selected), v1=len(_all_codes)))

# ── Tabs ─────────────────────────────────────────────────────────────
tabs = st.tabs(list(FORMULA_INFO.keys()))

for tab, (tab_name, info) in zip(tabs, FORMULA_INFO.items()):
    with tab:
        # Full width, with the ranking beneath rather than beside. A 21-series
        # legend in a three-fifths column fitted two entries per row and clipped
        # the longest names; across the full width it fits six and reads cleanly.
        with st.container(border=True):
            st.plotly_chart(
                county_trend_chart(
                    county_versions,
                    value_column=info["col"],
                    selected=_selected,
                    colours=_colours,
                    title=L("lj.v0_lansutveckling_v1", v0=tab_name, v1=PERIOD),
                ),
                width="stretch",
                config={"displayModeBar": "hover"},
            )

        with st.container(border=True):
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

        # The formula sits below the chart, collapsed. It is reference material
        # that a reader consults once and then skips past on every later visit,
        # and at the top of the tab it stood between them and the thing they
        # came for.
        with st.expander(L("lj.formel_och_definition")):
            st.latex(info["formula"])
            st.markdown(info["desc"])
            if "footnote" in info:
                st.caption(info["footnote"])

# ── Cross-formula comparison ─────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# Collapsed, and it now answers its own question before showing the lists. The
# heading asked "why do the versions differ?" and then showed three rankings
# without saying what differs, which left the reader to infer a methodology from
# a set of county names.
with st.expander(L("lj.varfor_skiljer_sig_versionerna_at")):
    st.markdown(L("lj.versionsskillnader_text"))
    st.markdown(
        render_table(
            pd.DataFrame([
                {"v": L("lj.version_a_kort"), "m": L("lj.vad_a_mater"), "r": L("lj.riktning_hogre_battre")},
                {"v": L("lj.version_b_kort"), "m": L("lj.vad_b_mater"), "r": L("lj.riktning_hogre_samre")},
                {"v": L("lj.version_c_kort"), "m": L("lj.vad_c_mater"), "r": L("lj.riktning_hogre_battre")},
            ]),
            [
                Column(L("lj.version"), lambda row: str(row["v"]), kind="name"),
                Column(L("lj.mater"), lambda row: str(row["m"])),
                Column(L("lj.riktning"), lambda row: str(row["r"])),
            ],
        ),
        unsafe_allow_html=True,
    )
    st.markdown(L("lj.darfor_ingen_a_flik"))
    st.latex(VERSION_A_FORMULA)
    st.caption(L("lj.den_enklaste_versionen_mater_hushallets"))

    # What A is for, as one figure rather than as a column. Derived from the
    # selected year: the factor is 4,71 in 2024 and 0,20 in every year from 2015
    # to 2021, where it is two rate floors divided and means nothing about
    # inflation. `explain_inflation_adjustment` picks the sentence that is true.
    st.markdown(explain_inflation_adjustment(inflation_adjustment(municipal, selected_year)))
    st.caption(L("lj.topp_5_och_botten_5_lan_per_flik"))

    year_data = county_versions[county_versions["year"] == selected_year].copy()

    if len(year_data) > 0:
        cols = st.columns(len(FORMULA_INFO))
        formula_colors = [CHART_PALETTE[0], CHART_PALETTE[4]]
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

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# Which formula is load-bearing, and how much the other two corroborate it.
# Before this section the site computed nine scoring columns and displayed three,
# leaving a reader no way to tell which number the rest of the app runs on.
with st.container(border=True):
    st.markdown(
        card_header(
            L("lj.vilken_version_styr"),
            L("lj.vilken_version_styr_underrubrik"),
            L("lj.robusthet"),
        ),
        unsafe_allow_html=True,
    )

    agreement = measure_agreement(ranked, selected_year)
    st.markdown(L("lj.c_driver_sajten"))

    class_rows = pd.DataFrame(
        [
            {
                "version": label,
                **{cls: agreement.counts[key][cls] for cls in ("hog", "medel", "lag")},
            }
            # A is absent on purpose: `risk_a` equals `risk_c` on every row, so
            # the row would have been C's own counts under another name. The
            # level difference it does carry is stated in the expander above.
            for key, label in (
                ("c", L("lj.version_c_kort")),
                ("b", L("lj.version_b_kort")),
            )
        ]
    )
    st.markdown(
        render_table(
            class_rows,
            [
                Column(L("lj.version"), lambda row: str(row["version"]), kind="name"),
                Column(L("lj.hog_risk"), lambda row: str(row["hog"]), numeric=True),
                Column(L("lj.medel_risk"), lambda row: str(row["medel"]), numeric=True),
                Column(L("lj.lag_risk"), lambda row: str(row["lag"]), numeric=True),
            ],
        ),
        unsafe_allow_html=True,
    )
    st.caption(L("lj.antal_kommuner_per_riskklass_v0", v0=str(selected_year)))

    st.markdown(
        L(
            "lj.b_ar_den_enda_som_kan_vara_oense",
            v0=str(agreement.b_differs_from_c),
            v1=str(agreement.n_kommuner),
            v2=f"{agreement.b_differs_pct:.0f}",
        )
    )

    divergent = where_b_and_c_disagree(ranked, selected_year)
    if not divergent.empty:
        st.markdown(
            render_table(
                divergent,
                [
                    Column(L("lj.kommun"), lambda row: str(row["region_name"]), kind="name"),
                    Column(L("lj.version_c_kort"), lambda row: risk_pill(row["risk_c"]), kind="pill"),
                    Column(L("lj.version_b_kort"), lambda row: risk_pill(row["risk_b"]), kind="pill"),
                    Column(L("lj.rangskillnad"), lambda row: str(int(row["rank_gap"])), numeric=True),
                ],
            ),
            unsafe_allow_html=True,
        )
        st.caption(L("lj.storst_avstand_mellan_b_och_c"))

explanation(L("lj.forklaring_kpi"))
with st.expander(L("lj.om_lansjamforelsen")):
    st.markdown(L("lj.om_lansjamforelsen_text"))

vintage_badge()
footer_note()
