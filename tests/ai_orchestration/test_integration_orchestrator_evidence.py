"""
Integration Tests: Orchestrator + Evidence Pack

Tests end-to-end workflow:
1. Orchestrator selects models
2. Evidence Pack captures the selection
3. Evidence Pack validates correctly
"""

import os
import pytest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from src.ai_orchestration.orchestrator import Orchestrator
from src.ai_orchestration.evidence_pack import (
    EvidencePackMetadata,
    EvidencePackValidator,
    create_evidence_pack,
    save_evidence_pack,
)
from src.ai_orchestration.models import (
    AutonomyLevel,
    LayerRunMetadata,
    RunLogging,
)


class TestOrchestratorEvidencePackIntegration:
    """Integration tests for Orchestrator + Evidence Pack."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        # Enable orchestrator for tests
        os.environ["ORCHESTRATOR_ENABLED"] = "true"
        orch = Orchestrator()
        yield orch
        # Cleanup
        if "ORCHESTRATOR_ENABLED" in os.environ:
            del os.environ["ORCHESTRATOR_ENABLED"]

    def test_orchestrator_selection_to_evidence_pack(self, orchestrator):
        """Test capturing orchestrator selection in Evidence Pack."""
        # Step 1: Use orchestrator to select models
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC
        )

        assert selection.primary_model_id
        assert selection.critic_model_id
        assert selection.sod_validated is True

        # Step 2: Create Evidence Pack from selection
        pack = create_evidence_pack(
            evidence_pack_id="EVP-INTEGRATION-001",
            phase_id="IntegrationTest",
            layer_id=selection.layer_id,
            autonomy_level=selection.autonomy_level,
            registry_version=selection.registry_version,
            description="Integration test: Orchestrator → Evidence Pack",
        )

        # Step 3: Add LayerRunMetadata based on selection
        pack.layer_run_metadata = LayerRunMetadata(
            layer_id=selection.layer_id,
            layer_name="Ops/Docs Tooling",
            autonomy_level=selection.autonomy_level,
            primary_model_id=selection.primary_model_id,
            critic_model_id=selection.critic_model_id,
            capability_scope_id=selection.capability_scope_id,
            matrix_version=selection.registry_version,
            fallback_model_id=(
                selection.fallback_model_ids[0]
                if selection.fallback_model_ids
                else None
            ),
        )

        # Step 4: Validate Evidence Pack
        pack.validate()

        # Assertions
        assert pack.layer_run_metadata.primary_model_id == selection.primary_model_id
        assert pack.layer_run_metadata.critic_model_id == selection.critic_model_id
        assert pack.layer_run_metadata.primary_model_id != pack.layer_run_metadata.critic_model_id

    def test_full_workflow_with_run_logs(self, orchestrator):
        """Test full workflow: Orchestrator → Run Logs → Evidence Pack."""
        # Step 1: Select models
        selection = orchestrator.select_model(
            layer_id="L2", autonomy_level=AutonomyLevel.PROP
        )

        # Step 2: Create Evidence Pack
        pack = create_evidence_pack(
            evidence_pack_id="EVP-INTEGRATION-002",
            phase_id="IntegrationTest-Full",
            layer_id=selection.layer_id,
            autonomy_level=selection.autonomy_level,
            registry_version=selection.registry_version,
        )

        # Step 3: Add LayerRunMetadata
        pack.layer_run_metadata = LayerRunMetadata(
            layer_id=selection.layer_id,
            layer_name="Macro Regime Forecasts",
            autonomy_level=selection.autonomy_level,
            primary_model_id=selection.primary_model_id,
            critic_model_id=selection.critic_model_id,
            capability_scope_id=selection.capability_scope_id,
            matrix_version=selection.registry_version,
        )

        # Step 4: Simulate run logs
        run_log = RunLogging(
            run_id="run-integration-001",
            prompt_hash="abc123def456",
            artifact_hash="ghi789jkl012",
            inputs_manifest=["config/macro_regimes/regime_default.toml"],
            outputs_manifest=["reports/macro_regime_forecast.json"],
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            model_id=selection.primary_model_id,
        )
        pack.run_logs = [run_log]

        # Step 5: Add test results
        pack.tests_total = 10
        pack.tests_passed = 10
        pack.validator_run = True

        # Step 6: Validate
        validator = EvidencePackValidator(strict=True)
        result = validator.validate_pack(pack)
        assert result is True

        # Step 7: Save to file
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "integration_evidence_pack.json"
            save_evidence_pack(pack, filepath)

            # Step 8: Load and re-validate
            validator2 = EvidencePackValidator(strict=True)
            result2 = validator2.validate_file(filepath)
            assert result2 is True

    def test_orchestrator_multiple_layers_to_evidence_packs(self, orchestrator):
        """Test creating Evidence Packs for multiple layer selections."""
        layers = ["L0", "L1", "L2"]
        packs = []

        for i, layer_id in enumerate(layers):
            # Select models for layer
            selection = orchestrator.select_model(
                layer_id=layer_id, autonomy_level=AutonomyLevel.REC
            )

            # Create Evidence Pack
            pack = create_evidence_pack(
                evidence_pack_id=f"EVP-INTEGRATION-MULTI-{i + 1}",
                phase_id=f"IntegrationTest-{layer_id}",
                layer_id=selection.layer_id,
                autonomy_level=selection.autonomy_level,
                registry_version=selection.registry_version,
            )

            # Add LayerRunMetadata
            pack.layer_run_metadata = LayerRunMetadata(
                layer_id=selection.layer_id,
                layer_name=f"Layer {layer_id}",
                autonomy_level=selection.autonomy_level,
                primary_model_id=selection.primary_model_id,
                critic_model_id=selection.critic_model_id,
                capability_scope_id=selection.capability_scope_id,
                matrix_version=selection.registry_version,
            )

            # Validate
            pack.validate()
            packs.append(pack)

        # Assertions
        assert len(packs) == 3
        for pack in packs:
            assert pack.layer_run_metadata
            assert pack.layer_run_metadata.primary_model_id != pack.layer_run_metadata.critic_model_id

    def test_orchestrator_evidence_pack_preserves_explainability(self, orchestrator):
        """Test that Evidence Pack preserves orchestrator explainability."""
        # Select models
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.RO
        )

        # Create Evidence Pack
        pack = create_evidence_pack(
            evidence_pack_id="EVP-INTEGRATION-EXPLAIN-001",
            phase_id="IntegrationTest-Explainability",
            layer_id=selection.layer_id,
            autonomy_level=selection.autonomy_level,
            registry_version=selection.registry_version,
            description=f"Selection reason: {selection.selection_reason}",
        )

        # Validate
        pack.validate()

        # Check that explainability is preserved
        assert selection.selection_reason in pack.description
        assert "registry" in pack.description.lower() or "layer" in pack.description.lower()

    def test_evidence_pack_catches_orchestrator_sod_violation(self, orchestrator):
        """Test that Evidence Pack catches SoD violations from orchestrator."""
        # Normal selection (should pass SoD)
        selection = orchestrator.select_model(
            layer_id="L0", autonomy_level=AutonomyLevel.REC
        )

        # Create Evidence Pack with INTENTIONALLY BROKEN LayerRunMetadata
        pack = create_evidence_pack(
            evidence_pack_id="EVP-INTEGRATION-SOD-FAIL",
            phase_id="IntegrationTest-SoDViolation",
            layer_id=selection.layer_id,
            autonomy_level=selection.autonomy_level,
            registry_version=selection.registry_version,
        )

        # Manually break SoD (for testing)
        pack.layer_run_metadata = LayerRunMetadata(
            layer_id=selection.layer_id,
            layer_name="Ops/Docs Tooling",
            autonomy_level=selection.autonomy_level,
            primary_model_id="gpt-5-2",
            critic_model_id="gpt-5-2",  # SoD violation!
            capability_scope_id=selection.capability_scope_id,
            matrix_version=selection.registry_version,
        )

        # Validate should fail
        with pytest.raises(ValueError, match="SoD FAIL"):
            pack.validate()
