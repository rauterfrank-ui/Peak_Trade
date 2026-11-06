"""Capability verifier for Cap 11.6 long-running autonomous Testnet evidence."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    PREDECESSOR_CAPABILITY_ID_11_3,
    PREDECESSOR_CAPABILITY_ID_11_4,
    PREDECESSOR_CAPABILITY_ID_11_5,
    TESTNET_AUTHORIZED,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_capability_11_4_dependency_retained_v1,
    prove_capability_11_5_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.long_running_campaign_evidence_contract_v1 import (
    prove_long_running_campaign_evidence_contract_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.observability_audit_evidence_contract_v1 import (
    prove_observability_audit_evidence_contract_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.reachability_and_parity_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.testnet_evidence_closure_contract_v1 import (
    prove_testnet_evidence_closure_contract_v1,
)


def verify_capability_11_6_v1() -> dict[str, Any]:
    proofs = {
        "long_running_campaign_evidence": prove_long_running_campaign_evidence_contract_v1(),
        "testnet_evidence_closure": prove_testnet_evidence_closure_contract_v1(),
        "observability_audit_evidence": prove_observability_audit_evidence_contract_v1(),
        "dependency_11_1": prove_capability_11_1_dependency_retained_v1(),
        "dependency_11_2": prove_capability_11_2_dependency_retained_v1(),
        "dependency_11_3": prove_capability_11_3_dependency_retained_v1(),
        "dependency_11_4": prove_capability_11_4_dependency_retained_v1(),
        "dependency_11_5": prove_capability_11_5_dependency_retained_v1(),
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
        "PREDECESSOR_CAPABILITY_ID_11_5": PREDECESSOR_CAPABILITY_ID_11_5,
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
        "CAPABILITY_11_5_DEPENDENCY_SATISFIED": proofs["dependency_11_5"].get(
            "CAPABILITY_11_5_DEPENDENCY_SATISFIED"
        ),
        "LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_BOUND": proofs[
            "long_running_campaign_evidence"
        ].get("LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_BOUND"),
        "LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_ACTIVATED": False,
        "TESTNET_EVIDENCE_CLOSURE_CONTRACT_BOUND": proofs["testnet_evidence_closure"].get(
            "TESTNET_EVIDENCE_CLOSURE_CONTRACT_BOUND"
        ),
        "TESTNET_EVIDENCE_CLOSURE_CONTRACT_ACTIVATED": False,
        "OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_BOUND": proofs["observability_audit_evidence"].get(
            "OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_BOUND"
        ),
        "OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_ACTIVATED": False,
        "LONG_RUNNING_AUTONOMOUS_TESTNET_EVIDENCE_FIXTURE_ONLY": True,
        "CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED": True,
        "LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_6": False,
        "TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_6": False,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": False,
        "TESTNET_RECONCILIATION_PROVEN": False,
        "TESTNET_RESTART_PROVEN": False,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": False,
        "TESTNET_KILL_SWITCH_PROVEN": False,
        "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": False,
        "TESTNET_EVIDENCE_VERIFIED": False,
        "CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED": False,
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
        "CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_RETAINED": proofs["dependency_11_5"].get(
            "CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_RETAINED"
        ),
        "CAPABILITY_11_5_NOT_ACTIVATED_RETAINED": proofs["dependency_11_5"].get(
            "CAPABILITY_11_5_NOT_ACTIVATED_RETAINED"
        ),
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_6": False,
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
