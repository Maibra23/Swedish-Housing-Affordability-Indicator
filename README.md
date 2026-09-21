# SHAI · Swedish Housing Affordability Indicator

A Streamlit dashboard measuring structural housing affordability across Sweden's
290 kommuner and 21 län, built on open data from SCB, Riksbanken and Kolada.

**Version:** 1.3.0 · **Python:** 3.11 · **Index period:** 2014–2024

## Project overview

Affordability is not one number. SHAI reports three, each answering a different
question about the same market:

| | Question it answers |
|---|---|
| **Version A** (bank) | Can a household carry the monthly cost at today's nominal rate? |
| **Version B** (macro) | How much pressure is the market under, relative to its own history? |
| **Version C** (real) | Version A adjusted for inflation, using the real rate. Recommended. |

Seven pages sit on top of that index:

- **Riksöversikt** · choropleth map and score distribution across all 290 kommuner.
- **Län jämförelse** · the 21 län ranked under each formula, #1 being the most affordable.
- **Kommun djupanalys** · per-kommun history with ARIMA and Prophet forecasts to 2030.
- **Kontantinsats** · down payment, savings time and monthly cost under the five Swedish
  mortgage regimes, from pre-2010 to the 2026 easing, for houses or apartments.
- **Scenariosimulator** · stress-test one län against rate, income, price and inflation shocks.
- **Metodologi** · formulas, sources and every documented limitation.

**Stack:** Streamlit · pandas · Plotly · Folium · statsmodels · pmdarima · Prophet · Parquet.

**Data vintage.** The index ends at 2024 because every formula divides by median
inkomst, and 2024 is the last year SCB has published it. Prices, unemployment and the
price index already reach 2025 and are used wherever they stand alone. A refresh will
not move the index forward until SCB publishes a new income year.

## Install

Two audiences, two installs. Serving only reads committed Parquet, so it needs
neither the API clients nor the forecast toolchain:

```bash
pip install -r requirements.txt     # run the dashboard (what Streamlit Cloud installs)
pip install -e ".[pipeline]"        # additionally refresh data from the APIs
streamlit run app.py
```

## Usage

**Reading the dashboard.** Choose a year and an optional risk filter in the sidebar;
both follow you between pages. Risk classes are relative to that year's national
distribution, so "hög risk" means "against its peers this year", never "worse than 2014".

**A worked example.** On Kontantinsats, Stockholm 2024, one income, 10 % sparkvot and a
1.7 pp bank margin needs 859 700 SEK down and 16.1 years to save it, at 47 252 SEK a
month. Switch Pristyp to Bostadsrätt and the analysis moves to län level, where the same
household needs 420 600 SEK and 7.6 years, because SCB publishes apartment prices per
län only.

**Refreshing the data**, after SCB or Kolada publish a new year:

```bash
python scripts/refresh_data.py                  # fetch, rebuild, recompute, reforecast
python scripts/refresh_data.py --no-fetch       # rebuild from cached raw data
python scripts/refresh_data.py --no-forecast    # skip forecasts, saves 5-15 min
```

Commit the regenerated files in `data/processed/`; the raw API cache in `data/raw/` is
gitignored. Run `python scripts/audit.py` to check the shipped artifacts independently,
and `pytest -q` for the suite.

## Contributing

Bugs and pull requests go through
[GitHub issues](https://github.com/Maibra23/Swedish-Housing-Affordability-Indicator/issues).

- **Reporting a bug:** name the page, the selected year and the region, and say what you
  expected the number to be. A number that looks wrong is the most valuable report here.
- **Pull requests:** branch off `main` and keep the suite green. Anything touching a
  formula, a normalisation rule or a regime definition needs a test: these carry an
  orientation contract, rank 1 = best and higher z = worse, that is easy to invert by
  accident and has been inverted before.
- **User-facing copy** lives in `src/ui/labels.py`, not inline in the pages, and the suite
  enforces that. Methodology changes need a matching edit to `docs/METHODOLOGY.md`. A
  limitation that is known but undocumented is treated as a bug.

## License

MIT, copyright (c) 2026 Maibra23. Use, modify and redistribute it, commercially included,
provided the copyright notice travels with it. See [`LICENSE`](LICENSE). Supplied without
warranty.

The data is not covered by this license: it belongs to SCB, Riksbanken and Kolada, under
their terms.

## Documentation

| File | Contents |
|------|----------|
| `docs/METHODOLOGY.md` | Formulas, variables, limitations |
| `docs/ANALYSIS_GUIDE.md` | How to read Kontantinsats and Scenariosimulator, and what A/B/C are for |
| `docs/DEPLOYMENT.md` | Deployment, data refresh, file inventory |
| `docs/REVITALIZATION_PLAN.md` | Work plan, audit findings, session log |
| `docs/OPTIMIZATION_PLAN.md` | Performance work and its measurements |
| `docs/OPEN_RISKS.md` | Known risks carried deliberately |
| `docs/DEVIATIONS.md` | Where the build departs from the PRD, and why |
| `docs/DESIGN_SYSTEM.md` | Design tokens, chart rules and component patterns |
| `docs/ADR/` | Decision records: what was chosen, what was rejected, and on what evidence |
| `docs/CHOROPLETH_MAP_REFERENCE.md` | Map implementation reference |
| `docs/PRD.md` | Product requirements |
| `docs/PLAYBOOK.md` | Development playbook |

`docs/archive/` holds superseded analyses. It is kept for provenance and is
not maintained; do not read it as current guidance.
