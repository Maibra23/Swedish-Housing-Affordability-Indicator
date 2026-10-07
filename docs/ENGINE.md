# The engine: how a number reaches the screen

**Who this is for.** Anyone who wants to know where a figure on the dashboard came
from, in enough detail to check it by hand or to change it safely. It assumes no
prior knowledge of the project.

`docs/APP_GUIDE.md` tells you what each page is *for*. This document tells you what
each page *computes*. `docs/METHODOLOGY.md` is the formal specification of the
formulas; this is the walkthrough.

Every figure below is drawn from the artifacts committed in `data/processed/`, so
you can reproduce any of them.

---

## 1. There is no single engine

There is a **pipeline** that runs on a developer's machine and writes files, and
there are **two calculators** that run live in the browser. Holding that split in
mind explains almost every design decision in the codebase.

```
  SCB, Riksbanken, Kolada              (1)  raw data, fetched once a year
            |
            v
  panel_municipal / county / national  (2)  one tidy grid per geography
            |
            v
  affordability_*.parquet              (3)  the three formulas applied
            |
            v
  affordability_ranked.parquet         (4)  z-scores, ranks, risk classes
            |
            v
  projection.parquet                   (5)  six years forward, three scenarios
            |
            +---> committed to git, read by the app, never recomputed in the browser
            |
            v
  Kontantinsats engine                 (L)  live, recomputed on every click
  Scenario simulator                   (L)  live, recomputed on every click
```

Stages 1 to 5 run when someone types `python scripts/refresh_data.py`. The outputs
are committed. The deployed app reads those files and makes **no API calls at
startup**; `requirements.txt` does not even contain an HTTP client.

The two live calculators are different in kind. They read raw panel inputs, not
index values, and they compute something new on every interaction.

### Why the split exists

Three reasons, all of them learned the hard way and recorded in
`docs/OPEN_RISKS.md`:

1. **Reproducibility.** A published number should be checkable. `scripts/audit.py`
   verifies the committed artifacts independently of the test suite. If the app
   recomputed the index at render time, there would be nothing stable to audit.
2. **Cold start.** The pipeline once required packages that compile from source.
   Keeping them off the serving host is why the dashboard starts in seconds.
3. **Stability.** Version B pools statistics across the whole panel. Recomputing
   those statistics meant that adding one new year silently rewrote eleven years
   of already published values. The pooling moments are now frozen in
   `data/processed/version_b_reference.json` precisely so that cannot happen.

---

## 2. Stage 1, the raw data

| Source | What it provides | Granularity |
|---|---|---|
| **SCB** | median income, house transaction prices, apartment prices, K/T ratio, population, construction, CPI | kommun, except apartment prices which are län only |
| **Riksbanken** | the policy rate | national |
| **Kolada** | unemployment | kommun |

Two facts here shape everything downstream.

**The policy rate and inflation are national.** There is no Stockholm interest rate.
Every kommun in a given year shares one `policy_rate` and one `cpi_yoy_pct`. This
single fact is why two of the three formulas turn out to produce the same ranking,
which section 4 proves.

**Income is published late.** Prices and unemployment already reach 2025. Income
stops at 2024. Every formula divides by income, so the index stops at 2024 as well.
A refresh will not move it forward until SCB publishes a new income year.

---

## 3. Stage 2, the panel

A panel is a rectangular table: one row per place per year, one column per
variable. Three get built.

| File | Rows |
|---|---|
| `panel_municipal.parquet` | 290 kommuner x 11 years = 3 190 |
| `panel_county.parquet` | 21 län x 11 years = 231 |
| `panel_national.parquet` | 11 |

One municipal row, Stockholm in 2024:

```
median_income            413 600 SEK
transaction_price_sek  8 597 000 SEK
policy_rate                 3.6285 pp    (national)
cpi_yoy_pct                 2.8583 pp    (national)
unemployment_rate           3.4583 %
kt_ratio                      1.23
```

### The imputed income rule, and why it matters

To keep the grid rectangular, income for years SCB has not yet published is filled
forward at 3 % a year (`IMPUTED_INCOME_GROWTH_RATE` in `src/data/panel_income.py`)
and the row is flagged `is_imputed_income`.

Those rows are then **excluded from scoring entirely**, by `complete_case()` in
`src/indices/affordability.py`. This is not fussiness. Version B pools its
statistics across whatever frame it is handed, so letting one filled year in shifts
the pooled mean and standard deviation and moves Version B for every historical
year. That happened once: it moved `version_b` on all 3 190 rows and changed 19
risk classes. Versions A and C are scored within year and were unaffected, which is
why it went unnoticed at the time.

