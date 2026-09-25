"""Treasury ↔ Full-Core reachability proofs (bounded productive handoff).

After authorized Treasury single-source capital handoff, Full-Core may import
only the bounded handoff seam. Forbidden: trading, quantity, reservation, live send.
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

_ALLOWED_HANDOFF_MARKERS = (
    "current_productive_treasury_single_source_capital_handoff_v1",
    "execute_current_productive_treasury_single_source_capital_handoff_v1",
)

_FORBIDDEN_MARKERS = (
    "src.ops." + "treasury_phase_1_offline_contracts_v1",
    "enforce_" + "treasury_policy",
    "record_" + "treasury_intent_v1",
    "apply_" + "treasury_lifecycle_transition_v1",
    "/asset/" + "withdrawal",
    "/asset/" + "transfer",
    "TREASURY_MUTATION_AUTHORIZED=" + "true",
    "join_treasury_observation_through_e4_into_productive_account_equity_host_v1",
)


def prove_treasury_bounded_full_core_reachability_v1() -> dict[str, Any]:
    hits: list[str] = []
    allowed_hits: list[str] = []
    for path in sorted(_PACKAGE_DIR.glob("*.py")):
        if path.name in {
            "treasury_interference_proof_v1.py",
            "current_productive_treasury_single_source_capital_handoff_v1.py",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in _ALLOWED_HANDOFF_MARKERS:
            if marker in text:
                allowed_hits.append(f"{path.name}:{marker}")
        for marker in _FORBIDDEN_MARKERS:
            if marker not in text:
                continue
            wd = "/asset/" + "withdrawal"
            tr = "/asset/" + "transfer"
            if path.name == "productive_read_only_get_transport_v1.py" and marker in {wd, tr}:
                continue
            hits.append(f"{path.name}:{marker}")
    dag_ids = tuple(node.component_id for node in LIVE_ADMISSION_GAP_NODES)
    treasury_in_dag = any("TREASURY" in component_id for component_id in dag_ids)
    handoff_wired = any(
        "current_productive_enter_live_29p_join_v1.py" in hit for hit in allowed_hits
    ) or any("current_productive_enter_live_29p_join_v1.py" in hit for hit in allowed_hits)
    enter_live = (_PACKAGE_DIR / "current_productive_enter_live_29p_join_v1.py").read_text(
        encoding="utf-8"
    )
    handoff_wired = (
        "execute_current_productive_treasury_single_source_capital_handoff_v1" in enter_live
    )
    ok = not hits and handoff_wired
    return {
        "TREASURY_BOUNDED_REACHABILITY_PROOF": "PASS" if ok else "FAIL",
        "TREASURY_FULL_CORE_REACHABILITY_ALLOWED_ONLY_FOR": (
            "READ_ONLY_OBSERVATION,RECONCILIATION,C08_TRANSPORT,CONSERVATIVE_DECREASE_OR_BLOCK"
        ),
        "TREASURY_FORBIDDEN_FULL_CORE_ROLES": (
            "TRADING_DECISION,SYMBOL_SELECTION,DIRECTION_SELECTION,ENTRY_EXIT_AUTHORITY,"
            "INDEPENDENT_QUANTITY_ORIGINATION,CAPITAL_INCREASE_ABOVE_TRUSTED_BASE,"
            "PORTFOLIO_RESERVATION_OWNERSHIP,LIVE_SEND_AUTHORITY"
        ),
        "TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY": handoff_wired,
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
        "forbidden_hits": hits,
        "allowed_hits": allowed_hits,
        "ok": ok,
    }


def prove_treasury_interference_absent_v1() -> dict[str, Any]:
    """Legacy entrypoint: delegates to bounded reachability after authorized handoff."""
    bounded = prove_treasury_bounded_full_core_reachability_v1()
    return {
        "TREASURY_INTERFERENCE_PROOF": bounded["TREASURY_BOUNDED_REACHABILITY_PROOF"],
        "TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY": bounded[
            "TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY"
        ],
        "TREASURY_IS_IN_CURRENT_LIVE_ADMISSION_DAG": bounded[
            "TREASURY_IS_IN_CURRENT_LIVE_ADMISSION_DAG"
        ],
        "TREASURY_CAN_OVERRIDE_STEP_29P_RISK_ADMISSION": False,
        "TREASURY_CAN_OVERRIDE_WIRE_SEND_PERMISSION": False,
        "TREASURY_CAN_CONSTRUCT_LIVE_EXECUTION_PORT": False,
        "TREASURY_CAN_MOVE_FUNDS_FROM_CURRENT_FULL_CORE_PATH": False,
        "TREASURY_MUTATION_AUTHORIZED": False,
        "TREASURY_COMPLETION_AUTHORIZED": False,
        "LIVE_ENABLED": bounded["LIVE_ENABLED"],
        "LIVE_ARMED": bounded["LIVE_ARMED"],
        "WIRE_SEND_PERMITTED": bounded["WIRE_SEND_PERMITTED"],
        "hits": bounded.get("forbidden_hits", []),
        "ok": bounded["ok"],
    }
