"""Typed, immutable domain entities for the deterministic strategy engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Mapping

from fibonacci.calculator import FibonacciDirection


class RangeStatus(str, Enum):
    """Classification defined by the E3-to-E5 range observations."""

    IGNORE_TRAP = "ignore_trap"
    IDEAL = "ideal"
    E6_PLUS_POSSIBLE = "e6_plus_possible"


class StrategyPhase(str, Enum):
    """Lifecycle phases supplied by the documented strategy workflow."""

    REJECTED = "rejected"
    WAITING_FOR_BO = "waiting_for_bo"
    WAITING_FOR_PULLBACK = "waiting_for_pullback"
    ACTIVE = "active"
    COMPLETE = "complete"


class StrategyEventType(str, Enum):
    """Semantic observations accepted by the phase-one state machine."""

    BO_CONFIRMED = "bo_confirmed"
    VOID_REACHED = "void_reached"
    PULLBACK_TO_LEVEL = "pullback_to_level"
    TARGET_REACHED = "target_reached"


@dataclass(frozen=True)
class StrategyEvent:
    """One externally classified strategy observation.

    Pullback classification is intentionally supplied by the caller because the
    strategy notes do not define how raw price data qualifies a pullback.
    """

    event_type: StrategyEventType
    level_name: str | None = None

    def __post_init__(self) -> None:
        if self.event_type is StrategyEventType.PULLBACK_TO_LEVEL and not self.level_name:
            raise ValueError("A pullback event requires a level name.")
        if self.event_type is not StrategyEventType.PULLBACK_TO_LEVEL and self.level_name is not None:
            raise ValueError("Only a pullback event may include a level name.")


@dataclass(frozen=True)
class SimulatedEntry:
    """A single simulated entry and its current target price."""

    level_name: str
    entry_price: float
    target_price: float


@dataclass(frozen=True)
class StrategyDecision:
    """An auditable outcome emitted by one state-machine transition."""

    name: str
    detail: str


@dataclass(frozen=True)
class StrategyState:
    """Complete immutable state of one simulation run."""

    phase: StrategyPhase
    direction: FibonacciDirection
    levels: Mapping[str, float]
    point_size: float
    range_status: RangeStatus
    entries: tuple[SimulatedEntry, ...] = ()
    void_reached: bool = False
    e5_entry_occurred: bool = False

    def __post_init__(self) -> None:
        try:
            point_size = float(self.point_size)
        except (TypeError, ValueError) as exc:
            raise ValueError("Symbol point size must be numeric.") from exc
        if not isfinite(point_size) or point_size <= 0:
            raise ValueError("Symbol point size must be finite and greater than zero.")
        if "E3" not in self.levels or "E4" not in self.levels or "E5" not in self.levels:
            raise ValueError("Strategy levels must include E3, E4, and E5.")
        normalized_levels: dict[str, float] = {}
        for name, price in self.levels.items():
            try:
                numeric_price = float(price)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Strategy level {name!r} must be numeric.") from exc
            if not isfinite(numeric_price):
                raise ValueError(f"Strategy level {name!r} must be finite.")
            normalized_levels[name] = numeric_price
        object.__setattr__(self, "point_size", point_size)
        object.__setattr__(self, "levels", MappingProxyType(normalized_levels))

