"""Fail-closed SEND_TIME_PASS_18_19_21_24 offline evaluation contract.

Named cluster residual. Offline-closable as a send-time evaluation gate.
PROVEN_AT_SEND remains false. Named higher-authority residuals remain
unauthorized.

Does not GET, POST, flatten, set LIVE_AUTHORIZED, issue a runtime permit,
or open a network session.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
SEND_TIME_PASS_18_19_21_24_STATUS = "PASS_OFFLINE_CONTRACT"
STP_NAMED_SEND_TIME_EVALUATION_CONTRACT_CLOSED = True
STP_SEND_TIME_EVALUATION_GATE_IMPLEMENTED = True
PREREQUISITE_18_PROVEN_AT_SEND = False
PREREQUISITE_19_PROVEN_AT_SEND = False
PREREQUISITE_21_PROVEN_AT_SEND = False
PREREQUISITE_24_PROVEN_AT_SEND = False
STP_FLATTEN_EXECUTE_AUTHORIZED = False
STP_NETWORK_SESSION_AUTHORIZED = False
STP_SEND_TIME_REOBSERVATION_PROVEN = False
STP_DOES_NOT_ISSUE_RUNTIME_PERMIT = True
STP_DOES_NOT_SET_LIVE_AUTHORIZED = True
STP_DOES_NOT_AUTHORIZE_FLATTEN = True
STP_DOES_NOT_GRANT_EXECUTION_READINESS = True
STP_DOES_NOT_AUTHORIZE_NETWORK_SESSION = True
STP_DOES_NOT_AUTHORIZE_AUTHENTICATED_PRODUCTIVE_TRANSPORT = True
FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE = True
P25_TEXT_REWRITTEN = False
P20_TEXT_REWRITTEN = False
P16_TEXT_REWRITTEN = False


class SendTimePass182124ContractError(RuntimeError):
    """Fail-closed SEND_TIME_PASS_18_19_21_24 contract violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise SendTimePass182124ContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_SEND_TIME_PASS"
        )


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("PREREQUISITE_18_PROVEN_AT_SEND") is True:
        raise SendTimePass182124ContractError("PROVEN_AT_SEND_18_CLAIMED")
    if payload.get("STP_FLATTEN_EXECUTE_AUTHORIZED") is True:
        raise SendTimePass182124ContractError("FLATTEN_EXECUTE_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise SendTimePass182124ContractError("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise SendTimePass182124ContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise SendTimePass182124ContractError("POST_CLAIMED")
