from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p64.run_online_readiness_runner_v1 import (
    P64RunContextV1,
    run_online_readiness_runner_v1,
)
from src.ops.p65.run_online_readiness_loop_runner_v1 import (
    P65RunContextV1,
    run_online_readiness_loop_runner_v1,
)


@dataclass(frozen=True)
class P66RunContextV1:
    mode: str  # paper|shadow only
    run_id: str
    out_dir: Optional[Path] = None

    # routing allowlists (deny-by-default if empty/None)
    allow_bull_strategies: Optional[list[str]] = None
    allow_bear_strategies: Optional[list[str]] = None

    # operator loop controls
    loop: bool = False
    iterations: int = 1
    sleep_seconds: float = 0.0  # must be 0 in-contract for determinism


def _deny_live_record(mode: str) -> None:
    if mode in ("live", "record"):
        raise PermissionError("P66 operator entrypoint blocks mode=live/record (paper/shadow only)")


def run_online_readiness_operator_entrypoint_v1(
    prices: list[float],
    ctx: P66RunContextV1,
) -> Dict[str, Any]:
    """
    Operator boundary:
      - deny live/record
      - paper/shadow only
      - dict-only return (JSON-serializable)
      - deterministic in-contract (sleep_seconds must be 0)
      - optional evidence writes happen in downstream stages when out_dir is set
    """
    _deny_live_record(ctx.mode)

    if ctx.loop:
        if ctx.iterations < 1:
            raise ValueError("iterations must be >= 1 when loop=True")
        if ctx.sleep_seconds != 0.0:
            # keep contract deterministic; allow future extension behind explicit flags
            raise ValueError("sleep_seconds must be 0.0 for v1 determinism contract")

        p65_ctx = P65RunContextV1(
            mode=ctx.mode,
            run_id=ctx.run_id,
            out_dir=ctx.out_dir,
            allow_bull_strategies=ctx.allow_bull_strategies or [],
            allow_bear_strategies=ctx.allow_bear_strategies or [],
            loops=ctx.iterations,
        )
        out = run_online_readiness_loop_runner_v1(prices, p65_ctx)
        return to_jsonable_v1(
            {
                "meta": {"phase": "p66", "mode": ctx.mode, "run_id": ctx.run_id, "loop": True},
                "p65": out,
            }
        )

    # single-shot
    p64_ctx = P64RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies or [],
        allow_bear_strategies=ctx.allow_bear_strategies or [],
    )
    out = run_online_readiness_runner_v1(prices, p64_ctx)
    return to_jsonable_v1(
        {
            "meta": {"phase": "p66", "mode": ctx.mode, "run_id": ctx.run_id, "loop": False},
            "p64": out,
        }
    )
