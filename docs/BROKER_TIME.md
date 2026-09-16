# Broker time

Telegram signal timestamps are confirmed to match the MT5 broker candle timestamps.
The signal timestamp is therefore treated as broker time and is not converted from
an assumed Telegram timezone.

`BROKER_TIMEZONE` in `config/settings.py` is the canonical timezone representation
used to keep timestamps timezone-aware. It identifies the broker-time representation;
it does not trigger a Telegram-to-broker conversion.
