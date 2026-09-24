"""F1/M9 productive apply execution boundary tests (no real productive apply)."""

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
    OwnerApplyAuthorizationInputV1,
    build_owner_apply_authorization_input_v1,
    compute_owner_apply_authorization_record_digest_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    ChainStageV1,
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    CLOSED_EXECUTION_BLOCKER,
    DECISION_CONFIG,
    F1M9ProductiveApplyExecutionPhaseV1,
    F1M9ProductiveApplyExecutionRequestV1,
    NEXT_TRUE_BLOCKER,
    POLICY_EDGE_STATUS_BOUND,
    PRODUCTIVE_APPLY_OCCURRED,
    STATUS_EXECUTION_READY,
    STATUS_REAL_APPLY_BLOCKED,
    evaluate_f1_m9_productive_apply_execution_boundary_v1,
    real_productive_apply_authorized_v1,
)
from src.governance.f1_m9_productive_apply_execution_closure_v1 import (
    prove_f1_m9_productive_apply_execution_boundary_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    F1M9ScopedOwnerApplyAdjudicationRequestV1,
    evaluate_f1_m9_scoped_owner_productive_apply_v1,
)
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
from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1 import (
    POLICY_EDGE_STATUS_BOUND as D29_BOUND,
    evaluate_explicit_owner_productive_apply_policy_edge_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
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


def _apply_input(artifacts: dict[str, Any]) -> Any:
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


def test_closure_and_decision() -> None:
    assert prove_f1_m9_productive_apply_execution_boundary_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["closed_execution_blocker"] == CLOSED_EXECUTION_BLOCKER
    assert decision["next_true_blocker"] == NEXT_TRUE_BLOCKER
    assert decision["real_productive_apply_authorized"] is False
    assert decision["execution_boundary_implemented"] is True


def test_execution_proof_happy_path(tmp_path: Path) -> None:
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
        )
    )
    assert result.execution_status == STATUS_EXECUTION_READY
    assert result.policy_edge_status == POLICY_EDGE_STATUS_BOUND
    assert result.productive_apply_authorized is True
    assert result.productive_apply_occurred is False
    assert result.consumer_module == POLICY_CONSUMER_MODULE
    assert result.execution_evidence_digest
    record = result.configuration_after_execution.configuration_record
    assert record is not None
    assert record["candidate_value_applied"] is False


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
        )
    )
    assert result.execution_status != STATUS_EXECUTION_READY


def test_configuration_digest_mismatch_rejected(tmp_path: Path) -> None:
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
        )
    )
    assert "CONFIGURATION_DIGEST_MISMATCH" in result.reason_codes


def test_registry_digest_mismatch_rejected(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    record = dict(apply_input.owner_apply_authorization_record)
    record["registry_digest"] = "1" * 64
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
        )
    )
    assert "REGISTRY_DIGEST_MISMATCH" in result.reason_codes


def test_stale_expired_record_rejected(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    now = datetime.now(timezone.utc)
    apply_input = build_owner_apply_authorization_input_v1(
        registry_digest=artifacts["registry_digest"],
        ingress_digest=str(artifacts["configuration"].configuration_record["ingress_digest"]),
        binding_digest=artifacts["binding"].binding_digest,
        owner_authorization_record_digest=str(
            artifacts["configuration"].configuration_record["owner_authorization_record_digest"]
        ),
        authorization_id=str(artifacts["configuration"].configuration_record["authorization_id"]),
        authorization_digest=str(
            artifacts["configuration"].configuration_record["authorization_digest"]
        ),
        configuration_id=str(artifacts["configuration"].configuration_record["configuration_id"]),
        configuration_digest=str(
            artifacts["configuration"].configuration_record["configuration_digest"]
        ),
        candidate_parameter_value_digest=str(
            artifacts["configuration"].configuration_record["candidate_parameter_value_digest"]
        ),
        productive_target_id=str(
            artifacts["configuration"].configuration_record["productive_target_id"]
        ),
        productive_target_version=str(
            artifacts["configuration"].configuration_record["productive_target_version"]
        ),
        productive_target_contract_digest=str(
            build_productive_target_contract_v1()["contract_digest"]
        ),
        not_before=(now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expires_at=(now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
            evaluation_time_utc=now,
        )
    )
    assert "APPLY_EXPIRED" in result.reason_codes


def test_apply_replay_idempotent_via_execution_boundary(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    paths = _ledger_paths(tmp_path)
    request = F1M9ProductiveApplyExecutionRequestV1(
        owner_apply_input=apply_input,
        per_ingress_binding=artifacts["binding"],
        authorization=artifacts["authorization"],
        configuration=artifacts["configuration"],
        registry_digest=artifacts["registry_digest"],
        ledger_paths=paths,
    )
    first = evaluate_f1_m9_productive_apply_execution_boundary_v1(request)
    second = evaluate_f1_m9_productive_apply_execution_boundary_v1(request)
    assert first.execution_status == STATUS_EXECUTION_READY
    assert second.execution_status == STATUS_EXECUTION_READY
    assert first.apply_ledger_entry_digest == second.apply_ledger_entry_digest


def test_direct_apply_without_policy_edge_still_possible_at_adjudicator(tmp_path: Path) -> None:
    """Adjudicator unit path exists; chain and execution boundary require policy edge first."""
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    direct = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
        )
    )
    assert direct.productive_apply_authorized is True
    boundary = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path / "boundary"),
        )
    )
    assert boundary.policy_edge_status == D29_BOUND


def test_policy_edge_alone_does_not_execute_apply(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    from src.governance.v32_d29_f1_m9_explicit_owner_productive_apply_policy_and_authority_edge_v1 import (
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1,
    )

    edge = evaluate_explicit_owner_productive_apply_policy_edge_v1(
        ExplicitOwnerProductiveApplyPolicyEdgeRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
        )
    )
    assert edge.policy_edge_status == D29_BOUND
    assert edge.productive_apply_occurred is False
    assert not (tmp_path / "apply.jsonl").exists()


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


def test_authorized_productive_apply_phase_blocked(tmp_path: Path) -> None:
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
        )
    )
    assert result.execution_status == STATUS_REAL_APPLY_BLOCKED
    assert real_productive_apply_authorized_v1(repo_root=REPO_ROOT) is False


def test_chain_uses_execution_boundary(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    apply_input = _apply_input(artifacts)
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=artifacts["ingress"],
        admission=artifacts["admission"],
        owner_input=artifacts["owner_input"],
        registry_digest=artifacts["registry_digest"],
        owner_apply_input=apply_input,
        ledger_paths=_ledger_paths(tmp_path),
    )
    assert chain.productive_apply_authorized is True
    assert chain.runtime_transport is not None


def test_global_invariants() -> None:
    assert PRODUCTIVE_APPLY_OCCURRED is False
    assert runtime_apply_possible_v1() is False
    assert direct_productive_write_possible_v1() is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False
