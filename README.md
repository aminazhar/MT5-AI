# Telegram → MT5 Fibonacci Demo Agent

This repository currently implements only the deterministic calculation foundation:

- A validated, timezone-aware OHLC `Candle` model.
- Wick-based Fibonacci calculations with configurable direction.
- An intentionally empty Fibonacci configuration.
- A placeholder E3/E4/E5 interface; no formulas have been assumed.

The Telegram test reader is implemented for an account authorized to access its configured channel. It only extracts and reports C.S.T. timestamps. MetaTrader 5, validation, and execution integrations are deliberately not implemented yet. No code in this project can place an order.

## Run the tests

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

Fibonacci ratios in tests are fixtures used to verify arithmetic only. Add your actual strategy levels to `config/settings.py` when you provide them.

## Read a closed MT5 candle

Start your local MT5 terminal, then run:

```powershell
python -m market.candles --timestamp "2026-09-16 10:33" --symbol FixedVol100
```

This is read-only. It uses the account already connected in your local terminal only to retrieve the M1 candle at the broker/CST timestamp, then displays OHLC plus Fibonacci levels. It has no order, position, or trade-execution code. Telegram signal timestamps are already confirmed to match the MT5 broker candle timestamps, so they are used directly without timezone conversion. The canonical broker timestamp timezone is configured by `BROKER_TIMEZONE`.

## Test the authorized Telegram reader

1. Ensure your local `.env` contains `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_CHANNEL`. The channel value can be its exact display title, public username, or numeric channel ID.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Start the listener: `python -m telegram.reader`.

On its first run, Telegram asks for the account phone number and login code. The local session file is placed in `data/` and excluded from Git. The reader currently accepts only `PROJECT V || Indicator NQ426` messages for `FixedVol100`, with a timestamp such as `C.S.T : 2026:09.16 10:06`; it ignores other symbols. Stop it with `Ctrl+C`.
