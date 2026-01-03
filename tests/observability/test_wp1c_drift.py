"""
Tests for WP1C - Drift Detection

Tests:
- Comparator stable on fixtures
- Report deterministic (exact match)
- Thresholds trigger pause deterministically
"""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from src.observability.drift.comparator import DriftComparator, DriftMetrics, SignalEvent
from src.observability.drift.daily_report import DailyReportGenerator
from src.observability.drift.pause_policy import AutoPausePolicy


class TestDriftComparator:
    """Test drift comparator."""

    def test_perfect_match(self):
        """Test perfect match between shadow and backtest."""
        shadow_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            )
        ]

        backtest_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            )
        ]

        comparator = DriftComparator()
        metrics = comparator.compare_signals(shadow_signals, backtest_signals)

        assert metrics.match_rate == 1.0
        assert metrics.matched_signals == 1
        assert metrics.divergent_signals == 0

    def test_price_divergence_detection(self):
        """Test price divergence detection."""
        shadow_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("51000"),  # 2% higher
            )
        ]

        backtest_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            )
        ]

        comparator = DriftComparator(price_tolerance_pct=1.0)  # Only 1% tolerance
        metrics = comparator.compare_signals(shadow_signals, backtest_signals)

        # Should NOT match (exceeds 1% tolerance)
        assert metrics.match_rate == 0.0
        assert metrics.divergent_signals == 1

    def test_price_within_tolerance_matches(self):
        """Test price within tolerance still matches."""
        shadow_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50250"),  # 0.5% higher
            )
        ]

        backtest_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            )
        ]

        comparator = DriftComparator(price_tolerance_pct=1.0)  # 1% tolerance
        metrics = comparator.compare_signals(shadow_signals, backtest_signals)

        # Should match (within 1% tolerance)
        assert metrics.match_rate == 1.0
        assert metrics.matched_signals == 1

    def test_time_divergence_detection(self):
        """Test time divergence detection."""
        shadow_signals = [
            SignalEvent(
                timestamp_ms=1010_000,  # 10 seconds later
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            )
        ]

        backtest_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            )
        ]

        comparator = DriftComparator(time_tolerance_ms=5000)  # 5 second tolerance
        metrics = comparator.compare_signals(shadow_signals, backtest_signals)

        # Should NOT match (exceeds 5s tolerance)
        assert metrics.match_rate == 0.0
        assert metrics.divergent_signals == 1

    def test_quantity_divergence_detection(self):
        """Test quantity divergence detection."""
        shadow_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.2"),  # 20% higher
                price=Decimal("50000"),
            )
        ]

        backtest_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            )
        ]

        comparator = DriftComparator(quantity_tolerance_pct=5.0)  # 5% tolerance
        metrics = comparator.compare_signals(shadow_signals, backtest_signals)

        # Should NOT match (exceeds 5% tolerance)
        assert metrics.match_rate == 0.0

    def test_multiple_signals_partial_match(self):
        """Test multiple signals with partial match."""
        shadow_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            ),
            SignalEvent(
                timestamp_ms=2000_000,
                symbol="ETH/USD",
                signal_type="SELL",
                quantity=Decimal("10.0"),
                price=Decimal("3000"),
            ),
            SignalEvent(
                timestamp_ms=3000_000,
                symbol="BTC/USD",
                signal_type="SELL",
                quantity=Decimal("0.5"),
                price=Decimal("100000"),  # Wrong price
            ),
        ]

        backtest_signals = [
            SignalEvent(
                timestamp_ms=1000_000,
                symbol="BTC/USD",
                signal_type="BUY",
                quantity=Decimal("1.0"),
                price=Decimal("50000"),
            ),
            SignalEvent(
                timestamp_ms=2000_000,
                symbol="ETH/USD",
                signal_type="SELL",
                quantity=Decimal("10.0"),
                price=Decimal("3000"),
            ),
            SignalEvent(
                timestamp_ms=3000_000,
                symbol="BTC/USD",
                signal_type="SELL",
                quantity=Decimal("0.5"),
                price=Decimal("51000"),  # Correct price
            ),
        ]

        comparator = DriftComparator()
        metrics = comparator.compare_signals(shadow_signals, backtest_signals)

        assert metrics.total_signals_shadow == 3
        assert metrics.matched_signals == 2  # First two match
        assert metrics.divergent_signals == 1  # Third diverges
        assert metrics.match_rate == pytest.approx(2.0 / 3.0)

    def test_empty_signals(self):
        """Test empty signal lists."""
        comparator = DriftComparator()
        metrics = comparator.compare_signals([], [])

        assert metrics.match_rate == 0.0
        assert metrics.matched_signals == 0
        assert metrics.divergent_signals == 0


