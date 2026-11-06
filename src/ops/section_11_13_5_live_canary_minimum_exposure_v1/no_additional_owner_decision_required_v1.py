"""Fail-closed EXECUTION_PREREQUISITE_25 no-additional-owner-decision contract.

Named dependency: after closed numbered CASE_B contracts, no additional
unstated owner decision is required at the numbered-prerequisite layer.
Already-named higher-authority residuals remain separate. This module never
GETs, POSTs, issues a runtime permit, or authorizes flatten execute.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)

P25_IMPLEMENTATION_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION"
    "_REQUIRED_MAXIMUM_SAFE_LEVERAGE_V1"
)
PASS_OFFLINE_CONTRACT = "PASS_OFFLINE_CONTRACT"
NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES: tuple[str, ...] = (
    "SEND_TIME_PASS_18_19_21_24",
    "AUTHENTICATED_PRODUCTIVE_TRANSPORT",
    "SEND_TIME_POSITION_REOBSERVATION",
    "BOUNDED_RUNTIME_PERMIT_ISSUANCE",
    "FLATTEN_EXECUTE",
    "NETWORK_SESSION",
)
NAMED_REMAINING_HIGHER_AUTHORITY_SET = frozenset(NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES)

REASON_P16_NOT_PASS = "P16_NOT_PASS_OFFLINE_CONTRACT"
REASON_P20_NOT_PASS = "P20_NOT_PASS_OFFLINE_CONTRACT"
REASON_MISSING_P16 = "P16_STATUS_MISSING"
REASON_MISSING_P20 = "P20_STATUS_MISSING"
REASON_MISSING_REMAINING = "REMAINING_HIGHER_AUTHORITY_SET_MISSING"
REASON_ADDITIONAL_PRESENT = "ADDITIONAL_OWNER_DECISION_PRESENT"
REASON_REMAINING_MISMATCH = "REMAINING_HIGHER_AUTHORITY_SET_MISMATCH"
REASON_LIVE_AUTHORIZED_SUBSTITUTE = (
    "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_NO_ADDITIONAL_OWNER_DECISION"
)
REASON_RUNTIME_PERMIT = "P25_MUST_NOT_ISSUE_RUNTIME_PERMIT"
REASON_FLATTEN_EXECUTE = "P25_MUST_NOT_AUTHORIZE_FLATTEN_EXECUTE"
REASON_NETWORK_SESSION = "P25_MUST_NOT_AUTHORIZE_NETWORK_SESSION"
REASON_POST = "P25_MUST_NOT_POST"
REASON_GET = "P25_MUST_NOT_GET"
REASON_IMPLEMENTATION_GO_AS_EXECUTE = "IMPLEMENTATION_GO_USED_AS_FLATTEN_EXECUTE"
REASON_INSTRUMENT_MISMATCH = "P25_INSTRUMENT_SCOPE_MISMATCH"
REASON_LINEAGE_MISMATCH = "P25_PREDECESSOR_LINEAGE_MISMATCH"


class NoAdditionalOwnerDecisionRequiredError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_25 contract violation."""


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


def evaluate_no_additional_owner_decision_required_v1(
    *,
    p16_status: str | None,
    p20_status: str | None,
    additional_owner_decisions: Sequence[str] | None,
    claimed_remaining_higher_authority: Sequence[str] | None,
    live_authorized_claim: bool = False,
    runtime_permit_issuance_claim: bool = False,
    flatten_execute_authorized_claim: bool = False,
    network_session_authorized_claim: bool = False,
    post_performed_claim: bool = False,
    get_performed_claim: bool = False,
    flatten_execute_owner_go: str | None = None,
    instrument_id: str | None = None,
    expected_instrument_id: str = DEFAULT_INSTRUMENT_ID,
    predecessor_lineage_ok: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never transmits. Never issues a permit.

    A later send still needs send-time pass 18/19/21/24, authenticated
    productive transport, send-time position reobservation, bounded runtime
    permit issuance, flatten-execute Owner-GO, and network-session
    authorization. An offline PASS is not that authority.
    """
    reasons: list[str] = []
    p16 = str(p16_status or "").strip()
    p20 = str(p20_status or "").strip()
    if not p16:
        reasons.append(REASON_MISSING_P16)
    elif p16 != PASS_OFFLINE_CONTRACT:
        reasons.append(REASON_P16_NOT_PASS)
    if not p20:
        reasons.append(REASON_MISSING_P20)
    elif p20 != PASS_OFFLINE_CONTRACT:
        reasons.append(REASON_P20_NOT_PASS)
    if claimed_remaining_higher_authority is None:
        reasons.append(REASON_MISSING_REMAINING)
    else:
        claimed = frozenset(_norm_items(claimed_remaining_higher_authority))
        if claimed != NAMED_REMAINING_HIGHER_AUTHORITY_SET:
            reasons.append(REASON_REMAINING_MISMATCH)
    additional = _norm_items(additional_owner_decisions)
    if additional:
        reasons.append(REASON_ADDITIONAL_PRESENT)
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
    if execute_go == P25_IMPLEMENTATION_OWNER_GO:
        reasons.append(REASON_IMPLEMENTATION_GO_AS_EXECUTE)
    target = str(instrument_id or "").strip()
    expected = str(expected_instrument_id or "").strip() or DEFAULT_INSTRUMENT_ID
    if target and target != expected:
        reasons.append(REASON_INSTRUMENT_MISMATCH)
    if predecessor_lineage_ok is not True:
        reasons.append(REASON_LINEAGE_MISMATCH)
    return (not reasons), tuple(reasons)


def canonical_remaining_higher_authority_v1() -> tuple[str, ...]:
    return NAMED_REMAINING_HIGHER_AUTHORITY_BOUNDARIES


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("PREREQUISITE_25_FLATTEN_EXECUTE_AUTHORIZED") is True:
        raise NoAdditionalOwnerDecisionRequiredError("FLATTEN_EXECUTE_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise NoAdditionalOwnerDecisionRequiredError("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise NoAdditionalOwnerDecisionRequiredError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise NoAdditionalOwnerDecisionRequiredError("POST_CLAIMED")
