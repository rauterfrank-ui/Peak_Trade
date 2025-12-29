"""
Tests for WP1A - Bar Aggregation

Tests:
- Tick to bar conversion
- Timeframe alignment
- OHLCV correctness
- Normalization consistency with backtest
"""

import pytest

from src.data.shadow.bar_aggregator import BarAggregator
from src.data.shadow.models import Tick


class TestBarAggregator:
    """Test suite for BarAggregator."""

    def test_single_tick_bar(self):
        """Test bar from single tick."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        tick = Tick(
            ts_ms=1000_000,  # 1000 seconds
            price=50000.0,
            volume=0.5,
            symbol="BTC/EUR",
        )

        bar = aggregator.add_tick(tick)

        # First tick should not emit bar yet
        assert bar is None

        # Check buffer stats
        stats = aggregator.get_stats()
        assert stats["ticks_processed"] == 1
        assert stats["bars_emitted"] == 0
        assert stats["active_buffers"] == 1

    def test_multiple_ticks_same_bar(self):
        """Test multiple ticks in same bar."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        # All ticks within same 1-minute window
        # Bar: [960_000, 1_020_000) - so ticks must be < 1_020_000
        base_ts_ms = 960_000
        ticks = [
            Tick(
                ts_ms=base_ts_ms + 0, price=50000.0, volume=0.5, symbol="BTC/EUR"
            ),
            Tick(
                ts_ms=base_ts_ms + 10_000,
                price=51000.0,
                volume=0.3,
                symbol="BTC/EUR",
            ),
            Tick(
                ts_ms=base_ts_ms + 20_000,
                price=49000.0,
                volume=0.2,
                symbol="BTC/EUR",
            ),
        ]

        bars = []
        for tick in ticks:
            bar = aggregator.add_tick(tick)
            if bar:
                bars.append(bar)

        # No bars emitted yet (all in same window)
        assert len(bars) == 0

        stats = aggregator.get_stats()
        assert stats["ticks_processed"] == 3
        assert stats["bars_emitted"] == 0

    def test_tick_triggers_bar_emission(self):
        """Test tick crossing timeframe boundary emits bar."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        # Ticks spanning two 1-minute windows
        # First bar: [960_000, 1_020_000)
        # Second bar: [1_020_000, 1_080_000)
        base_ts_ms = 960_000
        ticks = [
            Tick(
                ts_ms=base_ts_ms + 0, price=50000.0, volume=0.5, symbol="BTC/EUR"
            ),
            Tick(
                ts_ms=base_ts_ms + 30_000,
                price=51000.0,
                volume=0.3,
                symbol="BTC/EUR",
            ),
            Tick(
                ts_ms=base_ts_ms + 60_000,  # Next bar (at boundary)
                price=52000.0,
                volume=0.2,
                symbol="BTC/EUR",
            ),
        ]

        bars = []
        for tick in ticks:
            bar = aggregator.add_tick(tick)
            if bar:
                bars.append(bar)

        # Should emit one bar (first window)
        assert len(bars) == 1

        bar = bars[0]
        assert bar.symbol == "BTC/EUR"
        assert bar.timeframe == "1m"
        assert bar.open == 50000.0
        assert bar.high == 51000.0
        assert bar.low == 50000.0
        assert bar.close == 51000.0
        assert bar.volume == 0.8  # 0.5 + 0.3

        stats = aggregator.get_stats()
        assert stats["bars_emitted"] == 1

    def test_ohlc_correctness(self):
        """Test OHLC values are calculated correctly."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        # Bar: [960_000, 1_020_000)
        base_ts_ms = 960_000
        ticks = [
            Tick(ts_ms=base_ts_ms + 0, price=100.0, volume=1.0, symbol="BTC/EUR"),
            Tick(ts_ms=base_ts_ms + 10_000, price=110.0, volume=1.0, symbol="BTC/EUR"),  # High
            Tick(ts_ms=base_ts_ms + 20_000, price=90.0, volume=1.0, symbol="BTC/EUR"),  # Low
            Tick(ts_ms=base_ts_ms + 30_000, price=105.0, volume=1.0, symbol="BTC/EUR"),  # Close
            Tick(ts_ms=base_ts_ms + 60_000, price=200.0, volume=1.0, symbol="BTC/EUR"),  # Next bar
        ]

        bars = []
        for tick in ticks:
            bar = aggregator.add_tick(tick)
            if bar:
                bars.append(bar)

        assert len(bars) == 1

        bar = bars[0]
        assert bar.open == 100.0  # First tick
        assert bar.high == 110.0  # Highest
        assert bar.low == 90.0  # Lowest
        assert bar.close == 105.0  # Last tick
        assert bar.volume == 4.0  # Sum

    def test_multiple_symbols(self):
        """Test aggregator handles multiple symbols independently."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        base_ts_ms = 1000_000
        ticks = [
            Tick(ts_ms=base_ts_ms + 0, price=50000.0, volume=0.5, symbol="BTC/EUR"),
            Tick(ts_ms=base_ts_ms + 0, price=2000.0, volume=1.0, symbol="ETH/EUR"),
            Tick(ts_ms=base_ts_ms + 60_000, price=50100.0, volume=0.3, symbol="BTC/EUR"),
            Tick(ts_ms=base_ts_ms + 60_000, price=2010.0, volume=0.8, symbol="ETH/EUR"),
        ]

        bars = []
        for tick in ticks:
            bar = aggregator.add_tick(tick)
            if bar:
                bars.append(bar)

        # Should emit 2 bars (one per symbol)
        assert len(bars) == 2

        symbols = {bar.symbol for bar in bars}
        assert symbols == {"BTC/EUR", "ETH/EUR"}

    def test_flush(self):
        """Test flushing pending bars."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        base_ts_ms = 1000_000
        tick = Tick(
            ts_ms=base_ts_ms, price=50000.0, volume=0.5, symbol="BTC/EUR"
        )
        aggregator.add_tick(tick)

        # No bars emitted yet
        stats = aggregator.get_stats()
        assert stats["bars_emitted"] == 0

        # Flush
        bars = aggregator.flush()

        assert len(bars) == 1
        assert bars[0].symbol == "BTC/EUR"
        assert bars[0].close == 50000.0

        stats = aggregator.get_stats()
        assert stats["bars_emitted"] == 1
        assert stats["active_buffers"] == 0

    def test_flush_specific_symbol(self):
        """Test flushing specific symbol."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        base_ts_ms = 1000_000
        ticks = [
            Tick(ts_ms=base_ts_ms, price=50000.0, volume=0.5, symbol="BTC/EUR"),
            Tick(ts_ms=base_ts_ms, price=2000.0, volume=1.0, symbol="ETH/EUR"),
        ]

        for tick in ticks:
            aggregator.add_tick(tick)

        # Flush only BTC
        bars = aggregator.flush(symbol="BTC/EUR")

        assert len(bars) == 1
        assert bars[0].symbol == "BTC/EUR"

        # ETH should still be buffered
        stats = aggregator.get_stats()
        assert stats["active_buffers"] == 1

    def test_timeframe_alignment(self):
        """Test bars are aligned to timeframe boundaries."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        # Tick at arbitrary timestamp
        tick = Tick(
            ts_ms=1_234_567_890,  # Not aligned
            price=50000.0,
            volume=0.5,
            symbol="BTC/EUR",
        )
        aggregator.add_tick(tick)

        # Trigger emit
        next_tick = Tick(
            ts_ms=1_234_567_890 + 60_000,
            price=50100.0,
            volume=0.3,
            symbol="BTC/EUR",
        )
        bar = aggregator.add_tick(next_tick)

        assert bar is not None

        # Bar should be aligned to 1-minute boundary
        assert bar.start_ts_ms % 60_000 == 0
        assert bar.end_ts_ms == bar.start_ts_ms + 60_000


