"""Markup templates, kept out of the copy dictionary.

R9 in `docs/OPEN_RISKS.md`. T3.1 gathered every Swedish string into
`SWEDISH_LABELS`, which was the right move and is what
`tests/test_no_inline_copy.py` enforces. The side effect was that the dictionary
ended up holding two different kinds of thing: sentences a translator would
edit, and HTML a front-end developer would edit. A 2000-character regime table
and the word "Kommun" are not the same object.

**The rule, and it is enforced rather than described:** a string carrying HTML
tags lives here; `SWEDISH_LABELS` holds prose. `tests/test_labels.py` asserts
both directions, so a new markup block cannot drift back into the copy dict and
a sentence cannot end up here.

One carve-out, because the alternative is worse. Plotly hover templates contain
`<br>` and `<extra></extra>`, which is Plotly's own microformat rather than page
markup — those stay with the copy, since what a user reads in a tooltip is
copy. They are recognised by the `%{...}` placeholders no page HTML uses.

Everything here still goes through the same guards as the copy it left:
`test_copy_matches_artifacts.py` re-derives any figure quoted inside a template,
because prose that has been wrapped in a `<div>` can go stale exactly as easily.
"""

from __future__ import annotations

#: Markup blocks, keyed exactly as they were in `SWEDISH_LABELS` so a call site
#: changes only which function it calls.
TEMPLATES: dict[str, str] = {
    "landing.vad_hittar_du_har": """
<div class="shai-section">
    <div class="shai-section-title">Vad hittar du här?</div>
</div>
""",
    "kd.v1_har_storst_relativ_variation_och_driver": "<div style='font-size:13px;color:{v0};text-align:center;padding:8px 0;'><strong>{v1}</strong> har störst relativ variation och driver mest av SHAI-förändringen för {v2}.</div>",
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
    "ki.indata_v1_v2_analysar_v3_pristyp_v4_pris": "<div style='color:{v0};font-size:13px;line-height:1.55;'><strong>Indata</strong><br>- {v1}: <strong>{v2}</strong> (analysår {v3})<br>- Pristyp: <strong>{v4}</strong><br>- Pris (används): <strong>{v5} SEK</strong><br>",
    "ki.smahuspris_referens_v0_sek": "- Småhuspris (referens): <strong>{v0} SEK</strong><br>",
    "ki.bostadsrattspris_referens_v0_v1_sek": "- Bostadsrättspris (referens, {v0}): <strong>{v1} SEK</strong><br>",
    "ki.hushallstyp_v0_individuell_medianinkomst_v1": "- Hushållstyp: <strong>{v0}</strong><br>- Individuell medianinkomst: <strong>{v1} SEK</strong><br>- Hushållsinkomst (används): <strong>{v2} SEK</strong>{v3}<br>- Styrränta: <strong>{v4:.2f}%</strong><br>- Bankens räntepåslag: <strong>{v5:.1f} pp</strong><br>- Effektiv bolåneränta (används): <strong>{v6:.2f}%</strong><br>- Sparkvot: <strong>{v7}%</strong><br><br><strong>Konstant mellan regelverk</strong><br>- Samma pris, inkomst och räntenivå används i alla regimer<br>- Skillnaderna drivs av insatskrav, maxbelåning och amorteringsregler<br><br><strong>Metod</strong><br>Se Metodologi (Sida 06), avsnitt 6 för antaganden och definitioner.</div>",
    "ki.sa_laser_du_tabellen_kolumner_visar_skillnad": "<div style='color:{v0};font-size:13px;line-height:1.55;margin-top:8px;'><strong>Så läser du tabellen</strong><br>- Δ-kolumner visar skillnad mot <strong>idag (Lättnad 2026)</strong><br>- Markeringar: <strong>bäst</strong> = lägst för Insats/Sparår/Månkostnad, högst för Kvar</div>",
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
}


def T(key: str, **values: object) -> str:
    """Return the markup template for `key`, formatted with `values`.

    Mirrors :func:`src.ui.labels.L` deliberately: the two dictionaries are
    separate but the call shape should not be something to remember.

    Args:
        key: A key of :data:`TEMPLATES`.
        values: Substitutions for the template's placeholders.

    Returns:
        The template, formatted when `values` are supplied.

    Raises:
        KeyError: If `key` is not defined, naming the closest matches. A typo
            here renders as a blank area of a page rather than an error.
    """
    try:
        text = TEMPLATES[key]
    except KeyError:
        import difflib

        near = difflib.get_close_matches(key, TEMPLATES, n=3)
        raise KeyError(
            f"no template {key!r}" + (f"; did you mean {near}?" if near else "")
        ) from None
    return text.format(**values) if values else text
