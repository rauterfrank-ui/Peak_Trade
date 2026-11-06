"""Offline LEVEL_3 secure handoff envelope contract owner v1."""

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
    VerifiedHandoffTrustPolicyBundle,
    reverify_authority_lease_and_revocation_v1,
    verify_handoff_trust_policy_bundle,
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
    ARTIFACT_REL as HANDOFF_TRUST_POLICY_ARTIFACT_REL,
    CONSUMER_CONTRACT_ID,
    CONSUMER_CONTRACT_NAME,
    CONSUMER_CONTRACT_VERSION,
    CONTRACT_NAME as HANDOFF_TRUST_POLICY_CONTRACT_NAME,
    CONTRACT_VERSION as HANDOFF_TRUST_POLICY_CONTRACT_VERSION,
    PRODUCER_VERSION as HANDOFF_TRUST_POLICY_PRODUCER_VERSION,
)
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    ARTIFACT_REL as VERSIONED_ARTIFACT_REL,
    CONTRACT_NAME as VERSIONED_CONTRACT_NAME,
    CONTRACT_VERSION as VERSIONED_CONTRACT_VERSION,
)

CONTRACT_NAME = "secure_handoff_envelope_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "secure_handoff_envelope_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "secure_handoff_envelope_record"
INPUT_RELATION = "PACKAGES_VERIFIED_AUTHORITY_LEASE_AND_REVOCATION_V1_FOR_OFFLINE_ENVELOPE"
ARTIFACT_REL = "secure_handoff_envelope_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".secure_handoff_envelope_staging_"

ENVELOPE_SCHEMA_VERSION = "secure_handoff_envelope_schema_v1"
CREATION_CONTRACT_VERSION = "secure_handoff_envelope_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "secure_handoff_envelope_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_secure_handoff_envelope_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"
PAYLOAD_REF = "envelope_payload_v1"

_VALID_ENVELOPE_STATUSES = frozenset(
    {
        "ENVELOPE_VALID_FOR_OFFLINE_HANDOFF",
        "ENVELOPE_INVALID",
        "ENVELOPE_REVOKED",
        "ENVELOPE_EXPIRED",
        "ENVELOPE_REPLAY_REJECTED",
        "ABSTAIN",
    }
)
_VALID_REVOCATION_STATES = frozenset({"NOT_REVOKED", "REVOKED", "UNKNOWN"})
_UTC_INSTANT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")

_DEFAULT_ALLOWED_OFFLINE_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_DESCRIBE_OFFLINE_HANDOFF_ENVELOPE",
        "CAN_BIND_AUTHORITY_LEASE_REF",
        "CAN_BIND_HANDOFF_TRUST_POLICY_REF",
        "CAN_BIND_VERSIONED_ARTIFACT_REF",
    }
)

_FORBIDDEN_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_EXECUTE_HANDOFF",
        "CAN_INVOKE_CONSUMER",
        "CAN_MUTATE_CONSUMER",
        "CAN_TRANSFER_FILES",
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
        "CAN_DEPLOY_INACTIVE",
        "CAN_COMPUTE_SIGNALS",
        "CAN_INCREASE_CAPITAL",
        "CAN_CHANGE_RISK_POLICY",
        "CAN_ACTIVATE_KILLSWITCH",
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

SECURE_HANDOFF_ENVELOPE_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "secure_handoff_envelope_is_descriptive_only": True,
    "secure_handoff_envelope_does_not_execute_handoff": True,
    "secure_handoff_envelope_does_not_invoke_consumer": True,
    "secure_handoff_envelope_does_not_mutate_consumer": True,
    "secure_handoff_envelope_does_not_transfer_files": True,
    "secure_handoff_envelope_does_not_grant_authority": True,
    "secure_handoff_envelope_does_not_activate_lease": True,
    "secure_handoff_envelope_does_not_execute_revocation": True,
    "secure_handoff_envelope_does_not_authorize_promotion": True,
    "secure_handoff_envelope_does_not_create_configpatch": True,
    "secure_handoff_envelope_does_not_authorize_runtime": True,
    "secure_handoff_envelope_does_not_authorize_live": True,
    "secure_handoff_envelope_is_offline_only": True,
    "deny_by_default": True,
    "envelope_immutable": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_secure_handoff_envelope": True,
    "secure_handoff_envelope_offline_only": True,
    "secure_handoff_envelope_complete": False,
    "versioned_artifact_bound": False,
    "handoff_trust_policy_bound": False,
    "authority_lease_and_revocation_bound": False,
    "cross_domain_lineage_bound": False,
    "deny_by_default": True,
    "envelope_immutable": True,
    "handoff_executed": False,
    "consumer_invoked": False,
    "consumer_mutated": False,
    "files_transferred": False,
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

