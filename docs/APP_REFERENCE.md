# SHAI reference: app guide, open risks and map

Three documents merged into one, unchanged in substance:

- **Part I — App guide.** What each page is for and how to read its results.
- **Part II — Open risks.** Known risks carried deliberately, and pending decisions.
- **Part III — Choropleth map.** Map implementation reference.

Section numbers (§1–§12) refer to Part I; risk IDs (R1–R16) to Part II.


---

# Part I — App guide: what each page is for, and how to read what it gives back

One section per page, in the order the navigation lists them, then the method
and decisions that sit underneath all of them.

Each page section answers the same five questions: **what it is**, **why it
exists** when the other pages already exist, **how it works**, **when it is the
right tool**, and **what its numbers actually say** — including where they are
easy to misread, which is the part a dashboard usually leaves out.

Written against the committed artifacts, with every figure re-derived from them
rather than quoted from memory. Sections 4 and 5 were written 2026-09-18 for
Kontantinsats and Scenariosimulator; section 9 on the two charts added
2026-09-21; sections 1 to 3 added 2026-09-23, extending the same treatment to
the three pages a visitor meets first.

| | Page | Section |
|---|---|---|
| Sida 01 | Riksöversikt | 1 |
| Sida 02 | Län jämförelse | 2 |
| Sida 03 | Kommun djupanalys | 3 |
| Sida 04 | Kontantinsats analys | 4 |
| Sida 05 | Scenariosimulator | 5 |
| Sida 06 | Metodologi och källor | documented by `docs/METHODOLOGY.md`, which is its source |


**Where the numbers come from.** Pages 01 to 03 display what the refresh pipeline
already computed and committed; pages 04 and 05 take raw panel inputs and compute
something new on every click. `docs/ENGINE.md` walks the whole chain, from the three
source APIs through the formulas and the normalisation to the screen, with the
arithmetic worked out on one kommun so it can be checked by hand.
Sections 6 to 11 are not about a single page: the three formula versions, what
can and cannot be refreshed, the interpretation system both tool pages share, the
two charts, and the record of recommended work.

---

## 1. Riksöversikt (Sida 01)

### What it is

The whole country in one year: a choropleth of all 290 municipalities, a
four-card KPI strip above it, and a histogram of where those 290 sit relative to
each other.

### Why it exists

It is the only view that requires the reader to have chosen nothing. Every other
page needs a county, a municipality or a scenario before it can say anything.
This one opens with the answer already on screen, which is why it is the front
door and why the things it gets wrong cost the most.

### How it works

**Reads** `affordability_ranked.parquet`, filtered to the selected year. That is
stage 4 of the pipeline, so the colours and the ranks are read from the file and
never recalculated in the browser. The full chain is in `docs/ENGINE.md`.

The map does not colour the raw index. Version C is log-transformed, z-scored
**within the selected year**, and cut at ±0.67σ into three classes (decisions D5
and D6; `src/indices/normalize.py` owns all three steps). So a colour is a
statement about a municipality's position among its peers *that year*, not about
Sweden's affordability over time.

### When to use it

- Locating one municipality against the national distribution.
- Reading the *shape* of that distribution, which the histogram shows and the map
  cannot.
- Comparing the spread between years, as distinct from the level.

### What the numbers actually say, with real figures

2024, Version C:

| | Value |
|---|---|
| Låg / Medel / Hög risk | 70 / 136 / 84 |
| z range | −2,39 (Åsele, C = 74,9) to +2,62 (Lidingö, C = 4,6) |
| Genomsnittligt SHAI | 23,0, against 36,3 in 2023 |

**The page carries two kinds of number side by side, and only one of them can
trend.** This is the thing most likely to be misread here.

The high-risk *count* cannot move meaningfully. The ±0.67σ cuts are quantiles of
a normal distribution, so a near-fixed share lands in each class every year by
construction. Measured across all eleven years the high-risk share runs **27,6 %
to 29,0 %** — a spread of 1,4 points over a decade that contained a zero-rate era
and a rate shock. Reading "84 municipalities at high risk, up from 83" as
deterioration is reading noise in a definition. That is limitation F16, and the
KPI card labels itself "relativ position" for this reason.

The *average SHAI* can trend, because it is a mean of raw Version C rather than
of z-scores — but it cannot be read straight across years either, and the
2023-to-2024 fall is the case in point. 36,3 to 23,0 is a 36 % drop in which no
municipality's income or price did anything unusual. What changed is the
denominator: 2024 is the first year since 2014 in which the real rate cleared
the 0,5 pp floor, so Version C stopped dividing by a constant and started
dividing by a rate. The page now says so, and carries the table.

<details>
<summary><b>Which rate each formula actually divided by, year by year</b></summary>

Rendered on Sida 01, 02 and 06 by `src/ui/floor_panel.py`, collapsed, from
`agreement.floor_history()`. Rates in percentage points.

| Year | Styrränta | Inflation | Realränta | Golv binder för | C/A | Snitt-SHAI | Inkomst/pris |
|---|---|---|---|---|---|---|---|
| 2014 | 0,46 | −0,17 | 0,63 | inget | 0,74× | 36,3 | 22,9 % |
| 2015 | −0,25 | −0,03 | −0,23 | A och C | 0,20× | 43,1 | 21,5 % |
| 2016 | −0,48 | 0,98 | −1,46 | A och C | 0,20× | 41,9 | 20,9 % |
| 2017 | −0,50 | 1,81 | −2,31 | A och C | 0,20× | 39,1 | 19,6 % |
| 2018 | −0,50 | 1,95 | −2,45 | A och C | 0,20× | 38,1 | 19,1 % |
| 2019 | −0,26 | 1,80 | −2,06 | A och C | 0,20× | 37,6 | 18,8 % |
| 2020 | 0,00 | 0,49 | −0,49 | A och C | 0,20× | 36,5 | 18,2 % |
| 2021 | 0,00 | 2,17 | −2,17 | A och C | 0,20× | 32,4 | 16,2 % |
| 2022 | 0,77 | 8,35 | −7,58 | C | 1,54× | 32,0 | 16,0 % |
| 2023 | 3,46 | 8,65 | −5,19 | C | 6,93× | 36,3 | 18,1 % |
| 2024 | 3,63 | 2,86 | 0,77 | inget | 4,71× | 23,0 | 17,7 % |

Read the Snitt-SHAI column against the Golv column, not on its own. The three
years where the floor state changes — 2014→2015, 2021→2022, 2023→2024 — are the
three places the level moves for a reason that is not affordability.

**Inkomst/pris is the column that answers the question.** It is the mean index
with the rate divided out, which works exactly because the rate is national:
`mean C = (100/r) · mean(I/P)`. It contains no floor and compares across every
year — 22,9 % in 2014 to 17,7 % in 2024, so a median income went from buying
22,9 % of a house to 17,7 %. The panel also shows the split for the year on
screen against the one before it: 2023 to 2024 is −36,5 % in total, of which the
rate is −35,1 % and income against price −2,2 %, multiplied rather than added.
See `src/indices/decompose.py` and METHODOLOGY §3.

</details>

Both numbers sit in the same KPI strip. The card labels and the explanation line
beneath now distinguish them; before T1.9 the count carried a year-on-year delta,
which asserted a trend it cannot have.

---

## 2. Län jämförelse (Sida 02)

### What it is

21 counties as a trend chart with a ranking table beneath it, one tab per
formula that can rank differently — which is two of the three, not three.

### Why it exists

To answer an objection that any single-formula indicator invites: *is this
ranking just an artefact of the formula you happened to choose?* Sida 01 shows
one ranking with great confidence. This page exists to test it.

### How it works

**Reads** `affordability_municipal.parquet`, averaged into län with
`groupby("lan_code").mean()`, plus `affordability_ranked.parquet` for the
agreement panel. Stages 3 and 4, aggregated. See `docs/ENGINE.md`.

Municipal scores are averaged into counties — `municipal.groupby("lan_code")`
— and ranked within the selected year. Versions A and C are plotted on a
logarithmic axis, which is the same treatment decision D6 applies to them for
z-scoring and for the same reason: they are ratios with the policy rate in the
denominator, so when the rate approached zero they ran to 400+ and squashed
recent years flat against a linear axis.

Each county carries its own colour from `COUNTY_PALETTE` and its own legend
entry, and a selector cuts the 21 lines down to a chosen few; the rest stay on
as faint context so the spread is never lost. Before 2026-09-30 every county was
drawn in one muted tone with the legend off, which showed the shape of the
spread while making each line anonymous.

**Version A has no tab, deliberately.** Measured on this page's own county
figures, A and C produce the identical ordering in every year — rank correlation
1,0000 — and C reads exactly 4,71x A in 2024 for all 21 counties. A third tab
would show the same ranking with different numbers, which is the appearance of
corroboration rather than corroboration. A's formula and description moved into
the comparison expander, where that reason is stated.

The page also carries the rate-floor panel between the comparison expander and
Robusthet, collapsed, for the same reason Sida 01 does: the county trend chart
plots levels across years, and those levels move when the floor releases. The
"Om länsjämförelsen" text used to say the curves could be compared between years
because they are level values. They can, between years where the floor bound the
same way, which is what the copy now says.

**It no longer has a row in the Robusthet class table either, as of
2026-10-02.** That row was `risk_c`'s counts under another name, in the one table
on the site whose job is to show that the ranking survives a change of formula.
What replaced it is the thing only A can say: the size of the inflation
adjustment, derived from the selected year rather than quoted. The factor is
4,71 in 2024 and 0,20 in every year from 2015 to 2021, where both formulas are
dividing by their rate floors and it means nothing about inflation at all — so
the sentence around the figure changes with the year. See
`explain_inflation_adjustment` in `src/ui/interpret.py`, and METHODOLOGY
section 3 for the per-year table.

### When to use it

- Checking whether a county's standing survives a change of formula.
- Reading a county's trajectory over the full period rather than one year.
- Understanding what A, B and C each measure before trusting any of them.

### What the numbers actually say, with real figures

**Two of the three formulas cannot disagree.** Version A and Version C rank
identically, in every year, by construction: within a year the rate and inflation
are national constants, so A and C differ by a single constant factor that a
within-year z-score on logs removes exactly. `z_a` equals `z_c` on all 3 190
rows. Version B is the only one that can rank differently, and it does — for 73
of 290 municipalities in 2024.

So the honest form of this page's argument is not "three methods agree". It is
"the one method that *could* rank differently does so for a quarter of the
country, and here is where". The Robusthet section at the foot of the page states
that and shows the class counts for C and B.

Where A and C genuinely differ is in **level**: C reads 4,71 times A at 2024's
real rate. That is the inflation correction, and it is why C is the one the site
reports. In 2015 to 2023 the same quotient is an artefact of the two rate
floors rather than a correction for anything, which is why the page derives it
per year and labels what it is.

**A divergence this page does not announce.** The county figures here are means
of municipalities. The county figures on Sida 05 come from
`affordability_county.parquet`, which computes Version C from county-level income
and price rather than averaging municipal ratios. A mean of ratios is not the
ratio of means, so the two disagree:

| Län, 2024 | Sida 02 (mean of kommuner) | Sida 05 (county aggregate) |
|---|---|---|
| Västerbottens län | 44,62 | 16,85 |
| Norrbottens län | 37,73 | 22,62 |
| Stockholms län | 8,45 | 7,71 |
| Gotlands län | 10,63 | 10,63 |

The ratio between them runs 1,00 to **2,65**, median 1,42, and the rank
correlation is 0,806 — so the two do not even order the counties the same way.
Sparse northern counties diverge most, because a handful of very cheap
municipalities pull an unweighted mean upward while the aggregate is dominated by
where people actually live. Gotland agrees exactly, being one municipality.

Neither figure is wrong. They answer different questions: "what does the typical
municipality in this county look like" against "what does this county look like".
But the same label, *Stockholms län*, carries two different numbers two pages
apart with nothing saying so. Recorded here rather than silently corrected,
because choosing one is a product decision: population-weighting the Sida 02
mean would close the gap and change every value on the page.

---

## 3. Kommun djupanalys (Sida 03)

### What it is

One municipality at a time: its Version C history, a component KPI row, and a
six-year **conditional projection** under three stated assumptions about the real
interest rate.

### Why it exists

It is the only per-municipality time series in the app, and the only forward-
looking view other than the scenario simulator. Sida 01 says where a municipality
stands now; this says how it got there, and what the index becomes under
assumptions the reader can accept or reject.

### How it works

**Reads** `affordability_municipal.parquet` for the kommun,
`affordability_county.parquet` for its county, and `projection.parquet`. Stages 3
and 5. See `docs/ENGINE.md`.

History is municipal. **The projection is not.** `src/projection.py` carries the
county's last observed income and price forward at 3 % and 2 % a year, then
divides by each of three assumed real rates. SCB publishes nothing that would
support a municipal projection.

Nothing is fitted. Statistical model fitting was evaluated here and withdrawn
rather than repaired; the measurements are recorded as R16 and summarised below.

### When to use it

- Reading one municipality's trajectory rather than its rank.
- Seeing which component moved: the KPI row carries income, K/T and the rate
  beside the index.
- Asking what the index would be *if* the real rate settles at a given level.
  That is the only forward question this page now answers.

### What the numbers actually say, with real figures

**The projection is the county's, and the chart used to hide that.** It once began
at the *municipality's* last value, so Stockholm's line ran at
6,2 and then jumped to the county's 2025 value, which reads as a predicted
improvement and is in fact a seam between two geographies. Stockholm kommun
closed 2024 at 6,2; Stockholms län at 7,7. The chart draws the county history as
a separate series, labelled *Länet*, and anchors the projection to it. Nothing is
stitched across a geography. That remains true of the projection.

**The three scenarios, for Stockholms län (observed 2024 = 7,7):**

| År | Golvet, 0,5 pp | Dagens nivå, 0,77 pp | Normaliserad, 2,0 pp |
|---|---|---|---|
| 2025 | 12,0 | 7,8 | 3,0 |
| 2027 | 12,2 | 7,9 | 3,1 |
| 2030 | 12,6 | 8,2 | 3,1 |

**The first year moves by exactly 1,56× / 1,01× / 0,39× in all 21 counties.**
That uniformity is the point, not a defect: the real rate is national, so the
spread between the lines is a statement about monetary policy and not about any
municipality. A reader who sees the same fan over Norrbotten as over Stockholm
has learned the right thing.

**Why the floor is the whole story.** Version C is a reciprocal of
`max(R − π, 0,5)`. Stockholm's real rate ran 0,63, then 0,50 for nine years, then
0,77 — **at the floor in 9 of 11 years**. While it binds, Version C is *exactly*
200 × (inkomst / pris) and the rate contributes nothing; the identity holds to
four decimal places in the committed artifact. Yet the real rate carries **most**
of the variance in year-on-year changes of `log C`. A variable that is clamped
82 % of the time and still explains most of the movement is what makes an
extrapolated denominator unusable.

**Why nothing is fitted, in one line.** A fitted model's first year was
implausible for all 21 counties, each collapsing to roughly a quarter of its last
observed value before rebounding, and it lost to a naive carry-forward on every
component of the index. Closed by removal rather than by a better model; the full
measurements are in R16.

**What is checked now.** `tests/test_projection.py` asserts the floor identity,
the reciprocal sensitivity, that a rate below the floor is refused, and that no
county's first projected year falls outside 0,25× to 4× of its last observed
value. The earlier guard checked only that confidence bands widened, which they
did, while nothing checked the central path was plausible. There are no bands
now, and the spread between scenarios is **not** a confidence interval.

Beyond that, the honest bound is still eleven annual observations. The difference
is that the page no longer spends them on a fitted model.

---

## 4. Kontantinsats analys (Sida 04)

### What it is

A calculator that answers one question: **what does it actually take to buy this
home, under each of the five mortgage rule sets Sweden has had since 2010?**

It takes a region, a price type, a household type, a savings rate and a bank
margin, and returns four numbers per regime: the cash deposit required, the years
needed to save it, the resulting monthly cost, and the income left over.

### Why it exists

Every other page in SHAI is an index. An index is a comparison, not a decision.
A score of 8.1 tells a reader Stockholm is expensive relative to other kommuner;
it does not tell them what they need in the bank. This page converts the same
inputs into the two numbers a household actually plans around: a lump sum and a
monthly payment.

It is also the only page that makes regulation visible. The other pages treat
the rules as fixed background. Here the rules are the variable, which is what
makes the cost of each policy change legible.

### How it works

**Reads** `affordability_municipal.parquet` and `panel_county.parquet`, for price,
income and the policy rate only. Stage 2 inputs, then `src/kontantinsats/engine.py`
live on every interaction. Nothing on this page touches the A, B, C index. See
`docs/ENGINE.md`.

For each regime, given price `P`, household income `I`, policy rate `R` and bank
margin `m`:

