"""Read one closed M1 candle from a local MT5 terminal and display levels."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from config.settings import FIB_DIRECTION, FIB_LEVELS, SIGNAL_TIMEZONE, TARGET_SYMBOL
from fibonacci.calculator import calculate_named_fibonacci_levels
from market.models import Candle
from mt5.connector import connected_terminal


def retrieve_m1_candle(mt5: object, symbol: str, signal_time: datetime) -> Candle:
    """Retrieve the bar opened at ``signal_time``; MT5 storage is queried in UTC."""
    if signal_time.tzinfo is None:
        raise ValueError("Signal time must be timezone-aware.")
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Unable to select MT5 symbol {symbol!r}: {mt5.last_error()}")

    start_utc = signal_time.astimezone(UTC)
    end_utc = start_utc + timedelta(minutes=1)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_utc, end_utc)
    if rates is None:
        raise RuntimeError(f"MT5 candle lookup failed: {mt5.last_error()}")
    expected_epoch = int(start_utc.timestamp())
    matching_rates = [rate for rate in rates if int(rate["time"]) == expected_epoch]
    if not matching_rates:
        raise LookupError(
            f"No M1 candle for {symbol} at {signal_time.isoformat()}. "
            "Confirm the symbol, timezone, and terminal history."
        )
    rate = matching_rates[0]
    return Candle(
        timestamp=datetime.fromtimestamp(int(rate["time"]), UTC).astimezone(signal_time.tzinfo),
        open=float(rate["open"]),
        high=float(rate["high"]),
        low=float(rate["low"]),
        close=float(rate["close"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Read one MT5 M1 candle; no orders are sent.")
    parser.add_argument("--timestamp", required=True, help="Signal time in YYYY-MM-DD HH:MM broker/CST time.")
    parser.add_argument("--symbol", default=TARGET_SYMBOL)
    args = parser.parse_args()
    signal_time = datetime.strptime(args.timestamp, "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(SIGNAL_TIMEZONE)
    )

    with connected_terminal() as mt5:
        candle = retrieve_m1_candle(mt5, args.symbol, signal_time)
        symbol_info = mt5.symbol_info(args.symbol)
        if symbol_info is None or not symbol_info.point:
            raise RuntimeError(f"Unable to read point size for {args.symbol!r}: {mt5.last_error()}")
        symbol_point = float(symbol_info.point)
    levels = calculate_named_fibonacci_levels(candle.high, candle.low, FIB_LEVELS, FIB_DIRECTION)
    e3_e5_points = abs(levels["E3"] - levels["E5"]) / symbol_point
    if e3_e5_points < 35_000:
        range_status = "IGNORE_TRAP"
    elif e3_e5_points <= 45_000:
        range_status = "IDEAL"
    else:
        range_status = "E6_PLUS_POSSIBLE"
    print(f"Signal: {args.symbol} | {signal_time.isoformat()} | M1")
    print(f"Candle: O={candle.open} H={candle.high} L={candle.low} C={candle.close}")
    print(f"Fibonacci direction: {FIB_DIRECTION}")
    print(f"Symbol point: {symbol_point}")
    print(f"E3-E5 range: {e3_e5_points:.0f} points | {range_status}")
    for name, price in levels.items():
        print(f"{name}: {price}")


if __name__ == "__main__":
    main()
