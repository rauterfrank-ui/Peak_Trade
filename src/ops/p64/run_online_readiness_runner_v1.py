from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p63 import P63RunContextV1, run_online_readiness_shadow_runner_v1


@dataclass(frozen=True)
class P64RunContextV1:
    mode: str  # "paper" | "shadow"
    run_id: str
    out_dir: Optional[Path] = None
    allow_bull_strategies: Optional[List[str]] = None
    allow_bear_strategies: Optional[List[str]] = None


def run_online_readiness_runner_v1(prices: List[float], ctx: P64RunContextV1) -> Dict[str, Any]:
    if ctx.mode in ("live", "record"):
        raise PermissionError("P64 is paper/shadow only. live/record are hard-blocked.")

    p63_ctx = P63RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies or [],
        allow_bear_strategies=ctx.allow_bear_strategies or [],
    )
    out = run_online_readiness_shadow_runner_v1(prices, p63_ctx)

    # Ensure stable dict-only boundary
    return to_jsonable_v1(
        {
            "meta": {"p64_run_id": ctx.run_id, "mode": ctx.mode},
            "p63": out,
        }
    )
