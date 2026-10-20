"""The three index formulas as displayed LaTeX, in one place.

Sida 02 and Sida 06 both render them. They used to carry their own string
literals, and Sida 06 kept showing the withdrawn real-rate formulas after the
index became a cash-flow share. `tests/test_formula_latex.py` ties these strings
to the constants in `src/indices/cost_model.py`, so a changed assumption fails a
test instead of leaving a stale equation on screen.
"""

from __future__ import annotations

#: Gross interest on an 85 % loan, as a percentage of two median incomes.
VERSION_A = (
    r"A(i,t) = 100 \cdot \frac{0{,}85 \cdot P_{\text{SEK}}(i,t) \cdot r(t)}{2 \cdot I(i,t)}"
)

#: The macro composite: mortgage rate and KPIF, z-scored against a frozen reference.
VERSION_B = (
    r"B(i,t) = 0{,}35 \cdot z\!\left(\frac{P_{\text{SEK}}}{I}\right) + 0{,}25 \cdot z(r)"
    r" + 0{,}20 \cdot z(U) + 0{,}20 \cdot z(\pi_{\text{KPIF}})"
)

#: Net interest after the 30 % deduction plus the required amortisation.
VERSION_C = (
    r"C(i,t) = 100 \cdot \frac{0{,}85 \cdot P_{\text{SEK}}(i,t) \cdot"
    r" \big(r(t) \cdot (1 - 0{,}3) + a(t)\big)}{2 \cdot I(i,t)}"
)
