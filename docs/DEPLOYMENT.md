# SHAI — Deployment Guide

**Version:** 1.3.0
**Target:** Streamlit Community Cloud
**Last updated:** 2026-09-15

---

## Prerequisites

- Python **3.11 or newer** (`src/ui/sidebar.py` needs stdlib `tomllib`; the floor is
  declared as `requires-python = ">=3.11"` in `pyproject.toml`). Verified on 3.11 and 3.12.
- A GitHub repository connected to Streamlit Cloud
- No secrets or API keys required — all data is pre-built and committed

---

## Data vintage — what the deployed app is serving

The composite index covers **2014–2024** and **cannot currently advance past 2024**.

All three formulas require **median income** (SCB HE0110), which is published only
through 2024. The panel is ragged: several component series already have 2025.

| Source | Max year upstream | SHAI ships |
|--------|-------------------|-----------|
| Median income (SCB HE0110) | **2024** | 2024 |
| Småhus price (SCB BO0501B) | 2025 | 2024 |
| Bostadsrätt price (SCB BO0501C) | 2025 | 2024 |
| Price index (SCB BO0501A) | 2025 | 2024 |
| Unemployment (Kolada N03937) | 2025 | 2024 |
| CPI (SCB PR0101) | 2026M08 | 2026 |
| Policy rate (Riksbanken SWEA) | live | 2026 |

`data/processed/data_provenance.json` records both bounds separately — `panel_max_year`
for the component series and `complete_case_max_year` for the index — and the UI reads
its vintage from that artifact rather than from the system clock. A refresh therefore
moves `panel_max_year` and leaves the years offered in the sidebar unchanged.

---

## One-time deployment (Streamlit Cloud)

1. Push the repository to GitHub (all `data/processed/*.parquet` files must be committed)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select the repo, branch `main`, main file `app.py`
4. Click **Deploy** — no secrets needed

The app reads only from local parquet files at startup; no external API calls are made
during normal operation.

---

## Local development setup

Two installs, for two audiences. The runtime set is the one that gets deployed.

**Running the app** — what Streamlit Community Cloud performs:

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
streamlit run app.py
```

Eight packages, no compilers, no API calls at startup.

**Refreshing the data** — adds the API clients and the forecast toolchain:

```bash
pip install -e ".[pipeline]"
```

`prophet` and `pmdarima` build from source. That cost belongs on a developer's machine,
never on the serving host, which is why `requirements.txt` and
`[project.optional-dependencies] pipeline` are kept apart. `tests/test_packaging.py`
and `tests/test_runtime_dependencies.py` fail if the two ever drift.

**Running the tests:**

```bash
pip install -e ".[dev]"
pytest tests/
```

---

## Data refresh

SCB and Kolada publish annual data with a lag of 12–18 months. Run the refresh
script to pull new source data, rebuild all panels, and regenerate forecasts.

### Full refresh (recommended annually, Q1)

```bash
python scripts/refresh_data.py
```

This runs four steps in sequence:
1. **Fetch** — pulls all raw data from SCB PxWeb, Riksbanken Swea, and Kolada APIs
2. **Build panels** — rebuilds `data/processed/panel_{municipal,county,national}.parquet`
3. **Compute indices** — rebuilds `data/processed/affordability_*.parquet`
4. **Forecast** — re-runs ARIMA + Prophet and saves `data/processed/forecast_*.parquet`

Total runtime: ~15–30 minutes (dominated by SCB API chunked fetches and Prophet fitting).

### Faster options

```bash
# Skip API calls — rebuild from existing cached raw data only
python scripts/refresh_data.py --no-fetch

# Skip forecasts — rebuild panels and indices only
python scripts/refresh_data.py --no-forecast

