"""Closure proof for F1/M9 REAL prospective campaign execution enablement v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    orchestration_boundary_invariants_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_constants_v1 import (
    ENABLEMENT_DECISION_CONFIG,
    ENABLEMENT_NORMATIVE_SPEC,
    ENABLEMENT_WORKPACKAGE_ID,
    NEXT_TRUE_BLOCKER_AFTER_ENABLEMENT,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.orchestration_closure_v1 import (
    prove_f1_m9_prospective_campaign_authorized_run_orchestration_owner_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_public_md_session_adapter_v1 import (
    resolve_canonical_real_md_supplier_runtime_binding_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_artifacts_v1 import (
    post_real_campaign_handoff_bounded_complete_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_issuance_v1 import (
    ISSUANCE_OWNER_ID,
)

POST_REAL_HANDOFF_BLOCKER: Final[str] = (
    "F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETION_V1"
)
THRESHOLD_VALUE_BLOCKER: Final[str] = "F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_AUTHORIZATION_OWNER_GO"

SCHEMA_VERSION: Final[str] = "f1_m9_real_prospective_campaign_execution_enablement_closure/v1"


def prove_f1_m9_real_prospective_campaign_execution_enablement_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[3]
    required = (
        root / ENABLEMENT_NORMATIVE_SPEC,
        root / ENABLEMENT_DECISION_CONFIG,
        root / "src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/"
        "runtime_authorization_issuance_v1.py",
        root / "src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/"
        "execution_mode_v1.py",
        root / "src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/"
        "real_public_md_session_adapter_v1.py",
        root / "src/governance/f1_m9_prospective_candidate_selection_campaign_execution_v1/"
        "real_campaign_evidence_pipeline_v1.py",
        root / "tests/governance/test_f1_m9_real_prospective_campaign_execution_enablement_v1.py",
        root / "scripts/run_f1_m9_prospective_real_authorized_campaign_execution_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    if not prove_f1_m9_prospective_campaign_authorized_run_orchestration_owner_v1(repo_root=root):
        return False
    invariants = orchestration_boundary_invariants_v1()
    if not all(invariants.values()):
        return False
    supplier = resolve_canonical_real_md_supplier_runtime_binding_v1(repo_root=root)
    if not supplier.get("real_md_supplier_runtime_bound"):
        return False
    decision = json.loads((root / ENABLEMENT_DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != ENABLEMENT_WORKPACKAGE_ID:
        return False
    if decision.get("runtime_authorization_issuance_owner_present") is not True:
        return False
    if decision.get("runtime_authorization_issuance_owner_id") != ISSUANCE_OWNER_ID:
        return False
    if decision.get("real_authorized_campaign_execution_path_implemented") is not True:
        return False
    if decision.get("real_authorized_campaign_execution_path_proven") is not True:
        return False
    if decision.get("canonical_real_md_supplier_runtime_bound") is not True:
        return False
    if decision.get("preregistered_session_runner_runtime_bound") is not True:
        return False
    if decision.get("durable_real_evidence_runtime_bound") is not True:
        return False
    if decision.get("exactly_once_real_path_proven") is not True:
        return False
    if decision.get("build_bind_only_separate") is not True:
        return False
    if decision.get("hermetic_terminal_test_separate") is not True:
        return False
    if decision.get("real_authorized_execution_separate") is not True:
        return False
    handoff_complete = post_real_campaign_handoff_bounded_complete_v1(repo_root=root)
    orchestration = json.loads(
        (
            root
            / "config/governance/f1_m9_prospective_campaign_authorized_run_orchestration_v1_decision_v1.json"
        ).read_text(encoding="utf-8")
    )
    real_run_complete = orchestration.get("campaign_executed") is True
    if handoff_complete or real_run_complete:
        if decision.get("campaign_executed") is not True:
            return False
        if decision.get("real_evidence_written") is not True:
            return False
        if decision.get("runtime_authorization_issued_for_real_campaign") is not True:
            return False
        if decision.get("runtime_authorization_consumed") is not True:
            return False
        next_blocker = str(decision.get("next_true_blocker") or "")
        if next_blocker not in (POST_REAL_HANDOFF_BLOCKER, THRESHOLD_VALUE_BLOCKER):
            return False
    else:
        if decision.get("campaign_executed") is True:
            return False
        if decision.get("public_market_data_external_read_occurred") is True:
            return False
        if decision.get("real_evidence_written") is True:
            return False
        if decision.get("runtime_authorization_issued_for_real_campaign") is True:
            return False
        if decision.get("runtime_authorization_consumed") is True:
            return False
        if decision.get("next_true_blocker") != NEXT_TRUE_BLOCKER_AFTER_ENABLEMENT:
            return False
    return True


__all__ = [
    "ENABLEMENT_WORKPACKAGE_ID",
    "SCHEMA_VERSION",
    "prove_f1_m9_real_prospective_campaign_execution_enablement_v1",
]
