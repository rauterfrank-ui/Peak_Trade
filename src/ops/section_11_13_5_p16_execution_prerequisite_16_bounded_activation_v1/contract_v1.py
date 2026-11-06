"""Fail-closed EXECUTION_PREREQUISITE_16 bounded-activation contract.

Named dependency: bounded activation without global LIVE_AUTHORIZED.
Offline-closable as a gate/permit contract. Runtime permit issuance,
network session, and flatten execute remain unauthorized.

Does not GET, POST, flatten, set LIVE_AUTHORIZED, or open a network session.
"""

from __future__ import annotations

from typing import Any, Mapping

CASE = "CASE_B_OFFLINE_CLOSABLE_CONTRACT"
EXECUTION_PREREQUISITE_16_STATUS = "PASS_OFFLINE_CONTRACT"
P16_NAMED_WITHOUT_GLOBAL_LIVE_AUTHORIZED_CONTRACT_CLOSED = True
P16_BOUNDED_ACTIVATION_PERMIT_MECHANISM_IMPLEMENTED = True
PREREQUISITE_16_BOUNDED_RUNTIME_ACTIVATION_PROVEN = False
PREREQUISITE_16_NETWORK_SESSION_AUTHORIZED = False
PREREQUISITE_16_FLATTEN_EXECUTE_AUTHORIZED = False
GLOBAL_LIVE_AUTHORIZED_REQUIRED = False
BOUNDED_ACTIVATION_NARROWER_THAN_GLOBAL_LIVE = True
P16_DOES_NOT_ISSUE_RUNTIME_PERMIT = True
P16_DOES_NOT_SET_LIVE_AUTHORIZED = True
P16_DOES_NOT_AUTHORIZE_FLATTEN = True
P16_DOES_NOT_GRANT_EXECUTION_READINESS = True
P16_DOES_NOT_AUTHORIZE_NETWORK_SESSION = True
FAIL_CLOSED_IF_PREREQUISITE_16_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE = True
P13_TEXT_REWRITTEN = False


class BoundedActivationContractError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_16 contract violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise BoundedActivationContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_BOUNDED_PERMIT"
        )


def assert_missing_permit_denies_v1(*, permit: Mapping[str, Any] | None) -> None:
    if permit is None:
        return
    raise BoundedActivationContractError("PERMIT_PRESENT_WHEN_MISSING_EXPECTED")


def assert_runtime_activation_not_claimed_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("PREREQUISITE_16_BOUNDED_RUNTIME_ACTIVATION_PROVEN") is True:
        raise BoundedActivationContractError("RUNTIME_ACTIVATION_CLAIMED_FROM_OFFLINE_CODE")
    if payload.get("PREREQUISITE_16_NETWORK_SESSION_AUTHORIZED") is True:
        raise BoundedActivationContractError("NETWORK_SESSION_CLAIMED")
    if payload.get("LIVE_AUTHORIZED") is True:
        raise BoundedActivationContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("POST_PERFORMED") is True:
        raise BoundedActivationContractError("POST_CLAIMED")
