from datetime import datetime
from zoneinfo import ZoneInfo

from telegram.reader import parse_signal


def test_parses_the_supplied_cst_signal_format() -> None:
    message = "Project V | Indicator NQ426\n👉 FixedVol100.\nC.S.T: 2026.09.16 09:53"
    signal = parse_signal(message)
    assert signal is not None
    assert signal.timestamp == datetime(2026, 9, 16, 9, 53, tzinfo=ZoneInfo("Asia/Kuala_Lumpur"))
    assert signal.direction is None


def test_parses_colon_and_dot_date_separators() -> None:
    message = "PROJECT V || Indicator NQ426\nFixedVol100.\nC.S.T : 2026:09.16 10:06"
    signal = parse_signal(message)
    assert signal is not None
    assert signal.timestamp == datetime(2026, 9, 16, 10, 6, tzinfo=ZoneInfo("Asia/Kuala_Lumpur"))


def test_ignores_message_without_cst_timestamp() -> None:
    assert parse_signal("Draw Fibonacci Retracement. Read Pinned Post.") is None


def test_ignores_other_symbols_and_indicators() -> None:
    other_symbol = "PROJECT V || Indicator NQ426\nOtherSymbol\nC.S.T: 2026.09.16 10:06"
    other_indicator = "PROJECT X || Indicator ABC\nFixedVol100\nC.S.T: 2026.09.16 10:06"
    assert parse_signal(other_symbol) is None
    assert parse_signal(other_indicator) is None
