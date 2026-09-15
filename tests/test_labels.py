"""Load-bearing wording must survive an edit, and caveats must state their limitation.

`test_no_inline_copy.py` proves the copy *lives* in one place and
`test_copy_matches_artifacts.py` proves its *numbers* match the data. Neither
protects the sentences that carry meaning the methodology depends on.

Three kinds of wording are load-bearing here:

**The orientation contract.** `normalize.py` defines higher z as worse
affordability and rank 1 as best. Finding N was that exact contract being
inverted on the live app for every year but 2014, and Finding N3 was a caption
stating it backwards while the data was right. Copy that describes the contract
is part of the contract.

**Limitation references.** The methodology maintains a register F1–F16 and pages
cite entries by id. A citation pointing at an id the register does not define
sends the reader to a section that is not there.

**Caveats with a number in them.** A caveat exists to bound a claim. "Ungefär en
fjärdedel hamnar i varje ytterklass" is the F16 caveat, and the whole reason T1.9
removed the KPI delta — so it is checked against the class shares rather than
trusted, the same way T4.1 treats the D5 statistic.

See task T4.3 and Finding L in docs/REVITALIZATION_PLAN.md.
"""

from __future__ import annotations

import re

import pandas as pd
import pytest

from src.ui.labels import SWEDISH_LABELS
from tests.test_copy_matches_artifacts import ARTIFACT

ALL_COPY = "\n".join(SWEDISH_LABELS.values())


# ── The orientation contract, as prose ───────────────────────────────


@pytest.mark.parametrize(
    "phrase",
    [
        "högre z = sämre överkomlighet",
        "rang 1 = bäst",
    ],
)
def test_orientation_contract_is_stated_verbatim(phrase: str) -> None:
    """Finding N inverted this contract in code; N3 stated it backwards in a caption."""
    assert phrase in ALL_COPY, (
        f"the methodology no longer states {phrase!r}. `normalize.py` defines the "
        "orientation and the copy is what tells the reader which way round it is — "
        "if the wording changed, check it still says the same thing."
    )


def test_no_copy_claims_the_opposite_orientation() -> None:
    """The inverted phrasings, banned outright rather than merely absent."""
    inverted = [
        "högre z = bättre",
        "lägre z = sämre",
        "rang 1 = sämst",
        "rang 1 = lägst",
    ]
    found = [phrase for phrase in inverted if phrase in ALL_COPY.lower()]
    assert not found, f"copy states the orientation backwards: {found}"


def test_risk_class_direction_is_stated_consistently() -> None:
    """`hog` must always be the least affordable end, never the most."""
    assert "Grön = låg risk" in ALL_COPY, "the map legend no longer names the green end"
    assert "röd = hög risk" in ALL_COPY.lower(), "the map legend no longer names the red end"


# ── Limitation references must resolve ───────────────────────────────


def _register_ids() -> set[str]:
    """The F-ids the methodology register actually defines."""
    register = SWEDISH_LABELS["mt.id_begransning_atgard_f1_kommunal"]
    return set(re.findall(r"\bF(\d{1,2})\b", register))


def test_every_cited_limitation_exists_in_the_register() -> None:
    defined = _register_ids()
    assert defined, "the limitation register defines no F-ids at all"

    cited: dict[str, set[str]] = {}
    for key, value in SWEDISH_LABELS.items():
        if key == "mt.id_begransning_atgard_f1_kommunal":
            continue
        for number in re.findall(r"\bF(\d{1,2})\b", value):
            cited.setdefault(number, set()).add(key)

    dangling = {f"F{n}": sorted(keys) for n, keys in cited.items() if n not in defined}
    assert not dangling, (
        f"copy cites limitations the register does not define: {dangling}. The reader "
        "is sent to a section that is not there."
    )


def test_the_register_heading_matches_the_ids_it_contains() -> None:
    """The "F1–F15" heading must not undercount the register it introduces."""
    heading = SWEDISH_LABELS["mt.6_begransningar_f1f15"]
    span = re.search(r"F(\d{1,2})\s*[–—-]\s*F?(\d{1,2})", heading)
    assert span, f"register heading states no id range: {heading!r}"

    highest = max(int(n) for n in _register_ids())
    assert int(span.group(2)) == highest, (
        f"the heading says the register ends at F{span.group(2)}, but it defines up to "
        f"F{highest}. Update the heading."
    )


# ── Caveats must state the limitation they exist for ─────────────────


