"""P108 OKX adapter smoke tests (mocks only)."""

from __future__ import annotations

from src.execution.adapters.base_v1 import OrderIntentV1
from src.execution.adapters.providers.okx_v1 import OKXExecutionAdapterV1


def test_p108_okx_adapter_smoke_place_order_and_caps() -> None:
    ad = OKXExecutionAdapterV1()
    caps = ad.capabilities()
    assert caps.name == "okx"
    assert "spot" in caps.markets
    assert "perp" in caps.markets
    assert caps.supports_batch_cancel is True
    assert caps.supports_reduce_only is True

    out = ad.place_order(
        OrderIntentV1(
            symbol="BTC-USD",
            side="buy",
            qty=1.0,
            order_type="market",
            client_id="cid1",
        )
    )
    assert out.ok is True
    assert out.adapter == "okx"
    assert out.client_id == "cid1"
    assert out.order_id is not None
    assert ad.cancel_all(symbol="BTC-USD") == 1
