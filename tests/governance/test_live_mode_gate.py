"""
Tests for WP0C - Live Mode Gate

Comprehensive tests for governance layer:
- Blocked-by-default behavior
- Environment separation
- Config validation
- Approval workflow
- Audit logging
"""

import pytest
from datetime import datetime
from pathlib import Path
import json
import tempfile

from src.governance.live_mode_gate import (
    ExecutionEnvironment,
    LiveModeStatus,
    LiveModeGate,
    ValidationResult,
    create_gate,
    is_live_allowed,
)


class TestExecutionEnvironment:
    """Test ExecutionEnvironment enum."""

    def test_is_live_detection(self):
        """Test that testnet and prod are considered live."""
        assert ExecutionEnvironment.DEV.is_live() is False
        assert ExecutionEnvironment.SHADOW.is_live() is False
        assert ExecutionEnvironment.TESTNET.is_live() is True
        assert ExecutionEnvironment.PROD.is_live() is True

    def test_requires_extra_validation(self):
        """Test that live envs require extra validation."""
        assert ExecutionEnvironment.DEV.requires_extra_validation() is False
        assert ExecutionEnvironment.SHADOW.requires_extra_validation() is False
        assert ExecutionEnvironment.TESTNET.requires_extra_validation() is True
        assert ExecutionEnvironment.PROD.requires_extra_validation() is True


class TestLiveModeGateBlockedByDefault:
    """Test blocked-by-default behavior."""

    def test_gate_starts_blocked(self):
        """Gate should start in BLOCKED state by default."""
        gate = LiveModeGate(environment=ExecutionEnvironment.PROD)
        state = gate.get_state()

        assert state.status == LiveModeStatus.BLOCKED
        assert state.is_allowed() is False
        assert "blocked by default" in state.reason.lower()

    def test_is_live_allowed_false_initially(self):
        """Convenience function should return False initially."""
        gate = LiveModeGate(environment=ExecutionEnvironment.PROD)
        assert is_live_allowed(gate) is False

    def test_all_envs_start_blocked(self):
        """All environments should start blocked."""
        for env in ExecutionEnvironment:
            gate = LiveModeGate(environment=env)
            assert gate.get_state().status == LiveModeStatus.BLOCKED


class TestConfigValidation:
    """Test config validation logic."""

    def test_valid_config_for_live_env(self):
        """Valid config for live environment should pass."""
        config = {
            "session_id": "test_session_123",
            "strategy_id": "ma_crossover",
            "risk_limits": {
                "max_position_size": 1000,
                "max_drawdown": 0.1,
            },
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.TESTNET,
            config=config,
        )
        result = gate.validate_config()

        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_required_keys_for_live_env(self):
        """Missing required keys should fail validation for live env."""
        config = {
            "session_id": "test_session_123",
            # Missing: strategy_id, risk_limits
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.PROD,
            config=config,
        )
        result = gate.validate_config()

        assert result.valid is False
        assert len(result.errors) >= 2  # Missing strategy_id and risk_limits
        assert any("strategy_id" in err for err in result.errors)
        assert any("risk_limits" in err for err in result.errors)

    def test_empty_risk_limits_rejected_for_live_env(self):
        """Empty risk_limits should fail validation for live env."""
        config = {
            "session_id": "test_session_123",
            "strategy_id": "ma_crossover",
            "risk_limits": {},  # Empty!
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.PROD,
            config=config,
        )
        result = gate.validate_config()

        assert result.valid is False
        assert any("cannot be empty" in err for err in result.errors)

    def test_dev_env_allows_minimal_config(self):
        """Dev environment should allow minimal config."""
        config = {
            "strategy_id": "ma_crossover",
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.DEV,
            config=config,
        )
        result = gate.validate_config()

        assert result.valid is True
        # May have warnings, but should not have errors
        assert len(result.errors) == 0

    def test_invalid_strategy_id_type_rejected(self):
        """Invalid strategy_id type should fail validation."""
        config = {
            "session_id": "test_session_123",
            "strategy_id": 123,  # Should be string!
            "risk_limits": {"max_position_size": 1000},
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.PROD,
            config=config,
        )
        result = gate.validate_config()

        assert result.valid is False
        assert any("string" in err.lower() for err in result.errors)

    def test_validation_warnings_for_dev_env(self):
        """Dev env should get warnings for missing risk_limits."""
        config = {
            "strategy_id": "ma_crossover",
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.DEV,
            config=config,
        )
        result = gate.validate_config()

        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("risk_limits" in warn for warn in result.warnings)


