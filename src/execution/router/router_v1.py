"""P112: Execution router v1 (registry + hard mode guard, mocks only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.execution.adapters.base_v1 import (
    ExecutionAdapterV1,
    OrderIntentV1,
    OrderResultV1,
)
from src.execution.adapters.registry_v1 import select_execution_adapter_v1

_ALLOWED_MODES = {"shadow", "paper"}  # hard guardrail


@dataclass(frozen=True)
class ExecutionRouterContextV1:
    mode: str = "shadow"
    adapter_name: str = "mock"
    # Optional: enforce market scoping at router boundary (kept simple for v1)
    market: Optional[str] = None
    dry_run: bool = True


class ExecutionRouterV1:
    def __init__(self, ctx: ExecutionRouterContextV1, adapter: ExecutionAdapterV1) -> None:
        self._ctx = ctx
        self._adapter = adapter

    @property
    def ctx(self) -> ExecutionRouterContextV1:
        return self._ctx

    @property
    def adapter(self) -> ExecutionAdapterV1:
        return self._adapter

    def place_order(self, intent: OrderIntentV1) -> OrderResultV1:
        return self._adapter.place_order(intent)

    def cancel_all(self, symbol: Optional[str] = None) -> int:
        return self._adapter.cancel_all(symbol=symbol)

    def batch_cancel(self, order_ids: List[str]) -> int:
        return self._adapter.batch_cancel(order_ids=order_ids)


def build_execution_router_v1(ctx: ExecutionRouterContextV1) -> ExecutionRouterV1:
    if ctx.mode not in _ALLOWED_MODES:
        raise ValueError(f"router mode must be one of {sorted(_ALLOWED_MODES)}; got {ctx.mode!r}")

    adapter = select_execution_adapter_v1(ctx.adapter_name, market=ctx.market)
    return ExecutionRouterV1(ctx=ctx, adapter=adapter)
