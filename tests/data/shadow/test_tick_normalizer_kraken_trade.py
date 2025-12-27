"""
Tests für Kraken Trade Message Normalizer.

Prüft Parsing, Filtering, Sorting.
"""

from __future__ import annotations

import pytest

from src.data.shadow.tick_normalizer import (
    normalize_ticks_from_messages,
    parse_kraken_trade_message,
)


def test_parse_kraken_trade_message_single_trade():
    """Parsed Single Trade korrekt."""
    msg = [
        123,  # channelID
        [
            ["50000.0", "0.1", 1735347600.0, "b", "l", ""],  # price, vol, time, ...
        ],
        "trade",
        "XBT/EUR",
    ]

    ticks = parse_kraken_trade_message(msg)

    assert len(ticks) == 1
    tick = ticks[0]
    assert tick.symbol == "XBT/EUR"
    assert tick.price == 50000.0
    assert tick.volume == 0.1
    assert tick.ts_ms == 1735347600000  # seconds → ms


def test_parse_kraken_trade_message_multiple_trades():
    """Parsed Multiple Trades."""
    msg = [
        123,
        [
            ["50000.0", "0.1", 1735347600.0, "b", "l", ""],
            ["50010.0", "0.2", 1735347610.0, "s", "l", ""],
        ],
        "trade",
        "XBT/EUR",
    ]

    ticks = parse_kraken_trade_message(msg)

    assert len(ticks) == 2
    assert ticks[0].price == 50000.0
    assert ticks[1].price == 50010.0


def test_parse_kraken_trade_message_filters_invalid_price():
    """Filtert Trades mit price <= 0."""
    msg = [
        123,
        [
            ["0.0", "0.1", 1735347600.0, "b", "l", ""],  # price=0
            ["50000.0", "0.1", 1735347600.0, "b", "l", ""],  # valid
        ],
        "trade",
        "XBT/EUR",
    ]

    ticks = parse_kraken_trade_message(msg)

    assert len(ticks) == 1
    assert ticks[0].price == 50000.0


def test_parse_kraken_trade_message_filters_invalid_volume():
    """Filtert Trades mit volume <= 0."""
    msg = [
        123,
        [
            ["50000.0", "0.0", 1735347600.0, "b", "l", ""],  # volume=0
            ["50000.0", "0.1", 1735347600.0, "b", "l", ""],  # valid
        ],
        "trade",
        "XBT/EUR",
    ]

    ticks = parse_kraken_trade_message(msg)

    assert len(ticks) == 1
    assert ticks[0].volume == 0.1


def test_parse_kraken_trade_message_ignores_non_trade_channel():
    """Ignoriert Non-Trade Channels (z.B. heartbeat)."""
    msg = [
        123,
        [],
        "heartbeat",  # NOT "trade"
        "",
    ]

    ticks = parse_kraken_trade_message(msg)

    assert len(ticks) == 0


def test_parse_kraken_trade_message_ignores_invalid_format():
    """Ignoriert Messages mit falschem Format."""
    # Not a list
    assert parse_kraken_trade_message("invalid") == []

    # Too short
    assert parse_kraken_trade_message([1, 2]) == []

    # Trades not a list
    assert parse_kraken_trade_message([123, "notalist", "trade", "XBT/EUR"]) == []


def test_normalize_ticks_from_messages_sorts_by_ts():
    """normalize_ticks_from_messages sortiert nach ts_ms."""
    msg1 = [123, [["50000.0", "0.1", 1735347610.0, "b", "l", ""]], "trade", "XBT/EUR"]
    msg2 = [123, [["50010.0", "0.1", 1735347600.0, "b", "l", ""]], "trade", "XBT/EUR"]

    ticks = normalize_ticks_from_messages([msg1, msg2])

    assert len(ticks) == 2
    # Should be sorted by ts_ms (msg2 first)
    assert ticks[0].ts_ms == 1735347600000
    assert ticks[1].ts_ms == 1735347610000


def test_normalize_ticks_from_messages_flattens_multiple_messages():
    """normalize_ticks_from_messages flattet Messages."""
    msg1 = [123, [["50000.0", "0.1", 1735347600.0, "b", "l", ""]], "trade", "XBT/EUR"]
    msg2 = [123, [["50010.0", "0.1", 1735347610.0, "b", "l", ""]], "trade", "XBT/EUR"]

    ticks = normalize_ticks_from_messages([msg1, msg2])

    assert len(ticks) == 2


def test_normalize_ticks_from_messages_filters_invalid():
    """normalize_ticks_from_messages filtert invalid Ticks."""
    msg = [
        123,
        [
            ["0.0", "0.1", 1735347600.0, "b", "l", ""],  # price=0
            ["50000.0", "0.0", 1735347600.0, "b", "l", ""],  # volume=0
            ["50010.0", "0.1", 1735347600.0, "b", "l", ""],  # valid
        ],
        "trade",
        "XBT/EUR",
    ]

    ticks = normalize_ticks_from_messages([msg])

    assert len(ticks) == 1
    assert ticks[0].price == 50010.0
