"""Bounded Futures Testnet operator-closure lifecycle integration (v0, PE-25).

Deterministic, offline, explicit-input-only contract binding PE-12 readiness_decision
phase identity to PE-19/PE-20 operator-review proof chain, PE-22 risk/killswitch/flatten
proof, PE-23 capital-slot ratchet/release proof, and PE-24 pilot-envelope proof.

Static integration only — no operative operator closure, no operator decision, no
readiness authority lift, no network, testnet, runtime, credentials, orders, or
lifecycle transitions.
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
    PHASE_READINESS_DECISION,
    PHASE_RECONCILIATION_REVIEW,
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
from src.ops.bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE24_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_pe24_lifecycle_matrix_digest,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
    compute_lifecycle_matrix_digest as compute_pe22_lifecycle_matrix_digest,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_CLOSURE_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_operator_closure_lifecycle_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_operator_closure_lifecycle_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

GLOBAL_OPERATOR_CLOSURE_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_OPERATOR_CLOSURE_EXECUTED = False
OPERATIVE_OPERATOR_DECISION_CREATED = False
OPERATIVE_APPROVAL_CREATED = False
OPERATIVE_GO_NO_GO_CREATED = False
OPERATIVE_PILOT_EXECUTED = False
OPERATIVE_READINESS_DECISION_CREATED = False
OPERATIVE_SCOPE_SWITCH_EXECUTED = False
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
    "pe19_operator_review": PE19_CONTRACT_VERSION,
    "pe20_review_proof_package": PE20_CONTRACT_VERSION,
    "pe22_risk_killswitch_flatten": PE22_CONTRACT_VERSION,
    "pe23_capital_slot_ratchet_release": PE23_CONTRACT_VERSION,
    "pe24_pilot_envelope": PE24_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe19_operator_review: str
    pe20_review_proof_package: str
    pe22_risk_killswitch_flatten: str
    pe23_capital_slot_ratchet_release: str
    pe24_pilot_envelope: str
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
class DeclaredLifecycleStateBinding:
    state_id: str
    state_digest: str
    assigned_lifecycle_phase: str
    adapter_id: str


@dataclass(frozen=True)
class Pe19ReviewProofBinding:
    review_input_digest: str
    decision_record_digest: str
    review_proof_digest: str
    review_valid: bool
    decision: str
    reason_code: str
    non_authorizing: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    evidence_manifest_verify_rc: int


@dataclass(frozen=True)
class Pe20DurableReviewPackageBinding:
    package_id: str
    package_digest: str
    manifest_verify_rc: int
    static_glb016_reproducibility_satisfied: bool


@dataclass(frozen=True)
class Pe22RiskKillswitchFlattenProofBinding:
    integration_input_digest: str
    integration_proof_digest: str
    pe22_integration_pass: bool
    lifecycle_matrix_digest: str


@dataclass(frozen=True)
class Pe23CapitalSlotRatchetReleaseProofBinding:
    integration_input_digest: str
    integration_proof_digest: str
    pe23_integration_pass: bool
    lifecycle_matrix_digest: str


@dataclass(frozen=True)
class Pe24PilotEnvelopeProofBinding:
    integration_input_digest: str
    integration_proof_digest: str
    pe24_integration_pass: bool
    lifecycle_matrix_digest: str
    pilot_envelope_static_ready: bool


@dataclass(frozen=True)
class OperatorClosureSafetySnapshot:
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
class OperatorClosureLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    closure_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    pe19_review_proof: Pe19ReviewProofBinding
    pe20_durable_review_package: Pe20DurableReviewPackageBinding
    pe22_risk_killswitch_flatten_proof: Pe22RiskKillswitchFlattenProofBinding
    pe23_capital_slot_ratchet_release_proof: Pe23CapitalSlotRatchetReleaseProofBinding
    pe24_pilot_envelope_proof: Pe24PilotEnvelopeProofBinding
    lifecycle_state_before: LifecycleStateBinding
    declared_lifecycle_state_after: DeclaredLifecycleStateBinding
    lifecycle_matrix_proof: LifecycleMatrixProof
    safety_snapshot: OperatorClosureSafetySnapshot
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


def _closure_input_dict(
    integration_input: OperatorClosureLifecycleIntegrationInput,
) -> dict[str, Any]:
    return {
        "integration_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
        "repository_identity": integration_input.repository_identity,
        "adapter_id": integration_input.adapter_id,
        "closure_id": integration_input.closure_id,
        "instrument": integration_input.instrument,
        "market_type": integration_input.market_type,
        "contract_versions": asdict(integration_input.contract_versions),
        "pe19_review_proof": asdict(integration_input.pe19_review_proof),
        "pe20_durable_review_package": asdict(integration_input.pe20_durable_review_package),
        "pe22_risk_killswitch_flatten_proof": asdict(
            integration_input.pe22_risk_killswitch_flatten_proof
        ),
        "pe23_capital_slot_ratchet_release_proof": asdict(
            integration_input.pe23_capital_slot_ratchet_release_proof
        ),
        "pe24_pilot_envelope_proof": asdict(integration_input.pe24_pilot_envelope_proof),
        "lifecycle_state_before": asdict(integration_input.lifecycle_state_before),
        "declared_lifecycle_state_after": asdict(integration_input.declared_lifecycle_state_after),
        "lifecycle_matrix_proof": asdict(integration_input.lifecycle_matrix_proof),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_closure_input_canonical(
    integration_input: OperatorClosureLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _closure_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_closure_input_digest(
    integration_input: OperatorClosureLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_closure_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _closure_result_dict(
    integration_input: OperatorClosureLifecycleIntegrationInput,
    *,
    closure_result_digest: str | None = None,
    operator_closure_static_complete: bool = False,
) -> dict[str, Any]:
    payload = {
        "integration_contract_version": CONTRACT_VERSION,
        "closure_input_digest": compute_closure_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "closure_id": integration_input.closure_id,
        "lifecycle_matrix_digest": integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest,
        "assigned_lifecycle_phase": integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe12_operator_closure_static_integration_proven": operator_closure_static_complete,
        "operator_closure_static_complete": operator_closure_static_complete,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_approval_created": OPERATIVE_APPROVAL_CREATED,
        "operative_go_no_go_created": OPERATIVE_GO_NO_GO_CREATED,
        "operative_pilot_executed": OPERATIVE_PILOT_EXECUTED,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_scope_switch_executed": OPERATIVE_SCOPE_SWITCH_EXECUTED,
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
        "global_operator_closure_readiness": GLOBAL_OPERATOR_CLOSURE_READINESS,
        "non_authorizing": True,
    }
    if closure_result_digest is not None:
        payload["closure_result_digest"] = closure_result_digest
    return payload


def serialize_closure_result_canonical(
    integration_input: OperatorClosureLifecycleIntegrationInput,
    *,
    operator_closure_static_complete: bool = False,
) -> str:
    return json.dumps(
        _closure_result_dict(
            integration_input,
            operator_closure_static_complete=operator_closure_static_complete,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_closure_result_digest(
    integration_input: OperatorClosureLifecycleIntegrationInput,
    *,
    operator_closure_static_complete: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_closure_result_canonical(
            integration_input,
            operator_closure_static_complete=operator_closure_static_complete,
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


def _validate_safety_snapshot(snapshot: OperatorClosureSafetySnapshot) -> list[str]:
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
    elif not _valid_sha256_digest(binding.lifecycle_matrix_digest):
        fail_reasons.append(
            "pe22_risk_killswitch_flatten_proof: lifecycle_matrix_digest must be 64-char lowercase sha256 hex"
        )
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
    elif not _valid_sha256_digest(binding.lifecycle_matrix_digest):
        fail_reasons.append(
            "pe23_capital_slot_ratchet_release_proof: lifecycle_matrix_digest must be 64-char lowercase sha256 hex"
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
    elif not _valid_sha256_digest(binding.lifecycle_matrix_digest):
        fail_reasons.append(
            "pe24_pilot_envelope_proof: lifecycle_matrix_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.lifecycle_matrix_digest != compute_pe24_lifecycle_matrix_digest():
        fail_reasons.append("pe24_pilot_envelope_proof: lifecycle_matrix_digest mismatch")
    return fail_reasons


def validate_operator_closure_lifecycle_integration_input(
    integration_input: OperatorClosureLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit integration input bindings."""
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
    if not integration_input.closure_id:
        fail_reasons.append("closure_id required")

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

    fail_reasons.extend(_validate_pe19_review_proof(integration_input.pe19_review_proof))
    fail_reasons.extend(
        _validate_pe20_durable_review_package(integration_input.pe20_durable_review_package)
    )
    fail_reasons.extend(_validate_pe22_proof(integration_input.pe22_risk_killswitch_flatten_proof))
    fail_reasons.extend(
        _validate_pe23_proof(integration_input.pe23_capital_slot_ratchet_release_proof)
    )
    fail_reasons.extend(_validate_pe24_proof(integration_input.pe24_pilot_envelope_proof))

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
            f"declared_lifecycle_state_after: assigned_lifecycle_phase must be {PHASE_READINESS_DECISION!r}"
        )
    if before.adapter_id != integration_input.adapter_id:
        fail_reasons.append("lifecycle_state_before: adapter_id mismatch")
    if after.adapter_id != integration_input.adapter_id:
        fail_reasons.append("declared_lifecycle_state_after: adapter_id mismatch")

    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_readiness_decision_compatibility(
    integration_input: OperatorClosureLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 readiness_decision phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_READINESS_DECISION]
    snapshot = integration_input.safety_snapshot

    if descriptor.network_phase and snapshot.network_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: network_allowed true for readiness_decision"
        )
    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: orders_allowed true for readiness_decision"
        )
    if descriptor.credentials_phase and snapshot.credentials_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: credentials_allowed true for readiness_decision"
        )
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for readiness_decision"
        )
    if snapshot.live_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: live_authorized true for readiness_decision"
        )
    if snapshot.operator_closure_authorized:
        fail_reasons.append(
            "lifecycle/closure contradiction: operator_closure_authorized true for readiness_decision"
        )
    if snapshot.operator_decision_authorized:
        fail_reasons.append(
            "lifecycle/closure contradiction: operator_decision_authorized true for readiness_decision"
        )
    if snapshot.pilot_start_authorized:
        fail_reasons.append(
            "lifecycle/pilot contradiction: pilot_start_authorized true for readiness_decision"
        )
    if snapshot.promotion_authorized:
        fail_reasons.append("lifecycle/pilot contradiction: promotion_authorized true")
    if snapshot.capital_reallocation_authorized:
        fail_reasons.append("lifecycle/pilot contradiction: capital_reallocation_authorized true")
    if snapshot.reserve_topup_allowed:
        fail_reasons.append("lifecycle/pilot contradiction: reserve_topup_allowed true")

    if (
        integration_input.lifecycle_state_before.assigned_lifecycle_phase
        not in LIFECYCLE_PHASE_DESCRIPTORS
    ):
        fail_reasons.append("lifecycle_state_before: unsupported lifecycle phase")
    if (
        integration_input.declared_lifecycle_state_after.assigned_lifecycle_phase
        not in LIFECYCLE_PHASE_DESCRIPTORS
    ):
        fail_reasons.append("declared_lifecycle_state_after: unsupported lifecycle phase")

    return fail_reasons


