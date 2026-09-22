# Open risks and pending decisions

Things that are **not bugs today** but will cost something later, found while working
through `docs/REVITALIZATION_PLAN.md`. Each one is either a decision someone has to make
or a hazard that is currently held shut by a guard rather than fixed at the root.

Kept separate from the plan because the plan is a task list that ends when Phase 4 ends.
These outlive it.

**Created:** 2026-09-15 · after Phase 2
**Status key:** `OPEN` · `ACCEPTED` (decided, living with it) · `CLOSED`

| # | Risk | Severity | Status |
|---|------|----------|--------|
| R1 | Version B re-bases every historical value whenever the panel changes | **High** | **CLOSED** |
| R2 | Three pages read year lists from the data instead of `YEAR_RANGE` | Medium | **CLOSED** |
| R3 | The `pipeline` extra is unverified as an install | Medium | **CLOSED** |
| R4 | The forecast step exhausts memory on this machine | Medium | **CLOSED** |
| R5 | Refresh-pipeline modules have no tests (73 % overall, was 15 %) | **High** | **CLOSED** |
| R6 | The 67-render check lives in a scratch directory, not the repo | Medium | **CLOSED** |
| R7 | A fresh deploy installs major versions the app was never tested against | **High** | **ACCEPTED** |
| R8 | `folium_static` is deprecated and will be removed | Medium | **CLOSED** |
| R9 | `labels.py` holds markup and LaTeX, not only copy | Low | **CLOSED** |
| R10 | Two `src/data/` modules exceed the line limit and have no tests | Medium | **CLOSED** |
| R11 | The map cache cannot hold every year x risk combination | Low | **CLOSED** |
| R12 | A zero price divides to infinity in Version C | Low | **CLOSED** |
| R13 | 24 KB of CSS is inlined on every page load, unavoidably | Low | **ACCEPTED** |
| R14 | The chart layer sits outside every design guard | Medium | **CLOSED** |
| R15 | Numbers quoted in docstrings and markdown are guarded nowhere | Medium | **CLOSED** |

---

## R1 — Version B re-bases every historical value whenever the panel changes

**Severity: High. CLOSED** on 2026-09-21 by `src/indices/b_reference.py`.

`compute_version_b` z-scored its four components — price-index ratio, policy rate,
unemployment, CPI — **pooled across every row of the panel it was handed**. That pooling is
deliberate: D5 kept B's construction pooled because the pooled level is the only time trend
the index carries. Versions A and C are normalised within year and are immune.

The consequence was that B's published values were a function of panel composition. Add a
row anywhere and every year moved.

### What the measurement showed

This entry asked for one thing before a decision: *how many municipality-years actually
change class across a realistic refresh*, on the precedent of a 19-row incident in T2.4, and
suggested that 0.6 % might be small enough to accept with a note. Both cases were measured.

| Refresh | `version_b` rows moved | `rank_b` changed | `risk_b` changed |
|---|---|---|---|
| One ordinary year appended (2025, simulated) | 3190 of 3190 | 947, up to 4 places | 7 |
| The income-source switch of 2026-09-21 | 3190 of 3190 | 2971, up to **117** places | **225** |

Version C, normalised within year, moved on **zero** rows under the same appended year.

The second line is what settled it. The 19-row precedent came from appending data; a change
to a *source definition* is an order of magnitude worse, and that is the case that actually
occurred. Accepting 225 silent risk-class changes with a footnote was not defensible.

### The fix, and why it is not option C

The four options this entry listed were: leave pooled and announce it (A), freeze per
vintage (B), normalise within year like A and C (C), or split into a pooled level plus a
within-year rank (D).

What shipped is closest to B, with the cost that made B unattractive removed. This entry
framed freezing as "per vintage", which would leave two vintages incomparable. **The
reference is frozen once and carried forward instead**, so every vintage shares one
yardstick and all of them stay comparable. Re-basing becomes a deliberate act with a version
bump behind it.

Crucially this keeps the trend that ruled out option C. It arguably improves it: under the
moving reference, adding a high-rate year inflated the pooled standard deviation and pushed
earlier high-rate years back toward zero, so the yardstick shrank as the thing it measured
grew. "2.3 standard deviations above the 2014 to 2024 norm" now means the same thing in 2030
as it does today.

### Adoption cost: none

The reference was derived from the panel as it stood, so scoring against it reproduced every
existing value exactly. The rebuild that adopted it left all four affordability parquets
byte-identical; only the provenance timestamp changed.
`tests/test_version_b_reference.py` asserts that property at all three levels, so it cannot
be quietly lost.

One trap worth recording, because the first draft fell into it: the reference must be
derived from **exactly** the rows that get scored. `complete_case` returns 4060 municipal
rows while only 3190 carry every index input, and deriving from the first while scoring the
second put the frozen moments up to 0.19 away from the moving ones. `scorable_rows` is now
exposed from `affordability.py` so both paths call the same filter.

### What guards it

`tests/test_version_b_reference.py`:

- appending a year leaves every historical `version_b`, `rank_b` and `risk_b` untouched
- **the negative control**: the same append on the unreferenced path still rewrites history,
  so the test above cannot pass by describing a scenario that no longer occurs
- the committed reference matches what the committed panel produces, so the JSON cannot be
  hand-edited into a silent re-base
- the artifact covers all three levels, so `reference_for` never bootstraps a new norm from
  whatever panel happens to be in a checkout

