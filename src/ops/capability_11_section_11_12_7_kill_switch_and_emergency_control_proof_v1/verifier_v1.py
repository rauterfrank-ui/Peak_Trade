"""Verifier for Cap 11 §11.12.7 kill-switch and emergency control proof."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.constants_v1 import (
    ACTIVATION_STATE,
    ALLOWED_SECTION_11_12_7_COMMANDS,
    CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
    CAPABILITY_11_5_STARTED,
    CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
    KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED,
    KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME,
    KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    KILL_SWITCH_FAIL_CLOSED,
    KILL_SWITCH_PERSISTED,
    KILL_SWITCH_SURVIVES_RESTART,
    LIFECYCLE_NETWORK_EFFECT,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER_AUTHORITY_REQUIRED_TO_CLEAR,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    SECTION_11_12_8_STARTED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)
from src.ops.capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1.section_11_12_7_v1 import (
    prove_section_11_12_7_kill_switch_and_emergency_control_proof_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_6_RestartWithOpenOrderAndOpenPosition",
        "Cap11_5_KillSwitchAndEmergencyControl_FixtureOnly",
        "SimulatedExecutionPort",
    ],
    "section_11_12_7": "forbidden_until_section_11_12_6_closed",
    "kill_switch_and_emergency_control": "cap_11_5_fixture_contract_only",
    "network_submit": "forbidden",
    "section_11_12_8": "not_started",
    "cap_11_5_adapter": "contracts_only_not_activated",
    "kill_switch_contract": "bound_not_activated",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_6_RestartWithOpenOrderAndOpenPosition",
        "Cap11_Section_11_12_7_KillSwitchAndEmergencyControlProof",
        "SimulatedExecutionPort",
    ],
    "section_11_12_7": "productive_kill_switch_and_emergency_control_proof_bound",
    "path_class": PATH_CLASS,
    "cap_11_5_kill_switch_and_emergency_control_contract": "reused_fixture_only",
    "commands_bound": list(ALLOWED_SECTION_11_12_7_COMMANDS),
    "network_effect": LIFECYCLE_NETWORK_EFFECT,
    "order_send": "disabled",
    "network_writes": "unauthorized",
    "runtime_clear": "forbidden",
    "side_effect_bypass": "forbidden",
    "risk_increase": "forbidden",
    "activation": "not_activated",
    "kill_switch_contract": "not_activated",
    "testnet_kill_switch_proven": False,
    "section_11_12_8": "not_started",
    "cap_11_5_adapter": "not_activated",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_capability_11_section_11_12_7_kill_switch_and_emergency_control_proof_v1() -> dict[
    str, Any
]:
    proof = prove_section_11_12_7_kill_switch_and_emergency_control_proof_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED": (
            KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_ALLOWED
        ),
        "KILL_SWITCH_AND_EMERGENCY_CONTROL_PROOF_PERFORMED": proof.get(
            "kill_switch_and_emergency_control_proof_performed"
        ),
        "CAP_11_5_KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_REUSED": proof.get(
            "cap_11_5_kill_switch_and_emergency_control_contract_reused"
        ),
        "SECTION_11_12_6_PREDECESSOR_BOUND": proof.get("section_11_12_6_predecessor_bound"),
        "PATH_CLASS": proof.get("path_class"),
        "COMMANDS_COMPLETED": proof.get("commands_completed"),
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
        "KILL_SWITCH_CONTRACT_ACTIVATED": KILL_SWITCH_CONTRACT_ACTIVATED,
        "SECTION_11_12_8_STARTED": SECTION_11_12_8_STARTED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": TESTNET_ORDER_LIFECYCLE_PROVEN,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
        "TESTNET_RESTART_PROVEN": TESTNET_RESTART_PROVEN,
        "TESTNET_KILL_SWITCH_PROVEN": TESTNET_KILL_SWITCH_PROVEN,
        "KILL_SWITCH_PERSISTED": KILL_SWITCH_PERSISTED,
        "KILL_SWITCH_FAIL_CLOSED": KILL_SWITCH_FAIL_CLOSED,
        "KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT": (
            KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT
        ),
        "KILL_SWITCH_SURVIVES_RESTART": KILL_SWITCH_SURVIVES_RESTART,
        "KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME": KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME,
        "OWNER_AUTHORITY_REQUIRED_TO_CLEAR": OWNER_AUTHORITY_REQUIRED_TO_CLEAR,
        "CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA": CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
        "EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA": EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "SECTION_11_12_7_PROOF_OK": proof.get("ok"),
        "COMPLETE_EXECUTION_OK": proof.get("complete_execution_ok"),
        "INCOMPLETE_BLOCKED": proof.get("incomplete_blocked"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "NETWORK_WRITE_HARD_REJECT": proof.get("network_write_hard_reject"),
        "LIVE_MODE_BLOCKED": proof.get("live_mode_blocked"),
        "SECTION_11_12_8_COMMAND_BLOCKED": proof.get("section_11_12_8_command_blocked"),
        "UNKNOWN_COMMAND_BLOCKED": proof.get("unknown_command_blocked"),
        "RESTART_PATH_BLOCKED": proof.get("restart_path_blocked"),
        "SUBMIT_BLOCKED": proof.get("submit_blocked"),
        "ORDER_SEND_BLOCKED": proof.get("order_send_blocked"),
        "WRITE_BLOCKED": proof.get("write_blocked"),
        "RUNTIME_CLEAR_BLOCKED": proof.get("runtime_clear_blocked"),
        "SIDE_EFFECT_BYPASS_BLOCKED": proof.get("side_effect_bypass_blocked"),
        "RISK_INCREASE_BLOCKED": proof.get("risk_increase_blocked"),
        "SECTION_11_12_8_BLOCKED": proof.get("section_11_12_8_blocked"),
        "CAP_11_5_ADAPTER_BLOCKED": proof.get("cap_11_5_adapter_blocked"),
        "KILL_SWITCH_CONTRACT_ACTIVATION_BLOCKED": proof.get(
            "kill_switch_contract_activation_blocked"
        ),
        "CAP_11_13_BLOCKED": proof.get("cap_11_13_blocked"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"section_11_12_7": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
