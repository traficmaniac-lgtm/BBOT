from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Any


def _decimal_places_from_tick(tick_size: float | str | None) -> int:
    if tick_size in (None, 0):
        return 6
    try:
        tick_decimal = Decimal(str(tick_size)).normalize()
    except (InvalidOperation, ValueError):
        return 6
    # Normalize can strip trailing zeros; keep at least one decimal place when below 1
    if tick_decimal.as_tuple().exponent < 0:
        return abs(tick_decimal.as_tuple().exponent)
    return 0


def format_price(value: Any, tick_size: float | str | None = None, default_decimals: int = 6) -> str:
    """Format price respecting tick size when available."""

    if value in (None, ""):
        return "-"
    try:
        price = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)

    decimals = _decimal_places_from_tick(tick_size) if tick_size else default_decimals
    quantizer = Decimal(1).scaleb(-decimals)
    rounded = price.quantize(quantizer, rounding=ROUND_DOWN)
    formatted = f"{rounded:f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".") or "0"
    return formatted


def format_spread(spread_value: Any) -> str:
    """Format spread as percentage without scientific notation."""

    if spread_value in (None, ""):
        return "-"
    try:
        spread = Decimal(str(spread_value))
    except (InvalidOperation, ValueError):
        return str(spread_value)

    percent = spread * 100 if spread <= 1 else spread
    normalized = percent.quantize(Decimal("0.0001")) if abs(percent) < 1 else percent.quantize(Decimal("0.01"))
    return f"{normalized:f}%"


def format_volume(volume_value: Any) -> str:
    """Format 24h volume with thousand separators and sensible precision."""

    if volume_value in (None, ""):
        return "-"
    try:
        volume = float(volume_value)
    except (TypeError, ValueError):
        return str(volume_value)

    magnitude = abs(volume)
    if magnitude >= 1_000_000:
        decimals = 0
    elif magnitude >= 1_000:
        decimals = 1
    else:
        decimals = 2
    formatted = f"{volume:,.{decimals}f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted
