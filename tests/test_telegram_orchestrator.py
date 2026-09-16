from datetime import UTC, datetime

import pytest

from market.models import Candle
from market.monitor import MarketDataUnavailableError
from simulation.journal import SimulationJournal
from telegram.orchestrator import TelegramOrchestrator
from telegram.reader import TelegramSignal


class FakeMarketMonitor:
    def __init__(self, candle: Candle) -> None:
        self.candle = candle
        self.requested_timestamp: datetime | None = None

    def get_candle(self, timestamp: datetime) -> Candle:
        self.requested_timestamp = timestamp
        return self.candle


def candle() -> Candle:
    return Candle(
        timestamp=datetime(2026, 9, 16, 10, 0, tzinfo=UTC),
        open=150.0,
        high=200.0,
        low=100.0,
        close=150.0,
    )


def signal() -> TelegramSignal:
    return TelegramSignal(datetime(2026, 9, 16, 10, 0, tzinfo=UTC))


def test_process_signal_retrieves_a_candle_and_initializes_the_engine() -> None:
    monitor = FakeMarketMonitor(candle())
    journal = SimulationJournal()
    orchestrator = TelegramOrchestrator(monitor, point_size=0.008, journal=journal)

    result = orchestrator.process_signal(signal())

    assert monitor.requested_timestamp == signal().timestamp
    assert result.candle is monitor.candle
    assert result.strategy_engine.state.range_status.value == "ideal"
    assert result.journal is journal


def test_process_signal_rejects_an_unparsed_or_naive_signal() -> None:
    orchestrator = TelegramOrchestrator(FakeMarketMonitor(candle()), 0.008, SimulationJournal())

    with pytest.raises(ValueError, match="parsed TelegramSignal"):
        orchestrator.process_signal(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        orchestrator.process_signal(TelegramSignal(datetime(2026, 9, 16, 10, 0)))


def test_market_monitor_failure_is_propagated_without_mt5_access() -> None:
    class UnavailableMonitor:
        def get_candle(self, timestamp: datetime) -> Candle:
            raise MarketDataUnavailableError("MT5 client is unavailable.")

    orchestrator = TelegramOrchestrator(UnavailableMonitor(), 0.008, SimulationJournal())

    with pytest.raises(MarketDataUnavailableError, match="unavailable"):
        orchestrator.process_signal(signal())


def test_orchestrator_validates_required_dependencies() -> None:
    with pytest.raises(ValueError, match="get_candle"):
        TelegramOrchestrator(object(), 0.008, SimulationJournal())
    with pytest.raises(ValueError, match="point size"):
        TelegramOrchestrator(FakeMarketMonitor(candle()), 0, SimulationJournal())
    with pytest.raises(ValueError, match="SimulationJournal"):
        TelegramOrchestrator(FakeMarketMonitor(candle()), 0.008, object())  # type: ignore[arg-type]
