"""
Test: ExecutionEvent (FILL) → LedgerEntry Mapping

Verifies that:
- FILL events create TRADE LedgerEntry
- LedgerEntry contains correct details (symbol, side, quantity, price, fee)
- Mapping is deterministic
"""

from decimal import Decimal
from datetime import datetime

from src.execution.ledger_mapper import EventToLedgerMapper
from src.execution.orchestrator import ExecutionEvent
from src.execution.contracts import Fill, OrderSide


def test_fill_event_maps_to_trade_ledger_entry():
    """FILL event should create TRADE LedgerEntry with correct details"""

    # Create mapper
    mapper = EventToLedgerMapper()

    # Create Fill
    fill = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.1"),
        price=Decimal("50000.00"),
        fee=Decimal("5.00"),
    )

    # Create ExecutionEvent (FILL)
    execution_event = ExecutionEvent(
        event_type="FILL",
        order_id="order_001",
        exchange_order_id="exch_001",
        fill=fill,
    )

    # Map to LedgerEntry
    ledger_entries = mapper.map_event_to_ledger_entries(
        execution_event=execution_event,
        correlation_id="corr_123",
    )

    # Should create 1 entry
    assert len(ledger_entries) == 1

    entry = ledger_entries[0]

    # Verify entry type
    assert entry.event_type == "FILL_RECEIVED"
    assert entry.client_order_id == "order_001"

    # Verify details
    assert entry.details["symbol"] == "BTC/EUR"
    assert entry.details["side"] == "BUY"
    assert entry.details["quantity"] == "0.1"
    assert entry.details["price"] == "50000.00"
    assert entry.details["fee"] == "5.00"
    assert entry.details["correlation_id"] == "corr_123"
    assert entry.details["exchange_order_id"] == "exch_001"


def test_fill_event_deterministic():
    """Same FILL event should produce identical LedgerEntry (deterministic)"""

    # Create mapper
    mapper = EventToLedgerMapper()

    # Create Fill
    fill = Fill(
        fill_id="fill_002",
        client_order_id="order_002",
        exchange_order_id="exch_002",
        symbol="ETH/EUR",
        side=OrderSide.SELL,
        quantity=Decimal("1.0"),
        price=Decimal("3000.00"),
        fee=Decimal("3.00"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),  # Fixed timestamp
    )

    # Create ExecutionEvent
    execution_event = ExecutionEvent(
        event_type="FILL",
        order_id="order_002",
        fill=fill,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),  # Fixed timestamp
    )

    # Map twice
    entries1 = mapper.map_event_to_ledger_entries(
        execution_event=execution_event,
        correlation_id="corr_456",
    )

    # Reset mapper sequence (simulate fresh mapper)
    mapper.reset_sequence()

    entries2 = mapper.map_event_to_ledger_entries(
        execution_event=execution_event,
        correlation_id="corr_456",
    )

    # Should produce identical entries (except timestamp if default_factory used)
    assert len(entries1) == len(entries2) == 1

    e1 = entries1[0]
    e2 = entries2[0]

    # Details should be identical
    assert e1.details == e2.details
    assert e1.event_type == e2.event_type
    assert e1.client_order_id == e2.client_order_id


def test_trade_entry_creation():
    """create_trade_entry should create TRADE LedgerEntry"""

    mapper = EventToLedgerMapper()

    fill = Fill(
        fill_id="fill_003",
        client_order_id="order_003",
        exchange_order_id="exch_003",
        symbol="SOL/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("10.0"),
        price=Decimal("100.00"),
        fee=Decimal("1.00"),
        filled_at=datetime(2025, 1, 1, 13, 0, 0),
    )

    entry = mapper.create_trade_entry(
        fill=fill,
        correlation_id="corr_789",
        order_id="order_003",
    )

    # Verify TRADE entry
    assert entry.event_type == "TRADE"
    assert entry.client_order_id == "order_003"
    assert entry.details["symbol"] == "SOL/EUR"
    assert entry.details["side"] == "BUY"
    assert entry.details["quantity"] == "10.0"
    assert entry.details["price"] == "100.00"
    assert entry.details["fee"] == "1.00"
    assert Decimal(entry.details["notional"]) == Decimal("1000.00")  # 10.0 * 100.00


def test_fee_entry_creation():
    """create_fee_entry should create FEE LedgerEntry if fee > 0"""

    mapper = EventToLedgerMapper()

    fill = Fill(
        fill_id="fill_004",
        client_order_id="order_004",
        exchange_order_id="exch_004",
        symbol="BTC/EUR",
        side=OrderSide.SELL,
        quantity=Decimal("0.5"),
        price=Decimal("50000.00"),
        fee=Decimal("12.50"),
        filled_at=datetime(2025, 1, 1, 14, 0, 0),
    )

    entry = mapper.create_fee_entry(
        fill=fill,
        correlation_id="corr_abc",
        order_id="order_004",
    )

    # Should create FEE entry
    assert entry is not None
    assert entry.event_type == "FEE"
    assert entry.client_order_id == "order_004"
    assert entry.details["fee_asset"] == "EUR"
    assert entry.details["fee_amount"] == "12.50"
    assert entry.details["basis"] == "commission for order order_004"


def test_fee_entry_none_if_no_fee():
    """create_fee_entry should return None if fee = 0"""

    mapper = EventToLedgerMapper()

    fill = Fill(
        fill_id="fill_005",
        client_order_id="order_005",
        exchange_order_id="exch_005",
        symbol="ETH/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("3000.00"),
        fee=Decimal("0.00"),  # No fee
        filled_at=datetime(2025, 1, 1, 15, 0, 0),
    )

    entry = mapper.create_fee_entry(
        fill=fill,
        correlation_id="corr_def",
        order_id="order_005",
    )

    # Should return None (no fee)
    assert entry is None