# Both
python scripts/refresh_data.py --no-fetch --no-forecast
```

### After a refresh

Commit the updated parquet files and push to trigger a Streamlit Cloud redeploy:

```bash
git add data/processed/ data/raw/
git commit -m "chore: refresh SHAI data — <YYYY-MM-DD>"
git push
```

---

## Bostadsrätt (apartment) price data — BO0501C

The Kontantinsats page (sida 04) supports a **Pristyp** toggle (Småhus / Bostadsrätt).
The apartment price feature requires `data/raw/BO0501C_bostadsratt_price.parquet` to exist.

This file is created automatically by `python scripts/refresh_data.py` (step 1).

Until the file is present, the app falls back to villa (småhus) prices with an inline note.
This fallback is safe and documented.

Coverage once active: 21 counties (län) + national level. SCB publishes no
municipality-level bostadsrätt prices. When Bostadsrätt is selected on sida 04,
the analysis automatically switches to county level (21 län selector).

---

## Forecast refresh schedule

| Trigger | Action |
|---------|--------|
| New SCB/Kolada annual data release (~Q1 each year) | Full refresh |
| Riksbanken policy rate changes significantly | `--no-fetch --no-forecast` rebuild only |
| Bug fix or code change (no new data) | No refresh needed — push code only |

Forecasts are trained on the last non-imputed year of data (auto-detected from the
panel via `is_imputed_income == False`). The 6-year horizon (2025–2030 in the initial
build) shifts forward automatically on the next full refresh.

---

## Income imputation

SCB HE0110 income data lags 12–18 months. When the current calendar year exceeds the
last published income year, the panels forward-fill using 3% nominal growth per year
(`IMPUTED_INCOME_GROWTH_RATE = 0.03`). Imputed rows are flagged with
`is_imputed_income = True`.

The sidebar displays a warning banner `⚠ Inkomst 2025–<year> är modellberäknad (+3%/år)`
when imputed years are active. This disappears automatically once a data refresh
brings in new published income data.

---

## File inventory (must be committed for deploy)

### `data/processed/` — pre-built panels and indices

| File | Description |
|------|-------------|
| `panel_municipal.parquet` | 290 municipalities × years |
| `panel_county.parquet` | 21 counties × years |
| `panel_national.parquet` | National × years |
| `affordability_municipal.parquet` | Versions A/B/C + z-scores, municipal |
| `affordability_county.parquet` | Versions A/B/C + z-scores, county |
| `affordability_national.parquet` | Versions A/B/C + z-scores, national |
| `affordability_ranked.parquet` | Municipal + rank columns |
| `forecast_arima.parquet` | ARIMA 6-year county forecasts |
| `forecast_prophet.parquet` | Prophet 6-year county forecasts |
| `arima_metadata.parquet` | ARIMA model orders and AIC |

### `data/raw/` — cached API responses

| File | Source | Refresh frequency |
|------|--------|-------------------|
| `HE0110_income.parquet` | SCB HE0110 | Annual (Q1) |
| `BO0501_price_index.parquet` | SCB BO0501 | Annual |
| `BO0501_transaction_price.parquet` | SCB BO0501C2 | Annual |
| `BO0501_kt_ratio.parquet` | SCB BO0501C4 | Annual |
| `BO0501C_bostadsratt_price.parquet` | SCB BO0501C | Annual (created on first refresh) |
| `BE0101_population.parquet` | SCB BE0101 | Annual |
| `BO0101_construction.parquet` | SCB BO0101 | Annual |
| `PR0101_cpi.parquet` | SCB PR0101 | Annual |
| `AM0210_unemployment.parquet` | SCB AM0210 | Monthly (Kolada N03937 preferred) |
| `kolada_unemployment.parquet` | Kolada N03937 | Annual |
| `kolada_unemployment_all.parquet` | Kolada N03937 (all levels) | Annual |
| `policy_rate.parquet` | Riksbanken Swea | Annual |

### `data/geo/`

| File | Description |
|------|-------------|
| `kommuner.geojson` | 290 municipality polygons for choropleth map (843 KB) |

---

## Known limitations

See `docs/METHODOLOGY_v2.md` section 7 for the full list (F1–F15). Key ones for ops:

| ID | Description | Impact |
|----|-------------|--------|
| F11 | Apartment prices (BO0501C) require a data refresh to activate; county-level only | Sida 04 falls back to villa prices |
| F12 | Policy rate used as mortgage base (+ bank margin slider) | Rate approximation, documented |
| F13 | Version B uses national income variable | Less granular than A/C |
| F14 | Individual income used, not household | Couple toggle on sida 04 mitigates |
| F15 | CPI fixed in scenario simulator base | CPI shock slider available on sida 05 |

---

## Troubleshooting

**App fails to load with FileNotFoundError:**
Ensure all `data/processed/*.parquet` files are committed and pushed.

**Choropleth map blank:**
Check that `data/geo/kommuner.geojson` is committed (binary tracked by git).

**Forecast page shows empty charts:**
`data/processed/forecast_arima.parquet` or `forecast_prophet.parquet` missing.
Run `python scripts/refresh_data.py --no-fetch` to rebuild from existing raw data.

**BO0501C bostadsrätt data missing:**
Run `python scripts/refresh_data.py` (full refresh) to fetch from SCB API.
The app functions correctly without it — sida 04 falls back to villa prices.
