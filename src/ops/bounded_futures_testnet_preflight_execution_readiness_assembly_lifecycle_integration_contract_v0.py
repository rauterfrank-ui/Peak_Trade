"""Bounded Futures Testnet preflight execution readiness assembly (v0, PE-26).

Deterministic, offline, explicit-input-only contract composing static proof bindings
from PE-12 through PE-25 into one fail-closed zero-order preflight execution readiness
assembly assessment. Static integration only — no operative execution, operator decision,
readiness authority lift, network, testnet, runtime, credentials, orders, or lifecycle
transitions.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import asdict, dataclass, replace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        DurableEvidenceTraceabilityBoundaryInput,
    )

from src.ops.bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as GLB012_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_glb_lifecycle_matrix_digest,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE23_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_pe23_lifecycle_matrix_digest,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
    Pe19ReviewProofBinding,
    Pe20DurableReviewPackageBinding,
    Pe22RiskKillswitchFlattenProofBinding,
    Pe23CapitalSlotRatchetReleaseProofBinding,
    Pe24PilotEnvelopeProofBinding,
)
from src.ops.bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE24_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_pe24_lifecycle_matrix_digest,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    CONTRACT_VERSION as PE21_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_pe21_lifecycle_matrix_digest,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION as PE16_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION as PE14_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_COMPLETE,
    COMPLETENESS_CONTRACT_VERSION as PE17_CONTRACT_VERSION,
    TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION as PE13_CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    REPLAY_CONTRACT_VERSION as PE15_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_source_state_capture_contract_v0 import (
    CAPTURE_VALID,
    CONTRACT_VERSION as PE18_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_pe22_lifecycle_matrix_digest,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_ASSEMBLY_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = (
    "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration.v0"
)
SERIALIZATION_VERSION = "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"
PE37_CONTRACT_VERSION = (
    "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary.v0"
)
PE37_BOUNDARY_OWNER = PE37_CONTRACT_VERSION
ZERO_ORDER_CAPABILITY_OWNER = PHASE_CANONICAL_OWNERS[PHASE_ZERO_ORDER]

GLOBAL_PREFLIGHT_EXECUTION_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_PREFLIGHT_EXECUTION = False
OPERATIVE_OPERATOR_CLOSURE_EXECUTED = False
OPERATIVE_OPERATOR_DECISION_CREATED = False
OPERATIVE_APPROVAL_CREATED = False
OPERATIVE_GO_NO_GO_CREATED = False
OPERATIVE_PILOT_EXECUTED = False
OPERATIVE_READINESS_DECISION_CREATED = False
OPERATIVE_RECONCILIATION_EXECUTED = False
OPERATIVE_RISK_EVALUATION_EXECUTED = False
OPERATIVE_KILLSWITCH_EXECUTED = False
OPERATIVE_FLATTEN_EXECUTED = False
OPERATIVE_RATCHET_APPLIED = False
OPERATIVE_SLOT_RELEASE_EXECUTED = False
OPERATIVE_CAPITAL_REALLOCATION_EXECUTED = False
OPERATIVE_RESERVE_MOVEMENT_EXECUTED = False
ACCOUNT_STATE_QUERIED = False
POSITION_STATE_QUERIED = False
ORDER_STATE_QUERIED = False
EXCHANGE_STATE_QUERIED = False
LIFECYCLE_TRANSITION_EXECUTED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe13_packet": PE13_CONTRACT_VERSION,
    "pe14_builder": PE14_CONTRACT_VERSION,
    "pe15_replay": PE15_CONTRACT_VERSION,
    "pe16_archive": PE16_CONTRACT_VERSION,
    "pe17_completeness_truth": PE17_CONTRACT_VERSION,
    "pe18_source_state_capture": PE18_CONTRACT_VERSION,
    "pe19_operator_review": PE19_CONTRACT_VERSION,
    "pe20_review_proof_package": PE20_CONTRACT_VERSION,
    "glb012_adapter_capability": GLB012_CONTRACT_VERSION,
    "pe21_reconciliation_primary_evidence": PE21_CONTRACT_VERSION,
    "pe22_risk_killswitch_flatten": PE22_CONTRACT_VERSION,
    "pe23_capital_slot_ratchet_release": PE23_CONTRACT_VERSION,
    "pe24_pilot_envelope": PE24_CONTRACT_VERSION,
    "pe25_operator_closure": PE25_CONTRACT_VERSION,
    "pe37_traceability_boundary": PE37_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe13_packet: str
    pe14_builder: str
    pe15_replay: str
    pe16_archive: str
    pe17_completeness_truth: str
    pe18_source_state_capture: str
    pe19_operator_review: str
    pe20_review_proof_package: str
    glb012_adapter_capability: str
    pe21_reconciliation_primary_evidence: str
    pe22_risk_killswitch_flatten: str
    pe23_capital_slot_ratchet_release: str
    pe24_pilot_envelope: str
    pe25_operator_closure: str
    pe37_traceability_boundary: str
    integration: str


@dataclass(frozen=True)
class LifecycleMatrixProof:
    pe12_contract_version: str
    lifecycle_matrix_digest: str
    assigned_lifecycle_phase: str
    lifecycle_state_digest: str
    readiness_decision_phase: str


@dataclass(frozen=True)
class Pe13PacketProofBinding:
    packet_id: str
    packet_digest: str
    pe13_contract_version: str
    packet_validation_pass: bool


@dataclass(frozen=True)
class Pe14BuilderProofBinding:
    input_capture_digest: str
    builder_alignment_pass: bool
    pe14_contract_version: str


@dataclass(frozen=True)
class Pe15ReplayProofBinding:
    replay_manifest_digest: str
    replay_pass: bool
    manifest_verify_rc: int
    pe15_contract_version: str


@dataclass(frozen=True)
class Pe16ArchiveProofBinding:
    archive_identity: str
    archive_manifest_digest: str
    manifest_verify_rc: int
    static_persisted_verified: bool
    pe16_contract_version: str


@dataclass(frozen=True)
class Pe17CompletenessTruthProofBinding:
    completeness_status: str
    truth_status: str
    internal_static_chain_complete: bool
    pe17_contract_version: str


@dataclass(frozen=True)
class Pe18SourceStateProofBinding:
    source_state_digest: str
    capture_status: str
    dirty_state: bool
    pe18_contract_version: str


@dataclass(frozen=True)
class Glb012CapabilityProofBinding:
    integration_input_digest: str
    integration_proof_digest: str
    glb_integration_pass: bool
    lifecycle_matrix_digest: str


@dataclass(frozen=True)
class Pe21ReconciliationPrimaryEvidenceProofBinding:
    integration_input_digest: str
    integration_proof_digest: str
    pe21_integration_pass: bool
    durable_primary_evidence_binding_proven: bool
    lifecycle_matrix_digest: str


@dataclass(frozen=True)
class Pe25OperatorClosureProofBinding:
    closure_input_digest: str
    closure_result_digest: str
    pe25_integration_pass: bool
    operator_closure_static_complete: bool
    lifecycle_matrix_digest: str


@dataclass(frozen=True)
class Pe37TraceabilityProofBinding:
    traceability_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str
    traceability_identity: str
    pe37_integration_pass: bool
    durable_evidence_traceability_boundary_satisfied: bool


@dataclass(frozen=True)
class ZeroOrderCapabilityProofBinding:
    capability_owner: str
    capability_proof_digest: str
    zero_order_plan_only_capable: bool


@dataclass(frozen=True)
class AssemblySafetySnapshot:
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    zero_order_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    operator_closure_authorized: bool
    operator_decision_authorized: bool
    pilot_start_authorized: bool
    promotion_authorized: bool
    capital_reallocation_authorized: bool
    reserve_topup_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class PreflightExecutionReadinessAssemblyInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    assembly_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    lifecycle_matrix_proof: LifecycleMatrixProof
    pe13_packet_proof: Pe13PacketProofBinding
    pe14_builder_proof: Pe14BuilderProofBinding
    pe15_replay_proof: Pe15ReplayProofBinding
    pe16_archive_proof: Pe16ArchiveProofBinding
    pe17_completeness_truth_proof: Pe17CompletenessTruthProofBinding
    pe18_source_state_proof: Pe18SourceStateProofBinding
    pe19_review_proof: Pe19ReviewProofBinding
    pe20_durable_review_package: Pe20DurableReviewPackageBinding
    glb012_capability_proof: Glb012CapabilityProofBinding
    pe21_reconciliation_primary_evidence_proof: Pe21ReconciliationPrimaryEvidenceProofBinding
    pe22_risk_killswitch_flatten_proof: Pe22RiskKillswitchFlattenProofBinding
    pe23_capital_slot_ratchet_release_proof: Pe23CapitalSlotRatchetReleaseProofBinding
    pe24_pilot_envelope_proof: Pe24PilotEnvelopeProofBinding
    pe25_operator_closure_proof: Pe25OperatorClosureProofBinding
    pe37_traceability_boundary_input: DurableEvidenceTraceabilityBoundaryInput
    pe37_traceability_proof: Pe37TraceabilityProofBinding
    zero_order_capability_proof: ZeroOrderCapabilityProofBinding
    safety_snapshot: AssemblySafetySnapshot
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def compute_lifecycle_matrix_digest() -> str:
    """Deterministic digest of the canonical PE-12 lifecycle matrix identity."""
    matrix = {
        "hash_algorithm": HASH_ALGORITHM,
        "lifecycle_phase_order": list(LIFECYCLE_PHASE_ORDER),
        "network_execution_phases": sorted(NETWORK_EXECUTION_PHASES),
        "package_marker": PE12_PACKAGE_MARKER,
        "pe12_contract_version": PE12_CONTRACT_VERSION,
        "phase_descriptors": {
            phase_id: {
                "canonical_owner": descriptor.canonical_owner,
                "credentials_phase": descriptor.credentials_phase,
                "network_phase": descriptor.network_phase,
                "operator_go_token": descriptor.operator_go_token,
                "orders_phase": descriptor.orders_phase,
                "sequence_index": descriptor.sequence_index,
            }
            for phase_id, descriptor in sorted(LIFECYCLE_PHASE_DESCRIPTORS.items())
        },
    }
    return hashlib.sha256(
        json.dumps(matrix, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _assembly_input_dict(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
) -> dict[str, Any]:
    return {
        "integration_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": assembly_input.source_revision,
        "repository_identity": assembly_input.repository_identity,
        "adapter_id": assembly_input.adapter_id,
        "assembly_id": assembly_input.assembly_id,
        "instrument": assembly_input.instrument,
        "market_type": assembly_input.market_type,
        "contract_versions": asdict(assembly_input.contract_versions),
        "lifecycle_matrix_proof": asdict(assembly_input.lifecycle_matrix_proof),
        "pe13_packet_proof": asdict(assembly_input.pe13_packet_proof),
        "pe14_builder_proof": asdict(assembly_input.pe14_builder_proof),
        "pe15_replay_proof": asdict(assembly_input.pe15_replay_proof),
        "pe16_archive_proof": asdict(assembly_input.pe16_archive_proof),
        "pe17_completeness_truth_proof": asdict(assembly_input.pe17_completeness_truth_proof),
        "pe18_source_state_proof": asdict(assembly_input.pe18_source_state_proof),
        "pe19_review_proof": asdict(assembly_input.pe19_review_proof),
        "pe20_durable_review_package": asdict(assembly_input.pe20_durable_review_package),
        "glb012_capability_proof": asdict(assembly_input.glb012_capability_proof),
        "pe21_reconciliation_primary_evidence_proof": asdict(
            assembly_input.pe21_reconciliation_primary_evidence_proof
        ),
        "pe22_risk_killswitch_flatten_proof": asdict(
            assembly_input.pe22_risk_killswitch_flatten_proof
        ),
        "pe23_capital_slot_ratchet_release_proof": asdict(
            assembly_input.pe23_capital_slot_ratchet_release_proof
        ),
        "pe24_pilot_envelope_proof": asdict(assembly_input.pe24_pilot_envelope_proof),
        "pe25_operator_closure_proof": asdict(assembly_input.pe25_operator_closure_proof),
        "pe37_traceability_boundary_input_digest": _compute_pe37_boundary_input_digest(
            assembly_input.pe37_traceability_boundary_input
        ),
        "pe37_traceability_proof": asdict(assembly_input.pe37_traceability_proof),
        "traceability_identity": assembly_input.pe37_traceability_proof.traceability_identity,
        "zero_order_capability_proof": asdict(assembly_input.zero_order_capability_proof),
        "safety_snapshot": asdict(assembly_input.safety_snapshot),
        "futures_only": assembly_input.futures_only,
        "environment": assembly_input.environment,
        "non_authorizing": assembly_input.non_authorizing,
    }


def serialize_assembly_input_canonical(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
) -> str:
    return json.dumps(
        _assembly_input_dict(assembly_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_assembly_input_digest(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
) -> str:
    return hashlib.sha256(
        serialize_assembly_input_canonical(assembly_input).encode("utf-8")
    ).hexdigest()


def _assembly_result_dict(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
    *,
    assembly_result_digest: str | None = None,
    preflight_execution_readiness_assembly_complete: bool = False,
) -> dict[str, Any]:
    payload = {
        "integration_contract_version": CONTRACT_VERSION,
        "assembly_input_digest": compute_assembly_input_digest(assembly_input),
        "source_revision": assembly_input.source_revision,
        "adapter_id": assembly_input.adapter_id,
        "assembly_id": assembly_input.assembly_id,
        "lifecycle_matrix_digest": assembly_input.lifecycle_matrix_proof.lifecycle_matrix_digest,
        "assigned_lifecycle_phase": assembly_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "readiness_decision_phase": assembly_input.lifecycle_matrix_proof.readiness_decision_phase,
        "pe12_preflight_execution_readiness_assembly_proven": (
            preflight_execution_readiness_assembly_complete
        ),
        "preflight_execution_readiness_assembly_complete": (
            preflight_execution_readiness_assembly_complete
        ),
        "assembly_review_eligible": preflight_execution_readiness_assembly_complete,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_preflight_execution": OPERATIVE_PREFLIGHT_EXECUTION,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_approval_created": OPERATIVE_APPROVAL_CREATED,
        "operative_go_no_go_created": OPERATIVE_GO_NO_GO_CREATED,
        "operative_pilot_executed": OPERATIVE_PILOT_EXECUTED,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_reconciliation_executed": OPERATIVE_RECONCILIATION_EXECUTED,
        "operative_risk_evaluation_executed": OPERATIVE_RISK_EVALUATION_EXECUTED,
        "operative_killswitch_executed": OPERATIVE_KILLSWITCH_EXECUTED,
        "operative_flatten_executed": OPERATIVE_FLATTEN_EXECUTED,
        "operative_ratchet_applied": OPERATIVE_RATCHET_APPLIED,
        "operative_slot_release_executed": OPERATIVE_SLOT_RELEASE_EXECUTED,
        "operative_capital_reallocation_executed": OPERATIVE_CAPITAL_REALLOCATION_EXECUTED,
        "operative_reserve_movement_executed": OPERATIVE_RESERVE_MOVEMENT_EXECUTED,
        "account_state_queried": ACCOUNT_STATE_QUERIED,
        "position_state_queried": POSITION_STATE_QUERIED,
        "order_state_queried": ORDER_STATE_QUERIED,
        "exchange_state_queried": EXCHANGE_STATE_QUERIED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "global_preflight_execution_readiness": GLOBAL_PREFLIGHT_EXECUTION_READINESS,
        "non_authorizing": True,
    }
    if assembly_result_digest is not None:
        payload["assembly_result_digest"] = assembly_result_digest
    return payload


def serialize_assembly_result_canonical(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
    *,
    preflight_execution_readiness_assembly_complete: bool = False,
) -> str:
    return json.dumps(
        _assembly_result_dict(
            assembly_input,
            preflight_execution_readiness_assembly_complete=(
                preflight_execution_readiness_assembly_complete
            ),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_assembly_result_digest(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
    *,
    preflight_execution_readiness_assembly_complete: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_assembly_result_canonical(
            assembly_input,
            preflight_execution_readiness_assembly_complete=(
                preflight_execution_readiness_assembly_complete
            ),
        ).encode("utf-8")
    ).hexdigest()


def _validate_instrument_scope(instrument: str, market_type: str) -> list[str]:
    fail_reasons: list[str] = []
    if market_type != DEFAULT_MARKET_TYPE:
        fail_reasons.append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    if not instrument:
        fail_reasons.append("instrument required")
    if instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        fail_reasons.append(f"instrument {instrument!r} is a rejected futures placeholder")
    if instrument in SPOT_INSTRUMENTS:
        fail_reasons.append(f"instrument {instrument!r} is a spot instrument")
    for fragment in _FORBIDDEN_INSTRUMENT_FRAGMENTS:
        if fragment in instrument:
            fail_reasons.append(f"instrument {instrument!r} has forbidden orientation {fragment!r}")
    return fail_reasons


def _validate_safety_snapshot(snapshot: AssemblySafetySnapshot) -> list[str]:
    fail_reasons: list[str] = []
    required_bools = (
        ("preflight_remains_blocked", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("zero_order_authorized", False),
        ("network_allowed", False),
        ("credentials_allowed", False),
        ("orders_allowed", False),
        ("scheduler_runtime_allowed", False),
        ("operator_closure_authorized", False),
        ("operator_decision_authorized", False),
        ("pilot_start_authorized", False),
        ("promotion_authorized", False),
        ("capital_reallocation_authorized", False),
        ("reserve_topup_allowed", False),
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


def _validate_pe13_packet_proof(binding: Pe13PacketProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if binding.pe13_contract_version != PE13_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe13_packet_proof: pe13_contract_version must be {PE13_CONTRACT_VERSION!r}"
        )
    if not binding.packet_id:
        fail_reasons.append("pe13_packet_proof: packet_id required")
    elif not _valid_sha256_digest(binding.packet_id):
        fail_reasons.append("pe13_packet_proof: packet_id must be 64-char lowercase sha256 hex")
    if not binding.packet_digest:
        fail_reasons.append("pe13_packet_proof: packet_digest required")
    elif not _valid_sha256_digest(binding.packet_digest):
        fail_reasons.append("pe13_packet_proof: packet_digest must be 64-char lowercase sha256 hex")
    if binding.packet_validation_pass is not True:
        fail_reasons.append("pe13_packet_proof: packet_validation_pass must be true")
    return fail_reasons


def _validate_pe14_builder_proof(binding: Pe14BuilderProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if binding.pe14_contract_version != PE14_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe14_builder_proof: pe14_contract_version must be {PE14_CONTRACT_VERSION!r}"
        )
    if not binding.input_capture_digest:
        fail_reasons.append("pe14_builder_proof: input_capture_digest required")
    elif not _valid_sha256_digest(binding.input_capture_digest):
        fail_reasons.append(
            "pe14_builder_proof: input_capture_digest must be 64-char lowercase sha256 hex"
        )
    if binding.builder_alignment_pass is not True:
        fail_reasons.append("pe14_builder_proof: builder_alignment_pass must be true")
    return fail_reasons


def _validate_pe15_replay_proof(binding: Pe15ReplayProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if binding.pe15_contract_version != PE15_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe15_replay_proof: pe15_contract_version must be {PE15_CONTRACT_VERSION!r}"
        )
    if not binding.replay_manifest_digest:
        fail_reasons.append("pe15_replay_proof: replay_manifest_digest required")
    elif not _valid_sha256_digest(binding.replay_manifest_digest):
        fail_reasons.append(
            "pe15_replay_proof: replay_manifest_digest must be 64-char lowercase sha256 hex"
        )
    if binding.replay_pass is not True:
        fail_reasons.append("pe15_replay_proof: replay_pass must be true")
    if binding.manifest_verify_rc != 0:
        fail_reasons.append("pe15_replay_proof: manifest_verify_rc must be 0")
    return fail_reasons


def _validate_pe16_archive_proof(binding: Pe16ArchiveProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if binding.pe16_contract_version != PE16_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe16_archive_proof: pe16_contract_version must be {PE16_CONTRACT_VERSION!r}"
        )
    if not binding.archive_identity:
        fail_reasons.append("pe16_archive_proof: archive_identity required")
    elif not _valid_sha256_digest(binding.archive_identity):
        fail_reasons.append(
            "pe16_archive_proof: archive_identity must be 64-char lowercase sha256 hex"
        )
    if not binding.archive_manifest_digest:
        fail_reasons.append("pe16_archive_proof: archive_manifest_digest required")
    elif not _valid_sha256_digest(binding.archive_manifest_digest):
        fail_reasons.append(
            "pe16_archive_proof: archive_manifest_digest must be 64-char lowercase sha256 hex"
        )
    if binding.manifest_verify_rc != 0:
        fail_reasons.append("pe16_archive_proof: manifest_verify_rc must be 0")
    if binding.static_persisted_verified is not True:
        fail_reasons.append("pe16_archive_proof: static_persisted_verified must be true")
    return fail_reasons


def _validate_pe17_completeness_truth_proof(
    binding: Pe17CompletenessTruthProofBinding,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.pe17_contract_version != PE17_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe17_completeness_truth_proof: pe17_contract_version must be {PE17_CONTRACT_VERSION!r}"
        )
    if binding.completeness_status != COMPLETENESS_COMPLETE:
        fail_reasons.append(
            f"pe17_completeness_truth_proof: completeness_status must be {COMPLETENESS_COMPLETE!r}"
        )
    if binding.truth_status != TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW:
        fail_reasons.append(
            "pe17_completeness_truth_proof: truth_status must be "
            f"{TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW!r}"
        )
    if binding.internal_static_chain_complete is not True:
        fail_reasons.append(
            "pe17_completeness_truth_proof: internal_static_chain_complete must be true"
        )
    return fail_reasons


def _validate_pe18_source_state_proof(binding: Pe18SourceStateProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if binding.pe18_contract_version != PE18_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe18_source_state_proof: pe18_contract_version must be {PE18_CONTRACT_VERSION!r}"
        )
    if not binding.source_state_digest:
        fail_reasons.append("pe18_source_state_proof: source_state_digest required")
    elif not _valid_sha256_digest(binding.source_state_digest):
        fail_reasons.append(
            "pe18_source_state_proof: source_state_digest must be 64-char lowercase sha256 hex"
        )
    if binding.capture_status != CAPTURE_VALID:
        fail_reasons.append(f"pe18_source_state_proof: capture_status must be {CAPTURE_VALID!r}")
    if binding.dirty_state is not False:
        fail_reasons.append("pe18_source_state_proof: dirty_state must be false")
    return fail_reasons


def _validate_pe19_review_proof(proof: Pe19ReviewProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not proof.review_input_digest:
        fail_reasons.append("pe19_review_proof: review_input_digest required")
    elif not _valid_sha256_digest(proof.review_input_digest):
        fail_reasons.append(
            "pe19_review_proof: review_input_digest must be 64-char lowercase sha256 hex"
        )
    if not proof.decision_record_digest:
        fail_reasons.append("pe19_review_proof: decision_record_digest required")
    elif not _valid_sha256_digest(proof.decision_record_digest):
        fail_reasons.append(
            "pe19_review_proof: decision_record_digest must be 64-char lowercase sha256 hex"
        )
    if not proof.review_proof_digest:
        fail_reasons.append("pe19_review_proof: review_proof_digest required")
    elif not _valid_sha256_digest(proof.review_proof_digest):
        fail_reasons.append(
            "pe19_review_proof: review_proof_digest must be 64-char lowercase sha256 hex"
        )
    if proof.review_valid is not True:
        fail_reasons.append("pe19_review_proof: review_valid must be true")
    if proof.decision != DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW:
        fail_reasons.append(
            "pe19_review_proof: decision must be approve_for_separate_next_phase_review"
        )
    if not proof.reason_code:
        fail_reasons.append("pe19_review_proof: reason_code required")
    required_bools = (
        ("non_authorizing", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
    )
    for field_name, expected in required_bools:
        actual = getattr(proof, field_name)
        if actual is not expected:
            fail_reasons.append(f"pe19_review_proof: {field_name} must be {expected}")
    if proof.evidence_manifest_verify_rc != 0:
        fail_reasons.append("pe19_review_proof: evidence_manifest_verify_rc must be 0")
    return fail_reasons


def _validate_pe20_durable_review_package(binding: Pe20DurableReviewPackageBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.package_id:
        fail_reasons.append("pe20_durable_review_package: package_id required")
    elif not _valid_sha256_digest(binding.package_id):
        fail_reasons.append(
            "pe20_durable_review_package: package_id must be 64-char lowercase sha256 hex"
        )
    if not binding.package_digest:
        fail_reasons.append("pe20_durable_review_package: package_digest required")
    elif not _valid_sha256_digest(binding.package_digest):
        fail_reasons.append(
            "pe20_durable_review_package: package_digest must be 64-char lowercase sha256 hex"
        )
    if binding.manifest_verify_rc != 0:
        fail_reasons.append("pe20_durable_review_package: manifest_verify_rc must be 0")
    if binding.static_glb016_reproducibility_satisfied is not True:
        fail_reasons.append(
            "pe20_durable_review_package: static_glb016_reproducibility_satisfied must be true"
        )
    return fail_reasons


def _validate_glb012_capability_proof(binding: Glb012CapabilityProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.integration_input_digest:
        fail_reasons.append("glb012_capability_proof: integration_input_digest required")
    elif not _valid_sha256_digest(binding.integration_input_digest):
        fail_reasons.append(
            "glb012_capability_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    if not binding.integration_proof_digest:
        fail_reasons.append("glb012_capability_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(binding.integration_proof_digest):
        fail_reasons.append(
            "glb012_capability_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    if binding.glb_integration_pass is not True:
        fail_reasons.append("glb012_capability_proof: glb_integration_pass must be true")
    if not binding.lifecycle_matrix_digest:
        fail_reasons.append("glb012_capability_proof: lifecycle_matrix_digest required")
    elif binding.lifecycle_matrix_digest != compute_glb_lifecycle_matrix_digest():
        fail_reasons.append("glb012_capability_proof: lifecycle_matrix_digest mismatch")
    return fail_reasons


def _validate_pe21_reconciliation_proof(
    binding: Pe21ReconciliationPrimaryEvidenceProofBinding,
) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.integration_input_digest:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: integration_input_digest required"
        )
    elif not _valid_sha256_digest(binding.integration_input_digest):
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: integration_input_digest must be "
            "64-char lowercase sha256 hex"
        )
    if not binding.integration_proof_digest:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: integration_proof_digest required"
        )
    elif not _valid_sha256_digest(binding.integration_proof_digest):
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: integration_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    if binding.pe21_integration_pass is not True:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: pe21_integration_pass must be true"
        )
    if binding.durable_primary_evidence_binding_proven is not True:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: "
            "durable_primary_evidence_binding_proven must be true"
        )
    if not binding.lifecycle_matrix_digest:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: lifecycle_matrix_digest required"
        )
    elif binding.lifecycle_matrix_digest != compute_pe21_lifecycle_matrix_digest():
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_proof: lifecycle_matrix_digest mismatch"
        )
    return fail_reasons


def _validate_pe22_proof(binding: Pe22RiskKillswitchFlattenProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.integration_input_digest:
        fail_reasons.append("pe22_risk_killswitch_flatten_proof: integration_input_digest required")
    elif not _valid_sha256_digest(binding.integration_input_digest):
        fail_reasons.append(
            "pe22_risk_killswitch_flatten_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    if not binding.integration_proof_digest:
        fail_reasons.append("pe22_risk_killswitch_flatten_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(binding.integration_proof_digest):
        fail_reasons.append(
            "pe22_risk_killswitch_flatten_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    if binding.pe22_integration_pass is not True:
        fail_reasons.append(
            "pe22_risk_killswitch_flatten_proof: pe22_integration_pass must be true"
        )
    if not binding.lifecycle_matrix_digest:
        fail_reasons.append("pe22_risk_killswitch_flatten_proof: lifecycle_matrix_digest required")
    elif binding.lifecycle_matrix_digest != compute_pe22_lifecycle_matrix_digest():
        fail_reasons.append("pe22_risk_killswitch_flatten_proof: lifecycle_matrix_digest mismatch")
    return fail_reasons


def _validate_pe23_proof(binding: Pe23CapitalSlotRatchetReleaseProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.integration_input_digest:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: integration_input_digest required"
        )
    elif not _valid_sha256_digest(binding.integration_input_digest):
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    if not binding.integration_proof_digest:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: integration_proof_digest required"
        )
    elif not _valid_sha256_digest(binding.integration_proof_digest):
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    if binding.pe23_integration_pass is not True:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: pe23_integration_pass must be true"
        )
    if not binding.lifecycle_matrix_digest:
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: lifecycle_matrix_digest required"
        )
    elif binding.lifecycle_matrix_digest != compute_pe23_lifecycle_matrix_digest():
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: lifecycle_matrix_digest mismatch"
        )
    return fail_reasons


def _validate_pe24_proof(binding: Pe24PilotEnvelopeProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.integration_input_digest:
        fail_reasons.append("pe24_pilot_envelope_proof: integration_input_digest required")
    elif not _valid_sha256_digest(binding.integration_input_digest):
        fail_reasons.append(
            "pe24_pilot_envelope_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    if not binding.integration_proof_digest:
        fail_reasons.append("pe24_pilot_envelope_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(binding.integration_proof_digest):
        fail_reasons.append(
            "pe24_pilot_envelope_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    if binding.pe24_integration_pass is not True:
        fail_reasons.append("pe24_pilot_envelope_proof: pe24_integration_pass must be true")
    if binding.pilot_envelope_static_ready is not True:
        fail_reasons.append("pe24_pilot_envelope_proof: pilot_envelope_static_ready must be true")
    if not binding.lifecycle_matrix_digest:
        fail_reasons.append("pe24_pilot_envelope_proof: lifecycle_matrix_digest required")
    elif binding.lifecycle_matrix_digest != compute_pe24_lifecycle_matrix_digest():
        fail_reasons.append("pe24_pilot_envelope_proof: lifecycle_matrix_digest mismatch")
    return fail_reasons


def _validate_pe25_operator_closure_proof(binding: Pe25OperatorClosureProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.closure_input_digest:
        fail_reasons.append("pe25_operator_closure_proof: closure_input_digest required")
    elif not _valid_sha256_digest(binding.closure_input_digest):
        fail_reasons.append(
            "pe25_operator_closure_proof: closure_input_digest must be 64-char lowercase sha256 hex"
        )
    if not binding.closure_result_digest:
        fail_reasons.append("pe25_operator_closure_proof: closure_result_digest required")
    elif not _valid_sha256_digest(binding.closure_result_digest):
        fail_reasons.append(
            "pe25_operator_closure_proof: closure_result_digest must be 64-char lowercase sha256 hex"
        )
    if binding.pe25_integration_pass is not True:
        fail_reasons.append("pe25_operator_closure_proof: pe25_integration_pass must be true")
    if binding.operator_closure_static_complete is not True:
        fail_reasons.append(
            "pe25_operator_closure_proof: operator_closure_static_complete must be true"
        )
    if not binding.lifecycle_matrix_digest:
        fail_reasons.append("pe25_operator_closure_proof: lifecycle_matrix_digest required")
    elif binding.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("pe25_operator_closure_proof: lifecycle_matrix_digest mismatch")
    return fail_reasons


def _validate_zero_order_capability_proof(binding: ZeroOrderCapabilityProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if binding.capability_owner != ZERO_ORDER_CAPABILITY_OWNER:
        fail_reasons.append(
            f"zero_order_capability_proof: capability_owner must be {ZERO_ORDER_CAPABILITY_OWNER!r}"
        )
    if not binding.capability_proof_digest:
        fail_reasons.append("zero_order_capability_proof: capability_proof_digest required")
    elif not _valid_sha256_digest(binding.capability_proof_digest):
        fail_reasons.append(
            "zero_order_capability_proof: capability_proof_digest must be 64-char lowercase sha256 hex"
        )
    if binding.zero_order_plan_only_capable is not True:
        fail_reasons.append(
            "zero_order_capability_proof: zero_order_plan_only_capable must be true"
        )
    return fail_reasons


def _compute_pe37_boundary_input_digest(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
) -> str:
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        compute_boundary_input_digest,
    )

    return compute_boundary_input_digest(boundary_input)


def _validate_pe37_traceability_proof(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
) -> list[str]:
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        BOUNDARY_OWNER as pe37_boundary_owner,
        CONTRACT_VERSION as pe37_contract_version,
        compute_traceability_identity,
        evaluate_durable_evidence_traceability_boundary,
    )

    fail_reasons: list[str] = []
    proof = assembly_input.pe37_traceability_proof
    boundary_input = assembly_input.pe37_traceability_boundary_input

    if proof.traceability_owner != pe37_boundary_owner:
        fail_reasons.append(
            f"pe37_traceability_proof: traceability_owner must be {pe37_boundary_owner!r}"
        )
    if proof.traceability_owner != pe37_contract_version:
        fail_reasons.append(
            f"pe37_traceability_proof: traceability_owner must be {pe37_contract_version!r}"
        )

    if not proof.source_revision:
        fail_reasons.append("pe37_traceability_proof: source_revision required")
    elif not _valid_commit_sha(proof.source_revision):
        fail_reasons.append(
            "pe37_traceability_proof: source_revision must be full 40-char lowercase commit SHA"
        )
    elif proof.source_revision != assembly_input.source_revision:
        fail_reasons.append("pe37_traceability_proof: source_revision mismatch")

    computed_boundary_input_digest = _compute_pe37_boundary_input_digest(boundary_input)
    if not proof.boundary_input_digest:
        fail_reasons.append("pe37_traceability_proof: boundary_input_digest required")
    elif not _valid_sha256_digest(proof.boundary_input_digest):
        fail_reasons.append(
            "pe37_traceability_proof: boundary_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.boundary_input_digest != computed_boundary_input_digest:
        fail_reasons.append("pe37_traceability_proof: boundary_input_digest mismatch")

    if not proof.boundary_result_digest:
        fail_reasons.append("pe37_traceability_proof: boundary_result_digest required")
    elif not _valid_sha256_digest(proof.boundary_result_digest):
        fail_reasons.append(
            "pe37_traceability_proof: boundary_result_digest must be 64-char lowercase sha256 hex"
        )

    if not proof.traceability_identity:
        fail_reasons.append("pe37_traceability_proof: traceability_identity required")
    elif not _valid_sha256_digest(proof.traceability_identity):
        fail_reasons.append(
            "pe37_traceability_proof: traceability_identity must be 64-char lowercase sha256 hex"
        )

    if proof.pe37_integration_pass is not True:
        fail_reasons.append("pe37_traceability_proof: pe37_integration_pass must be true")
    if proof.durable_evidence_traceability_boundary_satisfied is not True:
        fail_reasons.append(
            "pe37_traceability_proof: durable_evidence_traceability_boundary_satisfied must be true"
        )

    pe37_result = evaluate_durable_evidence_traceability_boundary(boundary_input)
    if not pe37_result["boundary_pass"]:
        fail_reasons.append("pe37_traceability_boundary_input: PE-37 boundary evaluation failed")
        fail_reasons.extend(
            f"pe37_traceability_boundary_input: {reason}" for reason in pe37_result["fail_reasons"]
        )
    elif not pe37_result["durable_evidence_traceability_boundary_satisfied"]:
        fail_reasons.append(
            "pe37_traceability_boundary_input: durable_evidence_traceability_boundary_satisfied required"
        )

    computed_traceability_identity = pe37_result.get("traceability_identity")
    if computed_traceability_identity is not None:
        if proof.traceability_identity != computed_traceability_identity:
            fail_reasons.append("pe37_traceability_proof: traceability_identity mismatch")
        expected_traceability = compute_traceability_identity(
            source_revision=proof.source_revision,
            proof_chain=boundary_input.proof_chain,
            archive_identity=boundary_input.pe16_archive_binding.archive_identity,
            archive_manifest_digest=boundary_input.pe16_archive_binding.archive_manifest_digest,
            operator_review_proof_identity=boundary_input.pe19_pe20_review_proof.operator_review_proof_identity,
        )
        if proof.traceability_identity != expected_traceability:
            fail_reasons.append(
                "pe37_traceability_proof: traceability_identity drift from compute_traceability_identity"
            )

    computed_boundary_result_digest = pe37_result.get("boundary_result_digest")
    if computed_boundary_result_digest is not None:
        if proof.boundary_result_digest != computed_boundary_result_digest:
            fail_reasons.append("pe37_traceability_proof: boundary_result_digest mismatch")

    pe34_source = (
        boundary_input.pe36_boundary_input.pe35_boundary_input.pe34_handoff.source_revision
    )
    if pe34_source != assembly_input.source_revision:
        fail_reasons.append(
            "pe37_traceability_boundary_input: source_revision mismatch with assembly"
        )

    return fail_reasons


def validate_preflight_execution_readiness_assembly_input(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
) -> list[str]:
    """Fail-closed validation of explicit assembly input bindings."""
    fail_reasons: list[str] = []

    if not assembly_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(assembly_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not assembly_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif assembly_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")
    if not assembly_input.adapter_id:
        fail_reasons.append("adapter_id required")
    if not assembly_input.assembly_id:
        fail_reasons.append("assembly_id required")

    fail_reasons.extend(
        _validate_instrument_scope(assembly_input.instrument, assembly_input.market_type)
    )

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(assembly_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    matrix = assembly_input.lifecycle_matrix_proof
    if matrix.pe12_contract_version != PE12_CONTRACT_VERSION:
        fail_reasons.append(
            f"lifecycle_matrix_proof: pe12_contract_version must be {PE12_CONTRACT_VERSION!r}"
        )
    if not matrix.lifecycle_matrix_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest required")
    elif matrix.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest mismatch")
    if not matrix.lifecycle_state_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_state_digest required")
    elif not _valid_sha256_digest(matrix.lifecycle_state_digest):
        fail_reasons.append(
            "lifecycle_matrix_proof: lifecycle_state_digest must be 64-char lowercase sha256 hex"
        )
    if matrix.assigned_lifecycle_phase != PHASE_STATIC_PREFLIGHT:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be {PHASE_STATIC_PREFLIGHT!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")
    if matrix.readiness_decision_phase != PHASE_ZERO_ORDER:
        fail_reasons.append(
            f"lifecycle_matrix_proof: readiness_decision_phase must be {PHASE_ZERO_ORDER!r}"
        )

    fail_reasons.extend(_validate_pe13_packet_proof(assembly_input.pe13_packet_proof))
    fail_reasons.extend(_validate_pe14_builder_proof(assembly_input.pe14_builder_proof))
    fail_reasons.extend(_validate_pe15_replay_proof(assembly_input.pe15_replay_proof))
    fail_reasons.extend(_validate_pe16_archive_proof(assembly_input.pe16_archive_proof))
    fail_reasons.extend(
        _validate_pe17_completeness_truth_proof(assembly_input.pe17_completeness_truth_proof)
    )
    fail_reasons.extend(_validate_pe18_source_state_proof(assembly_input.pe18_source_state_proof))
    fail_reasons.extend(_validate_pe19_review_proof(assembly_input.pe19_review_proof))
    fail_reasons.extend(
        _validate_pe20_durable_review_package(assembly_input.pe20_durable_review_package)
    )
    fail_reasons.extend(_validate_glb012_capability_proof(assembly_input.glb012_capability_proof))
    fail_reasons.extend(
        _validate_pe21_reconciliation_proof(
            assembly_input.pe21_reconciliation_primary_evidence_proof
        )
    )
    fail_reasons.extend(_validate_pe22_proof(assembly_input.pe22_risk_killswitch_flatten_proof))
    fail_reasons.extend(
        _validate_pe23_proof(assembly_input.pe23_capital_slot_ratchet_release_proof)
    )
    fail_reasons.extend(_validate_pe24_proof(assembly_input.pe24_pilot_envelope_proof))
    fail_reasons.extend(
        _validate_pe25_operator_closure_proof(assembly_input.pe25_operator_closure_proof)
    )
    fail_reasons.extend(_validate_pe37_traceability_proof(assembly_input))
    fail_reasons.extend(
        _validate_zero_order_capability_proof(assembly_input.zero_order_capability_proof)
    )
    fail_reasons.extend(_validate_safety_snapshot(assembly_input.safety_snapshot))

    if assembly_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if assembly_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if assembly_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_static_preflight_compatibility(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 static_preflight phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_STATIC_PREFLIGHT]
    snapshot = assembly_input.safety_snapshot

    if descriptor.network_phase and snapshot.network_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: network_allowed true for static_preflight"
        )
    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: orders_allowed true for static_preflight"
        )
    if descriptor.credentials_phase and snapshot.credentials_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: credentials_allowed true for static_preflight"
        )
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for static_preflight"
        )
    if snapshot.live_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: live_authorized true for static_preflight"
        )
    if snapshot.zero_order_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: zero_order_authorized true for static_preflight"
        )
    if snapshot.operator_closure_authorized:
        fail_reasons.append(
            "lifecycle/closure contradiction: operator_closure_authorized true for static_preflight"
        )
    if snapshot.operator_decision_authorized:
        fail_reasons.append(
            "lifecycle/closure contradiction: operator_decision_authorized true for static_preflight"
        )
    if snapshot.pilot_start_authorized:
        fail_reasons.append(
            "lifecycle/pilot contradiction: pilot_start_authorized true for static_preflight"
        )
    if snapshot.promotion_authorized:
        fail_reasons.append("lifecycle/pilot contradiction: promotion_authorized true")
    if snapshot.capital_reallocation_authorized:
        fail_reasons.append("lifecycle/pilot contradiction: capital_reallocation_authorized true")
    if snapshot.reserve_topup_allowed:
        fail_reasons.append("lifecycle/pilot contradiction: reserve_topup_allowed true")

    return fail_reasons


def evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_packet_digest: str | None = None,
    expected_input_capture_digest: str | None = None,
    expected_replay_manifest_digest: str | None = None,
    expected_archive_identity: str | None = None,
    expected_source_state_digest: str | None = None,
    expected_pe19_review_proof_digest: str | None = None,
    expected_pe20_package_id: str | None = None,
    expected_glb012_integration_proof_digest: str | None = None,
    expected_pe21_integration_proof_digest: str | None = None,
    expected_pe22_integration_proof_digest: str | None = None,
    expected_pe23_integration_proof_digest: str | None = None,
    expected_pe24_integration_proof_digest: str | None = None,
    expected_pe25_closure_result_digest: str | None = None,
    expected_assembly_id: str | None = None,
    expected_traceability_identity: str | None = None,
    extra_traceability_fields: tuple[str, ...] = (),
    injected_traceability_overrides: dict[str, Any] | None = None,
    bound_traceability_identities: tuple[str, ...] = (),
    bound_admission_identities: tuple[str, ...] = (),
    dirty_source_state: bool = False,
    assembly_complete_without_proof_chain: bool = False,
    assembly_review_eligible_without_proof_chain: bool = False,
    operator_closure_authorized: bool = False,
    operator_decision_authorized: bool = False,
    approval_authorized: bool = False,
    go_no_go_authorized: bool = False,
    pilot_start_authorized: bool = False,
    promotion_authorized: bool = False,
    capital_reallocation_authorized: bool = False,
    reserve_topup_allowed: bool = False,
    network_allowed: bool = False,
    scheduler_runtime_allowed: bool = False,
    execution_authorized: bool = False,
    live_authorized: bool = False,
    zero_order_authorized: bool = False,
    credentials_allowed: bool = False,
    orders_allowed: bool = False,
    killswitch_active: bool = False,
    killswitch_triggered: bool = False,
    unresolved_risk_state: bool = False,
    invalid_ratchet: bool = False,
    disallowed_slot_basis_increase: bool = False,
    manipulated_release_eligibility: bool = False,
    loose_boolean_readiness: bool = False,
    unknown_lifecycle_state: str | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-12..PE-25 preflight execution readiness assembly proof."""
    fail_reasons = validate_preflight_execution_readiness_assembly_input(assembly_input)

    if expected_source_revision is not None:
        if assembly_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = assembly_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_packet_digest is not None:
        if assembly_input.pe13_packet_proof.packet_digest != expected_packet_digest:
            fail_reasons.append("pe13_packet_proof: packet_digest mismatch")

    if expected_input_capture_digest is not None:
        if assembly_input.pe14_builder_proof.input_capture_digest != expected_input_capture_digest:
            fail_reasons.append("pe14_builder_proof: input_capture_digest mismatch")

    if expected_replay_manifest_digest is not None:
        if (
            assembly_input.pe15_replay_proof.replay_manifest_digest
            != expected_replay_manifest_digest
        ):
            fail_reasons.append("pe15_replay_proof: replay_manifest_digest mismatch")

    if expected_archive_identity is not None:
        if assembly_input.pe16_archive_proof.archive_identity != expected_archive_identity:
            fail_reasons.append("pe16_archive_proof: archive_identity mismatch")

    if expected_source_state_digest is not None:
        if (
            assembly_input.pe18_source_state_proof.source_state_digest
            != expected_source_state_digest
        ):
            fail_reasons.append("pe18_source_state_proof: source_state_digest mismatch")

    if expected_pe19_review_proof_digest is not None:
        if (
            assembly_input.pe19_review_proof.review_proof_digest
            != expected_pe19_review_proof_digest
        ):
            fail_reasons.append("pe19_review_proof: review_proof_digest mismatch")

    if expected_pe20_package_id is not None:
        if assembly_input.pe20_durable_review_package.package_id != expected_pe20_package_id:
            fail_reasons.append("pe20_durable_review_package: package_id mismatch")

    if expected_glb012_integration_proof_digest is not None:
        if (
            assembly_input.glb012_capability_proof.integration_proof_digest
            != expected_glb012_integration_proof_digest
        ):
            fail_reasons.append("glb012_capability_proof: integration_proof_digest mismatch")

    if expected_pe21_integration_proof_digest is not None:
        if (
            assembly_input.pe21_reconciliation_primary_evidence_proof.integration_proof_digest
            != expected_pe21_integration_proof_digest
        ):
            fail_reasons.append(
                "pe21_reconciliation_primary_evidence_proof: integration_proof_digest mismatch"
            )

    if expected_pe22_integration_proof_digest is not None:
        if (
            assembly_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest
            != expected_pe22_integration_proof_digest
        ):
            fail_reasons.append(
                "pe22_risk_killswitch_flatten_proof: integration_proof_digest mismatch"
            )

    if expected_pe23_integration_proof_digest is not None:
        if (
            assembly_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest
            != expected_pe23_integration_proof_digest
        ):
            fail_reasons.append(
                "pe23_capital_slot_ratchet_release_proof: integration_proof_digest mismatch"
            )

    if expected_pe24_integration_proof_digest is not None:
        if (
            assembly_input.pe24_pilot_envelope_proof.integration_proof_digest
            != expected_pe24_integration_proof_digest
        ):
            fail_reasons.append("pe24_pilot_envelope_proof: integration_proof_digest mismatch")

    if expected_pe25_closure_result_digest is not None:
        if (
            assembly_input.pe25_operator_closure_proof.closure_result_digest
            != expected_pe25_closure_result_digest
        ):
            fail_reasons.append("pe25_operator_closure_proof: closure_result_digest mismatch")

    if expected_assembly_id is not None:
        if assembly_input.assembly_id != expected_assembly_id:
            fail_reasons.append("assembly_id mismatch")

    if expected_traceability_identity is not None:
        if (
            assembly_input.pe37_traceability_proof.traceability_identity
            != expected_traceability_identity
        ):
            fail_reasons.append("pe37_traceability_proof: traceability_identity mismatch")

    if extra_traceability_fields or injected_traceability_overrides:
        from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
            evaluate_durable_evidence_traceability_boundary,
        )

        pe37_boundary_input = assembly_input.pe37_traceability_boundary_input
        pe37_injection = evaluate_durable_evidence_traceability_boundary(
            pe37_boundary_input,
            extra_traceability_fields=extra_traceability_fields,
            injected_traceability_overrides=injected_traceability_overrides,
        )
        if pe37_injection["fail_reasons"]:
            fail_reasons.extend(
                f"pe37_traceability_boundary_input: {reason}"
                for reason in pe37_injection["fail_reasons"]
            )

    if bound_traceability_identities or bound_admission_identities:
        from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
            evaluate_durable_evidence_traceability_boundary,
        )

        pe37_boundary_input = replace(
            assembly_input.pe37_traceability_boundary_input,
            bound_traceability_identities=bound_traceability_identities,
            bound_admission_identities=bound_admission_identities,
        )
        pe37_replay = evaluate_durable_evidence_traceability_boundary(pe37_boundary_input)
        if pe37_replay["fail_reasons"]:
            fail_reasons.extend(
                f"pe37_traceability_boundary_input: {reason}"
                for reason in pe37_replay["fail_reasons"]
            )

    if dirty_source_state:
        fail_reasons.append("dirty_source_state=true is not allowed")
    if assembly_input.pe18_source_state_proof.dirty_state:
        fail_reasons.append("pe18_source_state_proof: dirty source state is not allowed")

    if assembly_complete_without_proof_chain:
        fail_reasons.append(
            "preflight_execution_readiness_assembly_complete=true without full proof chain is insufficient"
        )
    if assembly_review_eligible_without_proof_chain:
        fail_reasons.append(
            "assembly_review_eligible=true without full proof chain is insufficient"
        )
    if operator_closure_authorized:
        fail_reasons.append("operator_closure_authorized=true is not allowed")
    if operator_decision_authorized:
        fail_reasons.append("operator_decision_authorized=true is not allowed")
    if approval_authorized:
        fail_reasons.append("approval_authorized=true is not allowed")
    if go_no_go_authorized:
        fail_reasons.append("go_no_go_authorized=true is not allowed")
    if pilot_start_authorized:
        fail_reasons.append("pilot_start_authorized=true is not allowed")
    if promotion_authorized:
        fail_reasons.append("promotion_authorized=true is not allowed")
    if capital_reallocation_authorized:
        fail_reasons.append("capital_reallocation_authorized=true is not allowed")
    if reserve_topup_allowed:
        fail_reasons.append("reserve_topup_allowed=true is not allowed")
    if network_allowed:
        fail_reasons.append("network_allowed=true is not allowed")
    if scheduler_runtime_allowed:
        fail_reasons.append("scheduler_runtime_allowed=true is not allowed")
    if execution_authorized:
        fail_reasons.append("execution_authorized=true is not allowed")
    if live_authorized:
        fail_reasons.append("live_authorized=true is not allowed")
    if zero_order_authorized:
        fail_reasons.append("zero_order_authorized=true is not allowed")
    if credentials_allowed:
        fail_reasons.append("credentials_allowed=true is not allowed")
    if orders_allowed:
        fail_reasons.append("orders_allowed=true is not allowed")
    if killswitch_active:
        fail_reasons.append("killswitch_active=true is not allowed")
    if killswitch_triggered:
        fail_reasons.append("killswitch_triggered=true is not allowed")
    if unresolved_risk_state:
        fail_reasons.append("unresolved_risk_state=true is not allowed")
    if invalid_ratchet:
        fail_reasons.append("invalid_ratchet=true is not allowed")
    if disallowed_slot_basis_increase:
        fail_reasons.append("disallowed_slot_basis_increase=true is not allowed")
    if manipulated_release_eligibility:
        fail_reasons.append("manipulated_release_eligibility=true is not allowed")
    if loose_boolean_readiness:
        fail_reasons.append("loose_boolean_readiness=true is not allowed")
    if unknown_lifecycle_state is not None:
        if unknown_lifecycle_state not in LIFECYCLE_PHASE_DESCRIPTORS:
            fail_reasons.append(
                f"unknown lifecycle state {unknown_lifecycle_state!r} is not allowed"
            )

    if not fail_reasons:
        fail_reasons.extend(_validate_static_preflight_compatibility(assembly_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    preflight_execution_readiness_assembly_complete = integration_pass

    return {
        "integration_pass": integration_pass,
        "assembly_input_digest": compute_assembly_input_digest(assembly_input),
        "assembly_result_digest": (
            compute_assembly_result_digest(
                assembly_input,
                preflight_execution_readiness_assembly_complete=(
                    preflight_execution_readiness_assembly_complete
                ),
            )
            if integration_pass
            else None
        ),
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "readiness_decision_phase": matrix.readiness_decision_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "traceability_identity": (
            assembly_input.pe37_traceability_proof.traceability_identity
            if integration_pass
            else None
        ),
        "pe37_durable_evidence_traceability_boundary_static_proven": integration_pass,
        "pe12_preflight_execution_readiness_assembly_proven": (
            preflight_execution_readiness_assembly_complete
        ),
        "preflight_execution_readiness_assembly_complete": (
            preflight_execution_readiness_assembly_complete
        ),
        "assembly_review_eligible": preflight_execution_readiness_assembly_complete,
        "global_preflight_execution_readiness": GLOBAL_PREFLIGHT_EXECUTION_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_preflight_execution": OPERATIVE_PREFLIGHT_EXECUTION,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_approval_created": OPERATIVE_APPROVAL_CREATED,
        "operative_go_no_go_created": OPERATIVE_GO_NO_GO_CREATED,
        "operative_pilot_executed": OPERATIVE_PILOT_EXECUTED,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_reconciliation_executed": OPERATIVE_RECONCILIATION_EXECUTED,
        "operative_risk_evaluation_executed": OPERATIVE_RISK_EVALUATION_EXECUTED,
        "operative_killswitch_executed": OPERATIVE_KILLSWITCH_EXECUTED,
        "operative_flatten_executed": OPERATIVE_FLATTEN_EXECUTED,
        "operative_ratchet_applied": OPERATIVE_RATCHET_APPLIED,
        "operative_slot_release_executed": OPERATIVE_SLOT_RELEASE_EXECUTED,
        "operative_capital_reallocation_executed": OPERATIVE_CAPITAL_REALLOCATION_EXECUTED,
        "operative_reserve_movement_executed": OPERATIVE_RESERVE_MOVEMENT_EXECUTED,
        "account_state_queried": ACCOUNT_STATE_QUERIED,
        "position_state_queried": POSITION_STATE_QUERIED,
        "order_state_queried": ORDER_STATE_QUERIED,
        "exchange_state_queried": EXCHANGE_STATE_QUERIED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "zero_order_authorized": False,
        "network_allowed": False,
        "credentials_allowed": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "operator_closure_authorized": False,
        "operator_decision_authorized": False,
        "pilot_start_authorized": False,
        "promotion_authorized": False,
        "capital_reallocation_authorized": False,
        "reserve_topup_allowed": False,
        "fail_reasons": fail_reasons,
    }


def default_minimal_pe37_traceability_proof(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
) -> Pe37TraceabilityProofBinding:
    """Build canonical PE-37 traceability proof binding from explicit boundary evaluation."""
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        BOUNDARY_OWNER as pe37_boundary_owner,
        evaluate_durable_evidence_traceability_boundary,
    )

    pe37_result = evaluate_durable_evidence_traceability_boundary(boundary_input)
    traceability_identity = pe37_result["traceability_identity"]
    boundary_result_digest = pe37_result["boundary_result_digest"]
    if traceability_identity is None or boundary_result_digest is None:
        raise ValueError("PE-37 traceability proof binding requires satisfied boundary evaluation")
    return Pe37TraceabilityProofBinding(
        traceability_owner=pe37_boundary_owner,
        source_revision=boundary_input.pe36_boundary_input.pe35_boundary_input.pe34_handoff.source_revision,
        boundary_input_digest=_compute_pe37_boundary_input_digest(boundary_input),
        boundary_result_digest=boundary_result_digest,
        traceability_identity=traceability_identity,
        pe37_integration_pass=pe37_result["boundary_pass"],
        durable_evidence_traceability_boundary_satisfied=pe37_result[
            "durable_evidence_traceability_boundary_satisfied"
        ],
    )


_assembly_default_build_depth = threading.local()


def _assembly_default_build_depth_value() -> int:
    return int(getattr(_assembly_default_build_depth, "value", 0))


def _set_assembly_default_build_depth(value: int) -> None:
    _assembly_default_build_depth.value = value


def _default_minimal_pe37_traceability_stub(
    *,
    source_revision: str,
    satisfied: bool,
) -> tuple[DurableEvidenceTraceabilityBoundaryInput, Pe37TraceabilityProofBinding]:
    """Non-recursive PE-37 placeholder for nested default assembly construction."""
    from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
        HANDOFF_STATE_CURRENT,
        CanonicalCurrentBindings,
        HandoffLifecycleMetadata,
        HandoffStalenessRevocationRecoveryBoundaryInput,
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        OperatorReviewAdmissionPresentationBoundaryInput,
        default_minimal_pe35_proof_binding,
    )
    from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
        COHERENCE_OWNER as PE33_COHERENCE_OWNER,
    )
    from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
        ContractVersionsInput as Pe34ContractVersionsInput,
        OperatorReviewHandoffBoundaryInput,
        Pe19UndecidedReviewInputBinding,
        Pe20UndecidedPackageEligibilityBinding,
        Pe25CrossSliceClosureBinding,
        Pe33CoherenceProofBinding,
        compute_boundary_input_digest as compute_pe34_boundary_input_digest,
        compute_review_input_digest,
        default_minimal_safety_snapshot as default_minimal_pe34_safety_snapshot,
    )
    from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
        PACKAGE_SCHEMA_VERSION as PE20_PACKAGE_SCHEMA_VERSION,
    )
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        default_minimal_operator_review_input,
    )
    from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
        compute_archive_identity,
    )
    from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
        COMPLETENESS_CONTRACT_VERSION,
    )

    packet_digest = "a" * 64
    input_capture_digest = "b" * 64
    replay_manifest_digest = "c" * 64
    archive_manifest_digest = "e" * 64
    source_state_digest = "f" * 64
    archive_identity = compute_archive_identity(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=input_capture_digest,
        manifest_digest=archive_manifest_digest,
    )
    review_input = default_minimal_operator_review_input(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=input_capture_digest,
        replay_manifest_digest=replay_manifest_digest,
        archive_identity=archive_identity,
        archive_manifest_digest=archive_manifest_digest,
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
        source_state_digest=source_state_digest,
    )
    pe33_input_digest = "0" * 64
    pe33_proof_digest = "1" * 64
    pe25_slot_digest = "5" * 64
    review_input_digest = compute_review_input_digest(review_input)
    pe34_handoff = OperatorReviewHandoffBoundaryInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        handoff_id="operator-review-handoff-boundary-001",
        adapter_id="offline_bounded_futures_testnet_adapter_v0",
        instrument="PF_ETHUSD",
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=Pe34ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe19_operator_review=PE19_CONTRACT_VERSION,
            pe20_review_proof_package=PE20_CONTRACT_VERSION,
            pe25_operator_closure=PE25_CONTRACT_VERSION,
            pe33_cross_slice_proof_coherence="bounded_futures_testnet_cross_slice_proof_coherence_integration.v0",
            integration="bounded_futures_testnet_operator_review_handoff_boundary.v0",
        ),
        pe33_coherence_proof=Pe33CoherenceProofBinding(
            coherence_owner=PE33_COHERENCE_OWNER,
            source_revision=source_revision,
            integration_input_digest=pe33_input_digest,
            integration_proof_digest=pe33_proof_digest,
            cross_slice_proof_coherence_for_separate_operator_review=True,
            static_pe12_lifecycle_chain_complete=True,
            integration_pass=True,
        ),
        pe33_integration_input=None,
        pe19_undecided_review_input=Pe19UndecidedReviewInputBinding(
            review_input_owner=PE19_CONTRACT_VERSION,
            source_revision=source_revision,
            review_input=review_input,
            pe33_integration_proof_digest=pe33_proof_digest,
            operator_name_legibility=None,
        ),
        pe20_undecided_package_eligibility=Pe20UndecidedPackageEligibilityBinding(
            package_owner=PE20_CONTRACT_VERSION,
            source_revision=source_revision,
            review_input_digest=review_input_digest,
            package_schema_version=PE20_PACKAGE_SCHEMA_VERSION,
            undecided_package_eligibility=True,
            operative_decision_issued=False,
            decision_record_digest=None,
            package_id=None,
        ),
        pe25_cross_slice_closure=Pe25CrossSliceClosureBinding(
            closure_owner=PE25_CONTRACT_VERSION,
            source_revision=source_revision,
            closure_result_digest=pe25_slot_digest,
            pe33_pe25_slot_digest=pe25_slot_digest,
            operative_operator_closure_executed=False,
            operator_closure_static_complete=True,
        ),
        safety_snapshot=default_minimal_pe34_safety_snapshot(),
    )
    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe35_input = HandoffStalenessRevocationRecoveryBoundaryInput(
        pe34_handoff=pe34_handoff,
        canonical_current=CanonicalCurrentBindings(
            source_revision=source_revision,
            pe33_integration_proof_digest=pe33_proof_digest,
            pe34_handoff_digest=pe34_digest,
            replay_manifest_digest=replay_manifest_digest,
            archive_manifest_digest=archive_manifest_digest,
        ),
        lifecycle_metadata=HandoffLifecycleMetadata(
            lifecycle_state=HANDOFF_STATE_CURRENT,
            handoff_digest=pe34_digest,
            review_identity="glb-016-bounded-futures-testnet-operator-review",
            generation=0,
        ),
    )
    pe36_input = OperatorReviewAdmissionPresentationBoundaryInput(
        pe35_boundary_input=pe35_input,
        pe35_proof=default_minimal_pe35_proof_binding(pe35_input),
        operator_name_legibility=None,
    )
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        DurableEvidenceTraceabilityBoundaryInput,
        default_minimal_pe16_archive_binding,
        default_minimal_pe19_pe20_review_proof_binding,
        default_minimal_pe36_proof_binding,
        default_minimal_proof_chain_binding,
    )

    boundary_input = DurableEvidenceTraceabilityBoundaryInput(
        pe36_boundary_input=pe36_input,
        pe36_proof=default_minimal_pe36_proof_binding(pe36_input),
        pe16_archive_binding=default_minimal_pe16_archive_binding(pe36_input),
        pe19_pe20_review_proof=default_minimal_pe19_pe20_review_proof_binding(pe36_input),
        proof_chain=default_minimal_proof_chain_binding(pe36_input),
    )
    if satisfied:
        return boundary_input, default_minimal_pe37_traceability_proof(boundary_input)

    traceability_identity = "2" * 64
    proof = Pe37TraceabilityProofBinding(
        traceability_owner=PE37_BOUNDARY_OWNER,
        source_revision=source_revision,
        boundary_input_digest=_compute_pe37_boundary_input_digest(boundary_input),
        boundary_result_digest="3" * 64,
        traceability_identity=traceability_identity,
        pe37_integration_pass=False,
        durable_evidence_traceability_boundary_satisfied=False,
    )
    return boundary_input, proof


def default_minimal_safety_snapshot() -> AssemblySafetySnapshot:
    return AssemblySafetySnapshot(
        preflight_remains_blocked=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        zero_order_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        operator_closure_authorized=False,
        operator_decision_authorized=False,
        pilot_start_authorized=False,
        promotion_authorized=False,
        capital_reallocation_authorized=False,
        reserve_topup_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def default_minimal_assembly_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    assembly_id: str = "preflight-execution-readiness-assembly-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> PreflightExecutionReadinessAssemblyInput:
    """Minimal valid futures-generic assembly input for offline tests."""
    depth = _assembly_default_build_depth_value()
    _set_assembly_default_build_depth(depth + 1)
    try:
        state_digest = lifecycle_state_digest or "e" * 64
        matrix_digest = compute_lifecycle_matrix_digest()

        if depth > 0:
            pe37_boundary_input, pe37_traceability_proof = _default_minimal_pe37_traceability_stub(
                source_revision=source_revision,
                satisfied=False,
            )
        else:
            pe37_boundary_input, pe37_traceability_proof = _default_minimal_pe37_traceability_stub(
                source_revision=source_revision,
                satisfied=True,
            )

        return PreflightExecutionReadinessAssemblyInput(
            source_revision=source_revision,
            repository_identity=REPOSITORY_IDENTITY,
            adapter_id=adapter_id,
            assembly_id=assembly_id,
            instrument=instrument,
            market_type=DEFAULT_MARKET_TYPE,
            contract_versions=ContractVersionsInput(
                pe12_lifecycle=PE12_CONTRACT_VERSION,
                pe13_packet=PE13_CONTRACT_VERSION,
                pe14_builder=PE14_CONTRACT_VERSION,
                pe15_replay=PE15_CONTRACT_VERSION,
                pe16_archive=PE16_CONTRACT_VERSION,
                pe17_completeness_truth=PE17_CONTRACT_VERSION,
                pe18_source_state_capture=PE18_CONTRACT_VERSION,
                pe19_operator_review=PE19_CONTRACT_VERSION,
                pe20_review_proof_package=PE20_CONTRACT_VERSION,
                glb012_adapter_capability=GLB012_CONTRACT_VERSION,
                pe21_reconciliation_primary_evidence=PE21_CONTRACT_VERSION,
                pe22_risk_killswitch_flatten=PE22_CONTRACT_VERSION,
                pe23_capital_slot_ratchet_release=PE23_CONTRACT_VERSION,
                pe24_pilot_envelope=PE24_CONTRACT_VERSION,
                pe25_operator_closure=PE25_CONTRACT_VERSION,
                pe37_traceability_boundary=PE37_CONTRACT_VERSION,
                integration=CONTRACT_VERSION,
            ),
            lifecycle_matrix_proof=LifecycleMatrixProof(
                pe12_contract_version=PE12_CONTRACT_VERSION,
                lifecycle_matrix_digest=matrix_digest,
                assigned_lifecycle_phase=PHASE_STATIC_PREFLIGHT,
                lifecycle_state_digest=state_digest,
                readiness_decision_phase=PHASE_ZERO_ORDER,
            ),
            pe13_packet_proof=Pe13PacketProofBinding(
                packet_id="0" * 64,
                packet_digest="1" * 64,
                pe13_contract_version=PE13_CONTRACT_VERSION,
                packet_validation_pass=True,
            ),
            pe14_builder_proof=Pe14BuilderProofBinding(
                input_capture_digest="2" * 64,
                builder_alignment_pass=True,
                pe14_contract_version=PE14_CONTRACT_VERSION,
            ),
            pe15_replay_proof=Pe15ReplayProofBinding(
                replay_manifest_digest="3" * 64,
                replay_pass=True,
                manifest_verify_rc=0,
                pe15_contract_version=PE15_CONTRACT_VERSION,
            ),
            pe16_archive_proof=Pe16ArchiveProofBinding(
                archive_identity="4" * 64,
                archive_manifest_digest="5" * 64,
                manifest_verify_rc=0,
                static_persisted_verified=True,
                pe16_contract_version=PE16_CONTRACT_VERSION,
            ),
            pe17_completeness_truth_proof=Pe17CompletenessTruthProofBinding(
                completeness_status=COMPLETENESS_COMPLETE,
                truth_status=TRUTH_READY_FOR_SEPARATE_OPERATOR_REVIEW,
                internal_static_chain_complete=True,
                pe17_contract_version=PE17_CONTRACT_VERSION,
            ),
            pe18_source_state_proof=Pe18SourceStateProofBinding(
                source_state_digest="6" * 64,
                capture_status=CAPTURE_VALID,
                dirty_state=False,
                pe18_contract_version=PE18_CONTRACT_VERSION,
            ),
            pe19_review_proof=Pe19ReviewProofBinding(
                review_input_digest="7" * 64,
                decision_record_digest="8" * 64,
                review_proof_digest="9" * 64,
                review_valid=True,
                decision=DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
                reason_code="evidence_complete",
                non_authorizing=True,
                ready_for_operator_arming=False,
                execution_authorized=False,
                live_authorized=False,
                evidence_manifest_verify_rc=0,
            ),
            pe20_durable_review_package=Pe20DurableReviewPackageBinding(
                package_id="a" * 64,
                package_digest="b" * 64,
                manifest_verify_rc=0,
                static_glb016_reproducibility_satisfied=True,
            ),
            glb012_capability_proof=Glb012CapabilityProofBinding(
                integration_input_digest="c" * 64,
                integration_proof_digest="d" * 64,
                glb_integration_pass=True,
                lifecycle_matrix_digest=compute_glb_lifecycle_matrix_digest(),
            ),
            pe21_reconciliation_primary_evidence_proof=Pe21ReconciliationPrimaryEvidenceProofBinding(
                integration_input_digest="c" * 64,
                integration_proof_digest="d" * 64,
                pe21_integration_pass=True,
                durable_primary_evidence_binding_proven=True,
                lifecycle_matrix_digest=compute_pe21_lifecycle_matrix_digest(),
            ),
            pe22_risk_killswitch_flatten_proof=Pe22RiskKillswitchFlattenProofBinding(
                integration_input_digest="e" * 64,
                integration_proof_digest="f" * 64,
                pe22_integration_pass=True,
                lifecycle_matrix_digest=compute_pe22_lifecycle_matrix_digest(),
            ),
            pe23_capital_slot_ratchet_release_proof=Pe23CapitalSlotRatchetReleaseProofBinding(
                integration_input_digest="0" * 64,
                integration_proof_digest="1" * 64,
                pe23_integration_pass=True,
                lifecycle_matrix_digest=compute_pe23_lifecycle_matrix_digest(),
            ),
            pe24_pilot_envelope_proof=Pe24PilotEnvelopeProofBinding(
                integration_input_digest="2" * 64,
                integration_proof_digest="3" * 64,
                pe24_integration_pass=True,
                lifecycle_matrix_digest=compute_pe24_lifecycle_matrix_digest(),
                pilot_envelope_static_ready=True,
            ),
            pe25_operator_closure_proof=Pe25OperatorClosureProofBinding(
                closure_input_digest="4" * 64,
                closure_result_digest="5" * 64,
                pe25_integration_pass=True,
                operator_closure_static_complete=True,
                lifecycle_matrix_digest=matrix_digest,
            ),
            pe37_traceability_boundary_input=pe37_boundary_input,
            pe37_traceability_proof=pe37_traceability_proof,
            zero_order_capability_proof=ZeroOrderCapabilityProofBinding(
                capability_owner=ZERO_ORDER_CAPABILITY_OWNER,
                capability_proof_digest="6" * 64,
                zero_order_plan_only_capable=True,
            ),
            safety_snapshot=default_minimal_safety_snapshot(),
        )
    finally:
        _set_assembly_default_build_depth(depth)
