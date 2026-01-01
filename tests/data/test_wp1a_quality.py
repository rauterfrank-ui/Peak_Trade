"""
Tests for WP1A - Live Quality Checks

Tests:
- Timestamp monotonicity
- Gap detection
- Staleness detection
"""

import pytest

from src.data.shadow.live_quality_checks import LiveQualityChecker
from src.data.shadow.models import Bar, Tick


class TestLiveQualityChecker:
    """Test suite for LiveQualityChecker."""

    def test_monotonic_ticks(self):
        """Test monotonic ticks pass without issues."""
        checker = LiveQualityChecker()

        ticks = [
            Tick(ts_ms=1000_000, price=50000.0, volume=0.5, symbol="BTC/EUR"),
            Tick(ts_ms=1010_000, price=50100.0, volume=0.3, symbol="BTC/EUR"),
            Tick(ts_ms=1020_000, price=50200.0, volume=0.2, symbol="BTC/EUR"),
        ]

        for tick in ticks:
            issues = checker.check_tick(tick)
            assert len(issues) == 0

        stats = checker.get_stats()
        assert stats["issues_found"] == 0

    def test_non_monotonic_tick_detected(self):
        """Test non-monotonic tick is detected."""
        checker = LiveQualityChecker()

        ticks = [
            Tick(ts_ms=1000_000, price=50000.0, volume=0.5, symbol="BTC/EUR"),
            Tick(ts_ms=1010_000, price=50100.0, volume=0.3, symbol="BTC/EUR"),
            Tick(ts_ms=1005_000, price=50050.0, volume=0.2, symbol="BTC/EUR"),  # Earlier!
        ]

        all_issues = []
        for tick in ticks:
            issues = checker.check_tick(tick)
            all_issues.extend(issues)

        assert len(all_issues) == 1

        issue = all_issues[0]
        assert issue.kind == "NON_MONOTONIC_TICK"
        assert issue.severity == "WARN"
        assert issue.symbol == "BTC/EUR"
        assert issue.ts_ms == 1005_000

        stats = checker.get_stats()
        assert stats["issues_found"] == 1

    def test_monotonic_bars(self):
        """Test monotonic bars pass without issues."""
        checker = LiveQualityChecker()

        bars = [
            Bar(
                start_ts_ms=1000_000,
                end_ts_ms=1060_000,
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=10.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
            Bar(
                start_ts_ms=1060_000,
                end_ts_ms=1120_000,
                open=50050.0,
                high=50200.0,
                low=50000.0,
                close=50100.0,
                volume=12.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
        ]

        for bar in bars:
            issues = checker.check_bar(bar, timeframe_ms=60_000)
            assert len(issues) == 0

        stats = checker.get_stats()
        assert stats["issues_found"] == 0

    def test_non_monotonic_bar_detected(self):
        """Test non-monotonic bar is detected."""
        checker = LiveQualityChecker()

        bars = [
            Bar(
                start_ts_ms=1060_000,
                end_ts_ms=1120_000,
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=10.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
            Bar(
                start_ts_ms=1000_000,  # Earlier!
                end_ts_ms=1060_000,
                open=50050.0,
                high=50200.0,
                low=50000.0,
                close=50100.0,
                volume=12.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
        ]

        all_issues = []
        for bar in bars:
            issues = checker.check_bar(bar)
            all_issues.extend(issues)

        assert len(all_issues) == 1

        issue = all_issues[0]
        assert issue.kind == "NON_MONOTONIC_BAR"
        assert issue.severity == "WARN"
        assert issue.symbol == "BTC/EUR"

    def test_missing_bar_detected(self):
        """Test missing bar (gap) is detected."""
        checker = LiveQualityChecker()

        bars = [
            Bar(
                start_ts_ms=1000_000,
                end_ts_ms=1060_000,
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=10.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
            Bar(
                start_ts_ms=1180_000,  # Gap: skipped 1060-1120 and 1120-1180
                end_ts_ms=1240_000,
                open=50100.0,
                high=50200.0,
                low=50050.0,
                close=50150.0,
                volume=12.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
        ]

        all_issues = []
        for bar in bars:
            issues = checker.check_bar(bar, timeframe_ms=60_000)
            all_issues.extend(issues)

        assert len(all_issues) == 1

        issue = all_issues[0]
        assert issue.kind == "MISSING_BAR"
        assert issue.severity == "WARN"
        assert issue.details["missing_bars"] == 2  # Two bars missing

    def test_missing_bar_severity_block(self):
        """Test missing bar severity escalates to BLOCK for large gaps."""
        checker = LiveQualityChecker()

        bars = [
            Bar(
                start_ts_ms=1000_000,
                end_ts_ms=1060_000,
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=10.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
            Bar(
                start_ts_ms=1360_000,  # Gap: 6 bars (5+ triggers BLOCK)
                end_ts_ms=1420_000,
                open=50100.0,
                high=50200.0,
                low=50050.0,
                close=50150.0,
                volume=12.0,
                vwap=None,
                symbol="BTC/EUR",
                timeframe="1m",
            ),
        ]

        all_issues = []
        for bar in bars:
            issues = checker.check_bar(bar, timeframe_ms=60_000)
            all_issues.extend(issues)

        assert len(all_issues) == 1

        issue = all_issues[0]
        assert issue.kind == "MISSING_BAR"
        assert issue.severity == "BLOCK"  # Escalated
        assert issue.details["missing_bars"] == 5

    def test_staleness_detection(self):
        """Test staleness detection."""
        checker = LiveQualityChecker(stale_threshold_ms=10_000)

        # First tick
        tick1 = Tick(ts_ms=1000_000, price=50000.0, volume=0.5, symbol="BTC/EUR")
        checker.check_tick(tick1)

        # Check staleness after 5 seconds (not stale)
        issue = checker.check_staleness(current_ts_ms=1005_000, symbol="BTC/EUR")
        assert issue is None

        # Check staleness after 15 seconds (stale)
        issue = checker.check_staleness(current_ts_ms=1015_000, symbol="BTC/EUR")

        assert issue is not None
        assert issue.kind == "STALE_DATA"
        assert issue.severity == "WARN"
        assert issue.details["staleness_ms"] == 15_000

    def test_multiple_symbols_independent(self):
        """Test quality checks are independent per symbol."""
        checker = LiveQualityChecker()

        # BTC ticks
        btc_ticks = [
            Tick(ts_ms=1000_000, price=50000.0, volume=0.5, symbol="BTC/EUR"),
            Tick(ts_ms=1010_000, price=50100.0, volume=0.3, symbol="BTC/EUR"),
        ]

        # ETH ticks (non-monotonic)
        eth_ticks = [
            Tick(ts_ms=2000_000, price=2000.0, volume=1.0, symbol="ETH/EUR"),
            Tick(ts_ms=1990_000, price=1990.0, volume=0.8, symbol="ETH/EUR"),  # Earlier!
        ]

        all_issues = []
        for tick in btc_ticks + eth_ticks:
            issues = checker.check_tick(tick)
            all_issues.extend(issues)

        # Only ETH should have issue
        assert len(all_issues) == 1
        assert all_issues[0].symbol == "ETH/EUR"

    def test_checker_reset(self):
        """Test checker reset clears state."""
        checker = LiveQualityChecker()

        tick = Tick(ts_ms=1000_000, price=50000.0, volume=0.5, symbol="BTC/EUR")
        checker.check_tick(tick)

        stats_before = checker.get_stats()
        assert stats_before["symbols_tracked"] == 1

        checker.reset()

        stats_after = checker.get_stats()
        assert stats_after["symbols_tracked"] == 0
        assert stats_after["issues_found"] == 0

    def test_quality_issue_str(self):
        """Test QualityIssue string representation."""
        from src.data.shadow.live_quality_checks import QualityIssue

        issue = QualityIssue(
            kind="MISSING_BAR",
            severity="WARN",
            ts_ms=1000_000,
            symbol="BTC/EUR",
            details={"missing_bars": 2},
        )

        s = str(issue)
        assert "WARN" in s
        assert "MISSING_BAR" in s
        assert "BTC/EUR" in s
