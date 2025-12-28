"""Manual Trigger.

Trigger that can be activated manually via CLI or API.
"""

from .base import BaseTrigger, TriggerResult


class ManualTrigger(BaseTrigger):
    """Manual trigger for operator-initiated kill switch.

    This trigger always returns False in check() - it's activated
    directly by calling the KillSwitch.trigger() method.

    Config Example:
        {
            "enabled": true,
            "type": "manual"
        }
    """

    def __init__(self, name: str, config: dict):
        """Initialize manual trigger.

        Args:
            name: Trigger name
            config: Configuration
        """
        super().__init__(name, config)
        self._manual_triggered = False
        self._manual_reason = ""

    def check(self, context: dict) -> TriggerResult:
        """Check if manual trigger is active.

        Args:
            context: System context (ignored for manual trigger)

        Returns:
            TriggerResult (always False in normal operation)
        """
        if not self.enabled:
            return TriggerResult(
                should_trigger=False,
                reason=f"Manual trigger '{self.name}' disabled"
            )

        # Manual trigger doesn't auto-trigger
        # It's activated directly via KillSwitch.trigger()
        return TriggerResult(
            should_trigger=False,
            reason="Manual trigger waiting for operator action"
        )

    def request_trigger(self, reason: str) -> TriggerResult:
        """Request manual trigger.

        This is called by CLI/API when operator wants to trigger.

        Args:
            reason: Operator-provided reason

        Returns:
            TriggerResult indicating trigger should fire
        """
        if not self.enabled:
            return TriggerResult(
                should_trigger=False,
                reason=f"Manual trigger '{self.name}' disabled"
            )

        self._manual_triggered = True
        self._manual_reason = reason
        self.mark_triggered()

        return TriggerResult(
            should_trigger=True,
            reason=f"Manual trigger: {reason}",
            metadata={
                "trigger_name": self.name,
                "trigger_type": "manual",
                "manual_reason": reason,
            }
        )

    def reset(self):
        """Reset manual trigger state."""
        self._manual_triggered = False
        self._manual_reason = ""
