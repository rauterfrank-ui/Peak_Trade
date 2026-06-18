"""Bounded Futures Testnet durable run primary evidence completion integration (v0).

Deterministic, offline, explicit-input-only fail-closed integration composing PE-31
reconciliation-review lifecycle proof, PE-21 primary evidence reconciliation proof,
PE-22 risk/killswitch/flatten lifecycle proof, PE-23 capital-slot ratchet/release lifecycle
proof, PE-24 pilot-envelope lifecycle proof, PE-25 operator-closure lifecycle proof,
PE-35 handoff staleness/revocation/recovery boundary proof, PE-37 operator review chain
durable evidence traceability boundary proof,
PE-16 durable archive identity, SECTION5 Gap 4 output/reporter completion
semantics, and SECTION5 Gap 2a.1 primary-evidence enforcement completion semantics with
bounded durable run-root artifact/manifest requirements.

Static integration only — no run start, evidence write, archive I/O, manifest I/O,
network, testnet, runtime, credentials, orders, evidence acceptance, operative completion,
operative reconciliation, operative risk evaluation, KillSwitch trigger, flatten,
operative capital-slot ratchet/release/reallocation/reserve top-up,
operative pilot-envelope execution or pilot start, operative recovery, resume, retry,
replay, state mutation, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    MANIFEST_FILENAME,
    is_under_tmp,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    ARTIFACT_RECONCILIATION_RESULT,
    CONTRACT_VERSION as PE21_CONTRACT_VERSION,
    ManifestEntry,
    ReconciliationPrimaryEvidenceIntegrationInput,
    compute_integration_input_digest as compute_pe21_integration_input_digest,
    compute_integration_proof_digest as compute_pe21_integration_proof_digest,
    compute_manifest_digest,
    evaluate_position_order_reconciliation_primary_evidence_integration,
    evaluate_reconciliation_static,
    validate_primary_evidence_binding,
    validate_reconciliation_primary_evidence_integration_input,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
    PACKAGE_MARKER as PE16_PACKAGE_MARKER,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
    PRIMARY_EVIDENCE_OWNER,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE31_CONTRACT_VERSION,
    ReconciliationReviewLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe31_integration_input_digest,
    compute_integration_proof_digest as compute_pe31_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe31_integration_input,
    default_minimal_pe21_integration_proof,
    default_minimal_reconciliation_review_proof,
    evaluate_reconciliation_review_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE23_CONTRACT_VERSION,
    CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    Pe22UpstreamSafetyProof,
    compute_integration_input_digest as compute_pe23_integration_input_digest,
    compute_integration_proof_digest as compute_pe23_integration_proof_digest,
    compute_lifecycle_matrix_digest as compute_pe23_lifecycle_matrix_digest,
    compute_pe22_upstream_safety_digest,
    default_minimal_integration_input as default_minimal_pe23_integration_input,
    evaluate_capital_slot_ratchet_release_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE24_CONTRACT_VERSION,
    Pe22RiskKillswitchFlattenProofBinding as Pe24Pe22UpstreamProofBinding,
    Pe23CapitalSlotRatchetReleaseProofBinding as Pe24Pe23UpstreamProofBinding,
    PilotEnvelopeLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe24_integration_input_digest,
    compute_integration_proof_digest as compute_pe24_integration_proof_digest,
    compute_lifecycle_matrix_digest as compute_pe24_lifecycle_matrix_digest,
    default_minimal_integration_input as default_minimal_pe24_integration_input,
    evaluate_pilot_envelope_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
)
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    CONTRACT_VERSION as PE35_CONTRACT_VERSION,
    HANDOFF_STATE_CURRENT,
    HANDOFF_STATE_RECOVERED,
    HANDOFF_STATE_RECOVERY_REQUIRED,
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
    HandoffStalenessRevocationRecoveryBoundaryInput,
    compute_boundary_input_digest as compute_pe35_boundary_input_digest,
    compute_boundary_result_digest as compute_pe35_boundary_result_digest,
    default_minimal_boundary_input as default_minimal_pe35_boundary_input,
    evaluate_handoff_staleness_revocation_recovery_boundary,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE36_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE36_CONTRACT_VERSION,
    compute_boundary_input_digest as compute_pe36_boundary_input_digest,
    compute_boundary_result_digest as compute_pe36_boundary_result_digest,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE37_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE37_CONTRACT_VERSION,
    DurableEvidenceTraceabilityBoundaryInput,
    compute_boundary_input_digest as compute_pe37_boundary_input_digest,
    evaluate_durable_evidence_traceability_boundary,
    validate_durable_evidence_traceability_boundary_input,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
    OperatorClosureLifecycleIntegrationInput,
    compute_closure_input_digest as compute_pe25_closure_input_digest,
    compute_closure_result_digest as compute_pe25_closure_result_digest,
    evaluate_operator_closure_lifecycle_integration,
    validate_operator_closure_lifecycle_integration_input,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
    HANDOFF_OWNER as PE34_HANDOFF_OWNER,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
    RiskKillswitchLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe22_integration_input_digest,
    compute_integration_proof_digest as compute_pe22_integration_proof_digest,
    compute_lifecycle_matrix_digest as compute_pe22_lifecycle_matrix_digest,
    default_minimal_integration_input as default_minimal_pe22_integration_input,
    evaluate_risk_killswitch_lifecycle_integration,
)

PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_DURABLE_RUN_PRIMARY_EVIDENCE_COMPLETION_INTEGRATION_CONTRACT_V0=true"
)
CONTRACT_VERSION = "bounded_futures_testnet_durable_run_primary_evidence_completion_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_durable_run_primary_evidence_completion_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"
COMPLETION_INTEGRATION_OWNER = CONTRACT_VERSION

PE16_ARCHIVE_OWNER = "src/ops/bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
PE21_INTEGRATION_OWNER = PE21_CONTRACT_VERSION
PE31_INTEGRATION_OWNER = PE31_CONTRACT_VERSION
PE22_INTEGRATION_OWNER = PE22_CONTRACT_VERSION
PE23_INTEGRATION_OWNER = PE23_CONTRACT_VERSION
PE24_INTEGRATION_OWNER = PE24_CONTRACT_VERSION
PE35_INTEGRATION_OWNER = PE35_CONTRACT_VERSION
PE34_INTEGRATION_OWNER = PE34_CONTRACT_VERSION
PE36_INTEGRATION_OWNER = PE36_CONTRACT_VERSION
PE37_INTEGRATION_OWNER = PE37_CONTRACT_VERSION
PE25_INTEGRATION_OWNER = PE25_CONTRACT_VERSION
GAP4_COMPLETION_OWNER = "tests/ops/test_gap4_output_evidence_paths_contract_v0.py"
GAP2A1_ENFORCEMENT_OWNER = "tests/ops/test_gap2a1_primary_evidence_enforcement_contract_v0.py"
PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION = "primary_evidence_retention.v0"

SUPPORTED_RUN_TYPE = "bounded_futures_testnet"
REJECTED_RUN_TYPE_FRAGMENTS = (
    "spot",
    "bitcoin",
    "btc",
    "xbt",
    "paper",
    "shadow",
    "live",
    "scheduler",
    "supervisor",
    "order_capability",
)

EVIDENCE_MODE_DURABLE = "durable"
EVIDENCE_MODE_PLANNED = "planned"
EVIDENCE_MODE_SIMULATED = "simulated"
EVIDENCE_MODE_TMP_ONLY = "tmp_only"
ALLOWED_EVIDENCE_MODES = frozenset(
    {EVIDENCE_MODE_DURABLE, EVIDENCE_MODE_PLANNED, EVIDENCE_MODE_SIMULATED, EVIDENCE_MODE_TMP_ONLY}
)

PROOF_LIFECYCLE_CURRENT = "current"
PROOF_LIFECYCLE_STALE = "stale"
PROOF_LIFECYCLE_REVOKED = "revoked"
PROOF_LIFECYCLE_SUPERSEDED = "superseded"
PROOF_LIFECYCLE_REPLAY = "replay"
PROOF_LIFECYCLE_DUPLICATE = "duplicate"
ALLOWED_PROOF_LIFECYCLE_STATES = frozenset(
    {
        PROOF_LIFECYCLE_CURRENT,
        PROOF_LIFECYCLE_STALE,
        PROOF_LIFECYCLE_REVOKED,
        PROOF_LIFECYCLE_SUPERSEDED,
        PROOF_LIFECYCLE_REPLAY,
        PROOF_LIFECYCLE_DUPLICATE,
    }
)
INVALID_PROOF_LIFECYCLE_STATES = frozenset(
    {
        PROOF_LIFECYCLE_STALE,
        PROOF_LIFECYCLE_REVOKED,
        PROOF_LIFECYCLE_SUPERSEDED,
        PROOF_LIFECYCLE_REPLAY,
        PROOF_LIFECYCLE_DUPLICATE,
    }
)

GLOBAL_RUN_COMPLETION_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_RUN_COMPLETION_RECORDED = False
PRIMARY_EVIDENCE_OPERATIONALLY_ACCEPTED = False
RUN_STARTED = False
RUNNER_STARTED = False
SESSION_STARTED = False
ARCHIVE_READ = False
ARCHIVE_WRITTEN = False
MANIFEST_READ = False
MANIFEST_WRITTEN = False
FILESYSTEM_ACCESSED = False
REPLAY_EXECUTED = False
RECOVERY_EXECUTED = False
RESUME_EXECUTED = False
RETRY_EXECUTED = False
STATE_MUTATED = False
PARTIAL_FAILURE_OPERATIONALLY_RESOLVED = False
ADMISSION_EXECUTED = False
RECONCILIATION_EXECUTED = False
RISK_EVALUATION_EXECUTED = False
KILLSWITCH_TRIGGERED = False
FLATTEN_EXECUTED = False
CAPITAL_SLOT_RATCHET_EXECUTED = False
CAPITAL_SLOT_RELEASE_EXECUTED = False
CAPITAL_REALLOCATION_EXECUTED = False
RESERVE_TOP_UP_EXECUTED = False
PILOT_ENVELOPE_EXECUTED = False
PILOT_STARTED = False
AUTHORITY_LIFT = False
PREFLIGHT_REMAINS_BLOCKED = True

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_EXTRA_FIELD_FRAGMENTS = (
    "secret",
    "credential",
    "api_key",
    "password",
    "token",
    "command",
    "action",
    "authority",
    "acceptance",
    "completion_override",
    "decision",
    "execution_authorized",
    "live_authorized",
    "pilot_start",
    "promotion",
    "network_allowed",
    "orders_allowed",
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe16_archive": ARCHIVE_CONTRACT_VERSION,
    "pe16_primary_evidence_retention": PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
    "pe21_integration": PE21_CONTRACT_VERSION,
    "pe31_integration": PE31_CONTRACT_VERSION,
    "pe22_integration": PE22_CONTRACT_VERSION,
    "pe23_integration": PE23_CONTRACT_VERSION,
    "pe24_integration": PE24_CONTRACT_VERSION,
    "pe35_boundary": PE35_CONTRACT_VERSION,
    "pe34_handoff": PE34_CONTRACT_VERSION,
    "pe36_admission_presentation": PE36_CONTRACT_VERSION,
    "pe37_traceability": PE37_CONTRACT_VERSION,
    "pe25_operator_closure": PE25_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe16_archive: str
    pe16_primary_evidence_retention: str
    pe21_integration: str
    pe31_integration: str
    pe22_integration: str
    pe23_integration: str
    pe24_integration: str
    pe35_boundary: str
    pe34_handoff: str
    pe36_admission_presentation: str
    pe37_traceability: str
    pe25_operator_closure: str
    integration: str


@dataclass(frozen=True)
class RunIdentityBinding:
    run_id: str
    run_identity_digest: str


@dataclass(frozen=True)
class DurableRunRootBinding:
    durable_archive_root: str
    run_root_identity: str
    run_root_digest: str


@dataclass(frozen=True)
class PrimaryEvidenceIdentityBinding:
    primary_evidence_identity: str
    primary_evidence_owner: str
    retention_contract_version: str


@dataclass(frozen=True)
class Pe16ArchiveProofBinding:
    archive_owner: str
    archive_contract_version: str
    archive_identity: str
    archive_digest: str
    pe16_integration_pass: bool


@dataclass(frozen=True)
class Pe21PrimaryEvidenceProofBinding:
    integration_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    pe21_integration_pass: bool
    durable_primary_evidence_binding_proven: bool


@dataclass(frozen=True)
class Pe31ReconciliationReviewIntegrationProofBinding:
    integration_owner: str
    integration_input_digest: str
    integration_proof_digest: str
    pe31_integration_pass: bool
    reconciliation_review_lifecycle_eligibility: bool


@dataclass(frozen=True)
class Pe22RiskKillswitchFlattenProofBinding:
    integration_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    pe22_integration_pass: bool
    risk_evaluation_proof_digest: str
    killswitch_evaluation_proof_digest: str
    flatten_state_proof_digest: str
    lifecycle_matrix_digest: str
    traceability_identity: str
    run_identity_digest: str
    safe_completion_state_proven: bool


@dataclass(frozen=True)
class Pe23CapitalSlotRatchetReleaseProofBinding:
    integration_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    pe23_integration_pass: bool
    ratchet_evaluation_proof_digest: str
    release_eligibility_proof_digest: str
    reserve_topup_block_proof_digest: str
    lifecycle_matrix_digest: str
    traceability_identity: str
    run_identity_digest: str
    completion_identity_digest: str
    capital_slot_identity_digest: str
    capital_slot_coherence_proven: bool


@dataclass(frozen=True)
class Pe24PilotEnvelopeLifecycleProofBinding:
    integration_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    pe24_integration_pass: bool
    pilot_envelope_static_ready: bool
    lifecycle_matrix_digest: str
    traceability_identity: str
    run_identity_digest: str
    completion_identity_digest: str
    pilot_envelope_identity_digest: str
    pe19_review_proof_digest: str
    pe20_package_id: str
    pe22_integration_proof_digest: str
    pe23_integration_proof_digest: str
    pilot_envelope_coherence_proven: bool


@dataclass(frozen=True)
class Pe35HandoffRecoveryBoundaryProofBinding:
    boundary_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str
    pe35_boundary_pass: bool
    handoff_staleness_revocation_recovery_boundary_satisfied: bool
    durable_run_primary_evidence_completion_boundary_bound: bool
    recovery_boundary_bound: bool
    partial_failure_recovery_bound: bool
    idempotency_bound: bool
    resume_boundary_bound: bool
    retry_boundary_bound: bool
    replay_boundary_bound: bool
    supersession_bound: bool
    traceability_identity: str
    run_identity_digest: str
    completion_identity_digest: str
    manifest_identity_digest: str
    handoff_digest: str
    handoff_generation: int
    recovery_generation: int
    recovery_coherence_proven: bool


@dataclass(frozen=True)
class Pe37TraceabilityProofBinding:
    traceability_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str
    pe37_boundary_pass: bool
    durable_evidence_traceability_boundary_satisfied: bool
    pe34_handoff_bound: bool
    pe35_staleness_revocation_recovery_bound: bool
    pe36_admission_presentation_bound: bool
    durable_run_primary_evidence_completion_traceability_bound: bool
    operator_review_chain_durable_evidence_traceability_bound: bool
    traceability_identity: str
    admission_identity: str
    run_identity_digest: str
    completion_identity_digest: str
    manifest_identity_digest: str
    durable_artifact_identity: str
    review_chain_identity: str
    pe34_handoff_digest: str
    pe36_boundary_result_digest: str
    traceability_coherence_proven: bool


@dataclass(frozen=True)
class Pe25OperatorClosureLifecycleProofBinding:
    closure_owner: str
    source_revision: str
    closure_input_digest: str
    closure_result_digest: str
    admission_integration_proof_digest: str
    pe25_integration_pass: bool
    operator_closure_static_complete: bool
    operator_closure_lifecycle_bound: bool
    pe25_operator_closure_bound: bool
    durable_run_primary_evidence_completion_operator_closure_bound: bool
    pe34_handoff_bound: bool
    pe35_staleness_revocation_recovery_bound: bool
    pe36_admission_presentation_bound: bool
    pe37_durable_traceability_bound: bool
    traceability_identity: str
    admission_identity: str
    run_identity_digest: str
    completion_identity_digest: str
    manifest_identity_digest: str
    durable_artifact_identity: str
    pe34_handoff_digest: str
    pe35_boundary_result_digest: str
    pe36_boundary_result_digest: str
    pe37_traceability_identity: str
    closure_coherence_proven: bool


@dataclass(frozen=True)
class CompletionProofChainBinding:
    completion_referenced_pe31_proof_digest: str
    completion_referenced_pe22_proof_digest: str
    completion_referenced_pe23_proof_digest: str
    completion_referenced_pe24_proof_digest: str
    completion_referenced_pe35_boundary_result_digest: str
    completion_referenced_pe37_boundary_result_digest: str
    pe37_traceability_identity: str
    completion_referenced_pe25_closure_result_digest: str
    pe25_closure_input_digest: str
    closure_referenced_admission_proof_digest: str
    pe31_referenced_pe21_integration_proof_digest: str
    completion_referenced_pe21_integration_proof_digest: str
    shared_pe21_integration_input_digest: str
    shared_traceability_identity: str


@dataclass(frozen=True)
class Gap4CompletionProofBinding:
    gap4_owner: str
    source_revision: str
    output_evidence_depends_on_gap2a1: bool
    completion_invalid_without_durable_primary_evidence: bool
    completion_invalid_without_manifest_verify: bool
    durable_output_required_for_future_runs: bool
    gap4_output_evidence_paths_verified: bool
    gap4_integration_pass: bool


@dataclass(frozen=True)
class Gap2a1EnforcementProofBinding:
    gap2a1_owner: str
    source_revision: str
    primary_evidence_enforced: bool
    enforcement_default_on: bool
    enforcement_opt_in_only: bool
    tmp_only_evidence_invalid: bool
    manifest_verify_required: bool
    checksum_verify_required: bool
    run_incomplete_without_primary_evidence: bool
    gap2a1_integration_pass: bool


@dataclass(frozen=True)
class ArtifactChecksumEntry:
    relative_path: str
    digest: str


@dataclass(frozen=True)
class ManifestProofBinding:
    manifest_identity: str
    manifest_digest: str
    manifest_verify_rc: int
    manifest_entries: tuple[ArtifactChecksumEntry, ...]


@dataclass(frozen=True)
class PostWriteVerificationBinding:
    post_write_verification_pass: bool
    manifest_verify_rc: int


@dataclass(frozen=True)
class ProofLifecycleMetadata:
    lifecycle_state: str
    proof_generation: int = 0


@dataclass(frozen=True)
class CompletionSafetySnapshot:
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    evidence_acceptance_authorized: bool
    promotion_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class DurableRunPrimaryEvidenceCompletionIntegrationInput:
    source_revision: str
    repository_identity: str
    run_type: str
    run_identity: RunIdentityBinding
    durable_run_root: DurableRunRootBinding
    primary_evidence_identity: PrimaryEvidenceIdentityBinding
    pe21_proof: Pe21PrimaryEvidenceProofBinding
    pe21_integration_input: ReconciliationPrimaryEvidenceIntegrationInput
    pe31_reconciliation_review_integration_input: ReconciliationReviewLifecycleIntegrationInput
    pe31_reconciliation_review_integration_proof: Pe31ReconciliationReviewIntegrationProofBinding
    pe22_risk_killswitch_lifecycle_integration_input: RiskKillswitchLifecycleIntegrationInput
    pe22_risk_killswitch_flatten_proof: Pe22RiskKillswitchFlattenProofBinding
    pe23_capital_slot_ratchet_release_lifecycle_integration_input: (
        CapitalSlotRatchetReleaseLifecycleIntegrationInput
    )
    pe23_capital_slot_ratchet_release_proof: Pe23CapitalSlotRatchetReleaseProofBinding
    pe24_pilot_envelope_lifecycle_integration_input: PilotEnvelopeLifecycleIntegrationInput
    pe24_pilot_envelope_lifecycle_proof: Pe24PilotEnvelopeLifecycleProofBinding
    pe35_handoff_staleness_revocation_recovery_boundary_input: (
        HandoffStalenessRevocationRecoveryBoundaryInput
    )
    pe35_handoff_recovery_boundary_proof: Pe35HandoffRecoveryBoundaryProofBinding
    pe37_traceability_boundary_input: DurableEvidenceTraceabilityBoundaryInput
    pe37_traceability_proof: Pe37TraceabilityProofBinding
    pe25_closure_integration_input: OperatorClosureLifecycleIntegrationInput
    pe25_operator_closure_proof: Pe25OperatorClosureLifecycleProofBinding
    pe25_proof_lifecycle: ProofLifecycleMetadata
    completion_proof_chain: CompletionProofChainBinding
    pe16_archive: Pe16ArchiveProofBinding
    manifest_proof: ManifestProofBinding
    artifact_checksums: tuple[ArtifactChecksumEntry, ...]
    post_write_verification: PostWriteVerificationBinding
    gap4_completion: Gap4CompletionProofBinding
    gap2a1_enforcement: Gap2a1EnforcementProofBinding
    proof_lifecycle: ProofLifecycleMetadata
    evidence_mode: str
    completion_claimed: bool
    safety_snapshot: CompletionSafetySnapshot
    contract_versions: ContractVersionsInput
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def compute_run_identity_digest(*, run_id: str, run_type: str, source_revision: str) -> str:
    payload = {
        "hash_algorithm": HASH_ALGORITHM,
        "run_id": run_id,
        "run_type": run_type,
        "source_revision": source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_run_root_digest(
    *,
    durable_archive_root: str,
    run_root_identity: str,
    source_revision: str,
) -> str:
    payload = {
        "durable_archive_root": durable_archive_root,
        "hash_algorithm": HASH_ALGORITHM,
        "run_root_identity": run_root_identity,
        "source_revision": source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_primary_evidence_identity_digest(
    *,
    primary_evidence_identity: str,
    primary_evidence_owner: str,
    retention_contract_version: str,
    source_revision: str,
) -> str:
    payload = {
        "hash_algorithm": HASH_ALGORITHM,
        "primary_evidence_identity": primary_evidence_identity,
        "primary_evidence_owner": primary_evidence_owner,
        "retention_contract_version": retention_contract_version,
        "source_revision": source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_completion_identity_digest(
    *,
    run_root_digest: str,
    manifest_digest: str,
    source_revision: str,
) -> str:
    payload = {
        "hash_algorithm": HASH_ALGORITHM,
        "manifest_digest": manifest_digest,
        "run_root_digest": run_root_digest,
        "source_revision": source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_pilot_envelope_identity_digest(
    *,
    pilot_envelope_integration_input_digest: str,
    run_root_digest: str,
    completion_identity_digest: str,
    source_revision: str,
) -> str:
    payload = {
        "completion_identity_digest": completion_identity_digest,
        "hash_algorithm": HASH_ALGORITHM,
        "pilot_envelope_integration_input_digest": pilot_envelope_integration_input_digest,
        "run_root_digest": run_root_digest,
        "source_revision": source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _pe22_upstream_safety_proof_from_completion_pe22(
    pe22_proof: Pe22RiskKillswitchFlattenProofBinding,
) -> Pe22UpstreamSafetyProof:
    draft = Pe22UpstreamSafetyProof(
        proof_id="pe22-upstream-from-completion-001",
        proof_digest="",
        pe22_contract_version=PE22_CONTRACT_VERSION,
        integration_proof_digest=pe22_proof.integration_proof_digest,
        pe22_integration_pass=True,
        lifecycle_matrix_digest=pe22_proof.lifecycle_matrix_digest,
    )
    return Pe22UpstreamSafetyProof(
        proof_id=draft.proof_id,
        proof_digest=compute_pe22_upstream_safety_digest(draft),
        pe22_contract_version=draft.pe22_contract_version,
        integration_proof_digest=draft.integration_proof_digest,
        pe22_integration_pass=draft.pe22_integration_pass,
        lifecycle_matrix_digest=draft.lifecycle_matrix_digest,
    )


def _manifest_entries_from_artifacts(
    artifacts: tuple[ArtifactChecksumEntry, ...],
) -> tuple[ManifestEntry, ...]:
    return tuple(
        ManifestEntry(digest=entry.digest, relative_path=entry.relative_path)
        for entry in sorted(artifacts, key=lambda item: item.relative_path)
    )


def _validate_run_type(run_type: str) -> list[str]:
    fail_reasons: list[str] = []
    if not run_type:
        fail_reasons.append("run_type required")
        return fail_reasons
    if run_type != SUPPORTED_RUN_TYPE:
        fail_reasons.append(f"run_type must be {SUPPORTED_RUN_TYPE!r}")
    lowered = run_type.lower()
    for fragment in REJECTED_RUN_TYPE_FRAGMENTS:
        if fragment in lowered:
            fail_reasons.append(f"run_type contains rejected fragment {fragment!r}")
    return fail_reasons


def _validate_archive_root_identity(archive_root: str, relative_identity: str) -> list[str]:
    fail_reasons: list[str] = []
    if not archive_root:
        fail_reasons.append("durable_archive_root required")
    else:
        root_path = Path(archive_root)
        if is_under_tmp(root_path):
            fail_reasons.append("durable_archive_root must be outside /tmp")
    if not relative_identity:
        fail_reasons.append("run_root_identity required")
    elif relative_identity.startswith("/"):
        fail_reasons.append("run_root_identity must be relative")
    elif ".." in Path(relative_identity).parts:
        fail_reasons.append("run_root_identity must not contain '..'")
    combined = f"{archive_root.rstrip('/')}/{relative_identity}".replace("\\", "/")
    if "/../" in f"/{combined}/" or combined.endswith("/.."):
        fail_reasons.append("run root path traversal rejected")
    return fail_reasons


def _validate_safety_snapshot(snapshot: CompletionSafetySnapshot) -> list[str]:
    fail_reasons: list[str] = []
    required_bools = (
        ("preflight_remains_blocked", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("evidence_acceptance_authorized", False),
        ("promotion_authorized", False),
        ("network_allowed", False),
        ("credentials_allowed", False),
        ("orders_allowed", False),
        ("scheduler_runtime_allowed", False),
        ("futures_only", True),
        ("bitcoin_direction_allowed", False),
    )
    for field_name, expected in required_bools:
        actual = getattr(snapshot, field_name)
        if actual is not expected:
            fail_reasons.append(f"safety_snapshot: {field_name} must be {expected}")
    if snapshot.followup_run_gate != FOLLOWUP_RUN_GATE:
        fail_reasons.append(f"safety_snapshot: followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")
    return fail_reasons


def _validate_manifest_and_artifacts(
    manifest_proof: ManifestProofBinding,
    artifact_checksums: tuple[ArtifactChecksumEntry, ...],
) -> list[str]:
    fail_reasons: list[str] = []
    required_paths = set(BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS)
    required_manifest_paths = required_paths - {MANIFEST_FILENAME}
    artifact_paths = [entry.relative_path for entry in artifact_checksums]
    manifest_paths = [entry.relative_path for entry in manifest_proof.manifest_entries]

    if len(artifact_paths) != len(set(artifact_paths)):
        fail_reasons.append("duplicate artifact checksum paths")
    if len(manifest_paths) != len(set(manifest_paths)):
        fail_reasons.append("duplicate manifest entry paths")

    missing_required = sorted(required_paths - set(artifact_paths))
    if missing_required:
        fail_reasons.append(f"missing required artifact paths: {missing_required}")

    extra_artifacts = sorted(set(artifact_paths) - required_paths)
    if extra_artifacts:
        fail_reasons.append(f"unexpected artifact paths: {extra_artifacts}")

    if set(manifest_paths) != required_manifest_paths:
        fail_reasons.append("manifest entries must cover exactly the canonical required artifacts")

    checksum_by_path = {entry.relative_path: entry.digest for entry in artifact_checksums}
    for manifest_entry in manifest_proof.manifest_entries:
        if manifest_entry.relative_path.startswith("/"):
            fail_reasons.append(
                f"absolute manifest path rejected: {manifest_entry.relative_path!r}"
            )
        if ".." in Path(manifest_entry.relative_path).parts:
            fail_reasons.append(
                f"path traversal rejected in manifest entry: {manifest_entry.relative_path!r}"
            )
        if not _valid_sha256_digest(manifest_entry.digest):
            fail_reasons.append(
                f"invalid manifest entry digest for {manifest_entry.relative_path!r}"
            )
        expected_digest = checksum_by_path.get(manifest_entry.relative_path)
        if expected_digest is None:
            fail_reasons.append(
                f"manifest entry without artifact checksum: {manifest_entry.relative_path!r}"
            )
        elif expected_digest != manifest_entry.digest:
            fail_reasons.append(f"checksum mismatch for artifact {manifest_entry.relative_path!r}")

    for entry in artifact_checksums:
        if not _valid_sha256_digest(entry.digest):
            fail_reasons.append(f"invalid artifact checksum for {entry.relative_path!r}")
        if entry.relative_path.startswith("/"):
            fail_reasons.append(f"absolute artifact path rejected: {entry.relative_path!r}")
        if ".." in Path(entry.relative_path).parts:
            fail_reasons.append(f"path traversal rejected in artifact: {entry.relative_path!r}")

    if not manifest_proof.manifest_identity:
        fail_reasons.append("manifest_identity required")
    elif not _valid_sha256_digest(manifest_proof.manifest_identity):
        fail_reasons.append("manifest_identity must be 64-char lowercase sha256 hex")

    if not manifest_proof.manifest_digest:
        fail_reasons.append("manifest_digest required")
    elif not _valid_sha256_digest(manifest_proof.manifest_digest):
        fail_reasons.append("manifest_digest must be 64-char lowercase sha256 hex")

    manifest_artifact_entries = tuple(
        entry for entry in artifact_checksums if entry.relative_path != MANIFEST_FILENAME
    )
    computed_manifest_digest = compute_manifest_digest(
        _manifest_entries_from_artifacts(manifest_artifact_entries)
    )
    if manifest_proof.manifest_digest != computed_manifest_digest:
        fail_reasons.append("manifest_digest mismatch")
    if manifest_proof.manifest_identity != computed_manifest_digest:
        fail_reasons.append("manifest_identity mismatch with computed manifest digest")

    if manifest_proof.manifest_verify_rc != 0:
        fail_reasons.append("manifest_proof.manifest_verify_rc must be 0")

    return _sorted_unique(fail_reasons)


def _validate_pe16_archive_proof(
    archive: Pe16ArchiveProofBinding,
    *,
    source_revision: str,
    primary_evidence_identity: PrimaryEvidenceIdentityBinding,
    run_root_identity: str,
    manifest_digest: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if archive.archive_owner != PE16_ARCHIVE_OWNER:
        fail_reasons.append(f"pe16_archive: archive_owner must be {PE16_ARCHIVE_OWNER!r}")
    if archive.archive_contract_version != ARCHIVE_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe16_archive: archive_contract_version must be {ARCHIVE_CONTRACT_VERSION!r}"
        )
    if not archive.archive_identity:
        fail_reasons.append("pe16_archive: archive_identity required")
    elif archive.archive_identity != run_root_identity:
        fail_reasons.append("pe16_archive: archive_identity mismatch with run_root_identity")
    elif not _valid_sha256_digest(archive.archive_digest):
        fail_reasons.append("pe16_archive: archive_digest must be 64-char lowercase sha256 hex")
    if archive.pe16_integration_pass is not True:
        fail_reasons.append("pe16_archive: pe16_integration_pass must be true")
    if primary_evidence_identity.primary_evidence_owner != PRIMARY_EVIDENCE_OWNER:
        fail_reasons.append(f"primary_evidence_identity: owner must be {PRIMARY_EVIDENCE_OWNER!r}")
    if (
        primary_evidence_identity.retention_contract_version
        != PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION
    ):
        fail_reasons.append(
            "primary_evidence_identity: retention_contract_version must be "
            f"{PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION!r}"
        )
    expected_archive_digest = hashlib.sha256(
        json.dumps(
            {
                "archive_contract_version": archive.archive_contract_version,
                "archive_identity": archive.archive_identity,
                "manifest_digest": manifest_digest,
                "source_revision": source_revision,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if archive.archive_digest != expected_archive_digest:
        fail_reasons.append("pe16_archive: archive_digest mismatch")
    if PE16_PACKAGE_MARKER != "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_ARCHIVE_CONTRACT_V0=true":
        fail_reasons.append("pe16_archive: package marker drift")
    return fail_reasons


def _validate_pe21_proof_binding(
    proof: Pe21PrimaryEvidenceProofBinding,
    *,
    source_revision: str,
    pe21_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    if proof.integration_owner != PE21_INTEGRATION_OWNER:
        fail_reasons.append(f"pe21_proof: integration_owner must be {PE21_INTEGRATION_OWNER!r}")
    if proof.source_revision != source_revision:
        fail_reasons.append("pe21_proof: source_revision mismatch")
    if proof.integration_input_digest != pe21_result.get("integration_input_digest"):
        fail_reasons.append("pe21_proof: integration_input_digest mismatch")
    expected_proof_digest = pe21_result.get("integration_proof_digest")
    if proof.pe21_integration_pass is not True:
        fail_reasons.append("pe21_proof: pe21_integration_pass must be true")
    if not pe21_result.get("integration_pass"):
        fail_reasons.extend(pe21_result.get("fail_reasons", []))
    elif proof.integration_proof_digest != expected_proof_digest:
        fail_reasons.append("pe21_proof: integration_proof_digest mismatch")
    if proof.durable_primary_evidence_binding_proven is not True:
        fail_reasons.append("pe21_proof: durable_primary_evidence_binding_proven must be true")
    elif not pe21_result.get("durable_primary_evidence_binding_proven"):
        fail_reasons.append("pe21_proof: durable primary evidence binding not proven upstream")
    return fail_reasons


def _validate_pe21_reconciliation_result_manifest_integrity(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> list[str]:
    """Fail-closed PE-21 RECONCILIATION_RESULT.json manifest entry integrity enforcement."""
    fail_reasons: list[str] = []
    pe21_input = integration_input.pe21_integration_input
    pe21_binding = pe21_input.primary_evidence_binding
    recon = pe21_input.reconciliation_binding
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    prefix = "pe21_reconciliation_result_manifest"

    for entry in pe21_binding.manifest_entries:
        if not entry.relative_path:
            fail_reasons.append(f"{prefix}: empty manifest artifact path")

    canonical_entries = [
        entry
        for entry in pe21_binding.manifest_entries
        if entry.relative_path == ARTIFACT_RECONCILIATION_RESULT
    ]
    alias_entries = [
        entry
        for entry in pe21_binding.manifest_entries
        if entry.relative_path != ARTIFACT_RECONCILIATION_RESULT
        and (
            entry.relative_path.endswith(ARTIFACT_RECONCILIATION_RESULT)
            or "RECONCILIATION_RESULT" in entry.relative_path
        )
    ]

    if not canonical_entries:
        fail_reasons.append(f"{prefix}: {ARTIFACT_RECONCILIATION_RESULT} manifest entry required")
    elif len(canonical_entries) > 1:
        fail_reasons.append(
            f"{prefix}: duplicate {ARTIFACT_RECONCILIATION_RESULT} manifest entries"
        )

    if alias_entries:
        fail_reasons.append(f"{prefix}: alias or alternate reconciliation result manifest path")

    if ARTIFACT_RECONCILIATION_RESULT not in pe21_binding.expected_artifact_filenames:
        fail_reasons.append(
            f"{prefix}: {ARTIFACT_RECONCILIATION_RESULT} required in expected_artifact_filenames"
        )

    expected_result_digest = recon.result_digest
    if not expected_result_digest:
        fail_reasons.append(f"{prefix}: reconciliation_binding.result_digest required")
    elif not _valid_sha256_digest(expected_result_digest):
        fail_reasons.append(
            f"{prefix}: reconciliation_binding.result_digest must be 64-char lowercase sha256 hex"
        )
    else:
        static_recon = evaluate_reconciliation_static(
            expected_position=recon.expected_position,
            observed_position=recon.observed_position,
            expected_orders=recon.expected_orders,
            observed_orders=recon.observed_orders,
            instrument=pe21_input.instrument,
        )
        if expected_result_digest != static_recon["result_digest"]:
            fail_reasons.append(
                f"{prefix}: reconciliation_binding.result_digest mismatch with canonical algorithm"
            )

    if canonical_entries:
        entry = canonical_entries[0]
        if not entry.relative_path:
            fail_reasons.append(f"{prefix}: empty manifest artifact path")
        elif entry.relative_path != ARTIFACT_RECONCILIATION_RESULT:
            fail_reasons.append(
                f"{prefix}: manifest artifact path must be {ARTIFACT_RECONCILIATION_RESULT!r}"
            )
        if not entry.digest:
            fail_reasons.append(
                f"{prefix}: manifest digest required for {ARTIFACT_RECONCILIATION_RESULT}"
            )
        elif not _valid_sha256_digest(entry.digest):
            fail_reasons.append(f"{prefix}: manifest digest must be 64-char lowercase sha256 hex")
        elif expected_result_digest and entry.digest != expected_result_digest:
            fail_reasons.append(
                f"{prefix}: manifest digest mismatch with reconciliation_binding.result_digest"
            )

    if pe21_input.source_revision != integration_input.source_revision:
        fail_reasons.append(f"{prefix}: source_revision drift breaks run identity chain")

    if pe21_binding.durable_archive_root != durable_root.durable_archive_root:
        fail_reasons.append(f"{prefix}: durable_archive_root drift breaks evidence root chain")

    computed_pe21_manifest = compute_manifest_digest(pe21_binding.manifest_entries)
    if pe21_binding.manifest_digest != computed_pe21_manifest:
        fail_reasons.append(
            f"{prefix}: pe21 manifest_digest drift invalidates reconciliation result manifest entry"
        )
    if pe21_binding.manifest_proof_identity != computed_pe21_manifest:
        fail_reasons.append(
            f"{prefix}: pe21 manifest_proof_identity drift invalidates reconciliation result "
            "manifest entry"
        )

    completion_identity = compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=manifest_digest,
        source_revision=integration_input.source_revision,
    )
    if not run_identity.run_identity_digest:
        fail_reasons.append(f"{prefix}: run_identity_digest required for evidence chain")
    elif not _valid_sha256_digest(run_identity.run_identity_digest):
        fail_reasons.append(f"{prefix}: run_identity_digest must be 64-char lowercase sha256 hex")
    if not manifest_digest:
        fail_reasons.append(f"{prefix}: completion manifest_digest required for evidence chain")
    elif not _valid_sha256_digest(manifest_digest):
        fail_reasons.append(
            f"{prefix}: completion manifest_digest must be 64-char lowercase sha256 hex"
        )
    if not completion_identity:
        fail_reasons.append(f"{prefix}: completion_identity_digest unavailable for evidence chain")

    return _sorted_unique(fail_reasons)


def _validate_pe31_integration_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe31_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe31_reconciliation_review_integration_proof
    pe31_input = integration_input.pe31_reconciliation_review_integration_input

    if proof.integration_owner != PE31_INTEGRATION_OWNER:
        fail_reasons.append(f"pe31_proof: integration_owner must be {PE31_INTEGRATION_OWNER!r}")
    if not proof.integration_input_digest:
        fail_reasons.append("pe31_proof: integration_input_digest required")
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe31_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe31_integration_input_digest(pe31_input):
        fail_reasons.append("pe31_proof: integration_input_digest mismatch")

    if not proof.integration_proof_digest:
        fail_reasons.append("pe31_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe31_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe31_integration_proof_digest(
            pe31_input,
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review=True,
        )
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append("pe31_proof: integration_proof_digest mismatch")

    if proof.pe31_integration_pass is not True:
        fail_reasons.append("pe31_proof: pe31_integration_pass must be true")
    if proof.reconciliation_review_lifecycle_eligibility is not True:
        fail_reasons.append("pe31_proof: reconciliation_review_lifecycle_eligibility must be true")

    if not pe31_result.get("integration_pass"):
        fail_reasons.append("pe31_reconciliation_review_integration_input: PE-31 evaluation failed")
        fail_reasons.extend(
            f"pe31_reconciliation_review_integration_input: {reason}"
            for reason in pe31_result.get("fail_reasons", [])
        )
    elif not pe31_result.get(
        "reconciliation_review_lifecycle_eligibility_for_separate_operator_review"
    ):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: "
            "reconciliation_review_lifecycle_eligibility required"
        )

    if pe31_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: source_revision mismatch"
        )

    pe31_pe21_input = pe31_input.pe21_reconciliation_primary_evidence_integration_input
    if compute_pe21_integration_input_digest(
        pe31_pe21_input
    ) != compute_pe21_integration_input_digest(integration_input.pe21_integration_input):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: pe21_integration_input_digest mismatch "
            "with completion pe21_integration_input"
        )

    pe31_pe21_proof = pe31_input.pe21_reconciliation_primary_evidence_integration_proof
    if (
        pe31_pe21_proof.integration_proof_digest
        != integration_input.pe21_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: pe21_integration_proof_digest mismatch "
            "with completion pe21_proof"
        )
    if pe31_pe21_proof.reconciled is not True:
        fail_reasons.append("pe31_reconciliation_review_integration_input: reconciled must be true")

    review_proof = pe31_input.reconciliation_review_proof
    if review_proof.static_review_consistency_proven is not True:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: static_review_consistency_proven required"
        )
    if review_proof.orders_created != 0 or review_proof.orders_cancelled != 0:
        fail_reasons.append("pe31_reconciliation_review_integration_input: unresolved order state")
    if review_proof.positions_changed != 0:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: unresolved position state"
        )

    return fail_reasons


def _validate_pe22_integration_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe22_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe22_risk_killswitch_flatten_proof
    pe22_input = integration_input.pe22_risk_killswitch_lifecycle_integration_input
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity

    if proof.integration_owner != PE22_INTEGRATION_OWNER:
        fail_reasons.append(f"pe22_proof: integration_owner must be {PE22_INTEGRATION_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe22_proof: source_revision mismatch")
    if not proof.integration_input_digest:
        fail_reasons.append("pe22_proof: integration_input_digest required")
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe22_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe22_integration_input_digest(pe22_input):
        fail_reasons.append("pe22_proof: integration_input_digest mismatch")

    if not proof.integration_proof_digest:
        fail_reasons.append("pe22_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe22_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe22_integration_proof_digest(pe22_input)
        if proof.pe22_integration_pass is not True:
            fail_reasons.append("pe22_proof: pe22_integration_pass must be true")
        elif proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append("pe22_proof: integration_proof_digest mismatch")

    if proof.pe22_integration_pass is not True:
        fail_reasons.append("pe22_proof: pe22_integration_pass must be true")

    digest_fields = (
        ("risk_evaluation_proof_digest", proof.risk_evaluation_proof_digest),
        ("killswitch_evaluation_proof_digest", proof.killswitch_evaluation_proof_digest),
        ("flatten_state_proof_digest", proof.flatten_state_proof_digest),
        ("lifecycle_matrix_digest", proof.lifecycle_matrix_digest),
        ("traceability_identity", proof.traceability_identity),
        ("run_identity_digest", proof.run_identity_digest),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe22_proof: {field_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"pe22_proof: {field_name} must be 64-char lowercase sha256 hex")

    if proof.risk_evaluation_proof_digest != pe22_input.risk_evaluation_proof.proof_digest:
        fail_reasons.append("pe22_proof: risk_evaluation_proof_digest mismatch")
    if (
        proof.killswitch_evaluation_proof_digest
        != pe22_input.killswitch_evaluation_proof.proof_digest
    ):
        fail_reasons.append("pe22_proof: killswitch_evaluation_proof_digest mismatch")
    if proof.flatten_state_proof_digest != pe22_input.flatten_state_proof.proof_digest:
        fail_reasons.append("pe22_proof: flatten_state_proof_digest mismatch")
    if proof.lifecycle_matrix_digest != compute_pe22_lifecycle_matrix_digest():
        fail_reasons.append("pe22_proof: lifecycle_matrix_digest mismatch")
    if proof.traceability_identity != durable_root.run_root_digest:
        fail_reasons.append("pe22_proof: traceability_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe22_proof: run_identity_digest mismatch")

    if pe22_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe22_risk_killswitch_lifecycle_integration_input: source_revision mismatch with "
            "completion input"
        )

    pe22_matrix = pe22_input.lifecycle_matrix_proof
    if pe22_matrix.lifecycle_state_digest != durable_root.run_root_digest:
        fail_reasons.append(
            "pe22_risk_killswitch_lifecycle_integration_input: lifecycle_state_digest mismatch "
            "with run_root_digest"
        )

    risk_proof = pe22_input.risk_evaluation_proof
    killswitch_proof = pe22_input.killswitch_evaluation_proof
    flatten_proof = pe22_input.flatten_state_proof
    if proof.safe_completion_state_proven is not True:
        fail_reasons.append("pe22_proof: safe_completion_state_proven must be true")
    elif not (
        risk_proof.proof_pass is True
        and risk_proof.evaluation_allow is True
        and killswitch_proof.killswitch_clear is True
        and killswitch_proof.proof_pass is True
        and flatten_proof.position_flattened_by_end is True
        and flatten_proof.proof_pass is True
        and flatten_proof.cancel_or_close_evidence_valid is True
    ):
        fail_reasons.append("pe22_proof: safe completion state not proven upstream")

    if not pe22_result.get("integration_pass"):
        fail_reasons.append(
            "pe22_risk_killswitch_lifecycle_integration_input: PE-22 evaluation failed"
        )
        fail_reasons.extend(
            f"pe22_risk_killswitch_lifecycle_integration_input: {reason}"
            for reason in pe22_result.get("fail_reasons", [])
        )
    elif not pe22_result.get("pe12_tiny_order_risk_killswitch_flatten_static_integration_proven"):
        fail_reasons.append(
            "pe22_risk_killswitch_lifecycle_integration_input: "
            "pe12_tiny_order_risk_killswitch_flatten_static_integration_proven required"
        )

    return fail_reasons


def _validate_pe23_integration_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe23_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe23_capital_slot_ratchet_release_proof
    pe23_input = integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=manifest_digest,
        source_revision=integration_input.source_revision,
    )

    if proof.integration_owner != PE23_INTEGRATION_OWNER:
        fail_reasons.append(f"pe23_proof: integration_owner must be {PE23_INTEGRATION_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe23_proof: source_revision mismatch")
    if not proof.integration_input_digest:
        fail_reasons.append("pe23_proof: integration_input_digest required")
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe23_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe23_integration_input_digest(pe23_input):
        fail_reasons.append("pe23_proof: integration_input_digest mismatch")

    if not proof.integration_proof_digest:
        fail_reasons.append("pe23_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe23_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe23_integration_proof_digest(
            pe23_input,
            pe23_proven=True,
            release_eligibility_proven=pe23_input.release_eligibility_proof.release_eligible,
        )
        if proof.pe23_integration_pass is not True:
            fail_reasons.append("pe23_proof: pe23_integration_pass must be true")
        elif proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append("pe23_proof: integration_proof_digest mismatch")

    if proof.pe23_integration_pass is not True:
        fail_reasons.append("pe23_proof: pe23_integration_pass must be true")

    digest_fields = (
        ("ratchet_evaluation_proof_digest", proof.ratchet_evaluation_proof_digest),
        ("release_eligibility_proof_digest", proof.release_eligibility_proof_digest),
        ("reserve_topup_block_proof_digest", proof.reserve_topup_block_proof_digest),
        ("lifecycle_matrix_digest", proof.lifecycle_matrix_digest),
        ("traceability_identity", proof.traceability_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("capital_slot_identity_digest", proof.capital_slot_identity_digest),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe23_proof: {field_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"pe23_proof: {field_name} must be 64-char lowercase sha256 hex")

    if proof.ratchet_evaluation_proof_digest != pe23_input.ratchet_evaluation_proof.proof_digest:
        fail_reasons.append("pe23_proof: ratchet_evaluation_proof_digest mismatch")
    if proof.release_eligibility_proof_digest != pe23_input.release_eligibility_proof.proof_digest:
        fail_reasons.append("pe23_proof: release_eligibility_proof_digest mismatch")
    if proof.reserve_topup_block_proof_digest != pe23_input.reserve_topup_block_proof.proof_digest:
        fail_reasons.append("pe23_proof: reserve_topup_block_proof_digest mismatch")
    if proof.lifecycle_matrix_digest != compute_pe23_lifecycle_matrix_digest():
        fail_reasons.append("pe23_proof: lifecycle_matrix_digest mismatch")
    if proof.traceability_identity != durable_root.run_root_digest:
        fail_reasons.append("pe23_proof: traceability_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe23_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe23_proof: completion_identity_digest mismatch")
    if proof.capital_slot_identity_digest != pe23_input.slot_identity.slot_digest:
        fail_reasons.append("pe23_proof: capital_slot_identity_digest mismatch")

    if pe23_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_lifecycle_integration_input: "
            "source_revision mismatch with completion input"
        )

    pe23_matrix = pe23_input.lifecycle_matrix_proof
    if pe23_matrix.lifecycle_state_digest != durable_root.run_root_digest:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_lifecycle_integration_input: "
            "lifecycle_state_digest mismatch with run_root_digest"
        )

    completion_pe22 = integration_input.pe22_risk_killswitch_flatten_proof
    upstream = pe23_input.pe22_upstream_safety_proof
    if upstream.integration_proof_digest != completion_pe22.integration_proof_digest:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_lifecycle_integration_input: "
            "pe22_upstream integration_proof_digest mismatch with completion pe22_proof"
        )

    ratchet_proof = pe23_input.ratchet_evaluation_proof
    reserve_proof = pe23_input.reserve_topup_block_proof
    release_proof = pe23_input.release_eligibility_proof
    if proof.capital_slot_coherence_proven is not True:
        fail_reasons.append("pe23_proof: capital_slot_coherence_proven must be true")
    elif not (
        ratchet_proof.proof_pass is True
        and reserve_proof.proof_pass is True
        and reserve_proof.reserve_topup_blocked is True
        and reserve_proof.reserve_topup_attempted is False
        and pe23_input.capital_slot_config.allow_auto_top_up is False
    ):
        fail_reasons.append("pe23_proof: capital slot coherence not proven upstream")

    if not pe23_result.get("integration_pass"):
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_lifecycle_integration_input: PE-23 evaluation failed"
        )
        fail_reasons.extend(
            f"pe23_capital_slot_ratchet_release_lifecycle_integration_input: {reason}"
            for reason in pe23_result.get("fail_reasons", [])
        )
    elif not pe23_result.get("pe12_capital_slot_ratchet_release_static_integration_proven"):
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_lifecycle_integration_input: "
            "pe12_capital_slot_ratchet_release_static_integration_proven required"
        )

    return fail_reasons


def _pe24_upstream_proofs_from_completion(
    pe22_proof: Pe22RiskKillswitchFlattenProofBinding,
    pe23_proof: Pe23CapitalSlotRatchetReleaseProofBinding,
) -> tuple[Pe24Pe22UpstreamProofBinding, Pe24Pe23UpstreamProofBinding]:
    return (
        Pe24Pe22UpstreamProofBinding(
            integration_input_digest=pe22_proof.integration_input_digest,
            integration_proof_digest=pe22_proof.integration_proof_digest,
            pe22_integration_pass=True,
            lifecycle_matrix_digest=pe22_proof.lifecycle_matrix_digest,
        ),
        Pe24Pe23UpstreamProofBinding(
            integration_input_digest=pe23_proof.integration_input_digest,
            integration_proof_digest=pe23_proof.integration_proof_digest,
            pe23_integration_pass=True,
            lifecycle_matrix_digest=pe23_proof.lifecycle_matrix_digest,
        ),
    )


def _validate_pe24_integration_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe24_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe24_pilot_envelope_lifecycle_proof
    pe24_input = integration_input.pe24_pilot_envelope_lifecycle_integration_input
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=manifest_digest,
        source_revision=integration_input.source_revision,
    )
    completion_pe22 = integration_input.pe22_risk_killswitch_flatten_proof
    completion_pe23 = integration_input.pe23_capital_slot_ratchet_release_proof

    if proof.integration_owner != PE24_INTEGRATION_OWNER:
        fail_reasons.append(f"pe24_proof: integration_owner must be {PE24_INTEGRATION_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe24_proof: source_revision mismatch")
    if not proof.integration_input_digest:
        fail_reasons.append("pe24_proof: integration_input_digest required")
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe24_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe24_integration_input_digest(pe24_input):
        fail_reasons.append("pe24_proof: integration_input_digest mismatch")

    if not proof.integration_proof_digest:
        fail_reasons.append("pe24_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe24_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe24_integration_proof_digest(
            pe24_input,
            pilot_envelope_static_ready=True,
        )
        if proof.pe24_integration_pass is not True:
            fail_reasons.append("pe24_proof: pe24_integration_pass must be true")
        elif proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append("pe24_proof: integration_proof_digest mismatch")

    if proof.pe24_integration_pass is not True:
        fail_reasons.append("pe24_proof: pe24_integration_pass must be true")
    if proof.pilot_envelope_static_ready is not True:
        fail_reasons.append("pe24_proof: pilot_envelope_static_ready must be true")

    digest_fields = (
        ("lifecycle_matrix_digest", proof.lifecycle_matrix_digest),
        ("traceability_identity", proof.traceability_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("pilot_envelope_identity_digest", proof.pilot_envelope_identity_digest),
        ("pe19_review_proof_digest", proof.pe19_review_proof_digest),
        ("pe20_package_id", proof.pe20_package_id),
        ("pe22_integration_proof_digest", proof.pe22_integration_proof_digest),
        ("pe23_integration_proof_digest", proof.pe23_integration_proof_digest),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe24_proof: {field_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"pe24_proof: {field_name} must be 64-char lowercase sha256 hex")

    if proof.lifecycle_matrix_digest != compute_pe24_lifecycle_matrix_digest():
        fail_reasons.append("pe24_proof: lifecycle_matrix_digest mismatch")
    if proof.traceability_identity != durable_root.run_root_digest:
        fail_reasons.append("pe24_proof: traceability_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe24_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe24_proof: completion_identity_digest mismatch")

    expected_pilot_envelope_identity = compute_pilot_envelope_identity_digest(
        pilot_envelope_integration_input_digest=proof.integration_input_digest,
        run_root_digest=durable_root.run_root_digest,
        completion_identity_digest=completion_identity,
        source_revision=integration_input.source_revision,
    )
    if proof.pilot_envelope_identity_digest != expected_pilot_envelope_identity:
        fail_reasons.append("pe24_proof: pilot_envelope_identity_digest mismatch")

    if proof.pe19_review_proof_digest != pe24_input.pe19_review_proof.review_proof_digest:
        fail_reasons.append("pe24_proof: pe19_review_proof_digest mismatch")
    if proof.pe20_package_id != pe24_input.pe20_durable_review_package.package_id:
        fail_reasons.append("pe24_proof: pe20_package_id mismatch")
    if proof.pe22_integration_proof_digest != completion_pe22.integration_proof_digest:
        fail_reasons.append(
            "pe24_proof: pe22_integration_proof_digest mismatch with completion pe22_proof"
        )
    if proof.pe23_integration_proof_digest != completion_pe23.integration_proof_digest:
        fail_reasons.append(
            "pe24_proof: pe23_integration_proof_digest mismatch with completion pe23_proof"
        )

    if pe24_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe24_pilot_envelope_lifecycle_integration_input: source_revision mismatch with "
            "completion input"
        )

    pe24_matrix = pe24_input.lifecycle_matrix_proof
    if pe24_matrix.lifecycle_state_digest != durable_root.run_root_digest:
        fail_reasons.append(
            "pe24_pilot_envelope_lifecycle_integration_input: lifecycle_state_digest mismatch "
            "with run_root_digest"
        )

    pe19_proof = pe24_input.pe19_review_proof
    pe20_package = pe24_input.pe20_durable_review_package
    pe24_pe22 = pe24_input.pe22_risk_killswitch_flatten_proof
    pe24_pe23 = pe24_input.pe23_capital_slot_ratchet_release_proof
    if proof.pilot_envelope_coherence_proven is not True:
        fail_reasons.append("pe24_proof: pilot_envelope_coherence_proven must be true")
    elif not (
        pe19_proof.review_valid is True
        and pe19_proof.decision == DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW
        and pe19_proof.evidence_manifest_verify_rc == 0
        and pe20_package.manifest_verify_rc == 0
        and pe20_package.static_glb016_reproducibility_satisfied is True
        and pe24_pe22.pe22_integration_pass is True
        and pe24_pe23.pe23_integration_pass is True
        and pe24_pe22.integration_proof_digest == completion_pe22.integration_proof_digest
        and pe24_pe23.integration_proof_digest == completion_pe23.integration_proof_digest
    ):
        fail_reasons.append("pe24_proof: pilot envelope coherence not proven upstream")

    if not pe24_result.get("integration_pass"):
        fail_reasons.append(
            "pe24_pilot_envelope_lifecycle_integration_input: PE-24 evaluation failed"
        )
        fail_reasons.extend(
            f"pe24_pilot_envelope_lifecycle_integration_input: {reason}"
            for reason in pe24_result.get("fail_reasons", [])
        )
    elif not pe24_result.get("pilot_envelope_static_ready"):
        fail_reasons.append(
            "pe24_pilot_envelope_lifecycle_integration_input: pilot_envelope_static_ready required"
        )
    elif not pe24_result.get("pe12_pilot_envelope_static_integration_proven"):
        fail_reasons.append(
            "pe24_pilot_envelope_lifecycle_integration_input: "
            "pe12_pilot_envelope_static_integration_proven required"
        )

    return fail_reasons


def _build_pe35_boundary_input_for_completion(
    *,
    source_revision: str,
    manifest_digest: str,
) -> HandoffStalenessRevocationRecoveryBoundaryInput:
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        compute_review_input_digest,
    )
    from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
        compute_archive_identity,
    )

    pe35_base = default_minimal_pe35_boundary_input(source_revision=source_revision)
    pe34_handoff = pe35_base.pe34_handoff
    pe19_binding = pe34_handoff.pe19_undecided_review_input
    review_input = pe19_binding.review_input
    evidence_chain = review_input.evidence_chain
    updated_archive_identity = compute_archive_identity(
        source_revision=source_revision,
        packet_digest=evidence_chain.packet_digest,
        input_capture_digest=evidence_chain.input_capture_digest,
        manifest_digest=manifest_digest,
    )
    updated_evidence = replace(
        evidence_chain,
        archive_identity=updated_archive_identity,
        archive_manifest_digest=manifest_digest,
    )
    updated_review_input = replace(review_input, evidence_chain=updated_evidence)
    updated_review_input_digest = compute_review_input_digest(updated_review_input)
    updated_pe19 = replace(pe19_binding, review_input=updated_review_input)
    updated_pe20 = replace(
        pe34_handoff.pe20_undecided_package_eligibility,
        review_input_digest=updated_review_input_digest,
    )
    updated_pe34 = replace(
        pe34_handoff,
        pe19_undecided_review_input=updated_pe19,
        pe20_undecided_package_eligibility=updated_pe20,
    )
    pe34_digest = compute_pe34_boundary_input_digest(updated_pe34)
    return replace(
        pe35_base,
        pe34_handoff=updated_pe34,
        canonical_current=replace(
            pe35_base.canonical_current,
            pe34_handoff_digest=pe34_digest,
            archive_manifest_digest=manifest_digest,
        ),
        lifecycle_metadata=replace(
            pe35_base.lifecycle_metadata,
            handoff_digest=pe34_digest,
        ),
    )


def _build_pe37_boundary_input_from_pe35(
    pe35_input: HandoffStalenessRevocationRecoveryBoundaryInput,
) -> DurableEvidenceTraceabilityBoundaryInput:
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        OperatorReviewAdmissionPresentationBoundaryInput,
        default_minimal_pe35_proof_binding,
    )
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        default_minimal_pe16_archive_binding,
        default_minimal_pe19_pe20_review_proof_binding,
        default_minimal_pe36_proof_binding,
        default_minimal_proof_chain_binding,
    )
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        EXPECTED_OPERATOR_NAME,
    )

    pe36_input = OperatorReviewAdmissionPresentationBoundaryInput(
        pe35_boundary_input=pe35_input,
        pe35_proof=default_minimal_pe35_proof_binding(pe35_input),
        operator_name_legibility=EXPECTED_OPERATOR_NAME,
    )
    return DurableEvidenceTraceabilityBoundaryInput(
        pe36_boundary_input=pe36_input,
        pe36_proof=default_minimal_pe36_proof_binding(pe36_input),
        pe16_archive_binding=default_minimal_pe16_archive_binding(pe36_input),
        pe19_pe20_review_proof=default_minimal_pe19_pe20_review_proof_binding(pe36_input),
        proof_chain=default_minimal_proof_chain_binding(pe36_input),
    )


def _build_admission_presentation_lifecycle_input_from_completion(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> Any:
    """Build canonical admission-presentation lifecycle input from completion PE-34/35/36/37."""
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
        CONTRACT_VERSION as ADMISSION_LIFECYCLE_CONTRACT_VERSION,
        ContractVersionsInput as AdmissionContractVersionsInput,
        IntegrationProofChainBinding,
        OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
        Pe34HandoffProofBinding,
        Pe35StalenessProofBinding,
        Pe36AdmissionPresentationProofBinding,
        Pe37TraceabilityProofBinding,
        default_minimal_safety_snapshot as default_admission_safety_snapshot,
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        evaluate_operator_review_admission_presentation_boundary,
    )
    from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
        evaluate_operator_review_handoff_boundary,
    )
    from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_MARKET_TYPE

    pe37_input = integration_input.pe37_traceability_boundary_input
    pe36_input = pe37_input.pe36_boundary_input
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    pe34_handoff = pe35_input.pe34_handoff
    pe24_input = integration_input.pe24_pilot_envelope_lifecycle_integration_input

    pe34_result = evaluate_operator_review_handoff_boundary(pe34_handoff)
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    pe36_result = evaluate_operator_review_admission_presentation_boundary(pe36_input)
    pe37_result = evaluate_durable_evidence_traceability_boundary(pe37_input)

    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe35_input_digest = compute_pe35_boundary_input_digest(pe35_input)
    pe36_input_digest = compute_pe36_boundary_input_digest(pe36_input)
    pe37_input_digest = compute_pe37_boundary_input_digest(pe37_input)

    proof_chain = IntegrationProofChainBinding(
        pe34_handoff_digest=pe34_digest,
        pe35_boundary_input_digest=pe35_input_digest,
        pe35_boundary_result_digest=pe35_result["boundary_result_digest"],
        pe36_boundary_input_digest=pe36_input_digest,
        pe36_boundary_result_digest=pe36_result["boundary_result_digest"],
        pe36_presentation_projection_digest=pe36_result["presentation_projection_digest"],
        pe37_boundary_input_digest=pe37_input_digest,
        pe37_boundary_result_digest=pe37_result["boundary_result_digest"],
        pe37_traceability_identity=pe37_result["traceability_identity"],
    )

    return OperatorReviewAdmissionPresentationLifecycleIntegrationInput(
        source_revision=integration_input.source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        integration_id=f"completion-admission-lifecycle-{integration_input.run_identity.run_id}",
        adapter_id=pe24_input.adapter_id,
        instrument=pe24_input.instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=AdmissionContractVersionsInput(
            pe34_handoff=PE34_CONTRACT_VERSION,
            pe35_staleness=PE35_CONTRACT_VERSION,
            pe36_admission_presentation=PE36_CONTRACT_VERSION,
            pe37_traceability=PE37_CONTRACT_VERSION,
            integration=ADMISSION_LIFECYCLE_CONTRACT_VERSION,
        ),
        pe34_handoff_input=pe34_handoff,
        pe35_boundary_input=pe35_input,
        pe36_boundary_input=pe36_input,
        pe37_traceability_boundary_input=pe37_input,
        pe34_handoff_proof=Pe34HandoffProofBinding(
            handoff_owner=PE34_HANDOFF_OWNER,
            source_revision=integration_input.source_revision,
            boundary_input_digest=pe34_digest,
            boundary_result_digest=pe34_result["boundary_result_digest"],
            pe34_integration_pass=True,
            operator_review_handoff_boundary_satisfied=True,
        ),
        pe35_staleness_proof=Pe35StalenessProofBinding(
            boundary_owner=PE35_INTEGRATION_OWNER,
            source_revision=integration_input.source_revision,
            boundary_input_digest=pe35_input_digest,
            boundary_result_digest=pe35_result["boundary_result_digest"],
            handoff_current=pe35_result["handoff_current"],
            pe35_integration_pass=True,
            handoff_staleness_revocation_recovery_boundary_satisfied=True,
        ),
        pe36_admission_presentation_proof=Pe36AdmissionPresentationProofBinding(
            boundary_owner=PE36_BOUNDARY_OWNER,
            source_revision=integration_input.source_revision,
            boundary_input_digest=pe36_input_digest,
            boundary_result_digest=pe36_result["boundary_result_digest"],
            presentation_projection_digest=pe36_result["presentation_projection_digest"],
            pe36_integration_pass=True,
            operator_review_admission_presentation_boundary_satisfied=True,
        ),
        pe37_traceability_proof=Pe37TraceabilityProofBinding(
            traceability_owner=PE37_BOUNDARY_OWNER,
            source_revision=integration_input.source_revision,
            boundary_input_digest=pe37_input_digest,
            boundary_result_digest=pe37_result["boundary_result_digest"],
            traceability_identity=pe37_result["traceability_identity"],
            admission_identity=pe37_result["admission_identity"],
            pe37_integration_pass=True,
            durable_evidence_traceability_boundary_satisfied=True,
        ),
        proof_chain=proof_chain,
        safety_snapshot=default_admission_safety_snapshot(),
    )


def _build_pe25_closure_input_from_chain(
    *,
    source_revision: str,
    run_id: str,
    run_root_digest: str,
    pe22_integration_input: RiskKillswitchLifecycleIntegrationInput,
    pe22_proof: Pe22RiskKillswitchFlattenProofBinding,
    pe23_integration_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    pe23_proof: Pe23CapitalSlotRatchetReleaseProofBinding,
    pe24_integration_input: PilotEnvelopeLifecycleIntegrationInput,
    pe24_proof: Pe24PilotEnvelopeLifecycleProofBinding,
) -> OperatorClosureLifecycleIntegrationInput:
    """Build canonical PE-25 closure input from completion PE-22/23/24 lifecycle proofs."""
    from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_MARKET_TYPE
    from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
        PHASE_READINESS_DECISION,
        PHASE_RECONCILIATION_REVIEW,
        ContractVersionsInput as Pe25ContractVersionsInput,
        DeclaredLifecycleStateBinding,
        LifecycleMatrixProof,
        LifecycleStateBinding,
        Pe19ReviewProofBinding,
        Pe20DurableReviewPackageBinding,
        Pe22RiskKillswitchFlattenProofBinding,
        Pe23CapitalSlotRatchetReleaseProofBinding,
        Pe24PilotEnvelopeProofBinding,
        compute_lifecycle_matrix_digest,
        default_minimal_safety_snapshot as default_pe25_safety_snapshot,
    )
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    )
    from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
        CONTRACT_VERSION as PE20_CONTRACT_VERSION,
    )

    pe24_pe19 = pe24_integration_input.pe19_review_proof
    pe24_pe20 = pe24_integration_input.pe20_durable_review_package
    adapter_id = pe24_integration_input.adapter_id

    return OperatorClosureLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        closure_id=f"completion-closure-{run_id}",
        instrument=pe24_integration_input.instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=Pe25ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe19_operator_review=PE19_CONTRACT_VERSION,
            pe20_review_proof_package=PE20_CONTRACT_VERSION,
            pe22_risk_killswitch_flatten=PE22_CONTRACT_VERSION,
            pe23_capital_slot_ratchet_release=PE23_CONTRACT_VERSION,
            pe24_pilot_envelope=PE24_CONTRACT_VERSION,
            integration=PE25_CONTRACT_VERSION,
        ),
        pe19_review_proof=Pe19ReviewProofBinding(
            review_input_digest=pe24_pe19.review_input_digest,
            decision_record_digest=pe24_pe19.decision_record_digest,
            review_proof_digest=pe24_pe19.review_proof_digest,
            review_valid=pe24_pe19.review_valid,
            decision=pe24_pe19.decision,
            reason_code=pe24_pe19.reason_code,
            non_authorizing=pe24_pe19.non_authorizing,
            ready_for_operator_arming=pe24_pe19.ready_for_operator_arming,
            execution_authorized=pe24_pe19.execution_authorized,
            live_authorized=pe24_pe19.live_authorized,
            evidence_manifest_verify_rc=pe24_pe19.evidence_manifest_verify_rc,
        ),
        pe20_durable_review_package=Pe20DurableReviewPackageBinding(
            package_id=pe24_pe20.package_id,
            package_digest=pe24_pe20.package_digest,
            manifest_verify_rc=pe24_pe20.manifest_verify_rc,
            static_glb016_reproducibility_satisfied=pe24_pe20.static_glb016_reproducibility_satisfied,
        ),
        pe22_risk_killswitch_flatten_proof=Pe22RiskKillswitchFlattenProofBinding(
            integration_input_digest=compute_pe22_integration_input_digest(pe22_integration_input),
            integration_proof_digest=pe22_proof.integration_proof_digest,
            pe22_integration_pass=True,
            lifecycle_matrix_digest=pe22_proof.lifecycle_matrix_digest,
        ),
        pe23_capital_slot_ratchet_release_proof=Pe23CapitalSlotRatchetReleaseProofBinding(
            integration_input_digest=compute_pe23_integration_input_digest(pe23_integration_input),
            integration_proof_digest=pe23_proof.integration_proof_digest,
            pe23_integration_pass=True,
            lifecycle_matrix_digest=pe23_proof.lifecycle_matrix_digest,
        ),
        pe24_pilot_envelope_proof=Pe24PilotEnvelopeProofBinding(
            integration_input_digest=compute_pe24_integration_input_digest(pe24_integration_input),
            integration_proof_digest=pe24_proof.integration_proof_digest,
            pe24_integration_pass=True,
            lifecycle_matrix_digest=pe24_proof.lifecycle_matrix_digest,
            pilot_envelope_static_ready=True,
        ),
        lifecycle_state_before=LifecycleStateBinding(
            state_id="completion-lifecycle-before",
            state_digest=run_root_digest,
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            adapter_id=adapter_id,
        ),
        declared_lifecycle_state_after=DeclaredLifecycleStateBinding(
            state_id="completion-lifecycle-after",
            state_digest=run_root_digest,
            assigned_lifecycle_phase=PHASE_READINESS_DECISION,
            adapter_id=adapter_id,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=compute_lifecycle_matrix_digest(),
            assigned_lifecycle_phase=PHASE_READINESS_DECISION,
            lifecycle_state_digest=run_root_digest,
        ),
        safety_snapshot=default_pe25_safety_snapshot(),
    )


def _build_pe25_closure_input_from_completion(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> OperatorClosureLifecycleIntegrationInput:
    """Build canonical PE-25 closure input from completion PE-22/23/24 lifecycle proofs."""
    return _build_pe25_closure_input_from_chain(
        source_revision=integration_input.source_revision,
        run_id=integration_input.run_identity.run_id,
        run_root_digest=integration_input.durable_run_root.run_root_digest,
        pe22_integration_input=integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        pe22_proof=integration_input.pe22_risk_killswitch_flatten_proof,
        pe23_integration_input=integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input,
        pe23_proof=integration_input.pe23_capital_slot_ratchet_release_proof,
        pe24_integration_input=integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        pe24_proof=integration_input.pe24_pilot_envelope_lifecycle_proof,
    )


def _validate_pe35_recovery_boundary_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe35_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe35_handoff_recovery_boundary_proof
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=manifest_digest,
        source_revision=integration_input.source_revision,
    )
    lifecycle = pe35_input.lifecycle_metadata
    recovery = pe35_input.recovery_proof

    if proof.boundary_owner != PE35_INTEGRATION_OWNER:
        fail_reasons.append(f"pe35_proof: boundary_owner must be {PE35_INTEGRATION_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe35_proof: source_revision mismatch")
    if not proof.boundary_input_digest:
        fail_reasons.append("pe35_proof: boundary_input_digest required")
    elif not _valid_sha256_digest(proof.boundary_input_digest):
        fail_reasons.append(
            "pe35_proof: boundary_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.boundary_input_digest != compute_pe35_boundary_input_digest(pe35_input):
        fail_reasons.append("pe35_proof: boundary_input_digest mismatch")

    if not proof.boundary_result_digest:
        fail_reasons.append("pe35_proof: boundary_result_digest required")
    elif not _valid_sha256_digest(proof.boundary_result_digest):
        fail_reasons.append(
            "pe35_proof: boundary_result_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_result_digest = compute_pe35_boundary_result_digest(
            pe35_input,
            handoff_staleness_revocation_recovery_boundary_satisfied=True,
        )
        if proof.pe35_boundary_pass is not True:
            fail_reasons.append("pe35_proof: pe35_boundary_pass must be true")
        elif proof.boundary_result_digest != expected_result_digest:
            fail_reasons.append("pe35_proof: boundary_result_digest mismatch")

    if proof.pe35_boundary_pass is not True:
        fail_reasons.append("pe35_proof: pe35_boundary_pass must be true")
    if proof.handoff_staleness_revocation_recovery_boundary_satisfied is not True:
        fail_reasons.append(
            "pe35_proof: handoff_staleness_revocation_recovery_boundary_satisfied must be true"
        )
    if proof.durable_run_primary_evidence_completion_boundary_bound is not True:
        fail_reasons.append(
            "pe35_proof: durable_run_primary_evidence_completion_boundary_bound must be true"
        )
    if proof.recovery_boundary_bound is not True:
        fail_reasons.append("pe35_proof: recovery_boundary_bound must be true")
    if proof.partial_failure_recovery_bound is not True:
        fail_reasons.append("pe35_proof: partial_failure_recovery_bound must be true")
    if proof.idempotency_bound is not True:
        fail_reasons.append("pe35_proof: idempotency_bound must be true")
    if proof.resume_boundary_bound is not True:
        fail_reasons.append("pe35_proof: resume_boundary_bound must be true")
    if proof.retry_boundary_bound is not True:
        fail_reasons.append("pe35_proof: retry_boundary_bound must be true")
    if proof.replay_boundary_bound is not True:
        fail_reasons.append("pe35_proof: replay_boundary_bound must be true")
    if proof.supersession_bound is not True:
        fail_reasons.append("pe35_proof: supersession_bound must be true")
    if proof.recovery_coherence_proven is not True:
        fail_reasons.append("pe35_proof: recovery_coherence_proven must be true")

    digest_fields = (
        ("traceability_identity", proof.traceability_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("manifest_identity_digest", proof.manifest_identity_digest),
        ("handoff_digest", proof.handoff_digest),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe35_proof: {field_name} required")
        elif field_name != "handoff_digest" and not _valid_sha256_digest(value):
            fail_reasons.append(f"pe35_proof: {field_name} must be 64-char lowercase sha256 hex")
        elif field_name == "handoff_digest" and not _valid_sha256_digest(value):
            fail_reasons.append(f"pe35_proof: {field_name} must be 64-char lowercase sha256 hex")

    if proof.traceability_identity != durable_root.run_root_digest:
        fail_reasons.append("pe35_proof: traceability_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe35_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe35_proof: completion_identity_digest mismatch")
    if proof.manifest_identity_digest != manifest_digest:
        fail_reasons.append("pe35_proof: manifest_identity_digest mismatch")

    computed_handoff_digest = compute_pe34_boundary_input_digest(pe35_input.pe34_handoff)
    if proof.handoff_digest != computed_handoff_digest:
        fail_reasons.append("pe35_proof: handoff_digest mismatch with PE-34 handoff")
    if proof.handoff_generation != lifecycle.generation:
        fail_reasons.append("pe35_proof: handoff_generation mismatch with lifecycle metadata")

    expected_recovery_generation = recovery.recovery_generation if recovery is not None else 0
    if proof.recovery_generation != expected_recovery_generation:
        fail_reasons.append("pe35_proof: recovery_generation mismatch")

    if pe35_input.pe34_handoff.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe35_handoff_staleness_revocation_recovery_boundary_input: source_revision mismatch "
            "with completion input"
        )

    canonical = pe35_input.canonical_current
    if canonical.archive_manifest_digest is not None:
        if canonical.archive_manifest_digest != manifest_digest:
            fail_reasons.append(
                "pe35_handoff_staleness_revocation_recovery_boundary_input: "
                "archive_manifest_digest mismatch with completion manifest"
            )

    if lifecycle.lifecycle_state in {
        HANDOFF_STATE_STALE,
        HANDOFF_STATE_SUPERSEDED,
        HANDOFF_STATE_REVOKED,
        HANDOFF_STATE_RECOVERY_REQUIRED,
    }:
        fail_reasons.append(
            f"pe35_proof: open partial-failure lifecycle state {lifecycle.lifecycle_state!r}"
        )
    elif lifecycle.lifecycle_state == HANDOFF_STATE_RECOVERED and recovery is None:
        fail_reasons.append("pe35_proof: recovered lifecycle_state requires recovery_proof")
    elif lifecycle.lifecycle_state not in {HANDOFF_STATE_CURRENT, HANDOFF_STATE_RECOVERED}:
        fail_reasons.append(f"pe35_proof: unknown lifecycle_state {lifecycle.lifecycle_state!r}")

    if pe35_input.active_successor_handoff_digests:
        fail_reasons.append("pe35_proof: active successor handoff digests present")
    for link in pe35_input.supersession_links:
        if link.predecessor_handoff_digest == computed_handoff_digest:
            fail_reasons.append("pe35_proof: handoff superseded by successor link")

    if not pe35_result.get("boundary_pass"):
        fail_reasons.append(
            "pe35_handoff_staleness_revocation_recovery_boundary_input: PE-35 evaluation failed"
        )
        fail_reasons.extend(
            f"pe35_handoff_staleness_revocation_recovery_boundary_input: {reason}"
            for reason in pe35_result.get("fail_reasons", [])
        )
    elif not pe35_result.get("handoff_staleness_revocation_recovery_boundary_satisfied"):
        fail_reasons.append(
            "pe35_handoff_staleness_revocation_recovery_boundary_input: "
            "handoff_staleness_revocation_recovery_boundary_satisfied required"
        )
    elif pe35_result.get("recovery_executed"):
        fail_reasons.append("pe35_proof: operative recovery must not be executed")
    elif pe35_result.get("authority_lift"):
        fail_reasons.append("pe35_proof: authority_lift must remain false")

    return fail_reasons


def _validate_pe37_traceability_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe37_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe37_traceability_proof
    pe37_input = integration_input.pe37_traceability_boundary_input
    pe36_input = pe37_input.pe36_boundary_input
    pe35_input = pe36_input.pe35_boundary_input
    pe34_handoff = pe35_input.pe34_handoff
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=manifest_digest,
        source_revision=integration_input.source_revision,
    )
    completion_pe35 = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input

    if proof.traceability_owner != PE37_BOUNDARY_OWNER:
        fail_reasons.append(f"pe37_proof: traceability_owner must be {PE37_BOUNDARY_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe37_proof: source_revision mismatch")
    if not proof.boundary_input_digest:
        fail_reasons.append("pe37_proof: boundary_input_digest required")
    elif not _valid_sha256_digest(proof.boundary_input_digest):
        fail_reasons.append(
            "pe37_proof: boundary_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.boundary_input_digest != compute_pe37_boundary_input_digest(pe37_input):
        fail_reasons.append("pe37_proof: boundary_input_digest mismatch")

    if not proof.boundary_result_digest:
        fail_reasons.append("pe37_proof: boundary_result_digest required")
    elif not _valid_sha256_digest(proof.boundary_result_digest):
        fail_reasons.append(
            "pe37_proof: boundary_result_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.boundary_result_digest != pe37_result.get("boundary_result_digest"):
        fail_reasons.append("pe37_proof: boundary_result_digest mismatch")

    required_binding_flags = (
        ("pe37_boundary_pass", True),
        ("durable_evidence_traceability_boundary_satisfied", True),
        ("pe34_handoff_bound", True),
        ("pe35_staleness_revocation_recovery_bound", True),
        ("pe36_admission_presentation_bound", True),
        ("durable_run_primary_evidence_completion_traceability_bound", True),
        ("operator_review_chain_durable_evidence_traceability_bound", True),
        ("traceability_coherence_proven", True),
    )
    for field_name, expected in required_binding_flags:
        actual = getattr(proof, field_name)
        if actual is not expected:
            fail_reasons.append(f"pe37_proof: {field_name} must be {expected}")

    digest_fields = (
        ("traceability_identity", proof.traceability_identity),
        ("admission_identity", proof.admission_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("manifest_identity_digest", proof.manifest_identity_digest),
        ("durable_artifact_identity", proof.durable_artifact_identity),
        ("review_chain_identity", proof.review_chain_identity),
        ("pe34_handoff_digest", proof.pe34_handoff_digest),
        ("pe36_boundary_result_digest", proof.pe36_boundary_result_digest),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe37_proof: {field_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"pe37_proof: {field_name} must be 64-char lowercase sha256 hex")

    expected_traceability = pe37_result.get("traceability_identity")
    if expected_traceability is None:
        fail_reasons.append("pe37_proof: traceability_identity unavailable")
    elif proof.traceability_identity != expected_traceability:
        fail_reasons.append("pe37_proof: traceability_identity mismatch")
    if proof.admission_identity != pe37_result.get("admission_identity"):
        fail_reasons.append("pe37_proof: admission_identity mismatch")
    if proof.review_chain_identity != proof.traceability_identity:
        fail_reasons.append("pe37_proof: review_chain_identity mismatch with traceability_identity")
    if proof.durable_artifact_identity != durable_root.run_root_digest:
        fail_reasons.append("pe37_proof: durable_artifact_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe37_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe37_proof: completion_identity_digest mismatch")
    if proof.manifest_identity_digest != manifest_digest:
        fail_reasons.append("pe37_proof: manifest_identity_digest mismatch")

    computed_pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    if proof.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("pe37_proof: pe34_handoff_digest mismatch with PE-34 handoff")
    computed_pe36_result = pe37_result.get("pe36_boundary_result_digest")
    if proof.pe36_boundary_result_digest != computed_pe36_result:
        fail_reasons.append("pe37_proof: pe36_boundary_result_digest mismatch")

    if compute_pe35_boundary_input_digest(completion_pe35) != compute_pe35_boundary_input_digest(
        pe35_input
    ):
        fail_reasons.append(
            "pe37_traceability_boundary_input: PE-35 boundary input drift from completion PE-35"
        )

    if pe34_handoff.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe37_traceability_boundary_input: source_revision mismatch with completion input"
        )

    pe37_archive = pe37_input.pe16_archive_binding
    if pe37_archive.archive_manifest_digest != manifest_digest:
        fail_reasons.append(
            "pe37_traceability_boundary_input: archive_manifest_digest mismatch with completion "
            "manifest"
        )

    if pe37_input.pe36_proof.boundary_owner != PE36_BOUNDARY_OWNER:
        fail_reasons.append("pe37_proof: PE-36 boundary_owner mismatch in embedded chain")
    if pe37_input.proof_chain.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("pe37_proof: proof_chain pe34_handoff_digest drift")

    if not pe37_result.get("boundary_pass"):
        fail_reasons.append("pe37_traceability_boundary_input: PE-37 evaluation failed")
        fail_reasons.extend(
            f"pe37_traceability_boundary_input: {reason}"
            for reason in pe37_result.get("fail_reasons", [])
        )
    elif not pe37_result.get("durable_evidence_traceability_boundary_satisfied"):
        fail_reasons.append(
            "pe37_traceability_boundary_input: "
            "durable_evidence_traceability_boundary_satisfied required"
        )
    elif pe37_result.get("operator_review_executed"):
        fail_reasons.append("pe37_proof: operative operator review must not be executed")
    elif pe37_result.get("admission_executed"):
        fail_reasons.append("pe37_proof: operative admission must not be executed")
    elif pe37_result.get("authority_lift"):
        fail_reasons.append("pe37_proof: authority_lift must remain false")

    return fail_reasons


def _validate_pe25_operator_closure_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe25_result: dict[str, Any],
    admission_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe25_operator_closure_proof
    pe25_input = integration_input.pe25_closure_integration_input
    pe37_proof = integration_input.pe37_traceability_proof
    pe35_proof = integration_input.pe35_handoff_recovery_boundary_proof
    durable_root = integration_input.durable_run_root
    run_identity = integration_input.run_identity
    manifest_digest = integration_input.manifest_proof.manifest_digest
    completion_identity = compute_completion_identity_digest(
        run_root_digest=durable_root.run_root_digest,
        manifest_digest=manifest_digest,
        source_revision=integration_input.source_revision,
    )
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    pe34_handoff = pe35_input.pe34_handoff
    pe22_proof = integration_input.pe22_risk_killswitch_flatten_proof
    pe23_proof = integration_input.pe23_capital_slot_ratchet_release_proof
    pe24_proof = integration_input.pe24_pilot_envelope_lifecycle_proof

    pe25_lifecycle = integration_input.pe25_proof_lifecycle
    if pe25_lifecycle.lifecycle_state not in ALLOWED_PROOF_LIFECYCLE_STATES:
        fail_reasons.append(
            f"pe25_proof_lifecycle: unsupported lifecycle state {pe25_lifecycle.lifecycle_state!r}"
        )
    if pe25_lifecycle.lifecycle_state in INVALID_PROOF_LIFECYCLE_STATES:
        fail_reasons.append(
            f"pe25_proof_lifecycle: invalid lifecycle state {pe25_lifecycle.lifecycle_state!r}"
        )

    if proof.closure_owner != PE25_INTEGRATION_OWNER:
        fail_reasons.append(f"pe25_proof: closure_owner must be {PE25_INTEGRATION_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe25_proof: source_revision mismatch")
    if not proof.closure_input_digest:
        fail_reasons.append("pe25_proof: closure_input_digest required")
    elif not _valid_sha256_digest(proof.closure_input_digest):
        fail_reasons.append("pe25_proof: closure_input_digest must be 64-char lowercase sha256 hex")
    elif proof.closure_input_digest != compute_pe25_closure_input_digest(pe25_input):
        fail_reasons.append("pe25_proof: closure_input_digest mismatch")

    if not proof.closure_result_digest:
        fail_reasons.append("pe25_proof: closure_result_digest required")
    elif not _valid_sha256_digest(proof.closure_result_digest):
        fail_reasons.append(
            "pe25_proof: closure_result_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.closure_result_digest != pe25_result.get("closure_result_digest"):
        fail_reasons.append("pe25_proof: closure_result_digest mismatch")

    expected_admission_proof = admission_result.get("integration_proof_digest")
    if not proof.admission_integration_proof_digest:
        fail_reasons.append("pe25_proof: admission_integration_proof_digest required")
    elif expected_admission_proof is None:
        fail_reasons.append("pe25_proof: admission_integration_proof_digest unavailable")
    elif proof.admission_integration_proof_digest != expected_admission_proof:
        fail_reasons.append("pe25_proof: admission_integration_proof_digest mismatch")

    required_binding_flags = (
        ("pe25_integration_pass", True),
        ("operator_closure_static_complete", True),
        ("operator_closure_lifecycle_bound", True),
        ("pe25_operator_closure_bound", True),
        ("durable_run_primary_evidence_completion_operator_closure_bound", True),
        ("pe34_handoff_bound", True),
        ("pe35_staleness_revocation_recovery_bound", True),
        ("pe36_admission_presentation_bound", True),
        ("pe37_durable_traceability_bound", True),
        ("closure_coherence_proven", True),
    )
    for field_name, expected in required_binding_flags:
        actual = getattr(proof, field_name)
        if actual is not expected:
            fail_reasons.append(f"pe25_proof: {field_name} must be {expected}")

    digest_fields = (
        ("traceability_identity", proof.traceability_identity),
        ("admission_identity", proof.admission_identity),
        ("run_identity_digest", proof.run_identity_digest),
        ("completion_identity_digest", proof.completion_identity_digest),
        ("manifest_identity_digest", proof.manifest_identity_digest),
        ("durable_artifact_identity", proof.durable_artifact_identity),
        ("pe34_handoff_digest", proof.pe34_handoff_digest),
        ("pe35_boundary_result_digest", proof.pe35_boundary_result_digest),
        ("pe36_boundary_result_digest", proof.pe36_boundary_result_digest),
        ("pe37_traceability_identity", proof.pe37_traceability_identity),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"pe25_proof: {field_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"pe25_proof: {field_name} must be 64-char lowercase sha256 hex")

    if proof.traceability_identity != pe37_proof.traceability_identity:
        fail_reasons.append("pe25_proof: traceability_identity mismatch with PE-37")
    if proof.admission_identity != pe37_proof.admission_identity:
        fail_reasons.append("pe25_proof: admission_identity mismatch with PE-37")
    if proof.durable_artifact_identity != durable_root.run_root_digest:
        fail_reasons.append("pe25_proof: durable_artifact_identity mismatch with run_root_digest")
    if proof.run_identity_digest != run_identity.run_identity_digest:
        fail_reasons.append("pe25_proof: run_identity_digest mismatch")
    if proof.completion_identity_digest != completion_identity:
        fail_reasons.append("pe25_proof: completion_identity_digest mismatch")
    if proof.manifest_identity_digest != manifest_digest:
        fail_reasons.append("pe25_proof: manifest_identity_digest mismatch")

    computed_pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    if proof.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("pe25_proof: pe34_handoff_digest mismatch with PE-34 handoff")
    if proof.pe35_boundary_result_digest != pe35_proof.boundary_result_digest:
        fail_reasons.append("pe25_proof: pe35_boundary_result_digest mismatch with PE-35")
    if proof.pe36_boundary_result_digest != pe37_proof.pe36_boundary_result_digest:
        fail_reasons.append("pe25_proof: pe36_boundary_result_digest mismatch with PE-36")
    if proof.pe37_traceability_identity != pe37_proof.traceability_identity:
        fail_reasons.append("pe25_proof: pe37_traceability_identity mismatch with PE-37")

    if pe25_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe25_closure_integration_input: source_revision mismatch with completion input"
        )
    if (
        pe25_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest
        != pe22_proof.integration_proof_digest
    ):
        fail_reasons.append("pe25_proof: PE-22 integration_proof_digest drift from completion")
    if (
        pe25_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest
        != pe23_proof.integration_proof_digest
    ):
        fail_reasons.append("pe25_proof: PE-23 integration_proof_digest drift from completion")
    if (
        pe25_input.pe24_pilot_envelope_proof.integration_proof_digest
        != pe24_proof.integration_proof_digest
    ):
        fail_reasons.append("pe25_proof: PE-24 integration_proof_digest drift from completion")
    if pe25_input.lifecycle_matrix_proof.lifecycle_state_digest != durable_root.run_root_digest:
        fail_reasons.append("pe25_proof: lifecycle_state_digest mismatch with run_root_digest")

    if compute_pe25_closure_input_digest(pe25_input) != compute_pe25_closure_input_digest(
        _build_pe25_closure_input_from_completion(integration_input)
    ):
        fail_reasons.append(
            "pe25_closure_integration_input: PE-25 closure input drift from completion chain"
        )

    if not pe25_result.get("integration_pass"):
        fail_reasons.append("pe25_closure_integration_input: PE-25 evaluation failed")
        fail_reasons.extend(
            f"pe25_closure_integration_input: {reason}"
            for reason in pe25_result.get("fail_reasons", [])
        )
    elif not pe25_result.get("operator_closure_static_complete"):
        fail_reasons.append(
            "pe25_closure_integration_input: operator_closure_static_complete required"
        )
    elif pe25_result.get("operative_operator_closure_executed"):
        fail_reasons.append("pe25_proof: operative operator closure must not be executed")
    elif pe25_result.get("authority_lift"):
        fail_reasons.append("pe25_proof: authority_lift must remain false")

    if not admission_result.get("integration_pass"):
        fail_reasons.append(
            "pe25_proof: admission presentation lifecycle evaluation failed for PE-39 coherence"
        )

    return fail_reasons


def _validate_completion_proof_chain(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    chain = integration_input.completion_proof_chain
    pe31_proof = integration_input.pe31_reconciliation_review_integration_proof
    pe22_proof = integration_input.pe22_risk_killswitch_flatten_proof
    pe23_proof = integration_input.pe23_capital_slot_ratchet_release_proof
    pe24_proof = integration_input.pe24_pilot_envelope_lifecycle_proof
    pe35_proof = integration_input.pe35_handoff_recovery_boundary_proof
    pe37_proof = integration_input.pe37_traceability_proof
    pe25_proof = integration_input.pe25_operator_closure_proof
    pe21_proof = integration_input.pe21_proof
    pe31_pe21_proof = integration_input.pe31_reconciliation_review_integration_input.pe21_reconciliation_primary_evidence_integration_proof
    pe21_input_digest = compute_pe21_integration_input_digest(
        integration_input.pe21_integration_input
    )

    digest_fields = (
        ("completion_referenced_pe31_proof_digest", chain.completion_referenced_pe31_proof_digest),
        ("completion_referenced_pe22_proof_digest", chain.completion_referenced_pe22_proof_digest),
        ("completion_referenced_pe23_proof_digest", chain.completion_referenced_pe23_proof_digest),
        ("completion_referenced_pe24_proof_digest", chain.completion_referenced_pe24_proof_digest),
        (
            "completion_referenced_pe35_boundary_result_digest",
            chain.completion_referenced_pe35_boundary_result_digest,
        ),
        (
            "completion_referenced_pe37_boundary_result_digest",
            chain.completion_referenced_pe37_boundary_result_digest,
        ),
        ("pe37_traceability_identity", chain.pe37_traceability_identity),
        (
            "completion_referenced_pe25_closure_result_digest",
            chain.completion_referenced_pe25_closure_result_digest,
        ),
        ("pe25_closure_input_digest", chain.pe25_closure_input_digest),
        (
            "closure_referenced_admission_proof_digest",
            chain.closure_referenced_admission_proof_digest,
        ),
        (
            "pe31_referenced_pe21_integration_proof_digest",
            chain.pe31_referenced_pe21_integration_proof_digest,
        ),
        (
            "completion_referenced_pe21_integration_proof_digest",
            chain.completion_referenced_pe21_integration_proof_digest,
        ),
        ("shared_pe21_integration_input_digest", chain.shared_pe21_integration_input_digest),
        ("shared_traceability_identity", chain.shared_traceability_identity),
    )
    for field_name, value in digest_fields:
        if not value:
            fail_reasons.append(f"completion_proof_chain: {field_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(
                f"completion_proof_chain: {field_name} must be 64-char lowercase sha256 hex"
            )

    if chain.completion_referenced_pe31_proof_digest != pe31_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe31_proof_digest mismatch"
        )
    if chain.completion_referenced_pe22_proof_digest != pe22_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe22_proof_digest mismatch"
        )
    if chain.completion_referenced_pe23_proof_digest != pe23_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe23_proof_digest mismatch"
        )
    if chain.completion_referenced_pe24_proof_digest != pe24_proof.integration_proof_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe24_proof_digest mismatch"
        )
    if chain.completion_referenced_pe35_boundary_result_digest != pe35_proof.boundary_result_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe35_boundary_result_digest mismatch"
        )
    if chain.completion_referenced_pe37_boundary_result_digest != pe37_proof.boundary_result_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe37_boundary_result_digest mismatch"
        )
    if chain.pe37_traceability_identity != pe37_proof.traceability_identity:
        fail_reasons.append("completion_proof_chain: pe37_traceability_identity mismatch")
    if chain.completion_referenced_pe25_closure_result_digest != pe25_proof.closure_result_digest:
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe25_closure_result_digest mismatch"
        )
    if chain.pe25_closure_input_digest != pe25_proof.closure_input_digest:
        fail_reasons.append("completion_proof_chain: pe25_closure_input_digest mismatch")
    if (
        chain.closure_referenced_admission_proof_digest
        != pe25_proof.admission_integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: closure_referenced_admission_proof_digest mismatch"
        )
    if (
        chain.pe31_referenced_pe21_integration_proof_digest
        != pe31_pe21_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: pe31_referenced_pe21_integration_proof_digest mismatch"
        )
    if (
        chain.completion_referenced_pe21_integration_proof_digest
        != pe21_proof.integration_proof_digest
    ):
        fail_reasons.append(
            "completion_proof_chain: completion_referenced_pe21_integration_proof_digest mismatch"
        )
    if chain.shared_pe21_integration_input_digest != pe21_input_digest:
        fail_reasons.append("completion_proof_chain: shared_pe21_integration_input_digest mismatch")
    if chain.shared_traceability_identity != integration_input.durable_run_root.run_root_digest:
        fail_reasons.append("completion_proof_chain: shared_traceability_identity mismatch")

    return fail_reasons


def _validate_gap4_completion_proof(
    gap4: Gap4CompletionProofBinding,
    *,
    source_revision: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if gap4.gap4_owner != GAP4_COMPLETION_OWNER:
        fail_reasons.append(f"gap4_completion: gap4_owner must be {GAP4_COMPLETION_OWNER!r}")
    if gap4.source_revision != source_revision:
        fail_reasons.append("gap4_completion: source_revision mismatch")
    required_flags = (
        ("output_evidence_depends_on_gap2a1", True),
        ("completion_invalid_without_durable_primary_evidence", True),
        ("completion_invalid_without_manifest_verify", True),
        ("durable_output_required_for_future_runs", True),
        ("gap4_output_evidence_paths_verified", False),
        ("gap4_integration_pass", True),
    )
    for field_name, expected in required_flags:
        actual = getattr(gap4, field_name)
        if actual is not expected:
            fail_reasons.append(f"gap4_completion: {field_name} must be {expected}")
    return fail_reasons


def _validate_gap2a1_enforcement_proof(
    gap2a1: Gap2a1EnforcementProofBinding,
    *,
    source_revision: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if gap2a1.gap2a1_owner != GAP2A1_ENFORCEMENT_OWNER:
        fail_reasons.append(
            f"gap2a1_enforcement: gap2a1_owner must be {GAP2A1_ENFORCEMENT_OWNER!r}"
        )
    if gap2a1.source_revision != source_revision:
        fail_reasons.append("gap2a1_enforcement: source_revision mismatch")
    required_flags = (
        ("primary_evidence_enforced", False),
        ("enforcement_default_on", False),
        ("enforcement_opt_in_only", True),
        ("tmp_only_evidence_invalid", True),
        ("manifest_verify_required", True),
        ("checksum_verify_required", True),
        ("run_incomplete_without_primary_evidence", True),
        ("gap2a1_integration_pass", True),
    )
    for field_name, expected in required_flags:
        actual = getattr(gap2a1, field_name)
        if actual is not expected:
            fail_reasons.append(f"gap2a1_enforcement: {field_name} must be {expected}")
    return fail_reasons


def validate_durable_run_primary_evidence_completion_integration_input(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    extra_field_names: tuple[str, ...] = (),
) -> list[str]:
    """Fail-closed validation of explicit completion integration input bindings."""
    fail_reasons: list[str] = []

    for field_name in extra_field_names:
        lowered = field_name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_EXTRA_FIELD_FRAGMENTS):
            fail_reasons.append(f"forbidden extra field: {field_name!r}")

    if not integration_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(integration_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if integration_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")

    fail_reasons.extend(_validate_run_type(integration_input.run_type))

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(integration_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    run_identity = integration_input.run_identity
    if not run_identity.run_id:
        fail_reasons.append("run_identity: run_id required")
    if not run_identity.run_identity_digest:
        fail_reasons.append("run_identity: run_identity_digest required")
    elif not _valid_sha256_digest(run_identity.run_identity_digest):
        fail_reasons.append(
            "run_identity: run_identity_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_run_identity_digest = compute_run_identity_digest(
            run_id=run_identity.run_id,
            run_type=integration_input.run_type,
            source_revision=integration_input.source_revision,
        )
        if run_identity.run_identity_digest != expected_run_identity_digest:
            fail_reasons.append("run_identity: run_identity_digest mismatch")

    durable_root = integration_input.durable_run_root
    fail_reasons.extend(
        _validate_archive_root_identity(
            durable_root.durable_archive_root,
            durable_root.run_root_identity,
        )
    )
    if not durable_root.run_root_digest:
        fail_reasons.append("durable_run_root: run_root_digest required")
    elif not _valid_sha256_digest(durable_root.run_root_digest):
        fail_reasons.append(
            "durable_run_root: run_root_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_run_root_digest = compute_run_root_digest(
            durable_archive_root=durable_root.durable_archive_root,
            run_root_identity=durable_root.run_root_identity,
            source_revision=integration_input.source_revision,
        )
        if durable_root.run_root_digest != expected_run_root_digest:
            fail_reasons.append("durable_run_root: run_root_digest mismatch")

    pe_identity = integration_input.primary_evidence_identity
    if not pe_identity.primary_evidence_identity:
        fail_reasons.append("primary_evidence_identity required")
    elif not _valid_sha256_digest(pe_identity.primary_evidence_identity):
        fail_reasons.append("primary_evidence_identity must be 64-char lowercase sha256 hex")
    else:
        expected_pe_identity = compute_primary_evidence_identity_digest(
            primary_evidence_identity=durable_root.run_root_identity,
            primary_evidence_owner=pe_identity.primary_evidence_owner,
            retention_contract_version=pe_identity.retention_contract_version,
            source_revision=integration_input.source_revision,
        )
        if pe_identity.primary_evidence_identity != expected_pe_identity:
            fail_reasons.append("primary_evidence_identity digest mismatch")

    if integration_input.evidence_mode not in ALLOWED_EVIDENCE_MODES:
        fail_reasons.append(f"evidence_mode must be one of {sorted(ALLOWED_EVIDENCE_MODES)!r}")

    lifecycle = integration_input.proof_lifecycle
    if lifecycle.lifecycle_state not in ALLOWED_PROOF_LIFECYCLE_STATES:
        fail_reasons.append(f"unsupported proof lifecycle state {lifecycle.lifecycle_state!r}")
    if lifecycle.lifecycle_state in INVALID_PROOF_LIFECYCLE_STATES:
        fail_reasons.append(f"invalid proof lifecycle state {lifecycle.lifecycle_state!r}")

    fail_reasons.extend(
        _validate_manifest_and_artifacts(
            integration_input.manifest_proof,
            integration_input.artifact_checksums,
        )
    )

    post_write = integration_input.post_write_verification
    if post_write.post_write_verification_pass is not True:
        fail_reasons.append("post_write_verification_pass must be true")
    if post_write.manifest_verify_rc != 0:
        fail_reasons.append("post_write_verification.manifest_verify_rc must be 0")
    if post_write.manifest_verify_rc != integration_input.manifest_proof.manifest_verify_rc:
        fail_reasons.append("manifest_verify_rc drift between manifest and post-write proof")

    pe21_input = integration_input.pe21_integration_input
    if pe21_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe21_integration_input: source_revision mismatch with completion input"
        )
    fail_reasons.extend(validate_reconciliation_primary_evidence_integration_input(pe21_input))

    pe21_binding = pe21_input.primary_evidence_binding
    if pe21_binding.durable_archive_root != durable_root.durable_archive_root:
        fail_reasons.append("pe21 durable_archive_root mismatch with durable_run_root")
    fail_reasons.extend(validate_primary_evidence_binding(pe21_binding))
    fail_reasons.extend(_validate_pe21_reconciliation_result_manifest_integrity(integration_input))

    pe31_input = integration_input.pe31_reconciliation_review_integration_input
    if pe31_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: source_revision mismatch with "
            "completion input"
        )

    pe22_input = integration_input.pe22_risk_killswitch_lifecycle_integration_input
    if pe22_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe22_risk_killswitch_lifecycle_integration_input: source_revision mismatch with "
            "completion input"
        )

    pe23_input = integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    if pe23_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_lifecycle_integration_input: source_revision "
            "mismatch with completion input"
        )

    pe24_input = integration_input.pe24_pilot_envelope_lifecycle_integration_input
    if pe24_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe24_pilot_envelope_lifecycle_integration_input: source_revision mismatch with "
            "completion input"
        )

    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    if pe35_input.pe34_handoff.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe35_handoff_staleness_revocation_recovery_boundary_input: source_revision mismatch "
            "with completion input"
        )

    pe37_input = integration_input.pe37_traceability_boundary_input
    if (
        pe37_input.pe36_boundary_input.pe35_boundary_input.pe34_handoff.source_revision
        != integration_input.source_revision
    ):
        fail_reasons.append(
            "pe37_traceability_boundary_input: source_revision mismatch with completion input"
        )
    fail_reasons.extend(validate_durable_evidence_traceability_boundary_input(pe37_input))

    pe25_input = integration_input.pe25_closure_integration_input
    if pe25_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe25_closure_integration_input: source_revision mismatch with completion input"
        )
    fail_reasons.extend(validate_operator_closure_lifecycle_integration_input(pe25_input))

    fail_reasons.extend(_validate_completion_proof_chain(integration_input))

    fail_reasons.extend(
        _validate_pe16_archive_proof(
            integration_input.pe16_archive,
            source_revision=integration_input.source_revision,
            primary_evidence_identity=integration_input.primary_evidence_identity,
            run_root_identity=durable_root.run_root_identity,
            manifest_digest=integration_input.manifest_proof.manifest_digest,
        )
    )
    fail_reasons.extend(
        _validate_gap4_completion_proof(
            integration_input.gap4_completion,
            source_revision=integration_input.source_revision,
        )
    )
    fail_reasons.extend(
        _validate_gap2a1_enforcement_proof(
            integration_input.gap2a1_enforcement,
            source_revision=integration_input.source_revision,
        )
    )
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    if integration_input.evidence_mode != EVIDENCE_MODE_DURABLE:
        fail_reasons.append(f"evidence_mode must be {EVIDENCE_MODE_DURABLE!r} for completion")
    if integration_input.evidence_mode in {
        EVIDENCE_MODE_PLANNED,
        EVIDENCE_MODE_SIMULATED,
        EVIDENCE_MODE_TMP_ONLY,
    }:
        fail_reasons.append(
            f"evidence_mode {integration_input.evidence_mode!r} cannot satisfy completion"
        )

    if (
        integration_input.completion_claimed
        and integration_input.evidence_mode != EVIDENCE_MODE_DURABLE
    ):
        fail_reasons.append("completion_claimed=true requires durable evidence_mode")

    return _sorted_unique(fail_reasons)


def _integration_input_dict(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> dict[str, Any]:
    return {
        "artifact_checksums": [asdict(entry) for entry in integration_input.artifact_checksums],
        "completion_claimed": integration_input.completion_claimed,
        "contract_versions": asdict(integration_input.contract_versions),
        "durable_run_root": asdict(integration_input.durable_run_root),
        "environment": integration_input.environment,
        "evidence_mode": integration_input.evidence_mode,
        "futures_only": integration_input.futures_only,
        "gap2a1_enforcement": asdict(integration_input.gap2a1_enforcement),
        "gap4_completion": asdict(integration_input.gap4_completion),
        "integration_contract_version": CONTRACT_VERSION,
        "manifest_proof": asdict(integration_input.manifest_proof),
        "non_authorizing": integration_input.non_authorizing,
        "pe16_archive": asdict(integration_input.pe16_archive),
        "pe21_proof": asdict(integration_input.pe21_proof),
        "pe31_integration_input_digest": compute_pe31_integration_input_digest(
            integration_input.pe31_reconciliation_review_integration_input
        ),
        "pe31_reconciliation_review_integration_proof": asdict(
            integration_input.pe31_reconciliation_review_integration_proof
        ),
        "pe22_integration_input_digest": compute_pe22_integration_input_digest(
            integration_input.pe22_risk_killswitch_lifecycle_integration_input
        ),
        "pe22_risk_killswitch_flatten_proof": asdict(
            integration_input.pe22_risk_killswitch_flatten_proof
        ),
        "pe23_integration_input_digest": compute_pe23_integration_input_digest(
            integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
        ),
        "pe23_capital_slot_ratchet_release_proof": asdict(
            integration_input.pe23_capital_slot_ratchet_release_proof
        ),
        "pe24_integration_input_digest": compute_pe24_integration_input_digest(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input
        ),
        "pe24_pilot_envelope_lifecycle_proof": asdict(
            integration_input.pe24_pilot_envelope_lifecycle_proof
        ),
        "pe35_boundary_input_digest": compute_pe35_boundary_input_digest(
            integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
        ),
        "pe35_handoff_recovery_boundary_proof": asdict(
            integration_input.pe35_handoff_recovery_boundary_proof
        ),
        "pe37_boundary_input_digest": compute_pe37_boundary_input_digest(
            integration_input.pe37_traceability_boundary_input
        ),
        "pe37_traceability_proof": asdict(integration_input.pe37_traceability_proof),
        "pe25_closure_input_digest": compute_pe25_closure_input_digest(
            integration_input.pe25_closure_integration_input
        ),
        "pe25_operator_closure_proof": asdict(integration_input.pe25_operator_closure_proof),
        "pe25_proof_lifecycle": asdict(integration_input.pe25_proof_lifecycle),
        "completion_proof_chain": asdict(integration_input.completion_proof_chain),
        "post_write_verification": asdict(integration_input.post_write_verification),
        "primary_evidence_identity": asdict(integration_input.primary_evidence_identity),
        "proof_lifecycle": asdict(integration_input.proof_lifecycle),
        "repository_identity": integration_input.repository_identity,
        "run_identity": asdict(integration_input.run_identity),
        "run_type": integration_input.run_type,
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
    }


def serialize_completion_integration_input_canonical(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input), sort_keys=True, separators=(",", ":")
    )


def compute_completion_integration_input_digest(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_completion_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _integration_proof_dict(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    integration_pass: bool,
    completion_static_proven: bool,
) -> dict[str, Any]:
    return {
        "completion_integration_owner": COMPLETION_INTEGRATION_OWNER,
        "completion_static_proven": completion_static_proven,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "durable_run_primary_evidence_completion_integration_pass": integration_pass,
        "durable_run_primary_evidence_completion_bound": integration_pass,
        "pe21_reconciliation_primary_evidence_bound": integration_pass,
        "pe31_reconciliation_review_bound": integration_pass,
        "pe22_risk_killswitch_flatten_lifecycle_bound": integration_pass,
        "pe23_capital_slot_ratchet_release_lifecycle_bound": integration_pass,
        "pe24_pilot_envelope_lifecycle_bound": integration_pass,
        "pe35_handoff_recovery_boundary_bound": integration_pass,
        "recovery_boundary_bound": integration_pass,
        "partial_failure_recovery_bound": integration_pass,
        "pe37_operator_review_chain_durable_evidence_traceability_bound": integration_pass,
        "pe34_handoff_bound": integration_pass,
        "pe35_staleness_revocation_recovery_bound": integration_pass,
        "pe36_admission_presentation_bound": integration_pass,
        "pe25_operator_closure_lifecycle_bound": integration_pass,
        "global_run_completion_readiness": GLOBAL_RUN_COMPLETION_READINESS,
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_completion_integration_input_digest(integration_input),
        "manifest_digest": integration_input.manifest_proof.manifest_digest,
        "operative_run_completion_recorded": OPERATIVE_RUN_COMPLETION_RECORDED,
        "pe31_integration_pass": integration_pass,
        "pe22_integration_pass": integration_pass,
        "pe23_integration_pass": integration_pass,
        "primary_evidence_operationally_accepted": PRIMARY_EVIDENCE_OPERATIONALLY_ACCEPTED,
        "reconciliation_executed": RECONCILIATION_EXECUTED,
        "risk_evaluation_executed": RISK_EVALUATION_EXECUTED,
        "killswitch_triggered": KILLSWITCH_TRIGGERED,
        "flatten_executed": FLATTEN_EXECUTED,
        "capital_slot_ratchet_executed": CAPITAL_SLOT_RATCHET_EXECUTED,
        "capital_slot_release_executed": CAPITAL_SLOT_RELEASE_EXECUTED,
        "capital_reallocation_executed": CAPITAL_REALLOCATION_EXECUTED,
        "reserve_top_up_executed": RESERVE_TOP_UP_EXECUTED,
        "pilot_envelope_executed": PILOT_ENVELOPE_EXECUTED,
        "pilot_started": PILOT_STARTED,
        "recovery_executed": RECOVERY_EXECUTED,
        "resume_executed": RESUME_EXECUTED,
        "retry_executed": RETRY_EXECUTED,
        "replay_executed": REPLAY_EXECUTED,
        "state_mutated": STATE_MUTATED,
        "partial_failure_operationally_resolved": PARTIAL_FAILURE_OPERATIONALLY_RESOLVED,
        "run_identity_digest": integration_input.run_identity.run_identity_digest,
        "run_root_digest": integration_input.durable_run_root.run_root_digest,
        "run_type": integration_input.run_type,
        "source_revision": integration_input.source_revision,
        "non_authorizing": True,
    }


def compute_completion_integration_proof_digest(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    integration_pass: bool,
    completion_static_proven: bool,
) -> str:
    return hashlib.sha256(
        json.dumps(
            _integration_proof_dict(
                integration_input,
                integration_pass=integration_pass,
                completion_static_proven=completion_static_proven,
            ),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def evaluate_durable_run_primary_evidence_completion_integration(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    completion_claim_without_full_evidence: bool = False,
    extra_field_names: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Evaluate explicit durable run primary evidence completion integration proof."""
    fail_reasons = validate_durable_run_primary_evidence_completion_integration_input(
        integration_input,
        extra_field_names=extra_field_names,
    )

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    pe21_result = evaluate_position_order_reconciliation_primary_evidence_integration(
        integration_input.pe21_integration_input
    )
    fail_reasons.extend(
        _validate_pe21_proof_binding(
            integration_input.pe21_proof,
            source_revision=integration_input.source_revision,
            pe21_result=pe21_result,
        )
    )

    pe31_result = evaluate_reconciliation_review_lifecycle_integration(
        integration_input.pe31_reconciliation_review_integration_input
    )
    fail_reasons.extend(
        _validate_pe31_integration_proof(
            integration_input,
            pe31_result=pe31_result,
        )
    )

    pe22_result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input
    )
    fail_reasons.extend(
        _validate_pe22_integration_proof(
            integration_input,
            pe22_result=pe22_result,
        )
    )

    pe23_result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    )
    fail_reasons.extend(
        _validate_pe23_integration_proof(
            integration_input,
            pe23_result=pe23_result,
        )
    )

    pe24_result = evaluate_pilot_envelope_lifecycle_integration(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input
    )
    fail_reasons.extend(
        _validate_pe24_integration_proof(
            integration_input,
            pe24_result=pe24_result,
        )
    )

    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(
        integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    )
    fail_reasons.extend(
        _validate_pe35_recovery_boundary_proof(
            integration_input,
            pe35_result=pe35_result,
        )
    )

    pe37_result = evaluate_durable_evidence_traceability_boundary(
        integration_input.pe37_traceability_boundary_input
    )
    fail_reasons.extend(
        _validate_pe37_traceability_proof(
            integration_input,
            pe37_result=pe37_result,
        )
    )

    admission_input = _build_admission_presentation_lifecycle_input_from_completion(
        integration_input
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
        evaluate_operator_review_admission_presentation_lifecycle_integration,
    )

    admission_result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        admission_input
    )
    pe25_result = evaluate_operator_closure_lifecycle_integration(
        integration_input.pe25_closure_integration_input
    )
    fail_reasons.extend(
        _validate_pe25_operator_closure_proof(
            integration_input,
            pe25_result=pe25_result,
            admission_result=admission_result,
        )
    )

    if completion_claim_without_full_evidence and integration_input.completion_claimed:
        fail_reasons.append("completion_claimed=true without full evidence chain is insufficient")

    if integration_input.completion_claimed and fail_reasons:
        fail_reasons.append("completion_claimed=true with validation failures")

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    completion_static_proven = integration_pass and integration_input.completion_claimed

    return {
        "integration_pass": integration_pass,
        "completion_static_proven": completion_static_proven,
        "completion_claimed": integration_input.completion_claimed and completion_static_proven,
        "integration_input_digest": compute_completion_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_completion_integration_proof_digest(
                integration_input,
                integration_pass=integration_pass,
                completion_static_proven=completion_static_proven,
            )
            if integration_pass
            else None
        ),
        "pe21_integration_pass": pe21_result.get("integration_pass"),
        "pe31_integration_pass": pe31_result.get("integration_pass"),
        "pe22_integration_pass": pe22_result.get("integration_pass"),
        "pe23_integration_pass": pe23_result.get("integration_pass"),
        "pe24_integration_pass": pe24_result.get("integration_pass"),
        "pe35_boundary_pass": pe35_result.get("boundary_pass"),
        "pe37_boundary_pass": pe37_result.get("boundary_pass"),
        "durable_run_primary_evidence_completion_bound": integration_pass,
        "pe21_reconciliation_primary_evidence_bound": bool(pe21_result.get("integration_pass")),
        "pe31_reconciliation_review_bound": bool(pe31_result.get("integration_pass")),
        "pe22_risk_killswitch_flatten_lifecycle_bound": bool(pe22_result.get("integration_pass")),
        "pe23_capital_slot_ratchet_release_lifecycle_bound": bool(
            pe23_result.get("integration_pass")
        ),
        "pe24_pilot_envelope_lifecycle_bound": bool(pe24_result.get("integration_pass")),
        "pe35_handoff_recovery_boundary_bound": bool(
            pe35_result.get("handoff_staleness_revocation_recovery_boundary_satisfied")
        ),
        "recovery_boundary_bound": bool(
            pe35_result.get("handoff_staleness_revocation_recovery_boundary_satisfied")
        ),
        "partial_failure_recovery_bound": bool(pe35_result.get("boundary_pass")),
        "pe37_operator_review_chain_durable_evidence_traceability_bound": bool(
            pe37_result.get("durable_evidence_traceability_boundary_satisfied")
        ),
        "pe34_handoff_bound": bool(pe37_result.get("boundary_pass")),
        "pe35_staleness_revocation_recovery_bound": bool(pe37_result.get("proof_digests_coherent")),
        "pe36_admission_presentation_bound": bool(pe37_result.get("owner_identities_coherent")),
        "pe25_operator_closure_lifecycle_bound": bool(
            pe25_result.get("operator_closure_static_complete")
        ),
        "pe16_archive_identity": integration_input.pe16_archive.archive_identity,
        "gap4_completion_integration_pass": integration_input.gap4_completion.gap4_integration_pass,
        "gap2a1_enforcement_integration_pass": (
            integration_input.gap2a1_enforcement.gap2a1_integration_pass
        ),
        "manifest_digest": integration_input.manifest_proof.manifest_digest,
        "run_identity_digest": integration_input.run_identity.run_identity_digest,
        "run_root_digest": integration_input.durable_run_root.run_root_digest,
        "global_run_completion_readiness": GLOBAL_RUN_COMPLETION_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_run_completion_recorded": OPERATIVE_RUN_COMPLETION_RECORDED,
        "primary_evidence_operationally_accepted": PRIMARY_EVIDENCE_OPERATIONALLY_ACCEPTED,
        "reconciliation_executed": RECONCILIATION_EXECUTED,
        "risk_evaluation_executed": RISK_EVALUATION_EXECUTED,
        "killswitch_triggered": KILLSWITCH_TRIGGERED,
        "flatten_executed": FLATTEN_EXECUTED,
        "capital_slot_ratchet_executed": CAPITAL_SLOT_RATCHET_EXECUTED,
        "capital_slot_release_executed": CAPITAL_SLOT_RELEASE_EXECUTED,
        "capital_reallocation_executed": CAPITAL_REALLOCATION_EXECUTED,
        "reserve_top_up_executed": RESERVE_TOP_UP_EXECUTED,
        "pilot_envelope_executed": PILOT_ENVELOPE_EXECUTED,
        "pilot_started": PILOT_STARTED,
        "recovery_executed": RECOVERY_EXECUTED,
        "resume_executed": RESUME_EXECUTED,
        "retry_executed": RETRY_EXECUTED,
        "replay_executed": REPLAY_EXECUTED,
        "state_mutated": STATE_MUTATED,
        "partial_failure_operationally_resolved": PARTIAL_FAILURE_OPERATIONALLY_RESOLVED,
        "archive_read": ARCHIVE_READ,
        "archive_written": ARCHIVE_WRITTEN,
        "manifest_read": MANIFEST_READ,
        "manifest_written": MANIFEST_WRITTEN,
        "filesystem_accessed": FILESYSTEM_ACCESSED,
        "run_started": RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": PREFLIGHT_REMAINS_BLOCKED,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "evidence_acceptance_authorized": False,
        "fail_reasons": fail_reasons,
    }


