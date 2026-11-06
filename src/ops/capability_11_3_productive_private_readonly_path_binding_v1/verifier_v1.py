"""Verifier for Cap 11.3 productive private read-only path binding."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_3_productive_private_readonly_path_binding_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CONTRACT_CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
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
    PRIVATE_READONLY_FETCH_PERFORMED,
    PRIVATE_READONLY_GET_ONLY,
    PRIVATE_READONLY_NETWORK_REACHABLE,
    PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN,
    PRIVATE_READONLY_PATH_ALLOWED_DEFAULT,
    PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    WITHDRAWAL_PERMISSION,
)
from src.ops.capability_11_3_productive_private_readonly_path_binding_v1.path_binding_v1 import (
    prove_productive_private_readonly_path_binding_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_ProductiveCredentialLoadPathBinding",
        "Cap11_3_PrivateReadonlyContracts",
        "SimulatedExecutionPort",
    ],
    "private_readonly_fetch": "forbidden_contracts_only",
    "cap_11_4": "contracts_only_not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_ProductiveCredentialLoadPathBinding",
        "Cap11_3_PrivateReadonlyContracts",
        "Cap11_3_ProductivePrivateReadonlyPathBinding",
        "SimulatedExecutionPort",
    ],
    "private_readonly_fetch": "path_bound_fail_closed_never_executed",
    "get_allowlist": ["accounts", "open_positions", "open_orders"],
    "mutation": "forbidden",
    "network_session": "forbidden",
    "activation": "not_activated",
}


def verify_capability_11_3_productive_private_readonly_path_binding_v1() -> dict[str, Any]:
    proof = prove_productive_private_readonly_path_binding_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "CONTRACT_CAPABILITY_ID": CONTRACT_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "PRIVATE_READONLY_PATH_ALLOWED_DEFAULT": PRIVATE_READONLY_PATH_ALLOWED_DEFAULT,
        "PRIVATE_READONLY_FETCH_PERFORMED": PRIVATE_READONLY_FETCH_PERFORMED,
        "PRIVATE_READONLY_NETWORK_REACHABLE": PRIVATE_READONLY_NETWORK_REACHABLE,
        "PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED": (
            PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED
        ),
        "PRIVATE_READONLY_GET_ONLY": PRIVATE_READONLY_GET_ONLY,
        "PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN": PRIVATE_READONLY_ORDER_MUTATION_FORBIDDEN,
        "CREDENTIAL_LOAD_PERFORMED": CREDENTIAL_LOAD_PERFORMED,
        "CREDENTIAL_PLAINTEXT_LOADED": CREDENTIAL_PLAINTEXT_LOADED,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
        "NETWORK_SESSION_STARTED": NETWORK_SESSION_STARTED,
        "CAPABILITY_11_4_STARTED": CAPABILITY_11_4_STARTED,
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
        "COMPLETE_PATH_FETCH_STILL_FORBIDDEN": proof.get("complete_path_fetch_still_forbidden"),
        "UNKNOWN_ENDPOINT_BLOCKED": proof.get("unknown_endpoint_blocked"),
        "PLAINTEXT_REJECTED": proof.get("plaintext_rejected"),
        "WITHDRAWAL_REJECTED": proof.get("withdrawal_rejected"),
        "BAD_ALLOWLIST_BLOCKED": proof.get("bad_allowlist_blocked"),
        "MUTATION_BLOCKED": proof.get("mutation_blocked"),
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
