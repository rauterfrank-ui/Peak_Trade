from __future__ import annotations

from src.ops.recon.models import BalanceSnapshot, PositionSnapshot
from src.ops.recon.reconcile import reconcile, ReconTolerances


def test_reconcile_balances_ok():
    e = BalanceSnapshot(epoch=1, balances={"USD": 100.0, "BTC": 1.0})
    o = BalanceSnapshot(epoch=2, balances={"USD": 100.0, "BTC": 1.0})
    r = reconcile(e, o, tolerances=ReconTolerances(balance_abs=0.0))
    assert r.ok is True
    assert r.drifts == []


def test_reconcile_balances_drift():
    e = BalanceSnapshot(epoch=1, balances={"USD": 100.0})
    o = BalanceSnapshot(epoch=2, balances={"USD": 90.0})
    r = reconcile(e, o, tolerances=ReconTolerances(balance_abs=5.0))
    assert r.ok is False
    assert len(r.drifts) == 1


def test_reconcile_positions_optional():
    eb = BalanceSnapshot(epoch=1, balances={"USD": 100.0})
    ob = BalanceSnapshot(epoch=2, balances={"USD": 100.0})
    ep = PositionSnapshot(epoch=1, positions={"BTC-USD": 1.0})
    op = PositionSnapshot(epoch=2, positions={"BTC-USD": 1.2})
    r = reconcile(
        eb,
        ob,
        expected_positions=ep,
        observed_positions=op,
        tolerances=ReconTolerances(position_abs=0.1),
    )
    assert r.ok is False
    assert any("position[BTC-USD]" in x for x in r.drifts)