**Revisit if:** the Version B formula gains or loses a component, which the stored reference
will refuse rather than guess at, or the panel changes enough that the 2014 to 2024 norm
stops describing anything useful. Both are deliberate re-bases: bump `version` and expect
every B value to move.

---

## R2 — Three pages read year lists from the data instead of `YEAR_RANGE`

**Severity: Medium.** Currently harmless, same class as a defect already fixed once.

T1.4 made the sidebar derive its year selector from `complete_case_max_year()`. Three
pages never got the same treatment and still ask the dataframe what years exist:

| File | Line | Call |
|---|---|---|
| `pages/02_Lan_jamforelse.py` | 163, 180 | `sorted(county_versions["year"].unique())` |
| `pages/04_Kontantinsats.py` | 60 | `sorted(municipal["year"].unique(), reverse=True)` |
| `pages/05_Scenario.py` | 44 | `sorted(county_panel["year"].unique(), reverse=True)` |

Pages 04 and 05 read *panel* frames, which already run to 2026, so they have been exposed
the whole time. Page 02 reads an *affordability* frame, which is why the T2.4 refresh would
have printed a chart titled "2014–2025" until `complete_case()` pulled the index back.

The index is the only thing holding this shut. Any future change that legitimately extends
the index past what the selector offers reopens it in three places at once.

**Recommendation:** fold into Phase 3, alongside T3.7 (`src/ui/filters.py`), which already
exists to de-duplicate page filter logic. One shared accessor, and a source-level guard in
the style of `tests/test_pages_no_recompute.py` asserting no page derives its own year list.

### CLOSED 2026-09-22 — one accessor, a guard, and a fourth site nobody had listed

`src.provenance.selectable_years()` resolves the index period once, the same way the
sidebar has since T1.4, and the three sites now read it.

The exposure was real on two of them rather than stylistic. `04_Kontantinsats` and
`05_Scenario` built their "no data for this year, try one of these" fallbacks from *panel*
frames, which run to 2026 while the index stops at 2024. The suggestions were years that
render blank. Page 02's two sites were bounded correctly, because they read a scored
artifact, but were deriving a fact the page had already resolved from provenance at the top.

**The guard found a fourth site the register had not listed**, and it turned out to be dead
code rather than a wrong year list. `02_Lan_jamforelse` built `_imputed_years` from the
scored artifact to shade forward-filled years on its trend charts. T2.4 made
`step_compute_indices` score only `complete_case()` rows, so that artifact carries **zero**
imputed rows by construction — `is_imputed_income` is False on all 3190. The set was always
empty, the shading could never render, and the chart was advertising an annotation that
cannot appear. Removed, with the reason recorded where it stood.

That is the argument for writing the guard rather than just fixing the three known sites: a
list of three came from reading the code once, and the scan found the one that reading had
missed.

`tests/test_year_range.py` now asserts that no page asks a frame which years exist, that
`selectable_years()` matches the artifact it describes, and that it is the index period
rather than the panel's — the two differ by design, and conflating them is what R2 was.

---

## R3 — The `pipeline` extra is unverified as an install

**Severity: Medium.** A documented path that may not work.

T2.4 proved the refresh pipeline *runs*. It did not prove `pip install -e ".[pipeline]"`
*installs*, because `prophet` and `pmdarima` were already present in the working
environment. `pyproject.toml` now advertises that command in `README.md` and
`docs/DEPLOYMENT.md`, so if those two have no wheel for the target interpreter and no
build toolchain is present, the documented instruction fails for whoever tries it first.

Prophet in particular pulls Stan. It is the single most fragile dependency in the project,
which is exactly why T2.1 moved it out of the runtime set.

**Recommendation:** run `pip install -e ".[pipeline]"` in a genuinely empty venv on the
interpreter the docs promise, on the platform a maintainer would actually use. If it fails,
that is worth knowing now and worth writing down next to the command rather than leaving
someone to discover it. Consider pinning `prophet` and `pmdarima` to versions with
published wheels for the supported Python range.

### CLOSED 2026-09-22 — it installs

Run as documented, on the interpreter the docs promise: `python3.11 -m venv`, then
`pip install -e ".[pipeline]"` into it. **It succeeds**, and nothing compiles from source —
`prophet` and `pmdarima` both resolve to wheels.

| | Resolved |
|---|---|
| Python | 3.11.13 |
| prophet | 1.4.0 |
| pmdarima | 2.1.1 |
| statsmodels | 0.15.0 |

The recommendation to pin `prophet` and `pmdarima` to versions with published wheels is
therefore not needed today. It stays worth remembering: this verifies one interpreter on one
platform, and the fragility the risk described is real, it simply is not biting.

**One thing the run surfaced, and it belongs to R7 rather than here.** The clean install
resolved `pandas 3.0.6` and `numpy 2.4.6` — both inside the declared caps, and both major
versions above what the app is verified against. That is R7 happening in front of us rather
than in theory.
---

## R4 — The forecast step exhausts memory on this machine

**Severity: Medium.** Blocks a step that is currently, but not permanently, optional.

`step_forecasts` fits ARIMA and Prophet across 84 series. Run on 2026-09-15 it was killed
by the OS for low memory. Steps 1–3 completed normally, so this is specific to step 4.

It did not matter that time: the training window ends at `_resolve_end_year()`, still 2024,
and none of the forecast variables changed inside it, so the existing forecast parquets are
equivalent rather than merely stale. **That reasoning expires** the moment income publishes
2025 and the training window moves — at which point the forecasts genuinely must be
regenerated, and the step that cannot run is the one that has to.

