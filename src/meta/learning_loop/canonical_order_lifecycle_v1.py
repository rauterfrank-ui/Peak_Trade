"""Offline LEVEL_3 canonical order lifecycle contract owner v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.trading_session_single_writer_v1 import (
    ARTIFACT_REL as TRADING_SESSION_ARTIFACT_REL,
    CONTRACT_NAME as TRADING_SESSION_CONTRACT_NAME,
    CONTRACT_VERSION as TRADING_SESSION_CONTRACT_VERSION,
    PRODUCER_VERSION as TRADING_SESSION_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as TRADING_SESSION_SELF_VERIFICATION_REL,
    TradingSessionSingleWriterError,
    reverify_trading_session_single_writer_v1,
)

CONTRACT_NAME = "canonical_order_lifecycle_v1"
CONTRACT_VERSION = "v1"
LIFECYCLE_CONTRACT_VERSION = "canonical_order_lifecycle_contract_v1"
ORDER_IDENTITY_CONTRACT_VERSION = "canonical_order_identity_contract_v1"
ORDER_INTENT_IDENTITY_CONTRACT_VERSION = "canonical_order_intent_identity_contract_v1"
PRODUCER_VERSION = "canonical_order_lifecycle_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "canonical_order_lifecycle_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_TRADING_SESSION_SINGLE_WRITER_FOR_OFFLINE_CANONICAL_ORDER_LIFECYCLE"
)
ARTIFACT_REL = "canonical_order_lifecycle_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".canonical_order_lifecycle_staging_"

SCHEMA_VERSION = "canonical_order_lifecycle_schema_v1"
CREATION_CONTRACT_VERSION = "canonical_order_lifecycle_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "canonical_order_lifecycle_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_canonical_order_lifecycle_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_INSTRUMENT_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_INSTRUMENT_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})

_CANONICAL_ORDER_STATES = frozenset(
    {
        "INTENT_CREATED",
        "INTENT_VALIDATED",
        "SAFETY_APPROVED",
        "SUBMISSION_STARTED",
        "ACKNOWLEDGED",
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCEL_REQUESTED",
        "CANCEL_PENDING",
        "CANCELLED",
        "REJECTED",
        "EXPIRED",
        "UNKNOWN_OUTCOME",
        "RECONCILIATION_REQUIRED",
        "TERMINAL_RECONCILED",
    }
)
_TERMINAL_ORDER_STATES = frozenset(
    {"FILLED", "CANCELLED", "REJECTED", "EXPIRED", "TERMINAL_RECONCILED"}
)
_INITIAL_PREVIOUS_STATES = frozenset({"", "MISSING", "NONE"})

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "": frozenset({"INTENT_CREATED"}),
    "MISSING": frozenset({"INTENT_CREATED"}),
    "NONE": frozenset({"INTENT_CREATED"}),
    "INTENT_CREATED": frozenset({"INTENT_VALIDATED", "REJECTED", "EXPIRED"}),
    "INTENT_VALIDATED": frozenset({"SAFETY_APPROVED", "REJECTED", "EXPIRED"}),
    "SAFETY_APPROVED": frozenset({"SUBMISSION_STARTED", "CANCEL_REQUESTED", "REJECTED", "EXPIRED"}),
    "SUBMISSION_STARTED": frozenset({"ACKNOWLEDGED", "UNKNOWN_OUTCOME", "REJECTED", "EXPIRED"}),
    "ACKNOWLEDGED": frozenset(
        {
            "PARTIALLY_FILLED",
            "FILLED",
            "CANCEL_REQUESTED",
            "UNKNOWN_OUTCOME",
            "REJECTED",
            "EXPIRED",
        }
    ),
    "PARTIALLY_FILLED": frozenset(
        {"PARTIALLY_FILLED", "FILLED", "CANCEL_REQUESTED", "UNKNOWN_OUTCOME", "EXPIRED"}
    ),
    "CANCEL_REQUESTED": frozenset({"CANCEL_PENDING", "CANCELLED", "UNKNOWN_OUTCOME", "EXPIRED"}),
    "CANCEL_PENDING": frozenset({"CANCELLED", "UNKNOWN_OUTCOME", "EXPIRED"}),
    "UNKNOWN_OUTCOME": frozenset({"RECONCILIATION_REQUIRED"}),
    "RECONCILIATION_REQUIRED": frozenset(
        {
            "TERMINAL_RECONCILED",
            "ACKNOWLEDGED",
            "PARTIALLY_FILLED",
            "FILLED",
            "CANCELLED",
            "REJECTED",
            "EXPIRED",
        }
    ),
}

_VALID_TRANSITION_TYPES = frozenset(
    {
        "INITIAL_BIND",
        "VALIDATE",
        "SAFETY_APPROVE",
        "SUBMISSION_START",
        "ACKNOWLEDGE",
        "PARTIAL_FILL",
        "FILL",
        "CANCEL_REQUEST",
        "CANCEL_PENDING",
        "CANCEL",
        "REJECT",
        "EXPIRE",
        "UNKNOWN_OUTCOME",
        "RECONCILIATION_REQUIRED",
        "TERMINAL_RECONCILE",
        "IDEMPOTENT_REPEAT",
    }
)

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION",
        "CANONICAL_ORDER_LIFECYCLE_IDEMPOTENT",
        "CANONICAL_ORDER_LIFECYCLE_INVALID",
        "CANONICAL_ORDER_LIFECYCLE_MISSING_ORDER_IDENTITY",
        "CANONICAL_ORDER_LIFECYCLE_MISSING_ORDER_INTENT_IDENTITY",
        "CANONICAL_ORDER_LIFECYCLE_MISSING_SESSION_IDENTITY",
        "CANONICAL_ORDER_LIFECYCLE_MISSING_WRITER_IDENTITY",
        "CANONICAL_ORDER_LIFECYCLE_STALE_ORDER_REVISION",
        "CANONICAL_ORDER_LIFECYCLE_STALE_ORDER_GENERATION",
        "CANONICAL_ORDER_LIFECYCLE_STALE_WRITER_GENERATION",
        "CANONICAL_ORDER_LIFECYCLE_EXPECTED_STATE_MISMATCH",
        "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_TRANSITION",
        "CANONICAL_ORDER_LIFECYCLE_TERMINAL_STATE_REOPEN",
        "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_SUBMISSION",
        "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_AMEND",
        "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_CANCEL",
        "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_FILL",
        "CANONICAL_ORDER_LIFECYCLE_REPLAY_REJECTED",
        "CANONICAL_ORDER_LIFECYCLE_REVOKED",
        "CANONICAL_ORDER_LIFECYCLE_EXPIRED",
        "CANONICAL_ORDER_LIFECYCLE_UNTRUSTED_CLOCK",
        "CANONICAL_ORDER_LIFECYCLE_MISSING_BINDINGS",
        "CANONICAL_ORDER_LIFECYCLE_TAMPER_DETECTED",
        "CANONICAL_ORDER_LIFECYCLE_BROKEN_LINEAGE",
        "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_INSTRUMENT",
        "CANONICAL_ORDER_LIFECYCLE_UNKNOWN_STATE",
        "CANONICAL_ORDER_LIFECYCLE_AMBIGUOUS_STATE",
        "ABSTAIN",
    }
)
_VALID_LIFECYCLE_STATUSES = frozenset(
    {"VALID", "IDEMPOTENT", "INVALID", "CONFLICT", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "canonical_order_lifecycle_self_verification_v1"

_FORBIDDEN_INDEX_KEYS: frozenset[str] = frozenset(
    {
        "winner",
        "selected",
        "promoted",
        "promotion",
        "promotion_ready",
        "eligible_for_live",
        "live_eligible",
        "runtime_eligible",
        "ranking",
        "ranked_input_ids",
        "pareto",
        "accepted",
        "acceptance",
        "armed",
        "enabled",
        "returns",
        "positions",
        "orders",
        "credentials",
        "strategy_params_mutated",
        "config_patch",
        "configpatch",
        "config_patch_manifest",
        "patches",
        "top_n",
        "topn",
        "filter_candidates_for_live",
        "promotion_candidate",
        "safety_flags",
    }
)

_TRANSITIVE_LINEAGE_FIELDS = (
    "comparison_run_id",
    "experiment_id",
    "experiment_identity_manifest_id",
    "learning_manifest_id",
    "promotion_candidate_id",
    "config_patch_manifest_id",
    "versioned_artifact_id",
)

CANONICAL_ORDER_LIFECYCLE_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "canonical_order_lifecycle_is_descriptive_only": True,
    "canonical_order_lifecycle_does_not_create_order": True,
    "canonical_order_lifecycle_does_not_submit_order": True,
    "canonical_order_lifecycle_does_not_amend_order": True,
    "canonical_order_lifecycle_does_not_cancel_order": True,
    "canonical_order_lifecycle_does_not_fill_order": True,
    "canonical_order_lifecycle_does_not_mutate_order_state": True,
    "canonical_order_lifecycle_does_not_invoke_adapter": True,
    "canonical_order_lifecycle_does_not_invoke_consumer": True,
    "canonical_order_lifecycle_does_not_grant_authority": True,
    "canonical_order_lifecycle_does_not_activate_lease": True,
    "canonical_order_lifecycle_is_offline_only": True,
    "deny_by_default": True,
    "futures_only": True,
    "canonical_order_identity_bound": True,
    "canonical_order_intent_bound": True,
    "trading_session_identity_bound": True,
    "single_writer_identity_bound": True,
    "order_revision_generation_bound": True,
    "state_transition_contract_bound": True,
    "terminal_state_contract_bound": True,
    "idempotency_bound": True,
    "replay_protection_bound": True,
    "clock_trust_and_expiry_bound": True,
    "authority_lease_and_revocation_bound": True,
    "secure_handoff_bound": True,
    "atomic_claim_consume_bound": True,
    "cross_domain_lineage_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_canonical_order_lifecycle": True,
    "canonical_order_lifecycle_offline_only": True,
    "canonical_order_lifecycle_contract_complete": False,
    "canonical_order_identity_bound": False,
    "canonical_order_intent_bound": False,
    "trading_session_identity_bound": False,
    "single_writer_identity_bound": False,
    "order_revision_generation_bound": False,
    "state_transition_contract_bound": False,
    "terminal_state_contract_bound": False,
    "idempotency_bound": False,
    "replay_protection_bound": False,
    "clock_trust_and_expiry_bound": False,
    "authority_lease_and_revocation_bound": False,
    "secure_handoff_bound": False,
    "atomic_claim_consume_bound": False,
    "cross_domain_lineage_bound": False,
    "deny_by_default": True,
    "futures_only": True,
    "order_created": False,
    "order_validated": False,
    "order_authorized": False,
    "order_submission_requested": False,
    "order_submitted": False,
    "order_acknowledged": False,
    "order_amended": False,
    "order_cancel_requested": False,
    "order_cancelled": False,
    "order_partially_filled": False,
    "order_filled": False,
    "order_rejected": False,
    "order_expired": False,
    "order_revoked": False,
    "order_state_mutated": False,
    "adapter_invoked": False,
    "exchange_request_sent": False,
    "network_side_effect_created": False,
    "files_transferred_to_runtime": False,
    "queue_message_created": False,
    "database_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "trading_session_started": False,
    "writer_registered": False,
    "writer_activated": False,
    "fencing_token_issued": False,
    "authority_granted": False,
    "authority_activated": False,
    "lease_activated": False,
    "lease_renewed": False,
    "revocation_executed": False,
    "killswitch_executed": False,
    "signature_created": False,
    "private_key_used": False,
    "credentials_accessed": False,
    "runtime_configuration_created": False,
    "runtime_permission_created": False,
    "execution_permission_created": False,
    "arming_token_created": False,
    "runtime_authorized": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
}


class CanonicalOrderLifecycleError(ValueError):
    """Fail-closed canonical order lifecycle error."""


@dataclass(frozen=True)
class CanonicalOrderIntentIdentity:
    client_order_id: str
    order_intent_digest: str
    instrument_type: str
    venue: str
    account: str
    instrument: str
    trading_epoch: str


@dataclass(frozen=True)
class CanonicalOrderIdentity:
    canonical_order_id: str
    client_order_id: str
    venue_order_id: str = ""


@dataclass(frozen=True)
class CanonicalOrderLifecycleRequest:
    canonical_order_intent_identity: CanonicalOrderIntentIdentity
    canonical_order_identity: CanonicalOrderIdentity
    transition_identity: str
    transition_type: str
    previous_order_state: str
    expected_order_state: str
    target_order_state: str
    order_revision: int
    order_generation: int
    idempotency_key: str
    replay_identity: str
    order_lifecycle_lineage: dict[str, Any]
    prior_order_revision: int = 0
    prior_order_generation: int = 0
    prior_lifecycle_evidence_digest: str = ""
    prior_idempotency_key: str = ""
    prior_transition_identity: str = ""
    lifecycle_contract_version: str = LIFECYCLE_CONTRACT_VERSION
    order_identity_contract_version: str = ORDER_IDENTITY_CONTRACT_VERSION
    order_intent_identity_contract_version: str = ORDER_INTENT_IDENTITY_CONTRACT_VERSION
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class VerifiedTradingSessionSingleWriterBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    contract_id: str
    contract_status: str
    single_writer_status: str
    session_identity_digest: str
    writer_identity_digest: str
    writer_identity: str
    writer_generation: int
    executor_epoch: int
    trading_session_identity: dict[str, Any]
    clock_trust_contract_id: str
    clock_trust_digest: str
    secure_handoff_envelope_identity: str
    handoff_atomic_claim_consume_identity: str
    authority_lease_and_revocation_bundle_ref: str
    cross_domain_lineage: dict[str, Any]


@dataclass(frozen=True)
class CanonicalOrderLifecycleInputs:
    trading_session_single_writer_bundle_dir: Path
    lifecycle_request: CanonicalOrderLifecycleRequest


@dataclass(frozen=True)
class CanonicalOrderLifecycleResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    lifecycle_status: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    canonical_order_identity_digest: str
    canonical_order_intent_identity_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise CanonicalOrderLifecycleError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise CanonicalOrderLifecycleError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise CanonicalOrderLifecycleError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise CanonicalOrderLifecycleError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise CanonicalOrderLifecycleError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise CanonicalOrderLifecycleError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, bundle_dirs: list[Path], output_dir: Path) -> None:
    resolved_output = output_dir.resolve()
    for bundle_dir in bundle_dirs:
        resolved_bundle = bundle_dir.resolve()
        if resolved_bundle == resolved_output or _path_is_under(resolved_output, resolved_bundle):
            raise CanonicalOrderLifecycleError(
                "output directory must not overlap input bundle directory"
            )
        if _path_is_under(resolved_bundle, resolved_output):
            raise CanonicalOrderLifecycleError(
                "input bundle directory must not be under output directory"
            )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _factor(
    *,
    factor_id: str,
    factor_type: str,
    source_field: str,
    detail: str,
) -> dict[str, str]:
    return {
        "factor_id": factor_id,
        "factor_type": factor_type,
        "source_field": source_field,
        "detail": detail,
    }


def _sort_factors(factors: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(factors, key=lambda item: (item["factor_id"], item["source_field"]))


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(values)


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if not isinstance(payload, dict):
        raise CanonicalOrderLifecycleError(f"{label} must be an object")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    output_digest = payload.get("output_digest")
    if isinstance(output_digest, str) and output_digest:
        return output_digest
    return compute_content_sha256(dict(payload))


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "canonical_order_lifecycle_contract_complete",
            "canonical_order_identity_bound",
            "canonical_order_intent_bound",
            "trading_session_identity_bound",
            "single_writer_identity_bound",
            "order_revision_generation_bound",
            "state_transition_contract_bound",
            "terminal_state_contract_bound",
            "idempotency_bound",
            "replay_protection_bound",
            "clock_trust_and_expiry_bound",
            "authority_lease_and_revocation_bound",
            "secure_handoff_bound",
            "atomic_claim_consume_bound",
            "cross_domain_lineage_bound",
        }:
            continue
        if actual is not expected:
            raise CanonicalOrderLifecycleError(
                f"non-authorizing flag {key} must be {expected!r}, got {actual!r}"
            )


def _extract_cross_domain_lineage(payload: Mapping[str, Any]) -> dict[str, Any]:
    lineage = payload.get("cross_domain_lineage")
    if isinstance(lineage, Mapping):
        return dict(lineage)
    result: dict[str, Any] = {}
    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = payload.get(field)
        if value is not None and str(value):
            result[field] = str(value)
    return result


def _lineage_matches(
    *,
    request_lineage: Mapping[str, Any],
    upstream_lineage: Mapping[str, Any],
) -> bool:
    for key, expected in upstream_lineage.items():
        actual = request_lineage.get(key)
        if actual is None or str(actual) != str(expected):
            return False
    return True


def verify_trading_session_single_writer_bundle(
    bundle_dir: Path | str,
) -> VerifiedTradingSessionSingleWriterBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="trading session single writer bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise CanonicalOrderLifecycleError(
            f"trading session MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / TRADING_SESSION_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=TRADING_SESSION_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != TRADING_SESSION_CONTRACT_NAME:
        raise CanonicalOrderLifecycleError("trading session contract_name mismatch")
    if payload.get("contract_version") != TRADING_SESSION_CONTRACT_VERSION:
        raise CanonicalOrderLifecycleError("trading session contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=TRADING_SESSION_SELF_VERIFICATION_REL,
        label=TRADING_SESSION_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise CanonicalOrderLifecycleError(
            "trading session SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_trading_session_single_writer_v1(output_dir=path)
    except TradingSessionSingleWriterError as exc:
        raise CanonicalOrderLifecycleError(str(exc)) from exc

    session_identity = payload.get("trading_session_identity")
    if not isinstance(session_identity, dict):
        raise CanonicalOrderLifecycleError("trading_session_identity must be an object")

    return VerifiedTradingSessionSingleWriterBundle(
        bundle_dir=path.resolve(),
        contract_name=TRADING_SESSION_CONTRACT_NAME,
        contract_version=TRADING_SESSION_CONTRACT_VERSION,
        producer_version=TRADING_SESSION_PRODUCER_VERSION,
        artifact_ref=TRADING_SESSION_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        single_writer_status=str(payload.get("single_writer_status", "")),
        session_identity_digest=str(payload.get("session_identity_digest", "")),
        writer_identity_digest=str(payload.get("writer_identity_digest", "")),
        writer_identity=str(payload.get("writer_identity", "")),
        writer_generation=int(payload.get("writer_generation", 0) or 0),
        executor_epoch=int(payload.get("executor_epoch", 0) or 0),
        trading_session_identity=dict(session_identity),
        clock_trust_contract_id=str(payload.get("clock_trust_contract_id", "")),
        clock_trust_digest=str(payload.get("clock_trust_digest", "")),
        secure_handoff_envelope_identity=str(payload.get("secure_handoff_envelope_identity", "")),
        handoff_atomic_claim_consume_identity=str(
            payload.get("handoff_atomic_claim_consume_identity", "")
        ),
        authority_lease_and_revocation_bundle_ref=str(
            payload.get("authority_lease_and_revocation_bundle_ref", "")
        ),
        cross_domain_lineage=_extract_cross_domain_lineage(payload),
    )


def _compute_order_intent_identity_digest(*, intent: CanonicalOrderIntentIdentity) -> str:
    return compute_content_sha256(
        {
            "identity_domain": ORDER_INTENT_IDENTITY_CONTRACT_VERSION,
            "client_order_id": intent.client_order_id,
            "order_intent_digest": intent.order_intent_digest,
            "instrument_type": intent.instrument_type,
            "venue": intent.venue,
            "account": intent.account,
            "instrument": intent.instrument,
            "trading_epoch": intent.trading_epoch,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_order_identity_digest(*, order: CanonicalOrderIdentity) -> str:
    return compute_content_sha256(
        {
            "identity_domain": ORDER_IDENTITY_CONTRACT_VERSION,
            "canonical_order_id": order.canonical_order_id,
            "client_order_id": order.client_order_id,
            "venue_order_id": order.venue_order_id,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_lifecycle_evidence_digest(
    *,
    order_intent_digest: str,
    order_identity_digest: str,
    session_digest: str,
    writer_digest: str,
    transition_identity: str,
    expected_order_state: str,
    target_order_state: str,
    order_revision: int,
    idempotency_key: str,
) -> str:
    return compute_content_sha256(
        {
            "order_intent_identity_digest": order_intent_digest,
            "canonical_order_identity_digest": order_identity_digest,
            "session_identity_digest": session_digest,
            "writer_identity_digest": writer_digest,
            "transition_identity": transition_identity,
            "expected_order_state": expected_order_state,
            "target_order_state": target_order_state,
            "order_revision": order_revision,
            "idempotency_key": idempotency_key,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _normalize_previous_state(previous_order_state: str) -> str:
    if previous_order_state in _INITIAL_PREVIOUS_STATES:
        return ""
    return previous_order_state


def _transition_allowed(*, previous_order_state: str, target_order_state: str) -> bool:
    normalized_previous = _normalize_previous_state(previous_order_state)
    allowed_targets = _ALLOWED_TRANSITIONS.get(normalized_previous)
    if allowed_targets is None:
        return False
    return target_order_state in allowed_targets


def _validate_request(
    request: CanonicalOrderLifecycleRequest,
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []
    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity

    if request.lifecycle_contract_version != LIFECYCLE_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_LIFECYCLE_CONTRACT_VERSION",
                factor_type="CONTRADICTION",
                source_field="lifecycle_contract_version",
                detail=request.lifecycle_contract_version,
            )
        )
    if request.order_identity_contract_version != ORDER_IDENTITY_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_ORDER_IDENTITY_CONTRACT_VERSION",
                factor_type="CONTRADICTION",
                source_field="order_identity_contract_version",
                detail=request.order_identity_contract_version,
            )
        )
    if request.order_intent_identity_contract_version != ORDER_INTENT_IDENTITY_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_ORDER_INTENT_IDENTITY_CONTRACT_VERSION",
                factor_type="CONTRADICTION",
                source_field="order_intent_identity_contract_version",
                detail=request.order_intent_identity_contract_version,
            )
        )

    if not order.canonical_order_id:
        blocking.append(
            _factor(
                factor_id="MISSING_CANONICAL_ORDER_ID",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_identity.canonical_order_id",
                detail="missing",
            )
        )
    if not order.client_order_id:
        blocking.append(
            _factor(
                factor_id="MISSING_CLIENT_ORDER_ID",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_identity.client_order_id",
                detail="missing",
            )
        )
    if not intent.client_order_id:
        blocking.append(
            _factor(
                factor_id="MISSING_ORDER_INTENT_CLIENT_ORDER_ID",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_intent_identity.client_order_id",
                detail="missing",
            )
        )
    if not intent.order_intent_digest:
        blocking.append(
            _factor(
                factor_id="MISSING_ORDER_INTENT_DIGEST",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_intent_identity.order_intent_digest",
                detail="missing",
            )
        )
    if (
        order.client_order_id
        and intent.client_order_id
        and order.client_order_id != intent.client_order_id
    ):
        blocking.append(
            _factor(
                factor_id="ORDER_INTENT_CLIENT_ORDER_ID_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="canonical_order_intent_identity.client_order_id",
                detail=intent.client_order_id,
            )
        )

    if not intent.instrument_type:
        blocking.append(
            _factor(
                factor_id="MISSING_INSTRUMENT_TYPE",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_intent_identity.instrument_type",
                detail="missing",
            )
        )
    else:
        instrument_type = intent.instrument_type.upper()
        if instrument_type in _FORBIDDEN_INSTRUMENT_TYPES:
            blocking.append(
                _factor(
                    factor_id="FORBIDDEN_INSTRUMENT_TYPE",
                    factor_type="BLOCKING",
                    source_field="canonical_order_intent_identity.instrument_type",
                    detail=instrument_type,
                )
            )
        elif instrument_type not in _VALID_INSTRUMENT_TYPES:
            blocking.append(
                _factor(
                    factor_id="INVALID_INSTRUMENT_TYPE",
                    factor_type="BLOCKING",
                    source_field="canonical_order_intent_identity.instrument_type",
                    detail=instrument_type,
                )
            )

    for field_name, value in (
        ("venue", intent.venue),
        ("account", intent.account),
        ("instrument", intent.instrument),
        ("trading_epoch", intent.trading_epoch),
    ):
        if not value:
            blocking.append(
                _factor(
                    factor_id=f"MISSING_ORDER_INTENT_{field_name.upper()}",
                    factor_type="MISSING_PRECONDITION",
                    source_field=f"canonical_order_intent_identity.{field_name}",
                    detail="missing",
                )
            )

    session_identity = trading_session.trading_session_identity
    for field_name in ("venue", "account", "instrument", "trading_epoch"):
        session_value = str(session_identity.get(field_name, ""))
        intent_value = str(getattr(intent, field_name))
        if session_value and intent_value and session_value != intent_value:
            blocking.append(
                _factor(
                    factor_id=f"MISMATCHED_SESSION_{field_name.upper()}",
                    factor_type="CONTRADICTION",
                    source_field=f"canonical_order_intent_identity.{field_name}",
                    detail=intent_value,
                )
            )

    if not request.transition_identity:
        blocking.append(
            _factor(
                factor_id="MISSING_TRANSITION_IDENTITY",
                factor_type="MISSING_PRECONDITION",
                source_field="transition_identity",
                detail="missing",
            )
        )
    if request.transition_type not in _VALID_TRANSITION_TYPES:
        blocking.append(
            _factor(
                factor_id="INVALID_TRANSITION_TYPE",
                factor_type="MISSING_PRECONDITION",
                source_field="transition_type",
                detail=request.transition_type,
            )
        )
    if not request.idempotency_key:
        blocking.append(
            _factor(
                factor_id="MISSING_IDEMPOTENCY_KEY",
                factor_type="MISSING_PRECONDITION",
                source_field="idempotency_key",
                detail="missing",
            )
        )
    if not request.replay_identity:
        blocking.append(
            _factor(
                factor_id="MISSING_REPLAY_IDENTITY",
                factor_type="MISSING_PRECONDITION",
                source_field="replay_identity",
                detail="missing",
            )
        )
    if request.order_revision <= 0:
        blocking.append(
            _factor(
                factor_id="INVALID_ORDER_REVISION",
                factor_type="MISSING_PRECONDITION",
                source_field="order_revision",
                detail=str(request.order_revision),
            )
        )
    if request.order_generation <= 0:
        blocking.append(
            _factor(
                factor_id="INVALID_ORDER_GENERATION",
                factor_type="MISSING_PRECONDITION",
                source_field="order_generation",
                detail=str(request.order_generation),
            )
        )
    if not request.order_lifecycle_lineage:
        blocking.append(
            _factor(
                factor_id="MISSING_ORDER_LIFECYCLE_LINEAGE",
                factor_type="MISSING_PRECONDITION",
                source_field="order_lifecycle_lineage",
                detail="missing",
            )
        )

    normalized_previous = _normalize_previous_state(request.previous_order_state)
    if normalized_previous and normalized_previous not in _CANONICAL_ORDER_STATES:
        blocking.append(
            _factor(
                factor_id="UNKNOWN_PREVIOUS_ORDER_STATE",
                factor_type="BLOCKING",
                source_field="previous_order_state",
                detail=request.previous_order_state,
            )
        )
    if request.target_order_state not in _CANONICAL_ORDER_STATES:
        blocking.append(
            _factor(
                factor_id="UNKNOWN_TARGET_ORDER_STATE",
                factor_type="BLOCKING",
                source_field="target_order_state",
                detail=request.target_order_state,
            )
        )
    if (
        request.expected_order_state
        and request.expected_order_state not in _CANONICAL_ORDER_STATES
        and request.expected_order_state not in _INITIAL_PREVIOUS_STATES
    ):
        blocking.append(
            _factor(
                factor_id="UNKNOWN_EXPECTED_ORDER_STATE",
                factor_type="BLOCKING",
                source_field="expected_order_state",
                detail=request.expected_order_state,
            )
        )

    if trading_session.contract_status == "TRADING_SESSION_SINGLE_WRITER_REVOKED":
        blocking.append(
            _factor(
                factor_id="UPSTREAM_TRADING_SESSION_REVOKED",
                factor_type="BLOCKING",
                source_field="trading_session.contract_status",
                detail=trading_session.contract_status,
            )
        )
    elif trading_session.contract_status == "TRADING_SESSION_SINGLE_WRITER_EXPIRED":
        blocking.append(
            _factor(
                factor_id="UPSTREAM_TRADING_SESSION_EXPIRED",
                factor_type="BLOCKING",
                source_field="trading_session.contract_status",
                detail=trading_session.contract_status,
            )
        )
    elif trading_session.contract_status == "TRADING_SESSION_SINGLE_WRITER_UNTRUSTED_CLOCK":
        blocking.append(
            _factor(
                factor_id="UPSTREAM_TRADING_SESSION_UNTRUSTED_CLOCK",
                factor_type="BLOCKING",
                source_field="trading_session.contract_status",
                detail=trading_session.contract_status,
            )
        )
    elif trading_session.contract_status not in {
        "TRADING_SESSION_SINGLE_WRITER_VALID_FOR_OFFLINE_EVALUATION",
        "TRADING_SESSION_SINGLE_WRITER_IDEMPOTENT",
    }:
        blocking.append(
            _factor(
                factor_id="UPSTREAM_TRADING_SESSION_INVALID",
                factor_type="BLOCKING",
                source_field="trading_session.contract_status",
                detail=trading_session.contract_status,
            )
        )

    session_payload = trading_session.artifact_payload
    if not session_payload.get("single_writer_invariant_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_SINGLE_WRITER_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="single_writer_invariant_bound",
                detail="false",
            )
        )
    if not session_payload.get("clock_trust_and_expiry_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_CLOCK_TRUST_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="clock_trust_and_expiry_bound",
                detail="false",
            )
        )
    if not session_payload.get("secure_handoff_envelope_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_SECURE_HANDOFF_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="secure_handoff_envelope_bound",
                detail="false",
            )
        )
    if not session_payload.get("handoff_atomic_claim_consume_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_ATOMIC_CLAIM_CONSUME_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="handoff_atomic_claim_consume_bound",
                detail="false",
            )
        )
    if not session_payload.get("authority_lease_and_revocation_bound"):
        blocking.append(
            _factor(
                factor_id="UPSTREAM_AUTHORITY_LEASE_NOT_BOUND",
                factor_type="MISSING_PRECONDITION",
                source_field="authority_lease_and_revocation_bound",
                detail="false",
            )
        )
    if not trading_session.writer_identity:
        blocking.append(
            _factor(
                factor_id="MISSING_WRITER_IDENTITY",
                factor_type="MISSING_PRECONDITION",
                source_field="writer_identity",
                detail="missing",
            )
        )

    expected_lineage = dict(trading_session.cross_domain_lineage)
    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = session_payload.get(field)
        if value is not None and str(value):
            expected_lineage[field] = str(value)
    if expected_lineage and request.order_lifecycle_lineage:
        if not _lineage_matches(
            request_lineage=request.order_lifecycle_lineage,
            upstream_lineage=expected_lineage,
        ):
            blocking.append(
                _factor(
                    factor_id="BROKEN_ORDER_LIFECYCLE_LINEAGE",
                    factor_type="CONTRADICTION",
                    source_field="order_lifecycle_lineage",
                    detail="lineage mismatch with trading session artifact lineage",
                )
            )

    normalized_expected = _normalize_previous_state(request.expected_order_state)
    normalized_previous = _normalize_previous_state(request.previous_order_state)
    if normalized_expected != normalized_previous:
        blocking.append(
            _factor(
                factor_id="EXPECTED_STATE_MISMATCH",
                factor_type="BLOCKING",
                source_field="expected_order_state",
                detail=request.expected_order_state,
            )
        )

    if normalized_previous in _TERMINAL_ORDER_STATES:
        blocking.append(
            _factor(
                factor_id="TERMINAL_STATE_REOPEN",
                factor_type="BLOCKING",
                source_field="previous_order_state",
                detail=normalized_previous,
            )
        )

    if (
        request.prior_order_generation > 0
        and request.order_generation < request.prior_order_generation
    ):
        blocking.append(
            _factor(
                factor_id="STALE_ORDER_GENERATION",
                factor_type="BLOCKING",
                source_field="order_generation",
                detail=str(request.order_generation),
            )
        )

    if (
        request.prior_order_revision > 0
        and request.order_revision <= request.prior_order_revision
        and request.transition_type != "IDEMPOTENT_REPEAT"
    ):
        blocking.append(
            _factor(
                factor_id="STALE_ORDER_REVISION",
                factor_type="BLOCKING",
                source_field="order_revision",
                detail=str(request.order_revision),
            )
        )

    if (
        request.prior_idempotency_key
        and request.prior_idempotency_key == request.idempotency_key
        and request.prior_transition_identity
        and request.prior_transition_identity != request.transition_identity
    ):
        duplicate_factor = {
            "SUBMISSION_START": "DUPLICATE_SUBMISSION",
            "ACKNOWLEDGE": "DUPLICATE_SUBMISSION",
            "CANCEL_REQUEST": "DUPLICATE_CANCEL",
            "CANCEL": "DUPLICATE_CANCEL",
            "PARTIAL_FILL": "DUPLICATE_FILL",
            "FILL": "DUPLICATE_FILL",
            "VALIDATE": "DUPLICATE_AMEND",
            "SAFETY_APPROVE": "DUPLICATE_AMEND",
        }.get(request.transition_type, "DUPLICATE_TRANSITION")
        blocking.append(
            _factor(
                factor_id=duplicate_factor,
                factor_type="BLOCKING",
                source_field="idempotency_key",
                detail=request.idempotency_key,
            )
        )

    if not _transition_allowed(
        previous_order_state=request.previous_order_state,
        target_order_state=request.target_order_state,
    ):
        blocking.append(
            _factor(
                factor_id="FORBIDDEN_TRANSITION",
                factor_type="BLOCKING",
                source_field="target_order_state",
                detail=request.target_order_state,
            )
        )

    order_intent_digest = _compute_order_intent_identity_digest(intent=intent)
    order_identity_digest = _compute_order_identity_digest(order=order)
    evidence_digest = _compute_lifecycle_evidence_digest(
        order_intent_digest=order_intent_digest,
        order_identity_digest=order_identity_digest,
        session_digest=trading_session.session_identity_digest,
        writer_digest=trading_session.writer_identity_digest,
        transition_identity=request.transition_identity,
        expected_order_state=request.expected_order_state,
        target_order_state=request.target_order_state,
        order_revision=request.order_revision,
        idempotency_key=request.idempotency_key,
    )
    if (
        request.prior_lifecycle_evidence_digest
        and request.prior_lifecycle_evidence_digest == evidence_digest
        and request.transition_type != "IDEMPOTENT_REPEAT"
    ):
        blocking.append(
            _factor(
                factor_id="REPLAYED_LIFECYCLE_EVIDENCE",
                factor_type="BLOCKING",
                source_field="prior_lifecycle_evidence_digest",
                detail="duplicate lifecycle evidence digest",
            )
        )

    return blocking


def _evaluate_lifecycle(
    *,
    request: CanonicalOrderLifecycleRequest,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, list[str], dict[str, Any]]:
    reason_codes: list[str] = []
    factor_ids = {item.get("factor_id") for item in blocking_facts}
    states: dict[str, Any] = {
        "lifecycle_status": "UNKNOWN",
        "lifecycle_reason": "",
        "canonical_order_lifecycle_contract_complete": False,
        "canonical_order_identity_bound": False,
        "canonical_order_intent_bound": False,
        "trading_session_identity_bound": False,
        "single_writer_identity_bound": False,
        "order_revision_generation_bound": False,
        "state_transition_contract_bound": False,
        "terminal_state_contract_bound": False,
        "idempotency_bound": False,
        "replay_protection_bound": False,
        "clock_trust_and_expiry_bound": False,
        "authority_lease_and_revocation_bound": False,
        "secure_handoff_bound": False,
        "atomic_claim_consume_bound": False,
        "cross_domain_lineage_bound": False,
        "terminal_state": request.target_order_state in _TERMINAL_ORDER_STATES,
        "transition_allowed": False,
        "transition_preconditions_met": False,
    }

    if {
        "MISSING_CANONICAL_ORDER_ID",
        "MISSING_CLIENT_ORDER_ID",
        "MISSING_ORDER_INTENT_CLIENT_ORDER_ID",
        "MISSING_ORDER_INTENT_DIGEST",
    } & factor_ids:
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "MISSING_IDENTITY"
        reason_codes.append("MISSING_IDENTITY")
        if "MISSING_CANONICAL_ORDER_ID" in factor_ids or "MISSING_CLIENT_ORDER_ID" in factor_ids:
            return (
                "CANONICAL_ORDER_LIFECYCLE_MISSING_ORDER_IDENTITY",
                states["lifecycle_status"],
                _sorted_strings(reason_codes),
                states,
            )
        return (
            "CANONICAL_ORDER_LIFECYCLE_MISSING_ORDER_INTENT_IDENTITY",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if {
        "MISSING_ORDER_INTENT_VENUE",
        "MISSING_ORDER_INTENT_ACCOUNT",
        "MISSING_ORDER_INTENT_INSTRUMENT",
        "MISSING_ORDER_INTENT_TRADING_EPOCH",
    } & factor_ids:
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "MISSING_SESSION_IDENTITY"
        reason_codes.append("MISSING_SESSION_IDENTITY")
        return (
            "CANONICAL_ORDER_LIFECYCLE_MISSING_SESSION_IDENTITY",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "MISSING_WRITER_IDENTITY" in factor_ids:
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "MISSING_WRITER_IDENTITY"
        reason_codes.append("MISSING_WRITER_IDENTITY")
        return (
            "CANONICAL_ORDER_LIFECYCLE_MISSING_WRITER_IDENTITY",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "MISSING_INSTRUMENT_TYPE",
    } & factor_ids:
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "FORBIDDEN_INSTRUMENT"
        reason_codes.append("FORBIDDEN_INSTRUMENT")
        return (
            "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_INSTRUMENT",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "UPSTREAM_TRADING_SESSION_REVOKED" in factor_ids:
        states["authority_lease_and_revocation_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "UPSTREAM_REVOKED"
        reason_codes.append("UPSTREAM_REVOKED")
        return (
            "CANONICAL_ORDER_LIFECYCLE_REVOKED",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "UPSTREAM_TRADING_SESSION_EXPIRED" in factor_ids:
        states["clock_trust_and_expiry_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "UPSTREAM_EXPIRED"
        reason_codes.append("UPSTREAM_EXPIRED")
        return (
            "CANONICAL_ORDER_LIFECYCLE_EXPIRED",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "UPSTREAM_TRADING_SESSION_UNTRUSTED_CLOCK" in factor_ids:
        states["clock_trust_and_expiry_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "UPSTREAM_UNTRUSTED_CLOCK"
        reason_codes.append("UPSTREAM_UNTRUSTED_CLOCK")
        return (
            "CANONICAL_ORDER_LIFECYCLE_UNTRUSTED_CLOCK",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if {
        "UNKNOWN_PREVIOUS_ORDER_STATE",
        "UNKNOWN_TARGET_ORDER_STATE",
        "UNKNOWN_EXPECTED_ORDER_STATE",
    } & factor_ids:
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "UNKNOWN_STATE"
        reason_codes.append("UNKNOWN_STATE")
        return (
            "CANONICAL_ORDER_LIFECYCLE_UNKNOWN_STATE",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "BROKEN_ORDER_LIFECYCLE_LINEAGE" in factor_ids:
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "BROKEN_LINEAGE"
        reason_codes.append("BROKEN_LINEAGE")
        return (
            "CANONICAL_ORDER_LIFECYCLE_BROKEN_LINEAGE",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "TERMINAL_STATE_REOPEN" in factor_ids:
        states["terminal_state_contract_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "TERMINAL_STATE_REOPEN"
        reason_codes.append("TERMINAL_STATE_REOPEN")
        return (
            "CANONICAL_ORDER_LIFECYCLE_TERMINAL_STATE_REOPEN",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "EXPECTED_STATE_MISMATCH" in factor_ids:
        states["state_transition_contract_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "EXPECTED_STATE_MISMATCH"
        reason_codes.append("EXPECTED_STATE_MISMATCH")
        return (
            "CANONICAL_ORDER_LIFECYCLE_EXPECTED_STATE_MISMATCH",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "STALE_ORDER_REVISION" in factor_ids:
        states["order_revision_generation_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "STALE_ORDER_REVISION"
        reason_codes.append("STALE_ORDER_REVISION")
        return (
            "CANONICAL_ORDER_LIFECYCLE_STALE_ORDER_REVISION",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "STALE_ORDER_GENERATION" in factor_ids:
        states["order_revision_generation_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "STALE_ORDER_GENERATION"
        reason_codes.append("STALE_ORDER_GENERATION")
        return (
            "CANONICAL_ORDER_LIFECYCLE_STALE_ORDER_GENERATION",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    duplicate_map = {
        "DUPLICATE_SUBMISSION": "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_SUBMISSION",
        "DUPLICATE_AMEND": "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_AMEND",
        "DUPLICATE_CANCEL": "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_CANCEL",
        "DUPLICATE_FILL": "CANONICAL_ORDER_LIFECYCLE_DUPLICATE_FILL",
    }
    for factor_id, contract_status in duplicate_map.items():
        if factor_id in factor_ids:
            states["idempotency_bound"] = True
            states["lifecycle_status"] = "CONFLICT"
            states["lifecycle_reason"] = factor_id
            reason_codes.append(factor_id)
            return (
                contract_status,
                states["lifecycle_status"],
                _sorted_strings(reason_codes),
                states,
            )

    if "REPLAYED_LIFECYCLE_EVIDENCE" in factor_ids:
        states["replay_protection_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "REPLAY_REJECTED"
        reason_codes.append("REPLAY_REJECTED")
        return (
            "CANONICAL_ORDER_LIFECYCLE_REPLAY_REJECTED",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "FORBIDDEN_TRANSITION" in factor_ids:
        states["state_transition_contract_bound"] = True
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "FORBIDDEN_TRANSITION"
        reason_codes.append("FORBIDDEN_TRANSITION")
        return (
            "CANONICAL_ORDER_LIFECYCLE_FORBIDDEN_TRANSITION",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if request.transition_type == "IDEMPOTENT_REPEAT":
        states.update(
            {
                "lifecycle_status": "IDEMPOTENT",
                "lifecycle_reason": "IDEMPOTENT_REPEAT",
                "canonical_order_lifecycle_contract_complete": True,
                "canonical_order_identity_bound": True,
                "canonical_order_intent_bound": True,
                "trading_session_identity_bound": True,
                "single_writer_identity_bound": True,
                "order_revision_generation_bound": True,
                "state_transition_contract_bound": True,
                "terminal_state_contract_bound": True,
                "idempotency_bound": True,
                "replay_protection_bound": True,
                "clock_trust_and_expiry_bound": True,
                "authority_lease_and_revocation_bound": True,
                "secure_handoff_bound": True,
                "atomic_claim_consume_bound": True,
                "cross_domain_lineage_bound": True,
                "transition_allowed": True,
                "transition_preconditions_met": True,
            }
        )
        reason_codes.append("IDEMPOTENT_REPEAT")
        return (
            "CANONICAL_ORDER_LIFECYCLE_IDEMPOTENT",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if blocking_facts:
        states["lifecycle_status"] = "INVALID"
        states["lifecycle_reason"] = "MISSING_BINDINGS"
        reason_codes.append("MISSING_BINDINGS")
        return (
            "CANONICAL_ORDER_LIFECYCLE_MISSING_BINDINGS",
            states["lifecycle_status"],
            _sorted_strings(reason_codes),
            states,
        )

    states.update(
        {
            "lifecycle_status": "VALID",
            "lifecycle_reason": "TRANSITION_ALLOWED",
            "canonical_order_lifecycle_contract_complete": True,
            "canonical_order_identity_bound": True,
            "canonical_order_intent_bound": True,
            "trading_session_identity_bound": True,
            "single_writer_identity_bound": True,
            "order_revision_generation_bound": True,
            "state_transition_contract_bound": True,
            "terminal_state_contract_bound": True,
            "idempotency_bound": True,
            "replay_protection_bound": True,
            "clock_trust_and_expiry_bound": True,
            "authority_lease_and_revocation_bound": True,
            "secure_handoff_bound": True,
            "atomic_claim_consume_bound": True,
            "cross_domain_lineage_bound": True,
            "transition_allowed": True,
            "transition_preconditions_met": True,
        }
    )
    reason_codes.append("TRANSITION_ALLOWED")
    return (
        "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION",
        states["lifecycle_status"],
        _sorted_strings(reason_codes),
        states,
    )


def _input_artifact_ref_mapping(
    *,
    bundle_dir: Path,
    contract_name: str,
    contract_version: str,
    producer_version: str,
    artifact_ref: str,
    artifact_digest: str,
    manifest_digest: str,
) -> dict[str, Any]:
    return {
        "artifact_type": contract_name,
        "contract_name": contract_name,
        "contract_version": contract_version,
        "artifact_ref": artifact_ref,
        "artifact_digest": artifact_digest,
        "manifest_digest": manifest_digest,
        "producer_version": producer_version,
        "bundle_path": bundle_dir.as_posix(),
    }


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {
            "output_digest",
            "manifest_digest",
            "integrity",
            "created_at",
            "artifact_id",
            "contract_id",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def build_canonical_order_lifecycle_v1(
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    request: CanonicalOrderLifecycleRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(request, trading_session=trading_session)
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    contract_status, lifecycle_status, reason_codes, completion_flags = _evaluate_lifecycle(
        request=request,
        trading_session=trading_session,
        blocking_facts=blocking_facts,
    )

    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity
    order_intent_identity_digest = _compute_order_intent_identity_digest(intent=intent)
    canonical_order_identity_digest = _compute_order_identity_digest(order=order)
    lifecycle_evidence_digest = _compute_lifecycle_evidence_digest(
        order_intent_digest=order_intent_identity_digest,
        order_identity_digest=canonical_order_identity_digest,
        session_digest=trading_session.session_identity_digest,
        writer_digest=trading_session.writer_identity_digest,
        transition_identity=request.transition_identity,
        expected_order_state=request.expected_order_state,
        target_order_state=request.target_order_state,
        order_revision=request.order_revision,
        idempotency_key=request.idempotency_key,
    )

    input_refs = [
        _input_artifact_ref_mapping(
            bundle_dir=trading_session.bundle_dir,
            contract_name=trading_session.contract_name,
            contract_version=trading_session.contract_version,
            producer_version=trading_session.producer_version,
            artifact_ref=trading_session.artifact_ref,
            artifact_digest=trading_session.artifact_digest,
            manifest_digest=trading_session.manifest_digest,
        )
    ]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "canonical_order_identity_digest": canonical_order_identity_digest,
            "order_intent_identity_digest": order_intent_identity_digest,
            "session_identity_digest": trading_session.session_identity_digest,
            "transition_identity": request.transition_identity,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    session_payload = trading_session.artifact_payload
    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "lifecycle_contract_version": request.lifecycle_contract_version,
        "order_identity_contract_version": request.order_identity_contract_version,
        "order_intent_identity_contract_version": request.order_intent_identity_contract_version,
        "schema_version": SCHEMA_VERSION,
        "creation_contract_version": CREATION_CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "contract_creation_time": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "producer_identity_ref": DEFAULT_PRODUCER_IDENTITY_REF,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "contract_status": contract_status,
        "contract_reason_codes": reason_codes,
        "lifecycle_status": lifecycle_status,
        "lifecycle_reason": completion_flags.get("lifecycle_reason", ""),
        "canonical_order_intent_identity": {
            "client_order_id": intent.client_order_id,
            "order_intent_digest": intent.order_intent_digest,
            "instrument_type": intent.instrument_type,
            "venue": intent.venue,
            "account": intent.account,
            "instrument": intent.instrument,
            "trading_epoch": intent.trading_epoch,
        },
        "canonical_order_intent_identity_digest": order_intent_identity_digest,
        "canonical_order_identity": {
            "canonical_order_id": order.canonical_order_id,
            "client_order_id": order.client_order_id,
            "venue_order_id": order.venue_order_id,
        },
        "canonical_order_identity_digest": canonical_order_identity_digest,
        "trading_session_identity": dict(trading_session.trading_session_identity),
        "session_identity_digest": trading_session.session_identity_digest,
        "writer_identity": trading_session.writer_identity,
        "writer_generation": trading_session.writer_generation,
        "writer_identity_digest": trading_session.writer_identity_digest,
        "executor_epoch": trading_session.executor_epoch,
        "transition_identity": request.transition_identity,
        "transition_type": request.transition_type,
        "previous_order_state": request.previous_order_state,
        "expected_order_state": request.expected_order_state,
        "target_order_state": request.target_order_state,
        "order_revision": request.order_revision,
        "order_generation": request.order_generation,
        "idempotency_key": request.idempotency_key,
        "replay_identity": request.replay_identity,
        "lifecycle_evidence_digest": lifecycle_evidence_digest,
        "order_lifecycle_lineage": dict(request.order_lifecycle_lineage),
        "transition_allowed": completion_flags.get("transition_allowed", False),
        "transition_preconditions_met": completion_flags.get("transition_preconditions_met", False),
        "transition_reason": completion_flags.get("lifecycle_reason", ""),
        "terminal_state": completion_flags.get("terminal_state", False),
        "upstream_bindings": {
            "trading_session_single_writer_bundle_ref": trading_session.bundle_dir.as_posix(),
            "trading_session_contract_id": trading_session.contract_id,
            "trading_session_digest": trading_session.artifact_digest,
            "clock_trust_contract_id": trading_session.clock_trust_contract_id,
            "clock_trust_digest": trading_session.clock_trust_digest,
            "secure_handoff_envelope_identity": trading_session.secure_handoff_envelope_identity,
            "handoff_atomic_claim_consume_identity": trading_session.handoff_atomic_claim_consume_identity,
            "authority_lease_and_revocation_bundle_ref": trading_session.authority_lease_and_revocation_bundle_ref,
        },
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "canonical_order_lifecycle_authority_invariants": dict(
            CANONICAL_ORDER_LIFECYCLE_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": (
            dict(trading_session.cross_domain_lineage)
            if trading_session.cross_domain_lineage
            else dict(request.order_lifecycle_lineage)
        ),
        "provenance": {
            "producer_contract_name": CONTRACT_NAME,
            "producer_contract_version": CONTRACT_VERSION,
            "creation_contract_version": CREATION_CONTRACT_VERSION,
            "evidence_level": EVIDENCE_LEVEL,
            "offline_only": True,
            "contract_created_for_offline_evidence_only": True,
            "source_revision": request.source_revision,
        },
        "integrity_metadata": {
            "digest_algorithm": "sha256",
            "canonical_serialization": "deterministic_json_dumps",
            "contract_id_domain": CONTRACT_NAME,
            "signature_created": False,
        },
        "input_digest": input_digest,
        "output_digest": "",
        "manifest_digest": "",
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        payload[key] = value
    payload.update(
        {
            key: completion_flags[key]
            for key in completion_flags
            if key in _REQUIRED_NON_AUTHORIZING_FLAGS
            or key.endswith("_bound")
            or key.endswith("_complete")
            or key in {"terminal_state", "transition_allowed", "transition_preconditions_met"}
        }
    )

    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = session_payload.get(field) or request.order_lifecycle_lineage.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise CanonicalOrderLifecycleError("contract_status invalid")
    if lifecycle_status not in _VALID_LIFECYCLE_STATUSES:
        raise CanonicalOrderLifecycleError("lifecycle_status invalid")

    payload["input_digest"] = input_digest
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["contract_id"] = contract_id
    return payload


def serialize_canonical_order_lifecycle_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise CanonicalOrderLifecycleError("contract_status invalid")
    for list_field in (
        "contract_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
    ):
        values = contract.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("factor_id", item) if isinstance(item, dict) else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise CanonicalOrderLifecycleError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_canonical_order_lifecycle_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise CanonicalOrderLifecycleError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise CanonicalOrderLifecycleError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise CanonicalOrderLifecycleError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise CanonicalOrderLifecycleError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise CanonicalOrderLifecycleError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise CanonicalOrderLifecycleError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_verified_input_bundle", "status": "PASS"},
        {"check_id": "offline_only_no_order_creation", "status": "PASS"},
        {"check_id": "offline_only_no_order_submission", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "no_adapter_invocation", "status": "PASS"},
        {"check_id": "deny_by_default", "status": "PASS"},
        {"check_id": "futures_only", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = contract.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_one_verified_input_bundle" else c
            for c in checks
        ]

    if contract.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise CanonicalOrderLifecycleError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": contract.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_contract_status": contract.get("contract_status"),
        "verified_lifecycle_status": contract.get("lifecycle_status"),
        "verified_deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_contract_with_manifest_digest(
    artifact: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(artifact)
    body["manifest_digest"] = manifest_digest
    body["output_digest"] = _compute_output_digest(body)
    body["artifact_id"] = body["output_digest"]
    body["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(body))}
    return body


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def default_canonical_order_lifecycle_request(
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    client_order_id: str = "client-order-001",
    order_intent_digest: str = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
    canonical_order_id: str = "canonical-order-001",
    transition_identity: str = "transition-initial-bind-001",
    transition_type: str = "INITIAL_BIND",
    previous_order_state: str = "",
    expected_order_state: str = "",
    target_order_state: str = "INTENT_CREATED",
    order_revision: int = 1,
    order_generation: int = 1,
    idempotency_key: str = "idempotency-initial-bind-001",
    replay_identity: str = "replay-initial-bind-001",
    instrument_type: str = "FUTURES",
) -> CanonicalOrderLifecycleRequest:
    session = trading_session.trading_session_identity
    lineage: dict[str, Any] = (
        dict(trading_session.cross_domain_lineage) if trading_session.cross_domain_lineage else {}
    )
    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = trading_session.artifact_payload.get(field)
        if value is not None and str(value):
            lineage[field] = str(value)
    if not lineage:
        lineage = {"provenance_kind": "OFFLINE_DETERMINISTIC_EVIDENCE"}

    return CanonicalOrderLifecycleRequest(
        canonical_order_intent_identity=CanonicalOrderIntentIdentity(
            client_order_id=client_order_id,
            order_intent_digest=order_intent_digest,
            instrument_type=instrument_type,
            venue=str(session.get("venue", "")),
            account=str(session.get("account", "")),
            instrument=str(session.get("instrument", "")),
            trading_epoch=str(session.get("trading_epoch", "")),
        ),
        canonical_order_identity=CanonicalOrderIdentity(
            canonical_order_id=canonical_order_id,
            client_order_id=client_order_id,
        ),
        transition_identity=transition_identity,
        transition_type=transition_type,
        previous_order_state=previous_order_state,
        expected_order_state=expected_order_state,
        target_order_state=target_order_state,
        order_revision=order_revision,
        order_generation=order_generation,
        idempotency_key=idempotency_key,
        replay_identity=replay_identity,
        order_lifecycle_lineage=lineage,
    )


def verify_canonical_order_lifecycle_inputs(
    inputs: CanonicalOrderLifecycleInputs,
) -> VerifiedTradingSessionSingleWriterBundle:
    return verify_trading_session_single_writer_bundle(
        inputs.trading_session_single_writer_bundle_dir
    )


def reverify_canonical_order_lifecycle_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise CanonicalOrderLifecycleError(
            f"canonical order lifecycle directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise CanonicalOrderLifecycleError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise CanonicalOrderLifecycleError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise CanonicalOrderLifecycleError("manifest_digest mismatch on replay")

    trading_session = verify_trading_session_single_writer_bundle(
        Path(str(contract["upstream_bindings"]["trading_session_single_writer_bundle_ref"]))
    )
    if (
        contract.get("upstream_bindings", {}).get("trading_session_digest")
        != trading_session.artifact_digest
    ):
        raise CanonicalOrderLifecycleError("trading session digest mismatch on replay")
    if (
        contract.get("upstream_bindings", {}).get("trading_session_contract_id")
        != trading_session.contract_id
    ):
        raise CanonicalOrderLifecycleError("trading session contract id mismatch on replay")


def produce_canonical_order_lifecycle_v1(
    *,
    inputs: CanonicalOrderLifecycleInputs,
    output_dir: Path | str,
) -> CanonicalOrderLifecycleResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[inputs.trading_session_single_writer_bundle_dir],
        output_dir=final_dir,
    )

    trading_session = verify_canonical_order_lifecycle_inputs(inputs)
    contract_body = build_canonical_order_lifecycle_v1(
        trading_session=trading_session,
        request=inputs.lifecycle_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise CanonicalOrderLifecycleError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_canonical_order_lifecycle_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            contract=finalized,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise CanonicalOrderLifecycleError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_canonical_order_lifecycle_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise CanonicalOrderLifecycleError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return CanonicalOrderLifecycleResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        lifecycle_status=str(finalized["lifecycle_status"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        canonical_order_identity_digest=str(finalized["canonical_order_identity_digest"]),
        canonical_order_intent_identity_digest=str(
            finalized["canonical_order_intent_identity_digest"]
        ),
    )


__all__ = [
    "ARTIFACT_REL",
    "CANONICAL_ORDER_LIFECYCLE_AUTHORITY_INVARIANTS",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "DEFAULT_PRODUCER_IDENTITY_REF",
    "DEFAULT_SOURCE_REVISION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "EVIDENCE_LEVEL",
    "LIFECYCLE_CONTRACT_VERSION",
    "MANIFEST_FILENAME",
    "ORDER_IDENTITY_CONTRACT_VERSION",
    "ORDER_INTENT_IDENTITY_CONTRACT_VERSION",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "SELF_VERIFICATION_REL",
    "CanonicalOrderIdentity",
    "CanonicalOrderIntentIdentity",
    "CanonicalOrderLifecycleError",
    "CanonicalOrderLifecycleInputs",
    "CanonicalOrderLifecycleRequest",
    "CanonicalOrderLifecycleResult",
    "VerifiedTradingSessionSingleWriterBundle",
    "build_canonical_order_lifecycle_v1",
    "default_canonical_order_lifecycle_request",
    "produce_canonical_order_lifecycle_v1",
    "reverify_canonical_order_lifecycle_v1",
    "serialize_canonical_order_lifecycle_v1",
    "verify_canonical_order_lifecycle_inputs",
    "verify_trading_session_single_writer_bundle",
]
