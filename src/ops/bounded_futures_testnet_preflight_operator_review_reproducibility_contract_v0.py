"""Bounded Futures Testnet preflight operator-review reproducibility (v0, PE-19).

Deterministic, offline operator-review input package and explicit decision-record
binding for bounded futures-testnet preflight GLB-016 static reproducibility.
Composes PE-13 through PE-18 evidence bindings without implicit authority,
credentials, network, or exchange access.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION as PE13_CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    HASH_ALGORITHM,
    REPLAY_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_source_state_capture_contract_v0 import (
    CONTRACT_VERSION as PE18_CONTRACT_VERSION,
)

PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_OPERATOR_REVIEW_REPRODUCIBILITY_CONTRACT_V0=true"
)
CONTRACT_VERSION = "bounded_futures_testnet_preflight_operator_review_reproducibility.v0"
REVIEW_INPUT_SCHEMA_VERSION = (
    "bounded_futures_testnet_preflight_operator_review_input.serialization.v0"
)
DECISION_CONTRACT_VERSION = (
    "bounded_futures_testnet_preflight_operator_decision_record.serialization.v0"
)

REVIEW_INPUT_VALID = "valid"
REVIEW_INPUT_REJECTED = "rejected"
DECISION_VALID = "valid"
DECISION_REJECTED = "rejected"
REVIEW_PROOF_VALID = "valid"
REVIEW_PROOF_REJECTED = "rejected"

REPOSITORY_IDENTITY = "Peak_Trade"
EXPECTED_OPERATOR_NAME = "Frank Rauter"
REVIEWED_SCOPE = "glb-016_bounded_futures_testnet_preflight_reproducibility"

DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW = "approve_for_separate_next_phase_review"
DECISION_REJECT = "reject"
DECISION_REQUEST_CHANGES = "request_changes"

ALLOWED_DECISIONS = frozenset(
    {
        DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
        DECISION_REJECT,
        DECISION_REQUEST_CHANGES,
    }
)

FORBIDDEN_AUTHORITY_DECISIONS = frozenset(
    {
        "approve",
        "execute",
        "arm",
        "live",
        "zero_order_go",
        "network_go",
        "testnet_go",
    }
)

REASON_EVIDENCE_COMPLETE = "evidence_complete"
REASON_EVIDENCE_INCOMPLETE = "evidence_incomplete"
REASON_DIGEST_MISMATCH = "digest_mismatch"
REASON_SOURCE_STATE_INVALID = "source_state_invalid"
REASON_CHANGES_REQUIRED = "changes_required"
REASON_POLICY_BLOCKED = "policy_blocked"

ALLOWED_REASON_CODES = frozenset(
    {
        REASON_EVIDENCE_COMPLETE,
        REASON_EVIDENCE_INCOMPLETE,
        REASON_DIGEST_MISMATCH,
        REASON_SOURCE_STATE_INVALID,
        REASON_CHANGES_REQUIRED,
        REASON_POLICY_BLOCKED,
    }
)

_DECISION_REASON_MATRIX: dict[str, frozenset[str]] = {
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW: frozenset({REASON_EVIDENCE_COMPLETE}),
    DECISION_REJECT: frozenset(
        {
            REASON_EVIDENCE_INCOMPLETE,
            REASON_DIGEST_MISMATCH,
            REASON_SOURCE_STATE_INVALID,
            REASON_POLICY_BLOCKED,
        }
    ),
    DECISION_REQUEST_CHANGES: frozenset({REASON_CHANGES_REQUIRED}),
}

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_KEY_FRAGMENTS = (
    "password",
    "secret_key",
    "private_key",
    "api_key",
    "apikey",
    "token_value",
    "hostname",
    "host_name",
    "machine_id",
    "process_id",
    "wall_clock",
    "timestamp",
    "username",
    "user_name",
)

_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"^/tmp(?:/|$)"),
    re.compile(r"(?i)(password|secret|api[_-]?key|bearer\s)"),
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe13_packet": PE13_CONTRACT_VERSION,
    "pe14_builder": BUILDER_VERSION,
    "pe15_replay": REPLAY_CONTRACT_VERSION,
    "pe16_archive": ARCHIVE_CONTRACT_VERSION,
    "pe17_completeness_truth": COMPLETENESS_CONTRACT_VERSION,
    "pe18_source_state_capture": PE18_CONTRACT_VERSION,
    "pe19_operator_review": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe13_packet: str
    pe14_builder: str
    pe15_replay: str
    pe16_archive: str
    pe17_completeness_truth: str
    pe18_source_state_capture: str
    pe19_operator_review: str


@dataclass(frozen=True)
class EvidenceChainBinding:
    packet_digest: str
    input_capture_digest: str
    replay_manifest_digest: str
    archive_identity: str
    archive_manifest_digest: str
    completeness_truth_identity: str
    source_state_digest: str
    manifest_verify_rc: int


@dataclass(frozen=True)
class SafetySnapshot:
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    network_allowed: bool
    operator_go_present: bool
    followup_run_gate: str


@dataclass(frozen=True)
class PreflightOperatorReviewInput:
    source_revision: str
    repository_identity: str
    contract_versions: ContractVersionsInput
    evidence_chain: EvidenceChainBinding
    reviewed_scope: str
    safety_snapshot: SafetySnapshot
    futures_only: bool
    environment: str
    non_authorizing: bool


@dataclass(frozen=True)
class OperatorDecisionRecord:
    source_revision: str
    operator_name: str
    decision: str
    reason_code: str
    structured_reason: str
    review_input_digest: str
    evidence_manifest_verify_rc: int
    non_authorizing: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _scan_forbidden_content(data: Any, *, prefix: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(fragment in key_lower for fragment in _FORBIDDEN_KEY_FRAGMENTS):
                errors.append(f"{prefix}: forbidden key {key!r}")
            errors.extend(
                _scan_forbidden_content(value, prefix=f"{prefix}.{key}" if prefix else str(key))
            )
    elif isinstance(data, list):
        for index, item in enumerate(data):
            errors.extend(_scan_forbidden_content(item, prefix=f"{prefix}[{index}]"))
    elif isinstance(data, str):
        for pattern in _FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(data):
                errors.append(f"{prefix}: forbidden value pattern detected")
                break
    return errors


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def _review_input_dict(review_input: PreflightOperatorReviewInput) -> dict[str, Any]:
    return {
        "review_contract_version": CONTRACT_VERSION,
        "review_input_schema_version": REVIEW_INPUT_SCHEMA_VERSION,
        "source_revision": review_input.source_revision,
        "repository_identity": review_input.repository_identity,
        "contract_versions": asdict(review_input.contract_versions),
        "evidence_chain": asdict(review_input.evidence_chain),
        "reviewed_scope": review_input.reviewed_scope,
        "safety_snapshot": asdict(review_input.safety_snapshot),
        "futures_only": review_input.futures_only,
        "environment": review_input.environment,
        "non_authorizing": review_input.non_authorizing,
    }


def serialize_review_input_canonical(review_input: PreflightOperatorReviewInput) -> str:
    """Deterministic JSON serialization with stable mapping order."""
    return json.dumps(_review_input_dict(review_input), sort_keys=True, separators=(",", ":"))


def compute_review_input_digest(review_input: PreflightOperatorReviewInput) -> str:
    """Deterministic SHA-256 digest of canonical review-input serialization."""
    return hashlib.sha256(
        serialize_review_input_canonical(review_input).encode("utf-8")
    ).hexdigest()


def validate_review_input(review_input: PreflightOperatorReviewInput) -> list[str]:
    """Fail-closed validation of explicit review-input bindings."""
    fail_reasons: list[str] = []
    fail_reasons.extend(_scan_forbidden_content(_review_input_dict(review_input)))

    if not review_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(review_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not review_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif review_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(review_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    evidence = review_input.evidence_chain
    for field_name, value in asdict(evidence).items():
        if field_name == "manifest_verify_rc":
            if value != 0:
                fail_reasons.append("evidence_chain: manifest_verify_rc must be 0")
            continue
        if not value:
            fail_reasons.append(f"evidence_chain: {field_name} required")
        elif field_name.endswith("_digest") and not _valid_sha256_digest(str(value)):
            fail_reasons.append(
                f"evidence_chain: {field_name} must be 64-char lowercase sha256 hex"
            )
    if evidence.completeness_truth_identity != COMPLETENESS_CONTRACT_VERSION:
        fail_reasons.append(
            f"evidence_chain: completeness_truth_identity must be {COMPLETENESS_CONTRACT_VERSION!r}"
        )

    if review_input.reviewed_scope != REVIEWED_SCOPE:
        fail_reasons.append(f"reviewed_scope must be {REVIEWED_SCOPE!r}")

    policy = review_input.safety_snapshot
    required_policy_bools = (
        ("preflight_remains_blocked", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("credentials_allowed", False),
        ("orders_allowed", False),
        ("scheduler_runtime_allowed", False),
        ("network_allowed", False),
        ("operator_go_present", False),
    )
    for field_name, expected in required_policy_bools:
        actual = getattr(policy, field_name)
        if actual is not expected:
            fail_reasons.append(f"safety_snapshot: {field_name} must be {expected}")
    if policy.followup_run_gate != FOLLOWUP_RUN_GATE:
        fail_reasons.append(f"safety_snapshot: followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")

    if review_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if review_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if review_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _decision_record_dict(
    decision_record: OperatorDecisionRecord,
    *,
    decision_record_digest: str | None = None,
) -> dict[str, Any]:
    payload = {
        "decision_contract_version": DECISION_CONTRACT_VERSION,
        "review_input_digest": decision_record.review_input_digest,
        "source_revision": decision_record.source_revision,
        "operator_name": decision_record.operator_name,
        "decision": decision_record.decision,
        "reason_code": decision_record.reason_code,
        "structured_reason": decision_record.structured_reason,
        "evidence_manifest_verify_rc": decision_record.evidence_manifest_verify_rc,
        "non_authorizing": decision_record.non_authorizing,
        "ready_for_operator_arming": decision_record.ready_for_operator_arming,
        "execution_authorized": decision_record.execution_authorized,
        "live_authorized": decision_record.live_authorized,
    }
    if decision_record_digest is not None:
        payload["decision_record_digest"] = decision_record_digest
    return payload


def serialize_decision_record_canonical(decision_record: OperatorDecisionRecord) -> str:
    """Deterministic JSON serialization excluding self-referential digest field."""
    return json.dumps(
        _decision_record_dict(decision_record),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_decision_record_digest(decision_record: OperatorDecisionRecord) -> str:
    """Deterministic SHA-256 digest of canonical decision-record serialization."""
    return hashlib.sha256(
        serialize_decision_record_canonical(decision_record).encode("utf-8")
    ).hexdigest()


def validate_decision_record(
    decision_record: OperatorDecisionRecord,
    *,
    review_input: PreflightOperatorReviewInput | None = None,
    expected_review_input_digest: str | None = None,
) -> list[str]:
    """Fail-closed validation of explicit operator decision record."""
    fail_reasons: list[str] = []
    fail_reasons.extend(_scan_forbidden_content(_decision_record_dict(decision_record)))

    if not decision_record.source_revision:
        fail_reasons.append("decision_record: source_revision required")
    elif not _valid_commit_sha(decision_record.source_revision):
        fail_reasons.append(
            "decision_record: source_revision must be full 40-char lowercase commit SHA"
        )
    if review_input is not None and decision_record.source_revision != review_input.source_revision:
        fail_reasons.append("decision_record: source_revision mismatch with review input")

    if not decision_record.operator_name:
        fail_reasons.append("decision_record: operator_name required")
    elif decision_record.operator_name != EXPECTED_OPERATOR_NAME:
        fail_reasons.append(f"decision_record: operator_name must be {EXPECTED_OPERATOR_NAME!r}")

    if not decision_record.decision:
        fail_reasons.append("decision_record: decision required")
    elif decision_record.decision in FORBIDDEN_AUTHORITY_DECISIONS:
        fail_reasons.append(
            f"decision_record: authority-verleihende decision {decision_record.decision!r}"
        )
    elif decision_record.decision not in ALLOWED_DECISIONS:
        fail_reasons.append(f"decision_record: unknown decision {decision_record.decision!r}")

    if not decision_record.reason_code:
        fail_reasons.append("decision_record: reason_code required")
    elif decision_record.reason_code not in ALLOWED_REASON_CODES:
        fail_reasons.append(f"decision_record: unknown reason_code {decision_record.reason_code!r}")
    elif decision_record.decision in ALLOWED_DECISIONS:
        allowed_reasons = _DECISION_REASON_MATRIX[decision_record.decision]
        if decision_record.reason_code not in allowed_reasons:
            fail_reasons.append(
                "decision_record: reason_code inconsistent with decision "
                f"{decision_record.decision!r}"
            )

    if not decision_record.structured_reason:
        fail_reasons.append("decision_record: structured_reason required")

    if not decision_record.review_input_digest:
        fail_reasons.append("decision_record: review_input_digest required")
    elif not _valid_sha256_digest(decision_record.review_input_digest):
        fail_reasons.append(
            "decision_record: review_input_digest must be 64-char lowercase sha256 hex"
        )
    elif review_input is not None:
        actual_digest = compute_review_input_digest(review_input)
        if decision_record.review_input_digest != actual_digest:
            fail_reasons.append("decision_record: review_input_digest mismatch")
    elif expected_review_input_digest is not None:
        if decision_record.review_input_digest != expected_review_input_digest:
            fail_reasons.append("decision_record: review_input_digest mismatch")

    if decision_record.evidence_manifest_verify_rc != 0:
        fail_reasons.append("decision_record: evidence_manifest_verify_rc must be 0")

    required_decision_bools = (
        ("non_authorizing", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
    )
    for field_name, expected in required_decision_bools:
        actual = getattr(decision_record, field_name)
        if actual is not expected:
            fail_reasons.append(f"decision_record: {field_name} must be {expected}")

    return _sorted_unique(fail_reasons)


def evaluate_operator_review(
    review_input: PreflightOperatorReviewInput,
    decision_record: OperatorDecisionRecord,
    *,
    review_input_digest: str | None = None,
    decision_record_digest: str | None = None,
) -> dict[str, Any]:
    """Evaluate review proof binding input and decision record; never grants authority."""
    input_errors = validate_review_input(review_input)
    input_valid = not input_errors
    computed_input_digest = compute_review_input_digest(review_input) if input_valid else None

    if review_input_digest is not None and computed_input_digest is not None:
        if review_input_digest != computed_input_digest:
            input_errors.append("review_input_digest mismatch")
            input_valid = False

    decision_errors = validate_decision_record(
        decision_record,
        review_input=review_input if input_valid else None,
        expected_review_input_digest=computed_input_digest,
    )
    decision_valid = not decision_errors
    computed_decision_digest = (
        compute_decision_record_digest(decision_record) if decision_valid else None
    )

    if decision_record_digest is not None and computed_decision_digest is not None:
        if decision_record_digest != computed_decision_digest:
            decision_errors.append("decision_record_digest mismatch")
            decision_valid = False

    validation_errors = _sorted_unique(input_errors + decision_errors)
    review_input_digest_matches = (
        input_valid
        and review_input_digest is not None
        and computed_input_digest == review_input_digest
    ) or (input_valid and review_input_digest is None)
    decision_record_digest_matches = (
        decision_valid
        and decision_record_digest is not None
        and computed_decision_digest == decision_record_digest
    ) or (decision_valid and decision_record_digest is None)

    operator_identity_valid = (
        decision_valid and decision_record.operator_name == EXPECTED_OPERATOR_NAME
    )
    source_revision_matches = (
        input_valid
        and decision_valid
        and review_input.source_revision == decision_record.source_revision
    )
    contract_versions_match = input_valid and all(
        getattr(review_input.contract_versions, field) == expected
        for field, expected in _EXPECTED_CONTRACT_VERSIONS.items()
    )
    evidence_manifest_verified = (
        input_valid
        and review_input.evidence_chain.manifest_verify_rc == 0
        and decision_record.evidence_manifest_verify_rc == 0
    )

    review_reproducible = (
        input_valid
        and decision_valid
        and operator_identity_valid
        and source_revision_matches
        and contract_versions_match
        and evidence_manifest_verified
        and not validation_errors
    )
    review_valid = review_reproducible

    blocking_requirements: list[str] = []
    if not review_valid:
        blocking_requirements.append("operator_review_proof")

    return {
        "review_contract_version": CONTRACT_VERSION,
        "review_proof_status": REVIEW_PROOF_VALID if review_valid else REVIEW_PROOF_REJECTED,
        "review_input_valid": input_valid,
        "review_input_digest": computed_input_digest,
        "review_input_digest_matches": review_input_digest_matches,
        "decision_record_valid": decision_valid,
        "decision_record_digest": computed_decision_digest,
        "decision_record_digest_matches": decision_record_digest_matches,
        "operator_identity_valid": operator_identity_valid,
        "source_revision_matches": source_revision_matches,
        "contract_versions_match": contract_versions_match,
        "evidence_manifest_verified": evidence_manifest_verified,
        "review_reproducible": review_reproducible,
        "review_valid": review_valid,
        "decision": decision_record.decision if decision_valid else None,
        "reason_code": decision_record.reason_code if decision_valid else None,
        "blocking_requirements": blocking_requirements,
        "validation_errors": validation_errors,
        "non_authorizing": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }


def explicit_contract_proof_kwargs(review_proof: dict[str, Any]) -> dict[str, Any]:
    """Build kwargs for PE-17 ExplicitContractProof from a PE-19 review proof."""
    valid = review_proof.get("review_valid") is True
    return {
        "contract_version": CONTRACT_VERSION,
        "validation_pass": valid,
        "contract_marker": PACKAGE_MARKER if valid else None,
    }


def default_minimal_operator_review_input(
    *,
    source_revision: str,
    packet_digest: str,
    input_capture_digest: str,
    replay_manifest_digest: str,
    archive_identity: str,
    archive_manifest_digest: str,
    completeness_truth_identity: str,
    source_state_digest: str,
    manifest_verify_rc: int = 0,
) -> PreflightOperatorReviewInput:
    """Minimal generic futures-testnet review input with safe blocked defaults."""
    return PreflightOperatorReviewInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe13_packet=PE13_CONTRACT_VERSION,
            pe14_builder=BUILDER_VERSION,
            pe15_replay=REPLAY_CONTRACT_VERSION,
            pe16_archive=ARCHIVE_CONTRACT_VERSION,
            pe17_completeness_truth=COMPLETENESS_CONTRACT_VERSION,
            pe18_source_state_capture=PE18_CONTRACT_VERSION,
            pe19_operator_review=CONTRACT_VERSION,
        ),
        evidence_chain=EvidenceChainBinding(
            packet_digest=packet_digest,
            input_capture_digest=input_capture_digest,
            replay_manifest_digest=replay_manifest_digest,
            archive_identity=archive_identity,
            archive_manifest_digest=archive_manifest_digest,
            completeness_truth_identity=completeness_truth_identity,
            source_state_digest=source_state_digest,
            manifest_verify_rc=manifest_verify_rc,
        ),
        reviewed_scope=REVIEWED_SCOPE,
        safety_snapshot=SafetySnapshot(
            preflight_remains_blocked=True,
            ready_for_operator_arming=False,
            execution_authorized=False,
            live_authorized=False,
            credentials_allowed=False,
            orders_allowed=False,
            scheduler_runtime_allowed=False,
            network_allowed=False,
            operator_go_present=False,
            followup_run_gate=FOLLOWUP_RUN_GATE,
        ),
        futures_only=True,
        environment=ENVIRONMENT_TESTNET,
        non_authorizing=True,
    )


def default_minimal_decision_record(
    *,
    source_revision: str,
    review_input_digest: str,
    decision: str = DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
    reason_code: str = REASON_EVIDENCE_COMPLETE,
    structured_reason: str = "PE-13 through PE-18 evidence chain complete for static review.",
    operator_name: str = EXPECTED_OPERATOR_NAME,
    evidence_manifest_verify_rc: int = 0,
) -> OperatorDecisionRecord:
    """Minimal explicit decision record with safe non-authorizing defaults."""
    return OperatorDecisionRecord(
        source_revision=source_revision,
        operator_name=operator_name,
        decision=decision,
        reason_code=reason_code,
        structured_reason=structured_reason,
        review_input_digest=review_input_digest,
        evidence_manifest_verify_rc=evidence_manifest_verify_rc,
        non_authorizing=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
    )
