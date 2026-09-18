"""Every user-facing Swedish string in the application.

Code identifiers, comments and docstrings are English; everything a visitor reads
is Swedish and lives here. One dict, so copy can be reviewed as copy, changed
without reading Python, and — the reason this matters most — checked against the
data it describes. `tests/test_copy_matches_artifacts.py` (T4.1) re-derives every
number quoted below from the committed artifacts, which is the guard that stops
Findings A, C and H returning. That test cannot exist while the copy is scattered
across seven page scripts.

Keys are `<page>.<slug>`: `landing`, `rv` (Riksöversikt), `lj` (Län), `kd`
(Kommun), `ki` (Kontantinsats), `sc` (Scenario), `mt` (Metodologi).

Values with `{name}` placeholders are `str.format` templates — reach them through
:func:`L`, which formats and fails loudly on a missing key. Braces belonging to
the copy itself are doubled: Plotly hover templates (`%{{y:,.2f}}`) and inline CSS
both contain braces that `format` would otherwise read as fields.

See task T3.1 and Finding M in docs/REVITALIZATION_PLAN.md.
"""

from __future__ import annotations


def L(key: str, **values: object) -> str:
    """Return the Swedish string for `key`, formatted with `values`.

    Args:
        key: A key of :data:`SWEDISH_LABELS`.
        values: Substitutions for a template's placeholders.

    Returns:
        The label, formatted when `values` are supplied.

    Raises:
        KeyError: If `key` is not defined — naming the closest matches, because a
            typo in a key is otherwise a blank space on a rendered page.
    """
    try:
        text = SWEDISH_LABELS[key]
    except KeyError:
        import difflib

        near = difflib.get_close_matches(key, SWEDISH_LABELS, n=3)
        raise KeyError(
            f"no label {key!r}" + (f"; did you mean {near}?" if near else "")
        ) from None
    return text.format(**values) if values else text


