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
    "mt.expander_4_projektion_villkorad": "5. Projektion (villkorad)",
    "mt.expander_5_kontantinsats_regimhistorik": "6. Kontantinsats: regelverk över tid",
    "mt.expander_7_datavalidering": "8. Datavalidering",
    "mt.expander_8_referenser": "9. Referenser",
    "lj.lan": "Län",
    "lj.varde": "Snitt av kommunerna",
    "lj.lansniva": "Länsnivå",
    "lj.ranking": "RANKING",
    "lj.lansranking_v0": "Länsranking {v0}",
    "lj.ranking_subtitle_v0": "{v0} · #1 = bäst överkomlighet",
    # ── Chrome, glossary, explanations, expanders, table headers ─────────
    "ui.forklaring_av_begrepp": "Förklaring av begrepp",
    "ui.data_uppdaterad_v0": "Data uppdaterad {v0}",
    "glossary.zpoang.term": "Z-poäng",
    "glossary.zpoang.def": "Avstånd från årets genomsnitt i standardavvikelser, på logaritmisk skala. Beräknas inom varje år, så en kommuns z-poäng säger var den står jämfört med andra kommuner samma år, inte om Sverige som helhet blivit dyrare.",
    "glossary.riskklass.term": "Riskklass",
    "glossary.riskklass.def": "Låg, medel eller hög, satt vid ±0,67 standardavvikelser från årets genomsnitt. Eftersom gränserna mäts mot samma års fördelning hamnar nästan samma andel i varje klass varje år: ungefär en fjärdedel låg, hälften medel och knappt 30 % hög. Antalet i en klass kan därför inte läsas som en trend.",
    "glossary.version_c.term": "Version C",
    "glossary.version_c.def": "Den rekommenderade formeln: hushållets årliga boendekostnad för ett typiskt småhuslån, alltså ränta efter ränteavdrag plus amortering, i procent av två medianinkomster. Högre värde betyder sämre överkomlighet.",
    "glossary.rang.term": "Rang",
    "glossary.rang.def": "Placering inom året, där rang 1 är bäst överkomlighet. Rangen är densamma oavsett logaritmering, eftersom transformen är monoton.",
    "glossary.kt_kvot.term": "K/T-kvot",
    "glossary.kt_kvot.def": "Köpeskilling delat med taxeringsvärde. Deskriptiv. Den ingår inte i någon av formlerna; transaktionspriset i SEK används.",
    "rv.forklaring_kpi": "Talen ovan beskriver {v0} kommuner för {v1}. Genomsnittligt SHAI är en kostnadsandel i procent och kan jämföras mellan år, men den rymmer räntan, amorteringskravet och priserna på en gång. Panelen nedan delar upp förändringen i kostnad per lånad krona och pris mot inkomst. Antalet högriskkommuner är en relativ position inom året och kan inte jämföras mellan år alls.",
    "rv.forklaring_karta": "Färgskalan går från årets lägsta till årets högsta z-poäng, med brytpunkter vid kvartilerna. Skalan sätts om varje år, så en färg betyder ”bland årets mest ansträngda”, inte ett fast pris.",
    "rv.forklaring_histogram": "Fördelningen visar hur {v0} kommuner ligger i förhållande till varandra detta år. Eftersom z-poängen är centrerad inom året ligger tyngdpunkten alltid nära noll. Formen säger något, läget gör det inte.",
    "rv.forklaring_tabell": "Topplistorna är sorterade på Version C inom {v0}. De visar ytterkanterna av årets fördelning, inte kommuner som förändrats mest över tid.",
    "landing.forklaring_statistik": "Indexet täcker {v0} kommuner över {v1} år. Perioden slutar {v2} eftersom medianinkomsten publiceras med ett års fördröjning; pris och räntor sträcker sig längre.",
    "lj.forklaring_kpi": "Länsvärden är ovägda medelvärden av kommunerna i länet. Ett län med många små kommuner väger därför lika tungt som ett med få stora. Kolumnen Länsnivå visar länets värde räknat på länets egen medianinkomst och medelpris, samma tal som Sida 03 och Sida 05 visar.",
    "rv.om_kartan": "Om kartan",
    "rv.om_rankningstabellerna": "Om rankningstabellerna",
    "lj.om_lansjamforelsen": "Om länsjämförelsen",
    "lj.om_lansjamforelsen_text": "Varje län visas som ett ovägt medelvärde av sina kommuner, så Gotland (en kommun) väger lika tungt som Västra Götaland (49). Jämförelsen säger något om länens *typiska* kommun, inte om var flest människor bor. Kurvorna är kostnadsandelar i procent av inkomsten och kan jämföras mellan år. Panelen om ränta och pris visar hur mycket av en förändring som kom från finansieringen och hur mycket från priserna. Rangordningen inom ett år bygger på z-poäng och kan inte jämföras mellan år alls.",
    "kd.komp_rubrik": "Vad har drivit förändringen?",
    "kd.komp_inkomst": "Medianinkomst",
    "kd.komp_pris": "Medelpris småhus",
    "kd.komp_kostnadsranta": "Kostnad per lånad krona",
    "kd.komp_uppdelning": "Från {v1} till {v2} ändrades SHAI för {v0} med **{v3} %**. Inkomsten bidrog med {v4} %, priset med {v5} % och kostnaden per lånad krona med {v6} %. Bidragen multipliceras, och ett negativt bidrag sänkte kostnaden. Störst påverkan hade **{v7}**.",
    "kd.om_komponenterna": "Om komponentuppdelningen",
    "kd.om_komponenterna_text": "Diagrammen visar de tre storheter som Version C bygger på: medianinkomst, medelpris för småhus och kostnaden per lånad krona, det vill säga bolåneräntan efter 30 % ränteavdrag plus den amortering som gällde året. Uppdelningen är exakt: indexets förändring är produkten av de tre bidragen, så procentsatserna multipliceras i stället för att adderas. Kostnaden per lånad krona är nationell och samma för alla kommuner. Hoppet 2016–2017 är amorteringskravet, som infördes 1 juni 2016. Amortering är en utbetalning men bygger samtidigt upp hushållets egna kapital, så den är en kassaflödesbörda snarare än en förbrukad kostnad.",
    "rv.kommun": "Kommun",
    "rv.z_poang": "Z-poäng",
    "rv.shai": "SHAI",
    "rv.risk": "Risk",
    "rv.ranking": "RANKING",

    # ── Landing page (app.py) ─────────────────────────────────────
    "landing.shai_bostadsekonomisk_hallbarhet": "SHAI · Bostadsekonomisk hållbarhet",
    "landing.shai_bostadsekonomisk_hallbarhet_data_scb": "SHAI · Bostadsekonomisk hållbarhet. Källor och metod: se Metodologi och källor.",
    "landing.v0_ar_v_v1": "{v0} år  ·  v{v1}",
    "landing.lan": "Län",
    "landing.jamforda": "jämförda",
    "landing.riksoversikt": "Riksöversikt",
    "landing.nationell_overblick_med_karta_histogram_och": "Nationell överblick med karta, histogram och rankingtabeller för {v0} kommuner.",
    "landing.lan_jamforelse": "Länsjämförelse",
    "landing.21_lan_jamforda_under_tre_ekonometriska": "21 län jämförda formel för formel, med den version som kan rangordna annorlunda i egen flik.",
    "landing.jamfor_insatskrav_under_fem_regulatoriska": "Kontantinsats, spartid och månadskostnad under fem regelverk, från före bolånetaket till i dag.",
    "landing.stresstesta_med_ranta_inkomst_och": "Stresstesta med ändrad bolåneränta, inkomst och pris, per län och för hela riket.",
    "landing.vikter_version_b": "Vikterna i Version B (makroversion). Version A och C är kostnadsandelar utan vikter: lånets årliga kostnad delat med hushållets inkomst.",
    "landing.kommun_djupanalys_beskrivning": "Utveckling per kommun, och en villkorad projektion för kommunens län.",
    "kd.undertitel": "Historisk analys per kommun och villkorad projektion för länet",
    "landing.formler_datakallor_begransningar_f1f10_och": "Formler, datakällor, begränsningar (F1–F18) och validering.",

    # ── Sida 01 — Riksöversikt ────────────────────────────────────
    "rv.shai_riksoversikt": "SHAI · Riksöversikt",
    "rv.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "rv.inga_data_tillgangliga_for_den_valda": "Inga data tillgängliga för den valda perioden.",
    "rv.sida_01_nationell_oversikt": "Sida 01 · Nationell översikt",
    "rv.riksoversikt": "Riksöversikt",
    "rv.strukturell_bostadsekonomisk_hallbarhet_i": "Strukturell bostadsekonomisk hållbarhet i Sveriges {v0} kommuner · {v1}",
    "rv.procent_av_inkomsten": "% av inkomsten",
    "rv.genomsnittlig_version_c_poang_rakvot_inkomst": "Genomsnittlig Version C för alla {v0} kommuner: årlig ränta efter avdrag plus amortering på ett lån på 85 % av medelpriset, i procent av två medianinkomster. Högre = sämre överkomlighet.",
    "rv.hogrisk_kommuner": "Högriskkommuner",
    "rv.av_v0_relativ_position_v1": "av {v0}, relativ position {v1}",
    "rv.forsta_aret_ingen_jamforelse": "första året, ingen jämförelse",
    "rv.tabell_filtrerad_v0_v1": "{v0} · filter: {v1}",
    "rv.antal_kommuner_med_z_poang_0_67": "Antal kommuner med z-poäng > 0,67 standardavvikelser (riskklass Hög). Riskklassen är en relativ position inom året: kommunerna jämförs med varandra i just detta år, inte med ett fast gränsvärde. Antalet i klassen är nästan detsamma varje år, så det kan inte visa om Sverige som helhet blivit mer eller mindre överkomligt. Det svaret står i genomsnittligt SHAI och i panelen om ränta och pris nedan, som delar upp förändringen i finansiering och priser.",
    "rv.genomsnittlig_kopeskillingskoefficient_k_t": "Genomsnittlig köpeskillingskoefficient (K/T): köpeskilling delat med taxeringsvärde, vanligen mellan 1 och 3. Högre = dyrare i förhållande till taxeringsvärdet. Obs: K/T ingår ej i formlerna; transaktionspriset i SEK används i stället.",
    "rv.befolkningsforandring": "Befolkningsförändring",
    "rv.procentuell_befolkningsforandring_jamfort": "Procentuell befolkningsförändring jämfört med föregående år.",
    "rv.geografisk_fordelning": "Geografisk fördelning",
    "rv.kartlegend_rubrik": "SHAI-poäng (z) · lägre = bättre överkomlighet",
    "rv.fargskala_gron_lag_risk_z_0_67_gul_medel": "Färgskala: Grön = låg risk, röd = hög risk. Färgerna går gradvis, med brytpunkter vid årets kvartiler, nära riskklassernas gränser (z = ±0,67).",
    "rv.ingen_data_tillganglig_for_kartvisning": "Ingen data tillgänglig för kartvisning.",
    "rv.varje_kommun_visas_som_ett_ifyllt_polygon": "Varje kommun färgas efter sin z-poäng under Version C: grönt = bättre, rött = sämre överkomlighet. Håll musen över en kommun för detaljer. Kommunnamnen visas när du zoomar in ett steg.",
    "rv.fordelning_av_shai_poang": "Fördelning av SHAI-poäng",
    "rv.z_poang_standardavvikelser_pa_logaritmisk": "Z-poäng = avstånd från årets genomsnitt i standardavvikelser, på logaritmisk skala. Lägre z = bättre överkomlighet.",
    "rv.riskklass_hog": "Hög",
    "rv.riskklass_medel": "Medel",
    "rv.riskklass_lag": "Låg",
    "rv.shai_poang_z_poang": "SHAI-poäng (z-poäng)",
    "rv.om_fordelningsgrafen": "Om fördelningsgrafen",
    "rv.histogrammet_visar_hur_shai_poangen_z_poang": "Histogrammet visar hur SHAI-poängen (z-poäng) fördelar sig bland kommunerna. Skalan är vänd så att ett lägre z betyder bättre överkomlighet: grön stapel = låg risk, gul = medel, röd = hög risk. Färgen kommer från riskklassen i datafilen, inte från en gräns som räknas om här. Den streckade linjen visar medianen. Klassgränserna placerar ungefär en fjärdedel av kommunerna i låg risk och knappt 30 % i hög risk varje år, så fördelningens form säger mer än antalet i en klass.",
        "rv.samst_overkomlighet_topp_15": "Sämst överkomlighet (topp 15)",
    "rv.bast_overkomlighet_topp_15": "Bäst överkomlighet (topp 15)",
    "rv.tabellerna_visar_de_15_kommuner_med_samst": "Tabellerna visar de 15 kommuner med sämst respektive bäst överkomlighet enligt Version C (kassaflödesversion). Z-poängen anger hur långt kommunen ligger från årets genomsnitt, i standardavvikelser på logaritmisk skala.",

    # ── Sida 02 — Län jämförelse ──────────────────────────────────
    "lj.shai_lan_jamforelse": "SHAI · Länsjämförelse",
    "lj.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "lj.sida_02_regional_jamforelse": "Sida 02 · Regional jämförelse",
    "lj.lan_jamforelse": "Länsjämförelse",
    "lj.21_lan_jamforda_under_tre_bostadsekonomiska": "21 län under de två formler som kan rangordna olika",
    "lj.den_enklaste_versionen_mater_hushallets": "Bankens bruttosyn på samma lån som C: bara räntan, före ränteavdrag och utan amortering, i procent av två medianinkomster. Högre värde = dyrare.",
    "lj.en_sammansatt_riskindikator_som_viktar_fyra": "En sammansatt riskindikator som viktar fyra makrovariabler: pris/inkomst, bolåneränta, arbetslöshet och KPIF-inflation. Speglar ett makrotillsynsperspektiv. Högre värde = högre risk.",
    "lj.arbetsloshet_avser_oppet_arbetslosa_enligt": "Arbetslöshet avser öppet arbetslösa enligt Arbetsförmedlingen (18–65 år, 18–64 år till och med 2022), inte AKU. Obs: r och π är nationella variabler. De bidrar ej till kommunal rangordning inom ett enskilt år (se Begränsning F13). π är KPIF, inte KPI: KPI innehåller hushållens räntekostnader och stiger därför av sig själv när räntan höjs.",
    "lj.den_rekommenderade_versionen_justerar_for": "Den rekommenderade versionen: årlig ränta efter 30 % ränteavdrag plus den amortering som gällde året, på ett lån på 85 % av medelpriset, i procent av två medianinkomster. r är snitträntan på nya bolån över alla bindningstider och a amorteringskravet. Högre värde = dyrare.",
    "lj.att_olika_formler_rangordnar_lanen_olika_ar": "Att olika formler rangordnar länen olika är förväntat och inte ett fel. De mäter olika ekonomiska perspektiv.",
    "lj.v0_ar_x_varde_y_2f": "<b>{v0}</b><br>År: %{{x}}<br>Värde: %{{y:,.2f}}<extra></extra>",
    "lj.lansutveckling": "Länsutveckling",
    "lj.ar": "År",
    "lj.indexvarde": "Indexvärde (z-poäng mot fast referens)",
    "lj.indexvarde_log": "% av inkomsten (logaritmisk skala)",
        "lj.valj_lan": "Välj län att visa",
    "lj.inga_lan_valda": "Inga län valda. Välj minst ett län ovan för att visa diagrammet.",
    "lj.v0_av_v1_lan_visas": "{v0} av {v1} län visas. Övriga ritas som ljusgrå bakgrund så att spridningen fortfarande syns.",
    "lj.formel_och_definition": "Formel och definition",
    "lj.darfor_ingen_a_flik": """
    **Därför har Bankversion (A) ingen egen flik.** Den kan inte rangordna
    annorlunda än C, så en tredje flik hade visat samma ordning med andra tal.
    Rangkorrelationen mellan A och C är 1,0000 varje år. Det A faktiskt visar är
    räntebördan utan ränteavdrag och amortering, alltså bankens bruttosyn, inte
    en andra åsikt om vilka län som är ansträngda. Formeln står här för den som
    vill se den:
    
    """,
    "lj.mater": "Mäter",
    "lj.riktning": "Riktning",
    "lj.riktning_hogre_dyrare": "Högre = dyrare",
    "lj.riktning_hogre_samre": "Högre = högre risk",
    "lj.vad_a_mater": "Räntan på lånet före avdrag, mot inkomsten. Bankens bruttosyn.",
    "lj.vad_b_mater": "Sammanvägt makrotryck: pris/inkomst, bolåneränta, arbetslöshet och KPIF-inflation.",
    "lj.vad_c_mater": "Hushållets utbetalning: ränta efter avdrag plus amortering, mot inkomsten.",
    "lj.versionsskillnader_text": """
    Tre formler mäter tre olika saker, och skillnaderna är inte godtyckliga.

    **A och C rangordnar länen exakt lika.** Det är inte en tillfällighet utan
    matematik: bolåneräntan och amorteringskravet är nationella och lika för alla
    län ett givet år, så A och C skiljer sig med en konstant faktor som
    z-poängen räknar bort. Det de skiljer sig i är **nivå**, inte ordning. Hur
    stor den nivåskillnaden är för det valda året, och vad den består av, står
    längst ned i det här avsnittet.

    **B är den enda som kan rangordna annorlunda.** Den väger in arbetslöshet,
    som A och C inte gör alls, och dess z-poäng poolas över hela panelen i
    stället för inom år. Därför kan B bära en tidstrend av ett annat slag än A
    och C.

    **Alla tre pekar åt samma håll.** A och C är kostnadsandelar och B är ett
    riskmått, och för alla tre betyder ett högre värde sämre överkomlighet.
    Rangordningen sorteras därför så att plats 1 är bäst i varje flik.
    
    """,
    "lj.vilken_version_styr": "Vilken version styr sajten?",
    "lj.vilken_version_styr_underrubrik": "Version C driver kartan och sidorna. B är den enda formeln som kan rangordna annorlunda; A står för nivåskillnaden och förklaras i jämförelseavsnittet ovan.",
    "lj.robusthet": "ROBUSTHET",
    "lj.version": "Version",
    "lj.kommun": "Kommun",
    "lj.hog_risk": "Hög risk",
    "lj.medel_risk": "Medel",
    "lj.lag_risk": "Låg risk",
    "lj.version_a_kort": "Bankversion (A)",
    "lj.version_b_kort": "Makroversion (B)",
    "lj.version_c_kort": "Kassaflödesversion (C)",
    "lj.flik_c": "Kassaflödesversion",
    "lj.flik_b": "Makroversion",
    "lj.rangskillnad": "Rangskillnad",
    "lj.antal_kommuner_per_riskklass_v0": "Antal kommuner per riskklass, {v0}",
    "lj.storst_avstand_mellan_b_och_c": "Kommunerna där B och C är mest oense",
    "lj.c_driver_sajten": "**Version C är den som räknas.** Kartan, riskklasserna, KPI-raden, projektionen och scenariosimulatorn läser alla C. B står här för att svara på en rimlig invändning: att en kommuns placering bara är en effekt av vilken formel någon råkade välja.",
    "lj.b_ar_den_enda_som_kan_vara_oense": "**B är den enda formeln som kan vara oense med C**, och den är det för {v0} av {v1} kommuner ({v2} %). Det är den siffran som säger något om robusthet. **Bankversion (A) har ingen rad i tabellen:** den rangordnar exakt som C varje år, av matematiska skäl: bolåneräntan och amorteringskravet är nationella och lika för alla kommuner ett givet år, så A och C skiljer sig med en konstant faktor som z-poängen räknar bort. En rad för A hade upprepat C:s rad och sett ut som ett medhåll. Vad den konstanta faktorn består av står under *Varför skiljer sig versionerna åt?* ovan.",
    # The A-to-C factor, derived from the selected year by
    # `interpret.explain_cost_adjustment`. One reading in every year: what the
    # interest deduction and amortisation do to gross interest. It replaced five
    # sentences for the old "inflation adjustment", which meant four different
    # things depending on which rate floor bound.
    "lj.kostnadsjusteringen_ar_v0": """
    **Kassaflödesversionen är {v0}× bankversionen år {v1}.** Bankversion (A)
    räknar räntan på lånet, {v2} %. Kassaflödesversion (C) drar av 30 %
    ränteavdrag, så räntan blir {v3} %, och lägger till amorteringen, {v4} % av
    lånet per år. Varje kommuns värde multipliceras med samma faktor, så
    ordningen ändras inte, bara nivån.
    """,
    "lj.skillnaden_mellan_a_och_c_varierar": """
    **Skillnaden mellan A och C varierar mellan kommunerna år {v1}.** Den ska vara
    en nationell konstant: bolåneräntan och amorteringskravet är lika för alla
    kommuner ett givet år. Medianen är {v0}×, men spridningen är {v2}, så ingen
    enskild siffra beskriver året. Det är ett datafel och inte ett ekonomiskt
    resultat.
    
    """,
    "lj.varfor_skiljer_sig_versionerna_at": "Varför skiljer sig versionerna åt?",
    "lj.topp_5_och_botten_5_lan_per_flik": "Topp 5 och botten 5 län under Kassaflödesversion (C) och Makroversion (B). Bankversion (A) saknas med flit: den rangordnar exakt som C, så en tredje kolumn hade upprepat samma ordning med andra tal.",
    "lj.samst_overkomlighet": "*Sämst överkomlighet:*",
    "lj.bast_overkomlighet": "*Bäst överkomlighet:*",

    # ── The rate-and-price panel (src/ui/cost_panel.py, sidorna 01, 02, 06) ──
    # Collapsed on every page that opens it. Version C is a cost share, and the
    # national mean factors exactly into the cost per krona borrowed and the
    # mean price-to-income ratio. The panel shows both per year, so a reader can
    # see whether a move in the index came from financing or from prices. Every
    # figure is derived from the artifact by `agreement.cost_history`.
    "mt.kostnadspanelen_kunde_inte_laddas": "Panelen om ränta och pris kunde inte läsas från dataartefakten: {v0}",
    "kp.rubrik": "Ränta, amortering och pris år för år",
    "kp.inledning": """
    Kassaflödesversion (C) är årets kostnad för ett lån på {v0} % av medelpriset,
    i procent av {v1} medianinkomster. Kostnaden per lånad krona är bolåneräntan
    efter {v2} % ränteavdrag plus amorteringen som gällde året. Den är nationell,
    så snittindexet delar sig exakt i kostnad per lånad krona och pris mot inkomst.
    """,
    "kp.ar": "År",
    "kp.bolaneranta": "Bolåneränta",
    "kp.amortering": "Amortering",
    "kp.kostnad_per_krona": "Kostnad per lånad krona",
    "kp.faktor": "C/A",
    "kp.snittindex": "Snitt-SHAI",
    "kp.pris_inkomst": "Pris/inkomst",
    "kp.vald_rad": "Sidan visar {v0}. Bolåneränta: snitt för nya bolån över alla bindningstider (SCB), årsgenomsnitt i procent. Amortering och kostnad per lånad krona i procent av lånet per år. Snitt-SHAI i procent av inkomsten. Pris/inkomst i antal medianinkomster. C/A = hur många gånger större Version C är än Version A samma år.",
    "kp.svaret": """
    **Frågan "har bostäderna blivit dyrare i förhållande till inkomsterna?"
    besvaras av kolumnen Pris/inkomst.** Den är indexet med räntan och
    amorteringskravet bortdividerade. Ett småhus kostade i genomsnitt {v0}
    medianinkomster år {v2} och {v1} år {v3}, alltså {v4}.
    """,
    "kp.uppdelning": """
    **{v0} till {v1}:** snittindex {v2}, varav kostnad per lånad krona {v3} och
    pris mot inkomst {v4}. Delarna multipliceras, de adderas inte, och
    tillsammans förklarar de hela förändringen.
    """,
    "kp.forbehall": "Pris/inkomst är fri från formelns ränteterm, inte från räntans effekt på ekonomin: bostadspriser reagerar på räntan, så en räntecykel når kolumnen via priset.",
    "kp.slutsats": """
    **Snittindexet kan jämföras mellan år, men läs det tillsammans med
    kolumnerna.** Hoppet 2016–2017 är amorteringskravet, som infördes 1 juni
    2016: det höjer utbetalningen men bygger samtidigt eget kapital, så det är en
    kassaflödesbörda och inte en förbrukad kostnad. Version A, som bara räknar
    räntan, visar räntebördan utan amorteringen. Rangordningen inom ett år
    påverkas inte, eftersom kostnaden per lånad krona är lika för alla kommuner.
    """,

    # ── Sida 03 — Kommun djupanalys ───────────────────────────────
    "kd.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "kd.valj_kommun": "Välj kommun",
    "kd.inga_data_tillgangliga_for_den_valda": "Inga data tillgängliga för den valda kommunen.",
    "kd.procent_av_inkomsten": "% av inkomsten",
    "kd.kassaflodesversion_tooltip": "Kassaflödesversion: årlig ränta efter 30 % ränteavdrag plus amortering, på ett lån på 85 % av medelpriset, i procent av två medianinkomster. Högre = dyrare.",
    "kd.sammanraknad_forvarvsinkomst_medelvarde_per": "Medianinkomst: sammanräknad förvärvsinkomst per person, 20 år och äldre, före skatt. Individuell inkomst, inte hushållsinkomst.",
    "kd.kopeskillingskoefficient_kopeskilling": "Köpeskillingskoefficient: köpeskilling / taxeringsvärde. Speglar relativ prisnivå. Obs: K/T ingår ej i SHAI-formeln. Transaktionspriset i SEK används i stället.",
    "kd.serie_kommunen": "Kommunen",
    "kd.serie_lanet": "Länet",
    "kd.titel": "Kommunanalys",
    "kd.eyebrow": "Sida 03 · Kommunanalys",
    "kd.projektion_rubrik": "Projektion för {v0}",
    "kd.projektion_underrubrik": "Tre antaganden om bolåneräntan",
    "kd.projektion_tagg": "PROJEKTION",
    "kd.scenario_lag": "Lägsta nivån, {v0} %",
    "kd.scenario_dagens": "Nivå {v1}, {v0} %",
    "kd.scenario_hog": "Stress, {v0} %",
    "kd.projektion_y_axel": "SHAI, % av inkomsten",
    "kd.projektion_hover": "<b>%{x}</b><br>SHAI %{y:,.1f} % av inkomsten<extra>%{fullData.name}</extra>",
    "kd.lanet_hover": "<b>%{x}</b><br>SHAI %{y:,.1f} % av inkomsten<extra>Länet</extra>",
    "kd.projektion_antaganden": "Antaganden: inkomst +{v0} % och pris +{v1} % per år, räknat från {v2}, det sista år indexet kan beräknas. Priset skrivs fram även för år där SCB redan publicerat ett pris, eftersom inkomsten för samma år ännu saknas.",
    "kd.projektion_forklaring": "En projektion, inte en förutsägelse. De tre linjerna framåt visar länets index under var sitt antaget ränteläge. Välj själv vilket som är rimligast. Länets linje räknas på länets egen medianinkomst och medelpris, inte som medelvärdet av kommunerna på Sida 02, och kan därför skilja sig kraftigt från länsvärdet där.",
    "kd.projektion_mer_rubrik": "Varför tre antaganden i stället för en förutsägelse?",
    "kd.projektion_mer_text": "Bolåneräntan står för den största delen av indexets förändringar mellan år: sedan amorteringskravet trädde i kraft för ungefär 60 procent av variansen, mot 40 för priset. Den är ett utfall av penningpolitik och bankernas prissättning snarare än en statistisk process. Att extrapolera den från elva årsvärden vore att gissa Riksbankens politik sex år fram. Därför gissar sidan inte: den visar vad indexet blir under tre uttalade räntor, och du väljer vilken som är rimlig. Den låga är den lägsta årsnivån i indexperioden, den mellersta det senaste indexåret och den höga en stressnivå på 6 %, över toppen 2008 och under den kalkylränta på omkring 7 % som bankerna prövar nya låntagare mot. Version C är linjär i räntan, så linjerna ligger lika långt isär varje år. Inkomst och pris skrivs fram med fasta procentsatser; ingenting är modellanpassat. Amorteringen hålls på 2 % och lånet på 85 % av priset även efter april 2026, då bolånetaket höjdes till 90 %, så att åren går att jämföra.",
    "kd.bolaneranta": "Bolåneränta",
    "kd.bolaneranta_tooltip": "Snitträntan på nya bolån till hushåll över alla bindningstider (SCB), årsgenomsnitt. Nationell: samma värde för alla kommuner (Begränsning F2 och F12).",
    "kd.ar": "År",

    # ── Sida 04 — Kontantinsats ───────────────────────────────────
    "ki.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "ki.inga_data_tillgangliga_for_v0_valj_ett_ar": "Inga data tillgängliga för {v0}. Välj ett år med data: {v1}.",
    "ki.obs_priserna_avser_smahus_villor_scb": "**Obs:** Bostadsrättspriser saknas för valt år, så sidan visar bara småhus (villor). I storstäder är bostadsrätter ofta billigare än villor, så kontantinsats och spartid blir högre än för en typisk lägenhet. Se F11 i Metodologi.",
    "ki.valj_pristyp_bostadsrattspriser_scb_bo0501c": "**Pristyp:** Småhus visas per kommun ({v0} st), bostadsrätt per län (21 st), eftersom bostadsrättspriser bara publiceras på länsnivå.",
    "ki.valj_analysenhet": "Välj analysenhet",
    "ki.region_pristyp_hushallstyp_och": "Region, pristyp, hushållstyp och sparandeantagande",
    "ki.smahus_villa": "Småhus (villa)",
    "ki.bostadsratt": "Bostadsrätt",
    "ki.smahus_scb_bo0501c2_fastighetstyp_220": "Småhus: medelpris för villor, per kommun. Bostadsrätt: medelpris per bostadsrätt, per län.",
    "ki.stockholms_lan": "Stockholms län",
    "ki.valj_lan": "Välj län",
    "ki.valj_kommun": "Välj kommun",
    "ki.hushallstyp": "Hushållstyp",
    "ki.singelhushall": "Singelhushåll",
    "ki.par_2_inkomster": "Par (2 inkomster)",
    "ki.singelhushall_en_individuell_inkomst_par": "Singelhushåll: en medianinkomst. Par: två medianinkomster, vilket halverar spartiden och skuldkvoten. Båda är hushåll av en viss form, inte genomsnittet av alla hushåll i kommunen.",
    "ki.andel_av_bruttoinkomsten_som_sparas_arligen": "Andel av bruttoinkomsten som sparas varje år. Avgör hur lång tid det tar att spara ihop insatsen.",
    "ki.avancerade_installningar_rantepaslag": "Avancerade inställningar: räntepåslag",
    "ki.riksbankens_styrranta_anvands_som_bas": "Sidan räknar på ett rörligt lån (bundet högst tre månader): Riksbankens styrränta plus bankens påslag. Det är ett medvetet val, eftersom ett rörligt lån följer en ränteändring direkt. Indexet på övriga sidor använder i stället snitträntan på nya bolån över alla bindningstider, den ränta nya låntagare faktiskt avtalade (Begränsning F12).",
    "ki.bankens_rantepaslag_pp_ovan_styrrantan": "Bankens räntepåslag (pp ovan styrräntan)",
    "ki.faktisk_bolaneranta_styrranta_rantepaslag_0": "Bolåneräntan är ungefär styrräntan plus bankens påslag. Sedan 2014 har påslaget för nya rörliga bolån legat mellan 0,8 och 2,1 procentenheter: högst under åren med minusränta, lägst 2023–2024. 0 = enbart styrränta.",
    "ki.berakningsfel": "Beräkningen kunde inte göras för den valda regionen och året, eftersom indata saknas eller är ogiltiga.",
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
    "ki.bostadsratt_v0_scb_bo0501c": "Bostadsrätt i {v0}",
    "ki.bostadsrattspris_saknas_for_v0_smahuspriset": "Bostadsrättspris saknas för {v0}. Småhuspriset används som fallback.",
    "ki.smahus_fallback": "Småhus (fallback)",
    "ki.smahus_scb_bo0501c2": "Småhus",
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
    "ki.tolk_spartid": "Att spara ihop kontantinsatsen tar {v0} år vid {v1} % sparkvot, alltså {v2} SEK per år. Sparkvoten räknas på bruttoinkomsten, så det som faktiskt kan sparas efter skatt är normalt lägre och tiden därmed längre.",
    "ki.tolk_lattnad_avvagning": "Lättnaden 2026 sänker kontantinsatsen med {v0} SEK jämfört med det tidigare regelverket, men höjer månadskostnaden med {v1} SEK. Lägre tröskel in, högre kostnad att bo kvar: en mindre insats betyder ett större lån.",
    "ki.tolk_lattnad_battre": "Lättnaden 2026 sänker både kontantinsatsen, med {v0} SEK, och månadskostnaden, med {v1} SEK, jämfört med det tidigare regelverket.",
    "ki.tolk_singel_antagande": "Beräkningen utgår från en inkomst. De flesta bostadsköp i Sverige görs av två personer tillsammans. Välj Par ovan för att se hur siffrorna förändras.",
    # Affordability gap chart (sida 04).
    "ki.insikt_rubrik": "Nyckelinsikt",
    "ki.insikt_underrubrik": "Vad dagens regler betyder för hushållet, och vad som ändrades",
    "ki.insikt_idag": "För ett {v0} i {v1} krävs under dagens regler (Lättnad 2026) **{v2} SEK** i kontantinsats. Det tar **{v3} år** att spara ihop om {v4} % av bruttoinkomsten sparas varje år.",
    "ki.insikt_betalning": "Månadsbetalningen blir **{v0} SEK**: {v1} SEK i ränta ({v2} %) och {v3} SEK i amortering. Det motsvarar **{v4} % av bruttoinkomsten**.",
    "ki.insikt_over_inkomst": "**Betalningen är större än hela inkomsten, så köpet går inte att genomföra på den här inkomsten.** Siffrorna visar en uträkning, inte ett möjligt köp.",
    "ki.insikt_over_riktvarde": "Det ligger över det vanliga riktvärdet på {v0} %, så marginalen till andra utgifter är liten.",
    "ki.insikt_jamforelse": "Under det föregående regelverket ({v0}, {v1}) hade insatsen varit {v2} SEK ({v3} SEK) och tagit {v4} år längre att spara. Månadsbetalningen hade varit {v5} SEK ({v6} SEK), varav {v7} SEK amortering.",
    "ki.insikt_forbehall": "Alla regelverk räknas med pris och ränta för {v0}, så skillnaderna beror enbart på reglerna. Amorteringen minskar lånet och är ett sparande, inte en kostnad. Ränteavdrag och skatt ingår inte: sidan visar bruttobetalningen till banken. Indexet på övriga sidor drar av 30 % ränteavdrag.",
    "ki.ranta_man_sek": "Ränta/mån (SEK)",
    "ki.ranta_man_hjalp": "Räntekostnad per månad, utan ränteavdrag. Den del av betalningen som faktiskt är en kostnad.",
    "ki.amort_man_sek": "Amort./mån (SEK)",
    "ki.amort_man_hjalp": "Amortering per månad. Minskar lånet och är ett sparande, inte en kostnad.",
    "ki.syfte_rubrik": "Vad sidan svarar på",
    "ki.syfte_p1": "Övriga sidor visar ett index, alltså en jämförelse. Den här sidan räknar om samma data till det ett hushåll planerar efter: kontantinsats och månadskostnad.",
    "ki.syfte_p2": "Det är också den enda sidan som jämför regelverken sida vid sida, så du ser vad varje regeländring kostar.",
    "ki.syfte_nar_rubrik": "Använd sidan för att",
    "ki.syfte_nar_1": "se om en kommun är möjlig för ditt hushåll, inte bara hur den rankas",
    "ki.syfte_nar_2": "förstå hur en regeländring påverkat kontantinsatsen",
    "ki.syfte_nar_3": "jämföra villa mot bostadsrätt i samma region",
    "ki.gap_rubrik": "Vad räcker inkomsten till?",
    "ki.gap_underrubrik": "Högsta pris inkomsten bär, mot priset som faktiskt begärs",
    "ki.gap_tagg": "RÄCKVIDD",
    "ki.gap_faktiskt_pris": "Faktiskt pris",
    "ki.gap_max_pris": "Högsta pris inkomsten bär",
    "ki.gap_axel_pris": "Pris (SEK)",
    "ki.gap_saknas_v0": "{v0} SEK över räckvidd",
    "ki.gap_marginal_v0": "{v0} SEK marginal",
    "ki.gap_forklaring_v0": "Taket utgår från att banken lånar ut omkring {v0} gånger hushållsinkomsten. Det är vanlig bankpraxis, inte en regel, och enskilda banker gör egna bedömningar. Taket prövar enbart lånet mot inkomsten och förutsätter att kontantinsatsen redan är sparad, vilket är precis det som korten nedan mäter.",
    "ki.tillganglig": "Tillgänglig",
    "ki.anstrangd": "Ansträngd",
    "ki.otillganglig": "Otillgänglig",
    "ki.under_5x_normalt_510x_anstrangt_over_10x": "Under 5× normalt, 5–10× ansträngt, över 10× svårtillgängligt.",
    "ki.kontantinsatsborda": "Kontantinsatsbörda",
    "ki.x_arsinkomst": "× årsinkomst",
    "ki.detaljer_och_antaganden": "Detaljer och antaganden",
    "ki.paslag_forval_v0_v1": "Förvalt till {v0} pp, påslaget på nya rörliga bolån {v1} enligt SCB.",
    "ki.paslag_forval_saknas_v0": "Förvalt till {v0} pp: SCB:s påslag saknas för det valda året.",
    "ki.titel": "Kontantinsatsanalys",
    "ki.hur_manga_arsinkomster_kontantinsatsen": "Hur många årsinkomster kontantinsatsen motsvarar.",
    "ki.boendekostnadsborda": "Boendekostnadsbörda",
    "ki.andel_av_manadsinkomst_under_30_anses": "Andel av månadsinkomsten. Ett vanligt riktvärde är under 30 %.",
    "ki.tillganglighet": "Tillgänglighet",
    "ki.tillganglig_under_5_ars_spartid_anstrangd": "Tillgänglig = under 5 års spartid. Ansträngd = 5–10 år. Otillgänglig = över 10 år spartid vid vald sparkvot.",
    "ki.lansniva": "länsnivå",
    "ki.kommunniva": "kommunnivå",
    "ki.nulage_lattnad_2026_v0_v1_v2_sparkvot_v3_0f": "Nuläge · Lättnad 2026 · {v0} ({v1}) · {v2} · Sparkvot {v3:.0f} % · Pristyp: {v4}",
    "ki.inkomsten_ar_individuell_bruttoinkomst_scb": "Inkomsten är sammanräknad förvärvsinkomst per person, 20 år och äldre, före skatt. Välj Par ovan för ett hushåll med två medianinkomster. Par är alltså två medianinkomsttagare, inte medianparet: i kommuner med många ensamhushåll är det ett mer välbeställt hushåll än det typiska. Se Begränsning F14 i Metodologi (Sida 06).",
    "ki.villa_vs_bostadsratt": "Villa vs. bostadsrätt",
    "ki.v0_v1_lattnad_2026": "{v0} · {v1} · Lättnad 2026",
    "ki.pristypsjamforelse": "PRISTYPSJÄMFÖRELSE",
    "ki.smahus_villa_scb_bo0501c2_v0": "**Småhus (villa)**, {v0}",
    "ki.ar_att_spara": "År att spara",
    "ki.fyra_regelandringar_2010_2026": "Fyra regeländringar 2010–2026",
    "ki.ar": " år",
    "ki.manadskostnad": "Månadskostnad",
    "ki.bostadsratt_scb_bo0501c_lansniva": "**Bostadsrätt**, länsnivå",
    "ki.priskvot_villa_bostadsratt_v0_1f_bada_priser": "Priskvot villa/bostadsrätt: **{v0}×**. Båda priser avser **{v1}** (länsnivå). Samma hushållsinkomst, ränta och regelverk (Lättnad 2026).",
    "ki.priskvot_villa_bostadsratt_v0_1f_villapris": "Priskvot villa/bostadsrätt: **{v0}×**. Villapriset avser **{v1}** (kommun), bostadsrättspriset **{v2}** (län).",
    "ki.total_kontantinsats_10_av_medianpriset_under": "Total kontantinsats (10 % av medelpriset under nuvarande bolånetak, gäller fr.o.m. apr 2026).",
    "ki.ar_att_spara_idag": "År att spara (idag)",
    "ki.ar_2": "år",
    "ki.antal_ar_for_att_spara_kontantinsatsen_vid": "Antal år för att spara kontantinsatsen vid vald sparkvot.",
    "ki.manadskostnad_idag": "Månadskostnad (idag)",
    "ki.rante_amorteringskostnad_per_manad_efter_att": "Ränta och amortering per månad efter köpet. Amorteringen minskar lånet och är ett sparande.",
    "ki.sek_ar": "SEK/år",
    "ki.inkomst_kvar_efter_att_boendekostnaderna_ar": "Bruttoinkomst kvar per år efter ränta och amortering, före skatt.",
    "ki.ingen_formell_insatsniva_hog_belaning_var": "Ingen formell insatsnivå; hög belåning var vanligare.",
    "ki.bolanetak_infors_max_85_belaning_hogre": "Bolånetak införs (högst 85 % belåning), vilket höjer insatsen.",
    "ki.amorteringskrav_infors_hogre_manadskostnad": "Amorteringskrav införs, vilket höjer månadskostnaden vid hög belåning.",
    "ki.skarpt_amorteringskrav_skuldkvot_lti_4_5": "Skärpt amorteringskrav (skuldkvot LTI > 4,5×). Gällde mar 2018 – mar 2026.",
    "ki.bolanetak_hojt_till_90_insats_10_skarpt": "Bolånetaket höjt till 90 % (insats 10 %) och det skärpta amorteringskravet slopat. Gäller från april 2026.",
    "ki.kontantinsats_ar_eget_kapital_insats_som": "Kontantinsats är eget kapital (insats) som krävs vid köp. Lägre är bättre.",
    "ki.v0_1f_ar": "{v0:+.1f} år",
    "ki.antal_ar_for_att_spara_kontantinsatsen_vid_2": "Antal år för att spara kontantinsatsen vid vald sparkvot. Lägre är bättre.",
    "ki.summa_amortering_rantekostnad_per_manad": "Ränta plus amortering per månad. Amorteringen minskar lånet och är ett sparande, så en lägre summa betyder ofta bara mindre amortering, inte en billigare bostad.",
    "ki.obs_inget_formellt_insatskrav_men_banker": "Obs: Inget formellt insatskrav. Bankerna gjorde egna bedömningar.",
    "ki.valj_flik_for_att_jamfora_regelverken_fran": "Välj flik för att jämföra regelverken från olika perspektiv. Ändra år i sidopanelen för att se historiska scenarion.",
    "ki.manadskostnad_per_regelverk": "Månadskostnad per regelverk",
    "ki.jamforelse": "JÄMFÖRELSE",
    "ki.manadskostnad_sek": "Månadskostnad (SEK)",
    "ki.30_av_manadsink_v0_sek": "30 % av månadsink. · {v0} SEK",
    "ki.lagre_manadskostnad_innebar_mindre_lopande": "Staplarna visar ränta plus amortering med samma pris, inkomst och ränta. Amorteringen minskar lånet, så en lägre stapel betyder ofta bara mindre amortering, inte en billigare bostad.",
    "ki.ar_att_spara_kontantinsats": "År att spara kontantinsats",
    "ki.5_ar_tillganglig": "5 år – Tillgänglig",
    "ki.10_ar_otillganglig": "10 år – Otillgänglig",
    "ki.sparkvoten_paverkar_framst_sparar": "Sparkvoten påverkar främst sparår; regelverken påverkar kravet på insats och amortering.",
    "ki.kvarvarande_inkomst_sek_ar": "Kvarvarande inkomst (SEK/år)",
    "ki.nollgrans": "Nollgräns",
    "ki.hogre_kvarvarande_inkomst_innebar_mer": "Kvar = bruttoinkomst minus ränta och amortering, före skatt. Amorteringen räknas bort fast den är ett sparande, så ett regelverk utan amorteringskrav ser bättre ut här än det är.",
    "ki.singelhushall_2": "singelhushåll",
    "ki.lan": "Län",
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
    "ki.manadskostnad_ranta_amortering_lagre_ar": "Månadsbetalning: ränta och amortering. Amorteringen minskar lånet.",
    "ki.mankostnad_vs_idag": "Δ Månkostnad vs idag",
    "ki.skillnad_i_manadskostnad_jamfort_med_idag": "Skillnad i månadskostnad jämfört med idag.",
    "ki.kvar_sek_ar": "Kvar (SEK/år)",
    "ki.kvarvarande_inkomst_per_ar_efter": "Bruttoinkomst minus ränta och amortering per år, före skatt och andra utgifter.",
    "ki.skillnad_i_kvarvarande_inkomst_jamfort_med": "Skillnad i kvarvarande inkomst jämfört med idag.",
    "ki.belaningsgrad_lan_bostadspris": "Belåningsgrad: lån / bostadspris.",
    "ki.skuldkvot_lan_arsinkomst": "Skuldkvot: lån / årsinkomst.",
    "ki.arlig_amortering_i_av_lanet": "Årlig amortering i procent av lånet.",

    # ── Sida 05 — Scenario ────────────────────────────────────────
    "sc.shai_version_c_for_v0": "SHAI Version C för {v0}",
    # Result interpretation (sida 05).
    "sc.tolk_ranta_vid_golv": "Räntan hålls på {v0} % i scenariot. Lägre än så har snitträntan på nya bolån aldrig varit, så simulatorn räknar inte på det.",
    "sc.tolk_preset_cykel": "Scenariot följer årsgenomsnitten 2021–2023: snitträntan på nya bolån steg 3,0 procentenheter, medianinkomsten 9 % och småhuspriserna föll knappt 6 %, avrundat till reglagets steg på 5 %. Boendekostnaden steg, vilket är vad hushållen upplevde.",
    "sc.tolk_bindningstid": "Räntan går från {v0} % till {v1} %. Reglaget flyttar snitträntan på nya bolån, inte styrräntan. Hur mycket av en ändring av styrräntan som når hushållen under ett år beror på bindningstiden: ett rörligt lån följer inom tre månader, ett bundet först vid omsättningen. 2021–2023 steg styrräntan 3,5 och snitträntan på nya bolån 3,0 procentenheter i årsgenomsnitt.",
    "sc.rantechock_hjalp": "+3 pp ≈ uppgången i snitträntan på nya bolån 2021–2023 (från 1,5 till 4,5 %). Adderas till bolåneräntan, inte till styrräntan.",
    "sc.prischock_pct": "Prischock (%)",
    "sc.rantecykeln_2021_23": "Räntecykeln 2021–23",
    "sc.rantecykeln_hjalp": "+3,0 pp ränta, +9 % inkomst, −5 % pris: årsgenomsnitten 2021–2023.",
    "sc.lagrantelyftet": "Prisuppgången 2019–21",
    "sc.lagrantelyftet_hjalp": "Oförändrad ränta, +5 % inkomst, +25 % pris: årsgenomsnitten 2019–2021.",
    "sc.bolaneranta": "Bolåneränta (%)",
    # Rate and price surface (sida 05).
    "sc.riket_rubrik": "Samma scenario för hela riket",
    "sc.riket_underrubrik": "Hur många av {v0} kommuner som hamnar i varje riskklass när scenariot slår igenom",
    "sc.riket_tagg": "RIKET",
    "sc.riket_kommuner": "kommuner",
    "sc.riket_hog": "Hög risk",
    "sc.riket_medel": "Medelrisk",
    "sc.riket_lag": "Låg risk",
    "sc.riket_tooltip_v0": "Basfallet har {v0} kommuner i den här klassen.",
    "sc.riket_in_i_hog_v0": "Scenariot för **{v0} kommuner** in i hög risk.",
    "sc.riket_ut_ur_hog_v0": "Scenariot för **{v0} kommuner** ut ur hög risk.",
    "sc.riket_ingen_rorelse": "Scenariot flyttar ingen kommun mellan riskklasserna.",
    "sc.riket_median_v0_v1_v2": "Medianen för Version C över alla kommuner går från {v0} till {v1} ({v2} %). Den visar hur långt landet rör sig även när antalet i varje klass står still eller redan har nått taket.",
    "sc.riket_forklaring": "Klassgränserna hålls fast vid basårets fördelning, så hela landet rör sig mot en fast referens. Det är en annan fråga än kartans: där jämförs varje kommun med sina jämnåriga samma år, och en chock som träffar alla lika mycket flyttar därför ingen kommun alls. Här jämförs landet efter chocken med landet före den, vilket är det en scenariofråga faktiskt gäller.",
    "sc.syfte_rubrik": "Vad sidan svarar på",
    "sc.syfte_p1": "Ett stresstest: vad händer med ett läns boendekostnad om bolåneräntan, inkomsten eller priset ändras?",
    "sc.syfte_p2": "Här väljer du själv förändringarna. Räntereglaget flyttar snitträntan på nya bolån, inte styrräntan. Inflationen har inget eget reglage: den når resultatet bara genom vad den gör med inkomster, priser och ränta.",
    "sc.syfte_nar_rubrik": "Använd sidan för att",
    "sc.syfte_nar_1": "se vilken faktor som påverkar överkomligheten mest i ett län",
    "sc.syfte_nar_2": "spela upp en historisk episod med de förinställda scenarierna",
    "sc.syfte_nar_3": "pröva hur långt ett prisfall eller en löneökning väger upp en räntehöjning",
    "sc.yta_rubrik": "Ränta och pris tillsammans",
    "sc.yta_underrubrik": "Hur mycket scenariot ändrar boendekostnaden, över hela planet, med ditt scenario markerat",
    "sc.yta_tagg": "KÄNSLIGHET",
    "sc.yta_x_axel": "Prischock (%)",
    "sc.yta_y_axel": "Räntechock (procentenheter)",
    "sc.yta_skala": "Förändring mot basfall",
    "sc.yta_hover": "Räntechock %{y:+.2f} pp<br>Prischock %{x:+.0f} %<br>Bolåneränta %{customdata[1]:.2f} %<br>SHAI %{customdata[0]:.1f} % av inkomsten<br>Mot basfall %{z:+.0f} %<extra></extra>",
    "sc.yta_du_ar_har": "Ditt scenario<extra></extra>",
    "sc.yta_forklaring": "Färgen visar förändring av boendekostnaden mot basfallet i procent. Grönt är billigare, rött dyrare. Längs en konturlinje väger prisförändringen upp ränteförändringen exakt.",
    "sc.yta_mer_rubrik": "Hur läser jag diagrammet?",
    "sc.yta_mer_text": "Färgen visar hur mycket scenariot ändrar boendekostnaden mot basfallet, inte SHAI-värdet i sig, så den kan inte jämföras med kartans skala. Konturlinjerna lutar eftersom ett lägre pris ger ett mindre lån: längs en linje är kostnaden densamma, och lutningen visar hur många procent prisfall som behövs för att bära en procentenhet högre ränta i just det här länet. Inkomstreglaget flyttar hela planet lika mycket.",
    "sc.tolk_rubrik": "Så ska resultatet läsas",
    "sc.tolk_inget_scenario": "Inget scenario är valt ännu. Flytta ett reglage eller välj ett förinställt scenario för att se hur överkomligheten påverkas.",
    "sc.tolk_riktning_upp": "Scenariot **höjer** boendekostnaden med {v0} %, från {v1} till {v2} procent av inkomsten.",
    "sc.tolk_riktning_ner": "Scenariot **sänker** boendekostnaden med {v0} %, från {v1} till {v2} procent av inkomsten.",
    "sc.tolk_riktning_oforandrad": "Scenariot lämnar boendekostnaden oförändrad på {v1} procent av inkomsten.",
    "sc.tolk_skala": "Jämför basfall mot scenario här, inte mot kartans skala. Kartan visar z-poäng inom året.",
    "sc.kunde_inte_hamta_data_forsok_igen_senare": "Kunde inte hämta data. Försök igen senare.",
    "sc.inga_data_tillgangliga_for_v0_valj_ett_ar": "Inga data tillgängliga för {v0}. Välj ett år med data: {v1}.",
    "sc.simulera_effekten_av_ranta_inkomst_och": "Simulera hur ändrad bolåneränta, inkomst och pris påverkar boendekostnaden",
    "sc.scenariosimulatorn_beraknar_om_version_c": "Simulatorn räknar endast om **Version C (kassaflödesversion)** för valt län. Version A rangordnar likadant som C, och Version B bygger även på arbetslöshet, som inte kan chockas här. Länets värde räknas på länets egen medianinkomst och medelpris, inte som medelvärdet av kommunerna på Sida 02.",
    "sc.valj_lan": "Välj län",
    "sc.forinstallda_scenarier": "**Förinställda scenarier:**",
    "sc.loneboom_2": "Löneboom",
    "sc.1pp_ranta_5_lon_10_pris": "+1pp ränta, +5% lön, +10% pris",
    "sc.aterstall": "Återställ",
    "sc.nollstall_alla_scenariojusteringar_till": "Nollställ alla scenariojusteringar till basfall",
    "sc.rantechock_pp": "Bolåneränta, ändring (pp)",
    "sc.inkomsttillvaxt": "Inkomsttillväxt (%)",
    "sc.34_ett_ars_normal_loneutveckling_i_sverige_5": "+3–4 % ≈ ett normalt år: medianinkomsten har ökat 1,8–4,9 % per år sedan 2014. −5 % simulerar en recession med sjunkande inkomster.",
    "sc.prischock_hjalp": "−5 % ≈ småhuspriserna 2021–2023 i årsgenomsnitt; från toppen andra kvartalet 2022 till botten fjärde kvartalet 2023 föll de 13 %. +25 % ≈ uppgången 2019–2021.",
    "sc.inga_data_tillgangliga_for_det_valda_lanet": "Inga data tillgängliga för det valda länet och året.",
    "sc.berakningsfel_se_metodologisidan_for": "Beräkningsfel. Se metodologisidan för detaljer.",
    "sc.basfall_beraknat_fran_faktiska_data_for_valt": "Basfall: beräknat från länets egen medianinkomst och medelpris för valt år. Det är inte medelvärdet av kommunerna som Sida 02 visar, så talen skiljer sig.",
    "sc.scenario_beraknat_med_justerade_parametrar": "Scenario: beräknat med justerade parametrar.",
    "sc.forandring": "Förändring",
    "sc.procentenheter": "procentenheter",
    "sc.skillnad_mellan_scenario_och_basfall": "Skillnad mellan scenario och basfall, i procentenheter av inkomsten. Positivt = dyrare.",
    "sc.shai_poang": "SHAI, % av inkomsten",
    "sc.version_c_lansniva": "% av inkomsten, länsnivå",
    "sc.standardlan": "Stockholms län",
    "sc.jamforelsetabell": "Jämförelsetabell",
    "sc.forklaring": "Förklaring",
    "sc.version_c_kassaflode_beraknas_som_text": """
    **Version C (kassaflödesversion)** beräknas som:

    $$C = 100 \\cdot \\frac{0{,}85 \\cdot P \\cdot \\big(r \\cdot (1 - 0{,}30) + a\\big)}{2 \\cdot I}$$

    Där:
    - **I** = medianinkomst per person, 20 år och äldre, före skatt (SEK); hushållet har två
    - **P** = medelpris för småhus (SEK); lånet är 85 % av priset
    - **r** = snitträntan på nya bolån över alla bindningstider (SCB), årsgenomsnitt
    - **0,30** = ränteavdraget
    - **a** = amorteringskravet: 0 före juni 2016, därefter 2 % av lånet per år

    **Tolkning:** årlig boendekostnad i procent av hushållets inkomst. Högre värde = dyrare.

    **Scenariomekanik:**
    - Räntechocken adderas till bolåneräntan (procentenheter). Räntan sätts aldrig lägre än 0,5 %.
    - Inkomst- och prischock multipliceras med inkomst respektive pris (relativ förändring)
    - Räntan verkar bara genom räntetermen: en procentenhet höjer kostnaden med 0,7 % av lånet, medan amorteringen ligger still

    **Begränsning F15:** Chockerna slår lika mot alla kommuner. Regionala skillnader i ränte-
    eller prisutveckling modelleras inte. Räntechocken gäller snitträntan för nya lån; ett hushåll
    med bunden ränta märker den först vid omsättningen.
    
    """,

    # ── Sida 06 — Metodologi ──────────────────────────────────────
    "mt.metodologi_och_kallor": "Metodologi och källor",
    "mt.teoretisk_grund_formler_datakallor_och": "Hur indexet beräknas, vilka data det bygger på och var det har sina gränser",
    "mt.tre_perspektiv_pa_bostadsoverkomlighet": "Tre perspektiv på bostadsöverkomlighet",
    "mt.bostadsoverkomlighet_housing_affordability": """
    Bostadsöverkomlighet beskriver hur väl inkomsterna räcker till boendet. SHAI belyser
    frågan från tre håll:

    | Perspektiv | Frågan | Var i SHAI |
    |---|---|---|
    | Löpande kostnad | Hur stor del av inkomsten går till lånet på ett typiskt småhus? | Index A, B och C (Sida 01–03) |
    | Insats | Hur lång tid tar det att spara ihop kontantinsatsen? | Sida 04, Kontantinsats |
    | Stress | Vad händer om ränta, inkomst eller pris ändras? | Sida 05, Scenario |
    """,
    "mt.2_variabler_och_datakallor": "2. Data och källor",
    "mt.10_variabler_fran_officiella_svenska_kallor": "Officiell statistik från SCB, Riksbanken och Kolada",
    "mt.variabel_symbol_kalla_upplosning_frekvens": """
    | Variabel | Källa | Nivå | Publicerad period |
    |---|---|---|---|
    | Medianinkomst, 20 år och äldre (I) | SCB HE0110, sammanräknad förvärvsinkomst | Kommun, län | 1999–{income_max} |
    | Transaktionspris småhus, medelvärde (P) | SCB BO0501, köpeskilling för permanenta småhus | Kommun, län | 1981–{price_max} |
    | Transaktionspris bostadsrätt, medelvärde | SCB BO0501, försäljning av bostadsrätter | Län, riket | från 2000 |
    | Fastighetsprisindex (1990 = 100) | SCB BO0501 | Län | 1990–{price_index_max} |
    | Köpeskillingskoefficient (K/T) | SCB BO0501 | Kommun, län | 1981–{kt_max} |
    | Bolåneränta, nya avtal, alla bindningstider (r) | SCB FM5001 (RantaT04N) | Riket | 2005–idag |
    | KPIF-inflation (π) | SCB PR0101 (KPIF) | Riket | 1988–idag |
    | Styrränta | Riksbanken | Riket | 1994–idag; används bara på Sida 04 |
    | KPI | SCB PR0101 | Riket | 1981–idag; används bara för realinkomstkontrollen |
    | Arbetslöshet (U) | Kolada N03937 (Arbetsförmedlingen och SCB) | Kommun, län | 2010–{unemployment_max} |
    | Befolkning | SCB BE0101 | Kommun, län | 1968–{population_max} |
    | Bostadsbyggande, färdigställda lägenheter | SCB BO0101 | Kommun, län | 1938–{completions_max} |

    **Att tänka på**

    - **Priset är ett medelvärde, inte en median.** Några få dyra försäljningar kan lyfta värdet i en liten kommun.
    - **Formlerna använder småhuspriser.** Bostadsrättspriser publiceras bara per län och används på Sida 04 (F11).
    - **K/T och prisindex är beskrivande** och ingår ej i formlerna. Prisindexet startar på 100 i alla regioner och kan inte jämföra nivåer, och K/T påverkas av eftersläpande taxeringsvärden.
    - **Arbetslöshet** avser öppet arbetslösa hos Arbetsförmedlingen som andel av befolkningen 18–65 år (18–64 år till och med 2022). Det är inte samma mått som SCB:s arbetskraftsundersökning, AKU (F10).
    - **Bolåneräntan och inflationen** är nationella årsgenomsnitt och desamma för alla kommuner (F2).
    - **Bolåneräntan är snittet över alla bindningstider** för nya och omförhandlade lån, alltså den ränta nya låntagare faktiskt avtalade. Den rörliga räntan används bara på Sida 04, som räknar på ett rörligt lån (F12).
    - **KPIF, inte KPI.** KPI innehåller hushållens räntekostnader och stiger därför av sig själv när räntan höjs. Riksbanken har KPIF som målvariabel av samma skäl.
    """,
    "mt.1_vad_shai_mater": "1. Vad SHAI mäter",
    "mt.3_formler": "3. Formler",
    "mt.tre_satt_att_mata": "Tre sätt att mäta överkomlighet",
    "mt.version_a_rubrik": "### Version A: Bankversion",
    "mt.version_c_rubrik": "### Version C: Kassaflödesversion (rekommenderad)",
    "mt.4_fran_varde_till_riskklass": "4. Från värde till riskklass",
    "mt.normalisering_rang_och_riskklass": "Normalisering, rang och riskklass",
    "mt.beteckningar": "**Beteckningar:** I = medianinkomst per person, P = medelpris för småhus (SEK), r = snitträntan på nya bolån över alla bindningstider (%), a(t) = amorteringskravet året t (0 före juni 2016, därefter 2 % av lånet), π = KPIF-inflation, U = arbetslöshet. Lånet är 85 % av priset och hushållet har två medianinkomster.",
    "mt.mater_flodesoverkomlighet_hushallets_inkomst": """
    Räntan på ett lån på 85 % av medelpriset, före ränteavdrag och utan amortering, i
    procent av två medianinkomster. Ungefär så ser en bank på räntekostnaden.
    **Högre värde = dyrare.**
    
    """,
    "mt.version_b_makrokomposit_tryckmatt": "### Version B: Makroversion",
    "mt.sammansatt_riskindikator_som_viktar_pris": """
    Väger samman pris/inkomst, bolåneränta, arbetslöshet och KPIF-inflation till ett
    tryckmått. **Högre värde = högre risk.** z-poängen räknas mot en fast referens för hela
    panelen, så att redan publicerade värden inte ändras när ett nytt år läggs till.

    **Obs (F13):** r och π är nationella. Inom ett år flyttar de alla kommuner lika mycket,
    så rangordningen styrs i praktiken av pris/inkomst och arbetslöshet.
    
    """,
    "mt.kassaflode_version_c_text": """
    Hushållets faktiska utbetalning för samma lån som A: räntan efter 30 % ränteavdrag plus
    den amortering som gällde året, i procent av två medianinkomster.
    **Högre värde = dyrare.**

    Formeln multiplicerar med räntan i stället för att dela med den, så den behöver inget
    golv: snitträntan på nya bolån låg mellan 1,5 och 4,5 % under hela perioden. Fram till
    oktober 2026 delade Version C med styrräntan minus KPI-inflationen, och det golv på 0,5
    procentenheter som krävdes band nio av elva år (se METHODOLOGY.md, avsnitt 3).

    **Obs (F18):** Amorteringen är en utbetalning men bygger samtidigt eget kapital, så C
    mäter en kassaflödesbörda och inte en förbrukad kostnad. Version A visar räntebördan
    utan amorteringen. Det extra kravet på 1 % för lån över 4,5 gånger inkomsten
    (mars 2018 – mars 2026) ingår inte, eftersom det skulle göra kostnaden kommunspecifik.
    
    """,
    "mt.formlerna_ger_ett_nivavarde_per_kommun_och": """
    Formlerna ger ett nivåvärde per kommun och år. Det görs jämförbart i tre steg.

    1. **z-poäng inom år.** Varje kommun jämförs med samma års fördelning. Riskklassen säger
       hur en kommun ligger till jämfört med andra kommuner samma år, inte hur Sveriges
       överkomlighet utvecklas över tid.
    2. **Logaritm för A och C.** Kostnadsandelarna är snedfördelade. Utan logaritm förkastar
       Shapiro–Wilk-testet normalfördelning varje år; med logaritm inget år. Rangordningen
       påverkas inte, eftersom logaritmen är monoton.
    3. **Riskklass** efter normalfördelningens kvartiler:

    | z-poäng | Riskklass |
    |---|---|
    | ≤ −0,67 | Låg risk |
    | −0,67 till +0,67 | Medelrisk |
    | > +0,67 | Hög risk |

    Orienteringen är gemensam för alla versioner: **högre z = sämre överkomlighet**, och
    rang 1 = bäst.

    **Undantag, Version B:** B poolas över hela panelen mot en fast referens, så att den kan
    visa en trend över tid. Panelmedelvärdet går från −0,27 (2019) till +0,72 (2023) och
    följer ränteuppgången.

    **Obs (F16):** Gränserna är normalfördelningens kvantiler, mätta mot samma års fördelning,
    så andelen i varje klass är nästan densamma varje år: ungefär en fjärdedel låg risk och
    knappt 30 % hög risk. Antalet kommuner i en klass är därför ingen trend.
    """,
    "mt.projektion_tre_scenarier_bolaneranta": """
    Sida 03 visar en **projektion**, inte en förutsägelse: vad indexet blir under tre uttalade
    antaganden om bolåneräntan.

    | Scenario | Bolåneränta |
    |---|---|
    | Lägsta nivån | Den lägsta årsnivån i indexperioden |
    | Nivå senaste indexår | Räntan det sista år indexet kan beräknas |
    | Stress | 6 %, över toppen 2008 (5,3 %) och under bankernas kalkylränta på omkring 7 % |

    Inkomsten skrivs fram med 3 % och priset med 2 % per år, sex år framåt. Amorteringen hålls
    på 2 % och lånet på 85 % av priset.

    **Varför ingen statistisk modell:** räntan är den del av indexet som rör sig mest mellan
    år, och den bestäms av penningpolitiken och bankernas prissättning. Med {v0} årsvärden
    ({v1}) går den inte att skatta tillförlitligt (F4). Version C är linjär i räntan, så ett
    uttalat antagande ger ett exakt och förklarbart svar.

    **Obs (F6):** Avståndet mellan linjerna är inget konfidensintervall, bara skillnaden
    mellan tre antaganden.
    
    """,
    "mt.regelverk_period_kontantinsats": """
    | Regelverk | Period | Lägsta kontantinsats | Amorteringskrav |
    |---|---|---|---|
    | Före 2010 | Till okt 2010 | Inget formellt krav | Inget |
    | Bolånetak | Okt 2010 – jun 2016 | 15 % | Inget |
    | Amorteringskrav 1.0 | Jun 2016 – mar 2018 | 15 % | 2 % om belåning > 70 %, 1 % om > 50 % |
    | Amorteringskrav 2.0 | Mar 2018 – mar 2026 | 15 % | Som ovan, plus 1 % om skulden > 4,5 × bruttoinkomsten (skärpt krav) |
    | Lättnad 2026 | Apr 2026 – nuvarande | 10 % | 2 % om belåning > 70 %, 1 % om > 50 % |

    **Källor:** Finansinspektionens föreskrifter och allmänna råd fram till mars 2026. Från
    1 april 2026 regleras bolånetak och amortering i lag, som ersatte föreskrifterna.
    """,
    "mt.6_begransningar_f1f15": "7. Begränsningar (F1–F18)",
    "mt.id_begransning_atgard_f1_kommunal": """
    | ID | Begränsning | Hantering |
    |---|---|---|
    | **F1** | K/T saknas för vissa kommuner och år. | Länets värde används då, markerat med `has_native_kt`. K/T ingår inte i formlerna. |
    | **F2** | Bolåneräntan och inflationen är nationella och gäller alla kommuner och län. | Dokumenterat. |
    | **F3** | Version A och C rangordnar kommunerna identiskt varje år, eftersom bolåneräntan och amorteringskravet är nationella. Bara B kan ge en annan ordning. | Sida 02 visar C och B; identiteten testas automatiskt. |
    | **F4** | {v0} årsvärden räcker inte för att skatta en statistisk modell. | Villkorad projektion med uttalade antaganden. |
    | **F5** | Kontantinsatskravet ändras i steg när regelverket ändras. | Varje regelverk visas för sig. |
    | **F6** | Projektionens spridning är inget konfidensintervall. | Varje linje märks med sitt antagande. |
    | **F7** | Data uppdateras vid datauttag, inte löpande. | Datavintage visas på varje sida. |
    | **F8** | Gränssnittet finns bara på svenska. | – |
    | **F9** | Inkomst publiceras med ett års fördröjning. | Saknade år skrivs fram med 3 % och markeras `is_imputed_income`; de kan inte väljas i årsväljaren. |
    | **F10** | Arbetslöshet enligt Arbetsförmedlingen, inte AKU. | Förklaras här och på Sida 02. |
    | **F11** | Indexformlerna använder bara småhuspriser. Bostadsrättspriser finns bara per län. | Sida 04 har pristypsväljare och byter till länsnivå för bostadsrätt. |
    | **F12** | Indexet räknar med snitträntan på nya bolån över alla bindningstider, inte med räntan ett enskilt hushåll betalar. Ett hushåll med bunden ränta möter en ny ränta först vid omsättningen, och den utestående stocken av lån ligger därför efter. Sida 04 räknar i stället på ett rörligt lån: styrränta plus ett påslag, som för nya rörliga lån har legat mellan 0,8 och 2,1 procentenheter sedan 2014. | Indexets ränta anges som snitt över bindningstider på varje sida. Påslaget på Sida 04 väljs med reglage och är förvalt till det påslag SCB uppmätte det valda året. Räntechocken på Sida 05 gäller snitträntan, inte styrräntan. |
    | **F13** | I Version B bär r och π ingen skillnad mellan kommuner inom ett år (45 % av vikterna). | Se Version B ovan. |
    | **F14** | Inkomsten gäller personer, inte hushåll. Par = två medianinkomster, inte medianparet. | Hushållsväljare och förklaring på Sida 04. |
    | **F15** | Scenarier slår lika mot alla kommuner; regionala skillnader i ränta eller prisutveckling modelleras inte. | Sida 05 mäter mot basårets fasta klassgränser. |
    | **F16** | Klassgränserna mäts mot samma års fördelning, så antalet kommuner per klass är nästan detsamma varje år. | Antalet visas utan förändringspil. |
    | **F17** | *Stängd oktober 2026.* Räntegolven (A: 0,1, C: 0,5 procentenheter) gjorde att indexnivåerna inte kunde jämföras mellan år. | Formlerna räknar nu med bolåneräntan och multiplicerar med den, så inget golv behövs. |
    | **F18** | Amorteringen räknas som utbetalning, fast den bygger eget kapital; det extra kravet för lån över 4,5 gånger inkomsten ingår inte; lånet hålls på 85 % av priset även efter april 2026. | Version A visar räntebördan utan amortering. Antagandena står i formelbeskrivningen. |
    """,
    "mt.foljande_valideringskontroller_kors_innan": """
    Varje datauppdatering måste klara följande kontroller:

    1. Medianinkomsten ökar nominellt; högst tre år med nedgång tillåts.
    2. Realinkomsten är stabil: högsta året är under 1,35 gånger det lägsta.
    3. Stockholms län är bland de fem minst överkomliga länen under Version C.
    4. Skåne län ligger i den minst överkomliga tredjedelen under Version C.
    5. Norrbottens län är bland de fem mest överkomliga länen under Version A.
    6. Alla K/T-värden ligger mellan 1,0 och 4,0.
    7. Medelpriset för småhus i Stockholms län är minst 2,5 gånger Norrbottens.
    8. Projektionens första år ligger mellan 0,25 och 4 gånger länets senast observerade värde.
    """,
    "mt.scb_bo0501_fastighetspriser_och_lagfarter": """
    **Statistik**
    - SCB, Fastighetspriser och lagfarter (BO0501): [scb.se/bo0501](https://www.scb.se/bo0501)
    - SCB, Inkomster och skatter (HE0110): [scb.se/he0110](https://www.scb.se/he0110-en)
    - SCB, Konsumentprisindex och KPIF (PR0101): [scb.se/pr0101](https://www.scb.se/pr0101)
    - SCB, Befolkningsstatistik (BE0101): [scb.se/be0101](https://www.scb.se/be0101)
    - SCB, Bostadsbyggande (BO0101): [scb.se/bo0101](https://www.scb.se/bo0101)
    - Kolada, nyckeltal N03937 (arbetslöshet): [api.kolada.se](https://api.kolada.se/v3/kpi/N03937)
    - Riksbanken, styrränta (Sida 04): [riksbank.se](https://www.riksbank.se/sv/statistik/rantor-och-valutakurser/)
    - SCB, Bolåneräntor till hushåll (FM5001, tabell RantaT04N): [scb.se/fm5001](https://www.scb.se/fm5001)
    - SCB och Riksbanken, bolåneräntor till hushåll (finansmarknadsstatistik, tabell TAB5783): [statistikdatabasen.scb.se](https://www.statistikdatabasen.scb.se/)

    **Regelverk**
    - Regeringen, höjt bolånetak och slopat skärpt amorteringskrav (2026): [regeringen.se](https://regeringen.se/pressmeddelanden/2026/03/nya-lagandringar-ska-ge-fler-mojlighet-att-aga-sin-bostad/)
    - Finansinspektionen: [fi.se](https://www.fi.se/)

    **Datatjänster:** SCB PxWeb API ([scb.se/api](https://www.scb.se/api/)) och Kolada API v3.
    """,
    "mt.shai_v_v0_metodologi_baserad_pa_methodology": "SHAI v{v0}",
    "mt.kalla_sidfot": "SCB, Riksbanken, Kolada, Finansinspektionen",

}
