# SHAI Methodology Reference
## Theoretical Framework, Variables, Sources, Limitations

**Version:** 1.0
**Companion to:** PRD.md, PLAYBOOK.md
**Status:** Living document, update as build progresses

---

## 1. Theoretical foundation

Housing affordability is the relationship between a household's capacity to pay and the cost of housing. Banks operationalize this through three lenses:

1. **Flow affordability** (can the household service the monthly payment?)
2. **Stock affordability** (can the household assemble the down payment?)
3. **Risk affordability** (what happens under stress?)

SHAI implements all three through the formula triplet (A, B, C), the kontantinsats engine, and the scenario simulator respectively.

## 2. Variable register

| Variable | Symbol | Source | Resolution | Update frequency |
|----------|--------|--------|------------|------------------|
| Median disposable income | I | SCB HE0110 | Municipal, county, national | Annual |
| House price index | P | SCB BO0501 | County, national | Quarterly |
| Transaction price (K/T) | KT | SCB BO0501 | Municipal (pop>50k only), county | Quarterly |
| Policy rate | R | Riksbanken Swea | National | Daily |
| CPI | CPI | SCB PR0101 | National | Monthly |
| Real interest rate | r* = R − π | Derived | National | Monthly |
| Unemployment | U | SCB AM | Municipal, county, national | Monthly |
| Population | N | SCB BE0101 | Municipal, county, national | Annual |
| Housing completions | H | SCB BO | Municipal, county, national | Annual |

## 3. Formulas

### Version A: Bank style affordability ratio

```
Affordability_A(i, t) = Income(i, t) / (Price(i, t) × Rate(t))
```

**Use case:** Quick monthly cost ratio, mirrors traditional bank affordability calculators.
**Strength:** Intuitive, easy to explain to non technical stakeholders.
**Weakness:** Ignores inflation (nominal rate distortion), ignores down payment.

### Version B: Macro composite pressure index

```
Risk_B(i, t) = 0.35 × z(P/I) + 0.25 × z(R) + 0.20 × z(U) + 0.20 × z(π)
```

Where z() denotes z score normalization across the panel.

**Use case:** Multi factor pressure monitoring, mirrors central bank macroprudential dashboards.
**Strength:** Captures multiple risk channels simultaneously.
**Weakness:** Weights are subjective, z scores require stable reference period.

### Version C: Real affordability (primary, recommended)

```
Affordability_C(i, t) = Income(i, t) / (Price(i, t) × max(R(t) − π(t), 0.005))
```

The max() floor prevents division explosion when real rates are near zero or negative.

**Use case:** Academically defensible, captures real cost of capital.
**Strength:** Inflation adjusted, standard in economics literature.
**Weakness:** Real rate can be near zero or negative, requires floor handling.

## 4. Index normalization and ranking

For comparison across formulas, each index is z score normalized within its own distribution. Higher z score equals worse affordability for Version B (it is a risk index), better affordability for Versions A and C (they are capacity indices). The Riksöversikt page inverts A and C so all three display "higher equals worse" for visual consistency, with explicit labeling.

## 5. Forecasting approach

### Prophet (default in UI)

- Library: `prophet` (Meta)
- Decomposes into trend + seasonality + holidays
- Suitable for: user friendly visualization, non technical audiences
- **Limitation flag in UI:** "Prophet is optimized for daily business series. For quarterly macro data, see ARIMA tab."

### ARIMA (recommended for inference)

- Library: `statsmodels.tsa.arima.model`
- Order selection via auto_arima from `pmdarima`
- Suitable for: methodologically rigorous forecasting
- **Limitation flag in UI:** "Confidence intervals widen rapidly beyond 4 quarters. Interpret accordingly."

### Forecast targets

Forecast each component separately (income, price index, rate), then compose the affordability index. Direct affordability forecasting introduces stationarity issues.

### Horizon

Capped at 8 quarters (24 months). Beyond this, confidence intervals exceed useful interpretation.

## 6. Kontantinsats regime engine

Four regulatory regimes modeled:

| Regime | Period | Down payment | Amortization rule |
|--------|--------|--------------|-------------------|
| Pre 2010 | Until Oct 2010 | No formal min | None mandatory |
| Bolånetak | Oct 2010 to Jun 2016 | 15% min | None mandatory |
| Amortization 1.0 | Jun 2016 to Mar 2018 | 15% min | 2% if LTV>70%, 1% if LTV>50% |
| Amortization 2.0 | Mar 2018 to present | 15% min | Above + 1% extra if LTI>4.5x |

For each regime applied to today's median price and median income:
- Required cash (kontantinsats absolute amount)
- Years of saving needed at 10% savings rate
- Effective monthly cost (interest + amortization)
- Disposable income remaining after housing

## 7. Scenario simulator

Three sliders:

| Slider | Range | Step | Default |
|--------|-------|------|---------|
| Interest rate shock | -2% to +5% | 0.25% | 0% |
| Income growth shock | -10% to +10% | 1% | 0% |
| Price shock | -25% to +25% | 5% | 0% |

Output: recalculated Version C affordability for selected county, with delta from baseline highlighted.

## 8. Eight structural limitations (the F1 to F8 register)

| ID | Limitation | Mitigation |
|----|------------|------------|
| F1 | Municipal price coverage gap (only 39 of 290) | Use county price index for all, badge actual K/T where available |
| F2 | National interest rate at municipal level | Document explicitly, show that municipal variation comes from income |
| F3 | Three formulas rank differently | "Why these differ" panel with comparison table |
| F4 | Prophet weak for macro quarterly data | ARIMA recommended in tab labels |
| F5 | Kontantinsats is step function not continuous | Discrete regime selector, not slider |
| F6 | Long horizon forecasts mislead | Hard cap at 8 quarters |
| F7 | SCB API rate limits | Cached parquet, no live calls |
| F8 | Translation loses nuance | Glossary file in skill, banking specific terminology curated |

## 9. Data validation checks

Before publishing each computation:

1. Median income should be monotonically increasing nominally across years
2. Real income (deflated) should be roughly stable or slowly rising
3. Stockholm county should rank in top 5 worst affordability under Version C
4. Norrbotten county should rank in top 5 best affordability under Version A
5. K/T values should be between 1.0 and 4.0 for all included municipalities
6. Forecast intervals should widen monotonically

If any check fails, halt and investigate before proceeding.

## 10. References

- SCB BO0501 product page: https://www.scb.se/bo0501-en
- SCB HE0110 product page: https://www.scb.se/he0110-en
- Riksbanken Swea API: https://www.riksbank.se/en-gb/statistics/interest-rates-and-exchange-rates/
- Finansinspektionen amortization rules: https://www.fi.se/en/our-registers/the-amortisation-requirement/