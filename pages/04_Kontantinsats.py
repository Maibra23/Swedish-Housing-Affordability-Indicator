"""Sida 04 — Kontantinsats analys.

Jämförelse av kontantinsatskrav under fem regelverk (pre-2010, bolånetak, amort 1, amort 2, lättnad 2026).

When "Bostadsrätt" is selected the analysis switches to county level (21 län)
because SCB only publishes apartment prices at the county level.
"""

import streamlit as st

from src.ui.labels import L

st.set_page_config(
    page_title="SHAI · Kontantinsats",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None},
)

import pandas as pd
import plotly.graph_objects as go

from src.provenance import n_kommuner
from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import (
    _compact,
    page_title,
    format_sek,
    format_pct,
    card_header,
    footer_note,
    kpi_card,
    render_kpi_row,
)
from src.ui.chart_theme import get_chart_layout
from src.kontantinsats.engine import REGIMES, compare_regimes

inject_css()
selections = render_sidebar(page_key="ki")

# Granularity copy below quotes the municipality count; it reads the panel
# rather than a literal so it cannot outlive the panel. See T1.10.
N_KOMMUNER = n_kommuner()

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")
        county_data = pd.read_parquet("data/processed/panel_county.parquet")
except Exception as e:
    st.error(L("ki.kunde_inte_hamta_data_forsok_igen_senare"))
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
mun_year = municipal[municipal["year"] == selected_year]
county_yr = county_data[county_data["year"] == selected_year]

if len(mun_year) == 0:
    _available = sorted(municipal["year"].unique(), reverse=True)
    st.warning(
        L("ki.inga_data_tillgangliga_for_v0_valj_ett_ar", v0=selected_year, v1=', '.join(str(y) for y in _available[:5]))
    )
    st.stop()

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 04 · Kontantinsats",
    title="Kontantinsats analys",
    subtitle="Historiska och nuvarande regelverk och insatskrav",
    year=selected_year,
)

# ── Check bostadsrätt availability (county level) ────────────────────
_has_br_column = "bostadsratt_price_sek" in county_data.columns
_br_available = (
    _has_br_column
    and len(county_yr) > 0
    and county_yr["bostadsratt_price_sek"].notna().any()
)

if not _br_available:
    st.warning(
        L("ki.obs_priserna_avser_smahus_villor_scb")
    )
else:
    st.info(
        L("ki.valj_pristyp_bostadsrattspriser_scb_bo0501c", v0=N_KOMMUNER)
    )

# ── 1 · Controls ──────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        card_header(L("ki.valj_analysenhet"), L("ki.region_pristyp_hushallstyp_och"), "URVAL"),
        unsafe_allow_html=True,
    )

    col_pristyp, col_sel, col_type, col_slider = st.columns([1.1, 2, 1, 1])

    # Pristyp FIRST — determines whether selector shows kommun or län
    with col_pristyp:
        _pristyp_options = [L("ki.smahus_villa")]
        if _br_available:
            _pristyp_options.append(L("ki.bostadsratt"))
        pristyp = st.radio(
            "Pristyp",
            options=_pristyp_options,
            index=0,
            key="ki_pristyp",
            help=(
                L("ki.smahus_scb_bo0501c2_fastighetstyp_220", v0=N_KOMMUNER)
            ),
            horizontal=False,
        )
        use_bostadsratt = (pristyp == L("ki.bostadsratt"))

    # Conditional selector: län for bostadsrätt, kommun for småhus
    with col_sel:
        if use_bostadsratt:
            region_list = sorted(county_yr["region_name"].dropna().unique())
            _default_lan = (
                region_list.index(L("ki.stockholms_lan"))
                if L("ki.stockholms_lan") in region_list else 0
            )
            selected_name = st.selectbox(
                L("ki.valj_lan"),
                region_list,
                index=_default_lan,
                key="ki_lan_select",
            )
        else:
            region_list = sorted(mun_year["region_name"].unique())
            _default_kommun = (
                region_list.index("Stockholm")
                if "Stockholm" in region_list else 0
            )
            selected_name = st.selectbox(
                L("ki.valj_kommun"),
                region_list,
                index=_default_kommun,
                key="ki_kommun_select",
            )

    with col_type:
        household_type = st.radio(
            L("ki.hushallstyp"),
            options=[L("ki.singelhushall"), "Par (2 inkomster)"],
            index=0,
            key="ki_household_type",
            help=(
                L("ki.singelhushall_en_individuell_inkomst_par")
            ),
        )
        household_multiplier = 2 if household_type == "Par (2 inkomster)" else 1

    with col_slider:
        savings_rate = st.slider(
            "Sparkvot (%)",
            min_value=5,
            max_value=25,
            value=10,
            step=1,
            key="ki_savings_slider",
            help=(
                L("ki.andel_av_bruttoinkomsten_som_sparas_arligen")
            ),
        ) / 100.0
        _sparkvot_caption = st.empty()

    # Advanced settings (bank margin)
    with st.expander(L("ki.avancerade_installningar_rantepaslag")):
        st.caption(
            L("ki.riksbankens_styrranta_anvands_som_bas")
        )
        bank_margin_pct = st.slider(
            L("ki.bankens_rantepaslag_pp_ovan_styrrantan"),
            min_value=0.0,
            max_value=3.0,
            value=1.7,
            step=0.1,
            key="ki_bank_margin_slider",
            help=L("ki.faktisk_bolaneranta_styrranta_rantepaslag_0"),
        )
        bank_margin = bank_margin_pct / 100.0

