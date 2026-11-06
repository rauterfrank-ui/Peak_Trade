"""Capability verifier for Cap 11.4 testnet execution adapter and lifecycle closure."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    PREDECESSOR_CAPABILITY_ID_11_3,
    TESTNET_AUTHORIZED,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.order_serialization_dry_run_contract_v1 import (
    prove_order_serialization_dry_run_contract_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.reachability_and_parity_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_execution_adapter_v1 import (
    prove_testnet_execution_adapter_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_lifecycle_closure_contract_v1 import (
    prove_testnet_lifecycle_closure_contract_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.venue_adapter_anti_corruption_v1 import (
    prove_venue_adapter_anti_corruption_v1,
)


def verify_capability_11_4_v1() -> dict[str, Any]:
    proofs = {
        "testnet_execution_adapter": prove_testnet_execution_adapter_v1(),
        "order_serialization_dry_run": prove_order_serialization_dry_run_contract_v1(),
        "testnet_lifecycle_closure": prove_testnet_lifecycle_closure_contract_v1(),
        "venue_adapter_anti_corruption": prove_venue_adapter_anti_corruption_v1(),
        "dependency_11_1": prove_capability_11_1_dependency_retained_v1(),
        "dependency_11_2": prove_capability_11_2_dependency_retained_v1(),
        "dependency_11_3": prove_capability_11_3_dependency_retained_v1(),
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
        "TESTNET_EXECUTION_ADAPTER_DECLARED": proofs["testnet_execution_adapter"].get(
            "TESTNET_EXECUTION_ADAPTER_DECLARED"
        ),
        "TESTNET_EXECUTION_ADAPTER_CONSTRUCTIBLE": False,
        "TESTNET_EXECUTION_ADAPTER_ACTIVATED": False,
        "ORDER_SERIALIZATION_DRY_RUN_CONTRACT_BOUND": proofs["order_serialization_dry_run"].get(
            "ORDER_SERIALIZATION_DRY_RUN_CONTRACT_BOUND"
        ),
        "ORDER_SERIALIZATION_NETWORK_EFFECT": "NONE",
        "TESTNET_LIFECYCLE_CLOSURE_CONTRACT_BOUND": proofs["testnet_lifecycle_closure"].get(
            "TESTNET_LIFECYCLE_CLOSURE_CONTRACT_BOUND"
        ),
        "TESTNET_LIFECYCLE_FIXTURE_ONLY": True,
        "TESTNET_ENTRY_PARTIAL_FILL_CANCEL_EXIT_PATHS_BOUND": proofs[
            "testnet_lifecycle_closure"
        ].get("TESTNET_ENTRY_PARTIAL_FILL_CANCEL_EXIT_PATHS_BOUND"),
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4": False,
        "TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_4": False,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": False,
        "TESTNET_RESTART_PROVEN": False,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "TESTNET_KILL_SWITCH_PROVEN": False,
        "CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED": False,
        "VENUE_ADAPTER_DECISION_AUTHORITY": False,
        "NATIVE_ORDER_SERIALIZATION_EXPLICIT": True,
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
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_4": False,
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