**Recommendation:** treat `--no-forecast` as the default refresh and regenerate forecasts
as a separate, deliberate run. If it still cannot complete, make the pipeline checkpoint
per county so a kill loses one county rather than the whole step. Worth measuring actual
peak RSS before choosing a fix.

### CLOSED 2026-09-22 — measured, and it does not

This entry recommended measuring actual peak RSS before choosing a fix. Measured:

| | Result |
|---|---|
| ARIMA, 84 series | 103 s |
| Prophet, 84 series | 19 s |
| **Peak RSS** | **197 MB** |

The 2026-09-15 OOM kill does not reproduce. 197 MB is not close to exhausting anything, and
the whole step finishes in two minutes. Whatever happened that day was about the state of
that machine, not about this code.

That matters more than a closed row, because this risk carried an expiry: its own reasoning
for why the kill was harmless — that the training window still ended in 2024 and none of the
forecast variables had moved inside it — ends the moment SCB publishes 2025 income. The step
that could not run would have been the one that had to. It runs.

The full step was also exercised end to end on 2026-09-21 as part of the income switch, and
wrote all three forecast artifacts.

**What this leaves open, elsewhere:** the forecast pipelines remain at 0 % coverage, which is
R5, not this. And the failure mode that nearly shipped that day was not memory but silence —
steps 1 to 3 wrote their artifacts and step 4 exited on a missing import, leaving committed
forecasts derived from the previous income series. Worth a guard comparing artifact vintages;
recorded under R5's recommendation rather than reopening this.
---

## R5 — Whole subsystems have no tests

**Severity: High.** Improved substantially, not closed.

Measured after Phase 1 this was **15 %** overall, with `src/indices/affordability.py` — the
module computing Version A, B and C — at **0 %**. Both numbers are now out of date, which is
itself worth noting: a risk register goes stale exactly like the prose T4.1 polices.

Measured after Phase 4:

| | After Phase 1 | Now |
|---|---|---|
| `src/` overall | 15 % | **44 %** |
| `src/indices/affordability.py` | 0 % | 65 % |
| `src/indices/normalize.py` | 62 % | 62 % |
| `src/ui/` | ~45 % | 81–100 % |

Most of the gain is T4.4: putting the 67-render sweep inside the suite exercises every page and
nearly all of `src/ui/`. The index formulas gained coverage incidentally, through T2.4's
complete-case tests.

**Still at 0 %:**

| Module | Statements |
|---|---|
| `src/data/build_panel.py` | 346 |
| `src/data/scb_client.py` | 241 |
| `src/forecast/prophet_pipeline.py` | 110 |
| `src/forecast/arima_pipeline.py` | 108 |
| `src/data/riksbanken_client.py` | 67 |

These are the refresh pipeline: the code that builds the artifacts everything else reads. It
runs once or twice a year, by hand, and a mistake in it is invisible until a number looks wrong
on a page. `build_panel.py` in particular holds income imputation, the ragged-panel joins and
the forward-fill — the machinery behind D1, F9 and the `complete_case()` rule.

### Progress 2026-09-22 — the panel builder is covered, and the numbers above are stale

The table earlier in this entry reports 44 % overall and lists five modules at 0 %. Both
were out of date by the time they were read, which this entry itself predicted: *"a risk
register goes stale exactly like the prose T4.1 polices."*

Measured now:

| | After Phase 4 | Now |
|---|---|---|
| `src/` overall | 44 % | **68 %** |
| `src/data/build_panel.py` | 0 % | **91 %** |
| `src/data/clean_sources.py` | — | **95 %** |
| `src/data/panel_summary.py` | — | **100 %** |
| `src/data/scb_client.py` | 0 % | 13 % |

The narrowed recommendation this entry made — property tests for
`affordability.py` — had already been satisfied by
`tests/test_affordability_properties.py`, which covers orientation, monotonicity in income
and price, the floored real rate, the zero-price case and panel-composition dependence. That
left `build_panel.py` as the target, and it is done: `tests/test_build_panel.py` (28) drives
the whole builder in-process by patching `_read`, the single I/O seam, with synthetic frames
in each source's published shape.

What those tests assert is the part worth naming. They are not smoke tests; they pin the
**documented approximations**, each of which is a deliberate decision that would otherwise
become something else the first time a merge key moved:

- the county price index reaching every municipality (F1)
- the national policy rate and CPI at all three levels (F2)
- K/T and transaction-price fallback to county values, with `has_native_*` recording which
- income forward-filled past its vintage at 3 %/yr and flagged (F9), with
  `median_income_tkr` moving with `median_income`
- the combined `08+09` Kalmar and Gotland row split so both counties join
- Kolada's `00` + SCB code convention for counties
- quarterly K/T rows and non-permanent property types filtered out rather than averaged in

**Still at 0 %:** `src/forecast/arima_pipeline.py` (108 statements),
`src/forecast/prophet_pipeline.py` (110) and `src/data/riksbanken_client.py` (67). These are
the remaining reason this risk is reduced rather than closed. The forecast pipelines are the
larger gap; they feed page 03 and they are the step most likely to be skipped on a refresh,
which is exactly how the stale forecast artifacts of 2026-09-21 nearly shipped.

### CLOSED 2026-09-22 — no subsystem is at zero

The two modules that recommendation named are done, and with them the risk's own
framing — *whole subsystems have no tests* — stops being true of anything.

