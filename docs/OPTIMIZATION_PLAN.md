# SHAI Optimization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development`
> or `superpowers:executing-plans` to implement this task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Cut what the app sends to the browser and how often it rebuilds it, close the
last two High risks in `docs/OPEN_RISKS.md`, and fix one visual defect found while
measuring — without adding a runtime dependency.

**Architecture:** Four independent phases. A fixes a map defect and makes the map depend on
the year alone, which collapses the cache from 77 possible entries to 11. B shrinks the
GeoJSON by 49 % through coordinate precision alone, no geometry change and no new library.
C moves the stylesheet out of the per-page payload. D puts tests under the refresh pipeline,
which is the only part of the system with none.

**Tech Stack:** Streamlit 1.55, folium/branca, pandas, pyarrow, pytest. No additions.

**Created:** 2026-09-17, after the Windows performance audit (commit `5d0ec1e`).
**Status:** IN PROGRESS — 7 / 8 tasks. Phases A, B and D complete. Only C1 remains, gated on Q2.
**Prerequisite:** `pytest tests/` (645 passed) and `python scripts/audit.py` (27 passed) must
be green before starting, so any regression is attributable.

---

## 0. Constraints that shape every task — read before planning any change

These are not preferences. Each one has already caused a defect in this project.

### Streamlit's execution model

| Constraint | What it means here |
|---|---|
| **A widget change re-runs the whole script, top to bottom.** | There is no incremental update. Per-rerun cost *is* the user-facing latency. This is why the map cache mattered: 380 ms → 50 ms. |
| **`st.cache_data` hashes its arguments.** | Hashing a DataFrame costs time proportional to its size, so caching a cheap function on a large frame can be slower than not caching. Measure. |
| **`st.cache_data` returns a copy.** | Safe against caller mutation, but it means the cached value is serialised — a 1.2 MB HTML string costs 1.2 MB per entry. |
| **Components are iframes with `srcdoc`.** | The whole map document crosses to the browser per distinct render. Payload size is the lever, not CPU. |
| **No client-side state without extra libraries.** | A filter cannot be applied in the browser. Either the server rebuilds, or the filter must not affect that element. This is the whole of Decision Q1. |
| **`server.enableStaticServing` is `False` by default.** | Files under `./static/` are served at `/app/static/...` only when it is enabled. Needed for Task C1. |

### Two constraints specific to `build_panel.py`, found by reading it

Both change how Phase D has to be sequenced, so they are here rather than buried in a task.

1. **`data/raw/` is gitignored.** Only `.gitkeep` is tracked. `build_panel._read()` raises
   `FileNotFoundError` without it, so `build_municipal_panel()` **cannot run on a fresh
   clone or in CI**. Any test that calls it would pass only on a machine that has fetched.
   Tests must therefore target *pure* functions over synthetic frames.
2. **The imputation is triplicated, not a function.** The same growth-factor loop is inlined
   three times — `build_municipal_panel` (line 320), `build_county_panel` (449),
   `build_national_panel` (541). There is nothing to import and unit-test.

Together these invert the usual order. You cannot unit-test code that is not addressable, so
the extraction has to come first, and its safety net is **artifact identity** — regenerate the
panels and diff the output — rather than unit tests. D2 does the extraction under that net;
D3 tests what it exposed. Stated plainly because "tests before refactor" is the right default
and this is a considered exception, not an oversight.

### Streamlit Community Cloud

- **~1 GB RAM.** A cache of 77 × 1.2 MB map documents is ~93 MB, a tenth of the instance, for
  an interaction nobody performs exhaustively. This is why `max_entries=24` (R11).
- **Cold start installs from `requirements.txt`.** Every added package is cold-start latency
  for every visitor after an idle sleep. See T2.1.
- **The app sleeps when idle.** Caches are lost. First view after a sleep pays full cost, so
  reducing the *uncached* path matters as much as the cache hit rate.

### This project's own rules — all test-enforced, all will fail the build

| Rule | Guard |
|---|---|
| No new runtime dependency without strong justification | `tests/test_runtime_dependencies.py` derives the expected set from the import graph |
| No module over 400 lines | `tests/test_file_sizes.py` |
| Every user-facing string in `SWEDISH_LABELS` | `tests/test_no_inline_copy.py` |
| No literal municipality count or index period | `tests/test_no_hardcoded_counts.py` |
| Every number in copy derivable from the artifacts | `tests/test_copy_matches_artifacts.py` |
| Every `docs/*.md` linked from `README.md` | `tests/test_docs_inventory.py` |
| Per-file test counts cited in a plan must be accurate | `tests/test_docs_inventory.py` |
| Every CSS class used must be defined, and documented in `DESIGN_SYSTEM.md` | `tests/test_css_naming.py`, `tests/test_design_system_doc.py` |

**TDD throughout.** Write the failing test, watch it fail, implement, watch it pass, commit.

---

## 1. Locked decisions

| # | Decision | Chosen | Rationale |
|---|----------|--------|-----------|
| L1 | How to shrink the GeoJSON | **Coordinate precision, not topology simplification** | 5 decimal places is ~1.1 m, which is far below one screen pixel at national zoom, and costs **nothing**. Topology simplification needs `shapely` or `mapshaper` — a runtime dependency for a build-time job, against T2.1. Measured: 842 KB → 430 KB, −49 %. |
| L2 | Where the shrink happens | **A committed build script, output committed** | The app must not simplify geometry at request time. `data/geo/` is committed precisely so the server does no work. |
| L3 | Whether to keep `max_entries=24` | **Yes, but it stops mattering** | Under Q1 the map depends on the year alone, so 11 entries cover everything and 24 is comfortable headroom. |

---

## 2. Open decisions

