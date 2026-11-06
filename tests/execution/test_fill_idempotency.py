"""
Tests for Fill Idempotency / Duplicate-Fill Guard (Phase 16A).

Test coverage:
- Fill.get_idempotency_key() generates stable keys
- PositionLedger.apply_fill() skips idempotent duplicates
- PositionLedger.apply_fill() raises on conflicting duplicates
- duplicate_fill_skipped_count telemetry counter
"""

import pytest
from datetime import datetime
from decimal import Decimal

from src.execution.contracts import Fill, OrderSide
from src.execution.position_ledger import PositionLedger
from src.execution.pipeline import DuplicateFillConflictError


# =============================================================================
# Idempotency Key Generation Tests
# =============================================================================


def test_fill_idempotency_key_explicit():
    """Test that explicit idempotency_key is used when provided."""
    fill = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        idempotency_key="explicit_key_123",
    )

    assert fill.get_idempotency_key() == "explicit_key_123"


def test_fill_idempotency_key_derived_stable():
    """Test that derived idempotency_key is stable for same fill."""
    fill1 = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    fill2 = Fill(
        fill_id="fill_002",  # Different fill_id
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    # Derived keys should be identical (fill_id not in canonical tuple)
    assert fill1.get_idempotency_key() == fill2.get_idempotency_key()


def test_fill_idempotency_key_differs_on_payload_change():
    """Test that derived key differs when canonical attributes change."""
    base_fill = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    # Different price
    fill_diff_price = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50001.0"),  # Changed
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    # Different quantity
    fill_diff_qty = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.1"),  # Changed
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    base_key = base_fill.get_idempotency_key()
    assert fill_diff_price.get_idempotency_key() != base_key
    assert fill_diff_qty.get_idempotency_key() != base_key


# =============================================================================
# PositionLedger Idempotency Tests
# =============================================================================


def test_duplicate_fill_skipped_is_idempotent():
    """
    Test that applying the same fill twice (idempotent duplicate) is safe.

    Scenario:
    - Apply fill_1 (BUY 1.0 BTC @ 50000)
    - Apply fill_1 again (exact duplicate)
    - Result: position only updated once, skip counter incremented
    """
    ledger = PositionLedger(initial_cash=Decimal("100000"))

    fill_1 = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    # First apply: should succeed
    position_1 = ledger.apply_fill(fill_1)
    assert position_1.quantity == Decimal("1.0")
    assert ledger.duplicate_fill_skipped_count == 0

    # Second apply (duplicate): should skip
    position_2 = ledger.apply_fill(fill_1)
    assert position_2.quantity == Decimal("1.0")  # No change
    assert ledger.duplicate_fill_skipped_count == 1

    # Third apply: should skip again
    ledger.apply_fill(fill_1)
    assert ledger.duplicate_fill_skipped_count == 2

    # Verify position unchanged
    pos = ledger.get_position("BTC-USD")
    assert pos.quantity == Decimal("1.0")
    assert pos.total_buys == Decimal("1.0")  # Only counted once

    # Verify fills list only has one entry
    assert len(ledger.get_fills()) == 1


def test_duplicate_fill_conflict_raises():
    """
    Test that conflicting duplicate fills raise DuplicateFillConflictError.

    Scenario:
    - Apply fill_1 (BUY 1.0 BTC @ 50000)
    - Apply fill_2 with same idempotency_key but different price
    - Result: DuplicateFillConflictError raised
    """
    ledger = PositionLedger(initial_cash=Decimal("100000"))

    fill_1 = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
        idempotency_key="explicit_key_001",
    )

    fill_2_conflict = Fill(
        fill_id="fill_002",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50001.0"),  # Different price!
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
        idempotency_key="explicit_key_001",  # Same key
    )

    # First apply: should succeed
    ledger.apply_fill(fill_1)

    # Second apply (conflicting): should raise
    with pytest.raises(DuplicateFillConflictError) as exc_info:
        ledger.apply_fill(fill_2_conflict)

    # Verify exception details
    err = exc_info.value
    assert err.idempotency_key == "explicit_key_001"
    assert err.original_fill["fill_id"] == "fill_001"
    assert err.conflicting_fill["fill_id"] == "fill_002"
    assert err.original_fill["price"] == "50000.0"
    assert err.conflicting_fill["price"] == "50001.0"

    # Verify position unchanged
    pos = ledger.get_position("BTC-USD")
    assert pos.quantity == Decimal("1.0")
    assert pos.total_buys == Decimal("1.0")


def test_duplicate_fill_different_symbols_ok():
    """
    Test that fills with same attributes but different symbols are distinct.
    """
    ledger = PositionLedger(initial_cash=Decimal("100000"))

    fill_btc = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    fill_eth = Fill(
        fill_id="fill_002",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="ETH-USD",  # Different symbol
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )

    # Both should apply successfully (different symbols => different keys)
    ledger.apply_fill(fill_btc)
    ledger.apply_fill(fill_eth)

    assert ledger.get_position("BTC-USD").quantity == Decimal("1.0")
    assert ledger.get_position("ETH-USD").quantity == Decimal("1.0")
    assert ledger.duplicate_fill_skipped_count == 0


def test_duplicate_fill_telemetry_counter():
    """
    Test that duplicate_fill_skipped_count increments correctly.
    """
    ledger = PositionLedger(initial_cash=Decimal("100000"))

    fill = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-USD",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),
        price=Decimal("50000.0"),
        fee=Decimal("25.0"),
    )

    # Apply original
    ledger.apply_fill(fill)
    assert ledger.duplicate_fill_skipped_count == 0

    # Apply duplicates
    for i in range(5):
        ledger.apply_fill(fill)

    assert ledger.duplicate_fill_skipped_count == 5
