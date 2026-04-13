# Swedish Housing Affordability Indicator (SHAI)
## Product Requirements Document

**Version:** 1.0
**Owner:** Mustafa Ibrahim
**Date:** 2026 04 13
**Status:** Approved for build

---

## 1. Purpose

SHAI is a portfolio grade interactive dashboard that quantifies and forecasts housing affordability in Sweden across three geographic layers (national, county, municipality). The product is designed to signal credit risk literacy, macroeconomic understanding, and forecasting competence to Swedish banking, credit risk, and policy analyst recruiters.

The product is not a research publication. It is a hiring signal artifact.

## 2. Target audience

| Persona | Use case |
|---------|----------|
| Bank credit risk recruiter | Evaluates whether candidate understands affordability mechanics, regulatory regimes, and stress testing |
| Macroeconomic analyst hiring manager | Evaluates forecasting competence and macro variable construction |
| Portfolio reviewer (technical) | Evaluates code quality, dashboard interactivity, methodology transparency |
| Mustafa (self) | Demonstrates end to end project execution under tight time constraint |

## 3. Success criteria

A successful build delivers all of the following:

- Six page Streamlit dashboard deployed to Streamlit Community Cloud
- Three affordability formulas (Version A, B, C) computed for all 290 municipalities
- 21 county level forecasts using both Prophet and ARIMA
- Kontantinsats (down payment) regulatory regime comparison across four periods
- Interactive scenario simulator with three sliders
- Methodology page with full transparency on limitations
- Entire UI in Swedish from day 4 onward
- Visual design ported from KRI mockup (Source Sans Pro, IBM Plex Mono, navy and accent palette)
- Choropleth map matching the Geografisk fördelning pattern from the KRI dashboard

## 4. Out of scope

Items explicitly excluded to protect the 6 day timeline:

- Microdata access (would require institutional affiliation)
- Real estate price predictions at municipal level for kommuner under 50,000 population (data does not exist at that resolution)
- Mortgage spread modeling above policy rate (use policy rate as proxy)
- Bayesian structural time series forecasting (cut to keep scope)
- User authentication, accounts, or saved scenarios
- Mobile responsive design (desktop optimized only)
- A/B testing infrastructure
- Real time API calls from the Streamlit app (all data cached)

## 5. Geographic architecture (3 layer indicator)

### Layer 1: National
- Single time series for Sweden
- All variables available at this resolution
- Used for trend analysis and forecast benchmarking

### Layer 2: County (Län)
- 21 counties
- All variables available
- Primary forecasting layer (best signal to noise ratio)
- Primary user comparison view

### Layer 3: Municipality (Kommun)
- 290 municipalities
- Income, unemployment, population, construction at native resolution
- House price index inherited from county layer (documented limitation)
- K/T ratio supplementary badge for ~39 large municipalities

## 6. Affordability formulas

Three formulas implemented as tabs on the Län comparison page:

**Version A (Bank style):** Affordability = Income / (Price × Rate)
**Version B (Macro composite):** weighted z score of (price to income, rate, unemployment, inflation)
**Version C (Real affordability, primary):** Income / (Price × (Rate − Inflation))

Each formula displayed with: definition, use case, methodological strengths, methodological weaknesses, and a comparison table showing how the same kommun ranks under each.

## 7. Forecasting

Two models on the Kommun djupanalys page as tabs:

**Prophet (default):** user friendly, smooth curves, 8 quarter horizon cap
**ARIMA (recommended):** methodologically appropriate for quarterly macro data, with confidence intervals

Both display widening confidence bands. Forecast horizon capped at 8 quarters.

## 8. Kontantinsats regime engine

Four discrete regulatory regimes:

| Regime | Period | Key rules |
|--------|--------|-----------|
| Pre 2010 | Until October 2010 | No formal minimum down payment |
| Bolånetak | 2010 to 2016 | 15% minimum down payment |
| Amortization 1.0 | 2016 to 2018 | 15% down + amortization for LTV greater than 70% |
| Amortization 2.0 | 2018 to present | Above + extra 1% amortization for LTI greater than 4.5x |

User selects a regime and sees how today's prices translate to required cash and effective monthly cost.

## 9. Pages

| # | Slug | Swedish title | Purpose |
|---|------|---------------|---------|
| 1 | riksoversikt | Riksöversikt | National overview with KPIs and choropleth |
| 2 | lan-jamforelse | Län jämförelse | County comparison, 3 formula tabs |
| 3 | kommun-djupanalys | Kommun djupanalys | Single municipality deep dive with forecasts |
| 4 | kontantinsats | Kontantinsats analys | 4 regulatory regime comparison |
| 5 | scenario | Scenariosimulator | Interactive sliders for stress testing |
| 6 | metodologi | Metodologi och källor | Full methodology, limitations, sources |

## 10. Data sources (verified accessible)

| Source | Endpoint | Resolution | Lag |
|--------|----------|------------|-----|
| SCB HE0110 (income) | PxWebApi 2 | Municipal | ~12 to 18 months |
| SCB BO0501 (prices) | PxWebApi 2 | County (full), Municipal (pop>50k only) | Quarterly |
| SCB AM (unemployment proxy) | PxWebApi 2 | Municipal | Monthly |
| SCB BE0101 (population) | PxWebApi 2 | Municipal | Annual |
| SCB BO (construction) | PxWebApi 2 | Municipal | Annual |
| SCB PR0101 (CPI) | PxWebApi 2 | National | Monthly |
| Riksbanken Swea v1 | REST API | National | Daily |

All data cached as parquet. No live API calls from Streamlit.

## 11. Design system

Ported directly from KRI mockup:

- **Colors:** primary `#0B1F3F`, accent `#C4A35A`, low risk `#2E7D5B`, medium risk `#D4A03C`, high risk `#B94A48`
- **Fonts:** Source Sans Pro (UI), IBM Plex Mono (numerics)
- **Choropleth:** ECharts scatter on geo coordinates, same pattern as Geografisk fördelning
- **KPI cards:** left accent bar, label uppercase, value 32px tabular
- **Tables:** uppercase headers with 1.5px border, IBM Plex Mono for numerics

## 12. Tooling

- **Claude Code:** data extraction, panel construction, index computation, forecasting, kontantinsats engine
- **Cursor Pro+:** Streamlit pages, design system port, Swedish UI from day 4

## 13. Documented limitations (must appear on Metodologi page)

1. Municipal price data limited to pop greater than 50,000 (county fallback used elsewhere)
2. Interest rate national only (municipal differentiation comes from income and price)
3. Income data lags 12 to 18 months (latest = 2023)
4. Prophet forecasts smoother than reality (ARIMA recommended for inference)
5. Forecast horizon capped at 8 quarters
6. Mortgage spread above policy rate not modeled
7. K/T ratio is unweighted mean (SCB methodology)
8. Translation may not capture all Swedish banking nuance

## 14. Acceptance criteria checklist

- [ ] All 6 pages render without errors
- [ ] All 3 formulas computed and ranked consistently
- [ ] Both forecasting models produce 8 quarter outputs
- [ ] Kontantinsats engine handles all 4 regimes
- [ ] Choropleth renders all 290 municipalities with risk coloring
- [ ] Swedish UI throughout with no English leakage
- [ ] Methodology page documents all 8 limitations
- [ ] Deployed and publicly accessible URL