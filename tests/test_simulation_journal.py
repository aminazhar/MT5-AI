from datetime import datetime
from zoneinfo import ZoneInfo

from market.models import Candle
from simulation.journal import SimulationJournal
from strategy.engine import StrategyEngine
from strategy.entities import StrategyEvent, StrategyEventType


def fresh_engine() -> StrategyEngine:
    candle = Candle(
        timestamp=datetime(2026, 9, 16, 10, 0, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
        open=150.0,
        high=200.0,
        low=100.0,
        close=150.0,
    )
    return StrategyEngine(candle, point_size=0.008)


def test_journal_records_ordered_immutable_snapshots() -> None:
    engine = fresh_engine()
    journal = SimulationJournal()
    event = StrategyEvent(StrategyEventType.BO_CONFIRMED)
    journal.record(event, engine.submit(event), engine.state)

    assert journal.records[0].sequence == 1
    assert journal.records[0].state.direction.value == "low_to_high"


def test_journal_replays_the_same_events_through_a_fresh_engine() -> None:
    engine = fresh_engine()
    journal = SimulationJournal()
    for event in (
        StrategyEvent(StrategyEventType.BO_CONFIRMED),
        StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL, "E4"),
        StrategyEvent(StrategyEventType.PULLBACK_TO_LEVEL, "E5"),
    ):
        journal.record(event, engine.submit(event), engine.state)

    replayed = journal.replay(fresh_engine())

    assert [record.decisions for record in replayed] == [record.decisions for record in journal.records]
    assert replayed[-1].state.entries == journal.records[-1].state.entries
