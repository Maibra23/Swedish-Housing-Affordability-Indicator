"""Sida 06 — Metodologi och källor.

Formler, datakällor, begränsningar (F1–F10) och validering.
Sections 1–3 always visible, 4–8 in expanders.
"""

import streamlit as st

st.set_page_config(page_title="SHAI · Metodologi", layout="wide")

from src.ui.css import inject_css, COLORS
from src.ui.sidebar import render_sidebar
from src.ui.components import page_title

inject_css()
selections = render_sidebar()

page_title(
    eyebrow="Sida 06 · Metodologi",
    title="Metodologi och källor",
    subtitle="Teoretisk grund, formler, datakällor och dokumenterade begränsningar",
)

# ══════════════════════════════════════════════════════════════════════
# SECTION 1 — Teoretisk grund (always visible)
# ══════════════════════════════════════════════════════════════════════
st.markdown("## 1. Teoretisk grund")

st.markdown("""
Bostadsöverkomlighet (*housing affordability*) beskriver förhållandet mellan ett hushålls
betalningsförmåga och kostnaden för boende. Banker och tillsynsmyndigheter analyserar detta
genom tre perspektiv:

1. **Flödesöverkomlighet** — kan hushållet klara månadskostnaden?
2. **Stocköverkomlighet** — kan hushållet samla ihop kontantinsatsen?
3. **Risköverkomlighet** — vad händer under stressade förhållanden?

SHAI implementerar alla tre genom formeltrippletten (A, B, C), kontantinsatsmotorn
och scenariosimulatorn.
""")

# ══════════════════════════════════════════════════════════════════════
# SECTION 2 — Variabler och datakällor (always visible)
# ══════════════════════════════════════════════════════════════════════
st.markdown("## 2. Variabler och datakällor")

st.markdown("""
| Variabel | Symbol | Källa | Upplösning | Frekvens | Täckning |
|----------|--------|-------|------------|----------|----------|
| Median disponibel inkomst | I | SCB HE0110 | Kommun, län, riket | Årlig | 2011–2024 |
| Fastighetsprisindex | P | SCB BO0501A | Län (21), riket | Årlig | 1990–2025 |
| Köpeskillingskoefficient (K/T) | KT | SCB BO0501B | Kommun (312), län | Årlig | 1981–2024 |
| Styrränta | R | Riksbanken Swea | Riket | Dag → årssnitt | 2014–idag |
| KPI (skuggindex) | π | SCB PR0101 | Riket | Månad → årssnitt | 1980–idag |
| KPI årsförändring | π% | SCB PR0101 | Riket | Månad → årssnitt | 1981–idag |
| Realränta | r* = R − π | Härledd | Riket | Årlig | 2014–idag |
| Arbetslöshet | U | Kolada N03937 (Arbetsförmedlingen) | Kommun, län, riket | Årlig | 2010–2024 |
| Befolkning | N | SCB BE0101 | Kommun, län, riket | Årlig | 1968–2024 |
| Bostadsbyggande | H | SCB BO0101 | Kommun, län, riket | Årlig | 1975–2024 |

**Arbetslöshetsdefinition:** Öppet arbetslösa inskrivna vid Arbetsförmedlingen, 18–65 år,
som andel av befolkningen 18–65 år. Detta är *inte* samma som AKU/ILO-arbetslöshet.
""")

# ══════════════════════════════════════════════════════════════════════
# SECTION 3 — Formler (always visible)
# ══════════════════════════════════════════════════════════════════════
st.markdown("## 3. Formler")

st.markdown("### Version A: Bankmodell (affordability ratio)")
st.latex(r"\text{Affordability}_A(i,t) = \frac{I(i,t)}{KT(i,t) \times R(t)}")
st.markdown("""
Mäter flödesöverkomlighet — hushållets inkomst relativt bostadens pris och aktuell ränta.
Speglar traditionell bankbedömning. **Högre värde = bättre överkomlighet.**
""")

st.markdown("### Version B: Makrokomposit (tryckmått)")
st.latex(r"\text{Risk}_B(i,t) = 0{,}35 \cdot z\!\left(\frac{KT}{I}\right) + 0{,}25 \cdot z(R) + 0{,}20 \cdot z(U) + 0{,}20 \cdot z(\pi)")
st.markdown("""
Sammansatt riskindikator som viktar pris/inkomst, ränta, arbetslöshet och inflation.
z-poäng beräknas över hela panelen. **Högre värde = högre risk.**
""")