| | After Phase 1 | After Phase 4 | Now |
|---|---|---|---|
| `src/` overall | 15 % | 44 % | **73 %** |
| `src/data/build_panel.py` | 0 % | 0 % | 91 % |
| `src/data/clean_sources.py` | — | — | 95 % |
| `src/data/riksbanken_client.py` | 0 % | 0 % | **87 %** |
| `src/forecast/arima_pipeline.py` | 0 % | 0 % | 31 % |
| `src/forecast/prophet_pipeline.py` | 0 % | 0 % | 30 % |

**`riksbanken_client.py`** was named for leverage rather than size: 67 statements producing a
series that Version A divides by directly and Version C through the real rate. The tests
stub the network and pin the two things that can go wrong quietly — a rate that fails to
parse becoming `NaN` through `errors="coerce"`, and the fact that the annual figure is the
mean of the business days present rather than a time-weighted average. The second is a
modelling choice the whole panel inherits, and it was nowhere written down.

**The forecast pipelines are tested by contract, not by output**, and the low percentages
are the deliberate result. Pinning ARIMA's predicted values would be a change-detector: it
would fail whenever `pmdarima` changed a default, pass while the pipeline forecast the wrong
series entirely, and leave nobody able to say whether a diff was a regression or a better
model. The uncovered statements are the model fitting, which is exercised end to end
whenever a refresh runs.

What is covered is everything around the fit: `_resolve_end_year` ignoring the imputed tail,
the horizon and its consecutive target years, all 21 counties present for every variable,
bands that contain their own mean and are not inverted, and the widening validator on both
a widening and a narrowing series.

**The most valuable one is the vintage check**, and it closes the loop on the near-miss R4
describes. A forecast's first target year must be the year after the last observed one, so
the forecast artifacts and the index artifacts can be compared directly without either
recording a timestamp. On 2026-09-21 the refresh wrote panels and indices, then exited on a
missing import before the forecast step, leaving committed forecasts built on the previous
income series. It was caught by hand. It would now fail a test.

**Residual, and deliberately accepted:** the model-fitting bodies of both forecast pipelines
are not unit-tested. Unit tests are the wrong instrument there, and the right one — the
contract on their output, plus the vintage check — is in place.

---

## R6 — The 67-render check is not in the repository

**Severity: Medium.** The strongest evidence for Phase 1's exit criterion cannot be re-run.

Every page rendering for every offered year — 6 pages × 11 years + landing — is the check
that actually proves the app works. It has been run at each step and has passed 67/67 every
time. It exists as a script in a session scratch directory. It is not committed, no one
else can run it, and CI cannot.

T4.4 (`tests/test_pages_render.py`) is its slot in the plan, at the very end of Phase 4.

**Recommendation:** pull T4.4 forward. It is the highest-value test in the plan and it is
scheduled last. Every phase after this one changes the UI, which is precisely what this
check covers.

### CLOSED 2026-09-16

T4.4 pulled forward and landed as `tests/test_pages_render.py` — **81 tests in 14 s**, inside
the default suite. Wider than the scratch script it replaces: it also covers an empty risk
selection and a single-class selection on every page, parametrises years off `YEAR_RANGE` so
the sweep widens when provenance does, asserts each page rendered *something* (a page that
returned early used to pass silently), and includes two meta-tests proving the harness can
actually fail — one script that raises, one that renders nothing. Without those, 81 green
ticks could mean 81 renders or a broken harness.

---

## R7 — A fresh deploy installs major versions the app was never tested against

**Severity: High.** Discovered by T2.5; currently working, by luck rather than design.

`requirements.txt` pins lower bounds only, on the reasoning that Streamlit Cloud rebuilds
periodically and an upper pin would rot silently. The clean-environment check showed what
that actually resolves to today:

| Package | Verified against | Clean install resolved |
|---|---|---|
| pandas | 2.3.3 | **3.0.5** |
| numpy | 1.26.2 | **2.5.3** |
| streamlit | 1.55.0 | 1.64.0 |
| plotly | 6.6.0 | 7.1.0 |
| pyarrow | 23.0.1 | 25.0.1 |

pandas 2 → 3 and numpy 1 → 2 are major version boundaries with documented breaking
changes. **All 67 page renders pass on the resolved set**, so nothing is broken right now.
But a deploy today runs code paths no test in this repo has ever exercised against those
versions, and the next resolver shift happens without anyone choosing it.

The failure mode is the worst kind: the app works in the maintainer's environment
(pandas 2.3.3) and breaks only in production, on a rebuild nobody triggered.

### The decision

| Option | What it buys | What it costs |
|---|---|---|
| **A. Leave lower bounds** | Free security and bugfix updates; no pin maintenance | Untested majors reach production unannounced |
| **B. Cap the majors** (`pandas>=2.3.3,<4`, `numpy>=1.26.2,<3`) | Blocks the next major boundary from arriving silently | Needs a deliberate bump; a stale cap eventually blocks a needed fix |
| **C. Full lockfile** | Reproducible deploys, exactly | Streamlit Cloud does not consume one natively; heaviest to maintain |

**Recommendation: B, plus run the clean-environment check as part of the release routine.**
The cap is one line per package and turns a silent production break into a visible
resolution failure. The check is already scripted — see R6, which is the same gap wearing a
different hat: the verification exists but lives nowhere the project can re-run it.

### ACCEPTED 2026-09-16 — option B taken, residual risk remains

Caps applied to `requirements.txt` and mirrored into `pyproject.toml`, with
`test_every_requirement_caps_the_next_major` and a new test asserting the two files agree on
*specifiers*, not merely on package names.

Every cap sits **above** what T2.5 resolved and verified, so this is not a downgrade:

| Package | Verified | Cap |
|---|---|---|
| pandas | 3.0.5 works | `>=2.3.3,<4` |
| numpy | 2.5.3 works | `>=1.26.2,<3` |
| streamlit | 1.64.0 works | `>=1.55.0,<2` |
| plotly | 7.1.0 works | `>=6.6.0,<8` |
| pyarrow | 25.0.1 works | `>=23.0.1,<26` |
| folium, streamlit-folium, branca | 0.x | `<1` |

**Why this is ACCEPTED and not CLOSED.** Two gaps survive. The 0.x packages get `<1`, which
still admits breaking *minor* bumps — the 0.x convention means 0.21 may break what 0.20 did,
and `folium` is the one drawing the map. And a cap only converts a silent break into a
visible resolution failure; it does not tell anyone the app was never tested on what got
installed. That needs the clean-environment check to run on a schedule, not once per phase.

**Revisit when:** a deploy fails to resolve, or before any release that matters.

**Note on `requests`:** the clean install contains it as a transitive dependency of
streamlit, which is correct and expected — T2.1's criterion is that it is absent from
`requirements.txt`, not from the environment. It emits a `RequestsDependencyWarning` about
`charset_normalizer` in that venv. Harmless: the import graph confirms no page imports
`requests`.

---

## R8 — `folium_static` is deprecated and will be removed

**Severity: Medium.** A scheduled removal on the one component that draws the map.

`src/ui/choropleth.py:361` calls `folium_static(m, width=None, height=height)`. Surfaced by
T4.4: every page render that draws the map emits

    DeprecationWarning: folium_static is deprecated and will be removed in a future
    release, or simply replaced with st_folium which always passes
    returned_objects=[] to the component.

Thirteen warnings across the render sweep. Nothing is broken — but "will be removed" plus
`streamlit-folium` capped only at `<1` (see R7) means a future minor release deletes the
function and the choropleth stops rendering.

The migration is not a rename. `st_folium` returns interaction state to Python and triggers
a rerun on map events unless `returned_objects=[]` is passed; getting that wrong turns every
pan and zoom into a full page re-render. `folium_static` exists precisely to avoid that.

**Recommendation:** migrate to `st_folium(m, returned_objects=[], ...)` deliberately, during
Phase 3 while the map is already being touched (T3.9 adds the "Om kartan" expander), and
confirm through `tests/test_pages_render.py` that render counts and timing do not change.
Not urgent, but do not let it be discovered by a broken deploy.

### CLOSED 2026-09-16 — and it took `streamlit-folium` with it

Resolved by the performance work rather than by a migration. `folium_static` only ever
wrapped `st.components.v1.html(m.get_root().render(), ...)`, and caching that render meant
calling the two halves separately anyway. The deprecated call is gone, `st_folium` was never
needed, and **the suite now emits zero deprecation warnings**, down from 13 per render sweep.

Dropping it removed the last import of `streamlit-folium`, which `tests/test_runtime_dependencies.py`
caught immediately — declared in `requirements.txt` but no longer reachable from any page. The
runtime set is now **seven packages**.

---

## R9 — `labels.py` holds markup and LaTeX, not only copy

**Severity: Low.** Correct by T3.1's acceptance, wrong as a long-term home.

T3.1 required that no Swedish string literal remain inline in `app.py` or `pages/*.py`. Some
of those literals were not sentences — they were HTML blocks with inline CSS, a Plotly hover
template, and a LaTeX formula:

    sc.version_c_realversion_beraknas_som_text   $$	ext{Affordability}_C = rac{...}$$
    rv.v0_version_c_v1_ranking_kommun_z_poang    a full <div class="shai-card"> template
    lj.v0_ar_x_varde_y_2f                        <b>{v0}</b><br>År: %{{x}}<br>...

So `SWEDISH_LABELS` is now three things at once: copy, markup templates, and maths. Three
consequences. The brace-escaping rule exists only because of the markup, and is a live trap
for anyone adding a label by hand. A reviewer reading copy has to skim HTML. And T4.1, which
re-derives every quoted number from the artifacts, has to parse numbers out of markup rather
than out of sentences.

**Recommendation:** split when Phase 3 next touches these files — `SWEDISH_LABELS` for prose,
a separate `TEMPLATES` mapping (or component functions) for markup. T3.10 splits
`components.py` and is the natural moment: markup that lives in a component does not need to
live in a label at all. Low priority because nothing is broken and the guard tests pin the
current behaviour; worth doing before the dict grows past the point where anyone reads it.

### CLOSED 2026-09-22 — `src/ui/templates.py`

Ten markup blocks moved out of `SWEDISH_LABELS`: the two regime tables, the assumptions
panel, the landing blurb and five smaller fragments. 368 labels and 10 templates.

**The line is a rule rather than a judgement**, which is what makes it hold. A string
carrying HTML tags is a template; prose has none. `tests/test_labels.py` asserts both
directions, so a markup block cannot drift back into the copy dictionary and a sentence
cannot end up in the template file.

One carve-out, because the alternative is worse: Plotly hover templates contain `<br>` and
`<extra></extra>`, which is Plotly's microformat rather than page markup, and what a reader
sees in a tooltip is copy. They are recognised by their `%{...}` placeholders, which appear
in no page HTML, so the exemption needs no key-name convention to maintain.

The LaTeX this risk also named stayed put. There is exactly one formula string, it is read
by `st.latex` as content rather than assembled as markup, and a third dictionary for a
single entry would be structure for its own sake.

