"""
Tests for Basel Traffic Light System
======================================
"""

import pytest

from src.risk_layer.var_backtest.traffic_light import (
    BaselZone,
    TrafficLightResult,
    TrafficLightMonitor,
    basel_traffic_light,
    compute_zone_thresholds,
    traffic_light_recommendation,
)


class TestBaselTrafficLight:
    """Tests for basel_traffic_light()."""

    def test_traffic_light_green_zone(self):
        """Few violations should be GREEN zone."""
        # 99% VaR, 250 days, 2 violations (expected: 2.5)
        result = basel_traffic_light(n_violations=2, n_observations=250, alpha=0.01)

        assert isinstance(result, TrafficLightResult)
        assert result.zone == BaselZone.GREEN
        assert result.n_violations == 2
        assert result.n_observations == 250
        assert result.expected_violations == 2.5
        assert result.capital_multiplier == 3.0  # Base multiplier

    def test_traffic_light_yellow_zone(self):
        """Moderate violations should be YELLOW zone."""
        # 99% VaR, 250 days, 7 violations (expected: 2.5)
        result = basel_traffic_light(n_violations=7, n_observations=250, alpha=0.01)

        assert result.zone == BaselZone.YELLOW
        assert result.capital_multiplier > 3.0  # Penalty applied
        assert result.capital_multiplier < 4.0  # Not maximum

    def test_traffic_light_red_zone(self):
        """Many violations should be RED zone."""
        # 99% VaR, 250 days, 12 violations (expected: 2.5)
        result = basel_traffic_light(n_violations=12, n_observations=250, alpha=0.01)

        assert result.zone == BaselZone.RED
        assert result.capital_multiplier == 4.0  # Maximum penalty

    def test_traffic_light_basel_standard_thresholds(self):
        """Basel standard: 250 days, 99% VaR."""
        # GREEN: 0-4
        for n in range(5):
            result = basel_traffic_light(n, 250, 0.01)
            assert result.zone == BaselZone.GREEN, f"n={n} should be GREEN"

        # YELLOW: 5-9
        for n in range(5, 10):
            result = basel_traffic_light(n, 250, 0.01)
            assert result.zone == BaselZone.YELLOW, f"n={n} should be YELLOW"

        # RED: >=10
        for n in [10, 11, 15, 20]:
            result = basel_traffic_light(n, 250, 0.01)
            assert result.zone == BaselZone.RED, f"n={n} should be RED"

    def test_traffic_light_zero_violations(self):
        """Zero violations should be GREEN."""
        result = basel_traffic_light(n_violations=0, n_observations=250, alpha=0.01)

        assert result.zone == BaselZone.GREEN
        assert result.violation_rate == 0.0
        assert result.capital_multiplier == 3.0

    def test_traffic_light_all_violations(self):
        """All violations should be RED."""
        result = basel_traffic_light(n_violations=250, n_observations=250, alpha=0.01)

        assert result.zone == BaselZone.RED
        assert result.violation_rate == 1.0
        assert result.capital_multiplier == 4.0

    def test_traffic_light_different_alpha(self):
        """Test with different VaR confidence levels."""
        # 95% VaR (alpha=0.05): expect ~12.5 violations in 250 days
        result_95 = basel_traffic_light(n_violations=10, n_observations=250, alpha=0.05)

        # 99% VaR (alpha=0.01): expect ~2.5 violations in 250 days
        result_99 = basel_traffic_light(n_violations=10, n_observations=250, alpha=0.01)

        # Same number of violations, but different expected rates
        assert result_95.expected_violations > result_99.expected_violations
        # 10 violations is worse for 99% VaR
        assert result_99.zone.value >= result_95.zone.value  # RED >= YELLOW/GREEN

    def test_traffic_light_invalid_inputs(self):
        """Invalid inputs should raise ValueError."""
        with pytest.raises(ValueError, match="n_violations must be >= 0"):
            basel_traffic_light(n_violations=-1, n_observations=250, alpha=0.01)

        with pytest.raises(ValueError, match="n_observations must be > 0"):
            basel_traffic_light(n_violations=5, n_observations=0, alpha=0.01)

        with pytest.raises(ValueError, match="alpha must be in"):
            basel_traffic_light(n_violations=5, n_observations=250, alpha=1.5)


class TestZoneThresholds:
    """Tests for compute_zone_thresholds()."""

    def test_zone_thresholds_basel_standard(self):
        """Basel standard case: 250 days, 99% VaR."""
        green, yellow = compute_zone_thresholds(n_observations=250, alpha=0.01)

        # Basel standard thresholds
        assert green == 4
        assert yellow == 9

    def test_zone_thresholds_sensible_bounds(self):
        """Thresholds should be sensible."""
        green, yellow = compute_zone_thresholds(n_observations=100, alpha=0.05)

        # Yellow should be higher than green
        assert yellow > green
        # Both should be non-negative
        assert green >= 0
        assert yellow >= 0

    def test_zone_thresholds_different_n(self):
        """Different observation counts should give different thresholds."""
        green_100, yellow_100 = compute_zone_thresholds(n_observations=100, alpha=0.01)
        green_500, yellow_500 = compute_zone_thresholds(n_observations=500, alpha=0.01)

        # More observations -> higher thresholds
        assert green_500 > green_100
        assert yellow_500 > yellow_100


