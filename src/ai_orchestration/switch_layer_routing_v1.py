from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from src.ai.switch_layer.types_v1 import MarketRegimeV1, SwitchDecisionV1


@dataclass(frozen=True)
class RoutingDecisionV1:
    # deny-by-default: explicit allow-lists, otherwise empty
    allowed_strategies: tuple[str, ...] = ()
    ai_mode: str = "disabled"  # disabled|shadow|paper (never "live" here)
    reason: str = "deny_by_default"


def route_from_switch_decision_v1(
    *,
    decision: SwitchDecisionV1,
    allow_bull: Optional[Sequence[str]] = None,
    allow_bear: Optional[Sequence[str]] = None,
) -> RoutingDecisionV1:
    """
    Deterministic routing decision based on switch-layer output.
    Safety: deny-by-default unless allow_* is provided.
    """
    if decision.regime == MarketRegimeV1.BULL and allow_bull:
        return RoutingDecisionV1(tuple(allow_bull), ai_mode="shadow", reason="bull_allowlist")
    if decision.regime == MarketRegimeV1.BEAR and allow_bear:
        return RoutingDecisionV1(tuple(allow_bear), ai_mode="shadow", reason="bear_allowlist")
    return RoutingDecisionV1()
