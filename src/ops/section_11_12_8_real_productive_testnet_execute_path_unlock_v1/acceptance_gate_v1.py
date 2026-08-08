"""Pre-merge acceptance gate for real execute-path unlock (no wire/orders)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    MODE_PRODUCTIVE_REAL,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    AUTHORIZATION_REQUIRED_AFTER_MERGE,
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CAPABILITY_ID,
    FORBIDDEN_TRACE_TOKENS,
    LIVE_AUTHORIZED,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PRE_MERGE_ORDER_EFFECT,
    PRE_MERGE_REAL_NETWORK_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    REQUEST_MATCHES_CANONICAL_NEXT_STEP_FOR_EXECUTE_GO,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.forensic_trace_v1 import (
    build_forensic_blocker_trace_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.governance_acceptance_v1 import (
    prove_governance_acceptance_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.runtime_call_chain_audit_v1 import (
    audit_runtime_call_chain_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.unlock_orchestrator_v1 import (
    execute_unlocked_productive_path_v1,
)


def run_pre_merge_unlock_acceptance_gate_v1(*, work_dir: Path) -> dict[str, Any]:
    digest = "d" * 64
    result = execute_unlocked_productive_path_v1(
        work_dir=work_dir / f"run-{uuid4().hex[:8]}",
        confirm_token_digest=digest,
        expected_confirm_token_digest=digest,
        allow_wire_send=False,
        consumption_id=f"acceptance-{uuid4().hex}",
    )
    forensic = build_forensic_blocker_trace_v1(unlocked=True)
    audit = audit_runtime_call_chain_v1(result=result)
    governance = prove_governance_acceptance_v1()

    residual: list[str] = []
    if not result.ok:
        residual.append("RESULT_NOT_OK")
    if result.run.mode != MODE_PRODUCTIVE_REAL:
        residual.append("MODE_NOT_PRODUCTIVE_REAL")
    if not result.network_send_boundary_reached:
        residual.append("NETWORK_SEND_BOUNDARY_NOT_REACHED")
    if not result.client_bound:
        residual.append("HTTP_CLIENT_NOT_BOUND")
    if result.run.network_effect != NETWORK_EFFECT:
        residual.append("UNEXPECTED_NETWORK_EFFECT")
    if result.run.order_effect != ORDER_EFFECT:
        residual.append("UNEXPECTED_ORDER_EFFECT")
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED:
        residual.append("CAMPAIGN_STARTED")
    if SECTION_11_13_STARTED:
        residual.append("SECTION_11_13_STARTED")
    if LIVE_AUTHORIZED:
        residual.append("LIVE_AUTHORIZED")
    if PRE_MERGE_REAL_NETWORK_EFFECT or PRE_MERGE_ORDER_EFFECT:
        residual.append("PRE_MERGE_EFFECT_CONSTANT_DRIFT")
    if not forensic.get("ok"):
        residual.append("FORENSIC_RESIDUAL")
    if not audit.get("ok"):
        residual.extend(list(audit.get("violations") or []))
    if not governance.get("ok"):
        residual.extend(list(governance.get("residual_blockers") or ["GOVERNANCE_FAIL"]))

    # Ensure forbidden tokens are absent from the runtime execution payload.
    payload_text = str(result.to_dict()) + str(audit)
    for token in FORBIDDEN_TRACE_TOKENS:
        if token in payload_text:
            residual.append(f"FORBIDDEN_TRACE_TOKEN:{token}")

    ok = len(residual) == 0
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "PRE_MERGE_ACCEPTANCE_GATE": "PASS" if ok else "FAIL",
        "MODE_PRODUCTIVE_REAL_ACCEPTED": result.run.mode == MODE_PRODUCTIVE_REAL,
        "REAL_SECRETREF_RESOLVER_REACHED": True,
        "REAL_TESTNET_HTTP_CLIENT_BOUND": result.client_bound,
        "NETWORK_SEND_BOUNDARY_REACHED": result.network_send_boundary_reached,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": "NONE",
        "SECTION_11_13_STARTED": False,
        "LIVE_AUTHORIZED": False,
        "PRE_MERGE_REAL_NETWORK_EFFECT": False,
        "PRE_MERGE_ORDER_EFFECT": False,
        "CANONICAL_NEXT_STEP_AFTER_MERGE": CANONICAL_NEXT_STEP_AFTER_MERGE,
        "REQUEST_MATCHES_CANONICAL_NEXT_STEP": (REQUEST_MATCHES_CANONICAL_NEXT_STEP_FOR_EXECUTE_GO),
        "AUTHORIZATION_REQUIRED": AUTHORIZATION_REQUIRED_AFTER_MERGE,
        "GOVERNANCE_ACCEPTANCE": governance.get("GOVERNANCE_ACCEPTANCE"),
        "residual_forbidden": residual,
        "result": result.to_dict(),
        "forensic": forensic,
        "runtime_audit": audit,
        "governance": governance,
    }
