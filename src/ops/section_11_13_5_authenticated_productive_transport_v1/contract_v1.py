"""Fail-closed AUTHENTICATED_PRODUCTIVE_TRANSPORT offline contract.

Named send-time residual. Offline-closable as HMAC wiring plus header
presence and signing-input construction. Runtime authentication remains
false. Named higher-authority residuals remain unauthorized.

Does not GET, POST, flatten, set LIVE_AUTHORIZED, issue a runtime permit,
open a network session, or use live credentials.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS = "PASS_OFFLINE_CONTRACT"
APT_NAMED_AUTHENTICATED_TRANSPORT_CONTRACT_CLOSED = True
APT_AUTHENTICATED_TRANSPORT_GATE_IMPLEMENTED = True
APT_PRODUCTIVE_SIGNING_REUSE_WIRED = True
APT_AUTHENTICATION_PROVEN = False
APT_RUNTIME_PROVEN = False
NETWORK_PROVEN = False
CREDENTIAL_USE_PROVEN = False
PRIVATE_GET_PROVEN = False
POST_PROVEN = False
APT_FLATTEN_EXECUTE_AUTHORIZED = False
APT_NETWORK_SESSION_AUTHORIZED = False
APT_DOES_NOT_ISSUE_RUNTIME_PERMIT = True
APT_DOES_NOT_SET_LIVE_AUTHORIZED = True
APT_DOES_NOT_AUTHORIZE_FLATTEN = True
APT_DOES_NOT_GRANT_EXECUTION_READINESS = True
APT_DOES_NOT_AUTHORIZE_NETWORK_SESSION = True
APT_DOES_NOT_AUTHORIZE_SEND_TIME_POSITION_REOBSERVATION = True
FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE = True
STP_TEXT_REWRITTEN = False
P25_TEXT_REWRITTEN = False
P20_TEXT_REWRITTEN = False
P16_TEXT_REWRITTEN = False


class AuthenticatedProductiveTransportContractError(RuntimeError):
    """Fail-closed AUTHENTICATED_PRODUCTIVE_TRANSPORT contract violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise AuthenticatedProductiveTransportContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_AUTHENTICATED_PRODUCTIVE_TRANSPORT"
        )


def assert_runtime_authority_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("AUTHENTICATED_PRODUCTIVE_TRANSPORT_RUNTIME_PROVEN") is True:
        raise AuthenticatedProductiveTransportContractError("RUNTIME_AUTHENTICATION_CLAIMED")
    if payload.get("AUTHENTICATION_PROVEN") is True:
        raise AuthenticatedProductiveTransportContractError("AUTHENTICATION_PROVEN_CLAIMED")
    if payload.get("APT_FLATTEN_EXECUTE_AUTHORIZED") is True:
        raise AuthenticatedProductiveTransportContractError("FLATTEN_EXECUTE_CLAIMED")
    if payload.get("BOUNDED_RUNTIME_PERMIT_ISSUANCE") is True:
        raise AuthenticatedProductiveTransportContractError("RUNTIME_PERMIT_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise AuthenticatedProductiveTransportContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise AuthenticatedProductiveTransportContractError("POST_CLAIMED")
