"""Order-Capability cancel/cleanup fail-closed contract (v1).

Pure offline evaluation of cleanup readiness against payload, abort binding, and order
state snapshots. Does not authorize cancel, flatten, network, live, preflight lift, or
execute.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

PACKAGE_MARKER = "ORDER_CAPABILITY_CANCEL_CLEANUP_FAILCLOSED_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_cancel_cleanup_result.v1"
DEFAULT_CLEANUP_PLACEHOLDER_MARKER = "CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED"
ABORT_BINDING_PASS_VERDICT = "PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY"

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
READY_ORDER_STATES = frozenset(
    {
        "NONE",
        "CANCELLED",
        "REJECTED",
        "EXPIRED",
    }
)
OPEN_ORDER_STATES = frozenset(
    {
        "CREATED",
        "SUBMITTED",
        "ACKNOWLEDGED",
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

REASON_MISSING_PAYLOAD_CORRELATION = "MISSING_PAYLOAD_CORRELATION"
REASON_ABORT_BINDING_NOT_READY = "ABORT_BINDING_NOT_READY"
REASON_MISSING_ORDER_STATE_SOURCE = "MISSING_ORDER_STATE_SOURCE"
REASON_STALE_ORDER_STATE_SNAPSHOT = "STALE_ORDER_STATE_SNAPSHOT"
REASON_LIVE_ENVIRONMENT_REJECTED = "LIVE_ENVIRONMENT_REJECTED"
REASON_CLEANUP_TOKEN_MISMATCH = "CLEANUP_TOKEN_MISMATCH"
REASON_MISSING_CLEANUP_CORRELATION_MARKER = "MISSING_CLEANUP_CORRELATION_MARKER"
REASON_ENDPOINT_BOUNDARY_NOT_SATISFIED = "ENDPOINT_BOUNDARY_NOT_SATISFIED"
REASON_UNKNOWN_ORDER_STATE = "UNKNOWN_ORDER_STATE"
REASON_PARTIAL_FILL_WITHOUT_NO_MUTATION_POLICY = "PARTIAL_FILL_WITHOUT_NO_MUTATION_POLICY"
REASON_FILLED_STATE_REQUIRES_FLATTEN = "FILLED_STATE_REQUIRES_FLATTEN"
REASON_CORRELATION_MISMATCH = "CORRELATION_MISMATCH"
REASON_IDEMPOTENCY_MISMATCH = "IDEMPOTENCY_MISMATCH"
REASON_MISSING_EVIDENCE_CORRELATION = "MISSING_EVIDENCE_CORRELATION"
REASON_UNSAFE_PAYLOAD_OR_BINDING_FLAGS = "UNSAFE_PAYLOAD_OR_BINDING_FLAGS"
REASON_CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED = "CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED"


class OrderCapabilityCleanupError(ValueError):
    """Fail-closed cleanup evaluation or validation error."""


class OrderCapabilityCleanupVerdictKind(str, Enum):
    BLOCKED = "BLOCKED"
    READY_FOR_DRY_CLEANUP_PLAN_ONLY = "READY_FOR_DRY_CLEANUP_PLAN_ONLY"
    FAIL_CLOSED = "FAIL_CLOSED"


class OrderCapabilityOrderState(str, Enum):
    NONE = "NONE"
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"


@dataclass(frozen=True)
class OrderCapabilityPayloadCleanupSummary:
    evidence_correlation_id: str
    client_order_id: str
    idempotency_key: str
    cleanup_cancel_correlation_marker: str
    operator_go_token_binding: str
    environment: str
    no_submit: bool
    no_network: bool
    execute_authorized: bool
    cancel_executed: bool
    trade_position_mutation_executed: bool


@dataclass(frozen=True)
class OrderCapabilityAbortBindingSummary:
    verdict: str
    evidence_correlation_id: str
    reason_codes: tuple[str, ...]
    execute_authorized: bool
    cancel_executed: bool


@dataclass(frozen=True)
class OrderCapabilityCleanupOrderStateSnapshot:
    source_id: str
    source_kind: str
    order_state: str
    observed_at_utc: str
    ttl_seconds: int
    environment: str
    instrument: str
    client_order_id: str
    idempotency_key: str
    evidence_correlation_id: str
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0


@dataclass(frozen=True)
class OrderCapabilityCleanupPolicy:
    allow_partial_fill_plan_without_mutation: bool = False
    require_private_endpoint_boundary_satisfied: bool = True
    require_operator_cleanup_token: bool = True
    max_snapshot_age_seconds: int = 120


@dataclass(frozen=True)
class OrderCapabilityCleanupInput:
    payload_summary: OrderCapabilityPayloadCleanupSummary
    abort_binding_summary: OrderCapabilityAbortBindingSummary
    order_state_snapshot: OrderCapabilityCleanupOrderStateSnapshot
    cleanup_policy: OrderCapabilityCleanupPolicy
    operator_cleanup_go_token_binding: str
    expected_operator_cleanup_go_token_binding: str
    expected_environment: str
    now_utc: str
    private_endpoint_boundary_satisfied: bool = False


@dataclass(frozen=True)
class OrderCapabilityCleanupVerdict:
    verdict: OrderCapabilityCleanupVerdictKind
    reason_codes: tuple[str, ...]
    evidence_correlation_id: str
    snapshot_age_seconds: float | None
    dry_cleanup_plan_id: str
    no_authority_change: bool
    cancel_authorized: bool
    flatten_authorized: bool
    execute_authorized: bool
    order_submission_executed: bool
    cancel_executed: bool
    trade_position_mutation_executed: bool
    preflight_remains_blocked: bool
    live_ready: bool
    dashboard_truth_granted: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _normalize_order_state(state: str) -> str:
    return state.strip().upper().replace(" ", "_")


def _parse_utc_timestamp(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        raise OrderCapabilityCleanupError("timestamp must be non-empty")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _environment_forbidden(environment: str) -> bool:
    normalized = _normalize(environment)
    if not normalized:
        return True
    for marker in FORBIDDEN_ENVIRONMENT_MARKERS:
        if marker in normalized:
            return True
    return normalized not in ALLOWED_ENVIRONMENTS


def _snapshot_age_seconds(observed_at_utc: str, now_utc: str) -> float:
    observed = _parse_utc_timestamp(observed_at_utc)
    now = _parse_utc_timestamp(now_utc)
    return (now - observed).total_seconds()


def _deterministic_digest(*parts: str) -> str:
    material = "|".join(parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _dry_cleanup_plan_id(evidence_correlation_id: str, idempotency_key: str) -> str:
    digest = _deterministic_digest("dry-cleanup-plan", evidence_correlation_id, idempotency_key)
    return f"occc-dryplan-{digest[:24]}"


def _immutable_safety_verdict_fields(
    *,
    verdict: OrderCapabilityCleanupVerdictKind,
    reason_codes: list[str],
    evidence_correlation_id: str,
    snapshot_age_seconds: float | None,
    idempotency_key: str = "",
) -> OrderCapabilityCleanupVerdict:
    dry_plan_id = ""
    if verdict == OrderCapabilityCleanupVerdictKind.READY_FOR_DRY_CLEANUP_PLAN_ONLY:
        dry_plan_id = _dry_cleanup_plan_id(evidence_correlation_id, idempotency_key)
    return OrderCapabilityCleanupVerdict(
        verdict=verdict,
        reason_codes=tuple(reason_codes),
        evidence_correlation_id=evidence_correlation_id,
        snapshot_age_seconds=snapshot_age_seconds,
        dry_cleanup_plan_id=dry_plan_id,
        no_authority_change=True,
        cancel_authorized=False,
        flatten_authorized=False,
        execute_authorized=False,
        order_submission_executed=False,
        cancel_executed=False,
        trade_position_mutation_executed=False,
        preflight_remains_blocked=True,
        live_ready=False,
        dashboard_truth_granted=False,
    )


def _validate_payload_correlation(payload: OrderCapabilityPayloadCleanupSummary) -> list[str]:
    reasons: list[str] = []
    if (
        not payload.evidence_correlation_id.strip()
        or not payload.client_order_id.strip()
        or not payload.idempotency_key.strip()
    ):
        reasons.append(REASON_MISSING_PAYLOAD_CORRELATION)
    return reasons


def _validate_abort_binding(binding: OrderCapabilityAbortBindingSummary) -> list[str]:
    reasons: list[str] = []
    if not binding.verdict.strip():
        reasons.append(REASON_ABORT_BINDING_NOT_READY)
        return reasons
    if binding.verdict.strip() != ABORT_BINDING_PASS_VERDICT:
        reasons.append(REASON_ABORT_BINDING_NOT_READY)
    if binding.execute_authorized or binding.cancel_executed:
        reasons.append(REASON_UNSAFE_PAYLOAD_OR_BINDING_FLAGS)
    return reasons


def _validate_order_state_source(snapshot: OrderCapabilityCleanupOrderStateSnapshot) -> list[str]:
    reasons: list[str] = []
    if not snapshot.source_id.strip() or not snapshot.source_kind.strip():
        reasons.append(REASON_MISSING_ORDER_STATE_SOURCE)
    return reasons


def _validate_payload_safety(payload: OrderCapabilityPayloadCleanupSummary) -> list[str]:
    reasons: list[str] = []
    if not payload.no_submit or not payload.no_network:
        reasons.append(REASON_UNSAFE_PAYLOAD_OR_BINDING_FLAGS)
    if payload.execute_authorized or payload.cancel_executed:
        reasons.append(REASON_UNSAFE_PAYLOAD_OR_BINDING_FLAGS)
    if payload.trade_position_mutation_executed:
        reasons.append(REASON_UNSAFE_PAYLOAD_OR_BINDING_FLAGS)
    return reasons


def _validate_cleanup_marker(payload: OrderCapabilityPayloadCleanupSummary) -> list[str]:
    reasons: list[str] = []
    marker = payload.cleanup_cancel_correlation_marker.strip()
    if not marker:
        reasons.append(REASON_MISSING_CLEANUP_CORRELATION_MARKER)
        return reasons
    if marker == DEFAULT_CLEANUP_PLACEHOLDER_MARKER:
        reasons.append(REASON_CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED)
    return reasons


def _validate_cleanup_token(inp: OrderCapabilityCleanupInput) -> list[str]:
    reasons: list[str] = []
    if not inp.cleanup_policy.require_operator_cleanup_token:
        return reasons
    if not inp.operator_cleanup_go_token_binding.strip():
        reasons.append(REASON_CLEANUP_TOKEN_MISMATCH)
    elif not inp.expected_operator_cleanup_go_token_binding.strip():
        reasons.append(REASON_CLEANUP_TOKEN_MISMATCH)
    elif (
        inp.operator_cleanup_go_token_binding.strip()
        != inp.expected_operator_cleanup_go_token_binding.strip()
    ):
        reasons.append(REASON_CLEANUP_TOKEN_MISMATCH)
    return reasons


def _validate_order_state_rules(
    snapshot: OrderCapabilityCleanupOrderStateSnapshot,
    policy: OrderCapabilityCleanupPolicy,
) -> list[str]:
    reasons: list[str] = []
    normalized = _normalize_order_state(snapshot.order_state)
    if not normalized:
        reasons.append(REASON_MISSING_ORDER_STATE_SOURCE)
        return reasons
    if normalized in {"UNKNOWN", "MISSING"}:
        reasons.append(REASON_UNKNOWN_ORDER_STATE)
        return reasons
    if normalized == "FILLED":
        reasons.append(REASON_FILLED_STATE_REQUIRES_FLATTEN)
        return reasons
    if normalized == "PARTIALLY_FILLED":
        if snapshot.filled_quantity > 0 and not policy.allow_partial_fill_plan_without_mutation:
            reasons.append(REASON_PARTIAL_FILL_WITHOUT_NO_MUTATION_POLICY)
        return reasons
    if normalized in OPEN_ORDER_STATES:
        reasons.append(REASON_ABORT_BINDING_NOT_READY)
        return reasons
    if normalized not in READY_ORDER_STATES:
        reasons.append(REASON_UNKNOWN_ORDER_STATE)
    return reasons


def evaluate_order_capability_cancel_cleanup(
    inp: OrderCapabilityCleanupInput,
) -> OrderCapabilityCleanupVerdict:
    """Evaluate cancel/cleanup readiness without authorizing cancel or flatten."""
    reasons: list[str] = []
    payload = inp.payload_summary
    binding = inp.abort_binding_summary
    snapshot = inp.order_state_snapshot
    policy = inp.cleanup_policy

    evidence_correlation_id = payload.evidence_correlation_id.strip()
    if not evidence_correlation_id:
        reasons.append(REASON_MISSING_EVIDENCE_CORRELATION)

    reasons.extend(_validate_payload_correlation(payload))
    reasons.extend(_validate_abort_binding(binding))
    reasons.extend(_validate_order_state_source(snapshot))
    reasons.extend(_validate_payload_safety(payload))
    reasons.extend(_validate_cleanup_marker(payload))
    reasons.extend(_validate_cleanup_token(inp))

    if (
        policy.require_private_endpoint_boundary_satisfied
        and not inp.private_endpoint_boundary_satisfied
    ):
        reasons.append(REASON_ENDPOINT_BOUNDARY_NOT_SATISFIED)

    snapshot_age: float | None = None
    if snapshot.observed_at_utc.strip() and inp.now_utc.strip():
        try:
            snapshot_age = _snapshot_age_seconds(snapshot.observed_at_utc, inp.now_utc)
            max_age = (
                snapshot.ttl_seconds
                if snapshot.ttl_seconds > 0
                else policy.max_snapshot_age_seconds
            )
            if max_age > 0 and snapshot_age > max_age:
                reasons.append(REASON_STALE_ORDER_STATE_SNAPSHOT)
        except (OrderCapabilityCleanupError, ValueError):
            reasons.append(REASON_MISSING_ORDER_STATE_SOURCE)

    for environment in (
        payload.environment,
        snapshot.environment,
        inp.expected_environment,
    ):
        if environment.strip() and _environment_forbidden(environment):
            reasons.append(REASON_LIVE_ENVIRONMENT_REJECTED)

    if (
        evidence_correlation_id
        and binding.evidence_correlation_id.strip()
        and evidence_correlation_id != binding.evidence_correlation_id.strip()
    ):
        reasons.append(REASON_CORRELATION_MISMATCH)
    if (
        evidence_correlation_id
        and snapshot.evidence_correlation_id.strip()
        and evidence_correlation_id != snapshot.evidence_correlation_id.strip()
    ):
        reasons.append(REASON_CORRELATION_MISMATCH)

    if (
        payload.idempotency_key.strip()
        and snapshot.idempotency_key.strip()
        and payload.idempotency_key.strip() != snapshot.idempotency_key.strip()
    ):
        reasons.append(REASON_IDEMPOTENCY_MISMATCH)

    reasons.extend(_validate_order_state_rules(snapshot, policy))

    deduped_reasons = list(dict.fromkeys(reasons))
    if deduped_reasons:
        return _immutable_safety_verdict_fields(
            verdict=OrderCapabilityCleanupVerdictKind.FAIL_CLOSED,
            reason_codes=deduped_reasons,
            evidence_correlation_id=evidence_correlation_id,
            snapshot_age_seconds=snapshot_age,
        )

    return _immutable_safety_verdict_fields(
        verdict=OrderCapabilityCleanupVerdictKind.READY_FOR_DRY_CLEANUP_PLAN_ONLY,
        reason_codes=[],
        evidence_correlation_id=evidence_correlation_id,
        snapshot_age_seconds=snapshot_age,
        idempotency_key=payload.idempotency_key.strip(),
    )


def serialize_order_capability_cleanup_verdict(
    verdict: OrderCapabilityCleanupVerdict,
) -> dict[str, Any]:
    validate_order_capability_cleanup_verdict(verdict)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "verdict": verdict.verdict.value,
        "reason_codes": list(verdict.reason_codes),
        "evidence_correlation_id": verdict.evidence_correlation_id,
        "snapshot_age_seconds": verdict.snapshot_age_seconds,
        "dry_cleanup_plan_id": verdict.dry_cleanup_plan_id,
        "no_submit": True,
        "no_network": True,
        "no_authority_change": verdict.no_authority_change,
        "cancel_authorized": verdict.cancel_authorized,
        "flatten_authorized": verdict.flatten_authorized,
        "execute_authorized": verdict.execute_authorized,
        "order_submission_executed": verdict.order_submission_executed,
        "cancel_executed": verdict.cancel_executed,
        "trade_position_mutation_executed": verdict.trade_position_mutation_executed,
        "preflight_remains_blocked": verdict.preflight_remains_blocked,
        "live_ready": verdict.live_ready,
        "dashboard_truth_granted": verdict.dashboard_truth_granted,
    }
    _validate_serialized_keys(data)
    return data


def _validate_serialized_keys(data: dict[str, Any]) -> None:
    for key in data:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise OrderCapabilityCleanupError(
                f"serialized verdict must not include forbidden key {key!r}"
            )


def validate_order_capability_cleanup_verdict(
    verdict: OrderCapabilityCleanupVerdict,
) -> None:
    if verdict.verdict == OrderCapabilityCleanupVerdictKind.READY_FOR_DRY_CLEANUP_PLAN_ONLY:
        if verdict.reason_codes:
            raise OrderCapabilityCleanupError(
                "READY_FOR_DRY_CLEANUP_PLAN_ONLY must not include reason codes"
            )
        if not verdict.dry_cleanup_plan_id.strip():
            raise OrderCapabilityCleanupError(
                "READY_FOR_DRY_CLEANUP_PLAN_ONLY must include dry_cleanup_plan_id"
            )
    elif verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED:
        if not verdict.reason_codes:
            raise OrderCapabilityCleanupError("FAIL_CLOSED must include reason codes")
    if verdict.cancel_authorized or verdict.flatten_authorized:
        raise OrderCapabilityCleanupError(
            "cancel_authorized and flatten_authorized must remain false"
        )
    if verdict.execute_authorized:
        raise OrderCapabilityCleanupError("execute_authorized must remain false")
    if verdict.order_submission_executed or verdict.cancel_executed:
        raise OrderCapabilityCleanupError(
            "order_submission_executed and cancel_executed must remain false"
        )
    if verdict.trade_position_mutation_executed:
        raise OrderCapabilityCleanupError("trade_position_mutation_executed must remain false")
    if not verdict.no_authority_change or not verdict.preflight_remains_blocked:
        raise OrderCapabilityCleanupError(
            "no_authority_change and preflight_remains_blocked must remain true"
        )
    if verdict.live_ready or verdict.dashboard_truth_granted:
        raise OrderCapabilityCleanupError(
            "live_ready and dashboard_truth_granted must remain false"
        )
