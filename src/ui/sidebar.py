"""SHAI sidebar matching KRI dark navy design.

Renders brand block, page_link navigation, year pills, risk filter, and footer.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

PAGES = [
    ("app.py", "Startsida"),
    ("pages/01_Riksoversikt.py", "Riksöversikt"),
    ("pages/02_Lan_jamforelse.py", "Län jämförelse"),
    ("pages/03_Kommun_djupanalys.py", "Kommun djupanalys"),
    ("pages/04_Kontantinsats.py", "Kontantinsats analys"),
    ("pages/05_Scenario.py", "Scenariosimulator"),
    ("pages/06_Metodologi.py", "Metodologi och källor"),
]

YEAR_RANGE = list(range(2020, 2025))


def render_sidebar(page_key: str = "main") -> dict:
    """Render the SHAI sidebar and return user selections.

    Args:
        page_key: Unique prefix for widget keys to avoid collisions.

    Returns:
        dict with keys: selected_year, risk_filter, selected_risks
    """
    with st.sidebar:
        # ── Brand block ──────────────────────────────────────────
        st.markdown("""
        <div class="sidebar-brand">
            <div class="brand-mark">SHAI KONTROLLPANEL</div>
            <div class="brand-title">Bostadsekonomisk<br>hållbarhet</div>
            <div class="brand-sub">Sverige · 2014 till 2024</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation ───────────────────────────────────────────
        st.markdown('<div class="nav-section">Navigation</div>', unsafe_allow_html=True)
        for filepath, label in PAGES:
            st.page_link(filepath, label=label)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Year pills ───────────────────────────────────────────
        st.markdown(
            '<div class="control-label">Valt år</div>',
            unsafe_allow_html=True,
        )
        selected_year = st.pills(
            "Välj år",
            options=YEAR_RANGE,
            default=YEAR_RANGE[-1],
            label_visibility="collapsed",
            key=f"{page_key}_year_pills",
        )
        # Fallback if nothing selected
        if selected_year is None:
            selected_year = YEAR_RANGE[-1]

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ── Risk filter with legend ──────────────────────────────
        st.markdown("""
        <div class="control-label">Riskfilter</div>
        <div class="riskklass-legend">
            <div class="riskklass-rad">
                <span class="riskklass-punkt" style="background:#2E7D5B;"></span>
                <span>Låg risk</span>
            </div>
            <div class="riskklass-rad">
                <span class="riskklass-punkt" style="background:#D4A03C;"></span>
                <span>Medel risk</span>
            </div>
            <div class="riskklass-rad">
                <span class="riskklass-punkt" style="background:#B94A48;"></span>
                <span>Hög risk</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        selected_risks = st.pills(
            "Riskfilter",
            options=["Hög", "Medel", "Låg"],
            selection_mode="multi",
            label_visibility="collapsed",
            key=f"{page_key}_risk_pills",
        )
        # Empty selection = show all
        if not selected_risks:
            selected_risks = ["Hög", "Medel", "Låg"]

        # Map to filter key for backward compat
        risk_map_rev = {"Hög": "Hög risk", "Medel": "Medel risk", "Låg": "Låg risk"}
        if len(selected_risks) == 3:
            risk_filter = "Alla"
        elif len(selected_risks) == 1:
            risk_filter = risk_map_rev.get(selected_risks[0], "Alla")
        else:
            risk_filter = "Alla"

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # ── Footer ───────────────────────────────────────────────
        st.markdown(f"""
        <div class="sidebar-footer">
            <div style="margin-bottom:4px;"><strong>KÄLLA:</strong> SCB, Riksbanken, Kolada</div>
            <div>Senast uppdaterad: {date.today().strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)

    # Persist to session state
    st.session_state["selected_year"] = selected_year
    st.session_state["selected_risks"] = selected_risks

    return {
        "selected_year": selected_year,
        "risk_filter": risk_filter,
        "selected_risks": selected_risks,
    }
