"""
Unit tests for Runbook-B recon hook (offline, pure).
"""
from __future__ import annotations

from src.ops.recon.models import BalanceSnapshot
from src.ops.recon.recon_hook import ReconConfig, run_recon_if_enabled


def test_recon_hook_disabled_is_ok():
    cfg = ReconConfig(enabled=False, balance_abs=0.0, position_abs=0.0)
    e = BalanceSnapshot(epoch=1, balances={"USD": 100.0})
    o = BalanceSnapshot(epoch=2, balances={"USD": 0.0})
    rep = run_recon_if_enabled(cfg, expected_balances=e, observed_balances=o)
    assert rep.ok is True
    assert rep.drifts == []


def test_recon_hook_enabled_detects_drift():
    cfg = ReconConfig(enabled=True, balance_abs=5.0, position_abs=0.0)
    e = BalanceSnapshot(epoch=1, balances={"USD": 100.0})
    o = BalanceSnapshot(epoch=2, balances={"USD": 90.0})
    rep = run_recon_if_enabled(cfg, expected_balances=e, observed_balances=o)
    assert rep.ok is False
    assert len(rep.drifts) == 1
