from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from src.ai.switch_layer.config_v1 import SwitchLayerConfigV1
from src.ai.switch_layer.switch_layer_v1 import decide_regime_v1
from src.ai_orchestration.switch_layer_routing_v1 import route_from_switch_decision_v1
from src.ops.p53.switch_layer_evidence_v1 import write_switch_layer_evidence_pack_v1


@dataclass(frozen=True)
class P57RunContextV1:
    """
    Paper/Shadow orchestration context for Switch-Layer.
    Safety model:
      - paper/shadow may compute + route + optionally write evidence (requires out_dir).
      - live/record is deny-by-default at P57 (still requires P49/P50 to allow model calls elsewhere).
    """

    mode: str  # paper|shadow|live|record
    run_id: str
    out_dir: Optional[Path] = None
    # Allowlists (deny-by-default). Empty/None => no strategies allowed.
    allow_bull_strategies: Sequence[str] = ()
    allow_bear_strategies: Sequence[str] = ()
    # Optional config overrides (keep deterministic)
    cfg: Optional[SwitchLayerConfigV1] = None


def _ensure_outdir(ctx: P57RunContextV1) -> Optional[Path]:
    if ctx.out_dir is None:
        return None
    p = Path(ctx.out_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_switch_layer_paper_shadow_v1(
    prices: Sequence[float], ctx: P57RunContextV1
) -> Dict[str, Any]:
    """
    Runs:
      1) decide_regime_v1 (switch-layer decision)
      2) route_from_switch_decision_v1 (routing with allowlists)
      3) optional evidence pack write when ctx.out_dir is set

    Returns dict:
      {"regime": MarketRegimeV1, "decision": SwitchDecisionV1, "routing": RoutingDecisionV1, "meta": {...}}
    """
    mode = (ctx.mode or "").lower().strip()
    if mode not in {"paper", "shadow", "live", "record"}:
        raise ValueError(f"invalid mode: {ctx.mode!r}")

    # Hard deny at this layer for live/record (paper/shadow only).
    if mode in {"live", "record"}:
        raise PermissionError(
            "P57 switch-layer runner is not allowed in live/record (deny-by-default)"
        )

    cfg = ctx.cfg or SwitchLayerConfigV1()
    decision = decide_regime_v1(prices, cfg=cfg)
    regime = decision.regime

    allow_bull = tuple(ctx.allow_bull_strategies) if ctx.allow_bull_strategies else None
    allow_bear = tuple(ctx.allow_bear_strategies) if ctx.allow_bear_strategies else None
    routing = route_from_switch_decision_v1(
        decision=decision,
        allow_bull=allow_bull,
        allow_bear=allow_bear,
    )

    out_dir = _ensure_outdir(ctx)
    meta: Dict[str, Any] = {
        "p57_run_id": ctx.run_id,
        "mode": mode,
        "allow_bull": list(ctx.allow_bull_strategies),
        "allow_bear": list(ctx.allow_bear_strategies),
    }
    if out_dir is not None:
        write_switch_layer_evidence_pack_v1(
            out_dir=out_dir,
            run_id=ctx.run_id,
            meta=meta,
            decision=decision,
            routing=routing,
            regime=regime,
        )

    return {"regime": regime, "decision": decision, "routing": routing, "meta": meta}