```
required_cash  = P * min_down_pct
loan           = P - required_cash
LTV            = loan / P
LTI            = loan / I
years_to_save  = required_cash / (I * savings_rate)
annual_interest= loan * (R + m)
amort_pct      = highest LTV band met, plus 1pp if LTI > 4.5 (amort_2 only)
monthly_total  = (annual_interest + loan * amort_pct) / 12
residual       = I - (annual_interest + loan * amort_pct)
```

The five regimes and what changed at each step:

| Regime | Period | Min deposit | Amortisation |
|---|---|---|---|
| Före 2010 | to Oct 2010 | none | none |
| Bolånetak | Oct 2010 to Jun 2016 | 15 % | none |
| Amorteringskrav 1.0 | Jun 2016 to Mar 2018 | 15 % | 2 % if LTV > 70 %, 1 % if LTV > 50 % |
| Amorteringskrav 2.0 | Mar 2018 to Mar 2026 | 15 % | as above, plus 1 pp if LTI > 4.5 |
| Lättnad 2026 | Apr 2026 onward | 10 % | as 1.0; the LTI rule is gone |

### When to use it

- Deciding whether a specific kommun is reachable for a specific household.
- Understanding why a deposit got harder or easier after a rule change.
- Comparing a house against an apartment in the same region, which is the single
  most decision-relevant comparison the tool offers.

### What the numbers actually say, with real figures

Stockholm 2024, one income, 10 % savings rate, 1.7 pp bank margin:

| | Lättnad 2026 | Amorteringskrav 2.0 |
|---|---|---|
| Deposit | 859 700 SEK | 1 289 550 SEK |
| Years to save | 16.1 | 24.2 |
| Monthly cost | 47 252 SEK | 50 717 SEK |
| LTI | 14.5x | 13.7x |

Åsele 2024, same assumptions:

| | Lättnad 2026 | Amorteringskrav 2.0 |
|---|---|---|
| Deposit | 51 800 SEK | 77 700 SEK |
| Years to save | 1.4 | 2.1 |
| Monthly cost | 2 847 SEK | 2 689 SEK |

Two things in that table are worth pausing on, because both are easy to
misread and neither is currently explained on the page.

**The 2026 easing is not uniformly good.** In Åsele the monthly cost is *higher*
under Lättnad 2026 (2 847 SEK) than under the stricter 2.0 regime (2 689 SEK).
A smaller deposit means a larger loan, and a larger loan costs more every month.
The easing trades a lower barrier to entry for a higher ongoing cost. The page
shows both numbers but never says they move in opposite directions.

**Stockholm's LTI of 14.5x is the headline finding and the page buries it.** The
2.0 regime's extra amortisation triggered above 4.5x. Stockholm is at three times
that threshold. This says the median Stockholm household cannot buy the median
Stockholm house on one income at all, under any regime. No bank would write that
loan. The page instead presents a tidy "16.1 years to save", which implies the
purchase is merely distant rather than unavailable.

### Optimisation: what to change and how

These are ordered by how much user misunderstanding they remove per unit of work.

**1. Flag when the scenario is not lendable.** `LTI` is already computed and
returned by `apply_regime`, and already shown in the detail table. Nothing
surfaces it as a constraint. Swedish banks generally decline above roughly 5x to
6x LTI regardless of regime.

*Implementation:* in `src/kontantinsats/sections.py`, after `results` is
computed, compare `baseline["lti"]` against a named constant and render a warning
above the KPI strip. Roughly:

```python
LTI_LENDING_CEILING = 5.5   # typical Swedish bank practice, not a legal limit

if baseline["lti"] > LTI_LENDING_CEILING:
    st.warning(L("ki.lti_over_lending_ceiling", v0=f"{baseline['lti']:.1f}"))
```

with the label text stating plainly that at this ratio a bank would normally
decline, and that the savings figures below therefore describe an arithmetic
result rather than an achievable purchase. Copy belongs in `src/ui/labels.py`;
the suite enforces that.

**2. Say which direction each regime moved cost.** The cards already colour
deltas, but a user has to compare five cards to notice the deposit-versus-monthly
trade-off. One sentence under the regime row, derived rather than hardcoded,
stating whether the current regime is cheaper to enter and more expensive to
hold, or the reverse, for *this* region. The data to compute it is already in
`results`.

**3. Default the savings rate to something defensible.** It defaults to 10 %.
Swedish household saving varies widely and 10 % of *gross* income is optimistic
after tax. Either relabel it explicitly as a share of gross income, which it is,
or add a short note that net saving capacity is typically lower. This is a
one-line copy change with a real effect on how the years-to-save number is read.

**4. Make the couple case the default, or at least prominent.** `household_type`
defaults to `Singelhushåll`. Most Swedish home purchases are joint. The single
default produces the alarming numbers above, which are accurate but unrepresentative.
Changing the default is one line; the honest alternative is to show both.

---

## 5. Scenariosimulator (Sida 05)

### What it is

A stress test. It takes one län's actual figures for the selected year and asks
what Version C would be if rates, incomes, prices or inflation moved.

### Why it exists

Every other page is backward looking and stops at 2024, because that is the last
year SCB has published municipal income. This is the only page that can answer a
forward question at all. It is also the only place where the behaviour of the
real interest rate becomes visible, and that behaviour is genuinely
counterintuitive.

### How it works

**Reads** `panel_county.parquet` for the baseline row, then `src/scenario/simulator.py`
live on every slider move. Version C only. See `docs/ENGINE.md`.

```
real_rate  = max(R - pi, 0.5)          # percentage points, floored
Version C  = Income / (Price * real_rate/100)
```

Four sliders shift the inputs: rate shock and CPI shock are added in percentage
points, income and price shocks are applied as relative changes. The floor at
0.5 pp stops the formula dividing by zero or by a negative number when inflation
exceeds the policy rate.

### When to use it

- Testing sensitivity: which input actually moves affordability in this län.
- Understanding a historical episode, which the presets are built for.
- Sanity-checking an intuition about rate rises before acting on it.

### The central lesson, with real figures

Stockholms län 2024. Baseline: R = 3.63 %, inflation = 2.86 %, so the real rate
is 0.77 %. Version C is 10.6.

| Scenario | Real rate | Version C | Change |
|---|---|---|---|
| Rate +4 pp only | 4.77 % | 1.7 | **-83.9 %** |
| Rate +4 pp with CPI +8 pp | 0.50 % | 16.3 | **+54.0 %** |
| Price -15 % only | 0.77 % | 12.5 | +17.6 % |

The same nominal rate rise is catastrophic in one case and beneficial in the
other. The only difference is whether inflation moved with it. This is not a
quirk of the model; it is what actually happened in Sweden in 2022, when nominal
mortgage rates tripled while real rates stayed low.

A user who moves only the rate slider, which is the obvious thing to do, gets
the -83.9 % result and will reasonably conclude that rate rises destroy
affordability. That conclusion is an artefact of holding inflation fixed. The
page documents this as limitation F15 in an expander at the bottom. Almost
nobody will read it before drawing the wrong conclusion.

### Optimisation: what to change and how

**1. Move the F15 caveat to the point of use.** It currently sits in the
"Förklaring" expander below the results. It belongs next to the rate slider,
where the misreading happens.

*Implementation:* in `pages/05_Scenario.py`, when `rate_shock != 0` and
`cpi_shock == 0`, render an inline caption under the slider row:

```python
if rate_shock != 0 and cpi_shock == 0:
    st.caption(L("sc.rate_without_cpi_hint"))
```

with text saying that holding inflation fixed treats the whole nominal move as a
real move, and pointing at the CPI slider. This is the single highest-value
change on the page: it intercepts the specific wrong conclusion at the moment it
would be formed.

**2. Label the presets with what they teach, not just what they are.** The
"Riksbanken 2022" preset produces an *improvement*, which looks like a bug to
anyone who lived through 2022. A one-line result caption explaining that the
real rate fell because inflation outran the policy rate turns a confusing output
into the page's best lesson.

**3. State that the number is not the map's number.** The simulator shows raw
Version C (10.6 for Stockholms län). The Riksöversikt map shows a z-scored,
percentile-ranked transform of the same quantity. They are different scales and
must not be compared. A caption under the KPI row saying so costs one label.

**4. Consider widening the scope beyond one län.** The simulator answers "what
happens to this län". The more useful policy question is "how many kommuner
cross into hög risk under this scenario". That is a larger change, requiring the
shock to be applied across the municipal panel and re-ranked, and it is worth
scoping separately. Recorded here as a direction, not a quick win.

---

## 6. The three SHAI versions: what they mean and whether they matter here

### What each one is

| Version | Formula | Reads as |
|---|---|---|
| **Bankversion (A)** | `I / (P * R)` | Can a household carry this at today's nominal rate? A traditional bank view. |
| **Makroversion (B)** | `0.35*z(P/I) + 0.25*z(R) + 0.20*z(U) + 0.20*z(pi)` | How much macro pressure is this market under, relative to the panel's history? A supervisor's view. |
| **Realversion (C)** | `I / (P * max(R - pi, 0.5))` | Bankversion corrected for inflation, using the real rate. The floor is 0,5 **percentage points**, which `docs/METHODOLOGY.md` writes in decimal as 0.005. |

A and C are ratios where **higher is better**. B is a weighted sum of z-scores
where **higher is worse**. That sign difference is the single most error-prone
thing in the codebase and has produced real defects more than once.

### Why three rather than one

Because they disagree, and the disagreement is informative. A and C diverge
exactly when inflation is far from zero, which is precisely when a nominal
reading misleads. B can carry a time trend that A and C cannot, because its
z-scores are pooled across the whole panel rather than computed within each year.
Its panel mean runs from -0.31 in 2015 to +0.78 in 2023, tracking the rate cycle,
now measured against a frozen reference so the figures stop moving on a refresh
(R1).
A and C, normalised within year, are silent about whether Sweden as a whole got
better or worse.

### Are they important in our context? An honest answer

**Version C is the product. A and B are close to vestigial.**

Verified against the code:

- `version_c` is consumed by the choropleth map, the risk classification, the
  KPI row, the projection, the data tables and the scenario simulator.
- `version_a` is read in one page, `pages/02_Lan_jamforelse.py`: the county means feeding
  the comparison expander, and the A-to-C factor that expander states. It is also named in
  `src/lan/charts.py`'s `LOG_SCALED`, which is a property of the formula rather than of the
  current tabs. **It has no tab of its own, and since 2026-10-02 no Robusthet row**
  — see section 2.
- `version_b` likewise appears only in that comparison and in the methodology
  page that documents it.
- The ranked artifact computes and stores `z_a, rank_a, risk_a, z_b, rank_b,
  risk_b`. **No UI code reads any of them.** Only the `_c` family is used.

So six of the nine scoring columns are computed on every refresh, committed to
the artifact, and never displayed.

That is not automatically waste. There is a defensible reason to keep them: a
single-formula indicator invites the question "why this formula", and the ability
to show that the ranking is broadly robust across three different economic
framings is a real credibility argument. The Län jämförelse page exists to make
exactly that argument.

But the current arrangement is the expensive version of that argument. Three
recommendations, in order of confidence:

1. **Keep A and B, and say what they are for.** The comparison page should state
   plainly that C drives every other page and that A and B exist to show the
   ranking is not an artefact of one formula. Right now a user cannot tell which
   number is load-bearing. This is a copy change.
2. **Either display the A and B risk classes or stop computing them.** Six
   unused columns in a committed artifact will eventually drift or confuse.
   Displaying them on the comparison page is the better fix; dropping them is the
   cheaper one. Do not leave them as they are indefinitely.
3. **Never present B on the same axis as A and C** without restating its
   direction. Higher B is worse. Everything else on the site is the other way
   round.

### Correction, 2026-09-21: A and C are not two framings. They are one.

Reading the six unused columns before displaying them, per recommendation 2,
overturned part of the paragraph above.

**`z_a`, `rank_a` and `risk_a` are exact duplicates of the `_c` family in every
one of the 3 190 rows**, to 2·10⁻¹⁵. Not approximately, and not as a property of
this particular panel:

    A = I / (P · R)
    C = I / (P · max(R − π, 0.5))

`R` and `π` are national, so within a year A and C differ by one constant factor
across all 290 municipalities. Z-scores are taken within year on `ln(value)`,
where a constant factor is an additive shift the z-score removes exactly.

The consequence for the credibility argument is real. "Three economic framings
broadly agree" was, for two of the three, an arithmetic identity rather than
corroboration, and displaying A beside C would have presented it as evidence.
**Version B is the only formula that can disagree**, and it does: on 73 of 290
municipalities in 2024, and on 133 in 2015.

Where A and C genuinely differ is in *level*. At 2024's real rate C reads 4,71
times A, which is what makes C the one the site reports; a reader asking how bad
things are needs the level, while a map only needs the order. That multiple is
not a constant of the site, though: it is the quotient of the two rate floors
(0,20) in 2015 to 2021 and the nominal rate over C's floor in 2022 to 2023, so
Sida 02 derives it per year and names what it is. METHODOLOGY section 3 has the
table.

So the answer to recommendation 2 is neither of the two offered. The A columns
are kept and **asserted** rather than displayed: `tests/test_formula_agreement.py`
pins the identity and both floors, so if the transform, the normalisation window
or either floor ever changes, a test fails and the copy explaining it gets
revisited. Sida 02 shows the class counts for C and B, states that level
difference as one derived figure, and says plainly why A has neither a tab nor a
row.

---

## 7. Can the variables be changed or updated?

Two different questions live here.

### Investigated: can income be sourced to move the index past 2024?

Three candidates were checked live against the SCB API on 2026-09-18. The short
answer is that the index can move to 2025, but not with the table that looks like
the obvious choice, and not without an explicit decision about definitions.

#### Candidate 1: AM0106 `Kommun17g`, the table in the brief. Rejected.

"Genomsnittlig månadslön inom kommuner efter kommun och kön, 2007 to 2025",
published 2026-05-19. The year range is right and the release is recent, so it
looks ideal. It is not, and the reason is in the phrase "inom kommuner".

`Kommun17g` measures **the municipal sector as an employer**, not residents of a
municipality. Verified from the table's own figures:

| | Value | What it implies |
|---|---|---|
| Employees, Riket 2024 | 854 100 | Sweden's workforce is roughly 5.2 million. This is the municipal payroll, about 16 % |
| Employees, Stockholm 2024 | 45 300 | Stockholm has well over 400 000 employed residents. This is the headcount of Stockholm kommun as an employer |
| Region list | includes `Kommunalförbund` | A municipal federation is an employer, not a place |

So "Stockholm" in this table means people employed *by* Stockholm kommun
regardless of where they live: teachers, nurses, care staff, administrators. It
is a public-sector payroll series, heavily weighted to one set of occupations and
roughly 80 % women. It also reports gross monthly salary rather than annual
income.

Substituting it for a residence-based income measure would not extend the index.
It would silently replace the denominator with a different population and make
every ratio uninterpretable. **Do not use it for this.**

#### Candidate 2: HE0110M `MistTab1`. Viable, with one real obstacle.

Found while checking the first. "Individuell disponibel inkomst exkl.
kapitalinkomst efter region, kön och ålder", preliminary monthly statistics.

| Property | Value |
|---|---|
| Regions | **312**, the same granularity the panel uses |
| Statistic | Median is published, not only the mean |
| Coverage | **2025M01 to 2026M03**, monthly |
| Status | Preliminary |

This is genuinely current and at the right geography. A full calendar-year 2025
figure is computable today, because all twelve months of 2025 are present.

The obstacle is definitional, and it is not small. The panel's `median_income`
currently comes from `HE0110G/TabVX4bDispInkN`, which is **household** disposable
income. `MistTab1` is **individual** disposable income **excluding capital
income**. Different unit of analysis and different income concept. For Stockholm
the gap is about a third: roughly 335 kSEK annualised individual against 534 kSEK
household for 2024.

Worse, **the two series do not overlap**. `MistTab1` begins 2025M01;
`TabVX4bDispInkN` ends 2024. There is no year in which both exist, so the ratio
between them cannot be calibrated from data. Splicing would mean assuming a
conversion factor, which is the same class of unverifiable assumption the project
removed when it stopped forward-filling income at 3 %/yr.

**Recommendation:** do not splice it into the index. Use it, if at all, as a
clearly separated preliminary nowcast, labelled as a different series with its
own definition, shown beside the index rather than inside it. That keeps the
2014 to 2024 series internally consistent while giving a current reading.

#### Candidate 3: HE0110A `SamForvInk1`. Correct definition, still 2024.

"Sammanräknad förvärvsinkomst", 312 regions, median published, **1999 to 2024**.
This is the series the methodology documents, it has deep history and the right
geography, and it is still capped at 2024. It confirms that SCB has simply not
published 2025 income on the annual tables yet.

#### Direct answer: can the pipeline be repointed at `Kommun17g`?

Technically yes, in about ten lines of `src/data/scb_client.py`. It should not be.
The table would fetch cleanly, the panel would rebuild, the tests would pass and
every number on the site would become unreliable, because the denominator would
have quietly changed from "income of people who live here" to "salary of people
employed by this local council". Nothing in the suite checks the *meaning* of a
column, only its shape and orientation, so this is exactly the class of defect
that would survive a green test run. That is the reason for the recommendation
against, not the ten lines.

