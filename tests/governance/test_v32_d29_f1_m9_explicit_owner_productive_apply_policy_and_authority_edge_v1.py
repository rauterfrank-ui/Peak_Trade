"""V32 D29 F1/M9 explicit Owner Apply policy edge tests (no productive apply execution)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    build_owner_apply_authorization_input_v1,
    compute_owner_apply_authorization_record_digest_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressBindingStatusV1,
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
    runtime_apply_possible_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1 import (
    CLOSED_D29_BLOCKER,
    DECISION_CONFIG,
    ExplicitOwnerProductiveApplyPolicyEdgeRequestV1,
    NEXT_TRUE_BLOCKER,
    POLICY_EDGE_STATUS_BOUND,
    POLICY_EDGE_STATUS_DENIED,
    PRODUCTIVE_APPLY_OCCURRED,
    evaluate_explicit_owner_productive_apply_policy_edge_v1,
    prove_negative_stage_separation_v1,
)
from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_closure_v1 import (
    prove_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1,
)
from src.governance.v32_d29_f1_m9_per_ingress_productive_authorization_apply_adjudication_v1 import (
    AuthorityEdgeClassificationV1,
    AuthorityStageStatusV1,
    build_authority_stage_decomposition_v1,
    build_f1_m9_per_ingress_authority_census_v1,
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


def _artifacts(tmp_path: Path) -> dict[str, Any]:
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
    authorization = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    config = configuration.configuration_record
    assert config is not None
    contract = build_productive_target_contract_v1()
    now = datetime.now(timezone.utc)
    apply_input = build_owner_apply_authorization_input_v1(
        registry_digest=str(registry["registry_digest"]),
        ingress_digest=str(config["ingress_digest"]),
        binding_digest=binding.binding_digest,
        owner_authorization_record_digest=str(config["owner_authorization_record_digest"]),
        authorization_id=str(config["authorization_id"]),
        authorization_digest=str(config["authorization_digest"]),
        configuration_id=str(config["configuration_id"]),
        configuration_digest=str(config["configuration_digest"]),
        candidate_parameter_value_digest=str(config["candidate_parameter_value_digest"]),
        productive_target_id=str(config["productive_target_id"]),
        productive_target_version=str(config["productive_target_version"]),
        productive_target_contract_digest=str(contract["contract_digest"]),
        not_before=(now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expires_at=(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    return {
        "registry_digest": str(registry["registry_digest"]),
        "binding": binding,
        "authorization": authorization,
        "configuration": configuration,
        "apply_input": apply_input,
    }


def test_closure_and_decision_invariants() -> None:
    assert prove_v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1(
        repo_root=REPO_ROOT
    )
    assert prove_negative_stage_separation_v1()
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["closed_d29_blocker"] == CLOSED_D29_BLOCKER
    assert decision["next_true_blocker"] == NEXT_TRUE_BLOCKER
    assert decision["productive_apply_occurred"] is False
    assert decision["productive_numeric_values_set_current"] == 0
    assert PRODUCTIVE_APPLY_OCCURRED is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert runtime_apply_possible_v1() is False


def test_d29_census_apply_edge_adjudicated() -> None:
    apply_edge = next(
        e
        for e in build_f1_m9_per_ingress_authority_census_v1(repo_root=REPO_ROOT)
        if e.edge_id == "PRODUCTIVE_APPLY_BOUNDARY"
    )
    assert apply_edge.classification == AuthorityEdgeClassificationV1.ADJUDICATED
    stages = build_authority_stage_decomposition_v1(repo_root=REPO_ROOT)
    apply_stage = next(s for s in stages if s.stage == "PRODUCTIVE_APPLY")
    assert apply_stage.status == AuthorityStageStatusV1.PROVEN_CURRENT
    assert apply_stage.implies_next_stage is False


def test_policy_edge_binds_without_apply(tmp_path: Any) -> None:
    data = _artifacts(tmp_path)
    assert data["binding"].status == PerIngressBindingStatusV1.BOUND
    result = evaluate_explicit_owner_productive_apply_policy_edge_v1(
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1(
            owner_apply_input=data["apply_input"],
            per_ingress_binding=data["binding"],
            authorization=data["authorization"],
            configuration=data["configuration"],
            registry_digest=data["registry_digest"],
        )
    )
    assert result.policy_edge_status == POLICY_EDGE_STATUS_BOUND
    assert result.productive_apply_occurred is False
    assert result.productive_apply_authorized is False
    assert result.runtime_apply_authority == "NONE"
    record = data["configuration"].configuration_record
    assert record is not None
    assert record.get("runtime_applied") is not True


def test_policy_edge_denies_configuration_digest_mismatch(tmp_path: Any) -> None:
    data = _artifacts(tmp_path)
    record = dict(data["apply_input"].owner_apply_authorization_record)
    record["configuration_digest"] = "0" * 64
    record["owner_apply_authorization_record_digest"] = (
        compute_owner_apply_authorization_record_digest_v1(record)
    )
    from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
        OwnerApplyAuthorizationInputV1,
    )

    bad_input = OwnerApplyAuthorizationInputV1(
        owner_apply_authorization_record=record,
        owner_apply_authorization_record_digest=str(
            record["owner_apply_authorization_record_digest"]
        ),
    )
    result = evaluate_explicit_owner_productive_apply_policy_edge_v1(
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1(
            owner_apply_input=bad_input,
            per_ingress_binding=data["binding"],
            authorization=data["authorization"],
            configuration=data["configuration"],
            registry_digest=data["registry_digest"],
        )
    )
    assert result.policy_edge_status == POLICY_EDGE_STATUS_DENIED
    assert "CONFIGURATION_DIGEST_MISMATCH" in result.reason_codes


def test_policy_edge_denies_foreign_registry_digest(tmp_path: Any) -> None:
    data = _artifacts(tmp_path)
    record = dict(data["apply_input"].owner_apply_authorization_record)
    record["registry_digest"] = "f" * 64
    record["owner_apply_authorization_record_digest"] = (
        compute_owner_apply_authorization_record_digest_v1(record)
    )
    from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
        OwnerApplyAuthorizationInputV1,
    )

    bad_input = OwnerApplyAuthorizationInputV1(
        owner_apply_authorization_record=record,
        owner_apply_authorization_record_digest=str(
            record["owner_apply_authorization_record_digest"]
        ),
    )
    result = evaluate_explicit_owner_productive_apply_policy_edge_v1(
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1(
            owner_apply_input=bad_input,
            per_ingress_binding=data["binding"],
            authorization=data["authorization"],
            configuration=data["configuration"],
            registry_digest=data["registry_digest"],
        )
    )
    assert result.policy_edge_status == POLICY_EDGE_STATUS_DENIED
    assert "REGISTRY_DIGEST_MISMATCH" in result.reason_codes


def test_policy_edge_denies_expired_apply_record(tmp_path: Any) -> None:
    data = _artifacts(tmp_path)
    record = dict(data["apply_input"].owner_apply_authorization_record)
    record["expires_at"] = "2020-01-01T00:00:00Z"
    record["not_before"] = "2019-01-01T00:00:00Z"
    record["owner_apply_authorization_record_digest"] = (
        compute_owner_apply_authorization_record_digest_v1(record)
    )
    from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
        OwnerApplyAuthorizationInputV1,
    )

    expired = OwnerApplyAuthorizationInputV1(
        owner_apply_authorization_record=record,
        owner_apply_authorization_record_digest=str(
            record["owner_apply_authorization_record_digest"]
        ),
    )
    result = evaluate_explicit_owner_productive_apply_policy_edge_v1(
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1(
            owner_apply_input=expired,
            per_ingress_binding=data["binding"],
            authorization=data["authorization"],
            configuration=data["configuration"],
            registry_digest=data["registry_digest"],
            evaluation_time_utc=datetime(2021, 1, 1, tzinfo=timezone.utc),
        )
    )
    assert result.policy_edge_status == POLICY_EDGE_STATUS_DENIED
    assert "APPLY_EXPIRED" in result.reason_codes
