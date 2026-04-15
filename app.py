"""SHAI — Swedish Housing Affordability Indicator.

Entry point for the Streamlit multi-page dashboard.
"""

import streamlit as st

st.set_page_config(
    page_title="SHAI — Bostadsekonomisk hållbarhet",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.ui.css import inject_css
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title, kpi_card, render_kpi_row

inject_css()
selections = render_sidebar()

# Landing page content
page_title(
    eyebrow="Sida 00 · Startsida",
    title="SHAI Dashboard",
    subtitle="Strukturell bostadsekonomisk hållbarhet i Sveriges 290 kommuner",
)

st.markdown("""
Välkommen till **SHAI** (Swedish Housing Affordability Indicator).

Använd sidomenyn för att navigera mellan de sex analysvyerna:

1. **Riksöversikt** — nationell överblick med karta och nyckeltal
2. **Län jämförelse** — jämför 21 län under tre formelversioner
3. **Kommun djupanalys** — prognos och detaljanalys per kommun
4. **Kontantinsats analys** — historiska regimer och insatskrav
5. **Scenariosimulator** — stresstesta ränta, inkomst och prisförändringar
6. **Metodologi och källor** — formler, datakällor och begränsningar
""")

# Quick KPI preview
render_kpi_row([
    kpi_card("Valt år", str(selections["selected_year"]), variant="accent"),
    kpi_card("Kommuner", "290", variant="default"),
    kpi_card("Län", "21", variant="default"),
    kpi_card("Riskfilter", selections["risk_filter"], variant="default"),
])
