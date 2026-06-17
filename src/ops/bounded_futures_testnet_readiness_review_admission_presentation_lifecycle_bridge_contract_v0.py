"""Bounded Futures Testnet readiness review ↔ admission presentation lifecycle bridge (v0).

Deterministic, offline, explicit-input-only fail-closed bridge composing the canonical
PE-38 preflight execution readiness review lifecycle integration and the PE-34/35/36/37
operator review admission presentation lifecycle integration merged via PR #4436.

Static bridge only — no network, testnet, runtime, credentials, orders, operator review,
admission, presentation, decision, closure, evidence acceptance, completion, or authority lift.
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
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE36_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE36_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as ADMISSION_LIFECYCLE_CONTRACT_VERSION,
    OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
    compute_integration_input_digest as compute_admission_integration_input_digest,
    compute_integration_proof_digest as compute_admission_integration_proof_digest,
    evaluate_operator_review_admission_presentation_lifecycle_integration,
    validate_operator_review_admission_presentation_lifecycle_integration_input,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE37_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE37_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
    HANDOFF_OWNER as PE34_HANDOFF_OWNER,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE38_CONTRACT_VERSION,
    PreflightExecutionReadinessReviewLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe38_integration_input_digest,
    compute_integration_proof_digest as compute_pe38_integration_proof_digest,
    evaluate_preflight_execution_readiness_review_lifecycle_integration,
    validate_preflight_execution_readiness_review_lifecycle_integration_input,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_READINESS_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_BRIDGE_CONTRACT_V0=true"
CONTRACT_VERSION = (
    "bounded_futures_testnet_readiness_review_admission_presentation_lifecycle_bridge.v0"
)
SERIALIZATION_VERSION = "bounded_futures_testnet_readiness_review_admission_presentation_lifecycle_bridge.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

BRIDGE_MODE = "static_readiness_review_admission_presentation_lifecycle_bridge_proof_only"
BRIDGE_OWNER = CONTRACT_VERSION

CONTRACT_IMPLEMENTATION_ONLY = True
READINESS_REVIEW_EXECUTED = False
OPERATOR_REVIEW_EXECUTED = False
OPERATOR_DECISION_EXECUTED = False
OPERATOR_CLOSURE_EXECUTED = False
ADMISSION_EXECUTED = False
PRESENTATION_EXECUTED = False
EVIDENCE_OPERATIONALLY_ACCEPTED = False
RUN_COMPLETION_OPERATIONALLY_RECORDED = False
NEW_AUTHORITY_SURFACE_CREATED = False
SECOND_READINESS_SURFACE_CREATED = False
SECOND_REVIEW_SURFACE_CREATED = False
SECOND_HANDOFF_SURFACE_CREATED = False
SECOND_ADMISSION_SURFACE_CREATED = False
SECOND_PRESENTATION_SURFACE_CREATED = False
SECOND_TRACEABILITY_SURFACE_CREATED = False
SECOND_DECISION_SURFACE_CREATED = False
SECOND_CLOSURE_SURFACE_CREATED = False
SECOND_EVIDENCE_SURFACE_CREATED = False
SECOND_COMPLETION_SURFACE_CREATED = False
NEW_QUEUE_SURFACE_CREATED = False
NEW_UI_SURFACE_CREATED = False
NEW_DASHBOARD_SURFACE_CREATED = False
NEW_RUNTIME_PATH_CREATED = False
NEW_RUN_ENTRYPOINT_CREATED = False
RUN_STARTED = False
RUNNER_STARTED = False
SESSION_STARTED = False
FILESYSTEM_ACCESSED = False
ARCHIVE_READ = False
ARCHIVE_WRITTEN = False
MANIFEST_READ = False
MANIFEST_WRITTEN = False
REPLAY_EXECUTED = False
NETWORK_USED = False
CREDENTIALS_USED = False
EXCHANGE_API_CALLED = False
ADAPTER_CALLED = False
HARNESS_STARTED = False
SUBPROCESS_STARTED = False
PAPER_STARTED = False
SHADOW_STARTED = False
TESTNET_STARTED = False
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

BRIDGE_PROOF_CHAIN_SLOT_ORDER = (
    "pe38_integration_proof_digest",
    "pe38_pe34_handoff_digest",
    "pe38_pe37_traceability_identity",
    "admission_integration_proof_digest",
    "admission_pe34_handoff_digest",
    "admission_pe36_presentation_projection_digest",
    "admission_pe37_traceability_identity",
    "shared_pe35_boundary_result_digest",
    "shared_pe37_traceability_identity",
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe34_handoff": PE34_CONTRACT_VERSION,
    "pe35_staleness": PE35_CONTRACT_VERSION,
    "pe36_admission_presentation": PE36_CONTRACT_VERSION,
    "pe37_traceability": PE37_CONTRACT_VERSION,
    "pe38_readiness_review": PE38_CONTRACT_VERSION,
    "admission_presentation_lifecycle": ADMISSION_LIFECYCLE_CONTRACT_VERSION,
    "bridge": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe34_handoff: str
    pe35_staleness: str
    pe36_admission_presentation: str
    pe37_traceability: str
    pe38_readiness_review: str
    admission_presentation_lifecycle: str
    bridge: str


@dataclass(frozen=True)
class Pe38ReadinessReviewProofBinding:
    integration_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    pe34_handoff_digest: str
    pe35_boundary_result_digest: str
    pe37_traceability_identity: str
    pe38_integration_pass: bool
    readiness_review_lifecycle_bound: bool


@dataclass(frozen=True)
class AdmissionPresentationLifecycleProofBinding:
    integration_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    pe34_handoff_digest: str
    pe35_boundary_result_digest: str
    pe36_presentation_projection_digest: str
    pe37_traceability_identity: str
    admission_presentation_lifecycle_bound: bool
    pe34_handoff_bound: bool
    pe35_staleness_revocation_recovery_bound: bool
    pe36_admission_presentation_bound: bool
    pe37_durable_traceability_bound: bool


@dataclass(frozen=True)
class BridgeProofChainBinding:
    pe38_integration_proof_digest: str
    pe38_pe34_handoff_digest: str
    pe38_pe37_traceability_identity: str
    admission_integration_proof_digest: str
    admission_pe34_handoff_digest: str
    admission_pe36_presentation_projection_digest: str
    admission_pe37_traceability_identity: str
    shared_pe35_boundary_result_digest: str
    shared_pe37_traceability_identity: str


@dataclass(frozen=True)
class BridgeSafetySnapshot:
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
class ReadinessReviewAdmissionPresentationLifecycleBridgeInput:
    source_revision: str
    repository_identity: str
    bridge_id: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    pe38_integration_input: PreflightExecutionReadinessReviewLifecycleIntegrationInput
    admission_presentation_integration_input: (
        OperatorReviewAdmissionPresentationLifecycleIntegrationInput
    )
    pe38_readiness_review_proof: Pe38ReadinessReviewProofBinding
    admission_presentation_lifecycle_proof: AdmissionPresentationLifecycleProofBinding
    proof_chain: BridgeProofChainBinding
    safety_snapshot: BridgeSafetySnapshot
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


def _validate_safety_snapshot(snapshot: BridgeSafetySnapshot) -> list[str]:
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


def _validate_pe38_readiness_review_proof(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
    *,
    pe38_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = bridge_input.pe38_readiness_review_proof
    pe38_input = bridge_input.pe38_integration_input

    if proof.integration_owner != PE38_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe38_readiness_review_proof: integration_owner must be {PE38_CONTRACT_VERSION!r}"
        )
    if proof.source_revision != bridge_input.source_revision:
        fail_reasons.append("pe38_readiness_review_proof: source_revision mismatch")
    if proof.integration_input_digest != compute_pe38_integration_input_digest(pe38_input):
        fail_reasons.append("pe38_readiness_review_proof: integration_input_digest mismatch")
    expected_proof_digest = pe38_result.get("integration_proof_digest")
    if not proof.integration_proof_digest:
        fail_reasons.append("pe38_readiness_review_proof: integration_proof_digest required")
    elif expected_proof_digest is None:
        fail_reasons.append(
            "pe38_readiness_review_proof: PE-38 integration_proof_digest unavailable"
        )
    elif proof.integration_proof_digest != expected_proof_digest:
        fail_reasons.append("pe38_readiness_review_proof: integration_proof_digest mismatch")
    expected_pe34 = pe38_input.proof_chain.pe34_handoff_digest
    if not proof.pe34_handoff_digest:
        fail_reasons.append("pe38_readiness_review_proof: pe34_handoff_digest required")
    elif proof.pe34_handoff_digest != expected_pe34:
        fail_reasons.append("pe38_readiness_review_proof: pe34_handoff_digest mismatch")
    expected_pe35 = pe38_input.proof_chain.pe35_boundary_result_digest
    if not proof.pe35_boundary_result_digest:
        fail_reasons.append("pe38_readiness_review_proof: pe35_boundary_result_digest required")
    elif proof.pe35_boundary_result_digest != expected_pe35:
        fail_reasons.append("pe38_readiness_review_proof: pe35_boundary_result_digest mismatch")
    expected_pe37 = pe38_input.proof_chain.pe37_traceability_identity
    if not proof.pe37_traceability_identity:
        fail_reasons.append("pe38_readiness_review_proof: pe37_traceability_identity required")
    elif proof.pe37_traceability_identity != expected_pe37:
        fail_reasons.append("pe38_readiness_review_proof: pe37_traceability_identity mismatch")
    if proof.pe38_integration_pass is not True:
        fail_reasons.append("pe38_readiness_review_proof: pe38_integration_pass must be true")
    if proof.readiness_review_lifecycle_bound is not True:
        fail_reasons.append(
            "pe38_readiness_review_proof: readiness_review_lifecycle_bound must be true"
        )
    return fail_reasons


def _validate_admission_presentation_lifecycle_proof(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
    *,
    admission_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = bridge_input.admission_presentation_lifecycle_proof
    admission_input = bridge_input.admission_presentation_integration_input

    if proof.integration_owner != ADMISSION_LIFECYCLE_CONTRACT_VERSION:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: integration_owner must be "
            f"{ADMISSION_LIFECYCLE_CONTRACT_VERSION!r}"
        )
    if proof.source_revision != bridge_input.source_revision:
        fail_reasons.append("admission_presentation_lifecycle_proof: source_revision mismatch")
    if proof.integration_input_digest != compute_admission_integration_input_digest(
        admission_input
    ):
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: integration_input_digest mismatch"
        )
    expected_proof_digest = admission_result.get("integration_proof_digest")
    if not proof.integration_proof_digest:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: integration_proof_digest required"
        )
    elif expected_proof_digest is None:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: admission integration_proof_digest unavailable"
        )
    elif proof.integration_proof_digest != expected_proof_digest:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: integration_proof_digest mismatch"
        )
    expected_pe34 = admission_input.proof_chain.pe34_handoff_digest
    if not proof.pe34_handoff_digest:
        fail_reasons.append("admission_presentation_lifecycle_proof: pe34_handoff_digest required")
    elif proof.pe34_handoff_digest != expected_pe34:
        fail_reasons.append("admission_presentation_lifecycle_proof: pe34_handoff_digest mismatch")
    expected_pe35 = admission_input.proof_chain.pe35_boundary_result_digest
    if not proof.pe35_boundary_result_digest:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe35_boundary_result_digest required"
        )
    elif proof.pe35_boundary_result_digest != expected_pe35:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe35_boundary_result_digest mismatch"
        )
    expected_pe36 = admission_input.proof_chain.pe36_presentation_projection_digest
    if not proof.pe36_presentation_projection_digest:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe36_presentation_projection_digest required"
        )
    elif proof.pe36_presentation_projection_digest != expected_pe36:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe36_presentation_projection_digest mismatch"
        )
    expected_pe37 = admission_input.proof_chain.pe37_traceability_identity
    if not proof.pe37_traceability_identity:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe37_traceability_identity required"
        )
    elif proof.pe37_traceability_identity != expected_pe37:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe37_traceability_identity mismatch"
        )
    if proof.admission_presentation_lifecycle_bound is not True:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: admission_presentation_lifecycle_bound "
            "must be true"
        )
    if proof.pe34_handoff_bound is not True:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe34_handoff_bound must be true"
        )
    if proof.pe35_staleness_revocation_recovery_bound is not True:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe35_staleness_revocation_recovery_bound "
            "must be true"
        )
    if proof.pe36_admission_presentation_bound is not True:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe36_admission_presentation_bound must be true"
        )
    if proof.pe37_durable_traceability_bound is not True:
        fail_reasons.append(
            "admission_presentation_lifecycle_proof: pe37_durable_traceability_bound must be true"
        )
    return fail_reasons


def _validate_cross_lifecycle_coherence(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
) -> list[str]:
    fail_reasons: list[str] = []
    pe38 = bridge_input.pe38_integration_input
    admission = bridge_input.admission_presentation_integration_input

    if pe38.source_revision != bridge_input.source_revision:
        fail_reasons.append("composition: PE-38 source_revision mismatch")
    if admission.source_revision != bridge_input.source_revision:
        fail_reasons.append("composition: admission source_revision mismatch")
    if pe38.adapter_id != bridge_input.adapter_id:
        fail_reasons.append("composition: PE-38 adapter_id mismatch")
    if admission.adapter_id != bridge_input.adapter_id:
        fail_reasons.append("composition: admission adapter_id mismatch")
    if pe38.instrument != bridge_input.instrument:
        fail_reasons.append("composition: PE-38 instrument mismatch")
    if admission.instrument != bridge_input.instrument:
        fail_reasons.append("composition: admission instrument mismatch")

    pe38_pe34 = pe38.proof_chain.pe34_handoff_digest
    admission_pe34 = admission.proof_chain.pe34_handoff_digest
    if pe38_pe34 != admission_pe34:
        fail_reasons.append("bridge: PE-38 and admission pe34_handoff_digest mismatch")

    pe38_pe35 = pe38.proof_chain.pe35_boundary_result_digest
    admission_pe35 = admission.proof_chain.pe35_boundary_result_digest
    if pe38_pe35 != admission_pe35:
        fail_reasons.append("bridge: PE-38 and admission pe35_boundary_result_digest mismatch")

    pe38_pe37 = pe38.proof_chain.pe37_traceability_identity
    admission_pe37 = admission.proof_chain.pe37_traceability_identity
    if pe38_pe37 != admission_pe37:
        fail_reasons.append("bridge: PE-38 and admission pe37_traceability_identity mismatch")

    pe38_pe34_input = compute_pe34_boundary_input_digest(pe38.pe34_handoff_input)
    admission_pe34_input = compute_pe34_boundary_input_digest(admission.pe34_handoff_input)
    if pe38_pe34_input != admission_pe34_input:
        fail_reasons.append("bridge: PE-38 and admission pe34_handoff_input digest mismatch")

    return fail_reasons


def _validate_proof_chain_binding(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
    *,
    pe38_result: dict[str, Any],
    admission_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    chain = bridge_input.proof_chain
    pe38 = bridge_input.pe38_integration_input
    admission = bridge_input.admission_presentation_integration_input
    shared_pe35 = pe38.proof_chain.pe35_boundary_result_digest
    shared_pe37 = pe38.proof_chain.pe37_traceability_identity

    expected_slots = {
        "pe38_integration_proof_digest": pe38_result.get("integration_proof_digest") or "",
        "pe38_pe34_handoff_digest": pe38.proof_chain.pe34_handoff_digest,
        "pe38_pe37_traceability_identity": pe38.proof_chain.pe37_traceability_identity,
        "admission_integration_proof_digest": admission_result.get("integration_proof_digest")
        or "",
        "admission_pe34_handoff_digest": admission.proof_chain.pe34_handoff_digest,
        "admission_pe36_presentation_projection_digest": (
            admission.proof_chain.pe36_presentation_projection_digest
        ),
        "admission_pe37_traceability_identity": admission.proof_chain.pe37_traceability_identity,
        "shared_pe35_boundary_result_digest": shared_pe35,
        "shared_pe37_traceability_identity": shared_pe37,
    }
    for slot_name in BRIDGE_PROOF_CHAIN_SLOT_ORDER:
        value = getattr(chain, slot_name)
        if not value:
            fail_reasons.append(f"proof_chain: {slot_name} required")
        elif slot_name.endswith("traceability_identity") and not _valid_sha256_digest(value):
            fail_reasons.append(f"proof_chain: {slot_name} must be 64-char lowercase sha256 hex")
        elif not slot_name.endswith("traceability_identity") and not _valid_sha256_digest(value):
            fail_reasons.append(f"proof_chain: {slot_name} must be 64-char lowercase sha256 hex")
        elif value != expected_slots[slot_name]:
            fail_reasons.append(f"proof_chain: {slot_name} mismatch")
    return fail_reasons


def validate_readiness_review_admission_presentation_lifecycle_bridge_input(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-38 ↔ admission presentation lifecycle bridge."""
    fail_reasons: list[str] = []

    if not bridge_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(bridge_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not bridge_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif bridge_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")
    if not bridge_input.bridge_id:
        fail_reasons.append("bridge_id required")
    if not bridge_input.adapter_id:
        fail_reasons.append("adapter_id required")

    fail_reasons.extend(
        _validate_instrument_scope(bridge_input.instrument, bridge_input.market_type)
    )

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(bridge_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    fail_reasons.extend(
        validate_preflight_execution_readiness_review_lifecycle_integration_input(
            bridge_input.pe38_integration_input
        )
    )
    fail_reasons.extend(
        validate_operator_review_admission_presentation_lifecycle_integration_input(
            bridge_input.admission_presentation_integration_input
        )
    )
    fail_reasons.extend(_validate_cross_lifecycle_coherence(bridge_input))
    fail_reasons.extend(_validate_safety_snapshot(bridge_input.safety_snapshot))

    if bridge_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if bridge_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if bridge_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    pe38_result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        bridge_input.pe38_integration_input,
    )
    admission_result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        bridge_input.admission_presentation_integration_input,
    )

    if not pe38_result.get("integration_pass"):
        fail_reasons.append("pe38_integration_input: PE-38 evaluation failed")
        fail_reasons.extend(
            f"pe38_integration_input: {reason}" for reason in pe38_result.get("fail_reasons", [])
        )
    if not admission_result.get("integration_pass"):
        fail_reasons.append("admission_presentation_integration_input: admission evaluation failed")
        fail_reasons.extend(
            f"admission_presentation_integration_input: {reason}"
            for reason in admission_result.get("fail_reasons", [])
        )

    fail_reasons.extend(
        _validate_pe38_readiness_review_proof(bridge_input, pe38_result=pe38_result)
    )
    fail_reasons.extend(
        _validate_admission_presentation_lifecycle_proof(
            bridge_input, admission_result=admission_result
        )
    )
    fail_reasons.extend(
        _validate_proof_chain_binding(
            bridge_input, pe38_result=pe38_result, admission_result=admission_result
        )
    )

    return _sorted_unique(fail_reasons)


