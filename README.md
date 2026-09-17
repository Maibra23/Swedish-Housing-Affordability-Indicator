# SHAI — Swedish Housing Affordability Indicator

Streamlit dashboard analysing housing affordability across 290 Swedish municipalities
using three econometric formulas (Version A/B/C), a kontantinsats engine covering
four regulatory regimes, a scenario simulator, and 6-year ARIMA/Prophet forecasts.

**Version:** 1.3.0 · **Python:** 3.11+ · **Data:** SCB, Riksbanken, Kolada

## Data vintage

The composite index covers **2014–2024**. It ends at 2024 because **median income**
(SCB HE0110) ends at 2024, and all three formulas require it. Prices, the price index
and unemployment already have 2025 published — refreshing them advances those component
series but **cannot** move the index past 2024. The app reads its vintage from
`data/processed/data_provenance.json` rather than from the clock, so what it shows is
always the age of the data in front of you.

## Setup

Two installs, because there are two audiences.

**To run the app** — this is what Streamlit Community Cloud performs on deploy:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Eight packages, no compilers. The app only reads the committed parquet artifacts.

**To refresh the data** — adds the SCB/Riksbanken/Kolada clients and the forecast
toolchain. `prophet` and `pmdarima` compile from source, so expect a slow first install;
that is exactly why they are not in the runtime set:

```bash
pip install -e ".[pipeline]"
```

Add `.[dev]` for the test suite; the extras combine: `pip install -e ".[pipeline,dev]"`.

## Run locally

```bash
streamlit run app.py
```

## Tests

```bash
pytest tests/
```

## Auditing a release

```bash
python scripts/audit.py
```

Twenty-seven checks re-derived from the committed artifacts, independent of the test
suite: the index contract and its orientation, the sidebar against the data, the
methodology's quoted figures against what the data now says, and the docs against the
code. Exit code 0 means everything agrees. **Run it after every data refresh** — that is
when copy and data drift apart.

## Data refresh

Source data is pre-built and committed as parquet files. To refresh after SCB/Kolada
publish new annual data (typically Q1 each year):

```bash
# Full refresh — fetch APIs, rebuild panels, compute indices, regenerate forecasts
python scripts/refresh_data.py

# Faster options
python scripts/refresh_data.py --no-fetch       # rebuild from cached raw data
python scripts/refresh_data.py --no-forecast    # skip forecast step (~5–15 min saved)
```

After refreshing, commit the updated parquet files and push to redeploy:

```bash
# data/raw/ is a local cache and is gitignored — only data/processed/ deploys
git add data/processed/
git commit -m "chore: refresh SHAI data — $(date +%Y-%m-%d)"
git push
```

See `docs/DEPLOYMENT.md` for the full deployment guide, file inventory, and
troubleshooting reference.

## Documentation

| File | Contents |
|------|----------|
| `docs/METHODOLOGY.md` | Formulas, variables, normalisation decisions, limitations F1–F16 |
| `docs/DEPLOYMENT.md` | Install paths, data vintage, refresh, file inventory, troubleshooting |
| `docs/REVITALIZATION_PLAN.md` | The work plan this codebase is being brought back through |
| `docs/OPEN_RISKS.md` | Known hazards and pending decisions, with recommendations |
| `docs/OPTIMIZATION_PLAN.md` | Payload, caching and coverage work, with measurements |
| `docs/DESIGN_SYSTEM.md` | CSS tokens and component patterns |
| `docs/CHOROPLETH_MAP_REFERENCE.md` | Folium map implementation reference |
| `docs/PRD.md` | Product requirements |
| `docs/PLAYBOOK.md` | Development playbook |
| `docs/DEVIATIONS.md` | Where the implementation departs from the PRD, and why |
| `docs/archive/` | Build-time artifacts and superseded analyses, kept for reference only |

`docs/archive/` is not maintained. Nothing outside it should link into it as current
guidance.

## Troubleshooting

`docs/DEPLOYMENT.md` holds the operational troubleshooting reference.

**A deploy installs a compiler toolchain, or times out.** Something is installing from
`pyproject.toml` instead of `requirements.txt`. Only the latter is the runtime set;
`prophet` and `pmdarima` live in the `pipeline` extra so they never reach the serving host.

**The suite fails to collect.** Run it from the repository root. `pyproject.toml` puts
both the root and `src` on `pythonpath`, which is what resolves `src.provenance` and
`indices.real_rate`.
