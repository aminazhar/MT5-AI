from fibonacci.calculator import FibonacciDirection
from strategy.entities import RangeStatus, StrategyEvent, StrategyEventType, StrategyPhase, StrategyState
from strategy.state_machine import transition


def state() -> StrategyState:
    return StrategyState(
        StrategyPhase.WAITING_FOR_BO,
        FibonacciDirection.HIGH_TO_LOW,
        {"E3": 100.0, "E3.5": 110.0, "E4": 120.0, "E5": 140.0, "E6": 160.0},
        0.01,
        RangeStatus.IDEAL,
    )


def test_bo_confirmation_flips_direction_and_waits_for_pullback() -> None:
    next_state, decisions = transition(state(), StrategyEvent(StrategyEventType.BO_CONFIRMED))

    assert next_state.phase is StrategyPhase.WAITING_FOR_PULLBACK
    assert next_state.direction is FibonacciDirection.LOW_TO_HIGH
    assert decisions[0].name == "bo_confirmed"


def test_void_after_bo_waits_for_pullback_without_an_entry() -> None:
    bo_state, _ = transition(state(), StrategyEvent(StrategyEventType.BO_CONFIRMED))
    next_state, decisions = transition(bo_state, StrategyEvent(StrategyEventType.VOID_REACHED))

    assert next_state.void_reached is True
    assert next_state.entries == ()
    assert decisions[0].name == "void_reached"


def test_e5_replaces_all_existing_targets_with_e3() -> None:
    bo_state, _ = transition(state(), StrategyEvent(StrategyEventType.BO_CONFIRMED))
    e4_state, _ = transition(bo_state, StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL, "E4"))
    e5_state, decisions = transition(e4_state, StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL, "E5"))

    assert e5_state.e5_entry_occurred is True
    assert {entry.target_price for entry in e5_state.entries} == {100.0}
    assert [decision.name for decision in decisions] == ["entry_opened", "target_replaced"]


def test_later_entry_joins_e3_target_group_after_e5() -> None:
    bo_state, _ = transition(state(), StrategyEvent(StrategyEventType.BO_CONFIRMED))
    e5_state, _ = transition(bo_state, StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL, "E5"))
    e6_state, _ = transition(e5_state, StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL, "E6"))

    assert e6_state.entries[-1].target_price == e6_state.levels["E3"]


def test_target_reached_closes_all_entries_only_after_e5() -> None:
    bo_state, _ = transition(state(), StrategyEvent(StrategyEventType.BO_CONFIRMED))
    e5_state, _ = transition(bo_state, StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL, "E5"))
    next_state, decisions = transition(e5_state, StrategyEvent(StrategyEventType.TARGET_REACHED))

    assert next_state.phase is StrategyPhase.COMPLETE
    assert next_state.entries == ()
    assert decisions[0].name == "entries_closed"

