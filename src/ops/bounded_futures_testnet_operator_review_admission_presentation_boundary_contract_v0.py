"""Bounded Futures Testnet operator review admission presentation boundary (v0, PE-36).

Deterministic, offline, explicit-input-only fail-closed boundary guard over a
PE-35-validated handoff. Builds an immutable read-only presentation projection
from digest-bound canonical review fields without queue, UI, review execution,
decision selection, or authority lift.

Static admission/presentation boundary only — no operator review, no operator
decision, no operative proof-package issuance, no queue, no UI rendering,
network, testnet, runtime, credentials, orders, or exchange access.
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
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE35_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE35_CONTRACT_VERSION,
    HandoffStalenessRevocationRecoveryBoundaryInput,
    compute_boundary_input_digest as compute_pe35_boundary_input_digest,
    default_minimal_boundary_input as default_minimal_pe35_boundary_input,
    evaluate_handoff_staleness_revocation_recovery_boundary,
    validate_handoff_staleness_revocation_recovery_boundary_input,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    ALLOWED_LATER_DECISIONS,
    HANDOFF_OWNER as PE34_HANDOFF_OWNER,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    EXPECTED_OPERATOR_NAME,
    compute_review_input_digest,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
    COHERENCE_OWNER as PE33_COHERENCE_OWNER,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
)

PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_BOUNDARY_CONTRACT_V0=true"
)
CONTRACT_VERSION = "bounded_futures_testnet_operator_review_admission_presentation_boundary.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_operator_review_admission_presentation_boundary.serialization.v0"
)
PROJECTION_VERSION = "bounded_futures_testnet_operator_review_admission_presentation_projection.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

BOUNDARY_MODE = "static_operator_review_admission_presentation_boundary_guard_only"
BOUNDARY_OWNER = CONTRACT_VERSION
PRESENTATION_MODE = "read_only_review_presentation_for_separate_operator_review_only"
PRESENTATION_STATUS = "read_only_non_authorizing"

CONTRACT_IMPLEMENTATION_ONLY = True
OPERATOR_REVIEW_EXECUTED = False
OPERATOR_DECISION_SELECTED = False
OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED = False
SECOND_ASSEMBLY_CREATED = False
SECOND_READINESS_SURFACE_CREATED = False
SECOND_OPERATOR_REVIEW_SURFACE_CREATED = False
SECOND_HANDOFF_SURFACE_CREATED = False
SECOND_PRESENTATION_SURFACE_CREATED = False
REVIEW_QUEUE_CREATED = False
REVIEW_QUEUE_ENTRY_CREATED = False
UI_SURFACE_CREATED = False
PRESENTATION_RENDERED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

_FORBIDDEN_KEY_FRAGMENTS = (
    "password",
    "secret",
    "credential",
    "api_key",
    "apikey",
    "token",
    "private_key",
    "authorization",
    "auth_header",
    "balance",
    "equity",
    "margin",
    "position",
    "order_state",
    "order_id",
    "command",
    "workflow",
    "runtime",
    "testnet_action",
    "live_action",
    "callback",
    "html",
    "script",
    "function_ref",
    "selected_decision",
    "decision_record",
    "approve_default",
    "default_approve",
)

_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"^/tmp(?:/|$)"),
    re.compile(r"(?i)(password|secret|api[_-]?key|bearer\s|authorization:)"),
)

PRESENTATION_FIELD_ALLOWLIST = frozenset(
    {
        "projection_contract_version",
        "projection_mode",
        "presentation_status",
        "source_revision",
        "repository_identity",
        "review_identity",
        "handoff_id",
        "adapter_id",
        "instrument",
        "market_type",
        "pe33_coherence_owner",
        "pe34_handoff_owner",
        "pe35_boundary_owner",
        "pe19_review_input_owner",
        "pe20_package_owner",
        "pe25_closure_owner",
        "pe33_integration_proof_digest",
        "pe34_handoff_digest",
        "pe35_boundary_input_digest",
        "pe35_boundary_result_digest",
        "pe19_review_input_digest",
        "pe20_package_binding_digest",
        "pe25_closure_result_digest",
        "lifecycle_state",
        "handoff_current",
        "cross_slice_proof_coherence_for_separate_operator_review",
        "static_pe12_lifecycle_chain_complete",
        "operator_closure_static_complete",
        "undecided_package_eligibility",
        "operator_name_legibility",
        "non_authorizing",
        "allowed_later_decisions",
        "futures_only",
        "environment",
    }
)


@dataclass(frozen=True)
class Pe35BoundaryProofBinding:
    boundary_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str | None
    handoff_staleness_revocation_recovery_boundary_satisfied: bool


@dataclass(frozen=True)
class OperatorReviewAdmissionPresentationProjection:
    projection_contract_version: str
    projection_mode: str
    presentation_status: str
    source_revision: str
    repository_identity: str
    review_identity: str
    handoff_id: str
    adapter_id: str
    instrument: str
    market_type: str
    pe33_coherence_owner: str
    pe34_handoff_owner: str
    pe35_boundary_owner: str
    pe19_review_input_owner: str
    pe20_package_owner: str
    pe25_closure_owner: str
    pe33_integration_proof_digest: str
    pe34_handoff_digest: str
    pe35_boundary_input_digest: str
    pe35_boundary_result_digest: str
    pe19_review_input_digest: str
    pe20_package_binding_digest: str
    pe25_closure_result_digest: str
    lifecycle_state: str
    handoff_current: bool
    cross_slice_proof_coherence_for_separate_operator_review: bool
    static_pe12_lifecycle_chain_complete: bool
    operator_closure_static_complete: bool
    undecided_package_eligibility: bool
    operator_name_legibility: str | None
    non_authorizing: bool
    allowed_later_decisions: tuple[str, ...]
    futures_only: bool
    environment: str


@dataclass(frozen=True)
class OperatorReviewAdmissionPresentationBoundaryInput:
    pe35_boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput
    pe35_proof: Pe35BoundaryProofBinding
    operator_name_legibility: str | None = None
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


def _scan_forbidden_field(key: str, value: Any) -> list[str]:
    fail_reasons: list[str] = []
    key_lower = key.lower()
    for fragment in _FORBIDDEN_KEY_FRAGMENTS:
        if fragment in key_lower:
            fail_reasons.append(f"forbidden presentation field key {key!r}")
            break
    if isinstance(value, str):
        for pattern in _FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(value):
                fail_reasons.append(f"forbidden presentation field value for key {key!r}")
                break
    return fail_reasons


def _validate_pe35_proof_binding(
    binding: Pe35BoundaryProofBinding,
    *,
    expected_source_revision: str,
    expected_input_digest: str,
    expected_result_digest: str | None,
    expected_satisfied: bool,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.boundary_owner != PE35_BOUNDARY_OWNER:
        fail_reasons.append(f"pe35_proof: boundary_owner must be {PE35_BOUNDARY_OWNER!r}")
    if binding.boundary_owner != PE35_CONTRACT_VERSION:
        fail_reasons.append(f"pe35_proof: boundary_owner must be {PE35_CONTRACT_VERSION!r}")
    if not binding.source_revision:
        fail_reasons.append("pe35_proof: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append("pe35_proof: source_revision must be full 40-char lowercase commit SHA")
    elif binding.source_revision != expected_source_revision:
        fail_reasons.append("pe35_proof: source_revision mismatch")
    if not binding.boundary_input_digest:
        fail_reasons.append("pe35_proof: boundary_input_digest required")
    elif not _valid_sha256_digest(binding.boundary_input_digest):
        fail_reasons.append(
            "pe35_proof: boundary_input_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.boundary_input_digest != expected_input_digest:
        fail_reasons.append("pe35_proof: boundary_input_digest mismatch")
    if binding.handoff_staleness_revocation_recovery_boundary_satisfied is not expected_satisfied:
        fail_reasons.append(
            "pe35_proof: handoff_staleness_revocation_recovery_boundary_satisfied mismatch"
        )
    if expected_satisfied:
        if not binding.boundary_result_digest:
            fail_reasons.append("pe35_proof: boundary_result_digest required when satisfied")
        elif not _valid_sha256_digest(binding.boundary_result_digest):
            fail_reasons.append(
                "pe35_proof: boundary_result_digest must be 64-char lowercase sha256 hex"
            )
        elif binding.boundary_result_digest != expected_result_digest:
            fail_reasons.append("pe35_proof: boundary_result_digest mismatch")
    elif binding.boundary_result_digest is not None:
        fail_reasons.append("pe35_proof: boundary_result_digest must be absent when not satisfied")
    return fail_reasons


def validate_presentation_projection_dict(projection_dict: dict[str, Any]) -> list[str]:
    """Fail-closed validation of explicit presentation projection field allowlist."""
    fail_reasons: list[str] = []
    keys = set(projection_dict.keys())
    missing = PRESENTATION_FIELD_ALLOWLIST - keys
    extra = keys - PRESENTATION_FIELD_ALLOWLIST
    if missing:
        fail_reasons.append(f"presentation projection missing required fields: {sorted(missing)!r}")
    if extra:
        fail_reasons.append(f"presentation projection has unknown fields: {sorted(extra)!r}")
    for key, value in projection_dict.items():
        fail_reasons.extend(_scan_forbidden_field(key, value))
    return _sorted_unique(fail_reasons)


def validate_operator_review_admission_presentation_boundary_input(
    boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-36 boundary guard bindings."""
    fail_reasons: list[str] = []

    pe35_input = boundary_input.pe35_boundary_input
    fail_reasons.extend(validate_handoff_staleness_revocation_recovery_boundary_input(pe35_input))

    pe34_handoff = pe35_input.pe34_handoff
    fail_reasons.extend(
        _validate_instrument_scope(pe34_handoff.instrument, pe34_handoff.market_type)
    )

    computed_pe35_input_digest = compute_pe35_boundary_input_digest(pe35_input)
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    pe35_satisfied = pe35_result["handoff_staleness_revocation_recovery_boundary_satisfied"]
    expected_result_digest = pe35_result["boundary_result_digest"]

    fail_reasons.extend(
        _validate_pe35_proof_binding(
            boundary_input.pe35_proof,
            expected_source_revision=pe34_handoff.source_revision,
            expected_input_digest=computed_pe35_input_digest,
            expected_result_digest=expected_result_digest,
            expected_satisfied=pe35_satisfied,
        )
    )

    if boundary_input.operator_name_legibility is not None:
        if boundary_input.operator_name_legibility != EXPECTED_OPERATOR_NAME:
            fail_reasons.append(
                f"operator_name_legibility must be {EXPECTED_OPERATOR_NAME!r} when present"
            )

    if boundary_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if boundary_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if boundary_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _build_presentation_projection(
    boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
    *,
    pe35_result: dict[str, Any],
) -> OperatorReviewAdmissionPresentationProjection:
    pe35 = boundary_input.pe35_boundary_input
    pe34 = pe35.pe34_handoff
    lifecycle = pe35.lifecycle_metadata
    pe33_proof = pe34.pe33_coherence_proof
    pe19_digest = compute_review_input_digest(pe34.pe19_undecided_review_input.review_input)
    pe34_digest = compute_pe34_boundary_input_digest(pe34)
    pe35_input_digest = compute_pe35_boundary_input_digest(pe35)
    pe35_result_digest = pe35_result["boundary_result_digest"]
    if pe35_result_digest is None:
        raise ValueError("pe35 boundary_result_digest required for presentation projection")

    return OperatorReviewAdmissionPresentationProjection(
        projection_contract_version=PROJECTION_VERSION,
        projection_mode=PRESENTATION_MODE,
        presentation_status=PRESENTATION_STATUS,
        source_revision=pe34.source_revision,
        repository_identity=pe34.repository_identity,
        review_identity=lifecycle.review_identity,
        handoff_id=pe34.handoff_id,
        adapter_id=pe34.adapter_id,
        instrument=pe34.instrument,
        market_type=pe34.market_type,
        pe33_coherence_owner=PE33_COHERENCE_OWNER,
        pe34_handoff_owner=PE34_HANDOFF_OWNER,
        pe35_boundary_owner=PE35_BOUNDARY_OWNER,
        pe19_review_input_owner=PE19_CONTRACT_VERSION,
        pe20_package_owner=PE20_CONTRACT_VERSION,
        pe25_closure_owner=PE25_CONTRACT_VERSION,
        pe33_integration_proof_digest=pe33_proof.integration_proof_digest,
        pe34_handoff_digest=pe34_digest,
        pe35_boundary_input_digest=pe35_input_digest,
        pe35_boundary_result_digest=pe35_result_digest,
        pe19_review_input_digest=pe19_digest,
        pe20_package_binding_digest=pe34.pe20_undecided_package_eligibility.review_input_digest,
        pe25_closure_result_digest=pe34.pe25_cross_slice_closure.closure_result_digest,
        lifecycle_state=lifecycle.lifecycle_state,
        handoff_current=pe35_result["handoff_current"],
        cross_slice_proof_coherence_for_separate_operator_review=(
            pe33_proof.cross_slice_proof_coherence_for_separate_operator_review
        ),
        static_pe12_lifecycle_chain_complete=pe33_proof.static_pe12_lifecycle_chain_complete,
        operator_closure_static_complete=pe34.pe25_cross_slice_closure.operator_closure_static_complete,
        undecided_package_eligibility=pe34.pe20_undecided_package_eligibility.undecided_package_eligibility,
        operator_name_legibility=boundary_input.operator_name_legibility,
        non_authorizing=boundary_input.non_authorizing,
        allowed_later_decisions=tuple(sorted(ALLOWED_LATER_DECISIONS)),
        futures_only=boundary_input.futures_only,
        environment=boundary_input.environment,
    )


