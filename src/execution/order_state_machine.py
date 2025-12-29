"""
Order State Machine (WP0A - Phase 0 Execution Core)

Implements the deterministic order lifecycle state machine:
CREATED → SUBMITTED → ACKNOWLEDGED → PARTIALLY_FILLED → FILLED → CLOSED

Design Goals:
- Idempotent transitions (retry-safe)
- Deterministic state changes
- Validation of allowed transitions
- Integration with risk_hook for pre-submission checks
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

from src.execution.contracts import (
    Order,
    OrderState,
    Fill,
    LedgerEntry,
    validate_order,
)
from src.execution.risk_hook import RiskHook, NullRiskHook


# ============================================================================
# State Transition Rules
# ============================================================================


# Valid state transitions (deterministic state machine)
VALID_TRANSITIONS: Dict[OrderState, List[OrderState]] = {
    OrderState.CREATED: [
        OrderState.SUBMITTED,
        OrderState.CANCELLED,  # Cancel before submission
        OrderState.FAILED,     # Validation failed
    ],
    OrderState.SUBMITTED: [
        OrderState.ACKNOWLEDGED,
        OrderState.REJECTED,    # Exchange rejected
        OrderState.FAILED,      # Network/system failure
        OrderState.CANCELLED,   # Cancel in-flight
    ],
    OrderState.ACKNOWLEDGED: [
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.EXPIRED,
    ],
    OrderState.PARTIALLY_FILLED: [
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.EXPIRED,
    ],
    # Terminal states (no outgoing transitions)
    OrderState.FILLED: [],
    OrderState.CANCELLED: [],
    OrderState.REJECTED: [],
    OrderState.EXPIRED: [],
    OrderState.FAILED: [],
}


def is_valid_transition(from_state: OrderState, to_state: OrderState) -> bool:
    """
    Check if a state transition is valid.

    Args:
        from_state: Current state
        to_state: Target state

    Returns:
        True if transition is valid, False otherwise
    """
    return to_state in VALID_TRANSITIONS.get(from_state, [])


# ============================================================================
# State Machine Result
# ============================================================================


@dataclass
class StateMachineResult:
    """Result of a state machine operation"""

    success: bool
    order: Order
    message: str = ""
    ledger_entries: List[LedgerEntry] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging/debugging"""
        return {
            "success": self.success,
            "order_id": self.order.client_order_id,
            "state": self.order.state.value,
            "message": self.message,
            "ledger_entries_count": len(self.ledger_entries),
            "metadata": self.metadata,
        }


# ============================================================================
# Order State Machine
# ============================================================================


