"""Read-only connection helper for a locally running MetaTrader 5 terminal."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def connected_terminal() -> Iterator[object]:
    """Yield a read-only MT5 API connection to the already-running terminal.

    This function never logs in, submits orders, modifies orders, or calls a
    trading API. It only uses the account already connected in the local MT5
    terminal, whether demo or live, to retrieve market data.
    """
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError("MetaTrader5 is not installed. Run: python -m pip install -r requirements.txt") from exc

    if not mt5.initialize():
        raise RuntimeError(f"Unable to initialize local MT5 terminal: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        if account is None:
            raise RuntimeError(f"Unable to read MT5 account details: {mt5.last_error()}")
        yield mt5
    finally:
        mt5.shutdown()
