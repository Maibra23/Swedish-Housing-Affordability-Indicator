"""Turn a page's computed numbers into a plain statement of what they mean.

Every figure on Kontantinsats and Scenariosimulator is correct and almost none of
it is self-explanatory. A reader is shown "16,1 år" and a debt-to-income ratio of
14,5 and is left to work out that the second number makes the first irrelevant,
because no lender would write that loan. This module does that reasoning out
loud.

The rules here are thresholds, not opinions, and each one names its own source of
authority: the 4,5x amortisation trigger is Finansinspektionen's, the 30 percent
housing-cost guideline is conventional budgeting practice, the 5,5x lending
ceiling is typical Swedish bank behaviour rather than regulation and is labelled
as such. Anything that is a rule of thumb says so.

Findings are returned rather than rendered so they can be asserted in a test
without a Streamlit runtime, and so a caller can choose where to place them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import streamlit as st

from src.ui.labels import L

# Typical Swedish bank practice, not a legal limit. Lending above roughly this
# multiple of household income is rare regardless of which regime applies, so a
# scenario above it is arithmetic rather than a purchase anyone could make.
LTI_LENDING_CEILING = 5.5

# Finansinspektionen's skärpt amorteringskrav trigger, in force Mar 2018 to Mar
# 2026. Retained as a reference line because it is the only published, official
# statement of what counts as a high debt ratio in Sweden.
LTI_FI_THRESHOLD = 4.5

# Conventional budgeting guideline rather than a regulatory one.
HOUSING_COST_SHARE_GUIDELINE = 30.0

#: Years-to-save bands, matching the Tillgänglighet KPI on sida 04.
SAVE_YEARS_COMFORTABLE = 5.0
SAVE_YEARS_STRAINED = 10.0


@dataclass(frozen=True)
class Finding:
    """One statement about the result, with how much attention it deserves.

    Attributes:
        level: "critical", "warning", "note" or "good". Drives presentation only.
        text: The finished Swedish sentence, already formatted.
    """

    level: str
    text: str


def _sv(value: float, decimals: int = 1) -> str:
    """Format a number Swedish style, with a comma for the decimal mark."""
    return f"{value:.{decimals}f}".replace(".", ",")


# ── Kontantinsats ─────────────────────────────────────────────────────


def interpret_kontantinsats(
    *,
    baseline: dict,
    strictest: dict,
    income: float,
    cost_pct: float,
    savings_rate: float,
    household_multiplier: int,
) -> list[Finding]:
    """Explain one household's kontantinsats result.

    Args:
        baseline: `apply_regime` output for the current regime (Lättnad 2026).
        strictest: `apply_regime` output for Amorteringskrav 2.0, the regime that
            applied until Mar 2026, used to say which direction the easing moved
            cost for this particular region.
        income: Household income actually used, after any couple multiplier.
        cost_pct: Housing cost as a percentage of monthly income.
        savings_rate: Fraction of income saved per year.
        household_multiplier: 1 for a single income, 2 for a couple.

    Returns:
        Findings ordered most serious first.
    """
    findings: list[Finding] = []
    lti = baseline["lti"]
    years = baseline["years_to_save"]

    # 1. Lendability. This governs everything below it: if no bank would write
    #    the loan, the savings horizon is a hypothetical, not a plan.
    if lti > LTI_LENDING_CEILING:
        findings.append(Finding("critical", L(
            "ki.tolk_lti_over_tak", v0=_sv(lti), v1=_sv(LTI_LENDING_CEILING),
        )))
    elif lti > LTI_FI_THRESHOLD:
        findings.append(Finding("warning", L("ki.tolk_lti_over_fi", v0=_sv(lti))))
    else:
        findings.append(Finding("good", L("ki.tolk_lti_rimlig", v0=_sv(lti))))

    # 2. Can the monthly cost be carried at all?
    if cost_pct >= 100:
        findings.append(Finding("critical", L("ki.tolk_kostnad_over_100", v0=_sv(cost_pct, 0))))
    elif cost_pct >= HOUSING_COST_SHARE_GUIDELINE:
        findings.append(Finding("warning", L(
            "ki.tolk_kostnad_over_riktvarde", v0=_sv(cost_pct, 0),
            v1=_sv(HOUSING_COST_SHARE_GUIDELINE, 0),
        )))
    else:
        findings.append(Finding("good", L("ki.tolk_kostnad_under_riktvarde", v0=_sv(cost_pct, 0))))

    # 3. The savings horizon, stated with the assumption that produced it.
    findings.append(Finding(
        "note" if years < SAVE_YEARS_STRAINED else "warning",
        L("ki.tolk_spartid", v0=_sv(years), v1=_sv(savings_rate * 100, 0),
          v2=f"{income * savings_rate:,.0f}".replace(",", " ")),
    ))

    # 4. Which way the 2026 easing moved cost here. It lowers the deposit
    #    everywhere, but a smaller deposit is a larger loan, so the monthly cost
    #    can move either way depending on the region's price and rate.
    cash_delta = strictest["required_cash"] - baseline["required_cash"]
    monthly_delta = baseline["monthly_total"] - strictest["monthly_total"]
    if cash_delta > 0 and monthly_delta > 0:
        findings.append(Finding("note", L(
            "ki.tolk_lattnad_avvagning",
            v0=f"{cash_delta:,.0f}".replace(",", " "),
            v1=f"{monthly_delta:,.0f}".replace(",", " "),
        )))
    elif cash_delta > 0:
        findings.append(Finding("good", L(
            "ki.tolk_lattnad_battre",
            v0=f"{cash_delta:,.0f}".replace(",", " "),
            v1=f"{abs(monthly_delta):,.0f}".replace(",", " "),
        )))

    # 5. The single-income assumption is the most common reason a result looks
    #    worse than the reader's own situation.
    if household_multiplier == 1:
        findings.append(Finding("note", L("ki.tolk_singel_antagande")))

    return findings


# ── Scenariosimulator ─────────────────────────────────────────────────


def interpret_scenario(
    *,
    result: dict,
    rate_shock: float,
    income_shock_pct: float,
    price_shock_pct: float,
    cpi_shock: float,
) -> list[Finding]:
    """Explain one scenario result, and why it moved the way it did.

    Args:
        result: `simulate` output.
        rate_shock: Policy rate change in percentage points.
        income_shock_pct: Income change in percent.
        price_shock_pct: Price change in percent.
        cpi_shock: CPI change in percentage points.

    Returns:
        Findings ordered most serious first.
    """
    findings: list[Finding] = []
    untouched = not any((rate_shock, income_shock_pct, price_shock_pct, cpi_shock))
    if untouched:
        return [Finding("note", L("sc.tolk_inget_scenario"))]

    delta_pct = result["delta_pct"]
    real_base = result["real_rate_base"]
    real_scen = result["real_rate_scen"]

    # 1. The headline, naming the direction rather than leaving the reader to
    #    infer it from two numbers. A bare "changed by 72 %" reads as a rise.
    shift = dict(
        v0=_sv(abs(delta_pct), 1),
        v1=_sv(result["baseline_v_c"]),
        v2=_sv(result["scenario_v_c"]),
    )
    if delta_pct > 0:
        findings.append(Finding("good", L("sc.tolk_riktning_upp", **shift)))
    elif delta_pct < 0:
        findings.append(Finding("warning", L("sc.tolk_riktning_ner", **shift)))
    else:
        findings.append(Finding("note", L("sc.tolk_riktning_oforandrad", **shift)))

    # 2. What actually drove it. The real rate is the term most people do not
    #    track, so name it explicitly whenever it moved.
    if abs(real_scen - real_base) > 0.01:
        findings.append(Finding("note", L(
            "sc.tolk_realranta", v0=_sv(real_base, 2), v1=_sv(real_scen, 2),
        )))
    if real_scen <= 0.5 and (real_base - real_scen) > 0.01:
        findings.append(Finding("note", L("sc.tolk_golv_binder")))

    # 3. The specific misreading this page invites: moving the rate alone treats
    #    the entire nominal change as a change in the real rate.
    if rate_shock != 0 and cpi_shock == 0:
        findings.append(Finding("warning", L("sc.tolk_ranta_utan_inflation", v0=_sv(rate_shock, 2))))

    # 4. Scale. This number is not the one the map shows.
    findings.append(Finding("note", L("sc.tolk_skala")))

    return findings


# ── Rendering ─────────────────────────────────────────────────────────

_ICON = {"critical": "🔴", "warning": "🟠", "good": "🟢", "note": "•"}


def _bold(text: str) -> str:
    """Render `**...**` as markup.

    The lines are emitted inside a raw HTML block so the severity colour can be
    carried on the wrapper, and Streamlit does not parse markdown inside raw
    HTML. Without this the emphasis in a label renders as literal asterisks.
    """
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def render_findings(findings: list[Finding], *, title: str) -> None:
    """Render findings as a bordered panel, most serious first.

    Args:
        findings: From one of the `interpret_*` functions.
        title: Panel heading, from `SWEDISH_LABELS`.
    """
    if not findings:
        return
    with st.container(border=True):
        st.markdown(f"**{title}**")
        for f in findings:
            st.markdown(
                f'<div class="shai-interpret shai-interpret--{f.level}">'
                f'<span class="shai-interpret-icon">{_ICON.get(f.level, "•")}</span>'
                f"<span>{_bold(f.text)}</span></div>",
                unsafe_allow_html=True,
            )
