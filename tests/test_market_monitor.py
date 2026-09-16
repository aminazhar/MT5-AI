from datetime import UTC, datetime, timedelta

import pytest

from market.models import MarketPrice
from market.monitor import (
    MarketDataUnavailableError,
    MarketDataValidationError,
    MarketMonitor,
)


class FakeMt5:
    TIMEFRAME_M1 = "M1"

    def __init__(self) -> None:
        self.rates = [
            {"time": 1_789_688_400, "open": 100.0, "high": 110.0, "low": 90.0, "close": 105.0},
            {"time": 1_789_688_460, "open": 105.0, "high": 115.0, "low": 100.0, "close": 110.0},
        ]
        self.tick = {"time": 1_789_688_460, "bid": 109.0, "ask": 111.0, "last": 110.0}
        self.selected = True

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        return self.selected and enabled and symbol == "FixedVol100"

    def copy_rates_from(self, symbol: str, timeframe: object, start: datetime, count: int) -> list[dict[str, float]]:
        assert symbol == "FixedVol100"
        assert timeframe == self.TIMEFRAME_M1
        return self.rates[:count]

    def copy_rates_from_pos(self, symbol: str, timeframe: object, position: int, count: int) -> list[dict[str, float]]:
        assert position == 0
        return [self.rates[-1]][:count]

    def symbol_info_tick(self, symbol: str) -> dict[str, float] | None:
        return self.tick

    def last_error(self) -> tuple[int, str]:
        return (1, "fake MT5 error")


def timestamp() -> datetime:
    return datetime.fromtimestamp(1_789_688_400, UTC)


def test_get_candle_returns_a_validated_typed_candle() -> None:
    candle = MarketMonitor(FakeMt5(), "FixedVol100").get_candle(timestamp())

    assert candle.timestamp == timestamp()
    assert (candle.open, candle.high, candle.low, candle.close) == (100.0, 110.0, 90.0, 105.0)


def test_get_candles_is_generic_and_returns_an_immutable_typed_sequence() -> None:
    monitor = MarketMonitor(FakeMt5(), "FixedVol100")

    candles = monitor.get_candles(timestamp() - timedelta(minutes=10), 2)

    assert isinstance(candles, tuple)
    assert [candle.close for candle in candles] == [105.0, 110.0]


def test_get_latest_candle_returns_the_latest_available_candle() -> None:
    candle = MarketMonitor(FakeMt5(), "FixedVol100").get_latest_candle()

    assert candle.close == 110.0


def test_get_current_price_returns_a_typed_price_snapshot() -> None:
    price = MarketMonitor(FakeMt5(), "FixedVol100").get_current_price()

    assert isinstance(price, MarketPrice)
    assert (price.bid, price.ask, price.last) == (109.0, 111.0, 110.0)


def test_unavailable_client_and_missing_data_fail_with_clear_exceptions() -> None:
    with pytest.raises(MarketDataUnavailableError, match="unavailable"):
        MarketMonitor(None, "FixedVol100")

    client = FakeMt5()
    client.selected = False
    with pytest.raises(MarketDataUnavailableError, match="Unable to select"):
        MarketMonitor(client, "FixedVol100").get_latest_candle()


def test_invalid_mt5_payload_is_rejected() -> None:
    client = FakeMt5()
    client.rates = [{"time": 1_789_688_400, "open": 100.0, "high": 90.0, "low": 100.0, "close": 95.0}]

    with pytest.raises(MarketDataValidationError, match="invalid candle"):
        MarketMonitor(client, "FixedVol100").get_candle(timestamp())


def test_market_price_validates_bid_ask_order() -> None:
    with pytest.raises(ValueError, match="ask"):
        MarketPrice(timestamp(), bid=111.0, ask=109.0)