# ── Get data row ─────────────────────────────────────────────────────
if use_bostadsratt:
    selected_row_df = county_yr[county_yr["region_name"] == selected_name]
else:
    selected_row_df = mun_year[mun_year["region_name"] == selected_name]

if len(selected_row_df) == 0:
    st.warning(L("ki.inga_data_tillgangliga_for_den_valda"))
    st.stop()

selected_row = selected_row_df.iloc[0]

# ── Extract values ───────────────────────────────────────────────────
# County name lookup — only needed in kommun mode for BR price provenance
_LAN_NAMES = {
    "01": L("ki.stockholms_lan"), "03": L("ki.uppsala_lan"), "04": L("ki.sodermanlands_lan"),
    "05": L("ki.ostergotlands_lan"), "06": L("ki.jonkopings_lan"), "07": L("ki.kronobergs_lan"),
    "08": L("ki.kalmar_lan"), "09": L("ki.gotlands_lan"), "10": L("ki.blekinge_lan"),
    "12": L("ki.skane_lan"), "13": L("ki.hallands_lan"), "14": L("ki.vastra_gotalands_lan"),
    "17": L("ki.varmlands_lan"), "18": L("ki.orebro_lan"), "19": L("ki.vastmanlands_lan"),
    "20": L("ki.dalarnas_lan"), "21": L("ki.gavleborgs_lan"), "22": L("ki.vasternorrlands_lan"),
    "23": L("ki.jamtlands_lan"), "24": L("ki.vasterbottens_lan"), "25": L("ki.norrbottens_lan"),
}

pristyp_fallback_note: str | None = None
if use_bostadsratt:
    # County mode — both prices come from the county panel
    _br_price = selected_row.get("bostadsratt_price_sek")
    _villa_price = selected_row.get("transaction_price_sek")
    if pd.notna(_br_price):
        price = _br_price
        price_source_label = L("ki.bostadsratt_v0_scb_bo0501c", v0=selected_name)
    else:
        price = _villa_price
        pristyp_fallback_note = (
            L("ki.bostadsrattspris_saknas_for_v0_smahuspriset", v0=selected_name)
        )
        price_source_label = L("ki.smahus_fallback")
    _lan_code = str(selected_row.get("lan_code", "")).zfill(2)
    _lan_name = selected_name  # Already at county level
