"""The county ranking table on Sida 02.

Moved out of the page when it gained a second value column. The table shows the
county as Sida 02 defines it (the unweighted mean of its kommuner) beside the
county-level value Sida 03 and Sida 05 use (county income over county price), so
a reader who meets both numbers sees that they are two definitions, not an error.
"""

from __future__ import annotations

import pandas as pd

from src.ui.data_table import Column, render_table
from src.ui.formatting import format_dec
from src.ui.labels import L


def county_ranking_html(
    county_means: pd.DataFrame,
    county_level: pd.DataFrame,
    year: int,
    value_column: str,
    tab_name: str,
) -> str:
    """HTML for one year's ranking, #1 = best affordability in every tab.

    Args:
        county_means: Per county and year, the mean of kommun values, with
            `lan_code`, `region_name`, `year` and the version columns.
        county_level: `affordability_county.parquet`.
        year: The selected year.
        value_column: "version_c" or "version_b".
        tab_name: The tab's name, for the subtitle.

    Returns:
        The table HTML, or an empty string when the year has no rows.
    """
    rows = county_means[county_means["year"] == year].merge(
        county_level.loc[county_level["year"] == year, ["lan_code", value_column]]
        .rename(columns={value_column: "county_level"}),
        on="lan_code",
        how="left",
    )
    if rows.empty:
        return ""
    # All three versions read higher-is-worse since A and C became cost shares,
    # so all sort ascending and #1 is the cheapest county. Sorting against the
    # orientation once put the worst county at #1 under a caption saying the
    # opposite; `tests/test_ui_affordances.py` guards it.
    rows = rows.sort_values(value_column, ascending=True)
    rows = rows.assign(rank=range(1, len(rows) + 1))
    return render_table(
        rows,
        [
            Column("#", lambda row: str(row["rank"]), kind="rank"),
            Column(L("lj.lan"), lambda row: str(row["region_name"]), kind="name"),
            Column(L("lj.varde"), lambda row: format_dec(row[value_column], 2), numeric=True),
            Column(L("lj.lansniva"), lambda row: format_dec(row["county_level"], 2), numeric=True),
        ],
        title=L("lj.lansranking_v0", v0=year),
        subtitle=L("lj.ranking_subtitle_v0", v0=tab_name),
        tag=L("lj.ranking"),
    )
