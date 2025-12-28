"""Kill Switch Core Implementation.

This is the heart of the Emergency Kill Switch system - Layer 4 of the
Defense-in-Depth architecture. It MUST always work, regardless of other
system failures.
"""

import logging
from datetime import datetime, timedelta
from threading import RLock
from typing import Callable, List, Optional

from .state import KillSwitchEvent, KillSwitchState, validate_transition


class KillSwitch:
    """Emergency Kill Switch for Peak_Trade.

    Layer 4 of Defense-in-Depth architecture.
    Last line of defense - MUST ALWAYS WORK.

    Thread-safe through RLock.

    Usage:
        >>> config = {"recovery_cooldown_seconds": 300}
        >>> ks = KillSwitch(config)
        >>>
        >>> # Trigger emergency stop
        >>> ks.trigger("Drawdown threshold exceeded")
        >>>
        >>> # Check if trading is blocked
        >>> if ks.check_and_block():
        ...     raise TradingBlockedError()
        >>>
        >>> # Request recovery
        >>> ks.request_recovery("operator", "APPROVAL_CODE")
        >>>
        >>> # After cooldown
        >>> ks.complete_recovery()
    """

    def __init__(
        self,
        config: dict,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize Kill Switch.

        Args:
            config: Configuration dictionary (from config.toml)
            logger: Optional logger instance
        """
        self._lock = RLock()
        self._state = KillSwitchState.ACTIVE
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

        # Compatibility: Override flag for enabled property (does NOT mutate config)
        self._enabled_override: Optional[bool] = None

        # Check if disabled (backtest mode)
        if config.get("mode") == "disabled":
            self._state = KillSwitchState.DISABLED
            self._logger.warning(
                "⚠️  Kill Switch DISABLED (Backtest Mode) - Trading will NOT be blocked!"
            )

        # Event history for audit
        self._events: List[KillSwitchEvent] = []

        # Callbacks for state changes
        self._on_kill_callbacks: List[Callable[[KillSwitchEvent], None]] = []
        self._on_recover_callbacks: List[Callable[[KillSwitchEvent], None]] = []

        # Timestamps
        self._killed_at: Optional[datetime] = None
        self._recovery_started_at: Optional[datetime] = None

        # Cooldown configuration
        self._recovery_cooldown = timedelta(seconds=config.get("recovery_cooldown_seconds", 300))

        self._logger.info(
            f"KillSwitch initialized: state={self._state.name}, cooldown={self._recovery_cooldown}"
        )

    @property
    def state(self) -> KillSwitchState:
        """Current state (thread-safe read)."""
        with self._lock:
            return self._state

    @property
    def is_killed(self) -> bool:
        """True if trading is stopped."""
        return self.state in (KillSwitchState.KILLED, KillSwitchState.RECOVERING)

    @property
    def is_active(self) -> bool:
        """True if trading is allowed."""
        return self.state == KillSwitchState.ACTIVE

    @property
    def enabled(self) -> bool:
        """Check if Kill Switch is enabled.

        Compatibility property for legacy KillSwitchLayer API.

        Priority:
            1. Override flag (if set via setter)
            2. Config "enabled" key
            3. Default: True

        Returns:
            True if enabled, False if disabled
        """
        # Check override first (set via setter)
        if self._enabled_override is not None:
            return bool(self._enabled_override)

        # Check config
        cfg = getattr(self, "_config", None)
        if cfg is None:
            return True

        # Support both dict and object configs
        if isinstance(cfg, dict):
            return bool(cfg.get("enabled", True))

        return bool(getattr(cfg, "enabled", True))

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set enabled override.

        Does NOT mutate config - uses override flag instead.

        Args:
            value: True to enable, False to disable
        """
        with self._lock:
            self._enabled_override = bool(value)
            self._logger.debug(f"Kill Switch enabled override set to: {value}")

    @property
    def is_disabled(self) -> bool:
        """True if kill switch is disabled (backtest mode)."""
        return self.state == KillSwitchState.DISABLED

    def trigger(
        self,
        reason: str,
        triggered_by: str = "system",
        metadata: Optional[dict] = None,
    ) -> bool:
        """Activate Kill Switch (EMERGENCY STOP).

        This is idempotent - calling multiple times is safe.

        Args:
            reason: Reason for trigger (for audit)
            triggered_by: Who triggered ("system", "manual", "threshold", etc.)
            metadata: Additional context data

        Returns:
            True if successfully triggered or already killed
            False if disabled
        """
        with self._lock:
            if self._state == KillSwitchState.DISABLED:
                self._logger.warning("⚠️  Kill Switch is DISABLED (Backtest Mode) - Trigger ignored")
                return False

            if self._state == KillSwitchState.KILLED:
                self._logger.warning("Kill Switch already KILLED (idempotent)")
                return True  # Already in desired state

            # State transition
            previous = self._state
            self._state = KillSwitchState.KILLED
            self._killed_at = datetime.utcnow()

            # Log event
            event = KillSwitchEvent(
                timestamp=self._killed_at,
                previous_state=previous,
                new_state=self._state,
                trigger_reason=reason,
                triggered_by=triggered_by,
                metadata=metadata or {},
            )
            self._events.append(event)

            self._logger.critical(
                f"🚨 KILL SWITCH TRIGGERED: {reason} (by={triggered_by}, from={previous.name})"
            )

            # Execute callbacks (outside lock to avoid deadlocks)
            # We copy the list first
            callbacks = list(self._on_kill_callbacks)

        # Execute callbacks outside lock
        self._execute_callbacks(callbacks, event)

        return True

    def request_recovery(
        self,
        approved_by: str,
        approval_code: Optional[str] = None,
    ) -> bool:
        """Start recovery process (with cooldown).

        Args:
            approved_by: Who approved the recovery
            approval_code: Optional approval code for validation

        Returns:
            True if recovery started
            False if not in KILLED state or validation failed
        """
        with self._lock:
            # Idempotent: if already RECOVERING, return True
            if self._state == KillSwitchState.RECOVERING:
                self._logger.info(f"Already RECOVERING (idempotent request by {approved_by})")
                return True

            if self._state != KillSwitchState.KILLED:
                self._logger.warning(
                    f"Recovery only possible from KILLED state, currently: {self._state.name}"
                )
                return False

            # Validate approval code if required
            if self._config.get("require_approval_code", False):
                if not self._validate_approval_code(approval_code):
                    self._logger.error("❌ Invalid Approval Code")
                    return False

            # State transition
            previous = self._state
            self._state = KillSwitchState.RECOVERING
            self._recovery_started_at = datetime.utcnow()

            event = KillSwitchEvent(
                timestamp=self._recovery_started_at,
                previous_state=previous,
                new_state=self._state,
                trigger_reason=f"Recovery requested by {approved_by}",
                triggered_by="manual",
                metadata={"approved_by": approved_by},
            )
            self._events.append(event)

            self._logger.warning(
                f"⏳ RECOVERY STARTED: cooldown={self._recovery_cooldown}, "
                f"approved_by={approved_by}"
            )

            return True

    def complete_recovery(self) -> bool:
        """Complete recovery (after cooldown).

        Returns:
            True if successfully recovered
            False if not in RECOVERING state or cooldown not complete
        """
        with self._lock:
            if self._state != KillSwitchState.RECOVERING:
                self._logger.warning(
                    f"Complete recovery only possible from RECOVERING state, "
                    f"currently: {self._state.name}"
                )
                return False

            # Check cooldown
            if self._recovery_started_at:
                elapsed = datetime.utcnow() - self._recovery_started_at
                if elapsed < self._recovery_cooldown:
                    remaining = self._recovery_cooldown - elapsed
                    self._logger.warning(
                        f"⏳ Cooldown still active: {remaining.seconds}s remaining"
                    )
                    return False

            # State transition
            previous = self._state
            self._state = KillSwitchState.ACTIVE

            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=previous,
                new_state=self._state,
                trigger_reason="Recovery completed",
                triggered_by="system",
                metadata={},
            )
            self._events.append(event)

            # Reset timestamps
            self._killed_at = None
            self._recovery_started_at = None

            self._logger.info("✅ KILL SWITCH RECOVERED: Trading active again")

            # Execute callbacks
            callbacks = list(self._on_recover_callbacks)

        # Execute callbacks outside lock
        self._execute_callbacks(callbacks, event)

        return True

    def check_and_block(self) -> bool:
        """Check if trading is blocked.

        Returns:
            True if trading is BLOCKED (killed or recovering)
            False if trading is allowed

        Usage:
            if kill_switch.check_and_block():
                raise TradingBlockedError("Kill Switch active")
        """
        return self.is_killed

    def register_on_kill(self, callback: Callable[[KillSwitchEvent], None]):
        """Register callback for kill events.

        Args:
            callback: Function to call when kill switch is triggered
        """
        with self._lock:
            self._on_kill_callbacks.append(callback)

    def register_on_recover(self, callback: Callable[[KillSwitchEvent], None]):
        """Register callback for recovery events.

        Args:
            callback: Function to call when recovery completes
        """
        with self._lock:
            self._on_recover_callbacks.append(callback)

    def get_audit_trail(self) -> List[KillSwitchEvent]:
        """Get all events for audit.

        Returns:
            List of all kill switch events
        """
        with self._lock:
            return list(self._events)

    def get_status(self) -> dict:
        """Get current status information.

        Returns:
            Dictionary with current status
        """
        with self._lock:
            status = {
                "state": self._state.name,
                "is_killed": self.is_killed,
                "is_active": self.is_active,
                "killed_at": self._killed_at.isoformat() if self._killed_at else None,
                "recovery_started_at": (
                    self._recovery_started_at.isoformat() if self._recovery_started_at else None
                ),
                "event_count": len(self._events),
            }

            # Add cooldown info if recovering
            if self._state == KillSwitchState.RECOVERING and self._recovery_started_at:
                elapsed = datetime.utcnow() - self._recovery_started_at
                remaining = max(timedelta(0), self._recovery_cooldown - elapsed)
                status["cooldown_remaining_seconds"] = remaining.total_seconds()

            return status

    def _validate_approval_code(self, code: Optional[str]) -> bool:
        """Validate approval code.

        Args:
            code: Code to validate

        Returns:
            True if valid, False otherwise
        """
        expected = self._config.get("approval_code")

        # If no expected code is set, accept any (for testing)
        if not expected:
            return True

        return code == expected

    def _execute_callbacks(
        self,
        callbacks: List[Callable],
        event: KillSwitchEvent,
    ):
        """Execute callbacks safely.

        Args:
            callbacks: List of callback functions
            event: Event to pass to callbacks
        """
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Callback error: {e}", exc_info=True)


class TradingBlockedError(Exception):
    """Exception raised when trading is blocked by Kill Switch."""

    def __init__(self, message: str = "Trading blocked by Kill Switch"):
        super().__init__(message)
