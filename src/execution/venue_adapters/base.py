"""
Base Venue Adapter Protocol (WP0C - Phase 0 Foundation)

Defines the OrderAdapter protocol for venue execution.
This is a re-export/extension of the protocol defined in orchestrator.py.

IMPORTANT: NO live execution. Adapters are for paper/shadow/testnet only.
"""

from typing import Protocol

from src.execution.contracts import Order
from src.execution.orchestrator import ExecutionEvent


class OrderAdapter(Protocol):
    """
    Protocol for order execution adapters.

    Adapters must implement:
    - execute_order: Submit order and return execution event (ACK/REJECT/FILL)
    - Idempotency: Same idempotency_key → same result (no duplicates)
    - Timeout: Adapters should complete within 30s (configurable)

    Implementations:
    - SimulatedVenueAdapter: Deterministic paper/shadow execution
    - (Future) LiveVenueAdapter: Real exchange execution (Phase 2+)
    """

    def execute_order(self, order: Order, idempotency_key: str) -> ExecutionEvent:
        """
        Execute order and return execution event.

        Args:
            order: Order to execute
            idempotency_key: Idempotency key (prevents duplicate submission)

        Returns:
            ExecutionEvent (ACK/REJECT/FILL)

        Raises:
            VenueAdapterError: If execution fails (network, timeout, etc.)
        """
        ...


class VenueAdapterError(Exception):
    """
    Exception raised by venue adapters on execution failure.

    Categories:
    - Network errors (transient, retryable)
    - Timeout errors
    - Validation errors (non-retryable)
    - Exchange rejection (non-retryable)
    """

    pass
