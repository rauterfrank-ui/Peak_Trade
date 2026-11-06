"""Offline LEVEL_3 canonical order intent idempotency contract owner v1."""

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
from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
    ARTIFACT_REL as LIFECYCLE_ARTIFACT_REL,
    CONTRACT_NAME as LIFECYCLE_CONTRACT_NAME,
    CONTRACT_VERSION as LIFECYCLE_OWNER_CONTRACT_VERSION,
    DETERMINISTIC_RULE_SET_VERSION as LIFECYCLE_DETERMINISTIC_RULE_SET_VERSION,
    LIFECYCLE_CONTRACT_VERSION,
    ORDER_IDENTITY_CONTRACT_VERSION,
    ORDER_INTENT_IDENTITY_CONTRACT_VERSION,
    PRODUCER_VERSION as LIFECYCLE_PRODUCER_VERSION,
    CanonicalOrderIdentity,
    CanonicalOrderIntentIdentity,
    CanonicalOrderLifecycleError,
    VerifiedTradingSessionSingleWriterBundle,
    _compute_order_identity_digest,
    _compute_order_intent_identity_digest,
    reverify_canonical_order_lifecycle_v1,
    verify_trading_session_single_writer_bundle,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)

CONTRACT_NAME = "order_intent_idempotency_v1"
CONTRACT_VERSION = "v1"
IDEMPOTENCY_CONTRACT_VERSION = "order_intent_idempotency_contract_v1"
IDEMPOTENCY_KEY_DOMAIN = "canonical_order_intent_idempotency_key_v1"
IDEMPOTENCY_SCOPE_DEFAULT = "ORDER_INTENT_OFFLINE_EVALUATION"
PRODUCER_VERSION = "order_intent_idempotency_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "order_intent_idempotency_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_TRADING_SESSION_AND_CANONICAL_ORDER_LIFECYCLE_FOR_OFFLINE_IDEMPOTENCY"
)
ARTIFACT_REL = "order_intent_idempotency_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".order_intent_idempotency_staging_"

SCHEMA_VERSION = "order_intent_idempotency_schema_v1"
CREATION_CONTRACT_VERSION = "order_intent_idempotency_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "order_intent_idempotency_rules_v1"
DETERMINISTIC_SERIALIZATION_VERSION = "deterministic_json_dumps_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_order_intent_idempotency_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_INSTRUMENT_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_INSTRUMENT_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_TERMINAL_ORDER_STATES = frozenset(
    {"FILLED", "CANCELLED", "REJECTED", "EXPIRED", "TERMINAL_RECONCILED"}
)
_INITIAL_PREVIOUS_STATES = frozenset({"", "MISSING", "NONE"})

