"""F1/M9 productive apply execution boundary closure v1 (composition proof)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    CLOSED_EXECUTION_BLOCKER,
    DECISION_CONFIG,
    NEXT_TRUE_BLOCKER,
    NORMATIVE_SPEC,
    PREDECESSOR_DECISION,
    PRODUCTIVE_APPLY_OCCURRED,
    WORKPACKAGE_ID,
    real_productive_apply_authorized_v1,
)
from src.governance.governed_productive_configuration_v1 import runtime_apply_possible_v1
from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_closure_v1 import (
    prove_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "f1_m9_productive_apply_execution_closure_v1"


def prove_f1_m9_productive_apply_execution_boundary_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / DECISION_CONFIG,
        root / PREDECESSOR_DECISION,
        root / NORMATIVE_SPEC,
        root / "src/governance/f1_m9_productive_apply_execution_boundary_v1.py",
        root / "tests/governance/test_f1_m9_productive_apply_execution_boundary_v1.py",
    )
    if not all(path.is_file() for path in required):
        return False
    if not prove_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1(
        repo_root=root
    ):
        return False
    if PRODUCTIVE_APPLY_OCCURRED:
        return False
    decision_pre = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    handoff_ref = decision_pre.get("post_real_campaign_handoff_decision")
    handoff_complete = False
    if isinstance(handoff_ref, str) and (root / handoff_ref).is_file():
        handoff_complete = (
            json.loads((root / handoff_ref).read_text(encoding="utf-8")).get(
                "bounded_handoff_complete"
            )
            is True
        )
    if real_productive_apply_authorized_v1(repo_root=root) and not handoff_complete:
        return False
    if runtime_apply_possible_v1() is not False:
        return False
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        return False
    if int(PRODUCTIVE_NUMERIC_VALUES_SET) != 0:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("closed_execution_blocker") != CLOSED_EXECUTION_BLOCKER:
        return False
    if not handoff_complete and decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER:
        return False
    if decision.get("execution_boundary_implemented") is not True:
        return False
    if decision.get("productive_apply_occurred"):
        return False
    if decision.get("global_optimization_join_authorized"):
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_f1_m9_productive_apply_execution_boundary_v1",
]
