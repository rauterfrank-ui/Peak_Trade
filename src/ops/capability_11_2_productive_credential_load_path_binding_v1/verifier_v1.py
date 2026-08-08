"""Verifier for Cap 11.2 productive credential-load path binding."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_2_productive_credential_load_path_binding_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_11_3_PRIVATE_READONLY_STARTED,
    CAPABILITY_11_3_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_ALLOWED_DEFAULT,
    CREDENTIAL_LOAD_PERFORMED,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LEAST_PRIVILEGE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    NETWORK_SESSION_STARTED,
    NEXT_CONSUMER_CAPABILITY_ID,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    WITHDRAWAL_PERMISSION,
)
from src.ops.capability_11_2_productive_credential_load_path_binding_v1.path_binding_v1 import (
    prove_productive_credential_load_path_binding_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_CredentialAuthorizationBoundary",
        "SimulatedExecutionPort",
    ],
    "credential_load": "forbidden_in_cap_11_2_boundary",
    "cap_11_3": "contracts_only_not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_CredentialAuthorizationBoundary",
        "Cap11_2_ProductiveCredentialLoadPathBinding",
        "SimulatedExecutionPort",
    ],
    "credential_load": "path_bound_fail_closed_never_executed",
    "cap_11_3": "not_started_construction_forbidden",
    "network_session": "forbidden",
    "activation": "not_activated",
}


def verify_capability_11_2_productive_credential_load_path_binding_v1() -> dict[str, Any]:
    proof = prove_productive_credential_load_path_binding_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "CREDENTIAL_LOAD_ALLOWED_DEFAULT": CREDENTIAL_LOAD_ALLOWED_DEFAULT,
        "CREDENTIAL_LOAD_PERFORMED": CREDENTIAL_LOAD_PERFORMED,
        "CREDENTIAL_PLAINTEXT_LOADED": CREDENTIAL_PLAINTEXT_LOADED,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
        "NETWORK_SESSION_STARTED": NETWORK_SESSION_STARTED,
        "CAPABILITY_11_3_STARTED": CAPABILITY_11_3_STARTED,
        "CAPABILITY_11_3_PRIVATE_READONLY_STARTED": CAPABILITY_11_3_PRIVATE_READONLY_STARTED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": EXCHANGE_ORDER_SUBMIT_REACHABLE,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": AUTHORIZATION_CONSUMPTION_ALLOWED,
        "LEAST_PRIVILEGE": LEAST_PRIVILEGE,
        "WITHDRAWAL_PERMISSION": WITHDRAWAL_PERMISSION,
        "PATH_BINDING_PROOF_OK": proof.get("ok"),
        "COMPLETE_PATH_LOAD_STILL_FORBIDDEN": proof.get("complete_path_load_still_forbidden"),
        "PLAINTEXT_REJECTED": proof.get("plaintext_rejected"),
        "WITHDRAWAL_REJECTED": proof.get("withdrawal_rejected"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"path_binding": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
