"""
Evidence Pack Validator for AI Autonomy

Validates Evidence Packs against mandatory schema requirements.

Evidence Packs are structured records that document:
- Layer Run metadata
- Model selections
- Verification results
- SoD checks
- Audit trail

Reference:
- docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md
- docs/ops/PHASE3_VERIFICATION_EVIDENCE_PACK.md
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomli as toml
except ImportError:
    import tomllib as toml

from .models import (
    AutonomyLevel,
    CriticDecision,
    LayerRunMetadata,
    RunLogging,
    SoDCheckResult,
    SoDResult,
)


@dataclass
class EvidencePackMetadata:
    """
    Metadata for an Evidence Pack.

    Every Evidence Pack MUST include this metadata.
    """

    evidence_pack_id: str  # Unique ID (e.g., EVP-PHASE3B-20260108)
    phase_id: str  # Phase identifier (e.g., "Phase3B", "L0-RO-Run-42")
    creation_timestamp: str  # ISO8601
    registry_version: str  # Model registry version used
    layer_id: str  # L0-L6
    autonomy_level: AutonomyLevel

    # Evidence content
    layer_run_metadata: Optional[LayerRunMetadata] = None
    run_logs: List[RunLogging] = field(default_factory=list)
    sod_checks: List[SoDCheckResult] = field(default_factory=list)

    # Verification results
    validator_run: bool = False
    tests_passed: int = 0
    tests_total: int = 0

    # Additional metadata
    description: str = ""
    related_prs: List[str] = field(default_factory=list)
    related_evidence_packs: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """
        Validate mandatory fields.

        Raises:
            ValueError: If validation fails
        """
        # Evidence Pack ID must be present and non-empty
        if not self.evidence_pack_id or not self.evidence_pack_id.strip():
            raise ValueError("evidence_pack_id is required and must not be empty")

        # Phase ID must be present
        if not self.phase_id or not self.phase_id.strip():
            raise ValueError("phase_id is required and must not be empty")

        # Layer ID must be valid
        valid_layers = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
        if self.layer_id not in valid_layers:
            raise ValueError(f"Invalid layer_id: {self.layer_id}")

        # Autonomy level must be valid
        if not isinstance(self.autonomy_level, AutonomyLevel):
            raise ValueError(f"Invalid autonomy_level: {self.autonomy_level}")

        # EXEC is forbidden
        if self.autonomy_level == AutonomyLevel.EXEC:
            raise ValueError(
                f"EXEC is forbidden (layer {self.layer_id}). "
                "Execution requires explicit Evidence Packs + CodeGate + Go/NoGo."
            )

        # Registry version must be present
        if not self.registry_version or not self.registry_version.strip():
            raise ValueError("registry_version is required and must not be empty")

        # Creation timestamp must be valid ISO8601
        try:
            datetime.fromisoformat(self.creation_timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid creation_timestamp: {self.creation_timestamp}. Must be ISO8601."
            )

        # If LayerRunMetadata is present, validate it
        if self.layer_run_metadata:
            self.layer_run_metadata.validate()

        # If SoDChecks are present, validate them
        for sod_check in self.sod_checks:
            sod_check.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "evidence_pack_id": self.evidence_pack_id,
            "phase_id": self.phase_id,
            "creation_timestamp": self.creation_timestamp,
            "registry_version": self.registry_version,
            "layer_id": self.layer_id,
            "autonomy_level": self.autonomy_level.value,
            "validator_run": self.validator_run,
            "tests_passed": self.tests_passed,
            "tests_total": self.tests_total,
            "description": self.description,
            "related_prs": self.related_prs,
            "related_evidence_packs": self.related_evidence_packs,
        }

        # Add nested structures if present
        if self.layer_run_metadata:
            result["layer_run_metadata"] = asdict(self.layer_run_metadata)

        if self.run_logs:
            result["run_logs"] = [log.to_dict() for log in self.run_logs]

        if self.sod_checks:
            result["sod_checks"] = [check.to_dict() for check in self.sod_checks]

        return result


class EvidencePackValidator:
    """
    Validator for Evidence Packs.

    Validates Evidence Packs against mandatory schema requirements.
    """

    def __init__(self, strict: bool = True):
        """
        Initialize validator.

        Args:
            strict: If True, fail on any validation error.
                   If False, collect warnings but don't fail.
        """
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_pack(self, pack: EvidencePackMetadata) -> bool:
        """
        Validate an Evidence Pack.

        Args:
            pack: Evidence Pack to validate

        Returns:
            True if validation passed, False otherwise

        Raises:
            ValueError: If strict=True and validation fails
        """
        self.errors = []
        self.warnings = []

        try:
            pack.validate()
        except ValueError as e:
            self.errors.append(f"Validation error: {e}")
            if self.strict:
                raise ValueError(f"Evidence Pack validation failed: {e}") from e
            return False

        # Additional validation rules
        self._validate_run_logs(pack)
        self._validate_sod_checks(pack)
        self._validate_test_results(pack)

        if self.errors and self.strict:
            raise ValueError(f"Evidence Pack validation failed: {'; '.join(self.errors)}")

        return len(self.errors) == 0

    def _validate_run_logs(self, pack: EvidencePackMetadata) -> None:
        """Validate run logs in Evidence Pack."""
        if not pack.run_logs:
            self.warnings.append(
                "No run logs present. Evidence Pack should include run logs for audit trail."
            )
            return

        # Check for duplicate run IDs
        run_ids = [log.run_id for log in pack.run_logs]
        if len(run_ids) != len(set(run_ids)):
            self.errors.append(
                "Duplicate run_id detected in run_logs. Each run must have unique ID."
            )

    def _validate_sod_checks(self, pack: EvidencePackMetadata) -> None:
        """Validate SoD checks in Evidence Pack."""
        if not pack.sod_checks:
            self.warnings.append(
                "No SoD checks present. Evidence Pack should include SoD checks for audit trail."
            )
            return

        # Check that all SoD checks passed
        failed_sod_checks = [
            check for check in pack.sod_checks if check.sod_result == SoDResult.FAIL
        ]
        if failed_sod_checks:
            self.errors.append(
                f"SoD checks failed: {len(failed_sod_checks)}/{len(pack.sod_checks)} checks failed."
            )

    def _validate_test_results(self, pack: EvidencePackMetadata) -> None:
        """Validate test results in Evidence Pack."""
        if pack.tests_total > 0 and pack.tests_passed < pack.tests_total:
            self.warnings.append(f"Not all tests passed: {pack.tests_passed}/{pack.tests_total}")

        if pack.tests_total > 0 and pack.tests_passed == 0:
            self.errors.append("No tests passed. Evidence Pack must have passing tests.")

    def validate_file(self, filepath: Path) -> bool:
        """
        Validate an Evidence Pack from a file.

        Args:
            filepath: Path to Evidence Pack file (JSON or TOML)

        Returns:
            True if validation passed, False otherwise
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Evidence Pack file not found: {filepath}")

        # Load file based on extension
        suffix = filepath.suffix.lower()
        if suffix == ".json":
            with open(filepath, "r") as f:
                data = json.load(f)
        elif suffix == ".toml":
            with open(filepath, "rb") as f:
                data = toml.load(f)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .json or .toml")

        # Convert to EvidencePackMetadata
        pack = self._dict_to_pack(data)

        # Validate
        return self.validate_pack(pack)

    def _dict_to_pack(self, data: Dict[str, Any]) -> EvidencePackMetadata:
        """
        Convert dictionary to EvidencePackMetadata.

        Args:
            data: Dictionary representation of Evidence Pack

        Returns:
            EvidencePackMetadata instance
        """
        # Extract autonomy level
        autonomy_level = AutonomyLevel(data["autonomy_level"])

        # Extract LayerRunMetadata if present
        layer_run_metadata = None
        if "layer_run_metadata" in data and data["layer_run_metadata"]:
            lrm_data = data["layer_run_metadata"]
            layer_run_metadata = LayerRunMetadata(
                layer_id=lrm_data["layer_id"],
                layer_name=lrm_data["layer_name"],
                autonomy_level=AutonomyLevel(lrm_data["autonomy_level"]),
                primary_model_id=lrm_data["primary_model_id"],
                critic_model_id=lrm_data["critic_model_id"],
                capability_scope_id=lrm_data["capability_scope_id"],
                matrix_version=lrm_data["matrix_version"],
                fallback_model_id=lrm_data.get("fallback_model_id"),
            )

        # Extract RunLogs if present
        run_logs = []
        if "run_logs" in data and data["run_logs"]:
            for log_data in data["run_logs"]:
                run_log = RunLogging(
                    run_id=log_data["run_id"],
                    prompt_hash=log_data["prompt_hash"],
                    artifact_hash=log_data["artifact_hash"],
                    inputs_manifest=log_data["inputs_manifest"],
                    outputs_manifest=log_data["outputs_manifest"],
                    timestamp_utc=log_data["timestamp_utc"],
                    model_id=log_data["model_id"],
                )
                run_logs.append(run_log)

        # Extract SoDCheckResults if present
        sod_checks = []
        if "sod_checks" in data and data["sod_checks"]:
            for sod_data in data["sod_checks"]:
                sod_check = SoDCheckResult(
                    proposer_run_id=sod_data["proposer_run_id"],
                    proposer_model_id=sod_data["proposer_model_id"],
                    proposer_artifact_hash=sod_data["proposer_artifact_hash"],
                    critic_run_id=sod_data["critic_run_id"],
                    critic_model_id=sod_data["critic_model_id"],
                    critic_artifact_hash=sod_data["critic_artifact_hash"],
                    sod_result=(
                        SoDResult(sod_data["sod_result"]) if sod_data.get("sod_result") else None
                    ),
                    sod_check_timestamp=sod_data.get("sod_check_timestamp", ""),
                    critic_decision=(
                        CriticDecision(sod_data["critic_decision"])
                        if sod_data.get("critic_decision")
                        else None
                    ),
                    critic_rationale=sod_data.get("critic_rationale", ""),
                    evidence_ids=sod_data.get("evidence_ids", []),
                    related_evidence_packs=sod_data.get("related_evidence_packs", []),
                )
                sod_checks.append(sod_check)

        # Create EvidencePackMetadata
        pack = EvidencePackMetadata(
            evidence_pack_id=data["evidence_pack_id"],
            phase_id=data["phase_id"],
            creation_timestamp=data["creation_timestamp"],
            registry_version=data["registry_version"],
            layer_id=data["layer_id"],
            autonomy_level=autonomy_level,
            layer_run_metadata=layer_run_metadata,
            run_logs=run_logs,
            sod_checks=sod_checks,
            validator_run=data.get("validator_run", False),
            tests_passed=data.get("tests_passed", 0),
            tests_total=data.get("tests_total", 0),
            description=data.get("description", ""),
            related_prs=data.get("related_prs", []),
            related_evidence_packs=data.get("related_evidence_packs", []),
        )

        return pack


