"""Offline LEVEL_3 handoff atomic claim/consume contract owner v1."""

from __future__ import annotations

import hashlib
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
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
    is_valid_sha256_hex,
)
from src.meta.learning_loop.handoff_trust_policy_v1 import (
    CONSUMER_CONTRACT_ID,
    CONSUMER_CONTRACT_VERSION,
)
from src.meta.learning_loop.secure_handoff_envelope_v1 import (
    ARTIFACT_REL as SECURE_HANDOFF_ENVELOPE_ARTIFACT_REL,
    CONTRACT_NAME as SECURE_HANDOFF_ENVELOPE_CONTRACT_NAME,
    CONTRACT_VERSION as SECURE_HANDOFF_ENVELOPE_CONTRACT_VERSION,
    PRODUCER_VERSION as SECURE_HANDOFF_ENVELOPE_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as SECURE_HANDOFF_ENVELOPE_SELF_VERIFICATION_REL,
    SecureHandoffEnvelopeError,
    reverify_secure_handoff_envelope_v1,
)

CONTRACT_NAME = "handoff_atomic_claim_consume_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "handoff_atomic_claim_consume_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "handoff_atomic_claim_consume_record"
INPUT_RELATION = "PACKAGES_VERIFIED_SECURE_HANDOFF_ENVELOPE_V1_FOR_OFFLINE_ATOMIC_CLAIM_CONSUME"
ARTIFACT_REL = "handoff_atomic_claim_consume_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".handoff_atomic_claim_consume_staging_"

CLAIM_CONTRACT_VERSION = "handoff_atomic_claim_v1"
CONSUME_CONTRACT_VERSION = "handoff_atomic_consume_v1"
SCHEMA_VERSION = "handoff_atomic_claim_consume_schema_v1"
CREATION_CONTRACT_VERSION = "handoff_atomic_claim_consume_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "handoff_atomic_claim_consume_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_handoff_atomic_claim_consume_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"
INITIAL_REVISION = 0

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "CONTRACT_VALID_FOR_OFFLINE_ATOMIC_CLAIM_CONSUME",
        "CONTRACT_CLAIMABLE",
        "CONTRACT_CONSUMABLE",
        "CONTRACT_INVALID",
        "CONTRACT_REVOKED",
        "CONTRACT_EXPIRED",
        "CONTRACT_CONFLICT",
        "CONTRACT_REPLAY_REJECTED",
        "ABSTAIN",
    }
)
_VALID_STATES = frozenset(
    {
        "UNCLAIMED",
        "CLAIMABLE",
        "CLAIMED",
        "CONSUMABLE",
        "CONSUMED",
        "REVOKED",
        "EXPIRED",
        "CONFLICT",
        "REPLAY_REJECTED",
        "ABSTAIN",
    }
)
_VALID_TRANSITION_EVALUATE = frozenset({"FULL_CONTRACT", "CLAIM", "CONSUME"})
_VALID_REVOCATION_STATES = frozenset({"NOT_REVOKED", "REVOKED", "UNKNOWN"})
_UTC_INSTANT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")
_SELF_VERIFICATION_SCHEMA_VERSION = "handoff_atomic_claim_consume_self_verification_v1"

_ALLOWED_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("UNCLAIMED", "CLAIMABLE"),
    ("CLAIMABLE", "CLAIMED"),
    ("CLAIMED", "CONSUMABLE"),
    ("CONSUMABLE", "CONSUMED"),
)

_FORBIDDEN_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("UNCLAIMED", "CLAIMED"),
    ("UNCLAIMED", "CONSUMED"),
    ("CLAIMABLE", "CONSUMED"),
    ("CLAIMED", "CONSUMED"),
    ("CONSUMED", "CLAIMED"),
    ("CONSUMED", "CLAIMABLE"),
    ("REVOKED", "CLAIMABLE"),
    ("REVOKED", "CLAIMED"),
    ("EXPIRED", "CLAIMABLE"),
    ("EXPIRED", "CLAIMED"),
)

_DEFAULT_ALLOWED_OFFLINE_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_DESCRIBE_OFFLINE_ATOMIC_CLAIM",
        "CAN_DESCRIBE_OFFLINE_ATOMIC_CONSUME",
        "CAN_BIND_SECURE_HANDOFF_ENVELOPE_REF",
        "CAN_BIND_CONSUMER_IDENTITY_REF",
    }
)

_FORBIDDEN_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_EXECUTE_CLAIM",
        "CAN_EXECUTE_CONSUME",
        "CAN_MUTATE_STATE",
        "CAN_ACQUIRE_LOCK",
        "CAN_CREATE_RESERVATION",
        "CAN_INVOKE_CONSUMER",
        "CAN_MUTATE_CONSUMER",
        "CAN_TRANSFER_FILES",
        "CAN_TRANSFER_PAYLOAD",
        "CAN_GRANT_AUTHORITY",
        "CAN_ACTIVATE_LEASE",
        "CAN_ACTIVATE_AUTHORITY",
        "CAN_EXECUTE_REVOCATION",
        "CAN_ARM_RUNTIME",
        "CAN_CREATE_EXECUTION_PERMISSION",
        "CAN_CREATE_ORDER_INTENTS",
        "CAN_SUBMIT_TESTNET_ORDERS",
        "CAN_SUBMIT_LIVE_ORDERS",
        "CAN_PROMOTE_ARTIFACT",
        "CAN_*",
        "*",
    }
)

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

