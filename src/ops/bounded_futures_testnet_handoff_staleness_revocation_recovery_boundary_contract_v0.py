"""Bounded Futures Testnet handoff staleness, revocation and recovery boundary (v0, PE-35).

Deterministic, offline, explicit-input-only fail-closed negative guard over the
existing PE-34 operator-review handoff boundary. Detects stale proofs, source-revision
drift, digest drift, manifest drift, supersession, revocation, and invalid recovery
without persisting, revoking, reactivating, or granting authority.

Static boundary guard only — no operator review, no operator decision, no operative
proof-package issuance, no closure execution, no revocation execution, no recovery
execution, no authority lift, network, testnet, runtime, credentials, orders, or
exchange access.
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
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
    HANDOFF_OWNER as PE34_HANDOFF_OWNER,
    OperatorReviewHandoffBoundaryInput,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
    default_minimal_handoff_boundary_input,
    evaluate_operator_review_handoff_boundary,
    validate_operator_review_handoff_boundary_input,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
)

PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_HANDOFF_STALENESS_REVOCATION_RECOVERY_BOUNDARY_CONTRACT_V0=true"
)
CONTRACT_VERSION = "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

BOUNDARY_MODE = "static_handoff_staleness_revocation_recovery_boundary_guard_only"
BOUNDARY_OWNER = CONTRACT_VERSION

CONTRACT_IMPLEMENTATION_ONLY = True
REVOCATION_EXECUTED = False
RECOVERY_EXECUTED = False
OPERATOR_REVIEW_EXECUTED = False
OPERATOR_DECISION_SELECTED = False
OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED = False
SECOND_ASSEMBLY_CREATED = False
SECOND_READINESS_SURFACE_CREATED = False
SECOND_OPERATOR_REVIEW_SURFACE_CREATED = False
SECOND_HANDOFF_SURFACE_CREATED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

HANDOFF_STATE_CURRENT = "current"
HANDOFF_STATE_STALE = "stale"
HANDOFF_STATE_SUPERSEDED = "superseded"
HANDOFF_STATE_REVOKED = "revoked"
HANDOFF_STATE_RECOVERY_REQUIRED = "recovery_required"
HANDOFF_STATE_RECOVERED = "recovered"

ALLOWED_HANDOFF_LIFECYCLE_STATES = frozenset(
    {
        HANDOFF_STATE_CURRENT,
        HANDOFF_STATE_STALE,
        HANDOFF_STATE_SUPERSEDED,
        HANDOFF_STATE_REVOKED,
        HANDOFF_STATE_RECOVERY_REQUIRED,
        HANDOFF_STATE_RECOVERED,
    }
)

INVALIDATION_REASON_STALE = "stale"
INVALIDATION_REASON_SUPERSEDED = "superseded"
INVALIDATION_REASON_REVOKED = "revoked"
INVALIDATION_REASON_SOURCE_REVISION_DRIFT = "source_revision_drift"
INVALIDATION_REASON_PROOF_DIGEST_DRIFT = "proof_digest_drift"
INVALIDATION_REASON_MANIFEST_DRIFT = "manifest_drift"
INVALIDATION_REASON_REVIEW_INPUT_DRIFT = "review_input_drift"
INVALIDATION_REASON_PACKAGE_BINDING_DRIFT = "package_binding_drift"
INVALIDATION_REASON_CLOSURE_BINDING_DRIFT = "closure_binding_drift"

ALLOWED_INVALIDATION_REASONS = frozenset(
    {
        INVALIDATION_REASON_STALE,
        INVALIDATION_REASON_SUPERSEDED,
        INVALIDATION_REASON_REVOKED,
        INVALIDATION_REASON_SOURCE_REVISION_DRIFT,
        INVALIDATION_REASON_PROOF_DIGEST_DRIFT,
        INVALIDATION_REASON_MANIFEST_DRIFT,
        INVALIDATION_REASON_REVIEW_INPUT_DRIFT,
        INVALIDATION_REASON_PACKAGE_BINDING_DRIFT,
        INVALIDATION_REASON_CLOSURE_BINDING_DRIFT,
    }
)


@dataclass(frozen=True)
class CanonicalCurrentBindings:
    source_revision: str
    pe33_integration_proof_digest: str
    pe34_handoff_digest: str
    replay_manifest_digest: str | None = None
    archive_manifest_digest: str | None = None


@dataclass(frozen=True)
class HandoffLifecycleMetadata:
    lifecycle_state: str
    handoff_digest: str
    review_identity: str
    generation: int = 0


@dataclass(frozen=True)
class SupersessionLink:
    supersession_owner: str
    source_revision: str
    review_identity: str
    predecessor_review_input_digest: str
    successor_review_input_digest: str
    predecessor_handoff_digest: str
    successor_handoff_digest: str
    generation: int


@dataclass(frozen=True)
class RevocationProofBinding:
    revocation_owner: str
    source_revision: str
    target_handoff_digest: str
    revocation_reason: str


@dataclass(frozen=True)
class RecoveryProofBinding:
    recovery_owner: str
    source_revision: str
    invalidated_predecessor_handoff_digest: str
    invalidation_reason: str
    new_handoff_digest: str
    new_pe33_integration_proof_digest: str
    new_pe19_review_input_digest: str
    new_pe20_review_input_digest: str
    new_pe25_closure_result_digest: str
    recovery_generation: int
    new_review_identity: str | None = None


@dataclass(frozen=True)
class HandoffStalenessRevocationRecoveryBoundaryInput:
    pe34_handoff: OperatorReviewHandoffBoundaryInput
    canonical_current: CanonicalCurrentBindings
    lifecycle_metadata: HandoffLifecycleMetadata
    supersession_links: tuple[SupersessionLink, ...] = ()
    active_successor_handoff_digests: tuple[str, ...] = ()
    revocation_proofs: tuple[RevocationProofBinding, ...] = ()
    recovery_proof: RecoveryProofBinding | None = None
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


def _validate_canonical_current(bindings: CanonicalCurrentBindings) -> list[str]:
    fail_reasons: list[str] = []
    if not bindings.source_revision:
        fail_reasons.append("canonical_current: source_revision required")
    elif not _valid_commit_sha(bindings.source_revision):
        fail_reasons.append(
            "canonical_current: source_revision must be full 40-char lowercase commit SHA"
        )
    if not bindings.pe33_integration_proof_digest:
        fail_reasons.append("canonical_current: pe33_integration_proof_digest required")
    elif not _valid_sha256_digest(bindings.pe33_integration_proof_digest):
        fail_reasons.append(
            "canonical_current: pe33_integration_proof_digest must be 64-char lowercase sha256 hex"
        )
    if not bindings.pe34_handoff_digest:
        fail_reasons.append("canonical_current: pe34_handoff_digest required")
    elif not _valid_sha256_digest(bindings.pe34_handoff_digest):
        fail_reasons.append(
            "canonical_current: pe34_handoff_digest must be 64-char lowercase sha256 hex"
        )
    if bindings.replay_manifest_digest is not None and not _valid_sha256_digest(
        bindings.replay_manifest_digest
    ):
        fail_reasons.append(
            "canonical_current: replay_manifest_digest must be 64-char lowercase sha256 hex"
        )
    if bindings.archive_manifest_digest is not None and not _valid_sha256_digest(
        bindings.archive_manifest_digest
    ):
        fail_reasons.append(
            "canonical_current: archive_manifest_digest must be 64-char lowercase sha256 hex"
        )
    return fail_reasons


def _validate_lifecycle_metadata(metadata: HandoffLifecycleMetadata) -> list[str]:
    fail_reasons: list[str] = []
    if metadata.lifecycle_state not in ALLOWED_HANDOFF_LIFECYCLE_STATES:
        fail_reasons.append(
            f"lifecycle_metadata: lifecycle_state must be one of {sorted(ALLOWED_HANDOFF_LIFECYCLE_STATES)!r}"
        )
    if not metadata.handoff_digest:
        fail_reasons.append("lifecycle_metadata: handoff_digest required")
    elif not _valid_sha256_digest(metadata.handoff_digest):
        fail_reasons.append(
            "lifecycle_metadata: handoff_digest must be 64-char lowercase sha256 hex"
        )
    if not metadata.review_identity:
        fail_reasons.append("lifecycle_metadata: review_identity required")
    if metadata.generation < 0:
        fail_reasons.append("lifecycle_metadata: generation must be non-negative")
    return fail_reasons


def _validate_supersession_link(link: SupersessionLink) -> list[str]:
    fail_reasons: list[str] = []
    if link.supersession_owner != CONTRACT_VERSION:
        fail_reasons.append(f"supersession_link: supersession_owner must be {CONTRACT_VERSION!r}")
    if not link.source_revision or not _valid_commit_sha(link.source_revision):
        fail_reasons.append(
            "supersession_link: source_revision must be full 40-char lowercase commit SHA"
        )
    if not link.review_identity:
        fail_reasons.append("supersession_link: review_identity required")
    for field_name in (
        "predecessor_review_input_digest",
        "successor_review_input_digest",
        "predecessor_handoff_digest",
        "successor_handoff_digest",
    ):
        value = getattr(link, field_name)
        if not value or not _valid_sha256_digest(value):
            fail_reasons.append(f"supersession_link: {field_name} must be 64-char sha256 hex")
    if link.predecessor_handoff_digest == link.successor_handoff_digest:
        fail_reasons.append("supersession_link: self-supersession not allowed")
    if link.predecessor_review_input_digest == link.successor_review_input_digest:
        fail_reasons.append("supersession_link: identical predecessor/successor review digests")
    if link.generation < 0:
        fail_reasons.append("supersession_link: generation must be non-negative")
    return fail_reasons


def _validate_revocation_proof(proof: RevocationProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if proof.revocation_owner != CONTRACT_VERSION:
        fail_reasons.append(f"revocation_proof: revocation_owner must be {CONTRACT_VERSION!r}")
    if not proof.source_revision or not _valid_commit_sha(proof.source_revision):
        fail_reasons.append(
            "revocation_proof: source_revision must be full 40-char lowercase commit SHA"
        )
    if not proof.target_handoff_digest or not _valid_sha256_digest(proof.target_handoff_digest):
        fail_reasons.append(
            "revocation_proof: target_handoff_digest must be 64-char lowercase sha256 hex"
        )
    if not proof.revocation_reason:
        fail_reasons.append("revocation_proof: revocation_reason required")
    elif proof.revocation_reason not in ALLOWED_INVALIDATION_REASONS:
        fail_reasons.append(
            f"revocation_proof: revocation_reason must be one of {sorted(ALLOWED_INVALIDATION_REASONS)!r}"
        )
    return fail_reasons


def _validate_recovery_proof(proof: RecoveryProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    if proof.recovery_owner != CONTRACT_VERSION:
        fail_reasons.append(f"recovery_proof: recovery_owner must be {CONTRACT_VERSION!r}")
    if not proof.source_revision or not _valid_commit_sha(proof.source_revision):
        fail_reasons.append(
            "recovery_proof: source_revision must be full 40-char lowercase commit SHA"
        )
    if not proof.invalidated_predecessor_handoff_digest or not _valid_sha256_digest(
        proof.invalidated_predecessor_handoff_digest
    ):
        fail_reasons.append(
            "recovery_proof: invalidated_predecessor_handoff_digest must be 64-char sha256 hex"
        )
    if proof.invalidation_reason not in ALLOWED_INVALIDATION_REASONS:
        fail_reasons.append(
            f"recovery_proof: invalidation_reason must be one of {sorted(ALLOWED_INVALIDATION_REASONS)!r}"
        )
    for field_name in (
        "new_handoff_digest",
        "new_pe33_integration_proof_digest",
        "new_pe19_review_input_digest",
        "new_pe20_review_input_digest",
        "new_pe25_closure_result_digest",
    ):
        value = getattr(proof, field_name)
        if not value or not _valid_sha256_digest(value):
            fail_reasons.append(f"recovery_proof: {field_name} must be 64-char sha256 hex")
    if proof.recovery_generation < 1:
        fail_reasons.append("recovery_proof: recovery_generation must be >= 1")
    return fail_reasons


def _detect_supersession_cycles(links: tuple[SupersessionLink, ...]) -> list[str]:
    fail_reasons: list[str] = []
    graph: dict[str, str] = {}
    for link in links:
        pred = link.predecessor_handoff_digest
        succ = link.successor_handoff_digest
        if pred in graph and graph[pred] != succ:
            fail_reasons.append(
                "supersession_links: multiple active successors for same predecessor"
            )
        graph[pred] = succ

    visited: set[str] = set()
    for start in graph:
        seen: set[str] = set()
        current = start
        while current in graph:
            if current in seen:
                fail_reasons.append("supersession_links: cycle detected")
                break
            seen.add(current)
            current = graph[current]
        visited.update(seen)
    return _sorted_unique(fail_reasons)


def validate_handoff_staleness_revocation_recovery_boundary_input(
    boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-35 boundary guard bindings."""
    fail_reasons: list[str] = []

    pe34_handoff = boundary_input.pe34_handoff
    fail_reasons.extend(validate_operator_review_handoff_boundary_input(pe34_handoff))
    fail_reasons.extend(
        _validate_instrument_scope(pe34_handoff.instrument, pe34_handoff.market_type)
    )
    fail_reasons.extend(_validate_canonical_current(boundary_input.canonical_current))
    fail_reasons.extend(_validate_lifecycle_metadata(boundary_input.lifecycle_metadata))

    for link in boundary_input.supersession_links:
        fail_reasons.extend(_validate_supersession_link(link))

    for digest in boundary_input.active_successor_handoff_digests:
        if not _valid_sha256_digest(digest):
            fail_reasons.append(
                "active_successor_handoff_digests: each digest must be 64-char sha256 hex"
            )

    for proof in boundary_input.revocation_proofs:
        fail_reasons.extend(_validate_revocation_proof(proof))

    if boundary_input.recovery_proof is not None:
        fail_reasons.extend(_validate_recovery_proof(boundary_input.recovery_proof))

    fail_reasons.extend(_detect_supersession_cycles(boundary_input.supersession_links))

    if boundary_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if boundary_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if boundary_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _boundary_input_dict(
    boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput,
) -> dict[str, Any]:
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        compute_review_input_digest,
    )

    pe34 = boundary_input.pe34_handoff
    pe19 = pe34.pe19_undecided_review_input
    return {
        "boundary_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "pe34_handoff_digest": compute_pe34_boundary_input_digest(pe34),
        "pe34_handoff_owner": PE34_HANDOFF_OWNER,
        "pe34_contract_version": PE34_CONTRACT_VERSION,
        "canonical_current": asdict(boundary_input.canonical_current),
        "lifecycle_metadata": asdict(boundary_input.lifecycle_metadata),
        "supersession_links": [asdict(link) for link in boundary_input.supersession_links],
        "active_successor_handoff_digests": list(boundary_input.active_successor_handoff_digests),
        "revocation_proofs": [asdict(proof) for proof in boundary_input.revocation_proofs],
        "recovery_proof": (
            asdict(boundary_input.recovery_proof)
            if boundary_input.recovery_proof is not None
            else None
        ),
        "pe33_integration_proof_digest": pe34.pe33_coherence_proof.integration_proof_digest,
        "pe19_review_input_digest": compute_review_input_digest(pe19.review_input),
        "pe20_review_input_digest": pe34.pe20_undecided_package_eligibility.review_input_digest,
        "pe25_closure_result_digest": pe34.pe25_cross_slice_closure.closure_result_digest,
        "source_revision": pe34.source_revision,
        "futures_only": boundary_input.futures_only,
        "environment": boundary_input.environment,
        "non_authorizing": boundary_input.non_authorizing,
    }


