from __future__ import annotations

import pytest

from src.sim.paper.models import Order
from src.sim.paper.simulator import PaperAccount, PaperTradingSimulator


def test_ledger_has_snapshots_and_reconcile_returns_last() -> None:
    acct = PaperAccount(cash=1000.0)
    sim = PaperTradingSimulator()
    sim.execute(acct, Order(symbol="BTC", side="BUY", qty=1.0), mid_price=10.0)
    sim.execute(acct, Order(symbol="BTC", side="SELL", qty=1.0), mid_price=10.0)

    cash, pos = sim.reconcile(acct)
    assert isinstance(cash, float)
    assert "BTC" in pos
    assert len(sim.ledger) >= 3  # before each execute + final snapshot


def test_reconcile_no_orders_returns_initial_account() -> None:
    acct = PaperAccount(cash=1000.0)
    sim = PaperTradingSimulator()
    cash, pos = sim.reconcile(acct)
    assert cash == 1000.0
    assert pos == {}
    assert len(sim.ledger) == 1
