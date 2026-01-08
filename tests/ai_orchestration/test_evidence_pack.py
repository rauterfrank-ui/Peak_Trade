"""
Tests for Evidence Pack Validator

Tests cover:
- Evidence Pack creation and validation
- Mandatory fields enforcement
- SoD checks validation
- File I/O (JSON/TOML)
- Validator behavior (strict/lenient)
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from src.ai_orchestration.evidence_pack import (
    EvidencePackMetadata,
    EvidencePackValidator,
    create_evidence_pack,
    save_evidence_pack,
)
from src.ai_orchestration.models import (
    AutonomyLevel,
    CriticDecision,
    LayerRunMetadata,
    RunLogging,
    SoDCheckResult,
    SoDResult,
)


class TestEvidencePackCreation:
    """Test Evidence Pack creation and basic validation."""

    def test_create_minimal_evidence_pack(self):
        """Test creating Evidence Pack with minimal required fields."""
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-001",
            phase_id="Phase3B-Test",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
            description="Test Evidence Pack",
        )

        assert pack.evidence_pack_id == "EVP-TEST-001"
        assert pack.phase_id == "Phase3B-Test"
        assert pack.layer_id == "L0"
        assert pack.autonomy_level == AutonomyLevel.REC
        assert pack.registry_version == "1.0"
        assert pack.description == "Test Evidence Pack"
        assert pack.creation_timestamp  # Should be auto-generated

    def test_evidence_pack_validates_on_creation(self):
        """Test that Evidence Pack validates immediately on creation."""
        # Should succeed
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-002",
            phase_id="Phase3B",
            layer_id="L1",
            autonomy_level=AutonomyLevel.PROP,
            registry_version="1.0",
        )
        assert pack.evidence_pack_id == "EVP-TEST-002"

    def test_evidence_pack_rejects_exec_autonomy(self):
        """Test that EXEC autonomy level is rejected."""
        with pytest.raises(ValueError, match="EXEC is forbidden"):
            create_evidence_pack(
                evidence_pack_id="EVP-TEST-003",
                phase_id="Phase3B",
                layer_id="L0",
                autonomy_level=AutonomyLevel.EXEC,
                registry_version="1.0",
            )

    def test_evidence_pack_rejects_invalid_layer(self):
        """Test that invalid layer IDs are rejected."""
        pack = EvidencePackMetadata(
            evidence_pack_id="EVP-TEST-004",
            phase_id="Phase3B",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            registry_version="1.0",
            layer_id="LX",  # Invalid
            autonomy_level=AutonomyLevel.RO,
        )

        with pytest.raises(ValueError, match="Invalid layer_id"):
            pack.validate()


class TestEvidencePackMandatoryFields:
    """Test mandatory fields enforcement."""

    def test_evidence_pack_requires_id(self):
        """Test that evidence_pack_id is required."""
        pack = EvidencePackMetadata(
            evidence_pack_id="",  # Empty ID
            phase_id="Phase3B",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            registry_version="1.0",
            layer_id="L0",
            autonomy_level=AutonomyLevel.RO,
        )

        with pytest.raises(ValueError, match="evidence_pack_id is required"):
            pack.validate()

    def test_evidence_pack_requires_phase_id(self):
        """Test that phase_id is required."""
        pack = EvidencePackMetadata(
            evidence_pack_id="EVP-TEST-005",
            phase_id="",  # Empty phase ID
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            registry_version="1.0",
            layer_id="L0",
            autonomy_level=AutonomyLevel.RO,
        )

        with pytest.raises(ValueError, match="phase_id is required"):
            pack.validate()

    def test_evidence_pack_requires_registry_version(self):
        """Test that registry_version is required."""
        pack = EvidencePackMetadata(
            evidence_pack_id="EVP-TEST-006",
            phase_id="Phase3B",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            registry_version="",  # Empty registry version
            layer_id="L0",
            autonomy_level=AutonomyLevel.RO,
        )

        with pytest.raises(ValueError, match="registry_version is required"):
            pack.validate()

    def test_evidence_pack_requires_valid_timestamp(self):
        """Test that creation_timestamp must be valid ISO8601."""
        pack = EvidencePackMetadata(
            evidence_pack_id="EVP-TEST-007",
            phase_id="Phase3B",
            creation_timestamp="not-a-timestamp",  # Invalid timestamp
            registry_version="1.0",
            layer_id="L0",
            autonomy_level=AutonomyLevel.RO,
        )

        with pytest.raises(ValueError, match="Invalid creation_timestamp"):
            pack.validate()


class TestEvidencePackWithLayerRunMetadata:
    """Test Evidence Pack with Layer Run Metadata."""

    def test_evidence_pack_with_valid_layer_run_metadata(self):
        """Test Evidence Pack with valid LayerRunMetadata."""
        layer_run = LayerRunMetadata(
            layer_id="L0",
            layer_name="Ops/Docs Tooling",
            autonomy_level=AutonomyLevel.REC,
            primary_model_id="gpt-5-2",
            critic_model_id="deepseek-r1",
            capability_scope_id="L0_RO_REC_PROP",
            matrix_version="v1.0",
        )

        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-008",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )
        pack.layer_run_metadata = layer_run

        # Should validate successfully
        pack.validate()
        assert pack.layer_run_metadata.primary_model_id == "gpt-5-2"

    def test_evidence_pack_detects_sod_violation_in_layer_run(self):
        """Test that SoD violation in LayerRunMetadata is detected."""
        layer_run = LayerRunMetadata(
            layer_id="L0",
            layer_name="Ops/Docs Tooling",
            autonomy_level=AutonomyLevel.REC,
            primary_model_id="gpt-5-2",
            critic_model_id="gpt-5-2",  # SoD violation!
            capability_scope_id="L0_RO_REC_PROP",
            matrix_version="v1.0",
        )

        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-009",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )
        pack.layer_run_metadata = layer_run

        with pytest.raises(ValueError, match="SoD FAIL"):
            pack.validate()


class TestEvidencePackWithRunLogs:
    """Test Evidence Pack with Run Logs."""

    def test_evidence_pack_with_run_logs(self):
        """Test Evidence Pack with valid run logs."""
        run_log = RunLogging(
            run_id="run-001",
            prompt_hash="abc123",
            artifact_hash="def456",
            inputs_manifest=["input1.txt"],
            outputs_manifest=["output1.txt"],
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            model_id="gpt-5-2",
        )

        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-010",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )
        pack.run_logs = [run_log]

        pack.validate()
        assert len(pack.run_logs) == 1
        assert pack.run_logs[0].run_id == "run-001"

    def test_validator_detects_duplicate_run_ids(self):
        """Test that validator detects duplicate run IDs."""
        run_log_1 = RunLogging(
            run_id="run-duplicate",
            prompt_hash="abc123",
            artifact_hash="def456",
            inputs_manifest=["input1.txt"],
            outputs_manifest=["output1.txt"],
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            model_id="gpt-5-2",
        )

        run_log_2 = RunLogging(
            run_id="run-duplicate",  # Duplicate!
            prompt_hash="xyz789",
            artifact_hash="ghi012",
            inputs_manifest=["input2.txt"],
            outputs_manifest=["output2.txt"],
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            model_id="gpt-5-2",
        )

        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-011",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )
        pack.run_logs = [run_log_1, run_log_2]

        validator = EvidencePackValidator(strict=True)
        with pytest.raises(ValueError, match="Duplicate run_id"):
            validator.validate_pack(pack)


class TestEvidencePackWithSoDChecks:
    """Test Evidence Pack with SoD Checks."""

    def test_evidence_pack_with_valid_sod_check(self):
        """Test Evidence Pack with valid SoD check."""
        sod_check = SoDCheckResult(
            proposer_run_id="run-proposer-001",
            proposer_model_id="gpt-5-2",
            proposer_artifact_hash="abc123",
            critic_run_id="run-critic-001",
            critic_model_id="deepseek-r1",
            critic_artifact_hash="def456",
            critic_decision=CriticDecision.APPROVE,
            critic_rationale="All checks passed.",
            evidence_ids=["EVP-001", "EVP-002"],
        )

        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-012",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )
        pack.sod_checks = [sod_check]

        # Validate SoD check
        sod_check.validate()
        assert sod_check.sod_result == SoDResult.PASS

        # Validate Evidence Pack
        pack.validate()
        assert len(pack.sod_checks) == 1

    def test_evidence_pack_detects_failed_sod_check(self):
        """Test that validator detects failed SoD checks."""
        sod_check = SoDCheckResult(
            proposer_run_id="run-proposer-002",
            proposer_model_id="gpt-5-2",
            proposer_artifact_hash="abc123",
            critic_run_id="run-critic-002",
            critic_model_id="gpt-5-2",  # SoD violation!
            critic_artifact_hash="def456",
            critic_decision=CriticDecision.REJECT,
            critic_rationale="SoD violation detected.",
            evidence_ids=["EVP-003"],
            sod_result=SoDResult.FAIL,
        )

        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-013",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )
        pack.sod_checks = [sod_check]

        validator = EvidencePackValidator(strict=True)
        with pytest.raises(ValueError, match="SoD FAIL"):
            validator.validate_pack(pack)


class TestEvidencePackValidator:
    """Test EvidencePackValidator behavior."""

    def test_validator_strict_mode_fails_on_error(self):
        """Test that strict mode raises exception on validation error."""
        pack = EvidencePackMetadata(
            evidence_pack_id="",  # Invalid: empty ID
            phase_id="Phase3B",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            registry_version="1.0",
            layer_id="L0",
            autonomy_level=AutonomyLevel.RO,
        )

        validator = EvidencePackValidator(strict=True)
        with pytest.raises(ValueError, match="evidence_pack_id is required"):
            validator.validate_pack(pack)

    def test_validator_lenient_mode_collects_errors(self):
        """Test that lenient mode collects errors without raising."""
        pack = EvidencePackMetadata(
            evidence_pack_id="",  # Invalid: empty ID
            phase_id="Phase3B",
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            registry_version="1.0",
            layer_id="L0",
            autonomy_level=AutonomyLevel.RO,
        )

        validator = EvidencePackValidator(strict=False)
        result = validator.validate_pack(pack)

        assert result is False
        assert len(validator.errors) > 0
        assert "evidence_pack_id is required" in validator.errors[0]

    def test_validator_collects_warnings_for_missing_run_logs(self):
        """Test that validator warns about missing run logs."""
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-014",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )

        validator = EvidencePackValidator(strict=False)
        result = validator.validate_pack(pack)

        assert result is True  # No errors
        assert len(validator.warnings) > 0
        assert any("run logs" in w.lower() for w in validator.warnings)

    def test_validator_warns_about_failed_tests(self):
        """Test that validator warns about failed tests."""
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-015",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )
        pack.tests_total = 10
        pack.tests_passed = 7  # Some tests failed

        validator = EvidencePackValidator(strict=False)
        result = validator.validate_pack(pack)

        assert result is True  # No errors, just warnings
        assert len(validator.warnings) > 0
        assert any("not all tests passed" in w.lower() for w in validator.warnings)


class TestEvidencePackFileIO:
    """Test Evidence Pack file I/O."""

    def test_save_and_load_evidence_pack_json(self):
        """Test saving and loading Evidence Pack as JSON."""
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-016",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
            description="Test file I/O",
        )

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_pack.json"

            # Save
            save_evidence_pack(pack, filepath)
            assert filepath.exists()

            # Load and validate
            validator = EvidencePackValidator(strict=True)
            result = validator.validate_file(filepath)
            assert result is True

    def test_load_evidence_pack_with_all_fields(self):
        """Test loading Evidence Pack with all fields populated."""
        # Create pack with all fields
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-017",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )

        # Add LayerRunMetadata
        pack.layer_run_metadata = LayerRunMetadata(
            layer_id="L0",
            layer_name="Ops/Docs Tooling",
            autonomy_level=AutonomyLevel.REC,
            primary_model_id="gpt-5-2",
            critic_model_id="deepseek-r1",
            capability_scope_id="L0_RO_REC_PROP",
            matrix_version="v1.0",
        )

        # Add RunLogs
        pack.run_logs = [
            RunLogging(
                run_id="run-001",
                prompt_hash="abc123",
                artifact_hash="def456",
                inputs_manifest=["input1.txt"],
                outputs_manifest=["output1.txt"],
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                model_id="gpt-5-2",
            )
        ]

        # Add SoDChecks
        sod_check = SoDCheckResult(
            proposer_run_id="run-proposer-001",
            proposer_model_id="gpt-5-2",
            proposer_artifact_hash="abc123",
            critic_run_id="run-critic-001",
            critic_model_id="deepseek-r1",
            critic_artifact_hash="def456",
            critic_decision=CriticDecision.APPROVE,
            critic_rationale="All checks passed.",
            evidence_ids=["EVP-001"],
        )
        sod_check.validate()
        pack.sod_checks = [sod_check]

        # Add test results
        pack.tests_total = 10
        pack.tests_passed = 10

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_pack_full.json"

            # Save
            save_evidence_pack(pack, filepath)

            # Load and validate
            validator = EvidencePackValidator(strict=True)
            result = validator.validate_file(filepath)
            assert result is True

            # Check that all fields were preserved
            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["evidence_pack_id"] == "EVP-TEST-017"
            assert data["layer_run_metadata"]["primary_model_id"] == "gpt-5-2"
            assert len(data["run_logs"]) == 1
            assert len(data["sod_checks"]) == 1
            assert data["tests_passed"] == 10

    def test_validator_rejects_missing_file(self):
        """Test that validator raises error for missing file."""
        validator = EvidencePackValidator(strict=True)
        with pytest.raises(FileNotFoundError):
            validator.validate_file(Path("/nonexistent/file.json"))

    def test_validator_rejects_unsupported_format(self):
        """Test that validator rejects unsupported file formats."""
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-018",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_pack.yaml"

            with pytest.raises(ValueError, match="Unsupported file format"):
                save_evidence_pack(pack, filepath)


class TestEvidencePackToDictConversion:
    """Test Evidence Pack to_dict() conversion."""

    def test_evidence_pack_to_dict(self):
        """Test converting Evidence Pack to dictionary."""
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-019",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
            description="Test to_dict",
        )

        data = pack.to_dict()

        assert data["evidence_pack_id"] == "EVP-TEST-019"
        assert data["autonomy_level"] == "REC"
        assert "creation_timestamp" in data
        assert data["description"] == "Test to_dict"

    def test_evidence_pack_to_dict_with_nested_structures(self):
        """Test to_dict() with nested structures."""
        pack = create_evidence_pack(
            evidence_pack_id="EVP-TEST-020",
            phase_id="Phase3B",
            layer_id="L0",
            autonomy_level=AutonomyLevel.REC,
            registry_version="1.0",
        )

        # Add nested structures
        pack.layer_run_metadata = LayerRunMetadata(
            layer_id="L0",
            layer_name="Ops/Docs Tooling",
            autonomy_level=AutonomyLevel.REC,
            primary_model_id="gpt-5-2",
            critic_model_id="deepseek-r1",
            capability_scope_id="L0_RO_REC_PROP",
            matrix_version="v1.0",
        )

        data = pack.to_dict()

        assert "layer_run_metadata" in data
        assert data["layer_run_metadata"]["primary_model_id"] == "gpt-5-2"
        assert data["layer_run_metadata"]["critic_model_id"] == "deepseek-r1"
