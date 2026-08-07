"""Mode-specific execution port contracts for Cap 11.1 (scaffolding only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.constants_v1 import (
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    EXECUTION_PORT_CONTRACT_VERSION,
    LIVE_EXECUTION_PORT_DECLARED,
    LIVE_EXECUTION_REACHABLE,
    NO_EXECUTION_ADAPTER_DECISION_AUTHORITY,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    SIMULATED_EXECUTION_PORT_OWNER,
    SIMULATED_EXECUTION_PORT_RETAINED,
    SIMULATED_EXECUTION_PORT_SOLE_REACHABLE,
    TESTNET_EXECUTION_PORT_DECLARED,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
    construct_simulated_execution_port_v1,
    prove_execution_port_separation_v1,
    refuse_real_execution_adapter_construction_v1,
)


class ExecutionPortConstructionForbiddenError(RuntimeError):
    """Raised when Cap 11.1 forbids constructing Testnet/Live/real ports."""


@runtime_checkable
class ExecutionPortContractV1(Protocol):
    """Narrow mode-specific execution boundary contract.

    Adapters translate intent into mode-specific side effects only. They must
    never own decision, alpha, risk, safety, accounting, portfolio,
    reconciliation, or authorization authority.
    """

    PORT_KIND: str
    EXECUTION_MODE: str
    CONSTRUCTIBLE: bool
    REACHABLE: bool
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool
    ADAPTER_DECISION_AUTHORITY: bool
    ADAPTER_ALPHA_AUTHORITY: bool
    ADAPTER_RISK_AUTHORITY: bool
    ADAPTER_SAFETY_AUTHORITY: bool
    ADAPTER_ACCOUNTING_AUTHORITY: bool
    ADAPTER_PORTFOLIO_AUTHORITY: bool
    ADAPTER_RECONCILIATION_AUTHORITY: bool
    ADAPTER_AUTHORIZATION_AUTHORITY: bool


@dataclass(frozen=True)
class SimulatedExecutionPortContractDeclarationV1:
    PORT_KIND: str = "SIMULATED_EXECUTION_PORT_V1"
    EXECUTION_MODE: str = "SIMULATED"
    CONSTRUCTIBLE: bool = True
    REACHABLE: bool = True
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool = False
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool = False
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool = False
    ADAPTER_DECISION_AUTHORITY: bool = False
    ADAPTER_ALPHA_AUTHORITY: bool = False
    ADAPTER_RISK_AUTHORITY: bool = False
    ADAPTER_SAFETY_AUTHORITY: bool = False
    ADAPTER_ACCOUNTING_AUTHORITY: bool = False
    ADAPTER_PORTFOLIO_AUTHORITY: bool = False
    ADAPTER_RECONCILIATION_AUTHORITY: bool = False
    ADAPTER_AUTHORIZATION_AUTHORITY: bool = False
    OWNER: str = SIMULATED_EXECUTION_PORT_OWNER
    CONTRACT_VERSION: str = EXECUTION_PORT_CONTRACT_VERSION


@dataclass(frozen=True)
class TestnetExecutionPortContractDeclarationV1:
    """Declaration-only Testnet port. Construction permanently forbidden in 11.1."""

    PORT_KIND: str = "TESTNET_EXECUTION_PORT_V1_DECLARATION_ONLY"
    EXECUTION_MODE: str = "TESTNET"
    CONSTRUCTIBLE: bool = False
    REACHABLE: bool = False
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool = False
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool = False
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool = False
    ADAPTER_DECISION_AUTHORITY: bool = False
    ADAPTER_ALPHA_AUTHORITY: bool = False
    ADAPTER_RISK_AUTHORITY: bool = False
    ADAPTER_SAFETY_AUTHORITY: bool = False
    ADAPTER_ACCOUNTING_AUTHORITY: bool = False
    ADAPTER_PORTFOLIO_AUTHORITY: bool = False
    ADAPTER_RECONCILIATION_AUTHORITY: bool = False
    ADAPTER_AUTHORIZATION_AUTHORITY: bool = False
    CONTRACT_VERSION: str = EXECUTION_PORT_CONTRACT_VERSION


@dataclass(frozen=True)
class LiveExecutionPortContractDeclarationV1:
    """Declaration-only Live port. Construction permanently forbidden in 11.1."""

    PORT_KIND: str = "LIVE_EXECUTION_PORT_V1_DECLARATION_ONLY"
    EXECUTION_MODE: str = "LIVE"
    CONSTRUCTIBLE: bool = False
    REACHABLE: bool = False
    REAL_EXECUTION_ADAPTER_CONSTRUCTED: bool = False
    EXCHANGE_ORDER_SUBMIT_REACHABLE: bool = False
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE: bool = False
    ADAPTER_DECISION_AUTHORITY: bool = False
    ADAPTER_ALPHA_AUTHORITY: bool = False
    ADAPTER_RISK_AUTHORITY: bool = False
    ADAPTER_SAFETY_AUTHORITY: bool = False
    ADAPTER_ACCOUNTING_AUTHORITY: bool = False
    ADAPTER_PORTFOLIO_AUTHORITY: bool = False
    ADAPTER_RECONCILIATION_AUTHORITY: bool = False
    ADAPTER_AUTHORIZATION_AUTHORITY: bool = False
    CONTRACT_VERSION: str = EXECUTION_PORT_CONTRACT_VERSION


def declare_testnet_execution_port_v1() -> TestnetExecutionPortContractDeclarationV1:
    return TestnetExecutionPortContractDeclarationV1()


def declare_live_execution_port_v1() -> LiveExecutionPortContractDeclarationV1:
    return LiveExecutionPortContractDeclarationV1()


def construct_testnet_execution_port_v1(*_args: Any, **_kwargs: Any) -> None:
    raise ExecutionPortConstructionForbiddenError(
        "TESTNET_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1"
    )


def construct_live_execution_port_v1(*_args: Any, **_kwargs: Any) -> None:
    raise ExecutionPortConstructionForbiddenError(
        "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1"
    )


def bind_simulated_execution_port_v1() -> SimulatedExecutionPortV1:
    """Retain existing Cap 7.2 SimulatedExecutionPort as sole reachable port."""
    return construct_simulated_execution_port_v1()


def prove_mode_specific_execution_boundary_v1() -> dict[str, Any]:
    simulated = SimulatedExecutionPortContractDeclarationV1()
    testnet = declare_testnet_execution_port_v1()
    live = declare_live_execution_port_v1()
    port = bind_simulated_execution_port_v1()
    separation = prove_execution_port_separation_v1()

    testnet_construct_blocked = False
    try:
        construct_testnet_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        testnet_construct_blocked = True

    live_construct_blocked = False
    try:
        construct_live_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        live_construct_blocked = True

    real_construct_blocked = False
    try:
        refuse_real_execution_adapter_construction_v1()
    except Exception:
        real_construct_blocked = True

    ok = all(
        [
            simulated.REACHABLE is True,
            simulated.CONSTRUCTIBLE is True,
            testnet.REACHABLE is False,
            testnet.CONSTRUCTIBLE is False,
            live.REACHABLE is False,
            live.CONSTRUCTIBLE is False,
            isinstance(port, SimulatedExecutionPortV1),
            port.REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            port.EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            port.EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            testnet_construct_blocked,
            live_construct_blocked,
            real_construct_blocked,
            separation.get("ok") is True,
            NO_EXECUTION_ADAPTER_DECISION_AUTHORITY is True,
        ]
    )
    return {
        "ok": ok,
        "contract_version": EXECUTION_PORT_CONTRACT_VERSION,
        "SIMULATED_EXECUTION_PORT_RETAINED": SIMULATED_EXECUTION_PORT_RETAINED,
        "SIMULATED_EXECUTION_PORT_SOLE_REACHABLE": SIMULATED_EXECUTION_PORT_SOLE_REACHABLE,
        "TESTNET_EXECUTION_PORT_DECLARED": TESTNET_EXECUTION_PORT_DECLARED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_PORT_DECLARED": LIVE_EXECUTION_PORT_DECLARED,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": EXCHANGE_ORDER_SUBMIT_REACHABLE,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
        "testnet_construction_blocked": testnet_construct_blocked,
        "live_construction_blocked": live_construct_blocked,
        "real_adapter_construction_blocked": real_construct_blocked,
        "simulated_port_kind": port.PORT_KIND,
        "NO_EXECUTION_ADAPTER_DECISION_AUTHORITY": True,
        "CORE_LOGIC_CHANGE": False,
        "separation_proof": separation,
    }
