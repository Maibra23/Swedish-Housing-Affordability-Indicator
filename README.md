# SHAI (Swedish Housing Affordability Indicator)

Streamlit portfolio dashboard. Python 3.11.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Run

```bash
streamlit run app.py
```

If you ever installed `streamlit-echarts` in this environment and see frontend errors about ECharts/BidiComponent on the map page, remove the unused package: `pip uninstall streamlit-echarts` (the app uses Plotly for charts and the map).

Product and methodology details live in the `docs/` folder (PRD, METHODOLOGY, DESIGN_SYSTEM, PLAYBOOK).
