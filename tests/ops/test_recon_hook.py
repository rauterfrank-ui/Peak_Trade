"""
Unit tests for Runbook-B recon hook (offline, pure).
"""

from __future__ import annotations

import pytest

from src.ops.recon.models import BalanceSnapshot
from src.ops.recon.recon_hook import ReconConfig, config_from_env, run_recon_if_enabled


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


def test_config_from_env_invalid_balance_abs_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-numeric PEAK_RECON_BALANCE_ABS propagates float() ValueError (current contract)."""
    monkeypatch.setenv("PEAK_RECON_BALANCE_ABS", "not-a-number")
    monkeypatch.delenv("PEAK_RECON_POSITION_ABS", raising=False)
    monkeypatch.delenv("PEAK_RECON_ENABLED", raising=False)
    with pytest.raises(ValueError):
        config_from_env()


def test_config_from_env_invalid_position_abs_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-numeric PEAK_RECON_POSITION_ABS propagates float() ValueError (current contract)."""
    monkeypatch.setenv("PEAK_RECON_BALANCE_ABS", "0")
    monkeypatch.setenv("PEAK_RECON_POSITION_ABS", "not-a-number")
    monkeypatch.delenv("PEAK_RECON_ENABLED", raising=False)
    with pytest.raises(ValueError):
        config_from_env()
