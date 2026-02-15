from __future__ import annotations

from dataclasses import dataclass

from src.ops.common import to_jsonable_v1
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ops.p57 import P57RunContextV1, run_switch_layer_paper_shadow_v1


@dataclass(frozen=True)
class P58RunContextV1:
    """
    P58 runner = safety/readiness probe for switch-layer under paper/shadow only.

    - Hard-deny mode in {"live","record"}.
    - Uses P57 entrypoint to produce decision+routing + evidence pack.
    - Adds a small 'readiness' meta dict and returns outputs.
    """

    mode: str  # "paper" | "shadow"
    run_id: str
    out_dir: Optional[Path] = None
    allow_bull_strategies: Optional[List[str]] = None
    allow_bear_strategies: Optional[List[str]] = None


def run_switch_layer_online_readiness_v1(
    prices: List[float], ctx: P58RunContextV1
) -> Dict[str, Any]:
    if ctx.mode in ("live", "record"):
        raise PermissionError("P58: live/record not allowed")

    p57_ctx = P57RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies or [],
        allow_bear_strategies=ctx.allow_bear_strategies or [],
    )
    out = run_switch_layer_paper_shadow_v1(prices, p57_ctx)

    readiness = {
        "p58_run_id": ctx.run_id,
        "mode": ctx.mode,
        "has_out_dir": bool(ctx.out_dir),
        "allow_bull_n": len(ctx.allow_bull_strategies or []),
        "allow_bear_n": len(ctx.allow_bear_strategies or []),
        "note": "AI routing remains deny-by-default unless P49/P50 gates permit + allowlists set.",
    }

    res = {"readiness": readiness, **out}
    return to_jsonable_v1(res)
