"""Bounded Futures Testnet operator review admission presentation lifecycle integration (v0).

Deterministic, offline, explicit-input-only fail-closed integration composing PE-34
operator-review handoff boundary, PE-35 staleness/revocation/recovery boundary,
PE-36 operator-review admission presentation boundary, and PE-37 durable evidence
traceability boundary.

Static integration only — no network, testnet, runtime, credentials, orders, operator
review execution, operative admission, presentation rendering, evidence acceptance, or
authority lift.
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
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE36_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE36_CONTRACT_VERSION,
    OperatorReviewAdmissionPresentationBoundaryInput,
    compute_boundary_input_digest as compute_pe36_boundary_input_digest,
    compute_boundary_result_digest as compute_pe36_boundary_result_digest,
    evaluate_operator_review_admission_presentation_boundary,
    validate_operator_review_admission_presentation_boundary_input,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE37_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE37_CONTRACT_VERSION,
    DurableEvidenceTraceabilityBoundaryInput,
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
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = (
    "bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration.v0"
)
SERIALIZATION_VERSION = "bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

INTEGRATION_MODE = "static_operator_review_admission_presentation_lifecycle_integration_proof_only"
INTEGRATION_OWNER = CONTRACT_VERSION

CONTRACT_IMPLEMENTATION_ONLY = True
OPERATOR_REVIEW_EXECUTED = False
OPERATOR_DECISION_EXECUTED = False
OPERATOR_CLOSURE_EXECUTED = False
ADMISSION_EXECUTED = False
PRESENTATION_EXECUTED = False
EVIDENCE_OPERATIONALLY_ACCEPTED = False
NEW_AUTHORITY_SURFACE_CREATED = False
SECOND_REVIEW_SURFACE_CREATED = False
SECOND_HANDOFF_SURFACE_CREATED = False
SECOND_ADMISSION_SURFACE_CREATED = False
SECOND_PRESENTATION_SURFACE_CREATED = False
SECOND_TRACEABILITY_SURFACE_CREATED = False
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

PROOF_CHAIN_SLOT_ORDER = (
    "pe34_handoff_digest",
    "pe35_boundary_input_digest",
    "pe35_boundary_result_digest",
    "pe36_boundary_input_digest",
    "pe36_boundary_result_digest",
    "pe36_presentation_projection_digest",
    "pe37_boundary_input_digest",
    "pe37_boundary_result_digest",
    "pe37_traceability_identity",
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe34_handoff": PE34_CONTRACT_VERSION,
    "pe35_staleness": PE35_CONTRACT_VERSION,
    "pe36_admission_presentation": PE36_CONTRACT_VERSION,
    "pe37_traceability": PE37_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe34_handoff: str
    pe35_staleness: str
    pe36_admission_presentation: str
    pe37_traceability: str
    integration: str


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
class Pe36AdmissionPresentationProofBinding:
    boundary_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str | None
    presentation_projection_digest: str | None
    pe36_integration_pass: bool
    operator_review_admission_presentation_boundary_satisfied: bool


@dataclass(frozen=True)
class Pe37TraceabilityProofBinding:
    traceability_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str | None
    traceability_identity: str | None
    admission_identity: str | None
    pe37_integration_pass: bool
    durable_evidence_traceability_boundary_satisfied: bool


@dataclass(frozen=True)
class IntegrationProofChainBinding:
    pe34_handoff_digest: str
    pe35_boundary_input_digest: str
    pe35_boundary_result_digest: str
    pe36_boundary_input_digest: str
    pe36_boundary_result_digest: str
    pe36_presentation_projection_digest: str
    pe37_boundary_input_digest: str
    pe37_boundary_result_digest: str
    pe37_traceability_identity: str


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
class OperatorReviewAdmissionPresentationLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    integration_id: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    pe34_handoff_input: OperatorReviewHandoffBoundaryInput
    pe35_boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput
    pe36_boundary_input: OperatorReviewAdmissionPresentationBoundaryInput
    pe37_traceability_boundary_input: DurableEvidenceTraceabilityBoundaryInput
    pe34_handoff_proof: Pe34HandoffProofBinding
    pe35_staleness_proof: Pe35StalenessProofBinding
    pe36_admission_presentation_proof: Pe36AdmissionPresentationProofBinding
    pe37_traceability_proof: Pe37TraceabilityProofBinding
    proof_chain: IntegrationProofChainBinding
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


def _validate_embedded_chain_coherence(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    pe34 = integration_input.pe34_handoff_input
    pe35 = integration_input.pe35_boundary_input
    pe36 = integration_input.pe36_boundary_input
    pe37 = integration_input.pe37_traceability_boundary_input

    if pe35.pe34_handoff is not pe34:
        if compute_pe34_boundary_input_digest(
            pe35.pe34_handoff
        ) != compute_pe34_boundary_input_digest(pe34):
            fail_reasons.append("composition: PE-35 pe34_handoff mismatch")

    if pe36.pe35_boundary_input is not pe35:
        if compute_pe35_boundary_input_digest(pe36.pe35_boundary_input) != (
            compute_pe35_boundary_input_digest(pe35)
        ):
            fail_reasons.append("composition: PE-36 pe35_boundary_input mismatch")

    if pe37.pe36_boundary_input is not pe36:
        if compute_pe36_boundary_input_digest(pe37.pe36_boundary_input) != (
            compute_pe36_boundary_input_digest(pe36)
        ):
            fail_reasons.append("composition: PE-37 pe36_boundary_input mismatch")

    for label, actual, expected in (
        ("pe34", pe34.source_revision, integration_input.source_revision),
        ("pe35", pe35.pe34_handoff.source_revision, integration_input.source_revision),
        (
            "pe36",
            pe36.pe35_boundary_input.pe34_handoff.source_revision,
            integration_input.source_revision,
        ),
        (
            "pe37",
            pe37.pe36_boundary_input.pe35_boundary_input.pe34_handoff.source_revision,
            integration_input.source_revision,
        ),
    ):
        if actual != expected:
            fail_reasons.append(f"composition: {label} source_revision mismatch")

    for label, actual, expected in (
        ("pe34", pe34.adapter_id, integration_input.adapter_id),
        ("pe35", pe35.pe34_handoff.adapter_id, integration_input.adapter_id),
        ("pe36", pe36.pe35_boundary_input.pe34_handoff.adapter_id, integration_input.adapter_id),
    ):
        if actual != expected:
            fail_reasons.append(f"composition: {label} adapter_id mismatch")

    for label, actual, expected in (
        ("pe34", pe34.instrument, integration_input.instrument),
        ("pe35", pe35.pe34_handoff.instrument, integration_input.instrument),
        ("pe36", pe36.pe35_boundary_input.pe34_handoff.instrument, integration_input.instrument),
    ):
        if actual != expected:
            fail_reasons.append(f"composition: {label} instrument mismatch")

    return fail_reasons


def _validate_pe34_handoff_proof(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
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
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
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


def _validate_pe36_admission_presentation_proof(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
    *,
    pe36_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe36_admission_presentation_proof
    pe36_input = integration_input.pe36_boundary_input

    if proof.boundary_owner != PE36_BOUNDARY_OWNER:
        fail_reasons.append(
            f"pe36_admission_presentation_proof: boundary_owner must be {PE36_BOUNDARY_OWNER!r}"
        )
    if proof.source_revision != integration_input.source_revision:
        fail_reasons.append("pe36_admission_presentation_proof: source_revision mismatch")
    if proof.boundary_input_digest != compute_pe36_boundary_input_digest(pe36_input):
        fail_reasons.append("pe36_admission_presentation_proof: boundary_input_digest mismatch")
    expected_result_digest = pe36_result.get("boundary_result_digest")
    if proof.boundary_result_digest != expected_result_digest:
        fail_reasons.append("pe36_admission_presentation_proof: boundary_result_digest mismatch")
    expected_projection_digest = pe36_result.get("presentation_projection_digest")
    if proof.presentation_projection_digest != expected_projection_digest:
        fail_reasons.append(
            "pe36_admission_presentation_proof: presentation_projection_digest mismatch"
        )
    if proof.pe36_integration_pass is not True:
        fail_reasons.append("pe36_admission_presentation_proof: pe36_integration_pass must be true")
    if proof.operator_review_admission_presentation_boundary_satisfied is not True:
        fail_reasons.append(
            "pe36_admission_presentation_proof: "
            "operator_review_admission_presentation_boundary_satisfied must be true"
        )
    return fail_reasons


def _validate_pe37_traceability_proof(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
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
    if proof.boundary_result_digest != expected_result_digest:
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


def _validate_proof_chain_binding(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
    *,
    pe34_digest: str,
    pe35_result: dict[str, Any],
    pe36_result: dict[str, Any],
    pe37_result: dict[str, Any],
) -> list[str]:
    fail_reasons: list[str] = []
    chain = integration_input.proof_chain
    expected_slots = {
        "pe34_handoff_digest": pe34_digest,
        "pe35_boundary_input_digest": compute_pe35_boundary_input_digest(
            integration_input.pe35_boundary_input
        ),
        "pe35_boundary_result_digest": pe35_result.get("boundary_result_digest") or "",
        "pe36_boundary_input_digest": compute_pe36_boundary_input_digest(
            integration_input.pe36_boundary_input
        ),
        "pe36_boundary_result_digest": pe36_result.get("boundary_result_digest") or "",
        "pe36_presentation_projection_digest": pe36_result.get("presentation_projection_digest")
        or "",
        "pe37_boundary_input_digest": compute_pe37_boundary_input_digest(
            integration_input.pe37_traceability_boundary_input
        ),
        "pe37_boundary_result_digest": pe37_result.get("boundary_result_digest") or "",
        "pe37_traceability_identity": pe37_result.get("traceability_identity") or "",
    }
    for slot_name in PROOF_CHAIN_SLOT_ORDER:
        value = getattr(chain, slot_name)
        if not value:
            fail_reasons.append(f"proof_chain: {slot_name} required")
        elif slot_name != "pe37_traceability_identity" and not _valid_sha256_digest(value):
            fail_reasons.append(f"proof_chain: {slot_name} must be 64-char lowercase sha256 hex")
        elif slot_name == "pe37_traceability_identity" and not _valid_sha256_digest(value):
            fail_reasons.append(
                "proof_chain: pe37_traceability_identity must be 64-char lowercase sha256 hex"
            )
        elif value != expected_slots[slot_name]:
            fail_reasons.append(f"proof_chain: {slot_name} mismatch")
    return fail_reasons


def validate_operator_review_admission_presentation_lifecycle_integration_input(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-34/35/36/37 lifecycle integration bindings."""
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
        validate_operator_review_handoff_boundary_input(integration_input.pe34_handoff_input)
    )
    fail_reasons.extend(
        validate_handoff_staleness_revocation_recovery_boundary_input(
            integration_input.pe35_boundary_input
        )
    )
    fail_reasons.extend(
        validate_operator_review_admission_presentation_boundary_input(
            integration_input.pe36_boundary_input
        )
    )
    fail_reasons.extend(
        validate_durable_evidence_traceability_boundary_input(
            integration_input.pe37_traceability_boundary_input
        )
    )
    fail_reasons.extend(_validate_embedded_chain_coherence(integration_input))
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    pe34_result = evaluate_operator_review_handoff_boundary(integration_input.pe34_handoff_input)
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(
        integration_input.pe35_boundary_input
    )
    pe36_result = evaluate_operator_review_admission_presentation_boundary(
        integration_input.pe36_boundary_input
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
    if not pe36_result.get("operator_review_admission_presentation_boundary_satisfied"):
        fail_reasons.append("pe36_boundary_input: PE-36 evaluation failed")
        fail_reasons.extend(
            f"pe36_boundary_input: {reason}" for reason in pe36_result.get("fail_reasons", [])
        )
    if not pe37_result.get("durable_evidence_traceability_boundary_satisfied"):
        fail_reasons.append("pe37_traceability_boundary_input: PE-37 evaluation failed")
        fail_reasons.extend(
            f"pe37_traceability_boundary_input: {reason}"
            for reason in pe37_result.get("fail_reasons", [])
        )

    pe34_digest = compute_pe34_boundary_input_digest(integration_input.pe34_handoff_input)
    fail_reasons.extend(_validate_pe34_handoff_proof(integration_input, pe34_result=pe34_result))
    fail_reasons.extend(_validate_pe35_staleness_proof(integration_input, pe35_result=pe35_result))
    fail_reasons.extend(
        _validate_pe36_admission_presentation_proof(integration_input, pe36_result=pe36_result)
    )
    fail_reasons.extend(
        _validate_pe37_traceability_proof(integration_input, pe37_result=pe37_result)
    )
    fail_reasons.extend(
        _validate_proof_chain_binding(
            integration_input,
            pe34_digest=pe34_digest,
            pe35_result=pe35_result,
            pe36_result=pe36_result,
            pe37_result=pe37_result,
        )
    )

    return _sorted_unique(fail_reasons)


def _integration_input_dict(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
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
        "pe34_handoff_digest": compute_pe34_boundary_input_digest(
            integration_input.pe34_handoff_input
        ),
        "pe35_boundary_input_digest": compute_pe35_boundary_input_digest(
            integration_input.pe35_boundary_input
        ),
        "pe36_boundary_input_digest": compute_pe36_boundary_input_digest(
            integration_input.pe36_boundary_input
        ),
        "pe37_boundary_input_digest": compute_pe37_boundary_input_digest(
            integration_input.pe37_traceability_boundary_input
        ),
        "pe34_handoff_proof": asdict(integration_input.pe34_handoff_proof),
        "pe35_staleness_proof": asdict(integration_input.pe35_staleness_proof),
        "pe36_admission_presentation_proof": asdict(
            integration_input.pe36_admission_presentation_proof
        ),
        "pe37_traceability_proof": asdict(integration_input.pe37_traceability_proof),
        "proof_chain": asdict(integration_input.proof_chain),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "bound_traceability_identities": list(integration_input.bound_traceability_identities),
        "bound_admission_identities": list(integration_input.bound_admission_identities),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _integration_result_dict(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
    operator_review_admission_presentation_lifecycle_eligibility: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "integration_id": integration_input.integration_id,
        "integration_mode": INTEGRATION_MODE,
        "integration_owner": INTEGRATION_OWNER,
        "pe34_handoff_digest": integration_input.proof_chain.pe34_handoff_digest,
        "pe35_boundary_result_digest": integration_input.proof_chain.pe35_boundary_result_digest,
        "pe36_presentation_projection_digest": (
            integration_input.proof_chain.pe36_presentation_projection_digest
        ),
        "pe37_traceability_identity": integration_input.proof_chain.pe37_traceability_identity,
        "operator_review_admission_presentation_lifecycle_eligibility": (
            operator_review_admission_presentation_lifecycle_eligibility
        ),
        "pe34_handoff_bound": operator_review_admission_presentation_lifecycle_eligibility,
        "pe35_staleness_revocation_recovery_bound": (
            operator_review_admission_presentation_lifecycle_eligibility
        ),
        "pe36_admission_presentation_bound": (
            operator_review_admission_presentation_lifecycle_eligibility
        ),
        "pe37_durable_traceability_bound": (
            operator_review_admission_presentation_lifecycle_eligibility
        ),
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_executed": OPERATOR_DECISION_EXECUTED,
        "operator_closure_executed": OPERATOR_CLOSURE_EXECUTED,
        "admission_executed": ADMISSION_EXECUTED,
        "presentation_executed": PRESENTATION_EXECUTED,
        "evidence_operationally_accepted": EVIDENCE_OPERATIONALLY_ACCEPTED,
        "new_authority_surface_created": NEW_AUTHORITY_SURFACE_CREATED,
        "second_review_surface_created": SECOND_REVIEW_SURFACE_CREATED,
        "second_handoff_surface_created": SECOND_HANDOFF_SURFACE_CREATED,
        "second_admission_surface_created": SECOND_ADMISSION_SURFACE_CREATED,
        "second_presentation_surface_created": SECOND_PRESENTATION_SURFACE_CREATED,
        "second_traceability_surface_created": SECOND_TRACEABILITY_SURFACE_CREATED,
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
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_result_canonical(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
    *,
    operator_review_admission_presentation_lifecycle_eligibility: bool = False,
) -> str:
    return json.dumps(
        _integration_result_dict(
            integration_input,
            operator_review_admission_presentation_lifecycle_eligibility=(
                operator_review_admission_presentation_lifecycle_eligibility
            ),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
    *,
    operator_review_admission_presentation_lifecycle_eligibility: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_integration_result_canonical(
            integration_input,
            operator_review_admission_presentation_lifecycle_eligibility=(
                operator_review_admission_presentation_lifecycle_eligibility
            ),
        ).encode("utf-8")
    ).hexdigest()


def evaluate_operator_review_admission_presentation_lifecycle_integration(
    integration_input: OperatorReviewAdmissionPresentationLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_pe34_handoff_digest: str | None = None,
    expected_pe35_boundary_result_digest: str | None = None,
    expected_pe36_presentation_projection_digest: str | None = None,
    expected_pe37_traceability_identity: str | None = None,
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
    """Evaluate explicit PE-34/35/36/37 admission presentation lifecycle integration proof."""
    fail_reasons = validate_operator_review_admission_presentation_lifecycle_integration_input(
        integration_input
    )

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    chain = integration_input.proof_chain
    if expected_pe34_handoff_digest is not None:
        if chain.pe34_handoff_digest != expected_pe34_handoff_digest:
            fail_reasons.append("proof_chain: pe34_handoff_digest mismatch")
    if expected_pe35_boundary_result_digest is not None:
        if chain.pe35_boundary_result_digest != expected_pe35_boundary_result_digest:
            fail_reasons.append("proof_chain: pe35_boundary_result_digest mismatch")
    if expected_pe36_presentation_projection_digest is not None:
        if (
            chain.pe36_presentation_projection_digest
            != expected_pe36_presentation_projection_digest
        ):
            fail_reasons.append("proof_chain: pe36_presentation_projection_digest mismatch")
    if expected_pe37_traceability_identity is not None:
        if chain.pe37_traceability_identity != expected_pe37_traceability_identity:
            fail_reasons.append("proof_chain: pe37_traceability_identity mismatch")

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
            f"selected_decision {selected_decision!r} is not allowed at lifecycle integration"
        )
    if default_approve:
        fail_reasons.append("default_approve is not allowed at lifecycle integration")
    if implicit_approve:
        fail_reasons.append("implicit_approve is not allowed at lifecycle integration")
    if extra_fields:
        fail_reasons.extend(_reject_forbidden_extra_fields(extra_fields))
    if extra_proof_chain_slots:
        fail_reasons.append(f"unknown extra proof chain slots: {sorted(extra_proof_chain_slots)!r}")

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    eligibility = integration_pass

    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                operator_review_admission_presentation_lifecycle_eligibility=eligibility,
            )
            if integration_pass
            else None
        ),
        "integration_mode": INTEGRATION_MODE,
        "integration_owner": INTEGRATION_OWNER,
        "pe34_handoff_digest": chain.pe34_handoff_digest,
        "pe35_boundary_result_digest": chain.pe35_boundary_result_digest,
        "pe36_presentation_projection_digest": chain.pe36_presentation_projection_digest,
        "pe37_traceability_identity": chain.pe37_traceability_identity,
        "operator_review_admission_presentation_lifecycle_eligibility": eligibility,
        "pe34_handoff_bound": eligibility,
        "pe35_staleness_revocation_recovery_bound": eligibility,
        "pe36_admission_presentation_bound": eligibility,
        "pe37_durable_traceability_bound": eligibility,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_executed": OPERATOR_DECISION_EXECUTED,
        "operator_closure_executed": OPERATOR_CLOSURE_EXECUTED,
        "admission_executed": ADMISSION_EXECUTED,
        "presentation_executed": PRESENTATION_EXECUTED,
        "evidence_operationally_accepted": EVIDENCE_OPERATIONALLY_ACCEPTED,
        "new_authority_surface_created": NEW_AUTHORITY_SURFACE_CREATED,
        "second_review_surface_created": SECOND_REVIEW_SURFACE_CREATED,
        "second_handoff_surface_created": SECOND_HANDOFF_SURFACE_CREATED,
        "second_admission_surface_created": SECOND_ADMISSION_SURFACE_CREATED,
        "second_presentation_surface_created": SECOND_PRESENTATION_SURFACE_CREATED,
        "second_traceability_surface_created": SECOND_TRACEABILITY_SURFACE_CREATED,
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
    integration_id: str = "operator-review-admission-presentation-lifecycle-integration-001",
    instrument: str = "PF_ETHUSD",
    review_identity: str = "glb-016-bounded-futures-testnet-operator-review",
) -> OperatorReviewAdmissionPresentationLifecycleIntegrationInput:
    """Minimal valid futures-generic lifecycle integration input for offline tests."""
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        default_minimal_boundary_input as default_minimal_pe37_boundary_input,
    )

    pe37_boundary_input = default_minimal_pe37_boundary_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        review_identity=review_identity,
    )
    pe36_input = pe37_boundary_input.pe36_boundary_input
    pe35_input = pe36_input.pe35_boundary_input
    pe34_handoff = pe35_input.pe34_handoff

    pe34_result = evaluate_operator_review_handoff_boundary(pe34_handoff)
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    pe36_result = evaluate_operator_review_admission_presentation_boundary(pe36_input)
    pe37_result = evaluate_durable_evidence_traceability_boundary(pe37_boundary_input)

    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe35_input_digest = compute_pe35_boundary_input_digest(pe35_input)
    pe36_input_digest = compute_pe36_boundary_input_digest(pe36_input)
    pe37_input_digest = compute_pe37_boundary_input_digest(pe37_boundary_input)

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
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        integration_id=integration_id,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe34_handoff=PE34_CONTRACT_VERSION,
            pe35_staleness=PE35_CONTRACT_VERSION,
            pe36_admission_presentation=PE36_CONTRACT_VERSION,
            pe37_traceability=PE37_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        pe34_handoff_input=pe34_handoff,
        pe35_boundary_input=pe35_input,
        pe36_boundary_input=pe36_input,
        pe37_traceability_boundary_input=pe37_boundary_input,
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
        proof_chain=proof_chain,
        safety_snapshot=default_minimal_safety_snapshot(),
    )
