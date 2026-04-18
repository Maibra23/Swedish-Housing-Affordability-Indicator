# SHAI — Swedish Housing Affordability Indicator

Streamlit dashboard analysing housing affordability across 290 Swedish municipalities
using three econometric formulas (Version A/B/C), a kontantinsats engine covering
four regulatory regimes, a scenario simulator, and 6-year ARIMA/Prophet forecasts.

**Version:** 1.3.0 · **Python:** 3.11 · **Data:** SCB, Riksbanken, Kolada

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Run locally

```bash
streamlit run app.py
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

If you see frontend errors about ECharts/BidiComponent on the map page, remove the
unused package: `pip uninstall streamlit-echarts` (the app uses Plotly for charts
and Folium for the choropleth map).