def create_evidence_pack(
    evidence_pack_id: str,
    phase_id: str,
    layer_id: str,
    autonomy_level: AutonomyLevel,
    registry_version: str,
    description: str = "",
) -> EvidencePackMetadata:
    """
    Create a new Evidence Pack with minimal required fields.

    Args:
        evidence_pack_id: Unique ID for Evidence Pack
        phase_id: Phase identifier
        layer_id: Layer ID (L0-L6)
        autonomy_level: Autonomy level
        registry_version: Model registry version
        description: Optional description

    Returns:
        EvidencePackMetadata instance
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    pack = EvidencePackMetadata(
        evidence_pack_id=evidence_pack_id,
        phase_id=phase_id,
        creation_timestamp=timestamp,
        registry_version=registry_version,
        layer_id=layer_id,
        autonomy_level=autonomy_level,
        description=description,
    )

    # Validate immediately
    pack.validate()

    return pack


def save_evidence_pack(pack: EvidencePackMetadata, filepath: Path) -> None:
    """
    Save Evidence Pack to file.

    Args:
        pack: Evidence Pack to save
        filepath: Target file path (.json or .toml)
    """
    # Validate before saving
    pack.validate()

    # Convert to dictionary
    data = pack.to_dict()

    # Save based on extension
    suffix = filepath.suffix.lower()
    if suffix == ".json":
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .json for saving.")
