"""Live private read-only venue port contract (declaration only; no network)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.constants_v1 import (
    CONTRACT_VERSION,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LIVE_PRIVATE_READONLY_ACTIVATED,
    LIVE_PRIVATE_READONLY_CONTRACT_ACTIVATED,
    LIVE_PRIVATE_READONLY_CONTRACT_BOUND,
    LIVE_PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS,
    LIVE_PRIVATE_READONLY_GET_ENDPOINTS,
    LIVE_PRIVATE_READONLY_PORT_CONSTRUCTIBLE,
    LIVE_PRIVATE_READONLY_PORT_DECLARED,
    LIVE_PRIVATE_READONLY_PORT_OWNER,
    NETWORK_SESSION_STARTED,
    OWNER,
    PRIVATE_NETWORK_SESSION_STARTED,
    PRIVATE_READONLY_NETWORK_REACHABLE,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
)


class LivePrivateReadonlyPortError(RuntimeError):
    """Fail-closed Live private read-only port violation."""


@dataclass(frozen=True)
class LivePrivateReadonlyPortDeclarationV1:
    """Declaration-only Live private read-only port.

    Cap 11.7 binds the Live-mode private read-only contract surface.
    Construction of a real authenticated private network session is
    forbidden in this capability.
    """

    PORT_KIND: str = "LIVE_PRIVATE_READONLY_PORT_V1_DECLARATION_ONLY"
    EXECUTION_MODE: str = "LIVE_PRIVATE_READONLY"
    CONSTRUCTIBLE: bool = False
    REACHABLE: bool = False
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool = False
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool = False
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool = False
    NETWORK_SESSION_STARTED: bool = False
    PRIVATE_NETWORK_SESSION_STARTED: bool = False
    PRIVATE_READONLY_GET_ONLY: bool = True
    ORDER_MUTATION_FORBIDDEN: bool = True
    ADAPTER_DECISION_AUTHORITY: bool = False
    ADAPTER_RECONCILIATION_AUTHORITY: bool = False
    OWNER: str = LIVE_PRIVATE_READONLY_PORT_OWNER
    CONTRACT_VERSION: str = CONTRACT_VERSION
    ALLOWED_GET_ENDPOINTS: tuple[str, ...] = LIVE_PRIVATE_READONLY_GET_ENDPOINTS
    FORBIDDEN_MUTATION_ACTIONS: tuple[str, ...] = LIVE_PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS


def declare_live_private_readonly_port_v1() -> LivePrivateReadonlyPortDeclarationV1:
    return LivePrivateReadonlyPortDeclarationV1()


def construct_live_private_readonly_port_v1() -> None:
    """Always refuse real construction in Cap 11.7."""
    raise LivePrivateReadonlyPortError(
        "LIVE_PRIVATE_READONLY_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_7"
    )


def refuse_live_private_readonly_network_session_v1(*, session_id: str) -> dict[str, Any]:
    raise LivePrivateReadonlyPortError(
        f"LIVE_PRIVATE_NETWORK_SESSION_FORBIDDEN_IN_CAPABILITY_11_7:{session_id}"
    )


def refuse_live_private_readonly_network_fetch_v1(*, endpoint: str) -> dict[str, Any]:
    if endpoint not in LIVE_PRIVATE_READONLY_GET_ENDPOINTS:
        raise LivePrivateReadonlyPortError(
            f"LIVE_PRIVATE_READONLY_ENDPOINT_NOT_ALLOWLISTED:{endpoint}"
        )
    raise LivePrivateReadonlyPortError(
        "LIVE_PRIVATE_READONLY_NETWORK_FETCH_FORBIDDEN_IN_CAPABILITY_11_7"
    )


def refuse_live_private_readonly_mutation_v1(*, action: str) -> dict[str, Any]:
    raise LivePrivateReadonlyPortError(f"LIVE_PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN:{action}")


def refuse_live_private_readonly_credential_access_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LivePrivateReadonlyPortError(
        f"LIVE_PRIVATE_READONLY_CREDENTIAL_ACCESS_FORBIDDEN_IN_CAPABILITY_11_7:{claimed_action}"
    )


def prove_live_private_readonly_port_v1() -> dict[str, Any]:
    declaration = declare_live_private_readonly_port_v1()

    construction_blocked = False
    try:
        construct_live_private_readonly_port_v1()
    except LivePrivateReadonlyPortError as exc:
        construction_blocked = "CONSTRUCTION_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_live_private_readonly_network_session_v1(session_id="live-private-session")
    except LivePrivateReadonlyPortError as exc:
        session_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    fetch_blocked = False
    try:
        refuse_live_private_readonly_network_fetch_v1(endpoint="accounts")
    except LivePrivateReadonlyPortError as exc:
        fetch_blocked = "NETWORK_FETCH_FORBIDDEN" in str(exc)

    mutation_blocked = False
    try:
        refuse_live_private_readonly_mutation_v1(action="submit_order")
    except LivePrivateReadonlyPortError as exc:
        mutation_blocked = "ORDER_MUTATION_FORBIDDEN" in str(exc)

    credential_blocked = False
    try:
        refuse_live_private_readonly_credential_access_v1(claimed_action="load_api_key")
    except LivePrivateReadonlyPortError as exc:
        credential_blocked = "CREDENTIAL_ACCESS_FORBIDDEN" in str(exc)

    unknown_endpoint_blocked = False
    try:
        refuse_live_private_readonly_network_fetch_v1(endpoint="sendorder")
    except LivePrivateReadonlyPortError as exc:
        unknown_endpoint_blocked = "NOT_ALLOWLISTED" in str(exc)

    ok = all(
        [
            declaration.CONSTRUCTIBLE is False,
            declaration.REACHABLE is False,
            declaration.PRIVATE_READONLY_GET_ONLY is True,
            declaration.ORDER_MUTATION_FORBIDDEN is True,
            declaration.ADAPTER_DECISION_AUTHORITY is False,
            declaration.PRIVATE_NETWORK_SESSION_STARTED is False,
            construction_blocked,
            session_blocked,
            fetch_blocked,
            mutation_blocked,
            credential_blocked,
            unknown_endpoint_blocked,
            LIVE_PRIVATE_READONLY_PORT_DECLARED is True,
            LIVE_PRIVATE_READONLY_PORT_CONSTRUCTIBLE is False,
            LIVE_PRIVATE_READONLY_CONTRACT_BOUND is True,
            LIVE_PRIVATE_READONLY_CONTRACT_ACTIVATED is False,
            LIVE_PRIVATE_READONLY_ACTIVATED is False,
            PRIVATE_NETWORK_SESSION_STARTED is False,
            PRIVATE_READONLY_NETWORK_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
            declaration.OWNER == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_PRIVATE_READONLY_PORT_DECLARED": True,
        "LIVE_PRIVATE_READONLY_PORT_CONSTRUCTIBLE": False,
        "LIVE_PRIVATE_READONLY_CONTRACT_BOUND": True,
        "LIVE_PRIVATE_READONLY_CONTRACT_ACTIVATED": False,
        "LIVE_PRIVATE_READONLY_ACTIVATED": False,
        "PRIVATE_NETWORK_SESSION_STARTED": False,
        "PRIVATE_READONLY_NETWORK_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "construction_blocked": construction_blocked,
        "network_session_blocked": session_blocked,
        "fetch_blocked": fetch_blocked,
        "mutation_blocked": mutation_blocked,
        "credential_access_blocked": credential_blocked,
        "unknown_endpoint_blocked": unknown_endpoint_blocked,
        "allowed_get_endpoints": list(LIVE_PRIVATE_READONLY_GET_ENDPOINTS),
        "forbidden_mutation_actions": list(LIVE_PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS),
        "OWNER": OWNER,
    }
