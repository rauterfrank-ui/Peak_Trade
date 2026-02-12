from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from src.execution.contracts import Fill, OrderSide
from src.execution.ledger import LegacyLedgerEngine as LedgerEngine


def test_pnl_golden_wac_exact_export():
    """
    Golden scenario (WAC):
    - Start cash 10_000
    - Buy 10 @ 100, fee 1
    - Buy 10 @ 110, fee 1
    - Sell 15 @ 120, fee 1
    - Mark price 115

    Expected:
    - qty = 5
    - avg_cost = 105
    - realized_pnl = 225
    - unrealized_pnl = 50
    - cash = 9697
    - export JSON is stable and exact
    """
    eng = LedgerEngine(quote_currency="EUR")
    eng.open_cash(amount=Decimal("10000"))

    t0 = datetime(2025, 1, 1, 0, 0, 0)

    eng.apply(
        Fill(
            fill_id="b1",
            client_order_id="o1",
            exchange_order_id="e1",
            symbol="ABC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("10"),
            price=Decimal("100"),
            fee=Decimal("1"),
            fee_currency="EUR",
            filled_at=t0,
        )
    )
    eng.apply(
        Fill(
            fill_id="b2",
            client_order_id="o2",
            exchange_order_id="e2",
            symbol="ABC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("10"),
            price=Decimal("110"),
            fee=Decimal("1"),
            fee_currency="EUR",
            filled_at=t0,
        )
    )
    eng.apply(
        Fill(
            fill_id="s1",
            client_order_id="o3",
            exchange_order_id="e3",
            symbol="ABC/EUR",
            side=OrderSide.SELL,
            quantity=Decimal("15"),
            price=Decimal("120"),
            fee=Decimal("1"),
            fee_currency="EUR",
            filled_at=t0,
        )
    )

    pos = eng.state.positions["ABC/EUR"]
    assert pos.quantity == Decimal("5.00000000")
    assert pos.avg_cost == Decimal("105.00000000")
    assert pos.realized_pnl == Decimal("225.00000000")

    snap_json = eng.export_snapshot_json(ts_sim=3, mark_prices={"ABC/EUR": Decimal("115")})

    assert snap_json == (
        '{"cash":"9697.00000000","equity":"10272.00000000","meta":{},'
        '"positions":[{"avg_cost":"105.00000000","fees":"3.00000000","quantity":"5.00000000",'
        '"realized_pnl":"225.00000000","symbol":"ABC/EUR"}],'
        '"quote_currency":"EUR","realized_pnl":"225.00000000","ts_sim":3,'
        '"unrealized_pnl":"50.00000000"}'
    )