| # | Question | Blocks | Recommendation |
|---|----------|--------|----------------|
| | *Open decisions are `Q`; locked ones are `L`; tasks are `A1`–`D3`. An earlier draft numbered decisions `D1`/`D2`, which collided with Tasks D1 and D2.* | | |
| ~~**Q1**~~ | **ANSWERED 2026-09-17: No.** The map is the national picture; the pills filter the lists. Phase A proceeds as written. Should the risk-pill filter change the map at all? | A1, A2 | **No — the map is the national picture; the pills filter the lists.** Three reasons, not one. (a) It is already broken: an excluded municipality gets `_z = 0.0`, which paints `#e6e5e6` against a real median's `#e5e7eb` — indistinguishable, so filtering to "Hög" currently shows ~200 municipalities *lying* about being median. (b) The colour scale is currently built from the filtered subset, so the legend silently rescales when you touch a pill, and the same colour means different things. (c) It collapses the cache input space from 77 to 11. If you would rather the filter *did* affect the map, then A1 changes: keep passing `df_ranked`, and instead set `_z` to `None` for municipalities absent from the frame and return a neutral grey from `_style` when it is `None` — so an excluded municipality reads as excluded rather than as median. The colormap must still be built from the whole year, or the legend keeps rescaling. Accept that the cache holds 24 of 77 combinations and that R11 stays open. |
| Q2 | Enable `server.enableStaticServing` for the stylesheet? | C1 only | **Yes, with an inline fallback.** 24 KB per page load becomes one cached request. But it is unverified on Community Cloud, so the fallback is not optional. If C1 proves unreliable, mark it `SKIPPED` — this is the least valuable phase. |

---

## 3. Evidence — measured 2026-09-16/17

Every number below came from a measurement, not an estimate. Commands are in the tasks.

### Payload

| | Size | Note |
|---|---|---|
| `data/geo/kommuner.geojson` | **842 KB** | 290 features, 19 691 coordinate pairs, **9–15 decimal places** |
| Coordinate properties | 31 KB | so geometry is essentially the whole file |
| Rendered map document | **1 234 KB** | the GeoJSON embedded in folium's HTML |
| At 6 dp, minified | 469 KB | −44 % (~0.11 m) |
| **At 5 dp, minified** | **430 KB** | **−49 % (~1.1 m)** ← L1 |
| At 4 dp, minified | 392 KB | −53 % (~11 m) |
| Injected CSS | 24 KB | per page load, inline, uncacheable |

### Time (page 01, warm geojson cache)

| | Before `5d0ec1e` | After |
|---|---|---|
| Page 01 full render | 620 ms | **76 ms** |
| Year change | 380 ms | **50 ms** (cache hit) |
| Choropleth build | 520 ms | cached |
| — of which folium → HTML | **83 %** | the reason caching worked |

**Two hypotheses that measured false**, recorded so nobody re-tries them: the
`json.loads(json.dumps(...))` deep copy is 30 ms (6 %, and necessary — the features are
mutated afterwards), and the 290 label markers cost ~1 ms.

### Coverage

| | After Phase 1 | Now |
|---|---|---|
| `src/` overall | 15 % | 44 % |
| `src/indices/affordability.py` | 0 % | 65 % |
| **`src/data/build_panel.py`** | 0 % | **0 %** (346 statements) |
| **`src/data/scb_client.py`** | 0 % | **0 %** (241 statements) |
| `src/forecast/*` | 0 % | 0 % (218 statements) |

---

## 4. File structure

| File | Responsibility | Task |
|---|---|---|
| `src/ui/choropleth.py` | Modify — map takes the full year, cache keyed on year | A1, A2 |
| `pages/01_Riksoversikt.py` | Modify — pass unfiltered year data to the map | A1 |
| `tests/test_choropleth_cache.py` | **New** — cache identity and filter independence | A1, A2 |
| `scripts/shrink_geojson.py` | **New** — build step, precision + minify | B1 |
| `data/geo/kommuner.geojson` | Regenerated output, committed | B1 |
| `tests/test_geojson_payload.py` | **New** — size ceiling, precision, topology intact | B1, B2 |
| `static/shai.css` | **New** — extracted stylesheet | C1 |
| `src/ui/css.py` | Modify — link when static serving is on, inline otherwise | C1 |
| `tests/test_affordability_properties.py` | **New** — property tests on the three formulas | D1 |
| `src/data/panel_income.py` | **New** — the one imputation function, extracted from three copies | D2 |
| `tests/test_panel_income.py` | **New** — imputation over synthetic frames | D3 |

---

## 5. Progress

| Task | Title | Phase | Status |
|------|-------|-------|--------|
| A1 | Map shows every municipality; cache keyed on year | A | **DONE** |
| A2 | Assert the map is independent of the risk filter | A | **DONE** |
| B1 | `scripts/shrink_geojson.py` — 5 dp + minify | B | **DONE** |
| B2 | Payload ceiling test and render equivalence | B | **DONE** |
| C1 | Serve the stylesheet statically, with fallback | C | TODO |
| D1 | Property tests for `affordability.py` | D | **DONE** |
| D2 | De-triplicate the imputation into one pure function | D | **DONE** |
| D3 | Test the extracted function; drop the size exemption | D | **DONE** |

---

## 6. Phase A — The map defect, and the cache win it unlocks

**Goal:** the map tells the truth, and depends on the year alone.
**Exit criterion:** toggling a risk pill does not rebuild the map; no municipality is
painted a colour it did not earn. — **MET.** Risk toggles cost ~45 ms, down from ~370 ms;
no "Saknas" placeholder reaches the map; all 290 municipalities drawn on a stable, year-wide
colour scale. R11 closed.
**Gated by:** Q1 — **answered No on 2026-09-17**, so this phase is unblocked.

---

### Task A1 — Map shows every municipality; cache keyed on year · DONE

**Files:**
- Modify: `src/ui/choropleth.py` (the `_map_html` signature and `build_colormap` call)
- Modify: `pages/01_Riksoversikt.py` (the `render_choropleth` call site)
- Test: `tests/test_choropleth_cache.py` (new)

- [ ] **Step 1: Write the failing test**

Create `tests/test_choropleth_cache.py`:

```python
"""The map depends on the year, and on nothing else.

Two defects in one. An excluded municipality used to reach `_style` with
`_z = 0.0`, which `colormap` paints `#e6e5e6` — indistinguishable from a real
median's `#e5e7eb`. So filtering to "Hög" showed roughly 200 municipalities
claiming to be average. And because `build_colormap` was fed the *filtered*
subset, the legend rescaled whenever a pill moved: the same colour meant
different things before and after a click.