class OrderStateMachine:
    """
    Deterministic order lifecycle state machine.

    Features:
    - Idempotent transitions (safe for retries)
    - Validation of state transitions
    - Ledger integration (audit trail)
    - Risk hook integration (pre-submission checks)
    """

    def __init__(
        self,
        risk_hook: Optional[RiskHook] = None,
        enable_audit: bool = True,
    ):
        """
        Initialize state machine.

        Args:
            risk_hook: Risk evaluation hook (optional, defaults to NullRiskHook)
            enable_audit: Enable audit log generation
        """
        self.risk_hook = risk_hook or NullRiskHook()
        self.enable_audit = enable_audit
        self._ledger_sequence = 0

    def create_order(
        self,
        client_order_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        **kwargs,
    ) -> StateMachineResult:
        """
        Create a new order (initial state: CREATED).

        Args:
            client_order_id: Unique client order ID
            symbol: Trading symbol
            side: "BUY" or "SELL"
            quantity: Order quantity
            **kwargs: Additional order fields (price, order_type, etc.)

        Returns:
            StateMachineResult with created order
        """
        from src.execution.contracts import OrderSide, OrderType

        # Create order object
        order = Order(
            client_order_id=client_order_id,
            symbol=symbol,
            side=OrderSide(side),
            quantity=quantity,
            state=OrderState.CREATED,
            **kwargs,
        )

        # Validate order
        if not validate_order(order):
            return StateMachineResult(
                success=False,
                order=order,
                message="Order validation failed",
                metadata={"validation": "failed"},
            )

        # Generate ledger entry
        ledger_entries = []
        if self.enable_audit:
            ledger_entries.append(self._create_ledger_entry(
                order=order,
                event_type="ORDER_CREATED",
                old_state=None,
                new_state=OrderState.CREATED,
            ))

        return StateMachineResult(
            success=True,
            order=order,
            message=f"Order {client_order_id} created",
            ledger_entries=ledger_entries,
        )

    def submit_order(self, order: Order) -> StateMachineResult:
        """
        Submit order (transition: CREATED → SUBMITTED).

        Checks:
        - Current state is CREATED
        - Risk hook allows order
        - Valid transition

        Args:
            order: Order to submit

        Returns:
            StateMachineResult with updated order
        """
        # Check current state
        if order.state != OrderState.CREATED:
            # Idempotent: if already submitted, return success
            if order.state == OrderState.SUBMITTED:
                return StateMachineResult(
                    success=True,
                    order=order,
                    message=f"Order {order.client_order_id} already submitted",
                    metadata={"idempotent": True},
                )

            return StateMachineResult(
                success=False,
                order=order,
                message=f"Cannot submit order in state {order.state.value}",
                metadata={"invalid_state": order.state.value},
            )

        # Check risk hook
        risk_result = self.risk_hook.evaluate_order(order)
        if risk_result.decision.value != "ALLOW":
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Risk check blocked order: {risk_result.reason}",
                metadata={"risk_result": risk_result.to_dict()},
            )

        # Transition to SUBMITTED
        return self._transition(
            order=order,
            new_state=OrderState.SUBMITTED,
            event_type="ORDER_SUBMITTED",
            message=f"Order {order.client_order_id} submitted",
        )

    def acknowledge_order(
        self,
        order: Order,
        exchange_order_id: str,
    ) -> StateMachineResult:
        """
        Acknowledge order (transition: SUBMITTED → ACKNOWLEDGED).

        Args:
            order: Order to acknowledge
            exchange_order_id: Exchange-provided order ID

        Returns:
            StateMachineResult with updated order
        """
        # Check current state (idempotent)
        if order.state == OrderState.ACKNOWLEDGED:
            return StateMachineResult(
                success=True,
                order=order,
                message=f"Order {order.client_order_id} already acknowledged",
                metadata={"idempotent": True},
            )

        if order.state != OrderState.SUBMITTED:
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Cannot acknowledge order in state {order.state.value}",
                metadata={"invalid_state": order.state.value},
            )

        # Update exchange order ID
        order.exchange_order_id = exchange_order_id

        # Transition to ACKNOWLEDGED
        return self._transition(
            order=order,
            new_state=OrderState.ACKNOWLEDGED,
            event_type="ORDER_ACKNOWLEDGED",
            message=f"Order {order.client_order_id} acknowledged by exchange",
            metadata={"exchange_order_id": exchange_order_id},
        )

    def apply_fill(self, order: Order, fill: Fill) -> StateMachineResult:
        """
        Apply fill to order (transition: ACKNOWLEDGED/PARTIALLY_FILLED → PARTIALLY_FILLED/FILLED).

        Args:
            order: Order receiving fill
            fill: Fill to apply

        Returns:
            StateMachineResult with updated order
        """
        # Check current state
        if order.state.is_terminal():
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Cannot apply fill to order in terminal state {order.state.value}",
                metadata={"invalid_state": order.state.value},
            )

        if not order.state.is_active():
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Cannot apply fill to order in state {order.state.value}",
                metadata={"invalid_state": order.state.value},
            )

        # Determine new state based on fill quantity
        # (In real implementation, track cumulative fills)
        # For now, simple logic: if fill.quantity >= order.quantity → FILLED
        if fill.quantity >= order.quantity:
            new_state = OrderState.FILLED
            event_type = "ORDER_FILLED"
            message = f"Order {order.client_order_id} fully filled"
        else:
            new_state = OrderState.PARTIALLY_FILLED
            event_type = "ORDER_PARTIALLY_FILLED"
            message = f"Order {order.client_order_id} partially filled ({fill.quantity}/{order.quantity})"

        # Transition
        return self._transition(
            order=order,
            new_state=new_state,
            event_type=event_type,
            message=message,
            metadata={"fill_id": fill.fill_id, "fill_quantity": str(fill.quantity)},
        )

    def cancel_order(self, order: Order, reason: str = "") -> StateMachineResult:
        """
        Cancel order (transition: * → CANCELLED).

        Args:
            order: Order to cancel
            reason: Cancellation reason

        Returns:
            StateMachineResult with updated order
        """
        # Check if already terminal
        if order.state == OrderState.CANCELLED:
            return StateMachineResult(
                success=True,
                order=order,
                message=f"Order {order.client_order_id} already cancelled",
                metadata={"idempotent": True},
            )

        if order.state.is_terminal():
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Cannot cancel order in terminal state {order.state.value}",
                metadata={"invalid_state": order.state.value},
            )

        # Check if transition is valid
        if not is_valid_transition(order.state, OrderState.CANCELLED):
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Cannot cancel order in state {order.state.value}",
                metadata={"invalid_transition": True},
            )

        # Transition to CANCELLED
        return self._transition(
            order=order,
            new_state=OrderState.CANCELLED,
            event_type="ORDER_CANCELLED",
            message=f"Order {order.client_order_id} cancelled: {reason}",
            metadata={"reason": reason},
        )

    def reject_order(self, order: Order, reason: str = "") -> StateMachineResult:
        """
        Reject order (transition: SUBMITTED → REJECTED).

        Args:
            order: Order to reject
            reason: Rejection reason

        Returns:
            StateMachineResult with updated order
        """
        if order.state != OrderState.SUBMITTED:
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Cannot reject order in state {order.state.value}",
                metadata={"invalid_state": order.state.value},
            )

        return self._transition(
            order=order,
            new_state=OrderState.REJECTED,
            event_type="ORDER_REJECTED",
            message=f"Order {order.client_order_id} rejected: {reason}",
            metadata={"reason": reason},
        )

    def fail_order(self, order: Order, reason: str = "") -> StateMachineResult:
        """
        Mark order as failed (transition: * → FAILED).

        Args:
            order: Order that failed
            reason: Failure reason

        Returns:
            StateMachineResult with updated order
        """
        if order.state.is_terminal():
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Order {order.client_order_id} already in terminal state",
                metadata={"invalid_state": order.state.value},
            )

        return self._transition(
            order=order,
            new_state=OrderState.FAILED,
            event_type="ORDER_FAILED",
            message=f"Order {order.client_order_id} failed: {reason}",
            metadata={"reason": reason},
        )

    def _transition(
        self,
        order: Order,
        new_state: OrderState,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateMachineResult:
        """
        Internal: Perform state transition.

        Args:
            order: Order to transition
            new_state: Target state
            event_type: Event type for ledger
            message: Human-readable message
            metadata: Additional metadata

        Returns:
            StateMachineResult
        """
        old_state = order.state

        # Check if transition is valid
        if not is_valid_transition(old_state, new_state):
            return StateMachineResult(
                success=False,
                order=order,
                message=f"Invalid transition: {old_state.value} → {new_state.value}",
                metadata={"invalid_transition": True},
            )

        # Perform transition
        order.state = new_state
        order.updated_at = datetime.utcnow()

        # Generate ledger entry
        ledger_entries = []
        if self.enable_audit:
            ledger_entries.append(self._create_ledger_entry(
                order=order,
                event_type=event_type,
                old_state=old_state,
                new_state=new_state,
                details=metadata or {},
            ))

        return StateMachineResult(
            success=True,
            order=order,
            message=message,
            ledger_entries=ledger_entries,
            metadata=metadata or {},
        )

    def _create_ledger_entry(
        self,
        order: Order,
        event_type: str,
        old_state: Optional[OrderState],
        new_state: OrderState,
        details: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """
        Internal: Create ledger entry for audit trail.

        Args:
            order: Order
            event_type: Event type
            old_state: Previous state
            new_state: New state
            details: Additional details

        Returns:
            LedgerEntry
        """
        self._ledger_sequence += 1

        return LedgerEntry(
            entry_id=f"{order.client_order_id}_{self._ledger_sequence}",
            sequence=self._ledger_sequence,
            event_type=event_type,
            client_order_id=order.client_order_id,
            old_state=old_state,
            new_state=new_state,
            details=details or {},
        )
