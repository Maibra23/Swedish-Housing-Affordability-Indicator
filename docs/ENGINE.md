# The engine: how a number reaches the screen

**Who this is for.** Anyone who wants to know where a figure on the dashboard came
from, in enough detail to check it by hand or to change it safely. It assumes no
prior knowledge of the project.

`docs/APP_REFERENCE.md` (Part I) tells you what each page is *for*. This document tells you what
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
`docs/APP_REFERENCE.md` (Part II):

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
| **SCB** | median income, house transaction prices, apartment prices, K/T ratio, population, construction, KPI, KPIF, household mortgage rates | kommun, except apartment prices (län) and rates and prices indices (national) |
| **Riksbanken** | the policy rate, used only by Sida 04's floating-loan model | national |
| **Kolada** | unemployment | kommun |

Two facts here shape everything downstream.

**The mortgage rate and inflation are national.** There is no Stockholm interest rate.
Every kommun in a given year shares one `mortgage_rate` (SCB's mean on new household
loans across all fixation periods) and one `kpif_yoy_pct`. This single fact is why two
of the three formulas turn out to produce the same ranking, which section 4 proves.

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
mortgage_rate               4.2962 %     (national, all fixation periods)
kpif_yoy_pct                1.9083 pp    (national, Version B only)
policy_rate                 3.6285 pp    (national, Sida 04 only)
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

All three live in `src/indices/affordability.py`; A and C call `src/indices/cost_model.py`.
Worked on Stockholm 2024 so you can check the arithmetic.

A and C price the same loan: **85 % of the mean small-house price**, at the year's **mean
rate on new mortgages**, carried by **two earners on the median income**. Both come out as
a **percentage of household income**, so **higher is worse**, the same direction as B.

### Bankversion (A)

```
A = 100 x 0.85 x price x rate / (2 x income)
A = 100 x 0.85 x 8 597 000 x 0.042962 / 827 200 = 37.95
```

Read it as: gross interest on the loan takes 38 % of two median incomes. This is roughly
how a bank thinks about the interest burden.

### Kassaflödesversion (C), the one the site runs on

C is what actually leaves the household: interest after the 30 % ränteavdrag, plus the
amortisation the requirement demands of a loan above 70 % of value (0 before June 2016,
2 % after):

```
cost per krona = 4.2962 x 0.70 + 2.00 = 5.0073 % of the loan a year
C = 100 x 0.85 x 8 597 000 x 0.050073 / 827 200 = 44.23
```

The map, the risk classes, the KPI rows, the projection and the simulator all read C.

**No floor.** The rate multiplies; it is never a denominator. The mortgage rate stayed
between 1.5 and 4.5 % across the whole index period, and a non-positive rate is refused
rather than clipped. Until 2026-10-20 C divided by `max(policy rate − KPI, 0.5)`; that floor
bound in 9 of 11 years and is the history behind METHODOLOGY section 3.

**Read the level with its two parts.** Because the cost per krona `q` is national, the
national mean is exactly `0.425 x q x mean(price / income)`. `agreement.cost_history()`
returns both per year, and the 2016–2017 jump in the level is the amortisation requirement
taking effect, not prices. Sidor 01, 02 and 06 show that table in a collapsed panel.

### Makroversion (B)

```
B = 0.35 z(price/income) + 0.25 z(mortgage rate) + 0.20 z(unemployment) + 0.20 z(KPIF)
B = 1.4989  for Stockholm 2024
```

Structurally different in three ways:

1. **It is a weighted sum, not a ratio.** It goes negative, in 1 877 of the 3 190
   rows.
2. **Higher is worse**, like A and C since they became cost shares. Until 2026-10-20 A
   and C ran the other way and B was the odd one out; that sign flip was the most error
   prone thing in the codebase and was inverted by accident more than once, which is
   why `tests/test_ranked_artifact.py` and `tests/test_labels.py` assert the orientation.
3. **It is the only formula that uses unemployment**, and the only one whose
   statistics are pooled across all eleven years rather than taken within one year.
   That pooling is deliberate: it lets B's level carry a trend over time, from
   -0.27 in 2019 to +0.72 in 2023, tracking the rate shock. A and C, normalised
   within year, are silent about whether the country as a whole improved.

The pooling moments are read from `data/processed/version_b_reference.json`, not
recomputed. See `src/indices/b_reference.py` and R1 in `docs/APP_REFERENCE.md` (Part II).

