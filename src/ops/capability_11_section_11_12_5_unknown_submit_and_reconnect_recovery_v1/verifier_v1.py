"""Verifier for Cap 11 §11.12.5 unknown-submit and reconnect recovery."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1.constants_v1 import (
    ACTIVATION_STATE,
    ALLOWED_SECTION_11_12_5_PATHS,
    CAPABILITY_11_5_STARTED,
    CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIFECYCLE_NETWORK_EFFECT,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    SECTION_11_12_6_STARTED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
    UNKNOWN_SUBMIT_AND_RECONNECT_RECOVERY_ALLOWED,
)
from src.ops.capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1.section_11_12_5_v1 import (
    prove_section_11_12_5_unknown_submit_and_reconnect_recovery_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_4_EntryPartialFillCancelExitLifecycles",
        "Cap11_5_UnknownSubmitReconnect_FixtureOnly",
        "SimulatedExecutionPort",
    ],
    "section_11_12_5": "forbidden_until_section_11_12_4_closed",
    "unknown_submit_and_reconnect_recovery": "cap_11_5_fixture_contract_only",
    "network_submit": "forbidden",
    "section_11_12_6": "not_started",
    "cap_11_5_adapter": "contracts_only_not_activated",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_4_EntryPartialFillCancelExitLifecycles",
        "Cap11_Section_11_12_5_UnknownSubmitAndReconnectRecovery",
        "SimulatedExecutionPort",
    ],
    "section_11_12_5": "productive_unknown_submit_and_reconnect_recovery_bound",
    "path_class": PATH_CLASS,
    "cap_11_5_unknown_submit_reconnect_contract": "reused_fixture_only",
    "paths_bound": list(ALLOWED_SECTION_11_12_5_PATHS),
    "network_effect": LIFECYCLE_NETWORK_EFFECT,
    "order_send": "disabled",
    "network_writes": "unauthorized",
    "blind_retry": "forbidden",
    "exchange_query_before_retry": "required",
    "activation": "not_activated",
    "section_11_12_6": "not_started",
    "cap_11_5_adapter": "not_activated",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1() -> dict[
    str, Any
]:
    proof = prove_section_11_12_5_unknown_submit_and_reconnect_recovery_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "UNKNOWN_SUBMIT_AND_RECONNECT_RECOVERY_ALLOWED": (
            UNKNOWN_SUBMIT_AND_RECONNECT_RECOVERY_ALLOWED
        ),
        "UNKNOWN_SUBMIT_AND_RECONNECT_RECOVERY_PERFORMED": proof.get(
            "unknown_submit_and_reconnect_recovery_performed"
        ),
        "CAP_11_5_UNKNOWN_SUBMIT_RECONNECT_CONTRACT_REUSED": proof.get(
            "cap_11_5_unknown_submit_reconnect_contract_reused"
        ),
        "SECTION_11_12_4_PREDECESSOR_BOUND": proof.get("section_11_12_4_predecessor_bound"),
        "PATH_CLASS": proof.get("path_class"),
        "PATHS_COMPLETED": proof.get("paths_completed"),
        "LIFECYCLE_NETWORK_EFFECT": LIFECYCLE_NETWORK_EFFECT,
        "NETWORK_EFFECT": proof.get("network_effect"),
        "EXCHANGE_SUBMIT_PERFORMED": proof.get("exchange_submit_performed"),
        "LIFECYCLE_SOURCE": proof.get("lifecycle_source"),
        "ORDER_SEND_DISABLED": ORDER_SEND_DISABLED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "ORDER_PATH_STARTED": ORDER_PATH_STARTED,
        "MUTATING_EXCHANGE_CALLS": MUTATING_EXCHANGE_CALLS,
        "NETWORK_WRITES_AUTHORIZED": NETWORK_WRITES_AUTHORIZED,
        "NETWORK_WRITE_PERFORMED": proof.get("network_write_performed"),
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": proof.get("exchange_order_submit_reachable"),
        "TESTNET_ORDER_SUBMIT_PERFORMED": TESTNET_ORDER_SUBMIT_PERFORMED,
        "CAPABILITY_11_5_STARTED": CAPABILITY_11_5_STARTED,
        "CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED": (
            CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED
        ),
        "SECTION_11_12_6_STARTED": SECTION_11_12_6_STARTED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": TESTNET_ORDER_LIFECYCLE_PROVEN,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "SECTION_11_12_5_PROOF_OK": proof.get("ok"),
        "COMPLETE_EXECUTION_OK": proof.get("complete_execution_ok"),
        "INCOMPLETE_BLOCKED": proof.get("incomplete_blocked"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "NETWORK_WRITE_HARD_REJECT": proof.get("network_write_hard_reject"),
        "LIVE_MODE_BLOCKED": proof.get("live_mode_blocked"),
        "SECTION_11_12_6_PATH_BLOCKED": proof.get("section_11_12_6_path_blocked"),
        "ENTRY_PATH_BLOCKED": proof.get("entry_path_blocked"),
        "UNKNOWN_PATH_BLOCKED": proof.get("unknown_path_blocked"),
        "SUBMIT_BLOCKED": proof.get("submit_blocked"),
        "ORDER_SEND_BLOCKED": proof.get("order_send_blocked"),
        "WRITE_BLOCKED": proof.get("write_blocked"),
        "BLIND_RETRY_BLOCKED": proof.get("blind_retry_blocked"),
        "RECONNECT_ACTIVATION_BLOCKED": proof.get("reconnect_activation_blocked"),
        "SECTION_11_12_6_BLOCKED": proof.get("section_11_12_6_blocked"),
        "CAP_11_5_ADAPTER_BLOCKED": proof.get("cap_11_5_adapter_blocked"),
        "CAP_11_13_BLOCKED": proof.get("cap_11_13_blocked"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"section_11_12_5": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
