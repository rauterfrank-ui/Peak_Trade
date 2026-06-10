"""Order-Capability safety-cancel-under-KillSwitch contract (v1).

Pure offline evaluation of post-sendorder safety-cancel cleanup candidates when
KillSwitch is TRIPPED. Does not authorize cancel, network, live, preflight lift,
or execute.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

PACKAGE_MARKER = "ORDER_CAPABILITY_SAFETY_CANCEL_UNDER_KILLSWITCH_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_safety_cancel_under_killswitch_result.v1"
AUTHORITY_IMPACT = "NO_AUTHORITY_CHANGE"

LIFECYCLE_PHASE_POST_SENDORDER_CLEANUP = "post_sendorder_cleanup"
ALLOWED_CANCEL_ENDPOINT = "/cancelorder"
ALLOWED_HTTP_METHOD = "POST"
MAX_CANCEL_ATTEMPTS = 1

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
SAFETY_KILLSWITCH_STATES = frozenset(
    {
        "TRIPPED",
        "STOPPED",
        "BLOCKED",
    }
)
PASS_KILLSWITCH_CLEAR_STATES = frozenset(
    {
        "OK",
        "ARMED_SAFE",
        "CLEAR",
    }
)
CLEAR_OPEN_ORDER_STATES = frozenset(
    {
        "CREATED",
        "SUBMITTED",
        "ACKNOWLEDGED",
    }
)
AMBIGUOUS_ORDER_STATES = frozenset(
    {
        "UNKNOWN",
        "MISSING",
        "PARTIALLY_FILLED",
        "FILLED",
        "FAILED",
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

REASON_WRONG_LIFECYCLE_PHASE = "WRONG_LIFECYCLE_PHASE"
REASON_SENDORDER_NOT_ACCEPTED = "SENDORDER_NOT_ACCEPTED"
REASON_KILLSWITCH_NOT_TRIPPED = "KILLSWITCH_NOT_TRIPPED"
REASON_KILLSWITCH_STATE_AMBIGUOUS = "KILLSWITCH_STATE_AMBIGUOUS"
REASON_MISSING_INTENDED_ORDER_ID = "MISSING_INTENDED_ORDER_ID"
REASON_INTENDED_ORDER_ID_MISMATCH = "INTENDED_ORDER_ID_MISMATCH"
REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS = "FORBIDDEN_ENDPOINT_CANCELALLORDERS"
REASON_FORBIDDEN_ENDPOINT_BATCHORDER = "FORBIDDEN_ENDPOINT_BATCHORDER"
REASON_INVALID_CANCELORDER_ENDPOINT = "INVALID_CANCELORDER_ENDPOINT"
REASON_FORBIDDEN_METHOD_NOT_POST = "FORBIDDEN_METHOD_NOT_POST"
REASON_MAX_CANCEL_ATTEMPTS_EXCEEDED = "MAX_CANCEL_ATTEMPTS_EXCEEDED"
REASON_MISSING_EVIDENCE_CORRELATION = "MISSING_EVIDENCE_CORRELATION"
REASON_LIVE_ENVIRONMENT_REJECTED = "LIVE_ENVIRONMENT_REJECTED"
REASON_AMBIGUOUS_ORDER_STATE = "AMBIGUOUS_ORDER_STATE"


class OrderCapabilitySafetyCancelError(ValueError):
    """Fail-closed safety-cancel evaluation or validation error."""


class OrderCapabilitySafetyCancelVerdictKind(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY = "READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class OrderCapabilitySafetyCancelInput:
    lifecycle_phase: str
    sendorder_accepted: bool
    killswitch_state: str
    intended_order_id: str
    requested_order_id: str
    endpoint: str
    method: str
    cancel_attempts: int
    evidence_correlation_present: bool
    evidence_correlation_id: str
    environment: str
    order_state: str
    cancelallorders: bool = False
    batchorder: bool = False


@dataclass(frozen=True)
class OrderCapabilitySafetyCancelVerdict:
    status: OrderCapabilitySafetyCancelVerdictKind
    reason_codes: tuple[str, ...]
    allowed_for_execute_now: bool
    cancel_authorized_now: bool
    dry_safety_cancel_plan_candidate: bool
    intended_order_id_binding_verified: bool
    forbidden_endpoint_detected: bool
    evidence_required: bool
    authority_impact: str
    evidence_correlation_id: str
    dry_safety_cancel_plan_id: str
    no_authority_change: bool
    execute_authorized: bool
    order_submission_executed: bool
    cancel_executed: bool
    preflight_remains_blocked: bool
    live_ready: bool
    dashboard_truth_granted: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _normalize_state(state: str) -> str:
    return state.strip().upper().replace(" ", "_")


def _normalize_endpoint(endpoint: str) -> str:
    raw = endpoint.strip().lower()
    if not raw.startswith("/"):
        raw = f"/{raw}"
    return raw


def _environment_forbidden(environment: str) -> bool:
    normalized = _normalize(environment)
    if not normalized:
        return True
    for marker in FORBIDDEN_ENVIRONMENT_MARKERS:
        if marker in normalized:
            return True
    return normalized not in ALLOWED_ENVIRONMENTS


def _deterministic_digest(*parts: str) -> str:
    material = "|".join(parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _dry_safety_cancel_plan_id(evidence_correlation_id: str, intended_order_id: str) -> str:
    digest = _deterministic_digest(
        "dry-safety-cancel-plan",
        evidence_correlation_id,
        intended_order_id,
    )
    return f"ocsc-dryplan-{digest[:24]}"


def _immutable_safety_verdict_fields(
    *,
    status: OrderCapabilitySafetyCancelVerdictKind,
    reason_codes: list[str],
    evidence_correlation_id: str,
    intended_order_id_binding_verified: bool,
    forbidden_endpoint_detected: bool,
    evidence_required: bool,
    intended_order_id: str = "",
) -> OrderCapabilitySafetyCancelVerdict:
    dry_plan_id = ""
    dry_candidate = False
    if status == OrderCapabilitySafetyCancelVerdictKind.READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY:
        dry_candidate = True
        dry_plan_id = _dry_safety_cancel_plan_id(evidence_correlation_id, intended_order_id)
    return OrderCapabilitySafetyCancelVerdict(
        status=status,
        reason_codes=tuple(reason_codes),
        allowed_for_execute_now=False,
        cancel_authorized_now=False,
        dry_safety_cancel_plan_candidate=dry_candidate,
        intended_order_id_binding_verified=intended_order_id_binding_verified,
        forbidden_endpoint_detected=forbidden_endpoint_detected,
        evidence_required=evidence_required,
        authority_impact=AUTHORITY_IMPACT,
        evidence_correlation_id=evidence_correlation_id,
        dry_safety_cancel_plan_id=dry_plan_id,
        no_authority_change=True,
        execute_authorized=False,
        order_submission_executed=False,
        cancel_executed=False,
        preflight_remains_blocked=True,
        live_ready=False,
        dashboard_truth_granted=False,
    )


def _validate_lifecycle_phase(phase: str) -> list[str]:
    normalized = _normalize(phase).replace(" ", "_")
    if normalized != LIFECYCLE_PHASE_POST_SENDORDER_CLEANUP:
        return [REASON_WRONG_LIFECYCLE_PHASE]
    return []


def _validate_sendorder_accepted(accepted: bool) -> list[str]:
    if not accepted:
        return [REASON_SENDORDER_NOT_ACCEPTED]
    return []


def _validate_killswitch_state(state: str) -> list[str]:
    normalized = _normalize_state(state)
    if not normalized:
        return [REASON_KILLSWITCH_STATE_AMBIGUOUS]
    if normalized in PASS_KILLSWITCH_CLEAR_STATES:
        return [REASON_KILLSWITCH_NOT_TRIPPED]
    if normalized in SAFETY_KILLSWITCH_STATES:
        return []
    return [REASON_KILLSWITCH_STATE_AMBIGUOUS]


def _validate_intended_order_id(intended_order_id: str, requested_order_id: str) -> tuple[list[str], bool]:
    intended = intended_order_id.strip()
    requested = requested_order_id.strip()
    if not intended:
        return [REASON_MISSING_INTENDED_ORDER_ID], False
    if not requested or requested != intended:
        return [REASON_INTENDED_ORDER_ID_MISMATCH], False
    return [], True


def _validate_endpoint(
    endpoint: str,
    *,
    cancelallorders: bool,
    batchorder: bool,
) -> tuple[list[str], bool]:
    reasons: list[str] = []
    forbidden = False
    normalized = _normalize_endpoint(endpoint)

    if cancelallorders or normalized in {"/cancelallorders", "cancelallorders"}:
        reasons.append(REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS)
        forbidden = True
    if batchorder or normalized in {"/batchorder", "batchorder"}:
        reasons.append(REASON_FORBIDDEN_ENDPOINT_BATCHORDER)
        forbidden = True
    if normalized != ALLOWED_CANCEL_ENDPOINT:
        reasons.append(REASON_INVALID_CANCELORDER_ENDPOINT)
    return reasons, forbidden


def _validate_method(method: str) -> list[str]:
    if _normalize_state(method) != ALLOWED_HTTP_METHOD:
        return [REASON_FORBIDDEN_METHOD_NOT_POST]
    return []


def _validate_cancel_attempts(cancel_attempts: int) -> list[str]:
    if cancel_attempts > MAX_CANCEL_ATTEMPTS:
        return [REASON_MAX_CANCEL_ATTEMPTS_EXCEEDED]
    return []


def _validate_evidence(
    *,
    evidence_correlation_present: bool,
    evidence_correlation_id: str,
) -> tuple[list[str], bool]:
    correlation_id = evidence_correlation_id.strip()
    if not evidence_correlation_present or not correlation_id:
        return [REASON_MISSING_EVIDENCE_CORRELATION], True
    return [], True


def _validate_environment(environment: str) -> list[str]:
    if _environment_forbidden(environment):
        return [REASON_LIVE_ENVIRONMENT_REJECTED]
    return []


def _validate_order_state(order_state: str) -> list[str]:
    normalized = _normalize_state(order_state)
    if not normalized:
        return [REASON_AMBIGUOUS_ORDER_STATE]
    if normalized in AMBIGUOUS_ORDER_STATES:
        return [REASON_AMBIGUOUS_ORDER_STATE]
    if normalized not in CLEAR_OPEN_ORDER_STATES:
        return [REASON_AMBIGUOUS_ORDER_STATE]
    return []


def evaluate_order_capability_safety_cancel_under_killswitch(
    inp: OrderCapabilitySafetyCancelInput,
) -> OrderCapabilitySafetyCancelVerdict:
    """Evaluate safety-cancel cleanup candidate without authorizing cancel or execute."""
    reasons: list[str] = []
    evidence_correlation_id = inp.evidence_correlation_id.strip()

    reasons.extend(_validate_lifecycle_phase(inp.lifecycle_phase))
    reasons.extend(_validate_sendorder_accepted(inp.sendorder_accepted))
    reasons.extend(_validate_killswitch_state(inp.killswitch_state))

    order_reasons, binding_verified = _validate_intended_order_id(
        inp.intended_order_id,
        inp.requested_order_id,
    )
    reasons.extend(order_reasons)

    endpoint_reasons, forbidden_endpoint = _validate_endpoint(
        inp.endpoint,
        cancelallorders=inp.cancelallorders,
        batchorder=inp.batchorder,
    )
    reasons.extend(endpoint_reasons)

    reasons.extend(_validate_method(inp.method))
    reasons.extend(_validate_cancel_attempts(inp.cancel_attempts))

    evidence_reasons, evidence_required = _validate_evidence(
        evidence_correlation_present=inp.evidence_correlation_present,
        evidence_correlation_id=evidence_correlation_id,
    )
    reasons.extend(evidence_reasons)

    reasons.extend(_validate_environment(inp.environment))
    reasons.extend(_validate_order_state(inp.order_state))

    deduped_reasons = list(dict.fromkeys(reasons))
    if deduped_reasons:
        return _immutable_safety_verdict_fields(
            status=OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED,
            reason_codes=deduped_reasons,
            evidence_correlation_id=evidence_correlation_id,
            intended_order_id_binding_verified=binding_verified,
            forbidden_endpoint_detected=forbidden_endpoint,
            evidence_required=evidence_required,
        )

    return _immutable_safety_verdict_fields(
        status=OrderCapabilitySafetyCancelVerdictKind.READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY,
        reason_codes=[],
        evidence_correlation_id=evidence_correlation_id,
        intended_order_id_binding_verified=True,
        forbidden_endpoint_detected=False,
        evidence_required=True,
        intended_order_id=inp.intended_order_id.strip(),
    )


def serialize_order_capability_safety_cancel_verdict(
    verdict: OrderCapabilitySafetyCancelVerdict,
) -> dict[str, Any]:
    validate_order_capability_safety_cancel_verdict(verdict)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "status": verdict.status.value,
        "reason_codes": list(verdict.reason_codes),
        "allowed_for_execute_now": verdict.allowed_for_execute_now,
        "cancel_authorized_now": verdict.cancel_authorized_now,
        "dry_safety_cancel_plan_candidate": verdict.dry_safety_cancel_plan_candidate,
        "intended_order_id_binding_verified": verdict.intended_order_id_binding_verified,
        "forbidden_endpoint_detected": verdict.forbidden_endpoint_detected,
        "evidence_required": verdict.evidence_required,
        "authority_impact": verdict.authority_impact,
        "evidence_correlation_id": verdict.evidence_correlation_id,
        "dry_safety_cancel_plan_id": verdict.dry_safety_cancel_plan_id,
        "no_submit": True,
        "no_network": True,
        "no_authority_change": verdict.no_authority_change,
        "execute_authorized": verdict.execute_authorized,
        "order_submission_executed": verdict.order_submission_executed,
        "cancel_executed": verdict.cancel_executed,
        "preflight_remains_blocked": verdict.preflight_remains_blocked,
        "live_ready": verdict.live_ready,
        "dashboard_truth_granted": verdict.dashboard_truth_granted,
    }
    _validate_serialized_keys(data)
    return data


def _validate_serialized_keys(data: dict[str, Any]) -> None:
    for key in data:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise OrderCapabilitySafetyCancelError(
                f"serialized verdict must not include forbidden key {key!r}"
            )


def validate_order_capability_safety_cancel_verdict(
    verdict: OrderCapabilitySafetyCancelVerdict,
) -> None:
    if verdict.status == OrderCapabilitySafetyCancelVerdictKind.READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY:
        if verdict.reason_codes:
            raise OrderCapabilitySafetyCancelError(
                "READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY must not include reason codes"
            )
        if not verdict.dry_safety_cancel_plan_id.strip():
            raise OrderCapabilitySafetyCancelError(
                "READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY must include dry_safety_cancel_plan_id"
            )
        if not verdict.dry_safety_cancel_plan_candidate:
            raise OrderCapabilitySafetyCancelError(
                "READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY must set dry_safety_cancel_plan_candidate"
            )
        if not verdict.intended_order_id_binding_verified:
            raise OrderCapabilitySafetyCancelError(
                "READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY must verify intended_order_id binding"
            )
    elif verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED:
        if not verdict.reason_codes:
            raise OrderCapabilitySafetyCancelError("FAIL_CLOSED must include reason codes")
    if verdict.allowed_for_execute_now or verdict.cancel_authorized_now:
        raise OrderCapabilitySafetyCancelError(
            "allowed_for_execute_now and cancel_authorized_now must remain false"
        )
    if verdict.execute_authorized:
        raise OrderCapabilitySafetyCancelError("execute_authorized must remain false")
    if verdict.order_submission_executed or verdict.cancel_executed:
        raise OrderCapabilitySafetyCancelError(
            "order_submission_executed and cancel_executed must remain false"
        )
    if not verdict.no_authority_change or verdict.authority_impact != AUTHORITY_IMPACT:
        raise OrderCapabilitySafetyCancelError(
            "no_authority_change must remain true and authority_impact must be NO_AUTHORITY_CHANGE"
        )
    if not verdict.preflight_remains_blocked:
        raise OrderCapabilitySafetyCancelError("preflight_remains_blocked must remain true")
    if verdict.live_ready or verdict.dashboard_truth_granted:
        raise OrderCapabilitySafetyCancelError(
            "live_ready and dashboard_truth_granted must remain false"
        )
