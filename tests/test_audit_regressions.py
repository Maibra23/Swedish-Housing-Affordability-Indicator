"""Regression cases from the October 2026 release audit, one block per page.

Every expected value is computed here from the Parquet artifacts with formulas
written out in this file, never by calling the app's own engines, then compared
with the text the page actually renders. That is what separates this suite from
the unit tests: a page can call a correct engine and still print the wrong
number, the wrong year or the wrong place.

Each case names the audit issue it guards (A-xx, O-x).
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.kontantinsats.margin import default_margin_pp
from src.ui.version import APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app.py")
DATA = ROOT / "data" / "processed"
TIMEOUT = 180

RANKED = pd.read_parquet(DATA / "affordability_ranked.parquet")
PANEL_COUNTY = pd.read_parquet(DATA / "panel_county.parquet")
COUNTY = pd.read_parquet(DATA / "affordability_county.parquet")
YEARS = sorted(RANKED["year"].unique())
FIRST_YEAR, LAST_YEAR = int(YEARS[0]), int(YEARS[-1])

PAGE = {
    "rv": "pages/01_Riksoversikt.py",
    "lj": "pages/02_Lan_jamforelse.py",
    "kd": "pages/03_Kommun_djupanalys.py",
    "ki": "pages/04_Kontantinsats.py",
    "sc": "pages/05_Scenario.py",
    "mt": "pages/06_Metodologi.py",
}


# ── Helpers ──────────────────────────────────────────────────────────


def sv(value: float, decimals: int = 1, signed: bool = False) -> str:
    """The Swedish rendering every page is expected to use."""
    text = f"{value:{'+' if signed else ''},.{decimals}f}"
    return text.replace(",", " ").replace(".", ",").replace("-", "−")


def render(page: str | None = None, year: int | None = None, risks=None, actions=()) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if year is not None:
        at.session_state["shai_selected_year"] = year
    if risks is not None:
        at.session_state["shai_selected_risks"] = risks
    at.run()
    if page:
        at.switch_page(page)
        at.run()
    for act in actions:
        act(at)
        at.run()
    assert not at.exception, at.exception[0].message
    return at


def visible_text(at: AppTest) -> str:
    """Rendered copy with markup stripped and spaces normalised."""
    parts = []
    for kind in ("markdown", "caption", "info", "warning", "error"):
        parts += [str(e.value) for e in getattr(at, kind)]
    text = "\n".join(parts)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S)
    text = re.sub(r"<br\s*/?>|</div>|</p>|</li>|</tr>", "\n", text)
    text = re.sub(r"</td>|</th>", " | ", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"[ \t  ]+", " ", text)


def find(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.S)
    return match.group(1) if match else None


def plotly_specs(at: AppTest) -> list[dict]:
    import json

    return [json.loads(el.proto.spec) for el in at.get("plotly_chart")]


# ── Every page: repeat stability and the footer (A-01, A-14) ─────────


@pytest.mark.parametrize("key", [None, *PAGE], ids=lambda k: k or "start")
def test_page_is_deterministic_and_footer_renders_as_html(key: str | None) -> None:
    first, second = (render(PAGE.get(key)) for _ in range(2))
    assert visible_text(first) == visible_text(second)
    footers = [str(m.value) for m in first.markdown
               if str(m.value).lstrip().startswith('<div class="shai-footer-note"')]
    assert footers, "no footer rendered"
    for footer in footers:
        assert not re.search(r"\n[ \t]*\n", footer), "a blank line turns the footer into a code block"
        assert f"v{APP_VERSION}" in footer, "footer version is not the pyproject version"


def test_stale_year_in_session_falls_back_to_default() -> None:
    """O-1: a year the selector no longer offers must not crash the sidebar."""
    at = render(PAGE["rv"], year=LAST_YEAR + 6, risks=["Okänd"])
    assert at.session_state["shai_selected_year"] == LAST_YEAR


# ── Sida 01 Riksöversikt ─────────────────────────────────────────────


@pytest.mark.parametrize("year", [FIRST_YEAR, 2019, LAST_YEAR])
def test_riksoversikt_kpis_match_recomputation(year: int) -> None:
    rows = RANKED[RANKED["year"] == year]
    text = visible_text(render(PAGE["rv"], year))
    assert find(r"Genomsnittligt SHAI\s*([\d ]+,\d)\s*% av inkomsten", text) == sv(rows["version_c"].mean())
    assert find(r"Högriskkommuner\s*(\d+)\s*av", text) == str(int((rows["risk_c"] == "hog").sum()))
    assert find(r"K/T-kvot \(genomsnitt\)\s*([\d,]+)\s*genomsnitt", text) == sv(rows["kt_ratio"].mean(), 2)


def test_first_year_shows_no_fabricated_change() -> None:
    """A-05: with no prior year there is no delta to print."""
    text = visible_text(render(PAGE["rv"], FIRST_YEAR))
    assert not re.search(r"[▲▼◆] [+−-]0,0", text)
    assert "första året, ingen jämförelse" in text


def test_ranking_tables_use_swedish_numbers_and_order() -> None:
    """A-06: decimal comma, true minus, order from z_c."""
    text = visible_text(render(PAGE["rv"], LAST_YEAR))
    worst = text.split("Sämst överkomlighet (topp 15)")[1].split("Bäst överkomlighet")[0]
    expected = list(RANKED[RANKED["year"] == LAST_YEAR].nlargest(15, "z_c")["region_name"])
    assert re.findall(r"\n\d+ \| ([^|]+?) \|", worst) == expected
    assert not re.search(r"\| -?\d+\.\d+ \|", text), "dot decimal in a table"


def test_filtered_tables_say_they_are_filtered() -> None:
    """A-17."""
    text = visible_text(render(PAGE["rv"], LAST_YEAR, risks=["Hög"]))
    assert "filter: Hög" in text


# ── Sida 02 Länsjämförelse ───────────────────────────────────────────


@pytest.mark.parametrize("year", [FIRST_YEAR, 2015, 2022, LAST_YEAR])
def test_lan_ranking_and_disagreement_match_recomputation(year: int) -> None:
    rows = RANKED[RANKED["year"] == year]
    means = rows.groupby("lan_code")["version_c"].mean()
    names = COUNTY[COUNTY["year"] == year].set_index("lan_code")["region_name"]
    text = visible_text(render(PAGE["lj"], year))
    # A cost share: #1 is the cheapest county.
    assert find(rf"Länsranking {year}.*?\n1 \| ([^|]+?) \|", text) == names[means.idxmin()]
    disagree = int((rows["risk_b"] != rows["risk_c"]).sum())
    assert find(r"den är det för (\d+) av", text) == str(disagree)


def test_lan_ranking_shows_both_county_definitions() -> None:
    """A-02: the kommun mean and the county-level value, side by side."""
    text = visible_text(render(PAGE["lj"], LAST_YEAR))
    mean = RANKED[(RANKED["year"] == LAST_YEAR) & (RANKED["lan_code"] == "01")]["version_c"].mean()
    level = COUNTY[(COUNTY["year"] == LAST_YEAR) & (COUNTY["lan_code"] == "01")]["version_c"].iloc[0]
    assert "Snitt av kommunerna" in text and "Länsnivå" in text
    assert re.search(rf"Stockholms län \| {re.escape(sv(mean, 2))} \| {re.escape(sv(level, 2))} \|", text)


def test_empty_county_selection_keeps_the_rest_of_the_page() -> None:
    """A-16."""
    at = render(PAGE["lj"], actions=[lambda a: a.multiselect(key="lj_counties").set_value([])])
    text = visible_text(at)
    assert "Inga län valda" in text and "ROBUSTHET" in text and "Länsranking" in text


def test_log_axis_is_labelled() -> None:
    """A-09."""
    for spec in plotly_specs(render(PAGE["lj"])):
        axis = spec["layout"].get("yaxis", {})
        if axis.get("type") == "log":
            assert "logaritmisk" in axis["title"]["text"]


# ── Sida 03 Kommunanalys ─────────────────────────────────────────────


@pytest.mark.parametrize("kommun,year", [("Stockholm", LAST_YEAR), ("Åsele", LAST_YEAR), ("Gotland", 2019)])
def test_kommun_kpis_match_artifact(kommun: str, year: int) -> None:
    row = RANKED[(RANKED["region_name"] == kommun) & (RANKED["year"] == year)].iloc[0]
    at = render(PAGE["kd"], year, actions=[lambda a: a.selectbox(key="kd_kommun_select").set_value(kommun)])
    text = visible_text(at)
    assert find(r"SHAI \(Version C\)\s*([\d,]+)\s*% av inkomsten", text) == sv(row["version_c"])
    assert find(r"Medianinkomst\s*([\d ]+)\s*SEK", text) == sv(row["median_income"], 0)


def test_projection_title_and_scenario_label_name_county_and_year() -> None:
    """A-03, A-04: the lines are the county's, from its last index year."""
    at = render(PAGE["kd"], actions=[lambda a: a.selectbox(key="kd_kommun_select").set_value("Åsele")])
    text = visible_text(at)
    assert "Projektion för Västerbottens län" in text
    names = [t.get("name", "") for s in plotly_specs(at) for t in s["data"]]
    assert any(f"Nivå {LAST_YEAR}," in n for n in names), names
    assert not any("Dagens nivå" in n for n in names)


