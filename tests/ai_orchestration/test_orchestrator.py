"""
Tests for Runtime Orchestrator

Tests model selection, fail-closed enforcement, SoD validation.
"""

import os
import pytest
from pathlib import Path

from src.ai_orchestration.orchestrator import (
    Orchestrator,
    ModelSelection,
    SelectionConstraints,
    InvalidLayerError,
    InvalidModelError,
    ForbiddenAutonomyError,
    SoDViolationError,
    OrchestratorError,
)
from src.ai_orchestration.models import AutonomyLevel


@pytest.fixture
def config_dir():
    """Get config directory."""
    repo_root = Path(__file__).parent.parent.parent
    return repo_root / "config"


@pytest.fixture
def orchestrator_enabled(monkeypatch):
    """Enable orchestrator for tests."""
    monkeypatch.setenv("ORCHESTRATOR_ENABLED", "true")


@pytest.fixture
def orchestrator(config_dir, orchestrator_enabled):
    """Create orchestrator instance."""
    return Orchestrator(config_dir=config_dir)


class TestOrchestratorInit:
    """Test orchestrator initialization."""

    def test_init_success(self, config_dir, orchestrator_enabled):
        """Test successful initialization."""
        orch = Orchestrator(config_dir=config_dir)
        assert orch.registry is not None
        assert orch.scopes is not None
        assert orch.layer_mapping is not None
        assert orch.enabled is True

    def test_init_disabled_by_default(self, config_dir, monkeypatch):
        """Test orchestrator is disabled by default."""
        monkeypatch.delenv("ORCHESTRATOR_ENABLED", raising=False)
        orch = Orchestrator(config_dir=config_dir)
        assert orch.enabled is False

    def test_init_missing_registry(self, tmp_path, orchestrator_enabled):
        """Test initialization fails if registry missing."""
        with pytest.raises(FileNotFoundError, match="Model registry not found"):
            Orchestrator(config_dir=tmp_path)

    def test_health_check(self, orchestrator):
        """Test health check."""
        health = orchestrator.health_check()
        assert health["enabled"] is True
        assert health["registry_version"] == "1.0"
        assert health["models_count"] >= 8
        assert health["layers_mapped"] >= 7
        assert health["status"] == "healthy"


class TestModelSelection:
    """Test model selection (positive cases)."""

    def test_select_model_L0_REC(self, orchestrator):
        """Test L0 (Ops/Docs) REC selection."""
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC
        )

        assert selection.layer_id == "L0"
        assert selection.autonomy_level == AutonomyLevel.REC
        assert selection.primary_model_id == "gpt-5-2"
        assert "gpt-5-mini" in selection.fallback_model_ids
        assert selection.critic_model_id == "deepseek-r1"
        assert selection.registry_version == "1.0"
        assert selection.sod_validated is True
        assert "L0" in selection.selection_reason

    def test_select_model_L1_PROP(self, orchestrator):
        """Test L1 (DeepResearch) PROP selection."""
        selection = orchestrator.select_model(
            layer_id="L1", autonomy_level=AutonomyLevel.PROP
        )

        assert selection.layer_id == "L1"
        assert selection.autonomy_level == AutonomyLevel.PROP
        assert selection.primary_model_id == "o3-deep-research"
        assert "o4-mini-deep-research" in selection.fallback_model_ids
        assert "deepseek-r1" in selection.fallback_model_ids
        assert selection.critic_model_id == "o3-pro"
        assert selection.sod_validated is True

    def test_select_model_L2_PROP(self, orchestrator):
        """Test L2 (Market Outlook) PROP selection."""
        selection = orchestrator.select_model(
            layer_id="L2", autonomy_level=AutonomyLevel.PROP
        )

        assert selection.layer_id == "L2"
        assert selection.autonomy_level == AutonomyLevel.PROP
        assert selection.primary_model_id == "gpt-5-2-pro"
        assert "gpt-5-2" in selection.fallback_model_ids
        assert selection.critic_model_id == "deepseek-r1"
        assert selection.sod_validated is True

    def test_select_model_L3_REC(self, orchestrator):
        """Test L3 (Trade Plan Advisory) REC selection."""
        selection = orchestrator.select_model(
            layer_id="L3", autonomy_level=AutonomyLevel.REC
        )

        assert selection.layer_id == "L3"
        assert selection.autonomy_level == AutonomyLevel.REC
        assert selection.primary_model_id == "gpt-5-2-pro"
        assert selection.critic_model_id == "o3"
        assert selection.sod_validated is True

    def test_select_model_L4_RO(self, orchestrator):
        """Test L4 (Governance) RO selection."""
        selection = orchestrator.select_model(
            layer_id="L4", autonomy_level=AutonomyLevel.RO
        )

        assert selection.layer_id == "L4"
        assert selection.autonomy_level == AutonomyLevel.RO
        assert selection.primary_model_id == "o3-pro"
        assert "deepseek-r1" in selection.fallback_model_ids
        assert selection.critic_model_id == "gpt-5-2-pro"
        assert selection.sod_validated is True

    def test_select_model_with_context(self, orchestrator):
        """Test selection with context."""
        selection = orchestrator.select_model(
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            task_type="documentation",
            context={"priority": "high"},
        )

        assert selection.layer_id == "L0"
        assert selection.primary_model_id == "gpt-5-2"

    def test_select_model_to_dict(self, orchestrator):
        """Test ModelSelection serialization."""
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC
        )

        data = selection.to_dict()
        assert data["layer_id"] == "L0"
        assert data["autonomy_level"] == "REC"
        assert data["primary_model_id"] == "gpt-5-2"
        assert data["sod_validated"] is True
        assert "selection_timestamp" in data


