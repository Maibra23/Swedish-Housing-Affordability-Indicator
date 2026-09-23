"""What each fetched variable *means*, stated once, in a form a test can check.

The suite tests shape and orientation: that a column exists, that it has 290
regions, that rank 1 is the best. Nothing tested what a column **means**, and on
2026-09-21 that gap turned out to be load-bearing. `fetch_income` had been
pointed at `HE0110G/TabVX4bDispInkN`, which returns median *household
disposable* income, while `docs/METHODOLOGY.md`, the Metodologi page, the
Kontantinsats caption and the couple multiplier on Sida 04 all described
*individual gross earned* income. Every test passed. Every displayed number was
built on a denominator two definitions away from the one the site claimed.

That class of defect survives a green run because a wrong-but-well-formed series
is indistinguishable from a right one by shape alone. The same reasoning is why
`docs/APP_GUIDE.md` section 7 rejects AM0106 `Kommun17g`: it would fetch
cleanly, the panel would rebuild, the suite would stay green, and the denominator
would quietly have become "salary of people employed by this council" instead of
"income of people who live here".

A contract closes it from two directions at once:

- **Against the source.** `expected_title_contains` and `expected_value_texts`
  are asserted against the live PxWeb metadata, so SCB repointing, renaming or
  re-coding a table fails a test instead of silently changing a number.
- **Against the committed data.** `benchmarks` pin values a human checked by hand
  on the SCB site. A magnitude that moves 30 % because the selection changed
  fails even when the table name did not.

And `forbidden_operations` records the arithmetic a series will not survive,
which is the part no schema can express. The couple multiplier was valid
arithmetic on an invalid premise; the premise now has somewhere to live.

Used by `src/data/scb_client.py` at fetch time and by
`tests/test_variable_contracts.py` at test time.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Benchmark:
    """One value a human verified against the published source.

    Args:
        region_code: SCB region code.
        year: Calendar year.
        value: The value as published, in the table's own unit.
        note: Where it was read from, so the next person can re-check it.
    """

    region_code: str
    year: int
    value: float
    note: str


@dataclass(frozen=True)
class VariableContract:
    """What one fetched variable is, and what may be done with it.

    Args:
        name: The panel column this feeds.
        table_path: PxWeb path, the part after the API base URL.
        filters: Value selections that define the series. Every one of these
            narrows the population or the concept, so each is part of the
            definition rather than a performance choice.
        expected_title_contains: Fragments that must appear in the live table
            title. Chosen to be the words that distinguish this table from the
            one next to it, not merely words it happens to contain.
        expected_value_texts: `variable code -> value code -> text fragment`.
            Asserts the codes still select what they selected when this was
            written, which a title check cannot see.
        unit_of_analysis: Who or what one row counts.
        concept: Which income, price or rate concept this is.
        statistic: Median, mean, index, and so on.
        unit: The unit the source publishes in.
        permitted_operations: What the rest of the codebase may do with it.
        forbidden_operations: What it must not be subjected to, and why.
        benchmarks: Hand-verified values.
        min_year: Earliest year to request, or None for everything the table
            holds. Set where a source reaches further back than the panel does,
            so that widening the panel stays a deliberate decision rather than a
            side effect of changing a table.
    """

    name: str
    table_path: str
    filters: tuple[tuple[str, tuple[str, ...]], ...]
    expected_title_contains: tuple[str, ...]
    expected_value_texts: tuple[tuple[str, str, str], ...]
    unit_of_analysis: str
    concept: str
    statistic: str
    unit: str
    permitted_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    benchmarks: tuple[Benchmark, ...]
    min_year: int | None = None

    def as_overrides(self) -> dict[str, list[str]]:
        """The filters in the shape `_build_query` wants."""
        return {code: list(values) for code, values in self.filters}

    def year_selection(self, available: list[str]) -> list[str] | None:
        """The Tid values to request, given what the table offers.

        Args:
            available: Every `Tid` value code the table publishes.

        Returns:
            The subset at or after `min_year`, or None when the contract does
            not pin a floor and the whole range should be fetched.
        """
        if self.min_year is None:
            return None
        return [v for v in available if v[:4].isdigit() and int(v[:4]) >= self.min_year]


def assert_table_matches(meta: dict, contract: VariableContract) -> None:
    """Fail the fetch if SCB's table no longer matches its contract.

    A table path is not a definition. SCB can rename a table, retire a content
    code or re-use one, and a fetch would still succeed and still return well
    formed numbers of the wrong thing. That is precisely how `median_income`
    spent a release cycle holding household disposable income while every page
    called it individual gross.

    Checking the title and the selected value texts costs one request that was
    already being made, and turns an invisible substitution into a failed
    refresh.

    Args:
        meta: PxWeb table metadata, as returned by `_get_table_metadata`.
        contract: The contract this table is expected to satisfy.

    Raises:
        ValueError: If the title or any selected value no longer matches.
    """
    title = meta.get("title", "")
    for fragment in contract.expected_title_contains:
        if fragment.casefold() not in title.casefold():
            raise ValueError(
                f"{contract.name}: {contract.table_path} is titled {title!r}, "
                f"which does not contain {fragment!r}. The table may have been "
                f"repointed or replaced. Check it against "
                f"src/data/variable_contracts.py before trusting the numbers."
            )

    by_code = {v["code"]: v for v in meta.get("variables", [])}
    for var_code, value_code, expected_text in contract.expected_value_texts:
        var = by_code.get(var_code)
        if var is None:
            raise ValueError(
                f"{contract.name}: {contract.table_path} no longer has a "
                f"{var_code!r} variable."
            )
        pairs = dict(zip(var["values"], var["valueTexts"]))
        if value_code not in pairs:
            raise ValueError(
                f"{contract.name}: {var_code}={value_code!r} is gone from "
                f"{contract.table_path}."
            )
        if expected_text.casefold() not in pairs[value_code].casefold():
            raise ValueError(
                f"{contract.name}: {var_code}={value_code!r} now means "
                f"{pairs[value_code]!r}, not {expected_text!r}. The code was "
                f"re-used for a different series."
            )


INCOME_CONTRACT = VariableContract(
    name="median_income",
    table_path="HE/HE0110/HE0110A/SamForvInk1",
    filters=(
        ("Kon", ("1+2",)),
        ("Alder", ("tot20+",)),
        ("Inkomstklass", ("TOT",)),
        ("ContentsCode", ("HE0110J8",)),
    ),
    expected_title_contains=(
        "Sammanräknad förvärvsinkomst",
        "boende i Sverige",
    ),
    expected_value_texts=(
        ("Kon", "1+2", "totalt"),
        ("Alder", "tot20+", "20+"),
        ("Inkomstklass", "TOT", "totalt"),
        ("ContentsCode", "HE0110J8", "Medianinkomst"),
    ),
    unit_of_analysis="individual resident",
    concept="gross earned income before tax, excluding capital income",
    statistic="median",
    unit="tkr per year",
    permitted_operations=(
        "compare across regions within a year",
        "compare across years in nominal terms",
        "divide a price or a loan by it to form a ratio",
        "multiply by a household size to model a specific household, because "
        "the unit of analysis is one person",
    ),
    forbidden_operations=(
        "do not describe it as disposable income: it is before tax and transfers",
        "do not describe it as household income: it counts one person",
        "do not compare its level against HE0110G/TabVX4bDispInkN, which ran "
        "about 1.3 to 1.7 times higher depending on the municipality and year",
    ),
    benchmarks=(
        Benchmark("00", 2024, 359.2, "Riket, verified against statistikdatabasen 2026-09-21"),
        Benchmark("0180", 2024, 413.6, "Stockholm"),
        Benchmark("1280", 2024, 336.5, "Malmö"),
        Benchmark("2463", 2024, 298.9, "Åsele"),
        Benchmark("0162", 2024, 510.3, "Danderyd, the panel's highest"),
        Benchmark("2425", 2024, 313.9, "Dorotea, near the panel's lowest"),
    ),
    # The table reaches back to 1999, eleven years further than the panel. Taking
    # all of it would have widened the panel as a side effect of fixing a
    # definition, and bundled two changes an auditor would then have to separate.
    # The index cannot move earlier regardless: it needs the policy rate, which
    # starts 2014. Deepening the panel is available and is its own decision.
    min_year=2011,
)

TRANSACTION_PRICE_CONTRACT = VariableContract(
    name="transaction_price_sek",
    table_path="BO/BO0501/BO0501B/FastprisSHRegionAr",
    filters=(
        ("Fastighetstyp", ("220",)),
        ("ContentsCode", ("BO0501C2",)),
    ),
    expected_title_contains=("Försålda småhus",),
    expected_value_texts=(
        ("Fastighetstyp", "220", "permanent"),
        ("ContentsCode", "BO0501C2", "Köpeskilling, medelvärde"),
    ),
    unit_of_analysis="transaction",
    concept="purchase price for a permanent small house, excluding leasehold",
    statistic="arithmetic mean",
    unit="tkr",
    permitted_operations=(
        "compare across regions within a year",
        "form a price to income ratio",
    ),
    forbidden_operations=(
        "do not call it a median: this content code publishes the mean, which a "
        "few large sales can move",
        "do not read it as an apartment price: småhus only, see "
        "fetch_bostadsratt_price for bostadsrätt",
    ),
    benchmarks=(),
)

CPI_CONTRACT = VariableContract(
    name="cpi_yoy_pct",
    table_path="PR/PR0101/PR0101A/KPI2020M",
    filters=(("ContentsCode", ("00000807", "00000804")),),
    expected_title_contains=("Konsumentprisindex", "2020=100"),
    expected_value_texts=(
        ("ContentsCode", "00000804", "Årsförändring"),
        ("ContentsCode", "00000807", "skuggindex"),
    ),
    unit_of_analysis="national basket",
    concept="consumer price index, 2020 = 100, and its year on year change",
    statistic="index and percentage change",
    unit="index points and percent",
    permitted_operations=(
        "subtract the year on year change from a nominal rate to get a real rate",
    ),
    forbidden_operations=(
        "do not mix the index and the change: 00000807 is the level, 00000804 "
        "is the percentage change, and they are fetched together",
    ),
    benchmarks=(),
)

#: Every contract, by panel column. `fetch_all` and the tests iterate this.
CONTRACTS: dict[str, VariableContract] = {
    c.name: c
    for c in (INCOME_CONTRACT, TRANSACTION_PRICE_CONTRACT, CPI_CONTRACT)
}
