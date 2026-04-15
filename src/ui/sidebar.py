"""SHAI sidebar matching KRI mockup dark navy design.

Renders brand block, navigation, year selector, risk filter, and footer.
"""

from __future__ import annotations

from datetime import date

import streamlit as st


PAGES = [
    ("01", "Riksoversikt", "Riksöversikt"),
    ("02", "Lan_jamforelse", "Län jämförelse"),
    ("03", "Kommun_djupanalys", "Kommun djupanalys"),
    ("04", "Kontantinsats", "Kontantinsats analys"),
    ("05", "Scenario", "Scenariosimulator"),
    ("06", "Metodologi", "Metodologi och källor"),
]

YEAR_RANGE = list(range(2020, 2025))


def render_sidebar() -> dict:
    """Render the SHAI sidebar and return user selections.

    Returns:
        dict with keys: selected_year, risk_filter
    """
    with st.sidebar:
        # Brand block
        st.markdown("""
        <div class="shai-sidebar-brand">
            <div class="shai-sidebar-eyebrow">SHAI Dashboard</div>
            <div class="shai-sidebar-title">Bostadsekonomisk<br>hållbarhet</div>
            <div class="shai-sidebar-subtitle">Sverige · 2014 till 2024</div>
        </div>
        """, unsafe_allow_html=True)

        # Year selector
        st.markdown(
            '<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#9CA3AF;margin-bottom:6px;font-weight:600;">Valt år</div>',
            unsafe_allow_html=True,
        )
        selected_year = st.select_slider(
            "År",
            options=YEAR_RANGE,
            value=YEAR_RANGE[-1],
            label_visibility="collapsed",
        )

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Risk filter
        st.markdown(
            '<div style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#9CA3AF;margin-bottom:6px;font-weight:600;">Riskfilter</div>',
            unsafe_allow_html=True,
        )
        risk_options = ["Alla", "Låg risk", "Medel risk", "Hög risk"]
        risk_filter = st.radio(
            "Risk",
            risk_options,
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # Footer
        st.markdown(f"""
        <div class="shai-sidebar-footer">
            <div style="margin-bottom:4px;"><strong>KÄLLA:</strong> SCB, Riksbanken, Kolada</div>
            <div>Senast uppdaterad: {date.today().strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)

    return {
        "selected_year": selected_year,
        "risk_filter": risk_filter,
    }
