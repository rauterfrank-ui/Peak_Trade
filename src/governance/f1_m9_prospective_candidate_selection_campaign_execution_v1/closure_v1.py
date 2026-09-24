"""Closure proof for F1/M9 prospective campaign execution owner max-build v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    DECISION_CONFIG,
    NEXT_TRUE_BLOCKER,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_boundary_v1 import (
    CAMPAIGN_EXECUTED,
    NEW_DECISION_MAKING_EVIDENCE_GENERATED,
    prove_execution_proof_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_closure_v1 import (
    prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "f1_m9_prospective_campaign_execution_closure/v1"


def prove_f1_m9_prospective_candidate_selection_campaign_execution_owner_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[3]
    required = (
        root / NORMATIVE_SPEC,
        root / DECISION_CONFIG,
        root
        / "src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/execution_boundary_v1.py",
        root
        / "tests/governance/test_f1_m9_prospective_candidate_selection_campaign_execution_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    if not prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1(
        repo_root=root
    ):
        return False
    if not prove_execution_proof_v1(repo_root=root):
        return False
    if CAMPAIGN_EXECUTED:
        return False
    if NEW_DECISION_MAKING_EVIDENCE_GENERATED:
        return False
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        return False
    if int(PRODUCTIVE_NUMERIC_VALUES_SET) != 0:
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("execution_owner_implemented") is not True:
        return False
    if decision.get("runtime_authorization_active") is True:
        return False
    if decision.get("campaign_executed") is True:
        return False
    if decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER:
        return False
    return True


__all__ = [
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_f1_m9_prospective_candidate_selection_campaign_execution_owner_v1",
]