SWEDISH_LABELS: dict[str, str] = {
    "rv.kartfilen_saknas": "Kartfilen saknas (data/geo/kommuner.geojson). Kartan kan inte visas.",
    "mt.expander_4_prognoser_prophet_vs_arima": "4. Prognoser (Prophet vs ARIMA)",
    "mt.expander_5_kontantinsats_regimhistorik": "5. Kontantinsats: regimhistorik",
    "mt.expander_7_datavalidering": "7. Datavalidering",
    "mt.expander_8_referenser": "8. Referenser",
    "lj.lan": "Län",
    "lj.varde": "Värde",
    "lj.ranking": "RANKING",
    "lj.lansranking_v0": "Länsranking {v0}",
    "lj.ranking_subtitle_v0": "{v0} · #1 = bäst överkomlighet",
    # ── Chrome, glossary, explanations, expanders, table headers ─────────
    "ui.forklaring_av_begrepp": "Förklaring av begrepp",
    "ui.data_uppdaterad_v0": "Data uppdaterad {v0}",
    "glossary.zpoang.term": "Z-poäng",
    "glossary.zpoang.def": "Antal standardavvikelser från årets riksmedian, på logaritmisk skala. Beräknas inom varje år, så en kommuns z-poäng säger var den står bland sina jämnåriga, inte om Sverige som helhet blivit dyrare.",
    "glossary.riskklass.term": "Riskklass",
    "glossary.riskklass.def": "Låg, medel eller hög, satt vid ±0,67 standardavvikelser. Gränserna är kvantiler inom året, så ungefär lika stor andel hamnar i varje klass varje år. Antalet i en klass kan därför inte läsas som en trend.",
    "glossary.version_c.term": "Version C",
    "glossary.version_c.def": "Den rekommenderade formeln: inkomst delat med pris gånger realränta. Ett nivåvärde, inte ett 0–100-index. Högre värde betyder bättre överkomlighet.",
    "glossary.rang.term": "Rang",
    "glossary.rang.def": "Placering inom året, där rang 1 är bäst överkomlighet. Rangen är densamma oavsett logaritmering, eftersom transformen är monoton.",
    "glossary.kt_kvot.term": "K/T-kvot",
    "glossary.kt_kvot.def": "Köpeskilling delat med taxeringsvärde. Deskriptiv. Den ingår inte i någon av formlerna; transaktionspriset i SEK används.",
    "rv.forklaring_kpi": "Talen ovan beskriver {v0} kommuner för {v1}. Genomsnittligt SHAI är en nivåserie och kan jämföras mellan år; antalet högriskkommuner är en relativ position inom året och kan inte det.",
    "rv.forklaring_karta": "Färgskalan går från årets lägsta till årets högsta z-poäng, med brytpunkter vid kvartilerna. Skalan sätts om varje år, så en färg betyder ”bland årets mest ansträngda”, inte ett fast pris.",
    "rv.forklaring_histogram": "Fördelningen visar hur {v0} kommuner ligger i förhållande till varandra detta år. Eftersom z-poängen är centrerad inom året ligger tyngdpunkten alltid nära noll. Formen säger något, läget gör det inte.",
    "rv.forklaring_tabell": "Topplistorna är sorterade på Version C inom {v0}. De visar ytterkanterna av årets fördelning, inte kommuner som förändrats mest över tid.",
    "landing.forklaring_statistik": "Indexet täcker {v0} kommuner över {v1} år. Perioden slutar {v2} eftersom medianinkomsten gör det. Övriga serier sträcker sig längre.",
    "lj.forklaring_kpi": "Länsvärden är ovägda medelvärden av kommunerna i länet. Ett län med många små kommuner väger därför lika tungt som ett med få stora.",
    "kd.forklaring_prognos": "Prognosen bygger på {v0} årliga observationer. Det är en mycket kort serie: konfidensintervallen vidgas snabbt och allt bortom tre år bör läsas som riktning, inte nivå.",
    "rv.om_kartan": "Om kartan",
    "rv.om_rankningstabellerna": "Om rankningstabellerna",
    "lj.om_lansjamforelsen": "Om länsjämförelsen",
    "lj.om_lansjamforelsen_text": "Varje län visas som ett ovägt medelvärde av sina kommuner, så Gotland (en kommun) väger lika tungt som Västra Götaland (49). Jämförelsen säger något om länens *typiska* kommun, inte om var flest människor bor. Kurvorna kan jämföras mellan år eftersom de bygger på nivåvärden, men rangordningen inom ett år bygger på z-poäng och kan inte det.",
    "kd.om_prognosen": "Om prognosen",
    "kd.om_prognosen_text": "Prognosen framskrivs från det sista året med observerad inkomst, inte från dagens datum. Den bygger på {v0} årliga observationer, vilket är kort för statistisk framskrivning: konfidensintervallen vidgas snabbt och bortom tre år bör kurvan läsas som riktning, inte som nivå. Den säger ingenting om enskilda bostadsaffärer.",
    "kd.om_komponenterna": "Om komponentuppdelningen",
    "kd.om_komponenterna_text": "Staplarna visar hur mycket varje ingående variabel varierat över perioden för just denna kommun, mätt som variationskoefficient. En hög stapel betyder att variabeln rört sig mycket, inte att den bidrar mest till kommunens nivå.",
    "rv.kommun": "Kommun",
    "rv.z_poang": "Z-poäng",
    "rv.shai": "SHAI",
    "rv.risk": "Risk",
    "rv.ranking": "RANKING",

    # ── Landing page (app.py) ─────────────────────────────────────
    "landing.shai_bostadsekonomisk_hallbarhet": "SHAI · Bostadsekonomisk hållbarhet",
    "landing.shai_bostadsekonomisk_hallbarhet_data_scb": "SHAI · Bostadsekonomisk hållbarhet. Data: SCB, Riksbanken, Kolada.",
    "landing.v0_ar_v_v1": "{v0} år  ·  v{v1}",
    "landing.lan": "Län",
    "landing.jamforda": "jämförda",
    "landing.vad_hittar_du_har": """
<div class="shai-section">
    <div class="shai-section-title">Vad hittar du här?</div>
</div>
""",
    "landing.riksoversikt": "Riksöversikt",
    "landing.nationell_overblick_med_karta_histogram_och": "Nationell överblick med karta, histogram och rankingtabeller för {v0} kommuner.",
    "landing.lan_jamforelse": "Län jämförelse",
    "landing.21_lan_jamforda_under_tre_ekonometriska": "21 län jämförda under tre ekonometriska formler (A, B, C).",
    "landing.jamfor_insatskrav_under_fem_regulatoriska": "Jämför insatskrav under fem regulatoriska regimer sedan 2010.",
    "landing.stresstesta_med_ranta_inkomst_och": "Stresstesta med ränta-, inkomst- och prisförändringar per län.",
    "landing.formler_datakallor_begransningar_f1f10_och": "Formler, datakällor, begränsningar (F1–F10) och validering.",

    # ── Sida 01 — Riksöversikt ────────────────────────────────────
    "rv.shai_riksoversikt": "SHAI · Riksöversikt",
    "rv.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "rv.inga_data_tillgangliga_for_den_valda": "Inga data tillgängliga för den valda perioden.",
    "rv.sida_01_nationell_oversikt": "Sida 01 · Nationell översikt",
    "rv.riksoversikt": "Riksöversikt",
    "rv.strukturell_bostadsekonomisk_hallbarhet_i": "Strukturell bostadsekonomisk hållbarhet i Sveriges {v0} kommuner · {v1}",
    "rv.poang": "poäng",
    "rv.genomsnittlig_version_c_poang_rakvot_inkomst": "Genomsnittlig Version C-poäng (råkvot Inkomst / (Pris × Realränta)) för alla {v0} kommuner. Högre = bättre överkomlighet. Inte ett 0–100 index.",
    "rv.hogrisk_kommuner": "Högrisk kommuner",
    "rv.antal_kommuner_med_z_poang_0_67": "Antal kommuner med z-poäng > 0,67 standardavvikelser (riskklass Hög). Riskklassen är en relativ position inom året: kommunerna jämförs med varandra i just detta år, inte med ett fast gränsvärde. Ungefär lika många hamnar i varje klass varje år, så antalet kan inte visa om Sverige som helhet blivit mer eller mindre överkomligt. Läs det ur Genomsnittligt SHAI, som är en nivåserie.",
    "rv.genomsnittlig_kopeskillingskoefficient_k_t": "Genomsnittlig köpeskillingskoefficient (K/T): köpeskilling / taxeringsvärde. Dimensionslös kvot, typiskt 1,0–4,0. Högre = dyrare relativt taxeringsvärde. Obs: K/T ingår ej i formeln. Transaktionspriset i SEK används i stället.",
    "rv.befolkningsforandring": "Befolkningsförändring",
    "rv.procentuell_befolkningsforandring_jamfort": "Procentuell befolkningsförändring jämfört med föregående år.",
    "rv.geografisk_fordelning": "Geografisk fördelning",
    "rv.fargskala_gron_lag_risk_z_0_67_gul_medel": "Färgskala: Grön = låg risk (z ≤ −0,67) · Gul = medel risk · Röd = hög risk (z > 0,67)",
    "rv.ingen_data_tillganglig_for_kartvisning": "Ingen data tillgänglig för kartvisning.",
    "rv.varje_kommun_visas_som_ett_ifyllt_polygon": "Varje kommun visas som ett ifyllt polygon. Färgen baseras på z-poängen (Version C). Grön = låg risk, röd = hög risk. Håll musen över en kommun för att se detaljer. Små kommunnamn visas först när du zoomat in två steg från startläget (zoomkontrollen +). De är förankrade i kartfilens centrum. Bakgrundskartan visar inga världsstäder. Övrig text kommer från SHAI-data.",
    "rv.fordelning_av_shai_poang": "Fördelning av SHAI poäng",
    "rv.z_poang_standardavvikelser_pa_logaritmisk": "Z-poäng = standardavvikelser på logaritmisk skala. Noll = den typiska kommunen (riksmedianen). Lägre z = bättre överkomlighet.",
    "rv.lag_risk": "Låg risk",
    "rv.hog_risk": "Hög risk",
    "rv.shai_poang_z_poang": "SHAI poäng (z-poäng)",
    "rv.om_fordelningsgrafen": "Om fördelningsgrafen",
    "rv.histogrammet_visar_hur_shai_poangen_z_poang": "Histogrammet visar hur SHAI-poängen (z-poäng) fördelar sig bland kommunerna. Skalan är vänd så att ett lägre z betyder bättre överkomlighet: grön stapel = låg risk, gul = medel, röd = hög risk. Färgen kommer från riskklassen i datafilen, inte från en gräns som räknas om här. Den streckade linjen visar medianen. Klassgränserna placerar ungefär 25 % av kommunerna i varje ytterklass varje år, så fördelningens form säger mer än antalet i en klass.",
        "rv.samst_overkomlighet_topp_15": "Sämst överkomlighet (topp 15)",
    "rv.bast_overkomlighet_topp_15": "Bäst överkomlighet (topp 15)",
    "rv.tabellerna_visar_de_15_kommuner_med_samst": "Tabellerna visar de 15 kommuner med sämst respektive bäst överkomlighet enligt Version C (realversion). Z-poängen anger hur långt kommunen avviker från riksgenomsnittet i standardavvikelser.",

    # ── Sida 02 — Län jämförelse ──────────────────────────────────
    "lj.shai_lan_jamforelse": "SHAI · Län jämförelse",
    "lj.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "lj.sida_02_regional_jamforelse": "Sida 02 · Regional jämförelse",
    "lj.lan_jamforelse": "Län jämförelse",
    "lj.21_lan_jamforda_under_tre_bostadsekonomiska": "21 län jämförda under tre bostadsekonomiska formler",
    "lj.den_enklaste_versionen_mater_hushallets": "Den enklaste versionen mäter hushållets betalningsförmåga relativt bostadens transaktionspris och aktuell ränta. Speglar en traditionell bankbedömning. Högre värde = bättre överkomlighet.",
    "lj.en_sammansatt_riskindikator_som_viktar_fyra": "En sammansatt riskindikator som viktar fyra makrovariabler: pris/inkomst, ränta, arbetslöshet och inflation. Speglar centralbankens makrotillsynsperspektiv. Högre värde = högre risk.",
    "lj.arbetsloshet_avser_oppet_arbetslosa_enligt": "Arbetslöshet avser öppet arbetslösa enligt Arbetsförmedlingen (18–65 år), inte AKU. Obs: R och π är nationella variabler. De bidrar ej till kommunal rangordning inom ett enskilt år (se Begränsning F13).",
    "lj.den_rekommenderade_versionen_justerar_for": "Den rekommenderade versionen justerar för inflation genom att använda realräntan istället för nominalräntan. Akademiskt förankrad. Högre värde = bättre överkomlighet.",
    "lj.att_olika_formler_rangordnar_lanen_olika_ar": "Att olika formler rangordnar länen olika är förväntat och inte ett fel. De mäter olika ekonomiska perspektiv.",
    "lj.stockholm_visas_som_referenslan_markerat_med": "Stockholm visas som referenslän (markerat med starkare linje).",
    "lj.v0_ar_x_varde_y_2f": "<b>{v0}</b><br>År: %{{x}}<br>Värde: %{{y:,.2f}}<extra></extra>",
    "lj.v0_lansutveckling_v1": "{v0} · Länsutveckling {v1}",
    "lj.ar": "År",
    "lj.indexvarde": "Indexvärde",
        "lj.varfor_skiljer_sig_versionerna_at": "Varför skiljer sig versionerna åt?",
    "lj.topp_5_och_botten_5_lan_under_varje_formel": "Topp 5 och botten 5 län under varje formel",
    "lj.jamforelse": "JÄMFÖRELSE",
    "lj.samst_overkomlighet": "*Sämst överkomlighet:*",
    "lj.bast_overkomlighet": "*Bäst överkomlighet:*",

    # ── Sida 03 — Kommun djupanalys ───────────────────────────────
    "kd.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "kd.valj_kommun": "Välj kommun",
    "kd.inga_data_tillgangliga_for_den_valda": "Inga data tillgängliga för den valda kommunen.",
    "kd.poang": "poäng",
    "kd.realversion_inkomst_pris_max_r_0_5_hogre": "Realversion. Inkomst / (Pris × max(R−π, 0,5%)). Högre = bättre överkomlighet. Råkvot, ej ett 0–100 index.",
    "kd.sammanraknad_forvarvsinkomst_medelvarde_per": "Sammanräknad förvärvsinkomst, medelvärde per individ (SCB HE0110). Individuell bruttoinkomst, inte hushållsinkomst.",
    "kd.kopeskillingskoefficient_kopeskilling": "Köpeskillingskoefficient: köpeskilling / taxeringsvärde. Speglar relativ prisnivå. Obs: K/T ingår ej i SHAI-formeln. Transaktionspriset i SEK används i stället.",
    "kd.styrranta": "Styrränta",
    "kd.riksbankens_styrranta_arsgenomsnitt": "Riksbankens styrränta, årsgenomsnitt. Nationell: samma värde för alla kommuner. Bolåneränta ≈ styrränta + 1,5–2,5 pp bankens marginal (Begränsning F12).",
    "kd.prognoser_baseras_pa_v0_arliga_observationer": "**Prognoser baseras på {v0} årliga observationer ({v1}).** Konfidensintervall vidgas snabbt efter år 3. Tolka långtidsprognoser med försiktighet.",
    "kd.x_framskrivet_fran_2024": "<b>%{x}</b><br>Framskrivet från 2024<extra></extra>",
    "kd.ar": "År",
    "kd.prophet_ar_optimerat_for_dagliga": "Prophet är optimerat för dagliga affärsserier. För analys av makroekonomisk årlig data rekommenderas ARIMA-fliken.",
    "kd.prognos_for_v0": "Prognos för {v0}",
    "kd.prognoserna_beraknas_pa_lansniva_v0_inte_per": "Prognoserna beräknas på länsnivå ({v0}), inte per kommun.",
    "kd.v1_har_storst_relativ_variation_och_driver": "<div style='font-size:13px;color:{v0};text-align:center;padding:8px 0;'><strong>{v1}</strong> har störst relativ variation och driver mest av SHAI-förändringen för {v2}.</div>",

    # ── Sida 04 — Kontantinsats ───────────────────────────────────
    "ki.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "ki.inga_data_tillgangliga_for_v0_valj_ett_ar": "Inga data tillgängliga för {v0}. Välj ett år med data: {v1}.",
    "ki.obs_priserna_avser_smahus_villor_scb": "**Obs, priserna avser småhus (villor):** SCB BO0501C2 (Fastighetstyp 220) täcker permanenta småhus och villor. Bostadsrätter och lägenheter ingår ej ännu i panelen. I storstäder är typiska bostadsrätspriser lägre än villapriser. Kontantinsatskraven och spartiderna är därmed höga för stadsbor som söker lägenhet. Se Begränsning F11 i Metodologi (Sida 06).",
    "ki.valj_pristyp_bostadsrattspriser_scb_bo0501c": "**Välj Pristyp:** Bostadsrättspriser (SCB BO0501C) analyseras på **länsnivå** (21 län). SCB publicerar inga kommunspecifika bostadsrättspriser. Småhuspriser (SCB BO0501C2) analyseras på **kommunnivå** ({v0} kommuner). När du väljer Bostadsrätt byter analysen automatiskt till länsnivå.",
    "ki.valj_analysenhet": "Välj analysenhet",
    "ki.region_pristyp_hushallstyp_och": "Region, pristyp, hushållstyp och sparandeantagande",
    "ki.smahus_villa": "Småhus (villa)",
    "ki.bostadsratt": "Bostadsrätt",
    "ki.smahus_scb_bo0501c2_fastighetstyp_220": "Småhus = SCB BO0501C2 (Fastighetstyp 220), kommunnivå ({v0} kommuner). Bostadsrätt = SCB BO0501C, medelpris per bostadsrätt, **länsnivå** (21 län). SCB publicerar inga kommunspecifika bostadsrättspriser.",
    "ki.stockholms_lan": "Stockholms län",
    "ki.valj_lan": "Välj län",
    "ki.valj_kommun": "Välj kommun",
    "ki.hushallstyp": "Hushållstyp",
    "ki.singelhushall": "Singelhushåll",
    "ki.singelhushall_en_individuell_inkomst_par": "Singelhushåll: en individuell inkomst. Par: sammanlagd inkomst (2×), vilket halverar spartiden och sänker LTI.",
    "ki.andel_av_bruttoinkomsten_som_sparas_arligen": "Andel av bruttoinkomsten som sparas årligen. 10 % är vanligt; över 20 % är ambitiöst. Påverkar hur lång tid det tar att spara ihop insatsen.",
    "ki.avancerade_installningar_rantepaslag": "Avancerade inställningar: räntepåslag",
    "ki.riksbankens_styrranta_anvands_som_bas": "Riksbankens styrränta används som bas. Bankens räntepåslag adderas för att approximera faktisk bolåneränta. Typiskt ~1,7 pp för 3-månaders rörlig ränta.",
    "ki.bankens_rantepaslag_pp_ovan_styrrantan": "Bankens räntepåslag (pp ovan styrräntan)",
    "ki.faktisk_bolaneranta_styrranta_rantepaslag_0": "Faktisk bolåneränta ≈ styrränta + räntepåslag. 0 pp = enbart styrränta (historisk default). 1,7 pp = typisk 2024 bankmarknad.",
    "ki.inga_data_tillgangliga_for_den_valda": "Inga data tillgängliga för den valda regionen.",
    "ki.uppsala_lan": "Uppsala län",
    "ki.sodermanlands_lan": "Södermanlands län",
    "ki.ostergotlands_lan": "Östergötlands län",
    "ki.jonkopings_lan": "Jönköpings län",
    "ki.kronobergs_lan": "Kronobergs län",
    "ki.kalmar_lan": "Kalmar län",
    "ki.gotlands_lan": "Gotlands län",
    "ki.blekinge_lan": "Blekinge län",
    "ki.skane_lan": "Skåne län",
    "ki.hallands_lan": "Hallands län",
    "ki.vastra_gotalands_lan": "Västra Götalands län",
    "ki.varmlands_lan": "Värmlands län",
    "ki.orebro_lan": "Örebro län",
    "ki.vastmanlands_lan": "Västmanlands län",
    "ki.dalarnas_lan": "Dalarnas län",
    "ki.gavleborgs_lan": "Gävleborgs län",
    "ki.vasternorrlands_lan": "Västernorrlands län",
    "ki.jamtlands_lan": "Jämtlands län",
    "ki.vasterbottens_lan": "Västerbottens län",
    "ki.norrbottens_lan": "Norrbottens län",
    "ki.bostadsratt_v0_scb_bo0501c": "Bostadsrätt i {v0} (SCB BO0501C)",
    "ki.bostadsrattspris_saknas_for_v0_smahuspriset": "Bostadsrättspris saknas för {v0}. Småhuspriset används som fallback.",
    "ki.smahus_fallback": "Småhus (fallback)",
    "ki.smahus_scb_bo0501c2": "Småhus (SCB BO0501C2)",
    "ki.lan_v0": "Län {v0}",
    "ki.v0_sek_ar_v1": "= {v0} SEK/år ({v1})",
    # Result interpretation (sida 04). Every figure is interpolated from the
    # computed result; none is written into the sentence.
    "ki.tolk_rubrik": "Vad betyder det här för dig?",
    "ki.tolk_lti_over_tak": "**Lånet är sannolikt inte beviljningsbart.** Skuldkvoten blir {v0} gånger hushållets årsinkomst. Svenska banker beviljar sällan bolån över omkring {v1} gånger inkomsten, oavsett vilket regelverk som gäller. Siffrorna nedan beskriver alltså en uträkning, inte ett köp som går att genomföra på den här inkomsten.",
    "ki.tolk_lti_over_fi": "Skuldkvoten blir {v0} gånger årsinkomsten. Det ligger över 4,5 gånger, gränsen som utlöste det skärpta amorteringskravet fram till mars 2026. Lånet är möjligt men räknas som högt belånat.",
    "ki.tolk_lti_rimlig": "Skuldkvoten blir {v0} gånger årsinkomsten, vilket ligger inom det intervall banker normalt beviljar.",
    "ki.tolk_kostnad_over_100": "**Boendekostnaden överstiger inkomsten.** Den tar {v0} % av månadsinkomsten, alltså mer än hela inkomsten. Kvarvarande inkomst blir negativ.",
    "ki.tolk_kostnad_over_riktvarde": "Boendet tar {v0} % av månadsinkomsten. Ett vanligt riktvärde är att hålla sig under {v1} %, så marginalen till annat är liten.",
    "ki.tolk_kostnad_under_riktvarde": "Boendet tar {v0} % av månadsinkomsten, vilket ryms inom det vanliga riktvärdet på 30 %.",
    "ki.tolk_spartid": "Att spara ihop kontantinsatsen tar {v0} år vid {v1} % sparkvot, alltså {v2} kr per år. Sparkvoten räknas på bruttoinkomsten, så det som faktiskt kan sparas efter skatt är normalt lägre och tiden därmed längre.",
    "ki.tolk_lattnad_avvagning": "Lättnaden 2026 sänker kontantinsatsen med {v0} kr jämfört med det tidigare regelverket, men höjer månadskostnaden med {v1} kr. Lägre tröskel in, högre kostnad att bo kvar: en mindre insats betyder ett större lån.",
    "ki.tolk_lattnad_battre": "Lättnaden 2026 sänker både kontantinsatsen, med {v0} kr, och månadskostnaden, med {v1} kr, jämfört med det tidigare regelverket.",
    "ki.tolk_singel_antagande": "Beräkningen utgår från en inkomst. De flesta bostadsköp i Sverige görs av två personer tillsammans. Välj Par ovan för att se hur siffrorna förändras.",
    "ki.tillganglig": "Tillgänglig",
    "ki.anstrangd": "Ansträngd",
    "ki.otillganglig": "Otillgänglig",
    "ki.under_5x_normalt_510x_anstrangt_over_10x": "Under 5x normalt, 5–10x ansträngt, över 10x svårtillgängligt.",
    "ki.kontantinsatsborda": "Kontantinsatsbörda",
    "ki.x_arsinkomst": "x årsinkomst",
    "ki.hur_manga_arsinkomster_kontantinsatsen": "Hur många årsinkomster kontantinsatsen motsvarar.",
    "ki.boendekostnadsborda": "Boendekostnadsbörda",
    "ki.andel_av_manadsinkomst_under_30_anses": "Andel av månadsinkomst. Under 30 % anses hållbart.",
    "ki.tillganglighet": "Tillgänglighet",
    "ki.tillganglig_under_5_ars_spartid_anstrangd": "Tillgänglig = under 5 års spartid. Ansträngd = 5–10 år. Otillgänglig = över 10 år spartid vid vald sparkvot.",
    "ki.lansniva": "länsnivå",
    "ki.kommunniva": "kommunnivå",
    "ki.nulage_lattnad_2026_v0_v1_v2_sparkvot_v3_0f": "Nuläge · Lättnad 2026 · {v0} ({v1}) · {v2} · Sparkvot {v3:.0f}% · Pristyp: {v4}",
    "ki.inkomsten_ar_individuell_bruttoinkomst_scb": "Inkomsten är individuell bruttoinkomst (SCB HE0110). Vid gemensamt köp (par): dividera spartiden med 2. Se Begränsning F14 i Metodologi (Sida 06).",
    "ki.villa_vs_bostadsratt": "Villa vs. bostadsrätt",
    "ki.v0_v1_lattnad_2026": "{v0} · {v1} · Lättnad 2026",
    "ki.pristypsjamforelse": "PRISTYPSJÄMFÖRELSE",
    "ki.smahus_villa_scb_bo0501c2_v0": "**Småhus (villa)**, SCB BO0501C2 ({v0})",
    "ki.ar_att_spara": "År att spara",
    "ki.ar": " år",
    "ki.manadskostnad": "Månadskostnad",
    "ki.bostadsratt_scb_bo0501c_lansniva": "**Bostadsrätt**, SCB BO0501C (länsnivå)",
    "ki.priskvot_villa_bostadsratt_v0_1f_bada_priser": "Priskvot villa/bostadsrätt: **{v0:.1f}×**. Båda priser avser **{v1}** (länsnivå). Samma hushållsinkomst, ränta och regelverk (Lättnad 2026).",
    "ki.priskvot_villa_bostadsratt_v0_1f_villapris": "Priskvot villa/bostadsrätt: **{v0:.1f}×**. Villapris avser **{v1}** (kommunnivå). Bostadsrättspris avser **{v2}** (länsnivå, SCB BO0501C). SCB publicerar inga kommunspecifika bostadsrättspriser.",
    "ki.total_kontantinsats_10_av_medianpriset_under": "Total kontantinsats (10 % av medianpriset under nuvarande bolånetak, gäller fr.o.m. apr 2026).",
    "ki.ar_att_spara_idag": "År att spara (idag)",
    "ki.ar_2": "år",
    "ki.antal_ar_for_att_spara_kontantinsatsen_vid": "Antal år för att spara kontantinsatsen vid vald sparkvot.",
    "ki.manadskostnad_idag": "Månadskostnad (idag)",
    "ki.rante_amorteringskostnad_per_manad_efter_att": "Ränte- + amorteringskostnad per månad efter att ha köpt.",
    "ki.sek_ar": "SEK/år",
    "ki.inkomst_kvar_efter_att_boendekostnaderna_ar": "Inkomst kvar efter att boendekostnaderna är betalda (per år).",
    "ki.fore_2010_bolanetak_amorteringskrav_skarpt": """
<div style="display:flex;width:100%;border-radius:6px;overflow:hidden;margin-top:8px;height:48px;">
  <div style="flex:3;background:{v0};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Före 2010</span>
  </div>
  <div style="flex:3;background:{v1};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Bolånetak</span>
  </div>
  <div style="flex:1;background:{v2};display:flex;align-items:center;justify-content:center;padding:0 2px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Amorteringskrav</span>
  </div>
  <div style="flex:3;background:{v3};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:600;white-space:nowrap;">Skärpt amorteringskrav</span>
  </div>
  <div style="flex:2;background:{v4};border:2px solid {v5};display:flex;align-items:center;justify-content:center;padding:0 6px;">
    <span style="color:#fff;font-size:10px;font-weight:700;white-space:nowrap;">Lättnader i bolånereglerna</span>
  </div>
</div>
<div style="display:flex;width:100%;margin-top:4px;">
  <div style="flex:3;text-align:center;font-size:10px;color:{v6};"></div>
  <div style="flex:3;text-align:center;font-size:10px;color:{v7};">2010</div>
  <div style="flex:1;text-align:center;font-size:10px;color:{v8};">2016</div>
  <div style="flex:3;text-align:center;font-size:10px;color:{v9};">2018</div>
  <div style="flex:2;text-align:center;font-size:10px;color:{v10};">2026</div>
</div>
""",
    "ki.ingen_formell_insatsniva_hog_belaning_var": "Ingen formell insatsnivå; hög belåning var vanligare.",
    "ki.bolanetak_infors_max_85_belaning_hogre": "Bolånetak införs (max 85 % belåning) → högre insats.",
    "ki.amorteringskrav_infors_hogre_manadskostnad": "Amorteringskrav införs → högre månadskostnad vid hög belåning.",
    "ki.skarpt_amorteringskrav_skuldkvot_lti_4_5": "Skärpt amorteringskrav (skuldkvot LTI > 4,5×). Gällde mar 2018 – mar 2026.",
    "ki.bolanetak_hojt_till_90_insats_10_skarpt": "Bolånetak höjt till 90 % (insats 10 %) + skärpt amorteringskrav slopat. Gäller fr.o.m. apr 2026.",
    "ki.lagst": "LÄGST",
    "ki.hogst": "HÖGST",
    "ki.kontantinsats_ar_eget_kapital_insats_som": "Kontantinsats är eget kapital (insats) som krävs vid köp. Lägre är bättre.",
    "ki.v0_1f_ar": "{v0:+.1f} år",
    "ki.antal_ar_for_att_spara_kontantinsatsen_vid_2": "Antal år för att spara kontantinsatsen vid vald sparkvot. Lägre är bättre.",
    "ki.summa_amortering_rantekostnad_per_manad": "Summa amortering + räntekostnad per månad. Lägre är bättre.",
    "ki.obs_inget_formellt_insatskrav_men_banker": "Obs: Inget formellt insatskrav, men banker krävde ofta 5–10 %.",
    "ki.valj_flik_for_att_jamfora_regelverken_fran": "Välj flik för att jämföra regelverken från olika perspektiv. Ändra år i sidopanelen för att se historiska scenarion.",
    "ki.manadskostnad_per_regelverk": "Månadskostnad per regelverk",
    "ki.jamforelse": "JÄMFÖRELSE",
    "ki.manadskostnad_sek": "Månadskostnad (SEK)",
    "ki.30_av_manadsink_v0_sek": "30 % av månadsink. · {v0} SEK",
    "ki.lagre_manadskostnad_innebar_mindre_lopande": "Lägre månadskostnad innebär mindre löpande belastning givet samma pris- och inkomstnivå.",
    "ki.ar_att_spara_kontantinsats": "År att spara kontantinsats",
    "ki.5_ar_tillganglig": "5 år – Tillgänglig",
    "ki.10_ar_otillganglig": "10 år – Otillgänglig",
    "ki.sparkvoten_paverkar_framst_sparar": "Sparkvoten påverkar främst sparår; regelverken påverkar kravet på insats och amortering.",
    "ki.kvarvarande_inkomst_sek_ar": "Kvarvarande inkomst (SEK/år)",
    "ki.nollgrans": "Nollgräns",
    "ki.hogre_kvarvarande_inkomst_innebar_mer": "Högre kvarvarande inkomst innebär mer utrymme efter boendekostnader givet antagandena.",
    "ki.singelhushall_2": "singelhushåll",
    "ki.styrranta_v0_2f_paslag_v1_1f_pp_v2_2f": "styrränta {v0:.2f}% + påslag {v1:.1f} pp = {v2:.2f}%",
    "ki.styrranta_v0_2f": "styrränta {v0:.2f}%",
    "ki.nyckelinsikt_syntes_for_ett_v2_v3_under": """
<div class="shai-card" style="border-left:3px solid {v0};">
  <div class="shai-card-header">
    <div class="shai-card-title">Nyckelinsikt</div>
    <span class="shai-card-tag">SYNTES</span>
  </div>
  <p style="font-size:14px;color:{v1};line-height:1.7;margin:0;">
    För ett <strong>{v2}</strong> ({v3}) under
    <strong>nuvarande regler (Lättnad 2026)</strong> krävs
    <strong>{v4} SEK</strong> i kontantinsats,
    vilket tar <strong>{v5:.1f} år</strong> att spara
    vid {v6} % sparkvot.
    Månadskostnaden är <strong>{v7} SEK</strong>
    (<strong>{v8:.0f} % av månadsinkomst</strong>).<br><br>
    Det historiskt förmånligaste regelverket
    (<strong>{v9}</strong>) innebar
    <strong>{v10} SEK lägre</strong> månadskostnad
    ({v11:.0f} % billigare).
  </p>
</div>
""",
    "ki.lan": "Län",
    "ki.indata_v1_v2_analysar_v3_pristyp_v4_pris": "<div style='color:{v0};font-size:13px;line-height:1.55;'><strong>Indata</strong><br>- {v1}: <strong>{v2}</strong> (analysår {v3})<br>- Pristyp: <strong>{v4}</strong><br>- Pris (används): <strong>{v5} SEK</strong><br>",
    "ki.smahuspris_referens_v0_sek": "- Småhuspris (referens): <strong>{v0} SEK</strong><br>",
    "ki.bostadsrattspris_referens_v0_v1_sek": "- Bostadsrättspris (referens, {v0}): <strong>{v1} SEK</strong><br>",
    "ki.hushallstyp_v0_individuell_medianinkomst_v1": "- Hushållstyp: <strong>{v0}</strong><br>- Individuell medianinkomst: <strong>{v1} SEK</strong><br>- Hushållsinkomst (används): <strong>{v2} SEK</strong>{v3}<br>- Styrränta: <strong>{v4:.2f}%</strong><br>- Bankens räntepåslag: <strong>{v5:.1f} pp</strong><br>- Effektiv bolåneränta (används): <strong>{v6:.2f}%</strong><br>- Sparkvot: <strong>{v7}%</strong><br><br><strong>Konstant mellan regelverk</strong><br>- Samma pris, inkomst och räntenivå används i alla regimer<br>- Skillnaderna drivs av insatskrav, maxbelåning och amorteringsregler<br><br><strong>Metod</strong><br>Se Metodologi (Sida 06), avsnitt 6 för antaganden och definitioner.</div>",
    "ki.sa_laser_du_tabellen_kolumner_visar_skillnad": "<div style='color:{v0};font-size:13px;line-height:1.55;margin-top:8px;'><strong>Så läser du tabellen</strong><br>- Δ-kolumner visar skillnad mot <strong>idag (Lättnad 2026)</strong><br>- Markeringar: <strong>bäst</strong> = lägst för Insats/Sparår/Månkostnad, högst för Kvar</div>",
    "ki.sparar": "Sparår",
    "ki.sparar_2": "Δ Sparår",
    "ki.mankostnad": "Månkostnad",
    "ki.mankostnad_2": "Δ Månkostnad",
    "ki.regim_regelverk_som_jamfors": "Regim/regelverk som jämförs.",
    "ki.tidsperiod_da_regelverket_gallde": "Tidsperiod då regelverket gällde.",
    "ki.kontantinsats_i_sek_lagre_ar_battre": "Kontantinsats i SEK. Lägre är bättre.",
    "ki.skillnad_i_insats_jamfort_med_nuvarande": "Skillnad i insats jämfört med nuvarande regler.",
    "ki.ar_att_spara_kontantinsatsen_vid_vald": "År att spara kontantinsatsen vid vald sparkvot. Lägre är bättre.",
    "ki.sparar_vs_idag": "Δ Sparår vs idag",
    "ki.skillnad_i_sparar_jamfort_med_nuvarande": "Skillnad i sparår jämfört med nuvarande regler.",
    "ki.mankostnad_sek": "Månkostnad (SEK)",
    "ki.manadskostnad_ranta_amortering_lagre_ar": "Månadskostnad (ränta + amortering). Lägre är bättre.",
    "ki.mankostnad_vs_idag": "Δ Månkostnad vs idag",
    "ki.skillnad_i_manadskostnad_jamfort_med_idag": "Skillnad i månadskostnad jämfört med idag.",
    "ki.kvar_sek_ar": "Kvar (SEK/år)",
    "ki.kvarvarande_inkomst_per_ar_efter": "Kvarvarande inkomst per år efter boendekostnad. Högre är bättre.",
    "ki.skillnad_i_kvarvarande_inkomst_jamfort_med": "Skillnad i kvarvarande inkomst jämfört med idag.",
    "ki.belaningsgrad_lan_bostadspris": "Belåningsgrad: lån / bostadspris.",
    "ki.skuldkvot_lan_arsinkomst": "Skuldkvot: lån / årsinkomst.",
    "ki.arlig_amortering_i_av_lanet": "Årlig amortering i % av lånet.",

    # ── Sida 05 — Scenario ────────────────────────────────────────
    "sc.shai_version_c_for_v0": "SHAI Version C för {v0}",
    # Result interpretation (sida 05).
    "sc.tolk_rubrik": "Så ska resultatet läsas",
    "sc.tolk_inget_scenario": "Inget scenario är valt ännu. Flytta en reglage eller välj ett förinställt scenario för att se hur överkomligheten påverkas.",
    "sc.tolk_riktning_upp": "Scenariot **förbättrar** överkomligheten med {v0} %, från {v1} till {v2}.",
    "sc.tolk_riktning_ner": "Scenariot **försämrar** överkomligheten med {v0} %, från {v1} till {v2}.",
    "sc.tolk_riktning_oforandrad": "Scenariot lämnar överkomligheten oförändrad på {v1}.",
    "sc.tolk_realranta": "Drivkraften är realräntan, som går från {v0} % till {v1} %. Det är realräntan, alltså styrränta minus inflation, som formeln använder, inte den nominella räntan.",
    "sc.tolk_golv_binder": "Realräntan har nått golvet på 0,5 procentenheter. Under det slutar formeln reagera på ytterligare sänkningar, så resultatet underskattar effekten.",
    "sc.tolk_ranta_utan_inflation": "**Obs:** du har ändrat räntan med {v0} procentenheter men lämnat inflationen oförändrad. Hela ränteändringen räknas då som en real förändring. I verkligheten rör sig räntan och inflationen ofta åt samma håll, vilket dämpar eller vänder effekten. Prova KPI-chock för ett mer realistiskt scenario.",
    "sc.tolk_skala": "Värdet är ett råmått från formeln, inte samma skala som riskklasserna på Riksöversikt. Jämför basfall mot scenario här, inte mot kartans siffror.",
    "sc.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "sc.inga_data_tillgangliga_for_v0_valj_ett_ar": "Inga data tillgängliga för {v0}. Välj ett år med data: {v1}.",
    "sc.simulera_effekten_av_ranta_inkomst_och": "Simulera effekten av ränta-, inkomst- och prisförändringar på bostadsöverkomligheten",
    "sc.scenariosimulatorn_beraknar_om_version_c": "**Scenariosimulatorn** beräknar om Version C (realversion) för valt län. Versionerna A och B innehåller ytterligare variabler (arbetslöshet) som inte ingår i simulatorn för att hålla gränssnittet enkelt.",
    "sc.valj_lan": "Välj län",
    "sc.forinstallda_scenarier": "**Förinställda scenarier:**",
    "sc.loneboom": "löneboom",
    "sc.4pp_ranta_8pp_kpi_15_pris": "+4pp ränta, +8pp KPI, −15% pris",
    "sc.1pp_ranta_2pp_kpi_10_pris": "−1pp ränta, −2pp KPI, −10% pris",
    "sc.loneboom_2": "Löneboom",
    "sc.1pp_ranta_5_lon_10_pris": "+1pp ränta, +5% lön, +10% pris",
    "sc.aterstall": "Återställ",
    "sc.nollstall_alla_scenariojusteringar_till": "Nollställ alla scenariojusteringar till basfall",
    "sc.rantechock_pp": "Räntechock (pp)",
    "sc.4_pp_riksbankens_hojningscykel_20222023": "+4 pp ≈ Riksbankens höjningscykel 2022–2023. Adderas till styrräntan. Kombinera med KPI-chock för realistiska scenarier.",
    "sc.inkomsttillvaxt": "Inkomsttillväxt (%)",
    "sc.34_ett_ars_normal_loneutveckling_i_sverige_5": "+3–4 % ≈ ett års normal löneutveckling i Sverige. −5 % simulerar recession med lönesänkningar.",
    "sc.8_pp_svensk_inflationstopp_2022_paverkar": "+8 pp ≈ svensk inflationstopp 2022. Påverkar realräntan (R−π). Höjd KPI med oförändrad ränta sänker realräntan → bättre affordability.",
    "sc.inga_data_tillgangliga_for_det_valda_lanet": "Inga data tillgängliga för det valda länet och året.",
    "sc.berakningsfel_se_metodologisidan_for": "Beräkningsfel. Se metodologisidan för detaljer.",
    "sc.basfall_beraknat_fran_faktiska_data_for_valt": "Basfall: beräknat från faktiska data för valt län och år.",
    "sc.scenario_beraknat_med_justerade_parametrar": "Scenario: beräknat med justerade parametrar.",
    "sc.forandring": "Förändring",
    "sc.poang": "poäng",
    "sc.skillnad_mellan_scenario_och_basfall": "Skillnad mellan scenario och basfall. Positivt = bättre överkomlighet.",
    "sc.shai_poang": "SHAI poäng",
    "sc.jamforelsetabell": "Jämförelsetabell",
    "sc.styrranta": "Styrränta (%)",
    "sc.realranta": "Realränta (%)",
    "sc.forklaring": "Förklaring",
    "sc.version_c_realversion_beraknas_som_text": """
    **Version C (realversion)** beräknas som:

    $$\\text{Affordability}_C = \\frac{\\text{Inkomst}}{\\text{Transaktionspris} \\times \\max(R - \\pi,\\; 0{,}5) / 100}$$

    Där:
    - **Inkomst** = median disponibel hushållsinkomst (SEK)
    - **Transaktionspris** = median transaktionspris för bostäder (SEK, SCB BO0501)
    - **R** = Riksbankens styrränta i procentenheter (årsgenomsnitt)
    - **π** = KPI-inflation i procentenheter (årsgenomsnitt)
    - **0,5** = golv (procentenheter) för att förhindra division med noll vid negativ realränta

    **Tolkning:** Högre värde = bättre bostadsöverkomlighet.

    **Scenariomekanik:**
    - Räntechock adderas till styrräntan (procentenheter)
    - Inkomsttillväxt multipliceras med inkomsten (relativ förändring)
    - Prischock multipliceras med transaktionspriset (relativ förändring)

    **Begränsning F15, inflationen (π) hålls konstant:**
    Scenariosimulatorn ändrar inte KPI-inflationen när räntan chockas. Det innebär att
    en räntehöjning på +3 pp tolkas som en ökning av realräntan med +3 pp, vilket inte
    stämmer om höjningen är ett svar på hög inflation (som i 2022–2023 då realräntan
    förblev låg trots tredubblade nominella räntor). Resultaten gäller nominell räntechock
    med oförändrad inflation.
    """,

    # ── Sida 06 — Metodologi ──────────────────────────────────────
    "mt.metodologi_och_kallor": "Metodologi och källor",
    "mt.teoretisk_grund_formler_datakallor_och": "Teoretisk grund, formler, datakällor och dokumenterade begränsningar",
    "mt.tre_perspektiv_pa_bostadsoverkomlighet": "Tre perspektiv på bostadsöverkomlighet",
    "mt.bostadsoverkomlighet_housing_affordability": """
    Bostadsöverkomlighet (*housing affordability*) beskriver förhållandet mellan ett hushålls
    betalningsförmåga och kostnaden för boende. Banker och tillsynsmyndigheter analyserar detta
    genom tre perspektiv:

    1. **Flödesöverkomlighet:** kan hushållet klara månadskostnaden?
    2. **Stocköverkomlighet:** kan hushållet samla ihop kontantinsatsen?
    3. **Risköverkomlighet:** vad händer under stressade förhållanden?

    SHAI implementerar alla tre genom formeltrippletten (A, B, C), kontantinsatsmotorn
    och scenariosimulatorn.
    """,
    "mt.2_variabler_och_datakallor": "2. Variabler och datakällor",
    "mt.10_variabler_fran_officiella_svenska_kallor": "10 variabler från officiella svenska källor",
    "mt.variabel_symbol_kalla_upplosning_frekvens": """
    | Variabel | Symbol | Källa | Upplösning | Frekvens | Täckning |
    |----------|--------|-------|------------|----------|----------|
    | Medianinkomst (sammanräknad förvärvsinkomst) | I | SCB HE0110 | Kommun, län, riket | Årlig | 2011–{income_max} |
    | **Transaktionspris småhus (medelvärde, SEK)** | **P_SEK** | **SCB BO0501B (BO0501C2)** | **Kommun, län** | **Årlig** | **1981–{price_max}** |
    | **Transaktionspris bostadsrätt (medelvärde, SEK)** | **P_BR** | **SCB BO0501C (FastprisBRFRegionAr, BO0501R7)** | **Län (21), riket** | **Årlig** | **2000–present** |
    | Fastighetsprisindex | P_idx | SCB BO0501A | Län (21), riket | Årlig | 1990–{price_index_max} |
    | Köpeskillingskoefficient (K/T, deskriptiv) | KT | SCB BO0501B (BO0501C4) | Kommun (312), län | Årlig | 1981–{kt_max} |
    | Styrränta | R | Riksbanken Swea | Riket | Dag → årssnitt | 2014–idag |
    | KPI (skuggindex) | π | SCB PR0101 | Riket | Månad → årssnitt | 1980–idag |
    | KPI årsförändring | π% | SCB PR0101 | Riket | Månad → årssnitt | 1981–idag |
    | Realränta | r* = R − π | Härledd | Riket | Årlig | 2014–idag |
    | Arbetslöshet | U | Kolada N03937 (Af) | Kommun, län, riket | Årlig | 2010–{unemployment_max} |
    | Befolkning | N | SCB BE0101 | Kommun, län, riket | Årlig | 1968–{population_max} |
    | Bostadsbyggande | H | SCB BO0101 | Kommun, län, riket | Årlig | 1975–{completions_max} |

    **Obs:** P_SEK (SCB BO0501C2) är *medelvärdet* (ej medianen) av köpeskillingen för permanenta
    småhus (Fastighetstyp 220). SHAI-formlerna A, B och C använder P_SEK (villapris) som
    primär prisvariabel (systemisk vy). P_BR (SCB BO0501C, bostadsrättspris) ingår i panelen
    och exponeras som valbar "Pristyp" på Sida 04 (Kontantinsats), så att
    förstagångsköpare i städer kan få en mer realistisk bild av kontantinsatskraven
    (typisk bostadsrätt i Stockholm ≈ 3,5 MSEK vs. villa ≈ 8,6 MSEK).
    **OBS:** SCB publicerar inga kommunspecifika bostadsrättspriser, enbart 21 län och riksnivå.
    Sida 04 byter automatiskt till länsnivå när Bostadsrätt väljs. Se F11 nedan.
    K/T används enbart som deskriptiv indikator. Den ingår inte i formeln.

    **Arbetslöshetsdefinition:** Öppet arbetslösa inskrivna vid Arbetsförmedlingen, 18–65 år,
    som andel av befolkningen 18–65 år. Detta är *inte* samma som AKU/ILO-arbetslöshet.
    """,
    "mt.mater_flodesoverkomlighet_hushallets_inkomst": """
    Mäter flödesöverkomlighet: hushållets inkomst relativt bostadens transaktionspris och aktuell ränta.
    Speglar traditionell bankbedömning. **Högre värde = bättre överkomlighet.**

    - **I(i,t)** = medianinkomst, kommun i, år t (SEK)
    - **P_SEK(i,t)** = medeltransaktionspris för permanenta småhus, SCB BO0501C2 (SEK)
    - **R(t)** = Riksbankens styrränta, årsgenomsnitt (som decimaltal)
    """,
    "mt.version_b_makrokomposit_tryckmatt": "### Version B: Makrokomposit (tryckmått)",
    "mt.sammansatt_riskindikator_som_viktar_pris": """
    Sammansatt riskindikator som viktar pris/inkomst, ränta, arbetslöshet och inflation.
    z-poäng beräknas över hela panelen. **Högre värde = högre risk.**

    **Obs (Begränsning F13):** R och π är nationella variabler. De varierar enbart med år, inte mellan kommuner.
    Inom ett enskilt år bidrar dessa 45 % av vikterna (0,25 + 0,20) enbart till ett additivt skifte och
    påverkar inte den kommunala rangordningen. Rankingen inom ett år drivs i praktiken av z(P_SEK/I) och z(U).
    """,
    "mt.justerar_for_inflation_genom_realrantan": """
    Justerar för inflation genom realräntan. Golvet 0,005 förhindrar division med noll
    vid negativa realräntor. Akademiskt förankrad. **Högre värde = bättre överkomlighet.**

    **Obs (Begränsning M4):** Åren 2020–2021 har negativ realränta; golvet binder och Version C
    reduceras till ett rent pris/inkomst-mått med en konstant faktor. Se Begränsningar F11–F15 nedan.
    """,
    "mt.formlerna_ger_ett_nivavarde_per_kommun_och": """
    Formlerna ger ett *nivåvärde* per kommun och år. För att kunna jämföra kommuner
    omvandlas nivån till en **z-poäng**, som i sin tur ger rang och riskklass. Två val styr
    den omvandlingen.

    **1. Fönster: inom år.** Varje års kommuner poängsätts mot just det årets nationella
    fördelning. Riskklassen är alltså ett uttalande om kommunens läge *relativt sina
    jämnåriga*, inte om Sveriges överkomlighet över tid.

    Undantag, medvetet: Version B:s egen konstruktion (z-poängen *inuti* formeln ovan)
    beräknas över hela panelen. B är ett makrotrycksmått, och det är just poolningen som gör
    att dess nivå kan bära en tidstrend. Panelmedelvärdet går från −0,37 (2015) till +0,86
    (2023) och följer ränteuppgången. Att normalisera B inom år skulle nolla den signalen
    varje år och ta bort det B är byggt för att mäta.

    **2. Transform: logaritm för A och C.** Version A och C är *kvoter* mellan positiva
    storheter, och är därför lognormalfördelade, inte normalfördelade. Z-poängen beräknas
    därför på `ln(värdet)`. Utan logaritmen förkastas normalitetsantagandet i samtliga år
    (p < 6·10⁻¹⁵); med logaritmen gör det inte det i något år (p = 0,34–0,83).

    Detta har betydelse eftersom klassgränserna nedan är kvartiler i en *normalfördelning*.
    På den otransformerade kvoten gav de en skev fördelning som ingen valt: cirka 19 / 51 / 30
    i stället för 25 / 50 / 25.

    Version B logaritmeras inte: den är en viktad *summa* av z-poäng och antar negativa
    värden, så logaritmen är odefinierad.

    Eftersom logaritmen är monoton påverkar transformen **inte rangordningen**: `rank` är
    identisk med och utan den. Endast z-poängen och, för 16 av {v0} kommuner, riskklassen ändras.

    **3. Riskklass.** Klassgränserna ligger vid ±0,67 standardavvikelser, kvartilerna i en
    normalfördelning:

    | z-poäng | Klass |
    |---|---|
    | ≤ −0,67 | Låg risk |
    | −0,67 … +0,67 | Medel risk |
    | > +0,67 | Hög risk |

    Orienteringen är gemensam för alla tre versionerna: **högre z = sämre överkomlighet**,
    rang 1 = bäst. Version A och C teckenvänds därför före klassificeringen, eftersom deras
    råvärde går åt motsatt håll.

    **Obs (Begränsning F16):** Eftersom gränserna är fasta kvantiler hamnar ungefär en fjärdedel
    av kommunerna i varje ytterklass *varje år, per konstruktion*. Det nationella **antalet**
    kommuner i en klass kan därför inte tolkas som en trend. Bara fördelningens form och
    enskilda kommuners förflyttning mellan klasser bär information.
    """,
    "mt.varfor_transaktionspris_i_sek_inte_k_t_eller": "### Varför transaktionspris i SEK, inte K/T eller prisindex?",
    "mt.tre_alternativa_prismatt_overvagdes": """
    Tre alternativa prismått övervägdes:

    - **Prisindex (1990=100):** Ett *tillväxtmått* som inte kan jämföras mellan regioner:
      alla kommuner startar på 100 oavsett absolut prisnivå. Kan inte rangordna.
    - **K/T-kvot (köpeskilling/taxeringsvärde):** Ett *relativt mått* som snedvrids av eftersläpande
      taxeringsvärden. Höga K/T i glesbygd speglar gamla taxeringsvärden, inte hög prisnivå. K/T
      finns kvar i panelen som beskrivande marknadsvariabel.
    - **Transaktionspris i SEK (BO0501C2):** Ett *absolut nivåmått* direkt jämförbart mellan kommuner.
      Ger korrekt rangordning (Stockholm dyrast, Norrbotten billigast).

    Formlerna A, B, C beräknas med **transaktionspriset i SEK**, inte K/T.
    SCB:s BO0501C2 innehåller *medelvärdet* (medelvärde, ej median) av köpeskillingen för
    permanenta småhus (Fastighetstyp 220). Se Begränsning F11 och F12 nedan.
    """,
    "mt.prophet_standard_i_granssnittet_bibliotek": """
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
    **Alla prognoser baseras på {v0} årliga observationer ({v1}).** Detta är en
    extremt kort tidsserie för statistisk prognos. Konfidensintervallen vidgas snabbt
    och prognoser bortom 3 år bör tolkas med stor försiktighet.

    **Horisont:** 6 årliga steg (2025–2030). Begränsad till max 8 steg.
    """,
    "mt.fore_2010_inget_formellt_krav_okt_2010": """
    <div style="position:relative;padding:20px 0;margin:16px 0;">
        <div style="position:absolute;top:40px;left:0;right:0;height:3px;background:{v0};"></div>

        <div style="display:flex;justify-content:space-between;position:relative;">
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:{v1};margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Före 2010</div>
                <div style="font-size:10px;color:{v2};">Inget formellt krav</div>
            </div>
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:{v3};margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Okt 2010</div>
                <div style="font-size:10px;color:{v4};">Bolånetak 85%</div>
            </div>
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:{v5};margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Jun 2016</div>
                <div style="font-size:10px;color:{v6};">Amorteringskrav 1.0</div>
            </div>
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:{v7};margin:32px auto 8px;"></div>
                <div style="font-size:11px;font-weight:700;">Mar 2018</div>
                <div style="font-size:10px;color:{v8};">Amorteringskrav 2.0</div>
            </div>
            <div style="text-align:center;z-index:1;">
                <div style="width:16px;height:16px;border-radius:50%;background:{v9};margin:32px auto 8px;border:2px solid {v10};"></div>
                <div style="font-size:11px;font-weight:700;">Apr 2026</div>
                <div style="font-size:10px;color:{v11};">Lättnader 2026</div>
            </div>
        </div>
    </div>
    """,
    "mt.regelverk_period_kontantinsats": """
    | Regelverk | Period | Kontantinsats | Amorteringskrav |
    |-----------|--------|---------------|-----------------|
    | Före 2010 | Till okt 2010 | Inget formellt minimum | Inget obligatoriskt |
    | Bolånetak | Okt 2010 – jun 2016 | Min 15% | Inget obligatoriskt |
    | Amorteringskrav 1.0 | Jun 2016 – mar 2018 | Min 15% | 2% om LTV>70%, 1% om LTV>50% |
    | Amorteringskrav 2.0 | Mar 2018 – mar 2026 | Min 15% | Ovan + 1% extra om LTI>4,5x |
    | Lättnad 2026 | Apr 2026 – nuvarande | Min 10% | 2% om LTV>70%, 1% om LTV>50% (LTI-krav slopat) |

    **Källa:** Finansinspektionen
    """,
    "mt.6_begransningar_f1f15": "6. Begränsningar (F1–F16)",
    "mt.id_begransning_atgard_f1_kommunal": """
    | ID | Begränsning | Åtgärd |
    |----|-------------|--------|
    | **F1** | Kommunal pristäckning: länets K/T används som proxy. 88% av panelen har kommunspecifik K/T. | Flagga `has_native_kt` i data. |
    | **F2** | Nationell styrränta appliceras på alla kommuner och län. | Dokumenterat. |
    | **F3** | Tre formler ger olika rangordning av kommuner. | Korsformelsjämförelse på Sida 02. |
    | **F4** | Prophet är svagt för årlig makrodata. | ARIMA-flik märkt "rekommenderad". |
    | **F5** | Kontantinsats är en stegfunktion, inte kontinuerlig. | Diskreta regimkort. |
    | **F6** | Lång horisont vilseleder. | Max 8 steg; varningstext. |
    | **F7** | SCB API-gränser (30 anrop/10 s, 150k celler/fråga). | All data cachad som parquet. |
    | **F8** | Översättning tappar nyanser i bankterminologi. | Ordlista i dokumentation. |
    | **F9** | Imputering av inkomstdata efter senaste publicerade år. | `is_imputed_income`-flagga; framskrivning med 3 % nominell tillväxt per år. Dessa år är inte längre valbara i årsväljaren, indexet stannar vid senaste kompletta år. |
    | **F10** | Arbetslöshetsdefinition (Af, inte AKU/ILO). | Fotnot på relevanta sidor. |
    | **F11** | SHAI-indexformlerna (A, B, C) beräknas fortfarande enbart på villapriser (SCB BO0501C2, Fastighetstyp 220), en systemisk vy, bevarad för metodologisk kontinuitet. Bostadsrättspriser (SCB BO0501C) ingår nu i panelen och exponeras som valbar Pristyp på Sida 04 (Kontantinsats). SCB publicerar bostadsrättspriser enbart på länsnivå (21 län), inga kommunspecifika data finns. Sida 04 byter automatiskt till länsnivå vid Bostadsrätt-val. | Pristyp-väljare + automatisk nivåbyte på Sida 04. |
    | **F12** | Styrräntan används direkt som bolåneränta. Faktisk bolåneränta ≈ styrränta + bankens marginal (ca 1,5–2,5 pp). Månadskostnad och affordability-formler är optimistiska. | Notering i Detaljer på Sida 04. |
    | **F13** | Version B: R och π är nationella variabler (samma för alla kommuner ett givet år). Z-poäng för dessa bär ingen kommunspecifik information inom ett enskilt år. 45% av vikterna diskriminerar enbart i tid, inte i rum. | Dokumenterat i formelbeskriving ovan. |
    | **F14** | Inkomst är individuell bruttoinkomst. Bostad köps typiskt av ett hushåll (par). Spartiden för singelhushåll är 2× hushållssiffran. | Notering under "År att spara" KPI på Sida 04. |
    | **F16** | Riskklassens gränser (±0,67 σ) är fasta kvantiler, så andelen kommuner per klass är nära konstant varje år per konstruktion. Antalet högriskkommuner kan inte bära en nationell trend. | Dokumenterat under "Normalisering" ovan; ingen förändringspil visas på antalet. |
    | **F15** | Scenariosimulatorn håller KPI-inflationen (π) konstant när räntan chockas. Realränteförändringen är därmed identisk med den nominella räntechochen. | Notering i Förklaring på Sida 05. |
    """,
    "mt.foljande_valideringskontroller_kors_innan": """
    Följande valideringskontroller körs innan publicering:

    1. **Nominell inkomst ökande:** Medianinkomst bör öka nominellt år för år (2011–{income_max}).
    2. **Real inkomst stabil:** Deflaterad inkomst bör vara ungefär stabil eller svagt ökande.
    3. **Stockholm i topp 5 sämst (Version C):** Verifierat med K/T-data.
    4. **Norrbotten i topp 5 bäst (Version A):** Verifierat.
    5. **K/T-intervall:** Alla K/T-värden mellan 1,0 och 4,0.
    6. **Prognosintervall vidgas:** Konfidensband vidgas monotont med horisont.

    Alla kontroller implementerade i `tests/test_validation.py`.
    """,
    "mt.scb_bo0501_fastighetspriser_och_lagfarter": """
    - **SCB BO0501** (Fastighetspriser och lagfarter, småhus): [scb.se/bo0501](https://www.scb.se/bo0501-en)
    - **SCB BO0501C** (Bostadsrättspriser, FastprisBRFRegionAr): [scb.se/bo0501](https://www.scb.se/bo0501)
    - **SCB HE0110** (Hushållens ekonomi): [scb.se/he0110](https://www.scb.se/he0110-en)
    - **SCB BE0101** (Befolkningsstatistik): [scb.se/be0101](https://www.scb.se/be0101)
    - **SCB PR0101** (Konsumentprisindex): [scb.se/pr0101](https://www.scb.se/pr0101)
    - **SCB BO0101** (Bostadsbyggande): [scb.se/bo0101](https://www.scb.se/bo0101)
    - **Kolada API v3** (Kommunal statistik): [kolada.se](https://www.kolada.se/)
    - **Kolada N03937** (Arbetslöshet, Arbetsförmedlingen): [api.kolada.se/v3/](https://api.kolada.se/v3/)
    - **Riksbanken Swea API** (Räntor): [riksbank.se](https://www.riksbank.se/en-gb/statistics/interest-rates-and-exchange-rates/)
    - **Finansinspektionen** (Amorteringskrav): [fi.se](https://www.fi.se/en/our-registers/the-amortisation-requirement/)
    - **SCB PxWeb API v1**: [scb.se/api](https://www.scb.se/api/)
    """,
    "mt.shai_v_v0_metodologi_baserad_pa_methodology": "SHAI v{v0}, metodologi baserad på METHODOLOGY.md",

}