def _cost_share(income: float, price: float, rate_pct: float, year: int) -> float:
    """Version C written out: 85 % loan, 30 % deduction, 2 % amortisation from
    June 2016, two earners."""
    amort = 0.0 if year < 2016 else 0.02 * 7 / 12 if year == 2016 else 0.02
    return 100 * 0.85 * price * (rate_pct / 100 * 0.7 + amort) / (2 * income)


def test_projection_first_year_matches_formula() -> None:
    hist = COUNTY[COUNTY["lan_code"] == "01"].sort_values("year").iloc[-1]
    rates = COUNTY.groupby("year")["mortgage_rate"].median()
    at = render(PAGE["kd"])
    lines = {t["name"].split(",")[0]: t["y"][1] for s in plotly_specs(at) for t in s["data"] if " %" in t.get("name", "")}
    income, price = hist["median_income"] * 1.03, hist["transaction_price_sek"] * 1.02
    year = LAST_YEAR + 1
    for label, rate in (("Lägsta nivån", rates.min()), (f"Nivå {LAST_YEAR}", hist["mortgage_rate"]), ("Stress", 6.0)):
        assert lines[label] == pytest.approx(_cost_share(income, price, rate, year), rel=1e-6)


# ── Sida 04 Kontantinsats ────────────────────────────────────────────


