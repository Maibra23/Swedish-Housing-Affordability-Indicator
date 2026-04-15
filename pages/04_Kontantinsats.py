"""Sida 04 — Kontantinsats analys.

Jämförelse av kontantinsatskrav under fyra regelverk (pre-2010, bolånetak, amort 1, amort 2).
"""

import streamlit as st

st.set_page_config(page_title="SHAI · Kontantinsats", layout="wide")

import pandas as pd
import plotly.graph_objects as go

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title, kpi_card, render_kpi_row, format_sek
from src.kontantinsats.engine import REGIMES, apply_regime, compare_regimes

inject_css()
selections = render_sidebar()

# ── Load data ────────────────────────────────────────────────────────
try:
    with st.spinner("Laddar data..."):
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
mun_year = municipal[municipal["year"] == selected_year]

# ── Page title ───────────────────────────────────────────────────────
page_title(
    eyebrow="Sida 04 · Kontantinsats",
    title="Kontantinsats analys",
    subtitle="Historiska regelverk och insatskrav per kommun",
)

# ── Kommun selector + savings slider ─────────────────────────────────
col_sel, col_slider = st.columns([2, 1])

kommun_list = sorted(mun_year["region_name"].unique())
with col_sel:
    selected_kommun = st.selectbox(
        "Välj kommun",
        kommun_list,
        index=kommun_list.index("Stockholm") if "Stockholm" in kommun_list else 0,
    )

with col_slider:
    savings_rate = st.slider(
        "Sparkvot (%)",
        min_value=5,
        max_value=25,
        value=10,
        step=1,
    ) / 100.0

# Get kommun data
kommun_row = mun_year[mun_year["region_name"] == selected_kommun]
if len(kommun_row) == 0:
    st.warning("Inga data tillgängliga för den valda kommunen.")
    st.stop()

kommun_row = kommun_row.iloc[0]
price = kommun_row["transaction_price_sek"]
income = kommun_row["median_income"]
rate = kommun_row["policy_rate"] / 100.0  # Convert from % to decimal

# ── Compute all regimes ──────────────────────────────────────────────
results = compare_regimes(price, income, rate, savings_rate)

