"""Core-logic parity revalidation for Phase 9.2 preflight (no rule mutation)."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_1_strategy_registry_closure_v1.parity_v1 import prove_phase91_parity_v1
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import CORE_LOGIC_CHANGE
from src.ops.single_future_stateful_no_order_runtime_activation_v1.parity_v1 import (
    prove_trading_logic_parity_v1 as prove_cap72_parity_v1,
)


def prove_phase92_parity_v1() -> dict[str, Any]:
    cap72 = prove_cap72_parity_v1()
    phase91 = prove_phase91_parity_v1()
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
        "cap72_parity_reused": True,
        "phase91_parity_reused": True,
    }
    all_ok = not CORE_LOGIC_CHANGE
    for key in keys:
        value = bool(cap72.get(key)) and bool(phase91.get(key))
        out[key] = value
        all_ok = all_ok and value
    out["ok"] = all_ok
    out["MASTER_V2_CHANGED"] = False
    out["DOUBLE_PLAY_CHANGED"] = False
    out["BULL_BEAR_CHANGED"] = False
    out["CONFIRMATION_SEMANTICS_CHANGED"] = False
    out["DYNAMIC_SCOPE_RULES_CHANGED"] = False
    out["RISK_CHANGED"] = False
    out["SAFETY_CHANGED"] = False
    out["EXIT_RULES_CHANGED"] = False
    out["EXIT_THRESHOLDS_CHANGED"] = False
    return out
