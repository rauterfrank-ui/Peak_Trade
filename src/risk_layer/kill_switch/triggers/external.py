"""External Triggers.

Triggers based on external system state (exchange connection, network, etc.).
"""

import logging
from datetime import datetime
from typing import Optional

from .base import BaseTrigger, TriggerResult


logger = logging.getLogger(__name__)


class ExternalTrigger(BaseTrigger):
    """Trigger based on external system state.

    Monitors:
        - Exchange connection status
        - Network connectivity
        - API rate limits
        - External system health

    Config Example:
        {
            "enabled": true,
            "type": "external",
            "check_interval_seconds": 30,
            "max_consecutive_failures": 3
        }
    """

    def __init__(self, name: str, config: dict):
        """Initialize external trigger.

        Args:
            name: Trigger name
            config: Configuration
        """
        super().__init__(name, config)

        self.check_interval = config.get("check_interval_seconds", 30)
        self.max_failures = config.get("max_consecutive_failures", 3)

        self._consecutive_failures = 0
        self._last_check: Optional[datetime] = None

    def check(self, context: dict) -> TriggerResult:
        """Check external system health.

        Args:
            context: System context with external state
                Expected keys:
                - exchange_connected: bool
                - last_price_update: datetime
                - api_errors: int (recent count)

        Returns:
            TriggerResult indicating if external systems are failing
        """
        if not self.enabled:
            return TriggerResult(
                should_trigger=False, reason=f"External trigger '{self.name}' disabled"
            )

        # Check if we should check (rate limiting)
        now = datetime.utcnow()
        if self._last_check:
            elapsed = (now - self._last_check).total_seconds()
            if elapsed < self.check_interval:
                return TriggerResult(
                    should_trigger=False,
                    reason=f"Check interval not reached ({elapsed:.0f}s < {self.check_interval}s)",
                )

        self._last_check = now

        issues = []
        metadata = {}

        # Check exchange connection
        exchange_connected = context.get("exchange_connected", True)
        metadata["exchange_connected"] = exchange_connected

        if not exchange_connected:
            self._consecutive_failures += 1
            issues.append(
                f"Exchange disconnected ({self._consecutive_failures} consecutive failures)"
            )
        else:
            self._consecutive_failures = 0

        # Check last price update (stale data)
        last_price_update = context.get("last_price_update")
        if last_price_update:
            stale_seconds = (now - last_price_update).total_seconds()
            metadata["price_data_age_seconds"] = stale_seconds

            # If price data is >5 minutes old, that's a problem
            if stale_seconds > 300:
                issues.append(f"Stale price data: {stale_seconds:.0f}s old")

        # Check API errors
        api_errors = context.get("api_errors", 0)
        metadata["api_errors"] = api_errors

        if api_errors > 10:  # More than 10 recent errors
            issues.append(f"High API error rate: {api_errors} errors")

        # Trigger if we have consecutive failures
        if self._consecutive_failures >= self.max_failures:
            self.mark_triggered()
            return TriggerResult(
                should_trigger=True,
                reason=f"External system failure: {'; '.join(issues)}",
                metadata={
                    "trigger_name": self.name,
                    "trigger_type": "external",
                    "consecutive_failures": self._consecutive_failures,
                    **metadata,
                },
            )

        if issues:
            # Have issues but not yet at threshold
            return TriggerResult(
                should_trigger=False,
                reason=f"External issues detected: {'; '.join(issues)} "
                f"(failures: {self._consecutive_failures}/{self.max_failures})",
                metadata=metadata,
            )

        return TriggerResult(
            should_trigger=False,
            reason="External systems OK",
            metadata=metadata,
        )

    def reset(self):
        """Reset consecutive failure counter."""
        self._consecutive_failures = 0

    def __repr__(self) -> str:
        return (
            f"ExternalTrigger("
            f"name='{self.name}', "
            f"max_failures={self.max_failures}, "
            f"check_interval={self.check_interval}s, "
            f"enabled={self.enabled}"
            f")"
        )
