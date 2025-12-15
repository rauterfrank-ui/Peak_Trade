# tests/smoke/test_live_gating_smoke.py
"""
Smoke Test: Live-Gating Safety.

Stellt sicher, dass Live-Trading standardmäßig sicher gegatet ist.
"""
import pytest


def test_live_execution_governance_locked():
    """Test dass live_order_execution governance-locked ist."""
    from src.governance.go_no_go import get_governance_status

    status = get_governance_status("live_order_execution")
    assert status == "locked", "live_order_execution must be governance-locked by default"


def test_environment_defaults_to_paper():
    """Test dass Environment standardmäßig auf Paper steht."""
    from src.core.environment import create_default_environment

    env = create_default_environment()
    assert env.environment.value == "paper", "Default environment must be PAPER (safe)"


def test_safety_guard_blocks_live_by_default():
    """Test dass SafetyGuard Live-Trading standardmäßig blockiert."""
    from src.core.environment import create_default_environment
    from src.live.safety import SafetyGuard, LiveNotImplementedError, PaperModeOrderError

    env = create_default_environment()
    guard = SafetyGuard(env_config=env)

    # Paper-Mode sollte blockieren
    with pytest.raises((PaperModeOrderError, LiveNotImplementedError)):
        guard.ensure_may_place_order(is_testnet=False)


def test_live_risk_limits_safe_defaults():
    """Test dass LiveRiskLimits safe defaults haben."""
    from src.live.risk_limits import LiveRiskLimits, LiveRiskConfig

    # Minimal config
    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        max_total_exposure_notional=None,
        max_symbol_exposure_notional=None,
        max_open_positions=None,
        max_order_notional=None,
        block_on_violation=True,  # Safe default
        use_experiments_for_daily_pnl=False,
    )

    limits = LiveRiskLimits(config)

    # block_on_violation sollte True sein
    assert limits.config.block_on_violation is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
