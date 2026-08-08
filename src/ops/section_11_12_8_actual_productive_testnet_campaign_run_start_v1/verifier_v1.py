"""Verifier for ACTUAL productive §11.12.8 campaign run start package."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.acceptance_gate_v1 import (
    run_pre_merge_acceptance_gate_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.blocker_matrix_v1 import (
    build_b01_b24_closure_matrix_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.call_chain_proof_v1 import (
    build_static_productive_call_chain_proof_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    IMPLEMENTATION_ONLY,
    LIVE_AUTHORIZED,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NEW_WRAPPER_LAYER_CREATED,
    ORDER_EFFECT,
    OWNER,
    PREDECESSOR_CAPABILITY_ID,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SCOPED_OWNER_GO_AUTHORIZATION,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
    SECTION_11_13_STARTED,
)


def verify_section_11_12_8_actual_productive_testnet_campaign_run_start_v1(
    *,
    work_dir: Path,
) -> dict[str, Any]:
    gate = run_pre_merge_acceptance_gate_v1(work_dir=work_dir / "gate")
    chain = build_static_productive_call_chain_proof_v1()
    matrix = build_b01_b24_closure_matrix_v1()
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "IMPLEMENTATION_ONLY": IMPLEMENTATION_ONLY,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "NEW_WRAPPER_LAYER_CREATED": NEW_WRAPPER_LAYER_CREATED,
        "SCOPED_OWNER_GO_TOKEN": SCOPED_OWNER_GO_TOKEN,
        "SCOPED_OWNER_GO_SCOPE": SCOPED_OWNER_GO_SCOPE,
        "SCOPED_OWNER_GO_AUTHORIZATION": SCOPED_OWNER_GO_AUTHORIZATION,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "ALL_B01_B24_CLOSED": matrix.get("ALL_B01_B24_CLOSED"),
        "PRE_MERGE_ACCEPTANCE_GATE": gate.get("PRE_MERGE_ACCEPTANCE_GATE"),
        "STATIC_PRODUCTIVE_CALL_CHAIN": chain.get("ok"),
    }
    ok = all(
        [
            gate.get("ok") is True,
            chain.get("ok") is True,
            matrix.get("ok") is True,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
            SECTION_11_13_STARTED is False,
            LIVE_AUTHORIZED is False,
            NETWORK_EFFECT == "NONE",
            ORDER_EFFECT == "NONE",
            LIVE_ORDER_EFFECT == "NONE",
        ]
    )
    return {
        "ok": ok,
        "claims": claims,
        "gate": gate,
        "call_chain": chain,
        "blocker_matrix": matrix,
        "call_graph_before": {
            "productive_start": "missing",
            "next": "SEPARATE_OWNER_GO_REQUIRED_FOR_ACTUAL_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_START",
        },
        "call_graph_after": {
            "productive_start": "present_stubbed_acceptance_wired",
            "capability": CAPABILITY_ID,
            "next": "SEPARATE_OWNER_GO_REQUIRED_FOR_EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW",
            "consumption_probe": f"verify-{uuid4().hex[:8]}",
        },
    }