st.markdown("### Version C: Realversion (rekommenderad)")
st.latex(r"\text{Affordability}_C(i,t) = \frac{I(i,t)}{KT(i,t) \times \max(R(t) - \pi(t),\; 0{,}005)}")
st.markdown("""
Justerar för inflation genom realräntan. Golvet 0,005 förhindrar division med noll
vid negativa realräntor. Akademiskt förankrad. **Högre värde = bättre överkomlighet.**
""")

st.markdown("### Varför K/T, inte prisindex?")
st.markdown("""
Prisindex (1990=100) är ett *tillväxtmått* som inte kan jämföras mellan regioner —
alla län startar på 100 oavsett prisnivå. K/T-kvoten (köpeskilling/taxeringsvärde)
är ett *nivåmått* som speglar den faktiska prisnivån och möjliggör meningsfull
tvärsnittsrankning mellan kommuner.

Med prisindex som prisvariabel rankas Stockholm paradoxalt som mest överkomligt
(låg tillväxt = lågt index), vilket strider mot verkligheten. K/T-kvoten korrigerar detta.
""")

# ══════════════════════════════════════════════════════════════════════
# SECTION 4 — Prognoser (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("4. Prognoser (Prophet vs ARIMA)"):
    st.markdown("""
    ### Prophet (standard i gränssnittet)
    - **Bibliotek:** Meta Prophet
    - Dekomponerar i trend + säsongsvariation
    - Lämplig för visualisering och icke-tekniska målgrupper
    - **Begränsning:** Prophet är optimerat för dagliga affärsserier, inte årlig makrodata

    ### ARIMA (rekommenderad för analys)
    - **Bibliotek:** statsmodels + pmdarima (auto_arima)
    - Automatisk ordningsval via AIC
    - Metodologiskt rigorös för tidsserieanalys
    - **Begränsning:** Konfidensintervall vidgas snabbt efter 2–3 år

    ### Viktig kaveat
    **Alla prognoser baseras på 11 årliga observationer (2014–2024).** Detta är en
    extremt kort tidsserie för statistisk prognos. Konfidensintervallen vidgas snabbt
    och prognoser bortom 3 år bör tolkas med stor försiktighet.

    ### Prognosmetodik
    Varje komponent (inkomst, K/T, ränta) prognostiseras separat och komponeras
    sedan till ett affordability-index. Direkt prognos av indexet introducerar
    stationäritetsproblem.

    **Horisont:** 6 årliga steg (2025–2030). Begränsad till max 8 steg.
    """)

# ══════════════════════════════════════════════════════════════════════
# SECTION 5 — Kontantinsats (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("5. Kontantinsats — regimhistorik"):
    st.markdown("""
    Fyra regulatoriska regimer modelleras:
    """)

    # Timeline visual
    st.markdown("""
    <div style="position:relative;padding:20px 0;margin:16px 0;">
        <div style="position:absolute;top:40px;left:0;right:0;height:3px;background:#EEF0F3;"></div>

        <div style="display:flex;justify-content:space-between;position:relative;">
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:#9CA3AF;margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Före 2010</div>
                <div style="font-size:10px;color:#6B7280;">Inget formellt krav</div>
            </div>
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:#C4A35A;margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Okt 2010</div>
                <div style="font-size:10px;color:#6B7280;">Bolånetak 85%</div>
            </div>
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:#D4A03C;margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Jun 2016</div>
                <div style="font-size:10px;color:#6B7280;">Amorteringskrav 1.0</div>
            </div>
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:#B94A48;margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Mar 2018</div>
                <div style="font-size:10px;color:#6B7280;">Amorteringskrav 2.0</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    | Regelverk | Period | Kontantinsats | Amorteringskrav |
    |-----------|--------|---------------|-----------------|
    | Före 2010 | Till okt 2010 | Inget formellt minimum | Inget obligatoriskt |
    | Bolånetak | Okt 2010 – jun 2016 | Min 15% | Inget obligatoriskt |
    | Amorteringskrav 1.0 | Jun 2016 – mar 2018 | Min 15% | 2% om LTV>70%, 1% om LTV>50% |
    | Amorteringskrav 2.0 | Mar 2018 – nuvarande | Min 15% | Ovan + 1% extra om LTI>4,5x |

    **Källa:** Finansinspektionen
    """)