Making the map take the whole year fixes both and collapses the cache input space
from 11 years x 7 risk combinations to 11. See Decision Q1.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.ui.choropleth import _map_html

ARTIFACT = "data/processed/affordability_ranked.parquet"


@pytest.fixture(scope="module")
def year_frame() -> pd.DataFrame:
    ranked = pd.read_parquet(ARTIFACT)
    return ranked[ranked["year"] == ranked["year"].max()]


def test_a_filtered_frame_produces_a_different_map(year_frame: pd.DataFrame) -> None:
    """`_map_html` renders what it is handed — that is correct and worth pinning.

    An earlier draft of this test asserted the opposite: that filtering could not
    change the output. It can, and it should. The function is not where the fix
    lives; the fix is that the *page* stops handing it a filtered frame, which
    `test_the_page_does_not_hand_the_map_a_filtered_frame` asserts structurally.

    Keeping this test the right way round matters: if it ever starts passing,
    `_map_html` has begun ignoring its input.
    """
    full = _map_html(year_frame)
    high_only = _map_html(year_frame[year_frame["risk_c"] == "hog"])
    assert full != high_only, "_map_html ignored its data argument"


def test_a_full_year_produces_one_cache_entry_per_year() -> None:
    """The point of Q1: eleven inputs, not seventy-seven."""
    ranked = pd.read_parquet(ARTIFACT)
    years = sorted(ranked["year"].unique())
    documents = {_map_html(ranked[ranked["year"] == year]) for year in years}
    assert len(documents) == len(years), (
        "two years rendered identically; the map is not varying with its data"
    )


def test_every_municipality_is_drawn(year_frame: pd.DataFrame) -> None:
    html = _map_html(year_frame)
    for name in year_frame["region_name"].head(20):
        assert str(name) in html, f"{name} is missing from the map"


def test_no_municipality_is_painted_without_data(year_frame: pd.DataFrame) -> None:
    """The colour that caused this task: a real median, not a stand-in for absent."""
    html = _map_html(year_frame)
    assert "Saknas" not in html, (
        'a feature carries "Saknas" placeholders, so it was drawn without data'
    )
```

- [ ] **Step 2: Run it and watch it fail**

```bash
python -m pytest tests/test_choropleth_cache.py -v
```

Expected: `test_map_is_identical_whatever_the_risk_filter` FAILS — the two documents
differ, because the filtered call draws fewer municipalities with data and rescales the
colormap.

- [ ] **Step 3: Make the map take the whole year**

**The only functional change is at the call site.** `_map_html` already derives both the
colour domain and the per-feature data from whatever frame it is handed, so passing the
unfiltered year fixes the colormap rescaling and the `_z = 0.0` painting at once, with no
change to `choropleth.py` logic. Add only a comment there, above the existing
`colormap = build_colormap(...)` line, so the next reader knows the input is load-bearing:

```python
    # This must be the whole year, not a filtered subset. When it was the subset,
    # moving a risk pill rescaled the legend and the same colour meant different
    # things before and after the click. See Q1 in docs/OPTIMIZATION_PLAN.md.
```

Then change the call site in `pages/01_Riksoversikt.py` from

```python
            render_choropleth(df_ranked, key="rv_choropleth")
```

to

```python
            # The whole year, not `df_ranked`: the map is the national picture and the
            # risk pills filter the lists below it. Passing the filtered frame painted
            # excluded municipalities in the median colour and rescaled the legend on
            # every pill click. See Decision Q1 in docs/OPTIMIZATION_PLAN.md.
            render_choropleth(mun_year, key="rv_choropleth")
```

- [ ] **Step 4: Run the test and the render sweep**

```bash
python -m pytest tests/test_choropleth_cache.py tests/test_pages_render.py -q
```

Expected: PASS, 81 renders clean.

- [ ] **Step 5: Confirm the cache now holds every year**

```bash
python -c "import sys; sys.path.insert(0,'.'); from src.ui.choropleth import _map_html; import pandas as pd; r=pd.read_parquet('data/processed/affordability_ranked.parquet'); [_map_html(r[r.year==y]) for y in sorted(r.year.unique())]; print(_map_html.__wrapped__ is not None)"
```

Expected: no error. Eleven distinct entries, under the `max_entries=24` ceiling.

- [ ] **Step 6: Commit**

```bash
git add src/ui/choropleth.py pages/01_Riksoversikt.py tests/test_choropleth_cache.py
git commit -m "fix: map renders the whole year, not the risk-filtered subset"
```

---

### Task A2 — Assert the map is independent of the risk filter · DONE

**Files:**
- Modify: `tests/test_choropleth_cache.py`
- Modify: `docs/OPEN_RISKS.md` (close R11)

- [ ] **Step 1: Add the cache-behaviour test**

Append to `tests/test_choropleth_cache.py`:

```python
def test_the_page_does_not_hand_the_map_a_filtered_frame() -> None:
    """Structural, because the behavioural test above cannot see the call site."""
    import ast
    from pathlib import Path

    page = Path("pages/01_Riksoversikt.py")
    tree = ast.parse(page.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "render_choropleth"
        ):
            first = ast.unparse(node.args[0]) if node.args else ""
            assert "df_ranked" not in first, (
                f"the map is passed {first!r}, which the risk pills have filtered"
            )
            return
    raise AssertionError("no render_choropleth call found on page 01")
```

- [ ] **Step 2: Run it**

```bash
python -m pytest tests/test_choropleth_cache.py -q
```

Expected: PASS.

- [ ] **Step 3: Close R11 in the register**

In `docs/OPEN_RISKS.md`, change the R11 row status from `**ACCEPTED**` to `**CLOSED**`
and append to its section:

```markdown
### CLOSED 2026-09-17

Dissolved rather than mitigated. Decision Q1 made the map depend on the year alone, so the
input space is 11 entries rather than 77 and `max_entries=24` is comfortable headroom
instead of a rationed ceiling. The memory table above is kept because it is the reasoning
that led to the design change.
```

- [ ] **Step 4: Full suite and audit**

```bash
python -m pytest tests/ -q && python scripts/audit.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_choropleth_cache.py docs/OPEN_RISKS.md
git commit -m "test: pin the map's independence from the risk filter; close R11"
```

---

## 7. Phase B — Payload

**Goal:** the largest asset in the app stops being 842 KB.
**Exit criterion:** the GeoJSON is under 450 KB with 290 features intact, and the rendered
map document shrinks accordingly. — **MET.** 842 KB → **428 KB** (−49.2 %), and the rendered
map document 1 234 KB → **860 KB** (−30 %). All 290 features, every property, no collapsed
ring. 102 choropleth and render tests still pass.

---

### Task B1 — `scripts/shrink_geojson.py` · DONE

**Files:**
- Create: `scripts/shrink_geojson.py`
- Modify: `data/geo/kommuner.geojson` (regenerated, committed)
- Test: `tests/test_geojson_payload.py` (new)

**Why precision and not simplification:** see L1. 5 decimal places is ~1.1 m. At national
zoom one screen pixel is roughly 400 m, so this is three orders of magnitude below
visible. Topology simplification would need `shapely`, and adding a runtime dependency to
shrink a committed build artifact is exactly backwards.

- [ ] **Step 1: Write the failing test**

Create `tests/test_geojson_payload.py`:

```python
"""The map's geometry file is the largest asset the app sends. Keep it small.

842 KB of the 1 234 KB rendered map document was this file, carried into the
browser inside folium's HTML. It stored coordinates at 9 to 15 decimal places —
sub-millimetre precision for polygons drawn at national zoom, where one screen
pixel is roughly 400 m.

Truncating to 5 decimals (~1.1 m) and minifying costs nothing visible and removes
49 % of the file. It is a build step, not a request-time one: the output is
committed, because `data/geo/` exists so the server does no work.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

GEOJSON = Path(__file__).resolve().parents[1] / "data" / "geo" / "kommuner.geojson"
CEILING_KB = 450
MAX_DECIMALS = 5


@pytest.fixture(scope="module")
def geo() -> dict:
    return json.loads(GEOJSON.read_text(encoding="utf-8"))


def test_file_is_under_the_ceiling() -> None:
    kb = GEOJSON.stat().st_size / 1024
    assert kb < CEILING_KB, (
        f"kommuner.geojson is {kb:.0f} KB, over the {CEILING_KB} KB ceiling. Run "
        "`python scripts/shrink_geojson.py`."
    )


def test_no_coordinate_carries_more_precision_than_needed() -> None:
    text = GEOJSON.read_text(encoding="utf-8")
    over = {
        match
        for match in re.findall(r"-?\d+\.(\d{6,})", text)
    }
    assert not over, (
        f"{len(over)} coordinates carry more than {MAX_DECIMALS} decimals; "
        "precision beyond ~1 m is invisible at national zoom and costs payload"
    )


def test_every_municipality_survived(geo: dict) -> None:
    """Shrinking must not drop a feature — the whole point is 290 polygons."""
    assert len(geo["features"]) == 290


def test_every_feature_keeps_the_properties_the_map_needs(geo: dict) -> None:
    for feature in geo["features"]:
        props = feature["properties"]
        for key in ("id", "kom_namn", "lan_code", "geo_point_2d"):
            assert key in props, f"feature lost {key!r}"


def test_no_geometry_became_degenerate(geo: dict) -> None:
    """Rounding can collapse a ring. A polygon needs at least four positions."""
    thin = []
    for feature in geo["features"]:
        for ring in _rings(feature["geometry"]["coordinates"]):
            if len(ring) < 4:
                thin.append(feature["properties"].get("kom_namn"))
    assert not thin, f"rounding collapsed rings in: {sorted(set(thin))}"


def _rings(node: object) -> list[list]:
    """Every linear ring in a Polygon or MultiPolygon coordinate tree."""
    if not isinstance(node, list) or not node:
        return []
    if isinstance(node[0], (int, float)):
        return []
    if isinstance(node[0], list) and node[0] and isinstance(node[0][0], (int, float)):
        return [node]
    rings: list[list] = []
    for child in node:
        rings.extend(_rings(child))
    return rings
```

- [ ] **Step 2: Run it and watch it fail**

```bash
python -m pytest tests/test_geojson_payload.py -v
```

Expected: `test_file_is_under_the_ceiling` FAILS at 842 KB, and
`test_no_coordinate_carries_more_precision_than_needed` FAILS with thousands of matches.

- [ ] **Step 3: Write the build script**

Create `scripts/shrink_geojson.py`:

```python
"""Shrink data/geo/kommuner.geojson without changing its shape.

    python scripts/shrink_geojson.py

Coordinates arrived from the source at 9 to 15 decimal places. Five decimals is
~1.1 m; at national zoom one screen pixel is roughly 400 m, so everything past
the fifth decimal is payload nobody can see. Minifying the JSON separators
removes the rest.

Measured: 842 KB -> 430 KB, -49 %, with all 290 features and every property
intact. Verified by tests/test_geojson_payload.py.

Deliberately *not* topology simplification. That needs shapely or mapshaper, and
adding a runtime dependency to shrink a committed build artifact is backwards —
see L1 in docs/OPTIMIZATION_PLAN.md and T2.1 in docs/REVITALIZATION_PLAN.md.

Idempotent: running it twice produces the same bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

DECIMALS = 5
GEOJSON = Path(__file__).resolve().parents[1] / "data" / "geo" / "kommuner.geojson"


def round_coordinates(node: object, decimals: int = DECIMALS) -> object:
    """Round every coordinate in a GeoJSON coordinate tree.

    Args:
        node: A coordinate, a position, or any nesting of them.
        decimals: Decimal places to keep.

    Returns:
        The same structure with every number rounded.
    """
    if isinstance(node, list):
        if node and isinstance(node[0], (int, float)):
            return [round(value, decimals) for value in node]
        return [round_coordinates(child, decimals) for child in node]
    return node


