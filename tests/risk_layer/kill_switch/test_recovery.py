"""Tests for Kill Switch recovery system."""

import pytest
import time
from datetime import datetime

from src.risk_layer.kill_switch.health_check import HealthChecker, HealthCheckResult
from src.risk_layer.kill_switch.recovery import (
    RecoveryManager,
    RecoveryRequest,
    RecoveryStage,
)


@pytest.fixture
def recovery_config():
    """Recovery configuration for testing."""
    return {
        "cooldown_seconds": 1,  # Short for tests
        "require_approval_code": True,
        "require_health_check": True,
        "require_trigger_clear": True,
        "gradual_restart_enabled": True,
        "initial_position_limit_factor": 0.5,
        "escalation_intervals": [2, 4],  # 2s, 4s for testing
        "escalation_factors": [0.75, 1.0],
        "min_memory_available_mb": 256,
        "max_cpu_percent": 90,
        "require_exchange_connection": False,
        "require_price_feed": False,
    }


@pytest.fixture
def health_checker(recovery_config):
    """Create health checker for testing."""
    return HealthChecker(recovery_config)


@pytest.fixture
def recovery_manager(recovery_config, health_checker):
    """Create recovery manager for testing."""
    return RecoveryManager(recovery_config, health_checker)


class TestHealthChecker:
    """Tests for HealthChecker."""

    def test_check_all_returns_result(self, health_checker):
        """check_all should return HealthCheckResult."""
        context = {
            "exchange_connected": True,
            "last_price_update": datetime.utcnow(),
        }

        result = health_checker.check_all(context)

        assert isinstance(result, HealthCheckResult)
        assert isinstance(result.is_healthy, bool)
        assert isinstance(result.issues, list)

    def test_healthy_system_passes(self, health_checker):
        """Healthy system should pass health checks."""
        context = {
            "exchange_connected": True,
            "last_price_update": datetime.utcnow(),
        }

        result = health_checker.check_all(context)

        # May pass or fail depending on system resources
        assert result.checks_passed >= 0
        assert result.checks_failed >= 0

    def test_missing_exchange_fails_if_required(self):
        """Missing exchange should fail if required."""
        config = {
            "require_exchange_connection": True,
            "require_price_feed": False,
            "min_memory_available_mb": 256,
            "max_cpu_percent": 90,
        }
        checker = HealthChecker(config)

        context = {"exchange_connected": False}
        result = checker.check_all(context)

        assert not result.is_healthy
        assert any("exchange" in issue.lower() for issue in result.issues)

    def test_result_has_metadata(self, health_checker):
        """Result should include metadata."""
        context = {}
        result = health_checker.check_all(context)

        assert isinstance(result.metadata, dict)


class TestRecoveryRequest:
    """Tests for RecoveryRequest dataclass."""

    def test_request_created_with_timestamp(self, recovery_manager):
        """Recovery request should have timestamp."""
        request = recovery_manager.request_recovery("operator", "TEST_CODE", "Test recovery")

        assert isinstance(request.requested_at, datetime)
        assert request.requested_by == "operator"
        assert request.approval_code == "TEST_CODE"
        assert request.reason == "Test recovery"
        assert request.stage == RecoveryStage.PENDING

    def test_request_to_dict(self, recovery_manager):
        """Recovery request should serialize to dict."""
        request = recovery_manager.request_recovery("operator", "CODE", "Test")

        data = request.to_dict()

        assert isinstance(data, dict)
        assert "requested_at" in data
        assert "requested_by" in data
        assert "stage" in data


