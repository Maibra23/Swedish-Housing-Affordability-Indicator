"""What was just built, as text.

Extracted from `build_all`, which mixed two jobs: constructing and saving the
panels, and describing them on stdout. The description is the part a person
reads after a refresh to decide whether it worked, and it was 23 lines of
`print` buried inside the function it describes, where nothing could exercise it.

Returning a string rather than printing is the whole point. A refresh summary is
the first thing anyone looks at when a rebuild goes wrong, and until now it was
the one part of the pipeline that could not be checked for saying something
true.

Completing the R10 split: `clean_sources.py` holds the shapes, `build_panel.py`
holds the joins, and this holds the report.
"""

from __future__ import annotations

import pandas as pd


def summarise(panels: dict[str, pd.DataFrame]) -> str:
    """A human-readable report on the panels a refresh produced.

    Args:
        panels: `level -> frame`, as returned by `build_all`.

    Returns:
        The report, ready to print. Null percentages are listed only where they
        are non-zero, because a wall of zeroes is what stopped anyone reading
        the ones that matter.
    """
    lines: list[str] = []
    for name, panel in panels.items():
        lines.append("=" * 60)
        lines.append(f"Panel: {name}")
        lines.append(f"  Rows: {len(panel):,}")
        lines.append(f"  Columns: {len(panel.columns)}")
        lines.append(f"  Year range: {panel['year'].min()} – {panel['year'].max()}")

        if "region_code" in panel.columns:
            municipalities = [c for c in panel["region_code"].unique() if len(c) == 4]
            lines.append(f"  Municipalities: {len(municipalities)}")
        if "lan_code" in panel.columns:
            counties = [
                c for c in panel["lan_code"].unique() if len(c) == 2 and c != "00"
            ]
            lines.append(f"  Counties: {len(counties)}")

        lines.append("  Null %:")
        for column in panel.columns:
            pct = panel[column].isna().mean() * 100
            if pct > 0:
                lines.append(f"    {column}: {pct:.1f}%")

    return "\n".join(lines)
