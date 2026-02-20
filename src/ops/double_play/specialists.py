from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from src.ops.gates.switch_gate import SwitchGateConfig, SwitchGateState, step_switch_gate


@dataclass(frozen=True)
class DoublePlayDecision:
    enabled: bool
    active_specialist: str  # "bull"|"bear"
    switch_state: Dict[str, Any]
    reasons: Tuple[str, ...]
    details: Dict[str, Any]


def evaluate_double_play(*, context: Dict[str, Any]) -> DoublePlayDecision:
    """
    SAFE DEFAULT OFF.
    When enabled: update switch-gate state and return active specialist.
    This module does not execute trades; it only selects/annotates.
    """
    reasons = []
    details: Dict[str, Any] = {}

    enabled = bool(context.get("double_play_enabled", False))
    sg = context.get("switch_gate", {}) or {}

    score = float(sg.get("score", 0.0))
    state_d = sg.get("state", {}) or {}
    cfg_d = sg.get("cfg", {}) or {}

    state = SwitchGateState(
        active=str(state_d.get("active", "bull")),
        hold_remaining=int(state_d.get("hold_remaining", 0) or 0),
        cooldown_remaining=int(state_d.get("cooldown_remaining", 0) or 0),
    )
    cfg = SwitchGateConfig(
        hysteresis=float(cfg_d.get("hysteresis", 0.0)),
        min_hold_steps=int(cfg_d.get("min_hold_steps", 0) or 0),
        cooldown_steps=int(cfg_d.get("cooldown_steps", 0) or 0),
    )

    if not enabled:
        details.update(
            {"enabled": False, "active_specialist": state.active, "switch_state": state_d}
        )
        return DoublePlayDecision(False, state.active, dict(state_d), tuple(reasons), details)

    new_state = step_switch_gate(
        score=score, state=state, cfg=cfg, bull_label="bull", bear_label="bear"
    )
    details.update(
        {
            "enabled": True,
            "active_specialist": new_state.active,
            "switch_state": {
                "active": new_state.active,
                "hold_remaining": new_state.hold_remaining,
                "cooldown_remaining": new_state.cooldown_remaining,
            },
        }
    )
    return DoublePlayDecision(
        True, new_state.active, details["switch_state"], tuple(reasons), details
    )