def serialize_boundary_input_canonical(
    boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput,
) -> str:
    return json.dumps(
        _boundary_input_dict(boundary_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_boundary_input_digest(
    boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput,
) -> str:
    return hashlib.sha256(
        serialize_boundary_input_canonical(boundary_input).encode("utf-8")
    ).hexdigest()


def compute_boundary_result_digest(
    boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput,
    *,
    handoff_staleness_revocation_recovery_boundary_satisfied: bool,
) -> str:
    payload = {
        "boundary_contract_version": CONTRACT_VERSION,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "boundary_mode": BOUNDARY_MODE,
        "boundary_owner": BOUNDARY_OWNER,
        "handoff_staleness_revocation_recovery_boundary_satisfied": (
            handoff_staleness_revocation_recovery_boundary_satisfied
        ),
        "hash_algorithm": HASH_ALGORITHM,
        "package_marker": PACKAGE_MARKER,
        "pe34_handoff_digest": compute_pe34_boundary_input_digest(boundary_input.pe34_handoff),
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": boundary_input.pe34_handoff.source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def evaluate_handoff_staleness_revocation_recovery_boundary(
    boundary_input: HandoffStalenessRevocationRecoveryBoundaryInput,
    *,
    loose_recovered_flag: bool = False,
    loose_current_flag: bool = False,
    revoked_flag_cleared: bool = False,
    superseded_flag_cleared: bool = False,
    stale_flag_cleared: bool = False,
    implicit_reactivation: bool = False,
) -> dict[str, Any]:
    """Evaluate explicit PE-35 negative guard; never grants authority or executes recovery."""
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        compute_review_input_digest,
    )

    fail_reasons = validate_handoff_staleness_revocation_recovery_boundary_input(boundary_input)

    pe34_handoff = boundary_input.pe34_handoff
    pe34_result = evaluate_operator_review_handoff_boundary(pe34_handoff)
    if not pe34_result["operator_review_handoff_boundary_satisfied"]:
        fail_reasons.extend(pe34_result["fail_reasons"])

    computed_pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    canonical = boundary_input.canonical_current
    lifecycle = boundary_input.lifecycle_metadata
    pe33_bound = pe34_handoff.pe33_coherence_proof.integration_proof_digest
    pe19_review_digest = compute_review_input_digest(
        pe34_handoff.pe19_undecided_review_input.review_input
    )
    pe20_review_digest = pe34_handoff.pe20_undecided_package_eligibility.review_input_digest
    pe25_closure_digest = pe34_handoff.pe25_cross_slice_closure.closure_result_digest
    evidence = pe34_handoff.pe19_undecided_review_input.review_input.evidence_chain

    if lifecycle.handoff_digest != computed_pe34_digest:
        fail_reasons.append("lifecycle_metadata: handoff_digest mismatch with PE-34 handoff")

    if canonical.pe34_handoff_digest != computed_pe34_digest:
        fail_reasons.append("canonical_current: pe34_handoff_digest mismatch with PE-34 handoff")

    if canonical.pe33_integration_proof_digest != pe33_bound:
        fail_reasons.append("canonical_current: pe33_integration_proof_digest mismatch")

    if canonical.source_revision != pe34_handoff.source_revision:
        fail_reasons.append("canonical_current: source_revision mismatch with PE-34 handoff")

    if pe34_handoff.source_revision != canonical.source_revision:
        fail_reasons.append("source_revision drift: PE-34 handoff below canonical current")

    if canonical.replay_manifest_digest is not None:
        if evidence.replay_manifest_digest != canonical.replay_manifest_digest:
            fail_reasons.append("manifest drift: replay_manifest_digest mismatch")
    if canonical.archive_manifest_digest is not None:
        if evidence.archive_manifest_digest != canonical.archive_manifest_digest:
            fail_reasons.append("manifest drift: archive_manifest_digest mismatch")

    if lifecycle.lifecycle_state == HANDOFF_STATE_STALE:
        fail_reasons.append("handoff lifecycle_state is stale")
    elif lifecycle.lifecycle_state == HANDOFF_STATE_SUPERSEDED:
        fail_reasons.append("handoff lifecycle_state is superseded")
    elif lifecycle.lifecycle_state == HANDOFF_STATE_REVOKED:
        fail_reasons.append("handoff lifecycle_state is revoked")
    elif lifecycle.lifecycle_state == HANDOFF_STATE_RECOVERY_REQUIRED:
        fail_reasons.append("handoff lifecycle_state requires recovery")
    elif lifecycle.lifecycle_state == HANDOFF_STATE_RECOVERED:
        if boundary_input.recovery_proof is None:
            fail_reasons.append(
                "recovered lifecycle_state requires canonical recovery_proof binding"
            )
    elif lifecycle.lifecycle_state != HANDOFF_STATE_CURRENT:
        fail_reasons.append(f"unknown lifecycle_state {lifecycle.lifecycle_state!r}")

    matching_revocations = [
        proof
        for proof in boundary_input.revocation_proofs
        if proof.target_handoff_digest == computed_pe34_digest
    ]
    if matching_revocations:
        fail_reasons.append("revocation_proof binds to current PE-34 handoff digest")

    revocation_by_target: dict[str, list[RevocationProofBinding]] = {}
    for proof in boundary_input.revocation_proofs:
        revocation_by_target.setdefault(proof.target_handoff_digest, []).append(proof)
    for target, proofs in revocation_by_target.items():
        reasons = {proof.revocation_reason for proof in proofs}
        if len(proofs) > 1 and len(reasons) > 1:
            fail_reasons.append(f"contradictory revocation proofs for handoff digest {target}")

    if boundary_input.active_successor_handoff_digests:
        if computed_pe34_digest in boundary_input.active_successor_handoff_digests:
            fail_reasons.append("current handoff digest listed as active successor")
        fail_reasons.append("active successor handoff digests present for review identity")

    for link in boundary_input.supersession_links:
        if link.review_identity != lifecycle.review_identity:
            fail_reasons.append("supersession_link: review_identity mismatch")
        if link.predecessor_handoff_digest == computed_pe34_digest:
            fail_reasons.append("handoff superseded by canonical successor link")
        if (
            link.successor_handoff_digest == computed_pe34_digest
            and link.predecessor_handoff_digest != computed_pe34_digest
        ):
            if link.predecessor_review_input_digest == pe19_review_digest:
                fail_reasons.append("supersession_link: wrong predecessor review input digest")

    recovery = boundary_input.recovery_proof
    if recovery is not None:
        if recovery.new_handoff_digest != computed_pe34_digest:
            fail_reasons.append("recovery_proof: new_handoff_digest mismatch with PE-34 handoff")
        if recovery.new_pe33_integration_proof_digest != pe33_bound:
            fail_reasons.append("recovery_proof: new_pe33_integration_proof_digest mismatch")
        if recovery.new_pe19_review_input_digest != pe19_review_digest:
            fail_reasons.append("recovery_proof: new_pe19_review_input_digest mismatch")
        if recovery.new_pe20_review_input_digest != pe20_review_digest:
            fail_reasons.append("recovery_proof: new_pe20_review_input_digest mismatch")
        if recovery.new_pe25_closure_result_digest != pe25_closure_digest:
            fail_reasons.append("recovery_proof: new_pe25_closure_result_digest mismatch")
        if recovery.invalidated_predecessor_handoff_digest == computed_pe34_digest:
            fail_reasons.append("recovery_proof: recovery cycle (predecessor equals current)")
        if recovery.source_revision != pe34_handoff.source_revision:
            fail_reasons.append("recovery_proof: source_revision mismatch")
        if recovery.recovery_generation < 1:
            fail_reasons.append("recovery_proof: recovery_generation invalid")

        predecessor_invalidated = False
        for proof in boundary_input.revocation_proofs:
            if proof.target_handoff_digest == recovery.invalidated_predecessor_handoff_digest:
                predecessor_invalidated = True
        for link in boundary_input.supersession_links:
            if link.predecessor_handoff_digest == recovery.invalidated_predecessor_handoff_digest:
                predecessor_invalidated = True
        if not predecessor_invalidated:
            fail_reasons.append(
                "recovery_proof: invalidated_predecessor_handoff_digest not evidenced by "
                "revocation or supersession binding"
            )

    if loose_recovered_flag:
        fail_reasons.append("loose recovered=true cannot replace recovery_proof binding")
    if loose_current_flag:
        fail_reasons.append("loose current=true cannot replace lifecycle_state binding")
    if revoked_flag_cleared:
        fail_reasons.append("clearing revocation flag without recovery_proof does not reactivate")
    if superseded_flag_cleared:
        fail_reasons.append("clearing superseded flag without recovery_proof does not reactivate")
    if stale_flag_cleared:
        fail_reasons.append("clearing stale flag without recovery_proof does not reactivate")
    if implicit_reactivation:
        fail_reasons.append("implicit reactivation via metadata update is not allowed")

    fail_reasons = _sorted_unique(fail_reasons)
    structural_pass = len(fail_reasons) == 0
    boundary_satisfied = (
        structural_pass
        and lifecycle.lifecycle_state == HANDOFF_STATE_CURRENT
        and not matching_revocations
        and not boundary_input.active_successor_handoff_digests
    )

    return {
        "boundary_pass": structural_pass,
        "handoff_staleness_revocation_recovery_boundary_satisfied": boundary_satisfied,
        "pe35_handoff_staleness_revocation_recovery_boundary_static_proven": boundary_satisfied,
        "handoff_current": lifecycle.lifecycle_state == HANDOFF_STATE_CURRENT
        and boundary_satisfied,
        "handoff_stale": lifecycle.lifecycle_state == HANDOFF_STATE_STALE,
        "handoff_superseded": lifecycle.lifecycle_state == HANDOFF_STATE_SUPERSEDED,
        "handoff_revoked": lifecycle.lifecycle_state == HANDOFF_STATE_REVOKED
        or bool(matching_revocations),
        "recovery_required": lifecycle.lifecycle_state == HANDOFF_STATE_RECOVERY_REQUIRED,
        "recovery_proof_valid": recovery is not None and structural_pass,
        "boundary_mode": BOUNDARY_MODE,
        "boundary_owner": BOUNDARY_OWNER,
        "contract_version": CONTRACT_VERSION,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "revocation_executed": REVOCATION_EXECUTED,
        "recovery_executed": RECOVERY_EXECUTED,
        "operator_review_executed": OPERATOR_REVIEW_EXECUTED,
        "operator_decision_selected": OPERATOR_DECISION_SELECTED,
        "operator_proof_package_operationally_issued": OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED,
        "second_assembly_created": SECOND_ASSEMBLY_CREATED,
        "second_readiness_surface_created": SECOND_READINESS_SURFACE_CREATED,
        "second_operator_review_surface_created": SECOND_OPERATOR_REVIEW_SURFACE_CREATED,
        "second_handoff_surface_created": SECOND_HANDOFF_SURFACE_CREATED,
        "authority_lift": AUTHORITY_LIFT,
        "boundary_input_digest": compute_boundary_input_digest(boundary_input),
        "boundary_result_digest": (
            compute_boundary_result_digest(
                boundary_input,
                handoff_staleness_revocation_recovery_boundary_satisfied=boundary_satisfied,
            )
            if boundary_satisfied
            else None
        ),
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


def default_minimal_boundary_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    handoff_id: str = "operator-review-handoff-boundary-001",
    instrument: str = "PF_ETHUSD",
    review_identity: str = "glb-016-bounded-futures-testnet-operator-review",
    generation: int = 0,
) -> HandoffStalenessRevocationRecoveryBoundaryInput:
    """Minimal valid futures-generic PE-35 boundary input for offline tests."""
    from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
        compute_review_input_digest,
    )

    pe34_handoff = default_minimal_handoff_boundary_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        handoff_id=handoff_id,
        instrument=instrument,
    )
    pe34_digest = compute_pe34_boundary_input_digest(pe34_handoff)
    pe33_digest = pe34_handoff.pe33_coherence_proof.integration_proof_digest
    evidence = pe34_handoff.pe19_undecided_review_input.review_input.evidence_chain

    return HandoffStalenessRevocationRecoveryBoundaryInput(
        pe34_handoff=pe34_handoff,
        canonical_current=CanonicalCurrentBindings(
            source_revision=source_revision,
            pe33_integration_proof_digest=pe33_digest,
            pe34_handoff_digest=pe34_digest,
            replay_manifest_digest=evidence.replay_manifest_digest,
            archive_manifest_digest=evidence.archive_manifest_digest,
        ),
        lifecycle_metadata=HandoffLifecycleMetadata(
            lifecycle_state=HANDOFF_STATE_CURRENT,
            handoff_digest=pe34_digest,
            review_identity=review_identity,
            generation=generation,
        ),
    )
