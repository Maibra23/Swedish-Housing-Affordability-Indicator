"""Sida 04 — Kontantinsats analys.

Jämförelse av kontantinsatskrav under fem regelverk (pre-2010, bolånetak, amort 1, amort 2, lättnad 2026).

When "Bostadsrätt" is selected the analysis switches to county level (21 län)
because SCB only publishes apartment prices at the county level.
"""

import streamlit as st

st.set_page_config(
    page_title="SHAI · Kontantinsats",
    page_icon=None,
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
        county_data = pd.read_parquet("data/processed/panel_county.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

selected_year = selections["selected_year"]
mun_year = municipal[municipal["year"] == selected_year]
county_yr = county_data[county_data["year"] == selected_year]

if len(mun_year) == 0:
    _available = sorted(municipal["year"].unique(), reverse=True)
    st.warning(
        f"Inga data tillgängliga för {selected_year}. "
        f"Välj ett år med data: {', '.join(str(y) for y in _available[:5])}."
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
        "**Obs — Priserna avser småhus (villor):** SCB BO0501C2 (Fastighetstyp 220) täcker "
        "permanenta småhus och villor. Bostadsrätter och lägenheter ingår ej ännu i panelen. "
        "I storstäder är typiska bostadsrätspriser lägre än villapriser — "
        "kontantinsatskraven och spartiderna är därmed höga för stadsbor som söker lägenhet. "
        "Se Begränsning F11 i Metodologi (Sida 06)."
    )
else:
    st.info(
        "**Välj Pristyp:** Bostadsrättspriser (SCB BO0501C) analyseras på **länsnivå** "
        "(21 län) — SCB publicerar inga kommunspecifika bostadsrättspriser. "
        "Småhuspriser (SCB BO0501C2) analyseras på **kommunnivå** (290 kommuner). "
        "När du väljer Bostadsrätt byter analysen automatiskt till länsnivå."
    )

# ── 1 · Controls ──────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        card_header("Välj analysenhet", "Region, pristyp, hushållstyp och sparandeantagande", "URVAL"),
        unsafe_allow_html=True,
    )

    col_pristyp, col_sel, col_type, col_slider = st.columns([1.1, 2, 1, 1])

    # Pristyp FIRST — determines whether selector shows kommun or län
    with col_pristyp:
        _pristyp_options = ["Småhus (villa)"]
        if _br_available:
            _pristyp_options.append("Bostadsrätt")
        pristyp = st.radio(
            "Pristyp",
            options=_pristyp_options,
            index=0,
            key="ki_pristyp",
            help=(
                "Småhus = SCB BO0501C2 (Fastighetstyp 220), kommunnivå (290 kommuner). "
                "Bostadsrätt = SCB BO0501C, medelpris per bostadsrätt — **länsnivå** (21 län). "
                "SCB publicerar inga kommunspecifika bostadsrättspriser."
            ),
            horizontal=False,
        )
        use_bostadsratt = (pristyp == "Bostadsrätt")

    # Conditional selector: län for bostadsrätt, kommun for småhus
    with col_sel:
        if use_bostadsratt:
            region_list = sorted(county_yr["region_name"].dropna().unique())
            _default_lan = (
                region_list.index("Stockholms län")
                if "Stockholms län" in region_list else 0
            )
            selected_name = st.selectbox(
                "Välj län",
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
                "Välj kommun",
                region_list,
                index=_default_kommun,
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

# ── Get data row ─────────────────────────────────────────────────────
if use_bostadsratt:
    selected_row_df = county_yr[county_yr["region_name"] == selected_name]
else:
    selected_row_df = mun_year[mun_year["region_name"] == selected_name]

if len(selected_row_df) == 0:
    st.warning("Inga data tillgängliga för den valda regionen.")
    st.stop()

selected_row = selected_row_df.iloc[0]

# ── Extract values ───────────────────────────────────────────────────
# County name lookup — only needed in kommun mode for BR price provenance
_LAN_NAMES = {
    "01": "Stockholms län", "03": "Uppsala län", "04": "Södermanlands län",
    "05": "Östergötlands län", "06": "Jönköpings län", "07": "Kronobergs län",
    "08": "Kalmar län", "09": "Gotlands län", "10": "Blekinge län",
    "12": "Skåne län", "13": "Hallands län", "14": "Västra Götalands län",
    "17": "Värmlands län", "18": "Örebro län", "19": "Västmanlands län",
    "20": "Dalarnas län", "21": "Gävleborgs län", "22": "Västernorrlands län",
    "23": "Jämtlands län", "24": "Västerbottens län", "25": "Norrbottens län",
}

pristyp_fallback_note: str | None = None
if use_bostadsratt:
    # County mode — both prices come from the county panel
    _br_price = selected_row.get("bostadsratt_price_sek")
    _villa_price = selected_row.get("transaction_price_sek")
    if pd.notna(_br_price):
        price = _br_price
        price_source_label = f"Bostadsrätt — {selected_name} (SCB BO0501C)"
    else:
        price = _villa_price
        pristyp_fallback_note = (
            f"Bostadsrättspris saknas för {selected_name} — "
            "småhuspriset används som fallback."
        )
        price_source_label = "Småhus (fallback)"
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
    price_source_label = "Småhus (SCB BO0501C2)"
    _lan_code = str(selected_row.get("lan_code", "")).zfill(2)
    _lan_name = _LAN_NAMES.get(_lan_code, f"Län {_lan_code}")

_individual_income = selected_row["median_income"]
income = _individual_income * household_multiplier   # household income
rate = selected_row["policy_rate"] / 100.0
effective_rate_display_pct = selected_row["policy_rate"] + bank_margin_pct

_sparkvot_caption.caption(
    f"= {format_sek(income * savings_rate)} SEK/år "
    f"({'par' if household_multiplier == 2 else 'singel'})"
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
_level_label = "länsnivå" if use_bostadsratt else "kommunnivå"
st.caption(
    f"Nuläge · Lättnad 2026 · {selected_name} ({_level_label}) · {selected_year} · "
    f"Sparkvot {savings_rate*100:.0f}% · Pristyp: {price_source_label}"
)
st.caption(
    "Inkomsten är individuell bruttoinkomst (SCB HE0110). "
    "Vid gemensamt köp (par): dividera spartiden med 2. "
    "Se Begränsning F14 i Metodologi (Sida 06)."
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
                "Villa vs. bostadsrätt",
                f"{selected_name} · {selected_year} · Lättnad 2026",
                "PRISTYPSJÄMFÖRELSE",
            ),
            unsafe_allow_html=True,
        )
        c_villa, c_br = st.columns(2)
        with c_villa:
            _villa_level = "länsnivå" if use_bostadsratt else "kommunnivå"
            st.markdown(f"**Småhus (villa)** — SCB BO0501C2 ({_villa_level})")
            st.metric("Pris", f"{format_sek(_villa_price)} SEK")
            st.metric("Kontantinsats (10 %)",
                      f"{format_sek(_villa_res['required_cash'])} SEK")
            st.metric("År att spara",
                      f"{_villa_res['years_to_save']:.1f}".replace(".", ",") + " år")
            st.metric("Månadskostnad",
                      f"{format_sek(_villa_res['monthly_total'])} SEK")
        with c_br:
            st.markdown(f"**Bostadsrätt** — SCB BO0501C (länsnivå)")
            st.metric("Pris", f"{format_sek(_br_price)} SEK")
            st.metric("Kontantinsats (10 %)",
                      f"{format_sek(_br_res['required_cash'])} SEK")
            st.metric("År att spara",
                      f"{_br_res['years_to_save']:.1f}".replace(".", ",") + " år")
            st.metric("Månadskostnad",
                      f"{format_sek(_br_res['monthly_total'])} SEK")
        if use_bostadsratt:
            st.caption(
                f"Priskvot villa/bostadsrätt: **{_ratio:.1f}×**. "
                f"Båda priser avser **{selected_name}** (länsnivå). "
                "Samma hushållsinkomst, ränta och regelverk (Lättnad 2026)."
            )
        else:
            st.caption(
                f"Priskvot villa/bostadsrätt: **{_ratio:.1f}×**. "
                f"Villapris avser **{selected_name}** (kommunnivå). "
                f"Bostadsrättspris avser **{_lan_name}** (länsnivå, SCB BO0501C) — "
                "SCB publicerar inga kommunspecifika bostadsrättspriser."
            )

# ── 3 · Nuläge – baseline KPI strip (enhanced tooltips) ───────────────
render_kpi_row(
    [
        kpi_card(
            label="Kontantinsats (idag)",
            value=format_sek(baseline["required_cash"]),
            unit="SEK",
            variant="accent",
            tooltip="Total kontantinsats (10 % av medianpriset under nuvarande bolånetak, gäller fr.o.m. apr 2026).",
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
        card_header("Regelverksutveckling", "Fem milstolpar 2010–2026", "TIDSLINJE"),
        unsafe_allow_html=True,
    )
    timeline_html = f"""
<div style="display:flex;width:100%;border-radius:6px;overflow:hidden;margin-top:8px;height:48px;">
  <div style="flex:3;background:{COLORS['text_tertiary']};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Före 2010</span>
  </div>
  <div style="flex:3;background:{COLORS['accent']};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Bolånetak</span>
  </div>
  <div style="flex:1;background:{COLORS['medium_risk']};display:flex;align-items:center;justify-content:center;padding:0 2px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Amorteringskrav</span>
  </div>
  <div style="flex:3;background:{COLORS['high_risk']};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Skärpt amorteringskrav</span>
  </div>
  <div style="flex:2;background:{COLORS['low_risk']};border:2px solid {COLORS['accent']};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:700;white-space:nowrap;">Lättnader i bolånereglerna</span>
  </div>
</div>
<div style="display:flex;width:100%;margin-top:4px;">
  <div style="flex:3;text-align:center;font-size:10px;color:{COLORS['text_tertiary']};"></div>
  <div style="flex:3;text-align:center;font-size:10px;color:{COLORS['text_secondary']};">2010</div>
  <div style="flex:1;text-align:center;font-size:10px;color:{COLORS['text_secondary']};">2016</div>
  <div style="flex:3;text-align:center;font-size:10px;color:{COLORS['text_secondary']};">2018</div>
  <div style="flex:2;text-align:center;font-size:10px;color:{COLORS['text_secondary']};">2026</div>
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
    "amort_2": "Skärpt amorteringskrav (skuldkvot LTI > 4,5×). Gällde mar 2018 – mar 2026.",
    "latt_2026": "Bolånetak höjt till 90 % (insats 10 %) + skärpt amorteringskrav slopat. Gäller fr.o.m. apr 2026.",
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
                    delta=_fmt_delta_sek(delta_cash) if key != "latt_2026" else None,
                    delta_color="inverse",
                    help="Kontantinsats är eget kapital (insats) som krävs vid köp. Lägre är bättre.",
                )
                st.metric(
                    "År att spara",
                    f"{res['years_to_save']:.1f}".replace(".", ",") + " år",
                    delta=(
                        (f"{delta_years:+.1f} år".replace(".", ","))
                        if (key != "latt_2026" and abs(delta_years) >= 0.05)
                        else None
                    ),
                    delta_color="inverse",
                    help="Antal år för att spara kontantinsatsen vid vald sparkvot. Lägre är bättre.",
                )
                st.metric(
                    "Månadskostnad",
                    f"{format_sek(res['monthly_total'])} SEK",
                    delta=_fmt_delta_sek(delta_cost) if key != "latt_2026" else None,
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
                f"{selected_name} · {selected_year}",
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
            config={"displayModeBar": "hover"},
        )
        st.caption("Lägre månadskostnad innebär mindre löpande belastning givet samma pris- och inkomstnivå.")

    with tab_save:
        st.markdown(
            card_header(
                "År att spara kontantinsats",
                f"{selected_name} · {selected_year}",
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
            config={"displayModeBar": "hover"},
        )
        st.caption("Sparkvoten påverkar främst sparår; regelverken påverkar kravet på insats och amortering.")

    with tab_residual:
        st.markdown(
            card_header(
                "Kvarvarande inkomst per regelverk",
                f"{selected_name} · {selected_year}",
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
            config={"displayModeBar": "hover"},
        )
        st.caption("Högre kvarvarande inkomst innebär mer utrymme efter boendekostnader givet antagandena.")

# ── 7 · Nyckelinsikt ─────────────────────────────────────────────────
best_key  = min(regime_keys, key=lambda k: results[k]["monthly_total"])
worst_key = max(regime_keys, key=lambda k: results[k]["monthly_total"])
cost_diff = results[worst_key]["monthly_total"] - results[best_key]["monthly_total"]
pct_diff  = cost_diff / results[best_key]["monthly_total"] * 100

_hushall_label = "par" if household_multiplier == 2 else "singelhushåll"
_rate_note = (
    f"styrränta {selected_row['policy_rate']:.2f}% + påslag {bank_margin_pct:.1f} pp = {effective_rate_display_pct:.2f}%"
    if bank_margin_pct > 0
    else f"styrränta {selected_row['policy_rate']:.2f}%"
)
insight_html = f"""
<div class="shai-card" style="border-left:3px solid {COLORS['accent']};">
  <div class="shai-card-header">
    <div class="shai-card-title">Nyckelinsikt</div>
    <span class="shai-card-tag">SYNTES</span>
  </div>
  <p style="font-size:14px;color:{COLORS['text_primary']};line-height:1.7;margin:0;">
    För ett <strong>{_hushall_label}</strong> ({_rate_note}) under
    <strong>nuvarande regler (Lättnad 2026)</strong> krävs
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
    _region_label = "Län" if use_bostadsratt else "Kommun"
    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:13px;line-height:1.55;'>"
        "<strong>Indata</strong><br>"
        f"- {_region_label}: <strong>{selected_name}</strong> (analysår {selected_year})<br>"
        f"- Pristyp: <strong>{price_source_label}</strong><br>"
        f"- Pris (används): <strong>{format_sek(price)} SEK</strong><br>"
        + (
            f"- Småhuspris (referens): <strong>{format_sek(_villa_price)} SEK</strong><br>"
            if _villa_price is not None and pd.notna(_villa_price) and use_bostadsratt
            else ""
        )
        + (
            f"- Bostadsrättspris (referens, {_lan_name}): <strong>{format_sek(_br_price)} SEK</strong><br>"
            if _br_price is not None and pd.notna(_br_price) and not use_bostadsratt
            else ""
        ) +
        f"- Hushållstyp: <strong>{household_type}</strong><br>"
        f"- Individuell medianinkomst: <strong>{format_sek(_individual_income)} SEK</strong><br>"
        f"- Hushållsinkomst (används): <strong>{format_sek(income)} SEK</strong>"
        f"{' (2 × individuell)' if household_multiplier == 2 else ''}<br>"
        f"- Styrränta: <strong>{selected_row['policy_rate']:.2f}%</strong><br>"
        f"- Bankens räntepåslag: <strong>{bank_margin_pct:.1f} pp</strong><br>"
        f"- Effektiv bolåneränta (används): <strong>{effective_rate_display_pct:.2f}%</strong><br>"
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
        "- Δ-kolumner visar skillnad mot <strong>idag (Lättnad 2026)</strong><br>"
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
