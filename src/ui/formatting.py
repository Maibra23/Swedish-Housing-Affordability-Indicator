"""Swedish number formatting, in one place.

Split out of `components.py`, which re-exports every name here so existing
imports keep working. Pages used to format inline with ``f"{x:.2f}"`` and a
comma swap at most call sites but not all, which is how one page came to print
"2.62" beside "−36,5". Everything user-facing goes through these.
"""

from __future__ import annotations



def format_sek(value: float, decimals: int = 0) -> str:
    """Format a SEK value with non-breaking space thousand separators."""
    if decimals == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimals}f}"
    # True minus: "−153 427" rather than the hyphen in "-153 427".
    return formatted.replace(",", "\u00A0").replace(".", ",").replace("-", "\u2212")


def format_sek_compact(value: float) -> str:
    """Format a SEK value short: "Mkr" from 1 000 000, "tkr" from 10 000.

    For places where the grouped form ("2 041 350 SEK") is wider than its
    container, such as the five-across regime cards on sida 04. The CSS lets a
    long value wrap rather than clip; this keeps it from needing to.
    """
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"{value / 1_000_000:.2f}".replace(".", ",") + " Mkr"
    if magnitude >= 10_000:
        return f"{value / 1_000:.0f}".replace(".", ",") + " tkr"
    return format_sek(value) + " SEK"


#: Minus sign and the space before a unit, as Swedish typesetting uses them.
_MINUS = "\u2212"
_NBSP = "\u00A0"


def format_dec(value: float, decimals: int = 1, signed: bool = False) -> str:
    """A number Swedish style: decimal comma, grouped thousands, true minus.

    Pages used to format inline with ``f"{x:.2f}"`` and a comma swap at most call
    sites but not all, so the top-15 tables printed "2.62" and "-2.39" beside
    KPI cards printing "−36,5". One formatter makes that impossible.

    Args:
        value: The number.
        decimals: Digits after the comma.
        signed: Prefix "+" on positive values, for changes.
    """
    sign = "+" if signed else ""
    text = f"{value:{sign},.{decimals}f}"
    return text.replace(",", _NBSP).replace(".", ",").replace("-", _MINUS)


def format_pct(value: float, decimals: int = 1, signed: bool = False) -> str:
    """A percentage Swedish style, with a non-breaking space before "%"."""
    return format_dec(value, decimals, signed) + _NBSP + "%"


def format_ratio(value: float, decimals: int = 1) -> str:
    """A multiple such as a price-to-income ratio: "20,8×", never "20,8x"."""
    return format_dec(value, decimals) + "×"


def format_swedish_int(value: int) -> str:
    """Format integer with non-breaking space thousands separator."""
    return f"{value:,}".replace(",", "\u00A0")