class TestFailClosed:
    """Test fail-closed enforcement (negative cases)."""

    def test_orchestrator_disabled(self, config_dir, monkeypatch):
        """Test orchestrator raises if disabled."""
        monkeypatch.delenv("ORCHESTRATOR_ENABLED", raising=False)
        orch = Orchestrator(config_dir=config_dir)

        with pytest.raises(RuntimeError, match="Orchestrator is disabled"):
            orch.select_model(layer_id="L0", autonomy_level=AutonomyLevel.REC)

    def test_invalid_layer_unknown(self, orchestrator):
        """Test unknown layer_id raises."""
        with pytest.raises(InvalidLayerError, match="Invalid layer_id: LX"):
            orchestrator.select_model(layer_id="LX", autonomy_level=AutonomyLevel.REC)

    def test_invalid_layer_empty(self, orchestrator):
        """Test empty layer_id raises."""
        with pytest.raises(InvalidLayerError, match="Invalid layer_id"):
            orchestrator.select_model(layer_id="", autonomy_level=AutonomyLevel.REC)

    def test_forbidden_autonomy_exec(self, orchestrator):
        """Test EXEC autonomy level is forbidden."""
        with pytest.raises(ForbiddenAutonomyError, match="EXEC is forbidden"):
            orchestrator.select_model(layer_id="L0", autonomy_level=AutonomyLevel.EXEC)

    def test_forbidden_autonomy_exec_L2(self, orchestrator):
        """Test EXEC is forbidden even for L2."""
        with pytest.raises(ForbiddenAutonomyError, match="EXEC is forbidden"):
            orchestrator.select_model(layer_id="L2", autonomy_level=AutonomyLevel.EXEC)

    def test_layer_no_llm_support(self, orchestrator):
        """Test L5 (no LLM) raises."""
        with pytest.raises(InvalidModelError, match="has no LLM support"):
            orchestrator.select_model(layer_id="L5", autonomy_level=AutonomyLevel.RO)

    def test_layer_execution_forbidden(self, orchestrator):
        """Test L6 (execution) is forbidden."""
        with pytest.raises(InvalidModelError, match="has no LLM support"):
            orchestrator.select_model(layer_id="L6", autonomy_level=AutonomyLevel.RO)


class TestSoDValidation:
    """Test Separation of Duties validation."""

    def test_sod_pass_different_models(self, orchestrator):
        """Test SoD passes when primary != critic."""
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC
        )

        # L0: primary=gpt-5.2, critic=deepseek-r1
        assert selection.primary_model_id != selection.critic_model_id
        assert selection.sod_validated is True

    def test_sod_validation_internal(self, orchestrator):
        """Test internal _validate_sod method."""
        # Same model should raise
        with pytest.raises(SoDViolationError, match="SoD FAIL"):
            orchestrator._validate_sod("gpt-5.2", "gpt-5.2")

        # Different models should pass
        orchestrator._validate_sod("gpt-5.2", "deepseek-r1")  # No exception


class TestModelValidation:
    """Test model validation."""

    def test_validate_model_exists(self, orchestrator):
        """Test validating existing models."""
        # Should not raise
        orchestrator._validate_model("gpt-5.2-pro")
        orchestrator._validate_model("o3-deep-research")
        orchestrator._validate_model("deepseek-r1")

    def test_validate_model_unknown(self, orchestrator):
        """Test validating unknown model raises."""
        with pytest.raises(InvalidModelError, match="not found in registry"):
            orchestrator._validate_model("unknown-model-xyz")


class TestLayerValidation:
    """Test layer validation."""

    def test_validate_layer_valid(self, orchestrator):
        """Test validating valid layers."""
        # Should not raise
        for layer in ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]:
            orchestrator._validate_layer(layer)

    def test_validate_layer_invalid(self, orchestrator):
        """Test validating invalid layer raises."""
        with pytest.raises(InvalidLayerError, match="Invalid layer_id"):
            orchestrator._validate_layer("L99")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_multiple_fallbacks_L1(self, orchestrator):
        """Test L1 has multiple fallbacks."""
        selection = orchestrator.select_model(
            layer_id="L1", autonomy_level=AutonomyLevel.PROP
        )

        # L1 has multiple fallbacks
        assert len(selection.fallback_model_ids) >= 2
        assert "o4-mini-deep-research" in selection.fallback_model_ids
        assert "deepseek-r1" in selection.fallback_model_ids

    def test_selection_constraints_ignored_for_now(self, orchestrator):
        """Test selection constraints are accepted but not enforced yet."""
        constraints = SelectionConstraints(
            max_cost_per_1k_tokens=0.01, max_latency_ms=1000
        )

        # Should not raise (constraints not enforced in v0)
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC, constraints=constraints
        )

        assert selection.layer_id == "L0"

    def test_capability_scope_id_generation(self, orchestrator):
        """Test capability scope ID is generated correctly."""
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC
        )

        # L0 description: "Ops/Docs"
        assert "L0" in selection.capability_scope_id
        assert selection.capability_scope_id.startswith("L0_")

    def test_selection_timestamp_format(self, orchestrator):
        """Test selection timestamp is ISO8601."""
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC
        )

        # ISO8601 format
        assert "T" in selection.selection_timestamp
        assert selection.selection_timestamp.endswith("Z") or "+" in selection.selection_timestamp
