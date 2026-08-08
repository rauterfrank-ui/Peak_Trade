"""Exact runtime call-chain audit for unlocked productive path."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    CAPABILITY_ID,
    FORBIDDEN_TRACE_TOKENS,
    REQUIRED_RUNTIME_CHAIN,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.unlock_orchestrator_v1 import (
    UnlockExecutePathResultV1,
)


def audit_runtime_call_chain_v1(*, result: UnlockExecutePathResultV1) -> dict[str, Any]:
    violations: list[str] = []
    trace = result.runtime_trace
    stages = list(trace.get("stages") or [])
    if stages != list(REQUIRED_RUNTIME_CHAIN):
        violations.append("RUNTIME_CHAIN_MISMATCH")
    if result.run.mode != "PRODUCTIVE_REAL_NETWORK":
        violations.append("MODE_NOT_REAL")
    if not result.client_bound:
        violations.append("HTTP_CLIENT_NOT_BOUND")
    if not result.network_send_boundary_reached:
        violations.append("NETWORK_SEND_BOUNDARY_NOT_REACHED")
    if result.run.lifecycle.first_permitted_effect_stubbed:
        violations.append("STUBBED_FIRST_EFFECT")
    if not result.run.lifecycle.first_permitted_effect_invoked:
        violations.append("FIRST_EFFECT_NOT_INVOKED")
    if not result.run.evidence_seal_ok:
        violations.append("EVIDENCE_SEAL_FAIL")

    blob = str(result.to_dict())
    for token in FORBIDDEN_TRACE_TOKENS:
        if token in blob:
            violations.append(f"FORBIDDEN_TRACE_TOKEN:{token}")

    return {
        "ok": len(violations) == 0,
        "CAPABILITY_ID": CAPABILITY_ID,
        "stages": stages,
        "violations": violations,
        "read_only": True,
    }