def _bridge_input_dict(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
) -> dict[str, Any]:
    return {
        "bridge_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": bridge_input.source_revision,
        "repository_identity": bridge_input.repository_identity,
        "bridge_id": bridge_input.bridge_id,
        "adapter_id": bridge_input.adapter_id,
        "instrument": bridge_input.instrument,
        "market_type": bridge_input.market_type,
        "contract_versions": asdict(bridge_input.contract_versions),
        "pe38_integration_input_digest": compute_pe38_integration_input_digest(
            bridge_input.pe38_integration_input
        ),
        "admission_integration_input_digest": compute_admission_integration_input_digest(
            bridge_input.admission_presentation_integration_input
        ),
        "pe38_readiness_review_proof": asdict(bridge_input.pe38_readiness_review_proof),
        "admission_presentation_lifecycle_proof": asdict(
            bridge_input.admission_presentation_lifecycle_proof
        ),
        "proof_chain": asdict(bridge_input.proof_chain),
        "safety_snapshot": asdict(bridge_input.safety_snapshot),
        "bound_traceability_identities": list(bridge_input.bound_traceability_identities),
        "bound_admission_identities": list(bridge_input.bound_admission_identities),
        "futures_only": bridge_input.futures_only,
        "environment": bridge_input.environment,
        "non_authorizing": bridge_input.non_authorizing,
    }