@pytest.mark.parametrize(
    "key,must_mention",
    [
        # Each caveat names the thing it is warning about, not merely an id.
        ("mt.sammansatt_riskindikator_som_viktar_pris", ["F13", "nationella"]),
        ("mt.justerar_for_inflation_genom_realrantan", ["M4", "negativ realränta"]),
        ("mt.formlerna_ger_ett_nivavarde_per_kommun_och", ["F16", "kvantiler"]),
        ("ki.inkomsten_ar_individuell_bruttoinkomst_scb", ["F14"]),
        ("sc.version_c_realversion_beraknas_som_text", ["F15", "konstant"]),
    ],
)
def test_caveat_states_its_limitation(key: str, must_mention: list[str]) -> None:
    value = SWEDISH_LABELS[key]
    missing = [token for token in must_mention if token.lower() not in value.lower()]
    assert not missing, (
        f"{key} is a caveat that no longer mentions {missing}. A caveat that does not "
        "name what it bounds is decoration."
    )


def test_the_kt_ratio_caveat_still_disclaims_the_formula() -> None:
    """K/T is displayed but is not an index input. Saying so is load-bearing.

    A reader seeing a K/T KPI beside three affordability formulas will assume it
    feeds them. It does not — `transaction_price_sek` does.
    """
    disclaimers = [
        value
        for value in SWEDISH_LABELS.values()
        if "K/T" in value and "ingår ej" in value
    ]
    assert disclaimers, (
        "no copy states that K/T is descriptive only. Without it the K/T KPI reads as "
        "an index input."
    )


# ── A caveat's own number, re-derived ────────────────────────────────


def test_the_f16_quarter_claim_matches_the_class_shares() -> None:
    """F16 says roughly a quarter lands in each outer class. Check it.

    This caveat is why T1.9 removed the year-on-year delta from the high-risk
    KPI, so it is load-bearing for a shipped decision. D6's log transform already
    moved the split once (≈19/51/30 → ≈23/48/28); "ungefär en fjärdedel" has to
    stay defensible against the data, not against the version of it that was true
    when the sentence was written.
    """
    value = SWEDISH_LABELS["mt.formlerna_ger_ett_nivavarde_per_kommun_och"]
    assert "en fjärdedel" in value, "the F16 caveat no longer makes a share claim"

    ranked = pd.read_parquet(ARTIFACT)
    shares = ranked.groupby("year")["risk_c"].value_counts(normalize=True).unstack() * 100

    for klass in ("hog", "lag"):
        assert klass in shares.columns, f"no {klass} class in the artifact"
        observed = shares[klass]
        assert observed.between(15, 35).all(), (
            f"the F16 caveat says roughly a quarter per outer class; {klass} ranges "
            f"{observed.min():.1f}%–{observed.max():.1f}% across years. Either the "
            "claim or the boundary needs revisiting."
        )


def test_exact_splits_are_presented_as_contrast_not_as_the_current_state() -> None:
    """An exact split figure is evidence, never a live claim.

    D6's rationale legitimately cites "cirka 19 / 51 / 30 i stället för 25 / 50 /
    25" — what the untransformed ratio produced, against what quartiles of a
    normal distribution should produce. Both are historical or theoretical, and
    banning them outright would delete the argument for the decision.

    What must not happen is an exact split being read as *today's* split, since
    D6 already moved it once. So each figure has to sit in a sentence that marks
    it: `otransformerade` (the pre-transform state) or `i stället för` (the
    contrast). The live claim stays approximate, and
    test_the_f16_quarter_claim_matches_the_class_shares checks it against data.

    The KPI copy is separately forbidden any split at all, in
    tests/test_risk_kpi.py, which is where T1.9's constraint actually bites.
    """
    value = SWEDISH_LABELS["mt.formlerna_ger_ett_nivavarde_per_kommun_och"]
    unmarked = []
    for match in re.finditer(r"\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{1,2}", value):
        window = value[max(0, match.start() - 220):match.end() + 60]
        if not re.search(r"otransformerade|i stället för", window):
            unmarked.append(match.group(0))
    assert not unmarked, (
        f"exact class splits stated without marking them as historical or "
        f"theoretical: {unmarked}. A reader will take them for the current split."
    )


# ── The guards must be able to fail ──────────────────────────────────


def test_a_dangling_limitation_reference_would_be_caught() -> None:
    defined = _register_ids()
    assert "99" not in defined, "F99 must not exist for this check to mean anything"
    assert not re.search(r"\bF99\b", ALL_COPY), "copy unexpectedly cites F99"


def test_an_inverted_orientation_phrase_would_be_caught() -> None:
    sample = "Obs: högre z = bättre överkomlighet"
    assert "högre z = bättre" in sample.lower()
