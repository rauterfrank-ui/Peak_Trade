"""Bounded Futures Testnet reconciliation-review lifecycle integration (v0, PE-31).

Deterministic, offline, explicit-input-only contract binding a canonically verified
PE-26 preflight execution readiness assembly, PE-27 zero-order lifecycle integration,
PE-28 private-readonly lifecycle integration, PE-29 validate-only lifecycle integration,
PE-30 tiny-order lifecycle integration, and PE-21 position/order reconciliation plus
durable primary evidence integration to the PE-12 reconciliation_review lifecycle phase.

Static integration only — no network, testnet, runtime, credentials, orders, adapter calls,
exchange queries, operative reconciliation, evidence creation, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
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
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    CONTRACT_VERSION as PE21_CONTRACT_VERSION,
    ReconciliationPrimaryEvidenceIntegrationInput,
    compute_integration_input_digest as compute_pe21_integration_input_digest,
    compute_integration_proof_digest as compute_pe21_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe21_integration_input,
    evaluate_position_order_reconciliation_primary_evidence_integration,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
    compute_assembly_input_digest,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
    PRIMARY_EVIDENCE_OWNER,
    RECONCILIATION_OWNER,
)
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE28_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE30_CONTRACT_VERSION,
    TinyOrderLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe30_integration_input_digest,
    compute_integration_proof_digest as compute_pe30_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe30_integration_input,
    evaluate_tiny_order_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE29_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE27_CONTRACT_VERSION,
)

PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_RECONCILIATION_REVIEW_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
)
CONTRACT_VERSION = "bounded_futures_testnet_reconciliation_review_lifecycle_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_reconciliation_review_lifecycle_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

RECONCILIATION_REVIEW_MODE = "static_review_consistency_proof_only"
RECONCILIATION_REVIEW_OWNER = PHASE_CANONICAL_OWNERS[PHASE_RECONCILIATION_REVIEW]
PE26_ASSEMBLY_OWNER = PE26_CONTRACT_VERSION
PE27_INTEGRATION_OWNER = PE27_CONTRACT_VERSION
PE28_INTEGRATION_OWNER = PE28_CONTRACT_VERSION
PE29_INTEGRATION_OWNER = PE29_CONTRACT_VERSION
PE30_INTEGRATION_OWNER = PE30_CONTRACT_VERSION
PE21_INTEGRATION_OWNER = PE21_CONTRACT_VERSION

GLOBAL_RECONCILIATION_REVIEW_LIFECYCLE_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_RECONCILIATION_EXECUTED = False
OPERATIVE_ADAPTER_CALLED = False
EXCHANGE_API_CALLED = False
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
    "pe21_reconciliation_primary_evidence": PE21_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe26_assembly: str
    pe27_zero_order: str
    pe28_private_readonly: str
    pe29_validate_only: str
    pe30_tiny_order: str
    pe21_reconciliation_primary_evidence: str
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
class Pe30TinyOrderIntegrationProofBinding:
    integration_owner: str
    integration_input_digest: str
    integration_proof_digest: str
    pe30_integration_pass: bool
    tiny_order_lifecycle_eligibility: bool


@dataclass(frozen=True)
class Pe21ReconciliationPrimaryEvidenceIntegrationProofBinding:
    integration_owner: str
    integration_input_digest: str
    integration_proof_digest: str
    pe21_integration_pass: bool
    reconciled: bool
    durable_primary_evidence_binding_proven: bool
    reconciliation_result_digest: str


@dataclass(frozen=True)
class ReconciliationReviewProofBinding:
    reconciliation_review_owner: str
    reconciliation_owner: str
    primary_evidence_owner: str
    reconciliation_review_mode: str
    review_only: bool
    static_review_consistency_proven: bool
    manifest_verify_rc: int
    reconciliation_review_proof_digest: str
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
class IntegrationSafetySnapshot:
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    zero_order_authorized: bool
    private_readonly_authorized: bool
    validate_only_authorized: bool
    tiny_order_authorized: bool
    reconciliation_authorized: bool
    evidence_acceptance_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class ReconciliationReviewLifecycleIntegrationInput:
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
    pe30_tiny_order_integration_input: TinyOrderLifecycleIntegrationInput
    pe30_tiny_order_integration_proof: Pe30TinyOrderIntegrationProofBinding
    pe21_reconciliation_primary_evidence_integration_input: (
        ReconciliationPrimaryEvidenceIntegrationInput
    )
    pe21_reconciliation_primary_evidence_integration_proof: (
        Pe21ReconciliationPrimaryEvidenceIntegrationProofBinding
    )
    reconciliation_review_proof: ReconciliationReviewProofBinding
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


def _integration_input_dict(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
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
        "pe30_tiny_order_integration_input_digest": compute_pe30_integration_input_digest(
            integration_input.pe30_tiny_order_integration_input
        ),
        "pe30_tiny_order_integration_proof": asdict(
            integration_input.pe30_tiny_order_integration_proof
        ),
        "pe21_reconciliation_primary_evidence_integration_input_digest": (
            compute_pe21_integration_input_digest(
                integration_input.pe21_reconciliation_primary_evidence_integration_input
            )
        ),
        "pe21_reconciliation_primary_evidence_integration_proof": asdict(
            integration_input.pe21_reconciliation_primary_evidence_integration_proof
        ),
        "reconciliation_review_proof": asdict(integration_input.reconciliation_review_proof),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _reconciliation_review_proof_dict(binding: ReconciliationReviewProofBinding) -> dict[str, Any]:
    return {
        "account_state_queried": binding.account_state_queried,
        "adapter_called": binding.adapter_called,
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
        "primary_evidence_owner": binding.primary_evidence_owner,
        "reconciliation_owner": binding.reconciliation_owner,
        "reconciliation_review_mode": binding.reconciliation_review_mode,
        "reconciliation_review_owner": binding.reconciliation_review_owner,
        "request_count": binding.request_count,
        "review_only": binding.review_only,
        "runtime_started": binding.runtime_started,
        "secret_material_read": binding.secret_material_read,
        "secret_material_stored": binding.secret_material_stored,
        "static_review_consistency_proven": binding.static_review_consistency_proven,
        "subprocess_started": binding.subprocess_started,
        "testnet_started": binding.testnet_started,
    }


def serialize_reconciliation_review_proof_canonical(
    binding: ReconciliationReviewProofBinding,
) -> str:
    return json.dumps(
        _reconciliation_review_proof_dict(binding), sort_keys=True, separators=(",", ":")
    )


def compute_reconciliation_review_proof_digest(binding: ReconciliationReviewProofBinding) -> str:
    return hashlib.sha256(
        serialize_reconciliation_review_proof_canonical(binding).encode("utf-8")
    ).hexdigest()


def _integration_result_dict(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
    reconciliation_review_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> dict[str, Any]:
    matrix = integration_input.lifecycle_matrix_proof
    pe21_proof = integration_input.pe21_reconciliation_primary_evidence_integration_proof
    payload: dict[str, Any] = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "integration_id": integration_input.integration_id,
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe30_integration_proof_digest": (
            integration_input.pe30_tiny_order_integration_proof.integration_proof_digest
        ),
        "pe21_integration_proof_digest": pe21_proof.integration_proof_digest,
        "reconciliation_result_digest": pe21_proof.reconciliation_result_digest,
        "reconciliation_review_proof_digest": (
            integration_input.reconciliation_review_proof.reconciliation_review_proof_digest
        ),
        "reconciliation_review_lifecycle_eligibility_for_separate_operator_review": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe31_reconciliation_review_lifecycle_static_integration_proven": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe12_reconciliation_review_static_integration_proven": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "durable_primary_evidence_binding_proven": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
            and pe21_proof.durable_primary_evidence_binding_proven
        ),
        "global_reconciliation_review_lifecycle_readiness": (
            GLOBAL_RECONCILIATION_REVIEW_LIFECYCLE_READINESS
        ),
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_reconciliation_executed": OPERATIVE_RECONCILIATION_EXECUTED,
        "operative_adapter_called": OPERATIVE_ADAPTER_CALLED,
        "exchange_api_called": EXCHANGE_API_CALLED,
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
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
    *,
    reconciliation_review_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return json.dumps(
        _integration_result_dict(
            integration_input,
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review=(
                reconciliation_review_lifecycle_eligibility_for_separate_operator_review
            ),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
    *,
    reconciliation_review_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_integration_result_canonical(
            integration_input,
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review=(
                reconciliation_review_lifecycle_eligibility_for_separate_operator_review
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
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("zero_order_authorized", False),
        ("private_readonly_authorized", False),
        ("validate_only_authorized", False),
        ("tiny_order_authorized", False),
        ("reconciliation_authorized", False),
        ("evidence_acceptance_authorized", False),
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


def _validate_pe30_integration_proof(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe30_tiny_order_integration_proof
    pe30_input = integration_input.pe30_tiny_order_integration_input

    if proof.integration_owner != PE30_INTEGRATION_OWNER:
        fail_reasons.append(
            f"pe30_tiny_order_integration_proof: integration_owner must be "
            f"{PE30_INTEGRATION_OWNER!r}"
        )
    if not proof.integration_input_digest:
        fail_reasons.append("pe30_tiny_order_integration_proof: integration_input_digest required")
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe30_tiny_order_integration_proof: integration_input_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe30_integration_input_digest(pe30_input):
        fail_reasons.append("pe30_tiny_order_integration_proof: integration_input_digest mismatch")

    if not proof.integration_proof_digest:
        fail_reasons.append("pe30_tiny_order_integration_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe30_tiny_order_integration_proof: integration_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe30_integration_proof_digest(
            pe30_input,
            tiny_order_lifecycle_eligibility_for_separate_operator_review=True,
        )
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append(
                "pe30_tiny_order_integration_proof: integration_proof_digest mismatch"
            )

    if proof.pe30_integration_pass is not True:
        fail_reasons.append("pe30_tiny_order_integration_proof: pe30_integration_pass must be true")
    if proof.tiny_order_lifecycle_eligibility is not True:
        fail_reasons.append(
            "pe30_tiny_order_integration_proof: tiny_order_lifecycle_eligibility must be true"
        )

    pe30_result = evaluate_tiny_order_lifecycle_integration(pe30_input)
    if not pe30_result["integration_pass"]:
        fail_reasons.append("pe30_tiny_order_integration_input: PE-30 evaluation failed")
        fail_reasons.extend(
            f"pe30_tiny_order_integration_input: {reason}" for reason in pe30_result["fail_reasons"]
        )
    elif not pe30_result["tiny_order_lifecycle_eligibility_for_separate_operator_review"]:
        fail_reasons.append(
            "pe30_tiny_order_integration_input: tiny_order_lifecycle_eligibility required"
        )

    if pe30_input.source_revision != integration_input.source_revision:
        fail_reasons.append("pe30_tiny_order_integration_input: source_revision mismatch")
    if pe30_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append("pe30_tiny_order_integration_input: adapter_id mismatch")
    if pe30_input.instrument != integration_input.instrument:
        fail_reasons.append("pe30_tiny_order_integration_input: instrument mismatch")

    pe30_matrix = pe30_input.lifecycle_matrix_proof
    if pe30_matrix.assigned_lifecycle_phase != PHASE_TINY_ORDER:
        fail_reasons.append(
            f"pe30_tiny_order_integration_input: assigned_lifecycle_phase must be {PHASE_TINY_ORDER!r}"
        )

    pe30_assembly_digest = compute_assembly_input_digest(pe30_input.pe26_assembly_input)
    pe31_pe30_assembly_digest = compute_assembly_input_digest(
        integration_input.pe30_tiny_order_integration_input.pe26_assembly_input
    )
    if pe30_assembly_digest != pe31_pe30_assembly_digest:
        fail_reasons.append(
            "pe30_tiny_order_integration_input: pe26_assembly_input_digest mismatch"
        )

    return fail_reasons


def _validate_embedded_lifecycle_sequence(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> list[str]:
    """Validate canonical PE-27..PE-30 phase sequence inside embedded PE-30 input."""
    fail_reasons: list[str] = []
    pe30_input = integration_input.pe30_tiny_order_integration_input
    expected_phases = {
        "pe27": PHASE_ZERO_ORDER,
        "pe28": PHASE_PRIVATE_READONLY,
        "pe29": PHASE_VALIDATE_ONLY,
        "pe30": PHASE_TINY_ORDER,
    }
    actual_phases = {
        "pe27": pe30_input.pe27_zero_order_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe28": pe30_input.pe28_private_readonly_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe29": pe30_input.pe29_validate_only_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "pe30": pe30_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
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

    return fail_reasons


def _validate_pe21_integration_proof(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe21_reconciliation_primary_evidence_integration_proof
    pe21_input = integration_input.pe21_reconciliation_primary_evidence_integration_input

    if proof.integration_owner != PE21_INTEGRATION_OWNER:
        fail_reasons.append(
            f"pe21_reconciliation_primary_evidence_integration_proof: integration_owner must be "
            f"{PE21_INTEGRATION_OWNER!r}"
        )
    if not proof.integration_input_digest:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: integration_input_digest "
            "required"
        )
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: integration_input_digest must "
            "be 64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe21_integration_input_digest(pe21_input):
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: integration_input_digest "
            "mismatch"
        )

    if not proof.integration_proof_digest:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: integration_proof_digest "
            "required"
        )
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: integration_proof_digest "
            "must be 64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe21_integration_proof_digest(pe21_input)
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append(
                "pe21_reconciliation_primary_evidence_integration_proof: "
                "integration_proof_digest mismatch"
            )

    if proof.pe21_integration_pass is not True:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: pe21_integration_pass must "
            "be true"
        )
    if proof.reconciled is not True:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: reconciled must be true"
        )
    if proof.durable_primary_evidence_binding_proven is not True:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: "
            "durable_primary_evidence_binding_proven must be true"
        )

    if not proof.reconciliation_result_digest:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: "
            "reconciliation_result_digest required"
        )
    elif not _valid_sha256_digest(proof.reconciliation_result_digest):
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: "
            "reconciliation_result_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.reconciliation_result_digest != pe21_input.reconciliation_binding.result_digest:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_proof: "
            "reconciliation_result_digest mismatch"
        )

    pe21_result = evaluate_position_order_reconciliation_primary_evidence_integration(pe21_input)
    if not pe21_result["integration_pass"]:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_input: PE-21 evaluation failed"
        )
        fail_reasons.extend(
            f"pe21_reconciliation_primary_evidence_integration_input: {reason}"
            for reason in pe21_result["fail_reasons"]
        )
    elif not pe21_result["reconciled"]:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_input: reconciled required"
        )
    elif not pe21_result["durable_primary_evidence_binding_proven"]:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_input: "
            "durable_primary_evidence_binding_proven required"
        )

    if pe21_input.source_revision != integration_input.source_revision:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_input: source_revision mismatch"
        )
    if pe21_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_input: adapter_id mismatch"
        )
    if pe21_input.instrument != integration_input.instrument:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_input: instrument mismatch"
        )

    pe21_matrix = pe21_input.lifecycle_matrix_proof
    if pe21_matrix.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            "pe21_reconciliation_primary_evidence_integration_input: assigned_lifecycle_phase "
            f"must be {PHASE_RECONCILIATION_REVIEW!r}"
        )

    return fail_reasons


def _validate_reconciliation_review_proof(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    binding = integration_input.reconciliation_review_proof
    pe21_input = integration_input.pe21_reconciliation_primary_evidence_integration_input

    if binding.reconciliation_review_owner != RECONCILIATION_REVIEW_OWNER:
        fail_reasons.append(
            f"reconciliation_review_proof: reconciliation_review_owner must be "
            f"{RECONCILIATION_REVIEW_OWNER!r}"
        )
    if binding.reconciliation_owner != RECONCILIATION_OWNER:
        fail_reasons.append(
            f"reconciliation_review_proof: reconciliation_owner must be {RECONCILIATION_OWNER!r}"
        )
    if binding.primary_evidence_owner != PRIMARY_EVIDENCE_OWNER:
        fail_reasons.append(
            f"reconciliation_review_proof: primary_evidence_owner must be "
            f"{PRIMARY_EVIDENCE_OWNER!r}"
        )
    if binding.reconciliation_review_mode != RECONCILIATION_REVIEW_MODE:
        fail_reasons.append(
            f"reconciliation_review_proof: reconciliation_review_mode must be "
            f"{RECONCILIATION_REVIEW_MODE!r}"
        )
    if binding.review_only is not True:
        fail_reasons.append("reconciliation_review_proof: review_only must be true")
    if binding.static_review_consistency_proven is not True:
        fail_reasons.append(
            "reconciliation_review_proof: static_review_consistency_proven must be true"
        )
    if binding.manifest_verify_rc != 0:
        fail_reasons.append("reconciliation_review_proof: manifest_verify_rc must be 0")
    elif binding.manifest_verify_rc != pe21_input.primary_evidence_binding.manifest_verify_rc:
        fail_reasons.append(
            "reconciliation_review_proof: manifest_verify_rc mismatch with PE-21 binding"
        )

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
            fail_reasons.append(f"reconciliation_review_proof: {field_name} must be 0")

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
            fail_reasons.append(f"reconciliation_review_proof: {field_name} must be false")

    if not binding.reconciliation_review_proof_digest:
        fail_reasons.append(
            "reconciliation_review_proof: reconciliation_review_proof_digest required"
        )
    elif not _valid_sha256_digest(binding.reconciliation_review_proof_digest):
        fail_reasons.append(
            "reconciliation_review_proof: reconciliation_review_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif binding.reconciliation_review_proof_digest != compute_reconciliation_review_proof_digest(
        binding
    ):
        fail_reasons.append(
            "reconciliation_review_proof: reconciliation_review_proof_digest mismatch"
        )

    return fail_reasons


def validate_reconciliation_review_lifecycle_integration_input(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-31 integration input bindings."""
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
    if matrix.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be "
            f"{PHASE_RECONCILIATION_REVIEW!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")

    before = integration_input.lifecycle_state_before
    after = integration_input.declared_lifecycle_state_after
    if before.assigned_lifecycle_phase != PHASE_TINY_ORDER:
        fail_reasons.append(
            f"lifecycle_state_before: assigned_lifecycle_phase must be {PHASE_TINY_ORDER!r}"
        )
    if after.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            f"declared_lifecycle_state_after: assigned_lifecycle_phase must be "
            f"{PHASE_RECONCILIATION_REVIEW!r}"
        )
    if before.adapter_id != integration_input.adapter_id:
        fail_reasons.append("lifecycle_state_before: adapter_id mismatch")
    if after.adapter_id != integration_input.adapter_id:
        fail_reasons.append("declared_lifecycle_state_after: adapter_id mismatch")
    if matrix.lifecycle_state_digest != after.state_digest:
        fail_reasons.append(
            "lifecycle_matrix_proof: lifecycle_state_digest mismatch with declared after state"
        )

    fail_reasons.extend(_validate_pe30_integration_proof(integration_input))
    fail_reasons.extend(_validate_embedded_lifecycle_sequence(integration_input))
    fail_reasons.extend(_validate_pe21_integration_proof(integration_input))
    fail_reasons.extend(_validate_reconciliation_review_proof(integration_input))
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_reconciliation_review_lifecycle_compatibility(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 reconciliation_review phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_RECONCILIATION_REVIEW]
    snapshot = integration_input.safety_snapshot
    review_proof = integration_input.reconciliation_review_proof

    if descriptor.network_phase and snapshot.network_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: network_allowed true for reconciliation_review"
        )
    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append(
            "lifecycle/gate contradiction: orders_allowed true for reconciliation_review"
        )
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for reconciliation_review"
        )
    if snapshot.live_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: live_authorized true for reconciliation_review"
        )
    if snapshot.zero_order_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: zero_order_authorized true for reconciliation_review"
        )
    if snapshot.private_readonly_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: private_readonly_authorized true for "
            "reconciliation_review"
        )
    if snapshot.validate_only_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: validate_only_authorized true for reconciliation_review"
        )
    if snapshot.tiny_order_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: tiny_order_authorized true for reconciliation_review"
        )
    if snapshot.reconciliation_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: reconciliation_authorized true for reconciliation_review"
        )
    if snapshot.evidence_acceptance_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: evidence_acceptance_authorized true for "
            "reconciliation_review"
        )
    if review_proof.network_used:
        fail_reasons.append("review-only proof requires network_used false")
    if not review_proof.review_only or not review_proof.static_review_consistency_proven:
        fail_reasons.append("static reconciliation review proof not established")

    return fail_reasons