def serialize_bridge_input_canonical(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
) -> str:
    return json.dumps(_bridge_input_dict(bridge_input), sort_keys=True, separators=(",", ":"))


def compute_bridge_input_digest(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
) -> str:
    return hashlib.sha256(
        serialize_bridge_input_canonical(bridge_input).encode("utf-8")
    ).hexdigest()


def _bridge_result_dict(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
    *,
    bridge_proof_digest: str | None = None,
    readiness_review_admission_presentation_lifecycle_bridge_eligibility: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "bridge_contract_version": CONTRACT_VERSION,
        "bridge_input_digest": compute_bridge_input_digest(bridge_input),
        "source_revision": bridge_input.source_revision,
        "adapter_id": bridge_input.adapter_id,
        "bridge_id": bridge_input.bridge_id,
        "bridge_mode": BRIDGE_MODE,
        "bridge_owner": BRIDGE_OWNER,
        "pe38_integration_proof_digest": bridge_input.proof_chain.pe38_integration_proof_digest,
        "admission_integration_proof_digest": (
            bridge_input.proof_chain.admission_integration_proof_digest
        ),
        "shared_pe37_traceability_identity": bridge_input.proof_chain.shared_pe37_traceability_identity,
        "readiness_review_admission_presentation_lifecycle_bridge_eligibility": (
            readiness_review_admission_presentation_lifecycle_bridge_eligibility
        ),
        "readiness_review_lifecycle_bound": readiness_review_admission_presentation_lifecycle_bridge_eligibility,
        "pe38_durable_traceability_bound": readiness_review_admission_presentation_lifecycle_bridge_eligibility,
        "admission_presentation_lifecycle_bound": (
            readiness_review_admission_presentation_lifecycle_bridge_eligibility
        ),
        "pe34_handoff_bound": readiness_review_admission_presentation_lifecycle_bridge_eligibility,
        "pe35_staleness_revocation_recovery_bound": (
            readiness_review_admission_presentation_lifecycle_bridge_eligibility
        ),
        "pe36_admission_presentation_bound": (
            readiness_review_admission_presentation_lifecycle_bridge_eligibility
        ),
        "pe37_durable_traceability_bound": (
            readiness_review_admission_presentation_lifecycle_bridge_eligibility
        ),
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "readiness_review_executed": READINESS_REVIEW_EXECUTED,
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_executed": OPERATOR_DECISION_EXECUTED,
        "operator_closure_executed": OPERATOR_CLOSURE_EXECUTED,
        "admission_executed": ADMISSION_EXECUTED,
        "presentation_executed": PRESENTATION_EXECUTED,
        "evidence_operationally_accepted": EVIDENCE_OPERATIONALLY_ACCEPTED,
        "run_completion_operationally_recorded": RUN_COMPLETION_OPERATIONALLY_RECORDED,
        "new_authority_surface_created": NEW_AUTHORITY_SURFACE_CREATED,
        "second_readiness_surface_created": SECOND_READINESS_SURFACE_CREATED,
        "second_review_surface_created": SECOND_REVIEW_SURFACE_CREATED,
        "second_handoff_surface_created": SECOND_HANDOFF_SURFACE_CREATED,
        "second_admission_surface_created": SECOND_ADMISSION_SURFACE_CREATED,
        "second_presentation_surface_created": SECOND_PRESENTATION_SURFACE_CREATED,
        "second_traceability_surface_created": SECOND_TRACEABILITY_SURFACE_CREATED,
        "second_decision_surface_created": SECOND_DECISION_SURFACE_CREATED,
        "second_closure_surface_created": SECOND_CLOSURE_SURFACE_CREATED,
        "second_evidence_surface_created": SECOND_EVIDENCE_SURFACE_CREATED,
        "second_completion_surface_created": SECOND_COMPLETION_SURFACE_CREATED,
        "new_queue_surface_created": NEW_QUEUE_SURFACE_CREATED,
        "new_ui_surface_created": NEW_UI_SURFACE_CREATED,
        "new_dashboard_surface_created": NEW_DASHBOARD_SURFACE_CREATED,
        "new_runtime_path_created": NEW_RUNTIME_PATH_CREATED,
        "new_run_entrypoint_created": NEW_RUN_ENTRYPOINT_CREATED,
        "run_started": RUN_STARTED,
        "runner_started": RUNNER_STARTED,
        "session_started": SESSION_STARTED,
        "filesystem_accessed": FILESYSTEM_ACCESSED,
        "archive_read": ARCHIVE_READ,
        "archive_written": ARCHIVE_WRITTEN,
        "manifest_read": MANIFEST_READ,
        "manifest_written": MANIFEST_WRITTEN,
        "replay_executed": REPLAY_EXECUTED,
        "network_used": NETWORK_USED,
        "credentials_used": CREDENTIALS_USED,
        "exchange_api_called": EXCHANGE_API_CALLED,
        "adapter_called": ADAPTER_CALLED,
        "harness_started": HARNESS_STARTED,
        "subprocess_started": SUBPROCESS_STARTED,
        "paper_started": PAPER_STARTED,
        "shadow_started": SHADOW_STARTED,
        "testnet_started": TESTNET_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": PREFLIGHT_REMAINS_BLOCKED,
        "non_authorizing": True,
    }
    if bridge_proof_digest is not None:
        payload["bridge_proof_digest"] = bridge_proof_digest
    return payload


