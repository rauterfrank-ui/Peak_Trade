"""
Tests for AlertEvent dataclass.
"""

from datetime import datetime

import pytest

from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity


class TestAlertEvent:
    """Test AlertEvent creation and validation."""

    def test_create_minimal_event(self):
        """Test creating event with required fields only."""
        event = AlertEvent(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.RISK_LIMIT,
            source="test_module",
            message="Test alert",
        )

        assert event.severity == AlertSeverity.WARNING
        assert event.category == AlertCategory.RISK_LIMIT
        assert event.source == "test_module"
        assert event.message == "Test alert"
        assert isinstance(event.timestamp, datetime)
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 0
        assert event.context == {}

    def test_create_event_with_context(self):
        """Test creating event with context data."""
        context = {"position": "BTC-EUR", "limit": 0.03, "current": 0.05}
        event = AlertEvent(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.POSITION_VIOLATION,
            source="var_gate",
            message="VaR limit breached",
            context=context,
        )

        assert event.context == context
        assert event.context["position"] == "BTC-EUR"

    def test_event_immutability(self):
        """Test that AlertEvent is immutable (frozen dataclass)."""
        event = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            source="test",
            message="Test",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.message = "Modified"

    def test_unique_event_ids(self):
        """Test that each event gets a unique ID."""
        event1 = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="test",
            message="Event 1",
        )
        event2 = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="test",
            message="Event 2",
        )

        assert event1.event_id != event2.event_id

    def test_validation_empty_source(self):
        """Test validation fails for empty source."""
        with pytest.raises(ValueError, match="source cannot be empty"):
            AlertEvent(
                severity=AlertSeverity.INFO,
                category=AlertCategory.OTHER,
                source="",
                message="Test",
            )

    def test_validation_empty_message(self):
        """Test validation fails for empty message."""
        with pytest.raises(ValueError, match="message cannot be empty"):
            AlertEvent(
                severity=AlertSeverity.INFO,
                category=AlertCategory.OTHER,
                source="test",
                message="",
            )

    def test_validation_invalid_severity_type(self):
        """Test validation fails for invalid severity type."""
        with pytest.raises(TypeError, match="severity must be AlertSeverity"):
            AlertEvent(
                severity="warning",  # type: ignore
                category=AlertCategory.OTHER,
                source="test",
                message="Test",
            )

    def test_validation_invalid_category_type(self):
        """Test validation fails for invalid category type."""
        with pytest.raises(TypeError, match="category must be AlertCategory"):
            AlertEvent(
                severity=AlertSeverity.WARNING,
                category="risk_limit",  # type: ignore
                source="test",
                message="Test",
            )

    def test_to_dict(self):
        """Test serialization to dict."""
        event = AlertEvent(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.EXECUTION_ERROR,
            source="order_executor",
            message="Order failed",
            context={"order_id": "12345"},
        )

        result = event.to_dict()

        assert result["event_id"] == event.event_id
        assert result["severity"] == "error"
        assert result["category"] == "execution_error"
        assert result["source"] == "order_executor"
        assert result["message"] == "Order failed"
        assert result["context"] == {"order_id": "12345"}
        assert isinstance(result["timestamp"], str)  # ISO format

    def test_matches_filter_severity(self):
        """Test filtering by minimum severity."""
        event = AlertEvent(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.OTHER,
            source="test",
            message="Test",
        )

        # Matches: event severity >= filter
        assert event.matches_filter(min_severity=AlertSeverity.DEBUG)
        assert event.matches_filter(min_severity=AlertSeverity.INFO)
        assert event.matches_filter(min_severity=AlertSeverity.WARNING)

        # Does not match: event severity < filter
        assert not event.matches_filter(min_severity=AlertSeverity.ERROR)
        assert not event.matches_filter(min_severity=AlertSeverity.CRITICAL)

    def test_matches_filter_categories(self):
        """Test filtering by category list."""
        event = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.DATA_QUALITY,
            source="test",
            message="Test",
        )

        # Matches
        assert event.matches_filter(categories=[AlertCategory.DATA_QUALITY, AlertCategory.OTHER])
        assert event.matches_filter(categories=[AlertCategory.DATA_QUALITY])

        # Does not match
        assert not event.matches_filter(
            categories=[AlertCategory.RISK_LIMIT, AlertCategory.COMPLIANCE]
        )

    def test_matches_filter_sources(self):
        """Test filtering by source list."""
        event = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="var_gate",
            message="Test",
        )

        # Matches
        assert event.matches_filter(sources=["var_gate", "kill_switch"])
        assert event.matches_filter(sources=["var_gate"])

        # Does not match
        assert not event.matches_filter(sources=["stress_gate", "liquidity_gate"])

    def test_matches_filter_combined(self):
        """Test filtering with multiple criteria."""
        event = AlertEvent(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.RISK_LIMIT,
            source="var_gate",
            message="Test",
        )

        # All match
        assert event.matches_filter(
            min_severity=AlertSeverity.WARNING,
            categories=[AlertCategory.RISK_LIMIT],
            sources=["var_gate"],
        )

        # Severity doesn't match
        assert not event.matches_filter(
            min_severity=AlertSeverity.CRITICAL,
            categories=[AlertCategory.RISK_LIMIT],
            sources=["var_gate"],
        )

        # Category doesn't match
        assert not event.matches_filter(
            min_severity=AlertSeverity.WARNING,
            categories=[AlertCategory.COMPLIANCE],
            sources=["var_gate"],
        )

    def test_matches_filter_no_filters(self):
        """Test that event matches when no filters provided."""
        event = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="test",
            message="Test",
        )

        assert event.matches_filter()
        assert event.matches_filter(min_severity=None, categories=None, sources=None)
