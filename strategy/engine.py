"""Deterministic orchestration of strategy setup, transitions, and auditing."""

from __future__ import annotations

from dataclasses import replace

from config.settings import FIB_DIRECTION, FIB_LEVELS
from fibonacci.calculator import FibonacciDirection, calculate_named_fibonacci_levels
from market.models import Candle
from strategy.entities import (
    RangeStatus,
    StrategyDecision,
    StrategyEvent,
    StrategyPhase,
    StrategyState,
)
from strategy.state_machine import transition


MINIMUM_E3_E5_POINTS = 35_000
IDEAL_E3_E5_POINTS = 45_000


class StrategyEngine:
    """Run one deterministic, simulation-only strategy instance."""

    def __init__(self, candle: Candle, point_size: float) -> None:
        self._candle = candle
        self._state = self._initial_state(candle, point_size)

    @property
    def state(self) -> StrategyState:
        """Return the current immutable strategy state."""
        return self._state

    def submit(self, event: StrategyEvent) -> tuple[StrategyDecision, ...]:
        """Apply one semantic event and return all resulting decisions."""
        prior_direction = self._state.direction
        next_state, decisions = transition(self._state, event)
        if next_state.direction is not prior_direction:
            levels = calculate_named_fibonacci_levels(
                self._candle.high, self._candle.low, FIB_LEVELS, next_state.direction
            )
            next_state = replace(next_state, levels=levels)
        self._state = next_state
        return decisions

    @staticmethod
    def _initial_state(candle: Candle, point_size: float) -> StrategyState:
        direction = FibonacciDirection(FIB_DIRECTION)
        levels = calculate_named_fibonacci_levels(candle.high, candle.low, FIB_LEVELS, direction)
        range_points = abs(levels["E3"] - levels["E5"]) / float(point_size)
        if range_points < MINIMUM_E3_E5_POINTS:
            range_status = RangeStatus.IGNORE_TRAP
            phase = StrategyPhase.REJECTED
        elif range_points <= IDEAL_E3_E5_POINTS:
            range_status = RangeStatus.IDEAL
            phase = StrategyPhase.WAITING_FOR_BO
        else:
            range_status = RangeStatus.E6_PLUS_POSSIBLE
            phase = StrategyPhase.WAITING_FOR_BO
        return StrategyState(
            phase=phase,
            direction=direction,
            levels=levels,
            point_size=point_size,
            range_status=range_status,
        )