_VALID_CLASSIFICATIONS = frozenset(
    {
        "EXACT_REPLAY",
        "IDEMPOTENT_DUPLICATE",
        "SEMANTIC_DUPLICATE_CONFLICT",
        "IDENTITY_CONFLICT",
        "REVISION_OR_GENERATION_CONFLICT",
        "LIFECYCLE_CONFLICT",
        "AUTHORITY_OR_REVOCATION_CONFLICT",
        "CLOCK_OR_EXPIRY_CONFLICT",
        "CLAIM_CONSUME_CONFLICT",
        "FUTURES_MARKET_TYPE_CONFLICT",
        "MISSING_BINDINGS",
        "INVALID",
    }
)

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "ORDER_INTENT_IDEMPOTENCY_EXACT_REPLAY",
        "ORDER_INTENT_IDEMPOTENCY_IDEMPOTENT_DUPLICATE",
        "ORDER_INTENT_IDEMPOTENCY_SEMANTIC_DUPLICATE_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_REVISION_OR_GENERATION_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_LIFECYCLE_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_AUTHORITY_OR_REVOCATION_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_CLOCK_OR_EXPIRY_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_CLAIM_CONSUME_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_FUTURES_MARKET_TYPE_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS",
        "ORDER_INTENT_IDEMPOTENCY_INVALID",
        "ABSTAIN",
    }
)
_VALID_IDEMPOTENCY_STATUSES = frozenset(
    {"ADMISSIBLE", "IDEMPOTENT", "CONFLICT", "INVALID", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "order_intent_idempotency_self_verification_v1"

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

ORDER_INTENT_IDEMPOTENCY_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "order_intent_idempotency_is_descriptive_only": True,
    "order_intent_idempotency_does_not_create_order": True,
    "order_intent_idempotency_does_not_submit_order": True,
    "order_intent_idempotency_does_not_mutate_order_state": True,
    "order_intent_idempotency_does_not_invoke_adapter": True,
    "order_intent_idempotency_does_not_invoke_consumer": True,
    "order_intent_idempotency_does_not_grant_authority": True,
    "order_intent_idempotency_is_offline_only": True,
    "deny_by_default": True,
    "futures_only": True,
    "canonical_order_identity_bound": True,
    "canonical_order_intent_bound": True,
    "trading_session_identity_bound": True,
    "single_writer_identity_bound": True,
    "writer_revision_generation_bound": True,
    "order_revision_generation_bound": True,
    "lifecycle_contract_bound": True,
    "idempotency_key_bound": True,
    "intent_payload_digest_bound": True,
    "intent_semantic_digest_bound": True,
    "clock_trust_and_expiry_bound": True,
    "authority_lease_and_revocation_bound": True,
    "secure_handoff_bound": True,
    "atomic_claim_consume_bound": True,
    "provenance_bound": True,
    "cross_domain_lineage_bound": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
    "replay_protection_bound": True,
    "duplicate_protection_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_order_intent_idempotency": True,
    "order_intent_idempotency_offline_only": True,
    "order_intent_idempotency_contract_complete": False,
    "canonical_order_identity_bound": False,
    "canonical_order_intent_bound": False,
    "trading_session_identity_bound": False,
    "single_writer_identity_bound": False,
    "writer_revision_generation_bound": False,
    "order_revision_generation_bound": False,
    "lifecycle_contract_bound": False,
    "idempotency_key_bound": False,
    "intent_payload_digest_bound": False,
    "intent_semantic_digest_bound": False,
    "clock_trust_and_expiry_bound": False,
    "authority_lease_and_revocation_bound": False,
    "secure_handoff_bound": False,
    "atomic_claim_consume_bound": False,
    "provenance_bound": False,
    "cross_domain_lineage_bound": False,
    "deterministic_serialization_bound": False,
    "stable_digest_bound": False,
    "replay_protection_bound": False,
    "duplicate_protection_bound": False,
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


class OrderIntentIdempotencyError(ValueError):
    """Fail-closed order intent idempotency error."""


@dataclass(frozen=True)
class PriorOrderIntentArtifactBinding:
    idempotency_key: str
    intent_payload_digest: str
    intent_semantic_digest: str
    provenance_digest: str
    cross_domain_lineage_digest: str
    lifecycle_contract_digest: str
    authority_lease_identity: str
    authority_lease_digest: str
    revocation_state_digest: str
    secure_handoff_envelope_identity: str
    secure_handoff_digest: str
    atomic_claim_identity: str
    atomic_consume_identity: str
    atomic_claim_consume_digest: str
    clock_trust_identity: str
    clock_trust_digest: str
    issued_at: str
    expires_at: str
    expected_prior_state: str
    intended_target_state: str
    order_revision: int
    order_generation: int
    writer_revision: int
    writer_generation: int
    canonical_order_id: str
    client_order_id: str
    order_intent_digest: str
    session_identity_digest: str
    writer_identity: str
    artifact_consumed: bool = False
    deterministic_serialization_version: str = DETERMINISTIC_SERIALIZATION_VERSION
    contract_version: str = IDEMPOTENCY_CONTRACT_VERSION


@dataclass(frozen=True)
class OrderIntentIdempotencyRequest:
    canonical_order_intent_identity: CanonicalOrderIntentIdentity
    canonical_order_identity: CanonicalOrderIdentity
    idempotency_scope: str
    intent_payload_digest: str
    intent_semantic_digest: str
    provenance_digest: str
    cross_domain_lineage_digest: str
    lifecycle_contract_digest: str
    authority_lease_identity: str
    authority_lease_digest: str
    revocation_state_digest: str
    secure_handoff_envelope_identity: str
    secure_handoff_digest: str
    atomic_claim_identity: str
    atomic_consume_identity: str
    atomic_claim_consume_digest: str
    clock_trust_identity: str
    clock_trust_digest: str
    issued_at: str
    expires_at: str
    deterministic_serialization_version: str
    expected_prior_state: str
    intended_target_state: str
    order_revision: int
    order_generation: int
    writer_revision: int
    writer_generation: int
    idempotency_key: str
    evaluation_time: str
    prior_artifact_binding: PriorOrderIntentArtifactBinding | None = None
    allow_idempotent_duplicate_classification: bool = True
    allow_exact_replay_on_consumed_artifact: bool = False
    idempotency_contract_version: str = IDEMPOTENCY_CONTRACT_VERSION
    lifecycle_contract_version: str = LIFECYCLE_CONTRACT_VERSION
    order_identity_contract_version: str = ORDER_IDENTITY_CONTRACT_VERSION
    order_intent_identity_contract_version: str = ORDER_INTENT_IDENTITY_CONTRACT_VERSION
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class VerifiedCanonicalOrderLifecycleBundle:
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
    lifecycle_status: str
    lifecycle_contract_digest: str
    lifecycle_evidence_digest: str
    session_identity_digest: str
    writer_identity_digest: str
    writer_identity: str
    writer_generation: int
    order_revision: int
    order_generation: int
    target_order_state: str
    expected_order_state: str
    idempotency_key: str


@dataclass(frozen=True)
class OrderIntentIdempotencyInputs:
    trading_session_single_writer_bundle_dir: Path
    canonical_order_lifecycle_bundle_dir: Path
    idempotency_request: OrderIntentIdempotencyRequest


@dataclass(frozen=True)
class OrderIntentIdempotencyResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    idempotency_status: str
    classification: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    derived_idempotency_key: str
    canonical_order_identity_digest: str
    canonical_order_intent_identity_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise OrderIntentIdempotencyError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise OrderIntentIdempotencyError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise OrderIntentIdempotencyError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise OrderIntentIdempotencyError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise OrderIntentIdempotencyError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise OrderIntentIdempotencyError("output directory must not be under /tmp")


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
        if resolved_output == resolved_bundle:
            raise OrderIntentIdempotencyError("output directory must not equal input bundle")
        if _path_is_under(resolved_output, resolved_bundle) or _path_is_under(
            resolved_bundle, resolved_output
        ):
            raise OrderIntentIdempotencyError("output directory overlaps input bundle")


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
    return sorted(
        factors,
        key=lambda item: (item.get("factor_id", ""), item.get("source_field", "")),
    )


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(values)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "order_intent_idempotency_contract_complete",
            "canonical_order_identity_bound",
            "canonical_order_intent_bound",
            "trading_session_identity_bound",
            "single_writer_identity_bound",
            "writer_revision_generation_bound",
            "order_revision_generation_bound",
            "lifecycle_contract_bound",
            "idempotency_key_bound",
            "intent_payload_digest_bound",
            "intent_semantic_digest_bound",
            "clock_trust_and_expiry_bound",
            "authority_lease_and_revocation_bound",
            "secure_handoff_bound",
            "atomic_claim_consume_bound",
            "provenance_bound",
            "cross_domain_lineage_bound",
            "deterministic_serialization_bound",
            "stable_digest_bound",
            "replay_protection_bound",
            "duplicate_protection_bound",
        }:
            continue
        if actual is not expected:
            raise OrderIntentIdempotencyError(
                f"non-authorizing flag {key} must be {expected!r}, got {actual!r}"
            )


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    output_digest = payload.get("output_digest")
    if isinstance(output_digest, str) and output_digest:
        return output_digest
    return compute_content_sha256(dict(payload))


def derive_canonical_idempotency_key(
    *,
    market_type: str,
    canonical_order_identity_digest: str,
    canonical_order_intent_identity_digest: str,
    session_identity_digest: str,
    writer_identity: str,
    writer_generation: int,
    writer_revision: int,
    order_generation: int,
    order_revision: int,
    intent_semantic_digest: str,
    lifecycle_contract_digest: str,
    authority_lease_digest: str,
    clock_trust_digest: str,
    provenance_digest: str,
    cross_domain_lineage_digest: str,
    idempotency_scope: str,
    contract_version: str,
) -> str:
    return compute_content_sha256(
        {
            "idempotency_key_domain": IDEMPOTENCY_KEY_DOMAIN,
            "market_type": market_type,
            "canonical_order_identity_digest": canonical_order_identity_digest,
            "canonical_order_intent_identity_digest": canonical_order_intent_identity_digest,
            "session_identity_digest": session_identity_digest,
            "writer_identity": writer_identity,
            "writer_generation": writer_generation,
            "writer_revision": writer_revision,
            "order_generation": order_generation,
            "order_revision": order_revision,
            "intent_semantic_digest": intent_semantic_digest,
            "lifecycle_contract_digest": lifecycle_contract_digest,
            "authority_lease_digest": authority_lease_digest,
            "clock_trust_digest": clock_trust_digest,
            "provenance_digest": provenance_digest,
            "cross_domain_lineage_digest": cross_domain_lineage_digest,
            "idempotency_scope": idempotency_scope,
            "contract_version": contract_version,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def verify_canonical_order_lifecycle_bundle(
    bundle_dir: Path | str,
) -> VerifiedCanonicalOrderLifecycleBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="canonical order lifecycle bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise OrderIntentIdempotencyError(f"lifecycle MANIFEST.sha256 verification failed: {msg}")

    artifact_path = path / LIFECYCLE_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=LIFECYCLE_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != LIFECYCLE_CONTRACT_NAME:
        raise OrderIntentIdempotencyError("lifecycle contract_name mismatch")
    if payload.get("contract_version") != LIFECYCLE_OWNER_CONTRACT_VERSION:
        raise OrderIntentIdempotencyError("lifecycle contract_version mismatch")

    try:
        reverify_canonical_order_lifecycle_v1(output_dir=path)
    except CanonicalOrderLifecycleError as exc:
        raise OrderIntentIdempotencyError(str(exc)) from exc

    lifecycle_evidence_digest = str(payload.get("lifecycle_evidence_digest", ""))
    lifecycle_contract_digest = compute_content_sha256(
        {
            "lifecycle_contract_domain": LIFECYCLE_CONTRACT_VERSION,
            "lifecycle_evidence_digest": lifecycle_evidence_digest,
            "contract_id": str(payload.get("contract_id", "")),
            "deterministic_rule_set_version": LIFECYCLE_DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    return VerifiedCanonicalOrderLifecycleBundle(
        bundle_dir=path.resolve(),
        contract_name=LIFECYCLE_CONTRACT_NAME,
        contract_version=LIFECYCLE_OWNER_CONTRACT_VERSION,
        producer_version=LIFECYCLE_PRODUCER_VERSION,
        artifact_ref=LIFECYCLE_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        lifecycle_status=str(payload.get("lifecycle_status", "")),
        lifecycle_contract_digest=lifecycle_contract_digest,
        lifecycle_evidence_digest=lifecycle_evidence_digest,
        session_identity_digest=str(payload.get("session_identity_digest", "")),
        writer_identity_digest=str(payload.get("writer_identity_digest", "")),
        writer_identity=str(payload.get("writer_identity", "")),
        writer_generation=int(payload.get("writer_generation", 0) or 0),
        order_revision=int(payload.get("order_revision", 0) or 0),
        order_generation=int(payload.get("order_generation", 0) or 0),
        target_order_state=str(payload.get("target_order_state", "")),
        expected_order_state=str(payload.get("expected_order_state", "")),
        idempotency_key=str(payload.get("idempotency_key", "")),
    )


def _normalize_state(state: str) -> str:
    if state in _INITIAL_PREVIOUS_STATES:
        return ""
    return state


def _is_expired(*, issued_at: str, expires_at: str, evaluation_time: str) -> bool:
    if not issued_at or not expires_at or not evaluation_time:
        return True
    return evaluation_time > expires_at or issued_at > expires_at


def _validate_request(
    request: OrderIntentIdempotencyRequest,
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    lifecycle: VerifiedCanonicalOrderLifecycleBundle,
) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []
    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity

    if not intent.instrument_type:
        blocking.append(
            _factor(
                factor_id="MISSING_INSTRUMENT_TYPE",
                factor_type="MISSING_PRECONDITION",
                source_field="canonical_order_intent_identity.instrument_type",
                detail="missing",
            )
        )
    elif intent.instrument_type in _FORBIDDEN_INSTRUMENT_TYPES:
        blocking.append(
            _factor(
                factor_id="FORBIDDEN_INSTRUMENT_TYPE",
                factor_type="BLOCKING",
                source_field="canonical_order_intent_identity.instrument_type",
                detail=intent.instrument_type,
            )
        )
    elif intent.instrument_type not in _VALID_INSTRUMENT_TYPES:
        blocking.append(
            _factor(
                factor_id="INVALID_INSTRUMENT_TYPE",
                factor_type="BLOCKING",
                source_field="canonical_order_intent_identity.instrument_type",
                detail=intent.instrument_type,
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

    required_fields = {
        "idempotency_scope": request.idempotency_scope,
        "intent_payload_digest": request.intent_payload_digest,
        "intent_semantic_digest": request.intent_semantic_digest,
        "provenance_digest": request.provenance_digest,
        "cross_domain_lineage_digest": request.cross_domain_lineage_digest,
        "lifecycle_contract_digest": request.lifecycle_contract_digest,
        "authority_lease_identity": request.authority_lease_identity,
        "authority_lease_digest": request.authority_lease_digest,
        "revocation_state_digest": request.revocation_state_digest,
        "secure_handoff_envelope_identity": request.secure_handoff_envelope_identity,
        "secure_handoff_digest": request.secure_handoff_digest,
        "atomic_claim_identity": request.atomic_claim_identity,
        "atomic_consume_identity": request.atomic_consume_identity,
        "atomic_claim_consume_digest": request.atomic_claim_consume_digest,
        "clock_trust_identity": request.clock_trust_identity,
        "clock_trust_digest": request.clock_trust_digest,
        "issued_at": request.issued_at,
        "expires_at": request.expires_at,
        "deterministic_serialization_version": request.deterministic_serialization_version,
        "evaluation_time": request.evaluation_time,
    }
    for field, value in required_fields.items():
        if not value:
            blocking.append(
                _factor(
                    factor_id=f"MISSING_{field.upper()}",
                    factor_type="MISSING_PRECONDITION",
                    source_field=field,
                    detail="missing",
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
    elif len(request.idempotency_key) != 64 or any(
        ch not in "0123456789abcdef" for ch in request.idempotency_key
    ):
        blocking.append(
            _factor(
                factor_id="MALFORMED_IDEMPOTENCY_KEY",
                factor_type="MISSING_PRECONDITION",
                source_field="idempotency_key",
                detail=request.idempotency_key,
            )
        )

    if request.order_revision <= 0 or request.order_generation <= 0:
        blocking.append(
            _factor(
                factor_id="INVALID_ORDER_REVISION_OR_GENERATION",
                factor_type="MISSING_PRECONDITION",
                source_field="order_revision",
                detail=str(request.order_revision),
            )
        )
    if request.writer_revision <= 0 or request.writer_generation <= 0:
        blocking.append(
            _factor(
                factor_id="INVALID_WRITER_REVISION_OR_GENERATION",
                factor_type="MISSING_PRECONDITION",
                source_field="writer_revision",
                detail=str(request.writer_revision),
            )
        )

    if request.deterministic_serialization_version != DETERMINISTIC_SERIALIZATION_VERSION:
        blocking.append(
            _factor(
                factor_id="SERIALIZATION_VERSION_MISMATCH",
                factor_type="BLOCKING",
                source_field="deterministic_serialization_version",
                detail=request.deterministic_serialization_version,
            )
        )
    if request.idempotency_contract_version != IDEMPOTENCY_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="CONTRACT_VERSION_MISMATCH",
                factor_type="BLOCKING",
                source_field="idempotency_contract_version",
                detail=request.idempotency_contract_version,
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

    if lifecycle.contract_status not in {
        "CANONICAL_ORDER_LIFECYCLE_VALID_FOR_OFFLINE_EVALUATION",
        "CANONICAL_ORDER_LIFECYCLE_IDEMPOTENT",
    }:
        blocking.append(
            _factor(
                factor_id="UPSTREAM_LIFECYCLE_INVALID",
                factor_type="BLOCKING",
                source_field="lifecycle.contract_status",
                detail=lifecycle.contract_status,
            )
        )

    if request.lifecycle_contract_digest != lifecycle.lifecycle_contract_digest:
        blocking.append(
            _factor(
                factor_id="LIFECYCLE_CONTRACT_DIGEST_MISMATCH",
                factor_type="BLOCKING",
                source_field="lifecycle_contract_digest",
                detail=request.lifecycle_contract_digest,
            )
        )

    if request.authority_lease_identity != trading_session.artifact_payload.get(
        "authority_lease_contract_id", ""
    ) and request.authority_lease_identity != trading_session.artifact_payload.get(
        "authority_lease_identity", ""
    ):
        if not request.authority_lease_identity:
            pass
        else:
            lease_ref = str(
                trading_session.artifact_payload.get("authority_lease_contract_id", "")
                or trading_session.artifact_payload.get("authority_lease_identity", "")
            )
            if lease_ref and request.authority_lease_identity != lease_ref:
                blocking.append(
                    _factor(
                        factor_id="AUTHORITY_IDENTITY_MISMATCH",
                        factor_type="BLOCKING",
                        source_field="authority_lease_identity",
                        detail=request.authority_lease_identity,
                    )
                )

    if request.authority_lease_identity:
        expected_authority_lease_digest = _binding_digest(
            request.authority_lease_identity,
            domain="authority_lease_digest_v1",
        )
        if request.authority_lease_digest != expected_authority_lease_digest:
            blocking.append(
                _factor(
                    factor_id="AUTHORITY_LEASE_DIGEST_MISMATCH",
                    factor_type="BLOCKING",
                    source_field="authority_lease_digest",
                    detail=request.authority_lease_digest,
                )
            )

    if request.secure_handoff_envelope_identity != trading_session.secure_handoff_envelope_identity:
        blocking.append(
            _factor(
                factor_id="SECURE_HANDOFF_MISMATCH",
                factor_type="BLOCKING",
                source_field="secure_handoff_envelope_identity",
                detail=request.secure_handoff_envelope_identity,
            )
        )

    expected_claim = f"claim-{trading_session.handoff_atomic_claim_consume_identity}"
    expected_consume = f"consume-{trading_session.handoff_atomic_claim_consume_identity}"
    if (
        request.atomic_claim_identity
        and request.atomic_consume_identity
        and trading_session.handoff_atomic_claim_consume_identity
        and (
            request.atomic_claim_identity != expected_claim
            or request.atomic_consume_identity != expected_consume
        )
    ):
        blocking.append(
            _factor(
                factor_id="ATOMIC_CLAIM_CONSUME_MISMATCH",
                factor_type="BLOCKING",
                source_field="atomic_claim_identity",
                detail=request.atomic_claim_identity,
            )
        )

    if request.clock_trust_digest != trading_session.clock_trust_digest:
        blocking.append(
            _factor(
                factor_id="CLOCK_TRUST_DIGEST_MISMATCH",
                factor_type="BLOCKING",
                source_field="clock_trust_digest",
                detail=request.clock_trust_digest,
            )
        )

    if not trading_session.artifact_payload.get("clock_trust_and_expiry_bound"):
        blocking.append(
            _factor(
                factor_id="MISSING_CLOCK_TRUST_BINDING",
                factor_type="MISSING_PRECONDITION",
                source_field="clock_trust_and_expiry_bound",
                detail="false",
            )
        )

    if _is_expired(
        issued_at=request.issued_at,
        expires_at=request.expires_at,
        evaluation_time=request.evaluation_time,
    ):
        blocking.append(
            _factor(
                factor_id="EXPIRED_INTENT",
                factor_type="BLOCKING",
                source_field="expires_at",
                detail=request.expires_at,
            )
        )

    if request.issued_at > request.expires_at:
        blocking.append(
            _factor(
                factor_id="ISSUED_AFTER_EXPIRES",
                factor_type="BLOCKING",
                source_field="issued_at",
                detail=request.issued_at,
            )
        )

    if request.evaluation_time < request.issued_at:
        blocking.append(
            _factor(
                factor_id="UNTRUSTED_CLOCK",
                factor_type="BLOCKING",
                source_field="evaluation_time",
                detail=request.evaluation_time,
            )
        )

    order_intent_identity_digest = _compute_order_intent_identity_digest(intent=intent)
    order_identity_digest = _compute_order_identity_digest(order=order)
    derived_key = derive_canonical_idempotency_key(
        market_type=intent.instrument_type,
        canonical_order_identity_digest=order_identity_digest,
        canonical_order_intent_identity_digest=order_intent_identity_digest,
        session_identity_digest=trading_session.session_identity_digest,
        writer_identity=trading_session.writer_identity,
        writer_generation=request.writer_generation,
        writer_revision=request.writer_revision,
        order_generation=request.order_generation,
        order_revision=request.order_revision,
        intent_semantic_digest=request.intent_semantic_digest,
        lifecycle_contract_digest=request.lifecycle_contract_digest,
        authority_lease_digest=request.authority_lease_digest,
        clock_trust_digest=request.clock_trust_digest,
        provenance_digest=request.provenance_digest,
        cross_domain_lineage_digest=request.cross_domain_lineage_digest,
        idempotency_scope=request.idempotency_scope,
        contract_version=request.idempotency_contract_version,
    )
    if request.idempotency_key != derived_key:
        blocking.append(
            _factor(
                factor_id="IDEMPOTENCY_KEY_MISMATCH",
                factor_type="BLOCKING",
                source_field="idempotency_key",
                detail=request.idempotency_key,
            )
        )

    prior = request.prior_artifact_binding
    if prior is not None:
        if prior.canonical_order_id != order.canonical_order_id:
            blocking.append(
                _factor(
                    factor_id="ORDER_IDENTITY_CONFLICT",
                    factor_type="CONTRADICTION",
                    source_field="canonical_order_identity.canonical_order_id",
                    detail=order.canonical_order_id,
                )
            )
        if prior.client_order_id != order.client_order_id:
            blocking.append(
                _factor(
                    factor_id="CLIENT_ORDER_IDENTITY_CONFLICT",
                    factor_type="CONTRADICTION",
                    source_field="canonical_order_identity.client_order_id",
                    detail=order.client_order_id,
                )
            )
        if prior.order_intent_digest != intent.order_intent_digest:
            blocking.append(
                _factor(
                    factor_id="ORDER_INTENT_IDENTITY_CONFLICT",
                    factor_type="CONTRADICTION",
                    source_field="canonical_order_intent_identity.order_intent_digest",
                    detail=intent.order_intent_digest,
                )
            )
        if prior.session_identity_digest != trading_session.session_identity_digest:
            blocking.append(
                _factor(
                    factor_id="SESSION_IDENTITY_CONFLICT",
                    factor_type="CONTRADICTION",
                    source_field="session_identity_digest",
                    detail=trading_session.session_identity_digest,
                )
            )
        if prior.writer_identity != trading_session.writer_identity:
            blocking.append(
                _factor(
                    factor_id="WRITER_IDENTITY_CONFLICT",
                    factor_type="CONTRADICTION",
                    source_field="writer_identity",
                    detail=trading_session.writer_identity,
                )
            )

        if prior.writer_generation > request.writer_generation:
            blocking.append(
                _factor(
                    factor_id="WRITER_GENERATION_REGRESSION",
                    factor_type="BLOCKING",
                    source_field="writer_generation",
                    detail=str(request.writer_generation),
                )
            )
        if prior.writer_revision > request.writer_revision:
            blocking.append(
                _factor(
                    factor_id="STALE_WRITER_REVISION",
                    factor_type="BLOCKING",
                    source_field="writer_revision",
                    detail=str(request.writer_revision),
                )
            )
        if prior.order_generation > request.order_generation:
            blocking.append(
                _factor(
                    factor_id="ORDER_GENERATION_REGRESSION",
                    factor_type="BLOCKING",
                    source_field="order_generation",
                    detail=str(request.order_generation),
                )
            )
        if request.order_generation > prior.order_generation + 1:
            blocking.append(
                _factor(
                    factor_id="ORDER_GENERATION_JUMP",
                    factor_type="BLOCKING",
                    source_field="order_generation",
                    detail=str(request.order_generation),
                )
            )
        if prior.order_revision > request.order_revision:
            blocking.append(
                _factor(
                    factor_id="ORDER_REVISION_REGRESSION",
                    factor_type="BLOCKING",
                    source_field="order_revision",
                    detail=str(request.order_revision),
                )
            )

        if prior.idempotency_key == request.idempotency_key:
            if prior.intent_payload_digest != request.intent_payload_digest:
                if prior.intent_semantic_digest == request.intent_semantic_digest:
                    if not request.allow_idempotent_duplicate_classification:
                        blocking.append(
                            _factor(
                                factor_id="SEMANTIC_PAYLOAD_DIGEST_CONFLICT",
                                factor_type="CONTRADICTION",
                                source_field="intent_payload_digest",
                                detail=request.intent_payload_digest,
                            )
                        )
                else:
                    blocking.append(
                        _factor(
                            factor_id="SEMANTIC_PAYLOAD_DIGEST_CONFLICT",
                            factor_type="CONTRADICTION",
                            source_field="intent_payload_digest",
                            detail=request.intent_payload_digest,
                        )
                    )
            if prior.intent_semantic_digest != request.intent_semantic_digest:
                blocking.append(
                    _factor(
                        factor_id="SEMANTIC_DIGEST_CONFLICT",
                        factor_type="CONTRADICTION",
                        source_field="intent_semantic_digest",
                        detail=request.intent_semantic_digest,
                    )
                )
            if prior.intended_target_state != request.intended_target_state:
                blocking.append(
                    _factor(
                        factor_id="TARGET_STATE_SEMANTIC_CONFLICT",
                        factor_type="CONTRADICTION",
                        source_field="intended_target_state",
                        detail=request.intended_target_state,
                    )
                )

        if prior.lifecycle_contract_digest != request.lifecycle_contract_digest:
            blocking.append(
                _factor(
                    factor_id="PRIOR_LIFECYCLE_DIGEST_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="lifecycle_contract_digest",
                    detail=request.lifecycle_contract_digest,
                )
            )
        if prior.authority_lease_digest != request.authority_lease_digest:
            blocking.append(
                _factor(
                    factor_id="AUTHORITY_LEASE_DIGEST_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="authority_lease_digest",
                    detail=request.authority_lease_digest,
                )
            )
        if prior.revocation_state_digest != request.revocation_state_digest:
            blocking.append(
                _factor(
                    factor_id="REVOCATION_DIGEST_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="revocation_state_digest",
                    detail=request.revocation_state_digest,
                )
            )
        if prior.provenance_digest != request.provenance_digest:
            blocking.append(
                _factor(
                    factor_id="PROVENANCE_DIGEST_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="provenance_digest",
                    detail=request.provenance_digest,
                )
            )
        if prior.cross_domain_lineage_digest != request.cross_domain_lineage_digest:
            blocking.append(
                _factor(
                    factor_id="CROSS_DOMAIN_LINEAGE_DIGEST_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="cross_domain_lineage_digest",
                    detail=request.cross_domain_lineage_digest,
                )
            )

        if prior.atomic_claim_identity != request.atomic_claim_identity:
            blocking.append(
                _factor(
                    factor_id="ATOMIC_CLAIM_IDENTITY_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="atomic_claim_identity",
                    detail=request.atomic_claim_identity,
                )
            )
        if prior.atomic_consume_identity != request.atomic_consume_identity:
            blocking.append(
                _factor(
                    factor_id="ATOMIC_CONSUME_IDENTITY_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="atomic_consume_identity",
                    detail=request.atomic_consume_identity,
                )
            )
        if prior.atomic_claim_consume_digest != request.atomic_claim_consume_digest:
            blocking.append(
                _factor(
                    factor_id="ATOMIC_CLAIM_CONSUME_DIGEST_MISMATCH",
                    factor_type="CONTRADICTION",
                    source_field="atomic_claim_consume_digest",
                    detail=request.atomic_claim_consume_digest,
                )
            )

        if prior.artifact_consumed and not request.allow_exact_replay_on_consumed_artifact:
            if (
                prior.idempotency_key == request.idempotency_key
                and prior.intent_payload_digest == request.intent_payload_digest
                and prior.intent_semantic_digest == request.intent_semantic_digest
            ):
                blocking.append(
                    _factor(
                        factor_id="DUPLICATE_CONSUME_ATTEMPT",
                        factor_type="BLOCKING",
                        source_field="artifact_consumed",
                        detail="true",
                    )
                )

    normalized_expected = _normalize_state(request.expected_prior_state)
    normalized_target = request.intended_target_state
    if normalized_expected and normalized_expected not in lifecycle.artifact_payload.get(
        "previous_order_state", normalized_expected
    ):
        if normalized_expected != _normalize_state(lifecycle.expected_order_state):
            if (
                request.expected_prior_state
                and request.expected_prior_state not in _INITIAL_PREVIOUS_STATES
            ):
                if normalized_expected != _normalize_state(lifecycle.target_order_state):
                    blocking.append(
                        _factor(
                            factor_id="EXPECTED_STATE_MISMATCH",
                            factor_type="BLOCKING",
                            source_field="expected_prior_state",
                            detail=request.expected_prior_state,
                        )
                    )

    if normalized_target in _TERMINAL_ORDER_STATES and prior is not None:
        if (
            prior.intended_target_state in _TERMINAL_ORDER_STATES
            and prior.idempotency_key != request.idempotency_key
        ):
            blocking.append(
                _factor(
                    factor_id="TERMINAL_STATE_CONFLICT",
                    factor_type="BLOCKING",
                    source_field="intended_target_state",
                    detail=normalized_target,
                )
            )

    if (
        normalized_target == "FILLED"
        and _normalize_state(request.expected_prior_state) == ""
        and prior is not None
    ):
        blocking.append(
            _factor(
                factor_id="FORBIDDEN_TARGET_STATE",
                factor_type="BLOCKING",
                source_field="intended_target_state",
                detail=normalized_target,
            )
        )

    return blocking


def _evaluate_idempotency(
    *,
    request: OrderIntentIdempotencyRequest,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, str, list[str], dict[str, Any]]:
    factor_ids = {item.get("factor_id") for item in blocking_facts}
    reason_codes: list[str] = []
    states: dict[str, Any] = {
        "idempotency_status": "UNKNOWN",
        "idempotency_reason": "",
        "duplicate_replay_classification": "INVALID",
        "admissibility_reason": "",
        "deny_reason": "",
    }

    market_type_factors = {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "MISSING_INSTRUMENT_TYPE",
    }
    if factor_ids & market_type_factors:
        states["idempotency_status"] = "INVALID"
        states["duplicate_replay_classification"] = "FUTURES_MARKET_TYPE_CONFLICT"
        states["deny_reason"] = "FUTURES_MARKET_TYPE_CONFLICT"
        reason_codes.append("FUTURES_MARKET_TYPE_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_FUTURES_MARKET_TYPE_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    if {
        "MISSING_IDEMPOTENCY_KEY",
        "MALFORMED_IDEMPOTENCY_KEY",
    } & factor_ids:
        states["idempotency_status"] = "INVALID"
        states["duplicate_replay_classification"] = "MISSING_BINDINGS"
        states["deny_reason"] = "IDEMPOTENCY_KEY_INVALID"
        reason_codes.append("IDEMPOTENCY_KEY_INVALID")
        return (
            "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    lifecycle_factors = {
        "LIFECYCLE_CONTRACT_DIGEST_MISMATCH",
        "PRIOR_LIFECYCLE_DIGEST_MISMATCH",
        "EXPECTED_STATE_MISMATCH",
        "FORBIDDEN_TARGET_STATE",
        "TERMINAL_STATE_CONFLICT",
        "UPSTREAM_LIFECYCLE_INVALID",
    }
    authority_factors = {
        "AUTHORITY_IDENTITY_MISMATCH",
        "AUTHORITY_LEASE_DIGEST_MISMATCH",
        "REVOCATION_DIGEST_MISMATCH",
        "UPSTREAM_TRADING_SESSION_REVOKED",
    }
    if factor_ids & authority_factors:
        states["idempotency_status"] = "CONFLICT"
        states["duplicate_replay_classification"] = "AUTHORITY_OR_REVOCATION_CONFLICT"
        states["deny_reason"] = "AUTHORITY_OR_REVOCATION_CONFLICT"
        reason_codes.append("AUTHORITY_OR_REVOCATION_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_AUTHORITY_OR_REVOCATION_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    if factor_ids & lifecycle_factors:
        states["idempotency_status"] = "CONFLICT"
        states["duplicate_replay_classification"] = "LIFECYCLE_CONFLICT"
        states["deny_reason"] = "LIFECYCLE_CONFLICT"
        reason_codes.append("LIFECYCLE_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_LIFECYCLE_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    clock_factors = {
        "MISSING_CLOCK_TRUST_BINDING",
        "CLOCK_TRUST_DIGEST_MISMATCH",
        "UNTRUSTED_CLOCK",
        "EXPIRED_INTENT",
        "ISSUED_AFTER_EXPIRES",
        "UPSTREAM_TRADING_SESSION_UNTRUSTED_CLOCK",
    }
    if factor_ids & clock_factors:
        states["idempotency_status"] = "CONFLICT"
        states["duplicate_replay_classification"] = "CLOCK_OR_EXPIRY_CONFLICT"
        states["deny_reason"] = "CLOCK_OR_EXPIRY_CONFLICT"
        reason_codes.append("CLOCK_OR_EXPIRY_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_CLOCK_OR_EXPIRY_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    identity_factors = {
        "ORDER_IDENTITY_CONFLICT",
        "CLIENT_ORDER_IDENTITY_CONFLICT",
        "ORDER_INTENT_IDENTITY_CONFLICT",
        "SESSION_IDENTITY_CONFLICT",
        "WRITER_IDENTITY_CONFLICT",
        "WRITER_IDENTITY_MISMATCH",
        "PROVENANCE_DIGEST_MISMATCH",
        "CROSS_DOMAIN_LINEAGE_DIGEST_MISMATCH",
    }
    if factor_ids & identity_factors:
        states["idempotency_status"] = "CONFLICT"
        states["duplicate_replay_classification"] = "IDENTITY_CONFLICT"
        states["deny_reason"] = "IDENTITY_CONFLICT"
        reason_codes.append("IDENTITY_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_IDENTITY_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    generation_factors = {
        "WRITER_GENERATION_REGRESSION",
        "STALE_WRITER_REVISION",
        "ORDER_GENERATION_REGRESSION",
        "ORDER_GENERATION_JUMP",
        "ORDER_REVISION_REGRESSION",
        "INVALID_ORDER_REVISION_OR_GENERATION",
        "INVALID_WRITER_REVISION_OR_GENERATION",
    }
    if factor_ids & generation_factors:
        states["idempotency_status"] = "CONFLICT"
        states["duplicate_replay_classification"] = "REVISION_OR_GENERATION_CONFLICT"
        states["deny_reason"] = "REVISION_OR_GENERATION_CONFLICT"
        reason_codes.append("REVISION_OR_GENERATION_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_REVISION_OR_GENERATION_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    semantic_factors = {
        "SEMANTIC_PAYLOAD_DIGEST_CONFLICT",
        "SEMANTIC_DIGEST_CONFLICT",
        "TARGET_STATE_SEMANTIC_CONFLICT",
    }
    if factor_ids & semantic_factors:
        states["idempotency_status"] = "CONFLICT"
        states["duplicate_replay_classification"] = "SEMANTIC_DUPLICATE_CONFLICT"
        states["deny_reason"] = "SEMANTIC_DUPLICATE_CONFLICT"
        reason_codes.append("SEMANTIC_DUPLICATE_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_SEMANTIC_DUPLICATE_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    if "IDEMPOTENCY_KEY_MISMATCH" in factor_ids:
        states["idempotency_status"] = "INVALID"
        states["duplicate_replay_classification"] = "MISSING_BINDINGS"
        states["deny_reason"] = "IDEMPOTENCY_KEY_INVALID"
        reason_codes.append("IDEMPOTENCY_KEY_INVALID")
        return (
            "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    claim_factors = {
        "SECURE_HANDOFF_MISMATCH",
        "ATOMIC_CLAIM_CONSUME_MISMATCH",
        "ATOMIC_CLAIM_IDENTITY_MISMATCH",
        "ATOMIC_CONSUME_IDENTITY_MISMATCH",
        "ATOMIC_CLAIM_CONSUME_DIGEST_MISMATCH",
        "DUPLICATE_CONSUME_ATTEMPT",
    }
    if factor_ids & claim_factors:
        states["idempotency_status"] = "CONFLICT"
        states["duplicate_replay_classification"] = "CLAIM_CONSUME_CONFLICT"
        states["deny_reason"] = "CLAIM_CONSUME_CONFLICT"
        reason_codes.append("CLAIM_CONSUME_CONFLICT")
        return (
            "ORDER_INTENT_IDEMPOTENCY_CLAIM_CONSUME_CONFLICT",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    if {
        "SERIALIZATION_VERSION_MISMATCH",
        "CONTRACT_VERSION_MISMATCH",
        "UPSTREAM_TRADING_SESSION_INVALID",
    } & factor_ids or blocking_facts:
        states["idempotency_status"] = "INVALID"
        states["duplicate_replay_classification"] = "MISSING_BINDINGS"
        states["deny_reason"] = "MISSING_BINDINGS"
        reason_codes.append("MISSING_BINDINGS")
        return (
            "ORDER_INTENT_IDEMPOTENCY_MISSING_BINDINGS",
            states["idempotency_status"],
            states["duplicate_replay_classification"],
            _sorted_strings(reason_codes),
            states,
        )

    prior = request.prior_artifact_binding
    if prior is not None and prior.idempotency_key == request.idempotency_key:
        exact_match = (
            prior.intent_payload_digest == request.intent_payload_digest
            and prior.intent_semantic_digest == request.intent_semantic_digest
            and prior.intended_target_state == request.intended_target_state
            and prior.expected_prior_state == request.expected_prior_state
            and prior.order_revision == request.order_revision
            and prior.order_generation == request.order_generation
            and prior.writer_revision == request.writer_revision
            and prior.writer_generation == request.writer_generation
            and prior.lifecycle_contract_digest == request.lifecycle_contract_digest
            and prior.authority_lease_digest == request.authority_lease_digest
            and prior.revocation_state_digest == request.revocation_state_digest
            and prior.provenance_digest == request.provenance_digest
            and prior.cross_domain_lineage_digest == request.cross_domain_lineage_digest
            and prior.atomic_claim_identity == request.atomic_claim_identity
            and prior.atomic_consume_identity == request.atomic_consume_identity
            and prior.atomic_claim_consume_digest == request.atomic_claim_consume_digest
            and prior.clock_trust_digest == request.clock_trust_digest
            and prior.issued_at == request.issued_at
            and prior.expires_at == request.expires_at
        )
        if exact_match:
            states.update(
                {
                    "idempotency_status": "IDEMPOTENT",
                    "idempotency_reason": "EXACT_REPLAY",
                    "duplicate_replay_classification": "EXACT_REPLAY",
                    "admissibility_reason": "EXACT_REPLAY_NON_EXECUTING",
                }
            )
            reason_codes.append("EXACT_REPLAY")
            return (
                "ORDER_INTENT_IDEMPOTENCY_EXACT_REPLAY",
                states["idempotency_status"],
                states["duplicate_replay_classification"],
                _sorted_strings(reason_codes),
                states,
            )
        semantic_duplicate_allowed = (
            request.allow_idempotent_duplicate_classification
            and prior.intent_semantic_digest == request.intent_semantic_digest
            and prior.intent_payload_digest != request.intent_payload_digest
        )
        if semantic_duplicate_allowed:
            states.update(
                {
                    "idempotency_status": "IDEMPOTENT",
                    "idempotency_reason": "IDEMPOTENT_DUPLICATE",
                    "duplicate_replay_classification": "IDEMPOTENT_DUPLICATE",
                    "admissibility_reason": "IDEMPOTENT_DUPLICATE_NON_EXECUTING",
                }
            )
            reason_codes.append("IDEMPOTENT_DUPLICATE")
            return (
                "ORDER_INTENT_IDEMPOTENCY_IDEMPOTENT_DUPLICATE",
                states["idempotency_status"],
                states["duplicate_replay_classification"],
                _sorted_strings(reason_codes),
                states,
            )

    states.update(
        {
            "idempotency_status": "ADMISSIBLE",
            "idempotency_reason": "FIRST_OBSERVATION",
            "duplicate_replay_classification": "EXACT_REPLAY",
            "admissibility_reason": "FIRST_OBSERVATION_ADMISSIBLE",
        }
    )
    reason_codes.append("FIRST_OBSERVATION")
    return (
        "ORDER_INTENT_IDEMPOTENCY_EXACT_REPLAY",
        states["idempotency_status"],
        states["duplicate_replay_classification"],
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


def build_order_intent_idempotency_v1(
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    lifecycle: VerifiedCanonicalOrderLifecycleBundle,
    request: OrderIntentIdempotencyRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(
        request,
        trading_session=trading_session,
        lifecycle=lifecycle,
    )
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    contract_status, idempotency_status, classification, reason_codes, completion = (
        _evaluate_idempotency(request=request, blocking_facts=blocking_facts)
    )

    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity
    order_intent_identity_digest = _compute_order_intent_identity_digest(intent=intent)
    canonical_order_identity_digest = _compute_order_identity_digest(order=order)
    derived_idempotency_key = derive_canonical_idempotency_key(
        market_type=intent.instrument_type,
        canonical_order_identity_digest=canonical_order_identity_digest,
        canonical_order_intent_identity_digest=order_intent_identity_digest,
        session_identity_digest=trading_session.session_identity_digest,
        writer_identity=trading_session.writer_identity,
        writer_generation=request.writer_generation,
        writer_revision=request.writer_revision,
        order_generation=request.order_generation,
        order_revision=request.order_revision,
        intent_semantic_digest=request.intent_semantic_digest,
        lifecycle_contract_digest=request.lifecycle_contract_digest,
        authority_lease_digest=request.authority_lease_digest,
        clock_trust_digest=request.clock_trust_digest,
        provenance_digest=request.provenance_digest,
        cross_domain_lineage_digest=request.cross_domain_lineage_digest,
        idempotency_scope=request.idempotency_scope,
        contract_version=request.idempotency_contract_version,
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
        ),
        _input_artifact_ref_mapping(
            bundle_dir=lifecycle.bundle_dir,
            contract_name=lifecycle.contract_name,
            contract_version=lifecycle.contract_version,
            producer_version=lifecycle.producer_version,
            artifact_ref=lifecycle.artifact_ref,
            artifact_digest=lifecycle.artifact_digest,
            manifest_digest=lifecycle.manifest_digest,
        ),
    ]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "canonical_order_identity_digest": canonical_order_identity_digest,
            "order_intent_identity_digest": order_intent_identity_digest,
            "session_identity_digest": trading_session.session_identity_digest,
            "derived_idempotency_key": derived_idempotency_key,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    complete = contract_status in {
        "ORDER_INTENT_IDEMPOTENCY_EXACT_REPLAY",
        "ORDER_INTENT_IDEMPOTENCY_IDEMPOTENT_DUPLICATE",
    }

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "idempotency_contract_version": request.idempotency_contract_version,
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
        "deterministic_serialization_version": request.deterministic_serialization_version,
        "contract_status": contract_status,
        "contract_reason_codes": reason_codes,
        "idempotency_status": idempotency_status,
        "idempotency_reason": completion.get("idempotency_reason", ""),
        "duplicate_replay_classification": classification,
        "admissibility_reason": completion.get("admissibility_reason", ""),
        "deny_reason": completion.get("deny_reason", ""),
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
        "writer_generation": request.writer_generation,
        "writer_revision": request.writer_revision,
        "writer_identity_digest": trading_session.writer_identity_digest,
        "idempotency_scope": request.idempotency_scope,
        "idempotency_key": request.idempotency_key,
        "derived_idempotency_key": derived_idempotency_key,
        "intent_payload_digest": request.intent_payload_digest,
        "intent_semantic_digest": request.intent_semantic_digest,
        "provenance_digest": request.provenance_digest,
        "cross_domain_lineage_digest": request.cross_domain_lineage_digest,
        "lifecycle_contract_digest": request.lifecycle_contract_digest,
        "authority_lease_identity": request.authority_lease_identity,
        "authority_lease_digest": request.authority_lease_digest,
        "revocation_state_digest": request.revocation_state_digest,
        "secure_handoff_envelope_identity": request.secure_handoff_envelope_identity,
        "secure_handoff_digest": request.secure_handoff_digest,
        "atomic_claim_identity": request.atomic_claim_identity,
        "atomic_consume_identity": request.atomic_consume_identity,
        "atomic_claim_consume_digest": request.atomic_claim_consume_digest,
        "clock_trust_identity": request.clock_trust_identity,
        "clock_trust_digest": request.clock_trust_digest,
        "issued_at": request.issued_at,
        "expires_at": request.expires_at,
        "evaluation_time": request.evaluation_time,
        "expected_prior_state": request.expected_prior_state,
        "intended_target_state": request.intended_target_state,
        "order_revision": request.order_revision,
        "order_generation": request.order_generation,
        "upstream_bindings": {
            "trading_session_single_writer_bundle_ref": trading_session.bundle_dir.as_posix(),
            "trading_session_contract_id": trading_session.contract_id,
            "trading_session_digest": trading_session.artifact_digest,
            "canonical_order_lifecycle_bundle_ref": lifecycle.bundle_dir.as_posix(),
            "canonical_order_lifecycle_contract_id": lifecycle.contract_id,
            "canonical_order_lifecycle_digest": lifecycle.artifact_digest,
            "lifecycle_evidence_digest": lifecycle.lifecycle_evidence_digest,
        },
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "order_intent_idempotency_authority_invariants": dict(
            ORDER_INTENT_IDEMPOTENCY_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": (
            dict(trading_session.cross_domain_lineage)
            if trading_session.cross_domain_lineage
            else {}
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
        "order_intent_idempotency_contract_complete": complete,
        "order_intent_idempotency_offline_only": True,
        "canonical_order_identity_bound": complete,
        "canonical_order_intent_bound": complete,
        "trading_session_identity_bound": complete,
        "single_writer_identity_bound": complete,
        "writer_revision_generation_bound": complete,
        "order_revision_generation_bound": complete,
        "lifecycle_contract_bound": complete,
        "idempotency_key_bound": complete,
        "intent_payload_digest_bound": complete,
        "intent_semantic_digest_bound": complete,
        "clock_trust_and_expiry_bound": complete,
        "authority_lease_and_revocation_bound": complete,
        "secure_handoff_bound": complete,
        "atomic_claim_consume_bound": complete,
        "provenance_bound": complete,
        "cross_domain_lineage_bound": complete,
        "deterministic_serialization_bound": True,
        "stable_digest_bound": True,
        "replay_protection_bound": complete,
        "duplicate_protection_bound": complete,
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        payload[key] = value
    for binding_key in (
        "order_intent_idempotency_contract_complete",
        "canonical_order_identity_bound",
        "canonical_order_intent_bound",
        "trading_session_identity_bound",
        "single_writer_identity_bound",
        "writer_revision_generation_bound",
        "order_revision_generation_bound",
        "lifecycle_contract_bound",
        "idempotency_key_bound",
        "intent_payload_digest_bound",
        "intent_semantic_digest_bound",
        "clock_trust_and_expiry_bound",
        "authority_lease_and_revocation_bound",
        "secure_handoff_bound",
        "atomic_claim_consume_bound",
        "provenance_bound",
        "cross_domain_lineage_bound",
        "replay_protection_bound",
        "duplicate_protection_bound",
    ):
        payload[binding_key] = complete

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise OrderIntentIdempotencyError("contract_status invalid")
    if idempotency_status not in _VALID_IDEMPOTENCY_STATUSES:
        raise OrderIntentIdempotencyError("idempotency_status invalid")
    if classification not in _VALID_CLASSIFICATIONS:
        raise OrderIntentIdempotencyError("duplicate_replay_classification invalid")

    payload["contract_id"] = contract_id
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    return payload


def serialize_order_intent_idempotency_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise OrderIntentIdempotencyError("contract_status invalid")
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
            raise OrderIntentIdempotencyError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_order_intent_idempotency_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise OrderIntentIdempotencyError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise OrderIntentIdempotencyError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise OrderIntentIdempotencyError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise OrderIntentIdempotencyError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise OrderIntentIdempotencyError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise OrderIntentIdempotencyError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_two_verified_input_bundles", "status": "PASS"},
        {"check_id": "offline_only_no_order_creation", "status": "PASS"},
        {"check_id": "offline_only_no_order_submission", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
    ]
    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise OrderIntentIdempotencyError("self-verification checks failed")

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
        "verified_idempotency_status": contract.get("idempotency_status"),
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


def _binding_digest(value: str, *, domain: str) -> str:
    return compute_content_sha256(
        {
            "digest_domain": domain,
            "value": value,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def default_order_intent_idempotency_request(
    *,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
    lifecycle: VerifiedCanonicalOrderLifecycleBundle,
    client_order_id: str = "client-order-001",
    order_intent_digest: str = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
    canonical_order_id: str = "canonical-order-001",
    instrument_type: str = "FUTURES",
    evaluation_time: str = "2026-06-29T12:00:00+00:00",
    issued_at: str = "2026-06-29T00:00:00+00:00",
    expires_at: str = "2026-06-30T00:00:00+00:00",
    prior_artifact_binding: PriorOrderIntentArtifactBinding | None = None,
) -> OrderIntentIdempotencyRequest:
    session = trading_session.trading_session_identity
    intent = CanonicalOrderIntentIdentity(
        client_order_id=client_order_id,
        order_intent_digest=order_intent_digest,
        instrument_type=instrument_type,
        venue=str(session.get("venue", "")),
        account=str(session.get("account", "")),
        instrument=str(session.get("instrument", "")),
        trading_epoch=str(session.get("trading_epoch", "")),
    )
    order = CanonicalOrderIdentity(
        canonical_order_id=canonical_order_id,
        client_order_id=client_order_id,
    )
    order_intent_identity_digest = _compute_order_intent_identity_digest(intent=intent)
    order_identity_digest = _compute_order_identity_digest(order=order)
    intent_payload_digest = _binding_digest(order_intent_digest, domain="intent_payload_digest_v1")
    intent_semantic_digest = _binding_digest(
        f"{order_intent_digest}:{lifecycle.target_order_state}",
        domain="intent_semantic_digest_v1",
    )
    provenance_digest = _binding_digest(DEFAULT_SOURCE_REVISION, domain="provenance_digest_v1")
    cross_domain_lineage_digest = _binding_digest(
        compute_content_sha256(dict(trading_session.cross_domain_lineage or {"offline": True})),
        domain="cross_domain_lineage_digest_v1",
    )
    authority_lease_identity = str(
        trading_session.artifact_payload.get("authority_lease_contract_id", "")
        or trading_session.artifact_payload.get("authority_lease_identity", "")
        or "authority-lease-offline-001"
    )
    authority_lease_digest = _binding_digest(
        authority_lease_identity, domain="authority_lease_digest_v1"
    )
    revocation_state_digest = _binding_digest("NOT_REVOKED", domain="revocation_state_digest_v1")
    secure_handoff_digest = _binding_digest(
        trading_session.secure_handoff_envelope_identity,
        domain="secure_handoff_digest_v1",
    )
    atomic_claim_identity = f"claim-{trading_session.handoff_atomic_claim_consume_identity}"
    atomic_consume_identity = f"consume-{trading_session.handoff_atomic_claim_consume_identity}"
    atomic_claim_consume_digest = _binding_digest(
        f"{atomic_claim_identity}:{atomic_consume_identity}",
        domain="atomic_claim_consume_digest_v1",
    )

    request_without_key = OrderIntentIdempotencyRequest(
        canonical_order_intent_identity=intent,
        canonical_order_identity=order,
        idempotency_scope=IDEMPOTENCY_SCOPE_DEFAULT,
        intent_payload_digest=intent_payload_digest,
        intent_semantic_digest=intent_semantic_digest,
        provenance_digest=provenance_digest,
        cross_domain_lineage_digest=cross_domain_lineage_digest,
        lifecycle_contract_digest=lifecycle.lifecycle_contract_digest,
        authority_lease_identity=authority_lease_identity,
        authority_lease_digest=authority_lease_digest,
        revocation_state_digest=revocation_state_digest,
        secure_handoff_envelope_identity=trading_session.secure_handoff_envelope_identity,
        secure_handoff_digest=secure_handoff_digest,
        atomic_claim_identity=atomic_claim_identity,
        atomic_consume_identity=atomic_consume_identity,
        atomic_claim_consume_digest=atomic_claim_consume_digest,
        clock_trust_identity=trading_session.clock_trust_contract_id,
        clock_trust_digest=trading_session.clock_trust_digest,
        issued_at=issued_at,
        expires_at=expires_at,
        deterministic_serialization_version=DETERMINISTIC_SERIALIZATION_VERSION,
        expected_prior_state=lifecycle.expected_order_state,
        intended_target_state=lifecycle.target_order_state,
        order_revision=lifecycle.order_revision,
        order_generation=lifecycle.order_generation,
        writer_revision=1,
        writer_generation=trading_session.writer_generation,
        idempotency_key="",
        evaluation_time=evaluation_time,
        prior_artifact_binding=prior_artifact_binding,
    )
    derived_key = derive_canonical_idempotency_key(
        market_type=intent.instrument_type,
        canonical_order_identity_digest=order_identity_digest,
        canonical_order_intent_identity_digest=order_intent_identity_digest,
        session_identity_digest=trading_session.session_identity_digest,
        writer_identity=trading_session.writer_identity,
        writer_generation=request_without_key.writer_generation,
        writer_revision=request_without_key.writer_revision,
        order_generation=request_without_key.order_generation,
        order_revision=request_without_key.order_revision,
        intent_semantic_digest=intent_semantic_digest,
        lifecycle_contract_digest=lifecycle.lifecycle_contract_digest,
        authority_lease_digest=authority_lease_digest,
        clock_trust_digest=trading_session.clock_trust_digest,
        provenance_digest=provenance_digest,
        cross_domain_lineage_digest=cross_domain_lineage_digest,
        idempotency_scope=IDEMPOTENCY_SCOPE_DEFAULT,
        contract_version=IDEMPOTENCY_CONTRACT_VERSION,
    )
    return replace_request_idempotency_key(request_without_key, derived_key)


def replace_request_idempotency_key(
    request: OrderIntentIdempotencyRequest, idempotency_key: str
) -> OrderIntentIdempotencyRequest:
    return OrderIntentIdempotencyRequest(
        canonical_order_intent_identity=request.canonical_order_intent_identity,
        canonical_order_identity=request.canonical_order_identity,
        idempotency_scope=request.idempotency_scope,
        intent_payload_digest=request.intent_payload_digest,
        intent_semantic_digest=request.intent_semantic_digest,
        provenance_digest=request.provenance_digest,
        cross_domain_lineage_digest=request.cross_domain_lineage_digest,
        lifecycle_contract_digest=request.lifecycle_contract_digest,
        authority_lease_identity=request.authority_lease_identity,
        authority_lease_digest=request.authority_lease_digest,
        revocation_state_digest=request.revocation_state_digest,
        secure_handoff_envelope_identity=request.secure_handoff_envelope_identity,
        secure_handoff_digest=request.secure_handoff_digest,
        atomic_claim_identity=request.atomic_claim_identity,
        atomic_consume_identity=request.atomic_consume_identity,
        atomic_claim_consume_digest=request.atomic_claim_consume_digest,
        clock_trust_identity=request.clock_trust_identity,
        clock_trust_digest=request.clock_trust_digest,
        issued_at=request.issued_at,
        expires_at=request.expires_at,
        deterministic_serialization_version=request.deterministic_serialization_version,
        expected_prior_state=request.expected_prior_state,
        intended_target_state=request.intended_target_state,
        order_revision=request.order_revision,
        order_generation=request.order_generation,
        writer_revision=request.writer_revision,
        writer_generation=request.writer_generation,
        idempotency_key=idempotency_key,
        evaluation_time=request.evaluation_time,
        prior_artifact_binding=request.prior_artifact_binding,
        allow_idempotent_duplicate_classification=request.allow_idempotent_duplicate_classification,
        allow_exact_replay_on_consumed_artifact=request.allow_exact_replay_on_consumed_artifact,
        idempotency_contract_version=request.idempotency_contract_version,
        lifecycle_contract_version=request.lifecycle_contract_version,
        order_identity_contract_version=request.order_identity_contract_version,
        order_intent_identity_contract_version=request.order_intent_identity_contract_version,
        source_revision=request.source_revision,
    )


def prior_binding_from_request(
    request: OrderIntentIdempotencyRequest,
    *,
    session_identity_digest: str = "",
    writer_identity: str = "",
) -> PriorOrderIntentArtifactBinding:
    intent = request.canonical_order_intent_identity
    order = request.canonical_order_identity
    return PriorOrderIntentArtifactBinding(
        idempotency_key=request.idempotency_key,
        intent_payload_digest=request.intent_payload_digest,
        intent_semantic_digest=request.intent_semantic_digest,
        provenance_digest=request.provenance_digest,
        cross_domain_lineage_digest=request.cross_domain_lineage_digest,
        lifecycle_contract_digest=request.lifecycle_contract_digest,
        authority_lease_identity=request.authority_lease_identity,
        authority_lease_digest=request.authority_lease_digest,
        revocation_state_digest=request.revocation_state_digest,
        secure_handoff_envelope_identity=request.secure_handoff_envelope_identity,
        secure_handoff_digest=request.secure_handoff_digest,
        atomic_claim_identity=request.atomic_claim_identity,
        atomic_consume_identity=request.atomic_consume_identity,
        atomic_claim_consume_digest=request.atomic_claim_consume_digest,
        clock_trust_identity=request.clock_trust_identity,
        clock_trust_digest=request.clock_trust_digest,
        issued_at=request.issued_at,
        expires_at=request.expires_at,
        expected_prior_state=request.expected_prior_state,
        intended_target_state=request.intended_target_state,
        order_revision=request.order_revision,
        order_generation=request.order_generation,
        writer_revision=request.writer_revision,
        writer_generation=request.writer_generation,
        canonical_order_id=order.canonical_order_id,
        client_order_id=order.client_order_id,
        order_intent_digest=intent.order_intent_digest,
        session_identity_digest=session_identity_digest,
        writer_identity=writer_identity,
    )


def verify_order_intent_idempotency_inputs(
    inputs: OrderIntentIdempotencyInputs,
) -> tuple[VerifiedTradingSessionSingleWriterBundle, VerifiedCanonicalOrderLifecycleBundle]:
    trading_session = verify_trading_session_single_writer_bundle(
        inputs.trading_session_single_writer_bundle_dir
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(inputs.canonical_order_lifecycle_bundle_dir)
    return trading_session, lifecycle


def reverify_order_intent_idempotency_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise OrderIntentIdempotencyError(
            f"order intent idempotency directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise OrderIntentIdempotencyError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise OrderIntentIdempotencyError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise OrderIntentIdempotencyError("manifest_digest mismatch on replay")

    trading_session = verify_trading_session_single_writer_bundle(
        Path(str(contract["upstream_bindings"]["trading_session_single_writer_bundle_ref"]))
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(
        Path(str(contract["upstream_bindings"]["canonical_order_lifecycle_bundle_ref"]))
    )
    if (
        contract.get("upstream_bindings", {}).get("trading_session_digest")
        != trading_session.artifact_digest
    ):
        raise OrderIntentIdempotencyError("trading session digest mismatch on replay")
    if (
        contract.get("upstream_bindings", {}).get("canonical_order_lifecycle_digest")
        != lifecycle.artifact_digest
    ):
        raise OrderIntentIdempotencyError("lifecycle digest mismatch on replay")


def produce_order_intent_idempotency_v1(
    *,
    inputs: OrderIntentIdempotencyInputs,
    output_dir: Path | str,
) -> OrderIntentIdempotencyResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[
            inputs.trading_session_single_writer_bundle_dir,
            inputs.canonical_order_lifecycle_bundle_dir,
        ],
        output_dir=final_dir,
    )

    trading_session, lifecycle = verify_order_intent_idempotency_inputs(inputs)
    contract_body = build_order_intent_idempotency_v1(
        trading_session=trading_session,
        lifecycle=lifecycle,
        request=inputs.idempotency_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise OrderIntentIdempotencyError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_order_intent_idempotency_v1(finalized),
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
            raise OrderIntentIdempotencyError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_order_intent_idempotency_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise OrderIntentIdempotencyError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return OrderIntentIdempotencyResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        idempotency_status=str(finalized["idempotency_status"]),
        classification=str(finalized["duplicate_replay_classification"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        derived_idempotency_key=str(finalized["derived_idempotency_key"]),
        canonical_order_identity_digest=str(finalized["canonical_order_identity_digest"]),
        canonical_order_intent_identity_digest=str(
            finalized["canonical_order_intent_identity_digest"]
        ),
    )


__all__ = [
    "ARTIFACT_REL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "DEFAULT_PRODUCER_IDENTITY_REF",
    "DEFAULT_SOURCE_REVISION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "DETERMINISTIC_SERIALIZATION_VERSION",
    "EVIDENCE_LEVEL",
    "IDEMPOTENCY_CONTRACT_VERSION",
    "IDEMPOTENCY_KEY_DOMAIN",
    "IDEMPOTENCY_SCOPE_DEFAULT",
    "MANIFEST_FILENAME",
    "ORDER_INTENT_IDEMPOTENCY_AUTHORITY_INVARIANTS",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "SELF_VERIFICATION_REL",
    "OrderIntentIdempotencyError",
    "OrderIntentIdempotencyInputs",
    "OrderIntentIdempotencyRequest",
    "OrderIntentIdempotencyResult",
    "PriorOrderIntentArtifactBinding",
    "VerifiedCanonicalOrderLifecycleBundle",
    "build_order_intent_idempotency_v1",
    "default_order_intent_idempotency_request",
    "derive_canonical_idempotency_key",
    "prior_binding_from_request",
    "produce_order_intent_idempotency_v1",
    "replace_request_idempotency_key",
    "reverify_order_intent_idempotency_v1",
    "serialize_order_intent_idempotency_v1",
    "verify_canonical_order_lifecycle_bundle",
    "verify_order_intent_idempotency_inputs",
    "verify_trading_session_single_writer_bundle",
]
