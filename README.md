# SHAI, Swedish Housing Affordability Indicator

A Streamlit dashboard measuring how affordable housing is across Sweden's 290 kommuner
and 21 län, built from open SCB, Riksbanken and Kolada data. It answers one question:
**how much of a normal household's income does it take to carry a typical house loan
here, in this year, compared with everywhere else in Sweden?**

Version 1.3.0. Python 3.11. Index period 2014 to 2024.

The answer is a share of income. In 2024 a two-earner household on Lidingö's median
income would pay 60,5 % of it a year to carry an 85 % loan on the mean house there; in
Åsele, 3,7 %.

## When to use it

| If you want to | Start on |
|---|---|
| See which parts of Sweden are most strained | **Riksöversikt**, a map of all 290 kommuner |
| Test whether a ranking survives a change of formula | **Länsjämförelse**, the 21 län under both formulas that can disagree |
| Follow one kommun and see where it could go | **Kommunanalys**, its history plus a projection to 2030 |
| Work out the cash and the years needed to buy | **Kontantinsats**, all five Swedish mortgage regimes |
| Test a rate, income or price shock | **Scenariosimulator**, one län under assumptions you set |
| Check a formula, a source or a limitation | **Metodologi** |

A year and an optional risk filter sit in the sidebar and follow you between pages.

## What you will see

Set the sidebar year to **2024**, the latest complete year and the app's default, and
every page should show exactly this. Use it to check your install.

| Page | In 2024 |
|---|---|
| **Riksöversikt** | Mean index **16,3** % of income, **84 of 290** kommuner at hög risk, mean K/T **1,40**. Least affordable: Lidingö, Danderyd, Solna. Most affordable: Åsele, Sorsele, Ragunda |
| **Länsjämförelse** | Two tabs. The Robusthet panel at the foot shows C classing **84** kommuner hög and B classing **57**; B disagrees with C for **73 of 290**. The comparison expander puts Version C at **1,17×** Version A |
| **Kommunanalys** | Select Stockholm: index **44,2** % of income, income **413 600 SEK**, K/T **1,23**. Its county projects to **21,8 / 35,5 / 44,0** in 2025 at the low, current and stress mortgage rates |
| **Kontantinsats** | Stockholm, one income, 10 % sparkvot, and the bank margin SCB observed that year (0,8 pp): **859 700 SEK** down, **20,8 years** to save, **41 449 SEK** a month. Switch to Bostadsrätt and it moves to län level: **421 400 SEK** and **10,5 years** |
| **Scenariosimulator** | Opens on Stockholms län: baseline **35,9** % of income. Push the rate slider **+2 pp** and it rises to **45,9**, up 28 % |
| **Metodologi** | The three formulas, the F1 to F18 limitation register, no interactive data |

Those figures are re-derived from the shipped artifacts by
`tests/test_readme_figures.py`, so they cannot quietly go stale.

## The index

| | Question it answers |
|---|---|
| **Bankversion (A)** | What does the loan cost in gross interest, as a share of income? |
| **Makroversion (B)** | How much pressure is the market under, relative to its own history? |
| **Kassaflödesversion (C)** | What does the household actually pay out: interest after the 30 % deduction, plus required amortisation? Recommended. |

Versions A and C price the same loan: 85 % of the kommun's mean small-house price, at
SCB's mean rate on new household mortgages across all fixation periods, carried by two
earners on the kommun's median income. Both are a percentage of that income, so **higher
is worse**, the same direction as B.

**Kassaflödesversion (C) runs the site.** The map, the risk classes, the KPI row, the
projection and the simulator all read C. Makroversion (B) is the only formula that can
rank the country differently. Bankversion (A) ranks identically to C by construction,
because the rate and the amortisation rule are national, so it shows the size of the
deduction and amortisation rather than a second opinion: C is **1,17×** A in 2024.

<details>
<summary><b>Why the formula changed in October 2026</b></summary>

Until October 2026 Version C was `income / (price × max(policy rate − KPI, 0,5))`. It had
three problems an economist would name at once. Households pay the mortgage rate, not the
policy rate, and a negative policy rate never meant a negative mortgage rate. KPI prices
mortgage interest, so a rate rise lifted measured inflation by itself; the Riksbank
targets KPIF for that reason. And because the real rate sat at or below zero for most of
2015 to 2023, the 0,5 pp floor bound in nine of eleven years, which made a +2 pp shock cut
the index by 72 % and the national mean fall 36 % in the one year the floor released.

