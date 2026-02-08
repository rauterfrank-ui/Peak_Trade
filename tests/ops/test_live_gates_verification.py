# tests/ops/test_live_gates_verification.py
"""
P0: Deterministic verification tests for live gates and kill switch.

Safety-first: no network, no external tools. Asserts that:
- Live execution is disabled by default (no accidental enable).
- Enabling requires BOTH enabled+armed plus confirm token (gate contract).
- Dry-run mode does NOT touch execution layer (live_dry_run_mode blocks real orders).
- Kill switch toggles to safe state and blocks execution.
- Invariants are enforced via config + code paths (real imports, no mocks where possible).
"""

from __future__ import annotations

import time

import pytest

from src.core.environment import (
    TradingEnvironment,
    EnvironmentConfig,
    LIVE_CONFIRM_TOKEN,
    create_default_environment,
)
from src.live.safety import is_live_execution_allowed
from src.ops.gates.armed_gate import ArmedGate, ArmedState
from src.ops.gates.risk_gate import (
    RiskLimits,
    RiskContext,
    RiskDecision,
    RiskDenyReason,
    evaluate_risk,
)
from src.ops.wiring.execution_guards import (
    GuardConfig,
    GuardInputs,
    apply_execution_guards,
)


# -----------------------------------------------------------------------------
# 1) Live execution disabled by default
# -----------------------------------------------------------------------------


class TestLiveExecutionDisabledByDefault:
    """Live execution is disabled by default; no accidental enable."""

    def test_default_environment_blocks_live(self) -> None:
        """create_default_environment() yields config that does not allow real orders."""
        config = create_default_environment()
        assert config.enable_live_trading is False
        assert config.live_mode_armed is False
        assert config.live_dry_run_mode is True
        assert config.allows_real_orders is False

    def test_environment_config_defaults_block_live(self) -> None:
        """EnvironmentConfig() defaults block live (enable_live_trading=False, etc.)."""
        config = EnvironmentConfig()
        assert config.environment == TradingEnvironment.PAPER
        assert config.enable_live_trading is False
        assert config.live_mode_armed is False
        assert config.live_dry_run_mode is True
        assert config.allows_real_orders is False

    def test_is_live_execution_allowed_default_like_config_returns_false(self) -> None:
        """is_live_execution_allowed() returns (False, reason) for default-like LIVE config."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
            live_mode_armed=False,
            live_dry_run_mode=True,
        )
        allowed, reason = is_live_execution_allowed(config)
        assert allowed is False
        assert "enable_live_trading" in reason or "Gate 1" in reason


# -----------------------------------------------------------------------------
# 2) Enabling requires BOTH enabled+armed plus confirm token
# -----------------------------------------------------------------------------


class TestEnablingRequiresEnabledArmedAndConfirmToken:
    """Enabling live requires enabled + armed + confirm token (gate contract)."""

    def test_is_live_execution_allowed_requires_gate1(self) -> None:
        """Gate 1: enable_live_trading must be True."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
            live_mode_armed=True,
            live_dry_run_mode=False,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        allowed, reason = is_live_execution_allowed(config)
        assert allowed is False
        assert "enable_live_trading" in reason or "Gate 1" in reason

    def test_is_live_execution_allowed_requires_gate2_armed(self) -> None:
        """Gate 2: live_mode_armed must be True."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=False,
            live_dry_run_mode=False,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        allowed, reason = is_live_execution_allowed(config)
        assert allowed is False
        assert "live_mode_armed" in reason or "Gate 2" in reason

    def test_is_live_execution_allowed_requires_confirm_token(self) -> None:
        """When require_confirm_token=True, confirm_token must match LIVE_CONFIRM_TOKEN."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=False,
            require_confirm_token=True,
            confirm_token="WRONG_TOKEN",
        )
        allowed, reason = is_live_execution_allowed(config)
        assert allowed is False
        assert "confirm_token" in reason

    def test_armed_gate_require_armed_blocks_when_not_armed(self) -> None:
        """ArmedGate.require_armed() raises when state is not both enabled and armed."""
        state = ArmedState(
            enabled=True,
            armed=False,
            armed_since_epoch=None,
            token_issued_epoch=None,
        )
        with pytest.raises(RuntimeError, match="gate not armed"):
            ArmedGate.require_armed(state)

    def test_armed_gate_require_armed_blocks_when_disabled(self) -> None:
        """ArmedGate.require_armed() raises when enabled=False even if armed=True (invalid combo)."""
        # In practice armed should not be True when enabled=False; contract: both required
        state = ArmedState(
            enabled=False,
            armed=True,
            armed_since_epoch=int(time.time()),
            token_issued_epoch=None,
        )
        with pytest.raises(RuntimeError, match="gate not armed"):
            ArmedGate.require_armed(state)

    def test_guard_config_default_enabled_off(self) -> None:
        """GuardConfig default: enabled=False (global toggle OFF)."""
        cfg = GuardConfig()
        assert cfg.enabled is False

    def test_apply_execution_guards_disabled_allows_no_op(self) -> None:
        """When GuardConfig.enabled=False, apply_execution_guards returns allow=True (no-op)."""
        gate = ArmedGate(secret=b"test-secret", token_ttl_seconds=120)
        cfg = GuardConfig(enabled=False, armed_required=True, risk_enabled=True)
        now = int(time.time())
        inputs = GuardInputs(
            armed_state=ArmedState(
                enabled=False,
                armed=False,
                armed_since_epoch=None,
                token_issued_epoch=None,
            ),
            armed_token=None,
            limits=RiskLimits(enabled=True, kill_switch=False),
            ctx=RiskContext(
                now_epoch=now,
                market_data_age_seconds=0,
                session_pnl_usd=0.0,
                current_position=0.0,
                order_size=1.0,
                order_notional_usd=100.0,
            ),
        )
        result = apply_execution_guards(cfg, gate=gate, inputs=inputs)
        assert result.allow is True
        assert result.risk is None


