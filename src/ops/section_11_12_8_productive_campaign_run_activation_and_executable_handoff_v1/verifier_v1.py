"""Verifier for §11.12.8 activation + executable handoff."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.activation_executor_v1 import (
    prove_section_11_12_8_activation_and_executable_handoff_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    ACTIVATION_EXECUTOR_CANONICAL_ROLE,
    ACTIVATION_STATE,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    COMPLETE_BLOCKER_IDS,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_PLAINTEXT_LOADED,
    DEPRECATED_NON_EXTENDABLE,
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
    PRESERVED_EXECUTABLE_CONTROLS,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    REFERENCE_ONLY,
    SECTION_11_13_STARTED,
    TESTNET_AUTHORIZED,
)

CALL_GRAPH_BEFORE: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Section_11_12_8_TerminalProductiveConsumer",
        "Section_11_12_8_ProductiveCampaignRunConsumer",
        "Deprecated_PATH_EXECUTION_RUN_RUN_ACTIVATION_Wrappers",
    ],
    "activation_and_executable_handoff": "absent",
    "cap_11_13": "not_started",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "nodes": [
        "CanonicalStatefulTradingCore",
        "Section_11_12_8_TerminalProductiveConsumer",
        "Section_11_12_8_ProductiveCampaignRunConsumer",
        "Section_11_12_8_ActivationAndExecutableHandoff",
        "Phase92_HiddenConfirm_Reused",
        "RiskGate_Reused",
        "KillSwitch_Reused",
        "Phase92_NetworkSessionBoundary_Dry",
    ],
    "path_class": PATH_CLASS,
    "activation_executor": "present_non_deprecated_dry_executable",
    "productive_campaign_started": False,
    "network_effect": NETWORK_EFFECT,
    "order_effect": ORDER_EFFECT,
    "live_order_effect": LIVE_ORDER_EFFECT,
    "cap_11_13": "not_started",
    "next_consumer": NEXT_CONSUMER_CAPABILITY_ID,
}


def verify_section_11_12_8_activation_and_executable_handoff_v1(
    *,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    if work_dir is None:
        tmp = tempfile.TemporaryDirectory(prefix="pt_11_12_8_activation_verify_")
        try:
            proof = prove_section_11_12_8_activation_and_executable_handoff_v1(
                work_dir=Path(tmp.name)
            )
        finally:
            tmp.cleanup()
    else:
        proof = prove_section_11_12_8_activation_and_executable_handoff_v1(work_dir=work_dir)

    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "ACTIVATION_EXECUTOR_CANONICAL_ROLE": ACTIVATION_EXECUTOR_CANONICAL_ROLE,
        "PATH_CLASS": PATH_CLASS,
        "IMPLEMENTATION_ONLY": IMPLEMENTATION_ONLY,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "DEPRECATED_NON_EXTENDABLE": DEPRECATED_NON_EXTENDABLE,
        "NEW_WRAPPER_LAYER_CREATED": NEW_WRAPPER_LAYER_CREATED,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "COMPLETE_BLOCKER_SET_CLOSED": list(COMPLETE_BLOCKER_IDS),
        "PRESERVED_EXECUTABLE_CONTROLS": list(PRESERVED_EXECUTABLE_CONTROLS),
        "END_TO_END_DRY_ACTIVATION_PROOF": bool(proof.get("ok")),
        "CREDENTIAL_PLAINTEXT_LOADED": CREDENTIAL_PLAINTEXT_LOADED,
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
    }
    ok = all(
        [
            proof.get("ok") is True,
            DEPRECATED_NON_EXTENDABLE is False,
            NEW_WRAPPER_LAYER_CREATED is False,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
            NETWORK_EFFECT == "NONE",
            ORDER_EFFECT == "NONE",
            LIVE_ORDER_EFFECT == "NONE",
            SECTION_11_13_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            CORE_LOGIC_CHANGE is False,
            proof.get("PRODUCTIVE_TESTNET_CAMPAIGN_STARTED") is False,
            set(proof.get("COMPLETE_BLOCKER_SET_CLOSED") or []) == set(COMPLETE_BLOCKER_IDS),
        ]
    )
    return {
        "ok": ok,
        "capability_id": CAPABILITY_ID,
        "claims": claims,
        "proofs": {"dry_activation": proof},
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