Switching to the mortgage rate and KPIF inside the same formula would not have fixed it:
mortgage rate minus KPIF is still under 0,5 pp in seven of the eleven years. The cure was
the structure. A cash-flow share multiplies by the rate instead of dividing by it, so it
needs no floor, and the same +2 pp shock now raises Stockholms län's cost by 28 %.

Within each year nothing on the map moved: every municipality-year kept its rank and risk
class under all three versions, because the old and new values are reciprocals up to a
national constant. Levels, the projection and the simulator changed. METHODOLOGY section 3
has the full comparison.

</details>

## What it does not do

**It does not predict.** Sida 03 projects six years ahead under three stated mortgage
rates. The spread between them is the distance between assumptions, not a confidence
interval. The evidence behind that choice is R16 in `docs/APP_REFERENCE.md` (Part II).

**It is not mortgage advice.** Prices are kommun means, never your income or a specific
property. The rate is the market average for new loans; a household on a fixed rate
meets a new one only when it refixes (F12).

**It does not separate saving from spending.** Amortisation is cash paid out, but it
builds the household's equity. Version A shows the interest burden without it (F18).

**It does not rank absolute cost.** Risk classes are relative to the year you selected,
so "hög risk" means strained against this year's peers, never worse than 2014.

## Data

SCB supplies income, transaction and apartment prices, the K/T ratio, population,
construction, KPI, KPIF and household mortgage rates. Riksbanken supplies the policy rate,
used only on Sida 04, and Kolada unemployment. Everything is read from committed Parquet
files, so the app makes no API calls at startup.

**The index stops at 2024** because every formula divides by median inkomst, and 2024 is
the last year SCB has published it. Prices and unemployment already reach 2025 and are
used wherever they stand alone.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py                # http://localhost:8501
```

Refreshing from the source APIs needs the pipeline extra as well:

```bash
pip install -e ".[pipeline]"
python scripts/refresh_data.py                   # fetch, rebuild, recompute, reproject
python scripts/refresh_data.py --no-fetch        # rebuild from cached raw data
python scripts/refresh_data.py --no-projection   # skip the projection step
```

Commit the regenerated files in `data/processed/`. Run `python scripts/audit.py` to check
the shipped artifacts independently, and `pytest -q` for the suite. The suite includes a
browser pass (`tests/test_browser_render.py`) that opens every page in Chromium at desktop
and phone width; install it with `pip install -e ".[dev]"` and
`python -m playwright install chromium`, or skip it with `SHAI_SKIP_BROWSER=1`. For a quick rerun
while working, `pytest -m "not browser and not network"` skips the browser and live-API
tests and takes about a minute; run the full suite before deploying.

## Contributing

Through [GitHub
issues](https://github.com/Maibra23/Swedish-Housing-Affordability-Indicator/issues). A
number that looks wrong is the most valuable report here: name the page, the year and the
region, and say what you expected.

Pull requests branch off `main` and keep the suite green. Anything touching a formula, a
normalisation rule or a regime needs a test, because these carry an orientation contract,
rank 1 = best and higher = worse for every version, that is easy to invert by accident. User-facing copy
lives in `src/ui/labels.py`, and methodology changes need a matching edit to
`docs/METHODOLOGY.md`.

## License

MIT, copyright (c) 2026 Maibra23. See [`LICENSE`](LICENSE). The data is not covered: it
belongs to SCB, Riksbanken and Kolada under their own terms.

## Documentation

To use or change the app:

| File | Contents |
|---|---|
| `docs/ENGINE.md` | How a number reaches the screen: the pipeline, the formulas, and what each page computes |
| `docs/METHODOLOGY.md` | Formulas, variables, sources, limitations |
| `docs/APP_REFERENCE.md` | Part I: what each page is for and how to read its results. Part II: known risks carried deliberately. Part III: map implementation reference |
| `docs/DEPLOYMENT.md` | Deployment, data refresh, file inventory |
| `docs/DESIGN_SYSTEM.md` | Design tokens, chart rules, component patterns |
| `docs/ADR/` | Decision records, including what was rejected and why |