### Why A and C are one formula wearing two hats

```
C / A = 44.23 / 37.95 = 1.1655
```

Compute that ratio for any of the other 289 kommuner in 2024 and you get 1.1655 again.
Because:

```
A = k x (price / income) x r
C = k x (price / income) x (0.7 r + 100 a)
C / A = (0.7 r + 100 a) / r
```

and both `r` and `a` are national, so the quotient is one constant for the whole country
in a given year. **C is A multiplied by a constant.** Multiplying every value in a list by
the same number cannot reorder the list.

So A and C give the identical ranking in every year, and only the **level** differs. The
factor means the same thing every year: the deduction and amortisation against gross
interest. It is 0.70 in 2014–2015 (deduction only), 1.8 to 2.0 in 2017–2021, 1.17 in
2024. `cost_adjustment` in `src/indices/agreement.py` returns it with the rate and the
amortisation, and `explain_cost_adjustment` in `src/ui/interpret.py` states the parts on
Sida 02.

`tests/test_formula_agreement.py` pins the identity and the absence of a floor;
`tests/test_cost_history.py` pins the factor, the split and the METHODOLOGY table.

---

## 5. Stage 4, from a value to a colour

`src/indices/normalize.py` is the **only** place z-scores, ranks and risk classes
are computed. Three implementations of this logic once coexisted and disagreed on
orientation, which put the least affordable kommuner in the green class on the
national map.

Four steps.

**Step one, take logs for A and C.** They are products and ratios of positive
quantities, so they are log normal rather than normal. Z-scoring them raw would put the
class boundaries on a variable whose normality is rejected at p < 3e-16 in every year.
Taking logs first makes it normal in all eleven years independently, p = 0.24 to 0.66. B is a
sum, is often negative, and a log is undefined for it, so B is scored raw.

**Step two, z-score within the year.** For 2024 the 290 values of `log(C)` have mean
2.6394 and standard deviation 0.5583. Stockholm's `log(44.2346)` is 3.7895:

```
z = (3.7895 - 2.6394) / 0.5583 = +2.0599
```

Within year, not across years. A class is a statement about position among peers in
that year, never about the country over time.

**Step three, no sign flip.** All three versions already point the same way, higher =
worse, so the z-score is used as it is. (Until 2026-10-20 A and C were affordability
ratios and their z had to be negated here; the result was this same +2.0599.)

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
mortgage rate    = one of three scenarios the reader chooses
C(n)             = 100 x 0.85 x price(n) x (rate x 0.7 + 2 %) / (2 x income(n))
```

The income growth rate matches `IMPUTED_INCOME_GROWTH_RATE`, so the projection and
the panel's own forward fill cannot disagree about income.

Output is `projection.parquet`: 21 counties x 6 years x 3 scenarios = 378 rows.

Stockholms län closed 2024 at C = 35.86 % of income. Six years forward:

| Scenario | Mortgage rate assumed | 2025 | 2030 |
|---|---|---|---|
| `low` | 1.53 %, the lowest year in the window (2021) | **21.78** | 20.74 |
| `current` | 4.30 %, the last index year persists | **35.51** | 33.82 |
| `high` | 6.00 %, a stated stress level | **43.97** | 41.87 |

Read the 2025 column: 21.8, 35.5 and 44.0. C is linear in the rate, so equal rate steps
give equal gaps in cost. The lines drift down slowly because income grows 3 % and price
2 %, so the loan shrinks relative to income by about 1 % a year.

### Why nothing is fitted

Two fitted pipelines were built, measured and deleted. Backtested against a naive
carry forward control over 63 county horizons, they lost on **every** component:
income 16.2 % error against 6.7 %, price 19.5 % against 5.4 %, the rate 18.2 %
against 17.5 %. Under the old real-rate formula the first projected year was implausible
for 21 of 21 counties.

The deeper reason is that the rate drives most of the year on year variance in `log C`
(about 60 % since 2017), and the rate is policy and bank pricing. Projecting C six years
out means projecting those six years out. The full evidence is R16 in
`docs/APP_REFERENCE.md` (Part II).

The stress rate of 6 % is the one editorial judgement in the whole chain with no artifact
behind it; the low and current rates are read from the panel.

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

Worked all the way through, Stockholm 2024, single income, 10 % savings rate, and the
page's default bank margin for 2024, which is the margin SCB observed that year (0.76 pp,
rounded onto the slider's 0.1 grid as 0.8 pp), under today's rules:

```
price                      8 597 000 SEK
down payment      10 %  ->   859 700 SEK    the cash you need
loan                       7 737 300 SEK
LTV                             90 %
LTI                           18.7x         loan / income