def serialize_bridge_result_canonical(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
    *,
    readiness_review_admission_presentation_lifecycle_bridge_eligibility: bool = False,
) -> str:
    return json.dumps(
        _bridge_result_dict(
            bridge_input,
            readiness_review_admission_presentation_lifecycle_bridge_eligibility=(
                readiness_review_admission_presentation_lifecycle_bridge_eligibility
            ),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_bridge_proof_digest(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
    *,
    readiness_review_admission_presentation_lifecycle_bridge_eligibility: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_bridge_result_canonical(
            bridge_input,
            readiness_review_admission_presentation_lifecycle_bridge_eligibility=(
                readiness_review_admission_presentation_lifecycle_bridge_eligibility
            ),
        ).encode("utf-8")
    ).hexdigest()


def evaluate_readiness_review_admission_presentation_lifecycle_bridge(
    bridge_input: ReadinessReviewAdmissionPresentationLifecycleBridgeInput,
    *,
    expected_source_revision: str | None = None,
    expected_pe38_integration_proof_digest: str | None = None,
    expected_admission_integration_proof_digest: str | None = None,
    expected_shared_pe37_traceability_identity: str | None = None,
    loose_boolean_eligibility: bool = False,
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
    selected_decision: str | None = None,
    default_approve: bool = False,
    implicit_approve: bool = False,
    extra_fields: dict[str, Any] | None = None,
    extra_proof_chain_slots: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Evaluate explicit PE-38 ↔ admission presentation lifecycle bridge proof."""
    fail_reasons = validate_readiness_review_admission_presentation_lifecycle_bridge_input(
        bridge_input
    )

    if expected_source_revision is not None:
        if bridge_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    chain = bridge_input.proof_chain
    if expected_pe38_integration_proof_digest is not None:
        if chain.pe38_integration_proof_digest != expected_pe38_integration_proof_digest:
            fail_reasons.append("proof_chain: pe38_integration_proof_digest mismatch")
    if expected_admission_integration_proof_digest is not None:
        if chain.admission_integration_proof_digest != expected_admission_integration_proof_digest:
            fail_reasons.append("proof_chain: admission_integration_proof_digest mismatch")
    if expected_shared_pe37_traceability_identity is not None:
        if chain.shared_pe37_traceability_identity != expected_shared_pe37_traceability_identity:
            fail_reasons.append("proof_chain: shared_pe37_traceability_identity mismatch")

    if loose_boolean_eligibility:
        fail_reasons.append(
            "loose_boolean_eligibility=true without canonical proof is insufficient"
        )
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
    if selected_decision is not None:
        fail_reasons.append(
            f"selected_decision {selected_decision!r} is not allowed at lifecycle bridge"
        )
    if default_approve:
        fail_reasons.append("default_approve is not allowed at lifecycle bridge")
    if implicit_approve:
        fail_reasons.append("implicit_approve is not allowed at lifecycle bridge")
    if extra_fields:
        fail_reasons.extend(_reject_forbidden_extra_fields(extra_fields))
    if extra_proof_chain_slots:
        fail_reasons.append(f"unknown extra proof chain slots: {sorted(extra_proof_chain_slots)!r}")

    fail_reasons = _sorted_unique(fail_reasons)
    bridge_pass = not fail_reasons
    eligibility = bridge_pass

    return {
        "bridge_pass": bridge_pass,
        "bridge_input_digest": compute_bridge_input_digest(bridge_input),
        "bridge_proof_digest": (
            compute_bridge_proof_digest(
                bridge_input,
                readiness_review_admission_presentation_lifecycle_bridge_eligibility=eligibility,
            )
            if bridge_pass
            else None
        ),
        "bridge_mode": BRIDGE_MODE,
        "bridge_owner": BRIDGE_OWNER,
        "pe38_integration_proof_digest": chain.pe38_integration_proof_digest,
        "admission_integration_proof_digest": chain.admission_integration_proof_digest,
        "shared_pe37_traceability_identity": chain.shared_pe37_traceability_identity,
        "readiness_review_admission_presentation_lifecycle_bridge_eligibility": eligibility,
        "readiness_review_lifecycle_bound": eligibility,
        "pe38_durable_traceability_bound": eligibility,
        "admission_presentation_lifecycle_bound": eligibility,
        "pe34_handoff_bound": eligibility,
        "pe35_staleness_revocation_recovery_bound": eligibility,
        "pe36_admission_presentation_bound": eligibility,
        "pe37_durable_traceability_bound": eligibility,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "readiness_review_executed": READINESS_REVIEW_EXECUTED,
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_executed": OPERATOR_DECISION_EXECUTED,
        "operator_closure_executed": OPERATOR_CLOSURE_EXECUTED,
        "admission_executed": ADMISSION_EXECUTED,
        "presentation_executed": PRESENTATION_EXECUTED,
        "evidence_operationally_accepted": EVIDENCE_OPERATIONALLY_ACCEPTED,
        "run_completion_operationally_recorded": RUN_COMPLETION_OPERATIONALLY_RECORDED,
        "new_authority_surface_created": NEW_AUTHORITY_SURFACE_CREATED,
        "run_started": RUN_STARTED,
        "runner_started": RUNNER_STARTED,
        "session_started": SESSION_STARTED,
        "filesystem_accessed": FILESYSTEM_ACCESSED,
        "archive_read": ARCHIVE_READ,
        "archive_written": ARCHIVE_WRITTEN,
        "manifest_read": MANIFEST_READ,
        "manifest_written": MANIFEST_WRITTEN,
        "replay_executed": REPLAY_EXECUTED,
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
        "exchange_api_called": False,
        "exchange_request_count": 0,
        "orders_created": 0,
        "orders_cancelled": 0,
        "orders_amended": 0,
        "positions_changed": 0,
        "adapter_called": False,
        "testnet_started": False,
        "harness_started": False,
        "subprocess_started": False,
        "runtime_started": False,
        "fail_reasons": fail_reasons,
    }


def default_minimal_safety_snapshot() -> BridgeSafetySnapshot:
    return BridgeSafetySnapshot(
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


def default_minimal_bridge_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    bridge_id: str = "readiness-review-admission-presentation-lifecycle-bridge-001",
    instrument: str = "PF_ETHUSD",
) -> ReadinessReviewAdmissionPresentationLifecycleBridgeInput:
    """Minimal valid futures-generic bridge input for offline tests."""
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        compute_boundary_input_digest as compute_pe36_input_digest,
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
        ContractVersionsInput as AdmissionContractVersionsInput,
        IntegrationProofChainBinding as AdmissionProofChainBinding,
        IntegrationSafetySnapshot as AdmissionSafetySnapshot,
        Pe34HandoffProofBinding,
        Pe35StalenessProofBinding,
        Pe36AdmissionPresentationProofBinding,
        Pe37TraceabilityProofBinding,
        compute_integration_input_digest as compute_admission_input_digest,
        evaluate_operator_review_admission_presentation_lifecycle_integration as evaluate_admission,
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        evaluate_operator_review_admission_presentation_boundary,
    )
    from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
        compute_boundary_input_digest as compute_pe35_input_digest,
        evaluate_handoff_staleness_revocation_recovery_boundary,
    )
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        compute_boundary_input_digest as compute_pe37_input_digest,
        evaluate_durable_evidence_traceability_boundary,
    )
    from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
        evaluate_operator_review_handoff_boundary,
    )
    from src.ops.bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0 import (
        default_minimal_integration_input as default_minimal_pe38_input,
        evaluate_preflight_execution_readiness_review_lifecycle_integration as evaluate_pe38,
    )

    pe38_input = default_minimal_pe38_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
    )
    pe38_result = evaluate_pe38(pe38_input)

    pe34_handoff = pe38_input.pe34_handoff_input
    pe35_boundary = pe38_input.pe35_boundary_input
    pe37_boundary = pe38_input.pe37_traceability_boundary_input
    pe36_boundary = pe37_boundary.pe36_boundary_input

    pe34_result = evaluate_operator_review_handoff_boundary(pe34_handoff)
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_boundary)
    pe36_result = evaluate_operator_review_admission_presentation_boundary(pe36_boundary)
    pe37_result = evaluate_durable_evidence_traceability_boundary(pe37_boundary)

    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe35_input_digest = compute_pe35_input_digest(pe35_boundary)
    pe36_input_digest = compute_pe36_input_digest(pe36_boundary)
    pe37_input_digest = compute_pe37_input_digest(pe37_boundary)

    admission_proof_chain = AdmissionProofChainBinding(
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

    admission_input = OperatorReviewAdmissionPresentationLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        integration_id="operator-review-admission-presentation-lifecycle-integration-001",
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=AdmissionContractVersionsInput(
            pe34_handoff=PE34_CONTRACT_VERSION,
            pe35_staleness=PE35_CONTRACT_VERSION,
            pe36_admission_presentation=PE36_CONTRACT_VERSION,
            pe37_traceability=PE37_CONTRACT_VERSION,
            integration=ADMISSION_LIFECYCLE_CONTRACT_VERSION,
        ),
        pe34_handoff_input=pe34_handoff,
        pe35_boundary_input=pe35_boundary,
        pe36_boundary_input=pe36_boundary,
        pe37_traceability_boundary_input=pe37_boundary,
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
            boundary_input_digest=pe35_input_digest,
            boundary_result_digest=pe35_result["boundary_result_digest"],
            handoff_current=pe35_result["handoff_current"],
            pe35_integration_pass=True,
            handoff_staleness_revocation_recovery_boundary_satisfied=True,
        ),
        pe36_admission_presentation_proof=Pe36AdmissionPresentationProofBinding(
            boundary_owner=PE36_BOUNDARY_OWNER,
            source_revision=source_revision,
            boundary_input_digest=pe36_input_digest,
            boundary_result_digest=pe36_result["boundary_result_digest"],
            presentation_projection_digest=pe36_result["presentation_projection_digest"],
            pe36_integration_pass=True,
            operator_review_admission_presentation_boundary_satisfied=True,
        ),
        pe37_traceability_proof=Pe37TraceabilityProofBinding(
            traceability_owner=PE37_BOUNDARY_OWNER,
            source_revision=source_revision,
            boundary_input_digest=pe37_input_digest,
            boundary_result_digest=pe37_result["boundary_result_digest"],
            traceability_identity=pe37_result["traceability_identity"],
            admission_identity=pe37_result["admission_identity"],
            pe37_integration_pass=True,
            durable_evidence_traceability_boundary_satisfied=True,
        ),
        proof_chain=admission_proof_chain,
        safety_snapshot=AdmissionSafetySnapshot(
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
        ),
    )
    admission_result = evaluate_admission(admission_input)

    shared_pe35 = pe38_input.proof_chain.pe35_boundary_result_digest
    shared_pe37 = pe38_input.proof_chain.pe37_traceability_identity

    bridge_proof_chain = BridgeProofChainBinding(
        pe38_integration_proof_digest=pe38_result["integration_proof_digest"],
        pe38_pe34_handoff_digest=pe38_input.proof_chain.pe34_handoff_digest,
        pe38_pe37_traceability_identity=pe38_input.proof_chain.pe37_traceability_identity,
        admission_integration_proof_digest=admission_result["integration_proof_digest"],
        admission_pe34_handoff_digest=admission_input.proof_chain.pe34_handoff_digest,
        admission_pe36_presentation_projection_digest=(
            admission_input.proof_chain.pe36_presentation_projection_digest
        ),
        admission_pe37_traceability_identity=admission_input.proof_chain.pe37_traceability_identity,
        shared_pe35_boundary_result_digest=shared_pe35,
        shared_pe37_traceability_identity=shared_pe37,
    )

    return ReadinessReviewAdmissionPresentationLifecycleBridgeInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        bridge_id=bridge_id,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe34_handoff=PE34_CONTRACT_VERSION,
            pe35_staleness=PE35_CONTRACT_VERSION,
            pe36_admission_presentation=PE36_CONTRACT_VERSION,
            pe37_traceability=PE37_CONTRACT_VERSION,
            pe38_readiness_review=PE38_CONTRACT_VERSION,
            admission_presentation_lifecycle=ADMISSION_LIFECYCLE_CONTRACT_VERSION,
            bridge=CONTRACT_VERSION,
        ),
        pe38_integration_input=pe38_input,
        admission_presentation_integration_input=admission_input,
        pe38_readiness_review_proof=Pe38ReadinessReviewProofBinding(
            integration_owner=PE38_CONTRACT_VERSION,
            source_revision=source_revision,
            integration_input_digest=compute_pe38_integration_input_digest(pe38_input),
            integration_proof_digest=pe38_result["integration_proof_digest"],
            pe34_handoff_digest=pe38_input.proof_chain.pe34_handoff_digest,
            pe35_boundary_result_digest=shared_pe35,
            pe37_traceability_identity=shared_pe37,
            pe38_integration_pass=True,
            readiness_review_lifecycle_bound=True,
        ),
        admission_presentation_lifecycle_proof=AdmissionPresentationLifecycleProofBinding(
            integration_owner=ADMISSION_LIFECYCLE_CONTRACT_VERSION,
            source_revision=source_revision,
            integration_input_digest=compute_admission_input_digest(admission_input),
            integration_proof_digest=admission_result["integration_proof_digest"],
            pe34_handoff_digest=admission_input.proof_chain.pe34_handoff_digest,
            pe35_boundary_result_digest=admission_input.proof_chain.pe35_boundary_result_digest,
            pe36_presentation_projection_digest=(
                admission_input.proof_chain.pe36_presentation_projection_digest
            ),
            pe37_traceability_identity=admission_input.proof_chain.pe37_traceability_identity,
            admission_presentation_lifecycle_bound=True,
            pe34_handoff_bound=True,
            pe35_staleness_revocation_recovery_bound=True,
            pe36_admission_presentation_bound=True,
            pe37_durable_traceability_bound=True,
        ),
        proof_chain=bridge_proof_chain,
        safety_snapshot=default_minimal_safety_snapshot(),
    )
