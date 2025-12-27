"""
Tests for AlertDispatcher.
"""

from src.risk_layer.alerting.alert_dispatcher import AlertDispatcher
from src.risk_layer.alerting.alert_event import AlertEvent
from src.risk_layer.alerting.alert_types import AlertCategory, AlertSeverity


class TestAlertDispatcher:
    """Test AlertDispatcher Phase 1 implementation."""

    def test_create_dispatcher(self):
        """Test creating dispatcher."""
        dispatcher = AlertDispatcher()
        assert dispatcher.count() == 0

    def test_dispatch_single_event(self):
        """Test dispatching a single event."""
        dispatcher = AlertDispatcher()
        event = AlertEvent(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.RISK_LIMIT,
            source="test",
            message="Test alert",
        )

        dispatcher.dispatch(event)

        assert dispatcher.count() == 1
        dispatched = dispatcher.get_dispatched_events()
        assert len(dispatched) == 1
        assert dispatched[0] == event

    def test_dispatch_multiple_events(self):
        """Test dispatching multiple events."""
        dispatcher = AlertDispatcher()

        events = [
            AlertEvent(
                severity=AlertSeverity.INFO,
                category=AlertCategory.SYSTEM_HEALTH,
                source="test",
                message=f"Event {i}",
            )
            for i in range(5)
        ]

        for event in events:
            dispatcher.dispatch(event)

        assert dispatcher.count() == 5
        dispatched = dispatcher.get_dispatched_events()
        assert dispatched == events

    def test_clear_events(self):
        """Test clearing dispatched events."""
        dispatcher = AlertDispatcher()

        event = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="test",
            message="Test",
        )
        dispatcher.dispatch(event)

        assert dispatcher.count() == 1

        dispatcher.clear()

        assert dispatcher.count() == 0
        assert dispatcher.get_dispatched_events() == []

    def test_get_dispatched_events_returns_copy(self):
        """Test that get_dispatched_events returns a copy."""
        dispatcher = AlertDispatcher()
        event = AlertEvent(
            severity=AlertSeverity.INFO,
            category=AlertCategory.OTHER,
            source="test",
            message="Test",
        )
        dispatcher.dispatch(event)

        # Get events and modify the list
        events1 = dispatcher.get_dispatched_events()
        events1.append(None)  # type: ignore

        # Original should be unchanged
        events2 = dispatcher.get_dispatched_events()
        assert len(events2) == 1
        assert events2[0] == event