years to save    859 700 / (413 600 x 0.10) = 20.8 years

effective rate   3.6285 + 0.8 = 4.4285 %
annual interest  7 737 300 x 0.044285 = 342 646 SEK
amortisation     LTV 90 % > 70 %, so 2 %
annual amort     7 737 300 x 0.02     = 154 746 SEK
                                        ---------
annual total                            497 392 SEK
monthly                                  41 449 SEK
residual income  413 600 - 497 392    = -83 792 SEK
```

The engine reports that negative residual rather than hiding it. On a single median
Stockholm income this purchase is not financeable, and the page says so.

Switch the regime to Amorteringskrav 2.0 and nothing changes except the rules:
1 289 550 SEK of cash, 31.2 years, 3 % amortisation because LTI exceeds 4.5x, and
50 717 SEK a month. **Ten and a half extra years of saving, from one rule change.**

Two guards sit in front of that arithmetic (2026-10-05, APP_REFERENCE Part I section 12):

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
new rate = max(mortgage_rate + rate_shock, 0.5)
C_new    = 100 x 0.85 x price x (1+price_shock) x (new rate x 0.7 + a) / (2 x income x (1+income_shock))
```

The rate shock moves the **mean new-mortgage rate**, not the policy rate: how much of a
policy move reaches households depends on how many loans are fixed, so the slider states
the rate households face instead of guessing the pass-through (F12). There is no
inflation slider; inflation reaches a cash-flow share only through income, prices and
the rate.

Stockholms län 2024, baseline C = 35.86 % of income. Push the rate up 2 pp and change
nothing else:

```
cost per krona   5.01 -> 6.41 % of the loan
C                35.86 -> 45.88          a rise of 28.0 %
```

Add a 5 % pay rise on top and the rise is 21.9 %; a 10 % price fall instead brings it to
15.2 %. **The rate matters, but it no longer dwarfs everything else.** Under the old
real-rate formula the same +2 pp cut the value by 72 %, because it divided by a real rate
of 0.77; a 5 % pay rise then recovered 1.4 points of the 72 point fall.

The simulator validates its inputs (positive income, price and rate, finite values,
relative shocks above −100 %), and its baseline is tested equal to `compute_version_c` on
every county-year, so Sida 05 starts from the number the other pages show. What the page
*says* about a result lives in `src/ui/interpret.py`: the direction of the change in cost,
where the 2021–23 preset's numbers come from, the fixation limit whenever the rate moves,
and a note when the rate is held at its 0,5 % minimum.

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
Genomsnittligt SHAI        16,3 % of income   (−3,3 % against 2023)
Högrisk kommuner           84 of 290
K/T-kvot, genomsnitt       1,40
Worst three by z_c         Lidingö, Danderyd, Solna
Best three by z_c          Åsele, Sorsele, Ragunda
```

The −3,3 % splits into −3,2 % from the cost per krona (the rate eased) and −0,1 % from
prices against incomes; the collapsed panel on the page shows the split for any year.

### Sida 02, Länsjämförelse

**Reads:** `affordability_municipal.parquet`, then averages kommuner into their län
with `groupby("lan_code").mean()`, plus `affordability_ranked.parquet` for the
agreement panel. **Engine path:** stages 3 and 4, aggregated.

Two tabs, Kassaflödesversion and Makroversion. One tab per formula that can rank
differently, which is two of the three. Each county carries its own colour keyed by
county code, so it survives a filter change or a tab switch. Deselected counties
stay on as faint grey context. The y axis is logarithmic for Kassaflödesversion, because
county levels span a factor of ten (3 to 36 % of income) and a linear axis squashes
the cheap counties flat.

**Expect two different numbers for the same county.** This page averages kommuner.
Sida 05 reads `affordability_county.parquet`, which computes the index from county
level income and price. A mean of ratios is not the ratio of means:

| Län, 2024 | Sida 02, mean of kommuner | Sida 05, county aggregate |
|---|---|---|
| Stockholms län | 35,19 | 35,86 |
| Västerbottens län | 8,35 | 16,40 |
| Gotlands län | 25,99 | 25,99 |

Neither is wrong; they answer different questions. Gotland agrees exactly because it
is one municipality. Sparse northern counties diverge most, because many very cheap
inland kommuner pull an unweighted mean of cost shares down, while the county aggregate
is weighted towards Umeå's prices.

**Example, the Robusthet panel at the foot, 2024:**

```
Kassaflödesversion (C)    hög 84   medel 136   låg 70
Makroversion (B)          hög 57   medel 159   låg 74     genuinely different
```

Two rows, not three. Bankversion (A) had one until 2026-10-02 and it read `hög 84
medel 136 låg 70` — C's own counts, since `risk_a` equals `risk_c` on every row.
A table whose purpose is to show that the ranking survives a change of formula
cannot carry a row that agrees by construction. What A does say is stated above
instead, as one derived figure in the comparison expander.

B disagrees with C for **73 of 290 kommuner**. The sharpest case is Perstorp: medel
under C, hög under B, a gap of 150 rank places. B weighs in unemployment, which C
ignores entirely.

### Sida 03, Kommunanalys

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
SHAI (Version C)     44,2 % of income
Medianinkomst        413 600 SEK
K/T-kvot             1,23
Bolåneränta          4,30 %
```

