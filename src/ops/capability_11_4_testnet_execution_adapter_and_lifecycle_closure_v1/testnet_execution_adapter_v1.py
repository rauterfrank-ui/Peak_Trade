"""Testnet execution adapter contract (declaration only; no construction/submit)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_testnet_execution_port_v1,
    declare_testnet_execution_port_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.constants_v1 import (
    CONTRACT_VERSION,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    NETWORK_SESSION_STARTED,
    OWNER,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    TESTNET_EXECUTION_ADAPTER_ACTIVATED,
    TESTNET_EXECUTION_ADAPTER_DECLARED,
    TESTNET_EXECUTION_ADAPTER_OWNER,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_4,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4,
)


class TestnetExecutionAdapterError(RuntimeError):
    """Fail-closed Testnet execution adapter violation."""

    __test__ = False


@dataclass(frozen=True)
class TestnetExecutionAdapterDeclarationV1:
    """Declaration-only Testnet execution adapter for Cap 11.4.

    Reuses Cap 11.1 TestnetExecutionPort declaration. Construction, network
    session start, and exchange order submit remain permanently forbidden in
    Cap 11.4 (contracts-only / not_activated).
    """

    __test__ = False

    PORT_KIND: str = "TESTNET_EXECUTION_ADAPTER_V1_DECLARATION_ONLY"
    EXECUTION_MODE: str = "TESTNET"
    CONSTRUCTIBLE: bool = False
    REACHABLE: bool = False
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool = False
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool = False
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool = False
    NETWORK_SESSION_STARTED: bool = False
    ADAPTER_DECISION_AUTHORITY: bool = False
    ADAPTER_ALPHA_AUTHORITY: bool = False
    ADAPTER_RISK_AUTHORITY: bool = False
    ADAPTER_SAFETY_AUTHORITY: bool = False
    ADAPTER_ACCOUNTING_AUTHORITY: bool = False
    ADAPTER_PORTFOLIO_AUTHORITY: bool = False
    ADAPTER_RECONCILIATION_AUTHORITY: bool = False
    ADAPTER_AUTHORIZATION_AUTHORITY: bool = False
    OWNER: str = TESTNET_EXECUTION_ADAPTER_OWNER
    CONTRACT_VERSION: str = CONTRACT_VERSION


def declare_testnet_execution_adapter_v1() -> TestnetExecutionAdapterDeclarationV1:
    # Reuse Cap 11.1 declaration surface without activating it.
    predecessor = declare_testnet_execution_port_v1()
    if predecessor.REACHABLE or predecessor.CONSTRUCTIBLE:
        raise TestnetExecutionAdapterError("CAPABILITY_11_1_TESTNET_PORT_MUST_REMAIN_UNREACHABLE")
    return TestnetExecutionAdapterDeclarationV1()


def construct_testnet_execution_adapter_v1() -> None:
    """Always refuse real construction in Cap 11.4."""
    raise TestnetExecutionAdapterError(
        "TESTNET_EXECUTION_ADAPTER_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_4"
    )


def refuse_testnet_order_submit_v1(*, client_order_id: str) -> dict[str, Any]:
    if not client_order_id:
        raise TestnetExecutionAdapterError("CLIENT_ORDER_ID_REQUIRED")
    raise TestnetExecutionAdapterError("TESTNET_ORDER_SUBMIT_FORBIDDEN_IN_CAPABILITY_11_4")


def refuse_testnet_network_session_start_v1(*, session_id: str) -> dict[str, Any]:
    if not session_id:
        raise TestnetExecutionAdapterError("SESSION_ID_REQUIRED")
    raise TestnetExecutionAdapterError("TESTNET_NETWORK_SESSION_START_FORBIDDEN_IN_CAPABILITY_11_4")


def prove_testnet_execution_adapter_v1() -> dict[str, Any]:
    declaration = declare_testnet_execution_adapter_v1()

    construction_blocked = False
    try:
        construct_testnet_execution_adapter_v1()
    except TestnetExecutionAdapterError as exc:
        construction_blocked = "CONSTRUCTION_FORBIDDEN" in str(exc)

    predecessor_construction_blocked = False
    try:
        construct_testnet_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        predecessor_construction_blocked = True

    submit_blocked = False
    try:
        refuse_testnet_order_submit_v1(client_order_id="pt-coid-demo")
    except TestnetExecutionAdapterError as exc:
        submit_blocked = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_testnet_network_session_start_v1(session_id="session-demo")
    except TestnetExecutionAdapterError as exc:
        session_blocked = "NETWORK_SESSION_START_FORBIDDEN" in str(exc)

    ok = all(
        [
            declaration.CONSTRUCTIBLE is False,
            declaration.REACHABLE is False,
            declaration.ADAPTER_DECISION_AUTHORITY is False,
            construction_blocked,
            predecessor_construction_blocked,
            submit_blocked,
            session_blocked,
            TESTNET_EXECUTION_ADAPTER_DECLARED is True,
            TESTNET_EXECUTION_ADAPTER_ACTIVATED is False,
            TESTNET_EXECUTION_REACHABLE is False,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4 is False,
            TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_4 is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
            declaration.OWNER == OWNER,
        ]
    )
    return {
        "ok": ok,
        "TESTNET_EXECUTION_ADAPTER_DECLARED": True,
        "TESTNET_EXECUTION_ADAPTER_CONSTRUCTIBLE": False,
        "TESTNET_EXECUTION_ADAPTER_ACTIVATED": False,
        "TESTNET_EXECUTION_REACHABLE": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4": False,
        "TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_4": False,
        "construction_blocked": construction_blocked,
        "predecessor_construction_blocked": predecessor_construction_blocked,
        "submit_blocked": submit_blocked,
        "session_start_blocked": session_blocked,
        "OWNER": OWNER,
    }