def serialize_presentation_projection_canonical(
    projection: OperatorReviewAdmissionPresentationProjection,
) -> str:
    payload = asdict(projection)
    payload["allowed_later_decisions"] = list(projection.allowed_later_decisions)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_presentation_projection_digest(
    projection: OperatorReviewAdmissionPresentationProjection,
) -> str:
    return hashlib.sha256(
        serialize_presentation_projection_canonical(projection).encode("utf-8")
    ).hexdigest()


def _boundary_input_dict(
    boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> dict[str, Any]:
    return {
        "boundary_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "pe35_boundary_input_digest": compute_pe35_boundary_input_digest(
            boundary_input.pe35_boundary_input
        ),
        "pe35_boundary_owner": PE35_BOUNDARY_OWNER,
        "pe35_contract_version": PE35_CONTRACT_VERSION,
        "pe35_proof": asdict(boundary_input.pe35_proof),
        "operator_name_legibility": boundary_input.operator_name_legibility,
        "futures_only": boundary_input.futures_only,
        "environment": boundary_input.environment,
        "non_authorizing": boundary_input.non_authorizing,
    }


def serialize_boundary_input_canonical(
    boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> str:
    return json.dumps(
        _boundary_input_dict(boundary_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_boundary_input_digest(
    boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> str:
    return hashlib.sha256(
        serialize_boundary_input_canonical(boundary_input).encode("utf-8")
    ).hexdigest()


def compute_boundary_result_digest(
    boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
    *,
    operator_review_admission_presentation_boundary_satisfied: bool,
    presentation_projection_digest: str,
) -> str:
    payload = {
        "boundary_contract_version": CONTRACT_VERSION,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "boundary_mode": BOUNDARY_MODE,
        "boundary_owner": BOUNDARY_OWNER,
        "hash_algorithm": HASH_ALGORITHM,
        "operator_review_admission_presentation_boundary_satisfied": (
            operator_review_admission_presentation_boundary_satisfied
        ),
        "package_marker": PACKAGE_MARKER,
        "pe35_boundary_input_digest": compute_pe35_boundary_input_digest(
            boundary_input.pe35_boundary_input
        ),
        "presentation_projection_digest": presentation_projection_digest,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": boundary_input.pe35_boundary_input.pe34_handoff.source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def evaluate_operator_review_admission_presentation_boundary(
    boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
    *,
    loose_admitted_flag: bool = False,
    loose_presentable_flag: bool = False,
    selected_decision: str | None = None,
    default_approve: bool = False,
    implicit_approve: bool = False,
    extra_presentation_fields: tuple[str, ...] = (),
    injected_presentation_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-36 admission/presentation boundary; never grants authority."""
    fail_reasons = validate_operator_review_admission_presentation_boundary_input(boundary_input)

    pe35_input = boundary_input.pe35_boundary_input
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    if not pe35_result["handoff_staleness_revocation_recovery_boundary_satisfied"]:
        fail_reasons.append("PE-35 handoff_staleness_revocation_recovery_boundary_satisfied false")

    pe34_handoff = pe35_input.pe34_handoff
    computed_pe35_input_digest = compute_pe35_boundary_input_digest(pe35_input)
    computed_pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe33_bound = pe34_handoff.pe33_coherence_proof.integration_proof_digest
    pe19_review_digest = compute_review_input_digest(
        pe34_handoff.pe19_undecided_review_input.review_input
    )
    pe20_binding_digest = pe34_handoff.pe20_undecided_package_eligibility.review_input_digest
    pe25_closure_digest = pe34_handoff.pe25_cross_slice_closure.closure_result_digest

    proof = boundary_input.pe35_proof
    if proof.boundary_owner != PE35_BOUNDARY_OWNER:
        fail_reasons.append(f"pe35_proof: boundary_owner alias {proof.boundary_owner!r} rejected")
    if proof.boundary_input_digest != computed_pe35_input_digest:
        fail_reasons.append("pe35_proof: boundary_input_digest drift from computed PE-35 input")
    if proof.handoff_staleness_revocation_recovery_boundary_satisfied and (
        pe35_result["boundary_result_digest"] != proof.boundary_result_digest
    ):
        fail_reasons.append("pe35_proof: boundary_result_digest drift from computed PE-35 result")

    if pe35_input.canonical_current.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("PE-34 handoff digest mismatch with canonical current bindings")
    if pe35_input.canonical_current.pe33_integration_proof_digest != pe33_bound:
        fail_reasons.append("PE-33 integration proof digest mismatch with canonical current")
    if pe34_handoff.pe19_undecided_review_input.pe33_integration_proof_digest != pe33_bound:
        fail_reasons.append("PE-19 pe33_integration_proof_digest mismatch")
    if pe34_handoff.pe20_undecided_package_eligibility.review_input_digest != pe19_review_digest:
        fail_reasons.append("PE-20 package binding digest mismatch with PE-19 review input")
    if pe34_handoff.pe25_cross_slice_closure.closure_result_digest != pe25_closure_digest:
        fail_reasons.append("PE-25 closure result digest internal mismatch")

    if loose_admitted_flag:
        fail_reasons.append("loose admitted=true cannot replace PE-35 proof binding")
    if loose_presentable_flag:
        fail_reasons.append("loose presentable=true cannot replace presentation projection binding")
    if selected_decision is not None:
        fail_reasons.append(
            f"selected_decision {selected_decision!r} is not allowed at admission/presentation boundary"
        )
    if default_approve:
        fail_reasons.append("default_approve is not allowed at admission/presentation boundary")
    if implicit_approve:
        fail_reasons.append("implicit_approve is not allowed at admission/presentation boundary")
    if extra_presentation_fields:
        fail_reasons.append(
            f"unknown extra presentation fields: {sorted(extra_presentation_fields)!r}"
        )

    if injected_presentation_overrides:
        for key, value in injected_presentation_overrides.items():
            fail_reasons.extend(_scan_forbidden_field(key, value))
        fail_reasons.append(
            f"injected presentation overrides not allowed: {sorted(injected_presentation_overrides)!r}"
        )

    fail_reasons = _sorted_unique(fail_reasons)
    structural_pass = len(fail_reasons) == 0

    presentation_projection: OperatorReviewAdmissionPresentationProjection | None = None
    presentation_projection_digest: str | None = None
    if structural_pass and pe35_result["boundary_result_digest"] is not None:
        presentation_projection = _build_presentation_projection(
            boundary_input,
            pe35_result=pe35_result,
        )
        projection_dict = asdict(presentation_projection)
        projection_dict["allowed_later_decisions"] = list(
            presentation_projection.allowed_later_decisions
        )
        projection_fail = validate_presentation_projection_dict(projection_dict)
        if projection_fail:
            fail_reasons = _sorted_unique(fail_reasons + projection_fail)
            structural_pass = False
            presentation_projection = None
        else:
            presentation_projection_digest = compute_presentation_projection_digest(
                presentation_projection
            )

    boundary_satisfied = structural_pass and presentation_projection is not None

    return {
        "boundary_pass": structural_pass,
        "operator_review_admission_presentation_boundary_satisfied": boundary_satisfied,
        "pe36_operator_review_admission_presentation_boundary_static_proven": boundary_satisfied,
        "source_revision_coherent": structural_pass,
        "owner_identities_coherent": structural_pass,
        "proof_digests_coherent": structural_pass,
        "presentation_fields_allowlisted": boundary_satisfied,
        "secret_fields_present": False,
        "decision_preselected": False,
        "boundary_mode": BOUNDARY_MODE,
        "boundary_owner": BOUNDARY_OWNER,
        "presentation_mode": PRESENTATION_MODE,
        "contract_version": CONTRACT_VERSION,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "allowed_later_decisions": sorted(ALLOWED_LATER_DECISIONS),
        "presentation_projection": presentation_projection,
        "presentation_projection_digest": presentation_projection_digest,
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_selected": OPERATOR_DECISION_SELECTED,
        "operator_proof_package_operationally_issued": OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED,
        "second_assembly_created": SECOND_ASSEMBLY_CREATED,
        "second_readiness_surface_created": SECOND_READINESS_SURFACE_CREATED,
        "second_operator_review_surface_created": SECOND_OPERATOR_REVIEW_SURFACE_CREATED,
        "second_handoff_surface_created": SECOND_HANDOFF_SURFACE_CREATED,
        "second_presentation_surface_created": SECOND_PRESENTATION_SURFACE_CREATED,
        "review_queue_created": REVIEW_QUEUE_CREATED,
        "review_queue_entry_created": REVIEW_QUEUE_ENTRY_CREATED,
        "ui_surface_created": UI_SURFACE_CREATED,
        "presentation_rendered": PRESENTATION_RENDERED,
        "authority_lift": AUTHORITY_LIFT,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "boundary_result_digest": (
            compute_boundary_result_digest(
                boundary_input,
                operator_review_admission_presentation_boundary_satisfied=boundary_satisfied,
                presentation_projection_digest=presentation_projection_digest,
            )
            if boundary_satisfied and presentation_projection_digest is not None
            else None
        ),
        "pe35_boundary_input_digest": computed_pe35_input_digest,
        "pe34_handoff_digest": computed_pe34_digest,
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


def default_minimal_pe35_proof_binding(
    pe35_boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput,
) -> Pe35BoundaryProofBinding:
    """Build canonical PE-35 proof binding from explicit boundary input evaluation."""
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_boundary_input)
    return Pe35BoundaryProofBinding(
        boundary_owner=PE35_BOUNDARY_OWNER,
        source_revision=pe35_boundary_input.pe34_handoff.source_revision,
        boundary_input_digest=compute_pe35_boundary_input_digest(pe35_boundary_input),
        boundary_result_digest=pe35_result["boundary_result_digest"],
        handoff_staleness_revocation_recovery_boundary_satisfied=pe35_result[
            "handoff_staleness_revocation_recovery_boundary_satisfied"
        ],
    )


def default_minimal_boundary_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    handoff_id: str = "operator-review-handoff-boundary-001",
    instrument: str = "PF_ETHUSD",
    review_identity: str = "glb-016-bounded-futures-testnet-operator-review",
    operator_name_legibility: str | None = EXPECTED_OPERATOR_NAME,
) -> OperatorReviewAdmissionPresentationBoundaryInput:
    """Minimal valid futures-generic PE-36 boundary input for offline tests."""
    pe35_input = default_minimal_pe35_boundary_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        handoff_id=handoff_id,
        instrument=instrument,
        review_identity=review_identity,
    )
    return OperatorReviewAdmissionPresentationBoundaryInput(
        pe35_boundary_input=pe35_input,
        pe35_proof=default_minimal_pe35_proof_binding(pe35_input),
        operator_name_legibility=operator_name_legibility,
    )