else:
    # Municipality mode — villa price is municipal, BR price is county fallback
    _villa_price = selected_row["transaction_price_sek"]
    price = _villa_price
    _has_br_muni = "bostadsratt_price_sek" in municipal.columns
    _br_price = (
        selected_row["bostadsratt_price_sek"]
        if _has_br_muni and pd.notna(selected_row.get("bostadsratt_price_sek"))
        else None
    )
    price_source_label = L("ki.smahus_scb_bo0501c2")
    _lan_code = str(selected_row.get("lan_code", "")).zfill(2)
    _lan_name = _LAN_NAMES.get(_lan_code, L("ki.lan_v0", v0=_lan_code))

_individual_income = selected_row["median_income"]
income = _individual_income * household_multiplier   # household income
rate = selected_row["policy_rate"] / 100.0
effective_rate_display_pct = selected_row["policy_rate"] + bank_margin_pct

_sparkvot_caption.caption(
    L("ki.v0_sek_ar_v1", v0=format_sek(income * savings_rate), v1='par' if household_multiplier == 2 else 'singel')
)

# ── Compute all regimes ──────────────────────────────────────────────
results = compare_regimes(price, income, rate, savings_rate, bank_margin)
baseline = results["latt_2026"]
regime_keys = ["pre_2010", "bolanetak", "amort_1", "amort_2", "latt_2026"]

# ── 2 · Affordability Snapshot ────────────────────────────────────────
monthly_income = income / 12
pi_ratio       = price / income
insats_yrs     = baseline["required_cash"] / income
cost_pct       = baseline["monthly_total"] / monthly_income * 100
sparår         = baseline["years_to_save"]

if sparår < 5:
    aff_variant, aff_label = "success", L("ki.tillganglig")
elif sparår < 10:
    aff_variant, aff_label = "accent", L("ki.anstrangd")
else:
    aff_variant, aff_label = "danger", L("ki.otillganglig")

render_kpi_row(
    [
        kpi_card(
            label="Pris/Inkomst-kvot",
            value=f"{pi_ratio:.1f}".replace(".", ","),
            unit="x",
            variant="default",
            tooltip=L("ki.under_5x_normalt_510x_anstrangt_over_10x"),
        ),
        kpi_card(
            label=L("ki.kontantinsatsborda"),
            value=f"{insats_yrs:.1f}".replace(".", ","),
            unit=L("ki.x_arsinkomst"),
            variant="default",
            tooltip=L("ki.hur_manga_arsinkomster_kontantinsatsen"),
        ),
        kpi_card(
            label=L("ki.boendekostnadsborda"),
            value=format_pct(cost_pct),
            unit="",
            variant="accent" if cost_pct >= 30 else "default",
            tooltip=L("ki.andel_av_manadsinkomst_under_30_anses"),
        ),
        kpi_card(
            label=L("ki.tillganglighet"),
            value=aff_label,
            unit="",
            variant=aff_variant,
            tooltip=(
                L("ki.tillganglig_under_5_ars_spartid_anstrangd")
            ),
        ),
    ]
)
_level_label = L("ki.lansniva") if use_bostadsratt else L("ki.kommunniva")
st.caption(
    L("ki.nulage_lattnad_2026_v0_v1_v2_sparkvot_v3_0f", v0=selected_name, v1=_level_label, v2=selected_year, v3=savings_rate*100, v4=price_source_label)
)
st.caption(
    L("ki.inkomsten_ar_individuell_bruttoinkomst_scb")
)
if pristyp_fallback_note:
    st.caption(pristyp_fallback_note)

