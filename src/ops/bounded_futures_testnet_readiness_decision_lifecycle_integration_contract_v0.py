"""Bounded Futures Testnet readiness-decision lifecycle integration (v0, PE-32).

Deterministic, offline, explicit-input-only contract binding a canonically verified
PE-26 preflight execution readiness assembly, PE-27 zero-order lifecycle integration,
PE-28 private-readonly lifecycle integration, PE-29 validate-only lifecycle integration,
PE-30 tiny-order lifecycle integration, PE-31 reconciliation-review lifecycle integration,
PE-25 operator-closure lifecycle integration, PE-12 readiness_decision phase identity,
and an explicit injected blocker-register snapshot to a single non-authorizing
readiness-decision lifecycle eligibility assessment.

Static integration only — no network, testnet, runtime, credentials, orders, adapter calls,
exchange queries, operative readiness decisions, blocker lifts, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_READINESS_DECISION,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
    PHASE_PRIVATE_READONLY,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
    OperatorClosureLifecycleIntegrationInput,
    compute_closure_input_digest as compute_pe25_closure_input_digest,
    compute_closure_result_digest as compute_pe25_closure_result_digest,
    default_minimal_integration_input as default_minimal_pe25_integration_input,
    evaluate_operator_closure_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE28_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE31_CONTRACT_VERSION,
    ReconciliationReviewLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe31_integration_input_digest,
    compute_integration_proof_digest as compute_pe31_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe31_integration_input,
    evaluate_reconciliation_review_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE30_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE29_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE27_CONTRACT_VERSION,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_READINESS_DECISION_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_readiness_decision_lifecycle_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_readiness_decision_lifecycle_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

READINESS_DECISION_MODE = "static_readiness_decision_eligibility_proof_only"
READINESS_DECISION_OWNER = PHASE_CANONICAL_OWNERS[PHASE_READINESS_DECISION]
BLOCKER_REGISTER_OWNER = PHASE_CANONICAL_OWNERS[PHASE_READINESS_DECISION]
BLOCKER_REGISTER_DOC_PATH = "docs/ops/specs/MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"

PE26_ASSEMBLY_OWNER = PE26_CONTRACT_VERSION
PE27_INTEGRATION_OWNER = PE27_CONTRACT_VERSION
PE28_INTEGRATION_OWNER = PE28_CONTRACT_VERSION
PE29_INTEGRATION_OWNER = PE29_CONTRACT_VERSION
PE30_INTEGRATION_OWNER = PE30_CONTRACT_VERSION
PE31_INTEGRATION_OWNER = PE31_CONTRACT_VERSION
PE25_INTEGRATION_OWNER = PE25_CONTRACT_VERSION

GLOBAL_READINESS_DECISION_LIFECYCLE_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_READINESS_DECISION_CREATED = False
OPERATIVE_OPERATOR_DECISION_CREATED = False
OPERATIVE_OPERATOR_CLOSURE_EXECUTED = False
OPERATIVE_BLOCKER_LIFT_EXECUTED = False
LIFECYCLE_TRANSITION_EXECUTED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
RUNTIME_STARTED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe26_assembly": PE26_CONTRACT_VERSION,
    "pe27_zero_order": PE27_CONTRACT_VERSION,
    "pe28_private_readonly": PE28_CONTRACT_VERSION,
    "pe29_validate_only": PE29_CONTRACT_VERSION,
    "pe30_tiny_order": PE30_CONTRACT_VERSION,
    "pe31_reconciliation_review": PE31_CONTRACT_VERSION,
    "pe25_operator_closure": PE25_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}

REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS: tuple[str, ...] = (
    "GLB-006",
    "GLB-008",
    "GLB-009",
    "GLB-010",
    "GLB-011",
    "GLB-012",
    "GLB-013",
    "GLB-014",
    "GLB-015",
    "GLB-016",
    "GLB-017",
    "GLB-020",
)

_EXPECTED_DEFAULT_BLOCKER_STATES: dict[str, str] = {
    "GLB-006": "BLOCKED",
    "GLB-008": "BLOCKED",
    "GLB-009": "BLOCKED",
    "GLB-010": "BLOCKED",
    "GLB-011": "BLOCKED",
    "GLB-012": "BLOCKED",
    "GLB-013": "BLOCKED",
    "GLB-014": "BLOCKED",
    "GLB-015": "BLOCKED",
    "GLB-016": "BLOCKED",
    "GLB-017": "BLOCKED",
    "GLB-020": "BLOCKED",
}

_ALLOWED_BLOCKER_STATES_FOR_ELIGIBILITY = frozenset({"OPEN", "BLOCKED", "DEFERRED"})
_LIFTED_BLOCKER_STATES = frozenset({"CLOSED", "ACCEPTED_BY_AUTHORITY"})


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe26_assembly: str
    pe27_zero_order: str
    pe28_private_readonly: str
    pe29_validate_only: str
    pe30_tiny_order: str
    pe31_reconciliation_review: str
    pe25_operator_closure: str
    integration: str


@dataclass(frozen=True)
class LifecycleMatrixProof:
    pe12_contract_version: str
    lifecycle_matrix_digest: str
    assigned_lifecycle_phase: str
    lifecycle_state_digest: str


@dataclass(frozen=True)
class LifecycleStateBinding:
    state_id: str
    state_digest: str
    assigned_lifecycle_phase: str
    adapter_id: str


@dataclass(frozen=True)
class Pe31ReconciliationReviewIntegrationProofBinding:
    integration_owner: str
    integration_input_digest: str
    integration_proof_digest: str
    pe31_integration_pass: bool
    reconciliation_review_lifecycle_eligibility: bool


@dataclass(frozen=True)
class Pe25OperatorClosureIntegrationProofBinding:
    integration_owner: str
    closure_input_digest: str
    closure_result_digest: str
    pe25_integration_pass: bool
    operator_closure_static_complete: bool


@dataclass(frozen=True)
class BlockerSnapshotEntry:
    blocker_id: str
    blocker_state: str
    state_verified: bool
    lift_authorized: bool
    lift_proof_digest: str


@dataclass(frozen=True)
class BlockerRegisterSnapshotBinding:
    blocker_register_owner: str
    blocker_register_doc_path: str
    blocker_register_source_revision: str
    blocker_register_digest: str
    snapshot_complete: bool
    global_blocker_lift_authorized: bool
    preflight_lift_authorized: bool
    blocker_lift_proof_digest: str
    entries: tuple[BlockerSnapshotEntry, ...]


@dataclass(frozen=True)
class ReadinessDecisionProofBinding:
    readiness_decision_owner: str
    blocker_register_owner: str
    readiness_decision_mode: str
    review_only: bool
    static_eligibility_proven: bool
    manifest_verify_rc: int
    readiness_decision_proof_digest: str
    request_count: int
    exchange_request_count: int
    orders_created: int
    orders_cancelled: int
    orders_amended: int
    positions_changed: int
    network_used: bool
    credentials_used: bool
    secret_material_read: bool
    secret_material_stored: bool
    exchange_api_called: bool
    account_state_queried: bool
    adapter_called: bool
    runtime_started: bool
    testnet_started: bool
    harness_started: bool
    subprocess_started: bool
    evidence_created: bool
    evidence_mutated: bool


@dataclass(frozen=True)
class OperatorLegibilityMetadata:
    owner_operator_name: str
    legibility_only: bool


@dataclass(frozen=True)
class IntegrationSafetySnapshot:
    preflight_remains_blocked: bool
    global_blocker_lift_authorized: bool
    preflight_lift_authorized: bool
    ready_for_operator_arming: bool
    readiness_decision_authorized: bool
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
class ReadinessDecisionLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    integration_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    lifecycle_matrix_proof: LifecycleMatrixProof
    lifecycle_state_before: LifecycleStateBinding
    declared_lifecycle_state_after: LifecycleStateBinding
    pe31_reconciliation_review_integration_input: ReconciliationReviewLifecycleIntegrationInput
    pe31_reconciliation_review_integration_proof: Pe31ReconciliationReviewIntegrationProofBinding
    pe25_operator_closure_integration_input: OperatorClosureLifecycleIntegrationInput
    pe25_operator_closure_integration_proof: Pe25OperatorClosureIntegrationProofBinding
    blocker_register_snapshot: BlockerRegisterSnapshotBinding
    readiness_decision_proof: ReadinessDecisionProofBinding
    operator_legibility: OperatorLegibilityMetadata
    safety_snapshot: IntegrationSafetySnapshot
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


def _blocker_snapshot_dict(
    binding: BlockerRegisterSnapshotBinding,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "blocker_lift_proof_digest": binding.blocker_lift_proof_digest,
        "blocker_register_doc_path": binding.blocker_register_doc_path,
        "blocker_register_owner": binding.blocker_register_owner,
        "blocker_register_source_revision": binding.blocker_register_source_revision,
        "entries": [
            {
                "blocker_id": entry.blocker_id,
                "blocker_state": entry.blocker_state,
                "lift_authorized": entry.lift_authorized,
                "lift_proof_digest": entry.lift_proof_digest,
                "state_verified": entry.state_verified,
            }
            for entry in sorted(binding.entries, key=lambda item: item.blocker_id)
        ],
        "global_blocker_lift_authorized": binding.global_blocker_lift_authorized,
        "preflight_lift_authorized": binding.preflight_lift_authorized,
        "required_blocker_ids": list(REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS),
        "snapshot_complete": binding.snapshot_complete,
    }
    if include_digest:
        payload["blocker_register_digest"] = binding.blocker_register_digest
    return payload


def serialize_blocker_register_snapshot_canonical(binding: BlockerRegisterSnapshotBinding) -> str:
    return json.dumps(
        _blocker_snapshot_dict(binding, include_digest=True),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_blocker_register_snapshot_digest(binding: BlockerRegisterSnapshotBinding) -> str:
    return hashlib.sha256(
        json.dumps(
            _blocker_snapshot_dict(binding, include_digest=False),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _integration_input_dict(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> dict[str, Any]:
    return {
        "integration_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
        "repository_identity": integration_input.repository_identity,
        "adapter_id": integration_input.adapter_id,
        "integration_id": integration_input.integration_id,
        "instrument": integration_input.instrument,
        "market_type": integration_input.market_type,
        "contract_versions": asdict(integration_input.contract_versions),
        "lifecycle_matrix_proof": asdict(integration_input.lifecycle_matrix_proof),
        "lifecycle_state_before": asdict(integration_input.lifecycle_state_before),
        "declared_lifecycle_state_after": asdict(integration_input.declared_lifecycle_state_after),
        "pe31_reconciliation_review_integration_input_digest": (
            compute_pe31_integration_input_digest(
                integration_input.pe31_reconciliation_review_integration_input
            )
        ),
        "pe31_reconciliation_review_integration_proof": asdict(
            integration_input.pe31_reconciliation_review_integration_proof
        ),
        "pe25_operator_closure_integration_input_digest": compute_pe25_closure_input_digest(
            integration_input.pe25_operator_closure_integration_input
        ),
        "pe25_operator_closure_integration_proof": asdict(
            integration_input.pe25_operator_closure_integration_proof
        ),
        "blocker_register_snapshot_digest": compute_blocker_register_snapshot_digest(
            integration_input.blocker_register_snapshot
        ),
        "readiness_decision_proof": asdict(integration_input.readiness_decision_proof),
        "operator_legibility": asdict(integration_input.operator_legibility),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _readiness_decision_proof_dict(binding: ReadinessDecisionProofBinding) -> dict[str, Any]:
    return {
        "account_state_queried": binding.account_state_queried,
        "adapter_called": binding.adapter_called,
        "blocker_register_owner": binding.blocker_register_owner,
        "credentials_used": binding.credentials_used,
        "evidence_created": binding.evidence_created,
        "evidence_mutated": binding.evidence_mutated,
        "exchange_api_called": binding.exchange_api_called,
        "exchange_request_count": binding.exchange_request_count,
        "harness_started": binding.harness_started,
        "manifest_verify_rc": binding.manifest_verify_rc,
        "network_used": binding.network_used,
        "orders_amended": binding.orders_amended,
        "orders_cancelled": binding.orders_cancelled,
        "orders_created": binding.orders_created,
        "positions_changed": binding.positions_changed,
        "readiness_decision_mode": binding.readiness_decision_mode,
        "readiness_decision_owner": binding.readiness_decision_owner,
        "request_count": binding.request_count,
        "review_only": binding.review_only,
        "runtime_started": binding.runtime_started,
        "secret_material_read": binding.secret_material_read,
        "secret_material_stored": binding.secret_material_stored,
        "static_eligibility_proven": binding.static_eligibility_proven,
        "subprocess_started": binding.subprocess_started,
        "testnet_started": binding.testnet_started,
    }


def serialize_readiness_decision_proof_canonical(binding: ReadinessDecisionProofBinding) -> str:
    return json.dumps(
        _readiness_decision_proof_dict(binding), sort_keys=True, separators=(",", ":")
    )


def compute_readiness_decision_proof_digest(binding: ReadinessDecisionProofBinding) -> str:
    return hashlib.sha256(
        serialize_readiness_decision_proof_canonical(binding).encode("utf-8")
    ).hexdigest()


def _integration_result_dict(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
    readiness_decision_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> dict[str, Any]:
    matrix = integration_input.lifecycle_matrix_proof
    pe31_proof = integration_input.pe31_reconciliation_review_integration_proof
    pe25_proof = integration_input.pe25_operator_closure_integration_proof
    payload: dict[str, Any] = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "integration_id": integration_input.integration_id,
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe31_integration_proof_digest": pe31_proof.integration_proof_digest,
        "pe25_closure_result_digest": pe25_proof.closure_result_digest,
        "blocker_register_digest": integration_input.blocker_register_snapshot.blocker_register_digest,
        "readiness_decision_proof_digest": (
            integration_input.readiness_decision_proof.readiness_decision_proof_digest
        ),
        "readiness_decision_lifecycle_eligibility_for_separate_operator_review": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe32_readiness_decision_lifecycle_static_integration_proven": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe12_readiness_decision_static_integration_proven": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "static_pe12_lifecycle_chain_complete": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "global_readiness_decision_lifecycle_readiness": GLOBAL_READINESS_DECISION_LIFECYCLE_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_blocker_lift_executed": OPERATIVE_BLOCKER_LIFT_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "non_authorizing": True,
    }
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_result_canonical(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
    *,
    readiness_decision_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return json.dumps(
        _integration_result_dict(
            integration_input,
            readiness_decision_lifecycle_eligibility_for_separate_operator_review=(
                readiness_decision_lifecycle_eligibility_for_separate_operator_review
            ),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
    *,
    readiness_decision_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_integration_result_canonical(
            integration_input,
            readiness_decision_lifecycle_eligibility_for_separate_operator_review=(
                readiness_decision_lifecycle_eligibility_for_separate_operator_review
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


def _validate_safety_snapshot(snapshot: IntegrationSafetySnapshot) -> list[str]:
    fail_reasons: list[str] = []
    required_bools = (
        ("preflight_remains_blocked", True),
        ("global_blocker_lift_authorized", False),
        ("preflight_lift_authorized", False),
        ("ready_for_operator_arming", False),
        ("readiness_decision_authorized", False),
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


def _validate_operator_legibility(legibility: OperatorLegibilityMetadata) -> list[str]:
    fail_reasons: list[str] = []
    if not legibility.owner_operator_name:
        fail_reasons.append("operator_legibility: owner_operator_name required")
    if legibility.legibility_only is not True:
        fail_reasons.append("operator_legibility: legibility_only must be true")
    return fail_reasons


def _validate_pe31_integration_proof(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe31_reconciliation_review_integration_proof
    pe31_input = integration_input.pe31_reconciliation_review_integration_input

    if proof.integration_owner != PE31_INTEGRATION_OWNER:
        fail_reasons.append(
            f"pe31_reconciliation_review_integration_proof: integration_owner must be "
            f"{PE31_INTEGRATION_OWNER!r}"
        )
    if not proof.integration_input_digest:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_proof: integration_input_digest required"
        )
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_proof: integration_input_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe31_integration_input_digest(pe31_input):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_proof: integration_input_digest mismatch"
        )

    if not proof.integration_proof_digest:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_proof: integration_proof_digest required"
        )
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe31_reconciliation_review_integration_proof: integration_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe31_integration_proof_digest(
            pe31_input,
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review=True,
        )
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append(
                "pe31_reconciliation_review_integration_proof: integration_proof_digest mismatch"
            )

    if proof.pe31_integration_pass is not True:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_proof: pe31_integration_pass must be true"
        )
    if proof.reconciliation_review_lifecycle_eligibility is not True:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_proof: "
            "reconciliation_review_lifecycle_eligibility must be true"
        )

    pe31_result = evaluate_reconciliation_review_lifecycle_integration(pe31_input)
    if not pe31_result["integration_pass"]:
        fail_reasons.append("pe31_reconciliation_review_integration_input: PE-31 evaluation failed")
        fail_reasons.extend(
            f"pe31_reconciliation_review_integration_input: {reason}"
            for reason in pe31_result["fail_reasons"]
        )
    elif not pe31_result[
        "reconciliation_review_lifecycle_eligibility_for_separate_operator_review"
    ]:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: "
            "reconciliation_review_lifecycle_eligibility required"
        )

    if pe31_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: source_revision mismatch"
        )
    if pe31_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append("pe31_reconciliation_review_integration_input: adapter_id mismatch")
    if pe31_input.instrument != integration_input.instrument:
        fail_reasons.append("pe31_reconciliation_review_integration_input: instrument mismatch")

    pe31_matrix = pe31_input.lifecycle_matrix_proof
    if pe31_matrix.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            "pe31_reconciliation_review_integration_input: assigned_lifecycle_phase must be "
            f"{PHASE_RECONCILIATION_REVIEW!r}"
        )

    return fail_reasons


def _validate_pe25_integration_proof(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe25_operator_closure_integration_proof
    pe25_input = integration_input.pe25_operator_closure_integration_input

    if proof.integration_owner != PE25_INTEGRATION_OWNER:
        fail_reasons.append(
            f"pe25_operator_closure_integration_proof: integration_owner must be "
            f"{PE25_INTEGRATION_OWNER!r}"
        )
    if not proof.closure_input_digest:
        fail_reasons.append(
            "pe25_operator_closure_integration_proof: closure_input_digest required"
        )
    elif not _valid_sha256_digest(proof.closure_input_digest):
        fail_reasons.append(
            "pe25_operator_closure_integration_proof: closure_input_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif proof.closure_input_digest != compute_pe25_closure_input_digest(pe25_input):
        fail_reasons.append(
            "pe25_operator_closure_integration_proof: closure_input_digest mismatch"
        )

    if not proof.closure_result_digest:
        fail_reasons.append(
            "pe25_operator_closure_integration_proof: closure_result_digest required"
        )
    elif not _valid_sha256_digest(proof.closure_result_digest):
        fail_reasons.append(
            "pe25_operator_closure_integration_proof: closure_result_digest must be "
            "64-char lowercase sha256 hex"
        )
    else:
        expected_result_digest = compute_pe25_closure_result_digest(
            pe25_input,
            operator_closure_static_complete=True,
        )
        if proof.closure_result_digest != expected_result_digest:
            fail_reasons.append(
                "pe25_operator_closure_integration_proof: closure_result_digest mismatch"
            )

    if proof.pe25_integration_pass is not True:
        fail_reasons.append(
            "pe25_operator_closure_integration_proof: pe25_integration_pass must be true"
        )
    if proof.operator_closure_static_complete is not True:
        fail_reasons.append(
            "pe25_operator_closure_integration_proof: operator_closure_static_complete must be true"
        )

    pe25_result = evaluate_operator_closure_lifecycle_integration(pe25_input)
    if not pe25_result["integration_pass"]:
        fail_reasons.append("pe25_operator_closure_integration_input: PE-25 evaluation failed")
        fail_reasons.extend(
            f"pe25_operator_closure_integration_input: {reason}"
            for reason in pe25_result["fail_reasons"]
        )
    elif not pe25_result["operator_closure_static_complete"]:
        fail_reasons.append(
            "pe25_operator_closure_integration_input: operator_closure_static_complete required"
        )

    if pe25_input.source_revision != integration_input.source_revision:
        fail_reasons.append("pe25_operator_closure_integration_input: source_revision mismatch")
    if pe25_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append("pe25_operator_closure_integration_input: adapter_id mismatch")
    if pe25_input.instrument != integration_input.instrument:
        fail_reasons.append("pe25_operator_closure_integration_input: instrument mismatch")

    pe25_matrix = pe25_input.lifecycle_matrix_proof
    if pe25_matrix.assigned_lifecycle_phase != PHASE_READINESS_DECISION:
        fail_reasons.append(
            "pe25_operator_closure_integration_input: assigned_lifecycle_phase must be "
            f"{PHASE_READINESS_DECISION!r}"
        )

    return fail_reasons


def _validate_blocker_register_snapshot(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    binding = integration_input.blocker_register_snapshot

    if binding.blocker_register_owner != BLOCKER_REGISTER_OWNER:
        fail_reasons.append(
            f"blocker_register_snapshot: blocker_register_owner must be {BLOCKER_REGISTER_OWNER!r}"
        )
    if binding.blocker_register_doc_path != BLOCKER_REGISTER_DOC_PATH:
        fail_reasons.append(
            f"blocker_register_snapshot: blocker_register_doc_path must be "
            f"{BLOCKER_REGISTER_DOC_PATH!r}"
        )
    if not binding.blocker_register_source_revision:
        fail_reasons.append("blocker_register_snapshot: blocker_register_source_revision required")
    elif not _valid_sha256_digest(binding.blocker_register_source_revision):
        fail_reasons.append(
            "blocker_register_snapshot: blocker_register_source_revision must be "
            "64-char lowercase sha256 hex"
        )
    if not binding.blocker_register_digest:
        fail_reasons.append("blocker_register_snapshot: blocker_register_digest required")
    elif not _valid_sha256_digest(binding.blocker_register_digest):
        fail_reasons.append(
            "blocker_register_snapshot: blocker_register_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif binding.blocker_register_digest != compute_blocker_register_snapshot_digest(binding):
        fail_reasons.append("blocker_register_snapshot: blocker_register_digest mismatch")

    if binding.snapshot_complete is not True:
        fail_reasons.append("blocker_register_snapshot: snapshot_complete must be true")
    if binding.global_blocker_lift_authorized is not False:
        fail_reasons.append(
            "blocker_register_snapshot: global_blocker_lift_authorized must be false"
        )
    if binding.preflight_lift_authorized is not False:
        fail_reasons.append("blocker_register_snapshot: preflight_lift_authorized must be false")
    if binding.blocker_lift_proof_digest:
        fail_reasons.append(
            "blocker_register_snapshot: blocker_lift_proof_digest must be empty without lift proof"
        )

    if not binding.entries:
        fail_reasons.append("blocker_register_snapshot: entries required")
        return fail_reasons

    entry_ids = [entry.blocker_id for entry in binding.entries]
    if len(entry_ids) != len(set(entry_ids)):
        fail_reasons.append("blocker_register_snapshot: duplicate blocker_id in entries")

    required_ids = set(REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS)
    present_ids = set(entry_ids)
    missing = sorted(required_ids - present_ids)
    unknown = sorted(present_ids - required_ids)
    if missing:
        fail_reasons.append(f"blocker_register_snapshot: missing required blocker ids: {missing}")
    if unknown:
        fail_reasons.append(f"blocker_register_snapshot: unknown blocker ids: {unknown}")

    for entry in binding.entries:
        if not entry.blocker_id:
            fail_reasons.append("blocker_register_snapshot: blocker_id required")
            continue
        if entry.state_verified is not True:
            fail_reasons.append(
                f"blocker_register_snapshot: {entry.blocker_id} state_verified must be true"
            )
        if entry.lift_authorized is not False:
            fail_reasons.append(
                f"blocker_register_snapshot: {entry.blocker_id} lift_authorized must be false"
            )
        if entry.lift_proof_digest:
            fail_reasons.append(
                f"blocker_register_snapshot: {entry.blocker_id} lift_proof_digest must be empty"
            )
        if entry.blocker_state not in _ALLOWED_BLOCKER_STATES_FOR_ELIGIBILITY:
            fail_reasons.append(
                f"blocker_register_snapshot: {entry.blocker_id} blocker_state "
                f"{entry.blocker_state!r} not allowed for eligibility"
            )
        if entry.blocker_state in _LIFTED_BLOCKER_STATES:
            fail_reasons.append(
                f"blocker_register_snapshot: {entry.blocker_id} claims lifted state "
                f"{entry.blocker_state!r} without canonical proof"
            )
        expected_default = _EXPECTED_DEFAULT_BLOCKER_STATES.get(entry.blocker_id)
        if expected_default and entry.blocker_state != expected_default:
            if entry.blocker_state not in {"OPEN", "DEFERRED"}:
                fail_reasons.append(
                    f"blocker_register_snapshot: {entry.blocker_id} blocker_state "
                    f"must be {expected_default!r} or OPEN/DEFERRED, got {entry.blocker_state!r}"
                )

    return fail_reasons


def _validate_readiness_decision_proof(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    binding = integration_input.readiness_decision_proof
    blocker = integration_input.blocker_register_snapshot

    if binding.readiness_decision_owner != READINESS_DECISION_OWNER:
        fail_reasons.append(
            f"readiness_decision_proof: readiness_decision_owner must be "
            f"{READINESS_DECISION_OWNER!r}"
        )
    if binding.blocker_register_owner != BLOCKER_REGISTER_OWNER:
        fail_reasons.append(
            f"readiness_decision_proof: blocker_register_owner must be {BLOCKER_REGISTER_OWNER!r}"
        )
    if binding.readiness_decision_mode != READINESS_DECISION_MODE:
        fail_reasons.append(
            f"readiness_decision_proof: readiness_decision_mode must be {READINESS_DECISION_MODE!r}"
        )
    if binding.review_only is not True:
        fail_reasons.append("readiness_decision_proof: review_only must be true")
    if binding.static_eligibility_proven is not True:
        fail_reasons.append("readiness_decision_proof: static_eligibility_proven must be true")
    if binding.manifest_verify_rc != 0:
        fail_reasons.append("readiness_decision_proof: manifest_verify_rc must be 0")

    counter_checks = (
        ("request_count", binding.request_count),
        ("exchange_request_count", binding.exchange_request_count),
        ("orders_created", binding.orders_created),
        ("orders_cancelled", binding.orders_cancelled),
        ("orders_amended", binding.orders_amended),
        ("positions_changed", binding.positions_changed),
    )
    for field_name, value in counter_checks:
        if value != 0:
            fail_reasons.append(f"readiness_decision_proof: {field_name} must be 0")

    bool_checks = (
        ("network_used", binding.network_used),
        ("credentials_used", binding.credentials_used),
        ("secret_material_read", binding.secret_material_read),
        ("secret_material_stored", binding.secret_material_stored),
        ("exchange_api_called", binding.exchange_api_called),
        ("account_state_queried", binding.account_state_queried),
        ("adapter_called", binding.adapter_called),
        ("runtime_started", binding.runtime_started),
        ("testnet_started", binding.testnet_started),
        ("harness_started", binding.harness_started),
        ("subprocess_started", binding.subprocess_started),
        ("evidence_created", binding.evidence_created),
        ("evidence_mutated", binding.evidence_mutated),
    )
    for field_name, value in bool_checks:
        if value is not False:
            fail_reasons.append(f"readiness_decision_proof: {field_name} must be false")

    if not binding.readiness_decision_proof_digest:
        fail_reasons.append("readiness_decision_proof: readiness_decision_proof_digest required")
    elif not _valid_sha256_digest(binding.readiness_decision_proof_digest):
        fail_reasons.append(
            "readiness_decision_proof: readiness_decision_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif binding.readiness_decision_proof_digest != compute_readiness_decision_proof_digest(
        binding
    ):
        fail_reasons.append("readiness_decision_proof: readiness_decision_proof_digest mismatch")

    if blocker.global_blocker_lift_authorized:
        fail_reasons.append("readiness_decision_proof: global blocker lift not allowed")

    return fail_reasons


def _validate_embedded_lifecycle_sequence(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> list[str]:
    """Validate canonical PE-27..PE-31 phase sequence inside embedded PE-31 input."""
    fail_reasons: list[str] = []
    pe31_input = integration_input.pe31_reconciliation_review_integration_input
    pe30_input = pe31_input.pe30_tiny_order_integration_input
    expected_phases = {
        "pe27": PHASE_ZERO_ORDER,
        "pe28": PHASE_PRIVATE_READONLY,
        "pe29": PHASE_VALIDATE_ONLY,
        "pe30": PHASE_TINY_ORDER,
        "pe31": PHASE_RECONCILIATION_REVIEW,
    }
    actual_phases = {
        "pe27": pe30_input.pe27_zero_order_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe28": pe30_input.pe28_private_readonly_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe29": pe30_input.pe29_validate_only_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe30": pe30_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe31": pe31_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
    }
    for label, expected in expected_phases.items():
        actual = actual_phases[label]
        if actual != expected:
            fail_reasons.append(
                f"lifecycle sequence: {label} assigned_lifecycle_phase must be {expected!r}, "
                f"got {actual!r}"
            )

    phase_indices = [
        LIFECYCLE_PHASE_ORDER.index(phase_id)
        for phase_id in actual_phases.values()
        if phase_id in LIFECYCLE_PHASE_ORDER
    ]
    if phase_indices != sorted(phase_indices):
        fail_reasons.append("lifecycle sequence: embedded phases are not in canonical order")

    pe32_after = integration_input.declared_lifecycle_state_after.assigned_lifecycle_phase
    if pe32_after != PHASE_READINESS_DECISION:
        fail_reasons.append(
            f"lifecycle sequence: PE-32 after phase must be {PHASE_READINESS_DECISION!r}"
        )
    elif LIFECYCLE_PHASE_ORDER.index(pe32_after) <= LIFECYCLE_PHASE_ORDER.index(
        PHASE_RECONCILIATION_REVIEW
    ):
        fail_reasons.append(
            "lifecycle sequence: readiness_decision must follow reconciliation_review"
        )

    return fail_reasons


def validate_readiness_decision_lifecycle_integration_input(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-32 integration input bindings."""
    fail_reasons: list[str] = []

    if not integration_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(integration_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not integration_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif integration_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")
    if not integration_input.adapter_id:
        fail_reasons.append("adapter_id required")
    if not integration_input.integration_id:
        fail_reasons.append("integration_id required")

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

    matrix = integration_input.lifecycle_matrix_proof
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
    if matrix.assigned_lifecycle_phase != PHASE_READINESS_DECISION:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be {PHASE_READINESS_DECISION!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")

    before = integration_input.lifecycle_state_before
    after = integration_input.declared_lifecycle_state_after
    if before.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            f"lifecycle_state_before: assigned_lifecycle_phase must be {PHASE_RECONCILIATION_REVIEW!r}"
        )
    if after.assigned_lifecycle_phase != PHASE_READINESS_DECISION:
        fail_reasons.append(
            f"declared_lifecycle_state_after: assigned_lifecycle_phase must be "
            f"{PHASE_READINESS_DECISION!r}"
        )
    if before.adapter_id != integration_input.adapter_id:
        fail_reasons.append("lifecycle_state_before: adapter_id mismatch")
    if after.adapter_id != integration_input.adapter_id:
        fail_reasons.append("declared_lifecycle_state_after: adapter_id mismatch")
    if matrix.lifecycle_state_digest != after.state_digest:
        fail_reasons.append(
            "lifecycle_matrix_proof: lifecycle_state_digest mismatch with declared after state"
        )

    fail_reasons.extend(_validate_pe31_integration_proof(integration_input))
    fail_reasons.extend(_validate_pe25_integration_proof(integration_input))
    fail_reasons.extend(_validate_embedded_lifecycle_sequence(integration_input))
    fail_reasons.extend(_validate_blocker_register_snapshot(integration_input))
    fail_reasons.extend(_validate_readiness_decision_proof(integration_input))
    fail_reasons.extend(_validate_operator_legibility(integration_input.operator_legibility))
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_readiness_decision_lifecycle_compatibility(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 readiness_decision phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_READINESS_DECISION]
    snapshot = integration_input.safety_snapshot
    decision_proof = integration_input.readiness_decision_proof

    if descriptor.network_phase and snapshot.network_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: network_allowed true for readiness_decision"
        )
    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: orders_allowed true for readiness_decision"
        )
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for readiness_decision"
        )
    if snapshot.live_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: live_authorized true for readiness_decision"
        )
    if snapshot.readiness_decision_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: readiness_decision_authorized true for readiness_decision"
        )
    if snapshot.operator_decision_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: operator_decision_authorized true for readiness_decision"
        )
    if snapshot.operator_closure_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: operator_closure_authorized true for readiness_decision"
        )
    if snapshot.global_blocker_lift_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: global_blocker_lift_authorized true for readiness_decision"
        )
    if snapshot.preflight_lift_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: preflight_lift_authorized true for readiness_decision"
        )
    if snapshot.pilot_start_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: pilot_start_authorized true for readiness_decision"
        )
    if snapshot.promotion_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: promotion_authorized true for readiness_decision"
        )
    if decision_proof.network_used:
        fail_reasons.append("review-only proof requires network_used false")
    if not decision_proof.review_only or not decision_proof.static_eligibility_proven:
        fail_reasons.append("static readiness decision eligibility proof not established")

    return fail_reasons


