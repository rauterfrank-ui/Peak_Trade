"""Core-logic parity revalidation for Phase 9.2 restart harness (no rule mutation)."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_public_md_session_preflight_v1.parity_v1 import prove_phase92_parity_v1
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    BULL_BEAR_CHANGE,
    CONFIRMATION_SEMANTICS_CHANGE,
    CORE_LOGIC_CHANGE,
    DOUBLE_PLAY_CHANGE,
    DYNAMIC_SCOPE_LOGIC_CHANGE,
    EXECUTION_ECONOMICS_CHANGE,
    MASTER_V2_CHANGE,
    RISK_CHANGE,
    SAFETY_CHANGE,
    VOLATILITY_POLICY_CHANGE,
)


def prove_phase92_restart_parity_v1() -> dict[str, Any]:
    base = prove_phase92_parity_v1()
    keys = (
        "GOLDEN_VECTOR_PARITY_PASS",
        "CALL_ORDER_PARITY_PROVEN",
        "INPUT_OUTPUT_PARITY_PROVEN",
        "STATE_TRANSITION_PARITY_PROVEN",
        "DECISION_REASON_PARITY_PROVEN",
        "RISK_PARITY_PROVEN",
        "SAFETY_PARITY_PROVEN",
        "EXIT_PRECEDENCE_PARITY_PROVEN",
    )
    out: dict[str, Any] = {
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "CORE_LOGIC_CHANGED": CORE_LOGIC_CHANGE,
        "MASTER_V2_CHANGED": MASTER_V2_CHANGE,
        "DOUBLE_PLAY_CHANGED": DOUBLE_PLAY_CHANGE,
        "BULL_BEAR_CHANGED": BULL_BEAR_CHANGE,
        "DYNAMIC_SCOPE_LOGIC_CHANGED": DYNAMIC_SCOPE_LOGIC_CHANGE,
        "CONFIRMATION_SEMANTICS_CHANGED": CONFIRMATION_SEMANTICS_CHANGE,
        "VOLATILITY_POLICY_CHANGED": VOLATILITY_POLICY_CHANGE,
        "RISK_CHANGED": RISK_CHANGE,
        "SAFETY_CHANGED": SAFETY_CHANGE,
        "EXECUTION_ECONOMICS_CHANGED": EXECUTION_ECONOMICS_CHANGE,
        "phase92_parity_reused": True,
    }
    all_ok = (
        (not CORE_LOGIC_CHANGE)
        and (not MASTER_V2_CHANGE)
        and (not DOUBLE_PLAY_CHANGE)
        and (not RISK_CHANGE)
        and (not SAFETY_CHANGE)
    )
    for key in keys:
        value = bool(base.get(key))
        out[key] = value
        all_ok = all_ok and value
    out["ok"] = all_ok
    return out
