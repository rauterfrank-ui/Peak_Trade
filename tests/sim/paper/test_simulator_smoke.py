from __future__ import annotations

import pytest

from src.sim.paper.models import Order
from src.sim.paper.simulator import FeeModel, PaperAccount, PaperTradingSimulator
from src.sim.paper.slippage import SlippageModel


def test_buy_sell_roundtrip_deterministic() -> None:
    acct = PaperAccount(cash=1000.0)
    sim = PaperTradingSimulator(fee_model=FeeModel(rate=0.001), slippage=SlippageModel(bps=10.0))

    f1 = sim.execute(acct, Order(symbol="BTC", side="BUY", qty=1.0), mid_price=100.0)
    assert f1.price > 100.0
    assert acct.positions["BTC"] == 1.0
    assert acct.cash < 1000.0

    f2 = sim.execute(acct, Order(symbol="BTC", side="SELL", qty=1.0), mid_price=100.0)
    assert f2.price < 100.0
    assert acct.positions["BTC"] == 0.0

    cash, pos = sim.reconcile(acct)
    assert "BTC" in pos
    assert cash == acct.cash


def test_insufficient_cash() -> None:
    acct = PaperAccount(cash=1.0)
    sim = PaperTradingSimulator()
    with pytest.raises(RuntimeError, match="INSUFFICIENT_CASH"):
        sim.execute(acct, Order(symbol="BTC", side="BUY", qty=1.0), mid_price=100.0)


def test_insufficient_position() -> None:
    acct = PaperAccount(cash=1000.0)
    sim = PaperTradingSimulator()
    with pytest.raises(RuntimeError, match="INSUFFICIENT_POSITION"):
        sim.execute(acct, Order(symbol="BTC", side="SELL", qty=1.0), mid_price=100.0)
