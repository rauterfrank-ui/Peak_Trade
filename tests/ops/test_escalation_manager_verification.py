# tests/ops/test_escalation_manager_verification.py
"""
P0: Deterministic verification tests for escalation manager and safety-drill contracts.

Safety-first: no network, no external tools. Asserts that:
- Escalation manager does not escalate when disabled (enabled=False).
- Escalation manager does not escalate when current_environment not in enabled_environments.
- Escalation manager does not escalate when event severity not in critical_severities.
- build_escalation_manager_from_config respects enabled flag.
- Network escalation gate blocks when live gates not satisfied (contract alignment).
- Default live drill scenarios exist and have expected structure (A–F).
"""

from __future__ import annotations

import pytest

from src.infra.escalation import (
    EscalationManager,
    EscalationEvent,
    EscalationTarget,
    NullEscalationProvider,
    build_escalation_manager_from_config,
)
from src.infra.escalation.network_gate import ensure_may_use_network_escalation
from src.core.environment import (
    EnvironmentConfig,
    LIVE_CONFIRM_TOKEN,
    TradingEnvironment,
)
from src.live.drills import get_default_live_drill_scenarios


# -----------------------------------------------------------------------------
# 1) Escalation manager does not escalate when disabled
# -----------------------------------------------------------------------------


class TestEscalationManagerDisabledNoEscalation:
    """Escalation manager does not escalate when enabled=False."""

    def test_enabled_false_returns_false(self) -> None:
        """maybe_escalate() returns False when enabled=False (Gate 1)."""
        provider = NullEscalationProvider(log_would_escalate=False)
        manager = EscalationManager(
            provider=provider,
            targets=[EscalationTarget(name="On-Call", enabled=True)],
            enabled=False,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )
        event = EscalationEvent(
            alert_id="test-1",
            severity="CRITICAL",
            alert_type="RISK",
            summary="Test",
        )
        result = manager.maybe_escalate(event)
        assert result is False

    def test_environment_not_in_enabled_environments_returns_false(self) -> None:
        """maybe_escalate() returns False when current_environment not in enabled_environments (Gate 2)."""
        provider = NullEscalationProvider(log_would_escalate=False)
        manager = EscalationManager(
            provider=provider,
            targets=[EscalationTarget(name="On-Call", enabled=True)],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="paper",
        )
        event = EscalationEvent(
            alert_id="test-1",
            severity="CRITICAL",
            alert_type="RISK",
            summary="Test",
        )
        result = manager.maybe_escalate(event)
        assert result is False

    def test_severity_not_critical_returns_false(self) -> None:
        """maybe_escalate() returns False when event.severity not in critical_severities (Gate 3)."""
        provider = NullEscalationProvider(log_would_escalate=False)
        manager = EscalationManager(
            provider=provider,
            targets=[EscalationTarget(name="On-Call", enabled=True)],
            enabled=True,
            enabled_environments={"live"},
            critical_severities={"CRITICAL"},
            current_environment="live",
        )
        event = EscalationEvent(
            alert_id="test-1",
            severity="WARN",
            alert_type="RISK",
            summary="Test",
        )
        result = manager.maybe_escalate(event)
        assert result is False


# -----------------------------------------------------------------------------
# 2) build_escalation_manager_from_config respects enabled
# -----------------------------------------------------------------------------


class TestBuildEscalationManagerFromConfig:
    """build_escalation_manager_from_config yields manager with correct gates."""

    def test_config_enabled_false_yields_disabled_manager(self) -> None:
        """Config with escalation.enabled=false yields manager with enabled=False."""
        config = {
            "escalation": {
                "enabled": False,
                "enabled_environments": ["live"],
                "provider": "null",
                "critical_severities": ["CRITICAL"],
            },
        }
        manager = build_escalation_manager_from_config(config, environment="live")
        assert manager.enabled is False

    def test_config_enabled_true_yields_enabled_manager(self) -> None:
        """Config with escalation.enabled=true yields manager with enabled=True."""
        config = {
            "escalation": {
                "enabled": True,
                "enabled_environments": ["live"],
                "provider": "null",
                "critical_severities": ["CRITICAL"],
            },
        }
        manager = build_escalation_manager_from_config(config, environment="live")
        assert manager.enabled is True


# -----------------------------------------------------------------------------
# 3) Network escalation gate contract (alignment with live gates)
# -----------------------------------------------------------------------------


class TestNetworkEscalationGateContract:
    """Network escalation gate blocks when live gates not satisfied."""

    def test_allow_network_false_passes(self) -> None:
        """allow_network=False does not raise (no outbound call)."""
        ensure_may_use_network_escalation(allow_network=False, context="pagerduty")

    def test_allow_network_true_default_config_raises(self) -> None:
        """allow_network=True with default env config raises (gates not satisfied)."""
        with pytest.raises(RuntimeError, match="Network escalation blocked"):
            ensure_may_use_network_escalation(allow_network=True, context="pagerduty")

    def test_allow_network_true_with_gates_satisfied_passes(self) -> None:
        """allow_network=True with enable_live_trading, live_mode_armed, confirm_token passes."""
        cfg = EnvironmentConfig(
            environment=TradingEnvironment.PAPER,
            enable_live_trading=True,
            live_mode_armed=True,
            require_confirm_token=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        ensure_may_use_network_escalation(
            allow_network=True, context="pagerduty", env_config=cfg
        )


# -----------------------------------------------------------------------------
# 4) Default live drill scenarios (safety drills contract)
# -----------------------------------------------------------------------------


class TestDefaultLiveDrillScenarios:
    """Default live drill scenarios exist and have expected structure."""

    def test_returns_non_empty_list(self) -> None:
        """get_default_live_drill_scenarios() returns non-empty list."""
        scenarios = get_default_live_drill_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 4  # At least A, B, C, D

    def test_scenarios_have_expected_names(self) -> None:
        """Scenarios include A (Voll gebremst), B (Gate 2), C (Dry-Run), D (Confirm-Token)."""
        scenarios = get_default_live_drill_scenarios()
        names = [s.name for s in scenarios]
        assert any("A" in n and "Voll gebremst" in n for n in names)
        assert any("B" in n and "Gate 2" in n for n in names)
        assert any("C" in n and "Dry-Run" in n for n in names)
        assert any("D" in n and "Confirm-Token" in n for n in names)

    def test_each_scenario_has_required_attributes(self) -> None:
        """Each scenario has name, env_overrides, expected_is_live_execution_allowed, expected_reasons."""
        scenarios = get_default_live_drill_scenarios()
        for s in scenarios:
            assert hasattr(s, "name") and s.name
            assert hasattr(s, "env_overrides") and isinstance(s.env_overrides, dict)
            assert hasattr(s, "expected_is_live_execution_allowed")
            assert hasattr(s, "expected_reasons") and isinstance(s.expected_reasons, list)
