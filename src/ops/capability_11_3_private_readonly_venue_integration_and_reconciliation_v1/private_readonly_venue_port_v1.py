"""Private read-only venue port contract (declaration only; no network)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    CONTRACT_VERSION,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    NETWORK_SESSION_STARTED,
    OWNER,
    PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3,
    PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS,
    PRIVATE_READONLY_GET_ENDPOINTS,
    PRIVATE_READONLY_GET_ONLY,
    PRIVATE_READONLY_NETWORK_REACHABLE,
    PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN,
    PRIVATE_READONLY_PORT_DECLARED,
    PRIVATE_READONLY_PORT_OWNER,
    PRIVATE_READONLY_SIDE_EFFECTS_ONLY,
    PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
)


class PrivateReadonlyVenuePortError(RuntimeError):
    """Fail-closed private read-only venue port violation."""


@dataclass(frozen=True)
class PrivateReadonlyVenuePortDeclarationV1:
    """Declaration-only private read-only venue port.

    Cap 11.3 binds the contract surface for future private read-only
    integration. Construction of a real network/credential-backed port is
    forbidden in this capability.
    """

    PORT_KIND: str = "PRIVATE_READONLY_VENUE_PORT_V1_DECLARATION_ONLY"
    EXECUTION_MODE: str = "PRIVATE_READONLY"
    CONSTRUCTIBLE: bool = False
    REACHABLE: bool = False
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool = False
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool = False
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool = False
    NETWORK_SESSION_STARTED: bool = False
    PRIVATE_READONLY_GET_ONLY: bool = True
    ORDER_MUTATION_FORBIDDEN: bool = True
    ADAPTER_DECISION_AUTHORITY: bool = False
    ADAPTER_RECONCILIATION_AUTHORITY: bool = False
    OWNER: str = PRIVATE_READONLY_PORT_OWNER
    CONTRACT_VERSION: str = CONTRACT_VERSION
    ALLOWED_GET_ENDPOINTS: tuple[str, ...] = PRIVATE_READONLY_GET_ENDPOINTS
    FORBIDDEN_MUTATION_ACTIONS: tuple[str, ...] = PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS


def declare_private_readonly_venue_port_v1() -> PrivateReadonlyVenuePortDeclarationV1:
    return PrivateReadonlyVenuePortDeclarationV1()


def construct_private_readonly_venue_port_v1() -> None:
    """Always refuse real construction in Cap 11.3."""
    raise PrivateReadonlyVenuePortError(
        "PRIVATE_READONLY_VENUE_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_3"
    )


def refuse_private_readonly_network_fetch_v1(*, endpoint: str) -> dict[str, Any]:
    if endpoint not in PRIVATE_READONLY_GET_ENDPOINTS:
        raise PrivateReadonlyVenuePortError(f"PRIVATE_READONLY_ENDPOINT_NOT_ALLOWLISTED:{endpoint}")
    raise PrivateReadonlyVenuePortError(
        "PRIVATE_READONLY_NETWORK_FETCH_FORBIDDEN_IN_CAPABILITY_11_3"
    )


def refuse_private_readonly_mutation_v1(*, action: str) -> dict[str, Any]:
    raise PrivateReadonlyVenuePortError(f"PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN:{action}")


def prove_private_readonly_venue_port_v1() -> dict[str, Any]:
    declaration = declare_private_readonly_venue_port_v1()

    construction_blocked = False
    try:
        construct_private_readonly_venue_port_v1()
    except PrivateReadonlyVenuePortError as exc:
        construction_blocked = "CONSTRUCTION_FORBIDDEN" in str(exc)

    fetch_blocked = False
    try:
        refuse_private_readonly_network_fetch_v1(endpoint="accounts")
    except PrivateReadonlyVenuePortError as exc:
        fetch_blocked = "NETWORK_FETCH_FORBIDDEN" in str(exc)

    mutation_blocked = False
    try:
        refuse_private_readonly_mutation_v1(action="submit_order")
    except PrivateReadonlyVenuePortError as exc:
        mutation_blocked = "ORDER_MUTATION_FORBIDDEN" in str(exc)

    unknown_endpoint_blocked = False
    try:
        refuse_private_readonly_network_fetch_v1(endpoint="sendorder")
    except PrivateReadonlyVenuePortError as exc:
        unknown_endpoint_blocked = "NOT_ALLOWLISTED" in str(exc)

    ok = all(
        [
            declaration.CONSTRUCTIBLE is False,
            declaration.REACHABLE is False,
            declaration.PRIVATE_READONLY_GET_ONLY is True,
            declaration.ORDER_MUTATION_FORBIDDEN is True,
            declaration.ADAPTER_DECISION_AUTHORITY is False,
            construction_blocked,
            fetch_blocked,
            mutation_blocked,
            unknown_endpoint_blocked,
            PRIVATE_READONLY_PORT_DECLARED is True,
            PRIVATE_READONLY_SIDE_EFFECTS_ONLY is True,
            PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN is True,
            PRIVATE_READONLY_GET_ONLY is True,
            PRIVATE_READONLY_NETWORK_REACHABLE is False,
            PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED is False,
            PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3 is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
            declaration.OWNER == OWNER,
        ]
    )
    return {
        "ok": ok,
        "PRIVATE_READONLY_PORT_DECLARED": True,
        "PRIVATE_READONLY_PORT_CONSTRUCTIBLE": False,
        "PRIVATE_READONLY_NETWORK_REACHABLE": False,
        "PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED": False,
        "PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3": False,
        "PRIVATE_READONLY_GET_ONLY": True,
        "PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN": True,
        "construction_blocked": construction_blocked,
        "fetch_blocked": fetch_blocked,
        "mutation_blocked": mutation_blocked,
        "unknown_endpoint_blocked": unknown_endpoint_blocked,
        "allowed_get_endpoints": list(PRIVATE_READONLY_GET_ENDPOINTS),
        "forbidden_mutation_actions": list(PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS),
        "OWNER": OWNER,
    }
