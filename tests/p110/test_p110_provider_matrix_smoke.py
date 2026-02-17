"""P110: Provider adapter capability matrix smoke (mocks only)."""

from __future__ import annotations

from typing import List, Type

import pytest

from src.execution.adapters.base_v1 import (
    AdapterCapabilitiesV1,
    ExecutionAdapterV1,
    OrderIntentV1,
    OrderResultV1,
)


def _provider_classes() -> List[Type[ExecutionAdapterV1]]:
    # NOTE: keep imports inside to avoid import-time side effects; these are mocks-only.
    from src.execution.adapters.mock_v1 import MockExecutionAdapterV1
    from src.execution.adapters.providers.bybit_v1 import BybitExecutionAdapterV1
    from src.execution.adapters.providers.coinbase_v1 import CoinbaseExecutionAdapterV1
    from src.execution.adapters.providers.okx_v1 import OKXExecutionAdapterV1

    return [
        MockExecutionAdapterV1,
        CoinbaseExecutionAdapterV1,
        OKXExecutionAdapterV1,
        BybitExecutionAdapterV1,
    ]


def _make_adapter(cls: Type[ExecutionAdapterV1]) -> ExecutionAdapterV1:
    if cls.__name__ == "MockExecutionAdapterV1":
        return cls(
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
    return cls()  # type: ignore[call-arg]


@pytest.mark.parametrize("cls", _provider_classes())
def test_provider_adapter_matrix_smoke(cls: Type[ExecutionAdapterV1]) -> None:
    adapter = _make_adapter(cls)

    caps = adapter.capabilities()
    assert isinstance(caps.name, str) and caps.name.strip()
    assert isinstance(caps.markets, list) and len(caps.markets) >= 1
    assert isinstance(caps.order_types, list) and len(caps.order_types) >= 1

    # bool flags (defensive)
    for k in [
        "supports_post_only",
        "supports_reduce_only",
        "supports_batch_cancel",
        "supports_cancel_all",
        "supports_ws_orders",
        "supports_ws_fills",
    ]:
        v = getattr(caps, k, None)
        assert isinstance(v, bool), f"{cls.__name__}.{k} must be bool, got {type(v)}"

    intent = OrderIntentV1(
        symbol=caps.markets[0],
        side="buy",
        order_type=caps.order_types[0],
        qty=1.0,
        price=None,
        client_id="p110_smoke",
        post_only=False,
        reduce_only=False,
    )

    res = adapter.place_order(intent)
    assert isinstance(res, OrderResultV1)
    assert res.ok is True
    assert isinstance(res.adapter, str) and res.adapter.strip()
    assert isinstance(res.order_id, str) and res.order_id.strip()
    assert res.client_id == "p110_smoke"

    n = adapter.cancel_all(symbol=None)
    assert isinstance(n, int) and n >= 0

    order_ids = ["o1", "o2", "o3"]
    m = adapter.batch_cancel(order_ids)
    assert isinstance(m, int) and m >= 0