**The move nearly weakened a guard, which is the part worth recording.**
`test_copy_matches_artifacts.py` scanned `SWEDISH_LABELS` for unexamined year literals.
Four of the ten moved blocks carry 13 year literals between them — they are regime tables,
dense with 2010, 2016, 2018 and 2026 — so scanning only the copy dictionary afterwards would
have quietly narrowed the guard to the strings that happen not to carry markup. Prose wrapped
in a `<div>` goes stale exactly as easily. Its four scanning loops now read both dictionaries,
and that was verified by counting what came back into scope rather than assumed.

---

## R10 — Two `src/data/` modules exceed the line limit and have no tests

**Severity: Medium.** Two problems that make each other harder to fix.

T3.3, T3.10 and T3.11 brought every module under 400 lines except two, both outside Phase
3's scope:

| Module | Lines | Coverage |
|---|---|---|
| `src/data/build_panel.py` | 641 | 0 % |
| `src/data/scb_client.py` | 474 | 0 % |

`tests/test_file_sizes.py` exempts them **with their current lengths as ceilings**, so the
exemption covers the size they already are and not further growth.

They are left deliberately. Splitting a 641-line module with no tests is the riskiest
refactor available: `build_panel.py` is where income imputation, the ragged-panel joins and
the forward-fill live — the machinery behind D1, F9 and the `complete_case()` rule — and
nothing in the suite would catch a mistake in moving it.

**Recommendation:** tests before splitting, in that order. This is R5 wearing a second hat:
the modules that most need to be broken up are the ones it is least safe to touch, and the
way out is coverage, not courage.

### CLOSED 2026-09-22 — `build_panel.py` followed, and the set is empty

`build_panel.py` took the same route `scb_client.py` took the day before, in the order this
risk prescribed: tests first, then the split.

Coverage went 0 % to 87 % on the original module. With something able to catch a mistake,
the seam was obvious once looked for — the module was doing three jobs:

| Module | Lines | Holds |
|---|---|---|
| `src/data/clean_sources.py` | 267 | The shapes: one cleaner per raw source |
| `src/data/build_panel.py` | **387** | The joins, and the approximations they carry |
| `src/data/panel_summary.py` | 57 | The refresh report |

The report is the interesting extraction. It was 23 `print` statements inside `build_all`,
which meant the first thing anyone reads after a rebuild was the one part of the pipeline
nothing could check. It returns a string now, and two tests assert it describes what was
actually built.

**Verification:** the split was checked by rebuilding all three panels from the real cached
raw data and comparing to the pre-split artifacts. Identical, row for row, at every level. A
line count proves a file got shorter, not that it still works.

**The tests earned their keep during the split itself.** They failed the moment it landed,
because the cleaners resolve `_read` in their own module while `build_county_panel` also
calls it directly through the re-export, so patching one module left half the builder
reading the real `data/raw/`. That is precisely the class of mistake this risk said would go
uncaught in an untested module, and it was caught in seconds.

`EXEMPT_CEILINGS` is now empty, and `test_no_source_module_still_needs_a_ceiling` asserts it,
so re-opening the exemption is a visible decision rather than a quiet one. Only `labels.py`
remains exempt, as a data file with its own guards.

### Progress 2026-09-21 — `scb_client.py` is out

The condition this risk set was "tests before splitting, in that order". For
`scb_client.py` that condition was met, so the split happened.

The income-definition work gave the module its first tests:
`tests/test_variable_contracts.py` exercises its metadata path against fixtures and,
when a network is present, against the live SCB API. With something able to catch a
mistake, the transport layer moved to `src/data/pxweb.py`: rate limiting, querying,
caching and JSON-stat2 parsing on one side, and on the other only *which table, which
selection*. The two change for different reasons, which is the argument for the seam.

| Module | Before | After |
|---|---|---|
| `src/data/scb_client.py` | 487 | **328**, under the ordinary 400-line limit |
| `src/data/pxweb.py` | — | 194 |

`scb_client.py` has left `EXEMPT` entirely rather than receiving a lower ceiling, which
is what an exemption is supposed to become.

**Verification:** the refactor was checked by re-fetching the income table from SCB
afterwards and comparing the result to the pre-split cache. Identical in shape, columns
and every value. A line-count assertion proves a file got shorter, not that it still
works.

`build_panel.py` remains, at 615 lines and still without direct tests. It is the harder
half: income imputation, the ragged-panel joins and the `complete_case()` rule all live
there, and it keeps the recommendation unchanged.

### Progress 2026-09-17 — reduced, not closed

D2 and D3 took the first bite. The income forward-fill, which was written three times inside
`build_panel.py`, is now one tested function in `src/data/panel_income.py`:

| | Before | After |
|---|---|---|
| `build_panel.py` | 641 lines | **615** |
| its imputation logic | 3 copies, 0 tests | 1 function, **10 tests** |

Still over the 400-line limit, so the exemption stands — but its **ceiling is now 615**, so
the file cannot drift back up under cover of it. Ceilings ratchet downward only.

The remaining bulk is nine `_clean_*` helpers, one per source series. Each reads from
`data/raw/`, which is gitignored, so they cannot be tested as they stand; extracting them
would need the same artifact-identity net D2 used. `scb_client.py` is untouched and keeps its
474-line exemption.

---

## R11 — The map cache cannot hold every year × risk combination

**Severity: Low.** A deliberate memory ceiling, recorded so the next reader knows it was chosen.

The choropleth's rendered HTML is cached (`max_entries=24`), which took a year change from
380 ms to 50 ms. The frame arrives already risk-filtered, so the full input space is 11 years
× 7 risk combinations = **77 distinct maps**, and each document is ~1.2 MB:

