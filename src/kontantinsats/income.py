"""Turning one person's income into a household's, in exactly one place.

`median_income` is a **median individual** figure: SCB HE0110A/SamForvInk1,
sammanräknad förvärvsinkomst, ages 20 and over. Multiplying it by a household
size is therefore valid arithmetic, and this module is the only place that does
it.

That deserves a note, because the same line was a defect until 2026-09-21. The
panel then held *household disposable* income, and Sida 04 multiplied it by two
for the Par case, producing an income no household has and understating the
couple debt ratio by about a quarter. The arithmetic was never wrong; the
premise under it was. One accessor gives the premise somewhere to be stated,
and `tests/test_variable_contracts.py` asserts that nothing else in the codebase
scales the column.

**What the Par case means, precisely.** Two median earners, not the median
couple. Those are different households and the gap between them varies by
municipality, which is worth knowing before quoting a figure:

| Kommun | Two median earners | Median household, all types |
|---|---|---|
| Danderyd | 1 020 600 | 902 000 |
| Dorotea | 627 800 | 346 800 |

Danderyd's dual-earner households make the two readings converge; Dorotea's many
single and retired households pull them apart. Neither number is wrong. They
answer different questions, and this page asks the first one: what can a
household of *this shape* afford. Recorded as limitation F14.
"""

from __future__ import annotations

from src.ui.labels import L

#: Earners per household type, keyed by the label Sida 04 shows and built from
#: `SWEDISH_LABELS` so the Swedish text is still stated exactly once. The page
#: used to carry this as an inline conditional, which put the earner count and
#: the label in two places that nothing compared.
EARNERS_BY_HOUSEHOLD_TYPE: dict[str, int] = {
    L("ki.singelhushall"): 1,
    L("ki.par_2_inkomster"): 2,
}


def household_income(individual_income: float, earners: int) -> float:
    """Combined gross income for a household of `earners` median earners.

    Args:
        individual_income: Median individual income for the region, in SEK.
            Must be a per-person figure; see the module docstring for why that
            is not a formality.
        earners: How many median earners the household has.

    Returns:
        The household's combined annual gross income, in SEK.

    Raises:
        ValueError: If `earners` is not a positive whole number, which would
            mean the caller is scaling by something other than a household size.
    """
    if earners < 1 or int(earners) != earners:
        raise ValueError(
            f"earners must be a positive whole number, got {earners!r}. This "
            f"function exists to combine median individual incomes into a "
            f"household; any other scaling of median_income needs its own "
            f"justification and its own home."
        )
    return individual_income * earners
