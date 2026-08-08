"""Verifier for real productive Testnet execute-path unlock."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.acceptance_gate_v1 import (
    run_pre_merge_unlock_acceptance_gate_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    AUTHORIZATION_REQUIRED_AFTER_MERGE,
    AUTHORIZED_RUNTIME_PATH_IMPLEMENTATION_ONLY,
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    LIVE_HARD_BLOCK_PRESERVED,
    LIVE_ORDER_EFFECT,
    NETWORK_EFFECT,
    NEXT_CONSUMER_CAPABILITY_ID,
    NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE,
    ORDER_EFFECT,
    OWNER,
    PATH_IMPLEMENTATION_ONLY_REFUSAL_REMOVED,
    PREDECESSOR_CAPABILITY_ID_BOUND,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    REQUEST_MATCHES_CANONICAL_NEXT_STEP_FOR_EXECUTE_GO,
    SCOPED_OWNER_GO_AUTHORIZATION_BOUND,
    SCOPED_OWNER_GO_SCOPE_BOUND,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.forensic_trace_v1 import (
    build_forensic_blocker_trace_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.governance_acceptance_v1 import (
    prove_governance_acceptance_v1,
)


def verify_section_11_12_8_real_productive_testnet_execute_path_unlock_v1(
    *,
    work_dir: Path,
) -> dict[str, Any]:
    gate = run_pre_merge_unlock_acceptance_gate_v1(work_dir=work_dir / f"g-{uuid4().hex[:8]}")
    forensic = build_forensic_blocker_trace_v1(unlocked=True)
    governance = prove_governance_acceptance_v1()
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID_BOUND,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "CANONICAL_NEXT_STEP_AFTER_MERGE": CANONICAL_NEXT_STEP_AFTER_MERGE,
        "REQUEST_MATCHES_CANONICAL_NEXT_STEP": (REQUEST_MATCHES_CANONICAL_NEXT_STEP_FOR_EXECUTE_GO),
        "AUTHORIZATION_REQUIRED": AUTHORIZATION_REQUIRED_AFTER_MERGE,
        "NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE": (
            NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE
        ),
        "AUTHORIZED_RUNTIME_PATH_IMPLEMENTATION_ONLY": (
            AUTHORIZED_RUNTIME_PATH_IMPLEMENTATION_ONLY
        ),
        "SCOPED_OWNER_GO_SCOPE": SCOPED_OWNER_GO_SCOPE_BOUND,
        "SCOPED_OWNER_GO_AUTHORIZATION": SCOPED_OWNER_GO_AUTHORIZATION_BOUND,
        "PATH_IMPLEMENTATION_ONLY_REFUSAL_REMOVED": PATH_IMPLEMENTATION_ONLY_REFUSAL_REMOVED,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "LIVE_HARD_BLOCK_PRESERVED": LIVE_HARD_BLOCK_PRESERVED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "PRE_MERGE_ACCEPTANCE_GATE": gate.get("PRE_MERGE_ACCEPTANCE_GATE"),
        "GOVERNANCE_ACCEPTANCE": governance.get("GOVERNANCE_ACCEPTANCE"),
    }
    ok = all(
        [
            bool(gate.get("ok")),
            bool(forensic.get("ok")),
            bool(governance.get("ok")),
            PATH_IMPLEMENTATION_ONLY_REFUSAL_REMOVED,
            AUTHORIZED_RUNTIME_PATH_IMPLEMENTATION_ONLY is False,
            NO_ADDITIONAL_IMPLEMENTATION_GO_REQUIRED_BEFORE_EXECUTE,
            LIVE_HARD_BLOCK_PRESERVED,
            SECTION_11_13_STARTED is False,
        ]
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "claims": claims,
        "gate": gate,
        "forensic": forensic,
        "governance": governance,
    }
