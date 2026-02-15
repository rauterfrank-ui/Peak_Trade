from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.ai.switch_layer.switch_layer_v1 import decide_regime_v1
from src.ai.switch_layer.types_v1 import SwitchDecisionV1
from src.ops.p53.switch_layer_evidence_v1 import write_switch_layer_evidence_v1


@dataclass(frozen=True)
class SwitchLayerContextV1:
    symbol: str
    timeframe: str
    out_dir: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def run_switch_layer_orch_v1(
    *,
    returns: List[float],
    ctx: SwitchLayerContextV1,
) -> SwitchDecisionV1:
    """
    Orchestration adapter: compute deterministic regime + optionally write evidence.

    Safety invariants:
    - deterministic
    - no model calls
    - no network
    - no writes unless ctx.out_dir is set
    """
    decision = decide_regime_v1(returns)

    if ctx.out_dir:
        write_switch_layer_evidence_v1(
            out_dir=ctx.out_dir,
            symbol=ctx.symbol,
            timeframe=ctx.timeframe,
            decision=decision,
            meta=ctx.meta,
        )

    return decision
