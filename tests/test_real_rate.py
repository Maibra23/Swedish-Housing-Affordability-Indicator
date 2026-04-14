"""Unit tests for real interest rate computation (Task 2.1)."""

import pandas as pd
import pytest
from pathlib import Path

from indices.real_rate import compute_real_rate

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture
def national_panel():
    return pd.read_parquet(DATA_DIR / "panel_national.parquet")


@pytest.fixture
def real_rate(national_panel):
    return compute_real_rate(national_panel)


def test_real_rate_2022_negative(real_rate):
    """2022: inflation (8.35%) > policy rate (0.77%) → negative real rate."""
    row = real_rate[real_rate["year"] == 2022]
    assert len(row) == 1
    assert row.iloc[0]["real_rate"] < 0, "2022 real rate should be negative"


def test_real_rate_2024_positive(real_rate):
    """2024: policy rate (3.63%) > inflation (2.86%) → positive real rate."""
    row = real_rate[real_rate["year"] == 2024]
    assert len(row) == 1
    assert row.iloc[0]["real_rate"] > 0, "2024 real rate should be positive"


def test_floor_activates(real_rate):
    """Floor (0.5 pp) should activate for at least one year."""
    assert real_rate["is_floored"].any(), "Floor should activate in at least one year"
    # Where floored, floored value should be exactly 0.5
    floored_rows = real_rate[real_rate["is_floored"]]
    for _, row in floored_rows.iterrows():
        assert row["real_rate_floored"] == 0.5


def test_floored_never_below_threshold(real_rate):
    """Floored real rate should never be below 0.5."""
    assert (real_rate["real_rate_floored"] >= 0.5).all()
