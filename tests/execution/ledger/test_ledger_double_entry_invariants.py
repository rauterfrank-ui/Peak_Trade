from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from src.execution.contracts import Fill, OrderSide
from src.execution.ledger import LegacyLedgerEngine as LedgerEngine


def test_double_entry_and_cash_inventory_fees_invariants_long_roundtrip():
    eng = LedgerEngine(quote_currency="EUR")
    eng.open_cash(amount=Decimal("100000"))

    buy = Fill(
        fill_id="fill_buy_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01000000"),
        price=Decimal("50000.00000000"),
        fee=Decimal("0.50000000"),
        fee_currency="EUR",
        filled_at=datetime(2025, 1, 1, 12, 0, 0),
    )
    eng.apply(buy)

    # After BUY: cash decreases by notional + fee, inventory increases by notional, fees expense increases by fee.
    assert eng.state.cash() == Decimal("99499.50000000")
    assert eng.state.get_account("INVENTORY_COST:BTC/EUR:EUR") == Decimal("500.00000000")
    assert eng.state.get_account("FEES_EXPENSE:EUR") == Decimal("0.50000000")

    # Realized PnL must still be zero (no close yet).
    pos = eng.state.positions["BTC/EUR"]
    assert pos.realized_pnl == Decimal("0E-8") or pos.realized_pnl == Decimal("0.00000000")

    sell = Fill(
        fill_id="fill_sell_001",
        client_order_id="order_002",
        exchange_order_id="exch_002",
        symbol="BTC/EUR",
        side=OrderSide.SELL,
        quantity=Decimal("0.01000000"),
        price=Decimal("51000.00000000"),
        fee=Decimal("0.51000000"),
        fee_currency="EUR",
        filled_at=datetime(2025, 1, 1, 12, 5, 0),
    )
    eng.apply(sell)

    # Realized PnL: (51000 - 50000) * 0.01 = 10.0 (fees are separate).
    assert eng.state.positions["BTC/EUR"].realized_pnl == Decimal("10.00000000")

    # Inventory cost must return to 0 (flat), cash increased by (notional - fee).
    assert eng.state.get_account("INVENTORY_COST:BTC/EUR:EUR") == Decimal(
        "0E-8"
    ) or eng.state.get_account("INVENTORY_COST:BTC/EUR:EUR") == Decimal("0.00000000")
    assert eng.state.cash() == Decimal("100008.99000000")

    # Fees expense accumulated.
    assert eng.state.get_account("FEES_EXPENSE:EUR") == Decimal("1.01000000")

    # Double-entry invariant must hold for every journal entry.
    for je in eng.state.journal:
        assert je.postings_sum() == 0
