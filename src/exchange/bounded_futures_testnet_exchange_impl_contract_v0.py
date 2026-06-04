"""Bounded Futures Testnet exchange implementation contract (v0).

Offline contract for futures testnet exchange impl surface binding. No network I/O,
no credentials, no orders. Does not authorize execute; FUTURES_SESSION_AUTHORIZED_NOW
remains false via ops contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    ADAPTER_NETWORK_CALLS_ALLOWED,
    BoundedFuturesTestnetAdapterBinding,
    FUTURES_TESTNET_ENDPOINT_ALLOWLIST,
    default_offline_adapter_binding,
    validate_futures_testnet_adapter_binding,
)
from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_EXCHANGE_IMPL_CONTRACT_V0=true"
EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED = False
EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW = False
DEFAULT_IMPL_MODULE = "src.exchange.bounded_futures_testnet_exchange_impl_contract_v0"
DEFAULT_IMPL_CLASS = "BoundedFuturesTestnetExchangeImplStub"


@dataclass(frozen=True)
class BoundedFuturesTestnetExchangeImplDescriptor:
    impl_module: str
    impl_class: str
    adapter_binding: BoundedFuturesTestnetAdapterBinding
    network_calls_allowed: bool
    execute_authorized: bool
    testnet_scoped: bool
    supports_reduce_only: bool
    supports_position_read: bool
    supports_margin_read: bool


def default_offline_exchange_impl_descriptor() -> BoundedFuturesTestnetExchangeImplDescriptor:
    """Contract-default stub descriptor; no live exchange client."""
    binding = default_offline_adapter_binding()
    return BoundedFuturesTestnetExchangeImplDescriptor(
        impl_module=DEFAULT_IMPL_MODULE,
        impl_class=DEFAULT_IMPL_CLASS,
        adapter_binding=binding,
        network_calls_allowed=False,
        execute_authorized=False,
        testnet_scoped=True,
        supports_reduce_only=binding.reduce_only_supported,
        supports_position_read=True,
        supports_margin_read=True,
    )


class BoundedFuturesTestnetExchangeImplStub:
    """Offline stub; all exchange operations fail-closed (no network)."""

    def __init__(self, descriptor: BoundedFuturesTestnetExchangeImplDescriptor) -> None:
        self._descriptor = descriptor

    @property
    def descriptor(self) -> BoundedFuturesTestnetExchangeImplDescriptor:
        return self._descriptor

    def place_order_fail_closed(self) -> None:
        raise RuntimeError("exchange impl stub: place_order not authorized")

    def cancel_order_fail_closed(self) -> None:
        raise RuntimeError("exchange impl stub: cancel_order not authorized")


def validate_futures_testnet_exchange_impl_descriptor(
    descriptor: BoundedFuturesTestnetExchangeImplDescriptor,
) -> dict[str, Any]:
    """Fail-closed exchange impl validation (offline, no I/O)."""
    result: dict[str, Any] = {
        "exchange_impl_contract_pass": False,
        "adapter_binding_pass": False,
        "fail_reasons": [],
    }

    if descriptor.network_calls_allowed:
        result["fail_reasons"].append("network_calls_allowed must be false")
    if descriptor.execute_authorized:
        result["fail_reasons"].append("execute_authorized must be false")
    if EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW:
        result["fail_reasons"].append("EXCHANGE_IMPL_EXECUTE_AUTHORIZED_NOW must be false")
    if EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("EXCHANGE_IMPL_NETWORK_CALLS_ALLOWED must be false")
    if ADAPTER_NETWORK_CALLS_ALLOWED:
        result["fail_reasons"].append("ADAPTER_NETWORK_CALLS_ALLOWED must be false")
    if not descriptor.testnet_scoped:
        result["fail_reasons"].append("testnet_scoped must be true")
    if not descriptor.impl_module:
        result["fail_reasons"].append("impl_module required")
    if not descriptor.impl_class:
        result["fail_reasons"].append("impl_class required")
    if not descriptor.supports_reduce_only:
        result["fail_reasons"].append("supports_reduce_only must be true")
    if not descriptor.supports_position_read:
        result["fail_reasons"].append("supports_position_read must be true")
    if not descriptor.supports_margin_read:
        result["fail_reasons"].append("supports_margin_read must be true")

    adapter_result = validate_futures_testnet_adapter_binding(descriptor.adapter_binding)
    result["adapter_binding_pass"] = adapter_result["adapter_binding_pass"]
    result["fail_reasons"].extend(adapter_result["fail_reasons"])

    allowlist = descriptor.adapter_binding.endpoint_allowlist
    if not allowlist.issubset(FUTURES_TESTNET_ENDPOINT_ALLOWLIST):
        result["fail_reasons"].append("adapter endpoint_allowlist exceeds futures allowlist")

    if FUTURES_SESSION_AUTHORIZED_NOW:
        result["fail_reasons"].append("FUTURES_SESSION_AUTHORIZED_NOW must be false")

    result["exchange_impl_contract_pass"] = not result["fail_reasons"]
    return result
