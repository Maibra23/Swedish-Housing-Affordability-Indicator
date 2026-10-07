"""The component split on Sida 03 must be exact and must name the real driver.

It replaced a coefficient-of-variation ranking that included K/T, which is not in
the formula, and that always crowned the policy rate. See the module docstring of
`src/indices/kommun_components.py`.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from src.indices.kommun_components import COMPONENTS, attribute_change

RANKED = Path(__file__).resolve().parents[1] / "data" / "processed" / "affordability_ranked.parquet"


@pytest.fixture(scope="module")
def ranked() -> pd.DataFrame:
    return pd.read_parquet(RANKED)


def test_the_parts_multiply_to_the_whole_for_every_municipality(ranked: pd.DataFrame) -> None:
    for name, rows in ranked.groupby("region_name"):
        change = attribute_change(rows)
        product = math.prod(1 + change.parts_pct[k] / 100 for k in COMPONENTS)
        assert product == pytest.approx(1 + change.total_pct / 100, rel=1e-9), name


def test_the_driver_is_the_part_furthest_from_no_change(ranked: pd.DataFrame) -> None:
    change = attribute_change(ranked[ranked["region_name"] == "Stockholm"])
    sizes = {k: abs(math.log(1 + v / 100)) for k, v in change.parts_pct.items()}
    assert change.driver == max(sizes, key=sizes.get)


def test_k_t_is_not_a_component() -> None:
    assert "kt_ratio" not in COMPONENTS and "kt" not in " ".join(COMPONENTS)


def test_a_single_year_has_no_split(ranked: pd.DataFrame) -> None:
    one = ranked[(ranked["region_name"] == "Stockholm")].head(1)
    assert attribute_change(one) is None