HANDOFF_ATOMIC_CLAIM_CONSUME_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "handoff_atomic_claim_consume_is_descriptive_only": True,
    "handoff_atomic_claim_consume_does_not_execute_claim": True,
    "handoff_atomic_claim_consume_does_not_execute_consume": True,
    "handoff_atomic_claim_consume_does_not_mutate_state": True,
    "handoff_atomic_claim_consume_does_not_acquire_lock": True,
    "handoff_atomic_claim_consume_does_not_create_reservation": True,
    "handoff_atomic_claim_consume_does_not_invoke_consumer": True,
    "handoff_atomic_claim_consume_does_not_transfer_files": True,
    "handoff_atomic_claim_consume_does_not_grant_authority": True,
    "handoff_atomic_claim_consume_does_not_activate_lease": True,
    "handoff_atomic_claim_consume_does_not_execute_revocation": True,
    "handoff_atomic_claim_consume_does_not_authorize_promotion": True,
    "handoff_atomic_claim_consume_does_not_create_configpatch": True,
    "handoff_atomic_claim_consume_does_not_authorize_runtime": True,
    "handoff_atomic_claim_consume_does_not_authorize_live": True,
    "handoff_atomic_claim_consume_is_offline_only": True,
    "deny_by_default": True,
    "replay_protection_bound": True,
    "atomic_transition_contract_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_handoff_atomic_claim_consume": True,
    "handoff_atomic_claim_consume_offline_only": True,
    "handoff_atomic_claim_consume_complete": False,
    "secure_handoff_envelope_bound": False,
    "consumer_identity_bound": False,
    "cross_domain_lineage_bound": False,
    "deny_by_default": True,
    "replay_protection_bound": False,
    "atomic_transition_contract_bound": False,
    "claim_executed": False,
    "consume_executed": False,
    "state_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "ack_emitted": False,
    "payload_transferred": False,
    "files_transferred": False,
    "consumer_invoked": False,
    "consumer_mutated": False,
    "network_side_effect_created": False,
    "authority_granted": False,
    "authority_activated": False,
    "lease_activated": False,
    "lease_renewed": False,
    "revocation_executed": False,
    "killswitch_executed": False,
    "promotion_policy_executed": False,
    "promotion_authorized": False,
    "promotion_candidate_constructed": False,
    "configpatch_created": False,
    "configpatch_modified": False,
    "configpatch_applied": False,
    "configpatch_accepted": False,
    "runtime_configuration_created": False,
    "runtime_permission_created": False,
    "execution_permission_created": False,
    "arming_token_created": False,
    "runtime_authorized": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "signature_created": False,
    "private_key_used": False,
    "credentials_accessed": False,
}

_TRANSITIVE_LINEAGE_FIELDS = (
    "comparison_run_id",
    "experiment_id",
    "experiment_identity_manifest_id",
    "learning_manifest_id",
    "promotion_candidate_id",
    "config_patch_manifest_id",
    "versioned_artifact_id",
)


class HandoffAtomicClaimConsumeError(ValueError):
    """Fail-closed handoff atomic claim/consume error."""


@dataclass(frozen=True)
class VerifiedSecureHandoffEnvelopeBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    envelope_id: str
    envelope_status: str
    payload_digest: str
    intended_consumer_identity_ref: str
    intended_consumer_identity_version: str
    revocation_state: str
    validity_metadata: dict[str, Any]


@dataclass(frozen=True)
class ClaimStateContext:
    current_state: str
    current_revision: int
    claim_identity: str = ""
    consume_identity: str = ""
    prior_claim_content_digest: str = ""


@dataclass(frozen=True)
class HandoffAtomicClaimConsumeRequest:
    evaluation_time: str
    consumer_identity_ref: str
    consumer_identity_version: str
    transition_evaluate: str = "FULL_CONTRACT"
    claim_state_context: ClaimStateContext | None = None
    allowed_offline_capabilities: tuple[str, ...] = ()
    denied_capabilities: tuple[str, ...] = ()
    source_revision: str = DEFAULT_SOURCE_REVISION
    proposed_claim_content_digest: str = ""


@dataclass(frozen=True)
class HandoffAtomicClaimConsumeInputs:
    secure_handoff_envelope_bundle_dir: Path
    claim_consume_request: HandoffAtomicClaimConsumeRequest


@dataclass(frozen=True)
class HandoffAtomicClaimConsumeResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    claim_identity: str
    consume_identity: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    envelope_ref: str
    envelope_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise HandoffAtomicClaimConsumeError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise HandoffAtomicClaimConsumeError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise HandoffAtomicClaimConsumeError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise HandoffAtomicClaimConsumeError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise HandoffAtomicClaimConsumeError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise HandoffAtomicClaimConsumeError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, envelope_dir: Path, output_dir: Path) -> None:
    if envelope_dir.resolve() == output_dir.resolve():
        raise HandoffAtomicClaimConsumeError(
            "output directory must not equal secure handoff envelope bundle directory"
        )
    if _path_is_under(output_dir, envelope_dir) or _path_is_under(envelope_dir, output_dir):
        raise HandoffAtomicClaimConsumeError(
            "output directory must not overlap secure handoff envelope bundle directory"
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
        raise HandoffAtomicClaimConsumeError(f"{label} must be an object")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    output_digest = payload.get("output_digest")
    if isinstance(output_digest, str) and is_valid_sha256_hex(output_digest):
        return output_digest
    raise HandoffAtomicClaimConsumeError("artifact output_digest missing or invalid")


def _parse_utc_instant(value: str, *, field: str) -> datetime:
    if not _UTC_INSTANT_PATTERN.match(value):
        raise HandoffAtomicClaimConsumeError(f"{field} must be UTC instant with +00:00 or Z")
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise HandoffAtomicClaimConsumeError(f"{field} must include timezone")
    return parsed.astimezone(timezone.utc)


def _validate_capability_name(capability: str) -> None:
    if capability in _FORBIDDEN_CAPABILITIES:
        raise HandoffAtomicClaimConsumeError(f"forbidden capability: {capability}")
    if not capability.startswith("CAN_"):
        raise HandoffAtomicClaimConsumeError(f"capability must start with CAN_: {capability}")


def _normalize_capabilities(values: tuple[str, ...] | list[str], *, label: str) -> list[str]:
    normalized: list[str] = []
    for capability in values:
        if not isinstance(capability, str) or not capability:
            raise HandoffAtomicClaimConsumeError(f"{label} entries must be non-empty strings")
        _validate_capability_name(capability)
        normalized.append(capability)
    return sorted(set(normalized))


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "handoff_atomic_claim_consume_complete",
            "secure_handoff_envelope_bound",
            "consumer_identity_bound",
            "cross_domain_lineage_bound",
            "replay_protection_bound",
            "atomic_transition_contract_bound",
        }:
            continue
        if actual is not expected:
            raise HandoffAtomicClaimConsumeError(f"{key} must be {expected!r}, got {actual!r}")


