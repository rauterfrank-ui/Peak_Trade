"""Tests for recon snapshot extraction from SafetyGuard context dict."""

from __future__ import annotations

from src.ops.recon.context import normalize_pipeline_context_for_recon, recon_snapshots_from_context
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


def test_normalize_pipeline_context_for_recon_maps_recon_pipeline() -> None:
    block = {"expected_positions": {"epoch": 1, "positions": {"BTC/EUR": 0.1}}}
    out = normalize_pipeline_context_for_recon({"current_price": 1.0, "recon_pipeline": block})
    assert out["recon"] is block
    assert out["recon_pipeline"] is block


def test_normalize_pipeline_context_for_recon_keeps_explicit_recon() -> None:
    recon = {"expected_positions": {"epoch": 2, "positions": {"ETH/EUR": 1.0}}}
    other = {"expected_positions": {"epoch": 9, "positions": {"X": 0.0}}}
    out = normalize_pipeline_context_for_recon({"recon": recon, "recon_pipeline": other})
    assert out["recon"] is recon


def test_normalize_pipeline_context_for_recon_empty() -> None:
    assert normalize_pipeline_context_for_recon(None) == {}
    assert normalize_pipeline_context_for_recon({}) == {}


def test_recon_snapshots_accepts_dataclass_instances() -> None:
    eb = BalanceSnapshot(epoch=2, balances={"ETH": 1.0})
    ob = BalanceSnapshot(epoch=2, balances={"ETH": 1.0})
    ctx = {"recon": {"expected_balances": eb, "observed_balances": ob}}
    out_eb, out_ob, _, _ = recon_snapshots_from_context(ctx)
    assert out_eb is eb
    assert out_ob is ob
