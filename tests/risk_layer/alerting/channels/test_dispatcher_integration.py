"""
Smoke tests for AlertDispatcher integration with ChannelRouter.

Tests basic integration - detailed routing is tested in test_channel_router.py.
"""

import asyncio

from src.risk_layer.alerting.alert_dispatcher import AlertDispatcher
from src.risk_layer.alerting.channels.channel_router import ChannelRouter
from src.risk_layer.alerting.channels.console_channel import ConsoleChannel


class TestDispatcherIntegration:
    """Test AlertDispatcher integration with channels."""

    def test_dispatcher_with_no_router_uses_sink(self, event_warning):
        """Test dispatcher falls back to in-memory sink when no router."""
        dispatcher = AlertDispatcher()

        dispatcher.dispatch(event_warning)

        # Should be in sink
        assert len(dispatcher.get_dispatched_events()) == 1
        assert dispatcher.get_dispatched_events()[0] == event_warning

    def test_dispatcher_with_router(self, console_config, event_info):
        """Test dispatcher routes via ChannelRouter."""
        console = ConsoleChannel(console_config)
        router = ChannelRouter(channels=[console])
        dispatcher = AlertDispatcher(router=router)

        dispatcher.dispatch(event_info)

        # Note: sink still gets events, but router also gets them
        assert len(dispatcher.get_dispatched_events()) >= 1

    def test_dispatcher_routing_multiple_events(self, console_config, event_factory):
        """Test dispatcher handles multiple events."""
        console = ConsoleChannel(console_config)
        router = ChannelRouter(channels=[console])
        dispatcher = AlertDispatcher(router=router)

        # Dispatch 5 events
        for i in range(5):
            event = event_factory(message=f"Event {i}")
            dispatcher.dispatch(event)

        # Router should track stats
        stats = router.get_stats()
        assert stats["total_dispatches"] == 5

    def test_dispatcher_sync_wrapper(self, console_config, event_warning):
        """Test sync wrapper for dispatch."""
        console = ConsoleChannel(console_config)
        router = ChannelRouter(channels=[console])
        dispatcher = AlertDispatcher(router=router)

        # Use sync wrapper (if exists)
        if hasattr(dispatcher, "route_event_sync"):
            result = dispatcher.route_event_sync(event_warning)
            assert isinstance(result, dict)

    def test_dispatcher_with_disabled_channels(self, event_error):
        """Test dispatcher when all channels disabled."""
        disabled = ConsoleChannel({"enabled": False})
        router = ChannelRouter(channels=[disabled])
        dispatcher = AlertDispatcher(router=router)

        dispatcher.dispatch(event_error)

        # Sink always gets events
        assert len(dispatcher.get_dispatched_events()) == 1


class TestDispatcherEdgeCases:
    """Test edge cases and error handling."""

    def test_dispatcher_empty_router(self, event_info):
        """Test dispatcher with empty router."""
        router = ChannelRouter(channels=[])
        dispatcher = AlertDispatcher(router=router)

        dispatcher.dispatch(event_info)

        # Sink always gets events
        assert len(dispatcher.get_dispatched_events()) == 1

    def test_dispatcher_persists_sink_across_calls(self, event_factory):
        """Test sink accumulates events when no router."""
        dispatcher = AlertDispatcher()

        # Add multiple
        for i in range(3):
            event = event_factory(message=f"Event {i}")
            dispatcher.dispatch(event)

        assert len(dispatcher.get_dispatched_events()) == 3
