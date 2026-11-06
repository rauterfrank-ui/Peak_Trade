"""
Tests für Data Quality Monitor.

Prüft Gap Detection, Price/Volume Spike Detection.
"""

from __future__ import annotations

import math

import pytest

from src.data.shadow.models import Bar
from src.data.shadow.quality_monitor import DataQualityMonitor


def test_quality_monitor_no_events_for_continuous_bars():
    """Quality Monitor findet keine Events bei lückenlosen Bars."""
    base_ts = 1735347600000
    tf_ms = 60000  # 1m

    bars = [
        Bar(
            start_ts_ms=base_ts,
            end_ts_ms=base_ts + tf_ms,
            open=50000.0,
            high=50010.0,
            low=49990.0,
            close=50000.0,
            volume=1.0,
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
        Bar(
            start_ts_ms=base_ts + tf_ms,
            end_ts_ms=base_ts + 2 * tf_ms,
            open=50000.0,
            high=50010.0,
            low=49990.0,
            close=50005.0,
            volume=1.0,
            vwap=50005.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
    ]

    cfg = {"shadow": {"quality": {"enabled": True}}}
    monitor = DataQualityMonitor(cfg)
    events = monitor.check_bars(bars)

    assert len(events) == 0


def test_quality_monitor_detects_gap():
    """Quality Monitor erkennt Gap (fehlende Bar)."""
    base_ts = 1735347600000
    tf_ms = 60000  # 1m

    bars = [
        Bar(
            start_ts_ms=base_ts,
            end_ts_ms=base_ts + tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=50000.0,
            volume=1.0,
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
        # Gap: missing bar at base_ts + tf_ms
        Bar(
            start_ts_ms=base_ts + 2 * tf_ms,  # Skip one bar
            end_ts_ms=base_ts + 3 * tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=50000.0,
            volume=1.0,
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
    ]

    cfg = {"shadow": {"quality": {"enabled": True, "gap_severity": "WARN"}}}
    monitor = DataQualityMonitor(cfg)
    events = monitor.check_bars(bars)

    gap_events = [e for e in events if e.kind == "GAP"]
    assert len(gap_events) == 1

    event = gap_events[0]
    assert event.severity == "WARN"
    assert event.symbol == "XBT/EUR"
    assert event.details["missing_bars"] == 1


def test_quality_monitor_detects_price_spike():
    """Quality Monitor erkennt Price Spike (große Log-Return)."""
    base_ts = 1735347600000
    tf_ms = 60000

    bars = [
        Bar(
            start_ts_ms=base_ts,
            end_ts_ms=base_ts + tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=50000.0,
            volume=1.0,
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
        Bar(
            start_ts_ms=base_ts + tf_ms,
            end_ts_ms=base_ts + 2 * tf_ms,
            open=50000.0,
            high=60000.0,
            low=50000.0,
            close=60000.0,  # 20% jump
            volume=1.0,
            vwap=55000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
    ]

    cfg = {
        "shadow": {
            "quality": {
                "enabled": True,
                "spike_severity": "WARN",
                "max_abs_log_return": 0.10,  # 10% threshold
            }
        }
    }
    monitor = DataQualityMonitor(cfg)
    events = monitor.check_bars(bars)

    spike_events = [
        e for e in events if e.kind == "SPIKE" and e.details.get("type") == "price_spike"
    ]
    assert len(spike_events) >= 1

    event = spike_events[0]
    assert event.severity == "WARN"
    log_ret = math.log(60000.0 / 50000.0)
    assert event.details["abs_log_return"] == pytest.approx(abs(log_ret), rel=1e-6)


def test_quality_monitor_detects_volume_spike():
    """Quality Monitor erkennt Volume Spike."""
    base_ts = 1735347600000
    tf_ms = 60000

    bars = [
        Bar(
            start_ts_ms=base_ts,
            end_ts_ms=base_ts + tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=50000.0,
            volume=1.0,
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
        Bar(
            start_ts_ms=base_ts + tf_ms,
            end_ts_ms=base_ts + 2 * tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=50000.0,
            volume=1.0,
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
        Bar(
            start_ts_ms=base_ts + 2 * tf_ms,
            end_ts_ms=base_ts + 3 * tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=50000.0,
            volume=20.0,  # 20x median
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
    ]

    cfg = {
        "shadow": {
            "quality": {
                "enabled": True,
                "spike_severity": "WARN",
                "volume_spike_factor": 10.0,  # 10x threshold
            }
        }
    }
    monitor = DataQualityMonitor(cfg)
    events = monitor.check_bars(bars)

    volume_spike_events = [
        e for e in events if e.kind == "SPIKE" and e.details.get("type") == "volume_spike"
    ]
    assert len(volume_spike_events) >= 1

    event = volume_spike_events[0]
    assert event.details["volume"] == 20.0
    assert event.details["factor"] == 20.0  # 20 / median(1, 1, 20) = 20 / 1


def test_quality_monitor_disabled():
    """Quality Monitor gibt leere Liste wenn disabled."""
    bars = []
    cfg = {"shadow": {"quality": {"enabled": False}}}
    monitor = DataQualityMonitor(cfg)
    events = monitor.check_bars(bars)

    assert len(events) == 0


def test_quality_monitor_empty_bars():
    """Quality Monitor gibt leere Liste für leere Bars."""
    cfg = {"shadow": {"quality": {"enabled": True}}}
    monitor = DataQualityMonitor(cfg)
    events = monitor.check_bars([])

    assert len(events) == 0


def test_quality_monitor_custom_thresholds():
    """Quality Monitor respektiert custom thresholds."""
    base_ts = 1735347600000
    tf_ms = 60000

    bars = [
        Bar(
            start_ts_ms=base_ts,
            end_ts_ms=base_ts + tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=50000.0,
            volume=1.0,
            vwap=50000.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
        Bar(
            start_ts_ms=base_ts + tf_ms,
            end_ts_ms=base_ts + 2 * tf_ms,
            open=50000.0,
            high=50000.0,
            low=50000.0,
            close=53000.0,  # ~6% jump
            volume=1.0,
            vwap=51500.0,
            symbol="XBT/EUR",
            timeframe="1m",
        ),
    ]

    # High threshold: should NOT trigger
    cfg_high = {"shadow": {"quality": {"enabled": True, "max_abs_log_return": 0.20}}}
    monitor_high = DataQualityMonitor(cfg_high)
    events_high = monitor_high.check_bars(bars)
    price_spikes_high = [
        e for e in events_high if e.kind == "SPIKE" and e.details.get("type") == "price_spike"
    ]
    assert len(price_spikes_high) == 0

    # Low threshold: should trigger
    cfg_low = {"shadow": {"quality": {"enabled": True, "max_abs_log_return": 0.05}}}
    monitor_low = DataQualityMonitor(cfg_low)
    events_low = monitor_low.check_bars(bars)
    price_spikes_low = [
        e for e in events_low if e.kind == "SPIKE" and e.details.get("type") == "price_spike"
    ]
    assert len(price_spikes_low) >= 1
