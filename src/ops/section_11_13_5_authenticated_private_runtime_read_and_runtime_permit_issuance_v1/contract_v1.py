"""Fail-closed contract for authenticated private GET and runtime permit issuance.

Authorizes N11 private GET and N13 runtime permit issuance. Does not POST,
flatten, fund, unlock Live or Canary, or authorize productive flatten
network_session_authorized.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_RUNTIME_READ_AND_PERMIT_ISSUANCE"
AUTHENTICATED_PRIVATE_RUNTIME_READ_AUTHORIZED = True
RUNTIME_PERMIT_ISSUANCE_AUTHORIZED = True
PRODUCTIVE_FLATTEN_POST_AUTHORIZED = False
PRODUCTIVE_RECONCILIATION_AUTHORIZED = False
FLATTEN_EXECUTE_AUTHORIZED = False
NETWORK_SESSION_AUTHORIZED = False
POST_PROVEN = False
CENSUS_TEXT_REWRITTEN = False
STPR_TEXT_REWRITTEN = False
APT_TEXT_REWRITTEN = False
STP_TEXT_REWRITTEN = False
P16_TEXT_REWRITTEN = False
P20_TEXT_REWRITTEN = False
P25_TEXT_REWRITTEN = False
THIS_GO_DOES_NOT_AUTHORIZE_POST = True
THIS_GO_DOES_NOT_AUTHORIZE_FLATTEN = True
THIS_GO_DOES_NOT_SET_LIVE_AUTHORIZED = True
THIS_GO_DOES_NOT_AUTHORIZE_FLATTEN_NETWORK_SESSION = True
FAIL_CLOSED_IF_MARKED_FLATTEN_PROVEN_FROM_PERMIT_ALONE = True
EMPTY_DATA_IS_ZERO = False
ABSENT_TARGET_ROW_IS_ZERO = False


class AuthenticatedPrivateRuntimeReadContractError(RuntimeError):
    """Fail-closed authenticated private runtime read / permit issuance violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise AuthenticatedPrivateRuntimeReadContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_RUNTIME_PERMIT"
        )


def assert_productive_boundary_not_crossed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("POST_PERFORMED") is True:
        raise AuthenticatedPrivateRuntimeReadContractError("POST_CLAIMED")
    if payload.get("FLATTEN_EXECUTE_AUTHORIZED") is True:
        raise AuthenticatedPrivateRuntimeReadContractError("FLATTEN_EXECUTE_CLAIMED")
    if payload.get("NETWORK_SESSION_AUTHORIZED") is True:
        raise AuthenticatedPrivateRuntimeReadContractError("FLATTEN_NETWORK_SESSION_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise AuthenticatedPrivateRuntimeReadContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("CANARY_AUTHORIZED") is True:
        raise AuthenticatedPrivateRuntimeReadContractError("CANARY_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("PRODUCTIVE_FLATTEN_POST_AUTHORIZED") is True:
        raise AuthenticatedPrivateRuntimeReadContractError("PRODUCTIVE_FLATTEN_POST_CLAIMED")
    if payload.get("ORDER_SUBMIT_USED") is True:
        raise AuthenticatedPrivateRuntimeReadContractError("ORDER_SUBMIT_CLAIMED")
