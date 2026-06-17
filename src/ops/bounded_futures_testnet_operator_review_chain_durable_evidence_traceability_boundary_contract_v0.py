"""Bounded Futures Testnet operator review chain durable evidence traceability boundary (v0, PE-37).

Deterministic, offline, explicit-input-only fail-closed traceability guard over a
PE-36-validated admission/presentation boundary. Binds PE-33 through PE-36 proof digests
to PE-16 archive/manifest identities and PE-19/PE-20 operator-review proof semantics
without archive writes, manifest writes, admission execution, replay execution, or
authority lift.

Static traceability boundary only — no operator review, no operator decision, no operative
proof-package issuance, no evidence/archive/manifest surface creation, network, testnet,
runtime, credentials, orders, or exchange access.
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
from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
    COHERENCE_OWNER as PE33_COHERENCE_OWNER,
)
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE35_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE35_CONTRACT_VERSION,
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
    compute_presentation_projection_digest,
    default_minimal_pe35_proof_binding,
    evaluate_operator_review_admission_presentation_boundary,
    validate_operator_review_admission_presentation_boundary_input,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    HANDOFF_OWNER as PE34_HANDOFF_OWNER,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    EXPECTED_OPERATOR_NAME,
    compute_review_input_digest,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
    compute_archive_identity,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_CHAIN_DURABLE_EVIDENCE_TRACEABILITY_BOUNDARY_CONTRACT_V0=true"
CONTRACT_VERSION = (
    "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary.v0"
)
SERIALIZATION_VERSION = "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

BOUNDARY_MODE = "static_durable_evidence_traceability_boundary_guard_only"
BOUNDARY_OWNER = CONTRACT_VERSION
TRACEABILITY_MODE = "read_only_proof_chain_archive_manifest_binding_only"
TRACEABILITY_STATUS = "read_only_non_authorizing"

CONTRACT_IMPLEMENTATION_ONLY = True
OPERATOR_REVIEW_EXECUTED = False
OPERATOR_DECISION_SELECTED = False
OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED = False
SECOND_ASSEMBLY_CREATED = False
SECOND_READINESS_SURFACE_CREATED = False
SECOND_OPERATOR_REVIEW_SURFACE_CREATED = False
SECOND_HANDOFF_SURFACE_CREATED = False
SECOND_PRESENTATION_SURFACE_CREATED = False
SECOND_EVIDENCE_SURFACE_CREATED = False
SECOND_ARCHIVE_SURFACE_CREATED = False
SECOND_MANIFEST_SURFACE_CREATED = False
REVIEW_QUEUE_CREATED = False
REVIEW_QUEUE_ENTRY_CREATED = False
UI_SURFACE_CREATED = False
PRESENTATION_RENDERED = False
SECRET_FIELDS_PRESENT = False
DECISION_PRESELECTED = False
ARCHIVE_WRITTEN = False
MANIFEST_WRITTEN = False
REPLAY_EXECUTED = False
ADMISSION_EXECUTED = False
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

PROOF_CHAIN_SLOT_ORDER = (
    "pe33_integration_proof_digest",
    "pe34_handoff_digest",
    "pe35_boundary_input_digest",
    "pe35_boundary_result_digest",
    "pe36_boundary_input_digest",
    "pe36_boundary_result_digest",
    "pe36_presentation_projection_digest",
)


@dataclass(frozen=True)
class Pe16ArchiveManifestBinding:
    archive_owner: str
    source_revision: str
    archive_identity: str
    archive_manifest_digest: str
    packet_digest: str
    input_capture_digest: str
    replay_manifest_digest: str


@dataclass(frozen=True)
class Pe19Pe20OperatorReviewProofBinding:
    review_input_owner: str
    package_owner: str
    source_revision: str
    review_input_digest: str
    package_binding_digest: str
    operator_review_proof_identity: str


@dataclass(frozen=True)
class Pe36BoundaryProofBinding:
    boundary_owner: str
    source_revision: str
    boundary_input_digest: str
    boundary_result_digest: str | None
    presentation_projection_digest: str | None
    operator_review_admission_presentation_boundary_satisfied: bool


@dataclass(frozen=True)
class Pe33Pe36ProofChainBinding:
    pe33_integration_proof_digest: str
    pe34_handoff_digest: str
    pe35_boundary_input_digest: str
    pe35_boundary_result_digest: str
    pe36_boundary_input_digest: str
    pe36_boundary_result_digest: str
    pe36_presentation_projection_digest: str


@dataclass(frozen=True)
class DurableEvidenceTraceabilityBoundaryInput:
    pe36_boundary_input: OperatorReviewAdmissionPresentationBoundaryInput
    pe36_proof: Pe36BoundaryProofBinding
    pe16_archive_binding: Pe16ArchiveManifestBinding
    pe19_pe20_review_proof: Pe19Pe20OperatorReviewProofBinding
    proof_chain: Pe33Pe36ProofChainBinding
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
            fail_reasons.append(f"forbidden traceability field key {key!r}")
            break
    if isinstance(value, str):
        for pattern in _FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(value):
                fail_reasons.append(f"forbidden traceability field value for key {key!r}")
                break
    return fail_reasons


def compute_operator_review_proof_identity(
    *,
    review_input_owner: str,
    package_owner: str,
    source_revision: str,
    review_input_digest: str,
    package_binding_digest: str,
) -> str:
    """Deterministic operator-review proof identity from PE-19/PE-20 binding semantics."""
    payload = {
        "hash_algorithm": HASH_ALGORITHM,
        "package_binding_digest": package_binding_digest,
        "package_owner": package_owner,
        "review_input_digest": review_input_digest,
        "review_input_owner": review_input_owner,
        "source_revision": source_revision,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_traceability_identity(
    *,
    source_revision: str,
    proof_chain: Pe33Pe36ProofChainBinding,
    archive_identity: str,
    archive_manifest_digest: str,
    operator_review_proof_identity: str,
    boundary_owner: str = BOUNDARY_OWNER,
) -> str:
    """Deterministic traceability identity over explicit proof/archive/manifest bindings."""
    payload = {
        "archive_identity": archive_identity,
        "archive_manifest_digest": archive_manifest_digest,
        "boundary_owner": boundary_owner,
        "hash_algorithm": HASH_ALGORITHM,
        "operator_review_proof_identity": operator_review_proof_identity,
        "pe33_integration_proof_digest": proof_chain.pe33_integration_proof_digest,
        "pe34_handoff_digest": proof_chain.pe34_handoff_digest,
        "pe35_boundary_input_digest": proof_chain.pe35_boundary_input_digest,
        "pe35_boundary_result_digest": proof_chain.pe35_boundary_result_digest,
        "pe36_boundary_input_digest": proof_chain.pe36_boundary_input_digest,
        "pe36_boundary_result_digest": proof_chain.pe36_boundary_result_digest,
        "pe36_presentation_projection_digest": proof_chain.pe36_presentation_projection_digest,
        "source_revision": source_revision,
        "traceability_contract_version": CONTRACT_VERSION,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_admission_identity(
    *,
    pe36_boundary_result_digest: str,
    presentation_projection_digest: str,
) -> str:
    """Deterministic admission identity for duplicate-admission static detection."""
    payload = {
        "hash_algorithm": HASH_ALGORITHM,
        "pe36_boundary_result_digest": pe36_boundary_result_digest,
        "pe36_presentation_projection_digest": presentation_projection_digest,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_pe16_archive_binding(
    binding: Pe16ArchiveManifestBinding,
    *,
    expected_source_revision: str,
    expected_evidence_chain: Any,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.archive_owner != ARCHIVE_CONTRACT_VERSION:
        fail_reasons.append(f"pe16_archive: archive_owner must be {ARCHIVE_CONTRACT_VERSION!r}")
    if not binding.source_revision:
        fail_reasons.append("pe16_archive: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append(
            "pe16_archive: source_revision must be full 40-char lowercase commit SHA"
        )
    elif binding.source_revision != expected_source_revision:
        fail_reasons.append("pe16_archive: source_revision mismatch")
    for field_name in (
        "archive_identity",
        "archive_manifest_digest",
        "packet_digest",
        "input_capture_digest",
        "replay_manifest_digest",
    ):
        value = getattr(binding, field_name)
        if not value:
            fail_reasons.append(f"pe16_archive: {field_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"pe16_archive: {field_name} must be 64-char lowercase sha256 hex")
    if expected_evidence_chain is not None:
        if binding.packet_digest != expected_evidence_chain.packet_digest:
            fail_reasons.append("pe16_archive: packet_digest mismatch with evidence chain")
        if binding.input_capture_digest != expected_evidence_chain.input_capture_digest:
            fail_reasons.append("pe16_archive: input_capture_digest mismatch with evidence chain")
        if binding.replay_manifest_digest != expected_evidence_chain.replay_manifest_digest:
            fail_reasons.append("pe16_archive: replay_manifest_digest mismatch with evidence chain")
        if binding.archive_identity != expected_evidence_chain.archive_identity:
            fail_reasons.append("pe16_archive: archive_identity mismatch with evidence chain")
        if binding.archive_manifest_digest != expected_evidence_chain.archive_manifest_digest:
            fail_reasons.append(
                "pe16_archive: archive_manifest_digest mismatch with evidence chain"
            )
    expected_archive_identity = compute_archive_identity(
        source_revision=binding.source_revision,
        packet_digest=binding.packet_digest,
        input_capture_digest=binding.input_capture_digest,
        manifest_digest=binding.archive_manifest_digest,
    )
    if binding.archive_identity != expected_archive_identity:
        fail_reasons.append(
            "pe16_archive: archive_identity drift from PE-16 compute_archive_identity"
        )
    return fail_reasons


def _validate_pe19_pe20_review_proof_binding(
    binding: Pe19Pe20OperatorReviewProofBinding,
    *,
    expected_source_revision: str,
    expected_review_input_digest: str,
    expected_package_binding_digest: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.review_input_owner != PE19_CONTRACT_VERSION:
        fail_reasons.append(f"pe19_pe20: review_input_owner must be {PE19_CONTRACT_VERSION!r}")
    if binding.package_owner != PE20_CONTRACT_VERSION:
        fail_reasons.append(f"pe19_pe20: package_owner must be {PE20_CONTRACT_VERSION!r}")
    if not binding.source_revision:
        fail_reasons.append("pe19_pe20: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append("pe19_pe20: source_revision must be full 40-char lowercase commit SHA")
    elif binding.source_revision != expected_source_revision:
        fail_reasons.append("pe19_pe20: source_revision mismatch")
    if not binding.review_input_digest:
        fail_reasons.append("pe19_pe20: review_input_digest required")
    elif not _valid_sha256_digest(binding.review_input_digest):
        fail_reasons.append("pe19_pe20: review_input_digest must be 64-char lowercase sha256 hex")
    elif binding.review_input_digest != expected_review_input_digest:
        fail_reasons.append("pe19_pe20: review_input_digest mismatch")
    if not binding.package_binding_digest:
        fail_reasons.append("pe19_pe20: package_binding_digest required")
    elif not _valid_sha256_digest(binding.package_binding_digest):
        fail_reasons.append(
            "pe19_pe20: package_binding_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.package_binding_digest != expected_package_binding_digest:
        fail_reasons.append("pe19_pe20: package_binding_digest mismatch")
    if not binding.operator_review_proof_identity:
        fail_reasons.append("pe19_pe20: operator_review_proof_identity required")
    elif not _valid_sha256_digest(binding.operator_review_proof_identity):
        fail_reasons.append(
            "pe19_pe20: operator_review_proof_identity must be 64-char lowercase sha256 hex"
        )
    else:
        expected_identity = compute_operator_review_proof_identity(
            review_input_owner=binding.review_input_owner,
            package_owner=binding.package_owner,
            source_revision=binding.source_revision,
            review_input_digest=binding.review_input_digest,
            package_binding_digest=binding.package_binding_digest,
        )
        if binding.operator_review_proof_identity != expected_identity:
            fail_reasons.append("pe19_pe20: operator_review_proof_identity drift")
    return fail_reasons


def _validate_pe36_proof_binding(
    binding: Pe36BoundaryProofBinding,
    *,
    expected_source_revision: str,
    expected_input_digest: str,
    expected_result_digest: str | None,
    expected_projection_digest: str | None,
    expected_satisfied: bool,
) -> list[str]:
    fail_reasons: list[str] = []
    if binding.boundary_owner != PE36_BOUNDARY_OWNER:
        fail_reasons.append(f"pe36_proof: boundary_owner must be {PE36_BOUNDARY_OWNER!r}")
    if binding.boundary_owner != PE36_CONTRACT_VERSION:
        fail_reasons.append(f"pe36_proof: boundary_owner must be {PE36_CONTRACT_VERSION!r}")
    if not binding.source_revision:
        fail_reasons.append("pe36_proof: source_revision required")
    elif not _valid_commit_sha(binding.source_revision):
        fail_reasons.append("pe36_proof: source_revision must be full 40-char lowercase commit SHA")
    elif binding.source_revision != expected_source_revision:
        fail_reasons.append("pe36_proof: source_revision mismatch")
    if not binding.boundary_input_digest:
        fail_reasons.append("pe36_proof: boundary_input_digest required")
    elif not _valid_sha256_digest(binding.boundary_input_digest):
        fail_reasons.append(
            "pe36_proof: boundary_input_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.boundary_input_digest != expected_input_digest:
        fail_reasons.append("pe36_proof: boundary_input_digest mismatch")
    if binding.operator_review_admission_presentation_boundary_satisfied is not expected_satisfied:
        fail_reasons.append(
            "pe36_proof: operator_review_admission_presentation_boundary_satisfied mismatch"
        )
    if expected_satisfied:
        if not binding.boundary_result_digest:
            fail_reasons.append("pe36_proof: boundary_result_digest required when satisfied")
        elif not _valid_sha256_digest(binding.boundary_result_digest):
            fail_reasons.append(
                "pe36_proof: boundary_result_digest must be 64-char lowercase sha256 hex"
            )
        elif binding.boundary_result_digest != expected_result_digest:
            fail_reasons.append("pe36_proof: boundary_result_digest mismatch")
        if not binding.presentation_projection_digest:
            fail_reasons.append(
                "pe36_proof: presentation_projection_digest required when satisfied"
            )
        elif not _valid_sha256_digest(binding.presentation_projection_digest):
            fail_reasons.append(
                "pe36_proof: presentation_projection_digest must be 64-char lowercase sha256 hex"
            )
        elif binding.presentation_projection_digest != expected_projection_digest:
            fail_reasons.append("pe36_proof: presentation_projection_digest mismatch")
    else:
        if binding.boundary_result_digest is not None:
            fail_reasons.append(
                "pe36_proof: boundary_result_digest must be absent when not satisfied"
            )
        if binding.presentation_projection_digest is not None:
            fail_reasons.append(
                "pe36_proof: presentation_projection_digest must be absent when not satisfied"
            )
    return fail_reasons


def _validate_proof_chain_binding(
    proof_chain: Pe33Pe36ProofChainBinding,
    *,
    expected_pe33: str,
    expected_pe34: str,
    expected_pe35_input: str,
    expected_pe35_result: str,
    expected_pe36_input: str,
    expected_pe36_result: str,
    expected_pe36_projection: str,
) -> list[str]:
    fail_reasons: list[str] = []
    expected_slots = {
        "pe33_integration_proof_digest": expected_pe33,
        "pe34_handoff_digest": expected_pe34,
        "pe35_boundary_input_digest": expected_pe35_input,
        "pe35_boundary_result_digest": expected_pe35_result,
        "pe36_boundary_input_digest": expected_pe36_input,
        "pe36_boundary_result_digest": expected_pe36_result,
        "pe36_presentation_projection_digest": expected_pe36_projection,
    }
    for slot_name in PROOF_CHAIN_SLOT_ORDER:
        value = getattr(proof_chain, slot_name)
        if not value:
            fail_reasons.append(f"proof_chain: {slot_name} required")
        elif not _valid_sha256_digest(value):
            fail_reasons.append(f"proof_chain: {slot_name} must be 64-char lowercase sha256 hex")
        elif value != expected_slots[slot_name]:
            fail_reasons.append(f"proof_chain: {slot_name} mismatch")
    return fail_reasons


def validate_durable_evidence_traceability_boundary_input(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-37 traceability guard bindings."""
    fail_reasons: list[str] = []

    pe36_input = boundary_input.pe36_boundary_input
    fail_reasons.extend(validate_operator_review_admission_presentation_boundary_input(pe36_input))

    pe35_input = pe36_input.pe35_boundary_input
    fail_reasons.extend(validate_handoff_staleness_revocation_recovery_boundary_input(pe35_input))

    pe34_handoff = pe35_input.pe34_handoff
    fail_reasons.extend(
        _validate_instrument_scope(pe34_handoff.instrument, pe34_handoff.market_type)
    )

    source_revision = pe34_handoff.source_revision
    review_input = pe34_handoff.pe19_undecided_review_input.review_input
    evidence_chain = review_input.evidence_chain
    computed_review_digest = compute_review_input_digest(review_input)
    computed_package_binding = pe34_handoff.pe20_undecided_package_eligibility.review_input_digest

    pe36_result = evaluate_operator_review_admission_presentation_boundary(pe36_input)
    pe36_satisfied = pe36_result["operator_review_admission_presentation_boundary_satisfied"]
    computed_pe36_input_digest = compute_pe36_boundary_input_digest(pe36_input)
    computed_pe36_result_digest = pe36_result["boundary_result_digest"]
    computed_pe36_projection_digest = pe36_result["presentation_projection_digest"]

    fail_reasons.extend(
        _validate_pe36_proof_binding(
            boundary_input.pe36_proof,
            expected_source_revision=source_revision,
            expected_input_digest=computed_pe36_input_digest,
            expected_result_digest=computed_pe36_result_digest,
            expected_projection_digest=computed_pe36_projection_digest,
            expected_satisfied=pe36_satisfied,
        )
    )

    fail_reasons.extend(
        _validate_pe16_archive_binding(
            boundary_input.pe16_archive_binding,
            expected_source_revision=source_revision,
            expected_evidence_chain=evidence_chain,
        )
    )

    fail_reasons.extend(
        _validate_pe19_pe20_review_proof_binding(
            boundary_input.pe19_pe20_review_proof,
            expected_source_revision=source_revision,
            expected_review_input_digest=computed_review_digest,
            expected_package_binding_digest=computed_package_binding,
        )
    )

    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    pe35_result_digest = pe35_result["boundary_result_digest"]
    if pe35_result_digest is None:
        fail_reasons.append("PE-35 boundary_result_digest required for traceability chain")

    pe33_digest = pe34_handoff.pe33_coherence_proof.integration_proof_digest
    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe35_input_digest = compute_pe35_boundary_input_digest(pe35_input)

    if computed_pe36_result_digest is None or computed_pe36_projection_digest is None:
        fail_reasons.append("PE-36 result/projection digests required for proof chain binding")
        expected_pe36_result = ""
        expected_pe36_projection = ""
    else:
        expected_pe36_result = computed_pe36_result_digest
        expected_pe36_projection = computed_pe36_projection_digest

    fail_reasons.extend(
        _validate_proof_chain_binding(
            boundary_input.proof_chain,
            expected_pe33=pe33_digest,
            expected_pe34=pe34_digest,
            expected_pe35_input=pe35_input_digest,
            expected_pe35_result=pe35_result_digest or "",
            expected_pe36_input=computed_pe36_input_digest,
            expected_pe36_result=expected_pe36_result,
            expected_pe36_projection=expected_pe36_projection,
        )
    )

    if boundary_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if boundary_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if boundary_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _boundary_input_dict(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
) -> dict[str, Any]:
    return {
        "boundary_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "pe36_boundary_input_digest": compute_pe36_boundary_input_digest(
            boundary_input.pe36_boundary_input
        ),
        "pe36_boundary_owner": PE36_BOUNDARY_OWNER,
        "pe36_contract_version": PE36_CONTRACT_VERSION,
        "pe36_proof": asdict(boundary_input.pe36_proof),
        "pe16_archive_binding": asdict(boundary_input.pe16_archive_binding),
        "pe19_pe20_review_proof": asdict(boundary_input.pe19_pe20_review_proof),
        "proof_chain": asdict(boundary_input.proof_chain),
        "bound_traceability_identities": list(boundary_input.bound_traceability_identities),
        "bound_admission_identities": list(boundary_input.bound_admission_identities),
        "futures_only": boundary_input.futures_only,
        "environment": boundary_input.environment,
        "non_authorizing": boundary_input.non_authorizing,
    }


