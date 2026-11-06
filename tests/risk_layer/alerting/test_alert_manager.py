"""
Tests for AlertManager.
"""

import pytest

from src.risk_layer.alerting.alert_config import AlertConfig
from src.risk_layer.alerting.alert_dispatcher import AlertDispatcher
from src.risk_layer.alerting.alert_manager import AlertManager
from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity


class TestAlertManager:
    """Test AlertManager functionality."""

    def test_create_manager_with_defaults(self):
        """Test creating manager with default config."""
        config = AlertConfig()
        manager = AlertManager(config)

        assert manager.config == config
        assert isinstance(manager.dispatcher, AlertDispatcher)
        assert manager.get_event_count() == 0

    def test_create_manager_with_custom_dispatcher(self):
        """Test creating manager with custom dispatcher."""
        config = AlertConfig()
        dispatcher = AlertDispatcher()
        manager = AlertManager(config, dispatcher=dispatcher)

        assert manager.dispatcher is dispatcher

    def test_register_alert_basic(self):
        """Test registering a basic alert."""
        config = AlertConfig(enabled=True)
        manager = AlertManager(config)

        event = manager.register_alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.RISK_LIMIT,
            source="var_gate",
            message="VaR limit approached",
        )

        assert event is not None
        assert event.severity == AlertSeverity.WARNING
        assert event.category == AlertCategory.RISK_LIMIT
        assert event.source == "var_gate"
        assert event.message == "VaR limit approached"
        assert manager.get_event_count() == 1

    def test_register_alert_with_context(self):
        """Test registering alert with context data."""
        config = AlertConfig(enabled=True)
        manager = AlertManager(config)

        context = {"position": "BTC-EUR", "current_var": 0.05}
        event = manager.register_alert(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.POSITION_VIOLATION,
            source="risk_gate",
            message="Position limit exceeded",
            context=context,
        )

        assert event is not None
        assert event.context == context

    def test_register_alert_filtered_by_severity(self):
        """Test that alerts below min_severity are filtered out."""
        config = AlertConfig(min_severity=AlertSeverity.WARNING)
        manager = AlertManager(config)

        # Below threshold - should be filtered
        event_info = manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            source="test",
            message="Info message",
        )
        assert event_info is None
        assert manager.get_event_count() == 0

        # At threshold - should pass
        event_warning = manager.register_alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.SYSTEM_HEALTH,
            source="test",
            message="Warning message",
        )
        assert event_warning is not None
        assert manager.get_event_count() == 1

    def test_register_alert_dispatched_when_enabled(self):
        """Test that alerts are dispatched when alerting is enabled."""
        config = AlertConfig(enabled=True)
        dispatcher = AlertDispatcher()
        manager = AlertManager(config, dispatcher=dispatcher)

        manager.register_alert(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.EXECUTION_ERROR,
            source="order_executor",
            message="Order failed",
        )

        # Should be dispatched
        assert dispatcher.count() == 1

    def test_register_alert_not_dispatched_when_disabled(self):
        """Test that alerts are not dispatched when alerting is disabled."""
        config = AlertConfig(enabled=False)
        dispatcher = AlertDispatcher()
        manager = AlertManager(config, dispatcher=dispatcher)

        manager.register_alert(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.EXECUTION_ERROR,
            source="order_executor",
            message="Order failed",
        )

        # Should be buffered but not dispatched
        assert manager.get_event_count() == 1
        assert dispatcher.count() == 0

    def test_buffer_size_limit(self):
        """Test that buffer respects max size (FIFO)."""
        config = AlertConfig(buffer_size=3, min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        # Register 5 events (buffer size = 3)
        for i in range(5):
            manager.register_alert(
                severity=AlertSeverity.INFO,
                category=AlertCategory.OTHER,
                source="test",
                message=f"Event {i}",
            )

        # Only last 3 should be in buffer
        assert manager.get_event_count() == 3
        events = manager.list_all_events()
        assert events[0].message == "Event 2"
        assert events[1].message == "Event 3"
        assert events[2].message == "Event 4"

    def test_list_all_events(self):
        """Test listing all buffered events."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        for i in range(3):
            manager.register_alert(
                severity=AlertSeverity.INFO,
                category=AlertCategory.OTHER,
                source="test",
                message=f"Event {i}",
            )

        events = manager.list_all_events()
        assert len(events) == 3
        # Oldest first
        assert events[0].message == "Event 0"
        assert events[2].message == "Event 2"

    def test_get_recent_events_no_limit(self):
        """Test getting recent events without limit."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        for i in range(5):
            manager.register_alert(
                severity=AlertSeverity.INFO,
                category=AlertCategory.OTHER,
                source="test",
                message=f"Event {i}",
            )

        events = manager.get_recent_events()
        assert len(events) == 5
        # Newest first
        assert events[0].message == "Event 4"
        assert events[4].message == "Event 0"

    def test_get_recent_events_with_limit(self):
        """Test getting recent events with limit."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        for i in range(5):
            manager.register_alert(
                severity=AlertSeverity.INFO,
                category=AlertCategory.OTHER,
                source="test",
                message=f"Event {i}",
            )

        events = manager.get_recent_events(limit=2)
        assert len(events) == 2
        assert events[0].message == "Event 4"
        assert events[1].message == "Event 3"

    def test_get_recent_events_filter_severity(self):
        """Test filtering recent events by severity."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="test",
            message="Info",
        )
        manager.register_alert(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.OTHER,
            source="test",
            message="Error",
        )
        manager.register_alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.OTHER,
            source="test",
            message="Warning",
        )

        # Filter for ERROR and above
        events = manager.get_recent_events(min_severity=AlertSeverity.ERROR)
        assert len(events) == 1
        assert events[0].message == "Error"

    def test_get_recent_events_filter_categories(self):
        """Test filtering recent events by categories."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.RISK_LIMIT,
            source="test",
            message="Risk",
        )
        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.DATA_QUALITY,
            source="test",
            message="Data",
        )
        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.RISK_LIMIT,
            source="test",
            message="Risk2",
        )

        events = manager.get_recent_events(categories=[AlertCategory.RISK_LIMIT])
        assert len(events) == 2
        assert all(e.category == AlertCategory.RISK_LIMIT for e in events)

    def test_get_recent_events_filter_sources(self):
        """Test filtering recent events by sources."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="var_gate",
            message="VaR",
        )
        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="stress_gate",
            message="Stress",
        )
        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="var_gate",
            message="VaR2",
        )

        events = manager.get_recent_events(sources=["var_gate"])
        assert len(events) == 2
        assert all(e.source == "var_gate" for e in events)

    def test_get_recent_events_combined_filters(self):
        """Test filtering with multiple criteria."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        # Mix of events
        manager.register_alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.RISK_LIMIT,
            source="var_gate",
            message="Match",
        )
        manager.register_alert(
            severity=AlertSeverity.INFO,  # Too low severity
            category=AlertCategory.RISK_LIMIT,
            source="var_gate",
            message="No match - severity",
        )
        manager.register_alert(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.DATA_QUALITY,  # Wrong category
            source="var_gate",
            message="No match - category",
        )
        manager.register_alert(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.RISK_LIMIT,
            source="stress_gate",  # Wrong source
            message="No match - source",
        )

        events = manager.get_recent_events(
            min_severity=AlertSeverity.WARNING,
            categories=[AlertCategory.RISK_LIMIT],
            sources=["var_gate"],
        )

        assert len(events) == 1
        assert events[0].message == "Match"

    def test_clear_buffer(self):
        """Test clearing the event buffer."""
        config = AlertConfig(min_severity=AlertSeverity.DEBUG)
        manager = AlertManager(config)

        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="test",
            message="Test",
        )

        assert manager.get_event_count() == 1

        manager.clear_buffer()

        assert manager.get_event_count() == 0
        assert manager.list_all_events() == []

    def test_get_stats(self):
        """Test getting alerting statistics."""
        config = AlertConfig(enabled=True, min_severity=AlertSeverity.INFO)
        manager = AlertManager(config)

        # Register various events
        manager.register_alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            source="test",
            message="Info 1",
        )
        manager.register_alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.RISK_LIMIT,
            source="test",
            message="Warning 1",
        )
        manager.register_alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.RISK_LIMIT,
            source="test",
            message="Warning 2",
        )
        manager.register_alert(
            severity=AlertSeverity.ERROR,
            category=AlertCategory.EXECUTION_ERROR,
            source="test",
            message="Error 1",
        )

        stats = manager.get_stats()

        assert stats["total_events"] == 4
        assert stats["alerting_enabled"] is True
        assert stats["min_severity"] == "info"

        # Check severity counts
        assert stats["by_severity"]["info"] == 1
        assert stats["by_severity"]["warning"] == 2
        assert stats["by_severity"]["error"] == 1
        assert stats["by_severity"]["critical"] == 0

        # Check category counts
        assert stats["by_category"]["system_health"] == 1
        assert stats["by_category"]["risk_limit"] == 2
        assert stats["by_category"]["execution_error"] == 1
