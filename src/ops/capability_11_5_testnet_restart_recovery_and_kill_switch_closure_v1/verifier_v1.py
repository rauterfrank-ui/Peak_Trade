"""Capability verifier for Cap 11.5 testnet restart, recovery and kill-switch closure."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.autonomous_recovery_degradation_contract_v1 import (
    prove_autonomous_recovery_degradation_contract_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    PREDECESSOR_CAPABILITY_ID_11_3,
    PREDECESSOR_CAPABILITY_ID_11_4,
    TESTNET_AUTHORIZED,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_capability_11_4_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.kill_switch_and_emergency_control_contract_v1 import (
    prove_kill_switch_and_emergency_control_contract_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.reachability_and_parity_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.restart_with_open_order_position_contract_v1 import (
    prove_restart_with_open_order_position_contract_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.unknown_submit_reconnect_recovery_contract_v1 import (
    prove_unknown_submit_reconnect_recovery_contract_v1,
)


def verify_capability_11_5_v1() -> dict[str, Any]:
    proofs = {
        "unknown_submit_reconnect_recovery": prove_unknown_submit_reconnect_recovery_contract_v1(),
        "restart_with_open_order_position": prove_restart_with_open_order_position_contract_v1(),
        "kill_switch_and_emergency_control": prove_kill_switch_and_emergency_control_contract_v1(),
        "autonomous_recovery_degradation": prove_autonomous_recovery_degradation_contract_v1(),
        "dependency_11_1": prove_capability_11_1_dependency_retained_v1(),
        "dependency_11_2": prove_capability_11_2_dependency_retained_v1(),
        "dependency_11_3": prove_capability_11_3_dependency_retained_v1(),
        "dependency_11_4": prove_capability_11_4_dependency_retained_v1(),
        "state_ownership": prove_state_ownership_matrix_v1(),
        "negative_reachability": prove_negative_reachability_v1(),
        "core_logic_parity": prove_core_logic_parity_v1(),
    }
    ok = all(bool(p.get("ok")) for p in proofs.values())
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID_11_1": PREDECESSOR_CAPABILITY_ID_11_1,
        "PREDECESSOR_CAPABILITY_ID_11_2": PREDECESSOR_CAPABILITY_ID_11_2,
        "PREDECESSOR_CAPABILITY_ID_11_3": PREDECESSOR_CAPABILITY_ID_11_3,
        "PREDECESSOR_CAPABILITY_ID_11_4": PREDECESSOR_CAPABILITY_ID_11_4,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "CAPABILITY_11_1_DEPENDENCY_SATISFIED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_DEPENDENCY_SATISFIED"
        ),
        "CAPABILITY_11_2_DEPENDENCY_SATISFIED": proofs["dependency_11_2"].get(
            "CAPABILITY_11_2_DEPENDENCY_SATISFIED"
        ),
        "CAPABILITY_11_3_DEPENDENCY_SATISFIED": proofs["dependency_11_3"].get(
            "CAPABILITY_11_3_DEPENDENCY_SATISFIED"
        ),
        "CAPABILITY_11_4_DEPENDENCY_SATISFIED": proofs["dependency_11_4"].get(
            "CAPABILITY_11_4_DEPENDENCY_SATISFIED"
        ),
        "UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_BOUND": proofs[
            "unknown_submit_reconnect_recovery"
        ].get("UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_BOUND"),
        "UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED": False,
        "RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_BOUND": proofs[
            "restart_with_open_order_position"
        ].get("RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_BOUND"),
        "RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED": False,
        "KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_BOUND": proofs[
            "kill_switch_and_emergency_control"
        ].get("KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_BOUND"),
        "KILL_SWITCH_CONTRACT_ACTIVATED": False,
        "AUTONOMOUS_RECOVERY_DEGRADATION_CONTRACT_BOUND": proofs[
            "autonomous_recovery_degradation"
        ].get("AUTONOMOUS_RECOVERY_DEGRADATION_CONTRACT_BOUND"),
        "AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED": False,
        "TESTNET_RESTART_RECOVERY_KILL_SWITCH_FIXTURE_ONLY": True,
        "CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED": True,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5": False,
        "TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_5": False,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": False,
        "TESTNET_RESTART_PROVEN": False,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "TESTNET_KILL_SWITCH_PROVEN": False,
        "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": False,
        "CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED": False,
        "KILL_SWITCH_PERSISTED": True,
        "KILL_SWITCH_FAIL_CLOSED": True,
        "KILL_SWITCH_SURVIVES_RESTART": True,
        "KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME": True,
        "OWNER_AUTHORITY_REQUIRED_TO_CLEAR": True,
        "TESTNET_EXECUTION_REACHABLE": False,
        "LIVE_EXECUTION_REACHABLE": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "NETWORK_SESSION_STARTED": False,
        "PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED": False,
        "PRIVATE_READONLY_NETWORK_REACHABLE": False,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "CAPABILITY_11_1_FAIL_CLOSED_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_FAIL_CLOSED_RETAINED"
        ),
        "CAPABILITY_11_1_IDEMPOTENCY_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_IDEMPOTENCY_RETAINED"
        ),
        "CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED"
        ),
        "CAPABILITY_11_1_LIFECYCLE_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_LIFECYCLE_RETAINED"
        ),
        "CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED": proofs["dependency_11_2"].get(
            "CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED"
        ),
        "CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED": proofs["dependency_11_2"].get(
            "CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED"
        ),
        "CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED": proofs["dependency_11_2"].get(
            "CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED"
        ),
        "CAPABILITY_11_3_PRIVATE_READONLY_BOUNDARY_RETAINED": proofs["dependency_11_3"].get(
            "CAPABILITY_11_3_PRIVATE_READONLY_BOUNDARY_RETAINED"
        ),
        "CAPABILITY_11_3_RECONCILIATION_HIERARCHY_RETAINED": proofs["dependency_11_3"].get(
            "CAPABILITY_11_3_RECONCILIATION_HIERARCHY_RETAINED"
        ),
        "CAPABILITY_11_3_NOT_ACTIVATED_RETAINED": proofs["dependency_11_3"].get(
            "CAPABILITY_11_3_NOT_ACTIVATED_RETAINED"
        ),
        "CAPABILITY_11_4_TESTNET_ADAPTER_BOUNDARY_RETAINED": proofs["dependency_11_4"].get(
            "CAPABILITY_11_4_TESTNET_ADAPTER_BOUNDARY_RETAINED"
        ),
        "CAPABILITY_11_4_LIFECYCLE_CLOSURE_RETAINED": proofs["dependency_11_4"].get(
            "CAPABILITY_11_4_LIFECYCLE_CLOSURE_RETAINED"
        ),
        "CAPABILITY_11_4_NOT_ACTIVATED_RETAINED": proofs["dependency_11_4"].get(
            "CAPABILITY_11_4_NOT_ACTIVATED_RETAINED"
        ),
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_5": False,
    }
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "claims": claims,
        "proofs": proofs,
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
