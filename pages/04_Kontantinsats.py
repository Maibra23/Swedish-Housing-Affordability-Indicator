"""Sida 04 — Kontantinsats analys.

Jämförelse av kontantinsatskrav under fyra regelverk (pre-2010, bolånetak, amort 1, amort 2).
"""

import streamlit as st

st.set_page_config(
    page_title="SHAI · Kontantinsats",
    page_icon="🏠",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None},
)

import pandas as pd
import plotly.graph_objects as go

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title, format_sek, card_header, footer_note
from src.ui.chart_theme import get_chart_layout
from src.kontantinsats.engine import REGIMES, apply_regime, compare_regimes

inject_css()
selections = render_sidebar(page_key="ki")

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
    year=selected_year,
)

# ── Kommun selector + savings slider ─────────────────────────────────
col_sel, col_slider = st.columns([2, 1])

kommun_list = sorted(mun_year["region_name"].unique())
with col_sel:
    selected_kommun = st.selectbox(
        "Välj kommun",
        kommun_list,
        index=kommun_list.index("Stockholm") if "Stockholm" in kommun_list else 0,
        key="ki_kommun_select",
    )

with col_slider:
    savings_rate = st.slider(
        "Sparkvot (%)",
        min_value=5,
        max_value=25,
        value=10,
        step=1,
        key="ki_savings_slider",
    ) / 100.0

kommun_row = mun_year[mun_year["region_name"] == selected_kommun]
if len(kommun_row) == 0:
    st.warning("Inga data tillgängliga för den valda kommunen.")
    st.stop()

kommun_row = kommun_row.iloc[0]
price = kommun_row["transaction_price_sek"]
income = kommun_row["median_income"]
rate = kommun_row["policy_rate"] / 100.0

# ── Compute all regimes ──────────────────────────────────────────────
results = compare_regimes(price, income, rate, savings_rate)

# ── Context summary ──────────────────────────────────────────────────
st.markdown(
    f"<div style='font-size:13px;color:{COLORS['text_secondary']};margin-bottom:16px;'>"
    f"<strong>{selected_kommun}</strong> · "
    f"Medianpris: <strong>{format_sek(price)} SEK</strong> · "
    f"Medianinkomst: <strong>{format_sek(income)} SEK</strong> · "
    f"Ränta: <strong>{kommun_row['policy_rate']:.2f}%</strong> · "
    f"Sparkvot: <strong>{int(savings_rate*100)}%</strong>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Four regime cards (native Streamlit — avoids HTML escaping in nested divs) ──
regime_keys = ["pre_2010", "bolanetak", "amort_1", "amort_2"]
regime_cols = st.columns(4)

monthly_costs = {k: results[k]["monthly_total"] for k in regime_keys}
min_cost_key = min(monthly_costs, key=monthly_costs.get)
max_cost_key = max(monthly_costs, key=monthly_costs.get)

regime_accent_colors = {
    "pre_2010": "#9CA3AF",
    "bolanetak": "#C4A35A",
    "amort_1": "#D4A03C",
    "amort_2": "#B94A48",
}

for col, key in zip(regime_cols, regime_keys):
    with col:
        res = results[key]
        regime = REGIMES[key]
        with st.container(border=True):
            if key == min_cost_key:
                st.markdown(":green[**LÄGST KOSTNAD**]")
            elif key == max_cost_key:
                st.markdown(":red[**HÖGST KOSTNAD**]")
            st.markdown(f"**{regime['label']}**")
            st.caption(regime["period"])
            st.metric(
                "Kontantinsats",
                f"{format_sek(res['required_cash'])} SEK",
            )
            st.metric(
                "År att spara",
                f"{res['years_to_save']:.1f}".replace(".", ",") + " år",
            )
            st.metric(
                "Månadskostnad",
                f"{format_sek(res['monthly_total'])} SEK",
            )
            residual = res["residual_income"]
            st.metric(
                "Kvarvarande inkomst",
                f"{format_sek(residual)} SEK/år",
            )

# ── Comparison bar chart ─────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        card_header("Månadskostnad per regelverk", f"{selected_kommun} · {selected_year}", "JÄMFÖRELSE"),
        unsafe_allow_html=True,
    )

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
            bar_colors.append(regime_accent_colors.get(k, COLORS["secondary"]))

    fig.add_trace(go.Bar(
        x=labels,
        y=costs,
        marker_color=bar_colors,
        marker_line_color=[c.replace(")", ",0.8)").replace("rgb", "rgba") if "rgb" in c else c for c in bar_colors],
        marker_line_width=0,
        text=[f"{c:,.0f} SEK".replace(",", "\u00A0") for c in costs],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=12),
        hovertemplate="<b>%{x}</b><br>Månadskostnad: %{text}<extra></extra>",
    ))

    layout = get_chart_layout(height=380, yaxis_title="Månadskostnad (SEK)", showlegend=False)
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ── Detail table ─────────────────────────────────────────────────────
with st.expander("Detaljerad jämförelse"):
    detail_rows = []
    for key in regime_keys:
        res = results[key]
        regime = REGIMES[key]
        detail_rows.append(
            {
                "Regelverk": regime["label"],
                "Insats (SEK)": format_sek(res["required_cash"]),
                "Sparår": f"{res['years_to_save']:.1f}".replace(".", ","),
                "Lån (SEK)": format_sek(res["loan_amount"]),
                "LTV": f"{res['ltv']:.0%}",
                "LTI": f"{res['lti']:.1f}".replace(".", ",") + "x",
                "Amort.": f"{res['amort_pct']*100:.1f}".replace(".", ",") + "%",
                "Månkostnad (SEK)": format_sek(res["monthly_total"]),
            }
        )
    st.dataframe(
        pd.DataFrame(detail_rows),
        width="stretch",
        hide_index=True,
    )

footer_note(source="SCB, Riksbanken, Finansinspektionen")
