"""Fail-closed EXECUTION_PREREQUISITE_25 no-additional-owner-decision contract.

Named dependency: no additional unstated owner decision is required after
closed numbered CASE_B contracts. Offline-closable as an exhaustion gate.
Named higher-authority residuals remain unauthorized.

Does not GET, POST, flatten, set LIVE_AUTHORIZED, issue a runtime permit,
or open a network session.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
EXECUTION_PREREQUISITE_25_STATUS = "PASS_OFFLINE_CONTRACT"
P25_NAMED_NO_ADDITIONAL_OWNER_DECISION_CONTRACT_CLOSED = True
P25_EXHAUSTION_GATE_IMPLEMENTED = True
PREREQUISITE_25_FLATTEN_EXECUTE_AUTHORIZED = False
PREREQUISITE_25_NETWORK_SESSION_AUTHORIZED = False
PREREQUISITE_25_SEND_TIME_REOBSERVATION_PROVEN = False
P25_DOES_NOT_ISSUE_RUNTIME_PERMIT = True
P25_DOES_NOT_SET_LIVE_AUTHORIZED = True
P25_DOES_NOT_AUTHORIZE_FLATTEN = True
P25_DOES_NOT_GRANT_EXECUTION_READINESS = True
P25_DOES_NOT_AUTHORIZE_NETWORK_SESSION = True
P25_DOES_NOT_AUTHORIZE_SEND_TIME_PASS = True
FAIL_CLOSED_IF_PREREQUISITE_25_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE = True
P20_TEXT_REWRITTEN = False
P16_TEXT_REWRITTEN = False


class NoAdditionalOwnerDecisionContractError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_25 contract violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise NoAdditionalOwnerDecisionContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_NO_ADDITIONAL_OWNER_DECISION"
        )


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("PREREQUISITE_25_FLATTEN_EXECUTE_AUTHORIZED") is True:
        raise NoAdditionalOwnerDecisionContractError("FLATTEN_EXECUTE_CLAIMED")
    if payload.get("PREREQUISITE_25_NETWORK_SESSION_AUTHORIZED") is True:
        raise NoAdditionalOwnerDecisionContractError("NETWORK_SESSION_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise NoAdditionalOwnerDecisionContractError("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise NoAdditionalOwnerDecisionContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise NoAdditionalOwnerDecisionContractError("POST_CLAIMED")
