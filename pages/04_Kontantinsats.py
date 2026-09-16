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
from src.ui.data import load as load_artifact
from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import (
    _compact,
    page_title,
    format_sek,
    format_pct,
    card_header,
    footer_note,
    vintage_badge,
    kpi_card,
    render_kpi_row,
)
from src.ui.chart_theme import get_chart_layout
from src.kontantinsats.charts import (
    comparison_barchart,
    comparison_tab_specs,
    fmt_delta_sek,
)
from src.kontantinsats.engine import REGIMES, compare_regimes
from src.kontantinsats.assumptions import render_assumptions
from src.kontantinsats.sections import (
    Context,
    render_baseline_kpis,
    render_regime_cards,
    render_snapshot,
    render_villa_vs_bostadsratt,
)
from src.kontantinsats.regions import (
    _LAN_NAMES,
    REGIME_ACCENT_COLORS,
    REGIME_KEYS,
    REGIME_WHAT_CHANGED,
)

inject_css()
selections = render_sidebar(page_key="ki")

# Granularity copy below quotes the municipality count; it reads the panel
# rather than a literal so it cannot outlive the panel. See T1.10.
N_KOMMUNER = n_kommuner()

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = load_artifact("affordability_municipal.parquet")
        county_data = load_artifact("panel_county.parquet")
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
regime_keys = REGIME_KEYS

# Which regime is cheapest and dearest by monthly cost. Page state, not
# reference data: each comparison chart highlights a different pair.
monthly_costs = {k: results[k]["monthly_total"] for k in regime_keys}
min_cost_key = min(monthly_costs, key=monthly_costs.get)
max_cost_key = max(monthly_costs, key=monthly_costs.get)

# Derived once: read by three display sections and by the comparison charts.
monthly_income = income / 12
cost_pct = baseline["monthly_total"] / monthly_income * 100

# ── Display sections ─────────────────────────────────────────────────
# One context, built once. The sections were extracted verbatim in T3.11;
# the page's job from here is order and nothing else.
_ctx = Context(
    _br_price=_br_price,
    _individual_income=_individual_income,
    _lan_name=_lan_name,
    _villa_price=_villa_price,
    bank_margin=bank_margin,
    bank_margin_pct=bank_margin_pct,
    baseline=baseline,
    cost_pct=cost_pct,
    effective_rate_display_pct=effective_rate_display_pct,
    household_multiplier=household_multiplier,
    household_type=household_type,
    income=income,
    monthly_income=monthly_income,
    max_cost_key=max_cost_key,
    min_cost_key=min_cost_key,
    price=price,
    price_source_label=price_source_label,
    pristyp_fallback_note=pristyp_fallback_note,
    rate=rate,
    regime_keys=regime_keys,
    results=results,
    savings_rate=savings_rate,
    selected_name=selected_name,
    selected_row=selected_row,
    selected_year=selected_year,
    use_bostadsratt=use_bostadsratt,
)

render_snapshot(_ctx)
render_villa_vs_bostadsratt(_ctx)
render_baseline_kpis(_ctx)

# ── 4 · Regelverkstidslinje ───────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        card_header("Regelverksutveckling", "Fem milstolpar 2010–2026", "TIDSLINJE"),
        unsafe_allow_html=True,
    )
    timeline_html = L("ki.fore_2010_bolanetak_amorteringskrav_skarpt", v0=COLORS['text_tertiary'], v1=COLORS['accent'], v2=COLORS['medium_risk'], v3=COLORS['high_risk'], v4=COLORS['low_risk'], v5=COLORS['accent'], v6=COLORS['text_tertiary'], v7=COLORS['text_secondary'], v8=COLORS['text_secondary'], v9=COLORS['text_secondary'], v10=COLORS['text_secondary'])
    st.markdown(_compact(timeline_html), unsafe_allow_html=True)

render_regime_cards(_ctx)

# ── 6 · Jämförelsetabeller (with reference lines) ─────────────────────
# Specs live with the chart they configure; the page owns only the order.
_COMPARISON_TABS = comparison_tab_specs(monthly_income=monthly_income)

with st.container(border=True):
    st.caption(L("ki.valj_flik_for_att_jamfora_regelverken_fran"))
    for tab, spec in zip(st.tabs([s["tab"] for s in _COMPARISON_TABS]), _COMPARISON_TABS):
        with tab:
            st.markdown(
                card_header(
                    spec["heading"],
                    f"{selected_name} · {selected_year}",
                    L("ki.jamforelse"),
                ),
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                comparison_barchart(
                    best_key=min_cost_key,
                    worst_key=max_cost_key,
                    y_values=[results[k][spec["metric"]] for k in regime_keys],
                    yaxis_title=spec["yaxis"],
                    value_fmt=spec["value_fmt"],
                    ref_lines=spec["ref_lines"],
                ),
                width="stretch",
                config={"displayModeBar": "hover"},
            )
            st.caption(spec["caption"])

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

render_assumptions(_ctx)

# ── 9 · Footer ────────────────────────────────────────────────────────
vintage_badge()
footer_note(source="SCB, Riksbanken, Finansinspektionen")
