"""Does the data mean what the project says it means?

Every other test in this suite checks shape or orientation: a column exists, the
panel has 290 municipalities, rank 1 is the best. All of them passed for a year
while `median_income` held **household disposable** income and every page, the
methodology document and the couple multiplier on Sida 04 described **individual
gross** income. The column had the right name, the right dtype, the right region
count and the right year range. It was the wrong number.

`docs/ANALYSIS_GUIDE.md` section 4 makes the same point about a table that was
*not* adopted: repointing the pipeline at AM0106 `Kommun17g` would fetch
cleanly, rebuild the panel and keep the suite green, while silently changing the
denominator from "income of people who live here" to "salary of people employed
by this council". Nothing in the suite could have told the difference.

This file is the missing half. It checks meaning from two directions:

- **Against the committed data**, offline, on every run. Hand-verified
  benchmarks catch a selection that changed even when the table name did not.
- **Against the live source**, when the network allows. A title or value-text
  change at SCB is how a substitution arrives, and the fetch path asserts the
  same thing, so a refresh fails rather than quietly succeeding.

It also guards the one piece of arithmetic that the definition licenses: nothing
outside `src/kontantinsats/income.py` may scale `median_income` by a household
size, because that is the operation that was valid in form and wrong in premise.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from src.data.variable_contracts import CONTRACTS, INCOME_CONTRACT

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


# ---------------------------------------------------------------------------
# Against the committed data
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("benchmark", INCOME_CONTRACT.benchmarks, ids=lambda b: f"{b.region_code}-{b.year}")
def test_income_matches_hand_verified_benchmarks(benchmark) -> None:
    """Values a human read off statistikdatabasen, pinned.

    A benchmark is the only check that survives the source changing underneath
    the code *and* the code changing underneath the source. It is also the
    cheapest way to notice that a filter moved: switching `Alder` from `tot20+`
    to `tot16+` leaves every shape assertion intact and moves Riket by about
    5 %, which this catches and nothing else would.
    """
    cache = RAW / "HE0110_income.parquet"
    if not cache.exists():
        pytest.skip("data/raw is gitignored; run scripts/refresh_data.py to populate it")

    raw = pd.read_parquet(cache)
    row = raw[
        (raw["Region_code"] == benchmark.region_code)
        & (raw["Tid_code"] == str(benchmark.year))
    ]
    assert len(row) == 1, (
        f"expected exactly one row for {benchmark.region_code} in {benchmark.year}, "
        f"found {len(row)}. More than one means the selection stopped being unique."
    )
    actual = float(row["value"].iloc[0])
    assert actual == pytest.approx(benchmark.value, abs=0.05), (
        f"{benchmark.region_code} {benchmark.year}: contract says {benchmark.value} "
        f"tkr ({benchmark.note}), the cache holds {actual}. Either SCB revised the "
        f"series, or a filter in the contract changed what is being selected."
    )


def test_the_panel_income_is_an_individual_magnitude() -> None:
    """A household median and an individual median are told apart by size.

    The series this replaced ran 1.3 to 1.7 times higher. A bound this loose
    cannot mistake one for the other, and does not need revising when incomes
    grow.
    """
    panel = pd.read_parquet(PROCESSED / "panel_municipal.parquet")
    latest = panel[(panel["year"] == 2024) & panel["median_income"].notna()]
    median = float(latest["median_income"].median())
    assert 250_000 <= median <= 450_000, (
        f"2024 median municipal income is {median:,.0f} SEK. Individual gross "
        f"earned income sits near 340 000; the household disposable series this "
        f"replaced sat near 440 000. This number is in neither band, so check "
        f"what fetch_income is pointed at."
    )


def test_provenance_records_the_definition_not_only_the_vintage() -> None:
    """Coverage years say when a number is from, never what it is."""
    import json

    payload = json.loads((PROCESSED / "data_provenance.json").read_text(encoding="utf-8"))
    assert "definitions" in payload, (
        "the provenance artifact records coverage but not definitions; re-run "
        "scripts/refresh_data.py"
    )
    income = payload["definitions"]["median_income"]
    assert income["table_path"] == INCOME_CONTRACT.table_path
    assert income["filters"] == {code: list(values) for code, values in INCOME_CONTRACT.filters}
    assert income["unit_of_analysis"] == "individual resident"


# ---------------------------------------------------------------------------
# The operation the definition licenses
# ---------------------------------------------------------------------------

#: Multiplying or dividing `median_income`, or a variable holding it, by
#: something. The point is not to parse Python but to make the pattern that was
#: the bug visible if it comes back anywhere new.
SCALES_INCOME = re.compile(
    r"(median_income|_individual_income|individual_income)\s*[*/]|"
    r"[*/]\s*(household_multiplier|household_size|earners)\b"
)

#: Where scaling an individual income into a household income is allowed, and
#: the test that proves the accessor is exercised.
INCOME_SCALING_ALLOWED = {
    "src/kontantinsats/income.py",
    "tests/test_variable_contracts.py",
}


def test_only_one_module_turns_an_individual_income_into_a_household_one() -> None:
    """The multiplier was valid arithmetic on an invalid premise.

    Keeping it in one function means the premise is stated where the arithmetic
    happens, rather than being a fact about a parquet column that a page has to
    remember.
    """
    offenders: list[str] = []
    for path in sorted(ROOT.glob("pages/*.py")) + sorted(ROOT.glob("src/**/*.py")):
        rel = str(path.relative_to(ROOT))
        if rel in INCOME_SCALING_ALLOWED:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            if SCALES_INCOME.search(line):
                offenders.append(f"{rel}:{line_no} {line.strip()}")
    assert not offenders, (
        "median_income is scaled outside src/kontantinsats/income.py: "
        + "; ".join(offenders)
        + ". Route it through household_income(), which documents what the "
        "result models."
    )


def test_the_accessor_refuses_a_scaling_that_is_not_a_household() -> None:
    """A fractional or zero household is a caller doing something else."""
    from src.kontantinsats.income import household_income

    assert household_income(400_000, 2) == 800_000
    for bad in (0, -1, 1.5):
        with pytest.raises(ValueError):
            household_income(400_000, bad)


# ---------------------------------------------------------------------------
# Against the live source
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("contract", list(CONTRACTS.values()), ids=lambda c: c.name)
def test_the_live_scb_table_still_matches_its_contract(contract) -> None:
    """The check that would have caught the original defect at fetch time.

    Skipped without a network, because a test that fails on a train is a test
    people learn to ignore. `fetch_income` performs the same assertion on every
    refresh, where the network is a precondition rather than a nuisance, so the
    guarantee does not depend on this test running.
    """
    requests = pytest.importorskip("requests")
    from src.data.scb_client import _get_table_metadata
    from src.data.variable_contracts import assert_table_matches

    try:
        meta = _get_table_metadata(contract.table_path)
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
        pytest.skip(f"SCB unreachable: {exc}")

    assert_table_matches(meta, contract)


def test_the_contract_check_rejects_a_table_that_changed() -> None:
    """The negative control. A guard nobody has seen fail is a comment."""
    from src.data.variable_contracts import assert_table_matches

    wrong_title = {
        "title": "Genomsnittlig månadslön inom kommuner efter kommun och kön",
        "variables": [],
    }
    with pytest.raises(ValueError, match="does not contain"):
        assert_table_matches(wrong_title, INCOME_CONTRACT)

    reused_code = {
        "title": INCOME_CONTRACT.expected_title_contains[0]
        + " för boende i Sverige hela året",
        "variables": [
            {"code": "Kon", "values": ["1+2"], "valueTexts": ["totalt"]},
            {"code": "Alder", "values": ["tot20+"], "valueTexts": ["totalt 20+ år"]},
            {"code": "Inkomstklass", "values": ["TOT"], "valueTexts": ["totalt"]},
            {
                "code": "ContentsCode",
                "values": ["HE0110J8"],
                "valueTexts": ["Medelinkomst, tkr"],
            },
        ],
    }
    with pytest.raises(ValueError, match="now means"):
        assert_table_matches(reused_code, INCOME_CONTRACT)
