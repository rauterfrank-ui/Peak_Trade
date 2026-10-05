"""Authority / safety cross-reference (reuse connection closure + constants)."""

from __future__ import annotations

from typing import Any

from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
)
from src.ops.whole_system_connection_closure_bounded_wp_v1.proof_v1 import (
    prove_whole_system_connection_closure_v1,
)


def build_authority_safety_xref_v1() -> dict[str, Any]:
    conn = prove_whole_system_connection_closure_v1()
    rows = [
        {
            "AUTHORITY": "EXTERNAL_EFFECT_AUTHORIZED",
            "CURRENT_VALUE": EXTERNAL_EFFECT_AUTHORIZED,
            "REQUIRED_VALUE": False,
            "SCOPE": "global_productive",
            "FAILURE_MODE": "fail_closed_block_external_effect",
        },
        {
            "AUTHORITY": "MULTI_FUTURE_RUNTIME_AUTHORIZED",
            "CURRENT_VALUE": MULTI_FUTURE_RUNTIME_AUTHORIZED,
            "REQUIRED_VALUE": False,
            "SCOPE": "runtime",
        },
        {
            "AUTHORITY": "P5_AUTHORITY_CUTOVER_AUTHORIZED",
            "CURRENT_VALUE": P5_AUTHORITY_CUTOVER_AUTHORIZED,
            "REQUIRED_VALUE": False,
        },
        {
            "AUTHORITY": "PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED",
            "CURRENT_VALUE": PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
            "REQUIRED_VALUE": False,
        },
        {
            "AUTHORITY": "PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED",
            "CURRENT_VALUE": PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
            "REQUIRED_VALUE": True,
        },
        {
            "AUTHORITY": "MAX_POSITIONS_EFFECTIVE",
            "CURRENT_VALUE": MAX_POSITIONS_EFFECTIVE,
            "REQUIRED_VALUE": 1,
        },
    ]
    violations = [r for r in rows if r.get("CURRENT_VALUE") != r.get("REQUIRED_VALUE")]
    return {
        "AUTHORITY_ROWS": rows,
        "CONNECTION_CLOSURE_PROOF": {
            "ok": conn.ok,
            "guard_failures": list(conn.guard_failures),
            "unknown_callers": list(conn.unknown_callers),
            "miswired_productive_callers": list(conn.miswired_productive_callers),
        },
        "VIOLATIONS": violations,
        "SAFETY_OK": conn.ok and not violations,
    }
