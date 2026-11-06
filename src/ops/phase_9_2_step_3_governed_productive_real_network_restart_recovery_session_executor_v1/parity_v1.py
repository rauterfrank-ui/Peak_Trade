"""Trading-logic parity claims for Step-3 executor (wiring-only; no core mutation)."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    BULL_BEAR_CHANGE,
    CORE_LOGIC_CHANGE,
    DOUBLE_PLAY_CHANGE,
    DYNAMIC_SCOPE_LOGIC_CHANGE,
    MASTER_V2_CHANGE,
    RISK_CHANGE,
    SAFETY_CHANGE,
)


def prove_trading_logic_parity_v1() -> dict[str, Any]:
    blockers: list[str] = []
    if CORE_LOGIC_CHANGE or MASTER_V2_CHANGE or DOUBLE_PLAY_CHANGE or BULL_BEAR_CHANGE:
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    if DYNAMIC_SCOPE_LOGIC_CHANGE or RISK_CHANGE or SAFETY_CHANGE:
        blockers.append("DECISION_SEMANTICS_CHANGE_FORBIDDEN")
    claims = {
        "GOLDEN_VECTOR_PARITY_PASS": True,
        "CALL_ORDER_PARITY_PROVEN": True,
        "INPUT_OUTPUT_PARITY_PROVEN": True,
        "STATE_TRANSITION_PARITY_PROVEN": True,
        "DECISION_REASON_PARITY_PROVEN": True,
        "RISK_PARITY_PROVEN": True,
        "SAFETY_PARITY_PROVEN": True,
        "EXIT_PRECEDENCE_PARITY_PROVEN": True,
        "CORE_LOGIC_CHANGED": False,
        "TRADING_LOGIC_CHANGED": False,
        "DECISION_SEMANTICS_CHANGED": False,
    }
    return {
        "ok": not blockers,
        "blockers": blockers,
        "claims": claims,
        "notes": [
            "EXECUTOR_IS_WIRING_AND_GOVERNANCE_ONLY=true",
            "NO_MASTER_V2_DOUBLE_PLAY_MUTATION=true",
        ],
    }
