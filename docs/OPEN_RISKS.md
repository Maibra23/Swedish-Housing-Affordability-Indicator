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
| R1 | Version B re-bases every historical value whenever the panel changes | **High** | OPEN |
| R2 | Three pages read year lists from the data instead of `YEAR_RANGE` | Medium | OPEN |
| R3 | The `pipeline` extra is unverified as an install | Medium | OPEN |
| R4 | The forecast step exhausts memory on this machine | Medium | OPEN |
| R5 | `src/` is 15 % covered; the index formulas have no tests | **High** | OPEN |
| R6 | The 67-render check lives in a scratch directory, not the repo | Medium | OPEN |
| R7 | A fresh deploy installs major versions the app was never tested against | **High** | OPEN |

---

## R1 — Version B re-bases every historical value whenever the panel changes

**Severity: High.** Silent, and it changes published numbers.

`compute_version_b` z-scores its four components — price-index ratio, policy rate,
unemployment, CPI — **pooled across every row of the panel it is handed**. That is
deliberate: D5 kept B's construction pooled because the pooled level is the only time
trend the index carries. Versions A and C are normalised within year and are immune.

The consequence is that B's published values are a function of panel composition. Add a
row anywhere and every year moves.

This is not hypothetical. When the 2025 component data landed in T2.4, a single
forward-filled-income row for 2025 entered the index and shifted B for all eleven years:

| Effect on 2014–2024 | Measured |
|---|---|
| `z_b` moved | all 3190 rows, max 0.051 |
| `rank_b` changed | 1816 rows, max 8 positions |
| `risk_b` class changed | 19 rows |

`step_compute_indices` now filters through `complete_case()`, so an *imputed* year can no
longer do this. **That guard does not close the underlying issue.** Next spring SCB
publishes 2025 income, the complete case legitimately advances to 2025, and every
historical Version B value shifts again — correctly, and with nothing announcing it. A
municipality's 2018 risk class will differ from the one someone screenshotted this year.

### The decision

| Option | What it buys | What it costs |
|---|---|---|
| **A. Leave pooled, announce it** | B keeps its time trend, which is the whole reason D5 chose pooling | Every refresh silently rewrites history; anyone citing a B number must cite a vintage |
| **B. Freeze B per vintage** | Published values stop moving; citations stay valid | Two municipalities scored in different vintages are no longer comparable |
| **C. Normalise B within year like A and C** | Consistency across all three versions; no re-basing ever | **Deletes the trend B exists to measure** — D5 rejected this for that reason |
| **D. Split it** | A pooled `version_b_level` for the trend plus a within-year `z_b` for ranking | Two numbers to explain; more surface in the UI and the methodology |

**Recommendation: D, and A as the interim.** The two jobs B is doing — "how much macro
pressure is there now versus history" and "where does this kommun stand among its peers" —
genuinely need different normalisations, and forcing one number to do both is what creates
the instability. Until that is built, keep the pooling and state the vintage dependence
explicitly wherever a B rank or class is shown.

**Before deciding, check:** how many municipality-years actually change class across a
realistic refresh. Nineteen out of 3190 (0.6 %) may be small enough to accept with a note,
which makes A permanent and cheap.

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

---

## R5 — `src/` is 15 % covered and the index formulas have no tests

**Severity: High.** The most valuable code is the least verified.

Measured after Phase 1 (`pytest --cov=src`): **15 %** overall. At 0 %:

- `src/data/` — every API client and `build_panel.py` (346 statements)
- `src/forecast/` — both pipelines
- `src/kontantinsats/engine.py`, `src/scenario/simulator.py`
- **`src/indices/affordability.py`** — the module that computes Version A, B and C

The suite is strong where it exists, but it is mostly *source-level guards*: assertions
that a page does not recompute a z-score, that a literal is absent, that two files agree.
Those prevent the specific regressions the audit found. They do not check that the
formulas are right. Finding J is not meaningfully closed.

Note the coverage figure understates things — the 67-render AppTest check exercises the
pages and much of `src/ui/` but does not run under `pytest`. See R6.

**Recommendation:** prioritise `affordability.py` over the rest. It is 65 statements, it is
the heart of the product, and R1 above was found by reading it rather than by a test
failing. Property tests suit it well: orientation contracts, monotonicity in each input,
behaviour at zero and negative real rates.

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

**Note on `requests`:** the clean install contains it as a transitive dependency of
streamlit, which is correct and expected — T2.1's criterion is that it is absent from
`requirements.txt`, not from the environment. It emits a `RequestsDependencyWarning` about
`charset_normalizer` in that venv. Harmless: the import graph confirms no page imports
`requests`.

---

## How to use this file

Add a row to the table and a section when something turns up that is real but out of
scope. Move a row to `ACCEPTED` with a one-line reason when a decision is made to live
with it — that is a resolution, not a failure. Delete nothing; a risk that was closed is
worth being able to find later.
