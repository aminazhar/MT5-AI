"""Pure state transitions for the documented Phase 1 strategy workflow."""

from __future__ import annotations

from dataclasses import replace

from fibonacci.calculator import FibonacciDirection

from config.settings import VOID_TAKE_PROFIT_BUFFER_POINTS
from strategy.entities import (
    SimulatedEntry,
    StrategyDecision,
    StrategyEvent,
    StrategyEventType,
    StrategyPhase,
    StrategyState,
)


def transition(state: StrategyState, event: StrategyEvent) -> tuple[StrategyState, tuple[StrategyDecision, ...]]:
    """Apply one semantic event without performing I/O or price inference."""
    if state.phase in {StrategyPhase.REJECTED, StrategyPhase.COMPLETE}:
        return state, (
            StrategyDecision("event_ignored", f"{event.event_type.value} ignored in {state.phase.value}."),
        )

    if event.event_type is StrategyEventType.BO_CONFIRMED:
        return _confirm_bo(state)
    if event.event_type is StrategyEventType.VOID_REACHED:
        return _reach_void(state)
    if event.event_type is StrategyEventType.PULLBACK_TO_LEVEL:
        return _enter_on_pullback(state, event.level_name)
    if event.event_type is StrategyEventType.TARGET_REACHED:
        return _close_target_group(state)
    raise ValueError(f"Unsupported strategy event: {event.event_type!r}.")


def _confirm_bo(state: StrategyState) -> tuple[StrategyState, tuple[StrategyDecision, ...]]:
    if state.phase is not StrategyPhase.WAITING_FOR_BO:
        return state, (StrategyDecision("event_ignored", "BO is already confirmed."),)
    flipped_direction = (
        FibonacciDirection.LOW_TO_HIGH
        if state.direction is FibonacciDirection.HIGH_TO_LOW
        else FibonacciDirection.HIGH_TO_LOW
    )
    return replace(state, phase=StrategyPhase.WAITING_FOR_PULLBACK, direction=flipped_direction), (
        StrategyDecision("bo_confirmed", "BO/E4 breakout confirmed; Fibonacci direction flipped."),
    )


def _reach_void(state: StrategyState) -> tuple[StrategyState, tuple[StrategyDecision, ...]]:
    if state.phase is StrategyPhase.WAITING_FOR_BO:
        return state, (StrategyDecision("event_ignored", "Void cannot be reached before BO confirmation."),)
    if state.void_reached:
        return state, (StrategyDecision("event_ignored", "Void has already been reached."),)
    return replace(state, void_reached=True), (
        StrategyDecision("void_reached", "Void/E5 reached; wait for a pullback before considering an entry."),
    )


def _enter_on_pullback(
    state: StrategyState, level_name: str | None
) -> tuple[StrategyState, tuple[StrategyDecision, ...]]:
    if state.phase is StrategyPhase.WAITING_FOR_BO:
        return state, (StrategyDecision("event_ignored", "A pullback cannot enter before BO confirmation."),)
    if level_name is None or level_name not in state.levels:
        return state, (StrategyDecision("event_ignored", "Pullback level is not configured."),)
    if not _is_entry_level(level_name):
        return state, (StrategyDecision("event_ignored", f"{level_name} is not an E3-to-E10 entry level."),)
    if any(entry.level_name == level_name for entry in state.entries):
        return state, (StrategyDecision("event_ignored", f"An entry at {level_name} already exists."),)

    target_price = state.levels["E3"] if state.e5_entry_occurred or level_name == "E5" else _void_target(state)
    entry = SimulatedEntry(level_name, state.levels[level_name], target_price)
    next_state = replace(state, phase=StrategyPhase.ACTIVE, entries=(*state.entries, entry))
    decisions: list[StrategyDecision] = [
        StrategyDecision("entry_opened", f"Simulated {level_name} pullback entry opened.")
    ]
    if level_name == "E5":
        retargeted_entries = tuple(
            replace(existing, target_price=state.levels["E3"]) for existing in next_state.entries
        )
        next_state = replace(next_state, entries=retargeted_entries, e5_entry_occurred=True)
        decisions.append(
            StrategyDecision("target_replaced", "E5 entry changed all existing entry targets to E3.")
        )
    return next_state, tuple(decisions)


def _close_target_group(state: StrategyState) -> tuple[StrategyState, tuple[StrategyDecision, ...]]:
    if not state.e5_entry_occurred or not state.entries:
        return state, (StrategyDecision("event_ignored", "E3 group target is not active."),)
    return replace(state, phase=StrategyPhase.COMPLETE, entries=()), (
        StrategyDecision("entries_closed", "E3 reached after E5; all existing entries closed together."),
    )


def _void_target(state: StrategyState) -> float:
    return state.levels["E5"] + (VOID_TAKE_PROFIT_BUFFER_POINTS * state.point_size)


def _is_entry_level(level_name: str) -> bool:
    if not level_name.startswith("E"):
        return False
    try:
        numeric_level = float(level_name[1:])
    except ValueError:
        return False
    return 3.0 <= numeric_level <= 10.0

