"""Verifier for Cap 11 §11.12.6 restart with open order and open position."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.constants_v1 import (
    ACTIVATION_STATE,
    ALLOWED_SECTION_11_12_6_PATHS,
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
    RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_ALLOWED,
    SECTION_11_12_7_STARTED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)
from src.ops.capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.section_11_12_6_v1 import (
    prove_section_11_12_6_restart_with_open_order_and_open_position_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_5_UnknownSubmitAndReconnectRecovery",
        "Cap11_5_RestartWithOpenOrderPosition_FixtureOnly",
        "SimulatedExecutionPort",
    ],
    "section_11_12_6": "forbidden_until_section_11_12_5_closed",
    "restart_with_open_order_and_open_position": "cap_11_5_fixture_contract_only",
    "network_submit": "forbidden",
    "section_11_12_7": "not_started",
    "cap_11_5_adapter": "contracts_only_not_activated",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_5_UnknownSubmitAndReconnectRecovery",
        "Cap11_Section_11_12_6_RestartWithOpenOrderAndOpenPosition",
        "SimulatedExecutionPort",
    ],
    "section_11_12_6": "productive_restart_with_open_order_and_open_position_bound",
    "path_class": PATH_CLASS,
    "cap_11_5_restart_with_open_order_position_contract": "reused_fixture_only",
    "paths_bound": list(ALLOWED_SECTION_11_12_6_PATHS),
    "network_effect": LIFECYCLE_NETWORK_EFFECT,
    "order_send": "disabled",
    "network_writes": "unauthorized",
    "silent_reinitialization": "forbidden",
    "reconciliation_before_alpha": "required",
    "activation": "not_activated",
    "section_11_12_7": "not_started",
    "cap_11_5_adapter": "not_activated",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1() -> dict[
    str, Any
]:
    proof = prove_section_11_12_6_restart_with_open_order_and_open_position_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_ALLOWED": (
            RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_ALLOWED
        ),
        "RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_PERFORMED": proof.get(
            "restart_with_open_order_and_open_position_performed"
        ),
        "CAP_11_5_RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_REUSED": proof.get(
            "cap_11_5_restart_with_open_order_position_contract_reused"
        ),
        "SECTION_11_12_5_PREDECESSOR_BOUND": proof.get("section_11_12_5_predecessor_bound"),
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
        "SECTION_11_12_7_STARTED": SECTION_11_12_7_STARTED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": TESTNET_ORDER_LIFECYCLE_PROVEN,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
        "TESTNET_RESTART_PROVEN": TESTNET_RESTART_PROVEN,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "SECTION_11_12_6_PROOF_OK": proof.get("ok"),
        "COMPLETE_EXECUTION_OK": proof.get("complete_execution_ok"),
        "INCOMPLETE_BLOCKED": proof.get("incomplete_blocked"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "NETWORK_WRITE_HARD_REJECT": proof.get("network_write_hard_reject"),
        "LIVE_MODE_BLOCKED": proof.get("live_mode_blocked"),
        "SECTION_11_12_7_PATH_BLOCKED": proof.get("section_11_12_7_path_blocked"),
        "UNKNOWN_SUBMIT_PATH_BLOCKED": proof.get("unknown_submit_path_blocked"),
        "CAMPAIGN_PATH_BLOCKED": proof.get("campaign_path_blocked"),
        "SUBMIT_BLOCKED": proof.get("submit_blocked"),
        "ORDER_SEND_BLOCKED": proof.get("order_send_blocked"),
        "WRITE_BLOCKED": proof.get("write_blocked"),
        "SILENT_REINITIALIZATION_BLOCKED": proof.get("silent_reinitialization_blocked"),
        "RESTART_NETWORK_SESSION_ACTIVATION_BLOCKED": proof.get(
            "restart_network_session_activation_blocked"
        ),
        "SECTION_11_12_7_BLOCKED": proof.get("section_11_12_7_blocked"),
        "CAP_11_5_ADAPTER_BLOCKED": proof.get("cap_11_5_adapter_blocked"),
        "CAP_11_13_BLOCKED": proof.get("cap_11_13_blocked"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"section_11_12_6": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
