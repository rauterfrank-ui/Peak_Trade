"""Fail-closed SEND_TIME_POSITION_REOBSERVATION offline contract.

Named send-time residual. Offline-closable as the reobservation evaluation
gate: target-instrument binding, freshness, empty-data-not-zero, zero vs
nonzero, historical-reuse deny, and no-wire fake producer. Runtime GET
and PROVEN_AT_SEND remain false. Named higher-authority residuals remain
unauthorized.

Does not GET, POST, flatten, set LIVE_AUTHORIZED, issue a runtime permit,
or open a network session.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
SEND_TIME_POSITION_REOBSERVATION_STATUS = "PASS_OFFLINE_CONTRACT"
STPR_NAMED_REOBSERVATION_CONTRACT_CLOSED = True
STPR_REOBSERVATION_GATE_IMPLEMENTED = True
STPR_RUNTIME_PROVEN = False
STPR_OBSERVATION_RUNTIME_PROVEN = False
NETWORK_PROVEN = False
CREDENTIAL_USE_PROVEN = False
PRIVATE_GET_PROVEN = False
POST_PROVEN = False
PREREQUISITE_18_PROVEN_AT_SEND = False
PREREQUISITE_19_PROVEN_AT_SEND = False
PREREQUISITE_21_PROVEN_AT_SEND = False
PREREQUISITE_24_PROVEN_AT_SEND = False
STPR_FLATTEN_EXECUTE_AUTHORIZED = False
STPR_NETWORK_SESSION_AUTHORIZED = False
STPR_DOES_NOT_ISSUE_RUNTIME_PERMIT = True
STPR_DOES_NOT_SET_LIVE_AUTHORIZED = True
STPR_DOES_NOT_AUTHORIZE_FLATTEN = True
STPR_DOES_NOT_GRANT_EXECUTION_READINESS = True
STPR_DOES_NOT_AUTHORIZE_NETWORK_SESSION = True
STPR_DOES_NOT_AUTHORIZE_BOUNDED_RUNTIME_PERMIT_ISSUANCE = True
FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE = True
FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE = True
APT_TEXT_REWRITTEN = False
STP_TEXT_REWRITTEN = False
P25_TEXT_REWRITTEN = False
P20_TEXT_REWRITTEN = False
P16_TEXT_REWRITTEN = False
POSITION_GET_REQUIRED_THIS_PERSIST = False
POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO = False


class SendTimePositionReobservationContractError(RuntimeError):
    """Fail-closed SEND_TIME_POSITION_REOBSERVATION contract violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise SendTimePositionReobservationContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_SEND_TIME_POSITION_REOBSERVATION"
        )


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN") is True:
        raise SendTimePositionReobservationContractError("RUNTIME_OBSERVATION_CLAIMED")
    if payload.get("STPR_FLATTEN_EXECUTE_AUTHORIZED") is True:
        raise SendTimePositionReobservationContractError("FLATTEN_EXECUTE_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise SendTimePositionReobservationContractError("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise SendTimePositionReobservationContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise SendTimePositionReobservationContractError("POST_CLAIMED")
    if payload.get("PREREQUISITE_18_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationContractError("PROVEN_AT_SEND_18_CLAIMED")
    if payload.get("PREREQUISITE_19_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationContractError("PROVEN_AT_SEND_19_CLAIMED")
    if payload.get("PREREQUISITE_21_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationContractError("PROVEN_AT_SEND_21_CLAIMED")
    if payload.get("PREREQUISITE_24_PROVEN_AT_SEND") is True:
        raise SendTimePositionReobservationContractError("PROVEN_AT_SEND_24_CLAIMED")
