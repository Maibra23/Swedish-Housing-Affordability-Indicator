# Analysis guide: Kontantinsats, Scenariosimulator, and the three SHAI versions

What these two pages are for, how to read them correctly, where they currently
mislead a user, and what to do about it. Written 2026-09-18 against the committed
artifacts, with every figure re-derived from them rather than quoted from memory.
Section 6, on the two charts that shipped out of these recommendations, added
2026-09-21 on the same basis.

---

## 1. Kontantinsats analys (Sida 04)

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

## 2. Scenariosimulator (Sida 05)

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

## 3. The three SHAI versions: what they mean and whether they matter here

### What each one is

| Version | Formula | Reads as |
|---|---|---|
| **A, Bankversion** | `I / (P * R)` | Can a household carry this at today's nominal rate? A traditional bank view. |
| **B, Makroversion** | `0.35*z(P/I) + 0.25*z(R) + 0.20*z(U) + 0.20*z(pi)` | How much macro pressure is this market under, relative to the panel's history? A supervisor's view. |
| **C, Realversion** | `I / (P * max(R - pi, 0.5))` | Version A corrected for inflation, using the real rate. |

A and C are ratios where **higher is better**. B is a weighted sum of z-scores
where **higher is worse**. That sign difference is the single most error-prone
thing in the codebase and has produced real defects more than once.

### Why three rather than one

Because they disagree, and the disagreement is informative. A and C diverge
exactly when inflation is far from zero, which is precisely when a nominal
reading misleads. B can carry a time trend that A and C cannot, because its
z-scores are pooled across the whole panel rather than computed within each year.
Its panel mean runs from -0.37 in 2015 to +0.86 in 2023, tracking the rate cycle.
A and C, normalised within year, are silent about whether Sweden as a whole got
better or worse.

### Are they important in our context? An honest answer

**Version C is the product. A and B are close to vestigial.**

Verified against the code:

- `version_c` is consumed by the choropleth map, the risk classification, the
  KPI row, the forecasts, the data tables and the scenario simulator.
- `version_a` appears in exactly one file: the Län jämförelse comparison tab.
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

---

## 4. Can the variables be changed or updated?

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

## 5. The result interpretation system (implemented)

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
the Par rows inherit the multiplier bug described in section 4, so their LTI is
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

## 6. The two charts, checked against the design system and the data

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

### 6.1 Reachability, Sida 04. Fits.

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

### 6.2 The rate and inflation surface, Sida 05. Four defects.

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

The bold 10.6 at the origin is the baseline this document quotes in section 2.
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

### 6.3 Why this drifted

`tests/test_design_system_doc.py` checks the CSS class inventory in both
directions, `tests/test_css_naming.py` rejects a class outside the `shai-`
convention, and `tests/test_no_inline_copy.py` keeps strings out of pages. The
chart layer has none of that. No test asserts that a figure goes through
`get_chart_layout`, that its colours come from `COLORS` or `DIVERGING_SCALE`, or
that the toolbar setting is consistent. The design system is guarded everywhere
except where this drift happened, which is why it happened here and not in the
stylesheet.

Recorded as R14 in `docs/OPEN_RISKS.md`.

### 6.4 What to change, in order. All six done.

1. **Fix the caption.** Done, and it no longer asserts a direction in prose at
   all: the floor is drawn, per 2.
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

### 6.5 The guard, and what it found

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

## 7. Summary of recommended work

| # | Change | Page | Status |
|---|---|---|---|
| 1 | Warn when LTI exceeds a lendable ratio | 04 | **Done.** Delivered by the interpretation panel |
| 2 | Move the F15 inflation caveat next to the rate slider | 05 | **Done.** Fires only when the rate moved without CPI |
| 3 | State that the simulator's number is not the map's number | 05 | **Done.** Scale note in the panel |
| 4 | Explain the deposit versus monthly cost trade-off | 04 | **Done.** Computed per region, so it states the direction that applies here |
| 6 | Flag that the savings rate is a share of gross income | 04 | **Done.** Caveat travels with the savings figure |
| 8 | Surface the single-income assumption | 04 | **Done.** Panel names it and points at the Par control |
| 5 | Say what A and B are for, and that C drives the site | 02 | Open. Copy change |
| 7 | Display or remove the unused A and B risk columns | 02, pipeline | Open. Six dead artifact columns |
| 9 | Apply scenario shocks across all kommuner, not one län | 05 | Open. Large, scope separately |
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

Section 6 is implemented in full. Items 13 to 19 are done and the two
charts no longer ship as section 6 described them.
