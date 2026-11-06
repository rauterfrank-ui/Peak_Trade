"""V32 D29 F1/M9 explicit Owner Apply policy edge closure v1 (composition proof)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.governed_productive_configuration_v1 import runtime_apply_possible_v1
from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1 import (
    CLOSED_D29_BLOCKER,
    DECISION_CONFIG,
    NEXT_TRUE_BLOCKER,
    NORMATIVE_SPEC,
    PRODUCTIVE_APPLY_OCCURRED,
    WORKPACKAGE_ID,
    prove_negative_stage_separation_v1,
)
from src.governance.v32_d29_f1_m9_per_ingress_productive_authorization_apply_closure_v1 import (
    prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1,
)

SCHEMA_VERSION: Final[str] = "v32_d29_f1_m9_explicit_owner_productive_apply_policy_closure_v1"


def prove_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / NORMATIVE_SPEC,
        root
        / "src/governance/v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1.py",
        root / "tests/governance/"
        "test_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1.py",
    )
    if not all(path.is_file() for path in required):
        return False
    if not prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1(
        repo_root=root
    ):
        return False
    if not prove_negative_stage_separation_v1():
        return False
    if PRODUCTIVE_APPLY_OCCURRED:
        return False
    if runtime_apply_possible_v1() is not False:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("closed_d29_blocker") != CLOSED_D29_BLOCKER:
        return False
    if decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER:
        return False
    if decision.get("productive_apply_occurred"):
        return False
    if decision.get("apply_policy_edge_implemented") is not True:
        return False
    if int(decision.get("productive_numeric_values_set_current", -1)) != 0:
        return False
    if decision.get("global_optimization_join_authorized"):
        return False
    if decision.get("promotion_authorized"):
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1",
]
