"""Offline LEVEL_3 authority lease and revocation contract owner v1."""

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
    ARTIFACT_REL as HANDOFF_TRUST_POLICY_ARTIFACT_REL,
    CONTRACT_NAME as HANDOFF_TRUST_POLICY_CONTRACT_NAME,
    CONTRACT_VERSION as HANDOFF_TRUST_POLICY_CONTRACT_VERSION,
    HandoffTrustPolicyError,
    PRODUCER_VERSION as HANDOFF_TRUST_POLICY_PRODUCER_VERSION,
    SELF_VERIFICATION_REL as HANDOFF_TRUST_POLICY_SELF_VERIFICATION_REL,
    reverify_handoff_trust_policy_v1,
    verify_versioned_artifact_bundle,
)
from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    ARTIFACT_REL as VERSIONED_ARTIFACT_REL,
    CONTRACT_NAME as VERSIONED_CONTRACT_NAME,
    CONTRACT_VERSION as VERSIONED_CONTRACT_VERSION,
)

CONTRACT_NAME = "authority_lease_and_revocation_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "authority_lease_and_revocation_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "authority_lease_and_revocation_record"
INPUT_RELATION = "EVALUATES_VERIFIED_HANDOFF_TRUST_POLICY_V1"
ARTIFACT_REL = "authority_lease_and_revocation_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".authority_lease_and_revocation_staging_"

LEASE_SCHEMA_VERSION = "authority_lease_schema_v1"
DETERMINISTIC_RULE_SET_VERSION = "authority_lease_and_revocation_rules_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_ISSUER_IDENTITY_REF = "peak_trade_offline_authority_lease_issuer_v1"
DEFAULT_ISSUER_IDENTITY_DIGEST = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"

_VALID_AUTHORITY_DOMAINS = frozenset({"TRADING_DECISION_CORE", "SAFETY_EXECUTION_RUNTIME_CORE"})
_VALID_LEASE_STATUSES = frozenset(
    {
        "LEASE_CONTRACT_VALID",
        "LEASE_CONTRACT_INVALID",
        "LEASE_REVOKED",
        "LEASE_EXPIRED",
        "ABSTAIN",
    }
)
_VALID_REVOCATION_STATES = frozenset({"NOT_REVOKED", "REVOKED", "UNKNOWN"})
_UTC_INSTANT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$")

_DEFAULT_ALLOWED_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_DESCRIBE_OFFLINE_AUTHORITY_SCOPE",
        "CAN_BIND_HANDOFF_TRUST_POLICY_REF",
    }
)