Two separate guards exist as a result. The sidebar stops at
`complete_case_max_year()`, so a filled year cannot be *displayed*. The
`complete_case()` filter stops it being *pooled*.

---

## 4. Stage 3, the three formulas

All three live in `src/indices/affordability.py`. Worked on Stockholm 2024 so you
can check the arithmetic.

### Bankversion (A)

```
A = income / (price x nominal rate)
```

The rate arrives in percentage points and becomes a decimal:

```
A = 413 600 / (8 597 000 x 0.036285) = 1.3259
```

Read it as: annual income covers 1.33 times one year of interest on this house.
**Higher is better.** This is roughly how a bank thinks.

Its weakness is that 3.6 % nominal interest while inflation runs at 2.9 % is not
3.6 % of real cost. That is what C corrects.

### Realversion (C), the one the site runs on

The real rate is nominal minus inflation:

```
real rate = 3.6285 - 2.8583 = 0.7702 pp
C = 413 600 / (8 597 000 x 0.007702) = 6.2468
```

**Higher is better.** The map, the risk classes, the KPI rows, the projection and
the simulator all read C.

**The floor.** The real rate can reach zero or go negative, and dividing by zero
explodes, so the denominator is really `max(R - pi, 0.5)` with the floor at 0.5
percentage points. `docs/METHODOLOGY.md` writes the same floor as 0.005 because it
works in decimals. They are the same number.

The floor is not an edge case. It binds in 9 of the 11 observed years:

| Year | Policy rate | Inflation | Real rate | Used | Mean index |
|---|---|---|---|---|---|
| 2014 | 0.46 | -0.17 | 0.63 | 0.63 | 36.3 |
| 2015 | -0.25 | -0.03 | -0.23 | **0.50** | 43.1 |
| 2016 | -0.48 | 0.98 | -1.47 | **0.50** | 41.9 |
| 2017 | -0.50 | 1.81 | -2.31 | **0.50** | 39.1 |
| 2018 | -0.50 | 1.95 | -2.45 | **0.50** | 38.1 |
| 2019 | -0.26 | 1.80 | -2.06 | **0.50** | 37.6 |
| 2020 | 0.00 | 0.49 | -0.50 | **0.50** | 36.5 |
| 2021 | 0.00 | 2.17 | -2.17 | **0.50** | 32.4 |
| 2022 | 0.77 | 8.35 | -7.58 | **0.50** | 32.0 |
| 2023 | 3.46 | 8.65 | -5.19 | **0.50** | 36.3 |
| 2024 | 3.63 | 2.86 | 0.77 | 0.77 | **23.0** |

In every bolded year the interest rate contributed **nothing at all** and C reduced
to `200 x income / price`. In 2024 inflation fell faster than the policy rate, the
real rate rose above the floor for the first time since 2014, and the national mean
index fell by 36 % as a result. Affordability did not collapse by a third. The
floor stopped binding.

This table is the single most useful thing to understand about the index, and it is
also why the projection in stage 5 treats the real rate as a scenario rather than
something to estimate.

### Makroversion (B)

```
B = 0.35 z(price/income) + 0.25 z(rate) + 0.20 z(unemployment) + 0.20 z(inflation)
B = 1.6163  for Stockholm 2024
```

Structurally different in three ways:

1. **It is a weighted sum, not a ratio.** It goes negative, in 1 919 of the 3 190
   rows.
2. **Higher is worse.** A and C measure affordability, B measures risk. This sign
   flip is the most error prone thing in the codebase and has been inverted by
   accident before, which is why `tests/test_labels.py` asserts the orientation in
   prose as well as in code.
3. **It is the only formula that uses unemployment**, and the only one whose
   statistics are pooled across all eleven years rather than taken within one year.
   That pooling is deliberate: it lets B's level carry a trend over time, from
   -0.31 in 2015 to +0.78 in 2023, tracking the rate shock. A and C, normalised
   within year, are silent about whether the country as a whole improved.

The pooling moments are read from `data/processed/version_b_reference.json`, not
recomputed. See `src/indices/b_reference.py` and R1 in `docs/OPEN_RISKS.md`.

### Why A and C are one formula wearing two hats

```
C / A = 6.2468 / 1.3259 = 4.7114
```

Compute that ratio for any of the other 289 kommuner in 2024 and you get 4.7114
again. Because:

```
A = income / (price x R)
C = income / (price x real)
C / A = R / real
```

and both `R` and `real` are national, so the quotient is one constant for the whole
country in a given year. **C is A multiplied by a constant.** Multiplying every
value in a list by the same number cannot reorder the list.

So A and C give the identical ranking in every year, and only the **level** differs.
In 2024 the 4.71 factor *is* the inflation adjustment. A does not offer a second
opinion about which kommuner are strained; it tells you how large the correction is.

**In 2024. Not in nine of the other ten years.** Both formulas floor their rate — A
at 0.1 pp, C at 0.5 pp — and `C / A` is only `R / (R - pi)` when neither floor
binds, which is true for 2014 and 2024 alone:

| Year | A's rate | C's rate | C / A | The factor is |
|---|---|---|---|---|
| 2014 | 0.46 | 0.63 | 0.74 | the inflation adjustment |
| 2015-2021 | 0.10 floored | 0.50 floored | 0.20 | 0.1/0.5, two constants |
| 2022-2023 | 0.77, 3.46 | 0.50 floored | 1.54, 6.93 | nominal rate over a floor |
| 2024 | 3.63 | 0.77 | 4.71 | the inflation adjustment |

That is why Sida 02 derives the figure from the selected year rather than quoting
2024's: `inflation_adjustment` in `src/indices/agreement.py` returns the factor
*and* the two rates, and `explain_inflation_adjustment` in `src/ui/interpret.py`
picks a sentence that is true for the year on screen. See METHODOLOGY section 3.

`tests/test_formula_agreement.py` pins the identity and the floors, and
`tests/test_inflation_adjustment_copy.py` pins the sentence, so if the transform,
the normalisation window or either floor ever changes, a test fails and the copy
explaining it gets revisited.

---

## 5. Stage 4, from a value to a colour

`src/indices/normalize.py` is the **only** place z-scores, ranks and risk classes
are computed. Three implementations of this logic once coexisted and disagreed on
orientation, which put the least affordable kommuner in the green class on the
national map.

Four steps.

**Step one, take logs for A and C.** They are ratios of positive quantities, so
they are log normal rather than normal. Z-scoring them raw put the class boundaries
on a variable whose normality is rejected at p < 6e-15 in every year. Taking logs
first makes it normal in all eleven years independently, p = 0.34 to 0.83. B is a
sum, is often negative, and a log is undefined for it, so B is scored raw.

**Step two, z-score within the year.** For 2024 the 290 values of `log(C)` have mean
2.9821 and standard deviation 0.5583. Stockholm's `log(6.2468)` is 1.8321:

```
z = (1.8321 - 2.9821) / 0.5583 = -2.0599
```

Within year, not across years. A class is a statement about position among peers in
that year, never about the country over time.

**Step three, flip the sign for A and C** so all three versions point the same way:

```
z_c = +2.0599       higher z = worse affordability, for all three
rank 1 = best affordability, for all three
```

**Step four, cut into three classes** at plus and minus 0.67 standard deviations,
the quartiles of a normal distribution:

```
z < -0.67          lag     (green)
-0.67 to +0.67     medel   (yellow)
z > +0.67          hog     (red)
```

Stockholm's +2.06 is far past 0.67, so **hög risk**, ranked 286th of 290.

The identity again, straight from the artifact:

```
z_a = 2.0599239469689974
z_c = 2.0599239469689970
```

Equal to fifteen decimal places.

**A consequence worth stating plainly.** Because the boundaries are fixed quantiles,
roughly the same *number* of kommuner land in each class every year by construction.
The national count per class carries no trend information. 84 hög risk kommuner in
2024 does not mean things are worse than a year with 80.

---

## 6. Stage 5, the projection

`src/projection.py`. **Nothing here is fitted**, and that is the whole design.

```
income in year n = last observed income x 1.03^n     stated, not estimated
price  in year n = last observed price  x 1.02^n     stated, not estimated
real rate        = one of three scenarios the reader chooses
C(n)             = income(n) / (price(n) x real_rate_pp / 100)
```

The income growth rate matches `IMPUTED_INCOME_GROWTH_RATE`, so the projection and
the panel's own forward fill cannot disagree about income.

Output is `projection.parquet`: 21 counties x 6 years x 3 scenarios = 378 rows.

Stockholms län closed 2024 at C = 7.71. Six years forward:

