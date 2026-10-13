"""SHAI sidebar matching KRI dark navy design.

Renders brand block, page_link navigation, year pills, risk filter, and footer.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.provenance import complete_case_max_year, first_year, generated_at
from src.ui.filters import RISK_LABELS
from src.ui.version import APP_VERSION  # re-exported for app.py and Sida 06

PAGES = [
    ("app.py", "Startsida"),
    # Names only. The numbers were tried and removed: they matched the "Sida NN"
    # eyebrows but made the rail busy, and the order is already legible without
    # them (national, county, municipality, calculator, scenario, method).
    ("pages/01_Riksoversikt.py", "Riksöversikt"),
    ("pages/02_Lan_jamforelse.py", "Länsjämförelse"),
    ("pages/03_Kommun_djupanalys.py", "Kommunanalys"),
    ("pages/04_Kontantinsats.py", "Kontantinsatsanalys"),
    ("pages/05_Scenario.py", "Scenariosimulator"),
    ("pages/06_Metodologi.py", "Metodologi och källor"),
]

# The selector offers exactly the years the affordability index covers, both
# ends read from the provenance artifact.
#
# It used to run to the current calendar year on the theory that forward-filled
# income rows made 2025 and 2026 worth selecting. They were not: the panel
# forward-fills income but leaves transaction_price_sek and unemployment_rate
# null, so no formula can evaluate and every page hit st.stop() with "Inga data
# tillgängliga". Two of the seven offered years were dead ends (Finding B).
#
# complete_case_max_year() is the year income was last actually published, which
# is the real ceiling — see src/provenance.py.
YEAR_RANGE = list(range(first_year(), complete_case_max_year() + 1))


def default_year() -> int:
    """Year selected on first load: the most recent the index can compute."""
    return YEAR_RANGE[-1]


def data_vintage() -> str:
    """Date the data artifacts were built, as YYYY-MM-DD.

    This is the pipeline's run date, never the render date. The footer used to
    print the current date instead, so a visitor read "Senast uppdaterad" above
    an index whose newest input was two years older than that (Finding C).
    """
    return datetime.fromisoformat(generated_at()).strftime("%Y-%m-%d")


def footer_html() -> str:
    """Build the sidebar footer markup.

    Separated from :func:`render_sidebar` so the vintage it reports can be
    asserted without a Streamlit runtime.
    """
    return f"""
        <div class="shai-sidebar-footer">
            <div>Data uppdaterad: {data_vintage()}</div>
            <div style="margin-top:4px;font-size:10px;color:#8A8FA8;">v{APP_VERSION}</div>
        </div>
    """


def render_sidebar() -> dict:
    """Render the SHAI sidebar and return user selections.

    The year and risk filter persist across page navigation. See the comment on
    the year pills below for why one shared widget key is not enough on its own.

    Returns:
        dict with keys: selected_year, selected_risks
    """
    with st.sidebar:
        # ── Brand block ──────────────────────────────────────────
        st.markdown(f"""
        <div class="shai-sidebar-brand">
            <div class="shai-brand-mark">SHAI KONTROLLPANEL</div>
            <div class="shai-brand-title">Bostadsekonomisk<br>hållbarhet</div>
            <div class="shai-brand-sub">Sverige · {YEAR_RANGE[0]} till {YEAR_RANGE[-1]}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation ───────────────────────────────────────────
        st.markdown('<div class="shai-sidebar-section-label">Navigation</div>', unsafe_allow_html=True)
        for filepath, label in PAGES:
            st.page_link(filepath, label=label)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # ── Year pills ───────────────────────────────────────────
        st.markdown(
            '<div class="shai-control-label">Valt år</div>',
            unsafe_allow_html=True,
        )
        # Streamlit discards a widget's own session_state entry when the page
        # that rendered it stops being the active page. A page-scoped key means
        # every navigation lands on a widget that has never been touched, so the
        # year silently reverted to default_year() and each page appeared to
        # show different data. Sharing one key across pages does not fix it
        # either: the shared key is simply recreated at its default on arrival.
        # Verified empirically, not assumed.
        #
        # A plain (non-widget) session_state entry is not discarded that way, so
        # the selection is mirrored into one and read back as `default` on the
        # next page. That is what carries the year across navigation.
        # A stored year outside the offered range (a refresh can shorten it while
        # a session is open) would make st.pills raise on its default. Fall back
        # to the default year instead of crashing every page.
        if st.session_state.get("shai_selected_year") not in YEAR_RANGE:
            st.session_state["shai_selected_year"] = default_year()

        selected_year = st.pills(
            "Välj år",
            options=YEAR_RANGE,
            default=st.session_state["shai_selected_year"],
            label_visibility="collapsed",
            key="shai_year_pills",
        )
        # Fallback if nothing selected
        if selected_year is None:
            selected_year = st.session_state["shai_selected_year"]
        st.session_state["shai_selected_year"] = selected_year

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # ── Risk filter with legend ──────────────────────────────
        st.markdown("""
        <div class="shai-control-label">Riskfilter</div>
        <div class="shai-risk-legend">
            <div class="shai-risk-legend-row">
                <span class="shai-risk-legend-dot" style="background:#2E7D5B;"></span>
                <span>Låg risk</span>
            </div>
            <div class="shai-risk-legend-row">
                <span class="shai-risk-legend-dot" style="background:#D4A03C;"></span>
                <span>Medelrisk</span>
            </div>
            <div class="shai-risk-legend-row">
                <span class="shai-risk-legend-dot" style="background:#B94A48;"></span>
                <span>Hög risk</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Same persistence mechanism as the year pills above.
        # Same guard as the year: keep only labels the pills still offer.
        st.session_state["shai_selected_risks"] = [
            r for r in st.session_state.get("shai_selected_risks") or [] if r in RISK_LABELS
        ]

        selected_risks = st.pills(
            "Riskfilter",
            options=list(RISK_LABELS),
            selection_mode="multi",
            default=st.session_state["shai_selected_risks"],
            label_visibility="collapsed",
            key="shai_risk_pills",
        )
        st.session_state["shai_selected_risks"] = selected_risks or []
        # Empty selection = show all
        if not selected_risks:
            selected_risks = list(RISK_LABELS)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # ── Footer ───────────────────────────────────────────────
        # The forward-fill note that used to sit here is gone: the years it
        # warned about are no longer selectable, so it described a state the UI
        # cannot enter.
        st.markdown(footer_html(), unsafe_allow_html=True)

    return {
        "selected_year": selected_year,
        "selected_risks": selected_risks,
    }
