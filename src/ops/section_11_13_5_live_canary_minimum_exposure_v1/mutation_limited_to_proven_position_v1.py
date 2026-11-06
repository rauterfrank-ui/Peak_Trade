"""Fail-closed EXECUTION_PREREQUISITE_20 mutation-limited-to-proven-position.

The mutation object is the venue-native flatten Place Order body. It must
be derived from and limited to one proven nonzero target position. Global
LIVE_AUTHORIZED cannot substitute. This module never GETs, POSTs, issues a
runtime permit, or authorizes flatten execute.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
    observe_target_position_flatten_candidate_v1,
)

REASON_NO_PROVEN_POSITION = "FAIL_NO_PROVEN_POSITION"
REASON_ZERO_POSITION = "ZERO_POSITION_REJECTED"
REASON_MUTATION_BODY_MISSING = "MUTATION_BODY_MISSING"
REASON_INSTRUMENT_MISMATCH = "MUTATION_INSTRUMENT_NOT_PROVEN_POSITION"
REASON_PARTIAL = "PARTIAL_FLATTEN_FORBIDDEN"
REASON_OVERSIZE = "OVERSIZE_FLATTEN"
REASON_SIDE_MISMATCH = "FLATTEN_SIDE_NOT_PROVEN_POSITION"
REASON_SZ_UNPARSEABLE = "MUTATION_SZ_UNPARSEABLE"
REASON_LIVE_AUTHORIZED_SUBSTITUTE = "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_PROVEN_POSITION"


class MutationLimitedToProvenPositionError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_20 contract violation."""


def _sz_decimal(raw: Any) -> Decimal | None:
    text = str(raw if raw is not None else "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        return None


def evaluate_mutation_limited_to_proven_position_v1(
    *,
    positions_payload: Mapping[str, Any] | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    mutation_body: Mapping[str, Any] | None,
    live_authorized_claim: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never transmits. Never issues a permit.

    A later send-time request still needs a fresh proven position. A matching
    offline fixture body is not productive flatten authorization.
    """
    reasons: list[str] = []
    target = str(instrument_id or "").strip()
    if live_authorized_claim is True and mutation_body is None:
        reasons.append(REASON_LIVE_AUTHORIZED_SUBSTITUTE)
    classified = classify_target_position_state_v1(
        positions_payload=positions_payload,
        instrument_id=target or DEFAULT_INSTRUMENT_ID,
    )
    if classified.state == TARGET_POSITION_ZERO_PROVEN:
        reasons.append(REASON_ZERO_POSITION)
        return False, tuple(reasons)
    if classified.state != TARGET_POSITION_NONZERO_PROVEN:
        reasons.append(REASON_NO_PROVEN_POSITION)
        if live_authorized_claim is True and REASON_LIVE_AUTHORIZED_SUBSTITUTE not in reasons:
            reasons.append(REASON_LIVE_AUTHORIZED_SUBSTITUTE)
        return False, tuple(reasons)
    if not isinstance(mutation_body, Mapping) or not mutation_body:
        reasons.append(REASON_MUTATION_BODY_MISSING)
        if live_authorized_claim is True and REASON_LIVE_AUTHORIZED_SUBSTITUTE not in reasons:
            reasons.append(REASON_LIVE_AUTHORIZED_SUBSTITUTE)
        return False, tuple(reasons)
    try:
        observed = observe_target_position_flatten_candidate_v1(
            positions_payload=positions_payload or {},
            instrument_id=classified.instrument_id,
        )
    except LiveCanaryPositionObservationError as exc:
        reasons.append(REASON_NO_PROVEN_POSITION)
        reasons.append(str(exc))
        return False, tuple(reasons)
    body_inst = str(mutation_body.get("instId") or "").strip()
    if body_inst != observed.instrument_id or body_inst != target:
        reasons.append(REASON_INSTRUMENT_MISMATCH)
    body_side = str(mutation_body.get("side") or "").strip().upper()
    if body_side != observed.candidate_flatten_side:
        reasons.append(REASON_SIDE_MISMATCH)
    body_sz = _sz_decimal(mutation_body.get("sz"))
    if body_sz is None:
        reasons.append(REASON_SZ_UNPARSEABLE)
    else:
        if body_sz < observed.candidate_flatten_qty:
            reasons.append(REASON_PARTIAL)
        if body_sz > observed.candidate_flatten_qty:
            reasons.append(REASON_OVERSIZE)
    return (not reasons), tuple(reasons)
