"""The sentence Sida 02 states about Version A, held to the year it describes.

Version A was removed from the Robusthet class table, where its counts were
`risk_c`'s under another name, and replaced by one figure in the comparison
expander: what the inflation adjustment is worth. The figure is `version_c /
version_a` for the selected year.

That trade is only an improvement while the sentence around the figure is true,
and for nine of the eleven years the obvious sentence is false. Both formulas
clip their rate — A at 0,1 pp, C at 0,5 pp — and the clips bind in 2015 to 2023.
In 2015 to 2021 the factor is 0,1/0,5 = 0,20, two constants divided, carrying no
information about inflation whatsoever. In 2022 and 2023 it is the nominal rate
over C's floor. Only 2014 and 2024 give `R / (R - pi)`.

So a fixed "4,71× in 2024" in the copy would have been the same defect as A's
duplicated column, one paragraph further down the page: a number that looks like
evidence and is not. These tests pin the selection rather than the prose — they
compare against the label the branch should have chosen, so rewording a sentence
does not fail them, but choosing the wrong one does.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.indices.agreement import (
    NOMINAL_RATE_FLOOR_PP,
    REAL_RATE_FLOOR_PP,
    InflationAdjustment,
    inflation_adjustment,
)
from src.ui.interpret import explain_inflation_adjustment
from src.ui.labels import L

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "data" / "processed" / "affordability_municipal.parquet"

#: The claim only an unfloored year may make. Load-bearing: it is the whole
#: reason Version A is still computed and still shown.
THE_CLAIM = "Inflationsjusteringen är värd"


@pytest.fixture(scope="module")
def municipal() -> pd.DataFrame:
    return pd.read_parquet(ARTIFACT)


def _adjustment(
    *, factor: float, nominal: float, real: float, spread: float = 0.0, n_rows: int = 290
) -> InflationAdjustment:
    return InflationAdjustment(
        year=2024,
        factor=factor,
        spread=spread,
        n_rows=n_rows,
        nominal_rate=nominal,
        real_rate=real,
    )


# ── One branch per situation ─────────────────────────────────────────


def test_an_unfloored_year_states_the_inflation_adjustment() -> None:
    """Neither clip binds, so the factor is R / (R - pi) and may be named as such."""
    text = explain_inflation_adjustment(
        _adjustment(factor=4.7114, nominal=3.63, real=0.77)
    )
    assert text == L("lj.inflationsjusteringen_ar_vard_v0", v0="4,71", v1="2024")


def test_a_floored_real_rate_withdraws_the_claim_and_says_why() -> None:
    """2022 and 2023: the factor is the nominal rate over a constant."""
    text = explain_inflation_adjustment(
        _adjustment(factor=6.9283, nominal=3.46, real=-5.19)
    )
    assert text == L(
        "lj.skillnaden_mellan_a_och_c_ar_inte_inflationsjusteringen",
        v0="6,93",
        v1="2024",
        v2="−5,19",
        v3="0,5",
    )


def test_two_floored_rates_are_reported_as_two_constants() -> None:
    """2015 to 2021: 0,1/0,5, which is a property of the floors and nothing else."""
    text = explain_inflation_adjustment(
        _adjustment(
            factor=NOMINAL_RATE_FLOOR_PP / REAL_RATE_FLOOR_PP, nominal=-0.5, real=-2.45
        )
    )
    assert text == L(
        "lj.bada_formlerna_raknar_med_sina_golv", v0="0,20", v1="2024", v2="0,1", v3="0,5"
    )


def test_a_floored_nominal_rate_alone_is_reported_as_the_floor_it_is() -> None:
    """Possible rather than observed: a zero rate under deflation.

    Unreached by this panel — 2015's inflation was only −0,03, so the real rate
    was floored too — but the branch exists because the alternative is a sentence
    that silently becomes wrong if deflation ever returns at the lower bound.
    """
    text = explain_inflation_adjustment(
        _adjustment(factor=0.1, nominal=0.0, real=1.0)
    )
    assert text == L(
        "lj.bankversionen_raknar_med_sitt_golv", v0="0,10", v1="2024", v2="0,1"
    )


def test_a_factor_that_is_not_national_is_reported_as_a_defect() -> None:
    """One stated number requires one true number; the median would hide the rest."""
    text = explain_inflation_adjustment(
        _adjustment(factor=4.7114, nominal=3.63, real=0.77, spread=0.5)
    )
    assert text == L(
        "lj.skillnaden_mellan_a_och_c_varierar", v0="4,71", v1="2024", v2="5e-01"
    )


def test_an_unscored_year_states_no_factor(municipal: pd.DataFrame) -> None:
    adjustment = inflation_adjustment(municipal, int(municipal["year"].min()) - 1)
    assert explain_inflation_adjustment(adjustment) == L(
        "lj.skillnaden_mellan_a_och_c_varierar",
        v0="0,00",
        v1=str(adjustment.year),
        v2="0e+00",
    )


# ── Across the real panel ────────────────────────────────────────────


def test_only_an_unfloored_year_calls_the_factor_an_inflation_adjustment(
    municipal: pd.DataFrame,
) -> None:
    """The defect this replaced A's table row with, guarded year by year."""
    for year in sorted(municipal["year"].unique()):
        adjustment = inflation_adjustment(municipal, int(year))
        text = explain_inflation_adjustment(adjustment)
        claims_it = THE_CLAIM in text

        assert claims_it == adjustment.is_an_inflation_adjustment, (
            f"{year}: the page {'claims' if claims_it else 'does not claim'} an "
            f"inflation adjustment while the rate floors say otherwise "
            f"(R={adjustment.nominal_rate:.2f}, real={adjustment.real_rate:.2f}). "
            f"A floored year's factor is a quotient of constants."
        )


def test_every_year_states_its_factor(municipal: pd.DataFrame) -> None:
    """Whatever the floors do, the reader is shown the number it is about."""
    for year in sorted(municipal["year"].unique()):
        adjustment = inflation_adjustment(municipal, int(year))
        rendered = f"{adjustment.factor:.2f}".replace(".", ",")
        assert rendered in explain_inflation_adjustment(adjustment), (
            f"{year}: the sentence does not contain the factor {rendered} it describes"
        )


# ── The documents that quote the figure ──────────────────────────────

#: Everywhere the factor is written out in prose. The README's copy is also
#: checked by `tests/test_readme_figures.py`, which owns the demo table; this
#: catches the other three, which nothing else reads.
DOCS_QUOTING_THE_FACTOR = (
    "README.md",
    "docs/APP_GUIDE.md",
    "docs/ENGINE.md",
    "docs/METHODOLOGY.md",
)


@pytest.mark.parametrize("document", DOCS_QUOTING_THE_FACTOR)
def test_a_document_quoting_the_factor_quotes_the_derived_one(document: str) -> None:
    """Prose stating a number the artifacts moved is the defect this repo keeps
    finding. These four say what the latest year's factor is, so they are read.

    Both spellings are accepted: the Swedish copy writes 4,71 and the English
    walkthrough's code blocks write 4.71.
    """
    from src.provenance import complete_case_max_year

    year = complete_case_max_year()
    factor = inflation_adjustment(pd.read_parquet(ARTIFACT), year).factor
    swedish = f"{factor:.2f}".replace(".", ",")
    english = f"{factor:.2f}"

    text = (ROOT / document).read_text(encoding="utf-8")
    assert swedish in text or english in text, (
        f"{document} does not state {swedish} as the {year} A-to-C factor. The "
        f"artifacts moved; the prose has to move with them, and the year it is "
        f"attributed to has to be checked as well as the value."
    )