#### A definition mismatch, and a bug underneath it

`docs/METHODOLOGY.md` and the Metodologi page describe `median_income` as
*sammanräknad förvärvsinkomst* (SCB HE0110). The pipeline actually requests
`HE0110G/TabVX4bDispInkN` with `Hushallstyp = E90`, whose title is *Disponibel
inkomst för hushåll*, samtliga hushåll. Those are different measures on two axes
at once: household rather than individual, and disposable rather than gross.

Confirmed against the source, 2024 medians:

| Kommun | Panel value (household disposable) | SamForvInk1 (individual gross) |
|---|---|---|
| Stockholm | 533 800 | 413 600 |
| Malmö | 433 000 | 336 500 |
| Åsele | 368 000 | 298 900 |

The panel runs roughly 29 % above individual gross income, which is what a
household measure should do. The documented definition is the wrong one.

**The consequence is a live bug, not only a docs defect.**
`pages/04_Kontantinsats.py:255` computes `income = _individual_income *
household_multiplier`, where the multiplier is 2 for "Par (2 inkomster)". If
`median_income` were individual, that would be correct. It is a household median
already blending single- and dual-earner households, so selecting Par multiplies
a household figure by two and produces an income no real household has:

| Stockholm 2024, loan 7 737 300 kr | Income used | LTI |
|---|---|---|
| Singel, as shipped | 533 800 | 14.5 |
| Par, as shipped | 1 067 600 | 7.2 |
| Par, if income were truly individual | 827 200 | 9.4 |

The Par case is understating the debt ratio by roughly a quarter. The page
caption compounds it by stating "Inkomsten är individuell bruttoinkomst (SCB
HE0110)", which is false on both axes.

Three ways out were available, and the choice was a product decision rather
than a technical one:

1. **Switch the source to `HE0110A/SamForvInk1`**, the series everything already
   claims to use. 290 kommuner, history to 1999, and it makes the couple
   multiplier valid.
2. **Keep the household series and correct the surroundings**: fix the docs and
   the caption, and drop the multiplier, since a household median already
   includes both earners. Cost: the Par control loses its meaning.
3. Leave it and document it.

**Option 1 was taken on 2026-09-21.** `docs/ADR/0001-income-series.md` records
the reasoning, the rejected candidates and the measured cost. Neither 1 nor 2
moves the index past 2024: this was a correctness question, not a freshness one.

One estimate in this section was wrong and is worth correcting rather than
quietly fixing, because the error is instructive. The text above says the panel
runs "roughly 29 % above individual gross", inferred from three municipalities.
Measured across all 3 190 rows the ratio runs **1.10 to 1.77**, median 1.31 in
2024, and it carries a time trend from 1.74 in 2011 as individual earnings grew
about 51 % against household disposable income's 15 %. The three municipalities
sampled all sat at one end of that spread. A three-point sample of a quantity
with real cross-sectional variance is an anecdote, and it under-estimated the
re-ranking cost of the switch by a wide margin: 5.0 % of rows changed risk class
and a quarter moved more than ten rank places.

### Can the data be refreshed to a newer year?

Partly, and the limit is not technical.

| Variable | Coverage | Moves on a refresh? |
|---|---|---|
| `median_income` | 2011 to 2024 | **No.** SCB has not published 2025. |
| `transaction_price_sek` | 2011 to 2025 | Yes, already at 2025 |
| `unemployment_rate` | 2011 to 2025 | Yes, already at 2025 |
| `price_index`, `kt_ratio`, `completions` | 2011 to 2025 | Yes |
| `policy_rate`, `cpi_yoy_pct`, `cpi_index` | 2011 to 2026 | Yes, near current |
| `population` | 2011 to 2024 | No |

The composite index requires five inputs together: `median_income`,
`transaction_price_sek`, `policy_rate`, `unemployment_rate`, `cpi_yoy_pct`. It
can only be computed for a year where all five exist. Income is the binding
constraint, so **the index ends at 2024 and will stay there until SCB publishes
2025 income**, regardless of how fresh everything else becomes. The panel
already extends to 2026 for the fast-moving series, and the provenance artifact
records both boundaries separately so the UI never offers a year it cannot
compute.

### Can the model variables be changed?

Yes, and the places to change them are deliberately centralised:

| What | Where | Note |
|---|---|---|
| Version B weights (0.35 / 0.25 / 0.20 / 0.20) | `src/indices/affordability.py` | Changing these changes every B ranking; no test pins the values themselves |
| Real rate floor | `src/indices/affordability.py` and `src/scenario/simulator.py` | Same floor, **different units**: `0.005` as a decimal in the index, `0.5` as percentage points in the simulator. Change both, and convert |
| Risk class cuts (+/-0.67 sigma) | `src/indices/normalize.py` | Fixed quantiles, so class shares are near constant by construction |
| Regime deposit and amortisation rules | `src/kontantinsats/engine.py` | The `REGIMES` dict; add a regime by adding an entry |
| Imputed income growth (3 %/yr) | `src/data/panel_income.py` | Only affects years beyond the index ceiling |
| Bank margin default (1.7 pp) | Sida 04 slider | User-adjustable at runtime |

Three cautions that are easy to learn the hard way:

- **The orientation contract is load-bearing.** Rank 1 = best, higher z = worse,
  and A and C are sign-inverted before classification because their raw values
  run the other way. Changing a formula's direction without changing the
  inversion silently flips the map. This has happened.
- **The real rate floor must move in both files together.** They implement the
  same formula independently.
- **Anything touching a formula, a normalisation rule or a regime needs a test.**
  The suite already guards the orientation contract and re-derives every quoted
  number from the artifacts.

---

## 8. The result interpretation system (implemented)

Both pages now carry a panel that reads the user's own numbers and says what they
mean. It lives in `src/ui/interpret.py`; all copy is in `SWEDISH_LABELS` and
every figure it quotes is interpolated from the computed result, never written
into the sentence.

### How it is built

`interpret_kontantinsats()` and `interpret_scenario()` return a list of
`Finding(level, text)`. Levels are `critical`, `warning`, `good` and `note`, and
drive presentation only. `render_findings()` draws them, most serious first.
Returning findings rather than rendering them means the rules can be asserted in
a test with no Streamlit runtime.

Each threshold names its own authority, because they are not equally binding:

| Threshold | Value | Status |
|---|---|---|
| `LTI_LENDING_CEILING` | 5.5x | Typical Swedish bank practice. **Not** regulation, and labelled as such in the copy |
| `LTI_FI_THRESHOLD` | 4.5x | Finansinspektionen's skärpt amorteringskrav trigger, in force Mar 2018 to Mar 2026 |
| `HOUSING_COST_SHARE_GUIDELINE` | 30 % | Conventional budgeting guidance, not a rule |
| Savings bands | 5 and 10 years | Matches the existing Tillgänglighet KPI, so the two cannot disagree |

### What it says on Kontantinsats

In order: whether the loan is lendable at all, whether the monthly cost is
carryable, how long the deposit takes and under what assumption, which direction
the 2026 easing moved cost *for this region*, and whether the single-income
default is doing the damage.

Stockholm 2024, one income, produces:

> 🔴 **Lånet är sannolikt inte beviljningsbart.** Skuldkvoten blir 14,5 gånger
> hushållets årsinkomst. Svenska banker beviljar sällan bolån över omkring 5,5
> gånger inkomsten, oavsett vilket regelverk som gäller. Siffrorna nedan beskriver
> alltså en uträkning, inte ett köp som går att genomföra på den här inkomsten.
>
> 🔴 **Boendekostnaden överstiger inkomsten.** Den tar 106 % av månadsinkomsten.
>
> 🟠 Att spara ihop kontantinsatsen tar 16,1 år vid 10 % sparkvot. Sparkvoten
> räknas på bruttoinkomsten, så det som faktiskt kan sparas efter skatt är
> normalt lägre och tiden därmed längre.

That first line is the finding this document opened with, now stated on the page
instead of buried in a detail table. It also closes recommendation 1.

### What it says on Scenariosimulator

Direction in words rather than a signed number, then the real rate as the
mechanism, then a warning if the rate was moved without inflation, then the scale
note. A +2 pp rate shock with inflation left alone produces:

> 🟠 Scenariot **försämrar** överkomligheten med 72,2 %, från 25,6 till 7,1.
>
> • Drivkraften är realräntan, som går från 0,77 % till 2,77 %.
>
> 🟠 **Obs:** du har ändrat räntan med 2,00 procentenheter men lämnat inflationen
> oförändrad. Hela ränteändringen räknas då som en real förändring. Prova
> KPI-chock för ett mer realistiskt scenario.

The warning fires exactly on the interaction that produces the wrong conclusion,
at the moment it is produced. That closes recommendation 2.

### Deliberate design choices

- **Severity ordering, not chronology.** The lendability finding outranks the
  savings horizon because it determines whether the horizon means anything.
- **Every rule of thumb is labelled.** The 5.5x ceiling says "banker beviljar
  sällan", not "får inte". Presenting bank practice as law would be its own defect.
- **The gross-income caveat travels with the savings figure.** The slider is a
  share of gross income, which reads as more saveable than it is. That closes
  recommendation 6 without a relabel.

### How it behaves across the input space

Exercised over a matrix rather than one example: six kommuner spanning the whole
price range, both household types, three savings rates, and ten scenario
combinations. Checked against invariants, not eyeballed.

Kontantinsats, at a 5 % savings rate:

| Kommun | Household | LTI | Cost share | Severity sequence |
|---|---|---|---|---|
| Stockholm | singel | 14.5 | 106 % | critical, critical, warning, good, note |
| Stockholm | par | 7.2 | 53 % | critical, warning, warning, good |
| Göteborg | singel | 13.3 | 98 % | critical, warning, warning, good, note |
| Norrköping | singel | 7.8 | 57 % | critical, warning, warning, good, note |
| Norrköping | par | 3.9 | 28 % | good, good, note, note |
| Åsele | singel | 1.3 | 9 % | good, good, note, note, note |

The gradient behaves: the panel escalates with price and de-escalates with a
second income, and Åsele never trips a warning at any savings rate. Note that
the Par rows inherit the multiplier bug described in section 7, so their LTI is
optimistic.

Scenario, Stockholms län 2024:

| Scenario | Result | Real rate | Rate-without-CPI warning | Floor note |
|---|---|---|---|---|
| nothing moved | no change | 0.77 | no | no |
| rate +4 only | -83.9 % | 4.77 | **yes** | no |
| rate +4, CPI +8 | +54.0 % | 0.50 | no | yes |
| rate -2 only | +54.0 % | 0.50 | **yes** | yes |
| price -25 % | +33.3 % | 0.77 | no | no |
| income -10 % | -10.0 % | 0.77 | no | no |
| CPI +10 only | +54.0 % | 0.50 | no | yes |
| all four at once | -94.9 % | 10.77 | no | no |

Invariants asserted and holding: the warning fires whenever the rate moved
without CPI and never when it did not; direction wording never contradicts the
sign of the change; a critical finding always appears when the cost share reaches
100 %; the single-income note never appears for a couple.

**The matrix found one real defect.** A rate *cut* with inflation unchanged fired
the warning correctly, but the copy read "en räntehöjning följs ofta av högre
inflation", which is wrong for a cut. The text is now direction-neutral: "räntan
och inflationen rör sig ofta åt samma håll". A single worked example would not
have caught this, because the obvious example is a rate rise.

## 9. The two charts, checked against the design system and the data

Commit `60e150d` shipped two visualisations out of the recommendations above: a
reachability chart on Sida 04 and a rate/inflation surface on Sida 05. This
section holds them to the same rule as the rest of this document. Every figure
below is re-derived from the committed artifacts, and every claim about the app's
visual language is checked against `docs/DESIGN_SYSTEM.md` and the code it
describes.

The two did not come out the same way. One fits. One was off-system, and part of
what it told a reader was wrong. What follows is what the review found, kept in
the present tense of the review; 6.4 and 6.5 record what was done about it, which
is all of it.

### 9.1 Reachability, Sida 04. Fits.

`affordability_gap_chart` inverts the loan arithmetic to the largest price the
income supports at the lending ceiling, and puts the asked price beside it:

```
max_price = income * LTI_LENDING_CEILING / (1 - min_down_pct)
```

It sits inside the app's existing grammar: horizontal bars, the `low_risk`,
`high_risk` and `secondary` tokens, the shared `get_chart_layout`, and a
`card_header` inside a bordered container, which is how every other card on the
site is built. It answers a question nothing else on the page answers, in kronor
rather than in an index, so it complements the interpretation panel underneath
instead of repeating it: the panel gives the debt ratio, the chart gives the
shortfall in money.

Two things to tidy, neither structural:

- The deposit share is read from `REGIMES["latt_2026"]` inside the chart, while
  the page sets its baseline separately at `pages/04_Kontantinsats.py:265`. The
  two agree today. They are two statements of one fact, so changing the baseline
  regime would move the page and leave the chart behind. Pass the baseline
  regime in rather than naming it twice.
- The ceiling is a loan-to-income test and nothing else. It assumes the deposit
  is already in hand, which is the very thing the rest of the page exists to
  question. One clause in `ki.gap_forklaring_v0` closes that gap.

### 9.2 The rate and inflation surface, Sida 05. Four defects.

The intent is right: the page's lesson is that only `R - pi` reaches the formula,
a slider can only ever show one point on that plane, and a plane shows the whole
thing. The execution does not deliver it.

**Defect 1. The caption names the wrong corner, and a user can see it.**
`sc.yta_forklaring` says the flat field is *"uppe till höger"*. The floor binds
when `s_rate - s_cpi` falls to 0.5 pp or below, which is **low** rate shock with
**high** CPI shock. On this chart, with rate ascending up the y-axis and CPI
ascending to the right, that is the **lower right**. Version C over the plotted
grid, Stockholms län 2024, from `panel_county.parquet` (income 551 500 SEK,
price 6 748 000 SEK, R 3.63 %, pi 2.86 %):

| rate \ CPI | -4 | -2 | 0 | +2 | +4 | +6 | +8 | +10 |
|---|---|---|---|---|---|---|---|---|
| **+5** | 0.8 | 1.1 | 1.4 | 2.2 | 4.6 | 16.3 | 16.3 | 16.3 |
| **+4** | 0.9 | 1.2 | 1.7 | 3.0 | 10.6 | 16.3 | 16.3 | 16.3 |
| **+3** | 1.1 | 1.4 | 2.2 | 4.6 | 16.3 | 16.3 | 16.3 | 16.3 |
| **+2** | 1.2 | 1.7 | 3.0 | 10.6 | 16.3 | 16.3 | 16.3 | 16.3 |
| **+1** | 1.4 | 2.2 | 4.6 | 16.3 | 16.3 | 16.3 | 16.3 | 16.3 |
| **0** | 1.7 | 3.0 | **10.6** | 16.3 | 16.3 | 16.3 | 16.3 | 16.3 |
| **-1** | 2.2 | 4.6 | 16.3 | 16.3 | 16.3 | 16.3 | 16.3 | 16.3 |
| **-2** | 3.0 | 10.6 | 16.3 | 16.3 | 16.3 | 16.3 | 16.3 | 16.3 |

The bold 10.6 at the origin is the baseline this document quotes in section 5.
The flat field is unambiguously below and to the right of it.

**Defect 2. More than half the surface is one repeated number.** 36 of the 64
cells sit at the 0.5 pp floor and return an identical 16.3. Of the 28 that do
not, 20 fall below 4.1. Version C is a reciprocal of the real rate, so a linear
colour scale spends most of its range on a region the grid barely visits: the
chart reads as a large green block against a near-uniform red block, and the
diagonal banding it exists to teach survives only in the left column or two.

**Defect 3. The diagonals are not diagonals.** `RATE_STEPS` moves 1 pp per cell;
`CPI_STEPS` moves 2 pp per cell (`src/scenario/charts.py`). The axes are
categorical, so the cells are drawn equally wide. Lines of constant `R - pi`
therefore run at two cells up for every one cell across. The caption calls them
diagonals and says they are *"lika stora"*. The render does not show that, and
the table above is the proof: 4.6 appears at (+5, +4), (+3, +2), (+1, 0) and
(-1, -2), one CPI column per two rate rows.

**Defect 4. It breaks the single colour language.** `colorscale="RdYlGn"` is the
only place in the app that uses a ramp other than `DIVERGING_SCALE`, which
`DESIGN_SYSTEM.md` section 2 presents as the one diverging scale the project
owns. The result is a saturated red-to-green legend labelled "SHAI" sitting two
pages away from a muted red-to-green map legend labelled with a z-score, on a
different quantity and a different scale. That is precisely the confusion
recommendation 3 above was written to prevent, reintroduced by the chart that
was supposed to help. The scenario marker also hardcodes `#0B1F3F` instead of
`COLORS["primary"]`, and both new charts pass `displayModeBar: False` where the
seven charts that preceded them pass `"hover"`.