# ── Summary KPIs ─────────────────────────────────────────────────────
st.markdown(
    f"<div style='font-size:13px;color:#6B7280;margin-bottom:16px;'>"
    f"<strong>{selected_kommun}</strong> · Medianpris: {format_sek(price)} SEK · "
    f"Medianinkomst: {format_sek(income)} SEK · Ränta: {kommun_row['policy_rate']:.2f}%"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Four regime cards ────────────────────────────────────────────────
regime_keys = ["pre_2010", "bolanetak", "amort_1", "amort_2"]
regime_cols = st.columns(4)

# Find min/max monthly cost for visual indicators
monthly_costs = {k: results[k]["monthly_total"] for k in regime_keys}
min_cost_key = min(monthly_costs, key=monthly_costs.get)
max_cost_key = max(monthly_costs, key=monthly_costs.get)

for col, key in zip(regime_cols, regime_keys):
    with col:
        res = results[key]
        regime = REGIMES[key]

        # Visual indicator
        if key == min_cost_key:
            variant = "success"
            badge = "LÄGST KOSTNAD"
        elif key == max_cost_key:
            variant = "danger"
            badge = "HÖGST KOSTNAD"
        else:
            variant = "default"
            badge = ""

        badge_html = (
            f'<div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;'
            f'color:{"#2E7D5B" if variant == "success" else "#B94A48"};'
            f'font-weight:600;margin-bottom:8px;">{badge}</div>'
            if badge else ""
        )

        st.markdown(f"""
        <div class="shai-kpi-card variant-{variant}">
            {badge_html}
            <div class="shai-kpi-label">{regime['label']}</div>
            <div style="font-size:11px;color:#9CA3AF;margin-bottom:12px;">{regime['period']}</div>

            <div style="margin-bottom:8px;">
                <div style="font-size:10px;text-transform:uppercase;color:#9CA3AF;letter-spacing:0.5px;">Kontantinsats</div>
                <div style="font-size:20px;font-weight:700;color:#1A1A2E;">{format_sek(res['required_cash'])} SEK</div>
            </div>

            <div style="margin-bottom:8px;">
                <div style="font-size:10px;text-transform:uppercase;color:#9CA3AF;letter-spacing:0.5px;">År att spara</div>
                <div style="font-size:18px;font-weight:700;color:#1A1A2E;">{f"{res['years_to_save']:.1f}".replace(".", ",")} år</div>
            </div>

            <div style="margin-bottom:8px;">
                <div style="font-size:10px;text-transform:uppercase;color:#9CA3AF;letter-spacing:0.5px;">Månadskostnad</div>
                <div style="font-size:18px;font-weight:700;color:#1A1A2E;">{format_sek(res['monthly_total'])} SEK</div>
            </div>

            <div>
                <div style="font-size:10px;text-transform:uppercase;color:#9CA3AF;letter-spacing:0.5px;">Kvarvarande inkomst</div>
                <div style="font-size:16px;font-weight:600;color:{'#2E7D5B' if res['residual_income'] > 0 else '#B94A48'};">
                    {format_sek(res['residual_income'])} SEK/år
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Comparison bar chart ─────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

fig = go.Figure()

labels = [REGIMES[k]["label"] for k in regime_keys]
costs = [results[k]["monthly_total"] for k in regime_keys]
bar_colors = []
for k in regime_keys:
    if k == min_cost_key:
        bar_colors.append(COLORS["low_risk"])
    elif k == max_cost_key:
        bar_colors.append(COLORS["high_risk"])
    else:
        bar_colors.append(COLORS["secondary"])

fig.add_trace(go.Bar(
    x=labels,
    y=costs,
    marker_color=bar_colors,
    text=[f"{c:,.0f} SEK".replace(",", " ") for c in costs],
    textposition="outside",
    textfont=dict(family="IBM Plex Mono, monospace", size=12),
))

fig.update_layout(
    title=dict(text="Månadskostnad per regelverk", font=dict(size=15)),
    xaxis_title="Regelverk",
    yaxis_title="Månadskostnad (SEK)",
    font=dict(family="Source Sans 3, Source Sans Pro, sans-serif", size=12),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=50, r=20, t=60, b=50),
    height=380,
    showlegend=False,
    yaxis=dict(gridcolor=COLORS["grid"]),
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Detail table ─────────────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

with st.expander("Detaljerad jämförelse"):
    rows_html = ""
    for key in regime_keys:
        res = results[key]
        regime = REGIMES[key]
        rows_html += f"""
        <tr>
            <td>{regime['label']}</td>
            <td class="num">{format_sek(res['required_cash'])}</td>
            <td class="num">{f"{res['years_to_save']:.1f}".replace(".", ",")}</td>
            <td class="num">{format_sek(res['loan_amount'])}</td>
            <td class="num">{f"{res['ltv']:.0%}"}</td>
            <td class="num">{f"{res['lti']:.1f}".replace(".", ",")}x</td>
            <td class="num">{f"{res['amort_pct']*100:.1f}".replace(".", ",")}%</td>
            <td class="num">{format_sek(res['monthly_total'])}</td>
        </tr>"""

    st.markdown(f"""
    <table class="shai-table">
        <thead>
            <tr>
                <th>Regelverk</th>
                <th class="num">Insats</th>
                <th class="num">År</th>
                <th class="num">Lån</th>
                <th class="num">LTV</th>
                <th class="num">LTI</th>
                <th class="num">Amort.</th>
                <th class="num">Månkostnad</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

st.markdown(
    """<div style="font-size:11px;color:#9CA3AF;text-align:center;padding:12px 0;
    border-top:1px solid #EEF0F3;margin-top:32px;">
    <strong>KÄLLA:</strong> SCB, Riksbanken, Finansinspektionen &nbsp;·&nbsp; SHAI v1.3
    </div>""",
    unsafe_allow_html=True,
)
