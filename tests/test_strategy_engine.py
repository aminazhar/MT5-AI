from datetime import datetime
from zoneinfo import ZoneInfo

from fibonacci.calculator import FibonacciDirection
from market.models import Candle
from strategy.engine import StrategyEngine
from strategy.entities import RangeStatus, StrategyEvent, StrategyEventType, StrategyPhase


def candle() -> Candle:
    return Candle(
        timestamp=datetime(2026, 9, 16, 10, 0, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
        open=150.0,
        high=200.0,
        low=100.0,
        close=150.0,
    )


def test_engine_rejects_a_trap_range() -> None:
    engine = StrategyEngine(candle(), point_size=1.0)

    assert engine.state.range_status is RangeStatus.IGNORE_TRAP
    assert engine.state.phase is StrategyPhase.REJECTED


def test_engine_classifies_ideal_range_and_flips_recalculated_levels() -> None:
    engine = StrategyEngine(candle(), point_size=0.008)
    original_e4 = engine.state.levels["E4"]

    decisions = engine.submit(StrategyEvent(StrategyEventType.BO_CONFIRMED))

    assert engine.state.range_status is RangeStatus.IDEAL
    assert engine.state.direction is FibonacciDirection.LOW_TO_HIGH
    assert engine.state.levels["E4"] != original_e4
    assert decisions[0].name == "bo_confirmed"


def test_engine_classifies_large_range_without_changing_strategy_permission() -> None:
    engine = StrategyEngine(candle(), point_size=0.001)

    assert engine.state.range_status is RangeStatus.E6_PLUS_POSSIBLE
    assert engine.state.phase is StrategyPhase.WAITING_FOR_BO