class TestTrafficLightRecommendation:
    """Tests for traffic_light_recommendation()."""

    def test_recommendation_green_zone(self):
        """GREEN zone should give positive recommendation."""
        result = basel_traffic_light(n_violations=2, n_observations=250, alpha=0.01)
        recommendation = traffic_light_recommendation(result)

        assert "GREEN ZONE" in recommendation
        assert "acceptable" in recommendation.lower()
        assert "no action required" in recommendation.lower()

    def test_recommendation_yellow_zone(self):
        """YELLOW zone should give warning recommendation."""
        result = basel_traffic_light(n_violations=7, n_observations=250, alpha=0.01)
        recommendation = traffic_light_recommendation(result)

        assert "YELLOW ZONE" in recommendation
        assert "monitoring" in recommendation.lower()
        assert "Actions:" in recommendation

    def test_recommendation_red_zone(self):
        """RED zone should give urgent recommendation."""
        result = basel_traffic_light(n_violations=12, n_observations=250, alpha=0.01)
        recommendation = traffic_light_recommendation(result)

        assert "RED ZONE" in recommendation
        assert "IMMEDIATE ACTION REQUIRED" in recommendation
        assert "REVISE" in recommendation


class TestTrafficLightMonitor:
    """Tests for TrafficLightMonitor continuous monitoring."""

    def test_monitor_initialization(self):
        """Monitor should initialize correctly."""
        monitor = TrafficLightMonitor(alpha=0.01, window=250)

        assert monitor.alpha == 0.01
        assert monitor.window == 250
        assert len(monitor.violations) == 0
        assert monitor.current_zone is None

    def test_monitor_update_no_violation(self):
        """Update with no violation should work."""
        monitor = TrafficLightMonitor(alpha=0.01, window=250)

        # Loss < VaR -> no violation
        result = monitor.update(realized_loss=0.005, var_estimate=0.010)

        assert len(monitor.violations) == 1
        assert monitor.violations[0] is False
        assert result.zone == BaselZone.GREEN

    def test_monitor_update_with_violation(self):
        """Update with violation should work."""
        monitor = TrafficLightMonitor(alpha=0.01, window=250)

        # Loss > VaR -> violation
        result = monitor.update(realized_loss=0.015, var_estimate=0.010)

        assert len(monitor.violations) == 1
        assert monitor.violations[0] is True

    def test_monitor_rolling_window(self):
        """Monitor should keep only last window observations."""
        monitor = TrafficLightMonitor(alpha=0.01, window=10)

        # Add 15 observations
        for i in range(15):
            monitor.update(realized_loss=0.005, var_estimate=0.010)

        # Should keep only last 10
        assert len(monitor.violations) == 10

    def test_monitor_zone_progression(self):
        """Monitor should track zone changes."""
        monitor = TrafficLightMonitor(alpha=0.01, window=250)

        # Start with no violations -> GREEN
        for _ in range(100):
            result = monitor.update(realized_loss=0.005, var_estimate=0.010)
        assert result.zone == BaselZone.GREEN

        # Add some violations -> might move to YELLOW/RED
        for _ in range(10):
            monitor.update(realized_loss=0.015, var_estimate=0.010)

        result = monitor.update(realized_loss=0.005, var_estimate=0.010)
        # Should have violations now
        assert sum(monitor.violations) > 0

    def test_monitor_reset(self):
        """Reset should clear state."""
        monitor = TrafficLightMonitor(alpha=0.01, window=250)

        # Add some data
        for _ in range(10):
            monitor.update(realized_loss=0.015, var_estimate=0.010)

        # Reset
        monitor.reset()

        assert len(monitor.violations) == 0
        assert monitor.current_zone is None


class TestCapitalMultiplier:
    """Tests for capital multiplier calculation."""

    def test_capital_multiplier_green(self):
        """GREEN zone should have base multiplier."""
        result = basel_traffic_light(n_violations=3, n_observations=250, alpha=0.01)
        assert result.capital_multiplier == 3.0

    def test_capital_multiplier_yellow_increases(self):
        """YELLOW zone multiplier should increase with violations."""
        result_5 = basel_traffic_light(n_violations=5, n_observations=250, alpha=0.01)
        result_7 = basel_traffic_light(n_violations=7, n_observations=250, alpha=0.01)
        result_9 = basel_traffic_light(n_violations=9, n_observations=250, alpha=0.01)

        # All YELLOW, but increasing multipliers
        assert result_5.zone == BaselZone.YELLOW
        assert result_7.zone == BaselZone.YELLOW
        assert result_9.zone == BaselZone.YELLOW

        assert result_5.capital_multiplier < result_7.capital_multiplier
        assert result_7.capital_multiplier < result_9.capital_multiplier

    def test_capital_multiplier_red_maximum(self):
        """RED zone should have maximum multiplier."""
        result_10 = basel_traffic_light(n_violations=10, n_observations=250, alpha=0.01)
        result_20 = basel_traffic_light(n_violations=20, n_observations=250, alpha=0.01)

        # Both RED, same maximum multiplier
        assert result_10.capital_multiplier == 4.0
        assert result_20.capital_multiplier == 4.0


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_traffic_light_determinism(self):
        """Same input should give same output."""
        result1 = basel_traffic_light(n_violations=7, n_observations=250, alpha=0.01)
        result2 = basel_traffic_light(n_violations=7, n_observations=250, alpha=0.01)

        assert result1.zone == result2.zone
        assert result1.capital_multiplier == result2.capital_multiplier
        assert result1.violation_rate == result2.violation_rate

    def test_zone_thresholds_determinism(self):
        """Same input should give same thresholds."""
        green1, yellow1 = compute_zone_thresholds(n_observations=250, alpha=0.01)
        green2, yellow2 = compute_zone_thresholds(n_observations=250, alpha=0.01)

        assert green1 == green2
        assert yellow1 == yellow2
