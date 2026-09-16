"""Cached readers for the committed data artifacts.

Streamlit re-executes a page top to bottom whenever any widget changes, so a bare
`pd.read_parquet` at page scope re-read the file on every interaction — every year
pill, every risk toggle. The files are small (0.2–0.3 MB) so this was never the
dominant cost, but it is pure waste and it grows with the panel.

`@st.cache_data` also gives copy-on-return semantics, so a page mutating what it
receives cannot corrupt what the next page reads.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"


@st.cache_data(show_spinner=False)
def load(name: str) -> pd.DataFrame:
    """Read a processed artifact by filename, cached for the session.

    Args:
        name: File name inside `data/processed`, e.g. "affordability_ranked.parquet".

    Returns:
        The frame. Streamlit returns a copy, so callers may mutate freely.

    Raises:
        FileNotFoundError: If the artifact is missing — it is committed, so its
            absence means a broken checkout rather than a stale pipeline.
    """
    path = PROCESSED / name
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {path}")
    return pd.read_parquet(path)
