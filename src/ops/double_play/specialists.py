from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    OPS_EVALUATE_DOUBLE_PLAY_ROLE,
    OPS_MAY_WRITE_SIDE_STATE,
    OPS_SWITCH_AUTHORIZATION,
    OPS_SWITCH_GATE_AUTHORITY_STATUS,
    REASON_OPS_PROJECTION_ONLY,
    REASON_OPS_SWITCH_AUTHORITY_DISABLED,
)
from trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
    OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
    declare_legacy_duplicate_decision_path_v0,
)


@dataclass(frozen=True)
class DoublePlayDecision:
    enabled: bool
    active_specialist: str  # "bull"|"bear" — frozen projection of input state only
    switch_state: Dict[str, Any]
    reasons: Tuple[str, ...]
    details: Dict[str, Any]


def evaluate_double_play(*, context: Dict[str, Any]) -> DoublePlayDecision:
    """
    SAFE DEFAULT OFF. Projection / diagnostic consumer only.

    Competing SwitchGate authority is fail-closed disabled (quarantine v1).
    This callable never authorizes a Bull/Bear switch, never calls
    ``step_switch_gate``, and never writes SideState back into Double Play.

    Canonical Bull/Bear / Switch authority remains
    ``trading.master_v2.double_play_state.transition_state`` via
    ``run_integrated_offline_trading_logic_replay_v1``.
    """
    declare_legacy_duplicate_decision_path_v0(
        path_id=OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
        system_economic_evidence_requested=bool(
            context.get("system_economic_evidence_requested", False)
        ),
    )
    sg = context.get("switch_gate", {}) or {}
    state_d = dict(sg.get("state", {}) or {})
    active = str(state_d.get("active", "bull") or "bull")
    if active not in ("bull", "bear"):
        active = "bull"
    frozen_switch_state = {
        "active": active,
        "hold_remaining": int(state_d.get("hold_remaining", 0) or 0),
        "cooldown_remaining": int(state_d.get("cooldown_remaining", 0) or 0),
    }
    enabled = bool(context.get("double_play_enabled", False))
    reasons: Tuple[str, ...] = (
        REASON_OPS_PROJECTION_ONLY,
        REASON_OPS_SWITCH_AUTHORITY_DISABLED,
    )
    details: Dict[str, Any] = {
        "path_authority": OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
        "system_economic_evidence_admissible": False,
        "ops_role": OPS_EVALUATE_DOUBLE_PLAY_ROLE,
        "switch_gate_authority_status": OPS_SWITCH_GATE_AUTHORITY_STATUS,
        "switch_authorization": OPS_SWITCH_AUTHORIZATION,
        "may_write_side_state": OPS_MAY_WRITE_SIDE_STATE,
        "enabled": enabled,
        "active_specialist": active,
        "switch_state": frozen_switch_state,
        "score_observed": float((sg.get("score", 0.0) or 0.0)),
        "switch_gate_invoked": False,
    }
    # Enabled flag remains observational only — never advances switch state.
    return DoublePlayDecision(
        False if not enabled else True,
        active,
        frozen_switch_state,
        reasons,
        details,
    )