# -----------------------------------------------------------------------------
# 3) Dry-run mode does NOT touch execution layer
# -----------------------------------------------------------------------------


class TestDryRunModeDoesNotTouchExecution:
    """Dry-run mode does not allow real orders (live_dry_run_mode blocks)."""

    def test_live_dry_run_mode_blocks_real_orders(self) -> None:
        """live_dry_run_mode=True blocks real orders (Phase 71 technical gate)."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=True,  # blocks
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        assert config.allows_real_orders is False

    def test_is_live_execution_allowed_returns_false_when_dry_run(self) -> None:
        """is_live_execution_allowed() returns False when live_dry_run_mode=True."""
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=True,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        allowed, reason = is_live_execution_allowed(config)
        assert allowed is False
        assert "live_dry_run_mode" in reason or "Phase 71" in reason


# -----------------------------------------------------------------------------
# 4) Kill switch blocks execution
# -----------------------------------------------------------------------------


class TestKillSwitchBlocksExecution:
    """Kill switch toggles to safe state and blocks execution."""

    def test_risk_limits_kill_switch_denies(self) -> None:
        """evaluate_risk() with kill_switch=True returns allow=False, reason KILL_SWITCH."""
        limits = RiskLimits(enabled=True, kill_switch=True)
        ctx = RiskContext(
            now_epoch=int(time.time()),
            market_data_age_seconds=0,
            session_pnl_usd=0.0,
            current_position=0.0,
            order_size=1.0,
            order_notional_usd=100.0,
        )
        decision = evaluate_risk(limits, ctx)
        assert decision.allow is False
        assert decision.reason == RiskDenyReason.KILL_SWITCH
        assert decision.details.get("kill_switch") == "true"

    def test_risk_limits_disabled_denies(self) -> None:
        """evaluate_risk() with enabled=False returns allow=False (disabled gate)."""
        limits = RiskLimits(enabled=False, kill_switch=False)
        ctx = RiskContext(
            now_epoch=int(time.time()),
            market_data_age_seconds=0,
            session_pnl_usd=0.0,
            current_position=0.0,
            order_size=1.0,
            order_notional_usd=100.0,
        )
        decision = evaluate_risk(limits, ctx)
        assert decision.allow is False
        assert decision.reason == RiskDenyReason.DISABLED

    def test_risk_limits_no_kill_switch_allows_when_limits_ok(self) -> None:
        """evaluate_risk() with kill_switch=False and sane limits returns allow=True."""
        limits = RiskLimits(
            enabled=True,
            kill_switch=False,
            max_notional_usd=1000.0,
            max_order_size=10.0,
        )
        ctx = RiskContext(
            now_epoch=int(time.time()),
            market_data_age_seconds=0,
            session_pnl_usd=0.0,
            current_position=0.0,
            order_size=1.0,
            order_notional_usd=100.0,
        )
        decision = evaluate_risk(limits, ctx)
        assert decision.allow is True
        assert decision.reason is None


# -----------------------------------------------------------------------------
# 5) Config + code path invariants (integration-style, still deterministic)
# -----------------------------------------------------------------------------


class TestLiveGatesInvariants:
    """Invariants enforced via config + code paths."""

    def test_full_live_criteria_only_when_all_met(self) -> None:
        """is_live_execution_allowed() returns True only when all criteria met (design: Phase 71 blocks via live_dry_run_mode)."""
        # The only way to get True in code is live_dry_run_mode=False; in Phase 71 that is not used.
        config = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=False,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        allowed, reason = is_live_execution_allowed(config)
        # In Phase 71 design, we still expect reason to mention "theoretisch" or "live_dry_run_mode"
        assert allowed is True
        assert "Kriterien" in reason or "theoretisch" in reason

    def test_guard_with_kill_switch_blocks(self) -> None:
        """apply_execution_guards with risk_enabled=True and kill_switch=True raises."""
        gate = ArmedGate(secret=b"test-secret", token_ttl_seconds=120)
        token = gate.issue_token(int(time.time()))
        cfg = GuardConfig(enabled=True, armed_required=True, risk_enabled=True)
        now = int(time.time())
        inputs = GuardInputs(
            armed_state=ArmedState(
                enabled=True,
                armed=True,
                armed_since_epoch=now,
                token_issued_epoch=None,
            ),
            armed_token=token,
            limits=RiskLimits(enabled=True, kill_switch=True),  # kill switch on
            ctx=RiskContext(
                now_epoch=now,
                market_data_age_seconds=0,
                session_pnl_usd=0.0,
                current_position=0.0,
                order_size=1.0,
                order_notional_usd=100.0,
            ),
        )
        with pytest.raises(RuntimeError, match="risk_gate deny|kill_switch|Execution blocked"):
            apply_execution_guards(cfg, gate=gate, inputs=inputs)
