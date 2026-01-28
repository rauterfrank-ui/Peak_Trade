from __future__ import annotations

from decimal import Decimal

from src.execution.ledger import FillEvent, FifoLedgerEngine


def test_fifo_long_partial_close_realized_pnl_and_remaining_lot():
    eng = FifoLedgerEngine(base_ccy="USD")
    eng.open_cash(amount=Decimal("0"), ccy="USD")

    eng.apply(
        FillEvent(
            ts_utc="2026-01-01T00:00:00Z",
            seq=1,
            instrument="ABC/USD",
            side="BUY",
            qty=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0"),
            fee_ccy="USD",
        )
    )
    eng.apply(
        FillEvent(
            ts_utc="2026-01-01T00:00:01Z",
            seq=2,
            instrument="ABC/USD",
            side="BUY",
            qty=Decimal("1"),
            price=Decimal("110"),
            fee=Decimal("0"),
            fee_ccy="USD",
        )
    )
    eng.apply(
        FillEvent(
            ts_utc="2026-01-01T00:00:02Z",
            seq=3,
            instrument="ABC/USD",
            side="SELL",
            qty=Decimal("1.5"),
            price=Decimal("120"),
            fee=Decimal("0"),
            fee_ccy="USD",
        )
    )

    # FIFO realized: (120-100)*1 + (120-110)*0.5 = 25
    assert eng.account.realized_pnl_by_ccy["USD"] == Decimal("25.00000000")

    pos = eng.account.positions["ABC/USD"]
    assert pos.qty_signed == Decimal("0.50000000")
    assert len(pos.lots) == 1
    assert pos.lots[0].qty_signed == Decimal("0.50000000")
    assert pos.lots[0].price == Decimal("110.00000000")


def test_fifo_flip_to_short():
    eng = FifoLedgerEngine(base_ccy="USD")
    eng.open_cash(amount=Decimal("0"), ccy="USD")

    eng.apply(
        FillEvent(
            ts_utc="2026-01-01T00:00:00Z",
            seq=1,
            instrument="ABC/USD",
            side="BUY",
            qty=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0"),
            fee_ccy="USD",
        )
    )
    eng.apply(
        FillEvent(
            ts_utc="2026-01-01T00:00:01Z",
            seq=2,
            instrument="ABC/USD",
            side="SELL",
            qty=Decimal("2"),
            price=Decimal("90"),
            fee=Decimal("0"),
            fee_ccy="USD",
        )
    )

    # Close 1 long at loss: (90-100)*1 = -10, remaining short 1 @ 90
    assert eng.account.realized_pnl_by_ccy["USD"] == Decimal("-10.00000000")
    pos = eng.account.positions["ABC/USD"]
    assert pos.qty_signed == Decimal("-1.00000000")
    assert len(pos.lots) == 1
    assert pos.lots[0].qty_signed == Decimal("-1.00000000")
    assert pos.lots[0].price == Decimal("90.00000000")


def test_fifo_short_flip_to_long():
    eng = FifoLedgerEngine(base_ccy="USD")
    eng.open_cash(amount=Decimal("0"), ccy="USD")

    eng.apply(
        FillEvent(
            ts_utc="2026-01-01T00:00:00Z",
            seq=1,
            instrument="ABC/USD",
            side="SELL",
            qty=Decimal("1"),
            price=Decimal("100"),
            fee=Decimal("0"),
            fee_ccy="USD",
        )
    )
    eng.apply(
        FillEvent(
            ts_utc="2026-01-01T00:00:01Z",
            seq=2,
            instrument="ABC/USD",
            side="BUY",
            qty=Decimal("2"),
            price=Decimal("90"),
            fee=Decimal("0"),
            fee_ccy="USD",
        )
    )

    # Close 1 short at gain: (100-90)*1 = 10, remaining long 1 @ 90
    assert eng.account.realized_pnl_by_ccy["USD"] == Decimal("10.00000000")
    pos = eng.account.positions["ABC/USD"]
    assert pos.qty_signed == Decimal("1.00000000")
    assert len(pos.lots) == 1
    assert pos.lots[0].qty_signed == Decimal("1.00000000")
    assert pos.lots[0].price == Decimal("90.00000000")