### 9.3 Why this drifted

`tests/test_design_system_doc.py` checks the CSS class inventory in both
directions, `tests/test_css_naming.py` rejects a class outside the `shai-`
convention, and `tests/test_no_inline_copy.py` keeps strings out of pages. The
chart layer has none of that. No test asserts that a figure goes through
`get_chart_layout`, that its colours come from `COLORS` or `DIVERGING_SCALE`, or
that the toolbar setting is consistent. The design system is guarded everywhere
except where this drift happened, which is why it happened here and not in the
stylesheet.

Recorded as R14 in `docs/APP_REFERENCE.md` (Part II).

### 9.4 What to change, in order. All six done.

1. **Fix the caption.** Done, and it no longer asserts a direction in prose at
   all: the floor is drawn, per 9.2.
2. **Draw the `R - pi = 0.5` boundary** as an annotated dashed line. Done.
   `floor_boundary_intercept` derives it from the same arithmetic the simulator
   applies, and a test walks all 465 grid cells asserting that "below the line"
   and "the floor binds" never disagree. Limitation M4 is now a thing the reader
   sees. A caption can be wrong about a picture; a line derived from the formula
   cannot.
3. **Give both axes the same step in percentage points** and lock the aspect.
   Done: 0.5 pp on both, `yaxis.scaleanchor="x"` with ratio 1.
4. **Move from `go.Heatmap` to `go.Contour`.** Done, with `coloring="heatmap"`
   so the fill is smooth and the iso-lines are drawn on top. The grid now spans
   exactly the two sliders it explains, so the marked scenario is always inside
   the plane, and the marker sits on the exact scenario rather than snapping to
   a cell centre.
5. **Re-colour on `DIVERGING_SCALE`, centred on the change from baseline.** Done.
   `zmin` and `zmax` are fixed at -100 and +100 rather than autoscaled per
   county, so a colour means the same change in every län. The colourbar reads
   "Förändring mot basfall" and cannot be mistaken for the map's score.
6. **Add a chart-theme guard.** Done: `tests/test_chart_theme_guard.py`. See
   below.

### 9.5 The guard, and what it found

`tests/test_chart_theme_guard.py` makes three kinds of assertion, because there
are three ways to drift:

- **Built figures.** Every builder that can be called without a Streamlit process
  is called, and its layout is compared against `get_chart_layout`. Plotly's own
  default template is excluded: it ships a full palette for trace types this
  project never draws, so asserting against it would test Plotly.
- **Source text.** A colour written as `"#B94A48"` renders identically to
  `COLORS["high_risk"]`, so only the source can tell them apart, and the whole
  point of a token is that changing it moves every use. Same for a built-in
  colorscale name.
- **Call sites.** `displayModeBar` lives in the page, not the figure, so no built
  figure can show that drift.

Each of the three original deviations was re-introduced against the guard to
confirm it fails. A guard that has never been seen to fail is a comment.

**It found two more of the same kind on its first run**, neither previously
noticed: six colour literals in `pages/02_Lan_jamforelse.py` and three in
`pages/03_Kommun_djupanalys.py`. Every one was an exact palette value typed out
by hand, so every one rendered correctly and would have stopped doing so the day
the palette moved. That is the drift this section opened by describing, already
present in two older pages, which is the argument for the guard rather than for
the fix.

What the guard still does not reach: a chart built inline inside a page script
cannot be constructed without Streamlit, so the source scan covers it and the
built-figure assertions do not.

---

## 10. Summary of recommended work

| # | Change | Page | Status |
|---|---|---|---|
| 1 | Warn when LTI exceeds a lendable ratio | 04 | **Done.** Delivered by the interpretation panel |
| 2 | Move the F15 inflation caveat next to the rate slider | 05 | **Done.** Fires only when the rate moved without CPI |
| 3 | State that the simulator's number is not the map's number | 05 | **Done.** Scale note in the panel |
| 4 | Explain the deposit versus monthly cost trade-off | 04 | **Done.** Computed per region, so it states the direction that applies here |
| 6 | Flag that the savings rate is a share of gross income | 04 | **Done.** Caveat travels with the savings figure |
| 8 | Surface the single-income assumption | 04 | **Done.** Panel names it and points at the Par control |
| 5 | Say what A and B are for, and that C drives the site | 02 | **Done.** New robustness section on Sida 02 names C as load-bearing and quantifies B's disagreement |
| 7 | Display or remove the unused A and B risk columns | 02, pipeline | **Done, differently.** B's are displayed; A's are asserted, because they are identical to C's by construction. See the correction in section 6 |
| 9 | Apply scenario shocks across all kommuner, not one län | 05 | **Done.** `src/scenario/panel_scenario.py`. Required fixed class boundaries: a re-ranked panel provably cannot move. See 11.2 |
| 10 | Resolve the income definition: switch source, or fix docs and drop the multiplier | pipeline, docs | **Done.** Switched to `HE0110A/SamForvInk1`. See `docs/ADR/0001-income-series.md` |
| 12 | The Par multiplier doubled an already-household median | 04 | **Done.** The multiplier is now valid arithmetic on an individual median, and lives in `src/kontantinsats/income.py` |
| 11 | Decide whether to add HE0110M as a preliminary nowcast | pipeline | **Decided: no.** Recorded in the ADR. No overlap year means any splice assumes an uncalibrated conversion factor, which is the assumption this project removed when it stopped forward-filling income |
| 13 | The surface caption named the wrong corner of the plane | 05 | **Done.** The caption no longer claims a direction; the floor is drawn instead |
| 14 | Draw the 0,5 pp real-rate floor as a boundary instead of describing it | 05 | **Done.** Derived from the simulator's own floor and asserted across the grid |
| 15 | Equal pp steps on both surface axes, aspect locked | 05 | **Done.** 0,5 pp on both, `scaleanchor` ratio 1 |
| 16 | Move the surface from `go.Heatmap` to `go.Contour` | 05 | **Done.** Smooth fill, iso-lines drawn on top |
| 17 | Re-colour the surface on `DIVERGING_SCALE`, centred on change from baseline | 05 | **Done.** One diverging ramp again; bounds fixed so a colour means the same change in every län |
| 18 | Add a chart-theme guard: shared layout, tokens-only colours, consistent toolbar | tests | **Done.** `tests/test_chart_theme_guard.py`. Closed R14; found nine more colour literals in two older pages |
| 19 | Pass the baseline regime into the reachability chart instead of naming it twice | 04 | **Done.** `BASELINE_REGIME` in `engine.py`, read at all seven sites |

Items 1 and 2 were the two that changed what a user concludes rather than how
comfortable they are while concluding it. Both are now in place.

Of what remains, **12 and 13 are the two that put something wrong in front of a
reader.** They are wrong in different ways and cost different amounts to fix.

**12** makes a displayed number wrong, and it cannot be fixed independently of
10: whether the multiplier should be removed or made valid depends on which
income series the project decides to carry. That decision is deferred; nothing
in the pipeline has been changed.

**13** makes a sentence wrong while the numbers underneath it are right. It is a
single label and nothing blocks it, so it should not wait for the rest of the
chart work in 14 to 17.

Section 9 is implemented in full. Items 13 to 19 are done and the two
charts no longer ship as section 9 described them.

**Every item in this table is now closed.** Items 10, 11 and 12 were settled by
the income decision recorded in `docs/ADR/0001-income-series.md`; items 5, 7 and
9 by the work in section 11.

---

## 11. Closing items 5, 7 and 9, and what each one turned out to be

Two of the three were not the task the item described. Both times the difference
came from reading the data before building on it, which is the habit this
document keeps recommending and which keeps paying.

### 11.1 Items 5 and 7: the robustness argument was half an identity

Covered in the correction to section 6. Sida 02 now carries a **Robusthet**
section that states which version drives the site, shows the risk class counts
under C and B, and explains why A cannot disagree and therefore has no row. The six previously unread
columns are the subject of `tests/test_formula_agreement.py` rather than of a
table nobody can interpret.

The honest version of the argument turns out to be stronger than the advertised
one. "Three methods agree" invites the question of whether they were ever going
to disagree. "The one method that *can* rank differently does so for a quarter of
the country, and here are the eight municipalities where the gap is widest" is a
claim a reader can check.

### 11.2 Item 9: the obvious implementation returns zero, always

The item asked for the scenario to be applied across all 290 municipalities, so
the page could answer "how many kommuner cross into hög risk under this
scenario".

Built the obvious way, by shocking the panel and re-ranking it, **the answer is
zero for every scenario the sliders can produce.** All four sliders multiply each
municipality's Version C by the same constant: the rate and CPI shocks are
national, and the income and price shocks are relative. A within-year z-score on
logs removes a constant factor exactly. Measured on the committed panel, the
largest z change under a +4 pp rate shock, a +10 % income shock or a -25 % price
shock is 9·10⁻¹⁶.

This is the same property as the A-equals-C identity in section 6, arriving in a
different costume, and it is worth naming because the failure mode is so quiet:
you build the feature, see a table of unchanged counts, and go looking for a bug
in the code.

`src/scenario/panel_scenario.py` therefore **holds the class boundaries fixed at
the baseline year's distribution** and moves the country against them. That
changes what the number means, and the caption says so: a within-year class
compares a municipality to its peers that year, while a fixed-boundary class
compares the country after the shock to the country before it. The second is what
a scenario question is actually asking.

With that framing the national view delivers the page's central lesson at the
scale where it matters, for 2024:

| Scenario | Real rate | Hög risk, of 290 |
|---|---|---|
| Baseline | 0,77 % | 84 |
| Rate +4 pp only | 4,77 % | **290**, the entire country |
| Rate +4 pp with CPI +8 pp | 0,50 % | **20** |
| Price -25 % | 0,77 % | 36 |
| Income -10 % | 0,77 % | 97 |

The same nominal rate rise puts every municipality in the country into hög risk,
or takes 64 of them out of it, depending only on whether inflation moved with it.
That is limitation F15 stated in municipalities rather than in index points.

`tests/test_panel_scenario.py` asserts the no-op property directly across every
slider extreme, because it is the premise the design rests on: if a shock ever
stops being uniform, fixed boundaries become the wrong choice and the explanation
shown to readers becomes false.


---

## 12. Calculator audit and page copy, 2026-10-05

Two commits from two parallel sessions on `feature/conditional-projection`, made
in the same evening. Recorded here because neither changes a formula or an
artifact, so neither shows up in METHODOLOGY's register or in a refreshed figure,
and both change what a reader sees.

| Commit | Area | Kind |
|---|---|---|
| `4859813` | Kontantinsats engine, scenario simulator inputs, copy on Sida 03, 04 and 05 | Two engine defects fixed, copy shortened |
| `9e806a3` | Scenariosimulator result interpretation | Four misleading or missing explanations fixed |

### 12.1 The Kontantinsats engine paid borrowers in negative-rate years (`4859813`)

**Defect.** `apply_regime` used policy rate plus bank margin as the mortgage rate
with no lower bound. The policy rate was negative from 2015 to 2019 (−0,50 % in
2017 and 2018) and the margin slider reaches 0, so for a margin under about
0,5 pp the interest cost came out negative: the bank paying the borrower, which no
Swedish bank did.

**Fix.** The effective rate is floored at zero. Sida 04 used to compute the rate
it displays on its own (`policy_rate + margin`); it now reads `effective_rate`
back from the engine, so the page cannot show −0,50 % while the engine prices at
0 %.

**Effect.** Stockholm 2017, Lättnad 2026, monthly cost:

| Bank margin | Before | After | Rate used |
|---|---|---|---|
| 0,0 pp | 8 641 kr | 11 522 kr | 0,00 % |
| 1,7 pp (default) | 18 434 kr | 18 434 kr | 1,20 % |

Only years with a negative policy rate (2015 to 2020) change, and only when the
margin is smaller than the size of that negative rate. The default margin, and
every year from 2021, are unchanged, so no README or ENGINE demo figure moved. `tests/test_kontantinsats_engine.py` re-derives this table.

### 12.2 Impossible inputs returned reassuring answers (`4859813`)

**Defect.** A zero income returned 0 years to save and a debt ratio of 0, which
reads as the easiest purchase in the country rather than an impossible one. A
missing or negative price returned NaN or a negative cost without complaint.

**Fix.** Both engines validate at the boundary and raise `ValueError` naming the
argument: price and income must be positive and finite, savings rate in (0, 1],
bank margin non-negative, every rate and shock finite, relative shocks above
−100 %. `apply_regime` also refuses a rate above 0,25, which is a percentage
passed where a decimal belongs (3,46 for 0,0346). Sida 04 catches the error and
shows `ki.berakningsfel`; Sida 05 already caught simulator errors.

**Effect.** None on any selectable year, because no such row exists. A future
refresh that brings one in will show a message instead of a wrong number, and
before this Sida 04 would have crashed rather than either.

### 12.3 What the engine tests check (`4859813`)

66 tests in two files, written before the fixes and failing against the old code.

- `tests/test_kontantinsats_engine.py`: each regime by hand on round numbers
  against the rules in METHODOLOGY section 6; the LTI rule applying strictly above
  4,5; reconciliation of every derived field and no negative cost on a grid of
  price, income, rate (including negative) and margin; cost monotone in price and
  rate; same-deposit regimes ordered by strictness; the Par case halving years and
  debt ratio; every kommun and bostadsrätt county in every selectable year at every
  control extreme.
- `tests/test_scenario_engine.py`: the simulator's baseline equals
  `compute_version_c` on every county-year, so Sida 05 starts from the number the
  other pages show; equal rate and CPI shocks cancel; C halves when the real rate
  doubles above the floor; income and price act proportionally; the floor makes
  rate moves under it inert and caps the gain from cuts; every slider corner on
  every county-year is finite and positive.

The sweep also found county rows for 2011 to 2013 with no policy rate. They are
not selectable, so the test is limited to `selectable_years()` and nothing was
changed.

### 12.4 Scenario interpretation (`9e806a3`)

A statistical validation of the simulator (2022 and 2024, Monte Carlo, historical
replay, Sobol sensitivity) found the arithmetic exact and four explanations wrong
or missing. All four are in `src/ui/interpret.py` and `src/scenario/sections.py`,
guarded by `tests/test_scenario_interpretation.py`.

1. **Floor absorption was reported backwards.** On a floored baseline (2015 to
   2023) a rate or CPI shock that stays under the floor returned "oförändrad"
   plus the warning that the whole change counts as real, the opposite of what
   happened. A new finding, `sc.tolk_golv_absorberar`, names the absorption and
   the warning is suppressed in that case. This is the gap the 2023 reading guide
   recorded as "found, not fixed".
2. **The Riksbanken 2022 preset improves affordability with no explanation.** Its
   inputs stay as they are (section 5 item 2); a caption, `sc.tolk_preset_2022`,
   says why, and the help text says the values are peak-to-trough rather than
   annual means. The values moved to `src/scenario/presets.py` so the page and the
   caption cannot drift apart.
3. **Fragile baselines are flagged.** When the baseline real rate is within
   0,5 pp above the floor, `sc.tolk_nara_golvet` warns how much a 0,1 pp CPI
   revision moves the result. In 2024 the real rate is 0,77 pp, so about 13 %.
4. **The national class count saturates or freezes.** All 290 kommuner are hög
   risk by +4 pp in 2024, and on a floored year such as 2022 a rate or CPI shock
   leaves the counts frozen. The median Version C shift is now shown beside them.

### 12.5 Page copy (`4859813`)

Shortened on request: long text under a chart is read by nobody, and the detail
that has value moves into an expander instead of being lost.

| Page | Change |
|---|---|
| Sida 03 | Projection caption and explanation cut to two lines; the reasoning moved to the expander "Varför tre antaganden i stället för en förutsägelse?" |
| Sida 04 | "Vad sidan svarar på" and the Pristyp note cut to a few lines each |
| Sida 05 | Purpose panel, scope note, surface caption and four result notes cut; the surface explanation moved to the expander "Hur läser jag diagrammet?" |

Every rewritten sentence was checked against the code and data, which caught
errors, three of them inherited from the old copy:

- the scope note said Version A uses unemployment, when only B does;
- Sida 05 called itself the only forward-looking page, while Sida 03 projects;
- "Stockholm får 6,2 poäng" was a stale typed figure;
- the first rewrite of the projection line said every line is an assumption, when
  two of the five are history;
- Sida 04 said its rules "kan ändras", when they are compared rather than edited.

The first shortened projection line used a word from the withdrawn modelling
vocabulary, and `tests/test_withdrawn_vocabulary.py` rejected it; the copy says
"förutsägelse", as before.


---

# Part II — Open risks and pending decisions

Things that are **not bugs today** but will cost something later, found while revising
the project. Each one is either a decision someone has to make
or a hazard that is currently held shut by a guard rather than fixed at the root.

Kept separate from the plan because the plan is a task list that ends when Phase 4 ends.
These outlive it.