def evaluate_readiness_decision_lifecycle_integration(
    integration_input: ReadinessDecisionLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_pe31_integration_proof_digest: str | None = None,
    expected_pe25_closure_result_digest: str | None = None,
    expected_blocker_register_digest: str | None = None,
    expected_readiness_decision_proof_digest: str | None = None,
    loose_boolean_eligibility: bool = False,
    dirty_source_state: bool = False,
    readiness_decision_authorized: bool = False,
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
    unknown_lifecycle_state: str | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-32 readiness-decision lifecycle static integration proof."""
    fail_reasons = validate_readiness_decision_lifecycle_integration_input(integration_input)

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = integration_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_pe31_integration_proof_digest is not None:
        if (
            integration_input.pe31_reconciliation_review_integration_proof.integration_proof_digest
            != expected_pe31_integration_proof_digest
        ):
            fail_reasons.append(
                "pe31_reconciliation_review_integration_proof: integration_proof_digest mismatch"
            )

    if expected_pe25_closure_result_digest is not None:
        if (
            integration_input.pe25_operator_closure_integration_proof.closure_result_digest
            != expected_pe25_closure_result_digest
        ):
            fail_reasons.append(
                "pe25_operator_closure_integration_proof: closure_result_digest mismatch"
            )

    if expected_blocker_register_digest is not None:
        if (
            integration_input.blocker_register_snapshot.blocker_register_digest
            != expected_blocker_register_digest
        ):
            fail_reasons.append("blocker_register_snapshot: blocker_register_digest mismatch")

    if expected_readiness_decision_proof_digest is not None:
        if (
            integration_input.readiness_decision_proof.readiness_decision_proof_digest
            != expected_readiness_decision_proof_digest
        ):
            fail_reasons.append("readiness_decision_proof: proof_digest mismatch")

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

    if unknown_lifecycle_state is not None:
        if unknown_lifecycle_state not in LIFECYCLE_PHASE_DESCRIPTORS:
            fail_reasons.append(f"unknown lifecycle state: {unknown_lifecycle_state!r}")

    if not fail_reasons:
        fail_reasons.extend(_validate_readiness_decision_lifecycle_compatibility(integration_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    readiness_decision_lifecycle_eligibility_for_separate_operator_review = integration_pass

    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                readiness_decision_lifecycle_eligibility_for_separate_operator_review=(
                    readiness_decision_lifecycle_eligibility_for_separate_operator_review
                ),
            )
            if integration_pass
            else None
        ),
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe31_integration_proof_digest": (
            integration_input.pe31_reconciliation_review_integration_proof.integration_proof_digest
        ),
        "pe25_closure_result_digest": (
            integration_input.pe25_operator_closure_integration_proof.closure_result_digest
        ),
        "blocker_register_digest": integration_input.blocker_register_snapshot.blocker_register_digest,
        "readiness_decision_proof_digest": (
            integration_input.readiness_decision_proof.readiness_decision_proof_digest
        ),
        "readiness_decision_lifecycle_eligibility_for_separate_operator_review": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe32_readiness_decision_lifecycle_static_integration_proven": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe12_readiness_decision_static_integration_proven": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "static_pe12_lifecycle_chain_complete": (
            readiness_decision_lifecycle_eligibility_for_separate_operator_review
        ),
        "global_readiness_decision_lifecycle_readiness": GLOBAL_READINESS_DECISION_LIFECYCLE_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_blocker_lift_executed": OPERATIVE_BLOCKER_LIFT_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": True,
        "global_blocker_lift_authorized": False,
        "preflight_lift_authorized": False,
        "ready_for_operator_arming": False,
        "readiness_decision_authorized": False,
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


def default_minimal_blocker_snapshot_entries() -> tuple[BlockerSnapshotEntry, ...]:
    return tuple(
        BlockerSnapshotEntry(
            blocker_id=blocker_id,
            blocker_state=_EXPECTED_DEFAULT_BLOCKER_STATES[blocker_id],
            state_verified=True,
            lift_authorized=False,
            lift_proof_digest="",
        )
        for blocker_id in REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS
    )


def default_minimal_blocker_register_snapshot(
    *,
    blocker_register_source_revision: str = "f" * 64,
) -> BlockerRegisterSnapshotBinding:
    entries = default_minimal_blocker_snapshot_entries()
    binding = BlockerRegisterSnapshotBinding(
        blocker_register_owner=BLOCKER_REGISTER_OWNER,
        blocker_register_doc_path=BLOCKER_REGISTER_DOC_PATH,
        blocker_register_source_revision=blocker_register_source_revision,
        blocker_register_digest="",
        snapshot_complete=True,
        global_blocker_lift_authorized=False,
        preflight_lift_authorized=False,
        blocker_lift_proof_digest="",
        entries=entries,
    )
    digest = compute_blocker_register_snapshot_digest(binding)
    return BlockerRegisterSnapshotBinding(
        blocker_register_owner=binding.blocker_register_owner,
        blocker_register_doc_path=binding.blocker_register_doc_path,
        blocker_register_source_revision=binding.blocker_register_source_revision,
        blocker_register_digest=digest,
        snapshot_complete=binding.snapshot_complete,
        global_blocker_lift_authorized=binding.global_blocker_lift_authorized,
        preflight_lift_authorized=binding.preflight_lift_authorized,
        blocker_lift_proof_digest=binding.blocker_lift_proof_digest,
        entries=binding.entries,
    )


def default_minimal_readiness_decision_proof(
    *,
    readiness_decision_proof_digest: str | None = None,
) -> ReadinessDecisionProofBinding:
    binding = ReadinessDecisionProofBinding(
        readiness_decision_owner=READINESS_DECISION_OWNER,
        blocker_register_owner=BLOCKER_REGISTER_OWNER,
        readiness_decision_mode=READINESS_DECISION_MODE,
        review_only=True,
        static_eligibility_proven=True,
        manifest_verify_rc=0,
        readiness_decision_proof_digest="",
        request_count=0,
        exchange_request_count=0,
        orders_created=0,
        orders_cancelled=0,
        orders_amended=0,
        positions_changed=0,
        network_used=False,
        credentials_used=False,
        secret_material_read=False,
        secret_material_stored=False,
        exchange_api_called=False,
        account_state_queried=False,
        adapter_called=False,
        runtime_started=False,
        testnet_started=False,
        harness_started=False,
        subprocess_started=False,
        evidence_created=False,
        evidence_mutated=False,
    )
    digest = readiness_decision_proof_digest or compute_readiness_decision_proof_digest(binding)
    return ReadinessDecisionProofBinding(
        readiness_decision_owner=binding.readiness_decision_owner,
        blocker_register_owner=binding.blocker_register_owner,
        readiness_decision_mode=binding.readiness_decision_mode,
        review_only=binding.review_only,
        static_eligibility_proven=binding.static_eligibility_proven,
        manifest_verify_rc=binding.manifest_verify_rc,
        readiness_decision_proof_digest=digest,
        request_count=binding.request_count,
        exchange_request_count=binding.exchange_request_count,
        orders_created=binding.orders_created,
        orders_cancelled=binding.orders_cancelled,
        orders_amended=binding.orders_amended,
        positions_changed=binding.positions_changed,
        network_used=binding.network_used,
        credentials_used=binding.credentials_used,
        secret_material_read=binding.secret_material_read,
        secret_material_stored=binding.secret_material_stored,
        exchange_api_called=binding.exchange_api_called,
        account_state_queried=binding.account_state_queried,
        adapter_called=binding.adapter_called,
        runtime_started=binding.runtime_started,
        testnet_started=binding.testnet_started,
        harness_started=binding.harness_started,
        subprocess_started=binding.subprocess_started,
        evidence_created=binding.evidence_created,
        evidence_mutated=binding.evidence_mutated,
    )


def default_minimal_safety_snapshot() -> IntegrationSafetySnapshot:
    return IntegrationSafetySnapshot(
        preflight_remains_blocked=True,
        global_blocker_lift_authorized=False,
        preflight_lift_authorized=False,
        ready_for_operator_arming=False,
        readiness_decision_authorized=False,
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


def default_minimal_pe25_integration_proof(
    pe25_input: OperatorClosureLifecycleIntegrationInput,
) -> Pe25OperatorClosureIntegrationProofBinding:
    return Pe25OperatorClosureIntegrationProofBinding(
        integration_owner=PE25_INTEGRATION_OWNER,
        closure_input_digest=compute_pe25_closure_input_digest(pe25_input),
        closure_result_digest=compute_pe25_closure_result_digest(
            pe25_input,
            operator_closure_static_complete=True,
        ),
        pe25_integration_pass=True,
        operator_closure_static_complete=True,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    integration_id: str = "readiness-decision-lifecycle-integration-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
    operator_name: str = "Frank Rauter",
) -> ReadinessDecisionLifecycleIntegrationInput:
    """Minimal valid futures-generic PE-32 integration input for offline tests."""
    pe31_input = default_minimal_pe31_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
    )
    state_digest = lifecycle_state_digest or "f" * 64
    matrix_digest = compute_lifecycle_matrix_digest()
    pe25_input = default_minimal_pe25_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )
    blocker_snapshot = default_minimal_blocker_register_snapshot()
    readiness_proof = default_minimal_readiness_decision_proof()

    return ReadinessDecisionLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        integration_id=integration_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe26_assembly=PE26_CONTRACT_VERSION,
            pe27_zero_order=PE27_CONTRACT_VERSION,
            pe28_private_readonly=PE28_CONTRACT_VERSION,
            pe29_validate_only=PE29_CONTRACT_VERSION,
            pe30_tiny_order=PE30_CONTRACT_VERSION,
            pe31_reconciliation_review=PE31_CONTRACT_VERSION,
            pe25_operator_closure=PE25_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_READINESS_DECISION,
            lifecycle_state_digest=state_digest,
        ),
        lifecycle_state_before=LifecycleStateBinding(
            state_id="lifecycle-before-reconciliation-review",
            state_digest=pe31_input.lifecycle_matrix_proof.lifecycle_state_digest,
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            adapter_id=adapter_id,
        ),
        declared_lifecycle_state_after=LifecycleStateBinding(
            state_id="lifecycle-after-readiness-decision",
            state_digest=state_digest,
            assigned_lifecycle_phase=PHASE_READINESS_DECISION,
            adapter_id=adapter_id,
        ),
        pe31_reconciliation_review_integration_input=pe31_input,
        pe31_reconciliation_review_integration_proof=default_minimal_pe31_integration_proof(
            pe31_input
        ),
        pe25_operator_closure_integration_input=pe25_input,
        pe25_operator_closure_integration_proof=default_minimal_pe25_integration_proof(pe25_input),
        blocker_register_snapshot=blocker_snapshot,
        readiness_decision_proof=readiness_proof,
        operator_legibility=OperatorLegibilityMetadata(
            owner_operator_name=operator_name,
            legibility_only=True,
        ),
        safety_snapshot=default_minimal_safety_snapshot(),
    )
