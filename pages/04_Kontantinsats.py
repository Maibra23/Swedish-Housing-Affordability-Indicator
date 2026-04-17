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

st.warning(
    "**Obs — Priserna avser småhus (villor):** SCB BO0501C2 (Fastighetstyp 220) täcker "
    "permanenta småhus och villor. Bostadsrätter och lägenheter ingår ej. "
    "I storstäder är typiska bostadsrätspriser 2–3× lägre än villapriser — "
    "kontantinsatskraven och spartiderna är därmed höga för stadsbor som söker lägenhet. "
    "Se Begränsning F11 i Metodologi (Sida 06)."
)

# ── 1 · Controls ──────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        card_header("Välj analysenhet", "Kommun, hushållstyp och sparandeantagande", "URVAL"),
        unsafe_allow_html=True,
    )

    col_sel, col_type, col_slider = st.columns([2, 1, 1])

    kommun_list = sorted(mun_year["region_name"].unique())
    with col_sel:
        selected_kommun = st.selectbox(
            "Välj kommun",
            kommun_list,
            index=kommun_list.index("Stockholm") if "Stockholm" in kommun_list else 0,
            key="ki_kommun_select",
        )

    with col_type:
        household_type = st.radio(
            "Hushållstyp",
            options=["Singelhushåll", "Par (2 inkomster)"],
            index=0,
            key="ki_household_type",
            help=(
                "Singelhushåll: en individuell inkomst. "
                "Par: sammanlagd inkomst (2×) — halverar spartiden och sänker LTI."
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
                "Andel av bruttoinkomsten som sparas årligen. "
                "10 % är vanligt; över 20 % är ambitiöst. "
                "Påverkar hur lång tid det tar att spara ihop insatsen."
            ),
        ) / 100.0
        _sparkvot_caption = st.empty()

    # Advanced settings (bank margin)
    with st.expander("Avancerade inställningar — Räntepåslag"):
        st.caption(
            "Riksbankens styrränta används som bas. Bankens räntepåslag adderas för att "
            "approximera faktisk bolåneränta. Typiskt ~1,7 pp för 3-månaders rörlig ränta."
        )
        bank_margin_pct = st.slider(
            "Bankens räntepåslag (pp ovan styrräntan)",
            min_value=0.0,
            max_value=3.0,
            value=1.7,
            step=0.1,
            key="ki_bank_margin_slider",
            help="Faktisk bolåneränta ≈ styrränta + räntepåslag. 0 pp = enbart styrränta (historisk default). 1,7 pp = typisk 2024 bankmarknad.",
        )
        bank_margin = bank_margin_pct / 100.0

kommun_row = mun_year[mun_year["region_name"] == selected_kommun]
if len(kommun_row) == 0:
    st.warning("Inga data tillgängliga för den valda kommunen.")
    st.stop()

kommun_row = kommun_row.iloc[0]
price = kommun_row["transaction_price_sek"]
_individual_income = kommun_row["median_income"]
income = _individual_income * household_multiplier   # household income
rate = kommun_row["policy_rate"] / 100.0
effective_rate_pct = kommun_row["policy_rate"] + bank_margin_pct

_sparkvot_caption.caption(
    f"= {format_sek(income * savings_rate)} SEK/år "
    f"({'par' if household_multiplier == 2 else 'singel'})"
)

# ── Compute all regimes ──────────────────────────────────────────────
results = compare_regimes(price, income, rate, savings_rate, bank_margin)
baseline = results["amort_2"]
regime_keys = ["pre_2010", "bolanetak", "amort_1", "amort_2"]

# ── 2 · Affordability Snapshot ────────────────────────────────────────
monthly_income = income / 12
pi_ratio       = price / income
insats_yrs     = baseline["required_cash"] / income
cost_pct       = baseline["monthly_total"] / monthly_income * 100
sparår         = baseline["years_to_save"]

if sparår < 5:
    aff_variant, aff_label = "success", "Tillgänglig"
elif sparår < 10:
    aff_variant, aff_label = "accent", "Ansträngd"
else:
    aff_variant, aff_label = "danger", "Otillgänglig"

