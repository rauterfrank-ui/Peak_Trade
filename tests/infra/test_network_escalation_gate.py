from __future__ import annotations

import pytest

from src.infra.escalation.network_gate import ensure_may_use_network_escalation
from src.core.environment import EnvironmentConfig, LIVE_CONFIRM_TOKEN, TradingEnvironment


def test_allow_network_false_is_ok() -> None:
    ensure_may_use_network_escalation(allow_network=False)


def test_allow_network_true_is_blocked_by_default() -> None:
    with pytest.raises(RuntimeError, match="Network escalation blocked"):
        ensure_may_use_network_escalation(allow_network=True, context="pagerduty")


def test_allow_network_true_is_allowed_when_gates_satisfied() -> None:
    cfg = EnvironmentConfig(
        environment=TradingEnvironment.PAPER,  # we gate network w/o requiring LIVE
        enable_live_trading=True,
        live_mode_armed=True,
        require_confirm_token=True,
        confirm_token=LIVE_CONFIRM_TOKEN,
    )
    ensure_may_use_network_escalation(allow_network=True, context="pagerduty", env_config=cfg)
