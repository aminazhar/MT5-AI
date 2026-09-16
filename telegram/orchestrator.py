"""Coordinate parsed Telegram signals with existing market and strategy services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Protocol

from market.models import Candle
from simulation.journal import SimulationJournal
from strategy.engine import StrategyEngine
from telegram.reader import TelegramSignal


class CandleProvider(Protocol):
    """Minimum read-only market-data capability used by the orchestrator."""

    def get_candle(self, timestamp: datetime) -> Candle: ...


@dataclass(frozen=True)
class SignalProcessingResult:
    """Typed result of preparing one parsed signal for simulation."""

    signal: TelegramSignal
    candle: Candle
    strategy_engine: StrategyEngine
    journal: SimulationJournal


class TelegramOrchestrator:
    """Coordinate signal parsing output without containing trading rules."""

    def __init__(
        self,
        market_monitor: CandleProvider,
        point_size: float,
        journal: SimulationJournal,
    ) -> None:
        if not callable(getattr(market_monitor, "get_candle", None)):
            raise ValueError("Market monitor must provide get_candle().")
        try:
            numeric_point_size = float(point_size)
        except (TypeError, ValueError) as exc:
            raise ValueError("Symbol point size must be numeric.") from exc
        if not isfinite(numeric_point_size) or numeric_point_size <= 0:
            raise ValueError("Symbol point size must be finite and greater than zero.")
        if not isinstance(journal, SimulationJournal):
            raise ValueError("A SimulationJournal is required.")
        self._market_monitor = market_monitor
        self._point_size = numeric_point_size
        self._journal = journal

    def process_signal(self, signal: TelegramSignal) -> SignalProcessingResult:
        """Retrieve the signal candle and prepare its deterministic strategy engine."""
        self._validate_signal(signal)
        candle = self._market_monitor.get_candle(signal.timestamp)
        strategy_engine = StrategyEngine(candle, self._point_size)
        return SignalProcessingResult(signal, candle, strategy_engine, self._journal)

    @staticmethod
    def _validate_signal(signal: TelegramSignal) -> None:
        if not isinstance(signal, TelegramSignal):
            raise ValueError("A parsed TelegramSignal is required.")
        if not isinstance(signal.timestamp, datetime) or signal.timestamp.tzinfo is None:
            raise ValueError("Telegram signal timestamp must be timezone-aware.")
        if signal.direction is not None and not isinstance(signal.direction, str):
            raise ValueError("Telegram signal direction must be a string or None.")