# ── 2b · Villa vs. bostadsrätt side-by-side jämförelse ────────────────
_show_comparison = (
    _villa_price is not None and pd.notna(_villa_price)
    and _br_price is not None and pd.notna(_br_price)
)
if _show_comparison:
    from src.kontantinsats.engine import apply_regime as _apply_regime
    _villa_res = _apply_regime(_villa_price, income, rate, "latt_2026",
                               savings_rate, bank_margin)
    _br_res = _apply_regime(_br_price, income, rate, "latt_2026",
                            savings_rate, bank_margin)
    _ratio = _villa_price / _br_price if _br_price > 0 else float("nan")
    with st.container(border=True):
        st.markdown(
            card_header(
                L("ki.villa_vs_bostadsratt"),
                L("ki.v0_v1_lattnad_2026", v0=selected_name, v1=selected_year),
                L("ki.pristypsjamforelse"),
            ),
            unsafe_allow_html=True,
        )
        c_villa, c_br = st.columns(2)
        with c_villa:
            _villa_level = L("ki.lansniva") if use_bostadsratt else L("ki.kommunniva")
            st.markdown(L("ki.smahus_villa_scb_bo0501c2_v0", v0=_villa_level))
            st.metric("Pris", f"{format_sek(_villa_price)} SEK")
            st.metric("Kontantinsats (10 %)",
                      f"{format_sek(_villa_res['required_cash'])} SEK")
            st.metric(L("ki.ar_att_spara"),
                      f"{_villa_res['years_to_save']:.1f}".replace(".", ",") + L("ki.ar"))
            st.metric(L("ki.manadskostnad"),
                      f"{format_sek(_villa_res['monthly_total'])} SEK")
        with c_br:
            st.markdown(L("ki.bostadsratt_scb_bo0501c_lansniva", ))
            st.metric("Pris", f"{format_sek(_br_price)} SEK")
            st.metric("Kontantinsats (10 %)",
                      f"{format_sek(_br_res['required_cash'])} SEK")
            st.metric(L("ki.ar_att_spara"),
                      f"{_br_res['years_to_save']:.1f}".replace(".", ",") + L("ki.ar"))
            st.metric(L("ki.manadskostnad"),
                      f"{format_sek(_br_res['monthly_total'])} SEK")
        if use_bostadsratt:
            st.caption(
                L("ki.priskvot_villa_bostadsratt_v0_1f_bada_priser", v0=_ratio, v1=selected_name)
            )
        else:
            st.caption(
                L("ki.priskvot_villa_bostadsratt_v0_1f_villapris", v0=_ratio, v1=selected_name, v2=_lan_name)
            )

# ── 3 · Nuläge – baseline KPI strip (enhanced tooltips) ───────────────
render_kpi_row(
    [
        kpi_card(
            label="Kontantinsats (idag)",
            value=format_sek(baseline["required_cash"]),
            unit="SEK",
            variant="accent",
            tooltip=L("ki.total_kontantinsats_10_av_medianpriset_under"),
        ),
        kpi_card(
            label=L("ki.ar_att_spara_idag"),
            value=f"{baseline['years_to_save']:.1f}".replace(".", ","),
            unit=L("ki.ar_2"),
            variant="default",
            tooltip=L("ki.antal_ar_for_att_spara_kontantinsatsen_vid"),
        ),
        kpi_card(
            label=L("ki.manadskostnad_idag"),
            value=format_sek(baseline["monthly_total"]),
            unit="SEK",
            variant="default",
            tooltip=L("ki.rante_amorteringskostnad_per_manad_efter_att"),
        ),
        kpi_card(
            label="Kvarvarande inkomst (idag)",
            value=format_sek(baseline["residual_income"]),
            unit=L("ki.sek_ar"),
            variant="default",
            tooltip=L("ki.inkomst_kvar_efter_att_boendekostnaderna_ar"),
        ),
    ]
)

# ── 4 · Regelverkstidslinje ───────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        card_header("Regelverksutveckling", "Fem milstolpar 2010–2026", "TIDSLINJE"),
        unsafe_allow_html=True,
    )
    timeline_html = L("ki.fore_2010_bolanetak_amorteringskrav_skarpt", v0=COLORS['text_tertiary'], v1=COLORS['accent'], v2=COLORS['medium_risk'], v3=COLORS['high_risk'], v4=COLORS['low_risk'], v5=COLORS['accent'], v6=COLORS['text_tertiary'], v7=COLORS['text_secondary'], v8=COLORS['text_secondary'], v9=COLORS['text_secondary'], v10=COLORS['text_secondary'])
    st.markdown(_compact(timeline_html), unsafe_allow_html=True)

# ── 5 · Regime cards ─────────────────────────────────────────────────

def _fmt_delta_sek(delta: float) -> str | None:
    """Format a SEK delta: hide zeros, round to tkr when >= 10 000."""
    if abs(delta) < 1:
        return None
    if abs(delta) >= 10_000:
        tkr = round(delta / 1_000)
        sign = "+" if tkr > 0 else ""
        return f"{sign}{tkr}\u00A0tkr"
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:,.0f}\u00A0SEK".replace(",", "\u00A0")