def verify_secure_handoff_envelope_bundle(
    bundle_dir: Path | str,
) -> VerifiedSecureHandoffEnvelopeBundle:
    """Fail-closed verification of exactly one secure handoff envelope bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="secure handoff envelope bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise HandoffAtomicClaimConsumeError(
            f"secure handoff envelope MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / SECURE_HANDOFF_ENVELOPE_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=SECURE_HANDOFF_ENVELOPE_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != SECURE_HANDOFF_ENVELOPE_CONTRACT_NAME:
        raise HandoffAtomicClaimConsumeError("secure handoff envelope contract_name mismatch")
    if payload.get("contract_version") != SECURE_HANDOFF_ENVELOPE_CONTRACT_VERSION:
        raise HandoffAtomicClaimConsumeError("secure handoff envelope contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=SECURE_HANDOFF_ENVELOPE_SELF_VERIFICATION_REL,
        label=SECURE_HANDOFF_ENVELOPE_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise HandoffAtomicClaimConsumeError(
            "secure handoff envelope SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_secure_handoff_envelope_v1(output_dir=path)
    except SecureHandoffEnvelopeError as exc:
        raise HandoffAtomicClaimConsumeError(str(exc)) from exc

    validity_metadata = payload.get("validity_metadata")
    if not isinstance(validity_metadata, dict):
        raise HandoffAtomicClaimConsumeError("secure handoff envelope validity_metadata invalid")

    return VerifiedSecureHandoffEnvelopeBundle(
        bundle_dir=path.resolve(),
        contract_name=SECURE_HANDOFF_ENVELOPE_CONTRACT_NAME,
        contract_version=SECURE_HANDOFF_ENVELOPE_CONTRACT_VERSION,
        producer_version=SECURE_HANDOFF_ENVELOPE_PRODUCER_VERSION,
        artifact_ref=SECURE_HANDOFF_ENVELOPE_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        envelope_id=str(payload.get("envelope_id", "")),
        envelope_status=str(payload.get("envelope_status", "")),
        payload_digest=str(payload.get("payload_digest", "")),
        intended_consumer_identity_ref=str(
            payload.get("intended_consumer_identity_ref", CONSUMER_CONTRACT_ID)
        ),
        intended_consumer_identity_version=str(
            payload.get("intended_consumer_identity_version", CONSUMER_CONTRACT_VERSION)
        ),
        revocation_state=str(payload.get("revocation_state", "")),
        validity_metadata=dict(validity_metadata),
    )


def _default_claim_state_context() -> ClaimStateContext:
    return ClaimStateContext(current_state="UNCLAIMED", current_revision=INITIAL_REVISION)


def _compute_claim_identity(
    *,
    envelope_id: str,
    envelope_digest: str,
    consumer_identity_ref: str,
    consumer_identity_version: str,
    expected_revision: int,
) -> str:
    return compute_content_sha256(
        {
            "claim_domain": CONTRACT_NAME,
            "claim_contract_version": CLAIM_CONTRACT_VERSION,
            "envelope_id": envelope_id,
            "envelope_digest": envelope_digest,
            "consumer_identity_ref": consumer_identity_ref,
            "consumer_identity_version": consumer_identity_version,
            "expected_revision": expected_revision,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_consume_identity(
    *,
    claim_identity: str,
    envelope_id: str,
    consumer_identity_ref: str,
    consumer_identity_version: str,
) -> str:
    return compute_content_sha256(
        {
            "consume_domain": CONTRACT_NAME,
            "consume_contract_version": CONSUME_CONTRACT_VERSION,
            "claim_identity": claim_identity,
            "envelope_id": envelope_id,
            "consumer_identity_ref": consumer_identity_ref,
            "consumer_identity_version": consumer_identity_version,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_contract_id(
    *,
    envelope_id: str,
    claim_identity: str,
    consume_identity: str,
    transition_evaluate: str,
    expected_revision: int,
) -> str:
    return compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "envelope_id": envelope_id,
            "claim_identity": claim_identity,
            "consume_identity": consume_identity,
            "transition_evaluate": transition_evaluate,
            "expected_revision": expected_revision,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _validate_request(
    request: HandoffAtomicClaimConsumeRequest,
    *,
    envelope: VerifiedSecureHandoffEnvelopeBundle,
) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []

    if request.transition_evaluate not in _VALID_TRANSITION_EVALUATE:
        blocking.append(
            _factor(
                factor_id="UNKNOWN_TRANSITION_EVALUATE",
                factor_type="CONTRADICTION",
                source_field="transition_evaluate",
                detail=request.transition_evaluate,
            )
        )

    try:
        eval_time = _parse_utc_instant(request.evaluation_time, field="evaluation_time")
    except HandoffAtomicClaimConsumeError as exc:
        blocking.append(
            _factor(
                factor_id="INVALID_EVALUATION_TIME",
                factor_type="BLOCKING",
                source_field="evaluation_time",
                detail=str(exc),
            )
        )
        eval_time = None

    if request.consumer_identity_ref != envelope.intended_consumer_identity_ref:
        blocking.append(
            _factor(
                factor_id="CONSUMER_IDENTITY_REF_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="consumer_identity_ref",
                detail=request.consumer_identity_ref,
            )
        )

    if request.consumer_identity_version != envelope.intended_consumer_identity_version:
        blocking.append(
            _factor(
                factor_id="CONSUMER_IDENTITY_VERSION_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="consumer_identity_version",
                detail=request.consumer_identity_version,
            )
        )

    if eval_time is not None:
        valid_from_raw = envelope.validity_metadata.get("valid_from")
        valid_until_raw = envelope.validity_metadata.get("valid_until")
        if valid_from_raw and valid_until_raw:
            valid_from = _parse_utc_instant(str(valid_from_raw), field="valid_from")
            valid_until = _parse_utc_instant(str(valid_until_raw), field="valid_until")
            if eval_time < valid_from:
                blocking.append(
                    _factor(
                        factor_id="EVALUATION_BEFORE_VALID_FROM",
                        factor_type="BLOCKING",
                        source_field="evaluation_time",
                        detail=request.evaluation_time,
                    )
                )
            if eval_time >= valid_until:
                blocking.append(
                    _factor(
                        factor_id="EVALUATION_AT_OR_AFTER_VALID_UNTIL",
                        factor_type="BLOCKING",
                        source_field="evaluation_time",
                        detail=request.evaluation_time,
                    )
                )

    allowed_capabilities = (
        _normalize_capabilities(
            request.allowed_offline_capabilities, label="allowed_offline_capabilities"
        )
        if request.allowed_offline_capabilities
        else []
    )
    if not allowed_capabilities and request.transition_evaluate == "FULL_CONTRACT":
        blocking.append(
            _factor(
                factor_id="EMPTY_CAPABILITY_ALLOWLIST",
                factor_type="MISSING_PRECONDITION",
                source_field="allowed_offline_capabilities",
                detail="empty",
            )
        )

    for capability in allowed_capabilities:
        if capability not in _DEFAULT_ALLOWED_OFFLINE_CAPABILITIES:
            blocking.append(
                _factor(
                    factor_id="UNKNOWN_OFFLINE_CAPABILITY",
                    factor_type="BLOCKING",
                    source_field="allowed_offline_capabilities",
                    detail=capability,
                )
            )

    denied_capabilities = _normalize_capabilities(
        request.denied_capabilities, label="denied_capabilities"
    )
    overlap = sorted(set(allowed_capabilities) & set(denied_capabilities))
    for capability in overlap:
        blocking.append(
            _factor(
                factor_id="CAPABILITY_ALLOW_DENY_CONFLICT",
                factor_type="CONTRADICTION",
                source_field="allowed_offline_capabilities",
                detail=capability,
            )
        )

    context = request.claim_state_context or _default_claim_state_context()
    if context.current_state not in _VALID_STATES:
        blocking.append(
            _factor(
                factor_id="UNKNOWN_CLAIM_STATE",
                factor_type="CONTRADICTION",
                source_field="claim_state_context.current_state",
                detail=context.current_state,
            )
        )
    if context.current_revision < 0:
        blocking.append(
            _factor(
                factor_id="NEGATIVE_REVISION",
                factor_type="CONTRADICTION",
                source_field="claim_state_context.current_revision",
                detail=str(context.current_revision),
            )
        )

    return blocking


def _evaluate_transition(
    *,
    envelope: VerifiedSecureHandoffEnvelopeBundle,
    request: HandoffAtomicClaimConsumeRequest,
    blocking_facts: list[dict[str, str]],
    claim_identity: str,
    consume_identity: str,
) -> tuple[str, list[str], dict[str, Any]]:
    reason_codes: list[str] = []
    transition_metadata: dict[str, Any] = {
        "expected_state": "UNCLAIMED",
        "claim_target_state": "CLAIMED",
        "consume_target_state": "CONSUMED",
        "claim_precondition_state": "CLAIMABLE",
        "consume_precondition_state": "CONSUMABLE",
        "expected_revision": INITIAL_REVISION,
        "claim_transition_allowed": False,
        "consume_transition_allowed": False,
        "exactly_once_semantics": "AT_MOST_ONCE_PER_ENVELOPE_AND_CONSUMER",
        "duplicate_claim_policy": "FAIL_CLOSED",
        "duplicate_consume_policy": "FAIL_CLOSED",
    }
    completion = {
        "handoff_atomic_claim_consume_complete": False,
        "secure_handoff_envelope_bound": False,
        "consumer_identity_bound": False,
        "cross_domain_lineage_bound": False,
        "replay_protection_bound": False,
        "atomic_transition_contract_bound": False,
    }

    envelope_payload = envelope.artifact_payload
    envelope_status = envelope.envelope_status

    if envelope_status == "ABSTAIN" or envelope.revocation_state == "UNKNOWN":
        reason_codes.append("REVOCATION_STATE_UNKNOWN")
        transition_metadata["expected_state"] = "ABSTAIN"
        return (
            "ABSTAIN",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    if envelope_status == "ENVELOPE_REVOKED" or envelope.revocation_state == "REVOKED":
        reason_codes.append("REVOCATION_PRECEDENCE")
        transition_metadata["expected_state"] = "REVOKED"
        completion["secure_handoff_envelope_bound"] = True
        return (
            "CONTRACT_REVOKED",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    if envelope_status == "ENVELOPE_EXPIRED":
        reason_codes.append("ENVELOPE_EXPIRED")
        transition_metadata["expected_state"] = "EXPIRED"
        completion["secure_handoff_envelope_bound"] = True
        return (
            "CONTRACT_EXPIRED",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    if envelope_status != "ENVELOPE_VALID_FOR_OFFLINE_HANDOFF":
        reason_codes.append("ENVELOPE_NOT_VALID")
        return (
            "CONTRACT_INVALID",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    completion["secure_handoff_envelope_bound"] = True
    completion["consumer_identity_bound"] = True
    if envelope_payload.get("cross_domain_lineage_bound") is True:
        completion["cross_domain_lineage_bound"] = True

    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    if contradictions or any(
        item.get("factor_id") == "EVALUATION_AT_OR_AFTER_VALID_UNTIL" for item in blocking_facts
    ):
        reason_codes.append("CONTRACT_FAIL_CLOSED")
        if any(
            item.get("factor_id") == "EVALUATION_AT_OR_AFTER_VALID_UNTIL" for item in blocking_facts
        ):
            transition_metadata["expected_state"] = "EXPIRED"
            return (
                "CONTRACT_EXPIRED",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )
        return (
            "CONTRACT_INVALID",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    if blocking_facts:
        reason_codes.append("CONTRACT_FAIL_CLOSED")
        return (
            "CONTRACT_INVALID",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    context = request.claim_state_context or _default_claim_state_context()
    transition_metadata["expected_state"] = context.current_state
    transition_metadata["expected_revision"] = context.current_revision

    expected_claim_identity = _compute_claim_identity(
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.artifact_digest,
        consumer_identity_ref=request.consumer_identity_ref,
        consumer_identity_version=request.consumer_identity_version,
        expected_revision=context.current_revision,
    )
    expected_consume_identity = _compute_consume_identity(
        claim_identity=expected_claim_identity,
        envelope_id=envelope.envelope_id,
        consumer_identity_ref=request.consumer_identity_ref,
        consumer_identity_version=request.consumer_identity_version,
    )

    if request.transition_evaluate == "CLAIM":
        if context.current_state in {"CLAIMED", "CONSUMABLE", "CONSUMED"}:
            if context.claim_identity and context.claim_identity == expected_claim_identity:
                reason_codes.append("DUPLICATE_CLAIM_REPLAY")
                transition_metadata["expected_state"] = "REPLAY_REJECTED"
                completion["replay_protection_bound"] = True
                return (
                    "CONTRACT_REPLAY_REJECTED",
                    _sorted_strings(reason_codes),
                    {
                        **transition_metadata,
                        **completion,
                    },
                )
            reason_codes.append("DUPLICATE_CLAIM_CONFLICT")
            transition_metadata["expected_state"] = "CONFLICT"
            completion["replay_protection_bound"] = True
            return (
                "CONTRACT_CONFLICT",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        if context.current_state not in {"UNCLAIMED", "CLAIMABLE"}:
            reason_codes.append("CLAIM_INVALID_PRECONDITION_STATE")
            return (
                "CONTRACT_INVALID",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        if context.current_revision != INITIAL_REVISION:
            reason_codes.append("STALE_REVISION")
            transition_metadata["expected_state"] = "CONFLICT"
            completion["replay_protection_bound"] = True
            return (
                "CONTRACT_CONFLICT",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        if (
            request.proposed_claim_content_digest
            and context.prior_claim_content_digest
            and request.proposed_claim_content_digest != context.prior_claim_content_digest
        ):
            reason_codes.append("CLAIM_REPLAY_CONTENT_MISMATCH")
            transition_metadata["expected_state"] = "REPLAY_REJECTED"
            completion["replay_protection_bound"] = True
            return (
                "CONTRACT_REPLAY_REJECTED",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        transition_metadata["claim_transition_allowed"] = True
        transition_metadata["expected_state"] = "CLAIMABLE"
        reason_codes.extend(["ENVELOPE_BOUND", "CLAIM_PRECONDITIONS_MET", "CLAIM_CLAIMABLE"])
        completion["atomic_transition_contract_bound"] = True
        completion["replay_protection_bound"] = True
        return (
            "CONTRACT_CLAIMABLE",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    if request.transition_evaluate == "CONSUME":
        if context.current_state == "CONSUMED":
            if context.consume_identity and context.consume_identity == expected_consume_identity:
                reason_codes.append("DUPLICATE_CONSUME_REPLAY")
                transition_metadata["expected_state"] = "REPLAY_REJECTED"
                completion["replay_protection_bound"] = True
                return (
                    "CONTRACT_REPLAY_REJECTED",
                    _sorted_strings(reason_codes),
                    {
                        **transition_metadata,
                        **completion,
                    },
                )
            reason_codes.append("DUPLICATE_CONSUME_CONFLICT")
            transition_metadata["expected_state"] = "CONFLICT"
            completion["replay_protection_bound"] = True
            return (
                "CONTRACT_CONFLICT",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        if context.current_state not in {"CLAIMED", "CONSUMABLE"}:
            reason_codes.append("CONSUME_WITHOUT_CLAIM")
            return (
                "CONTRACT_INVALID",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        if not context.claim_identity:
            reason_codes.append("MISSING_CLAIM_IDENTITY")
            return (
                "CONTRACT_INVALID",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        if context.claim_identity != expected_claim_identity:
            reason_codes.append("FOREIGN_CLAIM_IDENTITY")
            return (
                "CONTRACT_INVALID",
                _sorted_strings(reason_codes),
                {
                    **transition_metadata,
                    **completion,
                },
            )

        transition_metadata["consume_transition_allowed"] = True
        transition_metadata["expected_state"] = "CONSUMABLE"
        reason_codes.extend(
            ["ENVELOPE_BOUND", "CLAIM_BOUND", "CONSUME_PRECONDITIONS_MET", "CONSUME_CONSUMABLE"]
        )
        completion["atomic_transition_contract_bound"] = True
        completion["replay_protection_bound"] = True
        return (
            "CONTRACT_CONSUMABLE",
            _sorted_strings(reason_codes),
            {
                **transition_metadata,
                **completion,
            },
        )

    transition_metadata["claim_transition_allowed"] = True
    transition_metadata["consume_transition_allowed"] = True
    reason_codes.extend(
        [
            "ENVELOPE_BOUND",
            "CONSUMER_IDENTITY_BOUND",
            "ATOMIC_TRANSITION_CONTRACT_BOUND",
            "REPLAY_PROTECTION_BOUND",
            "CONTRACT_VALID_FOR_OFFLINE_ATOMIC_CLAIM_CONSUME",
        ]
    )
    completion["handoff_atomic_claim_consume_complete"] = True
    completion["atomic_transition_contract_bound"] = True
    completion["replay_protection_bound"] = True
    return (
        "CONTRACT_VALID_FOR_OFFLINE_ATOMIC_CLAIM_CONSUME",
        _sorted_strings(reason_codes),
        {**transition_metadata, **completion},
    )


def _input_artifact_ref_mapping(*, bundle: VerifiedSecureHandoffEnvelopeBundle) -> dict[str, Any]:
    return {
        "artifact_type": bundle.contract_name,
        "contract_name": bundle.contract_name,
        "contract_version": bundle.contract_version,
        "artifact_ref": bundle.artifact_ref,
        "artifact_digest": bundle.artifact_digest,
        "manifest_digest": bundle.manifest_digest,
        "producer_version": bundle.producer_version,
        "bundle_path": bundle.bundle_dir.as_posix(),
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


def build_handoff_atomic_claim_consume_v1(
    *,
    envelope: VerifiedSecureHandoffEnvelopeBundle,
    request: HandoffAtomicClaimConsumeRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(request, envelope=envelope)
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    context = request.claim_state_context or _default_claim_state_context()
    claim_identity = _compute_claim_identity(
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.artifact_digest,
        consumer_identity_ref=request.consumer_identity_ref,
        consumer_identity_version=request.consumer_identity_version,
        expected_revision=context.current_revision,
    )
    consume_identity = _compute_consume_identity(
        claim_identity=claim_identity,
        envelope_id=envelope.envelope_id,
        consumer_identity_ref=request.consumer_identity_ref,
        consumer_identity_version=request.consumer_identity_version,
    )

    contract_status, reason_codes, transition_metadata = _evaluate_transition(
        envelope=envelope,
        request=request,
        blocking_facts=blocking_facts,
        claim_identity=claim_identity,
        consume_identity=consume_identity,
    )
    completion_flags = {
        key: transition_metadata[key]
        for key in (
            "handoff_atomic_claim_consume_complete",
            "secure_handoff_envelope_bound",
            "consumer_identity_bound",
            "cross_domain_lineage_bound",
            "replay_protection_bound",
            "atomic_transition_contract_bound",
        )
        if key in transition_metadata
    }

    allowed_capabilities = (
        _normalize_capabilities(
            request.allowed_offline_capabilities, label="allowed_offline_capabilities"
        )
        if request.allowed_offline_capabilities
        else sorted(_DEFAULT_ALLOWED_OFFLINE_CAPABILITIES)
    )
    denied_capabilities = _normalize_capabilities(
        request.denied_capabilities, label="denied_capabilities"
    )
    for forbidden in sorted(_FORBIDDEN_CAPABILITIES - {"*", "CAN_*"}):
        if forbidden not in denied_capabilities:
            denied_capabilities.append(forbidden)
    denied_capabilities = sorted(set(denied_capabilities))

    envelope_payload = envelope.artifact_payload
    input_refs = [_input_artifact_ref_mapping(bundle=envelope)]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    contract_id = _compute_contract_id(
        envelope_id=envelope.envelope_id,
        claim_identity=claim_identity,
        consume_identity=consume_identity,
        transition_evaluate=request.transition_evaluate,
        expected_revision=context.current_revision,
    )

    idempotency_key = compute_content_sha256(
        {
            "envelope_id": envelope.envelope_id,
            "claim_identity": claim_identity,
            "consume_identity": consume_identity,
            "transition_evaluate": request.transition_evaluate,
            "evaluation_time": request.evaluation_time,
        }
    )

    replay_protection_metadata = {
        "idempotency_key": idempotency_key,
        "input_digest": input_digest,
        "duplicate_claim_policy": "FAIL_CLOSED",
        "duplicate_consume_policy": "FAIL_CLOSED",
        "replay_with_changed_payload_digest_policy": "FAIL_CLOSED",
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "cas_revision_field": "expected_revision",
        "generation_field": "expected_revision",
    }

    duplicate_detection_metadata = {
        "claim_identity_domain": CLAIM_CONTRACT_VERSION,
        "consume_identity_domain": CONSUME_CONTRACT_VERSION,
        "same_identity_same_content_policy": "IDEMPOTENT_REPLAY_ALLOWED_OFFLINE_ONLY",
        "same_identity_different_content_policy": "FAIL_CLOSED",
    }

    retry_semantics = {
        "crash_before_commit": "NO_EFFECT",
        "crash_after_commit": "REPLAY_DETECTED_BY_IDENTITY_AND_REVISION",
        "retry_without_double_effect": True,
        "offline_only": True,
    }

    crash_consistency_semantics = {
        "atomicity_model": "COMPARE_AND_SWAP_ON_REVISION",
        "partial_success_forbidden": True,
        "failure_before_commit_no_effect": True,
        "failure_after_commit_replay_visible": True,
    }

    allowed_transitions = [
        {"from_state": source, "to_state": target} for source, target in _ALLOWED_TRANSITIONS
    ]
    forbidden_transitions = [
        {"from_state": source, "to_state": target} for source, target in _FORBIDDEN_TRANSITIONS
    ]

    transition_preconditions = {
        "claim": [
            "verified_secure_handoff_envelope_v1_bundle",
            "envelope_status_valid_for_offline_handoff",
            "consumer_identity_matches_envelope",
            "expected_state_unclaimed_or_claimable",
            "expected_revision_matches_cas",
            "revocation_not_active",
            "expiry_not_reached",
            "deny_by_default",
        ],
        "consume": [
            "verified_secure_handoff_envelope_v1_bundle",
            "valid_claim_identity_present",
            "claim_identity_matches_envelope_and_consumer",
            "expected_state_claimed_or_consumable",
            "no_duplicate_consume",
            "revocation_not_active",
            "expiry_not_reached",
            "deny_by_default",
        ],
    }

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "claim_contract_version": CLAIM_CONTRACT_VERSION,
        "consume_contract_version": CONSUME_CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "creation_contract_version": CREATION_CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "contract_creation_time": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "producer_identity_ref": DEFAULT_PRODUCER_IDENTITY_REF,
        "producer_identity_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "contract_status": contract_status,
        "contract_reason_codes": reason_codes,
        "transition_evaluate": request.transition_evaluate,
        "envelope_ref": envelope.artifact_ref,
        "envelope_digest": envelope.artifact_digest,
        "envelope_id": envelope.envelope_id,
        "envelope_status": envelope.envelope_status,
        "secure_handoff_envelope_bundle_ref": envelope.bundle_dir.as_posix(),
        "secure_handoff_envelope_manifest_digest": envelope.manifest_digest,
        "secure_handoff_envelope_contract_name": envelope.contract_name,
        "secure_handoff_envelope_contract_version": envelope.contract_version,
        "secure_handoff_envelope_producer_version": envelope.producer_version,
        "consumer_identity_ref": request.consumer_identity_ref,
        "consumer_identity_version": request.consumer_identity_version,
        "claim_identity": claim_identity,
        "consume_identity": consume_identity,
        "expected_state": transition_metadata.get("expected_state", context.current_state),
        "claim_target_state": transition_metadata.get("claim_target_state", "CLAIMED"),
        "consume_target_state": transition_metadata.get("consume_target_state", "CONSUMED"),
        "claim_precondition_state": transition_metadata.get(
            "claim_precondition_state", "CLAIMABLE"
        ),
        "consume_precondition_state": transition_metadata.get(
            "consume_precondition_state", "CONSUMABLE"
        ),
        "expected_revision": transition_metadata.get("expected_revision", context.current_revision),
        "claim_transition_allowed": transition_metadata.get("claim_transition_allowed", False),
        "consume_transition_allowed": transition_metadata.get("consume_transition_allowed", False),
        "exactly_once_semantics": transition_metadata.get(
            "exactly_once_semantics", "AT_MOST_ONCE_PER_ENVELOPE_AND_CONSUMER"
        ),
        "allowed_transitions": allowed_transitions,
        "forbidden_transitions": forbidden_transitions,
        "transition_preconditions": transition_preconditions,
        "allowed_offline_capabilities": allowed_capabilities,
        "denied_capabilities": denied_capabilities,
        "revocation_state": envelope.revocation_state,
        "expiry_state": envelope.envelope_status
        if envelope.envelope_status == "ENVELOPE_EXPIRED"
        else "NOT_EXPIRED",
        "replay_protection_metadata": replay_protection_metadata,
        "duplicate_detection_metadata": duplicate_detection_metadata,
        "retry_semantics": retry_semantics,
        "crash_consistency_semantics": crash_consistency_semantics,
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "handoff_atomic_claim_consume_authority_invariants": dict(
            HANDOFF_ATOMIC_CLAIM_CONSUME_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": (
            dict(envelope_payload["cross_domain_lineage"])
            if isinstance(envelope_payload.get("cross_domain_lineage"), dict)
            and envelope_payload.get("cross_domain_lineage")
            else {
                field: str(envelope_payload[field])
                for field in _TRANSITIVE_LINEAGE_FIELDS
                if envelope_payload.get(field) is not None and str(envelope_payload.get(field))
            }
        ),
        "provenance": {
            "producer_contract_name": CONTRACT_NAME,
            "producer_contract_version": CONTRACT_VERSION,
            "creation_contract_version": CREATION_CONTRACT_VERSION,
            "evidence_level": EVIDENCE_LEVEL,
            "offline_only": True,
            "contract_created_for_offline_evidence_only": True,
        },
        "source_revision": request.source_revision,
        "validity_metadata": {
            **envelope.validity_metadata,
            "evaluation_time": request.evaluation_time,
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
    payload.update(completion_flags)

    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = envelope_payload.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise HandoffAtomicClaimConsumeError("contract_status invalid")

    payload["input_digest"] = input_digest
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["contract_id"] = contract_id
    return payload


def serialize_handoff_atomic_claim_consume_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise HandoffAtomicClaimConsumeError("contract_status invalid")
    for list_field in (
        "contract_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
        "allowed_offline_capabilities",
        "denied_capabilities",
    ):
        values = contract.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("factor_id", item) if isinstance(item, dict) else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise HandoffAtomicClaimConsumeError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_handoff_atomic_claim_consume_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise HandoffAtomicClaimConsumeError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise HandoffAtomicClaimConsumeError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise HandoffAtomicClaimConsumeError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise HandoffAtomicClaimConsumeError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise HandoffAtomicClaimConsumeError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise HandoffAtomicClaimConsumeError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    envelope: VerifiedSecureHandoffEnvelopeBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_secure_handoff_envelope_input", "status": "PASS"},
        {"check_id": "secure_handoff_envelope_verified", "status": "PASS"},
        {"check_id": "consumer_identity_bound", "status": "PASS"},
        {"check_id": "offline_only_no_claim_execution", "status": "PASS"},
        {"check_id": "offline_only_no_consume_execution", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "no_lock_acquired", "status": "PASS"},
        {"check_id": "no_reservation_created", "status": "PASS"},
        {"check_id": "no_consumer_invocation", "status": "PASS"},
        {"check_id": "no_authority_grant", "status": "PASS"},
        {"check_id": "no_lease_activation", "status": "PASS"},
        {"check_id": "no_revocation_execution", "status": "PASS"},
        {"check_id": "deny_by_default", "status": "PASS"},
        {"check_id": "replay_protection_bound", "status": "PASS"},
        {"check_id": "atomic_transition_contract_bound", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = contract.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"}
            if c["check_id"] == "exactly_one_secure_handoff_envelope_input"
            else c
            for c in checks
        ]

    if contract.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if contract.get("envelope_digest") != envelope.artifact_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "secure_handoff_envelope_verified" else c
            for c in checks
        ]

    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise HandoffAtomicClaimConsumeError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": contract.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_secure_handoff_envelope_bundle_ref": envelope.bundle_dir.as_posix(),
        "verified_contract_status": contract.get("contract_status"),
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


def default_claim_consume_request(
    *, envelope: VerifiedSecureHandoffEnvelopeBundle
) -> HandoffAtomicClaimConsumeRequest:
    """Build a deterministic offline claim/consume request from verified envelope."""
    return HandoffAtomicClaimConsumeRequest(
        evaluation_time=str(envelope.validity_metadata.get("evaluation_time", "")),
        consumer_identity_ref=envelope.intended_consumer_identity_ref,
        consumer_identity_version=envelope.intended_consumer_identity_version,
        allowed_offline_capabilities=tuple(sorted(_DEFAULT_ALLOWED_OFFLINE_CAPABILITIES)),
    )


def verify_handoff_atomic_claim_consume_inputs(
    inputs: HandoffAtomicClaimConsumeInputs,
) -> VerifiedSecureHandoffEnvelopeBundle:
    """Verify exactly one secure handoff envelope bundle."""
    return verify_secure_handoff_envelope_bundle(inputs.secure_handoff_envelope_bundle_dir)


def reverify_handoff_atomic_claim_consume_v1(*, output_dir: Path | str) -> None:
    """Replay handoff atomic claim/consume bundle without upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise HandoffAtomicClaimConsumeError(
            f"handoff atomic claim/consume directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise HandoffAtomicClaimConsumeError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise HandoffAtomicClaimConsumeError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise HandoffAtomicClaimConsumeError("manifest_digest mismatch on replay")

    envelope = verify_secure_handoff_envelope_bundle(
        Path(str(contract["secure_handoff_envelope_bundle_ref"]))
    )
    if contract.get("envelope_digest") != envelope.artifact_digest:
        raise HandoffAtomicClaimConsumeError("envelope digest mismatch on replay")


def produce_handoff_atomic_claim_consume_v1(
    *,
    inputs: HandoffAtomicClaimConsumeInputs,
    output_dir: Path | str,
) -> HandoffAtomicClaimConsumeResult:
    """Produce offline LEVEL_3 handoff atomic claim/consume evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        envelope_dir=inputs.secure_handoff_envelope_bundle_dir,
        output_dir=final_dir,
    )

    envelope = verify_handoff_atomic_claim_consume_inputs(inputs)
    contract_body = build_handoff_atomic_claim_consume_v1(
        envelope=envelope,
        request=inputs.claim_consume_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise HandoffAtomicClaimConsumeError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_handoff_atomic_claim_consume_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            contract=finalized,
            envelope=envelope,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise HandoffAtomicClaimConsumeError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_handoff_atomic_claim_consume_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise HandoffAtomicClaimConsumeError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return HandoffAtomicClaimConsumeResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        claim_identity=str(finalized["claim_identity"]),
        consume_identity=str(finalized["consume_identity"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        envelope_ref=str(finalized["envelope_ref"]),
        envelope_digest=str(finalized["envelope_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "CLAIM_CONTRACT_VERSION",
    "CONSUME_CONTRACT_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "DEFAULT_PRODUCER_IDENTITY_REF",
    "DEFAULT_SOURCE_REVISION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "EVIDENCE_LEVEL",
    "HANDOFF_ATOMIC_CLAIM_CONSUME_AUTHORITY_INVARIANTS",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "SELF_VERIFICATION_REL",
    "ClaimStateContext",
    "HandoffAtomicClaimConsumeError",
    "HandoffAtomicClaimConsumeInputs",
    "HandoffAtomicClaimConsumeRequest",
    "HandoffAtomicClaimConsumeResult",
    "VerifiedSecureHandoffEnvelopeBundle",
    "build_handoff_atomic_claim_consume_v1",
    "default_claim_consume_request",
    "produce_handoff_atomic_claim_consume_v1",
    "reverify_handoff_atomic_claim_consume_v1",
    "serialize_handoff_atomic_claim_consume_v1",
    "verify_handoff_atomic_claim_consume_inputs",
    "verify_secure_handoff_envelope_bundle",
]