| Scenario | Real rate assumed | 2025 | 2030 |
|---|---|---|---|
| `floor` | 0.50 pp, the floor binds as in 9 of 11 years | **11.99** | 12.59 |
| `current` | 0.77 pp, today's rate persists | **7.78** | 8.17 |
| `normalised` | 2.00 pp, a return to a pre-2015 norm | **3.00** | 3.15 |

Read the 2025 column: 12.0, 7.8 and 3.0. One year out, from identical income and
price assumptions, the answer varies by a factor of four. Only the rate changed.

The `current` line barely moves from the observed 7.71 to 7.78, because income grows
3 % and price 2 %, a net 1 %.

### Why nothing is fitted

Two fitted pipelines were built, measured and deleted. Backtested against a naive
carry forward control over 63 county horizons, they lost on **every** component:
income 16.2 % error against 6.7 %, price 19.5 % against 5.4 %, the real rate 18.2 %
against 17.5 %. The first projected year was implausible for 21 of 21 counties.

The deeper reason is the formula. C is a reciprocal of the real rate, and the real
rate carries most of the variance in year on year changes of `log C`. Projecting C
six years out means projecting central bank policy six years out. The full evidence
is R16 in `docs/OPEN_RISKS.md` and D19 in `docs/DEVIATIONS.md`.

The three scenario values, 0.5 and last observed and 2.0, are the one editorial
judgement in the whole chain with no artifact behind them.

---

## 7. The two live calculators

### The Kontantinsats engine

`src/kontantinsats/engine.py`. Not part of the index at all. It answers: what does
it take to buy here, under which set of rules?

Five regimes, every one Sweden has actually had:

| Regime | Period | Minimum down | Amortisation |
|---|---|---|---|
| Före 2010 | to Oct 2010 | **0 %** | none |
| Bolånetak | Oct 2010 to Jun 2016 | 15 % | none |
| Amorteringskrav 1.0 | Jun 2016 to Mar 2018 | 15 % | 2 % if LTV > 70 %, 1 % if LTV > 50 % |
| Amorteringskrav 2.0 | Mar 2018 to Mar 2026 | 15 % | as above, **plus 1 % if loan > 4.5x income** |
| Lättnad 2026 | Apr 2026 onward | **10 %** | 2 % if LTV > 70 %, 1 % if LTV > 50 % |

Worked all the way through, Stockholm 2024, single income, 10 % savings rate, 1.7 pp
bank margin, under today's rules:

```
price                      8 597 000 SEK
down payment      10 %  ->   859 700 SEK    the cash you need
loan                       7 737 300 SEK
LTV                             90 %
LTI                           18.7x         loan / income

years to save    859 700 / (413 600 x 0.10) = 20.8 years

effective rate   3.6285 + 1.7 = 5.3285 %
annual interest  7 737 300 x 0.053285 = 412 196 SEK
amortisation     LTV 90 % > 70 %, so 2 %
annual amort     7 737 300 x 0.02     = 154 746 SEK
                                        ---------
annual total                            566 942 SEK
monthly                                  47 252 SEK
residual income  413 600 - 566 942    = -153 342 SEK
```

The engine reports that negative residual rather than hiding it. On a single median
Stockholm income this purchase is not financeable, and the page says so.

Switch the regime to Amorteringskrav 2.0 and nothing changes except the rules:
1 289 550 SEK of cash, 31.2 years, 3 % amortisation because LTI exceeds 4.5x, and
50 717 SEK a month. **Ten and a half extra years of saving, from one rule change.**

Two guards sit in front of that arithmetic (2026-10-05, APP_GUIDE section 12):

- **The effective rate never goes below zero.** In 2015 to 2020 the policy rate was
  negative, and with the margin slider near 0 the sum used to credit interest to the
  borrower. Stockholm 2017 at 0 pp margin read 8 641 SEK a month; it is 11 522.
  The page shows `effective_rate` as the engine returns it.
- **Impossible inputs raise `ValueError`.** A zero income used to report 0 years to
  save. Price and income must be positive and finite, the rate a decimal (a value
  over 0,25 is a percent passed by mistake), the savings rate in (0, 1].

### The scenario simulator

`src/scenario/simulator.py`. A pure function, no stored data, Version C only. B
needs unemployment, which is not exposed as a slider, and A would move in lockstep
with C.

```
new real rate = (policy_rate + rate_shock) - (cpi + cpi_shock)
C_new = income x (1+income_shock)
        / (price x (1+price_shock) x max(new real rate, 0.5) / 100)
```

Stockholms län 2024, baseline C = 7.71. Push the rate up 2 pp and change nothing
else:

