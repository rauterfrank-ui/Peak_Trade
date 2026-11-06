"""PRE_MERGE_ACCEPTANCE_GATE — stubbed Testnet boundary end-to-end proof."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.blocker_matrix_v1 import (
    build_b01_b24_closure_matrix_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.call_chain_proof_v1 import (
    build_static_productive_call_chain_proof_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    MODE_STUBBED_ACCEPTANCE,
    NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SCOPED_OWNER_GO_AUTHORIZATION,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_consumer_v1 import (
    execute_productive_section_11_12_8_campaign_run_v1,
)


def run_pre_merge_acceptance_gate_v1(*, work_dir: Path) -> dict[str, Any]:
    digest = "c" * 64
    result = execute_productive_section_11_12_8_campaign_run_v1(
        work_dir=work_dir,
        mode=MODE_STUBBED_ACCEPTANCE,
        owner_go_token=SCOPED_OWNER_GO_TOKEN,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE,
        owner_go_authorization=SCOPED_OWNER_GO_AUTHORIZATION,
        consumption_id=f"acceptance-{uuid4().hex}",
        confirm_token_digest=digest,
        expected_confirm_token_digest=digest,
    )
    chain = build_static_productive_call_chain_proof_v1(
        authorized_path=True, stubbed_external_effect=True
    )
    matrix = build_b01_b24_closure_matrix_v1()

    residual_forbidden = []
    if not result.ok:
        residual_forbidden.append("RESULT_NOT_OK")
    if result.next_operation_after_boundary != NEXT_OPERATION_AFTER_STUBBED_BOUNDARY:
        residual_forbidden.append("NEXT_OPERATION_MISMATCH")
    if not result.lifecycle.first_permitted_effect_invoked:
        residual_forbidden.append("FIRST_EFFECT_NOT_INVOKED")
    if not result.lifecycle.first_permitted_effect_stubbed:
        residual_forbidden.append("FIRST_EFFECT_NOT_STUBBED")
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is not False:
        residual_forbidden.append("CAMPAIGN_STARTED_CONSTANT_TRUE")
    if SECTION_11_13_STARTED:
        residual_forbidden.append("SECTION_11_13_STARTED")
    if not chain.get("ok"):
        residual_forbidden.append("CALL_CHAIN_FAIL")
    if not matrix.get("ok"):
        residual_forbidden.append("BLOCKER_MATRIX_OPEN")

    ok = len(residual_forbidden) == 0
    return {
        "ok": ok,
        "PRE_MERGE_ACCEPTANCE_GATE": "PASS" if ok else "FAIL",
        "ALL_B01_B24_CLOSED": matrix.get("ALL_B01_B24_CLOSED"),
        "RESIDUAL_BLOCKER_COUNT": matrix.get("RESIDUAL_BLOCKER_COUNT"),
        "STATIC_PRODUCTIVE_CALL_CHAIN": "PASS" if chain.get("ok") else "FAIL",
        "NEXT_OPERATION_AFTER_STUBBED_BOUNDARY": result.next_operation_after_boundary,
        "REMAINING_ARCHITECTURAL_BLOCKERS": 0 if ok else len(residual_forbidden),
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "LIVE_ORDER_EFFECT": "NONE",
        "SECTION_11_13_STARTED": False,
        "residual_forbidden": residual_forbidden,
        "result": result.to_dict(),
        "call_chain": chain,
        "blocker_matrix": matrix,
    }
