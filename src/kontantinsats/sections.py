"""Display sections of the Kontantinsats page.

T3.11 required the page under 400 lines; after the regime data, chart builder and
county lookup moved out it was still 690, because most of it was five long display
sections. They live here and the page is now load, controls, compute, then wiring.

Each section takes a :class:`Context` rather than twenty keyword arguments, and
unpacks what it needs into locals at the top. That unpacking is deliberate: the
section bodies moved **verbatim**, so the refactor could be checked by rendering
all 67 page/year states and diffing, rather than by reading 400 lines of moved
code and hoping.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.kontantinsats.charts import affordability_gap_chart, comparison_barchart, fmt_delta_sek
from src.kontantinsats.engine import BASELINE_REGIME, REGIMES, compare_regimes
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
    format_sek_compact,
    kpi_card,
    page_title,
    render_kpi_row,
)
from src.ui.interpret import (
    LTI_LENDING_CEILING,
    interpret_kontantinsats,
    render_findings,
)
from src.ui.labels import L
from src.ui.tokens import COLORS


def _sv_ceiling() -> str:
    """The lending ceiling as Swedish copy, so the caption cannot drift from it."""
    return f"{LTI_LENDING_CEILING:.1f}".replace(".", ",")


@dataclass(frozen=True)
class Context:
    """Page state the display sections read.

    Deliberately not typed more tightly: these are pandas scalars, numpy floats
    and plain Python numbers depending on the column, and narrowing the
    annotations would be a claim this module cannot keep.
    """

    _br_price: object
    _individual_income: object
    _lan_name: object
    _villa_price: object
    bank_margin: object
    bank_margin_pct: object
    baseline: object
    cost_pct: object
    effective_rate_display_pct: object
    household_multiplier: object
    household_type: object
    income: object
    monthly_income: object
    max_cost_key: object
    min_cost_key: object
    price: object
    price_source_label: object
    pristyp_fallback_note: object
    rate: object
    regime_keys: object
    results: object
    savings_rate: object
    selected_name: object
    selected_row: object
    selected_year: object
    use_bostadsratt: object


def render_snapshot(ctx: Context) -> None:
    """The affordability snapshot: price, income and the baseline verdict."""
    cost_pct = ctx.cost_pct
    baseline = ctx.baseline
    income = ctx.income
    price = ctx.price
    price_source_label = ctx.price_source_label
    pristyp_fallback_note = ctx.pristyp_fallback_note
    savings_rate = ctx.savings_rate
    selected_name = ctx.selected_name
    selected_year = ctx.selected_year
    use_bostadsratt = ctx.use_bostadsratt

    # ── 2 · Affordability Snapshot ────────────────────────────────────────
    pi_ratio       = price / income
    insats_yrs     = baseline["required_cash"] / income
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
    # Whether the purchase is reachable at all, before the page spends four
    # cards on how long its deposit takes to save.
    with st.container(border=True):
        st.markdown(
            card_header(L("ki.gap_rubrik"), L("ki.gap_underrubrik"), L("ki.gap_tagg")),
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            affordability_gap_chart(
                price=price,
                income=income,
                lending_ceiling=LTI_LENDING_CEILING,
                min_down_pct=REGIMES[BASELINE_REGIME]["min_down_pct"],
            ),
            width="stretch",
            config={"displayModeBar": "hover"},
        )
        st.caption(L("ki.gap_forklaring_v0", v0=_sv_ceiling()))

    # What those four numbers mean together. The debt ratio in particular
    # governs whether the savings horizon beside it is a plan or a hypothetical,
    # and nothing above states that.
    render_findings(
        interpret_kontantinsats(
            baseline=baseline,
            strictest=ctx.results["amort_2"],
            income=income,
            cost_pct=cost_pct,
            savings_rate=savings_rate,
            household_multiplier=int(ctx.household_multiplier),
        ),
        title=L("ki.tolk_rubrik"),
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



def render_villa_vs_bostadsratt(ctx: Context) -> None:
    """Side-by-side villa and apartment comparison, county level."""
    _br_price = ctx._br_price
    _lan_name = ctx._lan_name
    _villa_price = ctx._villa_price
    bank_margin = ctx.bank_margin
    income = ctx.income
    rate = ctx.rate
    savings_rate = ctx.savings_rate
    selected_name = ctx.selected_name
    selected_year = ctx.selected_year
    use_bostadsratt = ctx.use_bostadsratt

    # ── 2b · Villa vs. bostadsrätt side-by-side jämförelse ────────────────
    _show_comparison = (
        _villa_price is not None and pd.notna(_villa_price)
        and _br_price is not None and pd.notna(_br_price)
    )
    if _show_comparison:
        from src.kontantinsats.engine import apply_regime as _apply_regime
        _villa_res = _apply_regime(_villa_price, income, rate, BASELINE_REGIME,
                                   savings_rate, bank_margin)
        _br_res = _apply_regime(_br_price, income, rate, BASELINE_REGIME,
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



def render_baseline_kpis(ctx: Context) -> None:
    """Baseline KPI strip for the current regime."""
    baseline = ctx.baseline

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



def render_regime_cards(ctx: Context) -> None:
    """One card per regulatory regime, with the delta against baseline."""
    baseline = ctx.baseline
    max_cost_key = ctx.max_cost_key
    min_cost_key = ctx.min_cost_key
    regime_keys = ctx.regime_keys
    results = ctx.results
    selected_name = ctx.selected_name
    selected_year = ctx.selected_year

    # ── 5 · Regime cards ─────────────────────────────────────────────────

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
                        format_sek_compact(res["required_cash"]),
                        delta=fmt_delta_sek(delta_cash) if key != BASELINE_REGIME else None,
                        delta_color="inverse",
                        help=L("ki.kontantinsats_ar_eget_kapital_insats_som"),
                    )
                    st.metric(
                        L("ki.ar_att_spara"),
                        f"{res['years_to_save']:.1f}".replace(".", ",") + L("ki.ar"),
                        delta=(
                            (L("ki.v0_1f_ar", v0=delta_years).replace(".", ","))
                            if (key != BASELINE_REGIME and abs(delta_years) >= 0.05)
                            else None
                        ),
                        delta_color="inverse",
                        help=L("ki.antal_ar_for_att_spara_kontantinsatsen_vid_2"),
                    )
                    st.metric(
                        L("ki.manadskostnad"),
                        f"{format_sek(res['monthly_total'])} SEK",
                        delta=fmt_delta_sek(delta_cost) if key != BASELINE_REGIME else None,
                        delta_color="inverse",
                        help=L("ki.summa_amortering_rantekostnad_per_manad"),
                    )

                    if key == "pre_2010":
                        st.caption(L("ki.obs_inget_formellt_insatskrav_men_banker"))