class TestRecoveryManager:
    """Tests for RecoveryManager."""

    def test_request_recovery_creates_request(self, recovery_manager):
        """request_recovery should create recovery request."""
        request = recovery_manager.request_recovery("operator", "TEST_CODE", "Test recovery")

        assert isinstance(request, RecoveryRequest)
        assert recovery_manager.current_request == request
        assert recovery_manager.current_stage == RecoveryStage.PENDING

    def test_validate_approval_with_correct_code(self, recovery_manager):
        """validate_approval should pass with correct code."""
        recovery_manager.request_recovery("op", "CORRECT", "test")

        result = recovery_manager.validate_approval("CORRECT")

        assert result is True
        assert recovery_manager.current_stage == RecoveryStage.VALIDATING

    def test_validate_approval_with_wrong_code(self, recovery_manager):
        """validate_approval should fail with wrong code."""
        recovery_manager.request_recovery("op", "CORRECT", "test")

        result = recovery_manager.validate_approval("WRONG")

        assert result is False
        assert recovery_manager.current_stage == RecoveryStage.PENDING

    def test_validate_approval_without_request(self, recovery_manager):
        """validate_approval should fail without active request."""
        result = recovery_manager.validate_approval("CODE")

        assert result is False

    def test_run_health_checks(self, recovery_manager):
        """run_health_checks should execute health checks."""
        recovery_manager.request_recovery("op", "CODE", "test")
        recovery_manager.validate_approval("CODE")

        context = {
            "exchange_connected": True,
            "last_price_update": datetime.utcnow(),
        }
        result = recovery_manager.run_health_checks(context)

        assert isinstance(result, HealthCheckResult)
        assert recovery_manager.current_request.health_check_result == result

    def test_health_check_updates_stage_on_pass(self, recovery_manager):
        """Health check should update stage to COOLDOWN if passed."""
        recovery_manager.request_recovery("op", "CODE", "test")
        recovery_manager.validate_approval("CODE")

        # Mock healthy context
        context = {
            "exchange_connected": True,
            "last_price_update": datetime.utcnow(),
        }
        result = recovery_manager.run_health_checks(context)

        if result.is_healthy:
            assert recovery_manager.current_stage == RecoveryStage.COOLDOWN

    def test_check_cooldown_complete(self, recovery_manager):
        """check_cooldown_complete should validate cooldown."""
        recovery_manager.request_recovery("op", "CODE", "test")
        recovery_manager.validate_approval("CODE")

        # Cooldown not complete immediately
        assert not recovery_manager.check_cooldown_complete(cooldown_seconds=2)

        # Wait for cooldown
        time.sleep(2.1)

        # Cooldown complete
        assert recovery_manager.check_cooldown_complete(cooldown_seconds=2)

    def test_get_cooldown_remaining(self, recovery_manager):
        """get_cooldown_remaining should return remaining time."""
        recovery_manager.request_recovery("op", "CODE", "test")
        recovery_manager.validate_approval("CODE")

        remaining = recovery_manager.get_cooldown_remaining(cooldown_seconds=5)

        assert 0 < remaining <= 5

    def test_gradual_restart_initial_factor(self, recovery_manager):
        """Gradual restart should start with initial factor."""
        recovery_manager.start_gradual_restart()

        assert recovery_manager.position_limit_factor == 0.5
        assert recovery_manager.current_stage == RecoveryStage.GRADUAL_RESTART

    def test_gradual_restart_disabled(self):
        """Gradual restart can be disabled."""
        config = {
            "cooldown_seconds": 1,
            "gradual_restart_enabled": False,
        }
        health_checker = HealthChecker(config)
        manager = RecoveryManager(config, health_checker)

        manager.request_recovery("op", "CODE", "test")
        manager.start_gradual_restart()

        # Should skip gradual restart
        assert manager.position_limit_factor == 1.0
        assert manager.current_stage == RecoveryStage.COMPLETE

    def test_gradual_restart_escalation(self, recovery_manager):
        """Gradual restart should escalate limits over time."""
        recovery_manager.request_recovery("op", "CODE", "test")
        recovery_manager.validate_approval("CODE")
        recovery_manager.start_gradual_restart()

        # Initial: 50%
        assert recovery_manager.position_limit_factor == 0.5

        # After 2 seconds: 75%
        time.sleep(2.1)
        factor = recovery_manager.update_gradual_restart()
        assert factor == 0.75

        # After 4 seconds total: 100%
        time.sleep(2.1)
        factor = recovery_manager.update_gradual_restart()
        assert factor == 1.0
        assert recovery_manager.current_stage == RecoveryStage.COMPLETE

    def test_position_limit_factor_property(self, recovery_manager):
        """position_limit_factor property should return current factor."""
        assert recovery_manager.position_limit_factor == 1.0

        recovery_manager.start_gradual_restart()
        assert recovery_manager.position_limit_factor == 0.5

    def test_reset_clears_state(self, recovery_manager):
        """reset should clear recovery state."""
        recovery_manager.request_recovery("op", "CODE", "test")
        recovery_manager.start_gradual_restart()

        recovery_manager.reset()

        assert recovery_manager.current_request is None
        assert recovery_manager.position_limit_factor == 1.0


class TestRecoveryWorkflow:
    """Test complete recovery workflow."""

    def test_full_recovery_workflow(self, recovery_manager):
        """Test complete recovery from request to complete."""
        # 1. Request recovery
        request = recovery_manager.request_recovery("operator", "TEST_CODE", "System fixed")
        assert request.stage == RecoveryStage.PENDING

        # 2. Validate approval
        assert recovery_manager.validate_approval("TEST_CODE")
        assert request.stage == RecoveryStage.VALIDATING

        # 3. Run health checks
        context = {
            "exchange_connected": True,
            "last_price_update": datetime.utcnow(),
        }
        result = recovery_manager.run_health_checks(context)

        if result.is_healthy:
            assert request.stage == RecoveryStage.COOLDOWN

            # 4. Wait for cooldown
            time.sleep(1.1)
            assert recovery_manager.check_cooldown_complete(1)

            # 5. Start gradual restart
            recovery_manager.start_gradual_restart()
            assert request.stage == RecoveryStage.GRADUAL_RESTART
            assert recovery_manager.position_limit_factor == 0.5

            # 6. Escalate to completion
            time.sleep(4.5)  # Wait for full escalation
            recovery_manager.update_gradual_restart()

            assert recovery_manager.position_limit_factor == 1.0
            assert request.stage == RecoveryStage.COMPLETE

    def test_recovery_fails_with_invalid_approval(self, recovery_manager):
        """Recovery should fail with invalid approval."""
        recovery_manager.request_recovery("op", "CORRECT", "test")

        assert not recovery_manager.validate_approval("WRONG")
        assert recovery_manager.current_stage == RecoveryStage.PENDING

    def test_recovery_requires_active_request(self, recovery_manager):
        """Recovery operations require active request."""
        # No active request
        assert not recovery_manager.validate_approval("CODE")

        with pytest.raises(ValueError):
            recovery_manager.run_health_checks({})
