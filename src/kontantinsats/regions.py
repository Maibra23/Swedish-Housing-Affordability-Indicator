"""County-code to county-name lookup, and the regime change descriptions.

Extracted from `pages/04_Kontantinsats.py` by T3.11 (Finding K). Neither is
layout: the county names are reference data about Swedish geography, and the
regime descriptions are regulatory facts. A page file is the wrong home for
either — nothing can unit-test a constant that only exists inside a Streamlit
script, and the page was 885 lines partly because of them.

The regime copy keys match `REGIMES` in `engine.py`; `tests/test_kontantinsats_regimes.py`
asserts the two stay in step, because a regime added to the engine without a
description renders a blank card.
"""

from __future__ import annotations

from src.ui.labels import L
from src.ui.tokens import COLORS

_LAN_NAMES = {
    "01": L("ki.stockholms_lan"), "03": L("ki.uppsala_lan"), "04": L("ki.sodermanlands_lan"),
    "05": L("ki.ostergotlands_lan"), "06": L("ki.jonkopings_lan"), "07": L("ki.kronobergs_lan"),
    "08": L("ki.kalmar_lan"), "09": L("ki.gotlands_lan"), "10": L("ki.blekinge_lan"),
    "12": L("ki.skane_lan"), "13": L("ki.hallands_lan"), "14": L("ki.vastra_gotalands_lan"),
    "17": L("ki.varmlands_lan"), "18": L("ki.orebro_lan"), "19": L("ki.vastmanlands_lan"),
    "20": L("ki.dalarnas_lan"), "21": L("ki.gavleborgs_lan"), "22": L("ki.vasternorrlands_lan"),
    "23": L("ki.jamtlands_lan"), "24": L("ki.vasterbottens_lan"), "25": L("ki.norrbottens_lan"),
}


REGIME_WHAT_CHANGED = {
    "pre_2010": L("ki.ingen_formell_insatsniva_hog_belaning_var"),
    "bolanetak": L("ki.bolanetak_infors_max_85_belaning_hogre"),
    "amort_1": L("ki.amorteringskrav_infors_hogre_manadskostnad"),
    "amort_2": L("ki.skarpt_amorteringskrav_skuldkvot_lti_4_5"),
    "latt_2026": L("ki.bolanetak_hojt_till_90_insats_10_skarpt"),
}

regime_accent_colors = {
    "pre_2010": COLORS["text_tertiary"],
    "bolanetak": COLORS["accent"],
    "amort_1": COLORS["medium_risk"],
    "amort_2": COLORS["high_risk"],
    "latt_2026": COLORS["low_risk"],
}


# Every regime in `REGIMES`, in chronological order. The page iterates this rather
# than `REGIMES.keys()` so the order is explicit and stable.
REGIME_KEYS = ["pre_2010", "bolanetak", "amort_1", "amort_2", "latt_2026"]

# Accent per regime, used for bar fills. Reference data, not layout.
REGIME_ACCENT_COLORS = {
    "pre_2010": COLORS["text_tertiary"],
    "bolanetak": COLORS["accent"],
    "amort_1": COLORS["medium_risk"],
    "amort_2": COLORS["high_risk"],
    "latt_2026": COLORS["low_risk"],
}
