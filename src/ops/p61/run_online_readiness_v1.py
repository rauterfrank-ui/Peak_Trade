from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p58.switch_layer_online_readiness_v1 import (
    P58RunContextV1,
    run_switch_layer_online_readiness_v1,
)
from src.ops.p61.online_readiness_contract_v1 import (
    ReadinessCheckV1,
    build_online_readiness_report_v1,
)


@dataclass(frozen=True)
class P61RunContextV1:
    mode: str  # "paper" | "shadow"
    run_id: str
    out_dir: Optional[Path] = None
    allow_bull_strategies: Optional[List[str]] = None
    allow_bear_strategies: Optional[List[str]] = None


def run_online_readiness_v1(prices: List[float], ctx: P61RunContextV1) -> Dict[str, Any]:
    if ctx.mode not in ("paper", "shadow"):
        raise PermissionError(f"P61 only supports paper/shadow. mode={ctx.mode}")

    # Run existing readiness pipeline (already blocks live/record)
    p58_ctx = P58RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies or [],
        allow_bear_strategies=ctx.allow_bear_strategies or [],
    )
    res = run_switch_layer_online_readiness_v1(prices, p58_ctx)

    checks = [
        ReadinessCheckV1(
            name="paper_shadow_only",
            ok=True,
            detail="live/record not supported by this entrypoint",
        ),
        ReadinessCheckV1(
            name="evidence_written_if_outdir",
            ok=bool(ctx.out_dir),
            detail="out_dir set => evidence pack expected"
            if ctx.out_dir
            else "out_dir not set => no evidence written",
        ),
        ReadinessCheckV1(
            name="routing_deny_by_default_ok",
            ok=res.get("routing", {}).get("ai_mode", "") in ("disabled", "shadow"),
            detail=f"ai_mode={res.get('routing', {}).get('ai_mode', 'N/A')}",
        ),
    ]

    report = build_online_readiness_report_v1(checks=checks)

    out = {
        "report": report,
        "switch": res,
        "meta": {"p61_run_id": ctx.run_id, "mode": ctx.mode},
    }
    return to_jsonable_v1(out)
