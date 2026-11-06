"""D29 F1/M9 per-ingress authorization/apply adjudication max-build tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.governance.explicit_productive_authorization_v1 import (
    build_owner_explicit_productive_authorization_input_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    ChainStageV1,
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressBindingStatusV1,
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
    verify_per_ingress_binding_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1 import (
    AuthorityEdgeClassificationV1,
    AuthorityStageStatusV1,
    BLOCKER_EDGE,
    CLOSED_D29_BLOCKER,
    DECISION_CONFIG,
    MINIMAL_NEXT_OWNER_POLICY_QUESTION,
    NEXT_TRUE_BLOCKER,
    WORKPACKAGE_ID,
    build_authority_stage_decomposition_v1,
    build_f1_m9_per_ingress_authority_census_v1,
    prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1,
)
from src.governance.v32_d29_f1_m9_per_ingress_productive_authorization_apply_closure_v1 import (
    prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_max_build_proof_and_decision() -> None:
    assert prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_max_build_v1(
        repo_root=REPO_ROOT
    )
    assert prove_v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1(
        repo_root=REPO_ROOT
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["d28_status"] == "PROVEN_CURRENT"
    assert decision["d29_status"] == "PROVEN_CURRENT"
    assert decision["d29_closure_proven"] is True
    assert decision["closed_d29_blocker"] == CLOSED_D29_BLOCKER
    assert decision["next_true_blocker"] == NEXT_TRUE_BLOCKER
    assert decision["blocker_edge"] == BLOCKER_EDGE
    assert decision["minimal_next_owner_policy_question"] == MINIMAL_NEXT_OWNER_POLICY_QUESTION
    assert decision["productive_apply_authorized"] is False
    assert decision["promotion_authorized"] is False
    assert decision["productive_numeric_values_set_current"] == 0
    assert decision["global_optimization_join_authorized"] is False
    assert decision["external_effect_authorized"] is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0


def test_authority_census_and_apply_boundary() -> None:
    edges = build_f1_m9_per_ingress_authority_census_v1(repo_root=REPO_ROOT)
    assert len(edges) == 9
    apply_edge = next(e for e in edges if e.edge_id == "PRODUCTIVE_APPLY_BOUNDARY")
    assert apply_edge.classification == AuthorityEdgeClassificationV1.ADJUDICATED
    forbidden = next(e for e in edges if e.edge_id == "OPTIMIZATION_DIRECT_RUNTIME_WRITE")
    assert forbidden.classification == AuthorityEdgeClassificationV1.FORBIDDEN


def test_stage_decomposition_no_implicit_apply() -> None:
    stages = build_authority_stage_decomposition_v1(repo_root=REPO_ROOT)
    by_name = {s.stage: s for s in stages}
    assert by_name["PRODUCTIVE_APPLY"].status == AuthorityStageStatusV1.PROVEN_CURRENT
    assert by_name["EXTERNAL_EFFECT"].status == AuthorityStageStatusV1.FORBIDDEN
    for stage in stages:
        assert stage.implies_next_stage is False


def test_per_ingress_chain_resolves_through_transport_apply_blocked(tmp_path: Any) -> None:
    registry = load_scoped_join_registry_v1(repo_root=REPO_ROOT)
    ingress = _ingress_for_m9(tmp_path)
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    binding = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
    )
    assert binding.status == PerIngressBindingStatusV1.BOUND
    assert verify_per_ingress_binding_digest_v1(binding.binding_record)

    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=ingress,
        admission=admission,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
    )
    assert chain.chain_status == "RESOLVED_THROUGH_RUNTIME_TRANSPORT_APPLY_BLOCKED"
    assert chain.stop_stage == ChainStageV1.PRODUCTIVE_APPLY
    assert chain.productive_apply_authorized is False
    assert chain.runtime_transport is not None
    assert chain.runtime_transport.seam_for_consumer is not None


def test_per_ingress_binding_denied_on_registry_digest_mismatch(tmp_path: Any) -> None:
    ingress = _ingress_for_m9(tmp_path)
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    denied = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest="0" * 64,
    )
    assert denied.status == PerIngressBindingStatusV1.DENIED_FAIL_CLOSED
