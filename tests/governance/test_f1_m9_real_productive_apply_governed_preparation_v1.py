"""Governed preparation for F1/M9 real productive apply (no real apply in this slice)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import patch

import pytest

from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.f1_m9_canonical_productive_candidate_adjudication_v1 import (
    adjudicate_canonical_f1_m9_productive_candidate_v1,
)
from src.governance.f1_m9_canonical_productive_candidate_evidence_census_v1 import (
    CAMPAIGN_EXECUTION_BLOCKER,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
    build_owner_apply_authorization_input_v1,
    compute_owner_apply_authorization_record_digest_v1,
)
from src.governance.f1_m9_owner_apply_record_materialization_v1 import (
    STATUS_NOT_ATTEMPTED,
    materialize_owner_apply_record_when_canonical_candidate_resolved_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    ChainStageV1,
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 import (
    resolve_canonical_f1_m9_productive_apply_ledger_paths_v1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    DECISION_CONFIG,
    F1M9ProductiveApplyExecutionPhaseV1,
    F1M9ProductiveApplyExecutionRequestV1,
    NEXT_TRUE_BLOCKER,
    PRODUCTIVE_APPLY_OCCURRED,
    STATUS_EXECUTION_READY,
    STATUS_PRODUCTIVE_APPLY_COMPLETED,
    STATUS_REAL_APPLY_BLOCKED,
    evaluate_f1_m9_productive_apply_execution_boundary_v1,
    load_execution_boundary_decision_v1,
    real_productive_apply_authorized_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_real_productive_apply_decision_binding_v1 import (
    BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED,
    STATUS_NOT_AUTHORIZED,
    evaluate_real_productive_apply_decision_binding_v1,
    prove_decision_binding_contract_v1,
)
from src.governance.f1_m9_real_productive_apply_preparation_closure_v1 import (
    prove_f1_m9_real_productive_apply_governed_preparation_v1,
)
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import RUNTIME_APPLY_AUTHORITY_VALUE
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
    runtime_apply_possible_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    POLICY_CONSUMER_MODULE,
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    direct_productive_write_possible_v1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1 import (
    ExplicitOwnerProductiveApplyPolicyEdgeRequestV1,
    evaluate_explicit_owner_productive_apply_policy_edge_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    NUMERIC_MAX_AGE_DECIDED,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _ledger_paths(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=rev,
    )


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
    return {
        "registry_digest": str(registry["registry_digest"]),
        "ingress": ingress,
        "admission": admission,
        "owner_input": owner_input,
        "binding": binding,
        "authorization": authorization,
        "configuration": configuration,
    }


def _apply_input(artifacts: dict[str, Any]) -> OwnerApplyAuthorizationInputV1:
    config = artifacts["configuration"].configuration_record
    assert config is not None
    contract = build_productive_target_contract_v1()
    now = datetime.now(timezone.utc)
    return build_owner_apply_authorization_input_v1(
        registry_digest=artifacts["registry_digest"],
        ingress_digest=str(config["ingress_digest"]),
        binding_digest=artifacts["binding"].binding_digest,
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


def _decision_with_bound_digest(
    digest: str, *, authorized: bool = True
) -> MappingProxyType[str, Any]:
    raw = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    raw["real_productive_apply_authorized"] = authorized
    raw["authorized_owner_apply_record_digest"] = digest
    return MappingProxyType(raw)


def test_preparation_closure_and_decision_contract() -> None:
    assert prove_f1_m9_real_productive_apply_governed_preparation_v1(repo_root=REPO_ROOT)
    assert prove_decision_binding_contract_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["governed_preparation_implemented"] is True
    assert decision["next_true_blocker"] == NEXT_TRUE_BLOCKER
    assert decision["real_productive_apply_binding_mode"] == (
        BINDING_MODE_OWNER_APPLY_RECORD_DIGEST_REQUIRED
    )
    assert decision["real_productive_apply_authorized"] is False
    assert decision["authorized_owner_apply_record_digest"] is None
    assert decision["numeric_threshold_separate_authorization_required"] is True


def test_canonical_candidate_not_resolved_on_current_main() -> None:
    adj = adjudicate_canonical_f1_m9_productive_candidate_v1(repo_root=REPO_ROOT)
    assert adj.resolved is False
    assert adj.candidate_id is None
    assert adj.candidate_value is None
    assert adj.earliest_blocker.startswith("F1_M9_")
    assert CAMPAIGN_EXECUTION_BLOCKER in adj.reason_codes
    assert adj.explicit_productive_authorization_resolved is False


def test_owner_apply_record_materialization_not_attempted_without_candidate(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    mat = materialize_owner_apply_record_when_canonical_candidate_resolved_v1(
        registry_digest=artifacts["registry_digest"],
        ingress_digest=str(artifacts["configuration"].configuration_record["ingress_digest"]),
        binding=artifacts["binding"],
        authorization=artifacts["authorization"],
        configuration=artifacts["configuration"],
        not_before=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        repo_root=REPO_ROOT,
    )
    assert mat.materialization_status == STATUS_NOT_ATTEMPTED
    assert mat.owner_apply_input is None


def test_durable_ledger_paths_resolve_without_creating_files() -> None:
    paths = resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=REPO_ROOT)
    assert "f1_m9_scoped_owner_productive_apply_v1" in str(paths.apply_ledger_path)
    assert not paths.apply_ledger_path.exists()


def test_decision_flag_alone_no_apply(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    binding = evaluate_real_productive_apply_decision_binding_v1(
        owner_apply_authorization_record_digest=apply_input.owner_apply_authorization_record_digest,
        repo_root=REPO_ROOT,
    )
    assert binding.apply_permitted is False
    assert STATUS_NOT_AUTHORIZED in binding.reason_codes


def test_authorized_productive_apply_phase_blocked_without_binding(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
            execution_phase=F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY,
        ),
        repo_root=REPO_ROOT,
    )
    assert result.execution_status == STATUS_REAL_APPLY_BLOCKED
    assert result.productive_apply_occurred is False
    assert real_productive_apply_authorized_v1(repo_root=REPO_ROOT) is False


def test_authorized_productive_apply_test_path_when_digest_bound(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    digest = apply_input.owner_apply_authorization_record_digest
    bound_decision = _decision_with_bound_digest(digest)

    with patch(
        "src.governance.f1_m9_productive_apply_execution_boundary_v1.load_execution_boundary_decision_v1",
        return_value=bound_decision,
    ):
        result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
            F1M9ProductiveApplyExecutionRequestV1(
                owner_apply_input=apply_input,
                per_ingress_binding=artifacts["binding"],
                authorization=artifacts["authorization"],
                configuration=artifacts["configuration"],
                registry_digest=artifacts["registry_digest"],
                ledger_paths=_ledger_paths(tmp_path),
                execution_phase=F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY,
            ),
            repo_root=REPO_ROOT,
        )
    assert result.execution_status == STATUS_PRODUCTIVE_APPLY_COMPLETED
    assert result.productive_apply_occurred is True
    assert result.consumer_module == POLICY_CONSUMER_MODULE
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False


def test_execution_proof_zero_productive_mutation(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
        ),
        repo_root=REPO_ROOT,
    )
    assert result.execution_status == STATUS_EXECUTION_READY
    assert result.productive_apply_occurred is False


def test_policy_edge_alone_no_apply(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    edge = evaluate_explicit_owner_productive_apply_policy_edge_v1(
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
        )
    )
    assert edge.productive_apply_occurred is False


def test_materialization_alone_no_apply(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=artifacts["ingress"],
        admission=artifacts["admission"],
        owner_input=artifacts["owner_input"],
        registry_digest=artifacts["registry_digest"],
    )
    assert chain.productive_apply_authorized is False
    assert chain.stop_stage == ChainStageV1.PRODUCTIVE_APPLY


def test_missing_owner_apply_record_rejected(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=OwnerApplyAuthorizationInputV1(
                owner_apply_authorization_record={},
                owner_apply_authorization_record_digest="",
            ),
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
        ),
        repo_root=REPO_ROOT,
    )
    assert result.execution_status != STATUS_EXECUTION_READY


def test_wrong_configuration_digest_rejected(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    record = dict(apply_input.owner_apply_authorization_record)
    record["configuration_digest"] = "0" * 64
    record["owner_apply_authorization_record_digest"] = (
        compute_owner_apply_authorization_record_digest_v1(record)
    )
    bad = OwnerApplyAuthorizationInputV1(
        owner_apply_authorization_record=record,
        owner_apply_authorization_record_digest=str(
            record["owner_apply_authorization_record_digest"]
        ),
    )
    result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=bad,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
        ),
        repo_root=REPO_ROOT,
    )
    assert "CONFIGURATION_DIGEST_MISMATCH" in result.reason_codes


def test_global_invariants_unchanged() -> None:
    assert PRODUCTIVE_APPLY_OCCURRED is False
    assert runtime_apply_possible_v1() is False
    assert direct_productive_write_possible_v1() is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False
    decision = load_execution_boundary_decision_v1(repo_root=REPO_ROOT)
    assert decision.get("trading_decision_authority_changed") is False
    assert decision.get("selection_authority_changed") is False
    assert decision.get("promotion_authorized") is False
    assert decision.get("self_deploy_authorized") is False


def test_wrong_bound_digest_rejects_even_if_flag_true(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    bound_decision = _decision_with_bound_digest("f" * 64)
    with patch(
        "src.governance.f1_m9_productive_apply_execution_boundary_v1.load_execution_boundary_decision_v1",
        return_value=bound_decision,
    ):
        result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
            F1M9ProductiveApplyExecutionRequestV1(
                owner_apply_input=apply_input,
                per_ingress_binding=artifacts["binding"],
                authorization=artifacts["authorization"],
                configuration=artifacts["configuration"],
                registry_digest=artifacts["registry_digest"],
                ledger_paths=_ledger_paths(tmp_path),
                execution_phase=F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY,
            ),
            repo_root=REPO_ROOT,
        )
    assert result.execution_status == STATUS_REAL_APPLY_BLOCKED
    assert result.productive_apply_occurred is False


def test_runtime_apply_authority_remains_scoped_only(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    digest = apply_input.owner_apply_authorization_record_digest
    bound_decision = _decision_with_bound_digest(digest)
    with patch(
        "src.governance.f1_m9_productive_apply_execution_boundary_v1.load_execution_boundary_decision_v1",
        return_value=bound_decision,
    ):
        result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
            F1M9ProductiveApplyExecutionRequestV1(
                owner_apply_input=apply_input,
                per_ingress_binding=artifacts["binding"],
                authorization=artifacts["authorization"],
                configuration=artifacts["configuration"],
                registry_digest=artifacts["registry_digest"],
                ledger_paths=_ledger_paths(tmp_path),
                execution_phase=F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY,
            ),
            repo_root=REPO_ROOT,
        )
    assert result.runtime_apply_authority == RUNTIME_APPLY_AUTHORITY_VALUE
