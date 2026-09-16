"""Reusable, read-only retrieval of validated M1 market data from MT5."""

from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite
from typing import Any, Iterable, Mapping

from market.models import Candle, MarketPrice


class MarketMonitorError(RuntimeError):
    """Base exception for read-only market-monitor failures."""


class MarketDataUnavailableError(MarketMonitorError):
    """Raised when the MT5 client cannot provide requested market data."""


class MarketDataValidationError(MarketMonitorError):
    """Raised when MT5 returns data that cannot form a typed market object."""


class MarketMonitor:
    """Read and validate M1 data for one MT5 symbol.

    The monitor deliberately accepts an already-initialized client. Connection
    lifecycle remains owned by ``mt5.connector`` and callers can inject a fake
    client in tests.
    """

    def __init__(self, mt5: object | None, symbol: str) -> None:
        if mt5 is None:
            raise MarketDataUnavailableError("MT5 client is unavailable.")
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("Market symbol is required.")
        self._mt5 = mt5
        self._symbol = symbol

    def get_candle(self, timestamp: datetime) -> Candle:
        """Return the M1 candle opened at an exact timezone-aware timestamp."""
        requested = self._as_utc(timestamp)
        candles = self.get_candles(timestamp, 1)
        if not candles or candles[0].timestamp.astimezone(UTC) != requested:
            raise MarketDataUnavailableError(
                f"No M1 candle for {self._symbol!r} at {timestamp.isoformat()}."
            )
        return candles[0]

    def get_candles(self, start_timestamp: datetime, count: int) -> tuple[Candle, ...]:
        """Return up to ``count`` validated M1 candles starting at a timestamp."""
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise ValueError("Candle count must be a positive integer.")
        start_utc = self._as_utc(start_timestamp)
        self._select_symbol()
        copy_rates_from = self._method("copy_rates_from")
        rates = copy_rates_from(self._symbol, self._timeframe_m1(), start_utc, count)
        if rates is None:
            raise MarketDataUnavailableError(
                f"MT5 candle lookup failed for {self._symbol!r}: {self._last_error()}"
            )
        try:
            return tuple(self._candle_from_rate(rate) for rate in rates)
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketDataValidationError("MT5 returned an invalid candle payload.") from exc

    def get_latest_candle(self) -> Candle:
        """Return the latest M1 candle available from MT5."""
        self._select_symbol()
        copy_rates_from_pos = self._method("copy_rates_from_pos")
        rates = copy_rates_from_pos(self._symbol, self._timeframe_m1(), 0, 1)
        if rates is None or len(rates) == 0:
            raise MarketDataUnavailableError(
                f"No latest M1 candle is available for {self._symbol!r}: {self._last_error()}"
            )
        try:
            return self._candle_from_rate(rates[0])
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketDataValidationError("MT5 returned an invalid latest-candle payload.") from exc

    def get_current_price(self) -> MarketPrice:
        """Return the latest validated bid/ask/last price snapshot."""
        self._select_symbol()
        symbol_info_tick = self._method("symbol_info_tick")
        tick = symbol_info_tick(self._symbol)
        if tick is None:
            raise MarketDataUnavailableError(
                f"No current price is available for {self._symbol!r}: {self._last_error()}"
            )
        try:
            timestamp = datetime.fromtimestamp(int(self._field(tick, "time")), UTC)
            last_value = self._field(tick, "last")
            last = None if last_value in (None, 0, 0.0) else float(last_value)
            return MarketPrice(
                timestamp=timestamp,
                bid=float(self._field(tick, "bid")),
                ask=float(self._field(tick, "ask")),
                last=last,
            )
        except (OSError, OverflowError, TypeError, ValueError) as exc:
            raise MarketDataValidationError("MT5 returned an invalid current-price payload.") from exc

    def _select_symbol(self) -> None:
        symbol_select = self._method("symbol_select")
        if not symbol_select(self._symbol, True):
            raise MarketDataUnavailableError(
                f"Unable to select MT5 symbol {self._symbol!r}: {self._last_error()}"
            )

    def _timeframe_m1(self) -> object:
        try:
            return getattr(self._mt5, "TIMEFRAME_M1")
        except AttributeError as exc:
            raise MarketDataUnavailableError("MT5 client does not provide TIMEFRAME_M1.") from exc

    def _method(self, name: str) -> Any:
        method = getattr(self._mt5, name, None)
        if not callable(method):
            raise MarketDataUnavailableError(f"MT5 client does not provide {name}().")
        return method

    def _last_error(self) -> object:
        last_error = getattr(self._mt5, "last_error", None)
        return last_error() if callable(last_error) else "unknown MT5 error"

    @staticmethod
    def _as_utc(timestamp: datetime) -> datetime:
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            raise ValueError("Market-data timestamp must be timezone-aware.")
        return timestamp.astimezone(UTC)

    @staticmethod
    def _field(payload: object, name: str) -> object:
        if isinstance(payload, Mapping):
            return payload[name]
        return getattr(payload, name)

    @classmethod
    def _candle_from_rate(cls, rate: object) -> Candle:
        timestamp = datetime.fromtimestamp(int(cls._field(rate, "time")), UTC)
        return Candle(
            timestamp=timestamp,
            open=float(cls._field(rate, "open")),
            high=float(cls._field(rate, "high")),
            low=float(cls._field(rate, "low")),
            close=float(cls._field(rate, "close")),
        )