def evaluate_reconciliation_review_lifecycle_integration(
    integration_input: ReconciliationReviewLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_pe30_integration_proof_digest: str | None = None,
    expected_pe21_integration_proof_digest: str | None = None,
    expected_reconciliation_result_digest: str | None = None,
    expected_reconciliation_review_proof_digest: str | None = None,
    loose_boolean_eligibility: bool = False,
    dirty_source_state: bool = False,
    execution_authorized: bool = False,
    live_authorized: bool = False,
    zero_order_authorized: bool = False,
    private_readonly_authorized: bool = False,
    validate_only_authorized: bool = False,
    tiny_order_authorized: bool = False,
    reconciliation_authorized: bool = False,
    evidence_acceptance_authorized: bool = False,
    network_allowed: bool = False,
    credentials_allowed: bool = False,
    orders_allowed: bool = False,
    runtime_started: bool = False,
    adapter_called: bool = False,
    exchange_api_called_override: bool = False,
    account_state_queried_override: bool = False,
    new_evidence_generation: bool = False,
    existing_evidence_mutation: bool = False,
    unknown_lifecycle_state: str | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-31 reconciliation-review lifecycle static integration proof."""
    fail_reasons = validate_reconciliation_review_lifecycle_integration_input(integration_input)

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = integration_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_pe30_integration_proof_digest is not None:
        if (
            integration_input.pe30_tiny_order_integration_proof.integration_proof_digest
            != expected_pe30_integration_proof_digest
        ):
            fail_reasons.append(
                "pe30_tiny_order_integration_proof: integration_proof_digest mismatch"
            )

    if expected_pe21_integration_proof_digest is not None:
        if (
            integration_input.pe21_reconciliation_primary_evidence_integration_proof.integration_proof_digest
            != expected_pe21_integration_proof_digest
        ):
            fail_reasons.append(
                "pe21_reconciliation_primary_evidence_integration_proof: "
                "integration_proof_digest mismatch"
            )

    if expected_reconciliation_result_digest is not None:
        if (
            integration_input.pe21_reconciliation_primary_evidence_integration_proof.reconciliation_result_digest
            != expected_reconciliation_result_digest
        ):
            fail_reasons.append("reconciliation_result_digest mismatch")

    if expected_reconciliation_review_proof_digest is not None:
        if (
            integration_input.reconciliation_review_proof.reconciliation_review_proof_digest
            != expected_reconciliation_review_proof_digest
        ):
            fail_reasons.append("reconciliation_review_proof: proof_digest mismatch")

    if loose_boolean_eligibility:
        fail_reasons.append(
            "loose_boolean_eligibility=true without canonical proof is insufficient"
        )
    if dirty_source_state:
        fail_reasons.append("dirty_source_state=true is not allowed")
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

    if unknown_lifecycle_state is not None:
        if unknown_lifecycle_state not in LIFECYCLE_PHASE_DESCRIPTORS:
            fail_reasons.append(f"unknown lifecycle state: {unknown_lifecycle_state!r}")

    if not fail_reasons:
        fail_reasons.extend(
            _validate_reconciliation_review_lifecycle_compatibility(integration_input)
        )

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    reconciliation_review_lifecycle_eligibility_for_separate_operator_review = integration_pass

    pe21_proof = integration_input.pe21_reconciliation_primary_evidence_integration_proof
    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                reconciliation_review_lifecycle_eligibility_for_separate_operator_review=(
                    reconciliation_review_lifecycle_eligibility_for_separate_operator_review
                ),
            )
            if integration_pass
            else None
        ),
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe30_integration_proof_digest": (
            integration_input.pe30_tiny_order_integration_proof.integration_proof_digest
        ),
        "pe21_integration_proof_digest": pe21_proof.integration_proof_digest,
        "reconciliation_result_digest": pe21_proof.reconciliation_result_digest,
        "reconciliation_review_proof_digest": (
            integration_input.reconciliation_review_proof.reconciliation_review_proof_digest
        ),
        "reconciliation_review_lifecycle_eligibility_for_separate_operator_review": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe31_reconciliation_review_lifecycle_static_integration_proven": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "pe12_reconciliation_review_static_integration_proven": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
        ),
        "durable_primary_evidence_binding_proven": (
            reconciliation_review_lifecycle_eligibility_for_separate_operator_review
            and pe21_proof.durable_primary_evidence_binding_proven
        ),
        "global_reconciliation_review_lifecycle_readiness": (
            GLOBAL_RECONCILIATION_REVIEW_LIFECYCLE_READINESS
        ),
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_reconciliation_executed": OPERATIVE_RECONCILIATION_EXECUTED,
        "operative_adapter_called": OPERATIVE_ADAPTER_CALLED,
        "exchange_api_called": EXCHANGE_API_CALLED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": True,
        "ready_for_operator_arming": False,
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
        "operator_closure_authorized": False,
        "operator_decision_authorized": False,
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


def default_minimal_reconciliation_review_proof(
    pe21_input: ReconciliationPrimaryEvidenceIntegrationInput,
    *,
    reconciliation_review_proof_digest: str | None = None,
) -> ReconciliationReviewProofBinding:
    binding = ReconciliationReviewProofBinding(
        reconciliation_review_owner=RECONCILIATION_REVIEW_OWNER,
        reconciliation_owner=RECONCILIATION_OWNER,
        primary_evidence_owner=PRIMARY_EVIDENCE_OWNER,
        reconciliation_review_mode=RECONCILIATION_REVIEW_MODE,
        review_only=True,
        static_review_consistency_proven=True,
        manifest_verify_rc=pe21_input.primary_evidence_binding.manifest_verify_rc,
        reconciliation_review_proof_digest="",
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
    digest = reconciliation_review_proof_digest or compute_reconciliation_review_proof_digest(
        binding
    )
    return ReconciliationReviewProofBinding(
        reconciliation_review_owner=binding.reconciliation_review_owner,
        reconciliation_owner=binding.reconciliation_owner,
        primary_evidence_owner=binding.primary_evidence_owner,
        reconciliation_review_mode=binding.reconciliation_review_mode,
        review_only=binding.review_only,
        static_review_consistency_proven=binding.static_review_consistency_proven,
        manifest_verify_rc=binding.manifest_verify_rc,
        reconciliation_review_proof_digest=digest,
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
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        zero_order_authorized=False,
        private_readonly_authorized=False,
        validate_only_authorized=False,
        tiny_order_authorized=False,
        reconciliation_authorized=False,
        evidence_acceptance_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def default_minimal_pe30_integration_proof(
    pe30_input: TinyOrderLifecycleIntegrationInput,
) -> Pe30TinyOrderIntegrationProofBinding:
    return Pe30TinyOrderIntegrationProofBinding(
        integration_owner=PE30_INTEGRATION_OWNER,
        integration_input_digest=compute_pe30_integration_input_digest(pe30_input),
        integration_proof_digest=compute_pe30_integration_proof_digest(
            pe30_input,
            tiny_order_lifecycle_eligibility_for_separate_operator_review=True,
        ),
        pe30_integration_pass=True,
        tiny_order_lifecycle_eligibility=True,
    )


def default_minimal_pe21_integration_proof(
    pe21_input: ReconciliationPrimaryEvidenceIntegrationInput,
) -> Pe21ReconciliationPrimaryEvidenceIntegrationProofBinding:
    return Pe21ReconciliationPrimaryEvidenceIntegrationProofBinding(
        integration_owner=PE21_INTEGRATION_OWNER,
        integration_input_digest=compute_pe21_integration_input_digest(pe21_input),
        integration_proof_digest=compute_pe21_integration_proof_digest(pe21_input),
        pe21_integration_pass=True,
        reconciled=True,
        durable_primary_evidence_binding_proven=True,
        reconciliation_result_digest=pe21_input.reconciliation_binding.result_digest,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    integration_id: str = "reconciliation-review-lifecycle-integration-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> ReconciliationReviewLifecycleIntegrationInput:
    """Minimal valid futures-generic PE-31 integration input for offline tests."""
    pe30_input = default_minimal_pe30_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
    )
    pe21_input = default_minimal_pe21_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=lifecycle_state_digest,
    )
    after_state = pe21_input.adapter_lifecycle_state
    state_digest = after_state.state_digest
    matrix_digest = compute_lifecycle_matrix_digest()
    review_proof = default_minimal_reconciliation_review_proof(pe21_input)

    return ReconciliationReviewLifecycleIntegrationInput(
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
            pe21_reconciliation_primary_evidence=PE21_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            lifecycle_state_digest=state_digest,
        ),
        lifecycle_state_before=LifecycleStateBinding(
            state_id="lifecycle-before-tiny-order",
            state_digest=pe30_input.lifecycle_matrix_proof.lifecycle_state_digest,
            assigned_lifecycle_phase=PHASE_TINY_ORDER,
            adapter_id=adapter_id,
        ),
        declared_lifecycle_state_after=LifecycleStateBinding(
            state_id=after_state.state_id,
            state_digest=after_state.state_digest,
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            adapter_id=adapter_id,
        ),
        pe30_tiny_order_integration_input=pe30_input,
        pe30_tiny_order_integration_proof=default_minimal_pe30_integration_proof(pe30_input),
        pe21_reconciliation_primary_evidence_integration_input=pe21_input,
        pe21_reconciliation_primary_evidence_integration_proof=default_minimal_pe21_integration_proof(
            pe21_input
        ),
        reconciliation_review_proof=review_proof,
        safety_snapshot=default_minimal_safety_snapshot(),
    )
