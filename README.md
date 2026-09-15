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
git add data/processed/ data/raw/
git commit -m "chore: refresh SHAI data — $(date +%Y-%m-%d)"
git push
```

See `docs/DEPLOYMENT.md` for the full deployment guide, file inventory, and
troubleshooting reference.

## Documentation

| File | Contents |
|------|----------|
| `docs/METHODOLOGY_v2.md` | Formulas, variables, limitations (F1–F15) |
| `docs/DEPLOYMENT.md` | Deployment guide, data refresh, file inventory |
| `docs/PRD.md` | Product requirements |
| `docs/DESIGN_SYSTEM.md` | KRI design tokens and component patterns |
| `docs/PLAYBOOK_v2.md` | Development playbook |

## Troubleshooting

`docs/DEPLOYMENT.md` holds the operational troubleshooting reference.

**A deploy installs a compiler toolchain, or times out.** Something is installing from
`pyproject.toml` instead of `requirements.txt`. Only the latter is the runtime set;
`prophet` and `pmdarima` live in the `pipeline` extra so they never reach the serving host.

**The suite fails to collect.** Run it from the repository root. `pyproject.toml` puts
both the root and `src` on `pythonpath`, which is what resolves `src.provenance` and
`indices.real_rate`.
