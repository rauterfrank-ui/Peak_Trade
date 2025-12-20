"""
Event Bus for agent communication.

Provides a publish-subscribe system for event-driven agent interactions.
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types for the system."""
    STRATEGY_DISCOVERED = "strategy_discovered"
    RISK_ALERT = "risk_alert"
    EXECUTION_COMPLETED = "execution_completed"
    SYSTEM_ERROR = "system_error"
    MARKET_ANOMALY = "market_anomaly"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    CUSTOM = "custom"


@dataclass
class Event:
    """
    Base event class.
    
    Attributes:
        event_type: Type of event
        source: Agent or component that generated the event
        data: Event payload
        timestamp: When the event occurred
        metadata: Additional metadata
    """
    event_type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any]
    
    @classmethod
    def create(
        cls,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Event":
        """Create a new event."""
        return cls(
            event_type=event_type,
            source=source,
            data=data,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )


class EventBus:
    """
    Pub/Sub System for Agent Communication.
    
    Events:
    - strategy_discovered: New trading strategy found
    - risk_alert: Risk threshold exceeded
    - execution_completed: Trade execution finished
    - system_error: System error occurred
    - market_anomaly: Unusual market behavior detected
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        logger.info("Initialized EventBus")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify subscribers
        event_type = event.event_type
        if event_type in self._subscribers:
            logger.debug(f"Publishing event: {event_type} from {event.source}")
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed from event: {event_type}")
    
    def get_event_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.info("Cleared event history")
    
    def on(self, event_type: str) -> Callable:
        """
        Decorator for subscribing to events.
        
        Usage:
            @event_bus.on("risk_alert")
            def handle_risk_alert(event: Event):
                print(f"Risk alert: {event.data}")
        """
        def decorator(handler: Callable[[Event], None]) -> Callable[[Event], None]:
            self.subscribe(event_type, handler)
            return handler
        return decorator


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """
    Get the global event bus.
    
    Returns:
        Global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