render_kpi_row(
    [
        kpi_card(
            label="Pris/Inkomst-kvot",
            value=f"{pi_ratio:.1f}".replace(".", ","),
            unit="x",
            variant="default",
            tooltip="Under 5x normalt, 5–10x ansträngt, över 10x svårtillgängligt.",
        ),
        kpi_card(
            label="Kontantinsatsbörda",
            value=f"{insats_yrs:.1f}".replace(".", ","),
            unit="x årsinkomst",
            variant="default",
            tooltip="Hur många årsinkomster kontantinsatsen motsvarar.",
        ),
        kpi_card(
            label="Boendekostnadsbörda",
            value=format_pct(cost_pct),
            unit="",
            variant="accent" if cost_pct >= 30 else "default",
            tooltip="Andel av månadsinkomst. Under 30 % anses hållbart.",
        ),
        kpi_card(
            label="Tillgänglighet",
            value=aff_label,
            unit="",
            variant=aff_variant,
            tooltip=(
                "Tillgänglig = under 5 års spartid. "
                "Ansträngd = 5–10 år. "
                "Otillgänglig = över 10 år spartid vid vald sparkvot."
            ),
        ),
    ]
)
st.caption(
    f"Nuläge · Amorteringskrav 2.0 · {selected_kommun} {selected_year} · "
    f"Sparkvot {savings_rate*100:.0f}%"
)
st.caption(
    "Inkomsten är individuell bruttoinkomst (SCB HE0110). "
    "Vid gemensamt köp (par): dividera spartiden med 2. "
    "Se Begränsning F14 i Metodologi (Sida 06)."
)

# ── 3 · Nuläge – baseline KPI strip (enhanced tooltips) ───────────────
render_kpi_row(
    [
        kpi_card(
            label="Kontantinsats (idag)",
            value=format_sek(baseline["required_cash"]),
            unit="SEK",
            variant="accent",
            tooltip="Total kontantinsats (15 % av medianpriset under nuvarande bolånetak).",
        ),
        kpi_card(
            label="År att spara (idag)",
            value=f"{baseline['years_to_save']:.1f}".replace(".", ","),
            unit="år",
            variant="default",
            tooltip="Antal år för att spara kontantinsatsen vid vald sparkvot.",
        ),
        kpi_card(
            label="Månadskostnad (idag)",
            value=format_sek(baseline["monthly_total"]),
            unit="SEK",
            variant="default",
            tooltip="Ränte- + amorteringskostnad per månad efter att ha köpt.",
        ),
        kpi_card(
            label="Kvarvarande inkomst (idag)",
            value=format_sek(baseline["residual_income"]),
            unit="SEK/år",
            variant="default",
            tooltip="Inkomst kvar efter att boendekostnaderna är betalda (per år).",
        ),
    ]
)

# ── 4 · Regelverkstidslinje ───────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        card_header("Regelverksutveckling", "Fyra regimer sedan 2010", "TIDSLINJE"),
        unsafe_allow_html=True,
    )
    timeline_html = f"""
<div style="display:flex;width:100%;border-radius:6px;overflow:hidden;margin-top:8px;height:48px;">
  <div style="flex:4;background:{COLORS['text_tertiary']};display:flex;align-items:center;justify-content:center;padding:0 8px;">
    <span style="color:#fff;font-size:11px;font-weight:600;white-space:nowrap;">Före 2010</span>
  </div>
  <div style="flex:3;background:{COLORS['accent']};display:flex;align-items:center;justify-content:center;padding:0 8px;">
    <span style="color:#fff;font-size:11px;font-weight:600;white-space:nowrap;">Bolånetak 2010–2016</span>
  </div>
  <div style="flex:1;background:{COLORS['medium_risk']};display:flex;align-items:center;justify-content:center;padding:0 4px;">
    <span style="color:#fff;font-size:11px;font-weight:600;white-space:nowrap;">Amort 1.0 2016–18</span>
  </div>
  <div style="flex:3;background:{COLORS['primary']};border:2px solid {COLORS['accent']};display:flex;align-items:center;justify-content:center;padding:0 8px;">
    <span style="color:#fff;font-size:11px;font-weight:700;white-space:nowrap;">Amorteringskrav 2.0 · 2018 →</span>
  </div>
</div>
<div style="display:flex;width:100%;margin-top:4px;">
  <div style="flex:4;text-align:center;font-size:10px;color:{COLORS['text_tertiary']};"></div>
  <div style="flex:3;text-align:center;font-size:10px;color:{COLORS['text_secondary']};">Okt 2010</div>
  <div style="flex:1;text-align:center;font-size:10px;color:{COLORS['text_secondary']};">Jun 2016</div>
  <div style="flex:3;text-align:center;font-size:10px;color:{COLORS['text_secondary']};">Mar 2018</div>
</div>
"""
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
    "pre_2010": "Ingen formell insatsnivå; hög belåning var vanligare.",
    "bolanetak": "Bolånetak införs (max 85 % belåning) → högre insats.",
    "amort_1": "Amorteringskrav införs → högre månadskostnad vid hög belåning.",
    "amort_2": "Skärpt amorteringskrav (även skuldkvot) → högst krav idag.",
}

