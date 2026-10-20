"""The formulas a reader sees must be the formulas the code computes.

Sida 06 rendered the withdrawn real-rate formulas, `max(R − π, 0,005)` and all,
for a while after the index became a cash-flow share: the LaTeX lived as string
literals in two page scripts and nothing compared them with the code. They now
live in `src/ui/formulas.py`, and these tests tie them to the constants in
`src/indices/cost_model.py` and to the pages that render them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.indices.cost_model import EARNERS, INTEREST_DEDUCTION, LOAN_TO_VALUE
from src.ui import formulas

ROOT = Path(__file__).resolve().parents[1]


def _sv(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", "{,}")


@pytest.mark.parametrize("latex", [formulas.VERSION_A, formulas.VERSION_C])
def test_a_and_c_state_the_cost_model_constants(latex: str) -> None:
    assert _sv(LOAN_TO_VALUE) in latex
    assert f"{EARNERS} \\cdot I" in latex
    assert "max" not in latex, "a rate floor is back in a displayed formula"


def test_c_states_the_deduction_and_amortisation() -> None:
    assert f"(1 - {_sv(INTEREST_DEDUCTION)})" in formulas.VERSION_C
    assert "a(t)" in formulas.VERSION_C


def test_b_reads_the_mortgage_rate_and_kpif() -> None:
    assert "z(r)" in formulas.VERSION_B and "KPIF" in formulas.VERSION_B


@pytest.mark.parametrize("page", ["02_Lan_jamforelse.py", "06_Metodologi.py"])
def test_no_page_writes_its_own_formula(page: str) -> None:
    source = (ROOT / "pages" / page).read_text(encoding="utf-8")
    assert "\\frac" not in source and "st.latex(r" not in source, (
        f"{page} carries a formula literal; render one from src/ui/formulas.py"
    )