```
real rate   0.77 -> 2.77 pp
C           7.71 -> 2.14          a fall of 72.2 %
```

Now add a 5 % pay rise on top:

```
C           7.71 -> 2.25          a fall of 70.8 %
```

A 5 % pay rise recovers 1.4 points of a 72 point fall. **The real rate dominates
everything else in this index**, because C is a reciprocal of it while income is
only a numerator. That is the simulator's lesson in one move, and the reason nobody
tries to project C without stating a rate.

The simulator validates its inputs the same way (positive income and price, finite
values, relative shocks above −100 %), and its baseline is tested equal to
`compute_version_c` on every county-year, so Sida 05 starts from the number the
other pages show. What the page *says* about a result lives in
`src/ui/interpret.py`: since 2026-10-05 it names a shock the floor absorbed, explains
the Riksbanken 2022 preset and warns when the baseline real rate sits within 0,5 pp
above the floor.

---

## 8. Page by page

### Landing page (`app.py`)

**Reads:** `data_provenance.json` only. **Computes:** nothing.

Hero, a stat strip, an explanation of the index, and six navigation cards. The
counts come from provenance rather than literals, so the day the panel grows the
landing page grows with it.

### Sida 01, Riksöversikt

**Reads:** `affordability_ranked.parquet`, filtered to the selected year.
**Engine path:** stage 4. Colours and ranks are read from the file, never
recalculated in the browser.

Four KPI cards, a choropleth beside a distribution histogram, then two ranking
tables of 15 rows each.

The map colours each kommun by `risk_c`, which came from the plus and minus 0.67
cuts. Remember that the class counts carry no trend.

**Example, 2024:**

```
Genomsnittligt SHAI        23,0 points   (-36,5 % against 2023)
Högrisk kommuner           84 of 290
K/T-kvot, genomsnitt       1,40
Worst three by z_c         Lidingö, Danderyd, Solna
Best three by z_c          Åsele, Sorsele, Ragunda
```

That -36,5 % is the floor effect from section 4, not a collapse.

### Sida 02, Län jämförelse

**Reads:** `affordability_municipal.parquet`, then averages kommuner into their län
with `groupby("lan_code").mean()`, plus `affordability_ranked.parquet` for the
agreement panel. **Engine path:** stages 3 and 4, aggregated.

Two tabs, Realversion and Makroversion. One tab per formula that can rank
differently, which is two of the three. Each county carries its own colour keyed by
county code, so it survives a filter change or a tab switch. Deselected counties
stay on as faint grey context. The y axis is logarithmic for Realversion, because
when the real rate sat at its floor the values ran past 400 and squashed recent
years flat.

**Expect two different numbers for the same county.** This page averages kommuner.
Sida 05 reads `affordability_county.parquet`, which computes the index from county
level income and price. A mean of ratios is not the ratio of means:

| Län, 2024 | Sida 02, mean of kommuner | Sida 05, county aggregate |
|---|---|---|
| Stockholms län | 8,45 | 7,71 |
| Västerbottens län | 44,62 | 16,85 |
| Gotlands län | 10,63 | 10,63 |

Neither is wrong; they answer different questions. Gotland agrees exactly because it
is one municipality. Sparse northern counties diverge most, because a few very cheap
kommuner drag an unweighted mean upward.

**Example, the Robusthet panel at the foot, 2024:**

```
Realversion (C)    hög 84   medel 136   låg 70
Makroversion (B)   hög 57   medel 159   låg 74     genuinely different
```

Two rows, not three. Bankversion (A) had one until 2026-10-02 and it read `hög 84
medel 136 låg 70` — C's own counts, since `risk_a` equals `risk_c` on every row.
A table whose purpose is to show that the ranking survives a change of formula
cannot carry a row that agrees by construction. What A does say is stated above
instead, as one derived figure in the comparison expander.

B disagrees with C for **73 of 290 kommuner**. The sharpest case is Perstorp: medel
under C, hög under B, a gap of 150 rank places. B weighs in unemployment, which C
ignores entirely.

### Sida 03, Kommun djupanalys

**Reads:** `affordability_municipal` for the kommun, `affordability_county` for its
county, and `projection.parquet`. **Engine path:** stages 3 and 5.

A kommun dropdown, four KPI cards, the projection chart, then a component breakdown
of three small charts with the driving component highlighted.

**The projection is county level.** SCB publishes nothing supporting a municipal
projection, so the chart draws the kommun's own history, then the county's history
as its own labelled series, then continues the county forward. Select Nacka and the
three projected lines belong to Stockholms län, not to Nacka. The caption says so.

