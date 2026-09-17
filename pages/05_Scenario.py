"""Sida 05 — Scenariosimulator.

Stresstesta bostadsöverkomlighet (Version C) med ränta-, inkomst- och prisförändringar.
"""

import streamlit as st

from src.ui.labels import L

st.set_page_config(
    page_title="SHAI · Scenariosimulator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None},
)

import pandas as pd
import plotly.graph_objects as go

from src.ui.data import load as load_artifact
from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import (
    vintage_badge,
    page_title, kpi_card, render_kpi_row, format_sek, format_pct,
    card_header, footer_note,
)
from src.ui.chart_theme import get_chart_layout
from src.scenario.simulator import simulate

inject_css()
selections = render_sidebar()

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        county_panel = load_artifact("panel_county.parquet")
except Exception as e:
    st.error(L("sc.kunde_inte_hamta_data_forsok_igen_senare"))
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
county_year = county_panel[county_panel["year"] == selected_year]

if len(county_year) == 0:
    _available = sorted(county_panel["year"].unique(), reverse=True)
    st.warning(
        L("sc.inga_data_tillgangliga_for_v0_valj_ett_ar", v0=selected_year, v1=', '.join(str(y) for y in _available[:5]))
    )
    st.stop()

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 05 · Scenarioanalys",
    title="Scenariosimulator",
    subtitle=L("sc.simulera_effekten_av_ranta_inkomst_och"),
    year=selected_year,
)

# ── Scope note ───────────────────────────────────────────────────────
st.info(
    L("sc.scenariosimulatorn_beraknar_om_version_c")
)

# ── Controls ─────────────────────────────────────────────────────────
county_names = county_year[["lan_code", "region_name"]].sort_values("region_name")
county_options = dict(zip(county_names["region_name"], county_names["lan_code"]))

col_county, col_empty = st.columns([2, 1])
with col_county:
    selected_county_name = st.selectbox(
        L("sc.valj_lan"),
        list(county_options.keys()),
        index=0,
        key="sc_county_select",
    )
selected_county_code = county_options[selected_county_name]

# ── Preset scenario buttons ───────────────────────────────────────────
st.markdown(L("sc.forinstallda_scenarier"))
preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)

_presets = {
    "riksbanken_2022": {"rate": 4.0, "income": 0, "price": -15, "cpi": 8},
    "deflation_risk":  {"rate": -1.0, "income": 0, "price": -10, "cpi": -2},
    L("sc.loneboom"):        {"rate": 1.0, "income": 5, "price": 10, "cpi": 3},
    "reset":           {"rate": 0.0, "income": 0, "price": 0, "cpi": 0},
}

with preset_col1:
    if st.button("Riksbanken 2022", width="stretch", key="sc_preset_2022",
                 help=L("sc.4pp_ranta_8pp_kpi_15_pris")):
        p = _presets["riksbanken_2022"]
        st.session_state["sc_rate_slider"] = float(p["rate"])
        st.session_state["sc_income_slider"] = int(p["income"])
        st.session_state["sc_price_slider"] = int(p["price"])
        st.session_state["sc_cpi_slider"] = float(p["cpi"])
        st.rerun()
with preset_col2:
    if st.button("Deflationsrisk", width="stretch", key="sc_preset_deflation",
                 help=L("sc.1pp_ranta_2pp_kpi_10_pris")):
        p = _presets["deflation_risk"]
        st.session_state["sc_rate_slider"] = float(p["rate"])
        st.session_state["sc_income_slider"] = int(p["income"])
        st.session_state["sc_price_slider"] = int(p["price"])
        st.session_state["sc_cpi_slider"] = float(p["cpi"])
        st.rerun()
with preset_col3:
    if st.button(L("sc.loneboom_2"), width="stretch", key="sc_preset_wage",
                 help=L("sc.1pp_ranta_5_lon_10_pris")):
        p = _presets[L("sc.loneboom")]
        st.session_state["sc_rate_slider"] = float(p["rate"])
        st.session_state["sc_income_slider"] = int(p["income"])
        st.session_state["sc_price_slider"] = int(p["price"])
        st.session_state["sc_cpi_slider"] = float(p["cpi"])
        st.rerun()
with preset_col4:
    if st.button(L("sc.aterstall"), width="stretch", key="sc_preset_reset",
                 help=L("sc.nollstall_alla_scenariojusteringar_till")):
        p = _presets["reset"]
        st.session_state["sc_rate_slider"] = float(p["rate"])
        st.session_state["sc_income_slider"] = int(p["income"])
        st.session_state["sc_price_slider"] = int(p["price"])
        st.session_state["sc_cpi_slider"] = float(p["cpi"])
        st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

col_rate, col_income, col_price, col_cpi = st.columns(4)

with col_rate:
    rate_shock = st.slider(
        L("sc.rantechock_pp"),
        min_value=-2.0,
        max_value=5.0,
        value=float(st.session_state.get("sc_rate_slider", 0.0)),
        step=0.25,
        format="%.2f",
        key="sc_rate_slider",
        help=L("sc.4_pp_riksbankens_hojningscykel_20222023"),
    )

with col_income:
    income_shock_pct = st.slider(
        L("sc.inkomsttillvaxt"),
        min_value=-10,
        max_value=10,
        value=int(st.session_state.get("sc_income_slider", 0)),
        step=1,
        key="sc_income_slider",
        help=L("sc.34_ett_ars_normal_loneutveckling_i_sverige_5"),
    )

with col_price:
    price_shock_pct = st.slider(
        "Prischock (%)",
        min_value=-25,
        max_value=25,
        value=int(st.session_state.get("sc_price_slider", 0)),
        step=5,
        key="sc_price_slider",
        help="−20 % ≈ det svenska bostadsprisfallet 2022. +25 % simulerar en prisspiral.",
    )

with col_cpi:
    cpi_shock = st.slider(
        "KPI-chock (pp)",
        min_value=-5.0,
        max_value=10.0,
        value=float(st.session_state.get("sc_cpi_slider", 0.0)),
        step=0.5,
        format="%.1f",
        key="sc_cpi_slider",
        help=L("sc.8_pp_svensk_inflationstopp_2022_paverkar"),
    )

# ── Run simulation ───────────────────────────────────────────────────
county_row = county_year[county_year["lan_code"] == selected_county_code]

if len(county_row) == 0:
    st.warning(L("sc.inga_data_tillgangliga_for_det_valda_lanet"))
    st.stop()

county_row = county_row.iloc[0]

baseline_panel = {
    "income": county_row["median_income"],
    "transaction_price_sek": county_row["transaction_price_sek"],
    "policy_rate": county_row["policy_rate"],       # percentage points
    "cpi_yoy_pct": county_row["cpi_yoy_pct"],       # percentage points
}

try:
    result = simulate(
        county_kod=selected_county_code,
        rate_shock=rate_shock,                       # already in pp from slider
        income_shock=income_shock_pct / 100.0,
        price_shock=price_shock_pct / 100.0,
        baseline_panel=baseline_panel,
        cpi_shock=cpi_shock,                         # pp — new in Phase 3
    )
except Exception as e:
    st.error(L("sc.berakningsfel_se_metodologisidan_for"))
    st.caption(f"Detaljer: {e}")
    st.stop()

# ── Results ──────────────────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# Determine change direction (for SHAI, higher = better, so positive delta is good)
if result["delta"] > 0:
    change_variant = "success"
    change_direction = "down"  # green arrow down = improving
elif result["delta"] < 0:
    change_variant = "danger"
    change_direction = "up"  # red arrow up = worsening
else:
    change_variant = "default"
    change_direction = "flat"

render_kpi_row([
    kpi_card(
        label="Basfall SHAI",
        value=f"{result['baseline_v_c']:.1f}".replace(".", ","),
        unit="Version C",
        variant="default",
        tooltip=L("sc.basfall_beraknat_fran_faktiska_data_for_valt"),
    ),
    kpi_card(
        label="Scenario SHAI",
        value=f"{result['scenario_v_c']:.1f}".replace(".", ","),
        unit="Version C",
        variant="accent",
        tooltip=L("sc.scenario_beraknat_med_justerade_parametrar"),
    ),
    kpi_card(
        label=L("sc.forandring"),
        value=f"{result['delta']:+.1f}".replace(".", ","),
        unit=L("sc.poang"),
        delta=f"{result['delta_pct']:+.1f}%".replace(".", ","),
        delta_direction=change_direction,
        variant=change_variant,
        tooltip=L("sc.skillnad_mellan_scenario_och_basfall"),
    ),
])

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Side-by-side bar chart + comparison table ────────────────────────
col_chart, col_table = st.columns([3, 2])

with col_chart:
    with st.container(border=True):
        st.markdown(
            card_header(
                f"SHAI Version C — {selected_county_name}",
                "Basfall vs scenario",
                "SIMULERING",
            ),
            unsafe_allow_html=True,
        )

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Basfall", "Scenario"],
            y=[result["baseline_v_c"], result["scenario_v_c"]],
            marker_color=[COLORS["primary"], COLORS["accent"]],
            marker_line_width=0,
            text=[
                f"{result['baseline_v_c']:.1f}".replace(".", ","),
                f"{result['scenario_v_c']:.1f}".replace(".", ","),
            ],
            textposition="outside",
            textfont=dict(family="IBM Plex Mono, monospace", size=14, color=COLORS["text_primary"]),
            hovertemplate="<b>%{x}</b><br>SHAI: %{y:,.1f}<extra></extra>",
            width=0.5,
        ))

        layout = get_chart_layout(height=350, yaxis_title=L("sc.shai_poang"), showlegend=False)
        fig.update_layout(**layout)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": "hover"})

with col_table:
    with st.container(border=True):
        st.markdown(
            card_header(L("sc.jamforelsetabell"), "Basfall vs scenario", "DETALJER"),
            unsafe_allow_html=True,
        )

        comparison_data = {
            "Variabel": [
                "Medianinkomst (SEK)",
                "Transaktionspris (SEK)",
                L("sc.styrranta"),
                "KPI-inflation (%)",
                L("sc.realranta"),
                "SHAI (Version C)",
            ],
            "Basfall": [
                format_sek(result["baseline_income"]),
                format_sek(result["baseline_price"]),
                f"{result['baseline_rate']:.2f}%".replace(".", ","),
                f"{result['baseline_cpi']:.2f}%".replace(".", ","),
                f"{result['real_rate_base']:.2f}%".replace(".", ","),
                f"{result['baseline_v_c']:.1f}".replace(".", ","),
            ],
            "Scenario": [
                format_sek(result["scenario_income"]),
                format_sek(result["scenario_price"]),
                f"{result['scenario_rate']:.2f}%".replace(".", ","),
                f"{result['scenario_cpi']:.2f}%".replace(".", ","),
                f"{result['real_rate_scen']:.2f}%".replace(".", ","),
                f"{result['scenario_v_c']:.1f}".replace(".", ","),
            ],
        }
        st.dataframe(
            pd.DataFrame(comparison_data).set_index("Variabel"),
            width="stretch",
        )

# ── Explanation ──────────────────────────────────────────────────────
with st.expander(L("sc.forklaring")):
    st.markdown(L("sc.version_c_realversion_beraknas_som_text"))

vintage_badge()
footer_note()