**Created:** 2026-09-15 · after Phase 2
**Status key:** `OPEN` · `ACCEPTED` (decided, living with it) · `CLOSED`

| # | Risk | Severity | Status |
|---|------|----------|--------|
| R1 | Version B re-bases every historical value whenever the panel changes | **High** | **CLOSED** |
| R2 | Three pages read year lists from the data instead of `YEAR_RANGE` | Medium | **CLOSED** |
| R3 | The `pipeline` extra is unverified as an install | Medium | **CLOSED** |
| R4 | The model-fitting step exhausts memory on this machine | Medium | **CLOSED** |
| R5 | Refresh-pipeline modules have no tests (73 % overall, was 15 %) | **High** | **CLOSED** |
| R6 | The 67-render check lives in a scratch directory, not the repo | Medium | **CLOSED** |
| R7 | A fresh deploy installs major versions the app was never tested against | **High** | **ACCEPTED** |
| R8 | `folium_static` is deprecated and will be removed | Medium | **CLOSED** |
| R9 | `labels.py` holds markup and LaTeX, not only copy | Low | **CLOSED** |
| R10 | Two `src/data/` modules exceed the line limit and have no tests | Medium | **CLOSED** |
| R11 | The map cache cannot hold every year x risk combination | Low | **CLOSED** |
| R12 | A zero price divides to infinity in Version C | Low | **CLOSED** |
| R13 | 24 KB of CSS is inlined on every page load, unavoidably | Low | **ACCEPTED** |
| R14 | The chart layer sits outside every design guard | Medium | **CLOSED** |
| R15 | Numbers quoted in docstrings and markdown are guarded nowhere | Medium | **CLOSED** |
| R16 | The fitted model's first projected year is implausible for every county | **High** | **CLOSED** |

---

## R1 — Version B re-bases every historical value whenever the panel changes

**Severity: High. CLOSED** on 2026-09-21 by `src/indices/b_reference.py`.

`compute_version_b` z-scored its four components — price-index ratio, policy rate,
unemployment, CPI — **pooled across every row of the panel it was handed**. That pooling is
deliberate: D5 kept B's construction pooled because the pooled level is the only time trend
the index carries. Versions A and C are normalised within year and are immune.

The consequence was that B's published values were a function of panel composition. Add a
row anywhere and every year moved.

### What the measurement showed

This entry asked for one thing before a decision: *how many municipality-years actually
change class across a realistic refresh*, on the precedent of a 19-row incident in T2.4, and
suggested that 0.6 % might be small enough to accept with a note. Both cases were measured.

| Refresh | `version_b` rows moved | `rank_b` changed | `risk_b` changed |
|---|---|---|---|
| One ordinary year appended (2025, simulated) | 3190 of 3190 | 947, up to 4 places | 7 |
| The income-source switch of 2026-09-21 | 3190 of 3190 | 2971, up to **117** places | **225** |

Version C, normalised within year, moved on **zero** rows under the same appended year.

The second line is what settled it. The 19-row precedent came from appending data; a change
to a *source definition* is an order of magnitude worse, and that is the case that actually
occurred. Accepting 225 silent risk-class changes with a footnote was not defensible.

### The fix, and why it is not option C

The four options this entry listed were: leave pooled and announce it (A), freeze per
vintage (B), normalise within year like A and C (C), or split into a pooled level plus a
within-year rank (D).

What shipped is closest to B, with the cost that made B unattractive removed. This entry
framed freezing as "per vintage", which would leave two vintages incomparable. **The
reference is frozen once and carried forward instead**, so every vintage shares one
yardstick and all of them stay comparable. Re-basing becomes a deliberate act with a version
bump behind it.

Crucially this keeps the trend that ruled out option C. It arguably improves it: under the
moving reference, adding a high-rate year inflated the pooled standard deviation and pushed
earlier high-rate years back toward zero, so the yardstick shrank as the thing it measured
grew. "2.3 standard deviations above the 2014 to 2024 norm" now means the same thing in 2030
as it does today.

### Adoption cost: none

The reference was derived from the panel as it stood, so scoring against it reproduced every
existing value exactly. The rebuild that adopted it left all four affordability parquets
byte-identical; only the provenance timestamp changed.
`tests/test_version_b_reference.py` asserts that property at all three levels, so it cannot
be quietly lost.

One trap worth recording, because the first draft fell into it: the reference must be
derived from **exactly** the rows that get scored. `complete_case` returns 4060 municipal
rows while only 3190 carry every index input, and deriving from the first while scoring the
second put the frozen moments up to 0.19 away from the moving ones. `scorable_rows` is now
exposed from `affordability.py` so both paths call the same filter.

### What guards it

`tests/test_version_b_reference.py`:

- appending a year leaves every historical `version_b`, `rank_b` and `risk_b` untouched
- **the negative control**: the same append on the unreferenced path still rewrites history,
  so the test above cannot pass by describing a scenario that no longer occurs
- the committed reference matches what the committed panel produces, so the JSON cannot be
  hand-edited into a silent re-base
- the artifact covers all three levels, so `reference_for` never bootstraps a new norm from
  whatever panel happens to be in a checkout

**Revisit if:** the Version B formula gains or loses a component, which the stored reference
will refuse rather than guess at, or the panel changes enough that the 2014 to 2024 norm
stops describing anything useful. Both are deliberate re-bases: bump `version` and expect
every B value to move.

---

## R2 — Three pages read year lists from the data instead of `YEAR_RANGE`

**Severity: Medium.** Currently harmless, same class as a defect already fixed once.

T1.4 made the sidebar derive its year selector from `complete_case_max_year()`. Three
pages never got the same treatment and still ask the dataframe what years exist:

| File | Line | Call |
|---|---|---|
| `pages/02_Lan_jamforelse.py` | 163, 180 | `sorted(county_versions["year"].unique())` |
| `pages/04_Kontantinsats.py` | 60 | `sorted(municipal["year"].unique(), reverse=True)` |
| `pages/05_Scenario.py` | 44 | `sorted(county_panel["year"].unique(), reverse=True)` |

Pages 04 and 05 read *panel* frames, which already run to 2026, so they have been exposed
the whole time. Page 02 reads an *affordability* frame, which is why the T2.4 refresh would
have printed a chart titled "2014–2025" until `complete_case()` pulled the index back.

The index is the only thing holding this shut. Any future change that legitimately extends
the index past what the selector offers reopens it in three places at once.

**Recommendation:** fold into Phase 3, alongside T3.7 (`src/ui/filters.py`), which already
exists to de-duplicate page filter logic. One shared accessor, and a source-level guard in
the style of `tests/test_pages_no_recompute.py` asserting no page derives its own year list.

### CLOSED 2026-09-22 — one accessor, a guard, and a fourth site nobody had listed

`src.provenance.selectable_years()` resolves the index period once, the same way the
sidebar has since T1.4, and the three sites now read it.

The exposure was real on two of them rather than stylistic. `04_Kontantinsats` and
`05_Scenario` built their "no data for this year, try one of these" fallbacks from *panel*
frames, which run to 2026 while the index stops at 2024. The suggestions were years that
render blank. Page 02's two sites were bounded correctly, because they read a scored
artifact, but were deriving a fact the page had already resolved from provenance at the top.

**The guard found a fourth site the register had not listed**, and it turned out to be dead
code rather than a wrong year list. `02_Lan_jamforelse` built `_imputed_years` from the
scored artifact to shade forward-filled years on its trend charts. T2.4 made
`step_compute_indices` score only `complete_case()` rows, so that artifact carries **zero**
imputed rows by construction — `is_imputed_income` is False on all 3190. The set was always
empty, the shading could never render, and the chart was advertising an annotation that
cannot appear. Removed, with the reason recorded where it stood.

That is the argument for writing the guard rather than just fixing the three known sites: a
list of three came from reading the code once, and the scan found the one that reading had
missed.

`tests/test_year_range.py` now asserts that no page asks a frame which years exist, that
`selectable_years()` matches the artifact it describes, and that it is the index period
rather than the panel's — the two differ by design, and conflating them is what R2 was.

---

## R3 — The `pipeline` extra is unverified as an install

**Severity: Medium.** A documented path that may not work.

T2.4 proved the refresh pipeline *runs*. It did not prove `pip install -e ".[pipeline]"`
*installs*, because the compiled statistical packages were already present in the working
environment. `pyproject.toml` now advertises that command in `README.md` and
`docs/DEPLOYMENT.md`, so if those two have no wheel for the target interpreter and no
build toolchain is present, the documented instruction fails for whoever tries it first.

One of them pulled Stan. They were the single most fragile dependency in the project,
which is exactly why T2.1 moved it out of the runtime set.

**Recommendation:** run `pip install -e ".[pipeline]"` in a genuinely empty venv on the
interpreter the docs promise, on the platform a maintainer would actually use. If it fails,
that is worth knowing now and worth writing down next to the command rather than leaving
someone to discover it. Consider pinning them to versions with
published wheels for the supported Python range.

### CLOSED 2026-09-22 — it installs

Run as documented, on the interpreter the docs promise: `python3.11 -m venv`, then
`pip install -e ".[pipeline]"` into it. **It succeeds**, and nothing compiles from source —
both resolve to wheels.

| | Resolved |
|---|---|
| Python | 3.11.13 |

The recommendation to pin them to versions with published wheels is
therefore not needed today. It stays worth remembering: this verifies one interpreter on one
platform, and the fragility the risk described is real, it simply is not biting.

**One thing the run surfaced, and it belongs to R7 rather than here.** The clean install
resolved `pandas 3.0.6` and `numpy 2.4.6` — both inside the declared caps, and both major
versions above what the app is verified against. That is R7 happening in front of us rather
than in theory.
---

## R4 — The model-fitting step exhausts memory on this machine

**Severity: Medium.** Blocks a step that is currently, but not permanently, optional.

The model-fitting step ran two statistical models across 84 series. Run on 2026-09-15 it was killed
by the OS for low memory. Steps 1–3 completed normally, so this is specific to step 4.

It did not matter that time: the training window ends at `_resolve_end_year()`, still 2024,
and none of the fitted variables changed inside it, so the existing artifacts are
equivalent rather than merely stale. **That reasoning expires** the moment income publishes
2025 and the training window moves, at which point the artifacts genuinely must be
regenerated, and the step that cannot run is the one that has to.

**Recommendation:** treat model fitting as a separate, deliberate run and regenerate the artifacts
as a separate, deliberate run. If it still cannot complete, make the pipeline checkpoint
per county so a kill loses one county rather than the whole step. Worth measuring actual
peak RSS before choosing a fix.

*(Moot since 2026-09-25: R16 deleted both fitting pipelines. The step that could be
killed no longer exists, and its replacement is arithmetic over 21 rows. The flag is now
`--no-projection`.)*

### CLOSED 2026-09-22 — measured, and it does not

This entry recommended measuring actual peak RSS before choosing a fix. Measured:

| | Result |
|---|---|
| First model, 84 series | 103 s |
| Second model, 84 series | 19 s |
| **Peak RSS** | **197 MB** |

The 2026-09-15 OOM kill does not reproduce. 197 MB is not close to exhausting anything, and
the whole step finishes in two minutes. Whatever happened that day was about the state of
that machine, not about this code.

That matters more than a closed row, because this risk carried an expiry: its own reasoning
for why the kill was harmless — that the training window still ended in 2024 and none of the
fitted variables had moved inside it, ends the moment SCB publishes 2025 income. The step
that could not run would have been the one that had to. It runs.

The full step was also exercised end to end on 2026-09-21 as part of the income switch, and
wrote all three fitted artifacts.

**What this leaves open, elsewhere:** the fitted pipelines remain at 0 % coverage, which is
R5, not this. And the failure mode that nearly shipped that day was not memory but silence —
steps 1 to 3 wrote their artifacts and step 4 exited on a missing import, leaving committed
artifacts derived from the previous income series. Worth a guard comparing artifact vintages;
recorded under R5's recommendation rather than reopening this.
---

## R5 — Whole subsystems have no tests

**Severity: High.** Improved substantially, not closed.

Measured after Phase 1 this was **15 %** overall, with `src/indices/affordability.py` — the
module computing Version A, B and C — at **0 %**. Both numbers are now out of date, which is
itself worth noting: a risk register goes stale exactly like the prose T4.1 polices.

Measured after Phase 4:

| | After Phase 1 | Now |
|---|---|---|
| `src/` overall | 15 % | **44 %** |
| `src/indices/affordability.py` | 0 % | 65 % |
| `src/indices/normalize.py` | 62 % | 62 % |
| `src/ui/` | ~45 % | 81–100 % |

Most of the gain is T4.4: putting the 67-render sweep inside the suite exercises every page and
nearly all of `src/ui/`. The index formulas gained coverage incidentally, through T2.4's
complete-case tests.

**Still at 0 %:**

| Module | Statements |
|---|---|
| `src/data/build_panel.py` | 346 |
| `src/data/scb_client.py` | 241 |
| `src/data/riksbanken_client.py` | 67 |

These are the refresh pipeline: the code that builds the artifacts everything else reads. It
runs once or twice a year, by hand, and a mistake in it is invisible until a number looks wrong
on a page. `build_panel.py` in particular holds income imputation, the ragged-panel joins and
the forward-fill — the machinery behind D1, F9 and the `complete_case()` rule.

### Progress 2026-09-22 — the panel builder is covered, and the numbers above are stale

The table earlier in this entry reports 44 % overall and lists five modules at 0 %. Both
were out of date by the time they were read, which this entry itself predicted: *"a risk
register goes stale exactly like the prose T4.1 polices."*

Measured now:

| | After Phase 4 | Now |
|---|---|---|
| `src/` overall | 44 % | **68 %** |
| `src/data/build_panel.py` | 0 % | **91 %** |
| `src/data/clean_sources.py` | — | **95 %** |
| `src/data/panel_summary.py` | — | **100 %** |
| `src/data/scb_client.py` | 0 % | 13 % |

The narrowed recommendation this entry made — property tests for
`affordability.py` — had already been satisfied by
`tests/test_affordability_properties.py`, which covers orientation, monotonicity in income
and price, the floored real rate, the zero-price case and panel-composition dependence. That
left `build_panel.py` as the target, and it is done: `tests/test_build_panel.py` (28) drives
the whole builder in-process by patching `_read`, the single I/O seam, with synthetic frames
in each source's published shape.

What those tests assert is the part worth naming. They are not smoke tests; they pin the
**documented approximations**, each of which is a deliberate decision that would otherwise
become something else the first time a merge key moved:

- the county price index reaching every municipality (F1)
- the national policy rate and CPI at all three levels (F2)
- K/T and transaction-price fallback to county values, with `has_native_*` recording which
- income forward-filled past its vintage at 3 %/yr and flagged (F9), with
  `median_income_tkr` moving with `median_income`
- the combined `08+09` Kalmar and Gotland row split so both counties join
- Kolada's `00` + SCB code convention for counties
- quarterly K/T rows and non-permanent property types filtered out rather than averaged in

**Still at 0 %:** the two fitted pipelines (108 and 110 statements) and
`src/data/riksbanken_client.py` (67). These are
the remaining reason this risk is reduced rather than closed. Those pipelines are the
larger gap; they feed page 03 and they are the step most likely to be skipped on a refresh,
which is exactly how the stale artifacts of 2026-09-21 nearly shipped.

### CLOSED 2026-09-22 — no subsystem is at zero

The two modules that recommendation named are done, and with them the risk's own
framing — *whole subsystems have no tests* — stops being true of anything.

| | After Phase 1 | After Phase 4 | Now |
|---|---|---|---|
| `src/` overall | 15 % | 44 % | **73 %** |
| `src/data/build_panel.py` | 0 % | 0 % | 91 % |
| `src/data/clean_sources.py` | — | — | 95 % |
| `src/data/riksbanken_client.py` | 0 % | 0 % | **87 %** |

**`riksbanken_client.py`** was named for leverage rather than size: 67 statements producing a
series that Version A divides by directly and Version C through the real rate. The tests
stub the network and pin the two things that can go wrong quietly — a rate that fails to
parse becoming `NaN` through `errors="coerce"`, and the fact that the annual figure is the
mean of the business days present rather than a time-weighted average. The second is a
modelling choice the whole panel inherits, and it was nowhere written down.

**The fitted pipelines are tested by contract, not by output**, and the low percentages
are the deliberate result. Pinning their predicted values would be a change-detector: it
would fail whenever a library changed a default, pass while the pipeline projected the wrong
series entirely, and leave nobody able to say whether a diff was a regression or a better
model. The uncovered statements are the model fitting, which is exercised end to end
whenever a refresh runs.

What is covered is everything around the fit: `_resolve_end_year` ignoring the imputed tail,
the horizon and its consecutive target years, all 21 counties present for every variable,
bands that contain their own mean and are not inverted, and the widening validator on both
a widening and a narrowing series.

**The most valuable one is the vintage check**, and it closes the loop on the near-miss R4
describes. A projection's first target year must be the year after the last observed one, so
its artifacts and the index artifacts can be compared directly without either
recording a timestamp. On 2026-09-21 the refresh wrote panels and indices, then exited on a
missing import before the fitting step, leaving committed artifacts built on the previous
income series. It was caught by hand. It would now fail a test.

