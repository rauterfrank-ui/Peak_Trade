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


def route_from_switch_decision_with_config_v1(
    *,
    decision: SwitchDecisionV1,
    cfg: object,
) -> RoutingDecisionV1:
    """
    P56 helper: route using allowlist from SwitchLayerConfigV1.
    Duck-typed cfg: expects allow_bull_strategies, allow_bear_strategies (tuple).
    """
    allow_bull = tuple(getattr(cfg, "allow_bull_strategies", ()) or ())
    allow_bear = tuple(getattr(cfg, "allow_bear_strategies", ()) or ())
    return route_from_switch_decision_v1(
        decision=decision,
        allow_bull=allow_bull if allow_bull else None,
        allow_bear=allow_bear if allow_bear else None,
    )
