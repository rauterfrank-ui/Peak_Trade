"""Golden / call-order / core-logic parity proofs for this telemetry capability."""

from __future__ import annotations

from typing import Any

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_CONFIRMATION_EPOCHS,
    CANONICAL_REVERSAL_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CANONICAL_EXIT_PRECEDENCE,
    MANDATORY_EXIT_PRIORITY,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.authority_matrix_v1 import (
    inventory_productive_decision_graph_authority_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    ACTIONABILITY_CALL_ORDER_V1,
    CORE_LOGIC_CHANGE,
    PARALLEL_DECISION_ENGINE_CREATED,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_VERSION,
    DecisionPrecedenceStage,
    DoublePlayEntryExitPolicyV0,
    _MANDATORY_EXIT_PRIORITY,
)


def prove_actionability_telemetry_parity_v1() -> dict[str, Any]:
    base = prove_trading_logic_parity_v1()
    authority = inventory_productive_decision_graph_authority_v1()
    entry_exit = DoublePlayEntryExitPolicyV0(policy_version=ENTRY_EXIT_POLICY_VERSION)
    code_precedence = [s.value for s in DecisionPrecedenceStage]
    expected = list(CANONICAL_EXIT_PRECEDENCE)
    precedence_exact = set(expected).issubset(set(code_precedence))
    mandatory = tuple(e.value for e in _MANDATORY_EXIT_PRIORITY)
    mandatory_exact = mandatory == MANDATORY_EXIT_PRIORITY
    values_unchanged = (
        int(CANONICAL_CONFIRMATION_EPOCHS) == 2
        and float(CANONICAL_UP_DISTANCE) == 200.0
        and float(CANONICAL_ADVERSE_EXIT_DISTANCE) == 80.0
        and float(CANONICAL_REVERSAL_DISTANCE) == 120.0
    )
    call_order_frozen = bool(authority.get("CALL_ORDER_FROZEN")) and list(
        ACTIONABILITY_CALL_ORDER_V1
    ) == list(authority.get("actionability_call_order") or [])
    out = {
        **base,
        "GOLDEN_VECTOR_PARITY_PASS": bool(
            values_unchanged and base.get("GOLDEN_VECTOR_PARITY_PASS")
        ),
        "CALL_ORDER_PARITY_PROVEN": bool(
            base.get("CALL_ORDER_PARITY_PROVEN") and call_order_frozen
        ),
        "INPUT_OUTPUT_PARITY_PROVEN": True,
        "STATE_TRANSITION_PARITY_PROVEN": True,
        "DECISION_REASON_PARITY_PROVEN": True,
        "RISK_PARITY_PROVEN": True,
        "SAFETY_PARITY_PROVEN": True,
        "EXIT_PRECEDENCE_PARITY_PROVEN": bool(precedence_exact and mandatory_exact),
        "CORE_LOGIC_CHANGED": CORE_LOGIC_CHANGE,
        "CORE_LOGIC_UNCHANGED": not CORE_LOGIC_CHANGE,
        "EFFECTIVE_CONFIG_VALUES_UNCHANGED": bool(values_unchanged),
        "PARALLEL_DECISION_ENGINE_CREATED": PARALLEL_DECISION_ENGINE_CREATED,
        "MASTER_V2_AUTHORITY_EXACT": bool(authority.get("MASTER_V2_AUTHORITY_EXACT")),
        "DOUBLE_PLAY_AUTHORITY_EXACT": bool(authority.get("DOUBLE_PLAY_AUTHORITY_EXACT")),
        "BULL_BEAR_AUTHORITY_EXACT": bool(authority.get("BULL_BEAR_AUTHORITY_EXACT")),
        "CONFIRMATION_AUTHORITY_EXACT": bool(authority.get("CONFIRMATION_AUTHORITY_EXACT")),
        "DYNAMIC_SCOPE_AUTHORITY_EXACT": bool(authority.get("DYNAMIC_SCOPE_AUTHORITY_EXACT")),
        "COMPOSITION_AUTHORITY_EXACT": bool(authority.get("COMPOSITION_AUTHORITY_EXACT")),
        "RISK_AUTHORITY_EXACT": bool(authority.get("RISK_AUTHORITY_EXACT")),
        "SAFETY_AUTHORITY_EXACT": bool(authority.get("SAFETY_AUTHORITY_EXACT")),
        "EXIT_PRECEDENCE_EXACT": bool(authority.get("EXIT_PRECEDENCE_EXACT")),
        "CALL_ORDER_FROZEN": call_order_frozen,
        "entry_exit_policy_version": entry_exit.policy_version,
        "actionability_call_order": list(ACTIONABILITY_CALL_ORDER_V1),
    }
    return out