with the county projection from section 6 beneath it.

### Sida 04, Kontantinsats

**Reads:** `affordability_municipal` and `panel_county`, for price, income and the
policy rate only. **Engine path:** stage 2 inputs, then the live engine. Nothing
here touches the A, B, C index. It models a **floating** loan (policy rate plus the
margin SCB observed that year) and says so; the index uses the all-fixation mean.

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

A county dropdown, three sliders (mortgage rate shock in pp, income and price shocks
in percent), a KPI row of baseline against scenario, a surface over rate and price,
and a comparison table.

**Example:** the plus 2 pp walkthrough in section 7.

### Sida 06, Metodologi

**Reads:** provenance only, for counts. **Computes:** nothing.

Eight numbered sections: theory, the ten variables and their sources, the three
formulas with their LaTeX, normalisation and risk classes, the projection, the
regime history, the limitations register F1 to F18, validation, and references.

This is where A, B and C are formally defined, which is why the tab strip on Sida 02
does not need to carry the letters.

**Example:** open section 7 and read F13. The mortgage rate and inflation are
national, so 45 % of Version B's weight carries no information distinguishing one
kommun from another within a single year. Within year municipal rankings are driven
almost entirely by price over income at 35 % and unemployment at 20 %.

---

## 9. What the tests pin

These are the invariants. Break one and a test fails rather than a reader.

| Invariant | Guarded by |
|---|---|
| `z_a` equals `z_c` on every row | `tests/test_formula_agreement.py` |
| rank 1 = best, higher = worse for every version, stated in prose | `tests/test_ranked_artifact.py`, `tests/test_labels.py` |
| The cash-flow model's constants and arithmetic | `tests/test_cost_model.py` |
| The mean index factors into cost per krona and price/income; METHODOLOGY §3's table is the derived one | `tests/test_cost_history.py` |
| Every page renders for every offered year, 67 renders | `tests/test_pages_render.py` |
| Figures quoted in copy match the artifacts | `tests/test_copy_matches_artifacts.py` |
| No Swedish copy inline in a page | `tests/test_no_inline_copy.py` |
| Runtime and pipeline dependency sets never merge | `tests/test_packaging.py` |
| The withdrawn vocabulary never returns to the live surface | `tests/test_withdrawn_vocabulary.py` |
| Projected first year within 0.25x to 4x of the last observed | `tests/test_projection.py` |
| Each Kontantinsats regime matches its rules; no cost is negative; every selectable row at every control extreme is finite | `tests/test_kontantinsats_engine.py` |
| The simulator's baseline equals `compute_version_c`; equal rate steps move the cost equally; the minimum rate is named | `tests/test_scenario_engine.py` |
| Sida 05 calls a rise in cost a rise, names the fixation limit, ties the 2021–23 preset to the panel | `tests/test_scenario_interpretation.py` |

`python scripts/audit.py` checks the committed artifacts separately from the suite,
currently 27 checks.

---

## 10. What to touch when you change something

| To change | Edit | Then |
|---|---|---|
| A formula | `src/indices/affordability.py`, or an assumption in `src/indices/cost_model.py` | re-run the refresh, commit new parquet, update `docs/METHODOLOGY.md` |
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
