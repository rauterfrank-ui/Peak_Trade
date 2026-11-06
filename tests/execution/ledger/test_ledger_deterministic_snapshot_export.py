from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from src.execution.contracts import Fill, OrderSide
from src.execution.ledger import LegacyLedgerEngine as LedgerEngine


def test_snapshot_export_is_bit_identical_for_same_inputs():
    def build_engine() -> LedgerEngine:
        eng = LedgerEngine(quote_currency="EUR")
        eng.open_cash(amount=Decimal("1000"))
        return eng

    buy = Fill(
        fill_id="fill_001",
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

    eng_a = build_engine()
    eng_b = build_engine()

    eng_a.apply(buy)
    eng_b.apply(buy)

    mark_prices = {"BTC/EUR": Decimal("51000.00000000")}
    out_a = eng_a.export_snapshot_json(ts_sim=1, mark_prices=mark_prices)
    out_b = eng_b.export_snapshot_json(ts_sim=1, mark_prices=mark_prices)

    assert out_a == out_b
