from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p61 import P61RunContextV1, run_online_readiness_v1
from src.ops.p62 import P62RunContextV1, run_online_readiness_shadow_session_v1


@dataclass(frozen=True)
class P63RunContextV1:
    mode: str  # "paper" | "shadow" only
    run_id: str
    out_dir: Optional[Path] = None
    # allowlists (deny-by-default)
    allow_bull_strategies: Optional[List[str]] = None
    allow_bear_strategies: Optional[List[str]] = None


def run_online_readiness_shadow_runner_v1(
    prices: List[float], ctx: P63RunContextV1
) -> dict[str, Any]:
    """
    Canonical paper/shadow runner that composes P61 readiness + P62 shadow plan.
    Hard-blocks live/record. Writes evidence only when out_dir is set.
    Returns dict-only JSONable boundary.
    """
    if ctx.mode not in ("paper", "shadow"):
        raise PermissionError(f"mode={ctx.mode} is not allowed (paper/shadow only)")

    p61_ctx = P61RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies or [],
        allow_bear_strategies=ctx.allow_bear_strategies or [],
    )
    p61 = run_online_readiness_v1(prices, p61_ctx)

    p62_ctx = P62RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies,
        allow_bear_strategies=ctx.allow_bear_strategies,
    )
    p62 = run_online_readiness_shadow_session_v1(prices, p62_ctx)

    out = {
        "version": "p63_shadow_runner_v1",
        "meta": {
            "p63_run_id": ctx.run_id,
            "mode": ctx.mode,
            "out_dir": str(ctx.out_dir) if ctx.out_dir else None,
        },
        "readiness_report": p61.get("report"),
        "shadow_plan": p62.get("shadow_plan"),
        "switch": p61.get("switch") or p62.get("switch"),
    }
    return to_jsonable_v1(out)