class TestDailyReportGenerator:
    """Test daily report generator."""

    def test_generate_report_deterministic(self):
        """Test report generation is deterministic."""
        metrics = DriftMetrics(
            total_signals_shadow=100,
            total_signals_backtest=100,
            matched_signals=95,
            divergent_signals=5,
            match_rate=0.95,
            avg_price_divergence=0.5,
            avg_quantity_divergence=1.0,
            details={"shadow_symbols": ["BTC/USD"], "backtest_symbols": ["BTC/USD"]},
        )

        generator = DailyReportGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"

            # Generate twice
            generator.generate_report(metrics, datetime(2025, 1, 1), output_path)
            with open(output_path) as f:
                content1 = f.read()

            generator.generate_report(metrics, datetime(2025, 1, 1), output_path)
            with open(output_path) as f:
                content2 = f.read()

            # Should be identical (except timestamp)
            lines1 = [l for l in content1.split("\n") if not l.startswith("**Generated:")]
            lines2 = [l for l in content2.split("\n") if not l.startswith("**Generated:")]

            assert lines1 == lines2

    def test_report_contains_key_sections(self):
        """Test report contains all key sections."""
        metrics = DriftMetrics(
            total_signals_shadow=100,
            total_signals_backtest=100,
            matched_signals=85,
            divergent_signals=15,
            match_rate=0.85,
            avg_price_divergence=1.5,
            avg_quantity_divergence=3.0,
        )

        generator = DailyReportGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            generator.generate_report(metrics, datetime(2025, 1, 1), output_path)

            with open(output_path) as f:
                content = f.read()

            # Check key sections exist
            assert "# Daily Drift Report" in content
            assert "## 📊 Overview" in content
            assert "## 🎯 Signal Comparison" in content
            assert "## 📈 Divergence Statistics" in content
            assert "## ⚠️ Assessment" in content
            assert "## 💡 Recommendations" in content

    def test_severity_assessment(self):
        """Test severity assessment in report."""
        # Low severity (high match rate)
        metrics_low = DriftMetrics(
            match_rate=0.96,
            matched_signals=96,
            divergent_signals=4,
        )

        generator = DailyReportGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low.md"
            generator.generate_report(metrics_low, datetime(2025, 1, 1), output_path)

            with open(output_path) as f:
                content = f.read()

            assert "🟢" in content  # Green for LOW
            assert "LOW" in content

        # Critical severity (low match rate)
        metrics_critical = DriftMetrics(
            match_rate=0.60,
            matched_signals=60,
            divergent_signals=40,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "critical.md"
            generator.generate_report(metrics_critical, datetime(2025, 1, 1), output_path)

            with open(output_path) as f:
                content = f.read()

            assert "🔴" in content  # Red for CRITICAL
            assert "CRITICAL" in content


class TestAutoPausePolicy:
    """Test auto-pause policy."""

    def test_no_pause_on_good_metrics(self):
        """Test no pause on good metrics."""
        metrics = DriftMetrics(
            total_signals_shadow=100,
            matched_signals=95,
            match_rate=0.95,
            avg_price_divergence=0.5,
            avg_quantity_divergence=1.0,
        )

        policy = AutoPausePolicy(
            match_rate_threshold=0.85,
            min_signals_for_evaluation=10,
        )

        recommendation = policy.evaluate(metrics)

        assert recommendation.should_pause is False
        assert len(recommendation.reason_codes) == 0

    def test_pause_on_low_match_rate(self):
        """Test pause on low match rate."""
        metrics = DriftMetrics(
            total_signals_shadow=100,
            matched_signals=70,
            match_rate=0.70,
            avg_price_divergence=0.5,
            avg_quantity_divergence=1.0,
        )

        policy = AutoPausePolicy(
            match_rate_threshold=0.85,  # Requires 85%
            min_signals_for_evaluation=10,
        )

        recommendation = policy.evaluate(metrics)

        assert recommendation.should_pause is True
        assert "LOW_MATCH_RATE" in recommendation.reason_codes

    def test_pause_on_high_price_divergence(self):
        """Test pause on high price divergence."""
        metrics = DriftMetrics(
            total_signals_shadow=100,
            matched_signals=95,
            match_rate=0.95,
            avg_price_divergence=5.0,  # High divergence
            avg_quantity_divergence=1.0,
        )

        policy = AutoPausePolicy(
            price_divergence_threshold=3.0,  # Max 3%
            min_signals_for_evaluation=10,
        )

        recommendation = policy.evaluate(metrics)

        assert recommendation.should_pause is True
        assert "HIGH_PRICE_DIVERGENCE" in recommendation.reason_codes

    def test_pause_on_high_quantity_divergence(self):
        """Test pause on high quantity divergence."""
        metrics = DriftMetrics(
            total_signals_shadow=100,
            matched_signals=95,
            match_rate=0.95,
            avg_price_divergence=0.5,
            avg_quantity_divergence=15.0,  # High divergence
        )

        policy = AutoPausePolicy(
            quantity_divergence_threshold=10.0,  # Max 10%
            min_signals_for_evaluation=10,
        )

        recommendation = policy.evaluate(metrics)

        assert recommendation.should_pause is True
        assert "HIGH_QUANTITY_DIVERGENCE" in recommendation.reason_codes

    def test_insufficient_data_no_pause(self):
        """Test insufficient data does not trigger pause."""
        metrics = DriftMetrics(
            total_signals_shadow=5,  # Too few
            matched_signals=2,
            match_rate=0.40,  # Low but not enough data
            avg_price_divergence=0.5,
            avg_quantity_divergence=1.0,
        )

        policy = AutoPausePolicy(
            match_rate_threshold=0.85,
            min_signals_for_evaluation=10,  # Requires 10
        )

        recommendation = policy.evaluate(metrics)

        assert recommendation.should_pause is False
        assert recommendation.severity == "INSUFFICIENT_DATA"
        assert "INSUFFICIENT_SIGNALS" in recommendation.reason_codes

    def test_multiple_reasons_for_pause(self):
        """Test multiple reasons trigger pause."""
        metrics = DriftMetrics(
            total_signals_shadow=100,
            matched_signals=60,
            match_rate=0.60,
            avg_price_divergence=5.0,
            avg_quantity_divergence=15.0,
        )

        policy = AutoPausePolicy(
            match_rate_threshold=0.85,
            price_divergence_threshold=3.0,
            quantity_divergence_threshold=10.0,
            min_signals_for_evaluation=10,
        )

        recommendation = policy.evaluate(metrics)

        assert recommendation.should_pause is True
        assert "LOW_MATCH_RATE" in recommendation.reason_codes
        assert "HIGH_PRICE_DIVERGENCE" in recommendation.reason_codes
        assert "HIGH_QUANTITY_DIVERGENCE" in recommendation.reason_codes
        assert len(recommendation.reason_codes) == 3