monthly_costs = {k: results[k]["monthly_total"] for k in regime_keys}
min_cost_key = min(monthly_costs, key=monthly_costs.get)
max_cost_key = max(monthly_costs, key=monthly_costs.get)

REGIME_WHAT_CHANGED = {
    "pre_2010": L("ki.ingen_formell_insatsniva_hog_belaning_var"),
    "bolanetak": L("ki.bolanetak_infors_max_85_belaning_hogre"),
    "amort_1": L("ki.amorteringskrav_infors_hogre_manadskostnad"),
    "amort_2": L("ki.skarpt_amorteringskrav_skuldkvot_lti_4_5"),
    "latt_2026": L("ki.bolanetak_hojt_till_90_insats_10_skarpt"),
}

regime_accent_colors = {
    "pre_2010": COLORS["text_tertiary"],
    "bolanetak": COLORS["accent"],
    "amort_1": COLORS["medium_risk"],
    "amort_2": COLORS["high_risk"],
    "latt_2026": COLORS["low_risk"],
}

with st.container(border=True):
    st.markdown(
        card_header(
            "Kontantinsatskrav per regelverk",
            f"{selected_name} · {selected_year}",
            "FEM REGIMER",
        ),
        unsafe_allow_html=True,
    )

    regime_cols = st.columns(5)
    for col, key in zip(regime_cols, regime_keys):
        with col:
            res = results[key]
            regime = REGIMES[key]
            tag = L("ki.lagst") if key == min_cost_key else L("ki.hogst") if key == max_cost_key else ""

            with st.container(border=True):
                st.markdown(
                    card_header(regime["label"], regime["period"], tag),
                    unsafe_allow_html=True,
                )
                st.caption(REGIME_WHAT_CHANGED.get(key, ""))

                delta_cash = res["required_cash"] - baseline["required_cash"]
                delta_years = res["years_to_save"] - baseline["years_to_save"]
                delta_cost = res["monthly_total"] - baseline["monthly_total"]

                st.metric(
                    "Kontantinsats",
                    f"{format_sek(res['required_cash'])} SEK",
                    delta=_fmt_delta_sek(delta_cash) if key != "latt_2026" else None,
                    delta_color="inverse",
                    help=L("ki.kontantinsats_ar_eget_kapital_insats_som"),
                )
                st.metric(
                    L("ki.ar_att_spara"),
                    f"{res['years_to_save']:.1f}".replace(".", ",") + L("ki.ar"),
                    delta=(
                        (L("ki.v0_1f_ar", v0=delta_years).replace(".", ","))
                        if (key != "latt_2026" and abs(delta_years) >= 0.05)
                        else None
                    ),
                    delta_color="inverse",
                    help=L("ki.antal_ar_for_att_spara_kontantinsatsen_vid_2"),
                )
                st.metric(
                    L("ki.manadskostnad"),
                    f"{format_sek(res['monthly_total'])} SEK",
                    delta=_fmt_delta_sek(delta_cost) if key != "latt_2026" else None,
                    delta_color="inverse",
                    help=L("ki.summa_amortering_rantekostnad_per_manad"),
                )

                if key == "pre_2010":
                    st.caption(L("ki.obs_inget_formellt_insatskrav_men_banker"))

