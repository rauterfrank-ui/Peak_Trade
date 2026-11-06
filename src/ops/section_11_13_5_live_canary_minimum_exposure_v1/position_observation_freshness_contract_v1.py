"""Offline flatten pre-send position-observation freshness contract.

Owner-ratified numeric max-age for FLATTEN_PRE_SEND_POSITION_OBSERVATION
only. Clock domain is local monotonic elapsed time sampled at local
response-received. Not venue uTime/cTime, not quote ts, not public-MD
captured_at, not UTC wall-clock, not HMAC OK-ACCESS-TIMESTAMP.

Does not GET, POST, authorize send, or prove send-time PASS.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

POSITION_OBSERVATION_FRESHNESS_POLICY = (
    "POLICY_BOUND_ENFORCEMENT_IMPLEMENTED_OFFLINE_SEND_TIME_UNPROVEN"
)
POSITION_OBSERVATION_FRESHNESS_POLICY_RATIFIED = True
POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED = True
POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS = 5000
POSITION_OBSERVATION_FRESHNESS_UNIT = "ms"
POSITION_OBSERVATION_FRESHNESS_APPLIES_TO = "FLATTEN_PRE_SEND_POSITION_OBSERVATION"
POSITION_OBSERVATION_FRESHNESS_ALSO_APPLIES_TO_POST_ACTION_READBACK = False
OBSERVATION_TIMESTAMP_FIELD = "LOCAL_RESPONSE_RECEIVED_AT"
CLOCK_DOMAIN = "LOCAL_MONOTONIC_ELAPSED_TIME"
AGE_EVALUATION_POINT = "IMMEDIATELY_BEFORE_FLATTEN_SEND_PERMIT_DECISION"
BOUNDARY_COMPARATOR = "STRICT_GREATER_THAN"
AGE_EQUAL_TO_MAX_AGE_ALLOWED = True
FAIL_CLOSED_ON_AGE_EXCEEDED = True
PRE_SEND_EVIDENCE_KIND = "FLATTEN_PRE_SEND_POSITION_OBSERVATION"
POST_ACTION_READBACK_EVIDENCE_KIND = "FLATTEN_POST_ACTION_READBACK"
Z2AN_QUOTE_LOCK_5000MS_AUTHORITY_TRANSFERRED = False
SILENT_DEFAULT_MAX_AGE_FORBIDDEN = True
DERIVE_THRESHOLD_FROM_HTTP_TIMEOUTS_FORBIDDEN = True
DERIVE_THRESHOLD_FROM_INTERVALS_FORBIDDEN = True
DERIVE_THRESHOLD_FROM_QUOTE_LOCK_FORBIDDEN = True
SAME_GET_MAY_SERVE_PRE_SEND_AND_POST_READBACK = False

REASON_FRESHNESS_UNKNOWN = "FRESHNESS_UNKNOWN"
REASON_MALFORMED_TIMESTAMP = "MALFORMED_TIMESTAMP"
REASON_NEGATIVE_AGE = "NEGATIVE_AGE"
REASON_STALE = "STALE_POSITION_OBSERVATION"
REASON_CROSS_DECISION = "CROSS_DECISION_REUSE"
REASON_ASSOCIATION_UNPROVEN = "DECISION_ASSOCIATION_UNPROVEN"
REASON_POST_ACTION_KIND = "POST_ACTION_READBACK_EVIDENCE_FORBIDDEN"
REASON_SAME_GET_DUAL_USE = "SAME_GET_CANNOT_SERVE_PRE_SEND_AND_POST_READBACK"
REASON_POST_ACTION_CONSUME = "POST_ACTION_CANNOT_CONSUME_PRE_SEND_FRESHNESS"
REASON_EVALUATION_SAMPLE_MISSING = "EVALUATION_MONOTONIC_SAMPLE_MISSING"


class LiveCanaryPositionObservationFreshnessError(RuntimeError):
    """Fail-closed position-observation freshness violation."""


@dataclass(frozen=True)
class PositionObservationFreshnessEvidenceV1:
    """Caller-supplied observation sample. Never invented by the evaluator."""

    response_received_monotonic_ms: Any = None
    decision_id: str | None = None
    evidence_kind: str = PRE_SEND_EVIDENCE_KIND
    consumed_as_post_action_readback: bool = False
    observation_get_identity: str | None = None


@dataclass(frozen=True)
class PositionObservationFreshnessVerdictV1:
    """Offline freshness classification. Not send authorization."""

    allowed: bool
    age_ms: int | None
    reject_reason: str
    applies_to: str = POSITION_OBSERVATION_FRESHNESS_APPLIES_TO

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "age_ms": self.age_ms,
            "reject_reason": self.reject_reason,
            "applies_to": self.applies_to,
        }


def default_local_monotonic_ms_v1() -> int:
    """Local monotonic elapsed time in milliseconds. Not wall-clock UTC."""
    return int(time.monotonic() * 1000)


def parse_monotonic_ms_v1(raw: Any) -> int | str:
    """Return int ms or a reject token. Bool is not a timestamp."""
    if raw is None:
        return REASON_FRESHNESS_UNKNOWN
    if isinstance(raw, bool):
        return REASON_MALFORMED_TIMESTAMP
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return REASON_FRESHNESS_UNKNOWN
        if text[0] in "+-" and text[1:].isdigit():
            return int(text)
        if text.isdigit():
            return int(text)
        return REASON_MALFORMED_TIMESTAMP
    return REASON_MALFORMED_TIMESTAMP


def _denied(reason: str, *, age_ms: int | None = None) -> PositionObservationFreshnessVerdictV1:
    return PositionObservationFreshnessVerdictV1(
        allowed=False,
        age_ms=age_ms,
        reject_reason=reason,
    )


def evaluate_position_observation_freshness_v1(
    *,
    evidence: PositionObservationFreshnessEvidenceV1 | None,
    evaluation_monotonic_ms: Any,
    current_decision_id: str | None,
) -> PositionObservationFreshnessVerdictV1:
    """Fail-closed age check. Missing caller metadata is not treated as fresh."""
    if evidence is None:
        return _denied(REASON_FRESHNESS_UNKNOWN)
    if evidence.consumed_as_post_action_readback is True:
        return _denied(REASON_POST_ACTION_CONSUME)
    kind = str(evidence.evidence_kind or "").strip()
    if kind != PRE_SEND_EVIDENCE_KIND:
        if kind == POST_ACTION_READBACK_EVIDENCE_KIND:
            return _denied(REASON_POST_ACTION_KIND)
        return _denied(REASON_POST_ACTION_KIND)

    decision = str(current_decision_id or "").strip()
    bound = str(evidence.decision_id or "").strip()
    if not decision or not bound:
        return _denied(REASON_ASSOCIATION_UNPROVEN)
    if decision != bound:
        return _denied(REASON_CROSS_DECISION)

    observation_ms = parse_monotonic_ms_v1(evidence.response_received_monotonic_ms)
    if observation_ms == REASON_FRESHNESS_UNKNOWN:
        return _denied(REASON_FRESHNESS_UNKNOWN)
    if not isinstance(observation_ms, int):
        return _denied(REASON_MALFORMED_TIMESTAMP)

    evaluation_ms = parse_monotonic_ms_v1(evaluation_monotonic_ms)
    if evaluation_ms == REASON_FRESHNESS_UNKNOWN:
        return _denied(REASON_EVALUATION_SAMPLE_MISSING)
    if not isinstance(evaluation_ms, int):
        return _denied(REASON_MALFORMED_TIMESTAMP)

    age_ms = evaluation_ms - observation_ms
    if age_ms < 0:
        return _denied(REASON_NEGATIVE_AGE, age_ms=age_ms)
    if age_ms > POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS:
        return _denied(REASON_STALE, age_ms=age_ms)
    return PositionObservationFreshnessVerdictV1(
        allowed=True,
        age_ms=age_ms,
        reject_reason="",
    )


def reject_same_get_pre_send_and_post_readback_v1(
    *,
    pre_send_get_identity: str | None,
    post_readback_get_identity: str | None,
) -> str | None:
    """Same GET identity cannot serve pre-send and post-action readback."""
    pre = str(pre_send_get_identity or "").strip()
    post = str(post_readback_get_identity or "").strip()
    if pre and post and pre == post:
        return REASON_SAME_GET_DUAL_USE
    return None


def resolve_monotonic_ms_clock_v1(
    clock: Callable[[], int] | None,
) -> Callable[[], int]:
    if clock is None:
        return default_local_monotonic_ms_v1
    return clock
