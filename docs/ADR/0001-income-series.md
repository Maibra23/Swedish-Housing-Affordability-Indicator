# ADR 0001: Which income series SHAI divides by

**Status:** Accepted
**Date:** 2026-09-21
**Supersedes:** the undocumented choice of `HE0110G/TabVX4bDispInkN`

Every affordability figure on this site is a ratio with income underneath it.
Version A, Version B and Version C all divide by `median_income`; so does the
loan-to-income ratio on Sida 04, the years-to-save figure beside it, and the
reachability chart under that. Which income series is therefore not a detail of
the data layer. It is the denominator of the product.

This record exists because that choice was never written down, and because when
someone finally checked it, it was the wrong one.

---

## The defect this replaces

`fetch_income` requested `HE/HE0110/HE0110G/TabVX4bDispInkN` with
`Hushallstyp = E90`, whose title is *Disponibel inkomst för hushåll, samtliga
hushåll*. That is **median household disposable income**.

`docs/METHODOLOGY.md`, the Metodologi page, the caption under the Kontantinsats
KPI strip and limitation F14 all described **individual gross earned income**
(*sammanräknad förvärvsinkomst*). Two axes apart: household rather than
individual, disposable rather than gross.

The consequence was not only a documentation defect. `pages/04_Kontantinsats.py`
multiplied the figure by two for the "Par" case. On an individual median that is
correct. On a household median that already blends single- and dual-earner
households it produces an income no household has, and it understated the couple
debt ratio by about a quarter: Stockholm 2024 showed 7.2 where the honest
individual reading is 9.4.

**No test could have caught it.** The suite checks that a column exists, that it
covers 290 municipalities, that rank 1 is the best. A wrong-but-well-formed
series satisfies all of that. The same reasoning appears in
`docs/ANALYSIS_GUIDE.md` section 4 about a table that was *not* adopted: pointing
the pipeline at AM0106 `Kommun17g` would fetch cleanly, rebuild the panel and
keep the suite green while changing the denominator from "income of people who
live here" to "salary of people employed by this council".

---

## Candidates considered

Checked live against the SCB API on 2026-09-18 and again on 2026-09-21.

### Rejected: AM0106 `Kommun17g`

*Genomsnittlig månadslön inom kommuner*, 2007 to 2025. The year range is right
and the release is recent, which is exactly what makes it dangerous. The phrase
is "inom kommuner": it measures **the municipal sector as an employer**, not
residents of a municipality.

| Evidence from the table itself | Value | What it means |
|---|---|---|
| Employees, Riket 2024 | 854 100 | Sweden's workforce is about 5.2 million. This is the municipal payroll |
| Employees, Stockholm 2024 | 45 300 | Stockholm has well over 400 000 employed residents |
| Region list | includes `Kommunalförbund` | A municipal federation is an employer, not a place |

"Stockholm" here means people employed *by* Stockholm kommun wherever they live:
teachers, nurses, care staff, administrators. A public-sector payroll series,
heavily weighted to one set of occupations, reporting gross monthly salary rather
than annual income. It would not extend the index; it would make every ratio
uninterpretable.

### Rejected for the index: HE0110M `MistTab1`

*Individuell disponibel inkomst exkl. kapitalinkomst*, preliminary monthly
statistics, 312 regions, median published, 2025M01 onward. Genuinely current and
at the right geography, and a full calendar-year 2025 figure is computable today.

Two objections, one fatal for splicing:

1. Different concept again: disposable, and excluding capital income.
2. **The series do not overlap.** `MistTab1` begins 2025M01; the annual tables end
   2024. There is no year in which both exist, so the ratio between them cannot
   be calibrated from data. Splicing would mean assuming a conversion factor,
   which is the same class of unverifiable assumption this project removed when
   it stopped forward-filling income at 3 %/yr.

Usable as a clearly separated preliminary nowcast, labelled as its own series and
shown beside the index rather than inside it. Not usable as the denominator.

### Accepted: HE0110A `SamForvInk1`

*Sammanräknad förvärvsinkomst för boende i Sverige hela året*, 312 regions,
median published, 1999 to 2024.

Selected with:

| Variable | Value | Why this one |
|---|---|---|
| `Kon` | `1+2` | Both sexes. Either alone silently narrows the population |
| `Alder` | `tot20+` | `tot16+` folds in 16 to 19 year olds, whose near-zero earnings pull the median down about 5 % without describing anyone who buys a home |
| `Inkomstklass` | `TOT` | All income classes, not a bracket |
| `ContentsCode` | `HE0110J8` | The median. `HE0110J7` is the mean, which the top of the distribution drags |