# ── 6 · Jämförelsetabeller (with reference lines) ─────────────────────
def _comparison_barchart(
    *,
    y_values: list[float],
    yaxis_title: str,
    value_fmt: str,
    ref_lines: list[dict] | None = None,
) -> go.Figure:
    fig = go.Figure()

    labels = [REGIMES[k]["label"] for k in regime_keys]
    bar_colors: list[str] = []
    for k in regime_keys:
        if k == min_cost_key:
            bar_colors.append(COLORS["low_risk"])
        elif k == max_cost_key:
            bar_colors.append(COLORS["high_risk"])
        else:
            bar_colors.append(regime_accent_colors.get(k, COLORS["secondary"]))

    text = []
    for v in y_values:
        if value_fmt == "sek":
            text.append(f"{v:,.0f} SEK".replace(",", "\u00A0"))
        elif value_fmt == "years":
            text.append(f"{v:.1f}".replace(".", ",") + L("ki.ar"))
        else:
            text.append(str(v))

    fig.add_trace(
        go.Bar(
            x=labels,
            y=y_values,
            marker_color=bar_colors,
            marker_line_width=0,
            text=text,
            textposition="outside",
            textfont=dict(family="IBM Plex Mono, monospace", size=12),
            hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
        )
    )

    if ref_lines:
        for rl in ref_lines:
            fig.add_hline(
                y=rl["y"],
                line_dash=rl.get("dash", "dot"),
                line_color=rl.get("color", COLORS["text_secondary"]),
                line_width=rl.get("width", 1.5),
                annotation_text=rl.get("label", ""),
                annotation_position=rl.get("annotation_position", "top left"),
                annotation_font_size=11,
                annotation_font_color=rl.get(
                    "annotation_font_color", COLORS["text_secondary"]
                ),
            )

    layout = get_chart_layout(height=380, yaxis_title=yaxis_title, showlegend=False)
    fig.update_layout(**layout)
    return fig


with st.container(border=True):
    st.caption(
        L("ki.valj_flik_for_att_jamfora_regelverken_fran")
    )
    tab_cost, tab_save, tab_residual = st.tabs(
        [L("ki.manadskostnad"), L("ki.ar_att_spara"), "Kvarvarande inkomst"]
    )

    with tab_cost:
        st.markdown(
            card_header(
                L("ki.manadskostnad_per_regelverk"),
                f"{selected_name} · {selected_year}",
                L("ki.jamforelse"),
            ),
            unsafe_allow_html=True,
        )
        costs = [results[k]["monthly_total"] for k in regime_keys]
        st.plotly_chart(
            _comparison_barchart(
                y_values=costs,
                yaxis_title=L("ki.manadskostnad_sek"),
                value_fmt="sek",
                ref_lines=[
                    {
                        "y": monthly_income * 0.30,
                        "color": COLORS["text_secondary"],
                        "dash": "dot",
                        "width": 1.5,
                        "label": L("ki.30_av_manadsink_v0_sek", v0=format_sek(monthly_income * 0.30)),
                    }
                ],
            ),
            width="stretch",
            config={"displayModeBar": "hover"},
        )
        st.caption(L("ki.lagre_manadskostnad_innebar_mindre_lopande"))

    with tab_save:
        st.markdown(
            card_header(
                L("ki.ar_att_spara_kontantinsats"),
                f"{selected_name} · {selected_year}",
                L("ki.jamforelse"),
            ),
            unsafe_allow_html=True,
        )
        years = [results[k]["years_to_save"] for k in regime_keys]
        st.plotly_chart(
            _comparison_barchart(
                y_values=years,
                yaxis_title=L("ki.ar_att_spara"),
                value_fmt="years",
                ref_lines=[
                    {
                        "y": 5,
                        "color": COLORS["low_risk"],
                        "dash": "dot",
                        "width": 1.5,
                        "label": L("ki.5_ar_tillganglig"),
                        "annotation_position": "bottom right",
                        "annotation_font_color": COLORS["low_risk"],
                    },
                    {
                        "y": 10,
                        "color": COLORS["high_risk"],
                        "dash": "dot",
                        "width": 1.5,
                        "label": L("ki.10_ar_otillganglig"),
                        "annotation_position": "top left",
                        "annotation_font_color": COLORS["high_risk"],
                    },
                ],
            ),
            width="stretch",
            config={"displayModeBar": "hover"},
        )
        st.caption(L("ki.sparkvoten_paverkar_framst_sparar"))

    with tab_residual:
        st.markdown(
            card_header(
                "Kvarvarande inkomst per regelverk",
                f"{selected_name} · {selected_year}",
                L("ki.jamforelse"),
            ),
            unsafe_allow_html=True,
        )
        residuals = [results[k]["residual_income"] for k in regime_keys]
        st.plotly_chart(
            _comparison_barchart(
                y_values=residuals,
                yaxis_title=L("ki.kvarvarande_inkomst_sek_ar"),
                value_fmt="sek",
                ref_lines=[
                    {
                        "y": 0,
                        "color": COLORS["high_risk"],
                        "dash": "dash",
                        "width": 1.5,
                        "label": L("ki.nollgrans"),
                    }
                ],
            ),
            width="stretch",
            config={"displayModeBar": "hover"},
        )
        st.caption(L("ki.hogre_kvarvarande_inkomst_innebar_mer"))

