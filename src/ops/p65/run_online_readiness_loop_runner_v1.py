from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p64 import P64RunContextV1, run_online_readiness_runner_v1


@dataclass(frozen=True)
class P65RunContextV1:
    """
    Paper/Shadow loop runner for Online Readiness (P64).
    Safety:
      - live/record must remain blocked downstream (P64/P63/P62/P61 enforce PermissionError).
      - Evidence is written only when out_dir is set.
    """

    mode: str  # "paper" | "shadow" (anything else is rejected)
    run_id: str
    out_dir: Optional[Path] = None
    loops: int = 3
    allow_bull_strategies: Optional[List[str]] = None
    allow_bear_strategies: Optional[List[str]] = None


def _ensure_mode(mode: str) -> None:
    if mode not in ("paper", "shadow"):
        raise PermissionError(f"p65: only paper/shadow allowed (got mode={mode!r})")


def _loop_out_dir(base: Path, i: int) -> Path:
    return base / f"loop_{i:03d}"


def run_online_readiness_loop_runner_v1(
    prices: List[float], ctx: P65RunContextV1
) -> Dict[str, Any]:
    _ensure_mode(ctx.mode)
    if ctx.loops <= 0:
        raise ValueError("p65: loops must be >= 1")

    loops_out: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {
        "p65_run_id": ctx.run_id,
        "mode": ctx.mode,
        "loops": ctx.loops,
    }

    base_out_dir: Optional[Path] = ctx.out_dir
    if base_out_dir is not None:
        base_out_dir.mkdir(parents=True, exist_ok=True)
        meta["out_dir"] = str(base_out_dir)

    for i in range(ctx.loops):
        loop_run_id = f"{ctx.run_id}-loop-{i:03d}"
        loop_out_dir = _loop_out_dir(base_out_dir, i) if base_out_dir is not None else None

        p64_ctx = P64RunContextV1(
            mode=ctx.mode,
            run_id=loop_run_id,
            out_dir=loop_out_dir,
            allow_bull_strategies=ctx.allow_bull_strategies,
            allow_bear_strategies=ctx.allow_bear_strategies,
        )
        out = run_online_readiness_runner_v1(prices, p64_ctx)
        loops_out.append(out)

    result = {"meta": meta, "loops": loops_out}
    return to_jsonable_v1(result)
