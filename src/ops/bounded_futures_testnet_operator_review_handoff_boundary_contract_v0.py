"""Bounded Futures Testnet operator-review handoff boundary (v0, PE-34).

Deterministic, offline, explicit-input-only fail-closed boundary binding PE-33
cross-slice proof coherence, PE-19 undecided review input, PE-20 undecided
package eligibility, and PE-25 non-operative cross-slice closure bindings.

Static boundary only — no operator review, no operator decision, no operative
proof-package issuance, no closure execution, no authority lift, network,
testnet, runtime, credentials, orders, or exchange access.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
    CONTRACT_VERSION as PE33_CONTRACT_VERSION,
    COHERENCE_OWNER as PE33_COHERENCE_OWNER,
    CrossSliceProofCoherenceIntegrationInput,
    compute_integration_input_digest as compute_pe33_integration_input_digest,
    compute_integration_proof_digest as compute_pe33_integration_proof_digest,
    evaluate_cross_slice_proof_coherence_integration,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
    PACKAGE_SCHEMA_VERSION as PE20_PACKAGE_SCHEMA_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    EXPECTED_OPERATOR_NAME,
    PreflightOperatorReviewInput,
    compute_review_input_digest,
    validate_review_input,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_HANDOFF_BOUNDARY_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_operator_review_handoff_boundary.v0"
SERIALIZATION_VERSION = "bounded_futures_testnet_operator_review_handoff_boundary.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

HANDOFF_MODE = "static_operator_review_handoff_boundary_for_separate_operator_review_only"
HANDOFF_OWNER = CONTRACT_VERSION

CONTRACT_IMPLEMENTATION_ONLY = True
OPERATOR_REVIEW_EXECUTED = False
OPERATOR_DECISION_SELECTED = False
OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED = False
OPERATOR_CLOSURE_EXECUTED = False
SECOND_ASSEMBLY_CREATED = False
SECOND_READINESS_SURFACE_CREATED = False
SECOND_OPERATOR_REVIEW_SURFACE_CREATED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

ALLOWED_LATER_DECISIONS = frozenset(
    {
        "approve_for_separate_next_phase_review",
        "reject",
        "request_changes",
    }
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe19_operator_review": PE19_CONTRACT_VERSION,
    "pe20_review_proof_package": PE20_CONTRACT_VERSION,
    "pe25_operator_closure": PE25_CONTRACT_VERSION,
    "pe33_cross_slice_proof_coherence": PE33_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe19_operator_review: str
    pe20_review_proof_package: str
    pe25_operator_closure: str
    pe33_cross_slice_proof_coherence: str
    integration: str


@dataclass(frozen=True)
class Pe33CoherenceProofBinding:
    coherence_owner: str
    source_revision: str
    integration_input_digest: str
    integration_proof_digest: str
    cross_slice_proof_coherence_for_separate_operator_review: bool
    static_pe12_lifecycle_chain_complete: bool
    integration_pass: bool


@dataclass(frozen=True)
class Pe19UndecidedReviewInputBinding:
    review_input_owner: str
    source_revision: str
    review_input: PreflightOperatorReviewInput
    pe33_integration_proof_digest: str
    operator_name_legibility: str | None = None


@dataclass(frozen=True)
class Pe20UndecidedPackageEligibilityBinding:
    package_owner: str
    source_revision: str
    review_input_digest: str
    package_schema_version: str
    undecided_package_eligibility: bool
    operative_decision_issued: bool
    decision_record_digest: str | None = None
    package_id: str | None = None


@dataclass(frozen=True)
class Pe25CrossSliceClosureBinding:
    closure_owner: str
    source_revision: str
    closure_result_digest: str
    pe33_pe25_slot_digest: str
    operative_operator_closure_executed: bool
    operator_closure_static_complete: bool


@dataclass(frozen=True)
class HandoffBoundarySafetySnapshot:
    preflight_remains_blocked: bool
    global_blocker_lift_authorized: bool
    preflight_lift_authorized: bool
    ready_for_operator_arming: bool
    readiness_decision_authorized: bool
    operator_review_authorized: bool
    operator_decision_authorized: bool
    operator_closure_authorized: bool
    execution_authorized: bool
    zero_order_authorized: bool
    private_readonly_authorized: bool
    validate_only_authorized: bool
    tiny_order_authorized: bool
    reconciliation_authorized: bool
    evidence_acceptance_authorized: bool
    pilot_start_authorized: bool
    promotion_authorized: bool
    live_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class OperatorReviewHandoffBoundaryInput:
    source_revision: str
    repository_identity: str
    handoff_id: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    pe33_coherence_proof: Pe33CoherenceProofBinding
    pe33_integration_input: CrossSliceProofCoherenceIntegrationInput | None
    pe19_undecided_review_input: Pe19UndecidedReviewInputBinding
    pe20_undecided_package_eligibility: Pe20UndecidedPackageEligibilityBinding
    pe25_cross_slice_closure: Pe25CrossSliceClosureBinding
    safety_snapshot: HandoffBoundarySafetySnapshot
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


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


def _validate_safety_snapshot(snapshot: HandoffBoundarySafetySnapshot) -> list[str]:
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
        ("zero_order_authorized", False),
        ("private_readonly_authorized", False),
        ("validate_only_authorized", False),
        ("tiny_order_authorized", False),
        ("reconciliation_authorized", False),
        ("evidence_acceptance_authorized", False),
        ("pilot_start_authorized", False),
        ("promotion_authorized", False),
        ("live_authorized", False),
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


def _validate_pe33_coherence_proof(binding: Pe33CoherenceProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if binding.coherence_owner != PE33_COHERENCE_OWNER:
        fail_reasons.append(
            f"pe33_coherence_proof: coherence_owner must be {PE33_COHERENCE_OWNER!r}"
        )
    if not binding.source_revision:
        fail_reasons.append("pe33_coherence_proof: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append(
            "pe33_coherence_proof: source_revision must be full 40-char lowercase commit SHA"
        )
    if not binding.integration_input_digest:
        fail_reasons.append("pe33_coherence_proof: integration_input_digest required")
    elif not _valid_sha256_digest(binding.integration_input_digest):
        fail_reasons.append(
            "pe33_coherence_proof: integration_input_digest must be 64-char lowercase sha256 hex"
        )
    if not binding.integration_proof_digest:
        fail_reasons.append("pe33_coherence_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(binding.integration_proof_digest):
        fail_reasons.append(
            "pe33_coherence_proof: integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    if binding.integration_pass is not True:
        fail_reasons.append("pe33_coherence_proof: integration_pass must be true")
    if binding.cross_slice_proof_coherence_for_separate_operator_review is not True:
        fail_reasons.append(
            "pe33_coherence_proof: cross_slice_proof_coherence_for_separate_operator_review must be true"
        )
    if binding.static_pe12_lifecycle_chain_complete is not True:
        fail_reasons.append(
            "pe33_coherence_proof: static_pe12_lifecycle_chain_complete must be true"
        )
    return fail_reasons


def _validate_pe33_integration_input_coherence(
    binding: Pe33CoherenceProofBinding,
    integration_input: CrossSliceProofCoherenceIntegrationInput | None,
) -> list[str]:
    fail_reasons: list[str] = []
    if integration_input is None:
        return fail_reasons

    if integration_input.source_revision != binding.source_revision:
        fail_reasons.append("pe33_integration_input: source_revision mismatch with coherence proof")

    pe33_result = evaluate_cross_slice_proof_coherence_integration(integration_input)
    if not pe33_result["integration_pass"]:
        fail_reasons.append("pe33_integration_input: PE-33 integration_pass false")
    if not pe33_result["cross_slice_proof_coherence_for_separate_operator_review"]:
        fail_reasons.append(
            "pe33_integration_input: cross_slice_proof_coherence_for_separate_operator_review false"
        )

    computed_input_digest = compute_pe33_integration_input_digest(integration_input)
    if computed_input_digest != binding.integration_input_digest:
        fail_reasons.append("pe33_integration_input: integration_input_digest mismatch")

    computed_proof_digest = compute_pe33_integration_proof_digest(
        integration_input,
        cross_slice_proof_coherence_for_separate_operator_review=True,
    )
    if computed_proof_digest != binding.integration_proof_digest:
        fail_reasons.append("pe33_integration_input: integration_proof_digest mismatch")

    return fail_reasons


def _validate_pe19_undecided_review_input(
    binding: Pe19UndecidedReviewInputBinding,
    *,
    canonical_source_revision: str,
    expected_pe33_proof_digest: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.review_input_owner != PE19_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe19_undecided_review_input: review_input_owner must be {PE19_CONTRACT_VERSION!r}"
        )
    if not binding.source_revision:
        fail_reasons.append("pe19_undecided_review_input: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append(
            "pe19_undecided_review_input: source_revision must be full 40-char lowercase commit SHA"
        )
    elif binding.source_revision != canonical_source_revision:
        fail_reasons.append("pe19_undecided_review_input: source_revision mismatch")

    if not binding.pe33_integration_proof_digest:
        fail_reasons.append("pe19_undecided_review_input: pe33_integration_proof_digest required")
    elif not _valid_sha256_digest(binding.pe33_integration_proof_digest):
        fail_reasons.append(
            "pe19_undecided_review_input: pe33_integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.pe33_integration_proof_digest != expected_pe33_proof_digest:
        fail_reasons.append("pe19_undecided_review_input: pe33_integration_proof_digest mismatch")

    review_input = binding.review_input
    if review_input.source_revision != canonical_source_revision:
        fail_reasons.append("pe19_undecided_review_input: review_input source_revision mismatch")

    fail_reasons.extend(validate_review_input(review_input))

    if binding.operator_name_legibility is not None:
        if binding.operator_name_legibility != EXPECTED_OPERATOR_NAME:
            fail_reasons.append(
                f"pe19_undecided_review_input: operator_name_legibility must be {EXPECTED_OPERATOR_NAME!r}"
            )

    return fail_reasons


def _validate_pe20_undecided_package_eligibility(
    binding: Pe20UndecidedPackageEligibilityBinding,
    *,
    canonical_source_revision: str,
    expected_review_input_digest: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.package_owner != PE20_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe20_undecided_package_eligibility: package_owner must be {PE20_CONTRACT_VERSION!r}"
        )
    if not binding.source_revision:
        fail_reasons.append("pe20_undecided_package_eligibility: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append(
            "pe20_undecided_package_eligibility: source_revision must be full 40-char lowercase commit SHA"
        )
    elif binding.source_revision != canonical_source_revision:
        fail_reasons.append("pe20_undecided_package_eligibility: source_revision mismatch")

    if not binding.review_input_digest:
        fail_reasons.append("pe20_undecided_package_eligibility: review_input_digest required")
    elif not _valid_sha256_digest(binding.review_input_digest):
        fail_reasons.append(
            "pe20_undecided_package_eligibility: review_input_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.review_input_digest != expected_review_input_digest:
        fail_reasons.append("pe20_undecided_package_eligibility: review_input_digest mismatch")

    if binding.package_schema_version != PE20_PACKAGE_SCHEMA_VERSION:
        fail_reasons.append(
            f"pe20_undecided_package_eligibility: package_schema_version must be {PE20_PACKAGE_SCHEMA_VERSION!r}"
        )

    if binding.undecided_package_eligibility is not True:
        fail_reasons.append(
            "pe20_undecided_package_eligibility: undecided_package_eligibility must be true"
        )
    if binding.operative_decision_issued is not False:
        fail_reasons.append(
            "pe20_undecided_package_eligibility: operative_decision_issued must be false"
        )
    if binding.decision_record_digest:
        fail_reasons.append(
            "pe20_undecided_package_eligibility: decision_record_digest must be absent for undecided handoff"
        )
    if binding.package_id is not None and not _valid_sha256_digest(binding.package_id):
        fail_reasons.append(
            "pe20_undecided_package_eligibility: package_id must be 64-char lowercase sha256 hex when present"
        )

    return fail_reasons


def _validate_pe25_cross_slice_closure(
    binding: Pe25CrossSliceClosureBinding,
    *,
    canonical_source_revision: str,
    expected_pe25_slot_digest: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.closure_owner != PE25_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe25_cross_slice_closure: closure_owner must be {PE25_CONTRACT_VERSION!r}"
        )
    if not binding.source_revision:
        fail_reasons.append("pe25_cross_slice_closure: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append(
            "pe25_cross_slice_closure: source_revision must be full 40-char lowercase commit SHA"
        )
    elif binding.source_revision != canonical_source_revision:
        fail_reasons.append("pe25_cross_slice_closure: source_revision mismatch")

    if not binding.closure_result_digest:
        fail_reasons.append("pe25_cross_slice_closure: closure_result_digest required")
    elif not _valid_sha256_digest(binding.closure_result_digest):
        fail_reasons.append(
            "pe25_cross_slice_closure: closure_result_digest must be 64-char lowercase sha256 hex"
        )
    if not binding.pe33_pe25_slot_digest:
        fail_reasons.append("pe25_cross_slice_closure: pe33_pe25_slot_digest required")
    elif not _valid_sha256_digest(binding.pe33_pe25_slot_digest):
        fail_reasons.append(
            "pe25_cross_slice_closure: pe33_pe25_slot_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.pe33_pe25_slot_digest != expected_pe25_slot_digest:
        fail_reasons.append("pe25_cross_slice_closure: pe33_pe25_slot_digest mismatch")
    if binding.closure_result_digest and binding.closure_result_digest != expected_pe25_slot_digest:
        fail_reasons.append(
            "pe25_cross_slice_closure: closure_result_digest mismatch with PE-33 pe25 slot"
        )

    if binding.operative_operator_closure_executed is not False:
        fail_reasons.append(
            "pe25_cross_slice_closure: operative_operator_closure_executed must be false"
        )
    if binding.operator_closure_static_complete is not True:
        fail_reasons.append(
            "pe25_cross_slice_closure: operator_closure_static_complete must be true"
        )

    return fail_reasons


def _pe25_slot_digest_from_integration_input(
    integration_input: CrossSliceProofCoherenceIntegrationInput | None,
) -> str | None:
    if integration_input is None:
        return None
    for slot in integration_input.proof_slots:
        if slot.slot_id == "pe25":
            return slot.proof_digest
    return None


def validate_operator_review_handoff_boundary_input(
    boundary_input: OperatorReviewHandoffBoundaryInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-34 operator-review handoff boundary bindings."""
    fail_reasons: list[str] = []

    if not boundary_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(boundary_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not boundary_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif boundary_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")
    if not boundary_input.handoff_id:
        fail_reasons.append("handoff_id required")
    if not boundary_input.adapter_id:
        fail_reasons.append("adapter_id required")

    fail_reasons.extend(
        _validate_instrument_scope(boundary_input.instrument, boundary_input.market_type)
    )

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(boundary_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(f"contract_versions: {field_name} must be {expected!r}")

    pe33_proof = boundary_input.pe33_coherence_proof
    fail_reasons.extend(_validate_pe33_coherence_proof(pe33_proof))
    if pe33_proof.source_revision != boundary_input.source_revision:
        fail_reasons.append("pe33_coherence_proof: source_revision mismatch with boundary input")

    fail_reasons.extend(
        _validate_pe33_integration_input_coherence(
            pe33_proof,
            boundary_input.pe33_integration_input,
        )
    )

    pe25_slot_digest = _pe25_slot_digest_from_integration_input(
        boundary_input.pe33_integration_input
    )
    if pe25_slot_digest is None:
        pe25_slot_digest = boundary_input.pe25_cross_slice_closure.pe33_pe25_slot_digest

    review_input_binding = boundary_input.pe19_undecided_review_input
    fail_reasons.extend(
        _validate_pe19_undecided_review_input(
            review_input_binding,
            canonical_source_revision=boundary_input.source_revision,
            expected_pe33_proof_digest=pe33_proof.integration_proof_digest,
        )
    )

    review_input_digest = compute_review_input_digest(review_input_binding.review_input)
    fail_reasons.extend(
        _validate_pe20_undecided_package_eligibility(
            boundary_input.pe20_undecided_package_eligibility,
            canonical_source_revision=boundary_input.source_revision,
            expected_review_input_digest=review_input_digest,
        )
    )

    fail_reasons.extend(
        _validate_pe25_cross_slice_closure(
            boundary_input.pe25_cross_slice_closure,
            canonical_source_revision=boundary_input.source_revision,
            expected_pe25_slot_digest=pe25_slot_digest,
        )
    )

    fail_reasons.extend(_validate_safety_snapshot(boundary_input.safety_snapshot))

    if boundary_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if boundary_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if boundary_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _boundary_input_dict(boundary_input: OperatorReviewHandoffBoundaryInput) -> dict[str, Any]:
    pe19 = boundary_input.pe19_undecided_review_input
    return {
        "boundary_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": boundary_input.source_revision,
        "repository_identity": boundary_input.repository_identity,
        "handoff_id": boundary_input.handoff_id,
        "adapter_id": boundary_input.adapter_id,
        "instrument": boundary_input.instrument,
        "market_type": boundary_input.market_type,
        "contract_versions": asdict(boundary_input.contract_versions),
        "pe33_coherence_proof": asdict(boundary_input.pe33_coherence_proof),
        "pe33_integration_input_digest": (
            compute_pe33_integration_input_digest(boundary_input.pe33_integration_input)
            if boundary_input.pe33_integration_input is not None
            else boundary_input.pe33_coherence_proof.integration_input_digest
        ),
        "pe19_undecided_review_input": {
            "review_input_owner": pe19.review_input_owner,
            "source_revision": pe19.source_revision,
            "review_input_digest": compute_review_input_digest(pe19.review_input),
            "pe33_integration_proof_digest": pe19.pe33_integration_proof_digest,
            "operator_name_legibility": pe19.operator_name_legibility,
        },
        "pe20_undecided_package_eligibility": asdict(
            boundary_input.pe20_undecided_package_eligibility
        ),
        "pe25_cross_slice_closure": asdict(boundary_input.pe25_cross_slice_closure),
        "safety_snapshot": asdict(boundary_input.safety_snapshot),
        "futures_only": boundary_input.futures_only,
        "environment": boundary_input.environment,
        "non_authorizing": boundary_input.non_authorizing,
    }


def serialize_boundary_input_canonical(
    boundary_input: OperatorReviewHandoffBoundaryInput,
) -> str:
    return json.dumps(
        _boundary_input_dict(boundary_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_boundary_input_digest(
    boundary_input: OperatorReviewHandoffBoundaryInput,
) -> str:
    return hashlib.sha256(
        serialize_boundary_input_canonical(boundary_input).encode("utf-8")
    ).hexdigest()


def compute_boundary_result_digest(
    boundary_input: OperatorReviewHandoffBoundaryInput,
    *,
    operator_review_handoff_boundary_satisfied: bool,
) -> str:
    payload = {
        "boundary_contract_version": CONTRACT_VERSION,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "handoff_mode": HANDOFF_MODE,
        "handoff_owner": HANDOFF_OWNER,
        "hash_algorithm": HASH_ALGORITHM,
        "operator_review_handoff_boundary_satisfied": operator_review_handoff_boundary_satisfied,
        "package_marker": PACKAGE_MARKER,
        "pe33_integration_proof_digest": boundary_input.pe33_coherence_proof.integration_proof_digest,
        "pe19_review_input_digest": compute_review_input_digest(
            boundary_input.pe19_undecided_review_input.review_input
        ),
        "pe25_closure_result_digest": boundary_input.pe25_cross_slice_closure.closure_result_digest,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": boundary_input.source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def evaluate_operator_review_handoff_boundary(
    boundary_input: OperatorReviewHandoffBoundaryInput,
    *,
    expected_source_revision: str | None = None,
    loose_boolean_eligibility: bool = False,
    selected_decision: str | None = None,
    default_approve: bool = False,
    implicit_approve: bool = False,
    unknown_decision_state: str | None = None,
    operative_decision_issued: bool = False,
    operative_closure_executed: bool = False,
    extra_proof_slots: tuple[str, ...] = (),
    extra_decision_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Evaluate explicit PE-34 handoff boundary; never grants authority or selects decisions."""
    fail_reasons = validate_operator_review_handoff_boundary_input(boundary_input)

    if expected_source_revision is not None:
        if boundary_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    if loose_boolean_eligibility:
        fail_reasons.append("loose boolean eligibility cannot replace proof digest bindings")

    if selected_decision is not None:
        fail_reasons.append(
            f"selected_decision {selected_decision!r} is not allowed at handoff boundary"
        )
    if default_approve:
        fail_reasons.append("default_approve is not allowed at handoff boundary")
    if implicit_approve:
        fail_reasons.append("implicit_approve is not allowed at handoff boundary")
    if unknown_decision_state is not None:
        fail_reasons.append(f"unknown decision state {unknown_decision_state!r}")
    if operative_decision_issued:
        fail_reasons.append("operative_decision_issued=true is not allowed at handoff boundary")
    if operative_closure_executed:
        fail_reasons.append("operative_closure_executed=true is not allowed at handoff boundary")
    if extra_proof_slots:
        fail_reasons.append(f"unknown extra proof slots: {sorted(extra_proof_slots)!r}")
    if extra_decision_fields:
        fail_reasons.append(f"unknown extra decision fields: {sorted(extra_decision_fields)!r}")

    fail_reasons = _sorted_unique(fail_reasons)
    boundary_pass = len(fail_reasons) == 0
    handoff_satisfied = boundary_pass and not loose_boolean_eligibility

    return {
        "boundary_pass": boundary_pass,
        "operator_review_handoff_boundary_satisfied": handoff_satisfied,
        "pe34_operator_review_handoff_boundary_static_proven": handoff_satisfied,
        "source_revision_coherent": boundary_pass,
        "owner_identities_coherent": boundary_pass,
        "proof_digests_coherent": boundary_pass,
        "handoff_mode": HANDOFF_MODE,
        "handoff_owner": HANDOFF_OWNER,
        "contract_version": CONTRACT_VERSION,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "allowed_later_decisions": sorted(ALLOWED_LATER_DECISIONS),
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_selected": OPERATOR_DECISION_SELECTED,
        "operator_proof_package_operationally_issued": OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED,
        "operator_closure_executed": OPERATOR_CLOSURE_EXECUTED,
        "second_assembly_created": SECOND_ASSEMBLY_CREATED,
        "second_readiness_surface_created": SECOND_READINESS_SURFACE_CREATED,
        "second_operator_review_surface_created": SECOND_OPERATOR_REVIEW_SURFACE_CREATED,
        "authority_lift": AUTHORITY_LIFT,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "boundary_result_digest": (
            compute_boundary_result_digest(
                boundary_input,
                operator_review_handoff_boundary_satisfied=handoff_satisfied,
            )
            if boundary_pass
            else None
        ),
        "preflight_remains_blocked": True,
        "global_blocker_lift_authorized": False,
        "preflight_lift_authorized": False,
        "ready_for_operator_arming": False,
        "readiness_decision_authorized": False,
        "operator_review_authorized": False,
        "operator_decision_authorized": False,
        "operator_closure_authorized": False,
        "execution_authorized": False,
        "zero_order_authorized": False,
        "private_readonly_authorized": False,
        "validate_only_authorized": False,
        "tiny_order_authorized": False,
        "reconciliation_authorized": False,
        "evidence_acceptance_authorized": False,
        "pilot_start_authorized": False,
        "promotion_authorized": False,
        "live_authorized": False,
        "network_used": False,
        "credentials_used": False,
        "secret_material_read": False,
        "secret_material_stored": False,
        "exchange_api_called": False,
        "exchange_request_count": 0,
        "account_state_queried": False,
        "orders_created": 0,
        "orders_cancelled": 0,
        "orders_amended": 0,
        "positions_changed": 0,
        "adapter_called": False,
        "harness_started": False,
        "subprocess_started": False,
        "testnet_started": False,
        "runtime_started": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
        "fail_reasons": fail_reasons,
    }


def default_minimal_safety_snapshot() -> HandoffBoundarySafetySnapshot:
    return HandoffBoundarySafetySnapshot(
        preflight_remains_blocked=True,
        global_blocker_lift_authorized=False,
        preflight_lift_authorized=False,
        ready_for_operator_arming=False,
        readiness_decision_authorized=False,
        operator_review_authorized=False,
        operator_decision_authorized=False,
        operator_closure_authorized=False,
        execution_authorized=False,
        zero_order_authorized=False,
        private_readonly_authorized=False,
        validate_only_authorized=False,
        tiny_order_authorized=False,
        reconciliation_authorized=False,
        evidence_acceptance_authorized=False,
        pilot_start_authorized=False,
        promotion_authorized=False,
        live_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def default_minimal_handoff_boundary_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    handoff_id: str = "operator-review-handoff-boundary-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
    review_input: PreflightOperatorReviewInput | None = None,
    operator_name_legibility: str | None = EXPECTED_OPERATOR_NAME,
) -> OperatorReviewHandoffBoundaryInput:
    """Minimal valid futures-generic PE-34 handoff boundary input for offline tests."""
    from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
        default_minimal_integration_input as default_minimal_pe33_integration_input,
    )
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        default_minimal_operator_review_input,
    )

    pe33_input = default_minimal_pe33_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=lifecycle_state_digest,
    )
    pe33_result = evaluate_cross_slice_proof_coherence_integration(pe33_input)
    pe33_proof_digest = pe33_result["integration_proof_digest"]
    pe33_input_digest = pe33_result["integration_input_digest"]

    pe25_slot_digest = next(
        slot.proof_digest for slot in pe33_input.proof_slots if slot.slot_id == "pe25"
    )

    if review_input is None:
        review_input = default_minimal_operator_review_input(
            source_revision=source_revision,
            packet_digest="a" * 64,
            input_capture_digest="b" * 64,
            replay_manifest_digest="c" * 64,
            archive_identity="d" * 64,
            archive_manifest_digest="e" * 64,
            completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
            source_state_digest=lifecycle_state_digest or "f" * 64,
        )

    review_input_digest = compute_review_input_digest(review_input)

    return OperatorReviewHandoffBoundaryInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        handoff_id=handoff_id,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe19_operator_review=PE19_CONTRACT_VERSION,
            pe20_review_proof_package=PE20_CONTRACT_VERSION,
            pe25_operator_closure=PE25_CONTRACT_VERSION,
            pe33_cross_slice_proof_coherence=PE33_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
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
        pe33_integration_input=pe33_input,
        pe19_undecided_review_input=Pe19UndecidedReviewInputBinding(
            review_input_owner=PE19_CONTRACT_VERSION,
            source_revision=source_revision,
            review_input=review_input,
            pe33_integration_proof_digest=pe33_proof_digest,
            operator_name_legibility=operator_name_legibility,
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
        safety_snapshot=default_minimal_safety_snapshot(),
    )
