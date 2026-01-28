from __future__ import annotations

from decimal import Decimal

from src.execution.ledger import FillEvent, FifoLedgerEngine


def test_invariants_lots_sum_to_position_qty_realized_only_on_close_fees_and_cash_consistent():
    eng = FifoLedgerEngine(base_ccy="USD")
    eng.open_cash(amount=Decimal("1000"), ccy="USD")

    def cash() -> Decimal:
        return eng.account.cash_by_ccy.get("USD", Decimal("0"))

    # Open long: no realized pnl.
    e1 = FillEvent(
        ts_utc="2026-01-01T00:00:00Z",
        seq=1,
        instrument="ABC/USD",
        side="BUY",
        qty=Decimal("2"),
        price=Decimal("100"),
        fee=Decimal("1.00"),
        fee_ccy="USD",
    )
    eng.apply(e1)
    pos = eng.account.positions["ABC/USD"]
    assert sum((l.qty_signed for l in pos.lots), Decimal("0")) == pos.qty_signed
    assert eng.account.realized_pnl_by_ccy.get("USD", Decimal("0")) in {
        Decimal("0"),
        Decimal("0E-8"),
        Decimal("0.00000000"),
    }
    assert eng.account.fees_by_ccy["USD"] == Decimal("1.00000000")
    # Cash decreases by notional + fee
    assert cash() == Decimal("799.00000000")

    # Add to long: still no realized pnl.
    e2 = FillEvent(
        ts_utc="2026-01-01T00:00:01Z",
        seq=2,
        instrument="ABC/USD",
        side="BUY",
        qty=Decimal("1"),
        price=Decimal("110"),
        fee=Decimal("1.00"),
        fee_ccy="USD",
    )
    eng.apply(e2)
    pos = eng.account.positions["ABC/USD"]
    assert sum((l.qty_signed for l in pos.lots), Decimal("0")) == pos.qty_signed
    assert eng.account.realized_pnl_by_ccy.get("USD", Decimal("0")) in {
        Decimal("0"),
        Decimal("0E-8"),
        Decimal("0.00000000"),
    }
    assert eng.account.fees_by_ccy["USD"] == Decimal("2.00000000")
    assert cash() == Decimal("688.00000000")  # 799 - 110 - 1

    # Partial close (FIFO): realized pnl changes.
    e3 = FillEvent(
        ts_utc="2026-01-01T00:00:02Z",
        seq=3,
        instrument="ABC/USD",
        side="SELL",
        qty=Decimal("2.5"),
        price=Decimal("120"),
        fee=Decimal("1.00"),
        fee_ccy="USD",
    )
    eng.apply(e3)
    pos = eng.account.positions["ABC/USD"]
    assert sum((l.qty_signed for l in pos.lots), Decimal("0")) == pos.qty_signed
    assert eng.account.fees_by_ccy["USD"] == Decimal("3.00000000")

    # Cash increases by notional - fee
    assert cash() == Decimal("987.00000000")  # 688 + 300 - 1

    # Realized PnL (FIFO):
    # Close 2.0 @100 => (120-100)*2 = 40
    # Close 0.5 @110 => (120-110)*0.5 = 5
    assert eng.account.realized_pnl_by_ccy["USD"] == Decimal("45.00000000")
