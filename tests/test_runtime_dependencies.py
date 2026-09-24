"""`requirements.txt` must list what the running app imports — no more, no less.

Streamlit Community Cloud installs from `requirements.txt` and then boots the
app. Every package in that file is build time on a cold start, and `prophet` and
`pmdarima` both compile: they pull a C/C++ toolchain and, in Prophet's case,
Stan. Neither is imported by any page — they belong to the refresh pipeline,
which runs on a developer's machine, not on the server. Shipping them made
deploys slow and fragile for no runtime benefit. See Finding I, task T2.1.

The failure mode in the other direction is worse and quieter: a page grows an
`import scipy`, nothing in the repo notices, and the app crashes on the next
cold start while working perfectly in the developer's environment, which has
scipy installed for something else.

So the expected set is not written down here. It is **derived** from the import
graph, walked from `app.py` and `pages/*.py` through first-party code, and then
compared against the file. Add an import, and this test tells you which line to
add to `requirements.txt`.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"

# PyPI distribution names for import names that differ.
DISTRIBUTION: dict[str, str] = {}

# Required at runtime but never imported by name, so the graph cannot see them.
# Each entry has to justify itself in `test_indirect_dependencies_are_justified`.
INDIRECT = {"pyarrow": "pandas needs it to read the .parquet artifacts"}

# Refresh-pipeline packages. These must not reach the deploy environment.
PIPELINE_ONLY = {"prophet", "pmdarima", "statsmodels", "requests"}


def _imports(path: Path) -> list[str]:
    """Every module name imported by `path`, including inside function bodies."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module)
    return names


def _first_party_path(module: str) -> Path | None:
    base = ROOT / Path(*module.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.exists():
            return candidate
    return None


def runtime_third_party() -> set[str]:
    """Top-level third-party packages reachable from the Streamlit entrypoints."""
    queue = [ROOT / "app.py"] + sorted((ROOT / "pages").glob("*.py"))
    seen: set[Path] = set()
    third: set[str] = set()

    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        for module in _imports(current):
            top = module.split(".")[0]
            if top == "src":
                resolved = _first_party_path(module)
                assert resolved is not None, f"unresolved first-party import {module!r}"
                queue.append(resolved)
            elif top not in sys.stdlib_module_names:
                third.add(top)
    return third


def _declared() -> set[str]:
    """Distribution names listed in requirements.txt, lowercased."""
    lines = REQUIREMENTS.read_text(encoding="utf-8").splitlines()
    return {
        re.split(r"[<>=!~\[;]", line.strip(), maxsplit=1)[0].strip().lower()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    }


def _expected() -> set[str]:
    imported = {DISTRIBUTION.get(name, name) for name in runtime_third_party()}
    return {name.lower() for name in imported | set(INDIRECT)}


# ── The graph and the file must agree ────────────────────────────────


def test_requirements_file_exists() -> None:
    assert REQUIREMENTS.exists(), (
        "Streamlit Community Cloud installs from requirements.txt; without it the "
        "deploy falls back to the full pyproject dependency set"
    )


def test_every_runtime_import_is_declared() -> None:
    missing = _expected() - _declared()
    assert not missing, (
        f"imported at runtime but absent from requirements.txt: {sorted(missing)} — "
        "the app will crash on a cold start in a clean environment"
    )


def test_nothing_extra_is_declared() -> None:
    extra = _declared() - _expected()
    assert not extra, (
        f"declared but never imported by the running app: {sorted(extra)} — "
        "each one is build time and failure surface on every cold start"
    )


def test_pipeline_packages_are_absent() -> None:
    present = _declared() & PIPELINE_ONLY
    assert not present, (
        f"refresh-pipeline packages in the runtime file: {sorted(present)}. "
        "prophet and pmdarima compile from source on Streamlit Cloud."
    )


def test_pipeline_packages_are_genuinely_unused_at_runtime() -> None:
    """The claim behind the exclusion, asserted rather than assumed."""
    leaked = runtime_third_party() & PIPELINE_ONLY
    assert not leaked, (
        f"{sorted(leaked)} is reachable from a page, so excluding it from "
        "requirements.txt would break the deployed app"
    )


def test_every_requirement_pins_a_lower_bound() -> None:
    unpinned = [
        line.strip()
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip()
        and not line.strip().startswith("#")
        and not re.search(r"[><=~]=", line)
    ]
    assert not unpinned, f"no lower bound, so a resolver may pick anything: {unpinned}"


def test_every_requirement_caps_the_next_major() -> None:
    """An unverified major version must not reach production unannounced.

    The bounds were lower-only, on the reasoning that Streamlit Cloud rebuilds
    periodically and an upper pin would rot. The clean-environment check in T2.5
    showed what that resolves to: pandas 3.0.5 and numpy 2.5.3 against the 2.3.3
    and 1.26.2 the app was verified on — two major-version boundaries crossed
    without anyone choosing it. Everything passed, so the caps below sit *above*
    what is known to work; the point is to stop the *next* boundary arriving
    silently, not to pin to the oldest thing that runs.

    See R7 in docs/OPEN_RISKS.md.
    """
    uncapped = [
        line.strip()
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip()
        and not line.strip().startswith("#")
        and "<" not in line
    ]
    assert not uncapped, (
        "no upper bound, so the next major release deploys untested: "
        f"{uncapped}"
    )


def test_requirements_and_pyproject_agree_on_versions_not_just_names() -> None:
    """Two files claiming different versions of the same truth is the drift itself."""
    import tomllib

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = {
        spec.strip().lower().replace(" ", "")
        for spec in pyproject["project"]["dependencies"]
    }
    required = {
        line.strip().lower().replace(" ", "")
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert declared == required, (
        "pyproject and requirements.txt disagree on version specifiers — "
        f"only in pyproject: {sorted(declared - required)}; "
        f"only in requirements: {sorted(required - declared)}"
    )


def test_indirect_dependencies_are_justified() -> None:
    """`pyarrow` is in the file but in no import statement. Prove it is needed."""
    readers = [
        path.relative_to(ROOT).as_posix()
        for path in [ROOT / "app.py", *(ROOT / "pages").glob("*.py"), *(ROOT / "src").rglob("*.py")]
        if "read_parquet" in path.read_text(encoding="utf-8")
    ]
    assert readers, (
        "nothing reads parquet any more, so pyarrow should leave INDIRECT and "
        "requirements.txt together"
    )


def test_the_graph_walker_sees_transitive_imports() -> None:
    """A walker that stopped at the entrypoints would miss most of the truth.

    `folium` and `branca` are imported only by `src/ui/choropleth.py`, two hops
    from `app.py`. `streamlit_folium` used to be the third name here; dropping
    `folium_static` for `st.components.v1.html` removed the last import of it,
    and the guard above caught that the distribution was still declared.
    """
    assert {"folium", "branca"} <= runtime_third_party()
