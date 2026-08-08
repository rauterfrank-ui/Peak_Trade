"""Productive private Testnet transport — stubbable boundary, live hard-block."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.venue_adapter_anti_corruption_v1 import (
    prove_venue_adapter_anti_corruption_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.account_endpoint_binding_v1 import (
    assert_endpoint_allowlisted_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_VENUE,
    SIMULATION_HEADER_NAME,
    SIMULATION_HEADER_VALUE,
    TESTNET_PRIVATE_REST_BASE,
)


class ActualStartTransportError(RuntimeError):
    """Fail-closed transport violation."""


class TestnetTransportPortV1(Protocol):
    def request(
        self,
        *,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


@dataclass
class StubbedTestnetTransportV1:
    """Acceptance-gate transport: records intents, never opens sockets."""

    rest_base: str = TESTNET_PRIVATE_REST_BASE
    calls: list[dict[str, Any]] = field(default_factory=list)
    next_effect_pending: str = "FIRST_PERMITTED_TESTNET_SIDE_EFFECT"

    def request(
        self,
        *,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assert_endpoint_allowlisted_v1(endpoint=endpoint, rest_base=self.rest_base)
        if method.upper() not in {"GET", "POST"}:
            raise ActualStartTransportError(f"METHOD_FORBIDDEN:{method}")
        record = {
            "method": method.upper(),
            "endpoint": endpoint,
            "rest_base": self.rest_base,
            "simulation_header": {SIMULATION_HEADER_NAME: SIMULATION_HEADER_VALUE},
            "venue": CANONICAL_VENUE,
            "network_effect": "STUBBED",
            "submitted": False,
        }
        self.calls.append(record)
        return {
            "ok": True,
            "http_status": 200,
            "stubbed": True,
            "account_identity": "acct-uid-testnet-demo",
            "next_effect": self.next_effect_pending,
        }


@dataclass
class ProductiveTestnetTransportV1:
    """Real transport surface — refuses unless allow_real_network=True and client bound."""

    rest_base: str = TESTNET_PRIVATE_REST_BASE
    allow_real_network: bool = False
    http_client: Callable[..., dict[str, Any]] | None = None
    bound_client_kind: str = ""

    def request(
        self,
        *,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assert_endpoint_allowlisted_v1(endpoint=endpoint, rest_base=self.rest_base)
        anti = prove_venue_adapter_anti_corruption_v1()
        if anti.get("ok") is not True:
            raise ActualStartTransportError("CAP_11_4_ANTI_CORRUPTION_REQUIRED")
        if not self.allow_real_network:
            raise ActualStartTransportError("REAL_NETWORK_FORBIDDEN_WITHOUT_EXPLICIT_ALLOW")
        if self.http_client is None:
            raise ActualStartTransportError("HTTP_CLIENT_NOT_BOUND")
        result = self.http_client(
            method=method,
            url=f"{self.rest_base}{endpoint}",
            body=body or {},
            headers={SIMULATION_HEADER_NAME: SIMULATION_HEADER_VALUE},
        )
        if not isinstance(result, dict):
            raise ActualStartTransportError("HTTP_CLIENT_RESULT_NOT_OBJECT")
        return result


def build_stubbed_testnet_transport_v1() -> StubbedTestnetTransportV1:
    anti = prove_venue_adapter_anti_corruption_v1()
    if anti.get("ok") is not True:
        raise ActualStartTransportError("CAP_11_4_ANTI_CORRUPTION_REQUIRED")
    return StubbedTestnetTransportV1()


def build_productive_testnet_transport_v1(
    *,
    http_client: Callable[..., dict[str, Any]],
    allow_real_network: bool = True,
    rest_base: str = TESTNET_PRIVATE_REST_BASE,
    bound_client_kind: str = "BOUND_REAL_TESTNET_HTTP_CLIENT",
) -> ProductiveTestnetTransportV1:
    """Bind the real Testnet HTTP client to the productive transport boundary."""
    anti = prove_venue_adapter_anti_corruption_v1()
    if anti.get("ok") is not True:
        raise ActualStartTransportError("CAP_11_4_ANTI_CORRUPTION_REQUIRED")
    if http_client is None:
        raise ActualStartTransportError("HTTP_CLIENT_NOT_BOUND")
    if not allow_real_network:
        raise ActualStartTransportError("REAL_NETWORK_FORBIDDEN_WITHOUT_EXPLICIT_ALLOW")
    return ProductiveTestnetTransportV1(
        rest_base=rest_base,
        allow_real_network=True,
        http_client=http_client,
        bound_client_kind=bound_client_kind,
    )
