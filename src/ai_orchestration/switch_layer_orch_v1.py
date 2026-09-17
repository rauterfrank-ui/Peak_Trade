from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.ai.switch_layer.switch_layer_v1 import decide_regime_v1
from src.ai.switch_layer.types_v1 import SwitchDecisionV1


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
    Orchestration adapter: compute deterministic regime.

    The former p53 evidence writer is removed. ``ctx`` remains the public
    adapter contract for later reuse and is not an evidence authority.

    Safety invariants:
    - deterministic
    - no model calls
    - no network
    """
    _ = ctx
    return decide_regime_v1(returns)
