"""
Tests for AI Orchestration Data Models

Reference: docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md
"""

import pytest
from src.ai_orchestration.models import (
    LayerRunMetadata,
    SoDCheckResult,
    AutonomyLevel,
    SoDResult,
    CriticDecision,
)


class TestLayerRunMetadata:
    """Test LayerRunMetadata validation."""

    def test_valid_metadata(self):
        """Valid metadata passes validation."""
        metadata = LayerRunMetadata(
            layer_id="L2",
            layer_name="Market Outlook",
            autonomy_level=AutonomyLevel.PROP,
            primary_model_id="gpt-5.2-pro",
            fallback_model_id="gpt-5.2",
            critic_model_id="deepseek-r1",
            capability_scope_id="L2_market_outlook_v1",
            matrix_version="v1.0",
        )

        # Should not raise
        metadata.validate()

    def test_sod_fail_same_models(self):
        """SoD fails if Primary == Critic."""
        metadata = LayerRunMetadata(
            layer_id="L2",
            layer_name="Market Outlook",
            autonomy_level=AutonomyLevel.PROP,
            primary_model_id="gpt-5.2-pro",
            critic_model_id="gpt-5.2-pro",  # Same as primary!
            capability_scope_id="L2_market_outlook_v1",
            matrix_version="v1.0",
        )

        with pytest.raises(ValueError, match="SoD FAIL"):
            metadata.validate()

    def test_exec_forbidden(self):
        """EXEC autonomy level is forbidden."""
        metadata = LayerRunMetadata(
            layer_id="L6",
            layer_name="Execution",
            autonomy_level=AutonomyLevel.EXEC,  # Forbidden!
            primary_model_id="gpt-5.2-pro",
            critic_model_id="deepseek-r1",
            capability_scope_id="L6_execution",
            matrix_version="v1.0",
        )

        with pytest.raises(ValueError, match="EXEC is forbidden"):
            metadata.validate()

    def test_invalid_layer_id(self):
        """Invalid layer_id raises assertion."""
        metadata = LayerRunMetadata(
            layer_id="L99",  # Invalid!
            layer_name="Unknown",
            autonomy_level=AutonomyLevel.REC,
            primary_model_id="gpt-5.2",
            critic_model_id="deepseek-r1",
            capability_scope_id="test",
            matrix_version="v1.0",
        )

        with pytest.raises(AssertionError, match="Invalid layer_id"):
            metadata.validate()


class TestSoDCheckResult:
    """Test SoD Check validation."""

    def test_sod_pass(self):
        """Valid SoD check passes."""
        sod_result = SoDCheckResult(
            proposer_run_id="run_abc123",
            proposer_model_id="gpt-5.2-pro",
            proposer_artifact_hash="a1b2c3d4",
            critic_run_id="run_def456",
            critic_model_id="deepseek-r1",
            critic_artifact_hash="e5f6g7h8",
            sod_check_timestamp="2026-01-08T14:35:00Z",
            critic_decision=CriticDecision.APPROVE,
            critic_rationale="Scenario analysis passed. Safe.",
            evidence_ids=["EV-20260107-SEED"],
        )

        # Should not raise, should set sod_result = PASS
        sod_result.validate()
        assert sod_result.sod_result == SoDResult.PASS

    def test_sod_fail_same_models(self):
        """SoD fails if Proposer == Critic."""
        sod_result = SoDCheckResult(
            proposer_run_id="run_abc123",
            proposer_model_id="gpt-5.2-pro",
            proposer_artifact_hash="a1b2c3d4",
            critic_run_id="run_def456",
            critic_model_id="gpt-5.2-pro",  # Same as proposer!
            critic_artifact_hash="e5f6g7h8",
            sod_check_timestamp="2026-01-08T14:35:00Z",
            critic_decision=CriticDecision.APPROVE,
            critic_rationale="Test",
            evidence_ids=["EV-TEST"],
        )

        with pytest.raises(ValueError, match="SoD FAIL.*Proposer == Critic"):
            sod_result.validate()

        assert sod_result.sod_result == SoDResult.FAIL

    def test_sod_fail_empty_rationale(self):
        """SoD fails if critic_rationale is empty."""
        sod_result = SoDCheckResult(
            proposer_run_id="run_abc123",
            proposer_model_id="gpt-5.2-pro",
            proposer_artifact_hash="a1b2c3d4",
            critic_run_id="run_def456",
            critic_model_id="deepseek-r1",
            critic_artifact_hash="e5f6g7h8",
            sod_check_timestamp="2026-01-08T14:35:00Z",
            critic_decision=CriticDecision.APPROVE,
            critic_rationale="",  # Empty!
            evidence_ids=["EV-TEST"],
        )

        with pytest.raises(ValueError, match="SoD FAIL.*Empty critic_rationale"):
            sod_result.validate()

        assert sod_result.sod_result == SoDResult.FAIL

    def test_sod_fail_no_evidence_ids(self):
        """SoD fails if evidence_ids is empty."""
        sod_result = SoDCheckResult(
            proposer_run_id="run_abc123",
            proposer_model_id="gpt-5.2-pro",
            proposer_artifact_hash="a1b2c3d4",
            critic_run_id="run_def456",
            critic_model_id="deepseek-r1",
            critic_artifact_hash="e5f6g7h8",
            sod_check_timestamp="2026-01-08T14:35:00Z",
            critic_decision=CriticDecision.APPROVE,
            critic_rationale="Test rationale",
            evidence_ids=[],  # Empty!
        )

        with pytest.raises(ValueError, match="SoD FAIL.*No evidence_ids"):
            sod_result.validate()

        assert sod_result.sod_result == SoDResult.FAIL

    def test_sod_reject_is_valid(self):
        """Critic decision = REJECT is valid (SoD passes)."""
        sod_result = SoDCheckResult(
            proposer_run_id="run_abc123",
            proposer_model_id="gpt-5.2-pro",
            proposer_artifact_hash="a1b2c3d4",
            critic_run_id="run_def456",
            critic_model_id="deepseek-r1",
            critic_artifact_hash="e5f6g7h8",
            sod_check_timestamp="2026-01-08T14:35:00Z",
            critic_decision=CriticDecision.REJECT,  # REJECT is valid
            critic_rationale="Found execution trigger in output. Rejecting.",
            evidence_ids=["EV-20260107-SEED"],
        )

        sod_result.validate()
        assert sod_result.sod_result == SoDResult.PASS