Four reasons it is the right denominator:

1. **It is the series the project already claimed to use.** Adopting it makes
   the existing documentation true, rather than rewriting documentation to match
   an accident.
2. **It matches the thresholds it is compared against.** Finansinspektionen's
   4.5x amorteringskrav trigger and ordinary bank loan-to-income practice are
   both defined on gross income. Dividing a loan by *disposable* income and
   comparing the result to 4.5x was a category error independent of the
   multiplier.
3. **It makes the couple multiplier valid.** The unit of analysis is one person,
   so combining two of them into a household is arithmetic the definition
   licenses. See `src/kontantinsats/income.py`.
4. **It has deeper history**, 1999 rather than 2011.

---

## What it cost, measured rather than estimated

The earlier estimate, taken from a three-municipality sample, was that income
would fall about 23 % roughly uniformly and rankings would shift modestly. **The
uniformity part was wrong**, and it is worth recording why: the three
municipalities sampled happened to sit at one end of the distribution.

Across all 3 190 panel rows, the ratio of the old household series to the new
individual one runs **1.10 to 1.77**, with a median of 1.31 in 2024. It also has
a time trend: 1.74 in 2011 falling to 1.31 in 2024, because individual gross
earnings grew about 51 % over the period while median household disposable income
grew about 15 % and actually fell in nominal terms in 2022 and 2023.

Measured effect of the switch:

| | Effect |
|---|---|
| Panel median income, 2024 | 439 200 → 338 250 SEK, **-23.0 %** |
| Rows changing risk class | **161 of 3 190, 5.0 %** |
| Mean absolute rank shift | 7.1 places; 24.4 % of rows moved more than 10 |
| Largest single rank shift | 36 places |

The re-ranking is **systematic and interpretable**, which is the strongest
evidence that the new series is measuring what it claims. Dual-earner commuter
municipalities worsen (Vaggeryd -31 places, Kävlinge -29, Habo -27, Lerum -27,
Staffanstorp -26); northern industrial and university towns improve (Gällivare
+30, Kiruna +29, Karlstad +27, Östersund +27, Umeå +25). That is precisely the
difference between "what two median earners make here" and "what the median
household of all shapes takes home here".

Headline figures get more severe, not less. Stockholm 2024 on one income moves
from LTI 14.5 to **18.7**, and its housing cost share from 106 % to **137 %**.
The couple case moves from an understated 7.2 to **9.4**.

---

## What was deliberately not changed

**The panel still starts in 2011.** `SamForvInk1` reaches back to 1999, eleven
years further. Taking all of it would have widened the panel as a side effect of
fixing a definition and bundled two changes an auditor would then have to
separate. The index cannot move earlier regardless, because it needs the policy
rate and that starts in 2014. The floor is pinned as `min_year` in
`src/data/variable_contracts.py`; deepening the panel is available and is its own
decision.

**The index still ends in 2024.** This was a correctness question, not a
freshness one. No candidate moves the index past 2024, because SCB has not
published 2025 municipal income on the annual tables.

---

## How this is prevented from recurring

A decision record alone would not have prevented it: the old choice was
*documented*, in the sense that the methodology described a series. What was
missing was anything that compared the description to the data.

1. `src/data/variable_contracts.py` states each variable's table, its exact value
   selections, its unit of analysis, its concept, and the operations it does and
   does not survive.
2. `fetch_income` asserts the live table's title and value texts against the
   contract before it will fetch. A renamed table or a re-used content code now
   fails a refresh instead of quietly changing a number.
3. `tests/test_variable_contracts.py` pins hand-verified benchmark values, checks
   the panel's income is an individual-sized magnitude, and asserts that nothing
   outside `income.py` scales `median_income` by a household size.
4. `data_provenance.json` now records the table path and the filter set alongside
   the coverage years, so a figure on screen traces to a specific SCB query
   without anyone reading Python.

Each guard was run against the defect it is meant to catch before being kept.

---

## Related

- `docs/ANALYSIS_GUIDE.md` section 4, the investigation this came out of
- `docs/METHODOLOGY.md` limitation F14, on what the Par case models
- `src/kontantinsats/income.py`, the only place an individual income becomes a
  household one
