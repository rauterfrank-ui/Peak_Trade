"""P111: Execution adapter registry + selector (mocks only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from src.execution.adapters.base_v1 import AdapterCapabilitiesV1, ExecutionAdapterV1
from src.execution.adapters.mock_v1 import MockExecutionAdapterV1
from src.execution.adapters.providers.bybit_v1 import BybitExecutionAdapterV1
from src.execution.adapters.providers.coinbase_v1 import CoinbaseExecutionAdapterV1
from src.execution.adapters.providers.okx_v1 import OKXExecutionAdapterV1


@dataclass(frozen=True)
class AdapterRegistryEntryV1:
    name: str
    adapter_cls: Type[ExecutionAdapterV1]
    markets: List[str]


def build_adapter_registry_v1() -> Dict[str, AdapterRegistryEntryV1]:
    # NOTE: mocks-only providers; no network calls, no keys
    entries: List[AdapterRegistryEntryV1] = [
        AdapterRegistryEntryV1(name="mock", adapter_cls=MockExecutionAdapterV1, markets=["spot"]),
        AdapterRegistryEntryV1(
            name="coinbase",
            adapter_cls=CoinbaseExecutionAdapterV1,
            markets=["spot"],
        ),
        AdapterRegistryEntryV1(
            name="okx", adapter_cls=OKXExecutionAdapterV1, markets=["spot", "perp"]
        ),
        AdapterRegistryEntryV1(
            name="bybit",
            adapter_cls=BybitExecutionAdapterV1,
            markets=["spot", "perp"],
        ),
    ]
    return {e.name: e for e in entries}


def _instantiate_adapter(entry: AdapterRegistryEntryV1) -> ExecutionAdapterV1:
    if entry.adapter_cls is MockExecutionAdapterV1:
        return entry.adapter_cls(
            _caps=AdapterCapabilitiesV1(
                name="mock",
                markets=["spot"],
                order_types=["market", "limit"],
                supports_post_only=True,
                supports_reduce_only=False,
                supports_batch_cancel=True,
                supports_cancel_all=True,
                supports_ws_orders=False,
                supports_ws_fills=False,
            )
        )
    return entry.adapter_cls()  # type: ignore[call-arg]


def select_execution_adapter_v1(name: str, *, market: Optional[str] = None) -> ExecutionAdapterV1:
    reg = build_adapter_registry_v1()
    if name not in reg:
        raise ValueError(f"unknown_adapter: {name} (known={sorted(reg.keys())})")
    entry = reg[name]
    if market is not None and market not in entry.markets:
        raise ValueError(
            f"unsupported_market: {market} for adapter={name} (supports={entry.markets})"
        )
    return _instantiate_adapter(entry)
