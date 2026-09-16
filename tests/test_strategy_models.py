import pytest

from fibonacci.calculator import FibonacciDirection
from strategy.entities import RangeStatus, StrategyEvent, StrategyEventType, StrategyPhase, StrategyState


def test_pullback_event_requires_a_level_name() -> None:
    with pytest.raises(ValueError, match="requires a level"):
        StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL)


def test_non_pullback_event_rejects_a_level_name() -> None:
    with pytest.raises(ValueError, match="Only a pullback"):
        StrategyEvent(StrategyEventType.BO_CONFIRMED, "E4")


def test_state_normalizes_and_freezes_levels() -> None:
    levels = {"E3": 100, "E4": 120, "E5": 140}
    state = StrategyState(
        StrategyPhase.WAITING_FOR_BO,
        FibonacciDirection.HIGH_TO_LOW,
        levels,
        0.01,
        RangeStatus.IDEAL,
    )

    levels["E3"] = 999
    assert state.levels["E3"] == 100.0
    with pytest.raises(TypeError):
        state.levels["E3"] = 200  # type: ignore[index]


def test_state_rejects_invalid_point_size() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        StrategyState(
            StrategyPhase.WAITING_FOR_BO,
            FibonacciDirection.HIGH_TO_LOW,
            {"E3": 1, "E4": 2, "E5": 3},
            0,
            RangeStatus.IDEAL,
        )

