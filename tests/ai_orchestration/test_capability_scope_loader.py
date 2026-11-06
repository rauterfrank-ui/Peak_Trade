"""
Tests for Capability Scope Loader

Tests TOML parsing, validation, and pattern matching.
"""

import pytest
from pathlib import Path

from src.ai_orchestration import (
    CapabilityScopeLoader,
    CapabilityScopeError,
    CapabilityScope,
)


def test_load_l0_capability_scope():
    """Test loading L0 Ops/Docs capability scope."""
    loader = CapabilityScopeLoader()
    scope = loader.load("L0")

    assert isinstance(scope, CapabilityScope)
    assert scope.layer_id == "L0"
    assert scope.autonomy_level == "REC"
    assert scope.primary == "gpt-5.2"
    assert scope.fallback == "gpt-5-mini"
    assert scope.critic == "deepseek-r1"

    # Check tooling
    assert "files" in scope.tooling_allowed
    assert "web" in scope.tooling_forbidden
    assert "execution" in scope.tooling_forbidden

    # Check safety
    assert "no_live_toggle" in scope.safety_checks
    assert scope.alert_on_violation is True
    assert scope.alert_channel == "ops-safety"


def test_load_l2_capability_scope():
    """Test loading L2 Market Outlook capability scope."""
    loader = CapabilityScopeLoader()
    scope = loader.load("L2")

    assert scope.layer_id == "L2"
    assert scope.autonomy_level == "PROP"
    assert scope.primary == "gpt-5.2-pro"
    assert scope.critic == "deepseek-r1"

    # Check inputs
    assert "docs/market_outlook/**/*.yaml" in scope.inputs_allowed
    assert "src/execution/**/*" in scope.inputs_forbidden

    # Check outputs
    assert "ScenarioReport" in scope.outputs_allowed
    assert "ExecutionCommand" in scope.outputs_forbidden

    # Check tooling (web access allowed)
    assert "files" in scope.tooling_allowed
    assert "web" in scope.tooling_allowed

    # Check web access constraints
    assert scope.web_access is not None
    assert "allowed_domains" in scope.web_access
    assert "*.tradingeconomics.com" in scope.web_access["allowed_domains"]

    # Check validation
    assert scope.validation is not None
    assert scope.validation["min_scenario_count"] == 2


def test_load_l4_capability_scope():
    """Test loading L4 Governance Critic capability scope."""
    loader = CapabilityScopeLoader()
    scope = loader.load("L4")

    assert scope.layer_id == "L4"
    assert scope.autonomy_level == "RO/REC"
    assert scope.primary == "o3-pro"

    # Check that governance can read policy files
    assert "docs/governance/**/*.md" in scope.inputs_allowed

    # Check that governance cannot execute
    assert "ExecutionCommand" in scope.outputs_forbidden
    assert "execution" in scope.tooling_forbidden


def test_capability_scope_not_found():
    """Test error when capability scope not found."""
    loader = CapabilityScopeLoader()

    with pytest.raises(CapabilityScopeError, match="not found"):
        loader.load("L99")


def test_validate_input_allowed():
    """Test input validation - allowed path."""
    loader = CapabilityScopeLoader()

    # L0 allows docs/**/*.md
    assert loader.validate_input("L0", "docs/**/*.md") is True
    # Also test with specific path that matches pattern
    assert loader.validate_input("L0", "README.md") is True


def test_validate_input_forbidden():
    """Test input validation - forbidden path."""
    loader = CapabilityScopeLoader()

    # L0 forbids execution code
    assert loader.validate_input("L0", "src/execution/order.py") is False


def test_validate_output_allowed():
    """Test output validation - allowed type."""
    loader = CapabilityScopeLoader()

    # L2 allows ScenarioReport
    assert loader.validate_output("L2", "ScenarioReport") is True


def test_validate_output_forbidden():
    """Test output validation - forbidden type."""
    loader = CapabilityScopeLoader()

    # L2 forbids ExecutionCommand
    assert loader.validate_output("L2", "ExecutionCommand") is False


def test_validate_tooling_allowed():
    """Test tooling validation - allowed tool."""
    loader = CapabilityScopeLoader()

    # L2 allows web
    assert loader.validate_tooling("L2", "web") is True


def test_validate_tooling_forbidden():
    """Test tooling validation - forbidden tool."""
    loader = CapabilityScopeLoader()

    # L0 forbids web
    assert loader.validate_tooling("L0", "web") is False


def test_all_scopes_have_required_sections():
    """Test that all scope files have required sections."""
    loader = CapabilityScopeLoader()
    layers = ["L0", "L1", "L2", "L4"]

    for layer in layers:
        scope = loader.load(layer)

        # Check required fields
        assert scope.layer_id
        assert scope.autonomy_level
        assert scope.primary
        assert scope.critic
        assert len(scope.inputs_allowed) > 0
        assert len(scope.outputs_allowed) > 0
        assert len(scope.tooling_allowed) > 0
        assert len(scope.safety_checks) > 0
        assert scope.alert_channel
