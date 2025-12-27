"""
Tick Normalizer — Kraken WebSocket Trade Message Parser.

Parsed Kraken WS Trade-Messages zu standardisierten Tick-Objekten.
"""

from __future__ import annotations

import logging
from typing import Any, Union

from src.data.shadow.models import Tick

logger = logging.getLogger(__name__)


def parse_kraken_trade_message(msg: Any) -> list[Tick]:
    """
    Parsed eine Kraken WS Trade Message.

    Kraken Format:
    [
        channelID,
        [[price, volume, time, side, orderType, misc], ...],
        "trade",
        "XBT/EUR"
    ]

    Args:
        msg: Rohe Message (typisch list/dict)

    Returns:
        List[Tick]: Parsed Ticks (leer wenn nicht parsebar)
    """
    try:
        # Defensive: muss list sein
        if not isinstance(msg, list):
            return []

        # Minimum length check
        if len(msg) < 4:
            return []

        # [channelID, trades, channelName, symbol]
        channel_id, trades_data, channel_name, symbol = msg[0], msg[1], msg[2], msg[3]

        # Channel-Name check
        if channel_name != "trade":
            return []

        # Trades muss list sein
        if not isinstance(trades_data, list):
            return []

        ticks = []
        for trade in trades_data:
            try:
                # trade = [price, volume, time, side, orderType, misc]
                if not isinstance(trade, list) or len(trade) < 3:
                    continue

                price_str, volume_str, time_float = trade[0], trade[1], trade[2]

                # Parse
                price = float(price_str)
                volume = float(volume_str)
                time_sec = float(time_float)
                ts_ms = int(time_sec * 1000)

                # Filter invalid
                if price <= 0 or volume <= 0 or ts_ms <= 0:
                    continue

                tick = Tick(
                    ts_ms=ts_ms,
                    price=price,
                    volume=volume,
                    symbol=symbol,
                    source="kraken_ws",
                )
                ticks.append(tick)

            except (ValueError, TypeError, IndexError) as e:
                logger.debug(f"Skipping unparseable trade: {trade} — {e}")
                continue

        return ticks

    except Exception as e:
        logger.warning(f"Failed to parse Kraken trade message: {msg} — {e}")
        return []


def normalize_ticks_from_messages(messages: list[Any]) -> list[Tick]:
    """
    Parsed Liste von Messages, flattet Ticks und sortiert.

    Args:
        messages: Liste von Kraken WS Messages

    Returns:
        List[Tick]: Sortiert nach ts_ms, filtered (price/volume > 0)
    """
    all_ticks: list[Tick] = []

    for msg in messages:
        ticks = parse_kraken_trade_message(msg)
        all_ticks.extend(ticks)

    # Filter invalid (sollte schon in parse passiert sein, aber doppelt sicher)
    valid_ticks = [t for t in all_ticks if t.price > 0 and t.volume > 0]

    # Sort nach ts_ms
    valid_ticks.sort(key=lambda t: t.ts_ms)

    return valid_ticks