**Residual, and deliberately accepted:** the model-fitting bodies of both pipelines
are not unit-tested. Unit tests are the wrong instrument there, and the right one — the
contract on their output, plus the vintage check — is in place.

---

## R6 — The 67-render check is not in the repository

**Severity: Medium.** The strongest evidence for Phase 1's exit criterion cannot be re-run.

Every page rendering for every offered year — 6 pages × 11 years + landing — is the check
that actually proves the app works. It has been run at each step and has passed 67/67 every
time. It exists as a script in a session scratch directory. It is not committed, no one
else can run it, and CI cannot.

T4.4 (`tests/test_pages_render.py`) is its slot in the plan, at the very end of Phase 4.

**Recommendation:** pull T4.4 forward. It is the highest-value test in the plan and it is
scheduled last. Every phase after this one changes the UI, which is precisely what this
check covers.

### CLOSED 2026-09-16

T4.4 pulled forward and landed as `tests/test_pages_render.py` — **81 tests in 14 s**, inside
the default suite. Wider than the scratch script it replaces: it also covers an empty risk
selection and a single-class selection on every page, parametrises years off `YEAR_RANGE` so
the sweep widens when provenance does, asserts each page rendered *something* (a page that
returned early used to pass silently), and includes two meta-tests proving the harness can
actually fail — one script that raises, one that renders nothing. Without those, 81 green
ticks could mean 81 renders or a broken harness.

---

## R7 — A fresh deploy installs major versions the app was never tested against

**Severity: High.** Discovered by T2.5; currently working, by luck rather than design.

`requirements.txt` pins lower bounds only, on the reasoning that Streamlit Cloud rebuilds
periodically and an upper pin would rot silently. The clean-environment check showed what
that actually resolves to today:

| Package | Verified against | Clean install resolved |
|---|---|---|
| pandas | 2.3.3 | **3.0.5** |
| numpy | 1.26.2 | **2.5.3** |
| streamlit | 1.55.0 | 1.64.0 |
| plotly | 6.6.0 | 7.1.0 |
| pyarrow | 23.0.1 | 25.0.1 |

pandas 2 → 3 and numpy 1 → 2 are major version boundaries with documented breaking
changes. **All 67 page renders pass on the resolved set**, so nothing is broken right now.
But a deploy today runs code paths no test in this repo has ever exercised against those
versions, and the next resolver shift happens without anyone choosing it.

The failure mode is the worst kind: the app works in the maintainer's environment
(pandas 2.3.3) and breaks only in production, on a rebuild nobody triggered.

### The decision

| Option | What it buys | What it costs |
|---|---|---|
| **A. Leave lower bounds** | Free security and bugfix updates; no pin maintenance | Untested majors reach production unannounced |
| **B. Cap the majors** (`pandas>=2.3.3,<4`, `numpy>=1.26.2,<3`) | Blocks the next major boundary from arriving silently | Needs a deliberate bump; a stale cap eventually blocks a needed fix |
| **C. Full lockfile** | Reproducible deploys, exactly | Streamlit Cloud does not consume one natively; heaviest to maintain |

**Recommendation: B, plus run the clean-environment check as part of the release routine.**
The cap is one line per package and turns a silent production break into a visible
resolution failure. The check is already scripted — see R6, which is the same gap wearing a
different hat: the verification exists but lives nowhere the project can re-run it.

### ACCEPTED 2026-09-16 — option B taken, residual risk remains

Caps applied to `requirements.txt` and mirrored into `pyproject.toml`, with
`test_every_requirement_caps_the_next_major` and a new test asserting the two files agree on
*specifiers*, not merely on package names.

Every cap sits **above** what T2.5 resolved and verified, so this is not a downgrade:

| Package | Verified | Cap |
|---|---|---|
| pandas | 3.0.5 works | `>=2.3.3,<4` |
| numpy | 2.5.3 works | `>=1.26.2,<3` |
| streamlit | 1.64.0 works | `>=1.55.0,<2` |
| plotly | 7.1.0 works | `>=6.6.0,<8` |
| pyarrow | 25.0.1 works | `>=23.0.1,<26` |
| folium, streamlit-folium, branca | 0.x | `<1` |

**Why this is ACCEPTED and not CLOSED.** Two gaps survive. The 0.x packages get `<1`, which
still admits breaking *minor* bumps — the 0.x convention means 0.21 may break what 0.20 did,
and `folium` is the one drawing the map. And a cap only converts a silent break into a
visible resolution failure; it does not tell anyone the app was never tested on what got
installed. That needs the clean-environment check to run on a schedule, not once per phase.

**Revisit when:** a deploy fails to resolve, or before any release that matters.

**Note on `requests`:** the clean install contains it as a transitive dependency of
streamlit, which is correct and expected — T2.1's criterion is that it is absent from
`requirements.txt`, not from the environment. It emits a `RequestsDependencyWarning` about
`charset_normalizer` in that venv. Harmless: the import graph confirms no page imports
`requests`.

---

## R8 — `folium_static` is deprecated and will be removed

**Severity: Medium.** A scheduled removal on the one component that draws the map.

`src/ui/choropleth.py:361` calls `folium_static(m, width=None, height=height)`. Surfaced by
T4.4: every page render that draws the map emits

    DeprecationWarning: folium_static is deprecated and will be removed in a future
    release, or simply replaced with st_folium which always passes
    returned_objects=[] to the component.

Thirteen warnings across the render sweep. Nothing is broken — but "will be removed" plus
`streamlit-folium` capped only at `<1` (see R7) means a future minor release deletes the
function and the choropleth stops rendering.

The migration is not a rename. `st_folium` returns interaction state to Python and triggers
a rerun on map events unless `returned_objects=[]` is passed; getting that wrong turns every
pan and zoom into a full page re-render. `folium_static` exists precisely to avoid that.

**Recommendation:** migrate to `st_folium(m, returned_objects=[], ...)` deliberately, during
Phase 3 while the map is already being touched (T3.9 adds the "Om kartan" expander), and
confirm through `tests/test_pages_render.py` that render counts and timing do not change.
Not urgent, but do not let it be discovered by a broken deploy.

### CLOSED 2026-09-16 — and it took `streamlit-folium` with it

Resolved by the performance work rather than by a migration. `folium_static` only ever
wrapped `st.components.v1.html(m.get_root().render(), ...)`, and caching that render meant
calling the two halves separately anyway. The deprecated call is gone, `st_folium` was never
needed, and **the suite now emits zero deprecation warnings**, down from 13 per render sweep.

Dropping it removed the last import of `streamlit-folium`, which `tests/test_runtime_dependencies.py`
caught immediately — declared in `requirements.txt` but no longer reachable from any page. The
runtime set is now **seven packages**.

---

## R9 — `labels.py` holds markup and LaTeX, not only copy

**Severity: Low.** Correct by T3.1's acceptance, wrong as a long-term home.

T3.1 required that no Swedish string literal remain inline in `app.py` or `pages/*.py`. Some
of those literals were not sentences — they were HTML blocks with inline CSS, a Plotly hover
template, and a LaTeX formula:

    sc.version_c_realversion_beraknas_som_text   $$	ext{Affordability}_C = rac{...}$$
    rv.v0_version_c_v1_ranking_kommun_z_poang    a full <div class="shai-card"> template
    lj.v0_ar_x_varde_y_2f                        <b>{v0}</b><br>År: %{{x}}<br>...

So `SWEDISH_LABELS` is now three things at once: copy, markup templates, and maths. Three
consequences. The brace-escaping rule exists only because of the markup, and is a live trap
for anyone adding a label by hand. A reviewer reading copy has to skim HTML. And T4.1, which
re-derives every quoted number from the artifacts, has to parse numbers out of markup rather
than out of sentences.

**Recommendation:** split when Phase 3 next touches these files — `SWEDISH_LABELS` for prose,
a separate `TEMPLATES` mapping (or component functions) for markup. T3.10 splits
`components.py` and is the natural moment: markup that lives in a component does not need to
live in a label at all. Low priority because nothing is broken and the guard tests pin the
current behaviour; worth doing before the dict grows past the point where anyone reads it.

### CLOSED 2026-09-22 — `src/ui/templates.py`

Ten markup blocks moved out of `SWEDISH_LABELS`: the two regime tables, the assumptions
panel, the landing blurb and five smaller fragments. 368 labels and 10 templates.

**The line is a rule rather than a judgement**, which is what makes it hold. A string
carrying HTML tags is a template; prose has none. `tests/test_labels.py` asserts both
directions, so a markup block cannot drift back into the copy dictionary and a sentence
cannot end up in the template file.

One carve-out, because the alternative is worse: Plotly hover templates contain `<br>` and
`<extra></extra>`, which is Plotly's microformat rather than page markup, and what a reader
sees in a tooltip is copy. They are recognised by their `%{...}` placeholders, which appear
in no page HTML, so the exemption needs no key-name convention to maintain.

The LaTeX this risk also named stayed put. There is exactly one formula string, it is read
by `st.latex` as content rather than assembled as markup, and a third dictionary for a
single entry would be structure for its own sake.

**The move nearly weakened a guard, which is the part worth recording.**
`test_copy_matches_artifacts.py` scanned `SWEDISH_LABELS` for unexamined year literals.
Four of the ten moved blocks carry 13 year literals between them — they are regime tables,
dense with 2010, 2016, 2018 and 2026 — so scanning only the copy dictionary afterwards would
have quietly narrowed the guard to the strings that happen not to carry markup. Prose wrapped
in a `<div>` goes stale exactly as easily. Its four scanning loops now read both dictionaries,
and that was verified by counting what came back into scope rather than assumed.

---

## R10 — Two `src/data/` modules exceed the line limit and have no tests

**Severity: Medium.** Two problems that make each other harder to fix.

T3.3, T3.10 and T3.11 brought every module under 400 lines except two, both outside Phase
3's scope:

| Module | Lines | Coverage |
|---|---|---|
| `src/data/build_panel.py` | 641 | 0 % |
| `src/data/scb_client.py` | 474 | 0 % |

`tests/test_file_sizes.py` exempts them **with their current lengths as ceilings**, so the
exemption covers the size they already are and not further growth.

They are left deliberately. Splitting a 641-line module with no tests is the riskiest
refactor available: `build_panel.py` is where income imputation, the ragged-panel joins and
the forward-fill live — the machinery behind D1, F9 and the `complete_case()` rule — and
nothing in the suite would catch a mistake in moving it.

**Recommendation:** tests before splitting, in that order. This is R5 wearing a second hat:
the modules that most need to be broken up are the ones it is least safe to touch, and the
way out is coverage, not courage.

### CLOSED 2026-09-22 — `build_panel.py` followed, and the set is empty

`build_panel.py` took the same route `scb_client.py` took the day before, in the order this
risk prescribed: tests first, then the split.

Coverage went 0 % to 87 % on the original module. With something able to catch a mistake,
the seam was obvious once looked for — the module was doing three jobs:

| Module | Lines | Holds |
|---|---|---|
| `src/data/clean_sources.py` | 267 | The shapes: one cleaner per raw source |
| `src/data/build_panel.py` | **387** | The joins, and the approximations they carry |
| `src/data/panel_summary.py` | 57 | The refresh report |

The report is the interesting extraction. It was 23 `print` statements inside `build_all`,
which meant the first thing anyone reads after a rebuild was the one part of the pipeline
nothing could check. It returns a string now, and two tests assert it describes what was
actually built.

**Verification:** the split was checked by rebuilding all three panels from the real cached
raw data and comparing to the pre-split artifacts. Identical, row for row, at every level. A
line count proves a file got shorter, not that it still works.

**The tests earned their keep during the split itself.** They failed the moment it landed,
because the cleaners resolve `_read` in their own module while `build_county_panel` also
calls it directly through the re-export, so patching one module left half the builder
reading the real `data/raw/`. That is precisely the class of mistake this risk said would go
uncaught in an untested module, and it was caught in seconds.

`EXEMPT_CEILINGS` is now empty, and `test_no_source_module_still_needs_a_ceiling` asserts it,
so re-opening the exemption is a visible decision rather than a quiet one. Only `labels.py`
remains exempt, as a data file with its own guards.

### Progress 2026-09-21 — `scb_client.py` is out

The condition this risk set was "tests before splitting, in that order". For
`scb_client.py` that condition was met, so the split happened.

The income-definition work gave the module its first tests:
`tests/test_variable_contracts.py` exercises its metadata path against fixtures and,
when a network is present, against the live SCB API. With something able to catch a
mistake, the transport layer moved to `src/data/pxweb.py`: rate limiting, querying,
caching and JSON-stat2 parsing on one side, and on the other only *which table, which
selection*. The two change for different reasons, which is the argument for the seam.

| Module | Before | After |
|---|---|---|
| `src/data/scb_client.py` | 487 | **328**, under the ordinary 400-line limit |
| `src/data/pxweb.py` | — | 194 |

`scb_client.py` has left `EXEMPT` entirely rather than receiving a lower ceiling, which
is what an exemption is supposed to become.

**Verification:** the refactor was checked by re-fetching the income table from SCB
afterwards and comparing the result to the pre-split cache. Identical in shape, columns
and every value. A line-count assertion proves a file got shorter, not that it still
works.

`build_panel.py` remains, at 615 lines and still without direct tests. It is the harder
half: income imputation, the ragged-panel joins and the `complete_case()` rule all live
there, and it keeps the recommendation unchanged.

### Progress 2026-09-17 — reduced, not closed

D2 and D3 took the first bite. The income forward-fill, which was written three times inside
`build_panel.py`, is now one tested function in `src/data/panel_income.py`:

| | Before | After |
|---|---|---|
| `build_panel.py` | 641 lines | **615** |
| its imputation logic | 3 copies, 0 tests | 1 function, **10 tests** |

Still over the 400-line limit, so the exemption stands — but its **ceiling is now 615**, so
the file cannot drift back up under cover of it. Ceilings ratchet downward only.

The remaining bulk is nine `_clean_*` helpers, one per source series. Each reads from
`data/raw/`, which is gitignored, so they cannot be tested as they stand; extracting them
would need the same artifact-identity net D2 used. `scb_client.py` is untouched and keeps its
474-line exemption.

---

## R11 — The map cache cannot hold every year × risk combination

**Severity: Low.** A deliberate memory ceiling, recorded so the next reader knows it was chosen.

The choropleth's rendered HTML is cached (`max_entries=24`), which took a year change from
380 ms to 50 ms. The frame arrives already risk-filtered, so the full input space is 11 years
× 7 risk combinations = **77 distinct maps**, and each document is ~1.2 MB:

| Entries | Cache cost |
|---|---|
| 11 (years only, default filter) | 13 MB |
| **24 (chosen)** | **29 MB** |
| 77 (everything) | 93 MB |

Caching all of it would spend roughly a tenth of a 1 GB Streamlit Cloud instance on an
interaction nobody performs exhaustively. Year changes — the common move — fit comfortably;
an unusual risk combination pays one 380 ms rebuild.

**If this ever needs closing properly:** render all municipalities always and vary only the
polygon *style* by risk class, so the map depends on the year alone and 11 entries suffice.
That changes what the map shows — filtered municipalities would grey out rather than vanish —
which is a design decision, not a performance one.

### CLOSED 2026-09-17

Dissolved rather than mitigated. Decision Q1 was answered **No**: the map is the national
picture and the risk pills filter the lists below it, so the map depends on the year alone.
The input space is 11 entries, not 77, and `max_entries=24` is comfortable headroom rather
than a rationed ceiling.

The memory table above is kept because it is the reasoning that led to the design change, not
because the ceiling still binds.

Measured after the change: **toggling a risk pill costs ~45 ms, down from ~370 ms**, because
the map no longer rebuilds at all. That was the most common interaction on the page.

---

## R12 — A zero price divides to infinity in Version C

**Severity: Low.** Latent, not live. Found by the property tests in Task D1.

`compute_version_c` divides by `transaction_price_sek` without guarding zero, so a zero
price yields `inf`. That value would then flow into the within-year z-score, and because a
standard deviation computed over an infinite value is `NaN`, **one bad row would silently
void every other municipality's `z_c` for that year** — a whole year of the map going blank
from a single cell.

It is not reachable today:

| Panel | Zeros | Nulls | Minimum |
|---|---|---|---|
| municipal | 0 | 290 | 260 000 SEK |
| county | 0 | 21 | 930 000 SEK |
| national | 0 | 1 | 2 050 000 SEK |

Nulls are handled — they produce `NaN`, which `complete_case()` and the artifact build
already exclude. Zero is the unguarded case, and SCB has never published one.

**Left unfixed deliberately.** `tests/test_affordability_properties.py` marks the property
`xfail(strict=True)`, so it documents the gap and will fail loudly if someone adds the guard
without closing this entry. The reason for not simply fixing it: any change to
`compute_version_c` alters every published `z_*`, which is a decision with a blast radius,
not a tidy-up — the same reasoning that made D6 a locked decision rather than a patch.

