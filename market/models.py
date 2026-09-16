"""Validated market-domain data structures independent of MT5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Mapping


@dataclass(frozen=True)
class Candle:
    """One OHLC candle, whose high and low are its wick anchors."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime) or self.timestamp.tzinfo is None:
            raise ValueError("Candle timestamp must be a timezone-aware datetime.")
        for field_name in ("open", "high", "low", "close"):
            value = getattr(self, field_name)
            if value is None:
                raise ValueError(f"Candle {field_name} is required.")
            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Candle {field_name} must be numeric.") from exc
            if not isfinite(numeric_value):
                raise ValueError(f"Candle {field_name} must be finite.")
            object.__setattr__(self, field_name, numeric_value)
        if self.high <= self.low:
            raise ValueError("Candle high must be greater than candle low.")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Candle high/low must contain open and close.")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "Candle":
        """Create a candle from a source payload with an ISO-8601 timestamp."""
        required = ("timestamp", "open", "high", "low", "close")
        missing = [key for key in required if key not in payload or payload[key] is None]
        if missing:
            raise ValueError(f"Missing candle fields: {', '.join(missing)}.")
        try:
            timestamp = datetime.fromisoformat(str(payload["timestamp"]))
        except ValueError as exc:
            raise ValueError("Candle timestamp must be valid ISO-8601.") from exc
        return cls(timestamp, payload["open"], payload["high"], payload["low"], payload["close"])

    def require_timezone(self, timezone_name: str) -> None:
        """Reject a candle unless its supplied timestamp has the expected timezone."""
        timezone_key = getattr(self.timestamp.tzinfo, "key", None)
        timezone_label = self.timestamp.tzname()
        if timezone_key != timezone_name and timezone_label != timezone_name:
            raise ValueError(
                f"Candle timezone mismatch: expected {timezone_name}, "
                f"received {self.timestamp.tzinfo}."
            )


@dataclass(frozen=True)
class MarketPrice:
    """One validated bid/ask market-price snapshot."""

    timestamp: datetime
    bid: float
    ask: float
    last: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime) or self.timestamp.tzinfo is None:
            raise ValueError("Market-price timestamp must be a timezone-aware datetime.")
        for field_name in ("bid", "ask"):
            value = getattr(self, field_name)
            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Market-price {field_name} must be numeric.") from exc
            if not isfinite(numeric_value) or numeric_value <= 0:
                raise ValueError(f"Market-price {field_name} must be finite and greater than zero.")
            object.__setattr__(self, field_name, numeric_value)
        if self.ask < self.bid:
            raise ValueError("Market-price ask must be greater than or equal to bid.")
        if self.last is not None:
            try:
                last = float(self.last)
            except (TypeError, ValueError) as exc:
                raise ValueError("Market-price last must be numeric.") from exc
            if not isfinite(last) or last <= 0:
                raise ValueError("Market-price last must be finite and greater than zero.")
            object.__setattr__(self, "last", last)
