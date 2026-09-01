"""Autonomy scope limits for authorization (§11.6)."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.authorization_binding_contract_v1 import (
    AuthorizationBindingV1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    AUTONOMOUS_CAPITAL_LIMIT_INCREASE,
    AUTONOMOUS_TESTNET_TO_LIVE_TRANSITION,
    AUTONOMOUS_VENUE_ENABLEMENT,
    AUTONOMOUS_VENUE_SESSION_RENEWAL_WITHIN_AUTH_PERMITTED,
    AUTONOMOUS_AUTHORIZATION_SCOPE_EXTENSION,
)


class AutonomyScopeViolationError(ValueError):
    """Fail-closed autonomy scope limit violation."""


def admit_venue_session_renewal_within_auth_v1(
    binding: AuthorizationBindingV1,
    *,
    authorization_still_valid: bool,
) -> dict[str, Any]:
    """Ordinary venue-session renewal may be admitted within existing auth (contract)."""
    if not authorization_still_valid or binding.consumed:
        raise AutonomyScopeViolationError("AUTHORIZATION_NOT_VALID_FOR_SESSION_RENEWAL")
    if not AUTONOMOUS_VENUE_SESSION_RENEWAL_WITHIN_AUTH_PERMITTED:
        raise AutonomyScopeViolationError("VENUE_SESSION_RENEWAL_NOT_PERMITTED")
    return {
        "admitted": True,
        "side_effect": "venue_session_renewal_contract_only",
        "scope_extended": False,
        "network_session_started": False,
        "AUTONOMOUS_VENUE_SESSION_RENEWAL_WITHIN_AUTH_PERMITTED": True,
    }


def refuse_authorization_scope_extension_v1(
    binding: AuthorizationBindingV1,
    *,
    requested_change: str,
) -> dict[str, Any]:
    """Runtime must not autonomously extend authorization scope."""
    raise AutonomyScopeViolationError(
        f"AUTONOMOUS_AUTHORIZATION_SCOPE_EXTENSION_FORBIDDEN:"
        f"{binding.authorization_id}:{requested_change}"
    )


def refuse_capital_limit_increase_v1(binding: AuthorizationBindingV1) -> dict[str, Any]:
    raise AutonomyScopeViolationError(
        f"AUTONOMOUS_CAPITAL_LIMIT_INCREASE_FORBIDDEN:{binding.authorization_id}"
    )


def refuse_venue_enablement_v1(
    binding: AuthorizationBindingV1, *, new_venue: str
) -> dict[str, Any]:
    raise AutonomyScopeViolationError(
        f"AUTONOMOUS_VENUE_ENABLEMENT_FORBIDDEN:{binding.authorization_id}:{new_venue}"
    )


def refuse_testnet_to_live_transition_v1(
    binding: AuthorizationBindingV1,
) -> dict[str, Any]:
    raise AutonomyScopeViolationError(
        f"AUTONOMOUS_TESTNET_TO_LIVE_TRANSITION_FORBIDDEN:{binding.authorization_id}"
    )


def prove_autonomy_scope_limits_v1(binding: AuthorizationBindingV1) -> dict[str, Any]:
    renew = admit_venue_session_renewal_within_auth_v1(binding, authorization_still_valid=True)
    scope_blocked = False
    try:
        refuse_authorization_scope_extension_v1(
            binding, requested_change="increase_maximum_notional"
        )
    except AutonomyScopeViolationError:
        scope_blocked = True

    capital_blocked = False
    try:
        refuse_capital_limit_increase_v1(binding)
    except AutonomyScopeViolationError:
        capital_blocked = True

    venue_blocked = False
    try:
        refuse_venue_enablement_v1(binding, new_venue="UNDECLARED_VENUE")
    except AutonomyScopeViolationError:
        venue_blocked = True

    mode_blocked = False
    try:
        refuse_testnet_to_live_transition_v1(binding)
    except AutonomyScopeViolationError:
        mode_blocked = True

    invalid_renew_blocked = False
    try:
        admit_venue_session_renewal_within_auth_v1(binding, authorization_still_valid=False)
    except AutonomyScopeViolationError:
        invalid_renew_blocked = True

    ok = all(
        [
            renew.get("admitted") is True,
            renew.get("network_session_started") is False,
            scope_blocked,
            capital_blocked,
            venue_blocked,
            mode_blocked,
            invalid_renew_blocked,
            AUTONOMOUS_AUTHORIZATION_SCOPE_EXTENSION is False,
            AUTONOMOUS_CAPITAL_LIMIT_INCREASE is False,
            AUTONOMOUS_VENUE_ENABLEMENT is False,
            AUTONOMOUS_TESTNET_TO_LIVE_TRANSITION is False,
            AUTONOMOUS_VENUE_SESSION_RENEWAL_WITHIN_AUTH_PERMITTED is True,
        ]
    )
    return {
        "ok": ok,
        "AUTONOMOUS_VENUE_SESSION_RENEWAL_WITHIN_AUTH_PERMITTED": True,
        "AUTONOMOUS_AUTHORIZATION_SCOPE_EXTENSION": False,
        "AUTONOMOUS_CAPITAL_LIMIT_INCREASE": False,
        "AUTONOMOUS_VENUE_ENABLEMENT": False,
        "AUTONOMOUS_TESTNET_TO_LIVE_TRANSITION": False,
        "scope_extension_blocked": scope_blocked,
        "capital_increase_blocked": capital_blocked,
        "venue_enablement_blocked": venue_blocked,
        "testnet_to_live_blocked": mode_blocked,
        "invalid_renewal_blocked": invalid_renew_blocked,
        "NETWORK_SESSION_STARTED": False,
    }
