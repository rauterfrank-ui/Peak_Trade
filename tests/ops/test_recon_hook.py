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


def test_config_from_env_peak_recon_enabled_unset_is_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """PEAK_RECON_ENABLED unset defaults to disabled (current contract)."""
    monkeypatch.delenv("PEAK_RECON_ENABLED", raising=False)
    monkeypatch.setenv("PEAK_RECON_BALANCE_ABS", "0")
    monkeypatch.setenv("PEAK_RECON_POSITION_ABS", "0")
    assert config_from_env().enabled is False


@pytest.mark.parametrize(
    ("peak_recon_enabled", "expect_enabled"),
    [
        ("1", True),
        ("0", False),
        ("true", False),
        ("yes", False),
        ("1 ", False),
    ],
)
def test_config_from_env_peak_recon_enabled_strict_literal_one(
    monkeypatch: pytest.MonkeyPatch, peak_recon_enabled: str, expect_enabled: bool
) -> None:
    """Only PEAK_RECON_ENABLED exactly ``1`` enables recon; no truthy strings, no strip (current contract)."""
    monkeypatch.setenv("PEAK_RECON_ENABLED", peak_recon_enabled)
    monkeypatch.setenv("PEAK_RECON_BALANCE_ABS", "0")
    monkeypatch.setenv("PEAK_RECON_POSITION_ABS", "0")
    assert config_from_env().enabled is expect_enabled
