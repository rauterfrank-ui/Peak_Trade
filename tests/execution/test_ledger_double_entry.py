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

    assert eng.state.cash() == Decimal("99499.50000000")
    assert eng.state.get_account("INVENTORY_COST:BTC/EUR:EUR") == Decimal("500.00000000")
    assert eng.state.get_account("FEES_EXPENSE:EUR") == Decimal("0.50000000")
    assert eng.state.positions["BTC/EUR"].realized_pnl in {
        Decimal("0"),
        Decimal("0E-8"),
        Decimal("0.00000000"),
    }

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

    assert eng.state.positions["BTC/EUR"].realized_pnl == Decimal("10.00000000")
    assert eng.state.get_account("FEES_EXPENSE:EUR") == Decimal("1.01000000")

    inv = eng.state.get_account("INVENTORY_COST:BTC/EUR:EUR")
    assert inv in {Decimal("0"), Decimal("0E-8"), Decimal("0.00000000")}

    assert eng.state.cash() == Decimal("100008.99000000")

    for je in eng.state.journal:
        assert je.postings_sum() == 0