class TestApprovalWorkflow:
    """Test approval/revocation workflow."""

    def test_approval_with_valid_config(self):
        """Approval with valid config should succeed."""
        config = {
            "session_id": "test_session_123",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.TESTNET,
            config=config,
        )

        success = gate.request_approval(
            requester="operator@peak-trade.io",
            reason="Approved for testnet deployment",
        )

        assert success is True
        state = gate.get_state()
        assert state.status == LiveModeStatus.APPROVED
        assert state.is_allowed() is True
        assert state.approved_by == "operator@peak-trade.io"
        assert state.approved_at is not None

    def test_approval_rejected_with_invalid_config(self):
        """Approval with invalid config should fail."""
        config = {
            # Missing required keys
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.PROD,
            config=config,
        )

        success = gate.request_approval(
            requester="operator@peak-trade.io",
            reason="Attempt to approve with invalid config",
        )

        assert success is False
        state = gate.get_state()
        assert state.status == LiveModeStatus.FAILED_VALIDATION
        assert state.is_allowed() is False
        assert "validation failed" in state.reason.lower()

    def test_approval_includes_config_hash(self):
        """Approval should store config hash if provided."""
        config = {
            "session_id": "test_session_123",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.TESTNET,
            config=config,
        )

        config_hash = "abc123def456"
        success = gate.request_approval(
            requester="operator@peak-trade.io",
            reason="Approved with hash",
            config_hash=config_hash,
        )

        assert success is True
        assert gate.get_state().config_hash == config_hash

    def test_revoke_approval(self):
        """Revoking approval should suspend live mode."""
        config = {
            "session_id": "test_session_123",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.TESTNET,
            config=config,
        )

        # First approve
        gate.request_approval(
            requester="operator@peak-trade.io",
            reason="Initial approval",
        )
        assert gate.get_state().is_allowed() is True

        # Then revoke
        gate.revoke_approval(reason="Emergency suspension")

        state = gate.get_state()
        assert state.status == LiveModeStatus.SUSPENDED
        assert state.is_allowed() is False
        assert "emergency suspension" in state.reason.lower()

    def test_reset_gate(self):
        """Resetting gate should return to blocked state."""
        config = {
            "session_id": "test_session_123",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        gate = LiveModeGate(
            environment=ExecutionEnvironment.TESTNET,
            config=config,
        )

        # Approve first
        gate.request_approval(
            requester="operator@peak-trade.io",
            reason="Initial approval",
        )
        assert gate.get_state().is_allowed() is True

        # Reset
        gate.reset()

        state = gate.get_state()
        assert state.status == LiveModeStatus.BLOCKED
        assert state.is_allowed() is False
        assert state.approved_at is None
        assert state.approved_by is None


class TestAuditLogging:
    """Test audit logging behavior."""

    def test_audit_log_approval_granted(self):
        """Approval should be logged to audit log."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            audit_log_path = Path(f.name)

        try:
            config = {
                "session_id": "test_session_123",
                "strategy_id": "ma_crossover",
                "risk_limits": {"max_position_size": 1000},
            }
            gate = LiveModeGate(
                environment=ExecutionEnvironment.TESTNET,
                config=config,
                audit_log_path=audit_log_path,
            )

            gate.request_approval(
                requester="operator@peak-trade.io",
                reason="Test approval",
            )

            # Read audit log
            with open(audit_log_path, "r") as f:
                lines = f.readlines()

            assert len(lines) >= 1
            entry = json.loads(lines[0])
            assert entry["event_type"] == "approval_granted"
            assert entry["environment"] == "testnet"
            assert entry["details"]["requester"] == "operator@peak-trade.io"

        finally:
            audit_log_path.unlink(missing_ok=True)

    def test_audit_log_approval_rejected(self):
        """Rejected approval should be logged."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            audit_log_path = Path(f.name)

        try:
            config = {}  # Invalid config
            gate = LiveModeGate(
                environment=ExecutionEnvironment.PROD,
                config=config,
                audit_log_path=audit_log_path,
            )

            gate.request_approval(
                requester="operator@peak-trade.io",
                reason="Test approval",
            )

            # Read audit log
            with open(audit_log_path, "r") as f:
                lines = f.readlines()

            assert len(lines) >= 1
            entry = json.loads(lines[0])
            assert entry["event_type"] == "approval_rejected"
            assert "errors" in entry["details"]

        finally:
            audit_log_path.unlink(missing_ok=True)

    def test_audit_log_revocation(self):
        """Revocation should be logged."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            audit_log_path = Path(f.name)

        try:
            config = {
                "session_id": "test_session_123",
                "strategy_id": "ma_crossover",
                "risk_limits": {"max_position_size": 1000},
            }
            gate = LiveModeGate(
                environment=ExecutionEnvironment.TESTNET,
                config=config,
                audit_log_path=audit_log_path,
            )

            gate.request_approval(
                requester="operator@peak-trade.io",
                reason="Initial approval",
            )
            gate.revoke_approval(reason="Emergency stop")

            # Read audit log
            with open(audit_log_path, "r") as f:
                lines = f.readlines()

            assert len(lines) >= 2
            revoke_entry = json.loads(lines[1])
            assert revoke_entry["event_type"] == "approval_revoked"
            assert revoke_entry["details"]["reason"] == "Emergency stop"

        finally:
            audit_log_path.unlink(missing_ok=True)


class TestFactoryFunction:
    """Test factory function."""

    def test_create_gate_with_string_env(self):
        """Factory should accept string environment."""
        gate = create_gate(environment="testnet")
        assert gate.environment == ExecutionEnvironment.TESTNET
        assert gate.get_state().status == LiveModeStatus.BLOCKED

    def test_create_gate_with_enum_env(self):
        """Factory should accept enum environment."""
        gate = create_gate(environment=ExecutionEnvironment.PROD)
        assert gate.environment == ExecutionEnvironment.PROD

    def test_create_gate_with_config(self):
        """Factory should accept config."""
        config = {"strategy_id": "test"}
        gate = create_gate(
            environment="dev",
            config=config,
        )
        assert gate.config == config

    def test_create_gate_with_audit_log(self):
        """Factory should accept audit log path."""
        audit_log_path = Path("/tmp/test_audit.jsonl")
        gate = create_gate(
            environment="dev",
            audit_log_path=audit_log_path,
        )
        assert gate.audit_log_path == audit_log_path


class TestEnvironmentSeparation:
    """Test environment separation guarantees."""

    def test_each_env_has_independent_gate(self):
        """Each environment should have independent gate state."""
        gate_dev = create_gate("dev", config={"strategy_id": "test"})
        gate_prod = create_gate("prod", config={
            "session_id": "test_session_123",
            "strategy_id": "test",
            "risk_limits": {"max_position_size": 1000},
        })

        # Approve dev
        gate_dev.request_approval(requester="dev-operator", reason="Dev approval")

        # Prod should still be blocked
        assert gate_dev.get_state().is_allowed() is True
        assert gate_prod.get_state().is_allowed() is False

    def test_prod_config_not_valid_for_dev_gate(self):
        """Prod config should be validated independently per gate."""
        prod_config = {
            "session_id": "test_session_123",
            "strategy_id": "test",
            "risk_limits": {"max_position_size": 1000},
        }

        gate_dev = create_gate("dev", config={})  # Minimal config
        gate_prod = create_gate("prod", config=prod_config)

        # Dev gate with minimal config should validate (with warnings)
        dev_result = gate_dev.validate_config()
        assert dev_result.valid is True

        # Prod gate with full config should validate
        prod_result = gate_prod.validate_config()
        assert prod_result.valid is True
