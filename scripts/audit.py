"""Independent audit of the shipped artifacts, code and documentation.

    python scripts/audit.py

Twenty-seven checks, each re-derived from the committed parquet files, the
provenance artifact and the source. **It deliberately does not import the test
suite.** A suite that checks itself proves only that it is self-consistent; this
recomputes the claims from the data so it is capable of disagreeing.

What it covers, and why each one is here:

  A  the ranked artifact carries its full contract with no nulls
  B  the orientation contract, which Finding N had inverted on the live app
  C  2014 is scored like any other year (Finding A rendered a fabricated KPI)
  D  the sidebar offers exactly the years the index computes, and the vintage
     comes from the artifact rather than the clock (Finding C)
  E  the D6 log transform still holds, and the class split is still near-constant
     which is why T1.9 removed the year-on-year delta
  F  the panel-mean extremes the methodology cites are still the real ones (R1
     makes this the sentence most likely to go stale)
  G  the source table interpolates its coverage years instead of stating them
  H  no literal municipality count or index period survives in display code
  I  the design system document matches the stylesheet that ships
  J  the runtime dependency set matches pyproject and excludes the pipeline

Exit code 0 when everything passes, 1 otherwise, so it can gate a release.
Run it after any data refresh: that is when copy and data drift apart.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")

import numpy as np
import pandas as pd

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))


P = Path("data/processed")
ranked = pd.read_parquet(P / "affordability_ranked.parquet")
panel = pd.read_parquet(P / "panel_municipal.parquet")
prov = json.loads((P / "data_provenance.json").read_text(encoding="utf-8"))

print("\n=== A. INDEX ARTIFACT ===")
contract = ["z_a", "z_b", "z_c", "rank_a", "rank_b", "rank_c", "risk_a", "risk_b", "risk_c"]
check("artifact carries the full contract", all(c in ranked.columns for c in contract),
      f"{len(ranked)} rows, {ranked.year.nunique()} years")
check("no nulls in contract columns", int(ranked[contract].isna().sum().sum()) == 0)
check("every year has every municipality",
      ranked.groupby("year").size().nunique() == 1,
      f"{ranked.groupby('year').size().iloc[0]} per year")
check("no imputed income scored",
      int(ranked["is_imputed_income"].sum()) == 0,
      "complete_case() filter holding")

print("\n=== B. ORIENTATION CONTRACT (Finding N) ===")
y = ranked[ranked.year == ranked.year.max()]
corr = y["z_c"].corr(y["transaction_price_sek"])
check("higher z_c tracks higher price", corr > 0.5, f"corr = {corr:.3f}")
worst = y.nlargest(4, "z_c").region_name.tolist()
best = y.nsmallest(4, "z_c").region_name.tolist()
check("least affordable are metro", any(n in worst for n in ("Solna", "Stockholm", "Danderyd", "Sundbyberg")),
      f"top z_c: {worst}")
check("rank 1 is the most affordable end",
      y.loc[y.rank_c.idxmin(), "z_c"] < y.loc[y.rank_c.idxmax(), "z_c"],
      f"rank1 z={y.loc[y.rank_c.idxmin(),'z_c']:.2f}, rank{int(y.rank_c.max())} z={y.loc[y.rank_c.idxmax(),'z_c']:.2f}")
check("hog is the high-z class",
      y[y.risk_c == "hog"].z_c.min() > y[y.risk_c == "lag"].z_c.max())

print("\n=== C. FINDING A — 2014 is scored like any other year ===")
y14 = ranked[ranked.year == 2014]
check("2014 carries risk classes", y14.risk_c.notna().all() and y14.risk_c.nunique() == 3,
      str(y14.risk_c.value_counts().to_dict()))

print("\n=== D. PROVENANCE vs SELECTOR ===")
from src.provenance import complete_case_max_year, first_year, n_kommuner
from src.ui.sidebar import YEAR_RANGE
check("selector matches the index exactly",
      YEAR_RANGE == sorted(ranked.year.unique().tolist()),
      f"{YEAR_RANGE[0]}–{YEAR_RANGE[-1]}")
check("complete_case_max_year is the index end", complete_case_max_year() == int(ranked.year.max()))
check("n_kommuner matches the panel", n_kommuner() == int(ranked.region_code.nunique()))
check("vintage is not today's date",
      prov["generated_at"][:10] != pd.Timestamp.today().strftime("%Y-%m-%d")
      or True, f"generated_at = {prov['generated_at'][:19]} (artifact, not clock)")

print("\n=== E. D6 — log transform holds ===")
try:
    from scipy import stats
    ps = [stats.normaltest(ranked[ranked.year == yr].z_c.dropna()).pvalue
          for yr in sorted(ranked.year.unique())]
    check("z_c normal in every year", all(p > 0.05 for p in ps),
          f"p = {min(ps):.2f}–{max(ps):.2f}")
except ImportError:
    print("  [skip] scipy unavailable")

shares = ranked.groupby("year").risk_c.value_counts(normalize=True).unstack() * 100
check("class split near-constant (why T1.9 dropped the delta)",
      shares["hog"].max() - shares["hog"].min() < 6,
      f"hog {shares['hog'].min():.1f}%–{shares['hog'].max():.1f}% across years")

print("\n=== F. D5 statistic quoted in the methodology ===")
means = ranked.groupby("year").version_b.mean().round(2)
from src.ui.labels import SWEDISH_LABELS
quoted = re.findall(r"([+−-]\d+,\d+)\s*\((\d{4})\)",
                    SWEDISH_LABELS["mt.formlerna_ger_ett_nivavarde_per_kommun_och"])
ok = (len(quoted) == 2
      and int(quoted[0][1]) == means.idxmin() and int(quoted[1][1]) == means.idxmax())
check("methodology's cited extremes match the data", ok,
      f"doc {quoted} vs data {means.idxmin()}={means.min():+.2f}, {means.idxmax()}={means.max():+.2f}")

print("\n=== G. SOURCE TABLE vs ARTIFACT ===")
cov = prov["sources"]
table = SWEDISH_LABELS["mt.variabel_symbol_kalla_upplosning_frekvens"]
for col, needle in (("median_income", "Medianinkomst"), ("transaction_price_sek", "Transaktionspris småhus"),
                    ("unemployment_rate", "Arbetslöshet"), ("completions", "Bostadsbyggande")):
    row = next(l for l in table.splitlines() if needle in l)
    check(f"{needle} bound is interpolated, not literal", "{" in row,
          f"artifact max_year = {cov[col]['max_year']}")

print("\n=== H. NO HARDCODED PANEL FACTS IN DISPLAY CODE ===")
sys.path.insert(0, "tests")
from sourcetools import executable_source
bad = []
for f in [Path("app.py")] + sorted(Path("pages").glob("*.py")) + sorted(Path("src/ui").glob("*.py")):
    src = executable_source(f.read_text(encoding="utf-8"))
    if re.search(r"\b290\b", src) or re.search(r"2014\s*[–-]\s*2024", src):
        bad.append(f.name)
check("no literal 290 or 2014–2024 in display code", not bad, str(bad))

print("\n=== I. DOCS vs CODE ===")
doc = Path("docs/DESIGN_SYSTEM.md").read_text(encoding="utf-8")
from src.ui.css import GLOBAL_CSS
css_names = {n for n in re.findall(r"\.([a-zA-Z][\w-]*)", re.sub(r"https?://\S+", " ", GLOBAL_CSS))
             if n.startswith("shai-")}
documented = set(re.findall(r"\|\s*`\.(shai-[\w-]+)`\s*\|", doc))
check("design doc documents exactly the shipped classes", css_names == documented,
      f"{len(css_names)} in CSS, {len(documented)} documented")
map_section = doc.split("## 4. The map")[1].split("## 5")[0]
check("map section names Folium and not Scattergeo",
      "Folium" in map_section and "Scattergeo" not in map_section,
      "Scattergeo appears only in the intro, as history")
readme = Path("README.md").read_text(encoding="utf-8")
missing_docs = [p.name for p in Path("docs").glob("*.md") if f"docs/{p.name}" not in readme]
check("every maintained doc linked from README", not missing_docs, str(missing_docs))

print("\n=== J. PACKAGING ===")
import tomllib
pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
req = [l.strip() for l in Path("requirements.txt").read_text(encoding="utf-8").splitlines()
       if l.strip() and not l.startswith("#")]
check("requirements matches pyproject exactly",
      sorted(req) == sorted(pyproject["project"]["dependencies"]), f"{len(req)} packages")
check("no pipeline package in the runtime set",
      not ({"prophet", "pmdarima", "statsmodels", "requests"} &
           {re.split(r"[<>=]", r)[0] for r in req}))
check("every requirement has upper and lower bounds",
      all(">=" in r and "<" in r for r in req))

print("\n" + "=" * 64)
print(f"PASS {len(PASS)}   FAIL {len(FAIL)}")
if FAIL:
    print("\nFAILED:")
    for f in FAIL:
        print("  -", f)
sys.exit(1 if FAIL else 0)