# ── 7 · Nyckelinsikt ─────────────────────────────────────────────────
best_key  = min(regime_keys, key=lambda k: results[k]["monthly_total"])
worst_key = max(regime_keys, key=lambda k: results[k]["monthly_total"])
cost_diff = results[worst_key]["monthly_total"] - results[best_key]["monthly_total"]
pct_diff  = cost_diff / results[best_key]["monthly_total"] * 100

_hushall_label = "par" if household_multiplier == 2 else L("ki.singelhushall_2")
_rate_note = (
    L("ki.styrranta_v0_2f_paslag_v1_1f_pp_v2_2f", v0=selected_row['policy_rate'], v1=bank_margin_pct, v2=effective_rate_display_pct)
    if bank_margin_pct > 0
    else L("ki.styrranta_v0_2f", v0=selected_row['policy_rate'])
)
insight_html = L("ki.nyckelinsikt_syntes_for_ett_v2_v3_under", v0=COLORS['accent'], v1=COLORS['text_primary'], v2=_hushall_label, v3=_rate_note, v4=format_sek(baseline['required_cash']), v5=baseline['years_to_save'], v6=int(savings_rate*100), v7=format_sek(baseline['monthly_total']), v8=cost_pct, v9=REGIMES[best_key]['label'], v10=format_sek(cost_diff), v11=pct_diff)
st.markdown(_compact(insight_html), unsafe_allow_html=True)

