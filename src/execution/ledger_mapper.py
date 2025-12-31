"""
LedgerEntry Mapper (WP0D - Phase 0 Recon/Ledger Bridge)

Maps ExecutionEvents to LedgerEntry records for audit trail.

Design:
- FILL → TRADE LedgerEntry (+ optional FEE entry)
- REJECT → No LedgerEntry (audit log only)
- CANCEL_ACK → No LedgerEntry (order state only)
- ACK → No LedgerEntry (order state only)

Deterministic: Same input → same output (no random, no clock)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime
from src.execution.contracts import LedgerEntry, Fill, OrderState

if TYPE_CHECKING:
    from src.execution.orchestrator import ExecutionEvent


class EventToLedgerMapper:
    """
    Maps ExecutionEvent to LedgerEntry for audit trail.

    Rules:
    - FILL: Create TRADE entry (quantity, price, side, fees)
    - REJECT/CANCEL_ACK/ACK: No ledger entry (no position impact)
    """

    def __init__(self):
        """Initialize mapper with sequence counter."""
        self._sequence_counter = 0

    def map_event_to_ledger_entries(
        self,
        execution_event: "ExecutionEvent",
        correlation_id: str,
    ) -> List[LedgerEntry]:
        """
        Map ExecutionEvent to zero or more LedgerEntry records.

        Args:
            execution_event: Execution event from adapter
            correlation_id: Correlation ID for tracing

        Returns:
            List of LedgerEntry (empty for non-FILL events)
        """
        # Only FILL events create ledger entries
        if execution_event.event_type != "FILL":
            return []

        # Validate fill exists
        fill = execution_event.fill
        if fill is None:
            return []

        # Create TRADE entry
        self._sequence_counter += 1

        entry = LedgerEntry(
            entry_id=f"ledger_{correlation_id}_{self._sequence_counter}",
            timestamp=execution_event.timestamp,
            sequence=self._sequence_counter,
            event_type="FILL_RECEIVED",  # Changed from "TRADE" to match audit log conventions
            client_order_id=execution_event.order_id,
            old_state=None,  # Fills don't have state transitions
            new_state=None,
            details={
                "correlation_id": correlation_id,
                "exchange_order_id": execution_event.exchange_order_id,
                "symbol": fill.symbol,
                "side": fill.side.value,
                "quantity": str(fill.quantity),
                "price": str(fill.price),
                "fee": str(fill.fee),
                "filled_at": fill.filled_at.isoformat(),
            }
        )

        return [entry]

    def create_trade_entry(
        self,
        fill: Fill,
        correlation_id: str,
        order_id: str,
        timestamp: Optional[datetime] = None,
    ) -> LedgerEntry:
        """
        Create a TRADE LedgerEntry from a Fill.

        Args:
            fill: Fill details
            correlation_id: Correlation ID
            order_id: Order ID
            timestamp: Entry timestamp (defaults to fill.filled_at)

        Returns:
            LedgerEntry representing trade
        """
        self._sequence_counter += 1

        ts = timestamp or fill.filled_at

        return LedgerEntry(
            entry_id=f"trade_{correlation_id}_{self._sequence_counter}",
            timestamp=ts,
            sequence=self._sequence_counter,
            event_type="TRADE",
            client_order_id=order_id,
            old_state=None,
            new_state=None,
            details={
                "correlation_id": correlation_id,
                "symbol": fill.symbol,
                "side": fill.side.value,
                "quantity": str(fill.quantity),
                "price": str(fill.price),
                "fee": str(fill.fee),
                "notional": str(fill.quantity * fill.price),
                "filled_at": fill.filled_at.isoformat(),
            }
        )

    def create_fee_entry(
        self,
        fill: Fill,
        correlation_id: str,
        order_id: str,
        timestamp: Optional[datetime] = None,
    ) -> Optional[LedgerEntry]:
        """
        Create a FEE LedgerEntry from a Fill (if fee > 0).

        Args:
            fill: Fill details
            correlation_id: Correlation ID
            order_id: Order ID
            timestamp: Entry timestamp (defaults to fill.filled_at)

        Returns:
            LedgerEntry representing fee, or None if no fee
        """
        if fill.fee == 0:
            return None

        self._sequence_counter += 1

        ts = timestamp or fill.filled_at

        return LedgerEntry(
            entry_id=f"fee_{correlation_id}_{self._sequence_counter}",
            timestamp=ts,
            sequence=self._sequence_counter,
            event_type="FEE",
            client_order_id=order_id,
            old_state=None,
            new_state=None,
            details={
                "correlation_id": correlation_id,
                "symbol": fill.symbol,
                "fee_asset": "EUR",  # Hardcoded for now, should come from config
                "fee_amount": str(fill.fee),
                "basis": f"commission for order {order_id}",
            }
        )

    def reset_sequence(self):
        """Reset sequence counter (for testing)."""
        self._sequence_counter = 0
