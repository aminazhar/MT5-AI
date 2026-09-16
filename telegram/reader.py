"""Authorized Telegram signal reader; it only reports parsed timestamps."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from config.settings import BROKER_TIMEZONE, TARGET_SYMBOL

LOGGER = logging.getLogger(__name__)
TIMESTAMP_PATTERN = re.compile(
    r"\bC\.S\.T\s*:\s*(?P<date>\d{4}[.:\-]\d{2}[.:\-]\d{2})\s+(?P<time>\d{2}:\d{2})\b",
    re.IGNORECASE,
)
INDICATOR_PATTERN = re.compile(r"PROJECT\s+V\s*\|{1,2}\s*INDICATOR\s+NQ426", re.IGNORECASE)
SYMBOL_PATTERN = re.compile(rf"\b{re.escape(TARGET_SYMBOL)}\b", re.IGNORECASE)


@dataclass(frozen=True)
class TelegramSignal:
    """The intentionally minimal data available from the supplied signal format."""

    timestamp: datetime
    direction: str | None = None


def parse_signal(message_text: str) -> TelegramSignal | None:
    """Parse the configured message format using its timestamp as broker time."""
    if not INDICATOR_PATTERN.search(message_text) or not SYMBOL_PATTERN.search(message_text):
        return None
    match = TIMESTAMP_PATTERN.search(message_text)
    if match is None:
        return None
    normalized_date = re.sub(r"[.:]", "-", match.group("date"))
    try:
        timestamp = datetime.strptime(
            f"{normalized_date} {match.group('time')}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=ZoneInfo(BROKER_TIMEZONE))
    except ValueError as exc:
        raise ValueError(f"Invalid broker signal timestamp or timezone: {BROKER_TIMEZONE}.") from exc
    return TelegramSignal(timestamp=timestamp)


def _required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required. Add it to your local .env file.")
    return value


def _channel_reference(channel: str) -> str | int:
    return int(channel) if channel.lstrip("-").isdigit() else channel


async def _resolve_authorized_channel(client: object, configured_channel: str) -> object:
    """Resolve a username/ID, or an exact display title from authorized dialogs."""
    reference = _channel_reference(configured_channel)
    try:
        return await client.get_input_entity(reference)
    except ValueError:
        if not isinstance(reference, str):
            raise RuntimeError(f"Cannot find Telegram channel ID {reference}.") from None

    matches: list[object] = []
    async for dialog in client.iter_dialogs():
        if dialog.name.casefold() == reference.casefold():
            matches.append(dialog.entity)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError(
            f'More than one authorized chat is named "{configured_channel}". '
            "Set TELEGRAM_CHANNEL to its numeric channel ID instead."
        )
    raise RuntimeError(
        f'No authorized Telegram chat named "{configured_channel}" was found. '
        "Use its exact display title, public username, or numeric channel ID."
    )


async def watch_channel() -> None:
    """Listen to new messages from one channel that this account can access."""
    from telethon import TelegramClient, events

    load_dotenv()
    api_id = int(_required_environment("TELEGRAM_API_ID"))
    api_hash = _required_environment("TELEGRAM_API_HASH")
    channel = _required_environment("TELEGRAM_CHANNEL")
    session_path = os.getenv("TELEGRAM_SESSION_PATH", "data/telegram_reader")
    Path(session_path).parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(session_path, api_id, api_hash)

    await client.start()
    channel_entity = await _resolve_authorized_channel(client, channel)

    @client.on(events.NewMessage(chats=channel_entity))
    async def handle_new_message(event: object) -> None:
        signal = parse_signal(getattr(event, "raw_text", ""))
        if signal is None:
            LOGGER.info("New channel message has no supported C.S.T. timestamp.")
            return
        LOGGER.info("Signal timestamp received: %s", signal.timestamp.isoformat())
        print(f"Signal timestamp: {signal.timestamp.isoformat()}")

    LOGGER.info("Listening for new messages from the authorized configured channel.")
    await client.run_until_disconnected()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(watch_channel())


if __name__ == "__main__":
    main()
