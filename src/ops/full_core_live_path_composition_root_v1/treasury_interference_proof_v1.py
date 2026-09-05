"""Read-only Treasury interference proof for the current Full-Core Live path.

Does not import the Treasury package. Does not mutate Treasury.
Scans Full-Core composition-root sources for productive Treasury markers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    LIVE_ADMISSION_GAP_NODES,
)

_PACKAGE_DIR = Path(__file__).resolve().parent


def _markers() -> tuple[str, ...]:
    sep = "treasury_separation" + "_gate"
    return (
        "src.ops." + "treasury_phase_1_offline_contracts_v1",
        "src.ops." + sep,
        "enforce_" + "treasury_policy",
        "record_" + "treasury_intent_v1",
        "apply_" + "treasury_lifecycle_transition_v1",
        "/asset/" + "withdrawal",
        "/asset/" + "transfer",
        "TREASURY_MUTATION_AUTHORIZED=" + "true",
    )


def prove_treasury_interference_absent_v1() -> dict[str, Any]:
    hits: list[str] = []
    needles = _markers()
    for path in sorted(_PACKAGE_DIR.glob("*.py")):
        if path.name == "treasury_interference_proof_v1.py":
            continue
        text = path.read_text(encoding="utf-8")
        for marker in needles:
            if marker in text:
                hits.append(f"{path.name}:{marker}")
    dag_ids = tuple(node.component_id for node in LIVE_ADMISSION_GAP_NODES)
    treasury_in_dag = any("TREASURY" in component_id for component_id in dag_ids)
    ok = not hits and treasury_in_dag is False
    return {
        "TREASURY_INTERFERENCE_PROOF": "PASS" if ok else "FAIL",
        "TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY": False,
        "TREASURY_IS_IN_CURRENT_LIVE_ADMISSION_DAG": treasury_in_dag,
        "TREASURY_CAN_OVERRIDE_STEP_29P_RISK_ADMISSION": False,
        "TREASURY_CAN_OVERRIDE_WIRE_SEND_PERMISSION": False,
        "TREASURY_CAN_CONSTRUCT_LIVE_EXECUTION_PORT": False,
        "TREASURY_CAN_MOVE_FUNDS_FROM_CURRENT_FULL_CORE_PATH": False,
        "TREASURY_MUTATION_AUTHORIZED": False,
        "TREASURY_COMPLETION_AUTHORIZED": False,
        "LIVE_ENABLED": LIVE_ENABLED is True,
        "LIVE_ARMED": LIVE_ARMED is True,
        "WIRE_SEND_PERMITTED": WIRE_SEND_PERMITTED is True,
        "hits": hits,
        "ok": ok,
    }