regime_accent_colors = {
    "pre_2010": COLORS["text_tertiary"],
    "bolanetak": COLORS["accent"],
    "amort_1": COLORS["medium_risk"],
    "amort_2": COLORS["high_risk"],
}

with st.container(border=True):
    st.markdown(
        card_header(
            "Kontantinsatskrav per regelverk",
            f"{selected_kommun} · {selected_year}",
            "FYRA REGIMER",
        ),
        unsafe_allow_html=True,
    )

    regime_cols = st.columns(4)
    for col, key in zip(regime_cols, regime_keys):
        with col:
            res = results[key]
            regime = REGIMES[key]
            tag = "LÄGST" if key == min_cost_key else "HÖGST" if key == max_cost_key else ""

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
                    delta=_fmt_delta_sek(delta_cash) if key != "amort_2" else None,
                    delta_color="inverse",
                    help="Kontantinsats är eget kapital (insats) som krävs vid köp. Lägre är bättre.",
                )
                st.metric(
                    "År att spara",
                    f"{res['years_to_save']:.1f}".replace(".", ",") + " år",
                    delta=(
                        (f"{delta_years:+.1f} år".replace(".", ","))
                        if (key != "amort_2" and abs(delta_years) >= 0.05)
                        else None
                    ),
                    delta_color="inverse",
                    help="Antal år för att spara kontantinsatsen vid vald sparkvot. Lägre är bättre.",
                )
                st.metric(
                    "Månadskostnad",
                    f"{format_sek(res['monthly_total'])} SEK",
                    delta=_fmt_delta_sek(delta_cost) if key != "amort_2" else None,
                    delta_color="inverse",
                    help="Summa amortering + räntekostnad per månad. Lägre är bättre.",
                )

                if key == "pre_2010":
                    st.caption("Obs: Inget formellt insatskrav, men banker krävde ofta 5–10 %.")

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
            text.append(f"{v:.1f}".replace(".", ",") + " år")
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
        "Välj flik för att jämföra regelverken från olika perspektiv. "
        "Ändra år i sidopanelen för att se historiska scenarion."
    )
    tab_cost, tab_save, tab_residual = st.tabs(
        ["Månadskostnad", "År att spara", "Kvarvarande inkomst"]
    )

    with tab_cost:
        st.markdown(
            card_header(
                "Månadskostnad per regelverk",
                f"{selected_kommun} · {selected_year}",
                "JÄMFÖRELSE",
            ),
            unsafe_allow_html=True,
        )
        costs = [results[k]["monthly_total"] for k in regime_keys]
        st.plotly_chart(
            _comparison_barchart(
                y_values=costs,
                yaxis_title="Månadskostnad (SEK)",
                value_fmt="sek",
                ref_lines=[
                    {
                        "y": monthly_income * 0.30,
                        "color": COLORS["text_secondary"],
                        "dash": "dot",
                        "width": 1.5,
                        "label": f"30 % av månadsink. · {format_sek(monthly_income * 0.30)} SEK",
                    }
                ],
            ),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption("Lägre månadskostnad innebär mindre löpande belastning givet samma pris- och inkomstnivå.")

    with tab_save:
        st.markdown(
            card_header(
                "År att spara kontantinsats",
                f"{selected_kommun} · {selected_year}",
                "JÄMFÖRELSE",
            ),
            unsafe_allow_html=True,
        )
        years = [results[k]["years_to_save"] for k in regime_keys]
        st.plotly_chart(
            _comparison_barchart(
                y_values=years,
                yaxis_title="År att spara",
                value_fmt="years",
                ref_lines=[
                    {
                        "y": 5,
                        "color": COLORS["low_risk"],
                        "dash": "dot",
                        "width": 1.5,
                        "label": "5 år – Tillgänglig",
                        "annotation_position": "bottom right",
                        "annotation_font_color": COLORS["low_risk"],
                    },
                    {
                        "y": 10,
                        "color": COLORS["high_risk"],
                        "dash": "dot",
                        "width": 1.5,
                        "label": "10 år – Otillgänglig",
                        "annotation_position": "top left",
                        "annotation_font_color": COLORS["high_risk"],
                    },
                ],
            ),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption("Sparkvoten påverkar främst sparår; regelverken påverkar kravet på insats och amortering.")

    with tab_residual:
        st.markdown(
            card_header(
                "Kvarvarande inkomst per regelverk",
                f"{selected_kommun} · {selected_year}",
                "JÄMFÖRELSE",
            ),
            unsafe_allow_html=True,
        )
        residuals = [results[k]["residual_income"] for k in regime_keys]
        st.plotly_chart(
            _comparison_barchart(
                y_values=residuals,
                yaxis_title="Kvarvarande inkomst (SEK/år)",
                value_fmt="sek",
                ref_lines=[
                    {
                        "y": 0,
                        "color": COLORS["high_risk"],
                        "dash": "dash",
                        "width": 1.5,
                        "label": "Nollgräns",
                    }
                ],
            ),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption("Högre kvarvarande inkomst innebär mer utrymme efter boendekostnader givet antagandena.")

# ── 7 · Nyckelinsikt ─────────────────────────────────────────────────
best_key  = min(regime_keys, key=lambda k: results[k]["monthly_total"])
worst_key = max(regime_keys, key=lambda k: results[k]["monthly_total"])
cost_diff = results[worst_key]["monthly_total"] - results[best_key]["monthly_total"]
pct_diff  = cost_diff / results[best_key]["monthly_total"] * 100

_hushall_label = "par" if household_multiplier == 2 else "singelhushåll"
_rate_note = (
    f"styrränta {kommun_row['policy_rate']:.2f}% + påslag {bank_margin_pct:.1f} pp = {effective_rate_pct:.2f}%"
    if bank_margin_pct > 0
    else f"styrränta {kommun_row['policy_rate']:.2f}%"
)
insight_html = f"""
<div class="shai-card" style="border-left:3px solid {COLORS['accent']};">
  <div class="shai-card-header">
    <div class="shai-card-title">Nyckelinsikt</div>
    <span class="shai-card-tag">SYNTES</span>
  </div>
  <p style="font-size:14px;color:{COLORS['text_primary']};line-height:1.7;margin:0;">
    För ett <strong>{_hushall_label}</strong> ({_rate_note}) under
    <strong>nuvarande regler (Amorteringskrav 2.0)</strong> krävs
    <strong>{format_sek(baseline['required_cash'])} SEK</strong> i kontantinsats,
    vilket tar <strong>{baseline['years_to_save']:.1f} år</strong> att spara
    vid {int(savings_rate*100)} % sparkvot.
    Månadskostnaden är <strong>{format_sek(baseline['monthly_total'])} SEK</strong>
    (<strong>{cost_pct:.0f} % av månadsinkomst</strong>).<br><br>
    Det historiskt förmånligaste regelverket
    (<strong>{REGIMES[best_key]['label']}</strong>) innebar
    <strong>{format_sek(cost_diff)} SEK lägre</strong> månadskostnad
    ({pct_diff:.0f} % billigare).
  </p>
</div>
"""
st.markdown(_compact(insight_html), unsafe_allow_html=True)

# ── 8 · Detaljer & antaganden ─────────────────────────────────────────
with st.expander("Detaljer & antaganden"):
    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:13px;line-height:1.55;'>"
        "<strong>Indata</strong><br>"
        f"- Kommun: <strong>{selected_kommun}</strong> (analysår {selected_year})<br>"
        f"- Medianpris (småhus): <strong>{format_sek(price)} SEK</strong><br>"
        f"- Hushållstyp: <strong>{household_type}</strong><br>"
        f"- Individuell medianinkomst: <strong>{format_sek(_individual_income)} SEK</strong><br>"
        f"- Hushållsinkomst (används): <strong>{format_sek(income)} SEK</strong>"
        f"{' (2 × individuell)' if household_multiplier == 2 else ''}<br>"
        f"- Styrränta: <strong>{kommun_row['policy_rate']:.2f}%</strong><br>"
        f"- Bankens räntepåslag: <strong>{bank_margin_pct:.1f} pp</strong><br>"
        f"- Effektiv bolåneränta (används): <strong>{effective_rate_pct:.2f}%</strong><br>"
        f"- Sparkvot: <strong>{int(savings_rate*100)}%</strong><br><br>"
        "<strong>Konstant mellan regelverk</strong><br>"
        "- Samma pris, inkomst och räntenivå används i alla regimer<br>"
        "- Skillnaderna drivs av insatskrav, maxbelåning och amorteringsregler<br><br>"
        "<strong>Metod</strong><br>"
        "Se Metodologi (Sida 06), avsnitt 6 för antaganden och definitioner."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:13px;line-height:1.55;margin-top:8px;'>"
        "<strong>Så läser du tabellen</strong><br>"
        "- Δ-kolumner visar skillnad mot <strong>idag (Amorteringskrav 2.0)</strong><br>"
        "- Markeringar: <strong>bäst</strong> = lägst för Insats/Sparår/Månkostnad, högst för Kvar"
        "</div>",
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
                "Sparår": float(res["years_to_save"]),
                "Δ Sparår": float(res["years_to_save"] - baseline["years_to_save"]),
                "Månkostnad": float(res["monthly_total"]),
                "Δ Månkostnad": float(res["monthly_total"] - baseline["monthly_total"]),
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
        for col in ["Insats", "Sparår", "Månkostnad"]:
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
            "Sparår",
            "Δ Sparår",
            "Månkostnad",
            "Δ Månkostnad",
            "Kvar",
            "Δ Kvar",
            "LTV",
            "LTI",
            "Amort.",
        ],
        column_config={
            "Regelverk": st.column_config.TextColumn("Regelverk", help="Regim/regelverk som jämförs."),
            "Period": st.column_config.TextColumn("Period", help="Tidsperiod då regelverket gällde."),
            "Insats": st.column_config.NumberColumn("Insats (SEK)", format="%.0f", help="Kontantinsats i SEK. Lägre är bättre."),
            "Δ Insats": st.column_config.NumberColumn("Δ Insats vs idag", format="%+.0f", help="Skillnad i insats jämfört med nuvarande regler."),
            "Sparår": st.column_config.NumberColumn("Sparår", format="%.1f", help="År att spara kontantinsatsen vid vald sparkvot. Lägre är bättre."),
            "Δ Sparår": st.column_config.NumberColumn("Δ Sparår vs idag", format="%+.1f", help="Skillnad i sparår jämfört med nuvarande regler."),
            "Månkostnad": st.column_config.NumberColumn("Månkostnad (SEK)", format="%.0f", help="Månadskostnad (ränta + amortering). Lägre är bättre."),
            "Δ Månkostnad": st.column_config.NumberColumn("Δ Månkostnad vs idag", format="%+.0f", help="Skillnad i månadskostnad jämfört med idag."),
            "Kvar": st.column_config.NumberColumn("Kvar (SEK/år)", format="%.0f", help="Kvarvarande inkomst per år efter boendekostnad. Högre är bättre."),
            "Δ Kvar": st.column_config.NumberColumn("Δ Kvar vs idag", format="%+.0f", help="Skillnad i kvarvarande inkomst jämfört med idag."),
            "LTV": st.column_config.NumberColumn("LTV", format="%.0f%%", help="Belåningsgrad: lån / bostadspris."),
            "LTI": st.column_config.NumberColumn("LTI", format="%.1f", help="Skuldkvot: lån / årsinkomst."),
            "Amort.": st.column_config.NumberColumn("Amort.", format="%.1f%%", help="Årlig amortering i % av lånet."),
        },
    )

# ── 9 · Footer ────────────────────────────────────────────────────────
footer_note(source="SCB, Riksbanken, Finansinspektionen")
