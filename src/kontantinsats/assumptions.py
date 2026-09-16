"""The "Detaljer & antaganden" expander.

Split from `sections.py` in T3.11 for the same reason the page was split: at 109
lines this one section, with its inputs table and caveat list, was most of that
module. It reads the same :class:`Context`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.kontantinsats.charts import comparison_barchart, fmt_delta_sek
from src.kontantinsats.engine import REGIMES, compare_regimes
from src.kontantinsats.regions import (
    _LAN_NAMES,
    REGIME_ACCENT_COLORS,
    REGIME_KEYS,
    REGIME_WHAT_CHANGED,
)
from src.ui.chart_theme import get_chart_layout
from src.ui.components import (
    _compact,
    card_header,
    format_pct,
    format_sek,
    kpi_card,
    page_title,
    render_kpi_row,
)
from src.ui.labels import L
from src.ui.tokens import COLORS


from src.kontantinsats.sections import Context


def render_assumptions(ctx: Context) -> None:
    """The 'Detaljer & antaganden' expander: inputs, table and caveats."""
    _br_price = ctx._br_price
    _individual_income = ctx._individual_income
    _lan_name = ctx._lan_name
    _villa_price = ctx._villa_price
    bank_margin_pct = ctx.bank_margin_pct
    baseline = ctx.baseline
    effective_rate_display_pct = ctx.effective_rate_display_pct
    household_multiplier = ctx.household_multiplier
    household_type = ctx.household_type
    income = ctx.income
    price = ctx.price
    price_source_label = ctx.price_source_label
    regime_keys = ctx.regime_keys
    results = ctx.results
    savings_rate = ctx.savings_rate
    selected_name = ctx.selected_name
    selected_row = ctx.selected_row
    selected_year = ctx.selected_year
    use_bostadsratt = ctx.use_bostadsratt

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
            width="stretch",
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


