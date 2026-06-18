"""Bounded Futures Testnet preflight execution readiness review lifecycle integration (v0, PE-38/PE-41).

Deterministic, offline, explicit-input-only fail-closed integration composing PE-26
preflight execution readiness assembly, PE-40-hardened PE-32 readiness-decision lifecycle
integration (PE-39 admission-presentation→operator-closure proof chain), PE-37 durable
evidence traceability, PE-19/PE-20 operator-review input/proof bindings, PE-34
operator-review handoff boundary, PE-35 staleness/revocation/recovery boundary, PE-25
operator-closure bindings, and bounded-pilot lifecycle static proof composition.

Static integration only — no network, testnet, runtime, credentials, orders, operator
review execution, operative readiness decisions, blocker lifts, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from typing import Any

from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE35_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE35_CONTRACT_VERSION,
    HandoffStalenessRevocationRecoveryBoundaryInput,
    compute_boundary_input_digest as compute_pe35_boundary_input_digest,
    compute_boundary_result_digest as compute_pe35_boundary_result_digest,
    evaluate_handoff_staleness_revocation_recovery_boundary,
    validate_handoff_staleness_revocation_recovery_boundary_input,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
    compute_closure_input_digest as compute_pe25_closure_input_digest,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE37_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE37_CONTRACT_VERSION,
    DurableEvidenceTraceabilityBoundaryInput,
    Pe19Pe20OperatorReviewProofBinding,
    compute_boundary_input_digest as compute_pe37_boundary_input_digest,
    compute_boundary_result_digest as compute_pe37_boundary_result_digest,
    evaluate_durable_evidence_traceability_boundary,
    validate_durable_evidence_traceability_boundary_input,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
    HANDOFF_OWNER as PE34_HANDOFF_OWNER,
    OperatorReviewHandoffBoundaryInput,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
    compute_boundary_result_digest as compute_pe34_boundary_result_digest,
    evaluate_operator_review_handoff_boundary,
    validate_operator_review_handoff_boundary_input,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
    PreflightExecutionReadinessAssemblyInput,
    compute_assembly_input_digest as compute_pe26_assembly_input_digest,
    compute_assembly_result_digest as compute_pe26_assembly_result_digest,
    evaluate_preflight_execution_readiness_assembly_lifecycle_integration,
    validate_preflight_execution_readiness_assembly_input,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    compute_review_input_digest,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
    ADMISSION_LIFECYCLE_CONTRACT_VERSION,
    CONTRACT_VERSION as PE32_CONTRACT_VERSION,
    PE36_CONTRACT_VERSION,
    PE39_BRIDGE_OWNER,
    PE39_CONTRACT_VERSION,
    Pe39BridgeIntegrationProofBinding,
    ReadinessDecisionLifecycleIntegrationInput,
    ReadinessDecisionProofChainBinding,
    READINESS_DECISION_PROOF_CHAIN_SLOT_ORDER,
    compute_integration_input_digest as compute_pe32_integration_input_digest,
    compute_integration_proof_digest as compute_pe32_integration_proof_digest,
    default_minimal_pe39_bridge_integration_proof,
    default_minimal_readiness_decision_proof_chain,
    evaluate_pe39_admission_presentation_operator_closure_lifecycle_bridge,
    evaluate_readiness_decision_lifecycle_integration,
    validate_readiness_decision_lifecycle_integration_input,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = (
    "bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration.v0"
)
SERIALIZATION_VERSION = "bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

REVIEW_LIFECYCLE_MODE = (
    "static_preflight_execution_readiness_review_lifecycle_integration_proof_only"
)
REVIEW_LIFECYCLE_OWNER = CONTRACT_VERSION
CANONICAL_BLOCKER_STATE = "blocked"

GLOBAL_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_READINESS_DECISION_CREATED = False
OPERATIVE_OPERATOR_DECISION_CREATED = False
OPERATIVE_OPERATOR_CLOSURE_EXECUTED = False
OPERATIVE_OPERATOR_REVIEW_EXECUTED = False
OPERATIVE_BLOCKER_LIFT_EXECUTED = False
LIFECYCLE_TRANSITION_EXECUTED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
RUNTIME_STARTED = False
AUTHORITY_LIFT = False
PREFLIGHT_REMAINS_BLOCKED = True

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

_FORBIDDEN_EXTRA_FIELD_FRAGMENTS = (
    "secret",
    "credential",
    "api_key",
    "password",
    "token",
    "command",
    "action",
    "authority",
    "decision",
    "closure",
    "execution_authorized",
    "live_authorized",
    "pilot_start",
    "promotion",
    "network_allowed",
    "orders_allowed",
)

PROOF_CHAIN_SLOT_ORDER = (
    "pe39_bridge_proof_digest",
    "pe39_admission_integration_proof_digest",
    "pe40_pe32_integration_proof_digest",
    "pe38_referenced_pe40_pe32_proof_digest",
    "pe26_assembly_digest",
    "pe32_integration_proof_digest",
    "pe37_boundary_result_digest",
    "pe37_traceability_identity",
    "pe19_review_input_digest",
    "pe20_review_input_digest",
    "pe34_handoff_digest",
    "pe35_boundary_result_digest",
    "pe25_closure_result_digest",
    "pilot_composition_pe32_proof_digest",
    "pilot_composition_pe26_assembly_digest",
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe19_operator_review": PE19_CONTRACT_VERSION,
    "pe20_review_proof_package": PE20_CONTRACT_VERSION,
    "pe25_operator_closure": PE25_CONTRACT_VERSION,
    "pe26_assembly": PE26_CONTRACT_VERSION,
    "pe32_readiness_decision": PE32_CONTRACT_VERSION,
    "pe34_handoff": PE34_CONTRACT_VERSION,
    "pe35_staleness": PE35_CONTRACT_VERSION,
    "pe36_admission_presentation": PE36_CONTRACT_VERSION,
    "pe37_traceability": PE37_CONTRACT_VERSION,
    "admission_presentation_lifecycle": ADMISSION_LIFECYCLE_CONTRACT_VERSION,
    "pe39_bridge": PE39_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe19_operator_review: str
    pe20_review_proof_package: str
    pe25_operator_closure: str
    pe26_assembly: str
    pe32_readiness_decision: str
    pe34_handoff: str
    pe35_staleness: str
    pe36_admission_presentation: str
    pe37_traceability: str
    admission_presentation_lifecycle: str
    pe39_bridge: str
    integration: str


@dataclass(frozen=True)
class Pe26AssemblyProofBinding:
    assembly_owner: str
    source_revision: str
    assembly_input_digest: str
    assembly_result_digest: str
    traceability_identity: str
    pe26_integration_pass: bool
    preflight_execution_readiness_assembly_complete: bool


@dataclass(frozen=True)
class Pe32ReadinessLifecycleProofBinding:
    integration_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    lifecycle_chain_identity: str
    blocker_state: str
    pe32_integration_pass: bool
    readiness_decision_lifecycle_eligibility: bool


@dataclass(frozen=True)
class Pe37TraceabilityProofBinding:
    traceability_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str
    traceability_identity: str
    admission_identity: str | None
    pe37_integration_pass: bool
    durable_evidence_traceability_boundary_satisfied: bool


@dataclass(frozen=True)
class Pe34HandoffProofBinding:
    handoff_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str | None
    pe34_integration_pass: bool
    operator_review_handoff_boundary_satisfied: bool


@dataclass(frozen=True)
class Pe35StalenessProofBinding:
    boundary_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str | None
    handoff_current: bool
    pe35_integration_pass: bool
    handoff_staleness_revocation_recovery_boundary_satisfied: bool


@dataclass(frozen=True)
class Pe25ClosureProofBinding:
    closure_owner: str
    source_revision: str
    closure_result_digest: str
    operative_operator_closure_executed: bool
    operator_closure_static_complete: bool


@dataclass(frozen=True)
class PilotReadinessCompositionProofBinding:
    composition_mode: str
    source_revision: str
    composition_pass: bool
    static_readiness_proof_coherent: bool
    pe32_proof_digest: str
    pe26_assembly_digest: str
    pe26_traceability_identity: str
    pe32_blocker_state: str


@dataclass(frozen=True)
class ReviewLifecycleProofChainBinding:
    pe39_bridge_proof_digest: str
    pe39_admission_integration_proof_digest: str
    pe40_pe32_integration_proof_digest: str
    pe38_referenced_pe40_pe32_proof_digest: str
    pe26_assembly_digest: str
    pe32_integration_proof_digest: str
    pe37_boundary_result_digest: str
    pe37_traceability_identity: str
    pe19_review_input_digest: str
    pe20_review_input_digest: str
    pe34_handoff_digest: str
    pe35_boundary_result_digest: str
    pe25_closure_result_digest: str
    pilot_composition_pe32_proof_digest: str
    pilot_composition_pe26_assembly_digest: str


@dataclass(frozen=True)
class IntegrationSafetySnapshot:
    preflight_remains_blocked: bool
    global_blocker_lift_authorized: bool
    preflight_lift_authorized: bool
    ready_for_operator_arming: bool
    readiness_decision_authorized: bool
    operator_review_authorized: bool
    operator_decision_authorized: bool
    operator_closure_authorized: bool
    execution_authorized: bool
    live_authorized: bool
    zero_order_authorized: bool
    private_readonly_authorized: bool
    validate_only_authorized: bool
    tiny_order_authorized: bool
    reconciliation_authorized: bool
    evidence_acceptance_authorized: bool
    pilot_start_authorized: bool
    promotion_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class PreflightExecutionReadinessReviewLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    integration_id: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    pe26_assembly_input: PreflightExecutionReadinessAssemblyInput
    pe32_integration_input: ReadinessDecisionLifecycleIntegrationInput
    pe37_traceability_boundary_input: DurableEvidenceTraceabilityBoundaryInput
    pe34_handoff_input: OperatorReviewHandoffBoundaryInput
    pe35_boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput
    pe26_assembly_proof: Pe26AssemblyProofBinding
    pe32_readiness_proof: Pe32ReadinessLifecycleProofBinding
    pe37_traceability_proof: Pe37TraceabilityProofBinding
    pe19_pe20_review_proof: Pe19Pe20OperatorReviewProofBinding
    pe34_handoff_proof: Pe34HandoffProofBinding
    pe35_staleness_proof: Pe35StalenessProofBinding
    pe25_closure_proof: Pe25ClosureProofBinding
    pe39_bridge_integration_proof: Pe39BridgeIntegrationProofBinding
    pe40_readiness_decision_proof_chain: ReadinessDecisionProofChainBinding
    pilot_readiness_proof: PilotReadinessCompositionProofBinding
    proof_chain: ReviewLifecycleProofChainBinding
    safety_snapshot: IntegrationSafetySnapshot
    bound_traceability_identities: tuple[str, ...] = ()
    bound_admission_identities: tuple[str, ...] = ()
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def _reject_forbidden_extra_fields(extra_fields: dict[str, Any]) -> list[str]:
    fail_reasons: list[str] = []
    for field_name in extra_fields:
        lowered = field_name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_EXTRA_FIELD_FRAGMENTS):
            fail_reasons.append(f"forbidden extra field: {field_name}")
        else:
            fail_reasons.append(f"unknown extra field: {field_name}")
    return fail_reasons


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


def _validate_safety_snapshot(snapshot: IntegrationSafetySnapshot) -> list[str]:
    fail_reasons: list[str] = []
    required_bools = (
        ("preflight_remains_blocked", True),
        ("global_blocker_lift_authorized", False),
        ("preflight_lift_authorized", False),
        ("ready_for_operator_arming", False),
        ("readiness_decision_authorized", False),
        ("operator_review_authorized", False),
        ("operator_decision_authorized", False),
        ("operator_closure_authorized", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("zero_order_authorized", False),
        ("private_readonly_authorized", False),
        ("validate_only_authorized", False),
        ("tiny_order_authorized", False),
        ("reconciliation_authorized", False),
        ("evidence_acceptance_authorized", False),
        ("pilot_start_authorized", False),
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


def _validate_pe26_assembly_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe26_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe26_assembly_proof
    pe26_input = integration_input.pe26_assembly_input

    if proof.assembly_owner != PE26_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe26_assembly_proof: assembly_owner must be {PE26_CONTRACT_VERSION!r}"
        )
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe26_assembly_proof: source_revision mismatch")
    if proof.assembly_input_digest != compute_pe26_assembly_input_digest(pe26_input):
        fail_reasons.append("pe26_assembly_proof: assembly_input_digest mismatch")
    expected_result_digest = pe26_result.get("assembly_result_digest")
    if not proof.assembly_result_digest:
        fail_reasons.append("pe26_assembly_proof: assembly_result_digest required")
    elif expected_result_digest is None:
        fail_reasons.append("pe26_assembly_proof: PE-26 assembly_result_digest unavailable")
    elif proof.assembly_result_digest != expected_result_digest:
        fail_reasons.append("pe26_assembly_proof: assembly_result_digest mismatch")
    if not proof.traceability_identity:
        fail_reasons.append("pe26_assembly_proof: traceability_identity required")
    elif proof.traceability_identity != pe26_input.pe37_traceability_proof.traceability_identity:
        fail_reasons.append("pe26_assembly_proof: traceability_identity mismatch")
    if proof.pe26_integration_pass is not True:
        fail_reasons.append("pe26_assembly_proof: pe26_integration_pass must be true")
    if proof.preflight_execution_readiness_assembly_complete is not True:
        fail_reasons.append(
            "pe26_assembly_proof: preflight_execution_readiness_assembly_complete must be true"
        )
    return fail_reasons


def _validate_pe32_readiness_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe32_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe32_readiness_proof
    pe32_input = integration_input.pe32_integration_input

    if proof.integration_owner != PE32_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe32_readiness_proof: integration_owner must be {PE32_CONTRACT_VERSION!r}"
        )
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe32_readiness_proof: source_revision mismatch")
    if proof.integration_input_digest != compute_pe32_integration_input_digest(pe32_input):
        fail_reasons.append("pe32_readiness_proof: integration_input_digest mismatch")
    expected_proof_digest = pe32_result.get("integration_proof_digest")
    if not proof.integration_proof_digest:
        fail_reasons.append("pe32_readiness_proof: integration_proof_digest required")
    elif expected_proof_digest is None:
        fail_reasons.append("pe32_readiness_proof: PE-32 integration_proof_digest unavailable")
    elif proof.integration_proof_digest != expected_proof_digest:
        fail_reasons.append("pe32_readiness_proof: integration_proof_digest mismatch")
    lifecycle_chain_identity = pe32_input.lifecycle_matrix_proof.lifecycle_state_digest
    if proof.lifecycle_chain_identity != lifecycle_chain_identity:
        fail_reasons.append("pe32_readiness_proof: lifecycle_chain_identity mismatch")
    if proof.blocker_state != CANONICAL_BLOCKER_STATE:
        fail_reasons.append(
            f"pe32_readiness_proof: blocker_state must be {CANONICAL_BLOCKER_STATE!r}"
        )
    if proof.pe32_integration_pass is not True:
        fail_reasons.append("pe32_readiness_proof: pe32_integration_pass must be true")
    if proof.readiness_decision_lifecycle_eligibility is not True:
        fail_reasons.append(
            "pe32_readiness_proof: readiness_decision_lifecycle_eligibility must be true"
        )
    return fail_reasons


def _validate_pe37_traceability_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe37_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe37_traceability_proof
    pe37_input = integration_input.pe37_traceability_boundary_input

    if proof.traceability_owner != PE37_BOUNDARY_OWNER:
        fail_reasons.append(
            f"pe37_traceability_proof: traceability_owner must be {PE37_BOUNDARY_OWNER!r}"
        )
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe37_traceability_proof: source_revision mismatch")
    if proof.boundary_input_digest != compute_pe37_boundary_input_digest(pe37_input):
        fail_reasons.append("pe37_traceability_proof: boundary_input_digest mismatch")
    expected_result_digest = pe37_result.get("boundary_result_digest")
    if not proof.boundary_result_digest:
        fail_reasons.append("pe37_traceability_proof: boundary_result_digest required")
    elif expected_result_digest is None:
        fail_reasons.append("pe37_traceability_proof: PE-37 boundary_result_digest unavailable")
    elif proof.boundary_result_digest != expected_result_digest:
        fail_reasons.append("pe37_traceability_proof: boundary_result_digest mismatch")
    expected_traceability = pe37_result.get("traceability_identity")
    if not proof.traceability_identity:
        fail_reasons.append("pe37_traceability_proof: traceability_identity required")
    elif expected_traceability is None:
        fail_reasons.append("pe37_traceability_proof: traceability_identity unavailable")
    elif proof.traceability_identity != expected_traceability:
        fail_reasons.append("pe37_traceability_proof: traceability_identity mismatch")
    if proof.admission_identity != pe37_result.get("admission_identity"):
        fail_reasons.append("pe37_traceability_proof: admission_identity mismatch")
    if proof.pe37_integration_pass is not True:
        fail_reasons.append("pe37_traceability_proof: pe37_integration_pass must be true")
    if proof.durable_evidence_traceability_boundary_satisfied is not True:
        fail_reasons.append(
            "pe37_traceability_proof: durable_evidence_traceability_boundary_satisfied must be true"
        )
    return fail_reasons


def _validate_pe34_handoff_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe34_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe34_handoff_proof
    pe34_input = integration_input.pe34_handoff_input

    if proof.handoff_owner != PE34_HANDOFF_OWNER:
        fail_reasons.append(f"pe34_handoff_proof: handoff_owner must be {PE34_HANDOFF_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe34_handoff_proof: source_revision mismatch")
    if proof.boundary_input_digest != compute_pe34_boundary_input_digest(pe34_input):
        fail_reasons.append("pe34_handoff_proof: boundary_input_digest mismatch")
    expected_result_digest = pe34_result.get("boundary_result_digest")
    if proof.boundary_result_digest != expected_result_digest:
        fail_reasons.append("pe34_handoff_proof: boundary_result_digest mismatch")
    if proof.pe34_integration_pass is not True:
        fail_reasons.append("pe34_handoff_proof: pe34_integration_pass must be true")
    if proof.operator_review_handoff_boundary_satisfied is not True:
        fail_reasons.append(
            "pe34_handoff_proof: operator_review_handoff_boundary_satisfied must be true"
        )
    return fail_reasons


def _validate_pe35_staleness_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe35_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe35_staleness_proof
    pe35_input = integration_input.pe35_boundary_input

    if proof.boundary_owner != PE35_BOUNDARY_OWNER:
        fail_reasons.append(f"pe35_staleness_proof: boundary_owner must be {PE35_BOUNDARY_OWNER!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe35_staleness_proof: source_revision mismatch")
    if proof.boundary_input_digest != compute_pe35_boundary_input_digest(pe35_input):
        fail_reasons.append("pe35_staleness_proof: boundary_input_digest mismatch")
    expected_result_digest = pe35_result.get("boundary_result_digest")
    if proof.boundary_result_digest != expected_result_digest:
        fail_reasons.append("pe35_staleness_proof: boundary_result_digest mismatch")
    if proof.handoff_current is not pe35_result.get("handoff_current", False):
        fail_reasons.append("pe35_staleness_proof: handoff_current mismatch")
    if proof.pe35_integration_pass is not True:
        fail_reasons.append("pe35_staleness_proof: pe35_integration_pass must be true")
    if proof.handoff_staleness_revocation_recovery_boundary_satisfied is not True:
        fail_reasons.append(
            "pe35_staleness_proof: handoff_staleness_revocation_recovery_boundary_satisfied "
            "must be true"
        )
    return fail_reasons


def _validate_pe19_pe20_review_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    binding = integration_input.pe19_pe20_review_proof
    pe34 = integration_input.pe34_handoff_input
    computed_review_digest = compute_review_input_digest(
        pe34.pe19_undecided_review_input.review_input
    )
    computed_package_digest = pe34.pe20_undecided_package_eligibility.review_input_digest

    if binding.review_input_owner != PE19_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe19_pe20_review_proof: review_input_owner must be {PE19_CONTRACT_VERSION!r}"
        )
    if binding.package_owner != PE20_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe19_pe20_review_proof: package_owner must be {PE20_CONTRACT_VERSION!r}"
        )
    if binding.source_revision != integration_input.source_revision:
        fail_reasons.append("pe19_pe20_review_proof: source_revision mismatch")
    if binding.review_input_digest != computed_review_digest:
        fail_reasons.append("pe19_pe20_review_proof: review_input_digest mismatch")
    if binding.package_binding_digest != computed_package_digest:
        fail_reasons.append("pe19_pe20_review_proof: package_binding_digest mismatch")
    if not binding.operator_review_proof_identity:
        fail_reasons.append("pe19_pe20_review_proof: operator_review_proof_identity required")
    elif not _valid_sha256_digest(binding.operator_review_proof_identity):
        fail_reasons.append(
            "pe19_pe20_review_proof: operator_review_proof_identity must be 64-char sha256 hex"
        )
    expected = integration_input.pe37_traceability_boundary_input.pe19_pe20_review_proof
    if binding.operator_review_proof_identity != expected.operator_review_proof_identity:
        fail_reasons.append("pe19_pe20_review_proof: operator_review_proof_identity drift")
    return fail_reasons


def _validate_pe25_closure_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe25_closure_proof
    pe32_closure = integration_input.pe32_integration_input.pe25_operator_closure_integration_proof
    pe26_closure = integration_input.pe26_assembly_input.pe25_operator_closure_proof
    pe34_closure = integration_input.pe34_handoff_input.pe25_cross_slice_closure

    if proof.closure_owner != PE25_CONTRACT_VERSION:
        fail_reasons.append(f"pe25_closure_proof: closure_owner must be {PE25_CONTRACT_VERSION!r}")
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe25_closure_proof: source_revision mismatch")
    if not proof.closure_result_digest:
        fail_reasons.append("pe25_closure_proof: closure_result_digest required")
    elif proof.closure_result_digest != pe32_closure.closure_result_digest:
        fail_reasons.append("pe25_closure_proof: closure_result_digest mismatch with PE-32")
    elif proof.closure_result_digest != pe26_closure.closure_result_digest:
        fail_reasons.append("pe25_closure_proof: closure_result_digest mismatch with PE-26")
    elif integration_input.pe39_bridge_integration_proof.pe39_admission_presentation_operator_closure_bridge_bound:
        if proof.closure_result_digest != (
            integration_input.pe40_readiness_decision_proof_chain.pe25_closure_proof_digest
        ):
            fail_reasons.append(
                "pe25_closure_proof: closure_result_digest mismatch with PE-40 chain"
            )
    elif proof.closure_result_digest != pe34_closure.closure_result_digest:
        fail_reasons.append("pe25_closure_proof: closure_result_digest mismatch with PE-34")
    if proof.operative_operator_closure_executed is not False:
        fail_reasons.append("pe25_closure_proof: operative_operator_closure_executed must be false")
    if proof.operator_closure_static_complete is not True:
        fail_reasons.append("pe25_closure_proof: operator_closure_static_complete must be true")
    return fail_reasons


def _validate_pilot_readiness_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    composition_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pilot_readiness_proof

    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pilot_readiness_proof: source_revision mismatch")
    if proof.composition_mode != composition_result.get("composition_mode"):
        fail_reasons.append("pilot_readiness_proof: composition_mode mismatch")
    if proof.composition_pass is not composition_result.get("composition_pass"):
        fail_reasons.append("pilot_readiness_proof: composition_pass mismatch")
    if proof.static_readiness_proof_coherent is not composition_result.get(
        "static_readiness_proof_coherent"
    ):
        fail_reasons.append("pilot_readiness_proof: static_readiness_proof_coherent mismatch")
    expected_pe32_digest = composition_result.get("pe32_proof_digest")
    if not proof.pe32_proof_digest:
        fail_reasons.append("pilot_readiness_proof: pe32_proof_digest required")
    elif expected_pe32_digest is None:
        fail_reasons.append("pilot_readiness_proof: pe32_proof_digest unavailable")
    elif proof.pe32_proof_digest != expected_pe32_digest:
        fail_reasons.append("pilot_readiness_proof: pe32_proof_digest mismatch")
    expected_pe26_digest = composition_result.get("pe26_assembly_digest")
    if not proof.pe26_assembly_digest:
        fail_reasons.append("pilot_readiness_proof: pe26_assembly_digest required")
    elif expected_pe26_digest is None:
        fail_reasons.append("pilot_readiness_proof: pe26_assembly_digest unavailable")
    elif proof.pe26_assembly_digest != expected_pe26_digest:
        fail_reasons.append("pilot_readiness_proof: pe26_assembly_digest mismatch")
    if proof.pe26_traceability_identity != composition_result.get("pe26_traceability_identity"):
        fail_reasons.append("pilot_readiness_proof: pe26_traceability_identity mismatch")
    if proof.pe32_blocker_state != CANONICAL_BLOCKER_STATE:
        fail_reasons.append(
            f"pilot_readiness_proof: pe32_blocker_state must be {CANONICAL_BLOCKER_STATE!r}"
        )
    return fail_reasons


def _validate_pe39_bridge_review_proof(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe39_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe39_bridge_integration_proof
    pe32_proof = integration_input.pe32_integration_input.pe39_bridge_integration_proof
    pe39_input = integration_input.pe32_integration_input.pe39_bridge_integration_input

    if proof.bridge_owner != PE39_BRIDGE_OWNER:
        fail_reasons.append(
            f"pe39_bridge_integration_proof: bridge_owner must be {PE39_BRIDGE_OWNER!r}"
        )
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe39_bridge_integration_proof: source_revision mismatch")
    if proof.bridge_proof_digest != pe32_proof.bridge_proof_digest:
        fail_reasons.append(
            "pe39_bridge_integration_proof: bridge_proof_digest mismatch with PE-32"
        )
    if proof.admission_integration_proof_digest != pe32_proof.admission_integration_proof_digest:
        fail_reasons.append(
            "pe39_bridge_integration_proof: admission_integration_proof_digest mismatch with PE-32"
        )
    expected_bridge_proof = pe39_result.get("bridge_proof_digest")
    if not proof.bridge_proof_digest:
        fail_reasons.append("pe39_bridge_integration_proof: bridge_proof_digest required")
    elif expected_bridge_proof is None:
        fail_reasons.append("pe39_bridge_integration_proof: bridge_proof_digest unavailable")
    elif proof.bridge_proof_digest != expected_bridge_proof:
        fail_reasons.append("pe39_bridge_integration_proof: bridge_proof_digest mismatch")
    admission_proof = pe39_result.get("admission_integration_proof_digest") or ""
    if not proof.admission_integration_proof_digest:
        fail_reasons.append(
            "pe39_bridge_integration_proof: admission_integration_proof_digest required"
        )
    elif proof.admission_integration_proof_digest != admission_proof:
        fail_reasons.append(
            "pe39_bridge_integration_proof: admission_integration_proof_digest mismatch"
        )
    admission_chain = pe39_input.admission_presentation_integration_input.proof_chain
    if not proof.pe34_handoff_digest:
        fail_reasons.append("pe39_bridge_integration_proof: pe34_handoff_digest required")
    elif proof.pe34_handoff_digest != admission_chain.pe34_handoff_digest:
        fail_reasons.append("pe39_bridge_integration_proof: pe34_handoff_digest mismatch")
    if not proof.pe35_boundary_result_digest:
        fail_reasons.append("pe39_bridge_integration_proof: pe35_boundary_result_digest required")
    elif proof.pe35_boundary_result_digest != admission_chain.pe35_boundary_result_digest:
        fail_reasons.append("pe39_bridge_integration_proof: pe35_boundary_result_digest mismatch")
    if not proof.pe36_presentation_projection_digest:
        fail_reasons.append(
            "pe39_bridge_integration_proof: pe36_presentation_projection_digest required"
        )
    elif (
        proof.pe36_presentation_projection_digest
        != admission_chain.pe36_presentation_projection_digest
    ):
        fail_reasons.append(
            "pe39_bridge_integration_proof: pe36_presentation_projection_digest mismatch"
        )
    if not proof.pe37_traceability_identity:
        fail_reasons.append("pe39_bridge_integration_proof: pe37_traceability_identity required")
    elif proof.pe37_traceability_identity != admission_chain.pe37_traceability_identity:
        fail_reasons.append("pe39_bridge_integration_proof: pe37_traceability_identity mismatch")
    for field_name, expected in (
        ("pe39_admission_presentation_operator_closure_bridge_bound", True),
        ("admission_presentation_lifecycle_bound", True),
        ("pe34_handoff_bound", True),
        ("pe35_staleness_revocation_recovery_bound", True),
        ("pe36_admission_presentation_bound", True),
        ("pe37_durable_traceability_bound", True),
        ("pe25_operator_closure_bound", True),
    ):
        if getattr(proof, field_name) is not expected:
            fail_reasons.append(f"pe39_bridge_integration_proof: {field_name} must be {expected}")
    if not pe39_result.get("bridge_pass"):
        fail_reasons.append("pe39_bridge_integration_input: PE-39 bridge evaluation failed")
        fail_reasons.extend(
            f"pe39_bridge_integration_input: {reason}"
            for reason in pe39_result.get("fail_reasons", [])
        )
    return fail_reasons


def _validate_pe40_readiness_decision_proof_chain(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe39_result: dict[str, Any],
    pe32_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    chain = integration_input.pe40_readiness_decision_proof_chain
    pe32_chain = integration_input.pe32_integration_input.readiness_decision_proof_chain
    pe39_input = integration_input.pe32_integration_input.pe39_bridge_integration_input
    admission = pe39_input.admission_presentation_integration_input
    pe25 = pe39_input.pe25_closure_integration_input
    pe39_bridge_proof = pe39_result.get("bridge_proof_digest") or ""
    pe32_proof = pe32_result.get("integration_proof_digest") or ""
    pe25_closure_proof = integration_input.pe32_integration_input.pe25_operator_closure_integration_proof.closure_result_digest
    expected_slots = {
        "pe39_bridge_proof_digest": pe39_bridge_proof,
        "pe39_admission_integration_proof_digest": pe39_result.get(
            "admission_integration_proof_digest"
        )
        or "",
        "pe39_pe34_handoff_digest": admission.proof_chain.pe34_handoff_digest,
        "pe39_pe36_presentation_projection_digest": (
            admission.proof_chain.pe36_presentation_projection_digest
        ),
        "pe39_pe37_traceability_identity": admission.proof_chain.pe37_traceability_identity,
        "pe25_closure_proof_digest": pe25_closure_proof,
        "pe25_closure_input_digest": compute_pe25_closure_input_digest(pe25),
        "closure_referenced_pe39_bridge_proof_digest": pe39_bridge_proof,
        "readiness_decision_referenced_pe25_closure_digest": pe25_closure_proof,
        "shared_pe35_boundary_result_digest": admission.proof_chain.pe35_boundary_result_digest,
        "shared_pe37_traceability_identity": admission.proof_chain.pe37_traceability_identity,
    }
    for slot_name in READINESS_DECISION_PROOF_CHAIN_SLOT_ORDER:
        value = getattr(chain, slot_name)
        expected = getattr(pe32_chain, slot_name)
        if not value:
            fail_reasons.append(f"pe40_readiness_decision_proof_chain: {slot_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(
                f"pe40_readiness_decision_proof_chain: {slot_name} must be 64-char lowercase sha256 hex"
            )
        elif value != expected:
            fail_reasons.append(
                f"pe40_readiness_decision_proof_chain: {slot_name} mismatch with PE-32"
            )
        elif value != expected_slots[slot_name]:
            fail_reasons.append(f"pe40_readiness_decision_proof_chain: {slot_name} mismatch")
    if chain.closure_referenced_pe39_bridge_proof_digest != chain.pe39_bridge_proof_digest:
        fail_reasons.append(
            "pe40_readiness_decision_proof_chain: closure_referenced_pe39_bridge_proof_digest "
            "must match pe39_bridge_proof_digest"
        )
    if chain.readiness_decision_referenced_pe25_closure_digest != pe25_closure_proof:
        fail_reasons.append(
            "pe40_readiness_decision_proof_chain: readiness_decision_referenced_pe25_closure_digest "
            "mismatch"
        )
    if not pe32_result.get("integration_pass"):
        fail_reasons.append("pe32_integration_input: PE-40 readiness-decision evaluation failed")
        fail_reasons.extend(
            f"pe32_integration_input: {reason}" for reason in pe32_result.get("fail_reasons", [])
        )
    if pe32_proof and chain.pe39_bridge_proof_digest != pe39_bridge_proof:
        fail_reasons.append(
            "pe40_readiness_decision_proof_chain: pe39_bridge_proof_digest mismatch with PE-39"
        )
    return fail_reasons


def _validate_proof_chain_binding(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    pe26_result: dict[str, Any],
    pe32_result: dict[str, Any],
    pe37_result: dict[str, Any],
    pe34_digest: str,
    pe35_result: dict[str, Any],
    composition_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    chain = integration_input.proof_chain
    pe34 = integration_input.pe34_handoff_input
    pe32_proof = pe32_result.get("integration_proof_digest") or ""
    pe39_bridge_proof = integration_input.pe39_bridge_integration_proof.bridge_proof_digest
    pe39_admission_proof = (
        integration_input.pe39_bridge_integration_proof.admission_integration_proof_digest
    )
    expected_slots = {
        "pe39_bridge_proof_digest": pe39_bridge_proof,
        "pe39_admission_integration_proof_digest": pe39_admission_proof,
        "pe40_pe32_integration_proof_digest": pe32_proof,
        "pe38_referenced_pe40_pe32_proof_digest": pe32_proof,
        "pe26_assembly_digest": pe26_result.get("assembly_result_digest") or "",
        "pe32_integration_proof_digest": pe32_proof,
        "pe37_boundary_result_digest": pe37_result.get("boundary_result_digest") or "",
        "pe37_traceability_identity": pe37_result.get("traceability_identity") or "",
        "pe19_review_input_digest": compute_review_input_digest(
            pe34.pe19_undecided_review_input.review_input
        ),
        "pe20_review_input_digest": pe34.pe20_undecided_package_eligibility.review_input_digest,
        "pe34_handoff_digest": pe34_digest,
        "pe35_boundary_result_digest": pe35_result.get("boundary_result_digest") or "",
        "pe25_closure_result_digest": integration_input.pe25_closure_proof.closure_result_digest,
        "pilot_composition_pe32_proof_digest": composition_result.get("pe32_proof_digest") or "",
        "pilot_composition_pe26_assembly_digest": composition_result.get("pe26_assembly_digest")
        or "",
    }
    for slot_name in PROOF_CHAIN_SLOT_ORDER:
        value = getattr(chain, slot_name)
        if not value:
            fail_reasons.append(f"proof_chain: {slot_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"proof_chain: {slot_name} must be 64-char lowercase sha256 hex")
        elif value != expected_slots[slot_name]:
            fail_reasons.append(f"proof_chain: {slot_name} mismatch")
    if chain.pe40_pe32_integration_proof_digest != chain.pe38_referenced_pe40_pe32_proof_digest:
        fail_reasons.append(
            "proof_chain: pe38_referenced_pe40_pe32_proof_digest must match "
            "pe40_pe32_integration_proof_digest"
        )
    return fail_reasons


def _validate_embedded_chain_coherence(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    pe26 = integration_input.pe26_assembly_input
    pe37 = integration_input.pe37_traceability_boundary_input
    pe35 = integration_input.pe35_boundary_input
    pe34 = integration_input.pe34_handoff_input

    if pe26.pe37_traceability_boundary_input is not pe37:
        if compute_pe37_boundary_input_digest(pe26.pe37_traceability_boundary_input) != (
            compute_pe37_boundary_input_digest(pe37)
        ):
            fail_reasons.append("composition: PE-26 pe37_traceability_boundary_input mismatch")

    if pe37.pe36_boundary_input.pe35_boundary_input is not pe35:
        if compute_pe35_boundary_input_digest(pe37.pe36_boundary_input.pe35_boundary_input) != (
            compute_pe35_boundary_input_digest(pe35)
        ):
            fail_reasons.append("composition: PE-37 pe35_boundary_input mismatch")

    if pe35.pe34_handoff is not pe34:
        if compute_pe34_boundary_input_digest(
            pe35.pe34_handoff
        ) != compute_pe34_boundary_input_digest(pe34):
            fail_reasons.append("composition: PE-35 pe34_handoff mismatch")

    for label, actual, expected in (
        ("pe26", pe26.source_revision, integration_input.source_revision),
        (
            "pe32",
            integration_input.pe32_integration_input.source_revision,
            integration_input.source_revision,
        ),
        (
            "pe37",
            pe37.pe36_boundary_input.pe35_boundary_input.pe34_handoff.source_revision,
            integration_input.source_revision,
        ),
        ("pe34", pe34.source_revision, integration_input.source_revision),
    ):
        if actual != expected:
            fail_reasons.append(f"composition: {label} source_revision mismatch")

    for label, actual, expected in (
        ("pe26", pe26.adapter_id, integration_input.adapter_id),
        ("pe32", integration_input.pe32_integration_input.adapter_id, integration_input.adapter_id),
        ("pe34", pe34.adapter_id, integration_input.adapter_id),
    ):
        if actual != expected:
            fail_reasons.append(f"composition: {label} adapter_id mismatch")

    for label, actual, expected in (
        ("pe26", pe26.instrument, integration_input.instrument),
        ("pe32", integration_input.pe32_integration_input.instrument, integration_input.instrument),
        ("pe34", pe34.instrument, integration_input.instrument),
    ):
        if actual != expected:
            fail_reasons.append(f"composition: {label} instrument mismatch")

    return fail_reasons


def validate_preflight_execution_readiness_review_lifecycle_integration_input(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-38 integration input bindings."""
    fail_reasons: list[str] = []

    if not integration_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(integration_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not integration_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif integration_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")
    if not integration_input.integration_id:
        fail_reasons.append("integration_id required")
    if not integration_input.adapter_id:
        fail_reasons.append("adapter_id required")

    fail_reasons.extend(
        _validate_instrument_scope(integration_input.instrument, integration_input.market_type)
    )

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(integration_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    fail_reasons.extend(
        validate_preflight_execution_readiness_assembly_input(integration_input.pe26_assembly_input)
    )
    fail_reasons.extend(
        validate_readiness_decision_lifecycle_integration_input(
            integration_input.pe32_integration_input
        )
    )
    fail_reasons.extend(
        validate_durable_evidence_traceability_boundary_input(
            integration_input.pe37_traceability_boundary_input
        )
    )
    fail_reasons.extend(
        validate_operator_review_handoff_boundary_input(integration_input.pe34_handoff_input)
    )
    fail_reasons.extend(
        validate_handoff_staleness_revocation_recovery_boundary_input(
            integration_input.pe35_boundary_input
        )
    )
    fail_reasons.extend(_validate_embedded_chain_coherence(integration_input))
    fail_reasons.extend(_validate_pe19_pe20_review_proof(integration_input))
    fail_reasons.extend(_validate_pe25_closure_proof(integration_input))
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    pe26_result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        integration_input.pe26_assembly_input,
        bound_traceability_identities=integration_input.bound_traceability_identities,
        bound_admission_identities=integration_input.bound_admission_identities,
    )
    pe32_result = evaluate_readiness_decision_lifecycle_integration(
        integration_input.pe32_integration_input
    )
    pe39_result = evaluate_pe39_admission_presentation_operator_closure_lifecycle_bridge(
        integration_input.pe32_integration_input.pe39_bridge_integration_input
    )
    pe37_eval_input = integration_input.pe37_traceability_boundary_input
    if (
        integration_input.bound_traceability_identities
        or integration_input.bound_admission_identities
    ):
        pe37_eval_input = replace(
            pe37_eval_input,
            bound_traceability_identities=integration_input.bound_traceability_identities,
            bound_admission_identities=integration_input.bound_admission_identities,
        )
    pe37_result = evaluate_durable_evidence_traceability_boundary(pe37_eval_input)
    pe34_result = evaluate_operator_review_handoff_boundary(integration_input.pe34_handoff_input)
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(
        integration_input.pe35_boundary_input
    )

    from scripts.ops.check_bounded_pilot_readiness import (
        LifecycleStaticProofCompositionBinding,
        LifecycleStaticProofCompositionInput,
        evaluate_lifecycle_static_proof_composition,
    )

    composition_binding = LifecycleStaticProofCompositionBinding(
        source_revision=integration_input.source_revision,
        pe32_canonical_owner=PE32_CONTRACT_VERSION,
        pe32_proof_identity=integration_input.pe32_integration_input.integration_id,
        pe32_proof_digest=integration_input.pe32_readiness_proof.integration_proof_digest,
        pe32_lifecycle_chain_identity=integration_input.pe32_readiness_proof.lifecycle_chain_identity,
        pe32_blocker_state=integration_input.pe32_readiness_proof.blocker_state,
        pe26_canonical_owner=PE26_CONTRACT_VERSION,
        pe26_assembly_identity=integration_input.pe26_assembly_input.assembly_id,
        pe26_assembly_digest=integration_input.pe26_assembly_proof.assembly_result_digest,
        pe26_source_revision=integration_input.source_revision,
        pe26_traceability_identity=integration_input.pe26_assembly_proof.traceability_identity,
    )
    composition_input = LifecycleStaticProofCompositionInput(
        pe32_integration_input=integration_input.pe32_integration_input,
        pe26_assembly_input=integration_input.pe26_assembly_input,
        binding=composition_binding,
        bound_traceability_identities=integration_input.bound_traceability_identities,
        bound_admission_identities=integration_input.bound_admission_identities,
    )
    composition_result = evaluate_lifecycle_static_proof_composition(composition_input)

    if not pe26_result.get("integration_pass"):
        fail_reasons.append("pe26_assembly_input: PE-26 evaluation failed")
        fail_reasons.extend(
            f"pe26_assembly_input: {reason}" for reason in pe26_result.get("fail_reasons", [])
        )
    if not pe32_result.get("integration_pass"):
        fail_reasons.append("pe32_integration_input: PE-32 evaluation failed")
        fail_reasons.extend(
            f"pe32_integration_input: {reason}" for reason in pe32_result.get("fail_reasons", [])
        )
    if not pe37_result.get("durable_evidence_traceability_boundary_satisfied"):
        fail_reasons.append("pe37_traceability_boundary_input: PE-37 evaluation failed")
        fail_reasons.extend(
            f"pe37_traceability_boundary_input: {reason}"
            for reason in pe37_result.get("fail_reasons", [])
        )
    if not pe34_result.get("operator_review_handoff_boundary_satisfied"):
        fail_reasons.append("pe34_handoff_input: PE-34 evaluation failed")
        fail_reasons.extend(
            f"pe34_handoff_input: {reason}" for reason in pe34_result.get("fail_reasons", [])
        )
    if not pe35_result.get("handoff_staleness_revocation_recovery_boundary_satisfied"):
        fail_reasons.append("pe35_boundary_input: PE-35 evaluation failed")
        fail_reasons.extend(
            f"pe35_boundary_input: {reason}" for reason in pe35_result.get("fail_reasons", [])
        )
    if not composition_result.get("composition_pass"):
        fail_reasons.append("pilot_readiness_composition: evaluation failed")
        fail_reasons.extend(
            f"pilot_readiness_composition: {reason}"
            for reason in composition_result.get("fail_reasons", [])
        )

    pe34_digest = compute_pe34_boundary_input_digest(integration_input.pe34_handoff_input)
    fail_reasons.extend(_validate_pe26_assembly_proof(integration_input, pe26_result=pe26_result))
    fail_reasons.extend(_validate_pe32_readiness_proof(integration_input, pe32_result=pe32_result))
    fail_reasons.extend(
        _validate_pe39_bridge_review_proof(integration_input, pe39_result=pe39_result)
    )
    fail_reasons.extend(
        _validate_pe40_readiness_decision_proof_chain(
            integration_input,
            pe39_result=pe39_result,
            pe32_result=pe32_result,
        )
    )
    fail_reasons.extend(
        _validate_pe37_traceability_proof(integration_input, pe37_result=pe37_result)
    )
    fail_reasons.extend(_validate_pe34_handoff_proof(integration_input, pe34_result=pe34_result))
    fail_reasons.extend(_validate_pe35_staleness_proof(integration_input, pe35_result=pe35_result))
    fail_reasons.extend(
        _validate_pilot_readiness_proof(integration_input, composition_result=composition_result)
    )
    fail_reasons.extend(
        _validate_proof_chain_binding(
            integration_input,
            pe26_result=pe26_result,
            pe32_result=pe32_result,
            pe37_result=pe37_result,
            pe34_digest=pe34_digest,
            pe35_result=pe35_result,
            composition_result=composition_result,
        )
    )

    return _sorted_unique(fail_reasons)


def _integration_input_dict(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
) -> dict[str, Any]:
    return {
        "integration_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
        "repository_identity": integration_input.repository_identity,
        "integration_id": integration_input.integration_id,
        "adapter_id": integration_input.adapter_id,
        "instrument": integration_input.instrument,
        "market_type": integration_input.market_type,
        "contract_versions": asdict(integration_input.contract_versions),
        "pe26_assembly_input_digest": compute_pe26_assembly_input_digest(
            integration_input.pe26_assembly_input
        ),
        "pe32_integration_input_digest": compute_pe32_integration_input_digest(
            integration_input.pe32_integration_input
        ),
        "pe37_boundary_input_digest": compute_pe37_boundary_input_digest(
            integration_input.pe37_traceability_boundary_input
        ),
        "pe34_handoff_digest": compute_pe34_boundary_input_digest(
            integration_input.pe34_handoff_input
        ),
        "pe35_boundary_input_digest": compute_pe35_boundary_input_digest(
            integration_input.pe35_boundary_input
        ),
        "pe26_assembly_proof": asdict(integration_input.pe26_assembly_proof),
        "pe32_readiness_proof": asdict(integration_input.pe32_readiness_proof),
        "pe37_traceability_proof": asdict(integration_input.pe37_traceability_proof),
        "pe19_pe20_review_proof": asdict(integration_input.pe19_pe20_review_proof),
        "pe34_handoff_proof": asdict(integration_input.pe34_handoff_proof),
        "pe35_staleness_proof": asdict(integration_input.pe35_staleness_proof),
        "pe25_closure_proof": asdict(integration_input.pe25_closure_proof),
        "pe39_bridge_integration_proof": asdict(integration_input.pe39_bridge_integration_proof),
        "pe40_readiness_decision_proof_chain": asdict(
            integration_input.pe40_readiness_decision_proof_chain
        ),
        "pilot_readiness_proof": asdict(integration_input.pilot_readiness_proof),
        "proof_chain": asdict(integration_input.proof_chain),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "bound_traceability_identities": list(integration_input.bound_traceability_identities),
        "bound_admission_identities": list(integration_input.bound_admission_identities),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _integration_result_dict(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
    preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "integration_id": integration_input.integration_id,
        "review_lifecycle_mode": REVIEW_LIFECYCLE_MODE,
        "review_lifecycle_owner": REVIEW_LIFECYCLE_OWNER,
        "pe26_assembly_digest": integration_input.proof_chain.pe26_assembly_digest,
        "pe32_integration_proof_digest": integration_input.proof_chain.pe32_integration_proof_digest,
        "pe39_bridge_proof_digest": integration_input.proof_chain.pe39_bridge_proof_digest,
        "pe40_pe32_integration_proof_digest": (
            integration_input.proof_chain.pe40_pe32_integration_proof_digest
        ),
        "pe37_traceability_identity": integration_input.proof_chain.pe37_traceability_identity,
        "pe34_handoff_digest": integration_input.proof_chain.pe34_handoff_digest,
        "pe25_closure_result_digest": integration_input.proof_chain.pe25_closure_result_digest,
        "preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe38_preflight_execution_readiness_review_lifecycle_static_integration_proven": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe38_preflight_readiness_review_lifecycle_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe39_admission_presentation_operator_closure_bridge_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe40_readiness_decision_pe39_proof_chain_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe32_readiness_decision_lifecycle_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "admission_presentation_lifecycle_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe25_operator_closure_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe34_handoff_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe35_staleness_revocation_recovery_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe36_admission_presentation_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe37_durable_traceability_bound": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "static_pe12_lifecycle_chain_complete": (
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "global_preflight_execution_readiness_review_lifecycle_readiness": (
            GLOBAL_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_READINESS
        ),
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_operator_review_executed": OPERATIVE_OPERATOR_REVIEW_EXECUTED,
        "operative_blocker_lift_executed": OPERATIVE_BLOCKER_LIFT_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": PREFLIGHT_REMAINS_BLOCKED,
        "non_authorizing": True,
    }
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_result_canonical(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return json.dumps(
        _integration_result_dict(
            integration_input,
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review=(
                preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
            ),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_integration_result_canonical(
            integration_input,
            preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review=(
                preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review
            ),
        ).encode("utf-8")
    ).hexdigest()


def evaluate_preflight_execution_readiness_review_lifecycle_integration(
    integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_pe26_assembly_digest: str | None = None,
    expected_pe32_integration_proof_digest: str | None = None,
    expected_pe39_bridge_proof_digest: str | None = None,
    expected_pe40_pe32_integration_proof_digest: str | None = None,
    expected_pe37_traceability_identity: str | None = None,
    expected_pe34_handoff_digest: str | None = None,
    expected_pe25_closure_result_digest: str | None = None,
    loose_boolean_eligibility: bool = False,
    dirty_source_state: bool = False,
    readiness_decision_authorized: bool = False,
    operator_review_authorized: bool = False,
    operator_decision_authorized: bool = False,
    operator_closure_authorized: bool = False,
    global_blocker_lift_authorized: bool = False,
    preflight_lift_authorized: bool = False,
    execution_authorized: bool = False,
    live_authorized: bool = False,
    zero_order_authorized: bool = False,
    private_readonly_authorized: bool = False,
    validate_only_authorized: bool = False,
    tiny_order_authorized: bool = False,
    reconciliation_authorized: bool = False,
    evidence_acceptance_authorized: bool = False,
    pilot_start_authorized: bool = False,
    promotion_authorized: bool = False,
    network_allowed: bool = False,
    credentials_allowed: bool = False,
    orders_allowed: bool = False,
    runtime_started: bool = False,
    adapter_called: bool = False,
    exchange_api_called_override: bool = False,
    account_state_queried_override: bool = False,
    new_evidence_generation: bool = False,
    existing_evidence_mutation: bool = False,
    claimed_blocker_lift_without_proof: bool = False,
    operator_name_implies_decision: bool = False,
    selected_decision: str | None = None,
    default_approve: bool = False,
    implicit_approve: bool = False,
    extra_fields: dict[str, Any] | None = None,
    extra_proof_chain_slots: tuple[str, ...] = (),
    unknown_lifecycle_state: str | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-38 preflight execution readiness review lifecycle integration proof."""
    fail_reasons = validate_preflight_execution_readiness_review_lifecycle_integration_input(
        integration_input
    )

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    chain = integration_input.proof_chain
    if expected_pe26_assembly_digest is not None:
        if chain.pe26_assembly_digest != expected_pe26_assembly_digest:
            fail_reasons.append("proof_chain: pe26_assembly_digest mismatch")
    if expected_pe32_integration_proof_digest is not None:
        if chain.pe32_integration_proof_digest != expected_pe32_integration_proof_digest:
            fail_reasons.append("proof_chain: pe32_integration_proof_digest mismatch")
    if expected_pe39_bridge_proof_digest is not None:
        if chain.pe39_bridge_proof_digest != expected_pe39_bridge_proof_digest:
            fail_reasons.append("proof_chain: pe39_bridge_proof_digest mismatch")
    if expected_pe40_pe32_integration_proof_digest is not None:
        if chain.pe40_pe32_integration_proof_digest != expected_pe40_pe32_integration_proof_digest:
            fail_reasons.append("proof_chain: pe40_pe32_integration_proof_digest mismatch")
        if (
            chain.pe38_referenced_pe40_pe32_proof_digest
            != expected_pe40_pe32_integration_proof_digest
        ):
            fail_reasons.append("proof_chain: pe38_referenced_pe40_pe32_proof_digest mismatch")
    if expected_pe37_traceability_identity is not None:
        if chain.pe37_traceability_identity != expected_pe37_traceability_identity:
            fail_reasons.append("proof_chain: pe37_traceability_identity mismatch")
    if expected_pe34_handoff_digest is not None:
        if chain.pe34_handoff_digest != expected_pe34_handoff_digest:
            fail_reasons.append("proof_chain: pe34_handoff_digest mismatch")
    if expected_pe25_closure_result_digest is not None:
        if chain.pe25_closure_result_digest != expected_pe25_closure_result_digest:
            fail_reasons.append("proof_chain: pe25_closure_result_digest mismatch")

    if loose_boolean_eligibility:
        fail_reasons.append(
            "loose_boolean_eligibility=true without canonical proof is insufficient"
        )
    if dirty_source_state:
        fail_reasons.append("dirty_source_state=true is not allowed")
    if readiness_decision_authorized:
        fail_reasons.append(
            "readiness_decision_authorized=true without authority lift is forbidden"
        )
    if operator_review_authorized:
        fail_reasons.append("operator_review_authorized=true without authority lift is forbidden")
    if operator_decision_authorized:
        fail_reasons.append("operator_decision_authorized=true without authority lift is forbidden")
    if operator_closure_authorized:
        fail_reasons.append("operator_closure_authorized=true without authority lift is forbidden")
    if global_blocker_lift_authorized:
        fail_reasons.append("global_blocker_lift_authorized=true is not allowed")
    if preflight_lift_authorized:
        fail_reasons.append("preflight_lift_authorized=true is not allowed")
    if execution_authorized:
        fail_reasons.append("execution_authorized=true without authority lift is forbidden")
    if live_authorized:
        fail_reasons.append("live_authorized=true without authority lift is forbidden")
    if zero_order_authorized:
        fail_reasons.append("zero_order_authorized=true without authority lift is forbidden")
    if private_readonly_authorized:
        fail_reasons.append("private_readonly_authorized=true without authority lift is forbidden")
    if validate_only_authorized:
        fail_reasons.append("validate_only_authorized=true without authority lift is forbidden")
    if tiny_order_authorized:
        fail_reasons.append("tiny_order_authorized=true without authority lift is forbidden")
    if reconciliation_authorized:
        fail_reasons.append("reconciliation_authorized=true without authority lift is forbidden")
    if evidence_acceptance_authorized:
        fail_reasons.append(
            "evidence_acceptance_authorized=true without authority lift is forbidden"
        )
    if pilot_start_authorized:
        fail_reasons.append("pilot_start_authorized=true without authority lift is forbidden")
    if promotion_authorized:
        fail_reasons.append("promotion_authorized=true without authority lift is forbidden")
    if network_allowed:
        fail_reasons.append("network_allowed=true without authority lift is forbidden")
    if credentials_allowed:
        fail_reasons.append("credentials_allowed=true without authority lift is forbidden")
    if orders_allowed:
        fail_reasons.append("orders_allowed=true without authority lift is forbidden")
    if runtime_started:
        fail_reasons.append("runtime_started=true without runtime execution is forbidden")
    if adapter_called:
        fail_reasons.append("adapter_called=true without adapter execution is forbidden")
    if exchange_api_called_override:
        fail_reasons.append("exchange_api_called=true without exchange proof is forbidden")
    if account_state_queried_override:
        fail_reasons.append("account_state_queried=true without query proof is forbidden")
    if new_evidence_generation:
        fail_reasons.append("new_evidence_generation=true is not allowed")
    if existing_evidence_mutation:
        fail_reasons.append("existing_evidence_mutation=true is not allowed")
    if claimed_blocker_lift_without_proof:
        fail_reasons.append("claimed_blocker_lift_without_proof=true is not allowed")
    if operator_name_implies_decision:
        fail_reasons.append("operator_name_implies_decision=true is not allowed")
    if selected_decision is not None:
        fail_reasons.append(
            f"selected_decision {selected_decision!r} is not allowed at review lifecycle integration"
        )
    if default_approve:
        fail_reasons.append("default_approve is not allowed at review lifecycle integration")
    if implicit_approve:
        fail_reasons.append("implicit_approve is not allowed at review lifecycle integration")
    if extra_fields:
        fail_reasons.extend(_reject_forbidden_extra_fields(extra_fields))
    if extra_proof_chain_slots:
        fail_reasons.append(f"unknown extra proof chain slots: {sorted(extra_proof_chain_slots)!r}")
    if unknown_lifecycle_state is not None:
        fail_reasons.append(f"unknown lifecycle state: {unknown_lifecycle_state!r}")

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    eligibility = integration_pass

    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review=(
                    eligibility
                ),
            )
            if integration_pass
            else None
        ),
        "review_lifecycle_mode": REVIEW_LIFECYCLE_MODE,
        "review_lifecycle_owner": REVIEW_LIFECYCLE_OWNER,
        "pe26_assembly_digest": chain.pe26_assembly_digest,
        "pe32_integration_proof_digest": chain.pe32_integration_proof_digest,
        "pe39_bridge_proof_digest": chain.pe39_bridge_proof_digest,
        "pe40_pe32_integration_proof_digest": chain.pe40_pe32_integration_proof_digest,
        "pe37_traceability_identity": chain.pe37_traceability_identity,
        "pe34_handoff_digest": chain.pe34_handoff_digest,
        "pe25_closure_result_digest": chain.pe25_closure_result_digest,
        "preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review": (
            eligibility
        ),
        "pe38_preflight_execution_readiness_review_lifecycle_static_integration_proven": eligibility,
        "pe38_preflight_readiness_review_lifecycle_bound": eligibility,
        "pe39_admission_presentation_operator_closure_bridge_bound": eligibility,
        "pe40_readiness_decision_pe39_proof_chain_bound": eligibility,
        "pe32_readiness_decision_lifecycle_bound": eligibility,
        "admission_presentation_lifecycle_bound": eligibility,
        "pe25_operator_closure_bound": eligibility,
        "pe34_handoff_bound": eligibility,
        "pe35_staleness_revocation_recovery_bound": eligibility,
        "pe36_admission_presentation_bound": eligibility,
        "pe37_durable_traceability_bound": eligibility,
        "static_pe12_lifecycle_chain_complete": eligibility,
        "global_preflight_execution_readiness_review_lifecycle_readiness": (
            GLOBAL_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_READINESS
        ),
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_operator_review_executed": OPERATIVE_OPERATOR_REVIEW_EXECUTED,
        "operative_blocker_lift_executed": OPERATIVE_BLOCKER_LIFT_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": PREFLIGHT_REMAINS_BLOCKED,
        "global_blocker_lift_authorized": False,
        "preflight_lift_authorized": False,
        "ready_for_operator_arming": False,
        "readiness_decision_authorized": False,
        "operator_review_authorized": False,
        "operator_decision_authorized": False,
        "operator_closure_authorized": False,
        "execution_authorized": False,
        "live_authorized": False,
        "zero_order_authorized": False,
        "private_readonly_authorized": False,
        "validate_only_authorized": False,
        "tiny_order_authorized": False,
        "reconciliation_authorized": False,
        "evidence_acceptance_authorized": False,
        "pilot_start_authorized": False,
        "promotion_authorized": False,
        "network_allowed": False,
        "credentials_allowed": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "network_used": False,
        "credentials_used": False,
        "secret_material_read": False,
        "secret_material_stored": False,
        "exchange_request_count": 0,
        "orders_created": 0,
        "orders_cancelled": 0,
        "orders_amended": 0,
        "positions_changed": 0,
        "adapter_called": False,
        "testnet_started": False,
        "harness_started": False,
        "subprocess_started": False,
        "account_state_queried": False,
        "fail_reasons": fail_reasons,
    }


def default_minimal_safety_snapshot() -> IntegrationSafetySnapshot:
    return IntegrationSafetySnapshot(
        preflight_remains_blocked=True,
        global_blocker_lift_authorized=False,
        preflight_lift_authorized=False,
        ready_for_operator_arming=False,
        readiness_decision_authorized=False,
        operator_review_authorized=False,
        operator_decision_authorized=False,
        operator_closure_authorized=False,
        execution_authorized=False,
        live_authorized=False,
        zero_order_authorized=False,
        private_readonly_authorized=False,
        validate_only_authorized=False,
        tiny_order_authorized=False,
        reconciliation_authorized=False,
        evidence_acceptance_authorized=False,
        pilot_start_authorized=False,
        promotion_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    integration_id: str = "preflight-execution-readiness-review-lifecycle-integration-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> PreflightExecutionReadinessReviewLifecycleIntegrationInput:
    """Minimal valid futures-generic PE-38 integration input for offline tests."""
    from scripts.ops.check_bounded_pilot_readiness import (
        STATIC_PROOF_COMPOSITION_MODE,
        LifecycleStaticProofCompositionBinding,
        LifecycleStaticProofCompositionInput,
        evaluate_lifecycle_static_proof_composition,
    )
    from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
        compute_closure_result_digest,
    )
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        default_minimal_pe19_pe20_review_proof_binding,
    )
    from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
        Pe25OperatorClosureProofBinding as Pe26Pe25ProofBinding,
        compute_lifecycle_matrix_digest,
        default_minimal_assembly_input,
        default_minimal_pe37_traceability_proof,
    )
    from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
        default_minimal_integration_input as default_minimal_pe32_integration_input,
    )

    state_digest = lifecycle_state_digest or "a" * 64
    matrix_digest = compute_lifecycle_matrix_digest()

    pe32_input = default_minimal_pe32_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )
    pe32_result = evaluate_readiness_decision_lifecycle_integration(pe32_input)
    pe39_bridge_input = pe32_input.pe39_bridge_integration_input
    pe39_result = evaluate_pe39_admission_presentation_operator_closure_lifecycle_bridge(
        pe39_bridge_input
    )
    admission_input = pe39_bridge_input.admission_presentation_integration_input
    pe25_input = pe32_input.pe25_operator_closure_integration_input
    pe25_closure_result_digest = (
        pe32_input.pe25_operator_closure_integration_proof.closure_result_digest
    )
    pe32_proof_digest = pe32_result["integration_proof_digest"]
    pe39_bridge_proof = pe39_result["bridge_proof_digest"]
    pe39_admission_proof = pe39_result["admission_integration_proof_digest"]

    pe37_boundary_input = admission_input.pe37_traceability_boundary_input
    pe34_handoff = admission_input.pe34_handoff_input
    pe35_boundary = admission_input.pe35_boundary_input

    pe26_input = default_minimal_assembly_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        lifecycle_state_digest=state_digest,
    )
    pe26_pe25 = Pe26Pe25ProofBinding(
        closure_input_digest=pe32_input.pe25_operator_closure_integration_proof.closure_input_digest,
        closure_result_digest=pe25_closure_result_digest,
        pe25_integration_pass=True,
        operator_closure_static_complete=True,
        lifecycle_matrix_digest=matrix_digest,
    )
    pe26_input = replace(
        pe26_input,
        pe25_operator_closure_proof=pe26_pe25,
        pe37_traceability_boundary_input=pe37_boundary_input,
        pe37_traceability_proof=default_minimal_pe37_traceability_proof(pe37_boundary_input),
    )

    pe26_result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(pe26_input)
    pe37_result = evaluate_durable_evidence_traceability_boundary(pe37_boundary_input)
    pe34_result = evaluate_operator_review_handoff_boundary(pe34_handoff)
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_boundary)

    composition_binding = LifecycleStaticProofCompositionBinding(
        source_revision=source_revision,
        pe32_canonical_owner=PE32_CONTRACT_VERSION,
        pe32_proof_identity=pe32_input.integration_id,
        pe32_proof_digest=pe32_proof_digest,
        pe32_lifecycle_chain_identity=state_digest,
        pe32_blocker_state=CANONICAL_BLOCKER_STATE,
        pe26_canonical_owner=PE26_CONTRACT_VERSION,
        pe26_assembly_identity=pe26_input.assembly_id,
        pe26_assembly_digest=pe26_result["assembly_result_digest"],
        pe26_source_revision=source_revision,
        pe26_traceability_identity=pe26_input.pe37_traceability_proof.traceability_identity,
    )
    composition_input = LifecycleStaticProofCompositionInput(
        pe32_integration_input=pe32_input,
        pe26_assembly_input=pe26_input,
        binding=composition_binding,
    )
    composition_result = evaluate_lifecycle_static_proof_composition(composition_input)

    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe19_pe20 = default_minimal_pe19_pe20_review_proof_binding(
        pe37_boundary_input.pe36_boundary_input
    )
    pe39_bridge_integration_proof = default_minimal_pe39_bridge_integration_proof(
        pe39_bridge_input,
        pe39_result=pe39_result,
    )
    pe40_readiness_decision_proof_chain = default_minimal_readiness_decision_proof_chain(
        pe39_bridge_input,
        pe39_result=pe39_result,
        pe25_result={
            "closure_result_digest": pe25_closure_result_digest,
            "closure_input_digest": pe32_input.pe25_operator_closure_integration_proof.closure_input_digest,
        },
    )

    proof_chain = ReviewLifecycleProofChainBinding(
        pe39_bridge_proof_digest=pe39_bridge_proof,
        pe39_admission_integration_proof_digest=pe39_admission_proof,
        pe40_pe32_integration_proof_digest=pe32_proof_digest,
        pe38_referenced_pe40_pe32_proof_digest=pe32_proof_digest,
        pe26_assembly_digest=pe26_result["assembly_result_digest"],
        pe32_integration_proof_digest=pe32_proof_digest,
        pe37_boundary_result_digest=pe37_result["boundary_result_digest"],
        pe37_traceability_identity=pe37_result["traceability_identity"],
        pe19_review_input_digest=compute_review_input_digest(
            pe34_handoff.pe19_undecided_review_input.review_input
        ),
        pe20_review_input_digest=pe34_handoff.pe20_undecided_package_eligibility.review_input_digest,
        pe34_handoff_digest=pe34_digest,
        pe35_boundary_result_digest=pe35_result["boundary_result_digest"],
        pe25_closure_result_digest=pe25_closure_result_digest,
        pilot_composition_pe32_proof_digest=composition_result["pe32_proof_digest"],
        pilot_composition_pe26_assembly_digest=composition_result["pe26_assembly_digest"],
    )

    return PreflightExecutionReadinessReviewLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        integration_id=integration_id,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe19_operator_review=PE19_CONTRACT_VERSION,
            pe20_review_proof_package=PE20_CONTRACT_VERSION,
            pe25_operator_closure=PE25_CONTRACT_VERSION,
            pe26_assembly=PE26_CONTRACT_VERSION,
            pe32_readiness_decision=PE32_CONTRACT_VERSION,
            pe34_handoff=PE34_CONTRACT_VERSION,
            pe35_staleness=PE35_CONTRACT_VERSION,
            pe36_admission_presentation=PE36_CONTRACT_VERSION,
            pe37_traceability=PE37_CONTRACT_VERSION,
            admission_presentation_lifecycle=ADMISSION_LIFECYCLE_CONTRACT_VERSION,
            pe39_bridge=PE39_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        pe26_assembly_input=pe26_input,
        pe32_integration_input=pe32_input,
        pe37_traceability_boundary_input=pe37_boundary_input,
        pe34_handoff_input=pe34_handoff,
        pe35_boundary_input=pe35_boundary,
        pe26_assembly_proof=Pe26AssemblyProofBinding(
            assembly_owner=PE26_CONTRACT_VERSION,
            source_revision=source_revision,
            assembly_input_digest=compute_pe26_assembly_input_digest(pe26_input),
            assembly_result_digest=pe26_result["assembly_result_digest"],
            traceability_identity=pe26_input.pe37_traceability_proof.traceability_identity,
            pe26_integration_pass=True,
            preflight_execution_readiness_assembly_complete=True,
        ),
        pe32_readiness_proof=Pe32ReadinessLifecycleProofBinding(
            integration_owner=PE32_CONTRACT_VERSION,
            source_revision=source_revision,
            integration_input_digest=compute_pe32_integration_input_digest(pe32_input),
            integration_proof_digest=pe32_proof_digest,
            lifecycle_chain_identity=state_digest,
            blocker_state=CANONICAL_BLOCKER_STATE,
            pe32_integration_pass=True,
            readiness_decision_lifecycle_eligibility=True,
        ),
        pe37_traceability_proof=Pe37TraceabilityProofBinding(
            traceability_owner=PE37_BOUNDARY_OWNER,
            source_revision=source_revision,
            boundary_input_digest=compute_pe37_boundary_input_digest(pe37_boundary_input),
            boundary_result_digest=pe37_result["boundary_result_digest"],
            traceability_identity=pe37_result["traceability_identity"],
            admission_identity=pe37_result["admission_identity"],
            pe37_integration_pass=True,
            durable_evidence_traceability_boundary_satisfied=True,
        ),
        pe19_pe20_review_proof=pe19_pe20,
        pe34_handoff_proof=Pe34HandoffProofBinding(
            handoff_owner=PE34_HANDOFF_OWNER,
            source_revision=source_revision,
            boundary_input_digest=pe34_digest,
            boundary_result_digest=pe34_result["boundary_result_digest"],
            pe34_integration_pass=True,
            operator_review_handoff_boundary_satisfied=True,
        ),
        pe35_staleness_proof=Pe35StalenessProofBinding(
            boundary_owner=PE35_BOUNDARY_OWNER,
            source_revision=source_revision,
            boundary_input_digest=compute_pe35_boundary_input_digest(pe35_boundary),
            boundary_result_digest=pe35_result["boundary_result_digest"],
            handoff_current=pe35_result["handoff_current"],
            pe35_integration_pass=True,
            handoff_staleness_revocation_recovery_boundary_satisfied=True,
        ),
        pe25_closure_proof=Pe25ClosureProofBinding(
            closure_owner=PE25_CONTRACT_VERSION,
            source_revision=source_revision,
            closure_result_digest=pe25_closure_result_digest,
            operative_operator_closure_executed=False,
            operator_closure_static_complete=True,
        ),
        pe39_bridge_integration_proof=pe39_bridge_integration_proof,
        pe40_readiness_decision_proof_chain=pe40_readiness_decision_proof_chain,
        pilot_readiness_proof=PilotReadinessCompositionProofBinding(
            composition_mode=STATIC_PROOF_COMPOSITION_MODE,
            source_revision=source_revision,
            composition_pass=True,
            static_readiness_proof_coherent=True,
            pe32_proof_digest=composition_result["pe32_proof_digest"],
            pe26_assembly_digest=composition_result["pe26_assembly_digest"],
            pe26_traceability_identity=composition_result["pe26_traceability_identity"],
            pe32_blocker_state=CANONICAL_BLOCKER_STATE,
        ),
        proof_chain=proof_chain,
        safety_snapshot=default_minimal_safety_snapshot(),
    )
