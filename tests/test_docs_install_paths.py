"""The install docs must describe the install that exists, and the vintage the data has.

Three claims in `README.md` and `docs/DEPLOYMENT.md` had come loose from the repo:
a troubleshooting note telling the reader to uninstall `streamlit-echarts`, which
was never a dependency; a single `pip install -e .` that no longer describes how
the app is deployed; and no statement anywhere of how old the data actually is.
See Finding I and Finding L, task T2.3.

The vintage assertions are the point of this file. A number typed into prose is
exactly the kind of claim that survives the refresh that falsified it — the same
defect T1.10 removed from the UI — so the expected values are read from the
provenance artifact and the documents must agree with it.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from src.provenance import complete_case_max_year, first_year, n_kommuner

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DEPLOYMENT = ROOT / "docs" / "DEPLOYMENT.md"

INSTALL_DOCS = {"README.md": README, "docs/DEPLOYMENT.md": DEPLOYMENT}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── The note about a package that was never a dependency ─────────────


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_no_streamlit_echarts_reference(name: str, path: Path) -> None:
    assert "echarts" not in _text(path).lower(), (
        f"{name} still tells the reader to manage `streamlit-echarts`, which is not "
        "and never was a dependency of this project"
    )


# ── Two audiences, two install paths ─────────────────────────────────


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_runtime_install_path_is_documented(name: str, path: Path) -> None:
    assert re.search(r"pip install\s+-r\s+requirements\.txt", _text(path)), (
        f"{name} does not document `pip install -r requirements.txt` — the install "
        "Streamlit Community Cloud actually performs"
    )


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_pipeline_install_path_is_documented(name: str, path: Path) -> None:
    assert re.search(r"""pip install\s+-e\s+["']?\.\[pipeline\]""", _text(path)), (
        f"{name} does not document the `.[pipeline]` extra, so a reader cannot "
        "discover how to refresh the data at all"
    )


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_bare_editable_install_is_no_longer_offered_as_the_way_to_run(
    name: str, path: Path
) -> None:
    """`pip install -e .` alone installs no forecast toolchain and is not the deploy."""
    bare = re.findall(r"pip install\s+-e\s+\.(?!\[)", _text(path))
    assert not bare, (
        f"{name} still offers a bare `pip install -e .`: {bare}. It is neither "
        "install path — say which audience is being addressed."
    )


# ── The stated vintage must be the artifact's vintage ────────────────


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_documented_vintage_matches_the_artifact(name: str, path: Path) -> None:
    year = complete_case_max_year()
    assert str(year) in _text(path), (
        f"{name} never states the data vintage; the composite index ends at {year}"
    )


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_income_is_named_as_the_binding_series(name: str, path: Path) -> None:
    """Why the index stops where it does, not merely that it does.

    Prices, unemployment and the price index run ahead of income. Income is the
    series that holds the complete case back, so a reader who does not know that
    will keep expecting a refresh to move the index forward. It will not.
    """
    text = _text(path).lower()
    assert "inkomst" in text or "income" in text, (
        f"{name} does not name income as the series that bounds the index"
    )


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_no_stale_index_period_or_count(name: str, path: Path) -> None:
    """Any period or count stated must be the one the artifact records."""
    text = _text(path)

    for match in re.findall(r"\b(\d{4})\s*[–—-]\s*(\d{4})\b", text):
        start, end = int(match[0]), int(match[1])
        # Upstream source windows legitimately start earlier than the index.
        if start == first_year():
            assert end == complete_case_max_year(), (
                f"{name} states the index period as {start}–{end}; the artifact says "
                f"{first_year()}–{complete_case_max_year()}"
            )

    for count in re.findall(r"\b(\d{3})\s+(?:Swedish\s+)?municipalit|\b(\d{3})\s+kommun", text):
        stated = int(next(c for c in count if c))
        assert stated == n_kommuner(), (
            f"{name} states {stated} municipalities; the panel has {n_kommuner()}"
        )


# ── The interpreter the docs promise ─────────────────────────────────


@pytest.mark.parametrize("name,path", INSTALL_DOCS.items())
def test_documented_python_version_is_consistent_with_pyproject(name: str, path: Path) -> None:
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    spec = SpecifierSet(
        tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
            "requires-python"
        ]
    )
    for stated in re.findall(r"Python[^0-9\n]{0,12}(3\.\d+)", _text(path)):
        assert Version(f"{stated}.0") in spec, (
            f"{name} promises Python {stated}, which pyproject's {spec} excludes"
        )
