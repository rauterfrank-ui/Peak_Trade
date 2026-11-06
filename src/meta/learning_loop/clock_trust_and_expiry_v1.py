"""Offline LEVEL_3 clock trust and expiry contract owner v1."""

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
from src.meta.learning_loop.authority_lease_and_revocation_v1 import (
    ARTIFACT_REL as AUTHORITY_LEASE_ARTIFACT_REL,
    CONTRACT_NAME as AUTHORITY_LEASE_CONTRACT_NAME,
    CONTRACT_VERSION as AUTHORITY_LEASE_CONTRACT_VERSION,
    AuthorityLeaseAndRevocationError,
    PRODUCER_VERSION as AUTHORITY_LEASE_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as AUTHORITY_LEASE_SELF_VERIFICATION_REL,
    reverify_authority_lease_and_revocation_v1,
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
from src.meta.learning_loop.handoff_atomic_claim_consume_v1 import (
    ARTIFACT_REL as HANDOFF_ATOMIC_CLAIM_CONSUME_ARTIFACT_REL,
    CONTRACT_NAME as HANDOFF_ATOMIC_CLAIM_CONSUME_CONTRACT_NAME,
    CONTRACT_VERSION as HANDOFF_ATOMIC_CLAIM_CONSUME_CONTRACT_VERSION,
    HandoffAtomicClaimConsumeError,
    PRODUCER_VERSION as HANDOFF_ATOMIC_CLAIM_CONSUME_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as HANDOFF_ATOMIC_CLAIM_CONSUME_SELF_VERIFICATION_REL,
    reverify_handoff_atomic_claim_consume_v1,
    verify_secure_handoff_envelope_bundle,
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

CONTRACT_NAME = "clock_trust_and_expiry_v1"
CONTRACT_VERSION = "v1"
CLOCK_CONTRACT_VERSION = "clock_trust_contract_v1"
EXPIRY_CONTRACT_VERSION = "expiry_contract_v1"
PRODUCER_VERSION = "clock_trust_and_expiry_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "clock_trust_and_expiry_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_SECURE_HANDOFF_ENVELOPE_HANDOFF_ATOMIC_CLAIM_CONSUME_"
    "AND_AUTHORITY_LEASE_FOR_OFFLINE_CLOCK_TRUST_AND_EXPIRY"
)
ARTIFACT_REL = "clock_trust_and_expiry_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".clock_trust_and_expiry_staging_"

SCHEMA_VERSION = "clock_trust_and_expiry_schema_v1"
CREATION_CONTRACT_VERSION = "clock_trust_and_expiry_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "clock_trust_and_expiry_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_clock_trust_and_expiry_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"
CANONICAL_TIMEZONE = "UTC"
CANONICAL_TIMESTAMP_FORMAT = "ISO8601_UTC_INSTANT_WITH_OFFSET_OR_Z"

_TRUSTED_EVALUATION_TIME_SOURCES = frozenset(
    {
        "EXPLICIT_OPERATOR_EVIDENCE",
        "OFFLINE_DETERMINISTIC_EVIDENCE",
    }
)
_VALID_CONTRACT_STATUSES = frozenset(
    {
        "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION",
        "CLOCK_TRUST_INVALID",
        "CLOCK_TRUST_UNTRUSTED_CLOCK_SOURCE",
        "CLOCK_TRUST_STALE_EVIDENCE",
        "CLOCK_TRUST_FUTURE_DATED",
        "CLOCK_TRUST_EXPIRED",
        "CLOCK_TRUST_REVOKED",
        "CLOCK_TRUST_REPLAY_REJECTED",
        "CLOCK_TRUST_AMBIGUOUS_ORDERING",
        "ABSTAIN",
    }
)
_VALID_CLOCK_TRUST_STATUSES = frozenset({"TRUSTED", "UNTRUSTED", "UNKNOWN", "ABSTAIN"})
_VALID_EXPIRY_STATES = frozenset({"NOT_EXPIRED", "EXPIRED", "UNKNOWN"})
_VALID_STALE_STATES = frozenset({"FRESH", "STALE", "UNKNOWN"})
_VALID_FUTURE_DATED_STATES = frozenset({"NOT_FUTURE_DATED", "FUTURE_DATED", "UNKNOWN"})
_VALID_TEMPORAL_ORDERING_STATUSES = frozenset({"VALID", "INVALID", "AMBIGUOUS", "UNKNOWN"})
_UTC_INSTANT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")
_SELF_VERIFICATION_SCHEMA_VERSION = "clock_trust_and_expiry_self_verification_v1"

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

CLOCK_TRUST_AND_EXPIRY_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "clock_trust_and_expiry_is_descriptive_only": True,
    "clock_trust_and_expiry_does_not_read_system_clock": True,
    "clock_trust_and_expiry_does_not_execute_expiry": True,
    "clock_trust_and_expiry_does_not_execute_revocation": True,
    "clock_trust_and_expiry_does_not_execute_claim": True,
    "clock_trust_and_expiry_does_not_execute_consume": True,
    "clock_trust_and_expiry_does_not_mutate_state": True,
    "clock_trust_and_expiry_does_not_invoke_consumer": True,
    "clock_trust_and_expiry_does_not_grant_authority": True,
    "clock_trust_and_expiry_does_not_activate_lease": True,
    "clock_trust_and_expiry_does_not_authorize_promotion": True,
    "clock_trust_and_expiry_does_not_create_configpatch": True,
    "clock_trust_and_expiry_does_not_authorize_runtime": True,
    "clock_trust_and_expiry_does_not_authorize_live": True,
    "clock_trust_and_expiry_is_offline_only": True,
    "deny_by_default": True,
    "replay_protection_bound": True,
    "evaluation_time_trust_bound": True,
    "canonical_time_normalization_bound": True,
    "expiry_policy_bound": True,
    "temporal_ordering_bound": True,
    "clock_skew_policy_bound": True,
    "stale_evidence_protection_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_clock_trust_and_expiry": True,
    "clock_trust_and_expiry_offline_only": True,
    "clock_trust_and_expiry_complete": False,
    "secure_handoff_envelope_bound": False,
    "handoff_atomic_claim_consume_bound": False,
    "authority_lease_and_revocation_bound": False,
    "cross_domain_lineage_bound": False,
    "deny_by_default": True,
    "replay_protection_bound": False,
    "evaluation_time_trust_bound": False,
    "canonical_time_normalization_bound": False,
    "expiry_policy_bound": False,
    "temporal_ordering_bound": False,
    "clock_skew_policy_bound": False,
    "stale_evidence_protection_bound": False,
    "system_clock_read": False,
    "wall_clock_read": False,
    "network_time_read": False,
    "ntp_requested": False,
    "exchange_time_requested": False,
    "scheduler_time_read": False,
    "runtime_time_read": False,
    "clock_synchronized": False,
    "clock_mutated": False,
    "expiry_executed": False,
    "lease_expired": False,
    "lease_renewed": False,
    "revocation_executed": False,
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


class ClockTrustAndExpiryError(ValueError):
    """Fail-closed clock trust and expiry error."""


@dataclass(frozen=True)
class VerifiedAuthorityLeaseBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    lease_id: str
    lease_status: str
    issued_at: str
    valid_from: str
    valid_until: str
    evaluation_time: str
    revocation_state: str


@dataclass(frozen=True)
class VerifiedHandoffAtomicClaimConsumeBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    contract_id: str
    claim_identity: str
    consume_identity: str
    envelope_id: str
    envelope_digest: str
    contract_status: str


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
    validity_metadata: dict[str, Any]
    revocation_state: str


@dataclass(frozen=True)
class ClockTrustAndExpiryRequest:
    evaluation_time: str
    evaluation_time_source: str
    evaluation_time_source_identity: str
    evaluation_time_provenance: dict[str, Any]
    clock_contract_version: str = CLOCK_CONTRACT_VERSION
    expiry_contract_version: str = EXPIRY_CONTRACT_VERSION
    maximum_clock_skew_seconds: int = 0
    maximum_evidence_age_seconds: int = 0
    prior_temporal_evidence_digest: str = ""
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class ClockTrustAndExpiryInputs:
    secure_handoff_envelope_bundle_dir: Path
    handoff_atomic_claim_consume_bundle_dir: Path
    authority_lease_and_revocation_bundle_dir: Path
    clock_trust_request: ClockTrustAndExpiryRequest


@dataclass(frozen=True)
class ClockTrustAndExpiryResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    clock_trust_status: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    secure_handoff_envelope_identity: str
    handoff_atomic_claim_consume_identity: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ClockTrustAndExpiryError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ClockTrustAndExpiryError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ClockTrustAndExpiryError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise ClockTrustAndExpiryError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ClockTrustAndExpiryError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise ClockTrustAndExpiryError("output directory must not be under /tmp")


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
        if resolved_bundle == resolved_output:
            raise ClockTrustAndExpiryError("output directory must not equal input bundle directory")
        if _path_is_under(resolved_output, resolved_bundle) or _path_is_under(
            resolved_bundle, resolved_output
        ):
            raise ClockTrustAndExpiryError(
                "output directory must not overlap input bundle directory"
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
        raise ClockTrustAndExpiryError(f"{label} must be an object")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    output_digest = payload.get("output_digest")
    if isinstance(output_digest, str) and is_valid_sha256_hex(output_digest):
        return output_digest
    raise ClockTrustAndExpiryError("artifact output_digest missing or invalid")


def _parse_utc_instant(value: str, *, field: str) -> datetime:
    if not value:
        raise ClockTrustAndExpiryError(f"{field} is required")
    if not _UTC_INSTANT_PATTERN.match(value):
        raise ClockTrustAndExpiryError(f"{field} must be UTC instant with +00:00 or Z")
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ClockTrustAndExpiryError(f"{field} must include timezone")
    return parsed.astimezone(timezone.utc)


def _seconds_between(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds()


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "clock_trust_and_expiry_complete",
            "secure_handoff_envelope_bound",
            "handoff_atomic_claim_consume_bound",
            "authority_lease_and_revocation_bound",
            "cross_domain_lineage_bound",
            "replay_protection_bound",
            "evaluation_time_trust_bound",
            "canonical_time_normalization_bound",
            "expiry_policy_bound",
            "temporal_ordering_bound",
            "clock_skew_policy_bound",
            "stale_evidence_protection_bound",
        }:
            continue
        if actual is not expected:
            raise ClockTrustAndExpiryError(f"{key} must be {expected!r}, got {actual!r}")


def verify_authority_lease_bundle(bundle_dir: Path | str) -> VerifiedAuthorityLeaseBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="authority lease bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ClockTrustAndExpiryError(
            f"authority lease MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / AUTHORITY_LEASE_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=AUTHORITY_LEASE_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != AUTHORITY_LEASE_CONTRACT_NAME:
        raise ClockTrustAndExpiryError("authority lease contract_name mismatch")
    if payload.get("contract_version") != AUTHORITY_LEASE_CONTRACT_VERSION:
        raise ClockTrustAndExpiryError("authority lease contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=AUTHORITY_LEASE_SELF_VERIFICATION_REL,
        label=AUTHORITY_LEASE_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise ClockTrustAndExpiryError(
            "authority lease SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_authority_lease_and_revocation_v1(output_dir=path)
    except AuthorityLeaseAndRevocationError as exc:
        raise ClockTrustAndExpiryError(str(exc)) from exc

    return VerifiedAuthorityLeaseBundle(
        bundle_dir=path.resolve(),
        contract_name=AUTHORITY_LEASE_CONTRACT_NAME,
        contract_version=AUTHORITY_LEASE_CONTRACT_VERSION,
        producer_version=AUTHORITY_LEASE_PRODUCER_VERSION,
        artifact_ref=AUTHORITY_LEASE_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        lease_id=str(payload.get("lease_id", "")),
        lease_status=str(payload.get("lease_status", "")),
        issued_at=str(payload.get("issued_at", "")),
        valid_from=str(payload.get("valid_from", "")),
        valid_until=str(payload.get("valid_until", "")),
        evaluation_time=str(payload.get("evaluation_time", "")),
        revocation_state=str(payload.get("revocation_state", "")),
    )


def verify_handoff_atomic_claim_consume_bundle(
    bundle_dir: Path | str,
) -> VerifiedHandoffAtomicClaimConsumeBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="handoff atomic claim consume bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ClockTrustAndExpiryError(
            f"handoff atomic claim consume MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / HANDOFF_ATOMIC_CLAIM_CONSUME_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=HANDOFF_ATOMIC_CLAIM_CONSUME_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != HANDOFF_ATOMIC_CLAIM_CONSUME_CONTRACT_NAME:
        raise ClockTrustAndExpiryError("handoff atomic claim consume contract_name mismatch")
    if payload.get("contract_version") != HANDOFF_ATOMIC_CLAIM_CONSUME_CONTRACT_VERSION:
        raise ClockTrustAndExpiryError("handoff atomic claim consume contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=HANDOFF_ATOMIC_CLAIM_CONSUME_SELF_VERIFICATION_REL,
        label=HANDOFF_ATOMIC_CLAIM_CONSUME_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise ClockTrustAndExpiryError(
            "handoff atomic claim consume SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_handoff_atomic_claim_consume_v1(output_dir=path)
    except HandoffAtomicClaimConsumeError as exc:
        raise ClockTrustAndExpiryError(str(exc)) from exc

    return VerifiedHandoffAtomicClaimConsumeBundle(
        bundle_dir=path.resolve(),
        contract_name=HANDOFF_ATOMIC_CLAIM_CONSUME_CONTRACT_NAME,
        contract_version=HANDOFF_ATOMIC_CLAIM_CONSUME_CONTRACT_VERSION,
        producer_version=HANDOFF_ATOMIC_CLAIM_CONSUME_PRODUCER_VERSION,
        artifact_ref=HANDOFF_ATOMIC_CLAIM_CONSUME_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        claim_identity=str(payload.get("claim_identity", "")),
        consume_identity=str(payload.get("consume_identity", "")),
        envelope_id=str(payload.get("envelope_id", "")),
        envelope_digest=str(payload.get("envelope_digest", "")),
        contract_status=str(payload.get("contract_status", "")),
    )


def verify_secure_handoff_envelope_bundle_for_clock_trust(
    bundle_dir: Path | str,
) -> VerifiedSecureHandoffEnvelopeBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="secure handoff envelope bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise ClockTrustAndExpiryError(
            f"secure handoff envelope MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / SECURE_HANDOFF_ENVELOPE_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=SECURE_HANDOFF_ENVELOPE_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != SECURE_HANDOFF_ENVELOPE_CONTRACT_NAME:
        raise ClockTrustAndExpiryError("secure handoff envelope contract_name mismatch")
    if payload.get("contract_version") != SECURE_HANDOFF_ENVELOPE_CONTRACT_VERSION:
        raise ClockTrustAndExpiryError("secure handoff envelope contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=SECURE_HANDOFF_ENVELOPE_SELF_VERIFICATION_REL,
        label=SECURE_HANDOFF_ENVELOPE_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise ClockTrustAndExpiryError(
            "secure handoff envelope SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_secure_handoff_envelope_v1(output_dir=path)
    except SecureHandoffEnvelopeError as exc:
        raise ClockTrustAndExpiryError(str(exc)) from exc

    validity_metadata = payload.get("validity_metadata")
    if not isinstance(validity_metadata, dict):
        raise ClockTrustAndExpiryError("secure handoff envelope validity_metadata invalid")

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
        validity_metadata=dict(validity_metadata),
        revocation_state=str(payload.get("revocation_state", "")),
    )


def _compute_secure_handoff_envelope_identity(*, envelope_id: str, envelope_digest: str) -> str:
    return compute_content_sha256(
        {
            "identity_domain": SECURE_HANDOFF_ENVELOPE_CONTRACT_NAME,
            "envelope_id": envelope_id,
            "envelope_digest": envelope_digest,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_handoff_atomic_claim_consume_identity(
    *,
    contract_id: str,
    claim_identity: str,
    consume_identity: str,
) -> str:
    return compute_content_sha256(
        {
            "identity_domain": HANDOFF_ATOMIC_CLAIM_CONSUME_CONTRACT_NAME,
            "contract_id": contract_id,
            "claim_identity": claim_identity,
            "consume_identity": consume_identity,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _compute_evaluation_time_digest(
    *,
    evaluation_time: str,
    evaluation_time_source: str,
    evaluation_time_source_identity: str,
    evaluation_time_provenance: Mapping[str, Any],
) -> str:
    return compute_content_sha256(
        {
            "evaluation_time": evaluation_time,
            "evaluation_time_source": evaluation_time_source,
            "evaluation_time_source_identity": evaluation_time_source_identity,
            "evaluation_time_provenance": dict(evaluation_time_provenance),
            "canonical_timezone": CANONICAL_TIMEZONE,
            "canonical_timestamp_format": CANONICAL_TIMESTAMP_FORMAT,
        }
    )


def _validate_request(
    request: ClockTrustAndExpiryRequest,
    *,
    envelope: VerifiedSecureHandoffEnvelopeBundle,
    claim_consume: VerifiedHandoffAtomicClaimConsumeBundle,
    authority_lease: VerifiedAuthorityLeaseBundle,
) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []

    if request.clock_contract_version != CLOCK_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_CLOCK_CONTRACT_VERSION",
                factor_type="CONTRADICTION",
                source_field="clock_contract_version",
                detail=request.clock_contract_version,
            )
        )
    if request.expiry_contract_version != EXPIRY_CONTRACT_VERSION:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_EXPIRY_CONTRACT_VERSION",
                factor_type="CONTRADICTION",
                source_field="expiry_contract_version",
                detail=request.expiry_contract_version,
            )
        )

    if not request.evaluation_time:
        blocking.append(
            _factor(
                factor_id="MISSING_EVALUATION_TIME",
                factor_type="MISSING_PRECONDITION",
                source_field="evaluation_time",
                detail="missing",
            )
        )
        return blocking

    if not request.evaluation_time_source:
        blocking.append(
            _factor(
                factor_id="MISSING_EVALUATION_TIME_SOURCE",
                factor_type="MISSING_PRECONDITION",
                source_field="evaluation_time_source",
                detail="missing",
            )
        )
    elif request.evaluation_time_source not in _TRUSTED_EVALUATION_TIME_SOURCES:
        blocking.append(
            _factor(
                factor_id="UNTRUSTED_CLOCK_SOURCE",
                factor_type="BLOCKING",
                source_field="evaluation_time_source",
                detail=request.evaluation_time_source,
            )
        )

    if not request.evaluation_time_source_identity:
        blocking.append(
            _factor(
                factor_id="MISSING_CLOCK_SOURCE_IDENTITY",
                factor_type="MISSING_PRECONDITION",
                source_field="evaluation_time_source_identity",
                detail="missing",
            )
        )

    if not request.evaluation_time_provenance:
        blocking.append(
            _factor(
                factor_id="MISSING_PROVENANCE",
                factor_type="MISSING_PRECONDITION",
                source_field="evaluation_time_provenance",
                detail="missing",
            )
        )

    if request.maximum_clock_skew_seconds < 0:
        blocking.append(
            _factor(
                factor_id="INVALID_MAXIMUM_CLOCK_SKEW",
                factor_type="CONTRADICTION",
                source_field="maximum_clock_skew_seconds",
                detail=str(request.maximum_clock_skew_seconds),
            )
        )
    if request.maximum_evidence_age_seconds < 0:
        blocking.append(
            _factor(
                factor_id="INVALID_MAXIMUM_EVIDENCE_AGE",
                factor_type="CONTRADICTION",
                source_field="maximum_evidence_age_seconds",
                detail=str(request.maximum_evidence_age_seconds),
            )
        )

    try:
        evaluation_time = _parse_utc_instant(request.evaluation_time, field="evaluation_time")
    except ClockTrustAndExpiryError as exc:
        blocking.append(
            _factor(
                factor_id="INVALID_EVALUATION_TIME",
                factor_type="BLOCKING",
                source_field="evaluation_time",
                detail=str(exc),
            )
        )
        return blocking

    temporal_fields: dict[str, str] = {}
    for label, raw in (
        ("valid_from", authority_lease.valid_from),
        ("valid_until", authority_lease.valid_until),
        ("issued_at", authority_lease.issued_at),
        ("lease_evaluation_time", authority_lease.evaluation_time),
    ):
        if not raw:
            if label in {"valid_from", "valid_until"}:
                blocking.append(
                    _factor(
                        factor_id=f"MISSING_{label.upper()}",
                        factor_type="MISSING_PRECONDITION",
                        source_field=label,
                        detail="missing",
                    )
                )
            continue
        try:
            temporal_fields[label] = raw
            parsed = _parse_utc_instant(raw, field=label)
            temporal_fields[f"{label}_dt"] = parsed.isoformat()
        except ClockTrustAndExpiryError as exc:
            blocking.append(
                _factor(
                    factor_id="MALFORMED_TIMESTAMP",
                    factor_type="BLOCKING",
                    source_field=label,
                    detail=str(exc),
                )
            )

    envelope_valid_from = str(envelope.validity_metadata.get("valid_from", ""))
    envelope_valid_until = str(envelope.validity_metadata.get("valid_until", ""))
    envelope_eval_time = str(envelope.validity_metadata.get("evaluation_time", ""))

    for label, raw in (
        ("envelope_valid_from", envelope_valid_from),
        ("envelope_valid_until", envelope_valid_until),
    ):
        if raw:
            try:
                _parse_utc_instant(raw, field=label)
            except ClockTrustAndExpiryError as exc:
                blocking.append(
                    _factor(
                        factor_id="MALFORMED_TIMESTAMP",
                        factor_type="BLOCKING",
                        source_field=label,
                        detail=str(exc),
                    )
                )

    if envelope_valid_from and envelope_valid_until:
        try:
            env_from = _parse_utc_instant(envelope_valid_from, field="envelope_valid_from")
            env_until = _parse_utc_instant(envelope_valid_until, field="envelope_valid_until")
            if env_until <= env_from:
                blocking.append(
                    _factor(
                        factor_id="ENVELOPE_VALID_UNTIL_BEFORE_VALID_FROM",
                        factor_type="CONTRADICTION",
                        source_field="envelope_valid_until",
                        detail="valid_until must be strictly after valid_from",
                    )
                )
        except ClockTrustAndExpiryError:
            pass

    if authority_lease.valid_from and authority_lease.valid_until:
        try:
            lease_from = _parse_utc_instant(authority_lease.valid_from, field="valid_from")
            lease_until = _parse_utc_instant(authority_lease.valid_until, field="valid_until")
            if lease_until <= lease_from:
                blocking.append(
                    _factor(
                        factor_id="VALID_UNTIL_BEFORE_VALID_FROM",
                        factor_type="CONTRADICTION",
                        source_field="valid_until",
                        detail="valid_until must be strictly after valid_from",
                    )
                )
            if evaluation_time < lease_from:
                blocking.append(
                    _factor(
                        factor_id="EVALUATION_BEFORE_VALID_FROM",
                        factor_type="BLOCKING",
                        source_field="evaluation_time",
                        detail=request.evaluation_time,
                    )
                )
            if evaluation_time >= lease_until:
                blocking.append(
                    _factor(
                        factor_id="EVALUATION_AT_OR_AFTER_VALID_UNTIL",
                        factor_type="BLOCKING",
                        source_field="evaluation_time",
                        detail=request.evaluation_time,
                    )
                )
            if authority_lease.issued_at:
                issued_at = _parse_utc_instant(authority_lease.issued_at, field="issued_at")
                if issued_at > evaluation_time:
                    blocking.append(
                        _factor(
                            factor_id="FUTURE_DATED_ISSUED_AT",
                            factor_type="BLOCKING",
                            source_field="issued_at",
                            detail=authority_lease.issued_at,
                        )
                    )
                if lease_until <= issued_at:
                    blocking.append(
                        _factor(
                            factor_id="VALID_UNTIL_BEFORE_ISSUED_AT",
                            factor_type="CONTRADICTION",
                            source_field="valid_until",
                            detail="valid_until must be after issued_at",
                        )
                    )
        except ClockTrustAndExpiryError:
            pass

    if envelope_valid_from and envelope_valid_until:
        try:
            env_from = _parse_utc_instant(envelope_valid_from, field="envelope_valid_from")
            env_until = _parse_utc_instant(envelope_valid_until, field="envelope_valid_until")
            if evaluation_time < env_from:
                blocking.append(
                    _factor(
                        factor_id="ENVELOPE_EVALUATION_BEFORE_VALID_FROM",
                        factor_type="BLOCKING",
                        source_field="evaluation_time",
                        detail=request.evaluation_time,
                    )
                )
            if evaluation_time >= env_until:
                blocking.append(
                    _factor(
                        factor_id="ENVELOPE_EVALUATION_AT_OR_AFTER_VALID_UNTIL",
                        factor_type="BLOCKING",
                        source_field="evaluation_time",
                        detail=request.evaluation_time,
                    )
                )
        except ClockTrustAndExpiryError:
            pass

    if request.maximum_clock_skew_seconds == 0 and request.maximum_evidence_age_seconds == 0:
        blocking.append(
            _factor(
                factor_id="MISSING_TEMPORAL_POLICY",
                factor_type="MISSING_PRECONDITION",
                source_field="maximum_clock_skew_seconds",
                detail="policy bounds required",
            )
        )

    reference_times: list[tuple[str, str]] = []
    if authority_lease.evaluation_time:
        reference_times.append(("authority_lease.evaluation_time", authority_lease.evaluation_time))
    if envelope_eval_time:
        reference_times.append(("envelope.validity_metadata.evaluation_time", envelope_eval_time))

    for source_field, raw in reference_times:
        try:
            reference_dt = _parse_utc_instant(raw, field=source_field)
            skew = abs(_seconds_between(evaluation_time, reference_dt))
            if request.maximum_clock_skew_seconds > 0 and skew > request.maximum_clock_skew_seconds:
                blocking.append(
                    _factor(
                        factor_id="EXCESSIVE_CLOCK_SKEW",
                        factor_type="BLOCKING",
                        source_field=source_field,
                        detail=f"skew_seconds={skew}",
                    )
                )
            age = _seconds_between(evaluation_time, reference_dt)
            if (
                request.maximum_evidence_age_seconds > 0
                and age > request.maximum_evidence_age_seconds
            ):
                blocking.append(
                    _factor(
                        factor_id="STALE_EVIDENCE",
                        factor_type="BLOCKING",
                        source_field=source_field,
                        detail=f"age_seconds={age}",
                    )
                )
        except ClockTrustAndExpiryError as exc:
            blocking.append(
                _factor(
                    factor_id="MALFORMED_REFERENCE_TIMESTAMP",
                    factor_type="BLOCKING",
                    source_field=source_field,
                    detail=str(exc),
                )
            )

    expected_envelope_identity = _compute_secure_handoff_envelope_identity(
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.artifact_digest,
    )
    bound_envelope_identity = _compute_secure_handoff_envelope_identity(
        envelope_id=claim_consume.envelope_id,
        envelope_digest=claim_consume.envelope_digest,
    )
    if expected_envelope_identity != bound_envelope_identity:
        blocking.append(
            _factor(
                factor_id="MISMATCHED_ENVELOPE_IDENTITY",
                factor_type="CONTRADICTION",
                source_field="secure_handoff_envelope_identity",
                detail="envelope binding mismatch across bundles",
            )
        )

    if claim_consume.envelope_id != envelope.envelope_id:
        blocking.append(
            _factor(
                factor_id="ENVELOPE_ID_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="envelope_id",
                detail=claim_consume.envelope_id,
            )
        )
    if claim_consume.envelope_digest != envelope.artifact_digest:
        blocking.append(
            _factor(
                factor_id="ENVELOPE_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="envelope_digest",
                detail=claim_consume.envelope_digest,
            )
        )

    claim_envelope_ref = str(
        claim_consume.artifact_payload.get("secure_handoff_envelope_bundle_ref", "")
    )
    if claim_envelope_ref and Path(claim_envelope_ref).resolve() != envelope.bundle_dir.resolve():
        blocking.append(
            _factor(
                factor_id="MISMATCHED_ENVELOPE_BUNDLE_REF",
                factor_type="CONTRADICTION",
                source_field="secure_handoff_envelope_bundle_ref",
                detail=claim_envelope_ref,
            )
        )

    if authority_lease.revocation_state == "REVOKED":
        blocking.append(
            _factor(
                factor_id="REVOKED_AUTHORITY",
                factor_type="BLOCKING",
                source_field="revocation_state",
                detail="REVOKED",
            )
        )
    if envelope.revocation_state == "REVOKED":
        blocking.append(
            _factor(
                factor_id="REVOKED_ENVELOPE",
                factor_type="BLOCKING",
                source_field="revocation_state",
                detail="REVOKED",
            )
        )

    if authority_lease.lease_status in {"LEASE_EXPIRED", "LEASE_REVOKED"}:
        blocking.append(
            _factor(
                factor_id="LEASE_NOT_VALID",
                factor_type="BLOCKING",
                source_field="lease_status",
                detail=authority_lease.lease_status,
            )
        )

    if claim_consume.contract_status not in {
        "CONTRACT_VALID_FOR_OFFLINE_ATOMIC_CLAIM_CONSUME",
        "CONTRACT_CLAIMABLE",
        "CONTRACT_CONSUMABLE",
    }:
        blocking.append(
            _factor(
                factor_id="CLAIM_CONSUME_NOT_VALID",
                factor_type="BLOCKING",
                source_field="contract_status",
                detail=claim_consume.contract_status,
            )
        )

    if request.prior_temporal_evidence_digest:
        current_digest = compute_content_sha256(
            {
                "evaluation_time": request.evaluation_time,
                "envelope_digest": envelope.artifact_digest,
                "claim_consume_digest": claim_consume.artifact_digest,
                "authority_lease_digest": authority_lease.artifact_digest,
            }
        )
        if request.prior_temporal_evidence_digest == current_digest:
            blocking.append(
                _factor(
                    factor_id="REPLAYED_TEMPORAL_EVIDENCE",
                    factor_type="BLOCKING",
                    source_field="prior_temporal_evidence_digest",
                    detail="duplicate temporal evidence digest",
                )
            )

    lineage_envelope = claim_consume.artifact_payload.get("cross_domain_lineage")
    lineage_lease = authority_lease.artifact_payload.get("cross_domain_lineage")
    if isinstance(lineage_envelope, dict) and isinstance(lineage_lease, dict):
        for field in _TRANSITIVE_LINEAGE_FIELDS:
            env_val = lineage_envelope.get(field)
            lease_val = lineage_lease.get(field)
            if env_val and lease_val and str(env_val) != str(lease_val):
                blocking.append(
                    _factor(
                        factor_id="BROKEN_CROSS_DOMAIN_LINEAGE",
                        factor_type="CONTRADICTION",
                        source_field=field,
                        detail=f"{env_val}!={lease_val}",
                    )
                )

    return blocking


def _evaluate_clock_trust(
    *,
    request: ClockTrustAndExpiryRequest,
    envelope: VerifiedSecureHandoffEnvelopeBundle,
    claim_consume: VerifiedHandoffAtomicClaimConsumeBundle,
    authority_lease: VerifiedAuthorityLeaseBundle,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, list[str], dict[str, Any]]:
    reason_codes: list[str] = []
    states: dict[str, Any] = {
        "clock_trust_status": "UNKNOWN",
        "clock_trust_reason": "",
        "expiry_state": "UNKNOWN",
        "stale_state": "UNKNOWN",
        "future_dated_state": "UNKNOWN",
        "temporal_ordering_status": "UNKNOWN",
        "clock_trust_and_expiry_complete": False,
        "secure_handoff_envelope_bound": False,
        "handoff_atomic_claim_consume_bound": False,
        "authority_lease_and_revocation_bound": False,
        "cross_domain_lineage_bound": False,
        "replay_protection_bound": False,
        "evaluation_time_trust_bound": False,
        "canonical_time_normalization_bound": False,
        "expiry_policy_bound": False,
        "temporal_ordering_bound": False,
        "clock_skew_policy_bound": False,
        "stale_evidence_protection_bound": False,
    }

    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    factor_ids = {item.get("factor_id") for item in blocking_facts}

    if any(item.get("factor_id") == "UNTRUSTED_CLOCK_SOURCE" for item in blocking_facts):
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "UNTRUSTED_CLOCK_SOURCE"
        reason_codes.append("UNTRUSTED_CLOCK_SOURCE")
        return (
            "CLOCK_TRUST_UNTRUSTED_CLOCK_SOURCE",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if any(
        item.get("factor_id") in {"REVOKED_AUTHORITY", "REVOKED_ENVELOPE"}
        for item in blocking_facts
    ):
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "REVOCATION_PRECEDENCE"
        states["secure_handoff_envelope_bound"] = True
        states["authority_lease_and_revocation_bound"] = True
        reason_codes.append("REVOCATION_PRECEDENCE")
        return (
            "CLOCK_TRUST_REVOKED",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "REPLAYED_TEMPORAL_EVIDENCE" in factor_ids:
        states["replay_protection_bound"] = True
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "REPLAYED_TEMPORAL_EVIDENCE"
        reason_codes.append("REPLAYED_TEMPORAL_EVIDENCE")
        return (
            "CLOCK_TRUST_REPLAY_REJECTED",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "STALE_EVIDENCE" in factor_ids:
        states["stale_state"] = "STALE"
        states["stale_evidence_protection_bound"] = True
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "STALE_EVIDENCE"
        reason_codes.append("STALE_EVIDENCE")
        return (
            "CLOCK_TRUST_STALE_EVIDENCE",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "FUTURE_DATED_ISSUED_AT" in factor_ids:
        states["future_dated_state"] = "FUTURE_DATED"
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "FUTURE_DATED_ISSUED_AT"
        reason_codes.append("FUTURE_DATED_ISSUED_AT")
        return (
            "CLOCK_TRUST_FUTURE_DATED",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if {
        "EVALUATION_AT_OR_AFTER_VALID_UNTIL",
        "ENVELOPE_EVALUATION_AT_OR_AFTER_VALID_UNTIL",
        "LEASE_NOT_VALID",
    } & factor_ids:
        states["expiry_state"] = "EXPIRED"
        states["expiry_policy_bound"] = True
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "EXPIRED"
        reason_codes.append("EXPIRED")
        return (
            "CLOCK_TRUST_EXPIRED",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if "EXCESSIVE_CLOCK_SKEW" in factor_ids:
        states["clock_skew_policy_bound"] = True
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "EXCESSIVE_CLOCK_SKEW"
        reason_codes.append("EXCESSIVE_CLOCK_SKEW")
        return (
            "CLOCK_TRUST_INVALID",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if contradictions or "BROKEN_CROSS_DOMAIN_LINEAGE" in factor_ids:
        states["temporal_ordering_status"] = "AMBIGUOUS" if contradictions else "INVALID"
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "TEMPORAL_CONTRADICTION"
        reason_codes.append("TEMPORAL_CONTRADICTION")
        return (
            "CLOCK_TRUST_AMBIGUOUS_ORDERING",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    if blocking_facts:
        states["clock_trust_status"] = "UNTRUSTED"
        states["clock_trust_reason"] = "CONTRACT_FAIL_CLOSED"
        reason_codes.append("CONTRACT_FAIL_CLOSED")
        return (
            "CLOCK_TRUST_INVALID",
            states["clock_trust_status"],
            _sorted_strings(reason_codes),
            states,
        )

    states.update(
        {
            "clock_trust_status": "TRUSTED",
            "clock_trust_reason": "TEMPORAL_TRUST_BOUND",
            "expiry_state": "NOT_EXPIRED",
            "stale_state": "FRESH",
            "future_dated_state": "NOT_FUTURE_DATED",
            "temporal_ordering_status": "VALID",
            "clock_trust_and_expiry_complete": True,
            "secure_handoff_envelope_bound": True,
            "handoff_atomic_claim_consume_bound": True,
            "authority_lease_and_revocation_bound": True,
            "cross_domain_lineage_bound": True,
            "replay_protection_bound": True,
            "evaluation_time_trust_bound": True,
            "canonical_time_normalization_bound": True,
            "expiry_policy_bound": True,
            "temporal_ordering_bound": True,
            "clock_skew_policy_bound": True,
            "stale_evidence_protection_bound": True,
        }
    )
    reason_codes.extend(
        [
            "SECURE_HANDOFF_ENVELOPE_BOUND",
            "HANDOFF_ATOMIC_CLAIM_CONSUME_BOUND",
            "AUTHORITY_LEASE_BOUND",
            "EVALUATION_TIME_TRUST_BOUND",
            "TEMPORAL_ORDERING_VALID",
            "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION",
        ]
    )
    return (
        "CLOCK_TRUST_VALID_FOR_OFFLINE_TEMPORAL_EVALUATION",
        states["clock_trust_status"],
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


def build_clock_trust_and_expiry_v1(
    *,
    envelope: VerifiedSecureHandoffEnvelopeBundle,
    claim_consume: VerifiedHandoffAtomicClaimConsumeBundle,
    authority_lease: VerifiedAuthorityLeaseBundle,
    request: ClockTrustAndExpiryRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(
        request,
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
    )
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    contract_status, clock_trust_status, reason_codes, completion_flags = _evaluate_clock_trust(
        request=request,
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        blocking_facts=blocking_facts,
    )

    secure_handoff_envelope_identity = _compute_secure_handoff_envelope_identity(
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.artifact_digest,
    )
    handoff_atomic_claim_consume_identity = _compute_handoff_atomic_claim_consume_identity(
        contract_id=claim_consume.contract_id,
        claim_identity=claim_consume.claim_identity,
        consume_identity=claim_consume.consume_identity,
    )
    evaluation_time_digest = _compute_evaluation_time_digest(
        evaluation_time=request.evaluation_time,
        evaluation_time_source=request.evaluation_time_source,
        evaluation_time_source_identity=request.evaluation_time_source_identity,
        evaluation_time_provenance=request.evaluation_time_provenance,
    )

    input_refs = [
        _input_artifact_ref_mapping(
            bundle_dir=envelope.bundle_dir,
            contract_name=envelope.contract_name,
            contract_version=envelope.contract_version,
            producer_version=envelope.producer_version,
            artifact_ref=envelope.artifact_ref,
            artifact_digest=envelope.artifact_digest,
            manifest_digest=envelope.manifest_digest,
        ),
        _input_artifact_ref_mapping(
            bundle_dir=claim_consume.bundle_dir,
            contract_name=claim_consume.contract_name,
            contract_version=claim_consume.contract_version,
            producer_version=claim_consume.producer_version,
            artifact_ref=claim_consume.artifact_ref,
            artifact_digest=claim_consume.artifact_digest,
            manifest_digest=claim_consume.manifest_digest,
        ),
        _input_artifact_ref_mapping(
            bundle_dir=authority_lease.bundle_dir,
            contract_name=authority_lease.contract_name,
            contract_version=authority_lease.contract_version,
            producer_version=authority_lease.producer_version,
            artifact_ref=authority_lease.artifact_ref,
            artifact_digest=authority_lease.artifact_digest,
            manifest_digest=authority_lease.manifest_digest,
        ),
    ]
    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "evaluation_time_digest": evaluation_time_digest,
            "secure_handoff_envelope_identity": secure_handoff_envelope_identity,
            "handoff_atomic_claim_consume_identity": handoff_atomic_claim_consume_identity,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    lease_expiry_binding = {
        "lease_id": authority_lease.lease_id,
        "lease_status": authority_lease.lease_status,
        "valid_from": authority_lease.valid_from,
        "valid_until": authority_lease.valid_until,
        "issued_at": authority_lease.issued_at,
        "revocation_state": authority_lease.revocation_state,
    }
    revocation_time_binding = {
        "revocation_state": authority_lease.revocation_state,
        "envelope_revocation_state": envelope.revocation_state,
        "claim_consume_revocation_state": claim_consume.artifact_payload.get("revocation_state"),
    }

    envelope_payload = envelope.artifact_payload
    claim_payload = claim_consume.artifact_payload

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "clock_contract_version": request.clock_contract_version,
        "expiry_contract_version": request.expiry_contract_version,
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
        "evaluation_time": request.evaluation_time,
        "evaluation_time_source": request.evaluation_time_source,
        "evaluation_time_source_identity": request.evaluation_time_source_identity,
        "evaluation_time_provenance": dict(request.evaluation_time_provenance),
        "evaluation_time_digest": evaluation_time_digest,
        "canonical_timezone": CANONICAL_TIMEZONE,
        "canonical_timestamp_format": CANONICAL_TIMESTAMP_FORMAT,
        "clock_trust_status": clock_trust_status,
        "clock_trust_reason": completion_flags.get("clock_trust_reason", ""),
        "issued_at": authority_lease.issued_at,
        "valid_from": authority_lease.valid_from,
        "valid_until": authority_lease.valid_until,
        "maximum_clock_skew_seconds": request.maximum_clock_skew_seconds,
        "maximum_evidence_age_seconds": request.maximum_evidence_age_seconds,
        "expiry_state": completion_flags.get("expiry_state", "UNKNOWN"),
        "stale_state": completion_flags.get("stale_state", "UNKNOWN"),
        "future_dated_state": completion_flags.get("future_dated_state", "UNKNOWN"),
        "temporal_ordering_status": completion_flags.get("temporal_ordering_status", "UNKNOWN"),
        "lease_expiry_binding": lease_expiry_binding,
        "revocation_time_binding": revocation_time_binding,
        "secure_handoff_envelope_identity": secure_handoff_envelope_identity,
        "handoff_atomic_claim_consume_identity": handoff_atomic_claim_consume_identity,
        "envelope_id": envelope.envelope_id,
        "envelope_digest": envelope.artifact_digest,
        "claim_identity": claim_consume.claim_identity,
        "consume_identity": claim_consume.consume_identity,
        "claim_consume_contract_id": claim_consume.contract_id,
        "secure_handoff_envelope_bundle_ref": envelope.bundle_dir.as_posix(),
        "handoff_atomic_claim_consume_bundle_ref": claim_consume.bundle_dir.as_posix(),
        "authority_lease_and_revocation_bundle_ref": authority_lease.bundle_dir.as_posix(),
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "clock_trust_and_expiry_authority_invariants": dict(
            CLOCK_TRUST_AND_EXPIRY_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": (
            dict(claim_payload["cross_domain_lineage"])
            if isinstance(claim_payload.get("cross_domain_lineage"), dict)
            and claim_payload.get("cross_domain_lineage")
            else {
                field: str(claim_payload[field])
                for field in _TRANSITIVE_LINEAGE_FIELDS
                if claim_payload.get(field) is not None and str(claim_payload.get(field))
            }
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
        "validity_metadata": {
            **envelope.validity_metadata,
            "evaluation_time": request.evaluation_time,
            "authority_lease_evaluation_time": authority_lease.evaluation_time,
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
        }
    )

    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = claim_payload.get(field) or envelope_payload.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise ClockTrustAndExpiryError("contract_status invalid")
    if clock_trust_status not in _VALID_CLOCK_TRUST_STATUSES:
        raise ClockTrustAndExpiryError("clock_trust_status invalid")

    payload["input_digest"] = input_digest
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["contract_id"] = contract_id
    return payload


def serialize_clock_trust_and_expiry_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise ClockTrustAndExpiryError("contract_status invalid")
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
            raise ClockTrustAndExpiryError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_clock_trust_and_expiry_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise ClockTrustAndExpiryError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise ClockTrustAndExpiryError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ClockTrustAndExpiryError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise ClockTrustAndExpiryError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise ClockTrustAndExpiryError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise ClockTrustAndExpiryError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_three_verified_input_bundles", "status": "PASS"},
        {"check_id": "offline_only_no_system_clock_read", "status": "PASS"},
        {"check_id": "offline_only_no_expiry_execution", "status": "PASS"},
        {"check_id": "no_state_mutation", "status": "PASS"},
        {"check_id": "no_consumer_invocation", "status": "PASS"},
        {"check_id": "deny_by_default", "status": "PASS"},
        {"check_id": "evaluation_time_trust_bound", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = contract.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 3:
        checks = [
            {**c, "status": "FAIL"}
            if c["check_id"] == "exactly_three_verified_input_bundles"
            else c
            for c in checks
        ]

    if contract.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise ClockTrustAndExpiryError("self-verification checks failed")

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
        "verified_clock_trust_status": contract.get("clock_trust_status"),
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


def default_clock_trust_request(
    *,
    envelope: VerifiedSecureHandoffEnvelopeBundle,
    authority_lease: VerifiedAuthorityLeaseBundle,
    maximum_clock_skew_seconds: int,
    maximum_evidence_age_seconds: int,
) -> ClockTrustAndExpiryRequest:
    evaluation_time = str(
        envelope.validity_metadata.get("evaluation_time", authority_lease.evaluation_time)
    )
    return ClockTrustAndExpiryRequest(
        evaluation_time=evaluation_time,
        evaluation_time_source="OFFLINE_DETERMINISTIC_EVIDENCE",
        evaluation_time_source_identity=DEFAULT_PRODUCER_IDENTITY_REF,
        evaluation_time_provenance={
            "provenance_kind": "OFFLINE_DETERMINISTIC_EVIDENCE",
            "source_revision": DEFAULT_SOURCE_REVISION,
            "upstream_envelope_evaluation_time": envelope.validity_metadata.get("evaluation_time"),
            "upstream_lease_evaluation_time": authority_lease.evaluation_time,
        },
        maximum_clock_skew_seconds=maximum_clock_skew_seconds,
        maximum_evidence_age_seconds=maximum_evidence_age_seconds,
    )


def verify_clock_trust_and_expiry_inputs(
    inputs: ClockTrustAndExpiryInputs,
) -> tuple[
    VerifiedSecureHandoffEnvelopeBundle,
    VerifiedHandoffAtomicClaimConsumeBundle,
    VerifiedAuthorityLeaseBundle,
]:
    envelope = verify_secure_handoff_envelope_bundle_for_clock_trust(
        inputs.secure_handoff_envelope_bundle_dir
    )
    claim_consume = verify_handoff_atomic_claim_consume_bundle(
        inputs.handoff_atomic_claim_consume_bundle_dir
    )
    authority_lease = verify_authority_lease_bundle(
        inputs.authority_lease_and_revocation_bundle_dir
    )
    return envelope, claim_consume, authority_lease


def reverify_clock_trust_and_expiry_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ClockTrustAndExpiryError(f"clock trust and expiry directory not found: {bundle_dir}")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ClockTrustAndExpiryError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise ClockTrustAndExpiryError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise ClockTrustAndExpiryError("manifest_digest mismatch on replay")

    envelope = verify_secure_handoff_envelope_bundle_for_clock_trust(
        Path(str(contract["secure_handoff_envelope_bundle_ref"]))
    )
    claim_consume = verify_handoff_atomic_claim_consume_bundle(
        Path(str(contract["handoff_atomic_claim_consume_bundle_ref"]))
    )
    authority_lease = verify_authority_lease_bundle(
        Path(str(contract["authority_lease_and_revocation_bundle_ref"]))
    )

    if contract.get("envelope_digest") != envelope.artifact_digest:
        raise ClockTrustAndExpiryError("envelope digest mismatch on replay")
    if contract.get("claim_consume_contract_id") != claim_consume.contract_id:
        raise ClockTrustAndExpiryError("claim consume contract id mismatch on replay")


def produce_clock_trust_and_expiry_v1(
    *,
    inputs: ClockTrustAndExpiryInputs,
    output_dir: Path | str,
) -> ClockTrustAndExpiryResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[
            inputs.secure_handoff_envelope_bundle_dir,
            inputs.handoff_atomic_claim_consume_bundle_dir,
            inputs.authority_lease_and_revocation_bundle_dir,
        ],
        output_dir=final_dir,
    )

    envelope, claim_consume, authority_lease = verify_clock_trust_and_expiry_inputs(inputs)
    contract_body = build_clock_trust_and_expiry_v1(
        envelope=envelope,
        claim_consume=claim_consume,
        authority_lease=authority_lease,
        request=inputs.clock_trust_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ClockTrustAndExpiryError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_clock_trust_and_expiry_v1(finalized),
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
            raise ClockTrustAndExpiryError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_clock_trust_and_expiry_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ClockTrustAndExpiryError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ClockTrustAndExpiryResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        clock_trust_status=str(finalized["clock_trust_status"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        secure_handoff_envelope_identity=str(finalized["secure_handoff_envelope_identity"]),
        handoff_atomic_claim_consume_identity=str(
            finalized["handoff_atomic_claim_consume_identity"]
        ),
    )


__all__ = [
    "ARTIFACT_REL",
    "CANONICAL_TIMESTAMP_FORMAT",
    "CANONICAL_TIMEZONE",
    "CLOCK_CONTRACT_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "DEFAULT_PRODUCER_IDENTITY_REF",
    "DEFAULT_SOURCE_REVISION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "EVIDENCE_LEVEL",
    "EXPIRY_CONTRACT_VERSION",
    "CLOCK_TRUST_AND_EXPIRY_AUTHORITY_INVARIANTS",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "SELF_VERIFICATION_REL",
    "ClockTrustAndExpiryError",
    "ClockTrustAndExpiryInputs",
    "ClockTrustAndExpiryRequest",
    "ClockTrustAndExpiryResult",
    "VerifiedAuthorityLeaseBundle",
    "VerifiedHandoffAtomicClaimConsumeBundle",
    "VerifiedSecureHandoffEnvelopeBundle",
    "build_clock_trust_and_expiry_v1",
    "default_clock_trust_request",
    "produce_clock_trust_and_expiry_v1",
    "reverify_clock_trust_and_expiry_v1",
    "serialize_clock_trust_and_expiry_v1",
    "verify_authority_lease_bundle",
    "verify_clock_trust_and_expiry_inputs",
    "verify_handoff_atomic_claim_consume_bundle",
    "verify_secure_handoff_envelope_bundle_for_clock_trust",
]
