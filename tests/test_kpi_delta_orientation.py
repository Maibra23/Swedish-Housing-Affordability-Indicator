"""A KPI delta says two things, and they are not the same thing.

Found by launching the app and reading the front page. `Genomsnittligt SHAI`
had fallen 36,5 %, and the card rendered it as a green ▼ — good news. Version C
is an affordability ratio where higher is better, so a one-third fall is the
worst number on the page.

The cause was one parameter doing two jobs. `delta_direction` chose both the
arrow and the colour, and the stylesheet hardcoded up as red and down as green.
That assumption holds for a risk measure and fails for everything else, so
pages measuring the opposite bent the parameter to get the colour they wanted
and broke the arrow. The same quantity rendered three ways:

| Page | Change | Rendered |
|---|---|---|
| Sida 01 | −36,5 % | green ▼, read as good |
| Sida 03 | −35,2 % | red **▲**, arrow contradicts the number |
| Sida 05 | +81,2 % | **▼** beside a positive number |

Direction is arithmetic. Sentiment is a property of the metric, which the
component cannot infer. `delta_meta` returns both, and these tests pin the
split so it cannot quietly collapse back into one.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.ui.components import delta_meta, kpi_card

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "change,higher_is_better,direction,sentiment",
    [
        # An affordability ratio: a fall is bad however the arrow points.
        (-36.5, True, "down", "bad"),
        (81.2, True, "up", "good"),
        # A price-to-income ratio: a rise is bad.
        (20.9, False, "up", "bad"),
        (-5.0, False, "down", "good"),
        # No inherent direction. Colouring it would assert a judgement.
        (36003, None, "up", "neutral"),
        (-1200, None, "down", "neutral"),
        # No movement is never good or bad.
        (0, True, "flat", "neutral"),
        (0, None, "flat", "neutral"),
    ],
)
def test_direction_and_sentiment_are_decided_separately(
    change: float, higher_is_better: bool | None, direction: str, sentiment: str
) -> None:
    assert delta_meta(change, higher_is_better) == {
        "delta_direction": direction,
        "delta_sentiment": sentiment,
    }


def test_the_arrow_always_agrees_with_the_sign() -> None:
    """The defect on Sida 03 and 05: an arrow pointing against its own number."""
    for change in (-99.0, -0.1, 0.0, 0.1, 99.0):
        for better in (True, False, None):
            direction = delta_meta(change, better)["delta_direction"]
            expected = "up" if change > 0 else "down" if change < 0 else "flat"
            assert direction == expected, (
                f"a change of {change} renders a {direction} arrow"
            )


def test_the_same_movement_reads_differently_for_opposite_metrics() -> None:
    """The whole point: identical arithmetic, opposite meaning."""
    rise_in_affordability = delta_meta(10.0, higher_is_better=True)
    rise_in_price_ratio = delta_meta(10.0, higher_is_better=False)

    assert rise_in_affordability["delta_direction"] == rise_in_price_ratio["delta_direction"]
    assert rise_in_affordability["delta_sentiment"] == "good"
    assert rise_in_price_ratio["delta_sentiment"] == "bad"


def test_the_card_emits_both_classes() -> None:
    html = kpi_card(
        label="TEST", value="1,0", delta="-36,5%",
        **delta_meta(-36.5, higher_is_better=True),
    )
    assert "shai-dir-down" in html and "shai-mood-bad" in html
    assert "▼" in html, "a downward change must render a downward arrow"


def test_the_stylesheet_colours_sentiment_and_not_direction() -> None:
    """The root cause lived in CSS: `.up { red }` is an assumption about meaning.

    If a `dir-*` rule ever sets a colour again, the split is cosmetic and the
    defect is back.
    """
    css = (ROOT / "src" / "ui" / "css_components.py").read_text(encoding="utf-8")
    for direction in ("up", "down", "flat"):
        assert not re.search(rf"\.shai-dir-{direction}\s*\{{[^}}]*color", css), (
            f".shai-dir-{direction} sets a colour; direction is arithmetic and must "
            f"not decide sentiment"
        )
    for mood in ("good", "bad", "neutral"):
        assert f".shai-kpi-delta.shai-mood-{mood}" in css, f"no colour rule for {mood}"


def test_no_page_sets_the_two_by_hand() -> None:
    """Every call site goes through `delta_meta`, so the metric's direction is
    declared once, beside the metric, rather than inferred from a colour."""
    offenders: list[str] = []
    for path in sorted(ROOT.glob("pages/*.py")) + sorted(ROOT.glob("src/**/*.py")):
        if path.name == "components.py":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if "delta_direction=" in line or "delta_sentiment=" in line:
                offenders.append(f"{path.relative_to(ROOT)}:{line_no} {line.strip()}")
    assert not offenders, (
        "delta direction or sentiment set by hand: "
        + "; ".join(offenders)
        + ". Use delta_meta(change, higher_is_better=...)."
    )
