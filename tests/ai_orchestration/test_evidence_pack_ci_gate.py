"""
Tests for Evidence Pack CI Gate (Phase 4A)

Tests cover:
- Evidence Pack Runtime Helper
- Auto-creation during Layer Runs
- CI validation script behavior
- Smoke run end-to-end flow

These tests are designed to be fast and deterministic for CI execution.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.ai_orchestration.evidence_pack import EvidencePackValidator
from src.ai_orchestration.evidence_pack_runtime import (
    EvidencePackRuntime,
    create_minimal_evidence_pack_for_run,
)
from src.ai_orchestration.models import AutonomyLevel


class TestEvidencePackRuntime:
    """Test Evidence Pack Runtime Helper."""

    def test_runtime_initialization(self):
        """Test runtime initialization with default output dir."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            assert runtime.output_dir.exists()
            assert runtime.output_dir == Path(tmpdir)
            assert len(runtime.active_runs) == 0

    def test_start_run_creates_pack(self):
        """Test that start_run creates Evidence Pack."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            pack = runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
                description="Test run",
            )

            assert pack.evidence_pack_id.startswith("EVP-L0-")
            assert pack.layer_id == "L0"
            assert pack.autonomy_level == AutonomyLevel.REC
            assert run_id in runtime.active_runs
            assert run_id in runtime.run_metadata

    def test_start_run_rejects_duplicate_run_id(self):
        """Test that start_run rejects duplicate run_id."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            # Attempt to start same run again
            with pytest.raises(ValueError, match="already active"):
                runtime.start_run(
                    run_id=run_id,
                    layer_id="L0",
                    autonomy_level=AutonomyLevel.REC,
                )

    def test_add_layer_run_metadata(self):
        """Test adding layer run metadata to active pack."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            runtime.add_layer_run_metadata(
                run_id=run_id,
                layer_name="Layer 0",
                primary_model_id="gpt-5-2-pro",
                critic_model_id="deepseek-r1",
                capability_scope_id="L0_RO_REC_PROP",
                matrix_version="v1.0",
            )

            pack = runtime.get_pack(run_id)
            assert pack.layer_run_metadata is not None
            assert pack.layer_run_metadata.layer_name == "Layer 0"
            assert pack.layer_run_metadata.primary_model_id == "gpt-5-2-pro"
            assert pack.layer_run_metadata.critic_model_id == "deepseek-r1"

    def test_add_run_log(self):
        """Test adding run log to active pack."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            runtime.add_run_log(
                run_id=run_id,
                log_run_id=f"log-{uuid.uuid4().hex[:8]}",
                prompt_hash="abc123",
                artifact_hash="def456",
                inputs_manifest=["input1.txt"],
                outputs_manifest=["output1.txt"],
                model_id="gpt-5-2-pro",
            )

            pack = runtime.get_pack(run_id)
            assert len(pack.run_logs) == 1
            assert pack.run_logs[0].prompt_hash == "abc123"
            assert pack.run_logs[0].artifact_hash == "def456"

    def test_finish_run_updates_status(self):
        """Test that finish_run updates run status."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            runtime.finish_run(run_id=run_id, status="success", tests_passed=5, tests_total=5)

            pack = runtime.get_pack(run_id)
            assert pack.validator_run is True
            assert pack.tests_passed == 5
            assert pack.tests_total == 5

            assert runtime.run_metadata[run_id]["status"] == "success"
            assert runtime.run_metadata[run_id]["finished_at"] is not None

    def test_save_pack_creates_files(self):
        """Test that save_pack creates Evidence Pack file."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )
            runtime.finish_run(run_id=run_id, status="success")

            pack_path = runtime.save_pack(run_id=run_id)

            assert pack_path.exists()
            assert pack_path.name == "evidence_pack.json"
            assert (pack_path.parent / "run_metadata.json").exists()

    def test_save_pack_validates(self):
        """Test that saved pack validates successfully."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )
            runtime.finish_run(run_id=run_id, status="success")

            pack_path = runtime.save_pack(run_id=run_id)

            # Validate saved pack
            validator = EvidencePackValidator(strict=True)
            result = validator.validate_file(pack_path)

            assert result is True

    def test_git_sha_tracking(self):
        """Test that git SHA is tracked in run metadata."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            # Git SHA should be either real SHA or "local-dev"
            git_sha = runtime.run_metadata[run_id]["git_sha"]
            assert git_sha is not None
            assert len(git_sha) > 0

    def test_config_fingerprint_tracking(self):
        """Test that config fingerprint is tracked."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            # Config fingerprint should be present (SHA256 hex)
            fingerprint = runtime.run_metadata[run_id]["config_fingerprint"]
            assert fingerprint is not None
            assert len(fingerprint) == 64  # SHA256 hex = 64 chars

    def test_track_artifact(self):
        """Test artifact tracking."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            runtime.track_artifact(run_id=run_id, artifact_path=Path("output.txt"))
            runtime.track_artifact(run_id=run_id, artifact_path=Path("result.json"))

            artifacts = runtime.run_metadata[run_id]["artifacts"]
            assert len(artifacts) == 2
            assert "output.txt" in artifacts
            assert "result.json" in artifacts

    def test_cleanup_run(self):
        """Test cleanup removes run from active runs."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )

            assert run_id in runtime.active_runs
            runtime.cleanup_run(run_id=run_id)
            assert run_id not in runtime.active_runs
            assert run_id not in runtime.run_metadata


class TestCreateMinimalEvidencePack:
    """Test convenience function for minimal Evidence Pack creation."""

    def test_create_minimal_evidence_pack_for_run(self):
        """Test that convenience function creates and saves pack."""
        with TemporaryDirectory() as tmpdir:
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            pack_path = create_minimal_evidence_pack_for_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
                output_dir=Path(tmpdir),
                description="Test pack",
            )

            assert pack_path.exists()
            assert pack_path.name == "evidence_pack.json"

            # Validate saved pack
            validator = EvidencePackValidator(strict=True)
            result = validator.validate_file(pack_path)
            assert result is True


class TestEvidencePackCIGateEndToEnd:
    """End-to-end tests for CI gate flow."""

    def test_ci_gate_flow_minimal(self):
        """Test minimal CI gate flow: create pack, validate pack."""
        with TemporaryDirectory() as tmpdir:
            # Step 1: Create Evidence Pack
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"ci-test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
                phase_id="ci-gate-test",
                description="CI gate test pack",
            )

            runtime.add_layer_run_metadata(
                run_id=run_id,
                layer_name="Layer 0",
                primary_model_id="gpt-5-2-pro",
                critic_model_id="deepseek-r1",
                capability_scope_id="L0_CI_TEST",
                matrix_version="v1.0",
            )

            runtime.finish_run(run_id=run_id, status="success", tests_passed=1, tests_total=1)
            pack_path = runtime.save_pack(run_id=run_id)

            # Step 2: Validate Evidence Pack (CI gate)
            validator = EvidencePackValidator(strict=True)
            result = validator.validate_file(pack_path)

            assert result is True
            assert len(validator.errors) == 0

    def test_ci_gate_flow_with_invalid_pack(self):
        """Test CI gate flow with invalid pack (should fail)."""
        with TemporaryDirectory() as tmpdir:
            # Create invalid pack (missing required fields)
            pack_path = Path(tmpdir) / "invalid_pack.json"
            with open(pack_path, "w") as f:
                json.dump({"invalid": "pack"}, f)

            # Validate should fail
            validator = EvidencePackValidator(strict=True)
            with pytest.raises(Exception):
                validator.validate_file(pack_path)

    def test_ci_gate_flow_multiple_packs(self):
        """Test CI gate flow with multiple packs."""
        with TemporaryDirectory() as tmpdir:
            # Create multiple packs
            pack_paths = []
            for i in range(3):
                runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
                run_id = f"ci-test-{i}-{uuid.uuid4().hex[:8]}"

                runtime.start_run(
                    run_id=run_id,
                    layer_id="L0",
                    autonomy_level=AutonomyLevel.REC,
                )
                runtime.finish_run(run_id=run_id, status="success")
                pack_path = runtime.save_pack(run_id=run_id)
                pack_paths.append(pack_path)

            # Validate all packs
            validator = EvidencePackValidator(strict=True)
            for pack_path in pack_paths:
                result = validator.validate_file(pack_path)
                assert result is True


class TestEvidencePackRuntimeValidatorVersion:
    """Test validator version tracking."""

    def test_validator_version_present_in_metadata(self):
        """Test that validator version is present in run metadata."""
        with TemporaryDirectory() as tmpdir:
            runtime = EvidencePackRuntime(output_dir=Path(tmpdir))
            run_id = f"test-{uuid.uuid4().hex[:8]}"

            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.REC,
            )
            runtime.finish_run(run_id=run_id, status="success")
            pack_path = runtime.save_pack(run_id=run_id)

            # Load pack and check structure
            with open(pack_path) as f:
                pack_data = json.load(f)

            # Evidence Pack should have registry_version (validator version)
            assert "registry_version" in pack_data
            assert pack_data["registry_version"] == "1.0"
