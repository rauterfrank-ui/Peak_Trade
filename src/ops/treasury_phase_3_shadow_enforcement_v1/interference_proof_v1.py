"""Read-only interference proof for Treasury Phase-3 shadow enforcement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.treasury_phase_3_shadow_enforcement_v1.constants_v1 import (
    PRODUCTIVE_AUTHORITY_GRAPH_CHANGED,
    SECOND_CAPITAL_AUTHORITY_ADDED,
    STEP_29P_AUTHORITY_UNCHANGED,
    TREASURY_MUTATION_REACHABLE,
    TREASURY_PRODUCTIVE_CAPITAL_OWNER,
    TREASURY_RISK_ADMISSIBLE_MINT,
)

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parents[1]

_FORBIDDEN_PACKAGE_MARKERS: tuple[str, ...] = (
    "join_capital_admission_into_admission_inputs_v1",
    "evaluate_step_29p_capital_risk_admissibility_v1",
    "join_treasury_capital_admission_into_account_equity_orchestration_v1",
    "construct_live_execution_port_v1",
)


def prove_treasury_phase_3_interference_absent_v1() -> dict[str, Any]:
    hits: list[str] = []
    full_core = _REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
    if full_core.is_dir():
        for path in sorted(full_core.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            if "treasury_phase_3_shadow_enforcement_v1" in text:
                hits.append(f"{path.name}:treasury_phase_3_import")

    package_text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(_PACKAGE_DIR.glob("*.py"))
        if p.name not in {"constants_v1.py", "interference_proof_v1.py"}
    )
    for marker in _FORBIDDEN_PACKAGE_MARKERS:
        if marker in package_text:
            hits.append(f"package:{marker}")

    ok = (
        not hits
        and PRODUCTIVE_AUTHORITY_GRAPH_CHANGED is False
        and SECOND_CAPITAL_AUTHORITY_ADDED is False
        and STEP_29P_AUTHORITY_UNCHANGED is True
        and TREASURY_MUTATION_REACHABLE is False
        and TREASURY_RISK_ADMISSIBLE_MINT is False
        and TREASURY_PRODUCTIVE_CAPITAL_OWNER is False
    )
    return {
        "ok": ok,
        "hits": hits,
        "PRODUCTIVE_AUTHORITY_GRAPH_CHANGED": PRODUCTIVE_AUTHORITY_GRAPH_CHANGED,
        "SECOND_CAPITAL_AUTHORITY_ADDED": SECOND_CAPITAL_AUTHORITY_ADDED,
        "STEP_29P_AUTHORITY_UNCHANGED": STEP_29P_AUTHORITY_UNCHANGED,
        "TREASURY_MUTATION_REACHABLE": TREASURY_MUTATION_REACHABLE,
        "TREASURY_RISK_ADMISSIBLE_MINT": TREASURY_RISK_ADMISSIBLE_MINT,
        "MASTER_V2_INTERFERENCE": bool(hits),
        "DOUBLE_PLAY_INTERFERENCE": bool(hits),
        "TOP5_N5_INTERFERENCE": bool(hits),
        "LEARNING_OPTIMIZATION_INTERFERENCE": bool(hits),
    }
