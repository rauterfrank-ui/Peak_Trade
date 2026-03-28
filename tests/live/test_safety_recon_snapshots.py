"""SafetyGuard reconciliation uses context[\"recon\"] when PEAK_RECON_ENABLED=1."""

from __future__ import annotations

import pytest

from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.live.safety import SafetyGuard, PaperModeOrderError


@pytest.fixture
def monkeypatch_recon_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_EXEC_GUARDS_ENABLED", "0")
    monkeypatch.setenv("PEAK_RECON_ENABLED", "1")
    monkeypatch.setenv("PEAK_RECON_BALANCE_ABS", "0")
    monkeypatch.setenv("PEAK_RECON_POSITION_ABS", "0")


def test_recon_drift_blocks_before_paper_gate(monkeypatch_recon_enabled: None) -> None:
    guard = SafetyGuard(env_config=EnvironmentConfig(environment=TradingEnvironment.PAPER))
    ctx = {
        "recon": {
            "expected_balances": {"epoch": 1, "balances": {"USD": 100.0}},
            "observed_balances": {"epoch": 1, "balances": {"USD": 90.0}},
        }
    }
    with pytest.raises(RuntimeError, match="reconciliation drift"):
        guard.ensure_may_place_order(context=ctx)


def test_recon_match_then_paper_blocks(monkeypatch_recon_enabled: None) -> None:
    guard = SafetyGuard(env_config=EnvironmentConfig(environment=TradingEnvironment.PAPER))
    ctx = {
        "recon": {
            "expected_balances": {"epoch": 1, "balances": {"USD": 100.0}},
            "observed_balances": {"epoch": 1, "balances": {"USD": 100.0}},
        }
    }
    with pytest.raises(PaperModeOrderError):
        guard.ensure_may_place_order(context=ctx)
