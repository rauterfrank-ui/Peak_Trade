"""Parity proof for Session-GO capability (no trading-core mutation)."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    BULL_BEAR_CHANGE,
    CONFIRMATION_SEMANTICS_CHANGE,
    CORE_LOGIC_CHANGE,
    DOUBLE_PLAY_CHANGE,
    DYNAMIC_SCOPE_LOGIC_CHANGE,
    MASTER_V2_CHANGE,
    RISK_CHANGE,
    SAFETY_CHANGE,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.parity_v1 import (
    prove_phase92_productive_entrypoint_parity_v1,
)


def prove_phase92_session_go_parity_v1() -> dict[str, Any]:
    """Reuse entrypoint parity surface; Session-GO must not alter trading core."""
    base = prove_phase92_productive_entrypoint_parity_v1()
    claims = {
        "GOLDEN_VECTOR_PARITY_PASS": bool(base.get("GOLDEN_VECTOR_PARITY_PASS")),
        "CALL_ORDER_PARITY_PROVEN": bool(base.get("CALL_ORDER_PARITY_PROVEN")),
        "INPUT_OUTPUT_PARITY_PROVEN": bool(base.get("INPUT_OUTPUT_PARITY_PROVEN")),
        "STATE_TRANSITION_PARITY_PROVEN": bool(base.get("STATE_TRANSITION_PARITY_PROVEN")),
        "DECISION_REASON_PARITY_PROVEN": bool(base.get("DECISION_REASON_PARITY_PROVEN")),
        "RISK_PARITY_PROVEN": bool(base.get("RISK_PARITY_PROVEN")),
        "SAFETY_PARITY_PROVEN": bool(base.get("SAFETY_PARITY_PROVEN")),
        "EXIT_PRECEDENCE_PARITY_PROVEN": bool(base.get("EXIT_PRECEDENCE_PARITY_PROVEN")),
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "CORE_LOGIC_CHANGED": CORE_LOGIC_CHANGE,
        "MASTER_V2_CHANGED": MASTER_V2_CHANGE,
        "DOUBLE_PLAY_CHANGED": DOUBLE_PLAY_CHANGE,
        "BULL_BEAR_CHANGED": BULL_BEAR_CHANGE,
        "DYNAMIC_SCOPE_CHANGED": DYNAMIC_SCOPE_LOGIC_CHANGE,
        "CONFIRMATION_SEMANTICS_CHANGED": CONFIRMATION_SEMANTICS_CHANGE,
        "RISK_CHANGED": RISK_CHANGE,
        "SAFETY_CHANGED": SAFETY_CHANGE,
        "phase92_entrypoint_parity_reused": True,
    }
    ok = bool(base.get("ok")) and not any(
        (
            CORE_LOGIC_CHANGE,
            MASTER_V2_CHANGE,
            DOUBLE_PLAY_CHANGE,
            BULL_BEAR_CHANGE,
            DYNAMIC_SCOPE_LOGIC_CHANGE,
            CONFIRMATION_SEMANTICS_CHANGE,
            RISK_CHANGE,
            SAFETY_CHANGE,
        )
    )
    return {"ok": ok, **claims}
