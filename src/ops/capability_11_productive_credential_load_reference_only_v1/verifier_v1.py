"""Verifier for Cap 11 productive credential-load reference-only."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_productive_credential_load_reference_only_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_CONSUMED,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_CONSUMED,
    CREDENTIAL_LOAD_PERFORMED,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LEAST_PRIVILEGE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_SESSION_STARTED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    WITHDRAWAL_PERMISSION,
)
from src.ops.capability_11_productive_credential_load_reference_only_v1.reference_only_load_v1 import (
    prove_productive_credential_load_reference_only_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_ProductiveCredentialLoadPathBinding",
        "Cap11_3_ProductivePrivateReadonlyPathBinding",
        "OwnerAuthArtifactTestnetCredentialScopePrivateNetwork",
        "SimulatedExecutionPort",
    ],
    "credential_load": "forbidden_after_owner_auth_artifact",
    "cap_11_4": "contracts_only_not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_2_ProductiveCredentialLoadPathBinding",
        "Cap11_3_ProductivePrivateReadonlyPathBinding",
        "OwnerAuthArtifactTestnetCredentialScopePrivateNetwork",
        "Cap11_ProductiveCredentialLoadReferenceOnly",
        "SimulatedExecutionPort",
    ],
    "credential_load": "reference_only_bound_fail_closed_never_materialized",
    "authorization_consumption": "forbidden",
    "network_session": "forbidden",
    "order_send": "disabled",
    "activation": "not_activated",
}


def verify_capability_11_productive_credential_load_reference_only_v1() -> dict[str, Any]:
    proof = prove_productive_credential_load_reference_only_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT": REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT,
        "ORDER_SEND_DISABLED": ORDER_SEND_DISABLED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "ORDER_PATH_STARTED": ORDER_PATH_STARTED,
        "MUTATING_EXCHANGE_CALLS": MUTATING_EXCHANGE_CALLS,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": AUTHORIZATION_CONSUMPTION_ALLOWED,
        "AUTHORIZATION_CONSUMED": AUTHORIZATION_CONSUMED,
        "CREDENTIAL_CONSUMED": CREDENTIAL_CONSUMED,
        "NETWORK_SESSION_STARTED": NETWORK_SESSION_STARTED,
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
        "REFERENCE_ONLY_PROOF_OK": proof.get("ok"),
        "COMPLETE_REFERENCE_ONLY_LOAD_ADMISSIBLE": proof.get(
            "complete_reference_only_load_admissible"
        ),
        "INTENDED_CREDENTIAL_OBJECT_BOUND": proof.get("intended_credential_object_bound"),
        "COMPLETE_PATH_MATERIALIZATION_STILL_FORBIDDEN": proof.get(
            "complete_path_materialization_still_forbidden"
        ),
        "PLAINTEXT_REJECTED": proof.get("plaintext_rejected"),
        "WITHDRAWAL_REJECTED": proof.get("withdrawal_rejected"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "CONSUMED_HARD_REJECT": proof.get("consumed_hard_reject"),
        "CREDENTIAL_CONSUMED_HARD_REJECT": proof.get("credential_consumed_hard_reject"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"reference_only_load": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
