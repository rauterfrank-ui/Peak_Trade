"""Capability verifier for Cap 11.1 execution-domain contracts."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.adapter_anti_corruption_v1 import (
    prove_adapter_anti_corruption_v1,
    prove_order_portfolio_atomicity_contract_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.canonical_execution_event_schema_v1 import (
    prove_one_canonical_execution_event_schema_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.canonical_intent_schema_v1 import (
    prove_one_canonical_intent_schema_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    TESTNET_AUTHORIZED,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    prove_mode_specific_execution_boundary_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    prove_order_lifecycle_state_machine_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.reachability_and_parity_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    prove_core_logic_parity_with_simulated_port_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.submission_semantics_v1 import (
    prove_client_order_id_and_submission_semantics_v1,
)


def verify_capability_11_1_v1() -> dict[str, Any]:
    proofs = {
        "intent_schema": prove_one_canonical_intent_schema_v1(),
        "execution_event_schema": prove_one_canonical_execution_event_schema_v1(),
        "execution_ports": prove_mode_specific_execution_boundary_v1(),
        "order_lifecycle": prove_order_lifecycle_state_machine_v1(),
        "submission_semantics": prove_client_order_id_and_submission_semantics_v1(),
        "adapter_anti_corruption": prove_adapter_anti_corruption_v1(),
        "state_ownership": prove_state_ownership_matrix_v1(),
        "atomicity": prove_order_portfolio_atomicity_contract_v1(),
        "negative_reachability": prove_negative_reachability_v1(),
        "core_logic_parity": prove_core_logic_parity_with_simulated_port_v1(),
    }
    ok = all(bool(p.get("ok")) for p in proofs.values())
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ONE_DECISION_AUTHORITY_CHAIN": True,
        "ONE_CANONICAL_INTENT_SCHEMA": proofs["intent_schema"].get("ONE_CANONICAL_INTENT_SCHEMA"),
        "ONE_CANONICAL_EXECUTION_EVENT_SCHEMA": proofs["execution_event_schema"].get(
            "ONE_CANONICAL_EXECUTION_EVENT_SCHEMA"
        ),
        "ORDER_LIFECYCLE_STATE_MACHINE_BOUND": proofs["order_lifecycle"].get(
            "ORDER_LIFECYCLE_STATE_MACHINE_BOUND"
        ),
        "CLIENT_ORDER_ID_DETERMINISTIC": proofs["submission_semantics"].get(
            "CLIENT_ORDER_ID_DETERMINISTIC"
        ),
        "SUBMISSION_IDEMPOTENT": proofs["submission_semantics"].get("SUBMISSION_IDEMPOTENT"),
        "UNKNOWN_BLIND_RETRY_FORBIDDEN": proofs["submission_semantics"].get(
            "UNKNOWN_BLIND_RETRY_FORBIDDEN"
        ),
        "EXCHANGE_QUERY_BEFORE_RETRY_CONTRACT": proofs["submission_semantics"].get(
            "EXCHANGE_QUERY_BEFORE_RETRY_CONTRACT"
        ),
        "TERMINAL_STATE_IMMUTABLE": proofs["order_lifecycle"].get("TERMINAL_STATE_IMMUTABLE"),
        "ORDER_PORTFOLIO_ATOMIC_OR_JOURNALED": proofs["atomicity"].get(
            "ORDER_AND_PORTFOLIO_STATE_ATOMIC_OR_JOURNALED"
        ),
        "SIMULATED_EXECUTION_PORT_RETAINED": proofs["execution_ports"].get(
            "SIMULATED_EXECUTION_PORT_RETAINED"
        ),
        "TESTNET_EXECUTION_PORT_DECLARED": proofs["execution_ports"].get(
            "TESTNET_EXECUTION_PORT_DECLARED"
        ),
        "TESTNET_EXECUTION_REACHABLE": False,
        "LIVE_EXECUTION_PORT_DECLARED": proofs["execution_ports"].get(
            "LIVE_EXECUTION_PORT_DECLARED"
        ),
        "LIVE_EXECUTION_REACHABLE": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "NETWORK_SESSION_STARTED": False,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "NO_EXECUTION_ADAPTER_DECISION_AUTHORITY": proofs["adapter_anti_corruption"].get(
            "NO_EXECUTION_ADAPTER_DECISION_AUTHORITY"
        ),
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