class TestNormalizationConsistency:
    """Test bar normalization consistency with backtest."""

    def test_bar_schema_matches_backtest(self):
        """Test bar schema matches backtest OHLCV schema."""
        aggregator = BarAggregator(timeframe_ms=60_000, timeframe_str="1m")

        base_ts_ms = 1000_000
        ticks = [
            Tick(ts_ms=base_ts_ms + 0, price=100.0, volume=1.0, symbol="BTC/EUR"),
            Tick(ts_ms=base_ts_ms + 60_000, price=200.0, volume=1.0, symbol="BTC/EUR"),
        ]

        bars = []
        for tick in ticks:
            bar = aggregator.add_tick(tick)
            if bar:
                bars.append(bar)

        bar = bars[0]

        # Check all required fields exist
        assert hasattr(bar, "start_ts_ms")
        assert hasattr(bar, "end_ts_ms")
        assert hasattr(bar, "open")
        assert hasattr(bar, "high")
        assert hasattr(bar, "low")
        assert hasattr(bar, "close")
        assert hasattr(bar, "volume")
        assert hasattr(bar, "symbol")
        assert hasattr(bar, "timeframe")

        # Check types
        assert isinstance(bar.start_ts_ms, int)
        assert isinstance(bar.open, float)
        assert isinstance(bar.volume, float)

    def test_bar_validation_rules(self):
        """Test bars pass same validation as backtest bars."""
        from src.data.shadow.models import Bar

        # Valid bar (should not raise)
        bar = Bar(
            start_ts_ms=1000_000,
            end_ts_ms=1060_000,
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=10.0,
            vwap=None,
            symbol="BTC/EUR",
            timeframe="1m",
        )

        # Should not raise
        assert bar.start_ts_ms < bar.end_ts_ms

        # Invalid bar (should raise)
        with pytest.raises(ValueError, match="Invalid bar times"):
            Bar(
                start_ts_ms=1060_000,  # After end
                end_ts_ms=1000_000,
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=10.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            )