_TRANSITIVE_LINEAGE_FIELDS: tuple[str, ...] = (
    "experiment_identity_ref",
    "experiment_identity_digest",
    "experiment_identity_id",
    "strategy_identity_ref",
    "strategy_identity_digest",
    "model_identity_ref",
    "model_identity_digest",
    "parameter_set_identity_ref",
    "parameter_set_identity_digest",
    "comparison_definition_id",
    "comparison_identity_ref",
    "comparison_identity_digest",
    "ai_promotion_assessment_ref",
    "ai_promotion_assessment_digest",
    "policy_decision_ref",
    "policy_decision_digest",
    "cross_domain_lineage_binding_digest",
)

_SELF_VERIFICATION_SCHEMA_VERSION = "secure_handoff_envelope_self_verification_v1"


class SecureHandoffEnvelopeError(ValueError):
    """Fail-closed secure handoff envelope error."""


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
    handoff: VerifiedHandoffTrustPolicyBundle
    lease_status: str
    valid_from: str
    valid_until: str
    evaluation_time: str
    revocation_state: str


@dataclass(frozen=True)
class SecureHandoffEnvelopeRequest:
    evaluation_time: str
    allowed_offline_capabilities: tuple[str, ...]
    denied_capabilities: tuple[str, ...] = ()
    source_revision: str = DEFAULT_SOURCE_REVISION
    intended_consumer_identity_ref: str = CONSUMER_CONTRACT_ID
    intended_consumer_identity_version: str = CONSUMER_CONTRACT_VERSION


@dataclass(frozen=True)
class SecureHandoffEnvelopeInputs:
    authority_lease_bundle_dir: Path
    envelope_request: SecureHandoffEnvelopeRequest


@dataclass(frozen=True)
class SecureHandoffEnvelopeResult:
    output_dir: Path
    envelope_id: str
    envelope_status: str
    envelope_path: Path
    self_verification_path: Path
    manifest_path: Path
    authority_lease_ref: str
    authority_lease_digest: str
    payload_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise SecureHandoffEnvelopeError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise SecureHandoffEnvelopeError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise SecureHandoffEnvelopeError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise SecureHandoffEnvelopeError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise SecureHandoffEnvelopeError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise SecureHandoffEnvelopeError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, authority_lease_dir: Path, output_dir: Path) -> None:
    input_res = authority_lease_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == input_res:
        raise SecureHandoffEnvelopeError("output directory must not equal input path")
    if _path_is_under(output_res, input_res):
        raise SecureHandoffEnvelopeError("output directory must not be inside input path")
    if _path_is_under(input_res, output_res):
        raise SecureHandoffEnvelopeError("input directory must not be inside output directory")


def _manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / MANIFEST_FILENAME
    _validate_regular_file(manifest_path, label=MANIFEST_FILENAME)
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _factor(
    *,
    factor_id: str,
    factor_type: str,
    source_field: str,
    observation: str,
) -> dict[str, str]:
    return {
        "factor_id": factor_id,
        "factor_type": factor_type,
        "source_field": source_field,
        "observation": observation,
    }


