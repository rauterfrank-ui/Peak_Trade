"""P72: Unified shadow loop pack — P71 health gate + P68 shadow loop (paper/shadow only)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

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
    primary_evidence_enforce: bool = False
    scheduler_boundary_enforce: bool = False
    scheduler_preflight_status: Optional[Mapping[str, Any]] = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _maybe_finalize_pack_primary_evidence(ctx: P72PackContextV1) -> None:
    if not ctx.primary_evidence_enforce:
        return
    if not ctx.out_dir.is_dir():
        raise RuntimeError(f"ERR: primary evidence pack root missing: {ctx.out_dir}")
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import finalize_primary_evidence_root

    ok, msg = finalize_primary_evidence_root(ctx.out_dir)
    if not ok:
        raise RuntimeError(f"ERR: primary evidence pack finalize failed: {msg}")


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
        primary_evidence_enforce=ctx.primary_evidence_enforce,
        scheduler_boundary_enforce=ctx.scheduler_boundary_enforce,
        scheduler_preflight_status=ctx.scheduler_preflight_status,
    )
    loop_out = run_shadow_session_scheduler_v1(p67_ctx)

    result = {
        "p72_version": "v1",
        "gate_ok": True,
        "gate_report": gate_report,
        "loop_run": loop_out,
    }
    _maybe_finalize_pack_primary_evidence(ctx)
    return result
