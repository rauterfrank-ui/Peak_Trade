"""Fail-closed contract for productive flatten POST and reconciliation.

Authorizes the current-path flatten of the already-bound SUI XPerp position.
Does not authorize ENTER, reversal, funding, leverage/mode mutation, whitelist
mutation, or standing LIVE_AUTHORIZED / CANARY_AUTHORIZED unlock.
"""

from __future__ import annotations

from typing import Any, Mapping

PRODUCTIVE_FLATTEN_POST_AUTHORIZED = True
PRODUCTIVE_RECONCILIATION_AUTHORIZED = True
FLATTEN_EXECUTE_INVOCATION_AUTHORIZED = True
NETWORK_SESSION_INSTANCE_AUTHORIZED = True
STANDING_LIVE_AUTHORIZED_MUST_REMAIN_FALSE = True
STANDING_CANARY_AUTHORIZED_MUST_REMAIN_FALSE = True
EMPTY_DATA_IS_ZERO = False
ABSENT_TARGET_ROW_IS_ZERO = False
RETRY_ALLOWED = False
MERGE_AUTHORIZED_BY_THIS_PERSIST = False
THIS_GO_DOES_NOT_SET_LIVE_AUTHORIZED = True
THIS_GO_DOES_NOT_SET_CANARY_AUTHORIZED = True
THIS_GO_DOES_NOT_FUND = True
THIS_GO_DOES_NOT_OPEN_NEW_POSITION = True
THIS_GO_DOES_NOT_CHANGE_LEVERAGE = True
THIS_GO_DOES_NOT_CHANGE_MARGIN_MODE = True
THIS_GO_DOES_NOT_CHANGE_POSITION_MODE = True
THIS_GO_DOES_NOT_CHANGE_ACCOUNT_MODE = True
FAIL_CLOSED_IF_EXPOSURE_INCREASE_POSSIBLE = True
VENUE_ACCEPTED_IS_NOT_FILL_PROVEN = True
FILL_IS_NOT_POSITION_ZERO_PROVEN = True
POSITION_ZERO_IS_NOT_FULL_RECONCILIATION_ALONE = True


class ProductiveFlattenPostContractError(RuntimeError):
    """Fail-closed productive flatten POST / reconciliation violation."""


def assert_live_authorized_cannot_substitute_v1(*, live_authorized_claim: bool) -> None:
    if live_authorized_claim is True:
        raise ProductiveFlattenPostContractError(
            "GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE_FOR_BOUNDED_FLATTEN"
        )


def assert_standing_live_flags_remain_false_v1(
    *,
    live_authorized: bool,
    live_enabled: bool,
    live_armed: bool,
    dedicated_flatten_live_wire_enabled: bool,
) -> None:
    if live_authorized or live_enabled or live_armed or dedicated_flatten_live_wire_enabled:
        raise ProductiveFlattenPostContractError("STANDING_LIVE_FLAGS_MUST_REMAIN_FALSE")


def assert_no_retry_v1(*, retry_used: bool) -> None:
    if retry_used is True:
        raise ProductiveFlattenPostContractError("RETRY_FORBIDDEN")


def assert_payload_not_live_unlock_v1(payload: Mapping[str, Any]) -> None:
    if payload.get("LIVE_AUTHORIZED") is True:
        raise ProductiveFlattenPostContractError("LIVE_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("CANARY_AUTHORIZED") is True:
        raise ProductiveFlattenPostContractError("CANARY_AUTHORIZED_CLAIMED_TRUE")
    if payload.get("FUNDING_USED") is True:
        raise ProductiveFlattenPostContractError("FUNDING_CLAIMED")
    if payload.get("MERGE_AUTHORIZED_BY_THIS_PERSIST") is True:
        raise ProductiveFlattenPostContractError("MERGE_CLAIMED")
