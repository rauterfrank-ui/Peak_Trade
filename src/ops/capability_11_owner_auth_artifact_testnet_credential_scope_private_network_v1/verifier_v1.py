"""Verifier for Owner Auth Artifact Testnet credential scope private network."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_CONSUMED,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_PERFORMED,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LEAST_PRIVILEGE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_SCOPE_REQUIRED,
    NETWORK_SESSION_STARTED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    WITHDRAWAL_PERMISSION,
)
from src.ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1.owner_auth_artifact_v1 import (
    prove_owner_auth_artifact_testnet_credential_scope_private_network_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_ProductiveCredentialLoadPathBinding",
        "Cap11_3_ProductivePrivateReadonlyPathBinding",
        "SimulatedExecutionPort",
    ],
    "owner_auth_artifact": "absent",
    "order_send": "disabled",
    "cap_11_4": "contracts_only_not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_ProductiveCredentialLoadPathBinding",
        "Cap11_3_ProductivePrivateReadonlyPathBinding",
        "OwnerAuthArtifactTestnetCredentialScopePrivateNetwork",
        "SimulatedExecutionPort",
    ],
    "owner_auth_artifact": "issued_fail_closed_unconsumed",
    "network_scope": "PRIVATE_READONLY_GET_ONLY",
    "get_allowlist": ["accounts", "open_positions", "open_orders"],
    "order_send": "disabled",
    "authorization_consumption": "forbidden",
    "network_session": "forbidden",
    "credential_load": "forbidden",
    "activation": "not_activated",
}


def verify_capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1() -> dict[
    str, Any
]:
    proof = prove_owner_auth_artifact_testnet_credential_scope_private_network_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT": OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT,
        "ORDER_SEND_DISABLED": ORDER_SEND_DISABLED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "ORDER_PATH_STARTED": ORDER_PATH_STARTED,
        "MUTATING_EXCHANGE_CALLS": MUTATING_EXCHANGE_CALLS,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": AUTHORIZATION_CONSUMPTION_ALLOWED,
        "AUTHORIZATION_CONSUMED": AUTHORIZATION_CONSUMED,
        "NETWORK_SESSION_STARTED": NETWORK_SESSION_STARTED,
        "NETWORK_SCOPE_REQUIRED": NETWORK_SCOPE_REQUIRED,
        "CREDENTIAL_LOAD_PERFORMED": CREDENTIAL_LOAD_PERFORMED,
        "CREDENTIAL_PLAINTEXT_LOADED": CREDENTIAL_PLAINTEXT_LOADED,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
        "CAPABILITY_11_4_STARTED": CAPABILITY_11_4_STARTED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": EXCHANGE_ORDER_SUBMIT_REACHABLE,
        "LEAST_PRIVILEGE": LEAST_PRIVILEGE,
        "WITHDRAWAL_PERMISSION": WITHDRAWAL_PERMISSION,
        "OWNER_AUTH_ARTIFACT_PROOF_OK": proof.get("ok"),
        "COMPLETE_ARTIFACT_ADMISSIBLE": proof.get("complete_artifact_admissible"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "CONSUMED_HARD_REJECT": proof.get("consumed_hard_reject"),
        "PLAINTEXT_REJECTED": proof.get("plaintext_rejected"),
        "WITHDRAWAL_REJECTED": proof.get("withdrawal_rejected"),
        "BAD_NETWORK_SCOPE_BLOCKED": proof.get("bad_network_scope_blocked"),
        "BAD_ALLOWLIST_BLOCKED": proof.get("bad_allowlist_blocked"),
        "ORDER_TYPES_BLOCKED": proof.get("order_types_blocked"),
        "MUTATION_BLOCKED": proof.get("mutation_blocked"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"owner_auth_artifact": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
