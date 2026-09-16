"""Pure Fibonacci calculations based on candle wicks (high and low)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum
from math import isfinite


class FibonacciDirection(str, Enum):
    LOW_TO_HIGH = "low_to_high"
    HIGH_TO_LOW = "high_to_low"


def calculate_fibonacci_levels(
    high: float,
    low: float,
    levels: Iterable[float],
    direction: FibonacciDirection | str = FibonacciDirection.LOW_TO_HIGH,
) -> dict[float, float]:
    """Return each configured Fibonacci ratio mapped to its wick-based price.

    Ratios are intentionally not constrained to 0..1 because strategies may use
    extension levels. Candle body values (open/close) are never used here.
    """
    try:
        high = float(high)
        low = float(low)
    except (TypeError, ValueError) as exc:
        raise ValueError("Candle high and low must be numeric.") from exc
    if not isfinite(high) or not isfinite(low) or high <= low:
        raise ValueError("Candle high must be greater than candle low.")

    try:
        direction = FibonacciDirection(direction)
    except (TypeError, ValueError) as exc:
        valid = ", ".join(item.value for item in FibonacciDirection)
        raise ValueError(f"Unsupported Fibonacci direction. Use one of: {valid}.") from exc

    candle_range = high - low
    prices: dict[float, float] = {}
    for level in levels:
        try:
            ratio = float(level)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid Fibonacci level: {level!r}.") from exc
        if not isfinite(ratio):
            raise ValueError(f"Invalid Fibonacci level: {level!r}.")
        if direction is FibonacciDirection.LOW_TO_HIGH:
            prices[ratio] = low + (candle_range * ratio)
        else:
            prices[ratio] = high - (candle_range * ratio)
    return prices


def calculate_named_fibonacci_levels(
    high: float,
    low: float,
    levels: Mapping[str, float],
    direction: FibonacciDirection | str = FibonacciDirection.LOW_TO_HIGH,
) -> dict[str, float]:
    """Return named strategy levels while keeping labels such as E3 and E4."""
    numeric_prices = calculate_fibonacci_levels(high, low, levels.values(), direction)
    return {name: numeric_prices[float(level)] for name, level in levels.items()}