def main() -> None:
    before = GEOJSON.stat().st_size
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))

    for feature in geo["features"]:
        feature["geometry"]["coordinates"] = round_coordinates(
            feature["geometry"]["coordinates"]
        )
        # `geo_point_2d` is a coordinate too — it anchors the municipality name
        # labels (`src/ui/map_labels._label_latlon`). Rounding the geometry but
        # not this leaves 580 high-precision values in the file, which fails
        # tests/test_geojson_payload.py because that scans the whole document.
        point = feature["properties"].get("geo_point_2d")
        if point is not None:
            feature["properties"]["geo_point_2d"] = round_coordinates(point)

    GEOJSON.write_text(
        json.dumps(geo, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    after = GEOJSON.stat().st_size
    print(
        f"{GEOJSON.name}: {before/1024:.0f} KB -> {after/1024:.0f} KB "
        f"({100*(1-after/before):.1f}% smaller), {len(geo['features'])} features"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run it**

```bash
python scripts/shrink_geojson.py
```

Expected output: `kommuner.geojson: 842 KB -> 430 KB (48.9% smaller), 290 features`

- [ ] **Step 5: Confirm it is idempotent**

```bash
python scripts/shrink_geojson.py
```

Expected: `430 KB -> 430 KB (0.0% smaller)`. If the size moves on a second run, the
rounding is not stable and the script is wrong.

- [ ] **Step 6: Run the tests**

```bash
python -m pytest tests/test_geojson_payload.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/shrink_geojson.py data/geo/kommuner.geojson tests/test_geojson_payload.py
git commit -m "perf: shrink kommuner.geojson 49% by coordinate precision alone"
```

---

### Task B2 — Payload ceiling and render equivalence · DONE

**Files:**
- Modify: `tests/test_geojson_payload.py`
- Modify: `docs/DEPLOYMENT.md` (file inventory note)

- [ ] **Step 1: Add the map-document size test**

Append to `tests/test_geojson_payload.py`:

```python
def test_the_rendered_map_document_shrank_with_it() -> None:
    """The file matters because it is embedded in what crosses to the browser."""
    import pandas as pd

    from src.ui.choropleth import _map_html

    ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
    html = _map_html(ranked[ranked["year"] == ranked["year"].max()])
    kb = len(html.encode("utf-8")) / 1024
    assert kb < 900, (
        f"the rendered map is {kb:.0f} KB. It was 1 234 KB before B1 and should be "
        "roughly 800 KB after; if it has grown back, check whether something is "
        "re-adding precision or embedding the geometry twice."
    )
```

- [ ] **Step 2: Run it**

```bash
python -m pytest tests/test_geojson_payload.py -q
```

Expected: PASS.

- [ ] **Step 3: Confirm the map still looks right**

```bash
python -m pytest tests/test_choropleth.py tests/test_pages_render.py -q
```

Expected: PASS — 21 choropleth assertions and 81 renders. These cover the tile host, the
empirical colour domain and every page/year combination.

- [ ] **Step 4: Note it in the deployment inventory**

In `docs/DEPLOYMENT.md`, under the `data/geo/` heading, replace the `kommuner.geojson` row
description with:

```markdown
| `kommuner.geojson` | 290 municipality polygons for the choropleth (430 KB, coordinates at 5 dp — regenerate with `python scripts/shrink_geojson.py`) |
```

- [ ] **Step 5: Commit**

```bash
git add tests/test_geojson_payload.py docs/DEPLOYMENT.md
git commit -m "test: pin the map payload ceiling"
```

---

## 8. Phase C — Stylesheet delivery

**Goal:** stop sending 24 KB of CSS inline on every page load.
**Exit criterion:** the stylesheet is a cacheable request when static serving is available,
and inline when it is not.
**Gated by:** Q2. **This is the least valuable phase** — if it fights, skip it.

---

### Task C1 — Serve the stylesheet statically, with fallback · TODO

**Files:**
- Create: `static/shai.css`
- Modify: `src/ui/css.py`
- Modify: `.streamlit/config.toml`
- Test: `tests/test_css_delivery.py` (new)

**The Streamlit constraint that makes this awkward:** `server.enableStaticServing` is
`False` by default, serves from `./static/` at `/app/static/...`, and is **unverified on
Community Cloud**. The fallback is therefore load-bearing, not politeness.

- [ ] **Step 1: Write the failing test**

Create `tests/test_css_delivery.py`:

```python
"""The stylesheet must reach the browser either way, and be identical either way.

24 KB was inlined into every page load. A <link> to a static file is requested
once and then cached, but `server.enableStaticServing` is off by default and
unverified on Community Cloud — so both paths must work and must deliver the same
bytes. A fallback that serves different CSS is worse than no fallback.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.ui.css import GLOBAL_CSS, stylesheet_href

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static" / "shai.css"


def test_the_static_file_exists() -> None:
    assert STATIC.exists(), "static/shai.css is missing; run the extraction in C1"


def test_the_static_file_is_byte_identical_to_the_inline_sheet() -> None:
    """Two sources of one stylesheet is the drift this project keeps fixing."""
    inline = re.sub(r"</?style>", "", GLOBAL_CSS).strip()
    assert STATIC.read_text(encoding="utf-8").strip() == inline, (
        "static/shai.css and GLOBAL_CSS differ; regenerate the static file"
    )


def test_href_is_none_when_static_serving_is_disabled() -> None:
    """Default Streamlit config. The caller must fall back to inlining."""
    from streamlit import config

    if not config.get_option("server.enableStaticServing"):
        assert stylesheet_href() is None
    else:
        assert stylesheet_href() == "app/static/shai.css"
```

- [ ] **Step 2: Run it and watch it fail**

```bash
python -m pytest tests/test_css_delivery.py -v
```

Expected: all three FAIL — `static/shai.css` does not exist and `stylesheet_href` is not
defined.

- [ ] **Step 3: Extract the static file**

```bash
python -c "import sys,re; sys.path.insert(0,'.'); from pathlib import Path; from src.ui.css import GLOBAL_CSS; Path('static').mkdir(exist_ok=True); Path('static/shai.css').write_text(re.sub(r'</?style>','',GLOBAL_CSS).strip()+chr(10), encoding='utf-8'); print('written', Path('static/shai.css').stat().st_size, 'bytes')"
```

- [ ] **Step 4: Add the accessor and the fallback**

In `src/ui/css.py`, add after the `GLOBAL_CSS` assignment:

```python
def stylesheet_href() -> str | None:
    """Return the static stylesheet path, or None when static serving is off.

    Streamlit serves `./static/` at `/app/static/...` only when
    `server.enableStaticServing` is true. It defaults to false and is unverified
    on Community Cloud, so the caller must be able to fall back to inlining.

    Returns:
        The relative href, or None when the file must be inlined instead.
    """
    from streamlit import config

    if not config.get_option("server.enableStaticServing"):
        return None
    return "app/static/shai.css"
```

and replace the body of `inject_css` with:

```python
def inject_css() -> None:
    """Inject the stylesheet, by link when possible and inline otherwise.

    The link is requested once and cached by the browser; inlining costs 24 KB on
    every page load. `GLOBAL_CSS` remains the single source, and
    `tests/test_css_delivery.py` fails if the static copy drifts from it.
    """
    href = stylesheet_href()
    if href is None:
        st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
        return
    st.markdown(f'<link rel="stylesheet" href="{href}">', unsafe_allow_html=True)
```

- [ ] **Step 5: Enable static serving**

In `.streamlit/config.toml`, under `[server]` (add the section if absent):

```toml
[server]
# Serves ./static at /app/static/..., so the 24 KB stylesheet is one cached
# request rather than an inline payload on every page load. Unverified on
# Community Cloud — src/ui/css.py falls back to inlining when this is false.
enableStaticServing = true
```

- [ ] **Step 6: Run the tests and the render sweep**

```bash
python -m pytest tests/test_css_delivery.py tests/test_pages_render.py tests/test_css_naming.py -q
```

Expected: PASS. If any render fails, set `enableStaticServing = false` and stop — the
fallback path is then the shipped behaviour and this task is `SKIPPED`.

- [ ] **Step 7: Verify in a browser, because no test can**

```bash
streamlit run app.py
```

Open the app, then DevTools → Network. Expect one `shai.css` request, status 200, and
styled output. If the page renders unstyled, static serving is not working in this
environment: revert step 5 and mark the task `SKIPPED` with that finding.

- [ ] **Step 8: Commit**

```bash
git add static/shai.css src/ui/css.py .streamlit/config.toml tests/test_css_delivery.py
git commit -m "perf: serve the stylesheet statically, with an inline fallback"
```

---

## 9. Phase D — Tests under the refresh pipeline (R5, R10)

**Goal:** the code that produces every artifact stops being the only untested part.
**Exit criterion:** `affordability.py` has property tests, `build_panel.py` has tests for
imputation and the ragged-panel joins, and it is under 400 lines. — **PARTLY MET.**
`affordability.py` has seven property tests (one found R12). The imputation is one tested
function, 10 tests, verified to reproduce the shipped panel exactly. `build_panel.py` is 615
lines, still over 400: its exemption ceiling ratcheted 641 → 615, and the remaining bulk is
nine `_clean_*` readers that need `data/raw/` or fixtures. R10 reduced, not closed.

This is the highest-value phase and the least glamorous. R5 is High for a reason: a mistake
here is invisible until a number looks wrong on a page, and it runs by hand once or twice a
year.

---

### Task D1 — Property tests for `affordability.py` · DONE

**Files:**
- Test: `tests/test_affordability_properties.py` (new)

**Why properties and not examples:** R1 was found by *reading* this module, not by a test
failing. Example-based tests would have passed. What matters is the relationships the
formulas must preserve — orientation, monotonicity, behaviour at the real-rate floor.

- [ ] **Step 1: Write the failing test**

Create `tests/test_affordability_properties.py`:

```python
"""The three formulas, tested by the relationships they must preserve.

`src/indices/affordability.py` computes Version A, B and C, and had no direct
tests until now — the module R1 came out of, found by reading rather than by a
failure. Example-based tests would not have caught it: the defect was that
Version B pools its component z-scores, which only shows up when you vary the
panel.

So these are property tests. Each asserts a relationship the formula must hold
for any input, not a value it happens to produce for one.
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


def test_zero_price_does_not_raise_or_return_infinity() -> None:
    """Defensive: a missing price must not produce inf and poison a z-score."""
    values = compute_version_c(panel(transaction_price_sek=[0.0, 900_000.0, 0.0, 920_000.0]))
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
```

- [ ] **Step 2: Run it and see which properties already hold**

```bash
python -m pytest tests/test_affordability_properties.py -v
```

Expected: most PASS. Any FAIL is a real finding — record it in `docs/OPEN_RISKS.md`
before changing any formula, because changing one alters every published `z_*`.

- [ ] **Step 3: If a property fails, stop and record it**

Do not adjust the formula to make a test pass. Add a row to `docs/OPEN_RISKS.md`
describing the property, the observed behaviour and the blast radius, and bring it back
as a decision. This module's output is what the whole app displays.

- [ ] **Step 4: Check coverage moved**

```bash
python -m pytest tests/ -q --cov=src/indices --cov-report=term
```

Expected: `affordability.py` above 90 %, from 65 %.

- [ ] **Step 5: Commit**

```bash
git add tests/test_affordability_properties.py
git commit -m "test: property tests for the three affordability formulas (R5)"
```

---

### Task D2 — De-triplicate the imputation into one pure function · DONE

**Files:**
- Create: `src/data/panel_income.py`
- Modify: `src/data/build_panel.py` (three inlined loops at ~320, ~449, ~541)

**Read §0 first.** This is a refactor before its tests, deliberately. The imputation is not a
function — it is the same growth-factor loop written three times, inside
`build_municipal_panel`, `build_county_panel` and `build_national_panel` — so there is nothing
to unit-test until it is extracted. And `data/raw/` is gitignored, so no test can call the
`build_*` functions at all on a fresh clone. The safety net for this task is therefore
**artifact identity**: regenerate the panels and diff the output.

- [ ] **Step 1: Capture the baseline, before touching anything**

```bash
python -c "import sys;sys.path.insert(0,'.');import pandas as pd;[print(n,(d:=pd.read_parquet(f'data/processed/panel_{n}.parquet')).shape,round(float(d.select_dtypes('number').sum().sum()),4)) for n in ('municipal','county','national')]" > /tmp/panel_before.txt
cat /tmp/panel_before.txt
```

Expected: three lines, one per level, each with a shape and a checksum. Keep this file.

- [ ] **Step 2: Read the three loops and confirm they are the same**

```bash
sed -n '310,330p;443,458p;535,550p' src/data/build_panel.py
```

Expected: three near-identical blocks computing
`growth_factor = (1 + IMPUTED_INCOME_GROWTH_RATE) ** (fill_year - max_income_year)` and
setting `is_imputed_income = True`. **If they differ in substance, stop** — they are three
behaviours, not one, and merging them would change output. Record the difference in
`docs/OPEN_RISKS.md` and bring it back as a decision.

- [ ] **Step 3: Write the extracted function**

Create `src/data/panel_income.py`:

```python
"""Forward-fill of the income series, extracted from three inlined copies.

Income ends a year before prices, unemployment and the policy rate. To keep the
panel rectangular, `build_panel` extends it with 3 % nominal growth per year (F9)
and flags every filled row with `is_imputed_income` — the flag
`step_compute_indices` filters on before scoring, so an imputed year cannot
re-base Version B (T2.4).

That logic was written three times, once per panel level. This is the one copy.
It is pure: a frame in, a frame out, no file access — which is what makes it
testable at all, since `data/raw/` is gitignored and the `build_*` functions
cannot run without it.

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
    are easy to get wrong and were wrong in this plan's first draft:

    **The anchor year is global, not per region.** The original takes
    `panel["year"].max()` once and copies every row at that year. A per-region
    anchor would be different behaviour — arguably better, since it would also
    fill a region whose series ended early — but it is a change, not a move, and
    on today's data every region ends at the same year, so an artifact diff would
    *not* catch the difference. Do not silently improve it here.

    **`median_income_tkr` is scaled by the same factor.** Omitting it leaves the
    thousands-column at the ungrown value while `median_income` moves, breaking
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

    result["is_imputed_income"] = (
        result.get("is_imputed_income", False)
        if "is_imputed_income" in result.columns
        else False
    )
    result["is_imputed_income"] = (
        pd.Series(result["is_imputed_income"], index=result.index)
        .fillna(False)
        .astype(bool)
    )
    return result
```

- [ ] **Step 4: Point the three call sites at it**

In `src/data/build_panel.py`, add to the imports:

```python
from src.data.panel_income import IMPUTED_INCOME_GROWTH_RATE, impute_income_forward
```

Delete the module-level `IMPUTED_INCOME_GROWTH_RATE = 0.03` assignment so there is one
definition, then replace each of the three inlined loops with

```python
    panel = impute_income_forward(panel, through_year=current_year)
```

using whatever frame variable each function already has.

**One detail to preserve:** the original rebuilds `fill` from `panel` on each
iteration *after* the previous iteration appended to it. Because it always selects
`year == anchor_year`, and appended rows have later years, the selection is stable
— so the loop above is equivalent. Verify with Step 5 rather than by reading.

- [ ] **Step 5: Regenerate and prove the output is identical**

```bash
python scripts/refresh_data.py --no-fetch --no-forecast
python -c "import sys;sys.path.insert(0,'.');import pandas as pd;[print(n,(d:=pd.read_parquet(f'data/processed/panel_{n}.parquet')).shape,round(float(d.select_dtypes('number').sum().sum()),4)) for n in ('municipal','county','national')]" > /tmp/panel_after.txt
diff /tmp/panel_before.txt /tmp/panel_after.txt && echo IDENTICAL
```

Expected: `IDENTICAL`. If it differs, the three loops were not equivalent after all — revert,
return to Step 2, and treat the difference as the finding.

- [ ] **Step 6: Confirm no artifact moved and the suite is green**

```bash
git diff --stat data/ && python -m pytest tests/ -q && python scripts/audit.py
```

Expected: **no change under `data/`**, all tests pass, audit passes. A refactor that rewrites
an artifact is not a refactor.

- [ ] **Step 7: Commit**

```bash
git add src/data/panel_income.py src/data/build_panel.py
git commit -m "refactor: one income-imputation function instead of three copies"
```

---

### Task D3 — Test the extracted function; drop the size exemption · DONE

**Files:**
- Test: `tests/test_panel_income.py` (new)
- Modify: `tests/test_file_sizes.py`

- [ ] **Step 1: Write the test**

Create `tests/test_panel_income.py`:

```python
"""Income imputation: the behaviour three shipped decisions rest on.

`is_imputed_income` is what `complete_case()` filters on, and T2.4 found that an
unfiltered imputed row re-based Version B for every historical year — 1816 rank
changes caused by a year no page can render. F9 sets the growth rate. D1's honest
vintage depends on the flag being right.

None of it had a test, because the logic was inlined three times inside functions
that cannot run without `data/raw/`, which is gitignored. D2 extracted it; this
covers it.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data.panel_income import IMPUTED_INCOME_GROWTH_RATE, impute_income_forward


def observed() -> pd.DataFrame:
    """Two municipalities, income observed through 2024."""
    return pd.DataFrame({
        "region_code": ["0180", "2463"],
        "year": [2024, 2024],
        "median_income": [400.0, 300.0],
    })


def test_growth_rate_is_three_percent() -> None:
    """F9. Changing this changes every imputed year in the panel."""
    assert IMPUTED_INCOME_GROWTH_RATE == pytest.approx(0.03)


def test_filled_rows_are_flagged_and_observed_rows_are_not() -> None:
    """The flag `complete_case()` filters on. T2.4 is what happens when it lies."""
    result = impute_income_forward(observed(), through_year=2026)
    assert result[result["year"] <= 2024]["is_imputed_income"].eq(False).all()
    assert result[result["year"] > 2024]["is_imputed_income"].eq(True).all()


def test_growth_compounds_from_the_last_observed_year() -> None:
    result = impute_income_forward(observed(), through_year=2026)
    stockholm = result[result["region_code"] == "0180"].set_index("year")["median_income"]
    assert float(stockholm[2025]) == pytest.approx(412.0)
    assert float(stockholm[2026]) == pytest.approx(424.36)


def test_observed_values_are_never_modified() -> None:
    result = impute_income_forward(observed(), through_year=2027)
    kept = result[~result["is_imputed_income"]].sort_values("region_code")
    assert kept["median_income"].tolist() == [400.0, 300.0]


def test_the_anchor_year_is_global_not_per_region() -> None:
    """Pins the behaviour that exists, not the one that sounds right.

    The original takes `panel["year"].max()` once and copies every row at that
    year, so a region whose series ended earlier is **not** filled. That is
    arguably a flaw — but it is the shipped behaviour, and on current data every
    region ends at the same year, so an artifact diff cannot tell the two apart.
    Changing it is a decision for `docs/OPEN_RISKS.md`, not a detail to fix while
    extracting.
    """
    ragged = pd.DataFrame({
        "region_code": ["0180", "2463"],
        "year": [2024, 2022],
        "median_income": [400.0, 300.0],
    })
    result = impute_income_forward(ragged, through_year=2025)
    filled = result[result["is_imputed_income"]]

    assert filled["region_code"].tolist() == ["0180"], (
        "a region below the global anchor year was filled; that is a behaviour "
        "change, not an extraction"
    )
    assert float(filled["median_income"].iloc[0]) == pytest.approx(412.0)


def test_the_thousands_column_is_scaled_with_the_income() -> None:
    """Omitting this leaves median_income_tkr ungrown and breaks the 1000x ratio."""
    frame = pd.DataFrame({
        "region_code": ["0180"],
        "year": [2024],
        "median_income": [533800.0],
        "median_income_tkr": [533.8],
    })
    result = impute_income_forward(frame, through_year=2025)
    filled = result[result["is_imputed_income"]].iloc[0]
    assert float(filled["median_income"]) == pytest.approx(549814.0)
    assert float(filled["median_income_tkr"]) == pytest.approx(549.814)


def test_nothing_is_added_when_the_target_year_is_already_covered() -> None:
    result = impute_income_forward(observed(), through_year=2024)
    assert len(result) == 2
    assert result["is_imputed_income"].eq(False).all()


def test_an_empty_frame_is_returned_unchanged() -> None:
    empty = pd.DataFrame(columns=["region_code", "year", "median_income"])
    assert impute_income_forward(empty, through_year=2026).empty


def test_the_input_frame_is_not_mutated() -> None:
    """Pure, so it runs on a fresh clone where data/raw is empty."""
    frame = observed()
    before = frame.copy()
    impute_income_forward(frame, through_year=2026)
    pd.testing.assert_frame_equal(frame, before)
```

- [ ] **Step 2: Run it**

```bash
python -m pytest tests/test_panel_income.py -v
```

Expected: PASS if D2's extraction is faithful. Any failure is a real difference between the
documented intent and the extracted behaviour — fix the *function*, then re-run D2 Step 5 to
confirm the artifacts still match.

- [ ] **Step 3: Check whether `build_panel.py` now fits**

```bash
wc -l src/data/build_panel.py src/data/panel_income.py
```

- [ ] **Step 4: Update the exemption honestly**

If `build_panel.py` is at or under 400 lines, remove it from `EXEMPT` and from
`EXEMPT_CEILINGS` in `tests/test_file_sizes.py`. If it is still over, **lower its ceiling**
to the new count — an exemption must never cover more than the file currently is.

- [ ] **Step 5: Update the register**

In `docs/OPEN_RISKS.md`, note under R5 that the imputation is covered, and under R10 whether
`build_panel.py` is now within the limit. `scb_client.py` stays exempt: its tests need
network fixtures and are out of scope.

- [ ] **Step 6: Full verification**

```bash
python -m pytest tests/ -q && python scripts/audit.py && git diff --stat data/
```

Expected: all pass, no change under `data/`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_panel_income.py tests/test_file_sizes.py docs/OPEN_RISKS.md
git commit -m "test: cover income imputation now that it is one function (R5, R10)"
```

---

## 10. What this plan deliberately does not do

Recorded so a reader does not assume they were missed.

| Not doing | Why |
|---|---|
| Topology simplification of the GeoJSON | Needs `shapely` or `mapshaper`. Precision truncation gets 49 % for free; simplification might reach 70 % for a runtime dependency and a visible risk to coastlines. Revisit only if 430 KB proves too big. |
| Vector tiles or a tile server | Enormous change for an app with 290 static polygons. |
| Replacing folium with `pydeck` or `st.map` | Would lose the tooltip, the empirical colour domain and the zoom-gated labels — T1.6, T1.7 and T3.9 all rebuilt on folium. |
| Tests for `scb_client.py` and the forecast pipelines | Needs network mocking or fixture capture. Real work, separate plan. `scb_client.py` keeps its size exemption until then. |
| End-to-end tests of `build_municipal_panel()` | `data/raw/` is gitignored, so it cannot run on a fresh clone or in CI. Committing fixture raw data would work and is a separate decision — it is ~1.7 MB and would need refreshing alongside the real thing. |
| Persisting caches across restarts | `st.cache_data(persist="disk")` exists, but the app sleeps and wakes with a cold filesystem on Community Cloud. Measure before believing it helps. |
| Anything about the deployed app | Nobody has confirmed the Streamlit Cloud deploy. That is still open from T2.5 and needs the account owner. |

---

## 11. Session log

Append one line per work session: date, tasks touched, outcome, anything the next session
needs.

| Date | Tasks | Outcome | Notes for next session |
|------|-------|---------|------------------------|
| 2026-09-17 | Q1, A1, A2, D2, D3 | **Phases A and D done.** Q1 answered **No**, so the map takes the whole year: risk-pill toggles went ~370 ms → **~45 ms** and R11 closed outright. The imputation is one function reproducing the shipped panel exactly (580 rows, zero delta). Extracting it surfaced a pandas `FutureWarning` the original carried invisibly. | Only **C1** left, gated on Q2. `build_panel.py` is 615 lines — R10 reduced, not closed. |
| 2026-09-17 | B1, B2 | **Phase B DONE.** GeoJSON 842 KB → 428 KB (−49.2 %), map document 1 234 KB → 860 KB (−30 %), idempotent, 290 features intact. The `geo_point_2d` correction from the plan review mattered: rounding geometry alone would have left 580 high-precision values and failed the test. `tests/test_geojson_payload.py` (6). | Phase D is next and is ungated. **Phase A still needs Q1.** |
| 2026-09-17 | — | Plan written from the Windows audit. No code changed. | **Answer Q1 before starting Phase A.** Phases B and D are independent of it and of each other; D is the highest value. Start from a green suite (645 passed) and a green audit (27 passed). |
