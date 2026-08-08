"""Productive Testnet execution port under ACTUAL start authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_ALLOWED_ORDER_TYPES,
    CANONICAL_INSTRUMENT_SCOPE,
    CANONICAL_RUNTIME_MODE,
    CANONICAL_VENUE,
    CONTRACT_VERSION,
    OWNER,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.testnet_transport_v1 import (
    StubbedTestnetTransportV1,
    TestnetTransportPortV1,
)


class ActualStartPortError(RuntimeError):
    """Fail-closed productive execution port violation."""


@dataclass
class ProductiveTestnetExecutionPortV1:
    """Authorized productive submit surface (separate from terminal ALWAYS_REFUSE port)."""

    PORT_KIND: str = "TESTNET_EXECUTION_PORT_V1_ACTUAL_START_PRODUCTIVE"
    EXECUTION_MODE: str = CANONICAL_RUNTIME_MODE
    CONSTRUCTIBLE: bool = True
    REACHABLE: bool = True
    OWNER: str = OWNER
    CONTRACT_VERSION: str = CONTRACT_VERSION
    venue: str = CANONICAL_VENUE
    instrument_scope: tuple[str, ...] = CANONICAL_INSTRUMENT_SCOPE
    allowed_order_types: tuple[str, ...] = CANONICAL_ALLOWED_ORDER_TYPES
    authorized: bool = False
    stubbed: bool = True
    transport: TestnetTransportPortV1 | None = None
    submit_attempts: list[dict[str, Any]] = field(default_factory=list)

    def submit_order_v1(
        self,
        *,
        client_order_id: str,
        instrument: str,
        order_type: str,
        side: str,
        quantity: str,
    ) -> dict[str, Any]:
        if not self.authorized:
            raise ActualStartPortError("SUBMIT_FORBIDDEN_WITHOUT_AUTHORIZATION")
        if self.EXECUTION_MODE != "TESTNET":
            raise ActualStartPortError("LIVE_OR_NON_TESTNET_SUBMIT_FORBIDDEN")
        if instrument not in self.instrument_scope:
            raise ActualStartPortError(f"INSTRUMENT_OUT_OF_SCOPE:{instrument}")
        if order_type not in self.allowed_order_types:
            raise ActualStartPortError(f"ORDER_TYPE_FORBIDDEN:{order_type}")
        if self.transport is None:
            raise ActualStartPortError("TRANSPORT_NOT_BOUND")
        result = self.transport.request(
            method="POST",
            endpoint="/api/v5/trade/order",
            body={
                "client_order_id": client_order_id,
                "instrument": instrument,
                "order_type": order_type,
                "side": side,
                "quantity": quantity,
            },
        )
        attempt = {
            "client_order_id": client_order_id,
            "instrument": instrument,
            "order_type": order_type,
            "side": side,
            "quantity": quantity,
            "stubbed": bool(result.get("stubbed")),
            "submitted": not bool(result.get("stubbed")),
            "network_effect": "STUBBED" if result.get("stubbed") else "TESTNET",
            "live_order_effect": "NONE",
        }
        self.submit_attempts.append(attempt)
        return attempt

    def to_dict(self) -> dict[str, Any]:
        return {
            "PORT_KIND": self.PORT_KIND,
            "EXECUTION_MODE": self.EXECUTION_MODE,
            "authorized": self.authorized,
            "stubbed": self.stubbed,
            "venue": self.venue,
            "submit_attempt_count": len(self.submit_attempts),
            "OWNER": self.OWNER,
        }


def construct_productive_testnet_execution_port_v1(
    *,
    authorized: bool,
    transport: TestnetTransportPortV1 | None = None,
    stubbed: bool = True,
) -> ProductiveTestnetExecutionPortV1:
    if not authorized:
        raise ActualStartPortError("PORT_CONSTRUCTION_REQUIRES_AUTHORIZATION")
    bound_transport: TestnetTransportPortV1
    if transport is None:
        if not stubbed:
            raise ActualStartPortError("NON_STUBBED_TRANSPORT_REQUIRED")
        bound_transport = StubbedTestnetTransportV1()
    else:
        bound_transport = transport
    return ProductiveTestnetExecutionPortV1(
        authorized=True,
        stubbed=stubbed,
        transport=bound_transport,
    )
