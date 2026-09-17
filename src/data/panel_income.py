"""Forward-fill of the income series, extracted from three inlined copies.

Income ends a year before prices, unemployment and the policy rate. To keep the
panel rectangular, `build_panel` extends it with 3 % nominal growth per year (F9)
and flags every filled row with `is_imputed_income` — the flag
`step_compute_indices` filters on before scoring, so an imputed year cannot
re-base Version B (T2.4).

That logic was written three times, once per panel level, and the three copies
were verified byte-identical before this extraction. This is the one copy. It is
pure: a frame in, a frame out, no file access — which is what makes it testable
at all, since `data/raw/` is gitignored and the `build_*` functions cannot run
without it.

See Task D2 in docs/OPTIMIZATION_PLAN.md and R5 in docs/OPEN_RISKS.md.
"""

from __future__ import annotations

import pandas as pd

# 3 % nominal growth per year. Zero growth was the earlier, pessimistic
# assumption that F9 replaced; see docs/METHODOLOGY.md.
IMPUTED_INCOME_GROWTH_RATE = 0.03


def impute_income_forward(
    panel: pd.DataFrame,
    through_year: int,
    *,
    growth_rate: float = IMPUTED_INCOME_GROWTH_RATE,
) -> pd.DataFrame:
    """Extend the panel to `through_year` with compound nominal income growth.

    A faithful extraction of the three inlined loops, including two details that
    are easy to get wrong and were wrong in this task's first draft:

    **The anchor year is global, not per region.** The original takes
    `panel["year"].max()` once and copies every row at that year. A per-region
    anchor would be different behaviour — arguably better, since it would also
    fill a region whose series ended early — but it is a change, not a move, and
    on today's data every region ends at the same year, so an artifact diff would
    *not* catch the difference. Do not silently improve it here.

    **`median_income_tkr` is scaled by the same factor.** Omitting it leaves the
    thousands column at the ungrown value while `median_income` moves, breaking
    the 1000x relationship the panel maintains.

    Args:
        panel: Frame with `year`, `median_income`, and optionally
            `median_income_tkr` and `is_imputed_income`.
        through_year: Last year to fill, inclusive. Nothing is added when it is at
            or below the panel's last year.
        growth_rate: Annual nominal growth, as a fraction.

    Returns:
        The input plus a copy of the final year's rows for each missing year,
        income scaled compoundly and `is_imputed_income` True. Observed rows are
        never modified.
    """
    result = panel.copy()
    if result.empty:
        return result

    anchor_year = int(result["year"].max())
    for fill_year in range(anchor_year + 1, through_year + 1):
        fill = result[result["year"] == anchor_year].copy()
        fill["year"] = fill_year
        factor = (1 + growth_rate) ** (fill_year - anchor_year)
        fill["median_income"] = fill["median_income"] * factor
        if "median_income_tkr" in fill.columns:
            fill["median_income_tkr"] = fill["median_income_tkr"] * factor
        fill["is_imputed_income"] = True
        result = pd.concat([result, fill], ignore_index=True)

    if "is_imputed_income" not in result.columns:
        result["is_imputed_income"] = False
    result["is_imputed_income"] = result["is_imputed_income"].fillna(False).astype(bool)
    return result
