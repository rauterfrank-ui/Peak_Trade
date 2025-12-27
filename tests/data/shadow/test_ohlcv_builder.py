"""
Tests für OHLCV Builder.

Prüft Deterministik, OHLC-Korrektheit, Timeframes.
"""

from __future__ import annotations

import pytest

from src.data.shadow.models import Tick
from src.data.shadow.ohlcv_builder import OHLCVBuilder, tf_to_ms


def test_tf_to_ms_minutes():
    """tf_to_ms konvertiert Minuten."""
    assert tf_to_ms("1m") == 60 * 1000
    assert tf_to_ms("5m") == 5 * 60 * 1000
    assert tf_to_ms("15m") == 15 * 60 * 1000


def test_tf_to_ms_hours():
    """tf_to_ms konvertiert Stunden."""
    assert tf_to_ms("1h") == 60 * 60 * 1000
    assert tf_to_ms("4h") == 4 * 60 * 60 * 1000


def test_tf_to_ms_seconds():
    """tf_to_ms konvertiert Sekunden."""
    assert tf_to_ms("30s") == 30 * 1000


def test_tf_to_ms_invalid_format():
    """tf_to_ms wirft bei invalid Format."""
    with pytest.raises(ValueError):
        tf_to_ms("")

    with pytest.raises(ValueError):
        tf_to_ms("invalid")

    with pytest.raises(ValueError):
        tf_to_ms("5x")  # unknown unit


def test_ohlcv_builder_single_bar():
    """OHLCV Builder erstellt Single Bar korrekt."""
    base_ts = 1735347600000  # Aligned to minute

    ticks = [
        Tick(ts_ms=base_ts, price=50000.0, volume=0.1, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts + 10000, price=50010.0, volume=0.2, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts + 20000, price=50005.0, volume=0.15, symbol="XBT/EUR"),
    ]

    builder = OHLCVBuilder(symbol="XBT/EUR", timeframe="1m")
    builder.add_ticks(ticks)
    bars = builder.finalize()

    assert len(bars) == 1
    bar = bars[0]

    # OHLC: first tick by ts = open, last = close
    assert bar.open == 50000.0
    assert bar.close == 50005.0
    assert bar.high == 50010.0
    assert bar.low == 50000.0

    # Volume
    assert bar.volume == 0.1 + 0.2 + 0.15

    # VWAP
    expected_vwap = (50000 * 0.1 + 50010 * 0.2 + 50005 * 0.15) / (0.1 + 0.2 + 0.15)
    assert bar.vwap == pytest.approx(expected_vwap, rel=1e-6)


def test_ohlcv_builder_multiple_bars():
    """OHLCV Builder erstellt Multiple Bars."""
    base_ts = 1735347600000

    ticks = [
        # Minute 1
        Tick(ts_ms=base_ts, price=50000.0, volume=0.1, symbol="XBT/EUR"),
        # Minute 2
        Tick(ts_ms=base_ts + 60000, price=50100.0, volume=0.2, symbol="XBT/EUR"),
    ]

    builder = OHLCVBuilder(symbol="XBT/EUR", timeframe="1m")
    builder.add_ticks(ticks)
    bars = builder.finalize()

    assert len(bars) == 2

    # Bars sortiert nach start_ts_ms
    assert bars[0].start_ts_ms < bars[1].start_ts_ms

    # Bar 1
    assert bars[0].open == 50000.0
    assert bars[0].volume == 0.1

    # Bar 2
    assert bars[1].open == 50100.0
    assert bars[1].volume == 0.2


def test_ohlcv_builder_filters_wrong_symbol():
    """OHLCV Builder filtert Ticks mit falschem Symbol."""
    base_ts = 1735347600000

    ticks = [
        Tick(ts_ms=base_ts, price=50000.0, volume=0.1, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts, price=3000.0, volume=0.5, symbol="ETH/EUR"),  # wrong
    ]

    builder = OHLCVBuilder(symbol="XBT/EUR", timeframe="1m")
    builder.add_ticks(ticks)
    bars = builder.finalize()

    assert len(bars) == 1
    assert bars[0].symbol == "XBT/EUR"
    assert bars[0].volume == 0.1  # Only XBT tick


def test_ohlcv_builder_deterministisch():
    """OHLCV Builder ist deterministisch bei beliebiger Tick-Reihenfolge."""
    base_ts = 1735347600000

    # Ticks in zufälliger Reihenfolge
    ticks_order1 = [
        Tick(ts_ms=base_ts + 20000, price=50005.0, volume=0.15, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts, price=50000.0, volume=0.1, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts + 10000, price=50010.0, volume=0.2, symbol="XBT/EUR"),
    ]

    ticks_order2 = [
        Tick(ts_ms=base_ts + 10000, price=50010.0, volume=0.2, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts + 20000, price=50005.0, volume=0.15, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts, price=50000.0, volume=0.1, symbol="XBT/EUR"),
    ]

    builder1 = OHLCVBuilder(symbol="XBT/EUR", timeframe="1m")
    builder1.add_ticks(ticks_order1)
    bars1 = builder1.finalize()

    builder2 = OHLCVBuilder(symbol="XBT/EUR", timeframe="1m")
    builder2.add_ticks(ticks_order2)
    bars2 = builder2.finalize()

    # Sollten identisch sein
    assert len(bars1) == len(bars2)
    assert bars1[0].open == bars2[0].open
    assert bars1[0].close == bars2[0].close
    assert bars1[0].high == bars2[0].high
    assert bars1[0].low == bars2[0].low


def test_ohlcv_builder_5m_timeframe():
    """OHLCV Builder funktioniert mit 5m Timeframe."""
    base_ts = 1735347600000  # Aligned to 5m

    ticks = [
        # First 5m window
        Tick(ts_ms=base_ts, price=50000.0, volume=0.1, symbol="XBT/EUR"),
        Tick(ts_ms=base_ts + 60000, price=50100.0, volume=0.2, symbol="XBT/EUR"),
        # Second 5m window
        Tick(ts_ms=base_ts + 300000, price=50200.0, volume=0.3, symbol="XBT/EUR"),
    ]

    builder = OHLCVBuilder(symbol="XBT/EUR", timeframe="5m")
    builder.add_ticks(ticks)
    bars = builder.finalize()

    assert len(bars) == 2

    # First bar: 2 ticks
    assert bars[0].volume == 0.1 + 0.2

    # Second bar: 1 tick
    assert bars[1].volume == 0.3
