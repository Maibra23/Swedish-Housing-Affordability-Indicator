"""The three formulas, tested by the relationships they must preserve.

`src/indices/affordability.py` computes Version A, B and C, and had no direct
tests until now — the module R1 came out of, found by reading rather than by a
failure. Example-based tests would not have caught it: the defect was that
Version B pools its component z-scores, which only shows up when you vary the
panel.

So these are property tests. Each asserts a relationship the formula must hold
for any input, not a value it happens to produce for one.

See Task D1 in docs/OPTIMIZATION_PLAN.md and R5 in docs/OPEN_RISKS.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.indices.affordability import compute_all, compute_version_a, compute_version_c


def panel(**overrides) -> pd.DataFrame:
    """A minimal two-municipality, two-year panel with sane defaults."""
    base = {
        "region_code": ["0180", "2463", "0180", "2463"],
        "year": [2023, 2023, 2024, 2024],
        "median_income": [400.0, 300.0, 410.0, 305.0],
        "transaction_price_sek": [6_000_000.0, 900_000.0, 6_200_000.0, 920_000.0],
        "price_index": [300.0, 150.0, 310.0, 155.0],
        "kt_ratio": [3.0, 1.4, 3.1, 1.45],
        "policy_rate": [3.5, 3.5, 2.0, 2.0],
        "cpi_yoy_pct": [8.0, 8.0, 2.0, 2.0],
        "unemployment_rate": [5.0, 7.0, 5.2, 7.1],
        "is_imputed_income": [False, False, False, False],
    }
    base.update(overrides)
    return pd.DataFrame(base)


# ── Orientation ──────────────────────────────────────────────────────


def test_version_c_rises_with_income() -> None:
    """More income at the same price must mean better affordability."""
    poor = compute_version_c(panel())
    rich = compute_version_c(panel(median_income=[800.0, 600.0, 820.0, 610.0]))
    assert (rich > poor).all(), "Version C fell when income rose"


def test_version_c_falls_with_price() -> None:
    cheap = compute_version_c(panel())
    dear = compute_version_c(
        panel(transaction_price_sek=[12_000_000.0, 1_800_000.0, 12_400_000.0, 1_840_000.0])
    )
    assert (dear < cheap).all(), "Version C rose when prices rose"


def test_version_a_and_c_agree_on_direction() -> None:
    """Both are affordability ratios; they must move the same way on income."""
    a_poor, c_poor = compute_version_a(panel()), compute_version_c(panel())
    rich = panel(median_income=[800.0, 600.0, 820.0, 610.0])
    assert (compute_version_a(rich) > a_poor).all()
    assert (compute_version_c(rich) > c_poor).all()


# ── The real-rate floor ──────────────────────────────────────────────


def test_negative_real_rate_is_floored_not_propagated() -> None:
    """2020-2021 had negative real rates. Without a floor, C flips sign.

    Documented as limitation M4. A negative denominator would make a more
    expensive municipality score *better*, which is the orientation contract
    inverted — the Finding N failure mode arriving through arithmetic.
    """
    negative = panel(policy_rate=[0.0, 0.0, 0.0, 0.0], cpi_yoy_pct=[10.0, 10.0, 10.0, 10.0])
    values = compute_version_c(negative)
    assert (values > 0).all(), "Version C went non-positive under a negative real rate"
    assert np.isfinite(values).all()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "R12: a zero price divides to infinity rather than being guarded. Not "
        "reachable today — the panel has no zeros and a minimum of 260 000 SEK — "
        "so this documents a latent gap rather than a live defect. Marked xfail "
        "instead of being fixed, because changing the formula changes every "
        "published z_* and that is a decision, not a tidy-up. If this starts "
        "passing, someone added the guard: remove the marker and close R12."
    ),
)
def test_zero_price_does_not_return_infinity() -> None:
    """Defensive: a missing price must not produce inf and poison a z-score.

    An infinite value in `version_c` would propagate through the within-year
    z-score and make every other municipality's `z_c` NaN — one bad row silently
    voiding a whole year.
    """
    values = compute_version_c(
        panel(transaction_price_sek=[0.0, 900_000.0, 0.0, 920_000.0])
    )
    assert not np.isinf(values).any(), "a zero price produced infinity"


# ── Version B pools; that is the point of R1 ──────────────────────────


def test_version_b_depends_on_panel_composition() -> None:
    """The property behind R1, asserted so nobody 'fixes' it by accident.

    B z-scores its components across the whole frame, so adding rows changes
    every existing value. That is deliberate (D5) — it is what lets B carry a
    time trend — and it is why `complete_case()` must filter before scoring.
    If this test ever fails, B stopped pooling and R1 is obsolete.
    """
    small = compute_all(panel())
    wide = panel()
    extra = wide.iloc[[0]].copy()
    extra["region_code"] = "9999"
    extra["policy_rate"] = 25.0
    combined = compute_all(pd.concat([wide, extra], ignore_index=True))

    shared = combined.iloc[: len(small)]["version_b"].to_numpy()
    assert not np.allclose(shared, small["version_b"].to_numpy()), (
        "version_b no longer responds to panel composition; re-read R1"
    )


def test_version_a_and_c_do_not_depend_on_panel_composition() -> None:
    """A and C are row-wise. Adding a municipality must not move them."""
    small = compute_all(panel())
    wide = panel()
    extra = wide.iloc[[0]].copy()
    extra["region_code"] = "9999"
    combined = compute_all(pd.concat([wide, extra], ignore_index=True))

    for column in ("version_a", "version_c"):
        shared = combined.iloc[: len(small)][column].to_numpy()
        assert np.allclose(shared, small[column].to_numpy(), equal_nan=True), (
            f"{column} changed when an unrelated municipality was added"
        )
