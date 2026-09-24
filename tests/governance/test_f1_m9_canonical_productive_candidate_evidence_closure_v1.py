"""F1/M9 canonical candidate/evidence closure census (read-only)."""

from __future__ import annotations

from pathlib import Path

from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_canonical_productive_candidate_evidence_census_v1 import (
    CAMPAIGN_EXECUTION_OWNER_GO_BLOCKER,
    EVIDENCE_CLASS_COUNTERFACTUAL,
    run_f1_m9_canonical_productive_candidate_evidence_census_v1,
)
from src.governance.f1_m9_real_productive_apply_preparation_closure_v1 import (
    prove_f1_m9_real_productive_apply_governed_preparation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_evidence_census_chain_proven_and_fail_closed() -> None:
    census = run_f1_m9_canonical_productive_candidate_evidence_census_v1(repo_root=REPO_ROOT)
    assert census.chain_proven is True
    assert census.surface_id == "VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1"
    assert census.source_candidate_parameter == "max_age_seconds"
    assert census.preregistration_threshold_selection_authorized is False
    assert census.existing_campaign_evidence_class == EVIDENCE_CLASS_COUNTERFACTUAL
    assert census.existing_campaign_can_select_productive_candidate is False
    assert census.candidate_selection_authority_resolved is False
    assert census.candidate_selection_rule_id == "F1_M9_ROBUST_REGION_UNIQUE_SURVIVOR_POINT_V1"
    assert census.optimization_ingress_snapshot_tracked is False
    assert census.new_prospective_campaign_required is True
    assert census.owner_policy_required is False
    assert census.earliest_blocker == CAMPAIGN_EXECUTION_OWNER_GO_BLOCKER
    assert census.campaign_id == "cv_maxage_productive_evidence_campaign_v1_f5e3f95105cd847f"


def test_adjudication_remains_unresolved() -> None:
    adj = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=REPO_ROOT)
    assert adj.resolved is False
    assert adj.candidate_id is None
    assert adj.candidate_value is None
    assert adj.explicit_productive_authorization_resolved is False
    assert CAMPAIGN_EXECUTION_OWNER_GO_BLOCKER in adj.reason_codes


def test_preparation_closure_still_passes() -> None:
    assert prove_f1_m9_real_productive_apply_governed_preparation_v1(repo_root=REPO_ROOT)
