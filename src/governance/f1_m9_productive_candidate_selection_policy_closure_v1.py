"""Closure proof for F1/M9 selection policy + prospective preregistration slice."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_preregistration_v1 import (
    assert_historical_preregistration_unchanged_v1,
    resolve_prospective_preregistration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1 import (
    historical_evidence_cannot_select_v1,
)
from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
    HISTORICAL_PREREGISTRATION_DIGEST,
    NORMATIVE_SPEC,
    POLICY_DECISION_CONFIG,
    resolve_f1_m9_selection_policy_v1,
)
from src.governance.f1_m9_real_productive_apply_preparation_closure_v1 import (
    prove_f1_m9_real_productive_apply_governed_preparation_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "f1_m9_productive_candidate_selection_policy_closure/v1"
WORKPACKAGE_ID: Final[str] = (
    "F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_AND_PROSPECTIVE_CAMPAIGN_V1"
)
EARLIEST_REMAINING_BLOCKER: Final[str] = (
    "F1_M9_PROSPECTIVE_SELECTION_CAMPAIGN_EXECUTION_REQUIRES_OWNER_GO"
)


def prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1(
    *, repo_root: Path | None = None
) -> bool:
    root = repo_root or Path(__file__).resolve().parents[2]
    required = (
        root / NORMATIVE_SPEC,
        root / "src/governance/f1_m9_productive_candidate_selection_policy_v1.py",
        root
        / "src/governance/f1_m9_prospective_candidate_selection_campaign_preregistration_v1.py",
        root / "src/governance/f1_m9_prospective_candidate_selection_evidence_leakage_guard_v1.py",
        root
        / "tests/governance/test_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1.py",
    )
    if not all(p.is_file() for p in required):
        return False
    if not prove_f1_m9_real_productive_apply_governed_preparation_v1(repo_root=root):
        return False
    policy = resolve_f1_m9_selection_policy_v1(repo_root=root)
    if not policy.owner_selection_policy_resolved:
        return False
    if not policy.f1_m9_scoped_candidate_selection_policy_created:
        return False
    prereg = resolve_prospective_preregistration_v1(repo_root=root)
    if not prereg.new_prospective_campaign_preregistered:
        return False
    if prereg.new_prospective_campaign_executed:
        return False
    if prereg.new_decision_making_evidence_generated:
        return False
    if not prereg.threshold_selection_authorized_within_new_campaign:
        return False
    if not prereg.historical_preregistration_unchanged:
        return False
    if prereg.historical_evidence_decision_leakage:
        return False
    if not assert_historical_preregistration_unchanged_v1(repo_root=root):
        return False
    if not historical_evidence_cannot_select_v1(
        historical_campaign_id=HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
        historical_preregistration_digest=HISTORICAL_PREREGISTRATION_DIGEST,
    ):
        return False
    adj = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=root)
    if adj.resolved:
        return False
    if adj.candidate_id is not None:
        return False
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        return False
    if int(PRODUCTIVE_NUMERIC_VALUES_SET) != 0:
        return False
    decision_path = root / POLICY_DECISION_CONFIG
    if decision_path.is_file():
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        if decision.get("selection_authority_changed") is True:
            return False
        if decision.get("trading_authority_changed") is True:
            return False
        if decision.get("promotion_authority_changed") is True:
            return False
    return True


__all__ = [
    "EARLIEST_REMAINING_BLOCKER",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_f1_m9_productive_candidate_selection_policy_and_prospective_campaign_v1",
]
