"""Contract: When live is ARMED, confirm token must be present/valid or eligibility fails."""

from __future__ import annotations

from src.core.environment import (
    EnvironmentConfig,
    LIVE_CONFIRM_TOKEN,
    TradingEnvironment,
)
from src.live.safety import is_live_execution_allowed


def test_confirm_token_is_required_when_armed() -> None:
    """
    Contract: When live is ARMED, a confirm token must be present/valid or eligibility must fail.
    Uses is_live_execution_allowed (EnvironmentConfig) as the canonical gate.
    """
    # ARMED but no/invalid token
    config = EnvironmentConfig(
        environment=TradingEnvironment.LIVE,
        enable_live_trading=True,
        live_mode_armed=True,
        live_dry_run_mode=False,
        require_confirm_token=True,
        confirm_token=None,  # missing
    )
    allowed, reason = is_live_execution_allowed(config)
    assert allowed is False
    assert "confirm" in reason.lower() or "token" in reason.lower()


def test_confirm_token_invalid_when_wrong_value() -> None:
    """Invalid token value must fail."""
    config = EnvironmentConfig(
        environment=TradingEnvironment.LIVE,
        enable_live_trading=True,
        live_mode_armed=True,
        live_dry_run_mode=False,
        require_confirm_token=True,
        confirm_token="WRONG_TOKEN",
    )
    allowed, _ = is_live_execution_allowed(config)
    assert allowed is False


def test_confirm_token_passes_when_valid() -> None:
    """Valid token with LIVE_CONFIRM_TOKEN must pass (other gates permitting)."""
    config = EnvironmentConfig(
        environment=TradingEnvironment.LIVE,
        enable_live_trading=True,
        live_mode_armed=True,
        live_dry_run_mode=False,
        require_confirm_token=True,
        confirm_token=LIVE_CONFIRM_TOKEN,
    )
    allowed, reason = is_live_execution_allowed(config)
    assert allowed is True
    assert "Alle Kriterien" in reason or "erfüllt" in reason