# ── 8 · Detaljer & antaganden ─────────────────────────────────────────
with st.expander("Detaljer & antaganden"):
    _region_label = L("ki.lan") if use_bostadsratt else "Kommun"
    st.markdown(
        L("ki.indata_v1_v2_analysar_v3_pristyp_v4_pris", v0=COLORS['text_secondary'], v1=_region_label, v2=selected_name, v3=selected_year, v4=price_source_label, v5=format_sek(price))
        + (
            L("ki.smahuspris_referens_v0_sek", v0=format_sek(_villa_price))
            if _villa_price is not None and pd.notna(_villa_price) and use_bostadsratt
            else ""
        )
        + (
            L("ki.bostadsrattspris_referens_v0_v1_sek", v0=_lan_name, v1=format_sek(_br_price))
            if _br_price is not None and pd.notna(_br_price) and not use_bostadsratt
            else ""
        ) +
        L("ki.hushallstyp_v0_individuell_medianinkomst_v1", v0=household_type, v1=format_sek(_individual_income), v2=format_sek(income), v3=' (2 × individuell)' if household_multiplier == 2 else '', v4=selected_row['policy_rate'], v5=bank_margin_pct, v6=effective_rate_display_pct, v7=int(savings_rate*100)),
        unsafe_allow_html=True,
    )

    st.markdown(
        L("ki.sa_laser_du_tabellen_kolumner_visar_skillnad", v0=COLORS['text_secondary']),
        unsafe_allow_html=True,
    )

    rows = []
    for key in regime_keys:
        res = results[key]
        regime = REGIMES[key]
        rows.append(
            {
                "Regelverk": regime["label"],
                "Period": regime["period"],
                "Insats": float(res["required_cash"]),
                "Δ Insats": float(res["required_cash"] - baseline["required_cash"]),
                L("ki.sparar"): float(res["years_to_save"]),
                L("ki.sparar_2"): float(res["years_to_save"] - baseline["years_to_save"]),
                L("ki.mankostnad"): float(res["monthly_total"]),
                L("ki.mankostnad_2"): float(res["monthly_total"] - baseline["monthly_total"]),
                "Kvar": float(res["residual_income"]),
                "Δ Kvar": float(res["residual_income"] - baseline["residual_income"]),
                "LTV": float(res["ltv"]),
                "LTI": float(res["lti"]),
                "Amort.": float(res["amort_pct"]),
            }
        )

    df = pd.DataFrame(rows)

    def _style_best_worst(_df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame("", index=_df.index, columns=_df.columns)
        if len(_df) == 0:
            return out

        best_bg = "background-color: rgba(46,125,91,0.12);"   # low_risk
        worst_bg = "background-color: rgba(185,74,72,0.10);"  # high_risk

        # Lower is better
        for col in ["Insats", L("ki.sparar"), L("ki.mankostnad")]:
            if col in _df.columns:
                mn, mx = _df[col].min(), _df[col].max()
                out.loc[_df[col] == mn, col] += best_bg
                out.loc[_df[col] == mx, col] += worst_bg

        # Higher is better
        if "Kvar" in _df.columns:
            mn, mx = _df["Kvar"].min(), _df["Kvar"].max()
            out.loc[_df["Kvar"] == mx, "Kvar"] += best_bg
            out.loc[_df["Kvar"] == mn, "Kvar"] += worst_bg

        return out

    styled = df.style.apply(_style_best_worst, axis=None)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_order=[
            "Regelverk",
            "Period",
            "Insats",
            "Δ Insats",
            L("ki.sparar"),
            L("ki.sparar_2"),
            L("ki.mankostnad"),
            L("ki.mankostnad_2"),
            "Kvar",
            "Δ Kvar",
            "LTV",
            "LTI",
            "Amort.",
        ],
        column_config={
            "Regelverk": st.column_config.TextColumn("Regelverk", help=L("ki.regim_regelverk_som_jamfors")),
            "Period": st.column_config.TextColumn("Period", help=L("ki.tidsperiod_da_regelverket_gallde")),
            "Insats": st.column_config.NumberColumn("Insats (SEK)", format="%.0f", help=L("ki.kontantinsats_i_sek_lagre_ar_battre")),
            "Δ Insats": st.column_config.NumberColumn("Δ Insats vs idag", format="%+.0f", help=L("ki.skillnad_i_insats_jamfort_med_nuvarande")),
            L("ki.sparar"): st.column_config.NumberColumn(L("ki.sparar"), format="%.1f", help=L("ki.ar_att_spara_kontantinsatsen_vid_vald")),
            L("ki.sparar_2"): st.column_config.NumberColumn(L("ki.sparar_vs_idag"), format="%+.1f", help=L("ki.skillnad_i_sparar_jamfort_med_nuvarande")),
            L("ki.mankostnad"): st.column_config.NumberColumn(L("ki.mankostnad_sek"), format="%.0f", help=L("ki.manadskostnad_ranta_amortering_lagre_ar")),
            L("ki.mankostnad_2"): st.column_config.NumberColumn(L("ki.mankostnad_vs_idag"), format="%+.0f", help=L("ki.skillnad_i_manadskostnad_jamfort_med_idag")),
            "Kvar": st.column_config.NumberColumn(L("ki.kvar_sek_ar"), format="%.0f", help=L("ki.kvarvarande_inkomst_per_ar_efter")),
            "Δ Kvar": st.column_config.NumberColumn("Δ Kvar vs idag", format="%+.0f", help=L("ki.skillnad_i_kvarvarande_inkomst_jamfort_med")),
            "LTV": st.column_config.NumberColumn("LTV", format="%.0f%%", help=L("ki.belaningsgrad_lan_bostadspris")),
            "LTI": st.column_config.NumberColumn("LTI", format="%.1f", help=L("ki.skuldkvot_lan_arsinkomst")),
            "Amort.": st.column_config.NumberColumn("Amort.", format="%.1f%%", help=L("ki.arlig_amortering_i_av_lanet")),
        },
    )

# ── 9 · Footer ────────────────────────────────────────────────────────
footer_note(source="SCB, Riksbanken, Finansinspektionen")
