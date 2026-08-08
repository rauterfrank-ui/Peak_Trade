"""Verifier for Cap 11 §11.12.8 productive Testnet campaign run activation surface."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.activation_v1 import (
    prove_productive_testnet_campaign_run_activation_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.constants_v1 import (
    ACTIVATION_AUTHORIZED,
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMED,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    FUTURE_ACTIVATION_GO_CONSUMED,
    FUTURE_ACTIVATION_GO_CONSUMPTION_ALLOWED,
    LIVE_AUTHORIZED,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NETWORK_SESSION_STARTED,
    NETWORK_WRITE_PERFORMED,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    PRODUCTIVE_ACTIVATION_ENTRYPOINT_PRESENT,
    PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_ABSENT,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_PRESENT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    REFERENCE_ONLY,
    RUN_AUTHORIZED,
    RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
    RUN_PREDECESSOR_PRESERVED,
    SECTION_11_13_STARTED,
    TESTNET_AUTHORIZED,
    TESTNET_ORDER_SUBMIT_PERFORMED,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_8_ProductiveTestnetCampaignPath",
        "Cap11_Section_11_12_8_ProductiveTestnetCampaignExecution",
        "Cap11_Section_11_12_8_ProductiveTestnetCampaignRun",
        "SimulatedExecutionPort",
    ],
    "productive_testnet_campaign_run_activation": "absent",
    "cap_11_13": "not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_8_ProductiveTestnetCampaignPath",
        "Cap11_Section_11_12_8_ProductiveTestnetCampaignExecution",
        "Cap11_Section_11_12_8_ProductiveTestnetCampaignRun",
        "Cap11_Section_11_12_8_ProductiveTestnetCampaignRunActivation",
        "SimulatedExecutionPort",
    ],
    "path_class": PATH_CLASS,
    "run_predecessor": "preserved",
    "run_predecessor_origin_main_sha": RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
    "productive_testnet_campaign_run_activation": "present",
    "productive_activation_entrypoint": "present_hard_refuse_until_separate_owner_go",
    "productive_testnet_campaign_run_activation_go": "forbidden_until_separate_owner_go",
    "network_effect": NETWORK_EFFECT,
    "order_effect": ORDER_EFFECT,
    "live_order_effect": LIVE_ORDER_EFFECT,
    "campaign_started": False,
    "cap_11_13": "not_started",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1() -> dict[
    str, Any
]:
    proof = prove_productive_testnet_campaign_run_activation_v1()
    ok = bool(proof.get("ok"))
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "RUN_PREDECESSOR_ORIGIN_MAIN_SHA": RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "PATH_CLASS": PATH_CLASS,
        "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED": (
            PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED
        ),
        "RUN_PREDECESSOR_PRESERVED": RUN_PREDECESSOR_PRESERVED,
        "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_PRESENT": (
            PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_PRESENT
        ),
        "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_ABSENT": (
            PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_ABSENT
        ),
        "PRODUCTIVE_ACTIVATION_ENTRYPOINT_PRESENT": PRODUCTIVE_ACTIVATION_ENTRYPOINT_PRESENT,
        "RUN_AUTHORIZED": RUN_AUTHORIZED,
        "ACTIVATION_AUTHORIZED": ACTIVATION_AUTHORIZED,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
        "PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED": PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
        "ORDER_SEND_DISABLED": ORDER_SEND_DISABLED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "NETWORK_WRITES_AUTHORIZED": NETWORK_WRITES_AUTHORIZED,
        "NETWORK_WRITE_PERFORMED": NETWORK_WRITE_PERFORMED,
        "NETWORK_SESSION_STARTED": NETWORK_SESSION_STARTED,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": EXCHANGE_ORDER_SUBMIT_REACHABLE,
        "TESTNET_ORDER_SUBMIT_PERFORMED": TESTNET_ORDER_SUBMIT_PERFORMED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "AUTHORIZATION_CONSUMED": AUTHORIZATION_CONSUMED,
        "FUTURE_ACTIVATION_GO_CONSUMPTION_ALLOWED": FUTURE_ACTIVATION_GO_CONSUMPTION_ALLOWED,
        "FUTURE_ACTIVATION_GO_CONSUMED": FUTURE_ACTIVATION_GO_CONSUMED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "ACTIVATION_PROOF_OK": proof.get("ok"),
        "PROVE_ONLY_MAY_START": proof.get("prove_only_may_start"),
        "GATE_MAY_START": proof.get("gate_may_start"),
        "GATE_STARTED": proof.get("gate_started"),
        "ACTIVATION_AUTH_BLOCKED": proof.get("activation_auth_blocked"),
        "LIVE_BLOCKED": proof.get("live_blocked"),
        "CREDENTIAL_SCOPE_BLOCKED": proof.get("credential_scope_blocked"),
        "ENABLED_FALSE_BLOCKED": proof.get("enabled_false_blocked"),
        "ARMED_FALSE_BLOCKED": proof.get("armed_false_blocked"),
        "OWNER_AUTH_BLOCKED": proof.get("owner_auth_blocked"),
        "KILL_SWITCH_BLOCKED": proof.get("kill_switch_blocked"),
        "EMERGENCY_CONTROL_BLOCKED": proof.get("emergency_control_blocked"),
        "RISK_SCOPE_BLOCKED": proof.get("risk_scope_blocked"),
        "FUTURE_ACTIVATION_GO_BLOCKED": proof.get("future_activation_go_blocked"),
        "RUN_PREDECESSOR_SHA_BLOCKED": proof.get("run_predecessor_sha_blocked"),
        "CONFIRM_INVALID_BLOCKED": proof.get("confirm_invalid_blocked"),
        "ACTIVATION_REFUSED": proof.get("activation_refused"),
        "REFUSE_OK": proof.get("refuse_ok"),
        "ACTIVATION_BINDING_DIGEST": proof.get("activation_binding_digest"),
        "RUN_BINDING_DIGEST": proof.get("run_binding_digest"),
        "EXECUTION_BINDING_DIGEST": proof.get("execution_binding_digest"),
        "PATH_BINDING_DIGEST": proof.get("path_binding_digest"),
    }
    return {
        "ok": ok,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"productive_run_activation": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
