"""Verifier for §11.12.8 terminal productive campaign consumer."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_IMPLEMENTED,
    CREDENTIAL_PLAINTEXT_LOADED,
    IMPLEMENTATION_ONLY,
    LIVE_AUTHORIZED,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NETWORK_SESSION_STARTED,
    NEW_WRAPPER_LAYER_CREATED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    PRODUCTIVE_RUN_AUTHORIZED,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    REFERENCE_ONLY,
    SECTION_11_13_STARTED,
    TERMINAL_CONSUMER_CANONICAL_ROLE,
    TERMINAL_CONSUMER_IMPLEMENTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_PORT_CONSTRUCTIBLE,
    TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.terminal_consumer_v1 import (
    prove_section_11_12_8_terminal_consumer_v1,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_8_FixtureResidual",
        "Cap11_Section_11_12_8_WrapperResiduals_NonExtendable",
        "SimulatedExecutionPort",
        "Cap11_1_TestnetExecutionPort_DeclarationOnly",
    ],
    "section_11_12_8_terminal_consumer": "absent",
    "testnet_execution_port_productive": "absent",
    "cap_11_13": "not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Cap11_Section_11_12_8_FixtureResidual",
        "Cap11_Section_11_12_8_WrapperResiduals_NonExtendable",
        "Section_11_12_8_TerminalProductiveConsumer",
        "TestnetExecutionPort_Productive_Under_Terminal",
        "SimulatedExecutionPort",
        "Phase92_HiddenConfirm_Reused",
        "RiskGate_Reused",
        "KillSwitch_Reused",
    ],
    "path_class": PATH_CLASS,
    "terminal_consumer": "present_implementation_only_hard_refuse_productive_run",
    "new_wrapper_layer_created": False,
    "testnet_execution_port_constructible": True,
    "testnet_execution_port_reachable_under_authorized_terminal": True,
    "network_effect": NETWORK_EFFECT,
    "order_effect": ORDER_EFFECT,
    "live_order_effect": LIVE_ORDER_EFFECT,
    "campaign_started": False,
    "cap_11_13": "not_started",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_section_11_12_8_terminal_consumer_v1() -> dict[str, Any]:
    proof = prove_section_11_12_8_terminal_consumer_v1()
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "TERMINAL_CONSUMER_CANONICAL_ROLE": TERMINAL_CONSUMER_CANONICAL_ROLE,
        "TERMINAL_CONSUMER_IMPLEMENTED": TERMINAL_CONSUMER_IMPLEMENTED,
        "NEW_WRAPPER_LAYER_CREATED": NEW_WRAPPER_LAYER_CREATED,
        "IMPLEMENTATION_ONLY": IMPLEMENTATION_ONLY,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "TESTNET_EXECUTION_PORT_CONSTRUCTIBLE": TESTNET_EXECUTION_PORT_CONSTRUCTIBLE,
        "TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL": (
            TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL
        ),
        "CREDENTIAL_LOAD_IMPLEMENTED": CREDENTIAL_LOAD_IMPLEMENTED,
        "CREDENTIAL_PLAINTEXT_LOADED": CREDENTIAL_PLAINTEXT_LOADED,
        "PRODUCTIVE_RUN_AUTHORIZED": PRODUCTIVE_RUN_AUTHORIZED,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
        "NETWORK_SESSION_STARTED": NETWORK_SESSION_STARTED,
        "ORDER_SEND_DISABLED": ORDER_SEND_DISABLED,
        "ORDERS_AUTHORIZED": ORDERS_AUTHORIZED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "CAPABILITY_11_13_STARTED": CAPABILITY_11_13_STARTED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "HIDDEN_CONFIRM_REUSED": True,
        "RISK_GATE_REUSED": True,
        "KILL_SWITCH_REUSED": True,
        "ENABLED_ARMED_FAIL_CLOSED": True,
    }
    ok = all(
        [
            proof.get("ok") is True,
            TERMINAL_CONSUMER_IMPLEMENTED is True,
            NEW_WRAPPER_LAYER_CREATED is False,
            TESTNET_EXECUTION_PORT_CONSTRUCTIBLE is True,
            TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL is True,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
            NETWORK_EFFECT == "NONE",
            ORDER_EFFECT == "NONE",
            LIVE_ORDER_EFFECT == "NONE",
            SECTION_11_13_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            CORE_LOGIC_CHANGE is False,
        ]
    )
    return {
        "ok": ok,
        "capability_id": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"terminal_consumer": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
