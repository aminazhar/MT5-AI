"""Append-only in-memory journal for deterministic simulation auditing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from strategy.entities import StrategyDecision, StrategyEvent, StrategyState


@dataclass(frozen=True)
class JournalRecord:
    """One submitted event, its decisions, and the resulting state snapshot."""

    sequence: int
    event: StrategyEvent
    decisions: tuple[StrategyDecision, ...]
    state: StrategyState


class EventSubmitter(Protocol):
    """Minimum engine capability required for journal replay."""

    def submit(self, event: StrategyEvent) -> tuple[StrategyDecision, ...]: ...

    @property
    def state(self) -> StrategyState: ...


class SimulationJournal:
    """Record and replay a simulation's semantic event sequence."""

    def __init__(self) -> None:
        self._records: list[JournalRecord] = []

    @property
    def records(self) -> tuple[JournalRecord, ...]:
        """Return an immutable ordered view of all journal records."""
        return tuple(self._records)

    def record(
        self,
        event: StrategyEvent,
        decisions: tuple[StrategyDecision, ...],
        state: StrategyState,
    ) -> JournalRecord:
        """Append one result after the engine has handled an event."""
        record = JournalRecord(len(self._records) + 1, event, decisions, state)
        self._records.append(record)
        return record

    def replay(self, submitter: EventSubmitter) -> tuple[JournalRecord, ...]:
        """Replay recorded input events through a fresh deterministic engine."""
        replayed: list[JournalRecord] = []
        for record in self._records:
            decisions = submitter.submit(record.event)
            replayed.append(JournalRecord(record.sequence, record.event, decisions, submitter.state))
        return tuple(replayed)

