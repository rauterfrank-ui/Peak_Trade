"""Trigger System for Kill Switch.

This module provides various trigger mechanisms for the kill switch:
- ThresholdTrigger: Metric-based triggers (drawdown, loss, volatility)
- ManualTrigger: Operator-initiated triggers
- WatchdogTrigger: System health monitoring
- ExternalTrigger: External system state monitoring

The TriggerRegistry manages all triggers and provides a unified
check interface.
"""

import logging
from typing import Dict, List, Optional

from .base import BaseTrigger, TriggerResult
from .external import ExternalTrigger
from .manual import ManualTrigger
from .threshold import ThresholdTrigger
from .watchdog import WatchdogTrigger


logger = logging.getLogger(__name__)


class TriggerRegistry:
    """Registry for all kill switch triggers.

    Manages trigger lifecycle and provides unified check interface.

    Usage:
        >>> config = load_config()
        >>> registry = TriggerRegistry.from_config(config)
        >>>
        >>> # Check all triggers
        >>> context = {"portfolio_drawdown": -0.12, ...}
        >>> results = registry.check_all(context)
        >>>
        >>> # Check if any triggered
        >>> if any(r.should_trigger for r in results):
        ...     # Trigger kill switch
    """

    TRIGGER_TYPES = {
        "threshold": ThresholdTrigger,
        "manual": ManualTrigger,
        "watchdog": WatchdogTrigger,
        "external": ExternalTrigger,
    }

    def __init__(self):
        """Initialize empty trigger registry."""
        self._triggers: Dict[str, BaseTrigger] = {}

    def register(self, name: str, trigger: BaseTrigger):
        """Register a trigger.

        Args:
            name: Unique trigger name
            trigger: Trigger instance
        """
        if name in self._triggers:
            logger.warning(f"Trigger '{name}' already registered, replacing")

        self._triggers[name] = trigger
        logger.info(f"Registered trigger: {name} ({trigger.__class__.__name__})")

    def get(self, name: str) -> Optional[BaseTrigger]:
        """Get a trigger by name.

        Args:
            name: Trigger name

        Returns:
            Trigger instance or None if not found
        """
        return self._triggers.get(name)

    def check_all(self, context: dict) -> List[TriggerResult]:
        """Check all enabled triggers.

        Args:
            context: System context for trigger checks

        Returns:
            List of TriggerResults from all triggers
        """
        results = []

        for name, trigger in self._triggers.items():
            if not trigger.enabled:
                continue

            try:
                result = trigger.check(context)
                results.append(result)

                if result.should_trigger:
                    logger.warning(f"🚨 Trigger '{name}' FIRED: {result.reason}")

            except Exception as e:
                logger.error(f"Error checking trigger '{name}': {e}", exc_info=True)
                # Don't propagate trigger errors - fail safe
                results.append(
                    TriggerResult(
                        should_trigger=False,
                        reason=f"Trigger check failed: {e}",
                        metadata={"error": str(e), "trigger_name": name},
                    )
                )

        return results

    def get_triggered(self, context: dict) -> List[tuple[str, TriggerResult]]:
        """Get all triggers that should fire.

        Args:
            context: System context

        Returns:
            List of (trigger_name, result) tuples for triggered conditions
        """
        triggered = []
        results = self.check_all(context)

        for name, trigger in self._triggers.items():
            result = next((r for r in results if r.metadata.get("trigger_name") == name), None)
            if result and result.should_trigger:
                triggered.append((name, result))

        return triggered

    def list_triggers(self) -> List[str]:
        """List all registered trigger names.

        Returns:
            List of trigger names
        """
        return list(self._triggers.keys())

    def get_status(self) -> dict:
        """Get status of all triggers.

        Returns:
            Dictionary with trigger status information
        """
        status = {}

        for name, trigger in self._triggers.items():
            status[name] = {
                "enabled": trigger.enabled,
                "type": trigger.__class__.__name__,
                "on_cooldown": trigger.is_on_cooldown(),
                "cooldown_remaining": trigger.get_cooldown_remaining(),
            }

        return status

    @classmethod
    def from_config(cls, config: dict) -> "TriggerRegistry":
        """Create TriggerRegistry from configuration.

        Args:
            config: Full configuration dictionary

        Returns:
            Configured TriggerRegistry instance
        """
        registry = cls()

        # Load triggers from config
        triggers_config = config.get("kill_switch.triggers", {})

        for trigger_name, trigger_config in triggers_config.items():
            trigger_type = trigger_config.get("type")

            if trigger_type not in cls.TRIGGER_TYPES:
                logger.warning(
                    f"Unknown trigger type '{trigger_type}' for '{trigger_name}', skipping"
                )
                continue

            trigger_class = cls.TRIGGER_TYPES[trigger_type]

            try:
                trigger = trigger_class(trigger_name, trigger_config)
                registry.register(trigger_name, trigger)

            except Exception as e:
                logger.error(f"Failed to create trigger '{trigger_name}': {e}", exc_info=True)

        logger.info(
            f"Loaded {len(registry._triggers)} triggers: {', '.join(registry.list_triggers())}"
        )

        return registry


__all__ = [
    # Base
    "BaseTrigger",
    "TriggerResult",
    # Trigger types
    "ThresholdTrigger",
    "ManualTrigger",
    "WatchdogTrigger",
    "ExternalTrigger",
    # Registry
    "TriggerRegistry",
]
