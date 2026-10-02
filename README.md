# SHAI, Swedish Housing Affordability Indicator

A Streamlit dashboard measuring how affordable housing is across Sweden's 290 kommuner
and 21 län, built from open SCB, Riksbanken and Kolada data. It answers one question:
**how much housing can a normal income buy here, in this year, compared with everywhere
else in Sweden?**

Version 1.3.0. Python 3.11. Index period 2014 to 2024.

The answer is an index, not a price. In 2024 Åsele scored 75 and Lidingö 4,6.

## When to use it

| If you want to | Start on |
|---|---|
| See which parts of Sweden are most strained | **Riksöversikt**, a map of all 290 kommuner |
| Test whether a ranking survives a change of formula | **Län jämförelse**, the 21 län under both formulas that can disagree |
| Follow one kommun and see where it could go | **Kommun djupanalys**, its history plus a projection to 2030 |
| Work out the cash and the years needed to buy | **Kontantinsats**, all five Swedish mortgage regimes |
| Test a rate, income or price shock | **Scenariosimulator**, one län under assumptions you set |
| Check a formula, a source or a limitation | **Metodologi** |

A year and an optional risk filter sit in the sidebar and follow you between pages.

## What you will see

Set the sidebar year to **2024**, the latest complete year and the app's default, and
every page should show exactly this. Use it to check your install.

| Page | In 2024 |
|---|---|
| **Riksöversikt** | Mean index **23,0** points, **84 of 290** kommuner at hög risk, mean K/T **1,40**. Least affordable: Lidingö, Danderyd, Solna. Most affordable: Åsele, Sorsele, Ragunda |
| **Län jämförelse** | Two tabs. The Robusthet panel at the foot shows C classing **84** kommuner hög and B classing **57**; B disagrees with C for **73 of 290**. The comparison expander puts the inflation adjustment at **4,71×** |
| **Kommun djupanalys** | Select Stockholm: index **6,2**, income **413 600 SEK**, K/T **1,23**. Its county projects to **12,0 / 7,8 / 3,0** in 2025 under the floor, current and normalised rate scenarios |
| **Kontantinsats** | Stockholm, one income, 10 % sparkvot, 1,7 pp margin: **859 700 SEK** down, **20,8 years** to save, **47 252 SEK** a month. Switch to Bostadsrätt and it moves to län level: **421 400 SEK** and **10,5 years** |
| **Scenariosimulator** | Stockholms län baseline **7,71**. Push the rate slider **+2 pp** and it falls to **2,14**, down 72 % |
| **Metodologi** | The three formulas, the F1 to F16 limitation register, no interactive data |

Those figures are re-derived from the shipped artifacts by
`tests/test_readme_figures.py`, so they cannot quietly go stale.

## The index

| | Question it answers |
|---|---|
| **Bankversion (A)** | Can a household carry the monthly cost at today's nominal rate? |
| **Makroversion (B)** | How much pressure is the market under, relative to its own history? |
| **Realversion (C)** | Bankversion adjusted for inflation, using the real rate. Recommended. |

**Realversion (C) runs the site.** The map, the risk classes, the KPI row, the projection
and the simulator all read C. Makroversion (B) is the only formula that can rank the
country differently. Bankversion (A) ranks identically to C by construction, so it shows
the size of the inflation adjustment rather than a second opinion — C divided by A is
**4,71×** in 2024, and that is the whole difference between them.

That reading does not hold in every year. Both formulas floor their rate, and in 2015 to
2023 at least one floor binds, which makes the same quotient an artefact rather than a
correction — 0,20× for seven straight years, being 0,1 divided by 0,5. Sida 02 derives
the factor from the year you select and says which of the two it is looking at. The
per-year table is in `docs/METHODOLOGY.md` section 3.

## What it does not do

**It does not predict.** Sida 03 projects six years ahead under three stated real rate
assumptions. The spread between them is the distance between assumptions, not a
confidence interval. The evidence behind that choice is R16 in `docs/OPEN_RISKS.md`.

**It is not mortgage advice.** Prices are kommun means, never your income or a specific
property.

**It does not rank absolute cost.** Risk classes are relative to the year you selected,
so "hög risk" means strained against this year's peers, never worse than 2014.

## Data

SCB supplies income, transaction and apartment prices, the K/T ratio, population,
construction and CPI. Riksbanken supplies the policy rate and Kolada unemployment.
Everything is read from committed Parquet files, so the app makes no API calls at startup.

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
the shipped artifacts independently, and `pytest -q` for the suite.

## Contributing

Through [GitHub
issues](https://github.com/Maibra23/Swedish-Housing-Affordability-Indicator/issues). A
number that looks wrong is the most valuable report here: name the page, the year and the
region, and say what you expected.

Pull requests branch off `main` and keep the suite green. Anything touching a formula, a
normalisation rule or a regime needs a test, because these carry an orientation contract,
rank 1 = best and higher z = worse, that is easy to invert by accident. User-facing copy
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
| `docs/APP_GUIDE.md` | What each page is for and how to read its results |
| `docs/DEPLOYMENT.md` | Deployment, data refresh, file inventory |
| `docs/OPEN_RISKS.md` | Known risks carried deliberately |
| `docs/DESIGN_SYSTEM.md` | Design tokens, chart rules, component patterns |
| `docs/CHOROPLETH_MAP_REFERENCE.md` | Map implementation reference |
| `docs/ADR/` | Decision records, including what was rejected and why |

Records of how the app was built rather than what it does now:
`docs/REVITALIZATION_PLAN.md`, `docs/OPTIMIZATION_PLAN.md`, `docs/DEVIATIONS.md`,
`docs/PRD.md` and `docs/PLAYBOOK.md`.

`docs/archive/` holds superseded analyses. It is kept for provenance, is
not maintained, and should not be read as current guidance.
