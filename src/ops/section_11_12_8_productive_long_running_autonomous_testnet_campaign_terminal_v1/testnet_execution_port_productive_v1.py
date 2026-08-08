"""Constructible/reachable TestnetExecutionPort under §11.12.8 terminal.

Extends Cap 11.1 ExecutionPortContractV1 / declaration and Cap 11.4 adapter
anti-corruption. Cap 11.1/11.4 construction remains forbidden inside those
packages; productive construction lives only here under the terminal gate.

This implementation OWNER_GO never performs network or order side effects:
submit paths are present and testable but hard-refuse real effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_testnet_execution_port_v1 as cap_11_1_construct_forbidden,
    declare_testnet_execution_port_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_execution_adapter_v1 import (
    TestnetExecutionAdapterError,
    construct_testnet_execution_adapter_v1 as cap_11_4_construct_forbidden,
    declare_testnet_execution_adapter_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.venue_adapter_anti_corruption_v1 import (
    prove_venue_adapter_anti_corruption_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    CANONICAL_ALLOWED_ORDER_TYPES,
    CANONICAL_INSTRUMENT_SCOPE,
    CANONICAL_RUNTIME_MODE,
    CANONICAL_VENUE,
    CONTRACT_VERSION,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    OWNER,
    SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION,
)


class TestnetExecutionPortProductiveError(RuntimeError):
    """Fail-closed productive TestnetExecutionPort violation."""

    __test__ = False


@dataclass
class TestnetExecutionPortProductiveV1:
    """Productive TestnetExecutionPort (constructible/reachable under terminal).

    Implements Cap 11.1 ExecutionPortContractV1 fields. Does not own Alpha,
    risk, safety, accounting, portfolio, reconciliation, or authorization.
    """

    __test__ = False

    PORT_KIND: str = "TESTNET_EXECUTION_PORT_V1_PRODUCTIVE"
    EXECUTION_MODE: str = CANONICAL_RUNTIME_MODE
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
    OWNER: str = OWNER
    CONTRACT_VERSION: str = CONTRACT_VERSION
    venue: str = CANONICAL_VENUE
    instrument_scope: tuple[str, ...] = CANONICAL_INSTRUMENT_SCOPE
    allowed_order_types: tuple[str, ...] = CANONICAL_ALLOWED_ORDER_TYPES
    constructed_under_authorized_terminal: bool = False
    submit_attempts: list[dict[str, Any]] = field(default_factory=list)
    network_effect: str = NETWORK_EFFECT
    order_effect: str = ORDER_EFFECT
    live_order_effect: str = LIVE_ORDER_EFFECT

    def submit_order_v1(
        self,
        *,
        client_order_id: str,
        instrument: str,
        order_type: str,
        side: str,
        quantity: str,
        dry_run_record_only: bool = True,
    ) -> dict[str, Any]:
        """Order-submit surface: recordable for tests; never emits real effects here."""
        if not client_order_id:
            raise TestnetExecutionPortProductiveError("CLIENT_ORDER_ID_REQUIRED")
        if instrument not in self.instrument_scope:
            raise TestnetExecutionPortProductiveError(f"INSTRUMENT_OUT_OF_SCOPE:{instrument}")
        if order_type not in self.allowed_order_types:
            raise TestnetExecutionPortProductiveError(f"ORDER_TYPE_FORBIDDEN:{order_type}")
        if self.EXECUTION_MODE != "TESTNET":
            raise TestnetExecutionPortProductiveError("LIVE_OR_NON_TESTNET_SUBMIT_FORBIDDEN")
        if SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION or not dry_run_record_only:
            raise TestnetExecutionPortProductiveError(
                "ORDER_SUBMIT_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION_ONLY"
            )
        attempt = {
            "client_order_id": client_order_id,
            "instrument": instrument,
            "order_type": order_type,
            "side": side,
            "quantity": quantity,
            "submitted": False,
            "network_effect": "NONE",
            "order_effect": "NONE",
            "live_order_effect": "NONE",
            "dry_run_record_only": True,
        }
        self.submit_attempts.append(attempt)
        raise TestnetExecutionPortProductiveError(
            "ORDER_SUBMIT_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION_ONLY"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "PORT_KIND": self.PORT_KIND,
            "EXECUTION_MODE": self.EXECUTION_MODE,
            "CONSTRUCTIBLE": self.CONSTRUCTIBLE,
            "REACHABLE": self.REACHABLE,
            "constructed_under_authorized_terminal": self.constructed_under_authorized_terminal,
            "REAL_EXECUTION_ADAPTER_CONSTRUCTED": self.REAL_EXECUTION_ADAPTER_CONSTRUCTED,
            "EXCHANGE_ORDER_SUBMIT_REACHABLE": self.EXCHANGE_ORDER_SUBMIT_REACHABLE,
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": self.EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
            "ADAPTER_DECISION_AUTHORITY": self.ADAPTER_DECISION_AUTHORITY,
            "venue": self.venue,
            "instrument_scope": list(self.instrument_scope),
            "allowed_order_types": list(self.allowed_order_types),
            "NETWORK_EFFECT": self.network_effect,
            "ORDER_EFFECT": self.order_effect,
            "LIVE_ORDER_EFFECT": self.live_order_effect,
            "OWNER": self.OWNER,
            "CONTRACT_VERSION": self.CONTRACT_VERSION,
            "submit_attempt_count": len(self.submit_attempts),
        }


@dataclass(frozen=True)
class TestnetExecutionAdapterProductiveDeclarationV1:
    """Productive adapter binding reusing Cap 11.4 anti-corruption (no Cap 11.4 mutate)."""

    __test__ = False

    PORT_KIND: str = "TESTNET_EXECUTION_ADAPTER_V1_PRODUCTIVE_UNDER_TERMINAL"
    EXECUTION_MODE: str = CANONICAL_RUNTIME_MODE
    CONSTRUCTIBLE: bool = True
    REACHABLE: bool = True
    ADAPTER_DECISION_AUTHORITY: bool = False
    OWNER: str = OWNER
    CONTRACT_VERSION: str = CONTRACT_VERSION
    CAP_11_4_DECLARATION_PRESERVED: bool = True
    CAP_11_1_DECLARATION_PRESERVED: bool = True


def construct_testnet_execution_port_under_terminal_v1(
    *,
    authorized_terminal: bool,
) -> TestnetExecutionPortProductiveV1:
    """Construct productive TestnetExecutionPort only under authorized terminal gate."""
    if not authorized_terminal:
        raise TestnetExecutionPortProductiveError(
            "TESTNET_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_WITHOUT_AUTHORIZED_TERMINAL"
        )
    # Cap 11.1/11.4 construction must remain forbidden inside those packages.
    cap_11_1_still_blocked = False
    try:
        cap_11_1_construct_forbidden()
    except ExecutionPortConstructionForbiddenError:
        cap_11_1_still_blocked = True
    if not cap_11_1_still_blocked:
        raise TestnetExecutionPortProductiveError("CAP_11_1_CONSTRUCTION_MUST_REMAIN_FORBIDDEN")

    cap_11_4_still_blocked = False
    try:
        cap_11_4_construct_forbidden()
    except TestnetExecutionAdapterError as exc:
        cap_11_4_still_blocked = "CONSTRUCTION_FORBIDDEN" in str(exc)
    if not cap_11_4_still_blocked:
        raise TestnetExecutionPortProductiveError("CAP_11_4_CONSTRUCTION_MUST_REMAIN_FORBIDDEN")

    predecessor = declare_testnet_execution_port_v1()
    if predecessor.REACHABLE or predecessor.CONSTRUCTIBLE:
        raise TestnetExecutionPortProductiveError(
            "CAP_11_1_DECLARATION_MUST_REMAIN_UNREACHABLE_UNCONSTRUCTIBLE"
        )
    adapter_decl = declare_testnet_execution_adapter_v1()
    if adapter_decl.REACHABLE or adapter_decl.CONSTRUCTIBLE:
        raise TestnetExecutionPortProductiveError(
            "CAP_11_4_DECLARATION_MUST_REMAIN_UNREACHABLE_UNCONSTRUCTIBLE"
        )
    anti = prove_venue_adapter_anti_corruption_v1()
    if anti.get("ok") is not True:
        raise TestnetExecutionPortProductiveError("CAP_11_4_ANTI_CORRUPTION_PROOF_REQUIRED")

    return TestnetExecutionPortProductiveV1(constructed_under_authorized_terminal=True)


def prove_testnet_execution_port_productive_binding_v1() -> dict[str, Any]:
    unauthorized_blocked = False
    try:
        construct_testnet_execution_port_under_terminal_v1(authorized_terminal=False)
    except TestnetExecutionPortProductiveError as exc:
        unauthorized_blocked = "WITHOUT_AUTHORIZED_TERMINAL" in str(exc)

    port = construct_testnet_execution_port_under_terminal_v1(authorized_terminal=True)
    submit_blocked = False
    try:
        port.submit_order_v1(
            client_order_id="coid-demo",
            instrument="BTC-USDT-SWAP",
            order_type="LIMIT",
            side="buy",
            quantity="1",
        )
    except TestnetExecutionPortProductiveError as exc:
        submit_blocked = "ORDER_SUBMIT_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION_ONLY" in str(exc)

    live_blocked = False
    try:
        bad = TestnetExecutionPortProductiveV1(EXECUTION_MODE="LIVE")
        bad.submit_order_v1(
            client_order_id="coid-live",
            instrument="BTC-USDT-SWAP",
            order_type="LIMIT",
            side="buy",
            quantity="1",
        )
    except TestnetExecutionPortProductiveError as exc:
        live_blocked = "LIVE_OR_NON_TESTNET_SUBMIT_FORBIDDEN" in str(exc)

    ok = all(
        [
            unauthorized_blocked,
            port.CONSTRUCTIBLE is True,
            port.REACHABLE is True,
            port.constructed_under_authorized_terminal is True,
            port.ADAPTER_DECISION_AUTHORITY is False,
            submit_blocked,
            live_blocked,
            NETWORK_EFFECT == "NONE",
            ORDER_EFFECT == "NONE",
            LIVE_ORDER_EFFECT == "NONE",
        ]
    )
    return {
        "ok": ok,
        "unauthorized_construction_blocked": unauthorized_blocked,
        "port": port.to_dict(),
        "order_submit_blocked_in_implementation": submit_blocked,
        "live_submit_blocked": live_blocked,
        "cap_11_1_declaration_preserved": True,
        "cap_11_4_declaration_preserved": True,
        "adapter": TestnetExecutionAdapterProductiveDeclarationV1().__dict__,
    }