# ══════════════════════════════════════════════════════════════════════
# SECTION 6 — Begränsningar F1–F10 (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("6. Begränsningar (F1–F10)"):
    st.markdown("""
    | ID | Begränsning | Åtgärd |
    |----|-------------|--------|
    | **F1** | Kommunal pristäckning — länets K/T används som proxy. 88% av panelen har kommunspecifik K/T. | Flagga `has_native_kt` i data. Tydlig markering i kartan. |
    | **F2** | Nationell styrränta appliceras på alla kommuner och län. | Dokumenterat. Kommunal variation beror helt på inkomstskillnader. |
    | **F3** | Tre formler ger olika rangordning av kommuner. | "Varför skiljer sig versionerna åt"-panel med korsformelsjämförelse. |
    | **F4** | Prophet är svagt för årlig makrodata (designat för dagliga serier). | ARIMA-flik märkt "rekommenderad"; Prophet märkt "standard". |
    | **F5** | Kontantinsats är en stegfunktion, inte kontinuerlig. | Diskreta regimkort, inte reglage. |
    | **F6** | Lång horisont vilseleder — årlig data ger färre datapunkter. | Hård begränsning vid 8 steg; varningstext i gränssnitt. |
    | **F7** | SCB API-gränser (30 anrop/10 s, 150k celler/fråga). | All data cachad som parquet vid byggtid. Inga live-anrop från Streamlit. |
    | **F8** | Översättning tappar nyanser i bankterminologi. | Ordlista i svensk-översättningsskill; banktermer curaterade. |
    | **F9** | Imputering av inkomstdata. 2025–2026 använder framskrivna värden från 2024. | `is_imputed_income`-flagga synlig i data och gränssnitt. |
    | **F10** | Arbetslöshetsdefinition. Kolada N03937 mäter öppet arbetslösa (Af), inte AKU/ILO. | Fotnot på alla sidor som visar arbetslöshet. Tydligare definition i variabelregistret. |
    """)

# ══════════════════════════════════════════════════════════════════════
# SECTION 7 — Datavalidering (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("7. Datavalidering"):
    st.markdown("""
    Följande valideringskontroller körs innan publicering:

    1. **Nominell inkomst ökande:** Medianinkomst bör öka nominellt år för år (2011–2024).
       *Avvikelser:* 3 nominella minskningar observerade (2019, 2022, 2023) — dessa beror på
       SCB:s bearbetningsmetodik och ligger inom förväntade marginaler.

    2. **Real inkomst stabil:** Deflaterad inkomst bör vara ungefär stabil eller svagt ökande.

    3. **Stockholm i topp 5 sämst (Version C):** Stockholms kommun rankas bland de 5 kommuner
       med sämst bostadsöverkomlighet under Version C (realversion). Verifierat med K/T-data.

    4. **Norrbotten i topp 5 bäst (Version A):** Norrbottens län rankas bland de 5 bäst
       under Version A (bankmodell).

    5. **K/T-intervall:** Alla K/T-värden ligger mellan 1,0 och 4,0 för inkluderade kommuner.

    6. **Prognosintervall vidgas:** Konfidensband vidgas monotont med horisont.

    Alla kontroller implementerade i `tests/test_validation.py` och körs med pytest.
    """)

# ══════════════════════════════════════════════════════════════════════
# SECTION 8 — Referenser (expander)
# ══════════════════════════════════════════════════════════════════════
with st.expander("8. Referenser"):
    st.markdown("""
    - **SCB BO0501** (Fastighetspriser och lagfarter): [scb.se/bo0501](https://www.scb.se/bo0501-en)
    - **SCB HE0110** (Hushållens ekonomi): [scb.se/he0110](https://www.scb.se/he0110-en)
    - **SCB BE0101** (Befolkningsstatistik): [scb.se/be0101](https://www.scb.se/be0101)
    - **SCB PR0101** (Konsumentprisindex): [scb.se/pr0101](https://www.scb.se/pr0101)
    - **SCB BO0101** (Bostadsbyggande): [scb.se/bo0101](https://www.scb.se/bo0101)
    - **Kolada API v3** (Kommunal statistik): [kolada.se](https://www.kolada.se/)
    - **Kolada N03937** (Arbetslöshet, Arbetsförmedlingen): [api.kolada.se/v3/](https://api.kolada.se/v3/)
    - **Riksbanken Swea API** (Räntor): [riksbank.se](https://www.riksbank.se/en-gb/statistics/interest-rates-and-exchange-rates/)
    - **Finansinspektionen** (Amorteringskrav): [fi.se](https://www.fi.se/en/our-registers/the-amortisation-requirement/)
    - **SCB PxWeb API v1**: [scb.se/api](https://www.scb.se/api/)
    """)

st.markdown(
    """<div style="font-size:11px;color:#9CA3AF;text-align:center;padding:12px 0;
    border-top:1px solid #EEF0F3;margin-top:32px;">
    <strong>SHAI v1.3</strong> &nbsp;·&nbsp; Metodologi baserad på METHODOLOGY.md
    </div>""",
    unsafe_allow_html=True,
)
