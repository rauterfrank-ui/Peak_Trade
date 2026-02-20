from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.live.feature_activation import evaluate_feature_activation


@dataclass(frozen=True)
class OperatorWiringInput:
    enabled: bool = False
    armed: bool = False
    confirm_token_present: bool = False

    allow_double_play: bool = False
    allow_dynamic_leverage: bool = False

    # Optional tuning / signals
    strength: float = 0.0
    switch_gate: Optional[Dict[str, Any]] = None
    dynamic_leverage_cfg: Optional[Dict[str, Any]] = None


def build_live_context_from_operator(*, inp: OperatorWiringInput) -> Dict[str, Any]:
    """
    SAFE DEFAULT OFF.
    Builds the `context` dict used by live_gates, including derived feature enable flags.
    Deterministic, no IO, no env reads.
    """
    ctx: Dict[str, Any] = {
        "enabled": bool(inp.enabled),
        "armed": bool(inp.armed),
        "confirm_token_present": bool(inp.confirm_token_present),
        "allow_double_play": bool(inp.allow_double_play),
        "allow_dynamic_leverage": bool(inp.allow_dynamic_leverage),
        "strength": float(inp.strength),
    }
    if inp.switch_gate is not None:
        ctx["switch_gate"] = dict(inp.switch_gate)
    if inp.dynamic_leverage_cfg is not None:
        ctx["dynamic_leverage_cfg"] = dict(inp.dynamic_leverage_cfg)

    act = evaluate_feature_activation(context=ctx)
    # Derived flags consumed by the feature integrations (still SAFE default OFF)
    ctx["double_play_enabled"] = bool(act.allow_double_play)
    ctx["dynamic_leverage_enabled"] = bool(act.allow_dynamic_leverage)
    # Also keep activation details for auditability
    ctx["_features_activation_details"] = dict(act.details)

    return ctx
