"""Placeholders for strategy-owned E3/E4/E5 formulas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ELevels:
    e3: float | None = None
    e4: float | None = None
    e5: float | None = None


def calculate_e_levels(*, high: float, low: float, **_: object) -> ELevels:
    """Return uncomputed E-levels until the strategy formulas are provided.

    Parameters are accepted now so the public interface will remain stable when
    the formulas are implemented.
    """
    if float(high) <= float(low):
        raise ValueError("Candle high must be greater than candle low.")
    return ELevels()
