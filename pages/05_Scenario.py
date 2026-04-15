"""Sida 05 — Scenariosimulator.

Stresstesta bostadsöverkomlighet (Version C) med ränta-, inkomst- och prisförändringar.
"""

import streamlit as st

st.set_page_config(page_title="SHAI · Scenariosimulator", layout="wide")

import pandas as pd
import plotly.graph_objects as go

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title, kpi_card, render_kpi_row, format_sek, format_pct
from src.scenario.simulator import simulate

inject_css()
selections = render_sidebar()

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        county_panel = pd.read_parquet("data/processed/panel_county.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
county_year = county_panel[county_panel["year"] == selected_year]

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 05 · Scenarioanalys",
    title="Scenariosimulator",
    subtitle="Simulera effekten av ränta-, inkomst- och prisförändringar på bostadsöverkomligheten",
)

# ── Scope note ───────────────────────────────────────────────────────
st.info(
    "**Scenariosimulatorn** beräknar om Version C (realversion) för valt län. "
    "Versionerna A och B innehåller ytterligare variabler (arbetslöshet) som inte "
    "ingår i simulatorn för att hålla gränssnittet enkelt."
)

# ── Controls ─────────────────────────────────────────────────────────
county_names = county_year[["lan_code", "region_name"]].sort_values("region_name")
county_options = dict(zip(county_names["region_name"], county_names["lan_code"]))

col_county, col_empty = st.columns([2, 1])
with col_county:
    selected_county_name = st.selectbox(
        "Välj län",
        list(county_options.keys()),
        index=0,
    )
selected_county_code = county_options[selected_county_name]

col_rate, col_income, col_price = st.columns(3)

with col_rate:
    rate_shock = st.slider(
        "Räntechock (procentenheter)",
        min_value=-2.0,
        max_value=5.0,
        value=0.0,
        step=0.25,
        format="%.2f",
    )

with col_income:
    income_shock_pct = st.slider(
        "Inkomsttillväxt (%)",
        min_value=-10,
        max_value=10,
        value=0,
        step=1,
    )

with col_price:
    price_shock_pct = st.slider(
        "Prischock (%)",
        min_value=-25,
        max_value=25,
        value=0,
        step=5,
    )

# ── Run simulation ───────────────────────────────────────────────────
county_row = county_year[county_year["lan_code"] == selected_county_code]

if len(county_row) == 0:
    st.warning("Inga data tillgängliga för det valda länet och året.")
    st.stop()

county_row = county_row.iloc[0]

baseline_panel = {
    "income": county_row["median_income"],
    "kt_ratio": county_row["kt_ratio"],
    "policy_rate": county_row["policy_rate"] / 100.0,  # Convert % to decimal
    "cpi_yoy_pct": county_row["cpi_yoy_pct"] / 100.0,
}

try:
    result = simulate(
        county_kod=selected_county_code,
        rate_shock=rate_shock / 100.0,  # Convert from pct points to decimal
        income_shock=income_shock_pct / 100.0,
        price_shock=price_shock_pct / 100.0,
        baseline_panel=baseline_panel,
    )
except Exception as e:
    st.error("Beräkningsfel. Se metodologisidan för detaljer.")
    st.caption(f"Detaljer: {e}")
    st.stop()

# ── Results ──────────────────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# KPI row
delta_direction = "down" if result["delta"] > 0 else "up" if result["delta"] < 0 else "flat"
render_kpi_row([
    kpi_card(
        label="Basfall SHAI",
        value=f"{result['baseline_v_c']:.1f}".replace(".", ","),
        unit="Version C",
        variant="default",
    ),
    kpi_card(
        label="Scenario SHAI",
        value=f"{result['scenario_v_c']:.1f}".replace(".", ","),
        unit="Version C",
        variant="accent",
    ),
    kpi_card(
        label="Förändring",
        value=f"{result['delta']:+.1f}".replace(".", ","),
        delta=f"{result['delta_pct']:+.1f}%".replace(".", ","),
        delta_direction=delta_direction,
        variant="success" if result["delta"] > 0 else "danger" if result["delta"] < 0 else "default",
    ),
])

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# Side-by-side bar chart
col_chart, col_table = st.columns([3, 2])

with col_chart:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Basfall", "Scenario"],
        y=[result["baseline_v_c"], result["scenario_v_c"]],
        marker_color=[COLORS["primary"], COLORS["accent"]],
        text=[f"{result['baseline_v_c']:.1f}".replace(".", ","), f"{result['scenario_v_c']:.1f}".replace(".", ",")],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=14, color=COLORS["text_primary"]),
    ))

    fig.update_layout(
        title=dict(text=f"SHAI Version C — {selected_county_name}", font=dict(size=15)),
        yaxis_title="SHAI poäng",
        font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=12),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=50, r=20, t=60, b=50),
        height=350,
        showlegend=False,
        yaxis=dict(gridcolor=COLORS["grid"]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_table:
    st.markdown("""
    <div class="shai-card">
        <div class="shai-card-header">
            <div>
                <div class="shai-card-title">Jämförelsetabell</div>
                <div class="shai-card-subtitle">Basfall vs scenario</div>
            </div>
            <span class="shai-card-tag">DETALJER</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    comparison_data = {
        "Variabel": ["Medianinkomst (SEK)", "K/T-kvot", "Styrränta (%)", "Realränta (%)", "SHAI (Version C)"],
        "Basfall": [
            format_sek(result["baseline_income"]),
            f"{result['baseline_kt']:.3f}".replace(".", ","),
            f"{result['baseline_rate']*100:.2f}%".replace(".", ","),
            f"{result['real_rate_base']*100:.2f}%".replace(".", ","),
            f"{result['baseline_v_c']:.1f}".replace(".", ","),
        ],
        "Scenario": [
            format_sek(result["scenario_income"]),
            f"{result['scenario_kt']:.3f}".replace(".", ","),
            f"{result['scenario_rate']*100:.2f}%".replace(".", ","),
            f"{result['real_rate_scen']*100:.2f}%".replace(".", ","),
            f"{result['scenario_v_c']:.1f}".replace(".", ","),
        ],
    }
    st.dataframe(
        pd.DataFrame(comparison_data).set_index("Variabel"),
        use_container_width=True,
    )

# ── Explanation expander ─────────────────────────────────────────────
with st.expander("Förklaring"):
    st.markdown("""
    **Version C (realversion)** beräknas som:

    $$\\text{Affordability}_C = \\frac{\\text{Inkomst}}{\\text{K/T} \\times \\max(R - \\pi, 0{,}005)}$$

    Där:
    - **Inkomst** = median disponibel hushållsinkomst (SEK)
    - **K/T** = köpeskillingskoefficient (förhållande mellan köpeskilling och taxeringsvärde)
    - **R** = Riksbankens styrränta (årsgenomsnitt)
    - **π** = KPI-inflation (årsgenomsnitt)
    - **0,005** = golv för att förhindra division med noll vid negativ realränta

    **Tolkning:** Högre värde = bättre bostadsöverkomlighet.

    **Scenariomekanik:**
    - Räntechock adderas till styrräntan (procentenheter)
    - Inkomsttillväxt multipliceras med inkomsten (relativ förändring)
    - Prischock multipliceras med K/T-kvoten (relativ förändring)
    """)

st.markdown(
    """<div style="font-size:11px;color:#9CA3AF;text-align:center;padding:12px 0;
    border-top:1px solid #EEF0F3;margin-top:32px;">
    <strong>KÄLLA:</strong> SCB, Riksbanken, Kolada &nbsp;·&nbsp; SHAI v1.3
    </div>""",
    unsafe_allow_html=True,
)
