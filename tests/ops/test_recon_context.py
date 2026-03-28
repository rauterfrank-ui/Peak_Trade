"""Tests for recon snapshot extraction from SafetyGuard context dict."""

from __future__ import annotations

from src.ops.recon.context import recon_snapshots_from_context
from src.ops.recon.models import BalanceSnapshot, PositionSnapshot


def test_recon_snapshots_from_context_empty() -> None:
    assert recon_snapshots_from_context(None) == (None, None, None, None)
    assert recon_snapshots_from_context({}) == (None, None, None, None)
    assert recon_snapshots_from_context({"recon": "bad"}) == (None, None, None, None)


def test_recon_snapshots_from_context_parsed() -> None:
    ctx = {
        "recon": {
            "expected_balances": {"epoch": 1, "balances": {"USD": 100.0}},
            "observed_balances": {"epoch": 1, "balances": {"USD": 100.0}},
            "expected_positions": {"epoch": 1, "positions": {"BTC": 0.5}},
            "observed_positions": {"epoch": 1, "positions": {"BTC": 0.5}},
        }
    }
    eb, ob, ep, op = recon_snapshots_from_context(ctx)
    assert eb == BalanceSnapshot(epoch=1, balances={"USD": 100.0})
    assert ob == BalanceSnapshot(epoch=1, balances={"USD": 100.0})
    assert ep == PositionSnapshot(epoch=1, positions={"BTC": 0.5})
    assert op == PositionSnapshot(epoch=1, positions={"BTC": 0.5})


def test_recon_snapshots_accepts_dataclass_instances() -> None:
    eb = BalanceSnapshot(epoch=2, balances={"ETH": 1.0})
    ob = BalanceSnapshot(epoch=2, balances={"ETH": 1.0})
    ctx = {"recon": {"expected_balances": eb, "observed_balances": ob}}
    out_eb, out_ob, _, _ = recon_snapshots_from_context(ctx)
    assert out_eb is eb
    assert out_ob is ob
