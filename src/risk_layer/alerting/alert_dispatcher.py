"""
Alert Dispatcher
================

Routes alert events to configured channels.
Phase 1: Simple in-memory sink for testing.
Phase 2: Multi-channel routing with async dispatch.
"""

from typing import Dict, List, Optional

from src.risk_layer.alerting.alert_event import AlertEvent


class AlertDispatcher:
    """
    Dispatches alert events to configured channels.

    Phase 1 Implementation:
    - In-memory sink for testing and validation

    Phase 2 Implementation:
    - ChannelRouter integration for multi-channel dispatch
    - Backward compatible with Phase 1 sink

    Thread-safe for concurrent alert generation.
    """

    def __init__(self, router: Optional["ChannelRouter"] = None):  # type: ignore
        """
        Initialize dispatcher.

        Args:
            router: Optional ChannelRouter for Phase 2 multi-channel dispatch
        """
        # Phase 1: In-memory sink (always available for testing)
        self._sink: List[AlertEvent] = []

        # Phase 2: Channel router (optional)
        self._router = router

    def dispatch(self, event: AlertEvent) -> Dict[str, bool]:
        """
        Dispatch an alert event.

        Phase 1: Stores event in memory sink.
        Phase 2: Routes to channels via ChannelRouter (if configured).

        Args:
            event: AlertEvent to dispatch

        Returns:
            Dict mapping channel_name -> success (bool)
            Empty dict if no router configured
        """
        # Always store in sink (for testing/debugging)
        self._sink.append(event)

        # Route to channels if router configured
        if self._router:
            return self._router.route_event_sync(event)

        return {}

    def get_dispatched_events(self) -> List[AlertEvent]:
        """
        Get all dispatched events (for testing).

        Returns:
            List of all events sent to dispatcher
        """
        return list(self._sink)

    def clear(self) -> None:
        """
        Clear all dispatched events (for testing).
        """
        self._sink.clear()

    def count(self) -> int:
        """
        Count of dispatched events.

        Returns:
            Number of events in sink
        """
        return len(self._sink)

    def get_router(self) -> Optional["ChannelRouter"]:  # type: ignore
        """
        Get the configured ChannelRouter.

        Returns:
            ChannelRouter instance or None
        """
        return self._router

    def set_router(self, router: "ChannelRouter") -> None:  # type: ignore
        """
        Set or replace the ChannelRouter.

        Args:
            router: ChannelRouter instance
        """
        self._router = router