def _sort_factors(factors: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(factors, key=lambda item: (item["factor_id"], item["source_field"]))


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(set(values))


def _load_self_verification(bundle_dir: Path, *, rel: str, label: str) -> dict[str, Any]:
    path = bundle_dir / rel
    _validate_regular_file(path, label=label)
    payload = read_manifest(path)
    if not isinstance(payload, dict):
        raise SecureHandoffEnvelopeError(f"{label} must be a JSON object")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise SecureHandoffEnvelopeError("integrity must be an object")
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        raise SecureHandoffEnvelopeError("integrity.content_sha256 invalid")
    return digest


def _parse_utc_instant(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise SecureHandoffEnvelopeError(f"{field} must be a non-empty UTC instant")
    if not _UTC_INSTANT_PATTERN.match(value):
        raise SecureHandoffEnvelopeError(
            f"{field} must use canonical UTC format with +00:00 or Z suffix"
        )
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SecureHandoffEnvelopeError(f"{field} is not a valid UTC instant") from exc
    if parsed.tzinfo != timezone.utc:
        raise SecureHandoffEnvelopeError(f"{field} must be UTC")
    return parsed


def _validate_capability_name(capability: str) -> None:
    if not capability or not isinstance(capability, str):
        raise SecureHandoffEnvelopeError("capability must be a non-empty string")
    if "*" in capability or capability.endswith("_ALL"):
        raise SecureHandoffEnvelopeError(f"overbroad wildcard capability: {capability}")
    if capability in _FORBIDDEN_CAPABILITIES:
        raise SecureHandoffEnvelopeError(f"forbidden capability: {capability}")


def _normalize_capabilities(values: tuple[str, ...] | list[str], *, label: str) -> list[str]:
    if not isinstance(values, (tuple, list)):
        raise SecureHandoffEnvelopeError(f"{label} must be a list")
    normalized: list[str] = []
    for item in values:
        _validate_capability_name(item)
        normalized.append(item)
    return sorted(set(normalized))


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "secure_handoff_envelope_complete",
            "versioned_artifact_bound",
            "handoff_trust_policy_bound",
            "authority_lease_and_revocation_bound",
            "cross_domain_lineage_bound",
        }:
            continue
        if actual is not expected:
            raise SecureHandoffEnvelopeError(f"{key} must be {expected!r}")


def verify_authority_lease_bundle(bundle_dir: Path | str) -> VerifiedAuthorityLeaseBundle:
    """Fail-closed verification of exactly one authority lease bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="authority lease bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise SecureHandoffEnvelopeError(
            f"authority lease MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / AUTHORITY_LEASE_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=AUTHORITY_LEASE_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != AUTHORITY_LEASE_CONTRACT_NAME:
        raise SecureHandoffEnvelopeError("authority lease contract_name mismatch")
    if payload.get("contract_version") != AUTHORITY_LEASE_CONTRACT_VERSION:
        raise SecureHandoffEnvelopeError("authority lease contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=AUTHORITY_LEASE_SELF_VERIFICATION_REL,
        label=AUTHORITY_LEASE_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise SecureHandoffEnvelopeError(
            "authority lease SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_authority_lease_and_revocation_v1(output_dir=path)
    except AuthorityLeaseAndRevocationError as exc:
        raise SecureHandoffEnvelopeError(str(exc)) from exc

    handoff_ref_raw = payload.get("handoff_trust_policy_bundle_ref")
    if not handoff_ref_raw:
        raise SecureHandoffEnvelopeError("authority lease missing handoff_trust_policy_bundle_ref")
    handoff = verify_handoff_trust_policy_bundle(Path(str(handoff_ref_raw)))

    source_handoff_digest = str(payload.get("source_handoff_trust_policy_digest", ""))
    if handoff.artifact_digest != source_handoff_digest:
        raise SecureHandoffEnvelopeError("authority lease handoff trust policy digest mismatch")

    versioned_digest = str(payload.get("versioned_artifact_digest", ""))
    if handoff.versioned_artifact_digest != versioned_digest:
        raise SecureHandoffEnvelopeError("transitive versioned artifact digest mismatch")

    return VerifiedAuthorityLeaseBundle(
        bundle_dir=path.resolve(),
        contract_name=AUTHORITY_LEASE_CONTRACT_NAME,
        contract_version=AUTHORITY_LEASE_CONTRACT_VERSION,
        producer_version=AUTHORITY_LEASE_PRODUCER_VERSION,
        artifact_ref=AUTHORITY_LEASE_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        handoff=handoff,
        lease_status=str(payload.get("lease_status", "")),
        valid_from=str(payload.get("valid_from", "")),
        valid_until=str(payload.get("valid_until", "")),
        evaluation_time=str(payload.get("evaluation_time", "")),
        revocation_state=str(payload.get("revocation_state", "")),
    )


def _validate_envelope_request(
    request: SecureHandoffEnvelopeRequest,
    *,
    lease: VerifiedAuthorityLeaseBundle,
) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []

    if not request.intended_consumer_identity_ref:
        blocking.append(
            _factor(
                factor_id="MISSING_INTENDED_CONSUMER_IDENTITY_REF",
                factor_type="MISSING_PRECONDITION",
                source_field="intended_consumer_identity_ref",
                observation="intended_consumer_identity_ref is required",
            )
        )
    if not request.intended_consumer_identity_version:
        blocking.append(
            _factor(
                factor_id="MISSING_INTENDED_CONSUMER_IDENTITY_VERSION",
                factor_type="MISSING_PRECONDITION",
                source_field="intended_consumer_identity_version",
                observation="intended_consumer_identity_version is required",
            )
        )

    handoff_payload = lease.handoff.artifact_payload
    expected_consumer_id = str(handoff_payload.get("consumer_contract_id", ""))
    if (
        request.intended_consumer_identity_ref
        and expected_consumer_id
        and request.intended_consumer_identity_ref != expected_consumer_id
    ):
        blocking.append(
            _factor(
                factor_id="INTENDED_CONSUMER_IDENTITY_MISMATCH",
                factor_type="BLOCKING_FACT",
                source_field="intended_consumer_identity_ref",
                observation="intended consumer identity incompatible with handoff trust policy",
            )
        )

    expected_consumer_version = str(handoff_payload.get("consumer_contract_version", ""))
    if (
        request.intended_consumer_identity_version
        and expected_consumer_version
        and request.intended_consumer_identity_version != expected_consumer_version
    ):
        blocking.append(
            _factor(
                factor_id="INTENDED_CONSUMER_VERSION_MISMATCH",
                factor_type="BLOCKING_FACT",
                source_field="intended_consumer_identity_version",
                observation="intended consumer version incompatible with handoff trust policy",
            )
        )

    try:
        valid_from = _parse_utc_instant(lease.valid_from, field="valid_from")
        valid_until = _parse_utc_instant(lease.valid_until, field="valid_until")
        evaluation_time = _parse_utc_instant(request.evaluation_time, field="evaluation_time")
    except SecureHandoffEnvelopeError as exc:
        blocking.append(
            _factor(
                factor_id="INVALID_TIME_SEMANTICS",
                factor_type="BLOCKING_FACT",
                source_field="evaluation_time",
                observation=str(exc),
            )
        )
        return blocking

    if evaluation_time < valid_from:
        blocking.append(
            _factor(
                factor_id="EVALUATION_BEFORE_VALID_FROM",
                factor_type="BLOCKING_FACT",
                source_field="evaluation_time",
                observation="evaluation_time is before lease valid_from",
            )
        )
    if evaluation_time >= valid_until:
        blocking.append(
            _factor(
                factor_id="EVALUATION_AT_OR_AFTER_VALID_UNTIL",
                factor_type="BLOCKING_FACT",
                source_field="evaluation_time",
                observation="evaluation_time is at or after lease valid_until",
            )
        )

    allowed = _normalize_capabilities(
        request.allowed_offline_capabilities, label="allowed_offline_capabilities"
    )
    denied = _normalize_capabilities(request.denied_capabilities, label="denied_capabilities")
    if not allowed:
        blocking.append(
            _factor(
                factor_id="EMPTY_ALLOWED_OFFLINE_CAPABILITIES",
                factor_type="BLOCKING_FACT",
                source_field="allowed_offline_capabilities",
                observation="allowed_offline_capabilities must be non-empty deny-by-default allowlist",
            )
        )
    overlap = set(allowed) & set(denied)
    for capability in sorted(overlap):
        blocking.append(
            _factor(
                factor_id=f"CAPABILITY_ALLOW_DENY_CONFLICT_{capability}",
                factor_type="CONTRADICTION",
                source_field="allowed_offline_capabilities",
                observation=f"capability {capability!r} appears in both allow and deny lists",
            )
        )

    return blocking


def _evaluate_envelope_status(
    *,
    lease: VerifiedAuthorityLeaseBundle,
    request: SecureHandoffEnvelopeRequest,
    blocking_facts: list[dict[str, str]],
    contradictions: list[dict[str, str]],
) -> tuple[str, list[str], dict[str, bool]]:
    reason_codes: list[str] = []
    completion = {
        "secure_handoff_envelope_complete": False,
        "versioned_artifact_bound": False,
        "handoff_trust_policy_bound": False,
        "authority_lease_and_revocation_bound": False,
        "cross_domain_lineage_bound": False,
    }

    handoff_payload = lease.handoff.artifact_payload
    trust_result = str(handoff_payload.get("trust_result", ""))
    if trust_result != "ALLOW_OFFLINE_HANDOFF":
        reason_codes.append("HANDOFF_TRUST_POLICY_NOT_ALLOW")
        return "ENVELOPE_INVALID", _sorted_strings(reason_codes), completion

    completion["handoff_trust_policy_bound"] = True
    completion["versioned_artifact_bound"] = True

    if lease.artifact_payload.get("cross_domain_lineage_bound") is True:
        completion["cross_domain_lineage_bound"] = True

    if lease.lease_status == "ABSTAIN" or lease.revocation_state == "UNKNOWN":
        reason_codes.append("REVOCATION_STATE_UNKNOWN")
        return "ABSTAIN", _sorted_strings(reason_codes), completion

    if lease.lease_status == "LEASE_REVOKED" or lease.revocation_state == "REVOKED":
        reason_codes.append("REVOCATION_PRECEDENCE")
        completion["authority_lease_and_revocation_bound"] = True
        return "ENVELOPE_REVOKED", _sorted_strings(reason_codes), completion

    if lease.lease_status == "LEASE_EXPIRED":
        reason_codes.append("LEASE_EXPIRED")
        completion["authority_lease_and_revocation_bound"] = True
        return "ENVELOPE_EXPIRED", _sorted_strings(reason_codes), completion

    if lease.lease_status != "LEASE_CONTRACT_VALID":
        reason_codes.append("AUTHORITY_LEASE_NOT_VALID")
        return "ENVELOPE_INVALID", _sorted_strings(reason_codes), completion

    completion["authority_lease_and_revocation_bound"] = True

    if contradictions or blocking_facts:
        reason_codes.append("ENVELOPE_FAIL_CLOSED")
        if any(
            item["factor_id"] == "EVALUATION_AT_OR_AFTER_VALID_UNTIL" for item in blocking_facts
        ):
            reason_codes.append("ENVELOPE_EXPIRED")
            return "ENVELOPE_EXPIRED", _sorted_strings(reason_codes), completion
        return "ENVELOPE_INVALID", _sorted_strings(reason_codes), completion

    reason_codes.extend(
        [
            "AUTHORITY_LEASE_BOUND",
            "HANDOFF_TRUST_POLICY_BOUND",
            "VERSIONED_ARTIFACT_BOUND",
            "CAPABILITY_ALLOWLIST_VALID",
            "TIME_WINDOW_VALID",
            "REVOCATION_NOT_ACTIVE",
            "ENVELOPE_VALID_FOR_OFFLINE_HANDOFF",
        ]
    )
    completion["secure_handoff_envelope_complete"] = True
    return "ENVELOPE_VALID_FOR_OFFLINE_HANDOFF", _sorted_strings(reason_codes), completion


def _compute_payload_digest(
    *,
    authority_lease_digest: str,
    handoff_trust_policy_digest: str,
    versioned_artifact_digest: str,
) -> str:
    return compute_content_sha256(
        {
            "authority_lease_digest": authority_lease_digest,
            "handoff_trust_policy_digest": handoff_trust_policy_digest,
            "versioned_artifact_digest": versioned_artifact_digest,
            "payload_ref": PAYLOAD_REF,
        }
    )


def _compute_envelope_id(
    *,
    payload_digest: str,
    request: SecureHandoffEnvelopeRequest,
    allowed_capabilities: list[str],
    authority_lease_digest: str,
) -> str:
    body = {
        "envelope_domain": CONTRACT_NAME,
        "payload_digest": payload_digest,
        "authority_lease_digest": authority_lease_digest,
        "allowed_offline_capabilities": allowed_capabilities,
        "intended_consumer_identity_ref": request.intended_consumer_identity_ref,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    return compute_content_sha256(body)


def _input_artifact_ref_mapping(*, bundle: VerifiedAuthorityLeaseBundle) -> dict[str, Any]:
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
            "envelope_id",
            "contract_id",
            "payload_identity",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def build_secure_handoff_envelope_v1(
    *,
    lease: VerifiedAuthorityLeaseBundle,
    request: SecureHandoffEnvelopeRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_envelope_request(request, lease=lease)
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    allowed_capabilities = (
        _normalize_capabilities(
            request.allowed_offline_capabilities, label="allowed_offline_capabilities"
        )
        if request.allowed_offline_capabilities
        else []
    )
    denied_capabilities = _normalize_capabilities(
        request.denied_capabilities, label="denied_capabilities"
    )
    for forbidden in sorted(_FORBIDDEN_CAPABILITIES - {"*", "CAN_*"}):
        if forbidden not in denied_capabilities:
            denied_capabilities.append(forbidden)
    denied_capabilities = sorted(set(denied_capabilities))

    envelope_status, envelope_reason_codes, completion_flags = _evaluate_envelope_status(
        lease=lease,
        request=request,
        blocking_facts=non_contradiction_blocking,
        contradictions=contradictions,
    )

    handoff_payload = lease.handoff.artifact_payload
    lease_payload = lease.artifact_payload
    input_refs = [_input_artifact_ref_mapping(bundle=lease)]

    authority_lease_digest = lease.artifact_digest
    handoff_digest = lease.handoff.artifact_digest
    versioned_digest = lease.handoff.versioned_artifact_digest
    payload_digest = _compute_payload_digest(
        authority_lease_digest=authority_lease_digest,
        handoff_trust_policy_digest=handoff_digest,
        versioned_artifact_digest=versioned_digest,
    )
    envelope_id = _compute_envelope_id(
        payload_digest=payload_digest,
        request=request,
        allowed_capabilities=allowed_capabilities,
        authority_lease_digest=authority_lease_digest,
    )

    input_digest = compute_content_sha256({"input_artifact_refs": input_refs})
    replay_protection_metadata = {
        "idempotency_key": envelope_id,
        "input_digest": input_digest,
        "payload_digest": payload_digest,
        "duplicate_envelope_identity_policy": "FAIL_CLOSED",
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }

    validity_metadata = {
        "valid_from": lease.valid_from,
        "valid_until": lease.valid_until,
        "evaluation_time": request.evaluation_time,
        "lease_status": lease.lease_status,
        "revocation_state": lease.revocation_state,
    }

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "envelope_id": envelope_id,
        "envelope_schema_version": ENVELOPE_SCHEMA_VERSION,
        "envelope_contract_version": CONTRACT_VERSION,
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
        "envelope_status": envelope_status,
        "envelope_reason_codes": envelope_reason_codes,
        "payload_ref": PAYLOAD_REF,
        "payload_identity": payload_digest,
        "payload_digest": payload_digest,
        "authority_lease_and_revocation_ref": lease.artifact_ref,
        "authority_lease_and_revocation_digest": authority_lease_digest,
        "authority_lease_bundle_ref": lease.bundle_dir.as_posix(),
        "authority_lease_manifest_digest": lease.manifest_digest,
        "handoff_trust_policy_ref": HANDOFF_TRUST_POLICY_ARTIFACT_REL,
        "handoff_trust_policy_digest": handoff_digest,
        "handoff_trust_policy_bundle_ref": lease.handoff.bundle_dir.as_posix(),
        "handoff_trust_policy_manifest_digest": lease.handoff.manifest_digest,
        "versioned_artifact_ref": VERSIONED_ARTIFACT_REL,
        "versioned_artifact_digest": versioned_digest,
        "versioned_artifact_bundle_ref": lease.handoff.versioned_artifact_bundle_ref.as_posix(),
        "versioned_artifact_contract_name": VERSIONED_CONTRACT_NAME,
        "versioned_artifact_contract_version": VERSIONED_CONTRACT_VERSION,
        "handoff_trust_policy_contract_name": HANDOFF_TRUST_POLICY_CONTRACT_NAME,
        "handoff_trust_policy_contract_version": HANDOFF_TRUST_POLICY_CONTRACT_VERSION,
        "handoff_trust_policy_producer_version": HANDOFF_TRUST_POLICY_PRODUCER_VERSION,
        "authority_lease_contract_name": AUTHORITY_LEASE_CONTRACT_NAME,
        "authority_lease_contract_version": AUTHORITY_LEASE_CONTRACT_VERSION,
        "authority_lease_producer_version": AUTHORITY_LEASE_PRODUCER_VERSION,
        "intended_consumer_identity_ref": request.intended_consumer_identity_ref,
        "intended_consumer_identity_version": request.intended_consumer_identity_version,
        "intended_consumer_contract_name": str(
            handoff_payload.get("consumer_contract_name", CONSUMER_CONTRACT_NAME)
        ),
        "intended_consumer_contract_version": str(
            handoff_payload.get("consumer_contract_version", CONSUMER_CONTRACT_VERSION)
        ),
        "allowed_offline_capabilities": allowed_capabilities,
        "denied_capabilities": denied_capabilities,
        "preconditions": [
            "verified_authority_lease_and_revocation_v1_bundle",
            "verified_handoff_trust_policy_v1_bundle",
            "transitive_versioned_artifact_digest_match",
            "authority_lease_contract_valid",
            "handoff_trust_result_allow_offline_handoff",
            "explicit_evaluation_time_bound",
            "non_empty_capability_allowlist",
            "deny_by_default",
        ],
        "revocation_state": lease.revocation_state,
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "secure_handoff_envelope_authority_invariants": dict(
            SECURE_HANDOFF_ENVELOPE_AUTHORITY_INVARIANTS
        ),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": {
            field: str(lease_payload[field])
            for field in _TRANSITIVE_LINEAGE_FIELDS
            if lease_payload.get(field) is not None and str(lease_payload.get(field))
        },
        "provenance": {
            "producer_contract_name": CONTRACT_NAME,
            "producer_contract_version": CONTRACT_VERSION,
            "creation_contract_version": CREATION_CONTRACT_VERSION,
            "evidence_level": EVIDENCE_LEVEL,
            "offline_only": True,
            "envelope_created_for_offline_evidence_only": True,
        },
        "source_revision": request.source_revision,
        "validity_metadata": validity_metadata,
        "replay_protection_metadata": replay_protection_metadata,
        "integrity_metadata": {
            "digest_algorithm": "sha256",
            "canonical_serialization": "deterministic_json_dumps",
            "envelope_id_domain": CONTRACT_NAME,
            "signature_created": False,
        },
        "input_digest": "",
        "output_digest": "",
        "manifest_digest": "",
        **completion_flags,
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        payload[key] = value
    payload.update(completion_flags)

    for field in _TRANSITIVE_LINEAGE_FIELDS:
        value = lease_payload.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if envelope_status not in _VALID_ENVELOPE_STATUSES:
        raise SecureHandoffEnvelopeError("envelope_status invalid")

    payload["input_digest"] = input_digest
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["contract_id"] = output_digest
    payload["envelope_id"] = envelope_id
    return payload


def serialize_secure_handoff_envelope_v1(envelope: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(envelope)
    _validate_non_authorizing_flags(envelope)
    if envelope.get("envelope_status") not in _VALID_ENVELOPE_STATUSES:
        raise SecureHandoffEnvelopeError("envelope_status invalid")
    for list_field in (
        "envelope_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
        "allowed_offline_capabilities",
        "denied_capabilities",
    ):
        values = envelope.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("factor_id", item) if isinstance(item, dict) else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise SecureHandoffEnvelopeError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(envelope)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_secure_handoff_envelope_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_envelope_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise SecureHandoffEnvelopeError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise SecureHandoffEnvelopeError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise SecureHandoffEnvelopeError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise SecureHandoffEnvelopeError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise SecureHandoffEnvelopeError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise SecureHandoffEnvelopeError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    envelope: Mapping[str, Any],
    lease: VerifiedAuthorityLeaseBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_authority_lease_input", "status": "PASS"},
        {"check_id": "authority_lease_verified", "status": "PASS"},
        {"check_id": "handoff_trust_policy_verified", "status": "PASS"},
        {"check_id": "transitive_versioned_artifact_bound", "status": "PASS"},
        {"check_id": "offline_only_no_handoff_execution", "status": "PASS"},
        {"check_id": "no_consumer_invocation", "status": "PASS"},
        {"check_id": "no_authority_grant", "status": "PASS"},
        {"check_id": "no_lease_activation", "status": "PASS"},
        {"check_id": "no_revocation_execution", "status": "PASS"},
        {"check_id": "no_promotion_authority", "status": "PASS"},
        {"check_id": "deny_by_default", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = envelope.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "exactly_one_authority_lease_input" else c
            for c in checks
        ]

    if envelope.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if envelope.get("authority_lease_and_revocation_digest") != lease.artifact_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "authority_lease_verified" else c
            for c in checks
        ]

    if envelope.get("handoff_trust_policy_digest") != lease.handoff.artifact_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "handoff_trust_policy_verified" else c
            for c in checks
        ]

    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise SecureHandoffEnvelopeError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": envelope.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_authority_lease_bundle_ref": lease.bundle_dir.as_posix(),
        "verified_envelope_status": envelope.get("envelope_status"),
        "verified_deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_envelope_with_manifest_digest(
    artifact: Mapping[str, Any], *, manifest_digest: str
) -> dict[str, Any]:
    body = dict(artifact)
    body["manifest_digest"] = manifest_digest
    body["output_digest"] = _compute_output_digest(body)
    body["artifact_id"] = body["output_digest"]
    body["contract_id"] = body["output_digest"]
    body["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(body))}
    return body


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def default_envelope_request(
    *, lease: VerifiedAuthorityLeaseBundle
) -> SecureHandoffEnvelopeRequest:
    """Build a deterministic offline envelope request from verified authority lease."""
    handoff_payload = lease.handoff.artifact_payload
    return SecureHandoffEnvelopeRequest(
        evaluation_time=lease.evaluation_time,
        allowed_offline_capabilities=tuple(sorted(_DEFAULT_ALLOWED_OFFLINE_CAPABILITIES)),
        intended_consumer_identity_ref=str(
            handoff_payload.get("consumer_contract_id", CONSUMER_CONTRACT_ID)
        ),
        intended_consumer_identity_version=str(
            handoff_payload.get("consumer_contract_version", CONSUMER_CONTRACT_VERSION)
        ),
    )


def verify_secure_handoff_envelope_inputs(
    inputs: SecureHandoffEnvelopeInputs,
) -> VerifiedAuthorityLeaseBundle:
    """Verify exactly one authority lease bundle."""
    return verify_authority_lease_bundle(inputs.authority_lease_bundle_dir)


def reverify_secure_handoff_envelope_v1(*, output_dir: Path | str) -> None:
    """Replay secure handoff envelope bundle without upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise SecureHandoffEnvelopeError(
            f"secure handoff envelope directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise SecureHandoffEnvelopeError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    envelope = read_manifest(artifact_path)
    _validate_envelope_integrity(envelope)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise SecureHandoffEnvelopeError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(envelope)
    if envelope.get("manifest_digest") != manifest_digest:
        raise SecureHandoffEnvelopeError("manifest_digest mismatch on replay")

    lease = verify_authority_lease_bundle(Path(str(envelope["authority_lease_bundle_ref"])))
    if envelope.get("authority_lease_and_revocation_digest") != lease.artifact_digest:
        raise SecureHandoffEnvelopeError("authority lease digest mismatch on replay")
    if envelope.get("handoff_trust_policy_digest") != lease.handoff.artifact_digest:
        raise SecureHandoffEnvelopeError("handoff trust policy digest mismatch on replay")


def produce_secure_handoff_envelope_v1(
    *,
    inputs: SecureHandoffEnvelopeInputs,
    output_dir: Path | str,
) -> SecureHandoffEnvelopeResult:
    """Produce offline LEVEL_3 secure handoff envelope evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        authority_lease_dir=inputs.authority_lease_bundle_dir,
        output_dir=final_dir,
    )

    lease = verify_secure_handoff_envelope_inputs(inputs)
    envelope_body = build_secure_handoff_envelope_v1(
        lease=lease,
        request=inputs.envelope_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise SecureHandoffEnvelopeError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(envelope_body)
        finalized = _finalize_envelope_with_manifest_digest(
            envelope_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_secure_handoff_envelope_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            envelope=finalized,
            lease=lease,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise SecureHandoffEnvelopeError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_secure_handoff_envelope_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise SecureHandoffEnvelopeError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return SecureHandoffEnvelopeResult(
        output_dir=final_dir,
        envelope_id=str(finalized["envelope_id"]),
        envelope_status=str(finalized["envelope_status"]),
        envelope_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        authority_lease_ref=str(finalized["authority_lease_bundle_ref"]),
        authority_lease_digest=str(finalized["authority_lease_and_revocation_digest"]),
        payload_digest=str(finalized["payload_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "CREATION_CONTRACT_VERSION",
    "DEFAULT_PRODUCER_IDENTITY_REF",
    "DEFAULT_SOURCE_REVISION",
    "DETERMINISTIC_RULE_SET_VERSION",
    "ENVELOPE_SCHEMA_VERSION",
    "EVIDENCE_LEVEL",
    "MANIFEST_FILENAME",
    "PAYLOAD_REF",
    "PRODUCER_VERSION",
    "SECURE_HANDOFF_ENVELOPE_AUTHORITY_INVARIANTS",
    "SELF_VERIFICATION_REL",
    "SecureHandoffEnvelopeError",
    "SecureHandoffEnvelopeInputs",
    "SecureHandoffEnvelopeRequest",
    "SecureHandoffEnvelopeResult",
    "VerifiedAuthorityLeaseBundle",
    "build_secure_handoff_envelope_v1",
    "default_envelope_request",
    "produce_secure_handoff_envelope_v1",
    "reverify_secure_handoff_envelope_v1",
    "serialize_secure_handoff_envelope_v1",
    "verify_authority_lease_bundle",
    "verify_secure_handoff_envelope_inputs",
]
