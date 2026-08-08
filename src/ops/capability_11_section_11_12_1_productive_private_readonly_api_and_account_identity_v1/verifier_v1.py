"""Verifier for Cap 11 §11.12.1 productive private-readonly API and account identity."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.constants_v1 import (
    ACCOUNT_IDENTITY_ENDPOINT,
    ACCOUNT_IDENTITY_FETCH_ALLOWED,
    ACCOUNT_IDENTITY_HTTP_METHOD,
    ACCOUNT_IDENTITY_PATH_CLASS,
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PREDECESSOR_CAPABILITY_ID,
    PRIVATE_READONLY_NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    TESTNET_EXECUTION_REACHABLE,
    TRANSPORT_CLASS_GOVERNED_FIXTURE,
    WITHDRAWAL_PERMISSION,
)
from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.section_11_12_1_v1 import (
    prove_section_11_12_1_productive_private_readonly_api_and_account_identity_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_ProductivePrivateReadonlyFetchReferenceOnly",
        "SimulatedExecutionPort",
    ],
    "section_11_12_1": "forbidden_after_fetch_reference_only",
    "authorization_consumption": "forbidden_in_predecessor",
    "credential_consumption": "forbidden_in_predecessor",
    "private_readonly_network_session": "forbidden_in_predecessor",
    "cap_11_4": "contracts_only_not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_ProductivePrivateReadonlyFetchReferenceOnly",
        "Cap11_Section_11_12_1_ProductivePrivateReadonlyApiAndAccountIdentity",
        "SimulatedExecutionPort",
    ],
    "section_11_12_1": "productive_account_identity_get_bound",
    "http_method": ACCOUNT_IDENTITY_HTTP_METHOD,
    "endpoint": ACCOUNT_IDENTITY_ENDPOINT,
    "path_class": ACCOUNT_IDENTITY_PATH_CLASS,
    "authorization_consumption": "scoped_consumed_for_private_readonly_account_identity",
    "credential_consumption": "scoped_consumed_material_digest_only",
    "private_readonly_network_session": "started_get_only",
    "order_send": "disabled",
    "network_writes": "unauthorized",
    "activation": "not_activated",
    "cap_11_4": "not_started",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1() -> (
    dict[str, Any]
):
    proof = prove_section_11_12_1_productive_private_readonly_api_and_account_identity_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": AUTHORIZATION_CONSUMPTION_ALLOWED,
        "PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED": PRODUCTIVE_CREDENTIAL_CONSUMPTION_ALLOWED,
        "PRIVATE_READONLY_NETWORK_SESSION_ALLOWED": PRIVATE_READONLY_NETWORK_SESSION_ALLOWED,
        "ACCOUNT_IDENTITY_FETCH_ALLOWED": ACCOUNT_IDENTITY_FETCH_ALLOWED,
        "AUTHORIZATION_CONSUMED": proof.get("authorization_consumed"),
        "CREDENTIAL_CONSUMED": proof.get("credential_consumed"),
        "NETWORK_SESSION_STARTED": proof.get("network_session_started"),
        "ACCOUNT_IDENTITY_FETCH_PERFORMED": proof.get("account_identity_fetch_performed"),
        "HTTP_METHOD": proof.get("http_method"),
        "ENDPOINT": proof.get("endpoint"),
        "PATH_CLASS": proof.get("path_class"),
        "TRANSPORT_CLASS": proof.get("transport_class"),
        "VENUE_LIVE_CONTACT": proof.get("venue_live_contact"),
        "ORDER_SEND_DISABLED": ORDER_SEND_DISABLED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "ORDER_PATH_STARTED": ORDER_PATH_STARTED,
        "MUTATING_EXCHANGE_CALLS": MUTATING_EXCHANGE_CALLS,
        "NETWORK_WRITES_AUTHORIZED": NETWORK_WRITES_AUTHORIZED,
        "NETWORK_WRITE_PERFORMED": proof.get("network_write_performed"),
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": proof.get("exchange_order_submit_reachable"),
        "CAPABILITY_11_4_STARTED": CAPABILITY_11_4_STARTED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "WITHDRAWAL_PERMISSION": WITHDRAWAL_PERMISSION,
        "SECTION_11_12_1_PROOF_OK": proof.get("ok"),
        "COMPLETE_EXECUTION_OK": proof.get("complete_execution_ok"),
        "INCOMPLETE_BLOCKED": proof.get("incomplete_blocked"),
        "REPLAY_BLOCKED": proof.get("replay_blocked"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "NETWORK_WRITE_HARD_REJECT": proof.get("network_write_hard_reject"),
        "PLAINTEXT_REJECTED": proof.get("plaintext_rejected"),
        "NON_GET_BLOCKED": proof.get("non_get_blocked"),
        "OPEN_POSITIONS_BLOCKED": proof.get("open_positions_blocked"),
        "MUTATION_BLOCKED": proof.get("mutation_blocked"),
        "ORDER_SEND_BLOCKED": proof.get("order_send_blocked"),
        "WRITE_BLOCKED": proof.get("write_blocked"),
        "CAP_11_4_BLOCKED": proof.get("cap_11_4_blocked"),
        "CAP_11_13_BLOCKED": proof.get("cap_11_13_blocked"),
        "IDENTITY_MISMATCH_BLOCKED": proof.get("identity_mismatch_blocked"),
        "LIVE_MODE_BLOCKED": proof.get("live_mode_blocked"),
        "GOVERNED_FIXTURE_TRANSPORT": proof.get("transport_class")
        == TRANSPORT_CLASS_GOVERNED_FIXTURE,
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"section_11_12_1": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
