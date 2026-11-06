"""Execution Gate for Kill Switch Integration.

Provides the gate interface that blocks trading when kill switch is active.
"""

from typing import Protocol

from .core import KillSwitch, TradingBlockedError


class ExecutionGateProtocol(Protocol):
    """Protocol for execution gate.

    This defines the contract that any execution gate must implement.
    """

    def check_can_execute(self) -> bool:
        """Check if execution is allowed.

        Returns:
            True if allowed

        Raises:
            TradingBlockedError if blocked
        """
        ...


class ExecutionGate:
    """Gate for order execution.

    Integrates kill switch with the execution layer.
    Every order MUST pass through this gate.

    Usage:
        >>> gate = ExecutionGate(kill_switch)
        >>>
        >>> # Before executing order
        >>> try:
        ...     gate.check_can_execute()
        ...     # Execute order...
        ... except TradingBlockedError as e:
        ...     logger.error(f"Trading blocked: {e}")
        >>>
        >>> # Or use as context manager
        >>> with gate:
        ...     # Execute order...
    """

    def __init__(self, kill_switch: KillSwitch):
        """Initialize execution gate.

        Args:
            kill_switch: KillSwitch instance
        """
        self._kill_switch = kill_switch

    def check_can_execute(self) -> bool:
        """Check if execution is allowed.

        Returns:
            True if execution allowed

        Raises:
            TradingBlockedError if kill switch is active
        """
        if self._kill_switch.check_and_block():
            raise TradingBlockedError(
                f"Trading blocked: Kill Switch is {self._kill_switch.state.name}"
            )

        return True

    def execute_with_gate(self, order_func, *args, **kwargs):
        """Execute order function with gate check.

        Args:
            order_func: Function that executes the order
            *args, **kwargs: Arguments for order_func

        Returns:
            Result of order_func

        Raises:
            TradingBlockedError if blocked
        """
        self.check_can_execute()
        return order_func(*args, **kwargs)

    def is_blocked(self) -> bool:
        """Check if execution is blocked (without raising exception).

        Returns:
            True if blocked, False if allowed
        """
        return self._kill_switch.check_and_block()

    def get_block_reason(self) -> str:
        """Get reason for block.

        Returns:
            Human-readable block reason
        """
        if not self.is_blocked():
            return "Not blocked"

        status = self._kill_switch.get_status()
        state = status["state"]

        if state == "KILLED":
            return f"Kill Switch triggered at {status.get('killed_at', 'unknown')}"
        elif state == "RECOVERING":
            remaining = status.get("cooldown_remaining_seconds", 0)
            return f"Kill Switch recovering (cooldown: {remaining:.0f}s remaining)"
        else:
            return f"Kill Switch in state: {state}"

    # Context manager support
    def __enter__(self):
        """Enter context - check gate."""
        self.check_can_execute()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        return False  # Don't suppress exceptions
