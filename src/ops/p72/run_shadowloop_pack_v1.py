"""P72: Unified shadow loop pack — P71 health gate + P68 shadow loop (paper/shadow only)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from src.ops.p67 import run_shadow_session_scheduler_v1
from src.ops.p67.shadow_session_scheduler_v1 import P67RunContextV1
from src.ops.p71 import P71GateContextV1, run_online_readiness_health_gate_v1


@dataclass(frozen=True)
class P72PackContextV1:
    mode: str  # paper|shadow only
    run_id: str
    out_dir: Path
    allow_bull_strategies: Optional[list[str]] = None
    allow_bear_strategies: Optional[list[str]] = None
    iterations: int = 1
    interval_seconds: float = 0.0


def run_shadowloop_pack_v1(ctx: P72PackContextV1) -> Dict[str, Any]:
    """Run P71 health gate, then P67 shadow loop. Gate must PASS."""
    if ctx.mode not in ("paper", "shadow"):
        raise PermissionError("P72: only paper/shadow allowed (live/record hard-blocked)")

    # 1) P71 health gate
    p71_ctx = P71GateContextV1(
        mode=ctx.mode,
        run_id=f"{ctx.run_id}_gate",
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies,
        allow_bear_strategies=ctx.allow_bear_strategies,
    )
    prices = [0.001] * 240
    gate_report = run_online_readiness_health_gate_v1(prices, p71_ctx)
    if not gate_report.get("overall_ok"):
        return {
            "p72_version": "v1",
            "gate_ok": False,
            "gate_report": gate_report,
            "loop_run": None,
        }

    # 2) P67 shadow loop (uses internal default prices)
    p67_ctx = P67RunContextV1(
        mode=ctx.mode,
        run_id=f"{ctx.run_id}_loop",
        out_dir=ctx.out_dir,
        iterations=ctx.iterations,
        interval_seconds=ctx.interval_seconds,
    )
    loop_out = run_shadow_session_scheduler_v1(p67_ctx)

    return {
        "p72_version": "v1",
        "gate_ok": True,
        "gate_report": gate_report,
        "loop_run": loop_out,
    }