def _regime(price: float, income: float, rate: float, sav: float, margin: float) -> dict:
    """Lättnad 2026: 10 % down, 2 % amortisation above 70 % LTV, 1 % above 50 %."""
    cash = price * 0.10
    loan = price - cash
    amort = 0.02 if loan / price > 0.70 else 0.01 if loan / price > 0.50 else 0.0
    annual = loan * (max(rate + margin, 0.0) + amort)
    return {"cash": cash, "years": cash / (income * sav), "monthly": annual / 12}


@pytest.mark.parametrize(
    "year,par,sav,margin",
    [(LAST_YEAR, False, 10, None), (2016, False, 10, None), (LAST_YEAR, True, 25, 3.0), (2016, False, 5, 0.0)],
    ids=["default-2024", "default-2016", "par-max", "negative-rate-no-margin"],
)
def test_kontantinsats_matches_formula(year: int, par: bool, sav: int, margin: float | None) -> None:
    """None leaves the margin slider at its default: SCB's observed margin for the year."""
    def setup(at: AppTest) -> None:
        if par:
            radio = at.radio(key="ki_household_type")
            radio.set_value(radio.options[1])
        at.slider(key="ki_savings_slider").set_value(sav)
        if margin is not None:
            at.slider(key="ki_bank_margin_slider").set_value(margin)

    if margin is None:
        margin = default_margin_pp(year)
    row = RANKED[(RANKED["region_name"] == "Stockholm") & (RANKED["year"] == year)].iloc[0]
    expect = _regime(row["transaction_price_sek"], row["median_income"] * (2 if par else 1),
                     row["policy_rate"] / 100, sav / 100, margin / 100)
    text = visible_text(render(PAGE["ki"], year, actions=[setup]))
    assert find(r"Kontantinsats \(idag\)\s*([\d ]+)\s*SEK", text) == sv(expect["cash"], 0)
    assert find(r"År att spara \(idag\)\s*([\d,]+)\s*år", text) == sv(expect["years"])
    assert find(r"Månadskostnad \(idag\)\s*([\d ]+)\s*SEK", text) == sv(expect["monthly"], 0)


