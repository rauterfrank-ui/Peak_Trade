"""Base Trigger Interface.

All triggers must inherit from BaseTrigger and implement the check() method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class TriggerResult:
    """Result of a trigger check.

    Attributes:
        should_trigger: Whether kill switch should be triggered
        reason: Human-readable explanation
        metric_value: Actual value of the metric (if applicable)
        threshold: Threshold value (if applicable)
        metadata: Additional context data
    """

    should_trigger: bool
    reason: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "should_trigger": self.should_trigger,
            "reason": self.reason,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "metadata": self.metadata,
        }


class BaseTrigger(ABC):
    """Abstract base class for all triggers.

    Each trigger type (threshold, watchdog, external, manual)
    must inherit from this class and implement check().

    Attributes:
        name: Unique trigger name
        config: Trigger configuration
        enabled: Whether trigger is enabled
    """

    def __init__(self, name: str, config: dict):
        """Initialize trigger.

        Args:
            name: Unique trigger name
            config: Trigger configuration from TOML
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self._last_triggered: Optional[datetime] = None
        self._cooldown_seconds = config.get("cooldown_seconds", 0)

    @abstractmethod
    def check(self, context: dict) -> TriggerResult:
        """Check if trigger should fire.

        This method must be implemented by all trigger types.

        Args:
            context: Current system context (metrics, state, etc.)
                Example:
                {
                    "portfolio_drawdown": -0.12,
                    "daily_pnl": -0.03,
                    "realized_volatility_1h": 0.08,
                    "exchange_connected": True,
                    "last_price_update": datetime(...)
                }

        Returns:
            TriggerResult indicating if trigger should fire
        """
        pass

    def is_on_cooldown(self) -> bool:
        """Check if trigger is on cooldown.

        Returns:
            True if still in cooldown period
        """
        if not self._last_triggered or self._cooldown_seconds == 0:
            return False

        elapsed = (datetime.utcnow() - self._last_triggered).total_seconds()
        return elapsed < self._cooldown_seconds

    def mark_triggered(self):
        """Mark trigger as fired (for cooldown tracking)."""
        self._last_triggered = datetime.utcnow()

    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds.

        Returns:
            Remaining seconds, or 0 if not on cooldown
        """
        if not self.is_on_cooldown():
            return 0.0

        elapsed = (datetime.utcnow() - self._last_triggered).total_seconds()
        return max(0.0, self._cooldown_seconds - elapsed)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"enabled={self.enabled}, "
            f"cooldown={self._cooldown_seconds}s"
            f")"
        )
