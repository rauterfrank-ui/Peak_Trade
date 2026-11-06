"""
AI Orchestration Data Models

Implements the Mandatory Fields Schema from:
docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md

All Layer Runs and Evidence Packs MUST use these dataclasses.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class AutonomyLevel(str, Enum):
    """Autonomy levels (from Layer Map Matrix)."""

    RO = "RO"  # Read-Only
    REC = "REC"  # Recommend
    PROP = "PROP"  # Propose
    EXEC = "EXEC"  # Execute (FORBIDDEN)


class SoDResult(str, Enum):
    """Separation of Duties check result."""

    PASS = "PASS"
    FAIL = "FAIL"


class CriticDecision(str, Enum):
    """Critic decision outcomes."""

    APPROVE = "APPROVE"
    APPROVE_WITH_CHANGES = "APPROVE_WITH_CHANGES"
    REJECT = "REJECT"


@dataclass
class LayerRunMetadata:
    """
    Mandatory metadata for every Layer Run.

    Reference: docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md
    """

    # Layer Information (from Matrix)
    layer_id: str  # L0-L6
    layer_name: str
    autonomy_level: AutonomyLevel

    # Model Assignment (from Matrix)
    primary_model_id: str
    critic_model_id: str

    # Capability Scope
    capability_scope_id: str

    # Versioning
    matrix_version: str  # e.g., "v1.0"

    # Optional fields (must come after required fields)
    fallback_model_id: Optional[str] = None

    def validate(self) -> None:
        """
        Validate mandatory fields.

        Raises:
            AssertionError: If validation fails
        """
        # Layer ID must be L0-L6
        valid_layers = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
        assert self.layer_id in valid_layers, f"Invalid layer_id: {self.layer_id}"

        # EXEC is forbidden
        if self.autonomy_level == AutonomyLevel.EXEC:
            raise ValueError(
                f"EXEC is forbidden (layer {self.layer_id}). "
                "Execution requires explicit Evidence Packs + CodeGate + Go/NoGo."
            )

        # SoD: Primary != Critic
        if self.primary_model_id == self.critic_model_id:
            raise ValueError(
                f"SoD FAIL: primary_model_id == critic_model_id ({self.primary_model_id}). "
                "Proposer and Critic MUST be different models."
            )

        # Matrix version must be present
        assert self.matrix_version, "matrix_version is required"


@dataclass
class CapabilityScopeMetadata:
    """
    Capability Scope enforcement metadata.

    Defines what a Layer can access (inputs/outputs/tooling) and what is forbidden.
    """

    capability_scope_id: str
    inputs_allowed: List[str]
    outputs_allowed: List[str]
    tooling_allowed: List[str]  # ["none", "files", "web", "code-interpreter"]
    forbidden: List[str]

    def validate_input(self, input_path: str) -> bool:
        """Check if input is allowed by capability scope."""
        # Simplified: exact match or glob pattern match
        return any(pattern in input_path for pattern in self.inputs_allowed)

    def validate_output(self, output_type: str) -> bool:
        """Check if output type is allowed by capability scope."""
        return output_type in self.outputs_allowed

    def validate_tooling(self, tool: str) -> bool:
        """Check if tool is allowed by capability scope."""
        return tool in self.tooling_allowed


@dataclass
class RunLogging:
    """
    Mandatory logging fields per run.

    All Layer Runs MUST log these fields to audit trail.
    """

    run_id: str  # Unique identifier (UUID)
    prompt_hash: str  # SHA256 of prompt
    artifact_hash: str  # SHA256 of output
    inputs_manifest: List[str]  # Actual inputs used
    outputs_manifest: List[str]  # Outputs generated
    timestamp_utc: str  # ISO8601 timestamp
    model_id: str  # Actual model used (Primary or Fallback)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON logging."""
        return {
            "run_id": self.run_id,
            "prompt_hash": self.prompt_hash,
            "artifact_hash": self.artifact_hash,
            "inputs_manifest": self.inputs_manifest,
            "outputs_manifest": self.outputs_manifest,
            "timestamp_utc": self.timestamp_utc,
            "model_id": self.model_id,
        }


@dataclass
class SoDCheckResult:
    """
    Separation of Duties check result.

    Validates that Proposer != Critic and Critic provided valid decision + rationale.
    """

    # Proposer
    proposer_run_id: str
    proposer_model_id: str
    proposer_artifact_hash: str

    # Critic
    critic_run_id: str
    critic_model_id: str
    critic_artifact_hash: str

    # SoD Result (set by validate())
    sod_result: Optional[SoDResult] = None
    sod_check_timestamp: str = ""  # ISO8601

    # Critic Output
    critic_decision: Optional[CriticDecision] = None
    critic_rationale: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    related_evidence_packs: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """
        Validate SoD check.

        SoD PASS criteria:
        1. proposer_model_id != critic_model_id
        2. critic_decision in {APPROVE, APPROVE_WITH_CHANGES, REJECT}
        3. critic_rationale is not empty
        4. evidence_ids is not empty

        Raises:
            ValueError: If SoD check fails
        """
        # Rule 1: Proposer != Critic
        if self.proposer_model_id == self.critic_model_id:
            self.sod_result = SoDResult.FAIL
            raise ValueError(
                f"SoD FAIL: Proposer == Critic ({self.proposer_model_id}). "
                "Proposer and Critic MUST be different models."
            )

        # Rule 2: Valid Critic Decision
        if self.critic_decision not in [
            CriticDecision.APPROVE,
            CriticDecision.APPROVE_WITH_CHANGES,
            CriticDecision.REJECT,
        ]:
            self.sod_result = SoDResult.FAIL
            raise ValueError(
                f"SoD FAIL: Invalid critic_decision ({self.critic_decision}). "
                "Must be APPROVE, APPROVE_WITH_CHANGES, or REJECT."
            )

        # Rule 3: Rationale not empty
        if not self.critic_rationale or not self.critic_rationale.strip():
            self.sod_result = SoDResult.FAIL
            raise ValueError(
                "SoD FAIL: Empty critic_rationale. Critic MUST provide rationale for decision."
            )

        # Rule 4: Evidence IDs not empty
        if not self.evidence_ids:
            self.sod_result = SoDResult.FAIL
            raise ValueError(
                "SoD FAIL: No evidence_ids. Critic MUST reference Evidence IDs or run_ids."
            )

        # All checks passed
        self.sod_result = SoDResult.PASS

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "proposer_run_id": self.proposer_run_id,
            "proposer_model_id": self.proposer_model_id,
            "proposer_artifact_hash": self.proposer_artifact_hash,
            "critic_run_id": self.critic_run_id,
            "critic_model_id": self.critic_model_id,
            "critic_artifact_hash": self.critic_artifact_hash,
            "sod_result": self.sod_result.value if self.sod_result else None,
            "sod_check_timestamp": self.sod_check_timestamp,
            "critic_decision": self.critic_decision.value if self.critic_decision else None,
            "critic_rationale": self.critic_rationale,
            "evidence_ids": self.evidence_ids,
            "related_evidence_packs": self.related_evidence_packs,
        }