| Entries | Cache cost |
|---|---|
| 11 (years only, default filter) | 13 MB |
| **24 (chosen)** | **29 MB** |
| 77 (everything) | 93 MB |

Caching all of it would spend roughly a tenth of a 1 GB Streamlit Cloud instance on an
interaction nobody performs exhaustively. Year changes — the common move — fit comfortably;
an unusual risk combination pays one 380 ms rebuild.

**If this ever needs closing properly:** render all municipalities always and vary only the
polygon *style* by risk class, so the map depends on the year alone and 11 entries suffice.
That changes what the map shows — filtered municipalities would grey out rather than vanish —
which is a design decision, not a performance one.

### CLOSED 2026-09-17

Dissolved rather than mitigated. Decision Q1 was answered **No**: the map is the national
picture and the risk pills filter the lists below it, so the map depends on the year alone.
The input space is 11 entries, not 77, and `max_entries=24` is comfortable headroom rather
than a rationed ceiling.

The memory table above is kept because it is the reasoning that led to the design change, not
because the ceiling still binds.

Measured after the change: **toggling a risk pill costs ~45 ms, down from ~370 ms**, because
the map no longer rebuilds at all. That was the most common interaction on the page.

---

## R12 — A zero price divides to infinity in Version C

**Severity: Low.** Latent, not live. Found by the property tests in Task D1.

`compute_version_c` divides by `transaction_price_sek` without guarding zero, so a zero
price yields `inf`. That value would then flow into the within-year z-score, and because a
standard deviation computed over an infinite value is `NaN`, **one bad row would silently
void every other municipality's `z_c` for that year** — a whole year of the map going blank
from a single cell.

It is not reachable today:

| Panel | Zeros | Nulls | Minimum |
|---|---|---|---|
| municipal | 0 | 290 | 260 000 SEK |
| county | 0 | 21 | 930 000 SEK |
| national | 0 | 1 | 2 050 000 SEK |

Nulls are handled — they produce `NaN`, which `complete_case()` and the artifact build
already exclude. Zero is the unguarded case, and SCB has never published one.

**Left unfixed deliberately.** `tests/test_affordability_properties.py` marks the property
`xfail(strict=True)`, so it documents the gap and will fail loudly if someone adds the guard
without closing this entry. The reason for not simply fixing it: any change to
`compute_version_c` alters every published `z_*`, which is a decision with a blast radius,
not a tidy-up — the same reasoning that made D6 a locked decision rather than a patch.

**Recommendation:** guard it the next time the formula is being changed for another reason,
so the re-publication is paid once. A `price <= 0` row should yield `NaN`, joining the nulls
that `complete_case()` already drops, rather than `inf`.

### CLOSED 2026-09-22 — and the deferral reason turned out not to apply

The recommendation was to guard this the next time the formula was being changed for another
reason, so the re-publication is paid once. Checked before acting, that cost is zero: no
panel at any level holds a non-positive price, the lowest being 260 000 SEK, so the guard
removes no row and moves no value. The rebuild confirmed it — `version_a`, `version_b`,
`version_c` and `z_c` identical to the last byte, no risk class changed.

Guarded in two places, because they fail differently:

- **`scorable_rows`** drops non-positive prices *and incomes* at the input, so no formula
  ever sees one. Income is included because Version B divides by it to form the
  price-to-income ratio; it is the same defect in the same shape, and the register only
  named price because that is where it was found.
- **`compute_version_a` and `compute_version_c`** yield `NaN` rather than `inf` on a
  non-positive price, which guards the direct call that the property tests make.

`test_zero_price_does_not_return_infinity` was the suite's only `xfail`, carrying the
instruction "if this starts passing, someone added the guard: remove the marker and close
R12". It passes; the marker is gone.

`test_guarding_the_denominators_changed_no_published_value` keeps the claim honest: if a
future refresh brings in a non-positive price, it fails, and the re-publication becomes a
deliberate decision with a number attached instead of being paid by accident.
---

## R13 — 24 KB of CSS is inlined on every page load

**Severity: Low.** Accepted because Streamlit leaves no alternative, not because it is ideal.

`inject_css()` writes the whole 24 KB stylesheet into every page render. A `<link>` to a
static file would be fetched once and cached instead.

**Task C1 tried exactly that and it cannot work.** Streamlit's `server.enableStaticServing`
does serve `./static/`, but with the wrong media type:

```
GET /app/static/shai.css    HTTP 200   25.1 KB
  Content-Type: text/plain
  X-Content-Type-Options: nosniff
```

`nosniff` instructs the browser not to infer a better type, so a stylesheet link pointing
there is ignored and the page renders unstyled. Streamlit exposes no setting for the media
type. The work was implemented in full, measured, and reverted.

**Why it is Low.** 24 KB gzips to a few KB on the wire, it is the same bytes every time so an
HTTP/2 connection handles it cheaply, and it is dwarfed by the 860 KB map document that rides
in the same response. Fixing the map payload mattered; this does not.

**Revisit if:** Streamlit gains a media-type mapping for static files, or the app moves off
Community Cloud to a host where a reverse proxy can serve `/static` itself. Flipping it back
on is a small change — the reasoning is recorded in `src/ui/css.py:inject_css`.

---

## R14 — The chart layer sits outside every design guard

**Severity: Medium. CLOSED** by `tests/test_chart_theme_guard.py`.

