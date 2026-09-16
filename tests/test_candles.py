from datetime import datetime, timedelta, timezone

import pytest

from market.models import Candle


def sample_candle() -> Candle:
    return Candle(
        timestamp=datetime(
            2026,
            9,
            15,
            13,
            12,
            tzinfo=timezone(timedelta(hours=8), "Asia/Kuala_Lumpur"),
        ),
        open=3650.25,
        high=3654.80,
        low=3648.10,
        close=3653.40,
    )


def test_valid_candle_retains_ohlc_and_wick_values() -> None:
    candle = sample_candle()
    assert (candle.open, candle.high, candle.low, candle.close) == (3650.25, 3654.8, 3648.1, 3653.4)


def test_invalid_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="ISO-8601"):
        Candle.from_mapping({"timestamp": "not-a-date", "open": 1, "high": 3, "low": 0, "close": 2})


def test_missing_ohlc_is_rejected() -> None:
    with pytest.raises(ValueError, match="close"):
        Candle.from_mapping({"timestamp": "2026-09-15T13:12:00+08:00", "open": 1, "high": 3, "low": 0})


def test_invalid_wick_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="high"):
        Candle(
            datetime(2026, 9, 15, 13, 12, tzinfo=timezone(timedelta(hours=8), "Asia/Kuala_Lumpur")),
            1,
            2,
            2,
            1,
        )


def test_timezone_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone mismatch"):
        sample_candle().require_timezone("UTC")