_FORBIDDEN_CAPABILITIES: frozenset[str] = frozenset(
    {
        "CAN_GRANT_AUTHORITY",
        "CAN_ACTIVATE_LEASE",
        "CAN_RENEW_LEASE",
        "CAN_REVOKE_AUTHORITY",
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

AUTHORITY_LEASE_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "authority_lease_is_descriptive_only": True,
    "authority_lease_does_not_grant_authority": True,
    "authority_lease_does_not_activate_lease": True,
    "authority_lease_does_not_execute_revocation": True,
    "authority_lease_does_not_invoke_consumer": True,
    "authority_lease_does_not_mutate_consumer": True,
    "authority_lease_does_not_authorize_promotion": True,
    "authority_lease_does_not_create_configpatch": True,
    "authority_lease_does_not_authorize_runtime": True,
    "authority_lease_does_not_authorize_live": True,
    "authority_lease_is_offline_only": True,
    "deny_by_default": True,
    "revocation_precedence": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_authority_lease_and_revocation": True,
    "authority_lease_contract_offline_only": True,
    "authority_lease_and_revocation_contract_complete": False,
    "handoff_trust_policy_bound": False,
    "cross_domain_lineage_bound": False,
    "deny_by_default": True,
    "revocation_precedence": True,
    "authority_granted": False,
    "authority_activated": False,
    "lease_activated": False,
    "lease_renewed": False,
    "revocation_executed": False,
    "killswitch_executed": False,
    "handoff_executed": False,
    "consumer_invoked": False,
    "consumer_mutated": False,
    "files_transferred": False,
    "network_side_effect_created": False,
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

_SELF_VERIFICATION_SCHEMA_VERSION = "authority_lease_and_revocation_self_verification_v1"


class AuthorityLeaseAndRevocationError(ValueError):
    """Fail-closed authority lease and revocation error."""


@dataclass(frozen=True)
class VerifiedHandoffTrustPolicyBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    versioned_artifact_bundle_ref: Path
    versioned_artifact_digest: str


@dataclass(frozen=True)
class AuthorityLeaseRequest:
    authority_domain: str
    subject_identity_ref: str
    subject_identity_digest: str
    issuer_identity_ref: str
    issuer_identity_digest: str
    valid_from: str
    valid_until: str
    evaluation_time: str
    allowed_capabilities: tuple[str, ...]
    denied_capabilities: tuple[str, ...] = ()
    revocation_state: str = "NOT_REVOKED"
    revocation_ref: str | None = None
    revocation_digest: str | None = None
    revocation_reason_codes: tuple[str, ...] = ()
    revocation_priority: int = 100


@dataclass(frozen=True)
class AuthorityLeaseInputs:
    handoff_trust_policy_bundle_dir: Path
    lease_request: AuthorityLeaseRequest


@dataclass(frozen=True)
class AuthorityLeaseResult:
    output_dir: Path
    lease_id: str
    lease_status: str
    lease_contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    handoff_trust_policy_ref: str
    handoff_trust_policy_digest: str


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise AuthorityLeaseAndRevocationError(f"{label} must not be a symlink")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise AuthorityLeaseAndRevocationError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise AuthorityLeaseAndRevocationError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise AuthorityLeaseAndRevocationError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise AuthorityLeaseAndRevocationError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise AuthorityLeaseAndRevocationError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, handoff_trust_policy_dir: Path, output_dir: Path) -> None:
    input_res = handoff_trust_policy_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == input_res:
        raise AuthorityLeaseAndRevocationError("output directory must not equal input path")
    if _path_is_under(output_res, input_res):
        raise AuthorityLeaseAndRevocationError("output directory must not be inside input path")
    if _path_is_under(input_res, output_res):
        raise AuthorityLeaseAndRevocationError(
            "input directory must not be inside output directory"
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
        raise AuthorityLeaseAndRevocationError(f"{label} must be a JSON object")
    return payload


def _artifact_digest_from_payload(payload: Mapping[str, Any]) -> str:
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise AuthorityLeaseAndRevocationError("integrity must be an object")
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        raise AuthorityLeaseAndRevocationError("integrity.content_sha256 invalid")
    return digest


def _parse_utc_instant(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AuthorityLeaseAndRevocationError(f"{field} must be a non-empty UTC instant")
    if not _UTC_INSTANT_PATTERN.match(value):
        raise AuthorityLeaseAndRevocationError(
            f"{field} must use canonical UTC format with +00:00 or Z suffix"
        )
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AuthorityLeaseAndRevocationError(f"{field} is not a valid UTC instant") from exc
    if parsed.tzinfo != timezone.utc:
        raise AuthorityLeaseAndRevocationError(f"{field} must be UTC")
    return parsed


def _validate_capability_name(capability: str) -> None:
    if not capability or not isinstance(capability, str):
        raise AuthorityLeaseAndRevocationError("capability must be a non-empty string")
    if "*" in capability or capability.endswith("_ALL"):
        raise AuthorityLeaseAndRevocationError(f"overbroad wildcard capability: {capability}")
    if capability in _FORBIDDEN_CAPABILITIES:
        raise AuthorityLeaseAndRevocationError(f"forbidden capability: {capability}")


def _normalize_capabilities(values: tuple[str, ...] | list[str], *, label: str) -> list[str]:
    if not isinstance(values, (tuple, list)):
        raise AuthorityLeaseAndRevocationError(f"{label} must be a list")
    normalized: list[str] = []
    for item in values:
        _validate_capability_name(item)
        normalized.append(item)
    return sorted(set(normalized))


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        actual = payload.get(key)
        if key in {
            "authority_lease_and_revocation_contract_complete",
            "handoff_trust_policy_bound",
            "cross_domain_lineage_bound",
        }:
            continue
        if actual is not expected:
            raise AuthorityLeaseAndRevocationError(f"{key} must be {expected!r}")


def verify_handoff_trust_policy_bundle(
    bundle_dir: Path | str,
) -> VerifiedHandoffTrustPolicyBundle:
    """Fail-closed verification of exactly one handoff trust policy bundle."""
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="handoff trust policy bundle")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise AuthorityLeaseAndRevocationError(
            f"handoff trust policy MANIFEST.sha256 verification failed: {msg}"
        )

    artifact_path = path / HANDOFF_TRUST_POLICY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=HANDOFF_TRUST_POLICY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    if payload.get("contract_name") != HANDOFF_TRUST_POLICY_CONTRACT_NAME:
        raise AuthorityLeaseAndRevocationError("handoff trust policy contract_name mismatch")
    if payload.get("contract_version") != HANDOFF_TRUST_POLICY_CONTRACT_VERSION:
        raise AuthorityLeaseAndRevocationError("handoff trust policy contract_version mismatch")

    self_payload = _load_self_verification(
        path,
        rel=HANDOFF_TRUST_POLICY_SELF_VERIFICATION_REL,
        label=HANDOFF_TRUST_POLICY_SELF_VERIFICATION_REL,
    )
    if self_payload.get("overall_status") != "PASS":
        raise AuthorityLeaseAndRevocationError(
            "handoff trust policy SELF_VERIFICATION overall_status must be PASS"
        )

    try:
        reverify_handoff_trust_policy_v1(output_dir=path)
    except HandoffTrustPolicyError as exc:
        raise AuthorityLeaseAndRevocationError(str(exc)) from exc

    versioned_ref_raw = payload.get("versioned_artifact_bundle_ref")
    if not versioned_ref_raw:
        raise AuthorityLeaseAndRevocationError(
            "handoff trust policy missing versioned_artifact_bundle_ref"
        )
    versioned_ref = Path(str(versioned_ref_raw))
    versioned_digest = str(payload.get("versioned_artifact_digest", ""))
    if not is_valid_sha256_hex(versioned_digest):
        raise AuthorityLeaseAndRevocationError(
            "handoff trust policy versioned_artifact_digest invalid"
        )

    versioned_bundle = verify_versioned_artifact_bundle(versioned_ref)
    if versioned_bundle.artifact_digest != versioned_digest:
        raise AuthorityLeaseAndRevocationError("transitive versioned artifact digest mismatch")

    return VerifiedHandoffTrustPolicyBundle(
        bundle_dir=path.resolve(),
        contract_name=HANDOFF_TRUST_POLICY_CONTRACT_NAME,
        contract_version=HANDOFF_TRUST_POLICY_CONTRACT_VERSION,
        producer_version=HANDOFF_TRUST_POLICY_PRODUCER_VERSION,
        artifact_ref=HANDOFF_TRUST_POLICY_ARTIFACT_REL,
        artifact_digest=_artifact_digest_from_payload(payload),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        versioned_artifact_bundle_ref=versioned_ref.resolve(),
        versioned_artifact_digest=versioned_digest,
    )


def _validate_lease_request(request: AuthorityLeaseRequest) -> list[dict[str, str]]:
    blocking: list[dict[str, str]] = []
    if request.authority_domain not in _VALID_AUTHORITY_DOMAINS:
        blocking.append(
            _factor(
                factor_id="UNKNOWN_AUTHORITY_DOMAIN",
                factor_type="BLOCKING_FACT",
                source_field="authority_domain",
                observation=f"unknown authority domain {request.authority_domain!r}",
            )
        )
    if not request.subject_identity_ref:
        blocking.append(
            _factor(
                factor_id="MISSING_SUBJECT_IDENTITY_REF",
                factor_type="MISSING_PRECONDITION",
                source_field="subject_identity_ref",
                observation="subject_identity_ref is required",
            )
        )
    if not is_valid_sha256_hex(request.subject_identity_digest):
        blocking.append(
            _factor(
                factor_id="INVALID_SUBJECT_IDENTITY_DIGEST",
                factor_type="MISSING_PRECONDITION",
                source_field="subject_identity_digest",
                observation="subject_identity_digest must be valid sha256 hex",
            )
        )
    if not request.issuer_identity_ref:
        blocking.append(
            _factor(
                factor_id="MISSING_ISSUER_IDENTITY_REF",
                factor_type="MISSING_PRECONDITION",
                source_field="issuer_identity_ref",
                observation="issuer_identity_ref is required",
            )
        )
    if not is_valid_sha256_hex(request.issuer_identity_digest):
        blocking.append(
            _factor(
                factor_id="INVALID_ISSUER_IDENTITY_DIGEST",
                factor_type="MISSING_PRECONDITION",
                source_field="issuer_identity_digest",
                observation="issuer_identity_digest must be valid sha256 hex",
            )
        )

    try:
        valid_from = _parse_utc_instant(request.valid_from, field="valid_from")
        valid_until = _parse_utc_instant(request.valid_until, field="valid_until")
        evaluation_time = _parse_utc_instant(request.evaluation_time, field="evaluation_time")
    except AuthorityLeaseAndRevocationError as exc:
        blocking.append(
            _factor(
                factor_id="INVALID_TIME_SEMANTICS",
                factor_type="BLOCKING_FACT",
                source_field="evaluation_time",
                observation=str(exc),
            )
        )
        return blocking

    if valid_until <= valid_from:
        blocking.append(
            _factor(
                factor_id="VALID_UNTIL_BEFORE_VALID_FROM",
                factor_type="CONTRADICTION",
                source_field="valid_until",
                observation="valid_until must be strictly after valid_from",
            )
        )

    allowed = _normalize_capabilities(request.allowed_capabilities, label="allowed_capabilities")
    denied = _normalize_capabilities(request.denied_capabilities, label="denied_capabilities")
    if not allowed:
        blocking.append(
            _factor(
                factor_id="EMPTY_ALLOWED_CAPABILITIES",
                factor_type="BLOCKING_FACT",
                source_field="allowed_capabilities",
                observation="allowed_capabilities must be non-empty deny-by-default allowlist",
            )
        )
    overlap = set(allowed) & set(denied)
    for capability in sorted(overlap):
        blocking.append(
            _factor(
                factor_id=f"CAPABILITY_ALLOW_DENY_CONFLICT_{capability}",
                factor_type="CONTRADICTION",
                source_field="allowed_capabilities",
                observation=f"capability {capability!r} appears in both allow and deny lists",
            )
        )

    if request.revocation_state not in _VALID_REVOCATION_STATES:
        blocking.append(
            _factor(
                factor_id="UNKNOWN_REVOCATION_STATE",
                factor_type="BLOCKING_FACT",
                source_field="revocation_state",
                observation=f"unknown revocation state {request.revocation_state!r}",
            )
        )

    if request.revocation_state == "REVOKED":
        if not request.revocation_ref:
            blocking.append(
                _factor(
                    factor_id="MISSING_REVOCATION_REF",
                    factor_type="MISSING_PRECONDITION",
                    source_field="revocation_ref",
                    observation="revocation_ref required when revocation_state is REVOKED",
                )
            )
        if request.revocation_digest and not is_valid_sha256_hex(request.revocation_digest):
            blocking.append(
                _factor(
                    factor_id="INVALID_REVOCATION_DIGEST",
                    factor_type="BLOCKING_FACT",
                    source_field="revocation_digest",
                    observation="revocation_digest must be valid sha256 hex when present",
                )
            )

    if evaluation_time < valid_from:
        blocking.append(
            _factor(
                factor_id="EVALUATION_BEFORE_VALID_FROM",
                factor_type="BLOCKING_FACT",
                source_field="evaluation_time",
                observation="evaluation_time is before valid_from",
            )
        )
    if evaluation_time >= valid_until:
        blocking.append(
            _factor(
                factor_id="EVALUATION_AT_OR_AFTER_VALID_UNTIL",
                factor_type="BLOCKING_FACT",
                source_field="evaluation_time",
                observation="evaluation_time is at or after valid_until",
            )
        )

    return blocking


def _evaluate_lease_status(
    *,
    handoff: VerifiedHandoffTrustPolicyBundle,
    request: AuthorityLeaseRequest,
    blocking_facts: list[dict[str, str]],
    contradictions: list[dict[str, str]],
) -> tuple[str, list[str], dict[str, bool]]:
    reason_codes: list[str] = []
    completion = {
        "authority_lease_and_revocation_contract_complete": False,
        "handoff_trust_policy_bound": False,
        "cross_domain_lineage_bound": False,
    }

    trust_result = str(handoff.artifact_payload.get("trust_result", ""))
    if trust_result != "ALLOW_OFFLINE_HANDOFF":
        reason_codes.append("HANDOFF_TRUST_POLICY_NOT_ALLOW")
        return "LEASE_CONTRACT_INVALID", _sorted_strings(reason_codes), completion

    completion["handoff_trust_policy_bound"] = True

    if handoff.artifact_payload.get("cross_domain_lineage_bound") is True:
        completion["cross_domain_lineage_bound"] = True

    if request.revocation_state == "UNKNOWN":
        reason_codes.append("REVOCATION_STATE_UNKNOWN")
        return "ABSTAIN", _sorted_strings(reason_codes), completion

    if request.revocation_state == "REVOKED":
        reason_codes.append("REVOCATION_PRECEDENCE")
        return "LEASE_REVOKED", _sorted_strings(reason_codes), completion

    if contradictions or blocking_facts:
        reason_codes.append("LEASE_CONTRACT_FAIL_CLOSED")
        if any(
            item["factor_id"] == "EVALUATION_AT_OR_AFTER_VALID_UNTIL" for item in blocking_facts
        ):
            reason_codes.append("LEASE_EXPIRED")
            return "LEASE_EXPIRED", _sorted_strings(reason_codes), completion
        return "LEASE_CONTRACT_INVALID", _sorted_strings(reason_codes), completion

    reason_codes.extend(
        [
            "HANDOFF_TRUST_POLICY_BOUND",
            "CAPABILITY_ALLOWLIST_VALID",
            "TIME_WINDOW_VALID",
            "REVOCATION_NOT_ACTIVE",
            "LEASE_CONTRACT_VALID",
        ]
    )
    completion["authority_lease_and_revocation_contract_complete"] = True
    return "LEASE_CONTRACT_VALID", _sorted_strings(reason_codes), completion


def _compute_lease_id(
    *,
    handoff_digest: str,
    request: AuthorityLeaseRequest,
    allowed_capabilities: list[str],
) -> str:
    body = {
        "authority_domain": request.authority_domain,
        "subject_identity_digest": request.subject_identity_digest,
        "issuer_identity_digest": request.issuer_identity_digest,
        "valid_from": request.valid_from,
        "valid_until": request.valid_until,
        "allowed_capabilities": allowed_capabilities,
        "handoff_trust_policy_digest": handoff_digest,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    return compute_content_sha256(body)


def _input_artifact_ref_mapping(*, bundle: VerifiedHandoffTrustPolicyBundle) -> dict[str, Any]:
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
            "lease_id",
            "contract_id",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def build_authority_lease_and_revocation_v1(
    *,
    handoff: VerifiedHandoffTrustPolicyBundle,
    request: AuthorityLeaseRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_lease_request(request)
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    allowed_capabilities = (
        _normalize_capabilities(request.allowed_capabilities, label="allowed_capabilities")
        if request.allowed_capabilities
        else []
    )
    denied_capabilities = _normalize_capabilities(
        request.denied_capabilities, label="denied_capabilities"
    )
    for forbidden in sorted(_FORBIDDEN_CAPABILITIES - {"*", "CAN_*"}):
        if forbidden not in denied_capabilities:
            denied_capabilities.append(forbidden)
    denied_capabilities = sorted(set(denied_capabilities))

    lease_status, lease_reason_codes, completion_flags = _evaluate_lease_status(
        handoff=handoff,
        request=request,
        blocking_facts=non_contradiction_blocking,
        contradictions=contradictions,
    )

    input_refs = [_input_artifact_ref_mapping(bundle=handoff)]
    versioned_payload = handoff.artifact_payload
    lease_id = _compute_lease_id(
        handoff_digest=handoff.artifact_digest,
        request=request,
        allowed_capabilities=allowed_capabilities,
    )

    no_revocation_evidence = (
        request.revocation_state == "NOT_REVOKED" and not request.revocation_ref
    )

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "lease_id": lease_id,
        "lease_schema_version": LEASE_SCHEMA_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "contract_creation_time": OFFLINE_DETERMINISTIC_CREATED_AT,
        "issued_at": request.valid_from,
        "producer_version": PRODUCER_VERSION,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "authority_domain": request.authority_domain,
        "subject_identity_ref": request.subject_identity_ref,
        "subject_identity_digest": request.subject_identity_digest,
        "issuer_identity_ref": request.issuer_identity_ref,
        "issuer_identity_digest": request.issuer_identity_digest,
        "source_handoff_trust_policy_ref": handoff.artifact_ref,
        "source_handoff_trust_policy_digest": handoff.artifact_digest,
        "handoff_trust_policy_bundle_ref": handoff.bundle_dir.as_posix(),
        "handoff_trust_policy_manifest_digest": handoff.manifest_digest,
        "versioned_artifact_bundle_ref": handoff.versioned_artifact_bundle_ref.as_posix(),
        "versioned_artifact_artifact_ref": VERSIONED_ARTIFACT_REL,
        "versioned_artifact_digest": handoff.versioned_artifact_digest,
        "versioned_artifact_contract_name": VERSIONED_CONTRACT_NAME,
        "versioned_artifact_contract_version": VERSIONED_CONTRACT_VERSION,
        "allowed_capabilities": allowed_capabilities,
        "denied_capabilities": denied_capabilities,
        "preconditions": [
            "verified_handoff_trust_policy_v1_bundle",
            "handoff_trust_result_allow_offline_handoff",
            "transitive_versioned_artifact_digest_match",
            "explicit_evaluation_time_bound",
            "non_empty_capability_allowlist",
            "deny_by_default",
        ],
        "valid_from": request.valid_from,
        "valid_until": request.valid_until,
        "evaluation_time": request.evaluation_time,
        "revocation_state": request.revocation_state,
        "revocation_ref": request.revocation_ref,
        "revocation_digest": request.revocation_digest,
        "revocation_reason_codes": sorted(request.revocation_reason_codes),
        "revocation_priority": request.revocation_priority,
        "no_revocation_evidence_contract": no_revocation_evidence,
        "lease_status": lease_status,
        "lease_reason_codes": lease_reason_codes,
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "authority_lease_authority_invariants": dict(AUTHORITY_LEASE_AUTHORITY_INVARIANTS),
        "input_artifact_refs": input_refs,
        "cross_domain_lineage": {
            field: str(versioned_payload[field])
            for field in _TRANSITIVE_LINEAGE_FIELDS
            if versioned_payload.get(field) is not None and str(versioned_payload.get(field))
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
        value = versioned_payload.get(field)
        if value is not None and str(value):
            payload[field] = str(value)

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if lease_status not in _VALID_LEASE_STATUSES:
        raise AuthorityLeaseAndRevocationError("lease_status invalid")

    payload["input_digest"] = compute_content_sha256({"input_artifact_refs": input_refs})
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["contract_id"] = output_digest
    payload["lease_id"] = lease_id
    return payload


def serialize_authority_lease_and_revocation_v1(
    lease_contract: Mapping[str, Any],
) -> str:
    _reject_forbidden_index_keys(lease_contract)
    _validate_non_authorizing_flags(lease_contract)
    if lease_contract.get("lease_status") not in _VALID_LEASE_STATUSES:
        raise AuthorityLeaseAndRevocationError("lease_status invalid")
    for list_field in (
        "lease_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
        "allowed_capabilities",
        "denied_capabilities",
    ):
        values = lease_contract.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("factor_id", item) if isinstance(item, dict) else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise AuthorityLeaseAndRevocationError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(lease_contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_authority_lease_and_revocation_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_lease_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise AuthorityLeaseAndRevocationError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise AuthorityLeaseAndRevocationError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise AuthorityLeaseAndRevocationError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise AuthorityLeaseAndRevocationError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise AuthorityLeaseAndRevocationError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise AuthorityLeaseAndRevocationError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    lease_contract: Mapping[str, Any],
    handoff: VerifiedHandoffTrustPolicyBundle,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "evidence_level_level_3", "status": "PASS"},
        {"check_id": "exactly_one_handoff_trust_policy_input", "status": "PASS"},
        {"check_id": "handoff_trust_policy_verified", "status": "PASS"},
        {"check_id": "transitive_versioned_artifact_bound", "status": "PASS"},
        {"check_id": "offline_only_no_authority_grant", "status": "PASS"},
        {"check_id": "no_lease_activation", "status": "PASS"},
        {"check_id": "no_revocation_execution", "status": "PASS"},
        {"check_id": "no_consumer_invocation", "status": "PASS"},
        {"check_id": "no_promotion_authority", "status": "PASS"},
        {"check_id": "deny_by_default", "status": "PASS"},
        {"check_id": "revocation_precedence_modeled", "status": "PASS"},
        {"check_id": "output_digest", "status": "PASS"},
        {"check_id": "manifest_verification", "status": "PASS"},
        {"check_id": "deterministic_reverification", "status": "PASS"},
    ]

    input_refs = lease_contract.get("input_artifact_refs")
    if not isinstance(input_refs, list) or len(input_refs) != 1:
        checks = [
            {**c, "status": "FAIL"}
            if c["check_id"] == "exactly_one_handoff_trust_policy_input"
            else c
            for c in checks
        ]

    if lease_contract.get("manifest_digest") != manifest_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "manifest_verification" else c
            for c in checks
        ]

    if lease_contract.get("source_handoff_trust_policy_digest") != handoff.artifact_digest:
        checks = [
            {**c, "status": "FAIL"} if c["check_id"] == "handoff_trust_policy_verified" else c
            for c in checks
        ]

    structural_failures = [check for check in checks if check["status"] != "PASS"]
    if structural_failures:
        raise AuthorityLeaseAndRevocationError("self-verification checks failed")

    payload: dict[str, Any] = {
        "self_verification_schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": "PASS",
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "verified_output_digest": lease_contract.get("output_digest"),
        "verified_manifest_digest": manifest_digest,
        "verified_handoff_trust_policy_bundle_ref": handoff.bundle_dir.as_posix(),
        "verified_lease_status": lease_contract.get("lease_status"),
        "verified_deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def _finalize_lease_contract_with_manifest_digest(
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


def default_lease_request(
    *,
    handoff: VerifiedHandoffTrustPolicyBundle,
    authority_domain: str = "TRADING_DECISION_CORE",
    evaluation_time: str = "2026-06-29T12:00:00+00:00",
    valid_from: str = "2026-06-29T00:00:00+00:00",
    valid_until: str = "2026-06-30T00:00:00+00:00",
) -> AuthorityLeaseRequest:
    """Build a deterministic offline lease request from verified handoff lineage."""
    artifact = handoff.artifact_payload
    subject_ref = str(artifact.get("strategy_identity_ref", ""))
    subject_digest = str(artifact.get("strategy_identity_digest", ""))
    if not subject_ref or not is_valid_sha256_hex(subject_digest):
        raise AuthorityLeaseAndRevocationError(
            "handoff trust policy missing strategy identity for subject binding"
        )
    return AuthorityLeaseRequest(
        authority_domain=authority_domain,
        subject_identity_ref=subject_ref,
        subject_identity_digest=subject_digest,
        issuer_identity_ref=DEFAULT_ISSUER_IDENTITY_REF,
        issuer_identity_digest=DEFAULT_ISSUER_IDENTITY_DIGEST,
        valid_from=valid_from,
        valid_until=valid_until,
        evaluation_time=evaluation_time,
        allowed_capabilities=tuple(sorted(_DEFAULT_ALLOWED_CAPABILITIES)),
    )


def verify_authority_lease_inputs(
    inputs: AuthorityLeaseInputs,
) -> VerifiedHandoffTrustPolicyBundle:
    """Verify exactly one handoff trust policy bundle."""
    return verify_handoff_trust_policy_bundle(inputs.handoff_trust_policy_bundle_dir)


def reverify_authority_lease_and_revocation_v1(*, output_dir: Path | str) -> None:
    """Replay authority lease bundle without upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise AuthorityLeaseAndRevocationError(f"authority lease directory not found: {bundle_dir}")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise AuthorityLeaseAndRevocationError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    lease_contract = read_manifest(artifact_path)
    _validate_lease_contract_integrity(lease_contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise AuthorityLeaseAndRevocationError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(lease_contract)
    if lease_contract.get("manifest_digest") != manifest_digest:
        raise AuthorityLeaseAndRevocationError("manifest_digest mismatch on replay")

    handoff = verify_handoff_trust_policy_bundle(
        Path(str(lease_contract["handoff_trust_policy_bundle_ref"]))
    )
    if lease_contract.get("source_handoff_trust_policy_digest") != handoff.artifact_digest:
        raise AuthorityLeaseAndRevocationError("handoff trust policy digest mismatch on replay")


def produce_authority_lease_and_revocation_v1(
    *,
    inputs: AuthorityLeaseInputs,
    output_dir: Path | str,
) -> AuthorityLeaseResult:
    """Produce offline LEVEL_3 authority lease and revocation contract evidence."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        handoff_trust_policy_dir=inputs.handoff_trust_policy_bundle_dir,
        output_dir=final_dir,
    )

    handoff = verify_authority_lease_inputs(inputs)
    lease_body = build_authority_lease_and_revocation_v1(
        handoff=handoff,
        request=inputs.lease_request,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise AuthorityLeaseAndRevocationError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(lease_body)
        finalized = _finalize_lease_contract_with_manifest_digest(
            lease_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_authority_lease_and_revocation_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            lease_contract=finalized,
            handoff=handoff,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise AuthorityLeaseAndRevocationError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_authority_lease_and_revocation_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise AuthorityLeaseAndRevocationError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return AuthorityLeaseResult(
        output_dir=final_dir,
        lease_id=str(finalized["lease_id"]),
        lease_status=str(finalized["lease_status"]),
        lease_contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        handoff_trust_policy_ref=str(finalized["handoff_trust_policy_bundle_ref"]),
        handoff_trust_policy_digest=str(finalized["source_handoff_trust_policy_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_LEASE_AUTHORITY_INVARIANTS",
    "AUTHORITY_LEVEL",
    "AuthorityLeaseAndRevocationError",
    "AuthorityLeaseInputs",
    "AuthorityLeaseRequest",
    "AuthorityLeaseResult",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "DEFAULT_ISSUER_IDENTITY_DIGEST",
    "DEFAULT_ISSUER_IDENTITY_REF",
    "DETERMINISTIC_RULE_SET_VERSION",
    "EVIDENCE_LEVEL",
    "LEASE_SCHEMA_VERSION",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "VerifiedHandoffTrustPolicyBundle",
    "build_authority_lease_and_revocation_v1",
    "default_lease_request",
    "produce_authority_lease_and_revocation_v1",
    "reverify_authority_lease_and_revocation_v1",
    "serialize_authority_lease_and_revocation_v1",
    "verify_authority_lease_inputs",
    "verify_handoff_trust_policy_bundle",
]