The design system used to be enforced everywhere except where charts are.
`tests/test_design_system_doc.py` checks the CSS class inventory in both directions and
verifies the map section against `choropleth.py`. `tests/test_css_naming.py` rejects a
class defined outside the `shai-` convention. `tests/test_no_inline_copy.py` keeps user
strings out of pages. **Nothing checked a Plotly figure.**

This was not hypothetical. The two charts added in `60e150d` drifted on three axes at
once and the suite stayed green:

| Deviation | Where | Now |
|---|---|---|
| Plotly's built-in `RdYlGn` instead of `DIVERGING_SCALE`, so the app had two diverging ramps | `src/scenario/charts.py` | `DIVERGING_SCALE`, reversed |
| The primary navy hardcoded as a hex literal instead of `COLORS["primary"]` | `src/scenario/charts.py` | The token |
| `displayModeBar: False` where the seven earlier charts pass `"hover"` | `src/scenario/charts.py`, `src/kontantinsats/sections.py` | `"hover"` everywhere |

Fixing them turned up two more of the same kind that no one had noticed: six colour
literals in `pages/02_Lan_jamforelse.py` and three in `pages/03_Kommun_djupanalys.py`,
each one an exact palette value spelled out by hand. They painted the right pixel and
would have painted the wrong one the day the palette moved.

**Why it was Medium rather than Low.** A stylesheet drift is visible the moment someone
looks at the page. A chart drift looks deliberate: a second red-to-green ramp reads as a
design choice, and a reader has no way to tell it is not the map's scale.

**What the guard does**, in the shape the CSS tests already use: it builds every figure a
test can build and asserts the layout came from `get_chart_layout` and that every colour
in the rendered figure is a token; it scans the source of every figure-building file for
hex literals and built-in colorscale names, because a built figure cannot tell
`"#B94A48"` from `COLORS["high_risk"]`; and it scans call sites for `displayModeBar`,
which lives in the page rather than the figure. Each of the three original deviations was
re-introduced against the guard to confirm it fails rather than merely passing.

**What it still does not cover.** Charts built inline inside a page script cannot be
constructed without a Streamlit process, so they are reached by the source scan but not
by the built-figure assertions. Moving them into builder modules would close that gap.

**Revisit if:** an inline page chart grows enough logic to deserve a module, at which
point it should get one and fall under the built-figure half of the guard too.

---

## R15 — Numbers quoted in docstrings and markdown are guarded nowhere

**Severity: Medium. CLOSED** on 2026-09-22 by `tests/test_prose_matches_artifacts.py`.

`tests/test_copy_matches_artifacts.py` exists because of Findings A, C and H, which were
one defect wearing three coats: prose asserting a number the data no longer supported. It
polices `SWEDISH_LABELS`, which is where the copy a user reads lives, so it was the right
place to start. It works, too — it caught the Version B panel means within minutes of the
income source changing on 2026-09-21.

**It caught one of six.** The same figures were quoted in five other places, none of them
in the label dictionary, and all five survived the refresh silently:

| Where | What it was |
|---|---|
| `src/indices/normalize.py` | Module docstring explaining why B stays pooled |
| `docs/METHODOLOGY.md` | §4, the evidence for decision D5 |
| `docs/REVITALIZATION_PLAN.md` | The D5 decision row, and again in the O2 analysis |
| `tests/test_copy_matches_artifacts.py` | Its own docstring, and a comment beside `NOT_A_VINTAGE` |

The last row is the uncomfortable one. The guard against stale quoted figures had two stale
quoted figures in it, and would not have noticed if it had a hundred.

This is the project's own recurring defect in a place nobody thought to look. The label
dictionary was hardened; the rest of the repository was left as prose.

### Why it took a year to surface

Because until 2026-09-21 the figures happened to be correct. R1 meant Version B moved
whenever the panel did, and the panel had not moved in a way that touched those numbers.
The income switch moved all of them at once, and only the guarded copy noticed.

### The fix, and the limit on it

A general prose checker is not possible. Most numbers in a docstring are parameters,
thresholds or worked examples with no artifact behind them, and asserting against them would
be noise. What *is* checkable is a shape that only ever means one thing here: a signed
decimal bound to a year, as in "−0,31 (2015)". Every occurrence of that shape anywhere in
the repository is now re-derived from `affordability_ranked.parquet`.

Three details that decide whether it works:

- **Wrapped lines are rejoined first.** `labels.py` breaks the D5 sentence mid-claim, so a
  line-by-line scan saw the first figure and missed the second entirely. A guard that reads
  half a sentence is worse than none, because it looks like coverage.
- **Session-log rows are exempt by shape, not by allowlist.** Those entries record what was
  true on a date; rewriting them would destroy the record. Matching the table row means a
  new log entry needs no maintenance here.
- **The claim's own precision sets the tolerance**, so tightening a sentence to three
  decimals does not silently loosen its guard.

It found the four stale figures in `test_copy_matches_artifacts.py` on its first run, which
is the argument for it.

**What it still does not cover:** any quoted figure whose shape is not "signed decimal plus
year". A municipality count or a price in prose would pass unexamined. Extending it means
adding one pattern per checkable fact rather than attempting a general solution.

**Revisit if:** a second class of artifact-derived figure starts appearing in prose, at
which point the pattern list becomes a registry and deserves the structure that implies.

---

## How to use this file

Add a row to the table and a section when something turns up that is real but out of
scope. Move a row to `ACCEPTED` with a one-line reason when a decision is made to live
with it — that is a resolution, not a failure. Delete nothing; a risk that was closed is
worth being able to find later.
