"""Order-Capability KillSwitch/abort binding contract (v1).

Pure offline evaluation of KillSwitch snapshot DTOs against payload safety summaries.
Does not authorize orders, network, live, preflight lift, or execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

PACKAGE_MARKER = "ORDER_CAPABILITY_KILLSWITCH_ABORT_BINDING_CONTRACT_V1=true"
SCHEMA_VERSION = "order_capability_killswitch_abort_binding_result.v1"
DEFAULT_ABORT_ACK_MARKER = "CONFIRMED"

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
PASS_KILLSWITCH_STATES = frozenset(
    {
        "OK",
        "ARMED_SAFE",
        "CLEAR",
    }
)
FAIL_KILLSWITCH_STATES = frozenset(
    {
        "TRIPPED",
        "STOPPED",
        "BLOCKED",
        "UNKNOWN",
        "MISSING",
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

REASON_MISSING_KILLSWITCH_SOURCE = "MISSING_KILLSWITCH_SOURCE"
REASON_STALE_KILLSWITCH_SOURCE = "STALE_KILLSWITCH_SOURCE"
REASON_KILLSWITCH_TRIPPED = "KILLSWITCH_TRIPPED"
REASON_KILLSWITCH_STATE_UNKNOWN = "KILLSWITCH_STATE_UNKNOWN"
REASON_LIVE_ENVIRONMENT_REJECTED = "LIVE_ENVIRONMENT_REJECTED"
REASON_TOKEN_MISMATCH = "TOKEN_MISMATCH"
REASON_ABORT_ACK_NOT_CONFIRMED = "ABORT_ACK_NOT_CONFIRMED"
REASON_PAYLOAD_UNSAFE_FLAGS = "PAYLOAD_UNSAFE_FLAGS"
REASON_CORRELATION_MISMATCH = "CORRELATION_MISMATCH"
REASON_MISSING_EVIDENCE_CORRELATION = "MISSING_EVIDENCE_CORRELATION"


class OrderCapabilityAbortBindingError(ValueError):
    """Fail-closed binding evaluation or validation error."""


class OrderCapabilityBindingVerdict(str, Enum):
    BLOCKED = "BLOCKED"
    PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY = "PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class OrderCapabilityKillSwitchSnapshot:
    source: str
    source_id: str
    source_kind: str
    state: str
    observed_at_utc: str
    ttl_seconds: int
    correlation_id: str
    environment: str = ""


@dataclass(frozen=True)
class OrderCapabilityPayloadSafetySummary:
    evidence_correlation_id: str
    no_submit: bool
    no_network: bool
    execute_authorized: bool
    order_submission_executed: bool
    cancel_executed: bool
    trade_position_mutation_executed: bool
    abort_ack_marker: str
    operator_go_token_binding: str
    environment: str


@dataclass(frozen=True)
class OrderCapabilityAbortBindingInput:
    payload_summary: OrderCapabilityPayloadSafetySummary
    expected_operator_go_token_binding: str
    kill_switch_snapshot: OrderCapabilityKillSwitchSnapshot
    now_utc: str
    expected_environment: str = ""


@dataclass(frozen=True)
class OrderCapabilityAbortBindingVerdict:
    verdict: OrderCapabilityBindingVerdict
    reason_codes: tuple[str, ...]
    evidence_correlation_id: str
    snapshot_age_seconds: float | None
    no_authority_change: bool
    execute_authorized: bool
    order_submission_executed: bool
    cancel_executed: bool
    trade_position_mutation_executed: bool
    preflight_remains_blocked: bool
    live_ready: bool
    dashboard_truth_granted: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _normalize_state(state: str) -> str:
    return state.strip().upper().replace(" ", "_")


def _parse_utc_timestamp(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        raise OrderCapabilityAbortBindingError("timestamp must be non-empty")
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


def _immutable_safety_verdict_fields(
    *,
    verdict: OrderCapabilityBindingVerdict,
    reason_codes: list[str],
    evidence_correlation_id: str,
    snapshot_age_seconds: float | None,
) -> OrderCapabilityAbortBindingVerdict:
    return OrderCapabilityAbortBindingVerdict(
        verdict=verdict,
        reason_codes=tuple(reason_codes),
        evidence_correlation_id=evidence_correlation_id,
        snapshot_age_seconds=snapshot_age_seconds,
        no_authority_change=True,
        execute_authorized=False,
        order_submission_executed=False,
        cancel_executed=False,
        trade_position_mutation_executed=False,
        preflight_remains_blocked=True,
        live_ready=False,
        dashboard_truth_granted=False,
    )


def _validate_snapshot(snapshot: OrderCapabilityKillSwitchSnapshot) -> list[str]:
    reasons: list[str] = []
    if not snapshot.source.strip():
        reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)
    if not snapshot.source_id.strip():
        reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)
    if not snapshot.source_kind.strip():
        reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)
    if not snapshot.state.strip():
        reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)
    if not snapshot.observed_at_utc.strip():
        reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)
    if not snapshot.correlation_id.strip():
        reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)
    if snapshot.ttl_seconds <= 0:
        reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)
    return reasons


def _validate_killswitch_state(state: str) -> list[str]:
    normalized = _normalize_state(state)
    if not normalized:
        return [REASON_MISSING_KILLSWITCH_SOURCE]
    if normalized in FAIL_KILLSWITCH_STATES:
        if normalized in {"UNKNOWN", "MISSING"}:
            return [REASON_KILLSWITCH_STATE_UNKNOWN]
        return [REASON_KILLSWITCH_TRIPPED]
    if normalized not in PASS_KILLSWITCH_STATES:
        return [REASON_KILLSWITCH_STATE_UNKNOWN]
    return []


def _validate_payload_safety(summary: OrderCapabilityPayloadSafetySummary) -> list[str]:
    reasons: list[str] = []
    if not summary.no_submit or not summary.no_network:
        reasons.append(REASON_PAYLOAD_UNSAFE_FLAGS)
    if summary.execute_authorized:
        reasons.append(REASON_PAYLOAD_UNSAFE_FLAGS)
    if summary.order_submission_executed:
        reasons.append(REASON_PAYLOAD_UNSAFE_FLAGS)
    if summary.cancel_executed:
        reasons.append(REASON_PAYLOAD_UNSAFE_FLAGS)
    if summary.trade_position_mutation_executed:
        reasons.append(REASON_PAYLOAD_UNSAFE_FLAGS)
    return reasons


def evaluate_order_capability_abort_binding(
    inp: OrderCapabilityAbortBindingInput,
) -> OrderCapabilityAbortBindingVerdict:
    """Evaluate KillSwitch/abort binding against payload safety summary."""
    reasons: list[str] = []
    summary = inp.payload_summary
    snapshot = inp.kill_switch_snapshot

    evidence_correlation_id = summary.evidence_correlation_id.strip()
    if not evidence_correlation_id:
        reasons.append(REASON_MISSING_EVIDENCE_CORRELATION)

    reasons.extend(_validate_snapshot(snapshot))

    snapshot_age: float | None = None
    if snapshot.observed_at_utc.strip() and inp.now_utc.strip():
        try:
            snapshot_age = _snapshot_age_seconds(snapshot.observed_at_utc, inp.now_utc)
            if snapshot.ttl_seconds > 0 and snapshot_age > snapshot.ttl_seconds:
                reasons.append(REASON_STALE_KILLSWITCH_SOURCE)
        except (OrderCapabilityAbortBindingError, ValueError):
            reasons.append(REASON_MISSING_KILLSWITCH_SOURCE)

    reasons.extend(_validate_killswitch_state(snapshot.state))

    for environment in (
        summary.environment,
        snapshot.environment,
        inp.expected_environment,
    ):
        if environment.strip() and _environment_forbidden(environment):
            reasons.append(REASON_LIVE_ENVIRONMENT_REJECTED)

    if not summary.operator_go_token_binding.strip():
        reasons.append(REASON_TOKEN_MISMATCH)
    elif not inp.expected_operator_go_token_binding.strip():
        reasons.append(REASON_TOKEN_MISMATCH)
    elif summary.operator_go_token_binding.strip() != inp.expected_operator_go_token_binding.strip():
        reasons.append(REASON_TOKEN_MISMATCH)

    if _normalize(summary.abort_ack_marker) != _normalize(DEFAULT_ABORT_ACK_MARKER):
        reasons.append(REASON_ABORT_ACK_NOT_CONFIRMED)

    reasons.extend(_validate_payload_safety(summary))

    if (
        evidence_correlation_id
        and snapshot.correlation_id.strip()
        and evidence_correlation_id != snapshot.correlation_id.strip()
    ):
        reasons.append(REASON_CORRELATION_MISMATCH)

    deduped_reasons = list(dict.fromkeys(reasons))
    if deduped_reasons:
        return _immutable_safety_verdict_fields(
            verdict=OrderCapabilityBindingVerdict.FAIL_CLOSED,
            reason_codes=deduped_reasons,
            evidence_correlation_id=evidence_correlation_id,
            snapshot_age_seconds=snapshot_age,
        )

    return _immutable_safety_verdict_fields(
        verdict=OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY,
        reason_codes=[],
        evidence_correlation_id=evidence_correlation_id,
        snapshot_age_seconds=snapshot_age,
    )


def serialize_order_capability_abort_binding_verdict(
    verdict: OrderCapabilityAbortBindingVerdict,
) -> dict[str, Any]:
    validate_order_capability_abort_binding_verdict(verdict)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "verdict": verdict.verdict.value,
        "reason_codes": list(verdict.reason_codes),
        "evidence_correlation_id": verdict.evidence_correlation_id,
        "snapshot_age_seconds": verdict.snapshot_age_seconds,
        "no_submit": True,
        "no_network": True,
        "no_authority_change": verdict.no_authority_change,
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
            raise OrderCapabilityAbortBindingError(
                f"serialized verdict must not include forbidden key {key!r}"
            )


def validate_order_capability_abort_binding_verdict(
    verdict: OrderCapabilityAbortBindingVerdict,
) -> None:
    if verdict.verdict == OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY:
        if verdict.reason_codes:
            raise OrderCapabilityAbortBindingError(
                "PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY must not include reason codes"
            )
    elif verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED:
        if not verdict.reason_codes:
            raise OrderCapabilityAbortBindingError("FAIL_CLOSED must include reason codes")
    if verdict.execute_authorized:
        raise OrderCapabilityAbortBindingError("execute_authorized must remain false")
    if verdict.order_submission_executed or verdict.cancel_executed:
        raise OrderCapabilityAbortBindingError(
            "order_submission_executed and cancel_executed must remain false"
        )
    if verdict.trade_position_mutation_executed:
        raise OrderCapabilityAbortBindingError(
            "trade_position_mutation_executed must remain false"
        )
    if not verdict.no_authority_change or not verdict.preflight_remains_blocked:
        raise OrderCapabilityAbortBindingError(
            "no_authority_change and preflight_remains_blocked must remain true"
        )
    if verdict.live_ready or verdict.dashboard_truth_granted:
        raise OrderCapabilityAbortBindingError(
            "live_ready and dashboard_truth_granted must remain false"
        )