def serialize_boundary_input_canonical(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
) -> str:
    return json.dumps(
        _boundary_input_dict(boundary_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_boundary_input_digest(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
) -> str:
    return hashlib.sha256(
        serialize_boundary_input_canonical(boundary_input).encode("utf-8")
    ).hexdigest()


def compute_boundary_result_digest(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
    *,
    durable_evidence_traceability_boundary_satisfied: bool,
    traceability_identity: str,
) -> str:
    payload = {
        "boundary_contract_version": CONTRACT_VERSION,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "boundary_mode": BOUNDARY_MODE,
        "boundary_owner": BOUNDARY_OWNER,
        "durable_evidence_traceability_boundary_satisfied": (
            durable_evidence_traceability_boundary_satisfied
        ),
        "hash_algorithm": HASH_ALGORITHM,
        "package_marker": PACKAGE_MARKER,
        "pe36_boundary_input_digest": compute_pe36_boundary_input_digest(
            boundary_input.pe36_boundary_input
        ),
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": boundary_input.pe36_boundary_input.pe35_boundary_input.pe34_handoff.source_revision,
        "traceability_identity": traceability_identity,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def evaluate_durable_evidence_traceability_boundary(
    boundary_input: DurableEvidenceTraceabilityBoundaryInput,
    *,
    loose_traceable_flag: bool = False,
    selected_decision: str | None = None,
    default_approve: bool = False,
    implicit_approve: bool = False,
    extra_traceability_fields: tuple[str, ...] = (),
    injected_traceability_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-37 traceability boundary; never grants authority."""
    fail_reasons = validate_durable_evidence_traceability_boundary_input(boundary_input)

    pe36_input = boundary_input.pe36_boundary_input
    pe36_result = evaluate_operator_review_admission_presentation_boundary(pe36_input)
    if not pe36_result["operator_review_admission_presentation_boundary_satisfied"]:
        fail_reasons.append("PE-36 operator_review_admission_presentation_boundary_satisfied false")

    pe35_input = pe36_input.pe35_boundary_input
    pe34_handoff = pe35_input.pe34_handoff
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    if not pe35_result["handoff_staleness_revocation_recovery_boundary_satisfied"]:
        fail_reasons.append("PE-35 handoff_staleness_revocation_recovery_boundary_satisfied false")

    computed_pe33 = pe34_handoff.pe33_coherence_proof.integration_proof_digest
    computed_pe34 = compute_pe34_boundary_input_digest(pe34_handoff)
    computed_pe35_input = compute_pe35_boundary_input_digest(pe35_input)
    computed_pe36_input = compute_pe36_boundary_input_digest(pe36_input)
    computed_pe36_result = pe36_result["boundary_result_digest"]
    computed_pe36_projection = pe36_result["presentation_projection_digest"]

    proof = boundary_input.pe36_proof
    if proof.boundary_owner != PE36_BOUNDARY_OWNER:
        fail_reasons.append(f"pe36_proof: boundary_owner alias {proof.boundary_owner!r} rejected")
    if proof.boundary_input_digest != computed_pe36_input:
        fail_reasons.append("pe36_proof: boundary_input_digest drift from computed PE-36 input")
    if proof.operator_review_admission_presentation_boundary_satisfied and (
        pe36_result["boundary_result_digest"] != proof.boundary_result_digest
    ):
        fail_reasons.append("pe36_proof: boundary_result_digest drift from computed PE-36 result")

    chain = boundary_input.proof_chain
    if chain.pe33_integration_proof_digest != computed_pe33:
        fail_reasons.append("proof_chain: PE-33 integration proof digest drift")
    if chain.pe34_handoff_digest != computed_pe34:
        fail_reasons.append("proof_chain: PE-34 handoff digest drift")
    if chain.pe35_boundary_input_digest != computed_pe35_input:
        fail_reasons.append("proof_chain: PE-35 boundary input digest drift")
    if pe35_result["boundary_result_digest"] != chain.pe35_boundary_result_digest:
        fail_reasons.append("proof_chain: PE-35 boundary result digest drift")
    if chain.pe36_boundary_input_digest != computed_pe36_input:
        fail_reasons.append("proof_chain: PE-36 boundary input digest drift")
    if (
        computed_pe36_result is not None
        and chain.pe36_boundary_result_digest != computed_pe36_result
    ):
        fail_reasons.append("proof_chain: PE-36 boundary result digest drift")
    if (
        computed_pe36_projection is not None
        and chain.pe36_presentation_projection_digest != computed_pe36_projection
    ):
        fail_reasons.append("proof_chain: PE-36 presentation projection digest drift")

    archive = boundary_input.pe16_archive_binding
    if archive.archive_owner != ARCHIVE_CONTRACT_VERSION:
        fail_reasons.append(f"pe16_archive: archive_owner alias {archive.archive_owner!r} rejected")

    review_proof = boundary_input.pe19_pe20_review_proof
    if review_proof.review_input_owner != PE19_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe19_pe20: review_input_owner alias {review_proof.review_input_owner!r} rejected"
        )
    if review_proof.package_owner != PE20_CONTRACT_VERSION:
        fail_reasons.append(
            f"pe19_pe20: package_owner alias {review_proof.package_owner!r} rejected"
        )

    if pe34_handoff.pe33_coherence_proof.coherence_owner != PE33_COHERENCE_OWNER:
        fail_reasons.append("PE-33 coherence_owner mismatch")
    if pe34_handoff.pe19_undecided_review_input.review_input_owner != PE19_CONTRACT_VERSION:
        fail_reasons.append("PE-19 review_input_owner mismatch in handoff chain")
    if pe34_handoff.pe20_undecided_package_eligibility.package_owner != PE20_CONTRACT_VERSION:
        fail_reasons.append("PE-20 package_owner mismatch in handoff chain")

    if loose_traceable_flag:
        fail_reasons.append("loose traceable=true cannot replace proof/archive binding")
    if selected_decision is not None:
        fail_reasons.append(
            f"selected_decision {selected_decision!r} is not allowed at traceability boundary"
        )
    if default_approve:
        fail_reasons.append("default_approve is not allowed at traceability boundary")
    if implicit_approve:
        fail_reasons.append("implicit_approve is not allowed at traceability boundary")
    if extra_traceability_fields:
        fail_reasons.append(
            f"unknown extra traceability fields: {sorted(extra_traceability_fields)!r}"
        )
    if injected_traceability_overrides:
        for key, value in injected_traceability_overrides.items():
            fail_reasons.extend(_scan_forbidden_field(key, value))
        fail_reasons.append(
            f"injected traceability overrides not allowed: {sorted(injected_traceability_overrides)!r}"
        )

    fail_reasons = _sorted_unique(fail_reasons)
    structural_pass = len(fail_reasons) == 0

    traceability_identity: str | None = None
    admission_identity: str | None = None
    if (
        structural_pass
        and computed_pe36_result is not None
        and computed_pe36_projection is not None
    ):
        traceability_identity = compute_traceability_identity(
            source_revision=pe34_handoff.source_revision,
            proof_chain=chain,
            archive_identity=archive.archive_identity,
            archive_manifest_digest=archive.archive_manifest_digest,
            operator_review_proof_identity=review_proof.operator_review_proof_identity,
        )
        admission_identity = compute_admission_identity(
            pe36_boundary_result_digest=computed_pe36_result,
            presentation_projection_digest=computed_pe36_projection,
        )
        if traceability_identity in boundary_input.bound_traceability_identities:
            fail_reasons.append("replay of bound traceability identity detected")
            structural_pass = False
            traceability_identity = None
            admission_identity = None
        if admission_identity in boundary_input.bound_admission_identities:
            fail_reasons.append("duplicate admission identity detected")
            structural_pass = False
            traceability_identity = None
            admission_identity = None

    fail_reasons = _sorted_unique(fail_reasons)
    boundary_satisfied = structural_pass and traceability_identity is not None

    return {
        "boundary_pass": structural_pass,
        "durable_evidence_traceability_boundary_satisfied": boundary_satisfied,
        "pe37_durable_evidence_traceability_boundary_static_proven": boundary_satisfied,
        "source_revision_coherent": structural_pass,
        "owner_identities_coherent": structural_pass,
        "proof_digests_coherent": structural_pass,
        "archive_manifest_identities_coherent": boundary_satisfied,
        "operator_review_proof_identity_coherent": boundary_satisfied,
        "proof_chain_order_coherent": boundary_satisfied,
        "secret_fields_present": False,
        "decision_preselected": False,
        "boundary_mode": BOUNDARY_MODE,
        "boundary_owner": BOUNDARY_OWNER,
        "traceability_mode": TRACEABILITY_MODE,
        "traceability_status": TRACEABILITY_STATUS,
        "contract_version": CONTRACT_VERSION,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "traceability_identity": traceability_identity,
        "admission_identity": admission_identity,
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_selected": OPERATOR_DECISION_SELECTED,
        "operator_proof_package_operationally_issued": OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED,
        "second_assembly_created": SECOND_ASSEMBLY_CREATED,
        "second_readiness_surface_created": SECOND_READINESS_SURFACE_CREATED,
        "second_operator_review_surface_created": SECOND_OPERATOR_REVIEW_SURFACE_CREATED,
        "second_handoff_surface_created": SECOND_HANDOFF_SURFACE_CREATED,
        "second_presentation_surface_created": SECOND_PRESENTATION_SURFACE_CREATED,
        "second_evidence_surface_created": SECOND_EVIDENCE_SURFACE_CREATED,
        "second_archive_surface_created": SECOND_ARCHIVE_SURFACE_CREATED,
        "second_manifest_surface_created": SECOND_MANIFEST_SURFACE_CREATED,
        "review_queue_created": REVIEW_QUEUE_CREATED,
        "review_queue_entry_created": REVIEW_QUEUE_ENTRY_CREATED,
        "ui_surface_created": UI_SURFACE_CREATED,
        "presentation_rendered": PRESENTATION_RENDERED,
        "archive_written": ARCHIVE_WRITTEN,
        "manifest_written": MANIFEST_WRITTEN,
        "replay_executed": REPLAY_EXECUTED,
        "admission_executed": ADMISSION_EXECUTED,
        "authority_lift": AUTHORITY_LIFT,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "boundary_result_digest": (
            compute_boundary_result_digest(
                boundary_input,
                durable_evidence_traceability_boundary_satisfied=boundary_satisfied,
                traceability_identity=traceability_identity,
            )
            if boundary_satisfied and traceability_identity is not None
            else None
        ),
        "pe36_boundary_input_digest": computed_pe36_input,
        "pe36_boundary_result_digest": computed_pe36_result,
        "pe35_boundary_input_digest": computed_pe35_input,
        "pe34_handoff_digest": computed_pe34,
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


def default_minimal_pe36_proof_binding(
    pe36_boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> Pe36BoundaryProofBinding:
    """Build canonical PE-36 proof binding from explicit boundary input evaluation."""
    pe36_result = evaluate_operator_review_admission_presentation_boundary(pe36_boundary_input)
    return Pe36BoundaryProofBinding(
        boundary_owner=PE36_BOUNDARY_OWNER,
        source_revision=pe36_boundary_input.pe35_boundary_input.pe34_handoff.source_revision,
        boundary_input_digest=compute_pe36_boundary_input_digest(pe36_boundary_input),
        boundary_result_digest=pe36_result["boundary_result_digest"],
        presentation_projection_digest=pe36_result["presentation_projection_digest"],
        operator_review_admission_presentation_boundary_satisfied=pe36_result[
            "operator_review_admission_presentation_boundary_satisfied"
        ],
    )


def default_minimal_pe16_archive_binding(
    pe36_boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> Pe16ArchiveManifestBinding:
    """Build canonical PE-16 archive/manifest binding from handoff evidence chain."""
    pe34 = pe36_boundary_input.pe35_boundary_input.pe34_handoff
    evidence = pe34.pe19_undecided_review_input.review_input.evidence_chain
    return Pe16ArchiveManifestBinding(
        archive_owner=ARCHIVE_CONTRACT_VERSION,
        source_revision=pe34.source_revision,
        archive_identity=evidence.archive_identity,
        archive_manifest_digest=evidence.archive_manifest_digest,
        packet_digest=evidence.packet_digest,
        input_capture_digest=evidence.input_capture_digest,
        replay_manifest_digest=evidence.replay_manifest_digest,
    )


def default_minimal_pe19_pe20_review_proof_binding(
    pe36_boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> Pe19Pe20OperatorReviewProofBinding:
    """Build canonical PE-19/PE-20 operator-review proof binding from handoff chain."""
    pe34 = pe36_boundary_input.pe35_boundary_input.pe34_handoff
    review_input = pe34.pe19_undecided_review_input.review_input
    review_input_digest = compute_review_input_digest(review_input)
    package_binding_digest = pe34.pe20_undecided_package_eligibility.review_input_digest
    return Pe19Pe20OperatorReviewProofBinding(
        review_input_owner=PE19_CONTRACT_VERSION,
        package_owner=PE20_CONTRACT_VERSION,
        source_revision=pe34.source_revision,
        review_input_digest=review_input_digest,
        package_binding_digest=package_binding_digest,
        operator_review_proof_identity=compute_operator_review_proof_identity(
            review_input_owner=PE19_CONTRACT_VERSION,
            package_owner=PE20_CONTRACT_VERSION,
            source_revision=pe34.source_revision,
            review_input_digest=review_input_digest,
            package_binding_digest=package_binding_digest,
        ),
    )


def default_minimal_proof_chain_binding(
    pe36_boundary_input: OperatorReviewAdmissionPresentationBoundaryInput,
) -> Pe33Pe36ProofChainBinding:
    """Build canonical PE-33..PE-36 proof chain binding from explicit evaluations."""
    pe35_input = pe36_boundary_input.pe35_boundary_input
    pe34 = pe35_input.pe34_handoff
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    pe36_result = evaluate_operator_review_admission_presentation_boundary(pe36_boundary_input)
    pe35_result_digest = pe35_result["boundary_result_digest"]
    pe36_result_digest = pe36_result["boundary_result_digest"]
    pe36_projection_digest = pe36_result["presentation_projection_digest"]
    if pe35_result_digest is None or pe36_result_digest is None or pe36_projection_digest is None:
        raise ValueError("PE-35/PE-36 result digests required for proof chain binding")
    return Pe33Pe36ProofChainBinding(
        pe33_integration_proof_digest=pe34.pe33_coherence_proof.integration_proof_digest,
        pe34_handoff_digest=compute_pe34_boundary_input_digest(pe34),
        pe35_boundary_input_digest=compute_pe35_boundary_input_digest(pe35_input),
        pe35_boundary_result_digest=pe35_result_digest,
        pe36_boundary_input_digest=compute_pe36_boundary_input_digest(pe36_boundary_input),
        pe36_boundary_result_digest=pe36_result_digest,
        pe36_presentation_projection_digest=pe36_projection_digest,
    )


def default_minimal_boundary_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    handoff_id: str = "operator-review-handoff-boundary-001",
    instrument: str = "PF_ETHUSD",
    review_identity: str = "glb-016-bounded-futures-testnet-operator-review",
    operator_name_legibility: str | None = EXPECTED_OPERATOR_NAME,
    packet_digest: str = "a" * 64,
    input_capture_digest: str = "b" * 64,
    replay_manifest_digest: str = "c" * 64,
    archive_manifest_digest: str = "e" * 64,
    source_state_digest: str = "f" * 64,
) -> DurableEvidenceTraceabilityBoundaryInput:
    """Minimal valid futures-generic PE-37 traceability boundary input for offline tests."""
    from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
        default_minimal_boundary_input as default_minimal_pe35_boundary_input,
    )
    from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
        default_minimal_handoff_boundary_input,
    )
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        default_minimal_operator_review_input,
    )
    from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
        COMPLETENESS_CONTRACT_VERSION,
    )

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
    pe34_handoff = default_minimal_handoff_boundary_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        handoff_id=handoff_id,
        instrument=instrument,
        lifecycle_state_digest=source_state_digest,
        review_input=review_input,
        operator_name_legibility=operator_name_legibility,
    )
    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe35_input = default_minimal_pe35_boundary_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        handoff_id=handoff_id,
        instrument=instrument,
        review_identity=review_identity,
    )
    pe35_input = replace(
        pe35_input,
        pe34_handoff=pe34_handoff,
        canonical_current=replace(
            pe35_input.canonical_current,
            source_revision=source_revision,
            pe33_integration_proof_digest=pe34_handoff.pe33_coherence_proof.integration_proof_digest,
            pe34_handoff_digest=pe34_digest,
            replay_manifest_digest=replay_manifest_digest,
            archive_manifest_digest=archive_manifest_digest,
        ),
        lifecycle_metadata=replace(
            pe35_input.lifecycle_metadata,
            handoff_digest=pe34_digest,
            review_identity=review_identity,
        ),
    )
    pe36_input = OperatorReviewAdmissionPresentationBoundaryInput(
        pe35_boundary_input=pe35_input,
        pe35_proof=default_minimal_pe35_proof_binding(pe35_input),
        operator_name_legibility=operator_name_legibility,
    )
    return DurableEvidenceTraceabilityBoundaryInput(
        pe36_boundary_input=pe36_input,
        pe36_proof=default_minimal_pe36_proof_binding(pe36_input),
        pe16_archive_binding=default_minimal_pe16_archive_binding(pe36_input),
        pe19_pe20_review_proof=default_minimal_pe19_pe20_review_proof_binding(pe36_input),
        proof_chain=default_minimal_proof_chain_binding(pe36_input),
    )
