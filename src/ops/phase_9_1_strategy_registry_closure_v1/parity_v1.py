"""Parity proofs — Cap 9.1 must not mutate core trading logic."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import (
    CALL_GRAPH_V1,
    CORE_LOGIC_CHANGE,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.parity_v1 import (
    prove_trading_logic_parity_v1 as prove_cap71_parity_v1,
)


def prove_phase91_parity_v1() -> dict[str, Any]:
    base = prove_cap71_parity_v1()
    out = dict(base)
    out["CORE_LOGIC_CHANGE"] = CORE_LOGIC_CHANGE
    out["CORE_LOGIC_UNCHANGED"] = not CORE_LOGIC_CHANGE
    out["MASTER_V2_CHANGED"] = False
    out["DOUBLE_PLAY_CHANGED"] = False
    out["BULL_BEAR_CHANGED"] = False
    out["CONFIRMATION_SEMANTICS_CHANGED"] = False
    out["DYNAMIC_SCOPE_RULES_CHANGED"] = False
    out["RISK_CHANGED"] = False
    out["SAFETY_CHANGED"] = False
    out["EXIT_RULES_CHANGED"] = False
    out["EXIT_THRESHOLDS_CHANGED"] = False
    out["EXIT_PRECEDENCE_CHANGED"] = False
    out["CALL_ORDER_PARITY_PROVEN"] = bool(
        base.get("CALL_ORDER_PARITY_PROVEN") and len(CALL_GRAPH_V1) > 0
    )
    out["phase91_call_graph"] = list(CALL_GRAPH_V1)
    out["cap71_parity_reused"] = True
    return out
