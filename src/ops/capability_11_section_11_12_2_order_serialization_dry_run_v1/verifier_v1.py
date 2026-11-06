"""Verifier for Cap 11 §11.12.2 order serialization dry-run."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED,
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
    ORDER_SERIALIZATION_DRY_RUN_ALLOWED,
    ORDER_SERIALIZATION_NETWORK_EFFECT,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    SECTION_11_12_3_STARTED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ORDER_SUBMIT_PERFORMED,
)
from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.section_11_12_2_v1 import (
    prove_section_11_12_2_order_serialization_dry_run_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_1_ProductivePrivateReadonlyApiAndAccountIdentity",
        "Cap11_4_OrderSerializationDryRunContract_FixtureOnly",
        "SimulatedExecutionPort",
    ],
    "section_11_12_2": "forbidden_until_section_11_12_1_closed",
    "order_serialization_dry_run": "cap_11_4_fixture_contract_only",
    "network_submit": "forbidden",
    "section_11_12_3": "not_started",
    "cap_11_4_adapter": "contracts_only_not_activated",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_1_ProductivePrivateReadonlyApiAndAccountIdentity",
        "Cap11_Section_11_12_2_OrderSerializationDryRun",
        "SimulatedExecutionPort",
    ],
    "section_11_12_2": "productive_order_serialization_dry_run_bound",
    "path_class": PATH_CLASS,
    "cap_11_4_order_serialization_contract": "reused_fixture_only",
    "network_effect": ORDER_SERIALIZATION_NETWORK_EFFECT,
    "order_send": "disabled",
    "network_writes": "unauthorized",
    "activation": "not_activated",
    "section_11_12_3": "not_started",
    "cap_11_4_adapter": "not_activated",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_capability_11_section_11_12_2_order_serialization_dry_run_v1() -> dict[str, Any]:
    proof = prove_section_11_12_2_order_serialization_dry_run_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "ORDER_SERIALIZATION_DRY_RUN_ALLOWED": ORDER_SERIALIZATION_DRY_RUN_ALLOWED,
        "ORDER_SERIALIZATION_DRY_RUN_PERFORMED": proof.get("order_serialization_dry_run_performed"),
        "CAP_11_4_ORDER_SERIALIZATION_CONTRACT_REUSED": proof.get(
            "cap_11_4_order_serialization_contract_reused"
        ),
        "SECTION_11_12_1_PREDECESSOR_BOUND": proof.get("section_11_12_1_predecessor_bound"),
        "PATH_CLASS": proof.get("path_class"),
        "ORDER_SERIALIZATION_NETWORK_EFFECT": ORDER_SERIALIZATION_NETWORK_EFFECT,
        "NETWORK_EFFECT": proof.get("network_effect"),
        "SUBMITTED": proof.get("submitted"),
        "SERIALIZATION_SOURCE": proof.get("serialization_source"),
        "ORDER_SEND_DISABLED": ORDER_SEND_DISABLED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "ORDER_PATH_STARTED": ORDER_PATH_STARTED,
        "MUTATING_EXCHANGE_CALLS": MUTATING_EXCHANGE_CALLS,
        "NETWORK_WRITES_AUTHORIZED": NETWORK_WRITES_AUTHORIZED,
        "NETWORK_WRITE_PERFORMED": proof.get("network_write_performed"),
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": proof.get("exchange_order_submit_reachable"),
        "TESTNET_ORDER_SUBMIT_PERFORMED": TESTNET_ORDER_SUBMIT_PERFORMED,
        "CAPABILITY_11_4_STARTED": CAPABILITY_11_4_STARTED,
        "CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED": (
            CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED
        ),
        "SECTION_11_12_3_STARTED": SECTION_11_12_3_STARTED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "SECTION_11_12_2_PROOF_OK": proof.get("ok"),
        "COMPLETE_EXECUTION_OK": proof.get("complete_execution_ok"),
        "INCOMPLETE_BLOCKED": proof.get("incomplete_blocked"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "NETWORK_WRITE_HARD_REJECT": proof.get("network_write_hard_reject"),
        "LIVE_MODE_BLOCKED": proof.get("live_mode_blocked"),
        "NON_FIXTURE_BLOCKED": proof.get("non_fixture_blocked"),
        "SUBMIT_BLOCKED": proof.get("submit_blocked"),
        "ORDER_SEND_BLOCKED": proof.get("order_send_blocked"),
        "WRITE_BLOCKED": proof.get("write_blocked"),
        "SECTION_11_12_3_BLOCKED": proof.get("section_11_12_3_blocked"),
        "CAP_11_4_ADAPTER_BLOCKED": proof.get("cap_11_4_adapter_blocked"),
        "CAP_11_13_BLOCKED": proof.get("cap_11_13_blocked"),
        "FIELD_MISSING_BLOCKED": proof.get("field_missing_blocked"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"section_11_12_2": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
