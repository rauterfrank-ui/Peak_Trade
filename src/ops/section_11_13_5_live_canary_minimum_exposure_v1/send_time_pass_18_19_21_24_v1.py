"""Fail-closed SEND_TIME_PASS_18_19_21_24 offline evaluation contract.

Named cluster residual: independently evaluate prerequisites 18, 19, 21,
and 24 as send-time predicates. Offline CASE_B close does not claim
PROVEN_AT_SEND. This module never GETs, POSTs, issues a runtime permit,
or authorizes flatten execute.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    ORDER_COUNT_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.no_additional_owner_decision_required_v1 import (
    PASS_OFFLINE_CONTRACT as PASS_OFFLINE_CONTRACT,
)

STP_IMPLEMENTATION_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SEND_TIME_PASS_18_19_21_24_MAXIMUM_SAFE_LEVERAGE_V1"
)
NAMED_REMAINING_AFTER_SEND_TIME_PASS: tuple[str, ...] = (
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT",
    "SEND_TIME_POSITION_REOBSERVATION",
    "BOUNDED_RUNTIME_PERMIT_ISSUANCE",
    "FLATTEN_EXECUTE",
    "NETWORK_SESSION",
)
NAMED_REMAINING_AFTER_SEND_TIME_PASS_SET = frozenset(NAMED_REMAINING_AFTER_SEND_TIME_PASS)
CLOSE_POSITION_MARKER = "/trade/close-position"

REASON_P25_NOT_PASS = "P25_NOT_PASS_OFFLINE_CONTRACT"
REASON_MISSING_P25 = "P25_STATUS_MISSING"
REASON_MISSING_REMAINING = "REMAINING_AFTER_SEND_TIME_PASS_SET_MISSING"
REASON_REMAINING_MISMATCH = "REMAINING_AFTER_SEND_TIME_PASS_SET_MISMATCH"
REASON_18_FLATTEN_FLOW_NOT_BOUND = "PREREQUISITE_18_FLATTEN_FLOW_NOT_BOUND"
REASON_18_REDUCE_ONLY_REQUIRED = "PREREQUISITE_18_REDUCE_ONLY_REQUIRED"
REASON_18_ORDER_COUNT_LIMIT = "PREREQUISITE_18_ORDER_COUNT_LIMIT_MUST_REMAIN_1"
REASON_18_CLOSE_POSITION_ALLOWLISTED = "PREREQUISITE_18_CLOSE_POSITION_MUST_REMAIN_FORBIDDEN"
REASON_18_DEDICATED_TRANSPORT_REQUIRED = "PREREQUISITE_18_DEDICATED_FLATTEN_TRANSPORT_REQUIRED"
REASON_18_OPEN_ORDER_CONFLICT = "PREREQUISITE_18_OPEN_ORDER_CONFLICT"
REASON_19_INSTRUMENT_MISMATCH = "PREREQUISITE_19_INSTRUMENT_SCOPE_MISMATCH"
REASON_21_DUPLICATE_POST_REQUIRED = "PREREQUISITE_21_DUPLICATE_POST_PROTECTION_REQUIRED"
REASON_21_ONE_SHOT_REQUIRED = "PREREQUISITE_21_ONE_SHOT_NO_RETRY_REQUIRED"
REASON_24_AUDIT_BOUNDARY_MISSING = "PREREQUISITE_24_AUDIT_BOUNDARY_MISSING"
REASON_24_HTTP_200_IMPLIES_SUCCESS = "PREREQUISITE_24_HTTP_200_MUST_NOT_IMPLY_FLATTEN_SUCCESS"
REASON_PROVEN_AT_SEND_CLAIM = "SEND_TIME_PASS_MUST_NOT_CLAIM_PROVEN_AT_SEND"
REASON_LIVE_AUTHORIZED_SUBSTITUTE = "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_SEND_TIME_PASS"
REASON_RUNTIME_PERMIT = "SEND_TIME_PASS_MUST_NOT_ISSUE_RUNTIME_PERMIT"
REASON_FLATTEN_EXECUTE = "SEND_TIME_PASS_MUST_NOT_AUTHORIZE_FLATTEN_EXECUTE"
REASON_NETWORK_SESSION = "SEND_TIME_PASS_MUST_NOT_AUTHORIZE_NETWORK_SESSION"
REASON_POST = "SEND_TIME_PASS_MUST_NOT_POST"
REASON_GET = "SEND_TIME_PASS_MUST_NOT_GET"
REASON_IMPLEMENTATION_GO_AS_EXECUTE = "IMPLEMENTATION_GO_USED_AS_FLATTEN_EXECUTE"
REASON_LINEAGE_MISMATCH = "SEND_TIME_PASS_PREDECESSOR_LINEAGE_MISMATCH"


class SendTimePass182124Error(RuntimeError):
    """Fail-closed SEND_TIME_PASS_18_19_21_24 contract violation."""


def _norm_items(values: Sequence[str] | Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


def close_position_endpoint_forbidden_v1() -> bool:
    return CLOSE_POSITION_MARKER in FORBIDDEN_MUTATION_ENDPOINT_MARKERS


def evaluate_send_time_pass_18_19_21_24_v1(
    *,
    p25_status: str | None,
    reduce_only: bool,
    flatten_flow_bound: bool,
    dedicated_flatten_transport: bool,
    open_order_conflict: bool,
    instrument_id: str | None,
    expected_instrument_id: str = DEFAULT_INSTRUMENT_ID,
    duplicate_post_protection: bool,
    one_shot_no_retry: bool,
    audit_boundary_present: bool,
    http_200_implies_flatten_success: bool,
    claimed_remaining_after_send_time_pass: Sequence[str] | None,
    proven_at_send_18: bool = False,
    proven_at_send_19: bool = False,
    proven_at_send_21: bool = False,
    proven_at_send_24: bool = False,
    live_authorized_claim: bool = False,
    runtime_permit_issuance_claim: bool = False,
    flatten_execute_authorized_claim: bool = False,
    network_session_authorized_claim: bool = False,
    post_performed_claim: bool = False,
    get_performed_claim: bool = False,
    flatten_execute_owner_go: str | None = None,
    predecessor_lineage_ok: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never transmits. Never issues a permit.

    Offline PASS proves the send-time evaluation contract for 18/19/21/24.
    It does not prove those predicates at an authorized send.
    """
    reasons: list[str] = []
    p25 = str(p25_status or "").strip()
    if not p25:
        reasons.append(REASON_MISSING_P25)
    elif p25 != PASS_OFFLINE_CONTRACT:
        reasons.append(REASON_P25_NOT_PASS)
    if claimed_remaining_after_send_time_pass is None:
        reasons.append(REASON_MISSING_REMAINING)
    else:
        claimed = frozenset(_norm_items(claimed_remaining_after_send_time_pass))
        if claimed != NAMED_REMAINING_AFTER_SEND_TIME_PASS_SET:
            reasons.append(REASON_REMAINING_MISMATCH)
    if flatten_flow_bound is not True:
        reasons.append(REASON_18_FLATTEN_FLOW_NOT_BOUND)
    else:
        if reduce_only is not True:
            reasons.append(REASON_18_REDUCE_ONLY_REQUIRED)
        if int(ORDER_COUNT_LIMIT) != 1:
            reasons.append(REASON_18_ORDER_COUNT_LIMIT)
        if close_position_endpoint_forbidden_v1() is not True:
            reasons.append(REASON_18_CLOSE_POSITION_ALLOWLISTED)
        if dedicated_flatten_transport is not True:
            reasons.append(REASON_18_DEDICATED_TRANSPORT_REQUIRED)
        if open_order_conflict is True:
            reasons.append(REASON_18_OPEN_ORDER_CONFLICT)
    target = str(instrument_id or "").strip()
    expected = str(expected_instrument_id or "").strip() or DEFAULT_INSTRUMENT_ID
    if not target or target != expected:
        reasons.append(REASON_19_INSTRUMENT_MISMATCH)
    if duplicate_post_protection is not True:
        reasons.append(REASON_21_DUPLICATE_POST_REQUIRED)
    if one_shot_no_retry is not True:
        reasons.append(REASON_21_ONE_SHOT_REQUIRED)
    if audit_boundary_present is not True:
        reasons.append(REASON_24_AUDIT_BOUNDARY_MISSING)
    if http_200_implies_flatten_success is True:
        reasons.append(REASON_24_HTTP_200_IMPLIES_SUCCESS)
    if (
        proven_at_send_18 is True
        or proven_at_send_19 is True
        or proven_at_send_21 is True
        or proven_at_send_24 is True
    ):
        reasons.append(REASON_PROVEN_AT_SEND_CLAIM)
    if live_authorized_claim is True:
        reasons.append(REASON_LIVE_AUTHORIZED_SUBSTITUTE)
    if runtime_permit_issuance_claim is True:
        reasons.append(REASON_RUNTIME_PERMIT)
    if flatten_execute_authorized_claim is True:
        reasons.append(REASON_FLATTEN_EXECUTE)
    if network_session_authorized_claim is True:
        reasons.append(REASON_NETWORK_SESSION)
    if post_performed_claim is True:
        reasons.append(REASON_POST)
    if get_performed_claim is True:
        reasons.append(REASON_GET)
    execute_go = str(flatten_execute_owner_go or "").strip()
    if execute_go == STP_IMPLEMENTATION_OWNER_GO:
        reasons.append(REASON_IMPLEMENTATION_GO_AS_EXECUTE)
    if predecessor_lineage_ok is not True:
        reasons.append(REASON_LINEAGE_MISMATCH)
    return (not reasons), tuple(reasons)


def canonical_remaining_after_send_time_pass_v1() -> tuple[str, ...]:
    return NAMED_REMAINING_AFTER_SEND_TIME_PASS


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("PREREQUISITE_18_PROVEN_AT_SEND") is True:
        raise SendTimePass182124Error("PROVEN_AT_SEND_18_CLAIMED")
    if payload.get("PREREQUISITE_19_PROVEN_AT_SEND") is True:
        raise SendTimePass182124Error("PROVEN_AT_SEND_19_CLAIMED")
    if payload.get("PREREQUISITE_21_PROVEN_AT_SEND") is True:
        raise SendTimePass182124Error("PROVEN_AT_SEND_21_CLAIMED")
    if payload.get("PREREQUISITE_24_PROVEN_AT_SEND") is True:
        raise SendTimePass182124Error("PROVEN_AT_SEND_24_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise SendTimePass182124Error("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise SendTimePass182124Error("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise SendTimePass182124Error("POST_CLAIMED")