**Example, Stockholm kommun 2024:**

```
SHAI (Version C)     6,2 points
Medianinkomst        413 600 SEK
K/T-kvot             1,23
Styrränta            3,63 %
```

with the county projection from section 6 beneath it.

### Sida 04, Kontantinsats

**Reads:** `affordability_municipal` and `panel_county`, for price, income and the
policy rate only. **Engine path:** stage 2 inputs, then the live engine. Nothing
here touches the A, B, C index.

Controls: Pristyp (Småhus or Bostadsrätt), region, Hushållstyp (one income or two),
savings rate, and a bank margin behind an advanced expander.

**Selecting Bostadsrätt moves the whole page to län level**, because SCB publishes
apartment prices per län only. The region dropdown changes from 290 kommuner to 21
län underneath you. Documented as limitation F11, and it does surprise people.

**Example:** the full Stockholm 2024 walkthrough in section 7. Switching to
Bostadsrätt gives Stockholms län, mean price 4 214 000 SEK, 421 400 SEK of cash,
10,5 years and 23 162 SEK a month.

### Sida 05, Scenariosimulator

**Reads:** `panel_county` for the baseline row, `affordability_ranked` for context.
**Engine path:** stage 2 inputs, then the live simulator.

A county dropdown, four sliders (rate shock in pp, income and price shocks in
percent, inflation shock in pp), a KPI row of baseline against scenario, a surface
over rate and inflation, and a comparison table.

**Example:** the plus 2 pp walkthrough in section 7.

### Sida 06, Metodologi

**Reads:** provenance only, for counts. **Computes:** nothing.

Eight numbered sections: theory, the ten variables and their sources, the three
formulas with their LaTeX, normalisation and risk classes, the projection, the
regime history, the limitations register F1 to F16, validation, and references.

This is where A, B and C are formally defined, which is why the tab strip on Sida 02
does not need to carry the letters.

**Example:** open section 6 and read F13. The interest rate and inflation are
national, so 45 % of Version B's weight carries no information distinguishing one
kommun from another within a single year. Within year municipal rankings are driven
almost entirely by price over income at 35 % and unemployment at 20 %.

---

## 9. What the tests pin

These are the invariants. Break one and a test fails rather than a reader.

| Invariant | Guarded by |
|---|---|
| `z_a` equals `z_c` on every row | `tests/test_formula_agreement.py` |
| rank 1 = best, higher z = worse, stated in prose | `tests/test_labels.py` |
| Every page renders for every offered year, 67 renders | `tests/test_pages_render.py` |
| Figures quoted in copy match the artifacts | `tests/test_copy_matches_artifacts.py` |
| No Swedish copy inline in a page | `tests/test_no_inline_copy.py` |
| Runtime and pipeline dependency sets never merge | `tests/test_packaging.py` |
| The withdrawn vocabulary never returns to the live surface | `tests/test_withdrawn_vocabulary.py` |
| Projected first year within 0.25x to 4x of the last observed | `tests/test_projection.py` |
| Each Kontantinsats regime matches its rules; no cost is negative; every selectable row at every control extreme is finite | `tests/test_kontantinsats_engine.py` |
| The simulator's baseline equals `compute_version_c`; equal rate and CPI shocks cancel; the floor makes rate moves under it inert | `tests/test_scenario_engine.py` |
| Sida 05 names floor absorption, explains the 2022 preset, flags a fragile baseline | `tests/test_scenario_interpretation.py` |

`python scripts/audit.py` checks the committed artifacts separately from the suite,
currently 27 checks.

---

## 10. What to touch when you change something

| To change | Edit | Then |
|---|---|---|
| A formula | `src/indices/affordability.py` | re-run the refresh, commit new parquet, update `docs/METHODOLOGY.md` |
| Class boundaries or the transform | `src/indices/normalize.py` | re-run the refresh, commit new parquet |
| A mortgage rule | the `REGIMES` dict in `src/kontantinsats/engine.py` | nothing else, the page is live |
| A projection assumption | the constants at the top of `src/projection.py` | re-run step 4 only |
| Any user facing text | `src/ui/labels.py` | never inline in a page, the suite enforces it |
| A chart's colours | `src/ui/tokens.py` or `chart_theme.py` | never a literal in a page |

The refresh itself:

```bash
python scripts/refresh_data.py --no-fetch    # rebuild from cached raw data
python scripts/audit.py                      # verify the artifacts
pytest -q                                    # verify everything else
```
