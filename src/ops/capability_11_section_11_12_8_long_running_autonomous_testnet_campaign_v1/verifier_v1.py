"""Verifier for Cap 11 §11.12.8 long-running autonomous Testnet campaign."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.constants_v1 import (
    ACTIVATION_STATE,
    ALLOWED_SECTION_11_12_8_PATHS,
    CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
    CAPABILITY_11_5_STARTED,
    CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED,
    CAPABILITY_11_6_STARTED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
    KILL_SWITCH_BINDING_STATUS,
    KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME,
    KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    KILL_SWITCH_FAIL_CLOSED,
    KILL_SWITCH_PERSISTED,
    KILL_SWITCH_SURVIVES_RESTART,
    LIFECYCLE_NETWORK_EFFECT,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED,
    LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_SESSION_STARTED,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER_AUTHORITY_REQUIRED_TO_CLEAR,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    SECTION_11_13_STARTED,
    TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
    TESTNET_CAMPAIGN_COMPLETED,
    TESTNET_CAMPAIGN_STARTED,
    TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN,
    TESTNET_EVIDENCE_VERIFIED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_ORDER_SUBMIT_PERFORMED,
    TESTNET_RECONCILIATION_PROVEN,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.section_11_12_8_v1 import (
    prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_7_KillSwitchAndEmergencyControlProof",
        "Cap11_6_LongRunningCampaignEvidence_FixtureOnly",
        "SimulatedExecutionPort",
    ],
    "section_11_12_8": "forbidden_until_section_11_12_7_closed",
    "long_running_campaign_evidence": "cap_11_6_fixture_contract_only",
    "network_submit": "forbidden",
    "testnet_campaign": "not_started",
    "cap_11_13": "not_started",
    "kill_switch_contract": "bound_not_activated",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_7_KillSwitchAndEmergencyControlProof",
        "Cap11_Section_11_12_8_LongRunningAutonomousTestnetCampaignEvidence",
        "SimulatedExecutionPort",
    ],
    "section_11_12_8": "productive_long_running_campaign_evidence_bound",
    "path_class": PATH_CLASS,
    "cap_11_6_long_running_campaign_evidence_contract": "reused_fixture_only",
    "paths_bound": list(ALLOWED_SECTION_11_12_8_PATHS),
    "network_effect": LIFECYCLE_NETWORK_EFFECT,
    "order_effect": ORDER_EFFECT,
    "order_send": "disabled",
    "network_writes": "unauthorized",
    "testnet_campaign_started": False,
    "testnet_campaign_completed": False,
    "campaign_activated": False,
    "runtime_clear": "forbidden",
    "side_effect_bypass": "forbidden",
    "scope_escalation": "forbidden",
    "activation": "not_activated",
    "kill_switch_binding_status": KILL_SWITCH_BINDING_STATUS,
    "kill_switch_contract": "not_activated",
    "testnet_evidence_verified": False,
    "cap_11_13": "not_started",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1() -> dict[
    str, Any
]:
    proof = prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED": (
            LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_EVIDENCE_ALLOWED
        ),
        "LONG_RUNNING_CAMPAIGN_EVIDENCE_PERFORMED": proof.get(
            "long_running_campaign_evidence_performed"
        ),
        "CAP_11_6_LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_REUSED": proof.get(
            "cap_11_6_long_running_campaign_evidence_contract_reused"
        ),
        "SECTION_11_12_7_PREDECESSOR_BOUND": proof.get("section_11_12_7_predecessor_bound"),
        "KILL_SWITCH_BINDING_STATUS": proof.get("kill_switch_binding_status"),
        "PATH_CLASS": proof.get("path_class"),
        "PATHS_COMPLETED": proof.get("paths_completed"),
        "LIFECYCLE_NETWORK_EFFECT": LIFECYCLE_NETWORK_EFFECT,
        "NETWORK_EFFECT": proof.get("network_effect"),
        "ORDER_EFFECT": proof.get("order_effect"),
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
        "TESTNET_CAMPAIGN_STARTED": TESTNET_CAMPAIGN_STARTED,
        "TESTNET_CAMPAIGN_COMPLETED": TESTNET_CAMPAIGN_COMPLETED,
        "LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED": (
            LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED
        ),
        "NETWORK_SESSION_STARTED": NETWORK_SESSION_STARTED,
        "CAPABILITY_11_5_STARTED": CAPABILITY_11_5_STARTED,
        "CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED": (
            CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED
        ),
        "CAPABILITY_11_6_STARTED": CAPABILITY_11_6_STARTED,
        "KILL_SWITCH_CONTRACT_ACTIVATED": KILL_SWITCH_CONTRACT_ACTIVATED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": TESTNET_ORDER_LIFECYCLE_PROVEN,
        "TESTNET_RECONCILIATION_PROVEN": TESTNET_RECONCILIATION_PROVEN,
        "TESTNET_RESTART_PROVEN": TESTNET_RESTART_PROVEN,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
        "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN,
        "TESTNET_KILL_SWITCH_PROVEN": TESTNET_KILL_SWITCH_PROVEN,
        "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
        "TESTNET_EVIDENCE_VERIFIED": TESTNET_EVIDENCE_VERIFIED,
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
        "SECTION_11_12_8_PROOF_OK": proof.get("ok"),
        "COMPLETE_EXECUTION_OK": proof.get("complete_execution_ok"),
        "INCOMPLETE_BLOCKED": proof.get("incomplete_blocked"),
        "ORDER_SEND_HARD_REJECT": proof.get("order_send_hard_reject"),
        "ORDERS_AUTHORIZED_HARD_REJECT": proof.get("orders_authorized_hard_reject"),
        "NETWORK_WRITE_HARD_REJECT": proof.get("network_write_hard_reject"),
        "CAMPAIGN_START_HARD_REJECT": proof.get("campaign_start_hard_reject"),
        "LIVE_MODE_BLOCKED": proof.get("live_mode_blocked"),
        "UNKNOWN_PATH_BLOCKED": proof.get("unknown_path_blocked"),
        "PRODUCTIVE_PATH_BLOCKED": proof.get("productive_path_blocked"),
        "SUBMIT_BLOCKED": proof.get("submit_blocked"),
        "ORDER_SEND_BLOCKED": proof.get("order_send_blocked"),
        "WRITE_BLOCKED": proof.get("write_blocked"),
        "CAMPAIGN_START_BLOCKED": proof.get("campaign_start_blocked"),
        "SESSION_BLOCKED": proof.get("session_blocked"),
        "ACTIVATION_BLOCKED": proof.get("activation_blocked"),
        "RUNTIME_CLEAR_BLOCKED": proof.get("runtime_clear_blocked"),
        "SIDE_EFFECT_BYPASS_BLOCKED": proof.get("side_effect_bypass_blocked"),
        "SCOPE_ESCALATION_BLOCKED": proof.get("scope_escalation_blocked"),
        "CAP_11_6_ADAPTER_BLOCKED": proof.get("cap_11_6_adapter_blocked"),
        "KILL_SWITCH_CONTRACT_ACTIVATION_BLOCKED": proof.get(
            "kill_switch_contract_activation_blocked"
        ),
        "CAP_11_13_BLOCKED": proof.get("cap_11_13_blocked"),
        "PROVEN_OVERCLAIM_BLOCKED": proof.get("proven_overclaim_blocked"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"section_11_12_8": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
