#!/usr/bin/env python3
"""
Shadow Pipeline Smoke Test — Tick→OHLCV + Quality (Offline).

Testet:
- Kraken Trade Message Parsing
- Tick Normalization
- OHLCV Building (1m)
- Quality Monitoring (Gaps, Spikes)

NO NETWORK: Komplett offline mit Beispiel-Daten.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.shadow.ohlcv_builder import OHLCVBuilder
from src.data.shadow.quality_monitor import DataQualityMonitor
from src.data.shadow.tick_normalizer import normalize_ticks_from_messages


def main() -> int:
    """
    Führt Offline-Smoke-Test aus.

    Returns:
        0 = OK, 1 = FAIL
    """
    print("━" * 60)
    print("🎭 Shadow Pipeline Smoke Test: Tick→OHLCV + Quality")
    print("━" * 60)

    try:
        # 1) Beispiel Kraken Trade Messages (offline)
        print("\n1️⃣  Kraken Trade Messages (Beispiel)...")

        # Simuliere 3 Trades für BTC in 1-Minute-Window
        # Format: [channelID, [[price, volume, time, side, type, misc], ...], "trade", "XBT/EUR"]
        base_ts = 1735347600.0  # 2025-12-28 00:00:00 UTC

        messages = [
            [
                123,
                [
                    ["50000.0", "0.1", base_ts, "b", "l", ""],
                    ["50010.0", "0.2", base_ts + 10, "b", "l", ""],
                ],
                "trade",
                "XBT/EUR",
            ],
            [
                123,
                [
                    ["50020.0", "0.15", base_ts + 20, "s", "l", ""],
                ],
                "trade",
                "XBT/EUR",
            ],
            # Trade mit Gap (nächste Minute)
            [
                123,
                [
                    ["50100.0", "0.3", base_ts + 120, "b", "l", ""],
                ],
                "trade",
                "XBT/EUR",
            ],
        ]

        print(f"   ✅ {len(messages)} Beispiel-Messages erstellt")

        # 2) Tick Normalization
        print("\n2️⃣  Tick Normalization...")
        ticks = normalize_ticks_from_messages(messages)
        print(f"   ✅ {len(ticks)} Ticks normalisiert")

        # Verify
        assert len(ticks) == 4, f"Expected 4 ticks, got {len(ticks)}"
        assert ticks[0].symbol == "XBT/EUR"
        assert ticks[0].price == 50000.0

        # 3) OHLCV Building (1m)
        print("\n3️⃣  OHLCV Building (1m)...")
        builder = OHLCVBuilder(symbol="XBT/EUR", timeframe="1m")
        builder.add_ticks(ticks)
        bars = builder.finalize()

        print(f"   ✅ {len(bars)} Bars erstellt")

        for bar in bars:
            print(
                f"      - Bar: start={bar.start_ts_ms}, O={bar.open}, H={bar.high}, "
                f"L={bar.low}, C={bar.close}, V={bar.volume}, VWAP={bar.vwap:.2f}"
            )

        # Verify
        assert len(bars) == 2, (
            f"Expected 2 bars (1 trade in minute 1, 1 in minute 3), got {len(bars)}"
        )

        # First bar: 3 ticks (50000, 50010, 50020)
        bar1 = bars[0]
        assert bar1.open == 50000.0, f"Expected open=50000, got {bar1.open}"
        assert bar1.close == 50020.0, f"Expected close=50020, got {bar1.close}"
        assert bar1.high == 50020.0
        assert bar1.low == 50000.0

        # 4) Quality Monitoring
        print("\n4️⃣  Quality Monitoring (Gaps + Spikes)...")

        cfg = {
            "shadow": {
                "quality": {
                    "gap_severity": "WARN",
                    "spike_severity": "WARN",
                    "max_abs_log_return": 0.10,
                    "volume_spike_factor": 10.0,
                }
            }
        }

        monitor = DataQualityMonitor(cfg)
        events = monitor.check_bars(bars)

        print(f"   ✅ {len(events)} Quality Events gefunden")

        for event in events:
            print(f"      - {event.kind}: {event.severity} @ {event.ts_ms}")
            print(f"        Details: {event.details}")

        # Expect: 1 GAP (missing bar zwischen Minute 1 und 3)
        gap_events = [e for e in events if e.kind == "GAP"]
        assert len(gap_events) >= 1, "Expected at least 1 GAP event"

        print("\n" + "━" * 60)
        print("✅ Alle Smoke-Tests bestanden!")
        print("━" * 60)
        return 0

    except Exception as e:
        print("\n" + "━" * 60)
        print(f"❌ FAIL: {e}")
        print("━" * 60)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
