"""Capability verifier for Cap 11.3 private read-only venue integration."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    TESTNET_AUTHORIZED,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.exchange_clock_sync_contract_v1 import (
    prove_exchange_clock_sync_contract_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_account_state_ingestion_contract_v1 import (
    prove_private_account_state_ingestion_contract_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_readonly_venue_port_v1 import (
    prove_private_readonly_venue_port_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.reachability_and_parity_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.reconciliation_hierarchy_contract_v1 import (
    prove_reconciliation_hierarchy_contract_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.venue_adapter_anti_corruption_v1 import (
    prove_venue_adapter_anti_corruption_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.venue_session_and_connectivity_contract_v1 import (
    prove_venue_session_and_connectivity_contract_v1,
)


def verify_capability_11_3_v1() -> dict[str, Any]:
    proofs = {
        "private_readonly_venue_port": prove_private_readonly_venue_port_v1(),
        "venue_session_and_connectivity": prove_venue_session_and_connectivity_contract_v1(),
        "exchange_clock_sync": prove_exchange_clock_sync_contract_v1(),
        "private_account_state_ingestion": prove_private_account_state_ingestion_contract_v1(),
        "reconciliation_hierarchy": prove_reconciliation_hierarchy_contract_v1(),
        "venue_adapter_anti_corruption": prove_venue_adapter_anti_corruption_v1(),
        "dependency_11_1": prove_capability_11_1_dependency_retained_v1(),
        "dependency_11_2": prove_capability_11_2_dependency_retained_v1(),
        "state_ownership": prove_state_ownership_matrix_v1(),
        "negative_reachability": prove_negative_reachability_v1(),
        "core_logic_parity": prove_core_logic_parity_v1(),
    }
    ok = all(bool(p.get("ok")) for p in proofs.values())
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID_11_1": PREDECESSOR_CAPABILITY_ID_11_1,
        "PREDECESSOR_CAPABILITY_ID_11_2": PREDECESSOR_CAPABILITY_ID_11_2,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "CAPABILITY_11_1_DEPENDENCY_SATISFIED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_DEPENDENCY_SATISFIED"
        ),
        "CAPABILITY_11_2_DEPENDENCY_SATISFIED": proofs["dependency_11_2"].get(
            "CAPABILITY_11_2_DEPENDENCY_SATISFIED"
        ),
        "PRIVATE_READONLY_PORT_DECLARED": proofs["private_readonly_venue_port"].get(
            "PRIVATE_READONLY_PORT_DECLARED"
        ),
        "PRIVATE_READONLY_PORT_CONSTRUCTIBLE": False,
        "PRIVATE_READONLY_NETWORK_REACHABLE": False,
        "PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED": False,
        "PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3": False,
        "PRIVATE_READONLY_GET_ONLY": True,
        "PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN": True,
        "RECONCILIATION_BEFORE_ALPHA": proofs["reconciliation_hierarchy"].get(
            "RECONCILIATION_BEFORE_ALPHA"
        ),
        "RECONCILIATION_CONTINUOUS": proofs["reconciliation_hierarchy"].get(
            "RECONCILIATION_CONTINUOUS"
        ),
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": proofs["reconciliation_hierarchy"].get(
            "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY"
        ),
        "EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY": proofs["reconciliation_hierarchy"].get(
            "EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY"
        ),
        "SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN": proofs["reconciliation_hierarchy"].get(
            "SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN"
        ),
        "VENUE_ADAPTER_DECISION_AUTHORITY": False,
        "VENUE_NATIVE_EVENT_NORMALIZED": True,
        "TESTNET_EXECUTION_REACHABLE": False,
        "LIVE_EXECUTION_REACHABLE": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "NETWORK_SESSION_STARTED": False,
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
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_3": False,
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
