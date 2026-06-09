"""Order-Capability private endpoint boundary contract (v1).

Pure offline evaluation of secret-free evidence summaries against harness readonly
policy. Does not authorize network, secrets, cancel, flatten, live, preflight lift,
or execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.ops.bounded_futures_private_readonly_contract_v0 import (
    DEMO_FUTURES_REST_BASE_URL,
    FUTURES_ORDER_MUTATION_ENDPOINTS,
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    PACKAGE_MARKER as HARNESS_PACKAGE_MARKER,
    PRIVATE_READONLY_MODE,
    evaluate_private_readonly_policy,
    path_contains_forbidden_substring,
    validate_private_readonly_endpoint_path,
    validate_private_readonly_http_method,
    validate_private_readonly_rest_base_url,
)

PACKAGE_MARKER = "ORDER_CAPABILITY_PRIVATE_ENDPOINT_BOUNDARY_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_private_endpoint_boundary_result.v1"

ALLOWED_ENVIRONMENTS = frozenset(
    {
        "kraken_futures_demo",
        "demo",
        "testnet",
        "demo_testnet_only",
    }
)
FORBIDDEN_ENVIRONMENT_MARKERS = frozenset(
    {
        "live",
        "prod",
        "production",
        "mainnet",
    }
)
SUPPORTED_PROFILE_MODES = frozenset(
    {
        PRIVATE_READONLY_MODE,
        "offline_policy_summary",
    }
)
FORBIDDEN_SERIALIZATION_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "secret",
        "password",
        "token",
        "credential",
        "credentials",
        "private_key",
    }
)

REASON_MISSING_EVIDENCE_SUMMARY = "MISSING_EVIDENCE_SUMMARY"
REASON_MANIFEST_NOT_VERIFIED = "MANIFEST_NOT_VERIFIED"
REASON_LIVE_ENVIRONMENT_REJECTED = "LIVE_ENVIRONMENT_REJECTED"
REASON_SECRET_MATERIAL_PRESENT = "SECRET_MATERIAL_PRESENT"
REASON_NETWORK_PERFORMED = "NETWORK_PERFORMED"
REASON_ORDER_ENDPOINT_PRESENT = "ORDER_ENDPOINT_PRESENT"
REASON_CANCEL_ENDPOINT_PRESENT = "CANCEL_ENDPOINT_PRESENT"
REASON_MODIFY_ENDPOINT_PRESENT = "MODIFY_ENDPOINT_PRESENT"
REASON_POSITION_MUTATION_ENDPOINT_PRESENT = "POSITION_MUTATION_ENDPOINT_PRESENT"
REASON_MISSING_CORRELATION = "MISSING_CORRELATION"
REASON_UNSUPPORTED_PROFILE = "UNSUPPORTED_PROFILE"
REASON_READONLY_PROFILE_NOT_PROVEN = "READONLY_PROFILE_NOT_PROVEN"
REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED = (
    "BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED"
)
REASON_HARNESS_POLICY_MISMATCH = "HARNESS_POLICY_MISMATCH"
REASON_UNSAFE_AUTHORITY_FLAGS = "UNSAFE_AUTHORITY_FLAGS"

_MODIFY_PATH_MARKERS = frozenset({"validate-order", "validateorder"})
_CANCEL_PATH_MARKERS = frozenset({"cancelorder", "cancelallorders", "cancelall"})
_POSITION_MUTATION_MARKERS = frozenset({"withdraw", "transfer"})


class OrderCapabilityPrivateEndpointBoundaryError(ValueError):
    """Fail-closed boundary evaluation or validation error."""


class OrderCapabilityPrivateEndpointBoundaryVerdictKind(str, Enum):
    SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY = "SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY"
    FAIL_CLOSED = "FAIL_CLOSED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class OrderCapabilityPrivateEndpointBoundaryEvidenceSummary:
    source_contract_marker: str
    source_kind: str
    profile_mode: str
    environment: str
    evidence_correlation_id: str
    manifest_verified: bool
    endpoint_profile_paths: tuple[str, ...]
    http_methods_observed: tuple[str, ...]
    rest_base_url: str
    private_readonly_policy_pass: bool
    readonly_profile_proven: bool
    no_secret_material: bool = True
    no_network_performed: bool = True
    no_order_submission: bool = True
    no_cancel: bool = True
    no_position_mutation: bool = True


@dataclass(frozen=True)
class OrderCapabilityPrivateEndpointBoundaryPolicy:
    require_manifest_verified: bool = True
    require_readonly_profile_proven: bool = True
    require_offline_evaluator_only: bool = True
    allowed_environments: frozenset[str] = ALLOWED_ENVIRONMENTS
    forbidden_environment_markers: frozenset[str] = FORBIDDEN_ENVIRONMENT_MARKERS


@dataclass(frozen=True)
class OrderCapabilityPrivateEndpointBoundaryInput:
    evidence_summary: OrderCapabilityPrivateEndpointBoundaryEvidenceSummary
    policy: OrderCapabilityPrivateEndpointBoundaryPolicy
    expected_evidence_correlation_id: str = ""


@dataclass(frozen=True)
class OrderCapabilityPrivateEndpointBoundaryVerdict:
    verdict: OrderCapabilityPrivateEndpointBoundaryVerdictKind
    reason_codes: tuple[str, ...]
    evidence_correlation_id: str
    private_endpoint_boundary_satisfied: bool
    no_network_performed: bool
    no_secret_read: bool
    no_order_submission: bool
    no_cancel: bool
    no_position_mutation: bool
    execute_authorized: bool
    cancel_authorized: bool
    flatten_authorized: bool
    preflight_remains_blocked: bool
    live_ready: bool
    dashboard_truth_granted: bool
    no_authority_change: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _environment_forbidden(
    environment: str, policy: OrderCapabilityPrivateEndpointBoundaryPolicy
) -> bool:
    normalized = _normalize(environment)
    if not normalized:
        return True
    for marker in policy.forbidden_environment_markers:
        if marker in normalized:
            return True
    return normalized not in policy.allowed_environments


def _immutable_safety_verdict_fields(
    *,
    verdict: OrderCapabilityPrivateEndpointBoundaryVerdictKind,
    reason_codes: list[str],
    evidence_correlation_id: str,
    private_endpoint_boundary_satisfied: bool,
) -> OrderCapabilityPrivateEndpointBoundaryVerdict:
    return OrderCapabilityPrivateEndpointBoundaryVerdict(
        verdict=verdict,
        reason_codes=tuple(reason_codes),
        evidence_correlation_id=evidence_correlation_id,
        private_endpoint_boundary_satisfied=private_endpoint_boundary_satisfied,
        no_network_performed=True,
        no_secret_read=True,
        no_order_submission=True,
        no_cancel=True,
        no_position_mutation=True,
        execute_authorized=False,
        cancel_authorized=False,
        flatten_authorized=False,
        preflight_remains_blocked=True,
        live_ready=False,
        dashboard_truth_granted=False,
        no_authority_change=True,
    )


def _validate_evidence_presence(
    summary: OrderCapabilityPrivateEndpointBoundaryEvidenceSummary,
) -> list[str]:
    reasons: list[str] = []
    if not summary.source_kind.strip():
        reasons.append(REASON_MISSING_EVIDENCE_SUMMARY)
    if not summary.source_contract_marker.strip():
        reasons.append(REASON_MISSING_EVIDENCE_SUMMARY)
    return reasons


def _validate_safety_flags(
    summary: OrderCapabilityPrivateEndpointBoundaryEvidenceSummary,
) -> list[str]:
    reasons: list[str] = []
    if not summary.no_secret_material:
        reasons.append(REASON_SECRET_MATERIAL_PRESENT)
    if not summary.no_network_performed:
        reasons.append(REASON_NETWORK_PERFORMED)
    if not summary.no_order_submission:
        reasons.append(REASON_UNSAFE_AUTHORITY_FLAGS)
    if not summary.no_cancel:
        reasons.append(REASON_UNSAFE_AUTHORITY_FLAGS)
    if not summary.no_position_mutation:
        reasons.append(REASON_UNSAFE_AUTHORITY_FLAGS)
    return reasons


def _classify_endpoint_path(path: str) -> list[str]:
    reasons: list[str] = []
    lowered = path.lower()
    if path in FUTURES_ORDER_MUTATION_ENDPOINTS or "sendorder" in lowered:
        reasons.append(REASON_ORDER_ENDPOINT_PRESENT)
    for marker in _CANCEL_PATH_MARKERS:
        if marker in lowered:
            reasons.append(REASON_CANCEL_ENDPOINT_PRESENT)
            break
    for marker in _MODIFY_PATH_MARKERS:
        if marker in lowered:
            reasons.append(REASON_MODIFY_ENDPOINT_PRESENT)
            break
    for marker in _POSITION_MUTATION_MARKERS:
        if marker in lowered:
            reasons.append(REASON_POSITION_MUTATION_ENDPOINT_PRESENT)
            break
    forbidden = path_contains_forbidden_substring(path)
    if forbidden in _MODIFY_PATH_MARKERS and REASON_MODIFY_ENDPOINT_PRESENT not in reasons:
        reasons.append(REASON_MODIFY_ENDPOINT_PRESENT)
    if forbidden in _POSITION_MUTATION_MARKERS and (
        REASON_POSITION_MUTATION_ENDPOINT_PRESENT not in reasons
    ):
        reasons.append(REASON_POSITION_MUTATION_ENDPOINT_PRESENT)
    if forbidden in _CANCEL_PATH_MARKERS and REASON_CANCEL_ENDPOINT_PRESENT not in reasons:
        reasons.append(REASON_CANCEL_ENDPOINT_PRESENT)
    reasons.extend(validate_private_readonly_endpoint_path(path))
    return reasons


def _validate_endpoint_profile(
    summary: OrderCapabilityPrivateEndpointBoundaryEvidenceSummary,
) -> list[str]:
    reasons: list[str] = []
    if not summary.endpoint_profile_paths:
        reasons.append(REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED)
        return reasons
    for path in summary.endpoint_profile_paths:
        reasons.extend(_classify_endpoint_path(path))
    if set(summary.endpoint_profile_paths) - FUTURES_PRIVATE_READONLY_GET_ENDPOINTS:
        reasons.append(REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED)
    return reasons


def _validate_harness_policy(
    summary: OrderCapabilityPrivateEndpointBoundaryEvidenceSummary,
) -> list[str]:
    reasons: list[str] = []
    if summary.source_contract_marker.strip() != HARNESS_PACKAGE_MARKER:
        reasons.append(REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED)
    if not summary.private_readonly_policy_pass:
        reasons.append(REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED)
    rest_base = summary.rest_base_url.strip() or DEMO_FUTURES_REST_BASE_URL
    reasons.extend(validate_private_readonly_rest_base_url(rest_base))
    for method in summary.http_methods_observed:
        reasons.extend(validate_private_readonly_http_method(method))
    policy_result = evaluate_private_readonly_policy(
        endpoints_called=list(summary.endpoint_profile_paths),
        http_methods=list(summary.http_methods_observed) or ["GET"],
        rest_base_url=rest_base,
    )
    if not policy_result.get("private_readonly_policy_pass"):
        reasons.append(REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED)
    if summary.private_readonly_policy_pass != policy_result.get("private_readonly_policy_pass"):
        reasons.append(REASON_HARNESS_POLICY_MISMATCH)
    return reasons


def evaluate_order_capability_private_endpoint_boundary(
    inp: OrderCapabilityPrivateEndpointBoundaryInput,
) -> OrderCapabilityPrivateEndpointBoundaryVerdict:
    """Evaluate private endpoint boundary precondition without network or secrets."""
    reasons: list[str] = []
    summary = inp.evidence_summary
    policy = inp.policy

    evidence_correlation_id = summary.evidence_correlation_id.strip()
    if not evidence_correlation_id:
        reasons.append(REASON_MISSING_CORRELATION)

    reasons.extend(_validate_evidence_presence(summary))
    reasons.extend(_validate_safety_flags(summary))

    if policy.require_manifest_verified and not summary.manifest_verified:
        reasons.append(REASON_MANIFEST_NOT_VERIFIED)

    if _environment_forbidden(summary.environment, policy):
        reasons.append(REASON_LIVE_ENVIRONMENT_REJECTED)

    profile_mode = _normalize(summary.profile_mode)
    if profile_mode not in {_normalize(mode) for mode in SUPPORTED_PROFILE_MODES}:
        reasons.append(REASON_UNSUPPORTED_PROFILE)

    if policy.require_readonly_profile_proven and not summary.readonly_profile_proven:
        reasons.append(REASON_READONLY_PROFILE_NOT_PROVEN)

    if policy.require_offline_evaluator_only and not summary.no_network_performed:
        reasons.append(REASON_NETWORK_PERFORMED)

    reasons.extend(_validate_endpoint_profile(summary))
    reasons.extend(_validate_harness_policy(summary))

    if (
        inp.expected_evidence_correlation_id.strip()
        and evidence_correlation_id
        and evidence_correlation_id != inp.expected_evidence_correlation_id.strip()
    ):
        reasons.append(REASON_MISSING_CORRELATION)

    deduped_reasons = list(dict.fromkeys(reasons))
    if deduped_reasons:
        return _immutable_safety_verdict_fields(
            verdict=OrderCapabilityPrivateEndpointBoundaryVerdictKind.FAIL_CLOSED,
            reason_codes=deduped_reasons,
            evidence_correlation_id=evidence_correlation_id,
            private_endpoint_boundary_satisfied=False,
        )

    return _immutable_safety_verdict_fields(
        verdict=OrderCapabilityPrivateEndpointBoundaryVerdictKind.SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY,
        reason_codes=[],
        evidence_correlation_id=evidence_correlation_id,
        private_endpoint_boundary_satisfied=True,
    )


def map_boundary_verdict_to_cleanup_input_flag(
    verdict: OrderCapabilityPrivateEndpointBoundaryVerdict,
) -> bool:
    """Return True only when boundary is satisfied without authority elevation."""
    validate_order_capability_private_endpoint_boundary_verdict(verdict)
    return (
        verdict.verdict
        == OrderCapabilityPrivateEndpointBoundaryVerdictKind.SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY
        and verdict.private_endpoint_boundary_satisfied
        and not verdict.execute_authorized
        and not verdict.cancel_authorized
        and not verdict.flatten_authorized
    )


def serialize_order_capability_private_endpoint_boundary_verdict(
    verdict: OrderCapabilityPrivateEndpointBoundaryVerdict,
) -> dict[str, Any]:
    validate_order_capability_private_endpoint_boundary_verdict(verdict)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "verdict": verdict.verdict.value,
        "reason_codes": list(verdict.reason_codes),
        "evidence_correlation_id": verdict.evidence_correlation_id,
        "private_endpoint_boundary_satisfied": verdict.private_endpoint_boundary_satisfied,
        "no_network_performed": verdict.no_network_performed,
        "no_secret_read": verdict.no_secret_read,
        "no_order_submission": verdict.no_order_submission,
        "no_cancel": verdict.no_cancel,
        "no_position_mutation": verdict.no_position_mutation,
        "execute_authorized": verdict.execute_authorized,
        "cancel_authorized": verdict.cancel_authorized,
        "flatten_authorized": verdict.flatten_authorized,
        "preflight_remains_blocked": verdict.preflight_remains_blocked,
        "live_ready": verdict.live_ready,
        "dashboard_truth_granted": verdict.dashboard_truth_granted,
        "no_authority_change": verdict.no_authority_change,
    }
    _validate_serialized_keys(data)
    return data


def _validate_serialized_keys(data: dict[str, Any]) -> None:
    for key in data:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise OrderCapabilityPrivateEndpointBoundaryError(
                f"serialized verdict must not include forbidden key {key!r}"
            )


def validate_order_capability_private_endpoint_boundary_verdict(
    verdict: OrderCapabilityPrivateEndpointBoundaryVerdict,
) -> None:
    if (
        verdict.verdict
        == OrderCapabilityPrivateEndpointBoundaryVerdictKind.SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY
    ):
        if verdict.reason_codes:
            raise OrderCapabilityPrivateEndpointBoundaryError(
                "SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY must not include reason codes"
            )
        if not verdict.private_endpoint_boundary_satisfied:
            raise OrderCapabilityPrivateEndpointBoundaryError(
                "SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY requires private_endpoint_boundary_satisfied"
            )
    elif verdict.verdict == OrderCapabilityPrivateEndpointBoundaryVerdictKind.FAIL_CLOSED:
        if not verdict.reason_codes:
            raise OrderCapabilityPrivateEndpointBoundaryError(
                "FAIL_CLOSED must include reason codes"
            )
        if verdict.private_endpoint_boundary_satisfied:
            raise OrderCapabilityPrivateEndpointBoundaryError(
                "FAIL_CLOSED must not set private_endpoint_boundary_satisfied"
            )
    elif verdict.verdict == OrderCapabilityPrivateEndpointBoundaryVerdictKind.BLOCKED:
        if verdict.private_endpoint_boundary_satisfied:
            raise OrderCapabilityPrivateEndpointBoundaryError(
                "BLOCKED must not set private_endpoint_boundary_satisfied"
            )

    if verdict.execute_authorized or verdict.cancel_authorized or verdict.flatten_authorized:
        raise OrderCapabilityPrivateEndpointBoundaryError(REASON_UNSAFE_AUTHORITY_FLAGS)
    if not verdict.no_network_performed or not verdict.no_secret_read:
        raise OrderCapabilityPrivateEndpointBoundaryError(REASON_UNSAFE_AUTHORITY_FLAGS)
    if not verdict.no_order_submission or not verdict.no_cancel or not verdict.no_position_mutation:
        raise OrderCapabilityPrivateEndpointBoundaryError(REASON_UNSAFE_AUTHORITY_FLAGS)
    if not verdict.no_authority_change or not verdict.preflight_remains_blocked:
        raise OrderCapabilityPrivateEndpointBoundaryError(REASON_UNSAFE_AUTHORITY_FLAGS)
    if verdict.live_ready or verdict.dashboard_truth_granted:
        raise OrderCapabilityPrivateEndpointBoundaryError(REASON_UNSAFE_AUTHORITY_FLAGS)
