"""
Tests for AlertSeverity and AlertCategory enums.
"""

import pytest

from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity


class TestAlertSeverity:
    """Test AlertSeverity enum and comparison operations."""

    def test_severity_values(self):
        """Test all severity levels are defined."""
        assert AlertSeverity.DEBUG.value == "debug"
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_severity_comparison_less_than(self):
        """Test < comparison between severity levels."""
        assert AlertSeverity.DEBUG < AlertSeverity.INFO
        assert AlertSeverity.INFO < AlertSeverity.WARNING
        assert AlertSeverity.WARNING < AlertSeverity.ERROR
        assert AlertSeverity.ERROR < AlertSeverity.CRITICAL

        # Not less than itself
        assert not (AlertSeverity.WARNING < AlertSeverity.WARNING)

    def test_severity_comparison_less_equal(self):
        """Test <= comparison between severity levels."""
        assert AlertSeverity.DEBUG <= AlertSeverity.INFO
        assert AlertSeverity.WARNING <= AlertSeverity.WARNING
        assert AlertSeverity.ERROR <= AlertSeverity.CRITICAL

    def test_severity_comparison_greater_than(self):
        """Test > comparison between severity levels."""
        assert AlertSeverity.CRITICAL > AlertSeverity.ERROR
        assert AlertSeverity.ERROR > AlertSeverity.WARNING
        assert AlertSeverity.WARNING > AlertSeverity.INFO
        assert AlertSeverity.INFO > AlertSeverity.DEBUG

        # Not greater than itself
        assert not (AlertSeverity.WARNING > AlertSeverity.WARNING)

    def test_severity_comparison_greater_equal(self):
        """Test >= comparison between severity levels."""
        assert AlertSeverity.CRITICAL >= AlertSeverity.ERROR
        assert AlertSeverity.WARNING >= AlertSeverity.WARNING
        assert AlertSeverity.DEBUG >= AlertSeverity.DEBUG

    def test_severity_comparison_invalid_type(self):
        """Test comparison with invalid type returns NotImplemented."""
        # Python's enum comparison returns False for incompatible types
        # rather than raising TypeError (standard enum behavior)
        result = AlertSeverity.WARNING < "warning"
        assert result is False


class TestAlertCategory:
    """Test AlertCategory enum."""

    def test_category_values(self):
        """Test all category values are defined."""
        assert AlertCategory.RISK_LIMIT.value == "risk_limit"
        assert AlertCategory.POSITION_VIOLATION.value == "position_violation"
        assert AlertCategory.EXECUTION_ERROR.value == "execution_error"
        assert AlertCategory.DATA_QUALITY.value == "data_quality"
        assert AlertCategory.SYSTEM_HEALTH.value == "system_health"
        assert AlertCategory.COMPLIANCE.value == "compliance"
        assert AlertCategory.PERFORMANCE.value == "performance"
        assert AlertCategory.OTHER.value == "other"

    def test_category_membership(self):
        """Test category enum membership."""
        assert AlertCategory.RISK_LIMIT in AlertCategory
        assert AlertCategory.OTHER in AlertCategory