**Recommendation:** guard it the next time the formula is being changed for another reason,
so the re-publication is paid once. A `price <= 0` row should yield `NaN`, joining the nulls
that `complete_case()` already drops, rather than `inf`.

### CLOSED 2026-09-22 — and the deferral reason turned out not to apply

The recommendation was to guard this the next time the formula was being changed for another
reason, so the re-publication is paid once. Checked before acting, that cost is zero: no
panel at any level holds a non-positive price, the lowest being 260 000 SEK, so the guard
removes no row and moves no value. The rebuild confirmed it — `version_a`, `version_b`,
`version_c` and `z_c` identical to the last byte, no risk class changed.

Guarded in two places, because they fail differently:

- **`scorable_rows`** drops non-positive prices *and incomes* at the input, so no formula
  ever sees one. Income is included because Version B divides by it to form the
  price-to-income ratio; it is the same defect in the same shape, and the register only
  named price because that is where it was found.
- **`compute_version_a` and `compute_version_c`** yield `NaN` rather than `inf` on a
  non-positive price, which guards the direct call that the property tests make.

`test_zero_price_does_not_return_infinity` was the suite's only `xfail`, carrying the
instruction "if this starts passing, someone added the guard: remove the marker and close
R12". It passes; the marker is gone.

`test_guarding_the_denominators_changed_no_published_value` keeps the claim honest: if a
future refresh brings in a non-positive price, it fails, and the re-publication becomes a
deliberate decision with a number attached instead of being paid by accident.
---

## R13 — 24 KB of CSS is inlined on every page load

**Severity: Low.** Accepted because Streamlit leaves no alternative, not because it is ideal.

`inject_css()` writes the whole 24 KB stylesheet into every page render. A `<link>` to a
static file would be fetched once and cached instead.

**Task C1 tried exactly that and it cannot work.** Streamlit's `server.enableStaticServing`
does serve `./static/`, but with the wrong media type:

```
GET /app/static/shai.css    HTTP 200   25.1 KB
  Content-Type: text/plain
  X-Content-Type-Options: nosniff
```

`nosniff` instructs the browser not to infer a better type, so a stylesheet link pointing
there is ignored and the page renders unstyled. Streamlit exposes no setting for the media
type. The work was implemented in full, measured, and reverted.

**Why it is Low.** 24 KB gzips to a few KB on the wire, it is the same bytes every time so an
HTTP/2 connection handles it cheaply, and it is dwarfed by the 860 KB map document that rides
in the same response. Fixing the map payload mattered; this does not.

**Revisit if:** Streamlit gains a media-type mapping for static files, or the app moves off
Community Cloud to a host where a reverse proxy can serve `/static` itself. Flipping it back
on is a small change — the reasoning is recorded in `src/ui/css.py:inject_css`.

---

## R14 — The chart layer sits outside every design guard

**Severity: Medium. CLOSED** by `tests/test_chart_theme_guard.py`.

The design system used to be enforced everywhere except where charts are.
`tests/test_design_system_doc.py` checks the CSS class inventory in both directions and
verifies the map section against `choropleth.py`. `tests/test_css_naming.py` rejects a
class defined outside the `shai-` convention. `tests/test_no_inline_copy.py` keeps user
strings out of pages. **Nothing checked a Plotly figure.**

This was not hypothetical. The two charts added in `60e150d` drifted on three axes at
once and the suite stayed green:

| Deviation | Where | Now |
|---|---|---|
| Plotly's built-in `RdYlGn` instead of `DIVERGING_SCALE`, so the app had two diverging ramps | `src/scenario/charts.py` | `DIVERGING_SCALE`, reversed |
| The primary navy hardcoded as a hex literal instead of `COLORS["primary"]` | `src/scenario/charts.py` | The token |
| `displayModeBar: False` where the seven earlier charts pass `"hover"` | `src/scenario/charts.py`, `src/kontantinsats/sections.py` | `"hover"` everywhere |

Fixing them turned up two more of the same kind that no one had noticed: six colour
literals in `pages/02_Lan_jamforelse.py` and three in `pages/03_Kommun_djupanalys.py`,
each one an exact palette value spelled out by hand. They painted the right pixel and
would have painted the wrong one the day the palette moved.

**Why it was Medium rather than Low.** A stylesheet drift is visible the moment someone
looks at the page. A chart drift looks deliberate: a second red-to-green ramp reads as a
design choice, and a reader has no way to tell it is not the map's scale.

**What the guard does**, in the shape the CSS tests already use: it builds every figure a
test can build and asserts the layout came from `get_chart_layout` and that every colour
in the rendered figure is a token; it scans the source of every figure-building file for
hex literals and built-in colorscale names, because a built figure cannot tell
`"#B94A48"` from `COLORS["high_risk"]`; and it scans call sites for `displayModeBar`,
which lives in the page rather than the figure. Each of the three original deviations was
re-introduced against the guard to confirm it fails rather than merely passing.

**What it still does not cover.** Charts built inline inside a page script cannot be
constructed without a Streamlit process, so they are reached by the source scan but not
by the built-figure assertions. Moving them into builder modules would close that gap.

**Revisit if:** an inline page chart grows enough logic to deserve a module, at which
point it should get one and fall under the built-figure half of the guard too.

---

## R15 — Numbers quoted in docstrings and markdown are guarded nowhere

**Severity: Medium. CLOSED** on 2026-09-22 by `tests/test_prose_matches_artifacts.py`.

`tests/test_copy_matches_artifacts.py` exists because of Findings A, C and H, which were
one defect wearing three coats: prose asserting a number the data no longer supported. It
polices `SWEDISH_LABELS`, which is where the copy a user reads lives, so it was the right
place to start. It works, too — it caught the Version B panel means within minutes of the
income source changing on 2026-09-21.

**It caught one of six.** The same figures were quoted in five other places, none of them
in the label dictionary, and all five survived the refresh silently:

| Where | What it was |
|---|---|
| `src/indices/normalize.py` | Module docstring explaining why B stays pooled |
| `docs/METHODOLOGY.md` | §4, the evidence for decision D5 |
| `tests/test_copy_matches_artifacts.py` | Its own docstring, and a comment beside `NOT_A_VINTAGE` |

The last row is the uncomfortable one. The guard against stale quoted figures had two stale
quoted figures in it, and would not have noticed if it had a hundred.

This is the project's own recurring defect in a place nobody thought to look. The label
dictionary was hardened; the rest of the repository was left as prose.

### Why it took a year to surface

Because until 2026-09-21 the figures happened to be correct. R1 meant Version B moved
whenever the panel did, and the panel had not moved in a way that touched those numbers.
The income switch moved all of them at once, and only the guarded copy noticed.

### The fix, and the limit on it

A general prose checker is not possible. Most numbers in a docstring are parameters,
thresholds or worked examples with no artifact behind them, and asserting against them would
be noise. What *is* checkable is a shape that only ever means one thing here: a signed
decimal bound to a year, as in "−0,31 (2015)". Every occurrence of that shape anywhere in
the repository is now re-derived from `affordability_ranked.parquet`.

Three details that decide whether it works:

- **Wrapped lines are rejoined first.** `labels.py` breaks the D5 sentence mid-claim, so a
  line-by-line scan saw the first figure and missed the second entirely. A guard that reads
  half a sentence is worse than none, because it looks like coverage.
- **Session-log rows are exempt by shape, not by allowlist.** Those entries record what was
  true on a date; rewriting them would destroy the record. Matching the table row means a
  new log entry needs no maintenance here.
- **The claim's own precision sets the tolerance**, so tightening a sentence to three
  decimals does not silently loosen its guard.

It found the four stale figures in `test_copy_matches_artifacts.py` on its first run, which
is the argument for it.

**What it still does not cover:** any quoted figure whose shape is not "signed decimal plus
year". A municipality count or a price in prose would pass unexamined. Extending it means
adding one pattern per checkable fact rather than attempting a general solution.

**Revisit if:** a second class of artifact-derived figure starts appearing in prose, at
which point the pattern list becomes a registry and deserves the structure that implies.

---

## R16 — The fitted model's first projected year is implausible for every county

**Severity: High. CLOSED 2026-09-25 by removing the fitted models, not by replacing them.**

Found on 2026-09-23 while fixing the Sida 03 chart's geography seam. With the seam gone the
projected line became readable, and what it showed was not usable.

**Every county dropped to roughly a quarter of its last observed value in the first
projected year, then rebounded.** Not some counties. All 21:

| Län | 2024 observed | first projected year |
|---|---|---|
| 01 Stockholm | 7,7 | **1,9** |
| 03 Uppsala | 12,1 | **3,0** |
| 04 Södermanland | 13,5 | **3,2** |
| 06 Jönköping | 17,0 | **4,1** |
| 07 Kronoberg | 19,9 | **4,9** |

Stockholm's full path was 7,7 → 1,9 → 13,1 → 13,8 → 14,5 → 15,0 → 15,5. A dip one year deep
and then undone is the shape of an artefact, not of a projection.

### Why it happened, in two layers

**Layer 1: eleven annual observations cannot support a fitted model.** Expanding origin over
the county panel, fit on 2014→T, project T+1→2024, cutoffs at 2021, 2022 and 2023, giving 63
county-horizons. Control: carry the last observed value forward.

| Series | Fitted | Naive | Fitted wins? |
|---|---|---|---|
| income / price | 9,9 % | **8,4 %** | no |
| income | 16,2 % | **6,7 %** | no, 2,4× worse |
| real rate | 18,2 % | **17,5 %** | no |
| price | 19,5 % | **5,4 %** | no, 3,6× worse |

Whole-index MAPE: naive **25,9 %**, modelling Version C directly 30,5 %, modelling the real
rate and recombining 32,1 %, the shipped pipeline 32,9 %. **No method beat naive.** The
backtest also exposed a second latent defect the register never carried: the price series went
non-positive at two-year horizon and was guarded to `NaN`, so 7,9 % of projections silently
vanished.

**Layer 2: the formula amplifies whatever error survives.** Version C is a reciprocal of
`max(R − π, 0,5)`. Stockholm's real rate ran `0,63 · 0,50 × 9 · 0,77`, at the 0,5 pp floor in
**9 of 11 years**, during which Version C is exactly 200 × (income / price). Yet variance
decomposition of year-on-year changes in `log C` puts the **real rate at 99 %**. Escaping the
floor from 0,5 to 3,2 pp divides C by 6,4, which is what happened: the model put the first
projected real rate at 3,20 pp against a floor of 0,50.

### The statement that closes this risk

> An unconditional projection of Version C is an unconditional projection of Riksbank policy
> six years out, delivered with a confidence interval implying statistical warrant it does not
> have.

That is why naive wins: *"the floor keeps binding"* has been right 9 times in 11. Modelling
Version C directly is never implausible, but its 80 % intervals cover only **37 %** of
outcomes. It fails quietly, which is worse.

### Resolution

Both fitted pipelines (261 and 296 lines) are deleted, along with the compiled statistical
packages they needed, so the refresh toolchain compiles nothing. `src/projection.py` replaces
them: income and price carried forward at documented rates, and the real rate as three
labelled scenarios (0,5 pp floor, last observed, 2,0 pp normalised) rather than a number a
model invents. Sida 03 shows one chart and no tabs, which also dissolves an interface
contradiction the page had carried, since there is no longer a model to recommend.

The first-year sanity check the original recommendation asked for exists as
`tests/test_projection.py::test_no_projection_is_absurd`, but it now guards a construction
that cannot fail it rather than a fit that did, 21 times out of 21.

**This also closed the fragile half of R3 and all of R4.**

**What was traded away, stated plainly.** Confidence bands are gone; the spread between
scenarios is not one. And **someone owns the three scenario values** — 0,5 / last observed /
2,0 is an editorial decision, not a derived fact, and nothing re-derives it. It is documented
as one in `src/projection.py`.

---

## How to use this file

Add a row to the table and a section when something turns up that is real but out of
scope. Move a row to `ACCEPTED` with a one-line reason when a decision is made to live
with it — that is a resolution, not a failure. Delete nothing; a risk that was closed is
worth being able to find later.


---

# Part III — Choropleth map: complete reference

Short explanation: a **Folium + GeoJSON** choropleth (filled municipality polygons) colored by Version C z-score, embedded in **Streamlit** via **streamlit-folium**. The sections below use **Why / What / How / When**; the **entire executable code** needed to reproduce the same map is in the “Complete program listings” section (no out-of-doc references). Boundary data is not source code: you still need the GeoJSON file and Parquet data on disk.

---

## Why

- **Spatial view**: Complements KPIs and tables with *where* risks concentrate across 290 Swedish kommuner.
- **Polygons**: Real boundaries (not only centroid dots) show adjacency and regional patterns.
- **Folium + branca**: Leaflet-based map, `LinearColormap` for continuous z-score → fill color.
- **Diverging palette**: Green–gray–red matches the rest of the SHAI / KRI-style design.

## What

- **Languages / libraries**: Python 3.11, Streamlit, pandas, folium, branca, streamlit-folium.
- **Map behavior**: `folium.GeoJson` with `style_function` / `highlight_function`, `GeoJsonTooltip`, optional `DivIcon` labels for kommun names, zoom-gated label layer, CartoDB Positron (no labels) basemap, scroll zoom disabled for the map widget.

## How

- Load GeoJSON (`@st.cache_data`), merge a metric dict keyed by zero-padded `region_code` into each feature’s `properties`, set `_z` for styling, `LinearColormap` with `vmin`/`vmax` ±2.5, add layer + legend, `folium_static`.
- Join: DataFrame `region_code` and GeoJSON `properties.id` both normalized with `zfill(4)`.

## When

- The production UI calls the renderer after building `df_ranked` (year and risk filters applied on national overview). Labels appear on the map when zoom level reaches the configured minimum (default: zoom 6 with start zoom 5).

---

## Complete program listings (copy as-is)

Save files using the paths shown in each heading so imports match, or change imports to match your layout. Set the working directory to the project root when running Streamlit if paths are relative.

### 1) `pyproject.toml` — relevant dependency block

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "shai"
version = "1.3.0"
description = "Swedish Housing Affordability Indicator (SHAI) — Streamlit dashboard"
readme = "README.md"
requires-python = ">=3.11,<3.12"
dependencies = [
    "streamlit",
    "pandas",
    "numpy",
    "plotly",
    "folium",
    "streamlit-folium",
    "branca",
    "pyarrow",
    "pytest",
]

