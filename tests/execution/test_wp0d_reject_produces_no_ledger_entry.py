"""
Test: ExecutionEvent (REJECT/CANCEL_ACK/ACK) → No LedgerEntry

Verifies that:
- REJECT events do not create LedgerEntry (audit log only)
- CANCEL_ACK events do not create LedgerEntry (order state only)
- ACK events do not create LedgerEntry (order state only)
- Only FILL events create LedgerEntry (position impact)
"""

from decimal import Decimal
from datetime import datetime

from src.execution.ledger_mapper import EventToLedgerMapper
from src.execution.orchestrator import ExecutionEvent
from src.execution.contracts import Fill, OrderSide


def test_reject_event_no_ledger_entry():
    """REJECT event should NOT create LedgerEntry"""

    # Create mapper
    mapper = EventToLedgerMapper()

    # Create ExecutionEvent (REJECT)
    execution_event = ExecutionEvent(
        event_type="REJECT",
        order_id="order_reject_001",
        reject_reason="Insufficient margin",
    )

    # Map to LedgerEntry
    ledger_entries = mapper.map_event_to_ledger_entries(
        execution_event=execution_event,
        correlation_id="corr_reject_123",
    )

    # Should create NO entries (REJECT has no position impact)
    assert len(ledger_entries) == 0


def test_cancel_ack_event_no_ledger_entry():
    """CANCEL_ACK event should NOT create LedgerEntry"""

    mapper = EventToLedgerMapper()

    # Create ExecutionEvent (CANCEL_ACK)
    execution_event = ExecutionEvent(
        event_type="CANCEL_ACK",
        order_id="order_cancel_001",
        exchange_order_id="exch_cancel_001",
    )

    # Map to LedgerEntry
    ledger_entries = mapper.map_event_to_ledger_entries(
        execution_event=execution_event,
        correlation_id="corr_cancel_456",
    )

    # Should create NO entries (CANCEL_ACK has no position impact)
    assert len(ledger_entries) == 0


def test_ack_event_no_ledger_entry():
    """ACK event should NOT create LedgerEntry"""

    mapper = EventToLedgerMapper()

    # Create ExecutionEvent (ACK)
    execution_event = ExecutionEvent(
        event_type="ACK",
        order_id="order_ack_001",
        exchange_order_id="exch_ack_001",
    )

    # Map to LedgerEntry
    ledger_entries = mapper.map_event_to_ledger_entries(
        execution_event=execution_event,
        correlation_id="corr_ack_789",
    )

    # Should create NO entries (ACK has no position impact)
    assert len(ledger_entries) == 0


def test_only_fill_creates_ledger_entry():
    """Only FILL events should create LedgerEntry, all others should not"""

    mapper = EventToLedgerMapper()

    # Test all event types
    event_types = ["ACK", "REJECT", "CANCEL_ACK"]

    for event_type in event_types:
        execution_event = ExecutionEvent(
            event_type=event_type,
            order_id=f"order_{event_type}_001",
            exchange_order_id=f"exch_{event_type}_001",
            reject_reason="Test" if event_type == "REJECT" else None,
        )

        ledger_entries = mapper.map_event_to_ledger_entries(
            execution_event=execution_event,
            correlation_id=f"corr_{event_type}",
        )

        # Non-FILL events should NOT create entries
        assert len(ledger_entries) == 0, f"{event_type} should not create LedgerEntry"

    # FILL event should create entry
    fill = Fill(
        fill_id="fill_fill_001",
        client_order_id="order_fill_001",
        exchange_order_id="exch_fill_001",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.1"),
        price=Decimal("50000.00"),
        fee=Decimal("5.00"),
    )

    fill_event = ExecutionEvent(
        event_type="FILL",
        order_id="order_fill_001",
        fill=fill,
    )

    fill_entries = mapper.map_event_to_ledger_entries(
        execution_event=fill_event,
        correlation_id="corr_fill",
    )

    # FILL should create entry
    assert len(fill_entries) == 1


def test_fill_without_fill_details_no_entry():
    """FILL event without fill details should NOT create LedgerEntry"""

    mapper = EventToLedgerMapper()

    # Create FILL event but no fill details (malformed)
    execution_event = ExecutionEvent(
        event_type="FILL",
        order_id="order_malformed_001",
        fill=None,  # No fill details
    )

    ledger_entries = mapper.map_event_to_ledger_entries(
        execution_event=execution_event,
        correlation_id="corr_malformed",
    )

    # Should NOT create entries (fill is None)
    assert len(ledger_entries) == 0
