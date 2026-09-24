"""Closure proof for F1/M9 authorized campaign run orchestration owner v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    orchestration_boundary_invariants_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.closure_v1 import (
    prove_f1_m9_prospective_candidate_selection_campaign_execution_owner_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    NEXT_TRUE_BLOCKER_AFTER_ORCHESTRATION,
    ORCHESTRATION_DECISION_CONFIG,
    ORCHESTRATION_NORMATIVE_SPEC,
    ORCHESTRATION_OWNER_ID,
    ORCHESTRATION_WORKPACKAGE_ID,
)

SCHEMA_VERSION: Final[str] = "f1_m9_prospective_campaign_authorized_run_orchestration_closure/v1"


def prove_f1_m9_prospective_campaign_authorized_run_orchestration_owner_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[3]
    required = (
        root / ORCHESTRATION_NORMATIVE_SPEC,
        root / ORCHESTRATION_DECISION_CONFIG,
        root / "src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/"
        "authorized_run_orchestration_v1.py",
        root
        / "tests/governance/test_f1_m9_prospective_campaign_authorized_run_orchestration_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    if not prove_f1_m9_prospective_candidate_selection_campaign_execution_owner_v1(repo_root=root):
        return False
    invariants = orchestration_boundary_invariants_v1()
    if not all(invariants.values()):
        return False
    decision = json.loads((root / ORCHESTRATION_DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("orchestration_owner_id") != ORCHESTRATION_OWNER_ID:
        return False
    if decision.get("orchestration_owner_status") != "PRESENT_COMPLETE":
        return False
    if decision.get("authorized_campaign_execution_terminal_path_proven") is not True:
        return False
    if decision.get("campaign_executed") is True:
        return False
    if decision.get("public_market_data_external_read_occurred") is True:
        return False
    if decision.get("real_evidence_written") is True:
        return False
    if decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER_AFTER_ORCHESTRATION:
        return False
    return True


__all__ = [
    "ORCHESTRATION_OWNER_ID",
    "ORCHESTRATION_WORKPACKAGE_ID",
    "SCHEMA_VERSION",
    "prove_f1_m9_prospective_campaign_authorized_run_orchestration_owner_v1",
]