[tool.setuptools.packages.find]
where = ["src"]
```

**Minimum to run only the map and data prep (subset):** `streamlit`, `pandas`, `numpy`, `folium`, `streamlit-folium`, `branca`, `pyarrow`.

### 2) `src/ui/choropleth.py` — full map module (self-contained; `DIVERGING_SCALE` included here)

```python
"""Choropleth map component using Folium + GeoJSON.

Each municipality polygon is filled by SHAI z-score using a diverging
green-yellow-red scale.  Mirrors the KRI design system approach.
Requires folium, branca, and streamlit-folium.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from branca.element import MacroElement
from folium.features import DivIcon
from folium.template import Template
from streamlit_folium import folium_static

# Diverging 7-stop scale (green → neutral → red). Same as previous src/ui/css.py.
DIVERGING_SCALE = [
    "#2E7D5B", "#5B9E78", "#A8C4A4",
    "#E5E7EB",
    "#E8BE7C", "#D4A03C", "#B94A48",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GEOJSON_PATH = PROJECT_ROOT / "data" / "geo" / "kommuner.geojson"

# Initial map zoom; labels appear only after this many zoom-in steps from here.
_MAP_ZOOM_START = 5
_LABEL_ZOOM_STEPS = 1  # show labels one zoom step earlier for better UX
_LABEL_MIN_ZOOM = _MAP_ZOOM_START + _LABEL_ZOOM_STEPS


class _ZoomGatedKommunLabels(MacroElement):
    """Show the kommun label layer only when map zoom >= label_min_zoom."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function () {
            var map_ = {{ this._parent.get_name() }};
            var labels_ = {{ this.labels_fg.get_name() }};
            var minZ = {{ this.label_min_zoom }};
            function syncKommunLabels() {
                var z = map_.getZoom();
                if (z >= minZ) {
                    if (!map_.hasLayer(labels_)) { labels_.addTo(map_); }
                } else {
                    if (map_.hasLayer(labels_)) { map_.removeLayer(labels_); }
                }
            }
            map_.on("zoomend", syncKommunLabels);
            map_.whenReady(syncKommunLabels);
        })();
        {% endmacro %}
        """
    )

    def __init__(self, labels_fg: folium.FeatureGroup, label_min_zoom: int) -> None:
        super().__init__()
        self._name = "ZoomGatedKommunLabels"
        self.labels_fg = labels_fg
        self.label_min_zoom = int(label_min_zoom)


@st.cache_data(show_spinner=False)
def _load_geojson() -> dict | None:
    if not GEOJSON_PATH.exists():
        return None
    try:
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        st.error(f"Kunde inte läsa kartdata: {exc}")
        return None


def _mean_latlon_from_geometry(geometry: dict) -> tuple[float, float] | None:
    """Mean coordinate of GeoJSON Polygon/MultiPolygon rings (lon,lat → lat,lon)."""
    if not geometry or "coordinates" not in geometry:
        return None
    lats: list[float] = []
    lons: list[float] = []

    def walk(node: object) -> None:
        if isinstance(node, (list, tuple)) and node:
            if isinstance(node[0], (int, float)) and len(node) >= 2:
                lon, lat = float(node[0]), float(node[1])
                lons.append(lon)
                lats.append(lat)
            else:
                for child in node:
                    walk(child)

    walk(geometry["coordinates"])
    if not lats:
        return None
    return sum(lats) / len(lats), sum(lons) / len(lons)


def _label_latlon(feature: dict) -> tuple[float, float] | None:
    props = feature.get("properties") or {}
    gp = props.get("geo_point_2d")
    if isinstance(gp, (list, tuple)) and len(gp) >= 2:
        return float(gp[0]), float(gp[1])
    geom = feature.get("geometry")
    if geom:
        return _mean_latlon_from_geometry(geom)
    return None


def _municipality_label_div(name: str) -> str:
    """Small always-on label; halo keeps text legible on any fill colour."""
    safe = html.escape(name or "", quote=True)
    return (
        '<div style="font-size:7.5px;line-height:1.05;color:#1A1A2E;'
        "text-align:center;font-family:'Source Sans Pro',sans-serif;"
        "font-weight:600;white-space:nowrap;max-width:96px;"
        "overflow:hidden;text-overflow:ellipsis;"
        "text-shadow:-1px -1px 0 #fff,1px -1px 0 #fff,-1px 1px 0 #fff,1px 1px 0 #fff,"
        '0 0 4px #fff;pointer-events:none;">'
        + safe
        + "</div>"
    )


def render_choropleth(
    data: pd.DataFrame,
    value_col: str = "z_c",
    name_col: str = "region_name",
    risk_col: str = "risk_c",
    height: int = 480,
    key: str = "shai_choropleth",
) -> None:
    """Render a full polygon choropleth of Swedish municipalities.

    Args:
        data: One row per municipality with region_code and SHAI values.
        value_col: Column with the numeric z-score to visualize.
        name_col: Column with the municipality name.
        risk_col: Risk class column (lag/medel/hog).
        height: Map height in pixels.
        key: Unique key for the component.
    """
    risk_labels = {"lag": "Låg", "medel": "Medel", "hog": "Hög"}

    # Build per-code lookup with pre-formatted display strings
    sub = data.copy()
    sub["_code"] = sub["region_code"].astype(str).str.zfill(4)

    data_dict: dict[str, dict] = {}
    for _, row in sub.iterrows():
        code = str(row["_code"])
        z_val = float(row.get(value_col, 0))
        vc = float(row.get("version_c", 0))
        rank = row.get("rank_c", "—")
        risk = str(row.get(risk_col, "medel"))
        price = float(row.get("transaction_price_sek", 0))
        income = float(row.get("median_income", 0))
        unemp = float(row.get("unemployment_rate", 0))

        data_dict[code] = {
            "kommun_name": str(row.get(name_col, "") or "").strip(),
            "z_score": z_val,
            "risk_class": risk_labels.get(risk, risk),
            "z_fmt": f"{z_val:+.2f}".replace(".", ","),
            "shai_fmt": f"{vc:.1f}".replace(".", ","),
            "rank_fmt": f"{rank} / {len(sub)}" if rank != "—" else "—",
            "price_fmt": f"{int(price):,}".replace(",", "\u202f") + " SEK",
            "income_fmt": f"{int(income):,}".replace(",", "\u202f") + " SEK",
            "unemp_fmt": f"{unemp:.1f}".replace(".", ",") + " %",
        }

    # Load and enrich GeoJSON
    _raw = _load_geojson()
    if _raw is None:
        st.warning("Kartfilen saknas (data/geo/kommuner.geojson). Kartan kan inte visas.")
        return
    geojson = json.loads(json.dumps(_raw))

    for feat in geojson["features"]:
        code = feat["properties"].get("id", "").zfill(4)
        d = data_dict.get(code, {})
        feat["properties"]["Kommun"] = (
            d.get("kommun_name")
            or feat["properties"].get("kom_namn")
            or code
        )
        feat["properties"]["Riskklass"] = d.get("risk_class", "Saknas")
        feat["properties"]["SHAI Poäng"] = d.get("shai_fmt", "Saknas")
        feat["properties"]["Z-poäng"] = d.get("z_fmt", "Saknas")
        feat["properties"]["Rang"] = d.get("rank_fmt", "Saknas")
        feat["properties"]["Medelpris"] = d.get("price_fmt", "Saknas")
        feat["properties"]["Medianinkomst"] = d.get("income_fmt", "Saknas")
        feat["properties"]["Arbetslöshet"] = d.get("unemp_fmt", "Saknas")
        feat["properties"]["_z"] = d.get("z_score", 0.0)

    # Color scale — diverging green→neutral→red, matching KRI design
    colormap = cm.LinearColormap(
        colors=list(DIVERGING_SCALE),
        vmin=-2.5,
        vmax=2.5,
        caption="SHAI Poäng  ·  Lägre = bättre överkomlighet",
    )

    # Basemap — light polygons only (no OSM placenames: Positron "with labels"
    # shows cities worldwide and reads as unrelated to SHAI).
    m = folium.Map(
        location=[63.0, 17.5],
        zoom_start=_MAP_ZOOM_START,
        tiles="CartoDB.PositronNoLabels",
        prefer_canvas=True,
        zoom_control=True,
        scrollWheelZoom=False,
    )

    def _style(feature: dict) -> dict:
        z_val = feature["properties"].get("_z", 0.0)
        return {
            "fillColor": colormap(z_val),
            "color": "#CCCCCC",
            "weight": 0.5,
            "fillOpacity": 0.82,
        }

    def _highlight(feature: dict) -> dict:
        return {
            "color": "#1A1A2E",
            "weight": 2.0,
            "fillOpacity": 0.95,
        }

    tooltip_css = (
        "font-family: 'Source Sans Pro', sans-serif;"
        "font-size: 13px;"
        "line-height: 1.5;"
        "background: #ffffff;"
        "border: 1px solid #E5E7EB;"
        "border-radius: 6px;"
        "padding: 12px 14px;"
        "box-shadow: 0 4px 16px rgba(0,0,0,0.10);"
        "color: #1A1A2E;"
    )

    folium.GeoJson(
        geojson,
        style_function=_style,
        highlight_function=_highlight,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "Kommun", "Riskklass", "SHAI Poäng", "Z-poäng", "Rang",
                "Medelpris", "Medianinkomst", "Arbetslöshet",
            ],
            aliases=[
                "<b>Kommun</b>", "<b>Riskklass</b>", "SHAI Poäng", "Z-poäng", "Rang",
                "Medelpris", "Medianinkomst", "Arbetslöshet",
            ],
            sticky=True,
            style=tooltip_css,
        ),
    ).add_to(m)

    # Kommun names (GeoJSON `geo_point_2d`); layer is off-map until zoom >= default+2.
    labels = folium.FeatureGroup(name="Kommunnamn", show=False, control=False)
    for feat in geojson["features"]:
        name = (feat.get("properties") or {}).get("Kommun") or ""
        if not str(name).strip():
            continue
        pos = _label_latlon(feat)
        if pos is None:
            continue
        lat, lon = pos
        folium.Marker(
            location=[lat, lon],
            icon=DivIcon(
                html=_municipality_label_div(str(name)),
                icon_size=(100, 14),
                icon_anchor=(50, 7),
                class_name="shai-muni-label",
            ),
            interactive=False,
        ).add_to(labels)
    labels.add_to(m)
    _ZoomGatedKommunLabels(labels, _LABEL_MIN_ZOOM).add_to(m)

    colormap.add_to(m)

    folium_static(m, width=None, height=height)
```

### 3) `stand_alone_choropleth_page.py` — project root, minimal app (map + same `df_ranked` logic as production page)

Use this to run a map-only demo without the rest of the dashboard UI:

```python
"""
Minimal Streamlit entry: only data load, df_ranked build (same rules as
pages/01_Riksoversikt.py), and render_choropleth + caption + expander.

Run from project root:  streamlit run stand_alone_choropleth_page.py
Requires: data/processed/affordability_ranked.parquet,
          data/processed/affordability_municipal.parquet,
          data/geo/kommuner.geojson
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.ui.choropleth import render_choropleth

st.set_page_config(
    page_title="SHAI · Kartdemo",
    page_icon=None,
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None},
)

try:
    with st.spinner("Laddar data..."):
        ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
        municipal = pd.read_parquet("data/processed/affordability_municipal.parquet")
except Exception as e:
    st.error("Kunde inte hämta data. Försök igen senare.")
    st.caption(f"Detaljer: {e}")
    st.stop()

years = sorted(municipal["year"].dropna().unique().tolist(), reverse=True)
if not years:
    st.error("Inga år i data.")
    st.stop()

default_year = int(ranked["year"].iloc[0]) if "year" in ranked.columns else int(years[0])
if default_year not in years:
    default_year = int(years[0])

col_a, col_b = st.columns(2)
with col_a:
    selected_year = st.selectbox("År", options=years, index=years.index(default_year) if default_year in years else 0)
with col_b:
    risk_opts = ("Låg", "Medel", "Hög")
    selected_risks = st.multiselect("Riskklass (tom = alla)", options=risk_opts, default=risk_opts)

# Filter to selected year from municipal panel
mun_year = municipal[municipal["year"] == selected_year].copy()
mun_prev = municipal[municipal["year"] == selected_year - 1].copy()

# Use ranked data for baseline year, else recompute z_c within year
if "year" in ranked.columns and selected_year == int(ranked["year"].iloc[0]):
    df_ranked = ranked.copy()
else:
    df_ranked = mun_year.copy()
    if "version_c" in df_ranked.columns and len(df_ranked) > 0:
        mean_c = df_ranked["version_c"].mean()
        std_c = df_ranked["version_c"].std()
        if std_c and std_c > 0:
            df_ranked["z_c"] = (df_ranked["version_c"] - mean_c) / std_c
        else:
            df_ranked["z_c"] = 0.0
        df_ranked["rank_c"] = df_ranked["z_c"].rank(method="min").astype(int)
        df_ranked["risk_c"] = pd.cut(
            df_ranked["z_c"],
            bins=[-np.inf, -0.67, 0.67, np.inf],
            labels=["lag", "medel", "hog"],
        )
    else:
        st.error("Saknar version_c för z-beräkning.")
        st.stop()

# Risk filter
risk_label_map = {"Hög": "hog", "Medel": "medel", "Låg": "lag"}
if "risk_c" in df_ranked.columns and len(selected_risks) < 3 and len(selected_risks) > 0:
    allowed = [risk_label_map[r] for r in selected_risks if r in risk_label_map]
    df_ranked = df_ranked[df_ranked["risk_c"].isin(allowed)]

st.title("Kartdemo — geografisk fördelning")

if len(mun_year) == 0:
    st.warning("Inga data tillgängliga för den valda perioden.")
    st.stop()

with st.container(border=True):
    st.subheader("Geografisk fördelning")
    st.caption(f"Version C · {selected_year} · KOROPLETKARTA")
    if len(df_ranked) > 0:
        render_choropleth(df_ranked, key="stand_alone_choropleth")
        st.caption(
            "Färgskala: Grön = låg risk (z ≤ −0,67) · Gul = medel risk · Röd = hög risk (z > 0,67)"
        )
    else:
        st.info("Ingen data tillgänglig för kartvisning.")
    with st.expander("Om kartan"):
        st.markdown(
            "Varje kommun visas som ett ifyllt polygon. Färgen baseras på "
            "z-poängen (Version C). Grön = låg risk, röd = hög risk. "
            "Håll musen över en kommun för att se detaljer. "
            "Små kommunnamn visas när du zoomat in. "
        )
```

### 4) Production-style block — data prep, `card_header` (full helper), map + caption + expander

Copy below into a page after you have `ranked`, `municipal`, and `selections` (e.g. from your sidebar), or adapt `selections` to your own state. `inject_css()` is not required for the map to work; the header uses the same HTML structure as the rest of SHAI so it matches if global CSS is loaded.

```python
import numpy as np
import pandas as pd
import streamlit as st

from src.ui.choropleth import render_choropleth


def card_header(title: str, subtitle: str = "", tag: str = "") -> str:
    """Return card header HTML (same as src/ui/components.py in this project)."""
    tag_html = f'<span class="shai-card-tag">{tag}</span>' if tag else ""
    return f"""
    <div class="shai-card-header">
        <div>
            <div class="shai-card-title">{title}</div>
            {"<div class='shai-card-subtitle'>" + subtitle + "</div>" if subtitle else ""}
        </div>
        {tag_html}
    </div>
    """


# After: ranked, municipal = pd.read_parquet(...); selections = { "selected_year": ..., "selected_risks": ... }
selected_year = selections["selected_year"]
selected_risks = selections["selected_risks"]
mun_year = municipal[municipal["year"] == selected_year].copy()
mun_prev = municipal[municipal["year"] == selected_year - 1].copy()

if selected_year == ranked["year"].iloc[0]:
    df_ranked = ranked.copy()
else:
    df_ranked = mun_year.copy()
    if "version_c" in df_ranked.columns and len(df_ranked) > 0:
        mean_c = df_ranked["version_c"].mean()
        std_c = df_ranked["version_c"].std()
        if std_c > 0:
            df_ranked["z_c"] = (df_ranked["version_c"] - mean_c) / std_c
        else:
            df_ranked["z_c"] = 0.0
        df_ranked["rank_c"] = df_ranked["z_c"].rank(method="min").astype(int)
        df_ranked["risk_c"] = pd.cut(
            df_ranked["z_c"],
            bins=[-np.inf, -0.67, 0.67, np.inf],
            labels=["lag", "medel", "hog"],
        )

risk_label_map = {"Hög": "hog", "Medel": "medel", "Låg": "lag"}
if "risk_c" in df_ranked.columns and len(selected_risks) < 3:
    allowed = [risk_label_map[r] for r in selected_risks if r in risk_label_map]
    df_ranked = df_ranked[df_ranked["risk_c"].isin(allowed)]

col_map, _col_hist = st.columns([3, 2])
with col_map:
    with st.container(border=True):
        st.markdown(
            card_header("Geografisk fördelning", f"Version C · {selected_year}", "KOROPLETKARTA"),
            unsafe_allow_html=True,
        )
        if len(df_ranked) > 0:
            render_choropleth(df_ranked, key="rv_choropleth")
            st.caption("Färgskala: Grön = låg risk (z ≤ −0,67) · Gul = medel risk · Röd = hög risk (z > 0,67)")
        else:
            st.info("Ingen data tillgänglig för kartvisning.")
        with st.expander("Om kartan"):
            st.markdown(
                "Varje kommun visas som ett ifyllt polygon. Färgen baseras på "
                "z-poängen (Version C). Grön = låg risk, röd = hög risk. "
                "Håll musen över en kommun för att se detaljer. "
                "Små kommunnamn visas först när du zoomat in två steg från "
                "startläget (zoomkontrollen +). De är förankrade i kartfilens "
                "centrum. Bakgrundskartan visar inga världsstäder — övrig text "
                "kommer från SHAI-data.",
            )
```

If you already define `card_header` elsewhere, remove the duplicate `def card_header` and use your existing function. The full Riksöversikt page in this project also includes KPI row, histogram, and tables in addition to this block.

---

## Data and assets (not code)

- **GeoJSON** path (default): `data/geo/kommuner.geojson` — one feature per kommun, `properties.id` joinable to `region_code` (4-digit string), `kom_namn`, optional `geo_point_2d` as `[lat, lon]` for labels.
- **Parquet** inputs: `data/processed/affordability_ranked.parquet`, `data/processed/affordability_municipal.parquet`. Columns used by the choropleth are built from `render_choropleth` (see docstring in listing §2) — at minimum `region_code`, and for full tooltips `z_c`, `version_c`, `rank_c`, `risk_c`, `region_name`, `transaction_price_sek`, `median_income`, `unemployment_rate`.

---

## Run commands

```text
# From project root (after saving section 3 in this file to stand_alone_choropleth_page.py)
streamlit run stand_alone_choropleth_page.py
```

```text
# Your main Streamlit entry, if different
streamlit run <your_entry_script>.py
```

---

## Troubleshooting

- Missing file warning: ensure `data/geo/kommuner.geojson` is present and `GEOJSON_PATH` resolves to it from `src/ui/choropleth.py` (check `PROJECT_ROOT`).
- All gray / same color: `z_c` missing or join mismatch — align `region_code` with `properties.id`.
- Stale documentation: some older notes describe non-Folium maps; use the listings in this file as the current implementation.

---
