"""P27 — Execution integration wiring (feature-flag adapter)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from src.execution.p24.config import ExecutionModelV2Config
from src.execution.p24.execution_model_v2 import (
    ExecutionModelV2,
    MarketSnapshot as P24MarketSnapshot,
)
from src.execution.p26.adapter import ExecutionAdapterV1, FillRecord
from src.execution.p26.types import AdapterOrder


@dataclass(frozen=True)
class P27ExecutionWiringConfig:
    enabled: bool = False
    execution_mode: str = "legacy"  # "legacy" | "p26_v1"
    p24_config: Optional[ExecutionModelV2Config] = None


def build_p26_adapter(cfg: P27ExecutionWiringConfig) -> ExecutionAdapterV1:
    if cfg.p24_config is None:
        raise ValueError("p24_config is required when using execution_mode=p26_v1")
    model = ExecutionModelV2(cfg.p24_config)
    return ExecutionAdapterV1(model=model, cfg=cfg.p24_config)


def execute_bar_via_p26(
    adapter: ExecutionAdapterV1,
    bar: P24MarketSnapshot,
    orders: Iterable[AdapterOrder],
) -> List[FillRecord]:
    return adapter.execute_bar(snapshot=bar, orders=list(orders))
