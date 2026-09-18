# Analysis guide: Kontantinsats, Scenariosimulator, and the three SHAI versions

What these two pages are for, how to read them correctly, where they currently
mislead a user, and what to do about it. Written 2026-09-18 against the committed
artifacts, with every figure re-derived from them rather than quoted from memory.

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

## 5. Summary of recommended work

| # | Change | Page | Effort | Value |
|---|---|---|---|---|
| 1 | Warn when LTI exceeds a lendable ratio | 04 | Small | High. Stops the most serious misreading on the site |
| 2 | Move the F15 inflation caveat next to the rate slider | 05 | Small | High. Intercepts a wrong conclusion at the moment it forms |
| 3 | State that the simulator's number is not the map's number | 05 | Small | Medium |
| 4 | Explain the deposit versus monthly cost trade-off | 04 | Small | Medium |
| 5 | Say what A and B are for, and that C drives the site | 02 | Small | Medium |
| 6 | Relabel savings rate as a share of gross income | 04 | Trivial | Medium |
| 7 | Display or remove the unused A and B risk columns | 02, pipeline | Medium | Medium. Removes six dead artifact columns |
| 8 | Reconsider the single-household default | 04 | Trivial | Medium |
| 9 | Apply scenario shocks across all kommuner, not one län | 05 | Large | High, scope separately |

Items 1 and 2 are the two that change what a user concludes, rather than how
comfortable they are while concluding it. If only two things are done, do those.
