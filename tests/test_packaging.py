"""`pyproject.toml` must describe two audiences without mixing them.

The server runs the app and reads committed parquet. A developer refreshing the
data runs SCB and Riksbanken clients, Prophet and ARIMA. One dependency list for
both meant every cold start on Streamlit Cloud compiled Stan. The split is
`[project.dependencies]` for the first and the `pipeline` extra for the second,
with `requirements.txt` mirroring the first exactly. See Finding I, task T2.2.

`tests/test_runtime_dependencies.py` proves `requirements.txt` matches the import
graph. This file proves `pyproject.toml` matches `requirements.txt`. Together
they chain the deployed environment back to what the pages actually import.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
REQUIREMENTS = ROOT / "requirements.txt"

PIPELINE_ONLY = {"prophet", "pmdarima", "statsmodels", "requests"}


def _config() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _names(specifiers: list[str]) -> set[str]:
    return {
        re.split(r"[<>=!~\[;]", spec.strip(), maxsplit=1)[0].strip().lower()
        for spec in specifiers
        if spec.strip()
    }


def _requirements_names() -> set[str]:
    return _names(
        [
            line
            for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    )


# ── The two files must agree ─────────────────────────────────────────


def test_runtime_dependencies_match_requirements() -> None:
    declared = _names(_config()["project"]["dependencies"])
    assert declared == _requirements_names(), (
        "pyproject and requirements.txt disagree about what the app needs to run:\n"
        f"  only in pyproject:    {sorted(declared - _requirements_names())}\n"
        f"  only in requirements: {sorted(_requirements_names() - declared)}"
    )


def test_pipeline_packages_are_an_extra_not_a_runtime_dependency() -> None:
    config = _config()
    runtime = _names(config["project"]["dependencies"])
    assert not runtime & PIPELINE_ONLY, (
        f"refresh-only packages still in the runtime set: {sorted(runtime & PIPELINE_ONLY)}"
    )

    extras = config["project"].get("optional-dependencies", {})
    assert "pipeline" in extras, "no `pipeline` extra: the refresh toolchain is uninstallable"
    assert PIPELINE_ONLY <= _names(extras["pipeline"]), (
        f"the pipeline extra is missing {sorted(PIPELINE_ONLY - _names(extras['pipeline']))}"
    )


def test_pytest_is_not_a_runtime_dependency() -> None:
    """A test runner on the serving host is pure install cost."""
    assert "pytest" not in _names(_config()["project"]["dependencies"])


def test_no_poetry_configuration_remains() -> None:
    """`[tool.poetry] package-mode` suppressed a Poetry behaviour setuptools lacks."""
    assert "poetry" not in _config().get("tool", {}), (
        "a Poetry table in a setuptools project invites the next reader to run the "
        "wrong tool"
    )


# ── The declared interpreter range must admit the one in use ─────────


def test_requires_python_admits_the_running_interpreter() -> None:
    """A range the verified interpreter falls outside of blocks `pip install -e`."""
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    spec = SpecifierSet(_config()["project"]["requires-python"])
    running = Version(".".join(str(n) for n in sys.version_info[:3]))
    assert running in spec, (
        f"requires-python is {spec} but the suite passes on {running}; "
        "`pip install -e` refuses to install here"
    )


def test_requires_python_still_excludes_interpreters_without_tomllib() -> None:
    """`src/ui/sidebar.py` imports tomllib, which arrived in 3.11."""
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    spec = SpecifierSet(_config()["project"]["requires-python"])
    assert Version("3.10.0") not in spec
    assert "tomllib" in (ROOT / "src" / "ui" / "sidebar.py").read_text(encoding="utf-8")


# ── The suite must collect however pytest is invoked ─────────────────


def test_pythonpath_includes_the_repo_root() -> None:
    """Tests import `src.*` and `tests.sourcetools`; both resolve from the root.

    Without this the suite collects only under `python -m pytest`, which injects
    the working directory. Bare `pytest` — what editors and most CI runners
    call — failed collection on six files.
    """
    pythonpath = _config()["tool"]["pytest"]["ini_options"].get("pythonpath", [])
    assert "." in pythonpath, f"repo root absent from pytest pythonpath: {pythonpath}"


@pytest.mark.skipif(shutil.which("pytest") is None, reason="no bare pytest console script")
def test_bare_pytest_collects_the_whole_suite() -> None:
    """The structural check above, proven against the real invocation."""
    result = subprocess.run(
        [shutil.which("pytest"), "tests/", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "bare `pytest` cannot collect the suite:\n" + (result.stdout + result.stderr)[-2000:]
    )