def evaluate_operator_closure_lifecycle_integration(
    integration_input: OperatorClosureLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_pe19_review_proof_digest: str | None = None,
    expected_pe20_package_id: str | None = None,
    expected_pe22_integration_proof_digest: str | None = None,
    expected_pe23_integration_proof_digest: str | None = None,
    expected_pe24_integration_proof_digest: str | None = None,
    expected_closure_id: str | None = None,
    operator_closure_static_complete_without_proof_chain: bool = False,
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
    credentials_allowed: bool = False,
    orders_allowed: bool = False,
    killswitch_active: bool = False,
    killswitch_triggered: bool = False,
    unresolved_risk_state: bool = False,
    invalid_ratchet: bool = False,
    disallowed_slot_basis_increase: bool = False,
    manipulated_release_eligibility: bool = False,
) -> dict[str, Any]:
    """Evaluate explicit PE-12 readiness_decision operator-closure static integration proof."""
    fail_reasons = validate_operator_closure_lifecycle_integration_input(integration_input)

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = integration_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_pe19_review_proof_digest is not None:
        if (
            integration_input.pe19_review_proof.review_proof_digest
            != expected_pe19_review_proof_digest
        ):
            fail_reasons.append("pe19_review_proof: review_proof_digest mismatch")

    if expected_pe20_package_id is not None:
        if integration_input.pe20_durable_review_package.package_id != expected_pe20_package_id:
            fail_reasons.append("pe20_durable_review_package: package_id mismatch")

    if expected_pe22_integration_proof_digest is not None:
        if (
            integration_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest
            != expected_pe22_integration_proof_digest
        ):
            fail_reasons.append(
                "pe22_risk_killswitch_flatten_proof: integration_proof_digest mismatch"
            )

    if expected_pe23_integration_proof_digest is not None:
        if (
            integration_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest
            != expected_pe23_integration_proof_digest
        ):
            fail_reasons.append(
                "pe23_capital_slot_ratchet_release_proof: integration_proof_digest mismatch"
            )

    if expected_pe24_integration_proof_digest is not None:
        if (
            integration_input.pe24_pilot_envelope_proof.integration_proof_digest
            != expected_pe24_integration_proof_digest
        ):
            fail_reasons.append("pe24_pilot_envelope_proof: integration_proof_digest mismatch")

    if expected_closure_id is not None:
        if integration_input.closure_id != expected_closure_id:
            fail_reasons.append("closure_id mismatch")

    if operator_closure_static_complete_without_proof_chain:
        fail_reasons.append(
            "operator_closure_static_complete=true without full proof chain is insufficient"
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

    if not fail_reasons:
        fail_reasons.extend(_validate_readiness_decision_compatibility(integration_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    operator_closure_static_complete = integration_pass

    return {
        "integration_pass": integration_pass,
        "closure_input_digest": compute_closure_input_digest(integration_input),
        "closure_result_digest": (
            compute_closure_result_digest(
                integration_input,
                operator_closure_static_complete=operator_closure_static_complete,
            )
            if integration_pass
            else None
        ),
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe12_operator_closure_static_integration_proven": operator_closure_static_complete,
        "operator_closure_static_complete": operator_closure_static_complete,
        "global_operator_closure_readiness": GLOBAL_OPERATOR_CLOSURE_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_approval_created": OPERATIVE_APPROVAL_CREATED,
        "operative_go_no_go_created": OPERATIVE_GO_NO_GO_CREATED,
        "operative_pilot_executed": OPERATIVE_PILOT_EXECUTED,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_scope_switch_executed": OPERATIVE_SCOPE_SWITCH_EXECUTED,
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


def default_minimal_safety_snapshot() -> OperatorClosureSafetySnapshot:
    return OperatorClosureSafetySnapshot(
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


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    closure_id: str = "operator-closure-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> OperatorClosureLifecycleIntegrationInput:
    """Minimal valid futures-generic integration input for offline tests."""
    state_digest = lifecycle_state_digest or "e" * 64
    matrix_digest = compute_lifecycle_matrix_digest()

    pe19_review_proof = Pe19ReviewProofBinding(
        review_input_digest="1" * 64,
        decision_record_digest="2" * 64,
        review_proof_digest="3" * 64,
        review_valid=True,
        decision=DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
        reason_code="evidence_complete",
        non_authorizing=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        evidence_manifest_verify_rc=0,
    )
    pe20_package = Pe20DurableReviewPackageBinding(
        package_id="4" * 64,
        package_digest="5" * 64,
        manifest_verify_rc=0,
        static_glb016_reproducibility_satisfied=True,
    )
    pe22_proof = Pe22RiskKillswitchFlattenProofBinding(
        integration_input_digest="6" * 64,
        integration_proof_digest="7" * 64,
        pe22_integration_pass=True,
        lifecycle_matrix_digest=compute_pe22_lifecycle_matrix_digest(),
    )
    pe23_proof = Pe23CapitalSlotRatchetReleaseProofBinding(
        integration_input_digest="8" * 64,
        integration_proof_digest="9" * 64,
        pe23_integration_pass=True,
        lifecycle_matrix_digest=compute_pe23_lifecycle_matrix_digest(),
    )
    pe24_proof = Pe24PilotEnvelopeProofBinding(
        integration_input_digest="a" * 64,
        integration_proof_digest="b" * 64,
        pe24_integration_pass=True,
        lifecycle_matrix_digest=compute_pe24_lifecycle_matrix_digest(),
        pilot_envelope_static_ready=True,
    )

    return OperatorClosureLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        closure_id=closure_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe19_operator_review=PE19_CONTRACT_VERSION,
            pe20_review_proof_package=PE20_CONTRACT_VERSION,
            pe22_risk_killswitch_flatten=PE22_CONTRACT_VERSION,
            pe23_capital_slot_ratchet_release=PE23_CONTRACT_VERSION,
            pe24_pilot_envelope=PE24_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        pe19_review_proof=pe19_review_proof,
        pe20_durable_review_package=pe20_package,
        pe22_risk_killswitch_flatten_proof=pe22_proof,
        pe23_capital_slot_ratchet_release_proof=pe23_proof,
        pe24_pilot_envelope_proof=pe24_proof,
        lifecycle_state_before=LifecycleStateBinding(
            state_id="lifecycle-before-001",
            state_digest="c" * 64,
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            adapter_id=adapter_id,
        ),
        declared_lifecycle_state_after=DeclaredLifecycleStateBinding(
            state_id="lifecycle-after-001",
            state_digest="d" * 64,
            assigned_lifecycle_phase=PHASE_READINESS_DECISION,
            adapter_id=adapter_id,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_READINESS_DECISION,
            lifecycle_state_digest=state_digest,
        ),
        safety_snapshot=default_minimal_safety_snapshot(),
    )