def default_minimal_safety_snapshot() -> CompletionSafetySnapshot:
    return CompletionSafetySnapshot(
        preflight_remains_blocked=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        evidence_acceptance_authorized=False,
        promotion_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def default_minimal_pe31_integration_proof(
    pe31_input: ReconciliationReviewLifecycleIntegrationInput,
) -> Pe31ReconciliationReviewIntegrationProofBinding:
    return Pe31ReconciliationReviewIntegrationProofBinding(
        integration_owner=PE31_INTEGRATION_OWNER,
        integration_input_digest=compute_pe31_integration_input_digest(pe31_input),
        integration_proof_digest=compute_pe31_integration_proof_digest(
            pe31_input,
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review=True,
        ),
        pe31_integration_pass=True,
        reconciliation_review_lifecycle_eligibility=True,
    )


def default_minimal_pe22_integration_proof(
    pe22_input: RiskKillswitchLifecycleIntegrationInput,
    *,
    traceability_identity: str,
    run_identity_digest: str,
) -> Pe22RiskKillswitchFlattenProofBinding:
    return Pe22RiskKillswitchFlattenProofBinding(
        integration_owner=PE22_INTEGRATION_OWNER,
        source_revision=pe22_input.source_revision,
        integration_input_digest=compute_pe22_integration_input_digest(pe22_input),
        integration_proof_digest=compute_pe22_integration_proof_digest(pe22_input),
        pe22_integration_pass=True,
        risk_evaluation_proof_digest=pe22_input.risk_evaluation_proof.proof_digest,
        killswitch_evaluation_proof_digest=pe22_input.killswitch_evaluation_proof.proof_digest,
        flatten_state_proof_digest=pe22_input.flatten_state_proof.proof_digest,
        lifecycle_matrix_digest=compute_pe22_lifecycle_matrix_digest(),
        traceability_identity=traceability_identity,
        run_identity_digest=run_identity_digest,
        safe_completion_state_proven=True,
    )


def default_minimal_pe23_integration_proof(
    pe23_input: CapitalSlotRatchetReleaseLifecycleIntegrationInput,
    *,
    traceability_identity: str,
    run_identity_digest: str,
    completion_identity_digest: str,
) -> Pe23CapitalSlotRatchetReleaseProofBinding:
    release_eligible = pe23_input.release_eligibility_proof.release_eligible
    return Pe23CapitalSlotRatchetReleaseProofBinding(
        integration_owner=PE23_INTEGRATION_OWNER,
        source_revision=pe23_input.source_revision,
        integration_input_digest=compute_pe23_integration_input_digest(pe23_input),
        integration_proof_digest=compute_pe23_integration_proof_digest(
            pe23_input,
            pe23_proven=True,
            release_eligibility_proven=release_eligible,
        ),
        pe23_integration_pass=True,
        ratchet_evaluation_proof_digest=pe23_input.ratchet_evaluation_proof.proof_digest,
        release_eligibility_proof_digest=pe23_input.release_eligibility_proof.proof_digest,
        reserve_topup_block_proof_digest=pe23_input.reserve_topup_block_proof.proof_digest,
        lifecycle_matrix_digest=compute_pe23_lifecycle_matrix_digest(),
        traceability_identity=traceability_identity,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        capital_slot_identity_digest=pe23_input.slot_identity.slot_digest,
        capital_slot_coherence_proven=True,
    )


def default_minimal_pe24_integration_proof(
    pe24_input: PilotEnvelopeLifecycleIntegrationInput,
    *,
    traceability_identity: str,
    run_identity_digest: str,
    completion_identity_digest: str,
    pe22_integration_proof_digest: str,
    pe23_integration_proof_digest: str,
) -> Pe24PilotEnvelopeLifecycleProofBinding:
    integration_input_digest = compute_pe24_integration_input_digest(pe24_input)
    return Pe24PilotEnvelopeLifecycleProofBinding(
        integration_owner=PE24_INTEGRATION_OWNER,
        source_revision=pe24_input.source_revision,
        integration_input_digest=integration_input_digest,
        integration_proof_digest=compute_pe24_integration_proof_digest(
            pe24_input,
            pilot_envelope_static_ready=True,
        ),
        pe24_integration_pass=True,
        pilot_envelope_static_ready=True,
        lifecycle_matrix_digest=compute_pe24_lifecycle_matrix_digest(),
        traceability_identity=traceability_identity,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        pilot_envelope_identity_digest=compute_pilot_envelope_identity_digest(
            pilot_envelope_integration_input_digest=integration_input_digest,
            run_root_digest=traceability_identity,
            completion_identity_digest=completion_identity_digest,
            source_revision=pe24_input.source_revision,
        ),
        pe19_review_proof_digest=pe24_input.pe19_review_proof.review_proof_digest,
        pe20_package_id=pe24_input.pe20_durable_review_package.package_id,
        pe22_integration_proof_digest=pe22_integration_proof_digest,
        pe23_integration_proof_digest=pe23_integration_proof_digest,
        pilot_envelope_coherence_proven=True,
    )


def default_minimal_pe35_integration_proof(
    pe35_input: HandoffStalenessRevocationRecoveryBoundaryInput,
    *,
    traceability_identity: str,
    run_identity_digest: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
) -> Pe35HandoffRecoveryBoundaryProofBinding:
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    boundary_result_digest = pe35_result["boundary_result_digest"]
    if boundary_result_digest is None:
        raise ValueError("PE-35 boundary must be satisfied for default minimal proof")
    lifecycle = pe35_input.lifecycle_metadata
    recovery = pe35_input.recovery_proof
    return Pe35HandoffRecoveryBoundaryProofBinding(
        boundary_owner=PE35_INTEGRATION_OWNER,
        source_revision=pe35_input.pe34_handoff.source_revision,
        boundary_input_digest=compute_pe35_boundary_input_digest(pe35_input),
        boundary_result_digest=boundary_result_digest,
        pe35_boundary_pass=True,
        handoff_staleness_revocation_recovery_boundary_satisfied=True,
        durable_run_primary_evidence_completion_boundary_bound=True,
        recovery_boundary_bound=True,
        partial_failure_recovery_bound=True,
        idempotency_bound=True,
        resume_boundary_bound=True,
        retry_boundary_bound=True,
        replay_boundary_bound=True,
        supersession_bound=True,
        traceability_identity=traceability_identity,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_identity_digest,
        handoff_digest=pe35_result["pe34_handoff_digest"],
        handoff_generation=lifecycle.generation,
        recovery_generation=recovery.recovery_generation if recovery is not None else 0,
        recovery_coherence_proven=True,
    )


def default_minimal_pe37_integration_proof(
    pe37_input: DurableEvidenceTraceabilityBoundaryInput,
    *,
    traceability_identity: str,
    run_identity_digest: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    durable_artifact_identity: str,
) -> Pe37TraceabilityProofBinding:
    pe37_result = evaluate_durable_evidence_traceability_boundary(pe37_input)
    boundary_result_digest = pe37_result["boundary_result_digest"]
    if boundary_result_digest is None:
        raise ValueError("PE-37 boundary must be satisfied for default minimal proof")
    traceability_id = pe37_result["traceability_identity"]
    if traceability_id is None:
        raise ValueError("PE-37 traceability_identity required for default minimal proof")
    admission_identity = pe37_result["admission_identity"]
    if admission_identity is None:
        raise ValueError("PE-37 admission_identity required for default minimal proof")
    pe34_handoff = pe37_input.pe36_boundary_input.pe35_boundary_input.pe34_handoff
    return Pe37TraceabilityProofBinding(
        traceability_owner=PE37_BOUNDARY_OWNER,
        source_revision=pe34_handoff.source_revision,
        boundary_input_digest=compute_pe37_boundary_input_digest(pe37_input),
        boundary_result_digest=boundary_result_digest,
        pe37_boundary_pass=True,
        durable_evidence_traceability_boundary_satisfied=True,
        pe34_handoff_bound=True,
        pe35_staleness_revocation_recovery_bound=True,
        pe36_admission_presentation_bound=True,
        durable_run_primary_evidence_completion_traceability_bound=True,
        operator_review_chain_durable_evidence_traceability_bound=True,
        traceability_identity=traceability_id,
        admission_identity=admission_identity,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_identity_digest,
        durable_artifact_identity=durable_artifact_identity,
        review_chain_identity=traceability_id,
        pe34_handoff_digest=compute_pe34_boundary_input_digest(pe34_handoff),
        pe36_boundary_result_digest=pe37_result["pe36_boundary_result_digest"],
        traceability_coherence_proven=True,
    )


def default_minimal_pe25_integration_proof(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    *,
    pe25_input: OperatorClosureLifecycleIntegrationInput,
    pe25_result: dict[str, Any],
    admission_result: dict[str, Any],
    traceability_identity: str,
    admission_identity: str,
    run_identity_digest: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    durable_artifact_identity: str,
) -> Pe25OperatorClosureLifecycleProofBinding:
    closure_result_digest = pe25_result["closure_result_digest"]
    if closure_result_digest is None:
        raise ValueError("PE-25 closure must be satisfied for default minimal proof")
    admission_proof_digest = admission_result.get("integration_proof_digest")
    if admission_proof_digest is None:
        raise ValueError("Admission lifecycle proof required for default minimal PE-25 proof")
    pe37_proof = integration_input.pe37_traceability_proof
    pe35_proof = integration_input.pe35_handoff_recovery_boundary_proof
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    pe34_handoff = pe35_input.pe34_handoff
    return Pe25OperatorClosureLifecycleProofBinding(
        closure_owner=PE25_INTEGRATION_OWNER,
        source_revision=integration_input.source_revision,
        closure_input_digest=compute_pe25_closure_input_digest(pe25_input),
        closure_result_digest=closure_result_digest,
        admission_integration_proof_digest=admission_proof_digest,
        pe25_integration_pass=True,
        operator_closure_static_complete=True,
        operator_closure_lifecycle_bound=True,
        pe25_operator_closure_bound=True,
        durable_run_primary_evidence_completion_operator_closure_bound=True,
        pe34_handoff_bound=True,
        pe35_staleness_revocation_recovery_bound=True,
        pe36_admission_presentation_bound=True,
        pe37_durable_traceability_bound=True,
        traceability_identity=traceability_identity,
        admission_identity=admission_identity,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_identity_digest,
        durable_artifact_identity=durable_artifact_identity,
        pe34_handoff_digest=compute_pe34_boundary_input_digest(pe34_handoff),
        pe35_boundary_result_digest=pe35_proof.boundary_result_digest,
        pe36_boundary_result_digest=pe37_proof.pe36_boundary_result_digest,
        pe37_traceability_identity=pe37_proof.traceability_identity,
        closure_coherence_proven=True,
    )


def default_minimal_completion_proof_chain(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> CompletionProofChainBinding:
    pe31_proof = integration_input.pe31_reconciliation_review_integration_proof
    pe22_proof = integration_input.pe22_risk_killswitch_flatten_proof
    pe23_proof = integration_input.pe23_capital_slot_ratchet_release_proof
    pe24_proof = integration_input.pe24_pilot_envelope_lifecycle_proof
    pe35_proof = integration_input.pe35_handoff_recovery_boundary_proof
    pe37_proof = integration_input.pe37_traceability_proof
    pe25_proof = integration_input.pe25_operator_closure_proof
    pe21_proof = integration_input.pe21_proof
    pe31_pe21_proof = integration_input.pe31_reconciliation_review_integration_input.pe21_reconciliation_primary_evidence_integration_proof
    return CompletionProofChainBinding(
        completion_referenced_pe31_proof_digest=pe31_proof.integration_proof_digest,
        completion_referenced_pe22_proof_digest=pe22_proof.integration_proof_digest,
        completion_referenced_pe23_proof_digest=pe23_proof.integration_proof_digest,
        completion_referenced_pe24_proof_digest=pe24_proof.integration_proof_digest,
        completion_referenced_pe35_boundary_result_digest=pe35_proof.boundary_result_digest,
        completion_referenced_pe37_boundary_result_digest=pe37_proof.boundary_result_digest,
        pe37_traceability_identity=pe37_proof.traceability_identity,
        completion_referenced_pe25_closure_result_digest=pe25_proof.closure_result_digest,
        pe25_closure_input_digest=pe25_proof.closure_input_digest,
        closure_referenced_admission_proof_digest=pe25_proof.admission_integration_proof_digest,
        pe31_referenced_pe21_integration_proof_digest=pe31_pe21_proof.integration_proof_digest,
        completion_referenced_pe21_integration_proof_digest=pe21_proof.integration_proof_digest,
        shared_pe21_integration_input_digest=compute_pe21_integration_input_digest(
            integration_input.pe21_integration_input
        ),
        shared_traceability_identity=integration_input.durable_run_root.run_root_digest,
    )


def _default_bounded_artifact_checksums() -> tuple[ArtifactChecksumEntry, ...]:
    digests = {
        "RUN_METADATA.json": "a" * 64,
        "review/REVIEW_RESULT.json": "b" * 64,
        "wrapper_evidence/steps.jsonl": "c" * 64,
        "wrapper_evidence/manifest.json": "d" * 64,
        "logs/wrapper_stdout.log": "e" * 64,
        "logs/wrapper_stderr.log": "f" * 64,
        MANIFEST_FILENAME: "0" * 64,
    }
    return tuple(
        ArtifactChecksumEntry(relative_path=path, digest=digests[path])
        for path in BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    )


def default_minimal_completion_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    run_id: str = "bounded-futures-testnet-offline-run-001",
    durable_archive_root: str = (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
    ),
    run_root_identity: str = "bounded_futures_testnet_durable_run/offline-v0",
) -> DurableRunPrimaryEvidenceCompletionIntegrationInput:
    """Minimal valid bounded futures testnet completion integration input for offline tests."""
    from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
        default_minimal_integration_input as default_minimal_pe21_integration_input,
    )

    artifact_checksums = _default_bounded_artifact_checksums()
    manifest_entries = tuple(
        ArtifactChecksumEntry(relative_path=entry.relative_path, digest=entry.digest)
        for entry in artifact_checksums
        if entry.relative_path != MANIFEST_FILENAME
    )
    manifest_digest = compute_manifest_digest(_manifest_entries_from_artifacts(manifest_entries))

    pe21_integration_input = default_minimal_pe21_integration_input(
        source_revision=source_revision,
    )

    from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
        PrimaryEvidenceBindingInput,
    )

    pe21_binding = pe21_integration_input.primary_evidence_binding
    pe21_integration_input = replace(
        pe21_integration_input,
        primary_evidence_binding=PrimaryEvidenceBindingInput(
            retention_contract_version=pe21_binding.retention_contract_version,
            durable_archive_root=durable_archive_root,
            archive_identity=pe21_binding.archive_identity,
            expected_artifact_filenames=pe21_binding.expected_artifact_filenames,
            manifest_proof_identity=pe21_binding.manifest_proof_identity,
            manifest_digest=pe21_binding.manifest_digest,
            manifest_verify_rc=pe21_binding.manifest_verify_rc,
            manifest_entries=pe21_binding.manifest_entries,
        ),
    )
    pe21_result = evaluate_position_order_reconciliation_primary_evidence_integration(
        pe21_integration_input
    )

    pe31_base = default_minimal_pe31_integration_input(source_revision=source_revision)
    pe31_integration_input = replace(
        pe31_base,
        pe21_reconciliation_primary_evidence_integration_input=pe21_integration_input,
        pe21_reconciliation_primary_evidence_integration_proof=default_minimal_pe21_integration_proof(
            pe21_integration_input
        ),
        reconciliation_review_proof=default_minimal_reconciliation_review_proof(
            pe21_integration_input
        ),
    )
    pe31_proof = default_minimal_pe31_integration_proof(pe31_integration_input)

    run_identity_digest = compute_run_identity_digest(
        run_id=run_id,
        run_type=SUPPORTED_RUN_TYPE,
        source_revision=source_revision,
    )
    run_root_digest = compute_run_root_digest(
        durable_archive_root=durable_archive_root,
        run_root_identity=run_root_identity,
        source_revision=source_revision,
    )

    pe22_base = default_minimal_pe22_integration_input(source_revision=source_revision)
    pe22_integration_input = replace(
        pe22_base,
        lifecycle_matrix_proof=replace(
            pe22_base.lifecycle_matrix_proof,
            lifecycle_state_digest=run_root_digest,
        ),
    )
    pe22_result = evaluate_risk_killswitch_lifecycle_integration(pe22_integration_input)
    pe22_proof = default_minimal_pe22_integration_proof(
        pe22_integration_input,
        traceability_identity=run_root_digest,
        run_identity_digest=run_identity_digest,
    )

    pe23_base = default_minimal_pe23_integration_input(
        source_revision=source_revision,
        lifecycle_state_digest=run_root_digest,
    )
    pe23_integration_input = replace(
        pe23_base,
        pe22_upstream_safety_proof=_pe22_upstream_safety_proof_from_completion_pe22(pe22_proof),
        lifecycle_matrix_proof=replace(
            pe23_base.lifecycle_matrix_proof,
            lifecycle_state_digest=run_root_digest,
        ),
    )
    pe23_result = evaluate_capital_slot_ratchet_release_lifecycle_integration(
        pe23_integration_input
    )
    completion_identity_digest = compute_completion_identity_digest(
        run_root_digest=run_root_digest,
        manifest_digest=manifest_digest,
        source_revision=source_revision,
    )
    pe23_proof = default_minimal_pe23_integration_proof(
        pe23_integration_input,
        traceability_identity=run_root_digest,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
    )

    pe24_pe22_upstream, pe24_pe23_upstream = _pe24_upstream_proofs_from_completion(
        pe22_proof,
        pe23_proof,
    )
    pe24_base = default_minimal_pe24_integration_input(
        source_revision=source_revision,
        lifecycle_state_digest=run_root_digest,
    )
    pe24_integration_input = replace(
        pe24_base,
        pe22_risk_killswitch_flatten_proof=pe24_pe22_upstream,
        pe23_capital_slot_ratchet_release_proof=pe24_pe23_upstream,
        lifecycle_matrix_proof=replace(
            pe24_base.lifecycle_matrix_proof,
            lifecycle_state_digest=run_root_digest,
        ),
    )
    pe24_proof = default_minimal_pe24_integration_proof(
        pe24_integration_input,
        traceability_identity=run_root_digest,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        pe22_integration_proof_digest=pe22_proof.integration_proof_digest,
        pe23_integration_proof_digest=pe23_proof.integration_proof_digest,
    )

    pe35_boundary_input = _build_pe35_boundary_input_for_completion(
        source_revision=source_revision,
        manifest_digest=manifest_digest,
    )
    pe35_proof = default_minimal_pe35_integration_proof(
        pe35_boundary_input,
        traceability_identity=run_root_digest,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_digest,
    )

    pe37_boundary_input = _build_pe37_boundary_input_from_pe35(pe35_boundary_input)
    pe37_proof = default_minimal_pe37_integration_proof(
        pe37_boundary_input,
        traceability_identity=run_root_digest,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_digest,
        durable_artifact_identity=run_root_digest,
    )

    pe25_closure_input = _build_pe25_closure_input_from_chain(
        source_revision=source_revision,
        run_id=run_id,
        run_root_digest=run_root_digest,
        pe22_integration_input=pe22_integration_input,
        pe22_proof=pe22_proof,
        pe23_integration_input=pe23_integration_input,
        pe23_proof=pe23_proof,
        pe24_integration_input=pe24_integration_input,
        pe24_proof=pe24_proof,
    )
    pe25_result = evaluate_operator_closure_lifecycle_integration(pe25_closure_input)

    archive_digest = hashlib.sha256(
        json.dumps(
            {
                "archive_contract_version": ARCHIVE_CONTRACT_VERSION,
                "archive_identity": run_root_identity,
                "manifest_digest": manifest_digest,
                "source_revision": source_revision,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    primary_evidence_identity_digest = compute_primary_evidence_identity_digest(
        primary_evidence_identity=run_root_identity,
        primary_evidence_owner=PRIMARY_EVIDENCE_OWNER,
        retention_contract_version=PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
        source_revision=source_revision,
    )

    draft = DurableRunPrimaryEvidenceCompletionIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        run_type=SUPPORTED_RUN_TYPE,
        run_identity=RunIdentityBinding(
            run_id=run_id,
            run_identity_digest=run_identity_digest,
        ),
        durable_run_root=DurableRunRootBinding(
            durable_archive_root=durable_archive_root,
            run_root_identity=run_root_identity,
            run_root_digest=run_root_digest,
        ),
        primary_evidence_identity=PrimaryEvidenceIdentityBinding(
            primary_evidence_identity=primary_evidence_identity_digest,
            primary_evidence_owner=PRIMARY_EVIDENCE_OWNER,
            retention_contract_version=PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
        ),
        pe21_proof=Pe21PrimaryEvidenceProofBinding(
            integration_owner=PE21_INTEGRATION_OWNER,
            source_revision=source_revision,
            integration_input_digest=pe21_result["integration_input_digest"],
            integration_proof_digest=pe21_result["integration_proof_digest"],
            pe21_integration_pass=True,
            durable_primary_evidence_binding_proven=True,
        ),
        pe21_integration_input=pe21_integration_input,
        pe31_reconciliation_review_integration_input=pe31_integration_input,
        pe31_reconciliation_review_integration_proof=pe31_proof,
        pe22_risk_killswitch_lifecycle_integration_input=pe22_integration_input,
        pe22_risk_killswitch_flatten_proof=pe22_proof,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=pe23_integration_input,
        pe23_capital_slot_ratchet_release_proof=pe23_proof,
        pe24_pilot_envelope_lifecycle_integration_input=pe24_integration_input,
        pe24_pilot_envelope_lifecycle_proof=pe24_proof,
        pe35_handoff_staleness_revocation_recovery_boundary_input=pe35_boundary_input,
        pe35_handoff_recovery_boundary_proof=pe35_proof,
        pe37_traceability_boundary_input=pe37_boundary_input,
        pe37_traceability_proof=pe37_proof,
        pe25_closure_integration_input=pe25_closure_input,
        pe25_operator_closure_proof=Pe25OperatorClosureLifecycleProofBinding(
            closure_owner=PE25_INTEGRATION_OWNER,
            source_revision=source_revision,
            closure_input_digest="0" * 64,
            closure_result_digest="0" * 64,
            admission_integration_proof_digest="0" * 64,
            pe25_integration_pass=True,
            operator_closure_static_complete=True,
            operator_closure_lifecycle_bound=True,
            pe25_operator_closure_bound=True,
            durable_run_primary_evidence_completion_operator_closure_bound=True,
            pe34_handoff_bound=True,
            pe35_staleness_revocation_recovery_bound=True,
            pe36_admission_presentation_bound=True,
            pe37_durable_traceability_bound=True,
            traceability_identity=pe37_proof.traceability_identity,
            admission_identity=pe37_proof.admission_identity,
            run_identity_digest=run_identity_digest,
            completion_identity_digest=completion_identity_digest,
            manifest_identity_digest=manifest_digest,
            durable_artifact_identity=run_root_digest,
            pe34_handoff_digest=compute_pe34_boundary_input_digest(
                pe35_boundary_input.pe34_handoff
            ),
            pe35_boundary_result_digest=pe35_proof.boundary_result_digest,
            pe36_boundary_result_digest=pe37_proof.pe36_boundary_result_digest,
            pe37_traceability_identity=pe37_proof.traceability_identity,
            closure_coherence_proven=True,
        ),
        pe25_proof_lifecycle=ProofLifecycleMetadata(lifecycle_state=PROOF_LIFECYCLE_CURRENT),
        completion_proof_chain=CompletionProofChainBinding(
            completion_referenced_pe31_proof_digest=pe31_proof.integration_proof_digest,
            completion_referenced_pe22_proof_digest=pe22_result["integration_proof_digest"],
            completion_referenced_pe23_proof_digest=pe23_result["integration_proof_digest"],
            completion_referenced_pe24_proof_digest=pe24_proof.integration_proof_digest,
            completion_referenced_pe35_boundary_result_digest=pe35_proof.boundary_result_digest,
            completion_referenced_pe37_boundary_result_digest=pe37_proof.boundary_result_digest,
            pe37_traceability_identity=pe37_proof.traceability_identity,
            completion_referenced_pe25_closure_result_digest=pe25_result["closure_result_digest"]
            or ("0" * 64),
            pe25_closure_input_digest=compute_pe25_closure_input_digest(pe25_closure_input),
            closure_referenced_admission_proof_digest="0" * 64,
            pe31_referenced_pe21_integration_proof_digest=(
                pe31_integration_input.pe21_reconciliation_primary_evidence_integration_proof.integration_proof_digest
            ),
            completion_referenced_pe21_integration_proof_digest=pe21_result[
                "integration_proof_digest"
            ],
            shared_pe21_integration_input_digest=pe21_result["integration_input_digest"],
            shared_traceability_identity=run_root_digest,
        ),
        pe16_archive=Pe16ArchiveProofBinding(
            archive_owner=PE16_ARCHIVE_OWNER,
            archive_contract_version=ARCHIVE_CONTRACT_VERSION,
            archive_identity=run_root_identity,
            archive_digest=archive_digest,
            pe16_integration_pass=True,
        ),
        manifest_proof=ManifestProofBinding(
            manifest_identity=manifest_digest,
            manifest_digest=manifest_digest,
            manifest_verify_rc=0,
            manifest_entries=manifest_entries,
        ),
        artifact_checksums=artifact_checksums,
        post_write_verification=PostWriteVerificationBinding(
            post_write_verification_pass=True,
            manifest_verify_rc=0,
        ),
        gap4_completion=Gap4CompletionProofBinding(
            gap4_owner=GAP4_COMPLETION_OWNER,
            source_revision=source_revision,
            output_evidence_depends_on_gap2a1=True,
            completion_invalid_without_durable_primary_evidence=True,
            completion_invalid_without_manifest_verify=True,
            durable_output_required_for_future_runs=True,
            gap4_output_evidence_paths_verified=False,
            gap4_integration_pass=True,
        ),
        gap2a1_enforcement=Gap2a1EnforcementProofBinding(
            gap2a1_owner=GAP2A1_ENFORCEMENT_OWNER,
            source_revision=source_revision,
            primary_evidence_enforced=False,
            enforcement_default_on=False,
            enforcement_opt_in_only=True,
            tmp_only_evidence_invalid=True,
            manifest_verify_required=True,
            checksum_verify_required=True,
            run_incomplete_without_primary_evidence=True,
            gap2a1_integration_pass=True,
        ),
        proof_lifecycle=ProofLifecycleMetadata(lifecycle_state=PROOF_LIFECYCLE_CURRENT),
        evidence_mode=EVIDENCE_MODE_DURABLE,
        completion_claimed=True,
        safety_snapshot=default_minimal_safety_snapshot(),
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe16_archive=ARCHIVE_CONTRACT_VERSION,
            pe16_primary_evidence_retention=PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
            pe21_integration=PE21_CONTRACT_VERSION,
            pe31_integration=PE31_CONTRACT_VERSION,
            pe22_integration=PE22_CONTRACT_VERSION,
            pe23_integration=PE23_CONTRACT_VERSION,
            pe24_integration=PE24_CONTRACT_VERSION,
            pe35_boundary=PE35_CONTRACT_VERSION,
            pe34_handoff=PE34_CONTRACT_VERSION,
            pe36_admission_presentation=PE36_CONTRACT_VERSION,
            pe37_traceability=PE37_CONTRACT_VERSION,
            pe25_operator_closure=PE25_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
        evaluate_operator_review_admission_presentation_lifecycle_integration,
    )

    admission_input = _build_admission_presentation_lifecycle_input_from_completion(draft)
    admission_result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        admission_input
    )
    pe25_proof = default_minimal_pe25_integration_proof(
        draft,
        pe25_input=pe25_closure_input,
        pe25_result=pe25_result,
        admission_result=admission_result,
        traceability_identity=pe37_proof.traceability_identity,
        admission_identity=pe37_proof.admission_identity,
        run_identity_digest=run_identity_digest,
        completion_identity_digest=completion_identity_digest,
        manifest_identity_digest=manifest_digest,
        durable_artifact_identity=run_root_digest,
    )
    completed = replace(
        draft,
        pe25_operator_closure_proof=pe25_proof,
    )
    return replace(
        completed,
        completion_proof_chain=default_minimal_completion_proof_chain(completed),
    )