def test_kontantinsats_uses_one_currency_and_times_sign() -> None:
    """A-13."""
    text = visible_text(render(PAGE["ki"]))
    assert not re.search(r"\d kr\b", text)
    assert not re.search(r"\d+,\d+x\b|\d+x ", text)


# ── Sida 05 Scenariosimulator ────────────────────────────────────────


def _scenario_value(row: pd.Series, rate=0.0, income=0, price=0) -> float:
    return _cost_share(
        row["median_income"] * (1 + income / 100),
        row["transaction_price_sek"] * (1 + price / 100),
        max(row["mortgage_rate"] + rate, 0.5),
        int(row["year"]),
    )


@pytest.mark.parametrize(
    "shocks",
    [{}, {"rate": 2.0}, {"rate": -2.0, "price": 25}, {"rate": 5.0, "income": -10, "price": -25}],
    ids=["base", "plus2", "cut", "extremes"],
)
def test_scenario_matches_formula(shocks: dict) -> None:
    keys = {"rate": "sc_rate_slider", "income": "sc_income_slider", "price": "sc_price_slider"}
    acts = [lambda a, k=keys[n], v=v: a.select_slider(key=k).set_value(v) for n, v in shocks.items()]
    row = PANEL_COUNTY[(PANEL_COUNTY["region_name"] == "Stockholms län") & (PANEL_COUNTY["year"] == LAST_YEAR)].iloc[0]
    text = visible_text(render(PAGE["sc"], actions=acts))
    assert find(r"Basfall SHAI\s*([\d,]+)", text) == sv(_scenario_value(row))
    assert find(r"Scenario SHAI\s*([\d,]+)", text) == sv(_scenario_value(row, **shocks))


def test_scenario_defaults_to_stockholm_and_presets_reset() -> None:
    """A-12, plus the preset round trip."""
    at = render(PAGE["sc"])
    assert at.selectbox(key="sc_county_select").value == "Stockholms län"
    at.button(key="sc_preset_cycle").click().run()
    assert at.select_slider(key="sc_rate_slider").value == 3.0
    at.button(key="sc_preset_reset").click().run()
    assert at.select_slider(key="sc_rate_slider").value == 0.0


def test_surface_axes_end_where_the_sliders_end() -> None:
    """A-07."""
    surface = next(s for s in plotly_specs(render(PAGE["sc"])) if any(t["type"] == "contour" for t in s["data"]))
    assert surface["layout"]["xaxis"]["range"] == [-25, 25]
    assert surface["layout"]["yaxis"]["range"] == [-2.0, 5.0]


def test_scenario_copy_fixes() -> None:
    """A-11, A-19."""
    text = visible_text(render(PAGE["sc"]))
    assert "Flytta ett reglage" in text
    assert not re.search(r"realränta är bara [\d,]+ %", text)


# ── Sida 06 Metodologi ───────────────────────────────────────────────


@pytest.mark.parametrize("year", [FIRST_YEAR, LAST_YEAR])
def test_methodology_lists_every_limitation(year: int) -> None:
    text = visible_text(render(PAGE["mt"], year))
    found = sorted({int(n) for n in re.findall(r"\*\*F(\d+)\*\*", text)})
    assert found == list(range(1, 19))


# ── Copy that must not come back (A-10, A-15) ────────────────────────


SPLIT_COMPOUNDS = ("Län jämförelse", "Kommun djupanalys", "Kontantinsats analys",
                   "Högrisk kommuner", "SHAI poäng", "Medel risk")


@pytest.mark.parametrize("key", [None, *PAGE], ids=lambda k: k or "start")
def test_no_split_compounds_or_templated_symbols(key: str | None) -> None:
    text = visible_text(render(PAGE.get(key)))
    for phrase in SPLIT_COMPOUNDS:
        assert phrase not in text, phrase
    assert "—" not in text, "em dash in visible copy"
    assert "→" not in text, "arrow in visible copy"
    assert " & " not in text, "ampersand in visible copy"
